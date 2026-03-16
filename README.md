# ML Intern Take-Home Assignment

This repository contains a completed take-home assignment covering:

- **Part A:** Data cleaning & quality analysis of noisy call center conversations
- **Part B:** A minimal LoRA finetuning pipeline for a small conversational LLM

## Structure

```
repo/
├── README.md
├── requirements.txt
├── part_a/
│   ├── raw_conversations.jsonl
│   ├── cleaned_conversations.jsonl
│   ├── rejected_conversations.jsonl
│   ├── clean_data.py
│   ├── quality_report.py
│   ├── generate_raw.py
│   ├── injected_issues.md
│   └── writeup.md
└── part_b/
    ├── finetune.ipynb
    ├── eval.py
    └── finetune_writeup.md
```

## Getting Started

### Part A (Data Cleaning)

1. Install Python dependencies (none required beyond the standard library).
2. Generate the raw dataset:
   ```bash
   python part_a/generate_raw.py
   ```
3. Run the cleaning pipeline:
   ```bash
   python part_a/clean_data.py
   ```
4. View the quality report:
   ```bash
   python part_a/quality_report.py
   ```

### Part B (Finetuning)

1. Use Colab (T4) to run `part_b/finetune.ipynb`.
2. Optionally run the evaluation script:
   ```bash
   python part_b/eval.py
   ```

## Notes

- `clean_data.py` is defensive and will reject conversations with missing fields, invalid metadata, blank turns, or language mismatches.
- The finetuning notebook is designed as a minimal end-to-end example; it trains for just one epoch on a small subset of data for quick iteration.
