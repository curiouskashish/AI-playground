# Udhyam Idea Bank Evaluation Platform — Handover

This is a local web application that helps evaluate student business ideas, generate Idea Bank entries from pitch transcripts, and produce representative images for each idea. It runs entirely on your own machine — no cloud account is required to use it.

## What's inside

The platform has two top-level tabs in the browser:

1. **Single Evaluation** — for testing one idea / transcript at a time. Includes:
   - **Idea Submission Evaluation** — scores a written idea against Udhyam's evaluation matrix.
   - **Pitch Video Evaluation** — evaluates a pitch transcript.
   - **Idea Generation** — turns a pitch transcript into a structured Idea Bank entry (title, problem, solution, impact, themes, categories), and optionally generates a representative image in three sizes (197×171, 156×171, 116×171).

2. **Batch Processing** — for running the same operations over CSV files. Cards available:
   - Idea Submission Evaluation (CSV in, CSV out)
   - Pitch Video Evaluation (CSV in, CSV out)
   - Sector Assignment (large datasets, chunked)
   - **Idea Generation from Pitch Transcripts** (Card 1: text)
   - **Image Generation for Ideas** (Card 2: images, mapped to each idea by a unique `idea_id`)

Generated images are saved locally under `results/idea_images/ideas/<idea_id>/{large,medium,small}.png`. The on-disk layout is designed to migrate cleanly to S3 / Google Cloud Storage later with a single `aws s3 sync` or `gsutil rsync` command — no rewrites needed.

---

## 1. System requirements

