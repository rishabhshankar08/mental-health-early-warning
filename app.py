"""Streamlit application router for the early-warning system."""

from __future__ import annotations

import streamlit as st

from modules.clinical_intake import ClinicalIntakeModule
from modules.dashboard import InstitutionalDashboardModule
from modules.fusion_engine import TransparentFusionEngine
from modules.nlp_parser import NLPLinguisticParser
from modules.vision_task import VisionTaskModule
from utils.database import records_as_dataframe, save_checkin


st.set_page_config(page_title="Signal / Wellbeing", page_icon="+", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@500;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #171a1f; color: #f5f1ea; }
    [data-testid="stHeader"] { background: rgba(23, 26, 31, .88); }
    [data-testid="stSidebar"] { background: #20252c; border-right: 1px solid #3a424c; }
    [data-testid="stSidebar"] * { color: #f5f1ea; }
    .stMarkdown, label, p, span { color: #f5f1ea; }
    [data-testid="stMetric"] { background: #232830; border: 1px solid #3a424c; padding: .85rem; }
    [data-testid="stMetricLabel"] { color: #b8c3c4; }
    [data-testid="stMetricValue"] { color: #f5f1ea; }
    [data-testid="stExpander"] { background: #20252c; border: 1px solid #3a424c; }
    .stTextInput input, .stTextArea textarea { background: #232830; color: #f5f1ea; border-color: #53616a; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: 0; }
    .block-container { max-width: 1180px; padding-top: 3rem; }
    .eyebrow { color: #f29b82; font-size: .78rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
    .hero { background: #20252c; border: 1px solid #405b59; border-top: 4px solid #f29b82; padding: 1.5rem 1.75rem; margin-bottom: 1.5rem; }
    .hero h1 { font-size: clamp(1.8rem, 4vw, 3rem); line-height: 1.08; margin: .35rem 0 .8rem; color: #f5f1ea; }
    .hero p { max-width: 680px; color: #d0d8d3; font-size: 1rem; }
    .risk-box { border-left: 5px solid #f29b82; background: #2b3438; padding: 1rem 1.2rem; margin: 1rem 0; }
    .method-box { background: #20252c; border: 1px solid #3a424c; color: #f5f1ea; padding: 1.2rem; margin-top: 1.5rem; }
    .method-box strong { color: #f29b82; }
    .stAlert { background: #2d2b28; }
    @keyframes drift { from { transform: translateX(0); } to { transform: translateX(min(780px, 70vw)); } }
    </style>
    """,
    unsafe_allow_html=True,
)


def show_home() -> None:
    st.markdown('<div class="hero"><div class="eyebrow">A private moment for you</div><h1>Check in. Find your next good step.</h1><p>A gentle reflection space that combines your answers with transparent, optional signals to suggest support. It is not a diagnosis.</p></div>', unsafe_allow_html=True)
    st.warning("If you may be in immediate danger, contact local emergency services or your institution's crisis line now. This space is not an emergency service.")
    if "last_result" in st.session_state and "clinical_payload" not in st.session_state:
        result = st.session_state.last_result
        fusion = result["fusion"]
        st.markdown(f'<div class="risk-box"><div class="eyebrow">Your next step</div><h2>{fusion["tier"]} · {fusion["composite_score"]}/100</h2><p>{fusion["pathway"]}</p><strong>{fusion["tracking"]}</strong></div>', unsafe_allow_html=True)
        st.subheader("If help is not immediately available")
        st.caption("These are short-term support steps while you arrange appropriate care. They do not replace professional assessment or emergency help.")
        for step in fusion["early_steps"]:
            st.markdown(f"- {step}")
        st.warning("If you are in immediate danger, may act on thoughts of self-harm, or cannot keep yourself safe, stop here and contact local emergency services or a crisis line. Ask someone you trust to stay with you.")
        linguistic_result = result.get("linguistic", {})
        if linguistic_result.get("comfort_message"):
            st.markdown("**A note for you**")
            st.success(linguistic_result["comfort_message"])
        cols = st.columns(3)
        for column, name, label in zip(cols, ("clinical", "physiological", "linguistic"), ("Your answers", "Focus break", "Writing patterns")):
            column.metric(label, f"{fusion['components'][name]:.1f}/100", f"Weight {fusion['weights'][name]:.0%}")
        st.subheader("How this result was calculated")
        st.caption("Each component is normalized to 0–100. The fixed weights are applied exactly as shown; no hidden classifier is involved.")
        with st.expander("1. Your answers · clinical backbone", expanded=False):
            clinical_detail = result.get("clinical")
            if clinical_detail:
                st.write(f"PHQ-9 total: {clinical_detail['phq9_total']} out of 27. GAD-7 total: {clinical_detail['gad7_total']} out of 21. Together, {clinical_detail['phq9_total'] + clinical_detail['gad7_total']} points out of 48 becomes a clinical score of {fusion['components']['clinical']:.1f}/100. This component carries the primary 60% weight, contributing {fusion['contributions']['clinical']:.1f} points to the composite.")
            else:
                st.write(f"The clinical self-report score is {fusion['components']['clinical']:.1f}/100 and contributes {fusion['contributions']['clinical']:.1f} points at the primary 60% weight. Detailed totals are available for new check-ins.")
            st.caption("The individual responses are used for this private result but are not sent to the institutional aggregate dashboard.")
        with st.expander("2. Focus break · webcam signal"):
            vision_result = st.session_state.last_result["vision"]
            blink_rate = vision_result.get("blink_rate_per_minute", "unavailable")
            if vision_result.get("data_collected", True) is False:
                st.write("The camera was not used for this check-in. No physiological data was collected, so the model uses a neutral midpoint of 50/100 for this optional component. That contributes 10 points at the 20% weight rather than pretending simulated values came from you.")
            else:
                st.write(f"The continuous stream produced {vision_result.get('samples', 'an unspecified number')} usable eye samples from {vision_result.get('frames', 'an unspecified number')} video frames over {vision_result.get('elapsed_seconds', 'an unspecified duration')} seconds. Blink rate was {blink_rate} per minute, normalized iris-size variance was {vision_result['pupillometry_variance']}, and gaze attention was {float(vision_result['gaze_attention']):.0%}. These derived values produce a physiological score of {fusion['components']['physiological']:.1f}/100 and contribute {fusion['contributions']['physiological']:.1f} points at the 20% weight.")
            st.caption("Blink rate is estimated from closure transitions over the continuous stream. Iris size and eye openness are webcam proxies, not calibrated clinical measurements. Video frames are not stored.")
        with st.expander("3. Writing patterns · linguistic signal"):
            linguistic_result = st.session_state.last_result["linguistic"]
            st.write(linguistic_result.get("interpretation", "This language signal is based on a few explainable word patterns, not a diagnosis."))
            if linguistic_result.get("active_themes"):
                st.write(f"The clearest themes were: {', '.join(linguistic_result['active_themes'])}.")
            st.write(f"The language signal was {fusion['components']['linguistic']:.1f}/100. It contributes a smaller 20% context to the overall support signal. The pattern combines first-person focus, absolute wording, and negative-emotion language; positive language is shown as context and does not cancel out a difficult experience.")
            st.write(linguistic_result.get("score_reason", "The language signal uses bounded, explainable word counts rather than word-count density alone."))
            with st.expander("Show the underlying counts", expanded=False):
                st.write(f"{linguistic_result['token_count']} words across {linguistic_result.get('sentence_count', 'an unknown number')} sentences. First-person terms: {linguistic_result['first_person_count']} ({linguistic_result['first_person_frequency']:.1f}%). Absolutist terms: {linguistic_result['absolutist_count']} ({linguistic_result['absolutist_frequency']:.1f}%). Negative-emotion terms: {linguistic_result['negative_emotion_count']} ({linguistic_result['negative_emotion_density']:.1f}%). Positive-emotion terms: {linguistic_result.get('positive_emotion_count', 0)} ({linguistic_result.get('positive_emotion_density', 0):.1f}%).")
            st.caption("Only derived counts and themes are shown here. The original journal is not displayed or stored in analytics.")
        st.info(f"In plain language: your answers have the biggest influence because they count for 60%. The optional focus and writing signals each add a smaller 20% context. Together they place this check-in in the {fusion['tier']} range.")
        st.caption("This is a transparent support-routing signal, not a label. A qualified person should help interpret concerns.")
        if st.button("Start a new check-in", use_container_width=True):
            st.session_state.pop("last_result")
            st.session_state.pop("vision_result", None)
            st.session_state.pop("vision_samples", None)
            st.session_state.pop("last_frame_id", None)
            st.rerun()
        return
    intake = ClinicalIntakeModule()
    if "clinical_payload" not in st.session_state:
        payload = intake.render()
        if payload:
            st.session_state.clinical_payload = payload
            st.rerun()
        return

    payload = st.session_state.clinical_payload
    st.success("Thanks for sharing. Take the optional focus break when you’re ready.")
    vision = VisionTaskModule().render()
    can_generate = bool(vision.get("ready", True))
    if st.button("See my support summary", type="primary", use_container_width=True, disabled=not can_generate):
        linguistic = NLPLinguisticParser().analyze(payload["journal"])
        result = TransparentFusionEngine().score(payload["clinical_score"], vision["physio_score"], linguistic["linguistic_score"])
        save_checkin(
            composite_score=result["composite_score"], tier=result["tier"], clinical_score=payload["clinical_score"],
            physio_score=vision["physio_score"], linguistic_score=linguistic["linguistic_score"],
        )
        st.session_state.last_result = {
            "fusion": result,
            "linguistic": linguistic,
            "vision": vision,
            "clinical": {"phq9_total": payload["phq9_total"], "gad7_total": payload["gad7_total"]},
        }
        st.session_state.pop("clinical_payload", None)
        st.rerun()

def show_research() -> None:
    st.markdown('<div class="eyebrow">Methods and governance</div>', unsafe_allow_html=True)
    st.title("Research & architecture")
    st.write("This system treats clinical self-report as the primary signal and uses physiology and language as contextual, explainable companions.")
    st.markdown('<div class="method-box"><strong>Composite Risk Score</strong><br><br>0.6 × Clinical + 0.2 × Physiological + 0.2 × Linguistic<br><br>Every tier maps to a support pathway and a longitudinal follow-up state.</div>', unsafe_allow_html=True)
    st.subheader("Why mention fMRI literature?")
    st.write("fMRI research can help researchers study networks associated with affect, threat processing, reward, and cognitive control. Those findings are population-level evidence and are not direct measurements in this app. A webcam and a journal cannot reproduce an fMRI scan, and this product makes no neuroimaging or diagnostic claim.")
    st.subheader("Clinical guardrails")
    st.write("PHQ-9 and GAD-7 components are presented as validated self-report prompts. Any elevated signal should trigger human review and an offer of support, never an automated label, employment decision, academic penalty, or treatment recommendation.")
    st.subheader("Data boundary")
    st.write("The local store keeps derived scores and timestamps for trend aggregation. Raw journals and camera frames are not persisted. Production institutions must add authenticated access, retention limits, consent, encryption, audit logging, and a formal clinical safety review.")


def main() -> None:
    with st.sidebar:
        st.markdown("## Signal / Wellbeing")
        st.caption("Transparent support routing")
        page = st.radio("Workspace", ["User Portal", "Institutional Admin Dashboard", "Research & Architecture Documentation"])
        st.divider()
        st.caption("No diagnosis. No raw journals in analytics. Human support remains the decision-maker.")
    if page == "User Portal":
        show_home()
    elif page == "Institutional Admin Dashboard":
        InstitutionalDashboardModule().render(records_as_dataframe())
    else:
        show_research()


if __name__ == "__main__":
    main()
