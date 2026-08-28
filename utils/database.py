"""Anonymous, session-backed longitudinal storage.

This intentionally avoids an external database so the demo can run locally. Records
contain derived signals only; free-text journals and camera frames are never stored.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd
import streamlit as st


_RECORDS_KEY = "mh_early_warning_records"


def _initial_records() -> list[dict[str, Any]]:
    return []


def get_anonymous_id() -> str:
    """Return a non-identifying ID for this browser session."""
    if "mh_anonymous_id" not in st.session_state:
        import secrets

        st.session_state.mh_anonymous_id = f"session-{secrets.token_hex(4)}"
    return str(st.session_state.mh_anonymous_id)


def get_records() -> list[dict[str, Any]]:
    """Read records from Streamlit session state."""
    if _RECORDS_KEY not in st.session_state:
        st.session_state[_RECORDS_KEY] = _initial_records()
    return list(st.session_state[_RECORDS_KEY])


def save_checkin(
    *,
    composite_score: float,
    tier: str,
    clinical_score: float,
    physio_score: float,
    linguistic_score: float,
) -> dict[str, Any]:
    """Persist derived check-in signals without raw journal or biometric data."""
    record = {
        "anonymous_id": get_anonymous_id(),
        "date": date.today().isoformat(),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "composite_score": round(float(composite_score), 1),
        "tier": tier,
        "clinical_score": round(float(clinical_score), 1),
        "physio_score": round(float(physio_score), 1),
        "linguistic_score": round(float(linguistic_score), 1),
    }
    records = get_records()
    records.append(record)
    st.session_state[_RECORDS_KEY] = records[-100:]
    return record


def records_as_dataframe() -> pd.DataFrame:
    """Return an analytics-safe dataframe with no identifying or text fields."""
    records = get_records()
    columns = [
        "date",
        "timestamp",
        "composite_score",
        "tier",
        "clinical_score",
        "physio_score",
        "linguistic_score",
    ]
    return pd.DataFrame(records, columns=columns)
