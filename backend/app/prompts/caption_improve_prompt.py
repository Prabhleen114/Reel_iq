"""ReelIQ — Caption Improvement Prompt Template"""
import json
from typing import List, Optional


def build_caption_improve_prompt(
    caption: str,
    niche: Optional[str] = None,
    top_captions: Optional[List[str]] = None,
) -> str:
    """
    Build the prompt for improving a caption.

    Input: Original caption, niche, top performing captions from account
    Output: Improved caption with CTA, hashtags, tone analysis
    """
    niche_ctx = f"\nCreator's niche: {niche}" if niche else ""
    top_ctx = ""
    if top_captions:
        top_ctx = f"\n\nTheir top-performing captions for reference:\n" + "\n---\n".join(top_captions[:5])

    return f"""Improve this Instagram Reel caption to maximize engagement, saves, and shares.
{niche_ctx}

Original caption:
\"{caption}\"
{top_ctx}

Requirements for the improved caption:
1. **Hook Line** — First line must stop the scroll (emoji + pattern interrupt)
2. **Value Delivery** — 2-3 lines of actionable/entertaining content
3. **Social Proof or Specificity** — Include numbers, results, or relatable experiences
4. **CTA (Call to Action)** — End with a specific action (save, share, comment a specific word)
5. **Hashtag Strategy** — 15 relevant hashtags mixing high-volume (500K+), medium (50K-500K), and niche-specific tags

Return ONLY this JSON:
{{
    "improved_caption": "Full improved caption with line breaks",
    "cta_added": "The specific CTA used and why it works",
    "hashtags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10", "tag11", "tag12", "tag13", "tag14", "tag15"],
    "tone": "The tone used (e.g., 'authoritative + relatable', 'provocative + educational')",
    "why_better": "2-3 sentences explaining what specific improvements were made and their expected impact"
}}

The improved caption should feel natural, not robotic. Match the creator's voice but elevate it. Do NOT use generic CTAs like 'follow for more' — be creative and specific."""
