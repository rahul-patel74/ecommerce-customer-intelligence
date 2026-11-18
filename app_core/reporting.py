from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    PageBreak,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app_core.analytics import (
    category_scope,
    first_month_retention,
    monthly_scope,
    state_scope,
    status_scope,
)
from app_core.data import filter_by_period, load_manifest, selected_filters
from app_core.sharing import get_public_app_url, snapshot_metadata

NAVY = colors.HexColor("#10243A")
INK = colors.HexColor("#1B2D42")
TEAL = colors.HexColor("#178F83")
PALE = colors.HexColor("#EAF5F3")
MUTED = colors.HexColor("#65778B")
LINE = colors.HexColor("#D7E1E9")


def _fmt_currency(value: float) -> str:
    return f"R$ {float(value or 0):,.2f}"


def _safe_period(filters: dict) -> str:
    start, end = filters.get("date_start"), filters.get("date_end")
    if start is None or end is None:
        return "Full available period"
    return f"{pd.Timestamp(start):%b %Y} - {pd.Timestamp(end):%b %Y}"


def _delivery_summary(frame: pd.DataFrame) -> dict[str, float | int | None]:
    if frame.empty:
        return {
            "orders_with_dates": 0,
            "average_delivery_days": None,
            "on_time_delivery_rate": None,
        }
    weight = pd.to_numeric(frame["delivered_orders_with_dates"], errors="coerce").fillna(0)
    denominator = float(weight.sum())
    average_days = None
    on_time_rate = None
    if denominator:
        average_days = float(
            (pd.to_numeric(frame["average_delivery_days"], errors="coerce").fillna(0) * weight).sum()
            / denominator
        )
        on_time_rate = float(
            (pd.to_numeric(frame["on_time_delivery_rate"], errors="coerce").fillna(0) * weight).sum()
            / denominator
        )
    return {
        "orders_with_dates": int(denominator),
        "average_delivery_days": average_days,
        "on_time_delivery_rate": on_time_rate,
    }


def _context(data: dict[str, pd.DataFrame]) -> dict:
    """Build an export context with explicit filtered and full-history scopes."""
    filters = selected_filters()
    manifest = load_manifest()
    snapshot = snapshot_metadata(manifest)

    monthly = monthly_scope(data)
    categories = category_scope(data)
    states = state_scope(data)
    statuses = status_scope(data)
    delivery = filter_by_period(data["delivery_performance"])

    cohort = data["cohort_retention"]
    retained, eligible, month_one_rate = first_month_retention(cohort)
    kpi = data["overview_kpis"].iloc[0]

    total_orders = int(statuses["total_orders"].sum()) if not statuses.empty else 0
    delivered_orders = int(monthly["delivered_orders"].sum()) if not monthly.empty else 0
    delivered_payment = (
        float(monthly["delivered_recorded_payment_value"].sum())
        if not monthly.empty else 0.0
    )

    month_columns = [
        column for column in [
            "order_month", "total_orders", "delivered_orders",
            "delivered_recorded_payment_value", "all_status_recorded_payment_value",
        ]
        if column in monthly.columns
    ]
    monthly_for_report = monthly[month_columns].tail(18).copy()

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC"),
        "snapshot": snapshot,
        "period": _safe_period(filters),
        "states": filters.get("states") or [],
        "categories": filters.get("categories") or [],
        "delivered_customers": int(kpi["delivered_customers"]),
        "one_time_customers": int(kpi["one_time_customers"]),
        "repeat_customers": int(kpi["repeat_customers"]),
        "repeat_rate": float(kpi["repeat_customer_rate"]),
        "all_time_delivered_payment": float(kpi["delivered_recorded_payment_value"]),
        "filtered_total_orders": total_orders,
        "filtered_delivered_orders": delivered_orders,
        "filtered_delivered_payment": delivered_payment,
        "month_one_retained": retained,
        "month_one_eligible": eligible,
        "month_one_rate": month_one_rate,
        "top_categories": categories.head(10),
        "top_states": states.head(10),
        "statuses": statuses,
        "monthly": monthly_for_report,
        "delivery": _delivery_summary(delivery),
        "delivery_monthly": delivery.tail(18).copy(),
        "rfm": data["rfm_segments"].sort_values("customer_count", ascending=False),
        "cohort": cohort,
        "data_quality": data["data_quality"],
        "manifest": manifest,
        "public_url": get_public_app_url(),
    }


