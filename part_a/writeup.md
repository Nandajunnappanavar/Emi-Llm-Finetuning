# Part A Writeup

## Assumptions

- The dataset should include at least 100 conversations with the full range of labels (language/outcome).
- Quality issues are injected into ~35% of conversations and will be rejected during cleaning.
- A "training-ready" conversation must have:
  - A non-empty `conversation_id`.
  - A valid `language` label (`hindi`, `hinglish`, or `english`).
  - At least 2 non-empty turns (after removing blanks and duplicate consecutive turns).
  - Valid `metadata` with non-negative `call_duration_seconds` and a known `outcome`.

## Hardest issue to detect programmatically

Language mismatch is the hardest to detect without a full language detection model. I implemented a simple heuristic based on the presence of Devanagari characters and a small English keyword list. This will catch obvious cases but can still have false positives/negatives.

## Scaling to 100,000 conversations

With much larger data, I would:

- Use streaming processing (read/write line-by-line) instead of loading all data into memory.
- Add logging and progress reporting so long jobs can be monitored.
- Write the pipeline as a reusable library function and add unit tests.
- Consider using Apache Beam / Spark if the data is extremely large.
