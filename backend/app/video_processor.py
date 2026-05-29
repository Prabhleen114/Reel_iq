"""ReelIQ — Video Processing Pipeline (FFmpeg + OpenCV)"""
import os
import cv2
import numpy as np
import subprocess
import tempfile
import base64
import json
from typing import Dict, Any, List, Tuple
from pathlib import Path


class VideoProcessor:
    """Handles all video processing: frame extraction, scene detection, motion analysis."""

    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.frame_count / self.fps if self.fps > 0 else 0

    def get_metadata(self) -> Dict[str, Any]:
        """Extract video metadata."""
        return {
            "duration": round(self.duration, 2),
            "fps": round(self.fps, 2),
            "resolution": f"{self.width}x{self.height}",
            "frame_count": self.frame_count,
            "width": self.width,
            "height": self.height,
        }

    def extract_hook_frames(self, max_frames: int = 6) -> List[Dict[str, Any]]:
        """Extract frames from first 3 seconds for hook analysis."""
        hook_duration = min(3.0, self.duration)
        hook_frame_count = int(hook_duration * self.fps)
        interval = max(1, hook_frame_count // max_frames)

        frames = []
        for i in range(0, hook_frame_count, interval):
            if len(frames) >= max_frames:
                break
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = self.cap.read()
            if ret:
                # Resize for API efficiency (max 1024px wide)
                if frame.shape[1] > 1024:
                    scale = 1024 / frame.shape[1]
                    frame = cv2.resize(frame, None, fx=scale, fy=scale)

                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frames.append({
                    "timestamp": round(i / self.fps, 2),
                    "frame_index": i,
                    "data": base64.b64encode(buffer).decode("utf-8"),
                    "media_type": "image/jpeg",
                })

        return frames

    def extract_keyframes(self, interval_seconds: float = 2.0, max_frames: int = 15) -> List[Dict[str, Any]]:
        """Extract keyframes every N seconds for engagement mapping."""
        interval_frames = int(interval_seconds * self.fps)
        frames = []

        for i in range(0, self.frame_count, interval_frames):
            if len(frames) >= max_frames:
                break
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = self.cap.read()
            if ret:
                if frame.shape[1] > 1024:
                    scale = 1024 / frame.shape[1]
                    frame = cv2.resize(frame, None, fx=scale, fy=scale)

                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frames.append({
                    "timestamp": round(i / self.fps, 2),
                    "frame_index": i,
                    "data": base64.b64encode(buffer).decode("utf-8"),
                    "media_type": "image/jpeg",
                })

        return frames

    def detect_scene_changes(self, threshold: float = 30.0) -> List[Dict[str, Any]]:
        """Detect scene changes using frame differencing."""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        scene_changes = []
        prev_frame = None
        frame_idx = 0

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (320, 180))

            if prev_frame is not None:
                diff = cv2.absdiff(prev_frame, gray)
                mean_diff = np.mean(diff)

                if mean_diff > threshold:
                    scene_changes.append({
                        "timestamp": round(frame_idx / self.fps, 2),
                        "frame_index": frame_idx,
                        "intensity": round(float(mean_diff), 2),
                    })

            prev_frame = gray
            frame_idx += 1

            # Skip frames for performance (check every 5 frames)
            skip = 4
            for _ in range(skip):
                ret = self.cap.grab()
                if not ret:
                    break
                frame_idx += 1

        return scene_changes

    def compute_motion_intensity(self, segment_seconds: float = 1.0) -> List[Dict[str, Any]]:
        """Compute motion intensity per segment as an engagement proxy."""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        segment_frames = int(segment_seconds * self.fps)
        segments = []
        prev_frame = None
        frame_idx = 0
        current_segment_diffs = []
        segment_start = 0.0

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (320, 180))

            if prev_frame is not None:
                diff = cv2.absdiff(prev_frame, gray)
                current_segment_diffs.append(float(np.mean(diff)))

            if len(current_segment_diffs) >= segment_frames and current_segment_diffs:
                avg_motion = np.mean(current_segment_diffs)
                segments.append({
                    "start": round(segment_start, 2),
                    "end": round(frame_idx / self.fps, 2),
                    "motion_intensity": round(avg_motion, 2),
                    "engagement_proxy": min(100, round(avg_motion * 5, 1)),
                })
                segment_start = frame_idx / self.fps
                current_segment_diffs = []

            prev_frame = gray
            frame_idx += 1

        # Last segment
        if current_segment_diffs:
            avg_motion = np.mean(current_segment_diffs)
            segments.append({
                "start": round(segment_start, 2),
                "end": round(frame_idx / self.fps, 2),
                "motion_intensity": round(avg_motion, 2),
                "engagement_proxy": min(100, round(avg_motion * 5, 1)),
            })

        return segments

    def compute_visual_variety_score(self) -> float:
        """Compute overall visual variety score (0-100)."""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        histograms = []
        sample_interval = max(1, self.frame_count // 20)

        for i in range(0, self.frame_count, sample_interval):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (160, 90))
            hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            histograms.append(hist)

        if len(histograms) < 2:
            return 50.0

        # Compare consecutive histograms
        diffs = []
        for i in range(1, len(histograms)):
            diff = cv2.compareHist(histograms[i - 1], histograms[i], cv2.HISTCMP_BHATTACHARYYA)
            diffs.append(diff)

        avg_diff = np.mean(diffs)
        # Scale to 0-100 (Bhattacharyya distance is 0-1)
        return round(min(100, avg_diff * 150), 1)

    def extract_audio_waveform(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Extract audio waveform data using FFmpeg."""
        if output_path is None:
            output_path = self.video_path + "_audio.wav"

        try:
            subprocess.run(
                [
                    "ffmpeg", "-i", self.video_path,
                    "-vn", "-acodec", "pcm_s16le",
                    "-ar", "16000", "-ac", "1",
                    "-y", output_path,
                ],
                capture_output=True,
                timeout=30,
            )

            if os.path.exists(output_path):
                import wave
                with wave.open(output_path, "r") as wf:
                    frames = wf.readframes(wf.getnframes())
                    audio_data = np.frombuffer(frames, dtype=np.int16)

                    # Downsample for visualization
                    chunk_size = max(1, len(audio_data) // 100)
                    waveform = []
                    for i in range(0, len(audio_data), chunk_size):
                        chunk = audio_data[i:i + chunk_size]
                        waveform.append(round(float(np.abs(chunk).mean()) / 32768.0, 4))

                os.remove(output_path)

                return {
                    "waveform": waveform,
                    "has_audio": True,
                    "sample_rate": 16000,
                    "duration": round(len(audio_data) / 16000, 2),
                }
        except Exception as e:
            pass

        return {"waveform": [], "has_audio": False}

    def generate_thumbnail(self) -> bytes:
        """Generate a thumbnail from the first frame."""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = self.cap.read()
        if ret:
            # Resize to thumbnail
            frame = cv2.resize(frame, (480, 854))
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            return buffer.tobytes()
        return b""

    def run_full_analysis(self) -> Dict[str, Any]:
        """Run the complete video processing pipeline."""
        metadata = self.get_metadata()
        hook_frames = self.extract_hook_frames()
        keyframes = self.extract_keyframes()
        scene_changes = self.detect_scene_changes()
        motion_data = self.compute_motion_intensity()
        visual_variety = self.compute_visual_variety_score()
        audio_data = self.extract_audio_waveform()

        return {
            "metadata": metadata,
            "hook_frames": hook_frames,
            "keyframes": keyframes,
            "scene_changes": scene_changes,
            "motion_data": motion_data,
            "visual_variety_score": visual_variety,
            "audio_data": audio_data,
        }

    def close(self):
        """Release video capture."""
        if self.cap.isOpened():
            self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function for direct use
def process_video(video_path: str) -> Dict[str, Any]:
    """Process a video file and return all analysis data."""
    with VideoProcessor(video_path) as processor:
        return processor.run_full_analysis()