def _html_table(rows: list[list[str]], headers: list[str], empty_message: str) -> str:
    if not rows:
        body = f"<tr><td colspan='{len(headers)}'>{html.escape(empty_message)}</td></tr>"
    else:
        body = "".join(
            "<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in row) + "</tr>"
            for row in rows
        )
    header = "".join(f"<th>{html.escape(str(item))}</th>" for item in headers)
    return f"<div class='table-wrap'><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>"


def build_html_report(data: dict[str, pd.DataFrame]) -> bytes:
    c = _context(data)

    category_rows = [
        [str(row.product_category), f"{int(row.total_orders):,}", _fmt_currency(row.item_plus_freight_value)]
        for row in c["top_categories"].itertuples()
    ]
    state_rows = [
        [str(row.customer_state), f"{int(row.delivered_orders):,}", _fmt_currency(row.recorded_payment_value)]
        for row in c["top_states"].itertuples()
    ]
    status_rows = [
        [str(row.order_status).replace("_", " ").title(), f"{int(row.total_orders):,}"]
        for row in c["statuses"].itertuples()
    ]
    monthly_rows = []
    for row in c["monthly"].itertuples():
        month = pd.Timestamp(row.order_month).strftime("%b %Y")
        payment = getattr(row, "delivered_recorded_payment_value", 0)
        monthly_rows.append([
            month,
            f"{int(getattr(row, 'total_orders', 0)):,}",
            f"{int(row.delivered_orders):,}",
            _fmt_currency(payment),
        ])
    rfm_rows = [
        [str(row.customer_segment), f"{int(row.customer_count):,}", _fmt_currency(row.total_monetary)]
        for row in c["rfm"].itertuples()
    ]
    dq_rows = [
        [str(row.issue), f"{int(row.flagged_rows):,}", str(row.decision)]
        for row in c["data_quality"].itertuples()
    ]

    state_filter = ", ".join(c["states"]) if c["states"] else "All states"
    category_filter = ", ".join(c["categories"]) if c["categories"] else "All categories"
    snapshot_label = c["snapshot"]["ist"].strftime("%d %b %Y, %I:%M %p IST") if c["snapshot"]["available"] else "Not recorded"
    delivery = c["delivery"]
    delivery_days = f"{delivery['average_delivery_days']:.1f} days" if delivery["average_delivery_days"] is not None else "Not available"
    on_time = f"{delivery['on_time_delivery_rate']:.1f}%" if delivery["on_time_delivery_rate"] is not None else "Not available"
    app_link = (
        f"<a class='app-link' href='{html.escape(c['public_url'], quote=True)}'>Open live E-commerce IQ dashboard</a>"
        if c["public_url"] else ""
    )

    filter_scope = (
        f"Period: {html.escape(c['period'])}<br>"
        f"States: {html.escape(state_filter)}<br>"
        f"Categories: {html.escape(category_filter)}"
    )

    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>E-commerce IQ | Filtered Executive Brief</title>