| | Requirement |
|---|---|
| Operating system | macOS, Linux, or Windows 10/11 |
| Python | **3.9 or newer** (3.9, 3.10, 3.11, 3.12, 3.13 all work) |
| Disk space | ~250 MB for dependencies + however many images you generate (each idea adds ~50 KB of PNGs) |
| Internet | Required — the app calls OpenAI's API |
| Browser | Any modern browser (Chrome, Safari, Firefox, Edge) |
| OpenAI API key | Required. For **image generation**, the OpenAI organisation must be verified to access `gpt-image-1` (free verification at https://platform.openai.com/settings/organization/general) |

---

## 2. Install Python (if not already installed)

Open a Terminal (macOS / Linux) or Command Prompt / PowerShell (Windows) and run:

```
python3 --version
```

- If you see something like `Python 3.9.6` or higher → you're good, skip to step 3.
- If you get "command not found" or version below 3.9, install Python:
  - **macOS:** download the installer from https://www.python.org/downloads/macos/ and run it.
  - **Windows:** download from https://www.python.org/downloads/windows/ — during install, **tick "Add Python to PATH"**.
  - **Linux (Ubuntu/Debian):** `sudo apt update && sudo apt install python3 python3-pip`

After installing, close and reopen your terminal, then re-run `python3 --version` to confirm.

> On macOS, the command is `python3` (not `python`). On Windows it might be `python` — try both if one isn't found.

---

## 3. Unzip the project

If your manager sent you a Google Drive folder:

1. Download the whole folder as a ZIP from Google Drive.
2. Unzip it somewhere convenient — e.g. `~/Documents/udhyam-evaluator/` on macOS or `C:\Users\<you>\Documents\udhyam-evaluator\` on Windows.
3. Open a Terminal / Command Prompt and `cd` into that folder. For example:
   ```
   cd ~/Documents/udhyam-evaluator
   ```

You should be able to see these files when you run `ls` (macOS/Linux) or `dir` (Windows):

```
app.py
batch_processor.py
batch-script.js
config.js
image_generation.js
image_storage.py
index.html
README.md
HANDOVER.md
requirements.txt
script.js
styles.css
sample_idea_submissions.csv
sample_pitch_videos.csv
run_sector_batch_cli.py
```

---

## 4. Install Python dependencies

From inside the project folder, run **one** of these commands:

```
pip3 install -r requirements.txt
```

or (equivalent):

```
python3 -m pip install -r requirements.txt
```

If pip complains about permissions, add `--user`:

```
pip3 install --user -r requirements.txt
```

This installs:

| Package | Why |
|---|---|
| Flask 3.0.0 + flask-cors 4.0.0 | The local web server |
| pandas 2.1.3 + numpy 1.26.2 | CSV handling |
| requests 2.31.0 + httpx ≥0.25.0 | HTTP calls to OpenAI |
| openai ≥1.0.0 | OpenAI SDK |
| Pillow ≥10.0.0 | Server-side image cropping (for the 3 image sizes) |

Wait for the install to finish. It usually takes 30–90 seconds depending on internet speed.

---

## 5. Get an OpenAI API key

1. Go to https://platform.openai.com/api-keys and sign in (or create an account).
2. Click "Create new secret key", give it a name like "Udhyam Evaluator", and **copy the key** (it starts with `sk-...`). You will not be able to see it again.
3. **If you plan to use image generation**, your OpenAI organisation must also be verified:
   - Visit https://platform.openai.com/settings/organization/general
   - If the page mentions verification, complete it (one-time, takes a few minutes).
   - Without verification, text features work fine but image generation will return an error.

You will paste this key into the app's UI later — it is not stored in any file in this folder.

---

## 6. Start the application

From the project folder, run:

```
python3 app.py
```

You should see output like:

```
Starting Batch Evaluation Processor API...
Server running on http://localhost:5000
API endpoints:
  - POST /api/batch/evaluate/idea-submission
  - POST /api/batch/evaluate/pitch-video
  - POST /api/evaluate/llm (proxy for single evaluations)
  - POST /api/images/generate (proxy for OpenAI image generation)
  - POST /api/batch/idea-generation (Card 1: batch text idea generation)
  - POST /api/batch/idea-images (Card 2: batch image generation)
 * Running on http://127.0.0.1:5001
```

> Note: the banner mentions port 5000 but the server actually listens on **port 5001** — the banner is historical.

Leave this terminal window open. The server keeps running as long as the terminal is open. To stop the server later, press `Ctrl+C` in that terminal.

---

## 7. Open the application in a browser

Open any modern browser and go to:

```
http://localhost:5001
```

You should see the platform's homepage with two top-level tabs ("Single Evaluation" and "Batch Processing"). In the header, paste your OpenAI API key into the **API Key** field. The key is remembered in your browser's local storage and is sent to the local Flask server (which forwards it to OpenAI) — it never leaves your machine except for the OpenAI call itself.

---

## 8. Trying it out

### A. Single Idea Generation (with image)

1. Click **Single Evaluation → Idea Generation** sub-tab.
2. Paste a student pitch transcript (or click **Load Sample Data**).
3. Click **Generate Idea**. The structured Idea Bank entry appears within a few seconds.
4. Below the result, an **Image Prompt Template** and a **Generate Image** button appear. Click **Generate Image** — wait 10–30 seconds — three images render at 197×171, 156×171, and 116×171.
5. Use the per-size **Download** buttons to save PNGs, or **Export as JSON** at the top to download the full record (text + base64 images embedded).

### B. Batch Idea Generation + Images

Two cards work together:

1. **Card 1 — Idea Generation from Pitch Transcripts:**
   - Prepare a CSV with at least a `transcript` column (look at `sample_pitch_videos.csv` for the shape — it uses `transcript`).
   - Upload it on the card and click **Generate Ideas**.
   - You'll be served a CSV with all original columns + an `idea_id` column + the parsed Idea Bank fields. Save this file.

2. **Card 2 — Image Generation for Ideas:**
   - Upload the CSV from Card 1 (or any CSV with `idea_id`, `idea_title`, `problem_or_opportunity`, `solution_details`, `potential_impact`, `status`).
   - Adjust concurrency / skip-existing if you want.
   - Click **Generate Images**. For more than 50 rows you'll be asked to confirm (estimated cost displayed).
   - When done, a CSV downloads with three new path columns: `image_large_path`, `image_medium_path`, `image_small_path`. The actual PNG files are saved under `results/idea_images/ideas/<idea_id>/` — see "Output locations" below.

---

## 9. Output locations

All outputs live inside the `results/` folder of the project:

```
results/
  idea_submission_evaluations_<timestamp>.csv     ← single-idea batch evals
  pitch_video_evaluations_<timestamp>.csv
  sector_assignment_<timestamp>.csv
  idea_generation_batch_<timestamp>.csv           ← Card 1 output
  idea_images_batch_<timestamp>.csv               ← Card 2 output
  idea_images/                                    ← image files
    ideas/
      idea_V1StGXR8Z2/
        large.png    (197 × 171)
        medium.png   (156 × 171)
        small.png    (116 × 171)
      idea_8mZQp3kT9/
        large.png
        medium.png
        small.png
      ...
```

The path stored in the CSV (e.g. `ideas/idea_V1StGXR8Z2/large.png`) is **storage-root-relative**. When the project later moves to S3 or Google Cloud Storage, those same path strings become the object keys verbatim — a single `aws s3 sync results/idea_images/ s3://<bucket>/` would migrate everything without any CSV rewrite.

---

## 10. File / folder reference

| File | Purpose |
|---|---|
| `app.py` | Flask backend — all HTTP endpoints |
| `batch_processor.py` | Async batch logic: LLM calls, image generation, cropping (Pillow), DataFrame builders |
| `image_storage.py` | Pluggable storage backend (currently local-only; ready for S3/GCS extension) |
| `image_generation.js` | Browser-side image module (used by the single-idea page) |
| `index.html` | The full UI |
| `script.js` | Browser-side logic for the Single Evaluation tab |
| `batch-script.js` | Browser-side logic for the Batch Processing tab |
| `config.js` | Model list (OpenAI, Anthropic, Google) and default settings |
| `styles.css` | All visual styling |
| `requirements.txt` | Python dependencies |
| `run_sector_batch_cli.py` | Command-line tool for huge sector-classification jobs (50k+ rows) |
| `sample_idea_submissions.csv` | Example input for idea evaluation |
| `sample_pitch_videos.csv` | Example input for pitch evaluation / idea generation |
| `results/` | Where all outputs land (created on first use) |
| `README.md` | Original reference (kept; this HANDOVER.md supersedes it for setup) |

---

## 11. Troubleshooting

| Symptom | What to do |
|---|---|
| `command not found: pip` | Use `pip3` or `python3 -m pip` instead. |
| `command not found: python` (macOS) | Use `python3` instead. |
| Browser shows "Cannot connect to backend server" | Flask isn't running. Open a terminal in the project folder and run `python3 app.py`. Leave it running. |
| Flask says "Address already in use" on port 5001 | Another process is using port 5001. Either close that process, or restart your computer. (Older Flask sessions can linger — check with `lsof -i :5001` on macOS / Linux.) |
| Image generation returns "Your organization must be verified..." | Visit https://platform.openai.com/settings/organization/general and complete the verification. After it's approved (usually within minutes), retry. |
| All three image sizes appear as broken / empty boxes on the page | Hard-refresh the browser (Cmd+Shift+R on Mac, Ctrl+F5 on Windows) so cached CSS/JS reloads. |
| `module not found: PIL` when Flask starts | Re-run `pip3 install -r requirements.txt` — Pillow didn't install. |
| Card 2 says "missing required columns" | Make sure you're uploading the CSV that **came out of Card 1** (or any CSV with `idea_id`, `idea_title`, `problem_or_opportunity`, `solution_details`, `potential_impact`, `status`). |
| Card 2 says "X eligible rows exceed the safety cap of 200" | Split your CSV into chunks of ≤200 rows and run them sequentially. The cap is intentional to avoid runaway API costs. |
| Re-running Card 2 generates fresh images instead of skipping | Confirm the "Skip rows whose image files already exist" checkbox is ticked. |
| Re-running Card 2 always says "skipped" but you want fresh images | Untick the "Skip…" checkbox before clicking Generate Images. |
| Pasted API key disappears after refresh | The key is stored per-browser, per-model dropdown selection. Paste it again after changing models. |

---

## 12. Approximate costs (OpenAI, as of May 2026)

| Operation | Cost per row (approx) |
|---|---|
| Text idea generation (gpt-5-mini) | ~$0.001 |
| Image generation (gpt-image-1, 1024×1024) | ~$0.04 |
| Idea evaluation / pitch evaluation | ~$0.001–0.002 |

100 ideas with images ≈ $4 in OpenAI charges. Cards always show a confirmation modal for image batches above 50 rows.

---

## 13. Stopping the server

In the terminal where `python3 app.py` is running, press `Ctrl+C`. The server shuts down immediately. Your generated images and CSVs remain on disk under `results/` — they are never deleted automatically.

---

## 14. Contact / handover notes

- The project is currently designed for **local-only** use. All outputs (CSVs and images) live on the laptop running the app.
- The image storage layer (`image_storage.py`) was deliberately designed so a future move to S3 or GCS is a one-class addition + one env-var change. The path strings inside the CSVs are already structured as cloud object keys — no rewriting needed at migration time.
- If you intend to make this multi-user / deployed online, you'll want to add: authentication on the Flask endpoints, a real production WSGI server (e.g. gunicorn) in place of `app.run(debug=True)`, and proper secret management for the OpenAI key.
