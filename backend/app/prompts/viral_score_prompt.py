"""ReelIQ — Viral Score Prediction Prompt Template"""
import json
from typing import Optional, List, Dict, Any


def build_viral_score_prompt(
    hook: str,
    caption: str,
    niche: Optional[str] = None,
    hashtags: Optional[List[str]] = None,
    account_stats: Optional[Dict[str, Any]] = None,
    video_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build the prompt for viral score prediction.

    Input: Video metadata, hook, caption, niche, account stats
    Output: Viral score with confidence, key signals, missing elements
    """
    context_parts = [
        f'Hook: "{hook}"',
        f'Caption: "{caption}"',
    ]

    if niche:
        context_parts.append(f"Niche: {niche}")
    if hashtags:
        context_parts.append(f"Hashtags: {', '.join(['#' + h for h in hashtags])}")
    if account_stats:
        context_parts.append(f"Account stats: {json.dumps(account_stats, default=str)}")
    if video_metadata:
        context_parts.append(f"Video metadata: {json.dumps(video_metadata, default=str)}")

    context = "\n".join(context_parts)

    return f"""Predict the viral potential of this Instagram Reel based on the content signals provided.

{context}

Score this reel's viral potential from 0-100 using these weighted criteria:

1. **Hook Strength** (30% weight): Does the hook stop the scroll? Is it curiosity-driven?
2. **Content Value** (20% weight): Does the caption deliver value, entertainment, or emotion?
3. **Engagement Triggers** (15% weight): Are there CTAs, questions, or controversy that prompt comments?
4. **Shareability** (15% weight): Would someone share this? Is it relatable, funny, or useful enough?
5. **Niche Relevance** (10% weight): Does it match what performs in this niche?
6. **Technical Optimization** (10% weight): Hashtags, caption length, format signals

Return ONLY this JSON:
{{
    "viral_score": 0-100,
    "confidence": "low" | "medium" | "high",
    "key_signals": [
        {{"signal": "Name of positive signal", "impact": "positive" | "negative", "detail": "Explanation"}},
        {{"signal": "Another signal", "impact": "positive" | "negative", "detail": "Explanation"}}
    ],
    "missing_elements": ["Element 1 that would boost virality", "Element 2"],
    "predicted_reach_multiplier": 1.0-10.0
}}

A score of 80+ means high viral potential. 50-79 is average. Below 50 will likely underperform. The reach multiplier estimates how many times more reach than their average post this could get.

Be precise and critical. Don't inflate scores. If the content is mediocre, say so."""