<style>
:root{{--ink:#14253b;--muted:#65788e;--teal:#137f78;--bg:#f3f7fa;--line:#dbe5ec;--panel:#fff;--blue:#3565a8}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Inter,Segoe UI,Arial,sans-serif}}
main{{max-width:1120px;margin:32px auto;padding:0 22px 60px}}header{{background:linear-gradient(120deg,#0b1728,#123b50 68%,#27365f);color:#f4fbff;padding:34px;border-radius:20px;box-shadow:0 14px 36px rgba(14,37,59,.14)}}
header small{{color:#87e3d4;font-weight:800;letter-spacing:.16em;text-transform:uppercase}}h1{{font-size:34px;line-height:1.1;margin:9px 0}}header p{{color:#bfd0de;margin:8px 0 0}}.meta{{margin-top:16px;color:#c7d7e4;font-size:12px}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0}}.card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:0 5px 18px rgba(30,54,77,.04)}}.label{{color:var(--muted);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em}}.value{{font-size:25px;font-weight:800;margin-top:7px}}.sub{{font-size:11px;color:var(--muted);margin-top:5px}}
section{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:22px;margin-top:16px}}h2{{font-size:18px;margin:0 0 12px}}.callout{{border-left:4px solid var(--teal);background:#eef8f6;padding:14px 16px;border-radius:8px;margin:12px 0}}.scope{{background:#f5f8fc;border:1px solid var(--line);padding:13px 16px;border-radius:10px;font-size:13px}}
.table-wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:12px}}th,td{{text-align:left;padding:9px;border-bottom:1px solid var(--line);vertical-align:top}}th{{color:#4e6479;background:#f6f9fb}}td:last-child,th:last-child{{text-align:right}}.muted{{color:var(--muted);font-size:12px}}footer{{text-align:center;color:var(--muted);font-size:11px;margin-top:22px}}.app-link{{display:inline-block;margin-top:8px;color:#fff;background:#147e78;padding:10px 14px;border-radius:9px;text-decoration:none;font-weight:700}}
@media(max-width:760px){{.cards{{grid-template-columns:repeat(2,1fr)}}header{{padding:24px}}h1{{font-size:27px}}section{{padding:16px}}}}
</style></head><body><main>
<header><small>E-commerce IQ · Intelligence Studio</small><h1>Executive Performance Brief</h1><p>Filtered operating performance with clearly identified full-history customer context.</p><div class="meta">Report generated {html.escape(c['generated_at'])}<br>Data snapshot: {html.escape(snapshot_label)}</div>{app_link}</header>
<section><h2>Applied dashboard filters</h2><div class="scope">{filter_scope}</div><p class="muted">The period and state filters apply to monthly operating, order-status and state results. The category filter applies to delivered category analysis. Delivery measures are period-filtered. RFM, cohort retention, payment-method summary and data-quality checks remain full-snapshot context because those extracts do not contain all selected filter dimensions.</p></section>
<div class="cards">
<div class="card"><div class="label">Delivered shoppers · full history</div><div class="value">{c['delivered_customers']:,}</div><div class="sub">{c['one_time_customers']:,} one-time · {c['repeat_customers']:,} repeat</div></div>
<div class="card"><div class="label">Repeat customer rate · full history</div><div class="value">{c['repeat_rate']:.2f}%</div><div class="sub">Share with more than one delivered order</div></div>
<div class="card"><div class="label">Delivered orders · selected scope</div><div class="value">{c['filtered_delivered_orders']:,}</div><div class="sub">{c['filtered_total_orders']:,} total orders in selected view</div></div>
<div class="card"><div class="label">Delivered payment · selected scope</div><div class="value">{_fmt_currency(c['filtered_delivered_payment'])}</div><div class="sub">Recorded payment value, not profit</div></div>
</div>
<section><h2>Executive readout</h2><div class="callout"><b>Repeat purchasing:</b> {c['one_time_customers']:,} of {c['delivered_customers']:,} delivered shoppers ({100*c['one_time_customers']/max(c['delivered_customers'],1):.1f}%) made one delivered purchase in the full observed history.</div><div class="callout"><b>Month 1 cohort retention:</b> {c['month_one_retained']:,} of {c['month_one_eligible']:,} eligible customers returned in the next calendar month ({c['month_one_rate']:.2f}%). This is a full-history weighted measure, not limited by the selected filter range.</div></section>
<section><h2>Monthly operating trend · selected period and state scope</h2>{_html_table(monthly_rows, ['Month','All-status orders','Delivered orders','Delivered recorded payment'], 'No monthly records for the current filters')}<p class="muted">The all-status order count includes every order status. Payment is limited to delivered orders in this table.</p></section>
<section><h2>Order status · selected period and state scope</h2>{_html_table(status_rows, ['Order status','Orders'], 'No order-status records for the current filters')}</section>
<section><h2>Delivery performance · selected period</h2><div class="cards"><div class="card"><div class="label">Delivered orders with usable dates</div><div class="value">{delivery['orders_with_dates']:,}</div></div><div class="card"><div class="label">Average delivery time</div><div class="value">{html.escape(delivery_days)}</div></div><div class="card"><div class="label">On-time delivery rate</div><div class="value">{html.escape(on_time)}</div></div></div><p class="muted">Delivery extract is monthly and does not include state or category dimensions; only the period filter applies.</p></section>
<section><h2>Top product categories · selected period and category scope</h2>{_html_table(category_rows, ['Category','Orders','Product + freight value'], 'No category records for these filters')}<p class="muted">The state filter does not apply to this table because the category extract is not split by customer state. Values are not profit or accounting revenue.</p></section>
<section><h2>State performance · selected period and state scope</h2>{_html_table(state_rows, ['State','Delivered orders','Recorded payment value'], 'No state records for these filters')}<p class="muted">The category filter does not apply to this table because the state extract is not split by product category. State-level distinct shopper counts may overlap across states.</p></section>
<section><h2>RFM segments · full-history context</h2>{_html_table(rfm_rows, ['Segment','Customers','Total recorded payment value'], 'No RFM segment records')}<p class="muted">RFM is a full-history, rule-based segmentation and is not recalculated for the selected date, state or category filters.</p></section>
<section><h2>Data quality watchlist · full snapshot</h2>{_html_table(dq_rows, ['Check','Flagged rows','Handling decision'], 'No data-quality checks available')}<p class="muted">Flagged source records are retained. The approximate Brazil bounding-box check is not an official national boundary.</p></section>
<footer>Prepared from the Olist Brazilian E-Commerce dataset · E-commerce IQ<br>Historical transactions: 2016–2018 · Recorded payment value is not profit.</footer>
</main></body></html>"""
    return html_doc.encode("utf-8")


def build_pdf_report(data: dict[str, pd.DataFrame]) -> bytes:
    c = _context(data)
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=17 * mm,
        title="E-commerce IQ | Filtered Executive Performance Brief",
        author="E-commerce IQ",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="HeroTitleX", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=22, leading=26, textColor=NAVY, alignment=TA_LEFT, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="KickerX", parent=styles["Normal"], fontSize=8, leading=11,
        textColor=TEAL, tracking=1.4, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="SectionX", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, leading=15, textColor=NAVY, spaceBefore=10, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="BodyX", parent=styles["BodyText"], fontSize=8.5, leading=12,
        textColor=INK, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="MutedX", parent=styles["BodyText"], fontSize=7, leading=9,
        textColor=MUTED, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="CellX", parent=styles["BodyText"], fontSize=7, leading=9,
        textColor=INK,
    ))
    styles.add(ParagraphStyle(
        name="HeaderCellX", parent=styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=7, leading=9, textColor=colors.white,
    ))
    styles.add(ParagraphStyle(
        name="MetricLabelX", parent=styles["Normal"], fontSize=6.5, leading=8,
        textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        name="MetricValueX", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=14, leading=17, textColor=NAVY,
    ))

    snapshot_label = c["snapshot"]["ist"].strftime("%d %b %Y, %I:%M %p IST") if c["snapshot"]["available"] else "Not recorded"
    states_label = ", ".join(c["states"]) if c["states"] else "All states"
    categories_label = ", ".join(c["categories"]) if c["categories"] else "All categories"
    delivery = c["delivery"]
    delivery_days = f"{delivery['average_delivery_days']:.1f} days" if delivery["average_delivery_days"] is not None else "Not available"
    on_time = f"{delivery['on_time_delivery_rate']:.1f}%" if delivery["on_time_delivery_rate"] is not None else "Not available"

    story = [
        Paragraph("E-COMMERCE IQ  /  INTELLIGENCE STUDIO", styles["KickerX"]),
        Paragraph("Executive Performance Brief", styles["HeroTitleX"]),
        Paragraph(
            f"Filtered operating analysis with full-history customer context.<br/>"
            f"Generated {c['generated_at']}  |  Data snapshot {snapshot_label}",
            styles["MutedX"],
        ),
        Spacer(1, 3 * mm),
        Paragraph("Applied dashboard filters", styles["SectionX"]),
        Paragraph(
            f"<b>Period:</b> {c['period']}<br/>"
            f"<b>States:</b> {states_label}<br/>"
            f"<b>Categories:</b> {categories_label}",
            styles["BodyX"],
        ),
        Paragraph(
            "Period and state filters apply to monthly operating, order-status and state results. "
            "Category filters apply to category analysis. Delivery results are period-filtered. "
            "RFM, cohort retention and data-quality checks remain full-snapshot context because "
            "their extracts do not include every selected filter dimension.",
            styles["MutedX"],
        ),
    ]

    metric_data = [
        [Paragraph("DELIVERED SHOPPERS · ALL HISTORY", styles["MetricLabelX"]),
         Paragraph("REPEAT RATE · ALL HISTORY", styles["MetricLabelX"]),
         Paragraph("DELIVERED ORDERS · FILTERED", styles["MetricLabelX"]),
         Paragraph("DELIVERED PAYMENT · FILTERED", styles["MetricLabelX"])],
        [Paragraph(f"{c['delivered_customers']:,}", styles["MetricValueX"]),
         Paragraph(f"{c['repeat_rate']:.2f}%", styles["MetricValueX"]),
         Paragraph(f"{c['filtered_delivered_orders']:,}", styles["MetricValueX"]),
         Paragraph(f"R$ {c['filtered_delivered_payment']:,.0f}", styles["MetricValueX"])],
    ]
    metric_table = Table(metric_data, colWidths=[43.5 * mm] * 4, rowHeights=[9 * mm, 13 * mm])
    metric_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), .5, LINE),
        ("INNERGRID", (0, 0), (-1, -1), .4, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story += [metric_table, Spacer(1, 3 * mm)]

    story.append(Paragraph("Executive readout", styles["SectionX"]))
    one_time_pct = c["one_time_customers"] / max(c["delivered_customers"], 1) * 100
    story.append(Paragraph(
        f"<b>Repeat purchasing:</b> {c['one_time_customers']:,} of {c['delivered_customers']:,} "
        f"delivered shoppers ({one_time_pct:.1f}%) made one delivered purchase in the full observed history.",
        styles["BodyX"],
    ))
    story.append(Paragraph(
        f"<b>Month 1 cohort retention:</b> {c['month_one_retained']:,} of {c['month_one_eligible']:,} "
        f"eligible customers returned in the next calendar month ({c['month_one_rate']:.2f}%). "
        "This is a full-history weighted measure, not limited to the selected filter range.",
        styles["BodyX"],
    ))

    def add_table_section(title: str, headers: list[str], rows: list[list], widths: list[float], empty: str = "No records for these filters.") -> None:
        story.append(Paragraph(title, styles["SectionX"]))
        body_rows = rows if rows else [[empty] + [""] * (len(headers) - 1)]
        table_data = [[Paragraph(html.escape(str(item)), styles["HeaderCellX"]) for item in headers]]
        table_data += [[Paragraph(html.escape(str(item)), styles["CellX"]) for item in row] for row in body_rows]
        table = Table(table_data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F8FA")]),
            ("GRID", (0, 0), (-1, -1), .3, LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(table)

    monthly_rows = []
    for row in c["monthly"].itertuples():
        monthly_rows.append([
            pd.Timestamp(row.order_month).strftime("%b %Y"),
            f"{int(getattr(row, 'total_orders', 0)):,}",
            f"{int(row.delivered_orders):,}",
            _fmt_currency(getattr(row, "delivered_recorded_payment_value", 0)),
        ])
    add_table_section(
        "Monthly operating trend · selected period and state scope",
        ["Month", "All-status orders", "Delivered orders", "Delivered payment"],
        monthly_rows, [31 * mm, 35 * mm, 37 * mm, 49 * mm],
    )

    status_rows = [[str(row.order_status), f"{int(row.total_orders):,}"] for row in c["statuses"].itertuples()]
    add_table_section("Order status · selected period and state scope", ["Order status", "Orders"], status_rows, [100 * mm, 52 * mm])

    story.append(Paragraph("Delivery performance · selected period", styles["SectionX"]))
    story.append(Paragraph(
        f"Delivered orders with usable dates: <b>{delivery['orders_with_dates']:,}</b>  |  "
        f"Average delivery time: <b>{delivery_days}</b>  |  "
        f"On-time delivery rate: <b>{on_time}</b>",
        styles["BodyX"],
    ))
    story.append(Paragraph("Delivery extract is monthly and does not include state or category dimensions; only the period filter applies.", styles["MutedX"]))

    category_rows = [[str(row.product_category)[:52], f"{int(row.total_orders):,}", _fmt_currency(row.item_plus_freight_value)] for row in c["top_categories"].itertuples()]
    add_table_section("Top product categories · selected period and category scope", ["Category", "Orders", "Product + freight"], category_rows, [82 * mm, 30 * mm, 40 * mm])
    story.append(Paragraph("The state filter does not apply to category results because the available category extract is not split by customer state. Values are not profit or accounting revenue.", styles["MutedX"]))

    state_rows = [[str(row.customer_state), f"{int(row.delivered_orders):,}", _fmt_currency(row.recorded_payment_value)] for row in c["top_states"].itertuples()]
    add_table_section("State performance · selected period and state scope", ["State", "Delivered orders", "Recorded payment"], state_rows, [35 * mm, 45 * mm, 72 * mm])
    story.append(Paragraph("The category filter does not apply to state results because the state extract is not split by product category. State-level shopper counts can overlap.", styles["MutedX"]))

    story.append(PageBreak())
    story.append(Paragraph("Full-history context & data quality", styles["SectionX"]))
    rfm_rows = [[str(row.customer_segment), f"{int(row.customer_count):,}", _fmt_currency(row.total_monetary)] for row in c["rfm"].itertuples()]
    add_table_section("RFM segment summary · full history", ["Segment", "Customers", "Total monetary"], rfm_rows, [82 * mm, 30 * mm, 40 * mm])
    story.append(Paragraph("RFM segments are not recalculated for the selected date, state or category filters. They describe historical purchase behavior and are not predictions of future intent.", styles["MutedX"]))

    cohort = c["cohort"]
    cohort_summary = cohort.groupby("cohort_index", as_index=False).agg(
        eligible_customers=("cohort_size", "sum"),
        retained_customers=("retained_customers", "sum"),
    )
    cohort_summary["retention"] = cohort_summary.apply(
        lambda row: row.retained_customers / row.eligible_customers * 100 if row.eligible_customers else 0,
        axis=1,
    )
    cohort_rows = [[
        f"Month {int(row.cohort_index)}", f"{int(row.eligible_customers):,}",
        f"{int(row.retained_customers):,}", f"{row.retention:.2f}%",
    ] for row in cohort_summary.head(12).itertuples()]
    add_table_section("Weighted cohort retention · full history", ["Cohort age", "Eligible", "Retained", "Retention"], cohort_rows, [42 * mm, 38 * mm, 36 * mm, 36 * mm])
    story.append(Paragraph("Cohort results remain full-history context because the cohort extract does not contain state or category dimensions. Retention measures monthly delivered-purchase activity, not uninterrupted monthly loyalty.", styles["MutedX"]))

    dq_rows = [[str(row.issue), f"{int(row.flagged_rows):,}", str(row.severity)] for row in c["data_quality"].itertuples()]
    add_table_section("Data quality watchlist · full snapshot", ["Check", "Flagged", "Severity"], dq_rows, [92 * mm, 28 * mm, 32 * mm])
    story.append(Paragraph("Flagged source records were retained rather than silently corrected or deleted. The geographic boundary check uses an approximate bounding box, not an official national border.", styles["MutedX"]))

    if c["public_url"]:
        story.append(Paragraph("Live dashboard: " + html.escape(c["public_url"]), styles["MutedX"]))

    def draw_page(canvas, doc):
        canvas.saveState()
        width, _ = A4
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(.5)
        canvas.line(15 * mm, 13 * mm, width - 15 * mm, 13 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(15 * mm, 8 * mm, "E-commerce IQ  |  Olist Brazilian E-Commerce dataset")
        canvas.drawRightString(width - 15 * mm, 8 * mm, f"{doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    return buffer.getvalue()


def build_filtered_extract_bundle(data: dict[str, pd.DataFrame]) -> bytes:
    """Create a ZIP of current-filter extracts plus clearly labelled full-history context."""
    filters = selected_filters()
    monthly = monthly_scope(data)
    categories = category_scope(data)
    states = state_scope(data)
    statuses = status_scope(data)
    delivery = filter_by_period(data["delivery_performance"])

    full_history = {
        "rfm_segments_full_history.csv": data["rfm_segments"],
        "cohort_retention_full_history.csv": data["cohort_retention"],
        "payment_methods_full_history.csv": data["payment_methods"],
        "data_quality_full_snapshot.csv": data["data_quality"],
        "customer_type_metrics_full_history.csv": data["customer_type_metrics"],
        "customer_frequency_full_history.csv": data["customer_frequency"],
    }
    filtered = {
        "monthly_performance_filtered.csv": monthly,
        "order_status_filtered.csv": statuses,
        "category_performance_filtered.csv": categories,
        "state_performance_filtered.csv": states,
        "delivery_performance_period_filtered.csv": delivery,
    }

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "filters": {
            "date_start": str(filters.get("date_start")) if filters.get("date_start") else None,
            "date_end": str(filters.get("date_end")) if filters.get("date_end") else None,
            "states": filters.get("states") or [],
            "categories": filters.get("categories") or [],
        },
        "filtered_files": {
            "monthly_performance_filtered.csv": "Date and state filters applied.",
            "order_status_filtered.csv": "Date and state filters applied.",
            "category_performance_filtered.csv": "Date and category filters applied; state filter is not available in this aggregate.",
            "state_performance_filtered.csv": "Date and state filters applied; category filter is not available in this aggregate.",
            "delivery_performance_period_filtered.csv": "Date filter applied; state and category dimensions are not available in this aggregate.",
        },
        "full_history_files": {
            filename: "Full-history context; selected filters cannot be applied with the available aggregate dimensions."
            for filename in full_history
        },
        "metric_note": "Recorded payment value is not profit or accounting revenue.",
    }

    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for filename, frame in {**filtered, **full_history}.items():
            archive.writestr(filename, frame.to_csv(index=False))
        archive.writestr("filter_context.json", json.dumps(manifest, indent=2))
    return buffer.getvalue()
