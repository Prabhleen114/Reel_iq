"""ReelIQ — Competitor Analysis Prompt Template"""
import json
from typing import Optional, List, Dict, Any


def build_competitor_analysis_prompt(
    competitor_username: str,
    their_posts: Optional[List[Dict[str, Any]]] = None,
    your_stats: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build the prompt for competitor analysis.

    Input: Competitor username, their top posts data
    Output: Comprehensive competitive intelligence
    """
    posts_ctx = ""
    if their_posts:
        posts_ctx = f"\n\nTheir content data:\n{json.dumps(their_posts, indent=2, default=str)}"

    your_ctx = ""
    if your_stats:
        your_ctx = f"\n\nYour account stats for comparison:\n{json.dumps(your_stats, default=str)}"

    return f"""Analyze the Instagram account @{competitor_username} as a competitor and provide actionable competitive intelligence.
{posts_ctx}
{your_ctx}

Provide a thorough competitive analysis covering:

1. **Their Strengths** — What are they doing well? What content patterns work for them?
2. **Their Weaknesses** — Where are they falling short? What are they NOT doing?
3. **Content Gaps You Can Fill** — What topics/formats are they missing that you could own?
4. **Hook Styles They Use** — Categorize their opening hook patterns
5. **Posting Frequency** — How often do they post? Is it optimal?
6. **Engagement Rate** — Calculate their average engagement rate
7. **Steal-Worthy Ideas** — What specific content ideas can you adapt (not copy) from them?

Return ONLY this JSON:
{{
    "their_strengths": ["Specific strength with evidence"],
    "their_weaknesses": ["Specific weakness with evidence"],
    "content_gaps_you_can_fill": ["Gap 1 with explanation", "Gap 2"],
    "hook_styles_they_use": ["Style 1: description + example", "Style 2"],
    "posting_frequency": "X posts per week/day",
    "avg_engagement_rate": 0.0,
    "steal_these_ideas": ["Idea 1: specific adaptation suggestion", "Idea 2"]
}}

Be strategic, not petty. The goal is to learn from them and find angles they're missing. Every suggestion should be actionable and specific to this niche."""
