"""Generate a synthetic noisy raw_conversations.jsonl dataset.

This script creates 100 conversations with injected quality issues in ~35% of them.
Run:
    python generate_raw.py

It writes:
- part_a/raw_conversations.jsonl
- part_a/injected_issues.md (summary of where issues were injected)
"""

import json
import random
from pathlib import Path
from typing import Any, Dict, List

OUT_PATH = Path(__file__).parent / "raw_conversations.jsonl"
ISSUES_PATH = Path(__file__).parent / "injected_issues.md"

LANGUAGES = ["hindi", "hinglish", "english"]
OUTCOMES = ["payment_committed", "callback_scheduled", "escalated", "no_resolution"]

HINDI_EXAMPLES = [
    "Namaste, main apka EMI collection agent hoon.",
    "Aapka due amount Rs 4500 hai.",
    "Kripya aaj payment kar dein.",
    "Aapko callback schedule karna hai?",
]

HINGLISH_EXAMPLES = [
    "Hello sir, aapka EMI due hai.",
    "Aap online ya cash dono tarike se pay kar sakte hain.",
    "Please confirm kar dijiye.",
    "Aapka account number kya hai?",
]

ENGLISH_EXAMPLES = [
    "Hi, this is a reminder for your upcoming EMI payment.",
    "Can I help you with payment options?",
    "The due date is tomorrow.",
    "Would you like to schedule a callback?",
]

GARBLED_SNIPPETS = [
    "Ã©", "Ã±", "\ufffd", "\uFFFD", "â€“", "Ã¢â‚¬â€œ",
]


def _sample_turns(language: str) -> List[Dict[str, Any]]:
    # Start with agent greeting and customer response
    if language == "hindi":
        samples = HINDI_EXAMPLES
    elif language == "hinglish":
        samples = HINGLISH_EXAMPLES
    else:
        samples = ENGLISH_EXAMPLES

    turns = []
    for i in range(random.randint(2, 6)):
        role = "agent" if i % 2 == 0 else "customer"
        text = random.choice(samples)
        turns.append({"role": role, "text": text})
    return turns


def _inject_issue(conv: Dict[str, Any], issue: str) -> None:
    """Apply a single issue injection to a conversation in place."""
    if issue == "blank_turn":
        # Make a random turn blank or whitespace
        turns = conv["turns"]
        if turns:
            idx = random.randrange(len(turns))
            turns[idx]["text"] = "   "

    elif issue == "duplicate_turn":
        turns = conv["turns"]
        if len(turns) >= 2:
            idx = random.randrange(len(turns) - 1)
            turns.insert(idx + 1, turns[idx].copy())

    elif issue == "short_conversation":
        conv["turns"] = conv["turns"][:1]

    elif issue == "bad_metadata":
        # randomly choose between null outcome or negative duration
        if random.random() < 0.5:
            conv["metadata"]["outcome"] = None
        else:
            conv["metadata"]["call_duration_seconds"] = -10

    elif issue == "language_mismatch":
        # flip language label but keep text opposite
        conv["language"] = "hindi" if conv["language"] == "english" else "english"

    elif issue == "garbled_text":
        turns = conv["turns"]
        if turns:
            idx = random.randrange(len(turns))
            turns[idx]["text"] = turns[idx]["text"] + " " + random.choice(GARBLED_SNIPPETS)

    elif issue == "missing_fields":
        # remove metadata or turns completely
        if random.random() < 0.5:
            conv.pop("metadata", None)
        else:
            conv.pop("turns", None)


def main() -> None:
    random.seed(1234)
    conversations: List[Dict[str, Any]] = []
    injected: List[str] = []

    # create 100 conversations
    for i in range(1, 101):
        conv_id = f"conv_{i:03d}"
        language = random.choice(LANGUAGES)
        turns = _sample_turns(language)
        metadata = {
            "call_duration_seconds": random.randint(30, 600),
            "outcome": random.choice(OUTCOMES),
        }
        conv = {
            "conversation_id": conv_id,
            "language": language,
            "turns": turns,
            "metadata": metadata,
        }
        conversations.append(conv)

    # Inject issues into ~35% of conversations
    issue_types = [
        "blank_turn",
        "duplicate_turn",
        "short_conversation",
        "bad_metadata",
        "language_mismatch",
        "garbled_text",
        "missing_fields",
    ]

    num_issues = int(len(conversations) * 0.35)
    chosen_indices = random.sample(range(len(conversations)), num_issues)

    for idx in chosen_indices:
        conv = conversations[idx]
        issue = random.choice(issue_types)
        _inject_issue(conv, issue)
        injected.append(f"{conv['conversation_id']}: {issue}")

    # Write raw JSONL
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for conv in conversations:
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")

    # Document injections
    with ISSUES_PATH.open("w", encoding="utf-8") as f:
        f.write("# Injected issues (approx 35% of conversations)\n\n")
        for line in injected:
            f.write(f"- {line}\n")

    print(f"Wrote {len(conversations)} conversations to {OUT_PATH}")
    print(f"Logged injections to {ISSUES_PATH}")


if __name__ == "__main__":
    main()
