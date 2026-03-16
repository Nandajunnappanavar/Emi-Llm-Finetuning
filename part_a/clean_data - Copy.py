"""Clean raw conversation JSONL into training-ready dataset.

This script reads part_a/raw_conversations.jsonl and writes:
- part_a/cleaned_conversations.jsonl
- part_a/rejected_conversations.jsonl

Rejected conversations include a `rejection_reason` explaining why they were removed.

Usage:
    python clean_data.py
"""

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

RAW_PATH = Path(__file__).parent / "raw_conversations.jsonl"
CLEAN_PATH = Path(__file__).parent / "cleaned_conversations.jsonl"
REJECT_PATH = Path(__file__).parent / "rejected_conversations.jsonl"

VALID_LANGUAGES = {"hindi", "hinglish", "english"}
VALID_OUTCOMES = {"payment_committed", "callback_scheduled", "escalated", "no_resolution"}

# A small set of common English tokens to help flag language mismatches.
_ENGLISH_HINT_WORDS = {
    "payment",
    "emi",
    "due",
    "call",
    "please",
    "thank",
    "ok",
    "yes",
    "no",
    "customer",
    "agent",
    "balance",
    "account",
    "pay",
    "late",
    "today",
    "tomorrow",
    "sorry",
}


def _is_blank_text(text: Any) -> bool:
    if not isinstance(text, str):
        return True
    return text.strip() == ""


def _has_garbage(text: str) -> bool:
    # Common replacement characters and mojibake fragments
    if "�" in text or "\uFFFD" in text:
        return True
    # Some mojibake sequences from incorrect UTF-8/latin-1 decoding
    if "Ã" in text and "�" in text:
        return True
    return False


def _detect_language_mismatch(language: str, turns: List[Dict[str, Any]]) -> Optional[str]:
    """Boolean heuristic: if a conversation is labeled one language but text seems to be another.

    We treat:
      - Hindi/Hinglish should contain some Devanagari characters.
      - English should not contain Devanagari.
      - If the label is hindi/hinglish but turns are overwhelmingly English, flag.
    """

    text = " ".join(turn.get("text", "") for turn in turns if isinstance(turn.get("text"), str))
    has_devanagari = any("\u0900" <= ch <= "\u097F" for ch in text)

    if language in {"hindi", "hinglish"} and not has_devanagari:
        # If there are none of the Devanagari chars, and we see lots of English hints,
        # it is likely mislabeled (especially for "hindi").
        words = {w.lower().strip(".,!?;:") for w in text.split()}
        hits = words.intersection(_ENGLISH_HINT_WORDS)
        if len(hits) >= 2:
            return f"Language mismatch: labeled {language} but text appears English (found hints {sorted(hits)})"

    if language == "english" and has_devanagari:
        return "Language mismatch: labeled english but contains Devanagari characters"

    return None


def _validate_metadata(metadata: Any) -> Optional[str]:
    if not isinstance(metadata, dict):
        return "metadata must be an object"

    duration = metadata.get("call_duration_seconds")
    if not isinstance(duration, (int, float)) or duration < 0:
        return f"invalid call_duration_seconds: {duration!r}"

    outcome = metadata.get("outcome")
    if outcome not in VALID_OUTCOMES:
        return f"invalid outcome: {outcome!r}"

    return None


def _clean_turns(turns: Any) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Return (cleaned_turns, issues) where issues are found reasons (not fatal)."""
    cleaned: List[Dict[str, Any]] = []
    issues: List[str] = []

    if not isinstance(turns, list):
        return [], ["turns is not a list"]

    prev_turn: Optional[Dict[str, Any]] = None
    for idx, turn in enumerate(turns):
        if not isinstance(turn, dict):
            issues.append(f"turn[{idx}] is not an object")
            continue

        role = turn.get("role")
        text = turn.get("text")

        if role not in {"agent", "customer"}:
            issues.append(f"turn[{idx}] has invalid role: {role!r}")
            continue

        if _is_blank_text(text):
            issues.append(f"turn[{idx}] is blank")
            continue

        if not isinstance(text, str):
            issues.append(f"turn[{idx}] text is not a string")
            continue

        if _has_garbage(text):
            issues.append(f"turn[{idx}] has garbled characters")
            continue

        if prev_turn is not None and prev_turn.get("role") == role and prev_turn.get("text") == text:
            issues.append(f"duplicate consecutive turn at index {idx}")
            continue

        cleaned.append({"role": role, "text": text})
        prev_turn = turn

    return cleaned, issues


def _validate_conversation(conv: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validates and returns (is_valid, rejection_reason, cleaned_conversation)."""
    if not isinstance(conv, dict):
        return False, "conversation is not an object", None

    conv_id = conv.get("conversation_id")
    if not isinstance(conv_id, str) or not conv_id.strip():
        return False, "missing or invalid conversation_id", None

    language = conv.get("language")
    if language not in VALID_LANGUAGES:
        return False, f"invalid language label: {language!r}", None

    turns = conv.get("turns")
    cleaned_turns, turn_issues = _clean_turns(turns)

    if len(cleaned_turns) < 2:
        all_issues = "; ".join(turn_issues) if turn_issues else "fewer than 2 valid turns"
        return False, f"invalid turns: {all_issues}", None

    metadata = conv.get("metadata")
    meta_err = _validate_metadata(metadata)
    if meta_err:
        return False, meta_err, None

    lang_err = _detect_language_mismatch(language, cleaned_turns)
    if lang_err:
        return False, lang_err, None

    # Passed all checks; return normalized conversation
    cleaned = {
        "conversation_id": conv_id,
        "language": language,
        "turns": cleaned_turns,
        "metadata": metadata,
    }
    return True, None, cleaned


def main() -> None:
    raw_path = RAW_PATH
    if not raw_path.exists():
        raise FileNotFoundError(f"Missing {raw_path}. Run data generation first.")

    cleaned = []
    rejected = []

    with raw_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                conv = json.loads(line)
            except json.JSONDecodeError as e:
                rejected.append({"raw_line": line, "rejection_reason": f"invalid JSON: {e}"})
                continue

            ok, reason, cleaned_conv = _validate_conversation(conv)
            if ok and cleaned_conv:
                cleaned.append(cleaned_conv)
            else:
                rejected.append({**conv, "rejection_reason": reason})

    with CLEAN_PATH.open("w", encoding="utf-8") as f:
        for conv in cleaned:
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")

    with REJECT_PATH.open("w", encoding="utf-8") as f:
        for conv in rejected:
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")

    print(f"Wrote {len(cleaned)} cleaned conversations to {CLEAN_PATH}")
    print(f"Wrote {len(rejected)} rejected conversations to {REJECT_PATH}")


if __name__ == "__main__":
    main()
