"""ReelIQ — Celery Video Processing Pipeline Worker"""
import os
import tempfile
import traceback
from datetime import datetime

from app.workers import celery_app
from app.video_processor import VideoProcessor
from app.ai_client import call_groq, parse_json_response
from app.storage import download_video, get_video_url
from app.database import SyncSessionLocal
from app.models import VideoAnalysis
from app.prompts.video_analysis_prompt import build_video_analysis_prompt


@celery_app.task(bind=True, name="process_video_analysis", max_retries=2)
def process_video_analysis(self, analysis_id: str, video_key: str):
    """
    Complete video analysis pipeline:
    Step 1 — Download video from S3
    Step 2 — FFmpeg extracts frames, audio waveform
    Step 3 — OpenCV computes scene changes, motion intensity
    Step 4 — Groq Vision API analyzes frames
    Step 5 — Store results in database
    """
    db = SyncSessionLocal()

    try:
        # Update status to processing
        analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
        if not analysis:
            return {"error": "Analysis not found"}

        analysis.status = "processing"
        analysis.celery_task_id = self.request.id
        db.commit()

        # Step 1: Download video from S3
        self.update_state(state="PROGRESS", meta={"step": "downloading", "progress": 10})
        video_bytes = download_video(video_key)

        # Save to temp file for processing
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        try:
            # Step 2 & 3: Process video with FFmpeg + OpenCV
            self.update_state(state="PROGRESS", meta={"step": "processing_video", "progress": 30})

            with VideoProcessor(tmp_path) as processor:
                # Get metadata
                metadata = processor.get_metadata()
                analysis.duration = metadata["duration"]
                analysis.resolution = metadata["resolution"]
                analysis.fps = metadata["fps"]
                analysis.frame_count = metadata["frame_count"]

                # Extract frames
                hook_frames = processor.extract_hook_frames()
                keyframes = processor.extract_keyframes()

                # Compute analytics
                scene_changes = processor.detect_scene_changes()
                motion_data = processor.compute_motion_intensity()
                visual_variety = processor.compute_visual_variety_score()
                audio_data = processor.extract_audio_waveform()

            # Step 4: Groq Vision API Analysis
            self.update_state(state="PROGRESS", meta={"step": "ai_analyzing", "progress": 60})
            analysis.status = "analyzing"
            db.commit()

            # Analyze hook frames (first 3 seconds)
            hook_images = [{"data": f["data"], "media_type": f["media_type"]} for f in hook_frames[:4]]
            hook_prompt = build_video_analysis_prompt(
                metadata=metadata,
                motion_data=motion_data,
                scene_changes=scene_changes,
                visual_variety_score=visual_variety,
                audio_data=audio_data,
                is_hook_frames=True,
            )
            hook_result_text = call_groq(hook_prompt, images=hook_images)
            hook_result = parse_json_response(hook_result_text)

            self.update_state(state="PROGRESS", meta={"step": "ai_analyzing_engagement", "progress": 75})

            # Analyze all keyframes for engagement mapping
            engagement_images = [{"data": f["data"], "media_type": f["media_type"]} for f in keyframes[:8]]
            engagement_prompt = build_video_analysis_prompt(
                metadata=metadata,
                motion_data=motion_data,
                scene_changes=scene_changes,
                visual_variety_score=visual_variety,
                audio_data=audio_data,
                is_hook_frames=False,
            )
            engagement_result_text = call_groq(engagement_prompt, images=engagement_images)
            engagement_result = parse_json_response(engagement_result_text)

            # Step 5: Store results
            self.update_state(state="PROGRESS", meta={"step": "storing_results", "progress": 90})

            analysis.hook_score = hook_result.get("hook_score", 0)
            analysis.hook_analysis = hook_result.get("hook_analysis", "")
            analysis.hook_rewrites = hook_result.get("hook_rewrites", [])
            analysis.visual_engagement = hook_result.get("visual_engagement", 0)

            analysis.drop_off_points = engagement_result.get("drop_off_points", [])
            analysis.cut_suggestions = engagement_result.get("cut_suggestions", [])
            analysis.move_earlier_suggestions = engagement_result.get("move_earlier_suggestions", [])
            analysis.viral_optimizations = engagement_result.get("viral_optimizations", [])
            analysis.pacing_verdict = engagement_result.get("pacing_verdict", "")
            analysis.engagement_probability = engagement_result.get("engagement_probability", 0)

            # Compute combined viral score
            hook_weight = 0.4
            engagement_weight = 0.3
            variety_weight = 0.15
            motion_weight = 0.15

            avg_motion_engagement = 0
            if motion_data:
                avg_motion_engagement = sum(m.get("engagement_proxy", 0) for m in motion_data) / len(motion_data)

            analysis.viral_score = round(
                hook_result.get("hook_score", 50) * hook_weight +
                engagement_result.get("engagement_probability", 50) * engagement_weight +
                visual_variety * variety_weight +
                avg_motion_engagement * motion_weight,
                1
            )

            analysis.status = "completed"
            analysis.completed_at = datetime.utcnow()
            analysis.video_url = get_video_url(video_key)
            db.commit()

            return {
                "analysis_id": analysis_id,
                "status": "completed",
                "hook_score": analysis.hook_score,
                "viral_score": analysis.viral_score,
            }

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()

        raise self.retry(exc=e, countdown=30)

    finally:
        db.close()
