"""ReelIQ — Reel Rewrite Prompt Template"""
import json
from typing import Optional, Dict, Any


def build_reel_rewrite_prompt(
    hook: Optional[str] = None,
    caption: Optional[str] = None,
    video_analysis: Optional[Dict[str, Any]] = None,
    niche: Optional[str] = None,
) -> str:
    """
    Build the prompt for a full reel rewrite.

    Input: Video analysis data, current caption, hook
    Output: Complete reel rewrite with new hook, caption, structure, viral potential
    """
    context_parts = []

    if hook:
        context_parts.append(f"Current hook: \"{hook}\"")
    if caption:
        context_parts.append(f"Current caption: \"{caption}\"")
    if niche:
        context_parts.append(f"Creator's niche: {niche}")
    if video_analysis:
        context_parts.append(f"Video analysis data: {json.dumps(video_analysis, indent=2, default=str)}")

    context = "\n\n".join(context_parts)

    return f"""Completely rewrite this Instagram Reel to maximize its viral potential. Transform it from mediocre to scroll-stopping.

{context}

Your rewrite must address:
1. **New Hook** — A completely new opening that scores 80+ on hook strength. Use a proven hook framework (question, bold claim, story open, "POV:", "This is your sign to...", etc.)
2. **Hook Psychology** — Explain which psychological trigger the new hook uses and why it works for this niche
3. **New Caption** — Rewrite the entire caption with better structure, CTA, and engagement bait
4. **New Structure** — Provide a second-by-second content structure for the video
5. **Viral Potential** — Estimate the viral score improvement

Return ONLY this JSON:
{{
    "new_hook": "The new hook text (first thing viewers see/hear)",
    "hook_psychology": "Which psychological trigger this uses and why it's effective",
    "new_caption": "Complete rewritten caption with emojis, line breaks, and CTA",
    "new_structure": [
        {{"timestamp_range": "0:00-0:03", "content": "What happens in this segment", "why": "Why this is placed here"}},
        {{"timestamp_range": "0:03-0:08", "content": "Next segment", "why": "Strategic reason"}},
        {{"timestamp_range": "0:08-0:15", "content": "Next segment", "why": "Strategic reason"}},
        {{"timestamp_range": "0:15-0:25", "content": "Conclusion/CTA", "why": "Strategic reason"}}
    ],
    "viral_potential_after": 0-100,
    "what_changed": "Summary of all changes made and their expected impact on performance"
}}

Be bold with changes. Don't tweak — transform. The rewrite should feel like a completely different (better) reel while keeping the same core message."""
