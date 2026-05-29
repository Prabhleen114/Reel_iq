"""ReelIQ — Account Analysis Prompt Template"""
import json
from typing import List, Dict, Any


def build_account_analysis_prompt(reels_data: List[Dict[str, Any]]) -> str:
    """
    Build the prompt for full account analysis.

    Input: All reels JSON (views, likes, captions, posting times)
    Output: Comprehensive account analysis with strengths, weaknesses,
            niche, viral patterns, posting times, etc.
    """
    reels_summary = json.dumps(reels_data, indent=2, default=str)

    return f"""Analyze this Instagram creator's complete reel performance data and provide a comprehensive strategic analysis.

Here is their reel data (most recent first):
{reels_summary}

Analyze ALL of the following and return a structured JSON response:

1. **Strengths** — What content patterns consistently perform well? Look at views, engagement rate (likes+comments+saves/views), and shares.
2. **Weaknesses** — What patterns consistently underperform? What mistakes are they making?
3. **Niche Identification** — Based on captions, hashtags, and content themes, what is their primary niche?
4. **Content Categories** — Group their content into categories and score each category's performance.
5. **Viral Patterns** — What traits do their top 20% posts share? Look at hook style, posting time, caption length, hashtag strategy.
6. **Best Posting Times** — Based on their highest-performing posts, when should they post?
7. **Top Hashtags** — Which hashtags correlate with highest reach?
8. **Repetition Flags** — Are they repeating the same content, hooks, or formats too often?
9. **Growth Trajectory** — Based on chronological performance trends, are they growing, declining, or flat?

Return ONLY this JSON structure:
{{
    "strengths": [
        {{"pattern": "string", "evidence": "string with specific numbers", "recommendation": "string"}}
    ],
    "weaknesses": [
        {{"pattern": "string", "evidence": "string with specific numbers", "fix": "string"}}
    ],
    "niche": "string",
    "content_categories": [
        {{"name": "string", "performance_score": 0-100, "post_count": number, "avg_views": number}}
    ],
    "viral_patterns": [
        {{"trait": "string", "frequency": "string", "avg_views": number}}
    ],
    "best_posting_times": [
        {{"day": "string", "hour": number, "avg_engagement": number}}
    ],
    "top_hashtags": [
        {{"tag": "string", "avg_reach": number, "usage_count": number}}
    ],
    "repetition_flags": ["string"],
    "growth_trajectory": "up" | "down" | "flat"
}}

Be specific. Use actual numbers from their data. Don't give generic advice — every recommendation must reference specific posts or patterns from their data."""
