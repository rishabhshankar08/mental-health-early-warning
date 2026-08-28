"""Continuous webcam focus task with explainable eye metrics."""

from __future__ import annotations

import threading
import time
from typing import Any

import av
import cv2
import numpy as np
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_webrtc import VideoProcessorBase, WebRtcMode, webrtc_streamer


class LiveFocusProcessor(VideoProcessorBase):
    """Process webcam frames in memory and track blink timing over the stream."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.eye_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml")
        self.started_at = time.monotonic()
        self.last_blink_at = 0.0
        self.eyes_closed = False
        self.blinks = 0
        self.frames = 0
        self.valid_frames = 0
        self.pupil_values: list[float] = []
        self.gaze_values: list[float] = []

    @staticmethod
    def _pupil_metrics(eye: np.ndarray) -> tuple[float, float] | None:
        eye_height, eye_width = eye.shape[:2]
        threshold_input = cv2.GaussianBlur(eye, (5, 5), 0)
        _, threshold = cv2.threshold(threshold_input, 65, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = [contour for contour in contours if 0.01 * eye_width * eye_height < cv2.contourArea(contour) < 0.45 * eye_width * eye_height]
        if not candidates:
            return None
        pupil = max(candidates, key=cv2.contourArea)
        (center_x, _), radius = cv2.minEnclosingCircle(pupil)
        return max(radius * 2, 1) / max(eye_width, 1), center_x / max(eye_width, 1)

    def _metrics_from_frame(self, image: np.ndarray) -> tuple[float, float, float] | None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
        if len(faces) == 0:
            return None
        face_x, face_y, face_width, face_height = max(faces, key=lambda item: item[2] * item[3])
        upper_face = gray[face_y:face_y + face_height // 2, face_x:face_x + face_width]
        eyes = sorted(self.eye_detector.detectMultiScale(upper_face, scaleFactor=1.1, minNeighbors=6, minSize=(25, 18)), key=lambda item: item[0])[:2]
        if len(eyes) < 2:
            return None
        pupil_metrics: list[tuple[float, float]] = []
        eye_ratios: list[float] = []
        for eye_x, eye_y, eye_width, eye_height in eyes:
            metrics = self._pupil_metrics(upper_face[eye_y:eye_y + eye_height, eye_x:eye_x + eye_width])
            if metrics is None:
                return None
            pupil_metrics.append(metrics)
            eye_ratios.append(eye_height / max(eye_width, 1))
        pupil_size = float(np.mean([metric[0] for metric in pupil_metrics]))
        gaze_attention = 1 - min(1, abs(float(np.mean([metric[1] for metric in pupil_metrics])) - 0.5) * 2)
        ear = float(np.mean(eye_ratios))
        return pupil_size, float(np.clip(gaze_attention, 0, 1)), ear

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        image = frame.to_ndarray(format="bgr24")
        metrics = self._metrics_from_frame(image)
        now = time.monotonic()
        with self.lock:
            self.frames += 1
            if metrics is not None:
                pupil_size, gaze_attention, ear = metrics
                self.pupil_values.append(pupil_size)
                self.gaze_values.append(gaze_attention)
                self.valid_frames += 1
                is_closed = ear < 0.21
                if is_closed and not self.eyes_closed and now - self.last_blink_at > 0.25:
                    self.blinks += 1
                    self.last_blink_at = now
                self.eyes_closed = is_closed
                cv2.putText(image, f"eye openness proxy {ear:.2f}  blinks {self.blinks}", (18, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (242, 192, 120), 2)
            else:
                cv2.putText(image, "Face not detected - adjust lighting", (18, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (80, 210, 190), 2)
        return av.VideoFrame.from_ndarray(image, format="bgr24")

    def snapshot(self) -> dict[str, float | int | str] | None:
        with self.lock:
            if not self.pupil_values:
                return None
            elapsed = max(time.monotonic() - self.started_at, 0.1)
            detection_rate = self.valid_frames / max(self.frames, 1)
            blink_rate = self.blinks / elapsed * 60
            pupil_variance = float(np.var(self.pupil_values))
            gaze_attention = float(np.mean(self.gaze_values))
            score = np.clip(100 - (pupil_variance * 900) + ((gaze_attention - 0.5) * 35), 0, 100)
            return {
                "physio_score": round(float(score), 1),
                "pupillometry_variance": round(pupil_variance, 5),
                "blink_rate_per_minute": round(float(blink_rate), 1),
                "gaze_attention": round(gaze_attention, 3),
                "samples": len(self.pupil_values),
                "frames": self.frames,
                "detection_rate": round(float(detection_rate), 3),
                "elapsed_seconds": round(float(elapsed), 1),
                "ready": bool(elapsed >= 10 and len(self.pupil_values) >= 30 and detection_rate >= 0.5),
                "source": "live webcam + OpenCV eye tracking",
            }


class VisionTaskModule:
    """Render a live, privacy-preserving webcam stream with a simulation fallback."""

    @staticmethod
    def _simulate() -> dict[str, float | str]:
        rng = np.random.default_rng(42)
        pupil_variance = float(np.clip(rng.normal(0.38, 0.07), 0.12, 0.70))
        blink_rate = float(np.clip(rng.normal(15.0, 3.0), 7.0, 28.0))
        gaze_attention = float(np.clip(rng.normal(0.78, 0.08), 0.45, 0.98))
        score = np.clip(100 - (pupil_variance * 30) - (abs(blink_rate - 15) * 1.5) + ((gaze_attention - 0.5) * 35), 0, 100)
        return {
            "physio_score": round(float(score), 1),
            "pupillometry_variance": round(pupil_variance, 3),
            "blink_rate_per_minute": round(blink_rate, 1),
            "gaze_attention": round(gaze_attention, 3),
            "source": "high-fidelity simulation",
            "data_collected": False,
        }

    @staticmethod
    def _not_collected() -> dict[str, float | str | bool]:
        return {
            "physio_score": 50.0,
            "pupillometry_variance": "not collected",
            "blink_rate_per_minute": "not collected",
            "gaze_attention": 0.5,
            "source": "camera not used; neutral midpoint",
            "ready": True,
            "data_collected": False,
        }

    def render(self) -> dict[str, Any]:
        st.subheader("A moment to reset")
        st.write("Allow camera access and keep your face in view for a few seconds. The live stream measures iris size, blink rhythm, and gaze position locally.")
        st.caption("Frames are processed in memory and never saved. The stream needs camera permission and a secure browser context.")
        try:
            context = webrtc_streamer(
                key="focus-camera-stream",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=LiveFocusProcessor,
                media_stream_constraints={"video": True, "audio": False},
                async_processing=True,
            )
        except (ImportError, RuntimeError, OSError) as error:
            st.warning(f"Live video is unavailable in this environment ({type(error).__name__}).")
            context = None

        if context is not None and context.state.playing:
            st_autorefresh(interval=1000, limit=None, key="focus-metrics-refresh")

        if context is not None and context.video_processor is not None:
            result = context.video_processor.snapshot()
            if result is not None:
                if result["ready"]:
                    st.success("Live tracking is ready. Blink rate is calculated from at least 10 seconds of continuous video.")
                else:
                    st.info(f"Live tracking is collecting. Keep the stream running for {max(0, 10 - float(result['elapsed_seconds'])):.0f} more seconds with your face visible.")
                metrics = st.columns(3)
                metrics[0].metric("Blink rate", f"{result['blink_rate_per_minute']}/min" if result["ready"] else "Collecting")
                metrics[1].metric("Iris-size variance", result["pupillometry_variance"])
                metrics[2].metric("Gaze attention", f"{float(result['gaze_attention']):.0%}")
                st.caption(f"Quality: {float(result['detection_rate']):.0%} of {result['frames']} video frames contained a usable eye detection. The displayed eye openness is an OpenCV proxy, not clinical-grade EAR.")
                if result["ready"] and st.button("Use live webcam signal", type="primary", use_container_width=True):
                    st.session_state.vision_result = result
                    st.rerun()
                return result
            st.info("Start the stream and keep your face visible while metrics collect.")

        st.divider()
        st.caption("No camera? You can continue with a clearly labeled simulation.")
        if st.button("Use private simulation instead", use_container_width=True):
            st.session_state.vision_result = self._simulate()
            st.rerun()
        return st.session_state.get("vision_result", self._not_collected())
