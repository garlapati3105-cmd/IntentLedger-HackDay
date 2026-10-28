"""
IntentLedger – Prompt templates for baseline and improved extraction.

Baseline: straightforward extraction of the final state.
Improved: explicit instruction-tracking with corrections, rejections,
          partial updates, cancellations, and unresolved ambiguity.
"""

BASELINE_SYSTEM_PROMPT = """You are an AI assistant that extracts the final intended state from a conversation.

Given a multi-turn conversation transcript, extract the final state as a JSON object.
Only return a valid JSON object — no explanation, no markdown fences.

The JSON must include every field that is relevant to the user's final intent.
If the user expressed uncertainty, still extract your best guess for each field.
"""

IMPROVED_SYSTEM_PROMPT = """You are a precise intent-tracking AI that extracts the **final, confirmed intended state** from a multi-turn conversation.

Follow these rules strictly before writing any JSON:

1. CORRECTIONS: If the user overrides an earlier value, use ONLY the most recent value. Discard the original.
2. REJECTED SUGGESTIONS: If the assistant proposed something and the user said no (or any equivalent rejection), that suggestion must NOT appear in the output.
3. PARTIAL UPDATES: When the user says "keep everything else the same" or similar, retain all unchanged fields and update only the specified ones.
4. CANCELLATIONS: If the user cancels an earlier action, set the action to the cancellation (e.g. action = "cancel_subscription") and add status = "cancelled". Do not represent the original un-cancelled intent as active.
5. AMBIGUITY: If the user has NOT confirmed a specific value for a field (e.g. said "I'm not sure" or left a detail vague), set that field's value to the string "AMBIGUOUS" and add "clarification_needed": true plus a "clarification_question" field stating what you would ask next.

Return ONLY a valid JSON object with no markdown fences or explanations.
The JSON must accurately reflect the final, confirmed state after applying all of the above rules.
"""

EXTRACTION_USER_TEMPLATE = """
Here is the conversation transcript:

{transcript}

Extract the final intended state as a JSON object. Apply all instruction-tracking rules.
Return ONLY valid JSON.
"""


def format_transcript(conversation: list[dict]) -> str:
    """Format a conversation list into a readable transcript string."""
    lines = []
    for turn in conversation:
        role = turn["role"].upper()
        lines.append(f"{role}: {turn['content']}")
    return "\n\n".join(lines)


def build_extraction_prompt(conversation: list[dict], mode: str) -> tuple[str, str]:
    """
    Build system + user prompt for extraction.

    Args:
        conversation: list of {role, content} dicts
        mode: 'baseline' or 'improved'

    Returns:
        (system_prompt, user_prompt)
    """
    if mode == "baseline":
        system = BASELINE_SYSTEM_PROMPT
    elif mode == "improved":
        system = IMPROVED_SYSTEM_PROMPT
    else:
        raise ValueError(f"Unknown mode: {mode!r}. Use 'baseline' or 'improved'.")

    transcript = format_transcript(conversation)
    user = EXTRACTION_USER_TEMPLATE.format(transcript=transcript)
    return system, user
