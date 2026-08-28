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
OPTIONS = [
    "Not at all",
    "Several days",
    "More than half the days",
    "Nearly every day",
]


class ClinicalIntakeModule:
    """Collect and normalize validated self-report components."""

    def __init__(self) -> None:
        self.phq_max = len(PHQ9_ITEMS) * 3
        self.gad_max = len(GAD7_ITEMS) * 3

    def render(self) -> dict[str, Any] | None:
        """Render the intake form and return a payload after explicit submission."""
        st.subheader("How are things feeling lately?")
        st.caption("For each line, choose the answer that feels closest to your experience over the last two weeks.")
        with st.form("clinical_intake_form", clear_on_submit=False):
            phq_values: list[int] = []
            st.markdown("**Mood, energy, and daily life**")
            for index, question in enumerate(PHQ9_ITEMS):
                selected = st.select_slider(question, options=OPTIONS, value=OPTIONS[0], key=f"phq_{index}")
                phq_values.append(OPTIONS.index(selected))
            st.markdown("**Worry and ease**")
            gad_values: list[int] = []
            for index, question in enumerate(GAD7_ITEMS):
                key = f"gad_{index}"
                selected = st.select_slider(question, options=OPTIONS, value=OPTIONS[0], key=key)
                gad_values.append(OPTIONS.index(selected))
            journal = st.text_area(
                "Anything else you’d like to put into words?",
                placeholder="Share only what you are comfortable sharing.",
                height=130,
            )
            submitted = st.form_submit_button("Continue", type="primary", use_container_width=True)
        if not submitted:
            return None
        phq_score = sum(phq_values)
        gad_score = sum(gad_values)
        total = phq_score + gad_score
        maximum = self.phq_max + self.gad_max
        return {
            "phq9_responses": phq_values,
            "gad7_responses": gad_values,
            "phq9_total": phq_score,
            "gad7_total": gad_score,
            "clinical_score": round(total / maximum * 100, 1),
            "journal": journal.strip(),
        }
