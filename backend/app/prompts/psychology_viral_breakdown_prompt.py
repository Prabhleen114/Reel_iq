"""ReelIQ — Psychology Viral Breakdown Prompt Template"""
import json
from typing import Dict, Any


def build_psychology_breakdown_prompt(
    caption: str,
    metrics: Dict[str, Any],
) -> str:
    """
    Build the prompt for psychological breakdown of a viral reel.

    Input: A specific viral reel's caption + metrics
    Output: Deep psychological analysis of why it went viral
    """
    metrics_str = json.dumps(metrics, default=str)

    return f"""Perform a deep psychological breakdown of why this Instagram Reel went viral. Analyze it like a behavioral scientist studying social media engagement.

Caption: "{caption}"

Performance metrics: {metrics_str}

Analyze the following aspects:

1. **Psychological Triggers** — What specific cognitive biases or psychological principles are at play? (FOMO, social proof, curiosity gap, loss aversion, identity signaling, etc.)
2. **Emotion Activated** — What primary emotion does this content activate in the viewer?
3. **Shareability Reason** — Why would someone share this? What social currency does it provide?
4. **Hook Archetype** — Classify the hook style (Question, Bold Claim, Story, POV, Transformation, etc.)
5. **Algorithm Signals** — Why did the algorithm push this? What engagement signals did it generate?

Return ONLY this JSON:
{{
    "psychological_triggers": [
        {{"trigger": "Name of trigger", "how_used": "How this content specifically uses this trigger"}}
    ],
    "emotion_activated": "Primary emotion (e.g., 'curiosity + aspiration')",
    "shareability_reason": "Why someone would share this with friends",
    "hook_archetype": "The hook framework used (e.g., 'Curiosity Gap + Specificity')",
    "why_algorithm_pushed_it": "Specific engagement signals that the algorithm rewarded"
}}

Go deep. Don't just name the triggers — explain exactly how they're used in THIS specific piece of content. Reference specific words, phrases, or structural choices from the caption."""
