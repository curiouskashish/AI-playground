# Batch Evaluation Processor

A web application for batch processing Idea Submission evaluations and Pitch Video evaluations using CSV files.

## Features

- **Batch Processing**: Upload CSV files containing multiple submissions/videos
- **Evaluation Types**:
  - Idea Submission Evaluation
  - Pitch Video Evaluation
  - **Sector Assignment (Large Dataset)** — single output column (`sector`), chunked processing for 50k+ rows
- **CSV Export**: Download results as CSV files with evaluation scores and feedback
- **Modern UI**: Beautiful, responsive interface with drag-and-drop file upload

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Backend Server**:
   ```bash
   python app.py
   ```
   The server will start on `http://localhost:5001`

3. **Open the Frontend**:
   - Open `index.html` in your web browser
   - Or serve it using a local server (e.g., `python -m http.server 8000`)

## CSV Format

### Idea Submission Evaluation

Expected CSV columns (Input):
- `business_idea` (required): Text description of the business idea to evaluate

Example CSV:
```csv
business_idea
"Revolutionary AI assistant for students"
"Mobile app for fitness tracking"
"Eco-friendly packaging solutions"
```

Output CSV columns:
- `sector`: The business sector identified
- `multiple_ideas`: True/False — whether the input contains more than one distinct business idea
- `legibility_clarity`: True/False indicator for clarity
- `legibility_clarity_reason`: Reason for clarity evaluation
- `legibility_coherence`: True/False indicator for coherence
- `legibility_coherence_reason`: Reason for coherence evaluation
- `specificity_detailed`: True/False indicator for detailed
- `specificity_detailed_reason`: Reason for detailed evaluation
- `specificity_concrete`: True/False indicator for concrete
- `specificity_concrete_reason`: Reason for concrete evaluation
- `specificity_score`: Score from 1-10
- `executability_feasible`: True/False indicator for feasible
- `executability_feasible_reason`: Reason for feasible evaluation
- `executability_actionable`: True/False indicator for actionable
- `executability_actionable_reason`: Reason for actionable evaluation
- `novelty_novel`: True/False indicator for novel
- `novelty_novel_reason`: Reason for novelty evaluation

### Pitch Video Evaluation

Expected CSV columns (Input):
- `transcript` (required): The pitch video transcript text to evaluate

Example CSV:
```csv
transcript
"Hello, my name is Priya and I want to tell you about my business idea. In our area, many people have mobile phones but their phones get damaged easily. So I want to open a mobile repair shop in our locality. What makes us different is that we will provide home service also."
"Namaste, main Rahul hoon. Main ek soap business start karna chahti hoon. Market mein jo soap milte hain wo bahut mehnge hain. Mera soap natural hoga neem aur tulsi se bana."
```

Output CSV columns:
- `sector`: Business sector classification (Art and crafts, Agriculture, Education and social cause, Food, Personal care and hygiene, Sustainable environment, Tourism and hospitality, Technology driven solutions, Others)
- `articulation_idea_clearly_defined`: True/False if business idea is clear
- `articulation_idea_clearly_defined_reason`: Reason for the assessment
- `articulation_problem_mentioned`: True/False if problem/need is mentioned
- `articulation_problem_mentioned_reason`: Reason for the assessment
- `articulation_score`: Score from 1-10 for articulation quality
- `product_usp_mentioned`: True/False if USP is mentioned
- `product_usp_mentioned_reason`: Reason for the assessment
- `product_selling_plan_mentioned`: True/False if selling plan/target customers mentioned
- `product_selling_plan_mentioned_reason`: Reason for the assessment
- `product_quality_score`: Score from 1-10 for product description quality
- `transcript_quality_note`: Optional note about transcript quality issues

### Sector Assignment (Large Dataset)

Expected CSV columns (Input):
- `business_idea` (required): Text description of the business idea to classify

Output: **One extra column** — `sector` (one of: Art and crafts, Agriculture, Education and social cause, Food, Personal care and hygiene, Sustainable environment, Tourism and hospitality, Technology driven solutions, Others).

Optimised for very large files (e.g. 54,000 rows): uses **chunked processing** and configurable **concurrent requests** and **chunk size** in the UI. For the largest datasets, use the CLI script to avoid browser timeouts (see below).

## CLI: Sector-only batch for 54k+ rows (M2 MacBook)

For very large CSVs (e.g. 54,000 entries), run the sector assignment from the terminal so the job is not tied to the browser and can run for hours without timeouts. Recommended on M2 MacBook: run inside `tmux` or `screen`.

```bash
# From the project directory
python run_sector_batch_cli.py input.csv --api-key YOUR_OPENAI_KEY

# Optional: set chunk size and concurrency (defaults: 3000, 15)
python run_sector_batch_cli.py input.csv --api-key YOUR_OPENAI_KEY --chunk-size 3000 --max-concurrent 15

# Optional: output path (default: results/sector_assignment_<timestamp>.csv)
python run_sector_batch_cli.py input.csv --api-key YOUR_OPENAI_KEY -o ./output_with_sectors.csv

# Using environment variable for API key
export OPENAI_API_KEY=your_key
python run_sector_batch_cli.py input.csv
```

**Recommendations for 54k rows on M2 MacBook (no external processor):**

- Use **chunk size 2,000–5,000** (default 3,000) to limit memory and keep requests shorter.
- Use **max concurrent 10–15** to stay under API rate limits; increase only if your tier allows.
- Run in **tmux** or **screen** so the job continues if you disconnect.
- Output is written to `results/` (or your `-o` path) when the script finishes.

## Output

### Idea Submission Evaluation Results

The evaluation results CSV will include:
- All original columns from the input file (e.g., `business_idea`)
- Evaluation results with True/False indicators and reasons for each criterion:
  - Sector identification
  - Legibility (Clarity, Coherence)
  - Specificity (Detailed, Concrete, Score 1-10)
  - Executability (Feasible, Actionable)
  - Novelty (Novel)
- Each indicator includes both the True/False value and a reason text

### Pitch Video Evaluation Results

The evaluation results CSV will include:
- All original columns from the input file (e.g., `transcript`)
- Sector classification (one of 9 categories: Art and crafts, Agriculture, Education and social cause, Food, Personal care and hygiene, Sustainable environment, Tourism and hospitality, Technology driven solutions, Others)
- Articulation evaluation:
  - Business idea clarity (True/False + reason)
  - Problem/need mention (True/False + reason)
  - Articulation score (1-10)
- Product/service description:
  - USP mention (True/False + reason)
  - Selling plan/target customers (True/False + reason)
  - Quality score (1-10)
- Transcript quality note (optional)

## Customization

To customize the evaluation logic, modify the following functions in `app.py`:
- `evaluate_idea_submission(row)`: Customize Idea Submission evaluation criteria
- `evaluate_pitch_video(row)`: Customize Pitch Video evaluation criteria

## API Endpoints

- `POST /api/batch/evaluate/idea-submission`: Process Idea Submission CSV
- `POST /api/batch/evaluate/pitch-video`: Process Pitch Video CSV
- `POST /api/batch/evaluate/sector-only`: Sector-only assignment (chunked; form: `file`, `api_key`, `max_concurrent`, `chunk_size`)
- `GET /api/health`: Health check endpoint
- `GET /api/download-result/<filename>`: Download a saved result CSV

## Notes

- Maximum file size: 16MB
- Only CSV files are accepted
- Files are processed in memory (not saved to disk)
- Evaluation results are returned as downloadable CSV files
