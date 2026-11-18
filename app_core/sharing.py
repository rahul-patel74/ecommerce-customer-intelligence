from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)


def get_public_app_url() -> str | None:
    """Return a validated public app URL from Streamlit secrets or local .env."""
    configured = None

    try:
        configured = st.secrets.get("STREAMLIT_APP_URL")
    except Exception:
        configured = None

    if not configured:
        configured = os.getenv("STREAMLIT_APP_URL")

    if not configured:
        return None

    url = str(configured).strip()
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        return None
    if parsed.username or parsed.password:
        return None

    return url.rstrip("/")


def snapshot_metadata(manifest: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize manifest time into UTC/IST and calculate the snapshot age."""
    raw_timestamp = (manifest or {}).get("generated_at_utc")
    if not raw_timestamp:
        return {
            "available": False,
            "raw": None,
            "utc": None,
            "ist": None,
            "age_hours": None,
            "age_label": "Not recorded",
        }

    parsed = pd.to_datetime(raw_timestamp, utc=True, errors="coerce")
    if pd.isna(parsed):
        return {
            "available": False,
            "raw": str(raw_timestamp),
            "utc": None,
            "ist": None,
            "age_hours": None,
            "age_label": "Timestamp could not be parsed",
        }

    now_utc = pd.Timestamp(datetime.now(timezone.utc))
    age_hours = max(0.0, (now_utc - parsed).total_seconds() / 3600)
    if age_hours < 1:
        age_label = f"{int(age_hours * 60)} minutes ago"
    elif age_hours < 48:
        age_label = f"{age_hours:.1f} hours ago"
    else:
        age_label = f"{age_hours / 24:.1f} days ago"

    return {
        "available": True,
        "raw": str(raw_timestamp),
        "utc": parsed,
        "ist": parsed.tz_convert("Asia/Kolkata"),
        "age_hours": age_hours,
        "age_label": age_label,
    }
