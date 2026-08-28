"""Validated self-report intake for PHQ-9 and GAD-7 components."""

from __future__ import annotations

from typing import Any

import streamlit as st


PHQ9_ITEMS = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself, or that you are a failure",
    "Trouble concentrating on things",
    "Moving or speaking slowly, or being unusually restless",
    "Thoughts that you would be better off dead or hurting yourself",
]
GAD7_ITEMS = [
    "Feeling nervous, anxious, or on edge",
    "Not being able to stop or control worrying",
    "Worrying too much about different things",
    "Trouble relaxing",
    "Being so restless that it is hard to sit still",
    "Becoming easily annoyed or irritable",
    "Feeling afraid, as if something awful might happen",
]
SCALE_LABELS = "0.0 Not at all · 1.0 Several days · 2.0 More than half the days · 3.0 Nearly every day"


class ClinicalIntakeModule:
    """Collect and normalize validated self-report components."""

    def __init__(self) -> None:
        self.phq_max = len(PHQ9_ITEMS) * 3
        self.gad_max = len(GAD7_ITEMS) * 3

    def render(self) -> dict[str, Any] | None:
        """Render the intake form and return a payload after explicit submission."""
        st.subheader("How are things feeling lately?")
        st.caption("For each line, move the slider between the four anchors. The in-between values let you describe intensity more precisely.")
        with st.form("clinical_intake_form", clear_on_submit=False):
            phq_values: list[float] = []
            st.markdown("**Mood, energy, and daily life**")
            st.caption(SCALE_LABELS)
            for index, question in enumerate(PHQ9_ITEMS):
                phq_values.append(float(st.slider(question, min_value=0.0, max_value=3.0, value=0.0, step=0.1, key=f"phq_{index}", format="%.1f")))
            st.markdown("**Worry and ease**")
            gad_values: list[float] = []
            st.caption(SCALE_LABELS)
            for index, question in enumerate(GAD7_ITEMS):
                key = f"gad_{index}"
                gad_values.append(float(st.slider(question, min_value=0.0, max_value=3.0, value=0.0, step=0.1, key=key, format="%.1f")))
            journal = st.text_area(
                "Anything else you’d like to put into words?",
                placeholder="Share only what you are comfortable sharing.",
                height=130,
            )
            submitted = st.form_submit_button("Continue", type="primary", use_container_width=True)
        if not submitted:
            return None
        phq_score = round(sum(phq_values), 1)
        gad_score = round(sum(gad_values), 1)
        total = phq_score + gad_score
        maximum = self.phq_max + self.gad_max
        all_values = phq_values + gad_values
        moderate_or_higher = sum(value >= 1.5 for value in all_values)
        return {
            "phq9_responses": phq_values,
            "gad7_responses": gad_values,
            "phq9_total": phq_score,
            "gad7_total": gad_score,
            "average_intensity": round(total / len(all_values), 2),
            "moderate_or_higher_share": round(moderate_or_higher / len(all_values) * 100, 1),
            "depression_anxiety_balance": round((phq_score / self.phq_max) - (gad_score / self.gad_max), 2),
            "clinical_score": round(total / maximum * 100, 1),
            "journal": journal.strip(),
        }
