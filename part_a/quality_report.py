"""Generate quality report for raw/cleaned conversation datasets.

Usage:
    python quality_report.py

This script reads:
- part_a/raw_conversations.jsonl
- part_a/cleaned_conversations.jsonl
- part_a/rejected_conversations.jsonl

and prints summary statistics.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

RAW_PATH = Path(__file__).parent / "raw_conversations.jsonl"
CLEAN_PATH = Path(__file__).parent / "cleaned_conversations.jsonl"
REJECT_PATH = Path(__file__).parent / "rejected_conversations.jsonl"


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _safe_len_turns(conv: Dict[str, Any]) -> int:
    turns = conv.get("turns")
    if isinstance(turns, list):
        return len(turns)
    return 0


def _distribution(items: Iterable[Any]) -> Counter:
    return Counter(items)


def print_distribution(name: str, counter: Counter, total: int) -> None:
    print(name)
    for k, v in sorted(counter.items(), key=lambda x: (-x[1], str(x[0]))):
        pct = 100 * v / total if total else 0
        print(f"  {k}: {v} ({pct:.1f}%)")
    print()


def main() -> None:
    raw = _read_jsonl(RAW_PATH)
    clean = _read_jsonl(CLEAN_PATH)
    rejected = _read_jsonl(REJECT_PATH)

    print("=== Summary ===")
    print(f"Raw conversations:     {len(raw)}")
    print(f"Cleaned conversations: {len(clean)}")
    print(f"Rejected conversations:{len(rejected)}")
    print()

    # Rejection reasons
    reasons = [c.get("rejection_reason", "<none>") for c in rejected]
    reason_counts = Counter(reasons)
    print_distribution("Rejection reasons", reason_counts, len(rejected))

    # Language distribution
    raw_langs = [c.get("language") for c in raw]
    clean_langs = [c.get("language") for c in clean]
    print_distribution("Language distribution (raw)", Counter(raw_langs), len(raw))
    print_distribution("Language distribution (clean)", Counter(clean_langs), len(clean))

    # Outcomes
    raw_outcomes = [c.get("metadata", {}).get("outcome") for c in raw]
    clean_outcomes = [c.get("metadata", {}).get("outcome") for c in clean]
    print_distribution("Outcome distribution (raw)", Counter(raw_outcomes), len(raw))
    print_distribution("Outcome distribution (clean)", Counter(clean_outcomes), len(clean))

    # Turns per convo
    raw_turns = [_safe_len_turns(c) for c in raw]
    clean_turns = [_safe_len_turns(c) for c in clean]
    def _stats(vals: List[int]) -> Tuple[float, int, int]:
        if not vals:
            return 0.0, 0, 0
        return sum(vals) / len(vals), min(vals), max(vals)

    raw_avg, raw_min, raw_max = _stats(raw_turns)
    clean_avg, clean_min, clean_max = _stats(clean_turns)
    print("Turns per conversation")
    print(f"  Raw:   mean={raw_avg:.2f}, min={raw_min}, max={raw_max}")
    print(f"  Clean: mean={clean_avg:.2f}, min={clean_min}, max={clean_max}")

    # Additional stats: average call duration
    def _durations(convs: List[Dict[str, Any]]) -> List[float]:
        out = []
        for c in convs:
            m = c.get("metadata")
            if isinstance(m, dict):
                d = m.get("call_duration_seconds")
                if isinstance(d, (int, float)):
                    out.append(d)
        return out

    raw_durs = _durations(raw)
    clean_durs = _durations(clean)
    raw_avg_dur = sum(raw_durs) / len(raw_durs) if raw_durs else 0.0
    clean_avg_dur = sum(clean_durs) / len(clean_durs) if clean_durs else 0.0
    print()
    print(f"Avg call duration (raw):   {raw_avg_dur:.1f}s")
    print(f"Avg call duration (clean): {clean_avg_dur:.1f}s")


if __name__ == "__main__":
    main()
