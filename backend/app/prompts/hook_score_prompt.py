"""ReelIQ — Hook Score Prompt Template"""


def build_hook_score_prompt(hook: str, niche: str = None) -> str:
    """
    Build the prompt for scoring a hook.

    Input: Hook text or first-3-second transcript
    Output: Score, verdict, improvements, psychology analysis
    """
    niche_context = f"\nThis creator's niche: {niche}" if niche else ""

    return f"""Score this Instagram Reel hook on a scale of 0-100 based on its ability to stop the scroll and retain viewers for the first 3 seconds.
{niche_context}

Hook: "{hook}"

Evaluate against these criteria:
1. **Pattern Interrupt** (0-25): Does it break the scroll pattern? Unexpected visual, statement, or question?
2. **Curiosity Gap** (0-25): Does it create an information gap the viewer NEEDS to close?
3. **Emotional Trigger** (0-25): Does it trigger curiosity, fear, desire, outrage, or surprise?
4. **Specificity** (0-25): Does it use specific numbers, names, or details instead of vague claims?

A score of 80+ = viral hook potential. 60-79 = solid but improvable. Below 60 = likely causing swipe-aways.

Return ONLY this JSON:
{{
    "score": 0-100,
    "verdict": "One-line verdict on the hook quality",
    "why_it_works_or_fails": "2-3 sentence analysis of what makes this hook effective or weak",
    "improved_versions": [
        "Rewritten hook version 1 (more curiosity)",
        "Rewritten hook version 2 (more emotional)",
        "Rewritten hook version 3 (more specific)"
    ],
    "psychology_trigger_used": "Name the primary psychological trigger (or absence of one)"
}}

Be ruthlessly honest. If the hook is weak, say so and explain exactly why. Every improved version must be measurably better than the original."""
