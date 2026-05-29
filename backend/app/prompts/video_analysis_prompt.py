"""ReelIQ — Video Analysis Prompt Template (for Groq Vision API)"""
import json
from typing import Dict, Any, List


def build_video_analysis_prompt(
    metadata: Dict[str, Any],
    motion_data: List[Dict[str, Any]],
    scene_changes: List[Dict[str, Any]],
    visual_variety_score: float,
    audio_data: Dict[str, Any],
    is_hook_frames: bool = False,
) -> str:
    """
    Build the prompt for video frame analysis via Groq Vision API.

    For hook frames (first 3 seconds):
    - Analyze hook strength
    - Score the opening

    For all keyframes:
    - Detect drop-off risks
    - Analyze pacing
    """
    metadata_str = json.dumps(metadata, default=str)
    motion_str = json.dumps(motion_data[:10], default=str)
    scene_str = json.dumps(scene_changes[:10], default=str)

    if is_hook_frames:
        return f"""Analyze these frames from the FIRST 3 SECONDS of an Instagram Reel. These are the critical "hook" frames that determine whether a viewer swipes away or keeps watching.

Video metadata: {metadata_str}
Motion intensity data: {motion_str}
Visual variety score: {visual_variety_score}/100

For each frame, evaluate:
1. Is there immediate visual interest? (text overlay, face, action, contrast)
2. Does the opening create curiosity or emotional reaction?
3. Is there a clear subject/focus, or is it visually cluttered?
4. Does the pacing match what performs well on Reels (fast, dynamic)?

Return ONLY this JSON:
{{
    "hook_score": 0-100,
    "hook_analysis": "2-3 sentence analysis of the opening's effectiveness",
    "hook_rewrites": [
        "Suggested visual/text hook improvement 1",
        "Suggested visual/text hook improvement 2",
        "Suggested visual/text hook improvement 3"
    ],
    "visual_engagement": 0-100,
    "first_frame_verdict": "What a viewer sees in the first frame and whether it's compelling enough"
}}

Score honestly. Most Reels have weak hooks. A score above 70 means the hook is genuinely strong."""

    else:
        return f"""Analyze these keyframes from an Instagram Reel to identify engagement patterns, drop-off risks, and optimization opportunities.

Video metadata: {metadata_str}
Motion intensity by segment: {motion_str}
Scene changes detected: {scene_str}
Visual variety score: {visual_variety_score}/100
Has audio: {audio_data.get('has_audio', False)}

For each keyframe/segment, evaluate:
1. Where might viewers drop off? (visual boredom, no new information, pacing slowdown)
2. Which segments should be cut or shortened?
3. Which segments are the strongest and should be moved earlier?
4. Overall pacing assessment

Return ONLY this JSON:
{{
    "drop_off_points": [
        {{"timestamp": 0.0, "reason": "Why viewers would leave at this point"}}
    ],
    "cut_suggestions": [
        {{"start": 0.0, "end": 0.0, "reason": "Why this segment should be cut"}}
    ],
    "move_earlier_suggestions": [
        {{"segment": "timestamp range", "reason": "Why this high-energy moment should appear sooner"}}
    ],
    "viral_optimizations": [
        "Specific optimization suggestion 1",
        "Specific optimization suggestion 2"
    ],
    "pacing_verdict": "Overall assessment of the video's pacing and rhythm",
    "engagement_probability": 0-100
}}

Be specific about timestamps. Reference actual visual content from the frames when explaining your analysis."""
