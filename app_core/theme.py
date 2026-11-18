from __future__ import annotations

import html
import math
from typing import Iterable

import streamlit as st

PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
    "toImageButtonOptions": {"format": "png", "scale": 2},
}

COLORS = {
    "bg": "#07111F",
    "bg_soft": "#0B1728",
    "panel": "#101E31",
    "panel_2": "#14243A",
    "border": "rgba(151, 176, 204, 0.15)",
    "text": "#F2F6FC",
    "muted": "#95A7BD",
    "teal": "#46D8C1",
    "blue": "#6EA8FE",
    "purple": "#B39AFB",
    "amber": "#F6C56F",
    "coral": "#FF8290",
    "green": "#79D7A5",
}

PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, Segoe UI, sans-serif", "color": COLORS["text"], "size": 12},
        "title": {"font": {"size": 15, "color": COLORS["text"]}},
        "xaxis": {
            "gridcolor": "rgba(151,176,204,0.10)",
            "linecolor": "rgba(151,176,204,0.18)",
            "tickfont": {"color": COLORS["muted"]},
            "titlefont": {"color": COLORS["muted"]},
            "zerolinecolor": "rgba(151,176,204,0.12)",
        },
        "yaxis": {
            "gridcolor": "rgba(151,176,204,0.10)",
            "linecolor": "rgba(151,176,204,0.18)",
            "tickfont": {"color": COLORS["muted"]},
            "titlefont": {"color": COLORS["muted"]},
            "zerolinecolor": "rgba(151,176,204,0.12)",
        },
        "legend": {"font": {"color": COLORS["muted"]}, "bgcolor": "rgba(0,0,0,0)"},
        "hoverlabel": {
            "bgcolor": "#14243A", "bordercolor": "rgba(70,216,193,0.50)",
            "font": {"color": "#F2F6FC", "size": 12},
        },
        "colorway": [COLORS["teal"], COLORS["blue"], COLORS["purple"], COLORS["amber"], COLORS["coral"], COLORS["green"]],
        "margin": {"l": 12, "r": 12, "t": 28, "b": 12},
    }
}


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
        :root {
            --app-bg: #07111F;
            --app-panel: #101E31;
            --app-panel-2: #14243A;
            --app-border: rgba(151,176,204,.15);
            --app-text: #F2F6FC;
            --app-muted: #95A7BD;
            --app-teal: #46D8C1;
            --app-blue: #6EA8FE;
            --app-purple: #B39AFB;
            --app-amber: #F6C56F;
            --app-coral: #FF8290;
        }
        html, body, [data-testid="stAppViewContainer"] {
            background: radial-gradient(900px 460px at 83% -5%, rgba(55,118,160,.17), transparent 62%),
                        radial-gradient(760px 420px at 6% 18%, rgba(70,216,193,.10), transparent 64%),
                        #07111F !important;
            color: var(--app-text) !important;
            font-family: 'DM Sans', 'Segoe UI', sans-serif !important;
        }
        [data-testid="stHeader"] { background: rgba(7,17,31,.78); backdrop-filter: blur(14px); }
        [data-testid="stToolbar"] { right: 1rem; }
        [data-testid="stMainBlockContainer"] { max-width: 1540px; padding-top: 1.5rem; padding-bottom: 3rem; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0B1829 0%, #0A1423 100%) !important;
            border-right: 1px solid var(--app-border);
        }
        [data-testid="stSidebar"] > div:first-child { padding-top: 1.1rem; }
        [data-testid="stSidebar"] * { color: var(--app-text); }
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stCaption { color: var(--app-muted) !important; }
        [data-testid="stSidebarNav"] {
            padding: .45rem .55rem .9rem;
            border-bottom: 1px solid var(--app-border);
            margin-bottom: .85rem;
        }
        [data-testid="stSidebarNav"] a {
            border: 1px solid transparent !important;
            border-radius: 11px !important;
            margin: 3px 0 !important;
            color: #AFC1D5 !important;
            background: transparent !important;
            transition: background .18s ease, border-color .18s ease, transform .18s ease;
        }
        [data-testid="stSidebarNav"] a:hover {
            background: rgba(70,216,193,.08) !important;
            border-color: rgba(70,216,193,.22) !important;
            transform: translateX(2px);
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            color: #F4FFFC !important;
            background: linear-gradient(105deg, rgba(70,216,193,.17), rgba(110,168,254,.10)) !important;
            border-color: rgba(70,216,193,.32) !important;
            box-shadow: inset 3px 0 0 #46D8C1;
        }
        h1, h2, h3, h4 { font-family: 'Manrope', 'DM Sans', sans-serif !important; letter-spacing: -.035em; color: var(--app-text) !important; }
        h1 { font-weight: 800 !important; }
        h2, h3 { font-weight: 700 !important; }
        p, li, label, [data-testid="stMarkdownContainer"] { color: var(--app-text); }
        .muted, .eyebrow, [data-testid="stCaptionContainer"] { color: var(--app-muted) !important; }
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            background: linear-gradient(145deg, rgba(20,36,58,.94), rgba(13,27,45,.92));
            border: 1px solid var(--app-border) !important;
            border-radius: 18px !important;
            box-shadow: 0 10px 30px rgba(0,0,0,.12);
        }
        [data-testid="stMetric"] {
            background: transparent;
        }
        [data-testid="stMetricLabel"] { color: var(--app-muted) !important; font-size: .82rem !important; }
        [data-testid="stMetricValue"] { color: var(--app-text) !important; font-family: 'Manrope', sans-serif; }
        [data-testid="stMetricDelta"] { font-size: .76rem; }
        [data-testid="stButton"] button, [data-testid="stDownloadButton"] button, [data-testid="stLinkButton"] a, [data-testid="stPageLink"] a {
            border-radius: 11px !important; border: 1px solid rgba(70,216,193,.28) !important;
            background: linear-gradient(135deg, rgba(70,216,193,.16), rgba(110,168,254,.10)) !important;
            color: #EAFBF8 !important; font-weight: 650 !important; transition: all .18s ease;
        }
        [data-testid="stButton"] button:hover, [data-testid="stDownloadButton"] button:hover, [data-testid="stPageLink"] a:hover {
            border-color: rgba(70,216,193,.72) !important; transform: translateY(-1px);
            box-shadow: 0 8px 22px rgba(70,216,193,.12);
        }
        [data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="textarea"] > div {
            background: #0E1B2D !important; border-color: var(--app-border) !important; border-radius: 10px !important;
        }
        [data-testid="stTabs"] button { color: var(--app-muted); }
        [data-testid="stTabs"] button[aria-selected="true"] { color: var(--app-teal); }
        [data-testid="stDataFrame"] { border: 1px solid var(--app-border); border-radius: 12px; overflow: hidden; }
        [data-testid="stAlert"] { border-radius: 13px; }
        hr { border-color: var(--app-border) !important; }
        a { color: var(--app-teal) !important; }
        .brand-lockup { display:flex; align-items:center; gap:11px; padding: 5px 2px 18px; }
        .brand-mark { width:42px; height:42px; flex:0 0 auto; filter: drop-shadow(0 7px 18px rgba(70,216,193,.18)); }
        .brand-name { font:800 17px 'Manrope', sans-serif; letter-spacing:-.04em; color:#F2F6FC; }
        .brand-sub { font-size:10px; color:#89A0B8; letter-spacing:.16em; text-transform:uppercase; margin-top:2px; }
        .hero {
            position:relative; overflow:hidden; border-radius:24px; padding:26px 30px 25px; animation:heroIn .55s ease-out both;
            background: linear-gradient(115deg, rgba(19,49,68,.96), rgba(19,35,61,.98) 58%, rgba(47,43,78,.94));
            border:1px solid rgba(119,182,208,.22); box-shadow:0 18px 52px rgba(0,0,0,.18); margin-bottom:18px;
        }
        .hero:before { content:''; position:absolute; width:310px; height:310px; right:-80px; top:-160px; border-radius:50%; background:radial-gradient(circle, rgba(70,216,193,.22), transparent 68%); }
        .hero:after { content:''; position:absolute; width:250px; height:250px; right:170px; bottom:-205px; border-radius:50%; background:radial-gradient(circle, rgba(179,154,251,.20), transparent 68%); }
        .hero-kicker { color:#8EE9DA; font-size:10px; font-weight:800; letter-spacing:.19em; text-transform:uppercase; margin-bottom:9px; position:relative; z-index:1; }
        .hero-title { color:#F7FBFF; font:800 clamp(25px,3vw,37px) 'Manrope',sans-serif; line-height:1.12; letter-spacing:-.05em; margin:0; position:relative; z-index:1; }
        .hero-copy { color:#B4C6D9; font-size:13px; max-width:780px; margin-top:10px; line-height:1.65; position:relative; z-index:1; }
        .hero-pills { display:flex; flex-wrap:wrap; gap:8px; margin-top:17px; position:relative; z-index:1; }
        .hero-pill { border:1px solid rgba(183,214,232,.2); background:rgba(6,16,30,.24); color:#C9D8E7; font-size:10px; padding:6px 10px; border-radius:99px; }
        .section-head { display:flex; align-items:flex-end; justify-content:space-between; gap:12px; margin:21px 0 11px; }
        .section-title { font:750 17px 'Manrope',sans-serif; letter-spacing:-.025em; color:#F2F6FC; }
        .section-note { color:var(--app-muted); font-size:11px; }
        .metric-card {
            min-height:142px; position:relative; overflow:hidden; padding:16px 17px 13px;
            background:linear-gradient(145deg, rgba(19,36,58,.98), rgba(13,27,45,.98));
            border:1px solid rgba(151,176,204,.15); border-radius:17px;
            box-shadow:0 11px 30px rgba(0,0,0,.15); transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease; animation:cardIn .48s ease-out both;
        }
        .metric-card:hover { transform:translateY(-4px); border-color:var(--accent); box-shadow:0 17px 34px rgba(0,0,0,.24),0 0 22px color-mix(in srgb,var(--accent) 12%,transparent); }
        .metric-card:before { content:''; position:absolute; top:0; left:0; width:100%; height:2px; background:linear-gradient(90deg,var(--accent),transparent 78%); opacity:.95; }
        .metric-top { display:flex; justify-content:space-between; align-items:center; gap:8px; }
        .metric-label { color:#9EB0C5; font-size:11px; font-weight:650; letter-spacing:.04em; }
        .metric-icon { color:var(--accent); background:color-mix(in srgb,var(--accent) 13%,transparent); width:27px;height:27px;border-radius:9px;display:grid;place-items:center;font-size:14px; }
        .metric-value { color:#F5F8FD; font:800 clamp(22px,2.2vw,29px) 'Manrope',sans-serif; letter-spacing:-.045em; margin-top:8px; line-height:1.08; }
        .metric-foot { color:#91A5BA; font-size:10px; margin-top:6px; }
        .metric-bottom { display:flex; justify-content:space-between; align-items:flex-end; gap:8px; margin-top:2px; }
        .metric-trend { color:#78D9B1; font-size:10px; font-weight:700; white-space:nowrap; }
        .metric-trend.down { color:#FF9B9F; }
        .metric-spark { width:94px; height:33px; overflow:visible; opacity:.95; }
        .insight-card { padding:15px 16px; border:1px solid var(--app-border); border-radius:15px; background:linear-gradient(140deg,rgba(19,37,59,.88),rgba(13,26,43,.86)); min-height:112px; }
        .insight-label { color:#91A8BD; font-size:10px; font-weight:800; letter-spacing:.11em; text-transform:uppercase; }
        .insight-title { color:#F0F6FC; font:700 14px 'Manrope',sans-serif; margin-top:7px; }
        .insight-copy { color:#9FB2C8; font-size:11px; line-height:1.55; margin-top:5px; }
        .status-dot { display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:6px;background:#70D9AA;box-shadow:0 0 10px rgba(112,217,170,.5); }
        .small-badge { display:inline-block; padding:5px 9px; border-radius:99px; background:rgba(70,216,193,.1); color:#86E6D8; border:1px solid rgba(70,216,193,.18); font-size:10px; font-weight:700; }
        .callout { padding:13px 15px; border-radius:13px; border:1px solid rgba(246,197,111,.22); background:rgba(246,197,111,.07); color:#E8D6B2; font-size:12px; line-height:1.55; }
        .good-callout { border-color:rgba(70,216,193,.20);background:rgba(70,216,193,.06);color:#B6EAE1; }
        .page-foot { color:#7389A1; font-size:10px; text-align:center; padding:20px 0 4px; }
        [data-testid="stPlotlyChart"] { border-radius:13px; overflow:hidden; }
        @keyframes heroIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
        @keyframes cardIn { from { opacity:0; transform:translateY(7px); } to { opacity:1; transform:translateY(0); } }
        @media (prefers-reduced-motion: reduce) { .hero, .metric-card { animation:none !important; transition:none !important; } }
        @media (max-width: 800px) {
            [data-testid="stMainBlockContainer"] { padding-left:1rem; padding-right:1rem; }
            .hero { padding:22px 20px; }
            .metric-card { min-height:130px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def brand_lockup(compact: bool = False) -> None:
    label = "E-commerce IQ" if compact else "E-commerce IQ"
    sub = "INTELLIGENCE STUDIO" if compact else "CUSTOMER INTELLIGENCE & RETENTION"
    st.markdown(
        f"""
        <div class="brand-lockup">
          <svg class="brand-mark" viewBox="0 0 64 64" role="img" aria-label="E-commerce IQ mark">
            <defs>
              <linearGradient id="brandGradient" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stop-color="#46D8C1"/>
                <stop offset="1" stop-color="#6EA8FE"/>
              </linearGradient>
            </defs>
            <rect x="3" y="3" width="58" height="58" rx="18" fill="#142A40" stroke="#5DDCCB" stroke-opacity=".35"/>
            <path d="M16 43V34h8v9M29 43V25h8v18M42 43V18h7v25" fill="url(#brandGradient)" opacity=".96"/>
            <path d="M15 26l11-8 9 4 15-10" fill="none" stroke="#B7A6FF" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="50" cy="12" r="3" fill="#F6C56F"/>
          </svg>
          <div>
            <div class="brand-name">{label}</div>
            <div class="brand-sub">{sub}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(kicker: str, title: str, copy: str, pills: Iterable[str] = ()) -> None:
    safe_kicker = html.escape(str(kicker))
    safe_title = html.escape(str(title))
    safe_copy = html.escape(str(copy))
    pills_html = "".join(f'<span class="hero-pill">{html.escape(str(item))}</span>' for item in pills)
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-kicker">{safe_kicker}</div>
          <div class="hero-title">{safe_title}</div>
          <div class="hero-copy">{safe_copy}</div>
          <div class="hero-pills">{pills_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_heading(title: str, note: str | None = None) -> None:
    note_html = f'<div class="section-note">{note}</div>' if note else ""
    st.markdown(
        f'<div class="section-head"><div class="section-title">{title}</div>{note_html}</div>',
        unsafe_allow_html=True,
    )


def _sparkline(values: list[float], color: str) -> str:
    cleaned = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if len(cleaned) < 2:
        cleaned = cleaned or [0.0, 0.0]
    low, high = min(cleaned), max(cleaned)
    spread = high - low or 1.0
    points = []
    for index, value in enumerate(cleaned):
        x = 2 + index * (90 / max(1, len(cleaned) - 1))
        y = 27 - ((value - low) / spread) * 22
        points.append(f"{x:.1f},{y:.1f}")
    point_string = " ".join(points)
    return (
        f'<svg class="metric-spark" viewBox="0 0 94 34" aria-hidden="true">'
        f'<polyline points="{point_string}" fill="none" stroke="{color}" '
        f'stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{points[-1].split(",")[0]}" cy="{points[-1].split(",")[1]}" r="2.7" fill="{color}"/>'
        f'</svg>'
    )


def metric_card(label: str, value: str, foot: str, icon: str, accent: str, spark: list[float] | None = None, trend: str | None = None, trend_down: bool = False) -> None:
    safe_label = html.escape(str(label))
    safe_value = html.escape(str(value))
    safe_foot = html.escape(str(foot))
    safe_icon = html.escape(str(icon))
    safe_accent = accent if accent.startswith("#") else COLORS["teal"]
    spark_html = _sparkline(spark or [], safe_accent) if spark is not None else ""
    trend_html = ""
    if trend:
        trend_html = f'<span class="metric-trend {"down" if trend_down else ""}">{html.escape(str(trend))}</span>'
    st.markdown(
        f"""
        <div class="metric-card" style="--accent:{safe_accent}">
          <div class="metric-top">
            <div class="metric-label">{safe_label}</div>
            <div class="metric-icon">{safe_icon}</div>
          </div>
          <div class="metric-value">{safe_value}</div>
          <div class="metric-foot">{safe_foot}</div>
          <div class="metric-bottom">{trend_html}{spark_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(label: str, title: str, copy: str, accent: str = "#46D8C1") -> None:
    safe_label = html.escape(str(label))
    safe_title = html.escape(str(title))
    safe_copy = html.escape(str(copy))
    safe_accent = accent if accent.startswith("#") else COLORS["teal"]
    st.markdown(
        f"""
        <div class="insight-card" style="border-top:2px solid {safe_accent}">
          <div class="insight-label">{safe_label}</div>
          <div class="insight-title">{safe_title}</div>
          <div class="insight-copy">{safe_copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_style(fig, height: int = 340):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Segoe UI, sans-serif", "color": COLORS["text"], "size": 11},
        height=height,
        margin={"l": 12, "r": 12, "t": 28, "b": 12},
        hoverlabel={"bgcolor": "#172A40", "bordercolor": "#46D8C1", "font": {"color": "#F2F6FC"}},
        legend={"bgcolor": "rgba(0,0,0,0)", "font": {"color": COLORS["muted"]}},
    )
    fig.update_xaxes(gridcolor="rgba(151,176,204,.09)", zerolinecolor="rgba(151,176,204,.10)")
    fig.update_yaxes(gridcolor="rgba(151,176,204,.09)", zerolinecolor="rgba(151,176,204,.10)")
    return fig


def format_compact(value: float, prefix: str = "") -> str:
    value = float(value or 0)
    if abs(value) >= 1_000_000:
        return f"{prefix}{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{prefix}{value / 1_000:.1f}K"
    return f"{prefix}{value:,.0f}"


def format_brl(value: float, compact: bool = False) -> str:
    value = float(value or 0)
    if compact:
        return format_compact(value, "R$ ")
    return f"R$ {value:,.2f}"
