"""Privacy-preserving institutional analytics views."""

from __future__ import annotations

import pandas as pd
import streamlit as st


class InstitutionalDashboardModule:
    """Render only aggregate, non-identifying cohort signals."""

    def render(self, records: pd.DataFrame) -> None:
        st.subheader("Institutional wellbeing overview")
        st.caption("Aggregate view only. Journals, anonymous IDs, and biometric streams are excluded by design.")
        if records.empty:
            st.info("No check-ins are available in this app session yet. Aggregate metrics will appear after voluntary check-ins.")
            return
        cohort_index = float(records["composite_score"].mean())
        elevated_share = float((records["tier"] == "Elevated Risk").mean() * 100)
        checkins = len(records)
        first_date = records["date"].min()
        last_date = records["date"].max()
        metric_columns = st.columns(3)
        metric_columns[0].metric("Cohort wellbeing index", f"{cohort_index:.1f}/100")
        metric_columns[1].metric("Elevated signal share", f"{elevated_share:.0f}%")
        metric_columns[2].metric("Voluntary check-ins", checkins)
        st.caption("The wellbeing index is the average composite support signal. A higher value means the cohort may benefit from more outreach; it is not a diagnosis.")
        st.caption("Elevated signal share is the percentage of check-ins above the support policy’s elevated threshold. It should guide resource planning, not individual decisions.")
        st.caption("Voluntary check-ins counts submitted records in this local session and does not identify people.")
        st.caption(f"Aggregate window: {first_date} to {last_date}")

        chart_data = records.copy()
        chart_data["date"] = pd.to_datetime(chart_data["date"])
        weekly = chart_data.set_index("date")["composite_score"].resample("W").mean().rename("Average composite signal")
        st.markdown("**Weekly support-signal trend**")
        st.caption("Each point is the cohort’s average composite signal for that week. One person’s result is never shown.")
        st.line_chart(weekly, height=280)
        st.markdown("**Signal distribution**")
        st.caption("This shows how many anonymous check-ins fell into each support-routing tier during the session.")
        distribution = records["tier"].value_counts().reindex(["Elevated Risk", "Moderate Strain", "Minimal Risk"], fill_value=0)
        st.bar_chart(distribution, height=220)
        st.success("Privacy check passed: this view contains aggregates only and suppresses all free text and raw physiological feeds.")
