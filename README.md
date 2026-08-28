# Institutional Multimodal Mental Health Early-Warning System

A transparent Streamlit prototype for confidential check-ins and anonymized institutional trend review. It is a support-routing tool, not a diagnostic instrument.

## Run locally

```powershell
cd mental-health-early-warning
python -m pip install -r requirements.txt
streamlit run app.py
```

## Architecture

- `modules/clinical_intake.py`: PHQ-9 and GAD-7 self-report collection and normalization.
- `modules/vision_task.py`: optional webcam focus task with deterministic simulation fallback.
- `modules/nlp_parser.py`: explainable LIWC-inspired lexical markers.
- `modules/fusion_engine.py`: fixed 60/20/20 weighted heuristic and support pathways.
- `modules/dashboard.py`: privacy-preserving cohort analytics.
- `utils/database.py`: anonymous Streamlit session storage of derived values only.

## Clinical and privacy boundaries

The app does not diagnose, infer a condition, or expose journals, frames, or individual biometric streams to administrators. Scores are signals for voluntary support and should be reviewed with qualified professionals. Production deployment requires institutional consent, retention controls, access control, accessibility review, and clinical governance.

The research page explains the relationship to fMRI literature: neuroimaging findings can motivate hypotheses about mechanisms, but they do not turn this lightweight behavioral check-in into an fMRI measurement or clinical diagnosis.
