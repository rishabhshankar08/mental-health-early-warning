"""Explainable lexical markers inspired by Pennebaker and LIWC principles."""

from __future__ import annotations

import re
from typing import Any


class NLPLinguisticParser:
    """Compute explainable language markers and a warm, non-diagnostic response."""

    FIRST_PERSON = {"i", "me", "my", "mine", "myself"}
    ABSOLUTIST = {"always", "never", "completely", "totally"}
    NEGATIVE = {
        "anxious", "anger", "angry", "bad", "burden", "crisis", "depressed", "despair",
        "difficult", "exhausted", "failure", "fear", "hopeless", "lonely", "overwhelmed",
        "pain", "sad", "stress", "stressed", "tired", "worry", "worried",
    }
    HIGH_CONCERN = {
        "die", "dying", "hurt", "hurting", "kill", "suicide", "unsafe", "worthless", "hopeless",
    }
    POSITIVE = {
        "calm", "comfortable", "connected", "enjoy", "enjoyed", "glad", "good", "grateful",
        "hope", "hopeful", "laugh", "love", "okay", "peace", "proud", "relaxed", "rested",
        "smile", "supported", "thankful", "well", "better",
    }
    THEMES = {
        "energy": {"energy", "exhausted", "fatigue", "sleep", "tired", "rest", "awake"},
        "worry": {"anxious", "fear", "nervous", "panic", "stress", "stressed", "worry", "worried"},
        "mood": {"depressed", "despair", "hopeless", "lonely", "sad", "down", "empty"},
        "pressure": {"busy", "deadline", "demands", "failure", "overwhelmed", "pressure", "work"},
        "connection": {"alone", "family", "friend", "friends", "isolated", "lonely", "people", "support"},
    }

    def analyze(self, text: str) -> dict[str, Any]:
        tokens = re.findall(r"[a-zA-Z]+", text.lower())
        count = max(len(tokens), 1)
        sentences = [sentence.strip() for sentence in re.split(r"[.!?]+", text) if sentence.strip()]
        first_person = sum(token in self.FIRST_PERSON for token in tokens)
        absolutist = sum(token in self.ABSOLUTIST for token in tokens)
        negative = sum(token in self.NEGATIVE for token in tokens)
        high_concern = sum(token in self.HIGH_CONCERN for token in tokens)
        positive = sum(token in self.POSITIVE for token in tokens)
        first_person_density = first_person / count
        absolutist_density = absolutist / count
        negative_density = negative / count
        negative_signal = min(65.0, (negative * 14.0) + (high_concern * 18.0))
        absolutist_signal = min(25.0, absolutist * 12.5)
        first_person_signal = min(10.0, first_person * 2.0)
        score = min(100.0, negative_signal + absolutist_signal + first_person_signal)
        themes = {theme: sum(token in words for token in tokens) for theme, words in self.THEMES.items()}
        active_themes = [theme for theme, matches in themes.items() if matches]
        emotion_balance = positive - negative
        if negative >= 4 or negative > positive * 2:
            tone = "carrying a lot right now"
        elif negative > positive:
            tone = "a little weighed down"
        elif positive > negative:
            tone = "finding some steadier ground"
        else:
            tone = "mixed or hard to read from a short note"
        interpretation = self._interpretation(tone, active_themes, len(sentences))
        return {
            "linguistic_score": round(score, 1),
            "token_count": len(tokens),
            "first_person_count": first_person,
            "absolutist_count": absolutist,
            "negative_emotion_count": negative,
            "high_concern_count": high_concern,
            "first_person_frequency": round(first_person_density * 100, 1),
            "absolutist_frequency": round(absolutist_density * 100, 1),
            "negative_emotion_density": round(negative_density * 100, 1),
            "positive_emotion_count": positive,
            "positive_emotion_density": round(positive / count * 100, 1),
            "sentence_count": len(sentences),
            "themes": themes,
            "active_themes": active_themes,
            "emotion_balance": emotion_balance,
            "score_reason": f"The score reflects {negative} negative-emotion marker(s), {absolutist} absolutist marker(s), and {high_concern} high-concern marker(s). The category caps prevent longer writing from automatically counting as more concerning.",
            "tone": tone,
            "interpretation": interpretation,
            "comfort_message": self._comfort_message(tone, active_themes),
        }

    @staticmethod
    def _interpretation(tone: str, themes: list[str], sentence_count: int) -> str:
        if not themes:
            return f"This is a short note, so there is not much language to interpret. The overall tone comes across as {tone}."
        readable_themes = ", ".join(themes)
        return f"The note sounds {tone}, with the clearest threads around {readable_themes}. This is a language pattern, not a verdict about how you are feeling."

    @staticmethod
    def _comfort_message(tone: str, themes: list[str]) -> str:
        if tone == "carrying a lot right now":
            return "That sounds like a heavy stretch. You do not have to sort it all out today; choose one small thing that would make the next hour gentler, and let someone you trust know you could use a little company."
        if tone == "a little weighed down":
            return "It sounds like this week has taken more out of you than usual. Be kind to yourself about that. One manageable step, a proper pause, or a quick check-in with someone close can be enough for today."
        if tone == "finding some steadier ground":
            return "There is some steadiness in what you shared. Hold on to whatever helped, even if it was small, and give yourself credit for noticing what is working."
        return "Thank you for putting a few words to your week. Sometimes a short check-in is all we can manage. You can come back to this when you have a little more space."
