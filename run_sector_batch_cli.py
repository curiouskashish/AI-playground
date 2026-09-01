#!/usr/bin/env python3
"""
CLI script for sector-only batch assignment on very large CSV files (e.g. 54,000+ rows).
Run from the terminal to avoid browser timeouts. Uses chunked processing and in-process
API calls (no Flask). Recommended for M2 MacBook: run in tmux/screen for long jobs.

Usage:
  python run_sector_batch_cli.py input.csv --api-key YOUR_OPENAI_KEY [options]
  python run_sector_batch_cli.py input.csv --api-key $(cat .env | grep OPENAI) --chunk-size 3000 --max-concurrent 15

Options:
  --api-key       OpenAI API key (required, or set OPENAI_API_KEY env var)
  --output        Output CSV path (default: sector_assignment_<timestamp>.csv in ./results)
  --chunk-size    Rows per chunk (default: 3000). Lower = less memory, more chunks.
  --max-concurrent Concurrent API requests per chunk (default: 15)
"""

import argparse
import os
import sys
from datetime import datetime

import pandas as pd

# Add project root so batch_processor can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from batch_processor import (
    run_batch_evaluation,
    parse_results_to_dataframe_sector_only,
)

SECTOR_ONLY_PROMPT = """You are an expert evaluator for Udhyam Learning Foundation's entrepreneurial mindsets development program conducted in government schools across India.

## CONTEXT
- Students are from government schools in India (typically ages 13-17)
- Students have access to limited resources: seed funding of approximately ₹5,000 to ₹10,000 INR
- Expected project execution timeline: 2-3 months
- Ideas should be practical for school-going learners to implement alongside their studies
- Students are expected to mention either the problem they are solving with business idea or clearly articulated business idea. A lot of details around business idea and execution plan are not expected in this submission.

IMPORTANT: Be lenient in your evaluation considering the expectations from students in idea submissions.
---

### 1. SECTOR CLASSIFICATION
Classify the business idea into ONE of the following 9 sectors. Choose the MOST appropriate sector based on the primary nature of the business:

| Sector | Description |
|--------|-------------|
| Art and crafts | Handmade items, paintings, decorative products, handicrafts, creative artwork |
| Agriculture | Farming, gardening, plant nursery, organic produce, agricultural tools/services |
| Education and social cause | Tutoring, teaching aids, social impact initiatives, community welfare services |
| Food | Food products, cooking services, tiffin services, snacks, beverages, catering |
| Personal care and hygiene | Health related, Soaps, sanitizers, beauty products, hygiene kits, grooming services |
| Sustainable environment | Eco-friendly products, waste management, recycling, renewable solutions (NOT art/crafts) |
| Tourism and hospitality | Travel guides, local tours, hospitality services, cultural experiences |
| Technology driven solutions | Apps, websites, digital services, tech-based problem solving |
| Others | Ideas that do not clearly fit into any of the above 8 categories |

OUTPUT FORMAT: Respond with only a JSON object containing the sector key. Example: {"sector": "Food"}. Provide only valid JSON, no additional text."""


def main():
    parser = argparse.ArgumentParser(
        description="Batch sector assignment for large CSV (business_idea -> sector)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input_csv", help="Path to input CSV with business_idea column")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY"), help="OpenAI API key")
    parser.add_argument("--output", "-o", help="Output CSV path (default: results/sector_assignment_<timestamp>.csv)")
    parser.add_argument("--chunk-size", type=int, default=3000, help="Rows per chunk (default: 3000)")
    parser.add_argument("--max-concurrent", type=int, default=15, help="Concurrent requests per chunk (default: 15)")
    args = parser.parse_args()

    if not args.api_key:
        print("Error: --api-key required or set OPENAI_API_KEY", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.input_csv):
        print(f"Error: Input file not found: {args.input_csv}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(args.input_csv)
    if "business_idea" not in df.columns:
        print("Error: CSV must have a 'business_idea' column", file=sys.stderr)
        sys.exit(1)

    rows = []
    for idx, row in df.iterrows():
        idea = str(row.get("business_idea", "")).strip()
        rows.append((idx, idea, row.to_dict()))

    total = len(rows)
    chunk_size = max(500, min(10000, args.chunk_size))
    max_concurrent = max(1, min(30, args.max_concurrent))

    all_sectors = [None] * total
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    def progress_cb(completed, total_chunk):
        print(f"  Chunk progress: {completed}/{total_chunk}", end="\r", flush=True)

    num_chunks = (total + chunk_size - 1) // chunk_size
    print(f"Total rows: {total}. Chunk size: {chunk_size}, max_concurrent: {max_concurrent}. Chunks: {num_chunks}")

    for start in range(0, total, chunk_size):
        end = min(start + chunk_size, total)
        chunk = rows[start:end]
        ideas_list = [t[1] for t in chunk]
        chunk_num = start // chunk_size + 1
        print(f"\nChunk {chunk_num}/{num_chunks} (rows {start}-{end})...")
        batch_results = run_batch_evaluation(
            ideas_list=ideas_list,
            system_prompt=SECTOR_ONLY_PROMPT,
            api_key=args.api_key,
            max_concurrent=max_concurrent,
            progress_callback=progress_cb,
            user_message_prefix="Assign a sector to this business idea:",
            item_label="SECTOR",
            max_completion_tokens=128,
        )
        sector_df = parse_results_to_dataframe_sector_only(batch_results)
        for i in range(len(chunk)):
            global_idx = start + i
            if i < len(sector_df):
                all_sectors[global_idx] = sector_df.iloc[i].get("sector") or ""

    output_df = df.copy()
    output_df["sector"] = [s or "" for s in all_sectors]

    if args.output:
        out_path = args.output
    else:
        out_path = os.path.join(
            results_dir,
            f"sector_assignment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
    output_df.to_csv(out_path, index=False)
    print(f"\nDone. Output: {out_path}")


if __name__ == "__main__":
    main()
