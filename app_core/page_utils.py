from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from app_core.data import filter_context_label, load_dashboard_data, load_manifest
from app_core.theme import COLORS, hero


def page_data():
    return load_dashboard_data()


def page_footer():
    manifest = load_manifest()
    timestamp = manifest.get("generated_at_utc")
    label = "snapshot time unavailable"
    if timestamp:
        try:
            label = pd.Timestamp(timestamp).strftime("%d %b %Y %H:%M UTC")
        except (TypeError, ValueError):
            label = str(timestamp)
    st.markdown(
        f"<div class='page-foot'>Olist Brazilian E-Commerce · Snapshot: {label} · "
        "Recorded payment value is not profit.</div>",
        unsafe_allow_html=True,
    )


def page_hero(kicker: str, title: str, copy: str, data: dict | None = None):
    manifest = load_manifest()
    period = filter_context_label()
    snapshot = manifest.get("generated_at_utc", "Snapshot date unavailable")
    try:
        snapshot = pd.Timestamp(snapshot).strftime("%d %b %Y")
    except (TypeError, ValueError):
        pass
    hero(kicker, title, copy, [period, f"Snapshot · {snapshot}", "Historical data · 2016–2018"])


def panel_title(title: str, subtitle: str | None = None):
    st.markdown(f"<div style='font:750 15px Manrope,sans-serif;color:{COLORS['text']};margin:0 0 3px'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)


def brl(value: float, compact: bool = False) -> str:
    value = float(value or 0)
    if compact and abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:.2f}M"
    if compact and abs(value) >= 1_000:
        return f"R$ {value / 1_000:.1f}K"
    return f"R$ {value:,.2f}"
