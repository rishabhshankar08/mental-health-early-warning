"""Auditable weighted fusion and support routing."""

from __future__ import annotations

from typing import Any


class TransparentFusionEngine:
    """Apply the fixed clinical-first 60/20/20 scoring policy."""

    WEIGHTS = {"clinical": 0.6, "physiological": 0.2, "linguistic": 0.2}

    def score(self, clinical: float, physiological: float, linguistic: float) -> dict[str, Any]:
        values = {
            "clinical": max(0.0, min(100.0, float(clinical))),
            "physiological": max(0.0, min(100.0, float(physiological))),
            "linguistic": max(0.0, min(100.0, float(linguistic))),
        }
        composite = sum(values[name] * weight for name, weight in self.WEIGHTS.items())
        contributions = {name: round(values[name] * weight, 1) for name, weight in self.WEIGHTS.items()}
        if composite >= 60:
            tier = "Elevated Risk"
            pathway = "Offer counselor booking within 24 hours and display the campus crisis helpline."
            tracking = "Priority follow-up: invite a check-in within 7 days."
            early_steps = [
                "Tell someone you trust today that you are having a difficult time, and ask them to stay connected.",
                "Reduce non-essential demands for the next day and focus on basics such as water, food, medication as prescribed, and rest.",
                "If you might hurt yourself or cannot stay safe, contact emergency services or a crisis line now and do not stay alone.",
            ]
        elif composite >= 30:
            tier = "Moderate Strain"
            pathway = "Recommend a counseling consultation, wellbeing resources, and a self-guided support plan."
            tracking = "Active monitoring: invite a check-in within 14 days."
            early_steps = [
                "Choose one small stabilizing action today: eat, hydrate, take a short walk, or create a calmer sleep routine.",
                "Share a simple version of what is going on with someone supportive instead of carrying it alone.",
                "Arrange a counseling or primary-care appointment, and contact the service directly if your symptoms worsen.",
            ]
        else:
            tier = "Minimal Risk"
            pathway = "Share preventative wellbeing resources and keep voluntary check-ins available."
            tracking = "Routine tracking: invite the next weekly check-in."
            early_steps = [
                "Keep one protective routine this week, such as regular sleep, meals, movement, or time with people you trust.",
                "Notice what is increasing or easing stress and write down one practical adjustment you can try.",
                "Reach out sooner if your mood, worry, sleep, energy, or safety changes noticeably.",
            ]
        return {
            "composite_score": round(composite, 1),
            "tier": tier,
            "pathway": pathway,
            "tracking": tracking,
            "early_steps": early_steps,
            "components": values,
            "weights": dict(self.WEIGHTS),
            "contributions": contributions,
        }
