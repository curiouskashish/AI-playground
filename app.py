from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import io
from datetime import datetime
import csv
import requests
import json
import logging
import os
from batch_processor import (
    run_batch_evaluation,
    parse_results_to_dataframe,
    parse_results_to_dataframe_sector_only,
    process_ideas_batch,
    generate_idea_id,
    parse_idea_generation_results_to_dataframe,
    run_image_batch,
    merge_image_results_into_dataframe,
)
from batch_image_batch_api import (
    create_idea_image_batch_job,
    ensure_job_output_ready,
    load_job as load_idea_image_batch_job,
    public_job_view,
)
from image_storage import get_storage_backend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
# Enable CORS for all origins (including file:// protocol)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Maximum file size: 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def evaluate_idea_submission(row):
    """
    Evaluate an idea submission based on innovation, feasibility, and market_potential.
    
    Args:
        row: pandas Series containing idea data
        
    Returns:
        dict: Evaluation results with score, status, and feedback
    """
    try:
        # Extract scores (handle missing values)
        innovation = float(row.get('innovation', 0)) if pd.notna(row.get('innovation')) else 0
        feasibility = float(row.get('feasibility', 0)) if pd.notna(row.get('feasibility')) else 0
        market_potential = float(row.get('market_potential', 0)) if pd.notna(row.get('market_potential')) else 0
        
        # Validate score ranges
        innovation = max(0, min(3, innovation))
        feasibility = max(0, min(2, feasibility))
        market_potential = max(0, min(2, market_potential))
        
        # Calculate weighted overall score (0-100 scale)
        # Innovation (0-3): 40% weight → (innovation/3) * 40
        # Feasibility (0-2): 30% weight → (feasibility/2) * 30
        # Market Potential (0-2): 30% weight → (market_potential/2) * 30
        innovation_score = (innovation / 3) * 40
        feasibility_score = (feasibility / 2) * 30
        market_score = (market_potential / 2) * 30
        
        overall_score = round(innovation_score + feasibility_score + market_score, 2)
        
        # Determine status based on score
        if overall_score >= 80:
            status = "Approved"
        elif overall_score >= 60:
            status = "Under Review"
        else:
            status = "Needs Improvement"
        
        # Generate feedback
        idea_desc = str(row.get('idea_description', 'N/A'))[:100]  # First 100 chars
        feedback_parts = []
        
        if innovation >= 2.5:
            feedback_parts.append("Excellent innovation with strong unique value proposition.")
        elif innovation >= 1.5:
            feedback_parts.append("Good innovation, but could be more distinctive.")
        else:
            feedback_parts.append("Needs more innovation and uniqueness.")
        
        if feasibility >= 1.5:
            feedback_parts.append("Highly feasible with clear implementation path.")
        elif feasibility >= 1.0:
            feedback_parts.append("Moderately feasible but may face implementation challenges.")
        else:
            feedback_parts.append("Feasibility concerns - needs more detailed planning.")
        
        if market_potential >= 1.5:
            feedback_parts.append("Strong market potential with good target audience.")
        elif market_potential >= 1.0:
            feedback_parts.append("Moderate market potential, consider market validation.")
        else:
            feedback_parts.append("Limited market potential - research target market further.")
        
        feedback = " ".join(feedback_parts)
        
        return {
            'score': overall_score,
            'status': status,
            'feedback': feedback,
            'evaluated_at': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'score': 0,
            'status': 'Error',
            'feedback': f'Evaluation error: {str(e)}',
            'evaluated_at': datetime.now().isoformat()
        }


def evaluate_pitch_video(row):
    """
    Evaluate a pitch video based on presentation_quality, clarity, engagement, and call_to_action.
    
    Args:
        row: pandas Series containing pitch data
        
    Returns:
        dict: Evaluation results with score, status, and feedback
    """
    try:
        # Extract scores (handle missing values)
        presentation_quality = float(row.get('presentation_quality', 0)) if pd.notna(row.get('presentation_quality')) else 0
        clarity = float(row.get('clarity', 0)) if pd.notna(row.get('clarity')) else 0
        engagement = float(row.get('engagement', 0)) if pd.notna(row.get('engagement')) else 0
        call_to_action = float(row.get('call_to_action', 0)) if pd.notna(row.get('call_to_action')) else 0
        
        # Validate score ranges
        presentation_quality = max(0, min(2, presentation_quality))
        clarity = max(0, min(2, clarity))
        engagement = max(0, min(2, engagement))
        call_to_action = max(0, min(2, call_to_action))
        
        # Calculate weighted overall score (0-100 scale)
        # Each criterion (0-2): 25% weight → (score/2) * 25
        presentation_score = (presentation_quality / 2) * 25
        clarity_score = (clarity / 2) * 25
        engagement_score = (engagement / 2) * 25
        cta_score = (call_to_action / 2) * 25
        
        overall_score = round(presentation_score + clarity_score + engagement_score + cta_score, 2)
        
        # Determine status based on score
        if overall_score >= 80:
            status = "Approved"
        elif overall_score >= 60:
            status = "Under Review"
        else:
            status = "Needs Improvement"
        
        # Generate feedback
        feedback_parts = []
        
        if presentation_quality >= 1.5:
            feedback_parts.append("Professional presentation with good structure and flow.")
        elif presentation_quality >= 1.0:
            feedback_parts.append("Adequate presentation but could be more polished.")
        else:
            feedback_parts.append("Presentation needs significant improvement in structure and delivery.")
        
        if clarity >= 1.5:
            feedback_parts.append("Clear and well-articulated message.")
        elif clarity >= 1.0:
            feedback_parts.append("Moderately clear but could be more concise.")
        else:
            feedback_parts.append("Message clarity needs improvement - simplify and focus.")
        
        if engagement >= 1.5:
            feedback_parts.append("Highly engaging with good audience connection.")
        elif engagement >= 1.0:
            feedback_parts.append("Moderately engaging, try to increase audience interaction.")
        else:
            feedback_parts.append("Low engagement - incorporate storytelling and examples.")
        
        if call_to_action >= 1.5:
            feedback_parts.append("Strong call-to-action with clear next steps.")
        elif call_to_action >= 1.0:
            feedback_parts.append("Call-to-action present but could be more compelling.")
        else:
            feedback_parts.append("Missing or weak call-to-action - clearly state desired outcome.")
        
        feedback = " ".join(feedback_parts)
        
        return {
            'score': overall_score,
            'status': status,
            'feedback': feedback,
            'evaluated_at': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'score': 0,
            'status': 'Error',
            'feedback': f'Evaluation error: {str(e)}',
            'evaluated_at': datetime.now().isoformat()
        }


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Batch Evaluation Processor API is running'})

@app.route('/', methods=['GET'])
def serve_index():
    """Serve the main HTML file"""
    try:
        file_path = os.path.join(BASE_DIR, 'index.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return jsonify({'error': f'index.html not found at {BASE_DIR}'}), 404
    except Exception as e:
        return jsonify({'error': f'Error reading index.html: {str(e)}'}), 500

@app.route('/<path:filename>', methods=['GET'])
def serve_static(filename):
    """Serve static files (CSS, JS, etc.)"""
    if filename in ['styles.css', 'script.js', 'batch-script.js', 'config.js', 'image_generation.js']:
        try:
            file_path = os.path.join(BASE_DIR, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content_type = 'text/css' if filename.endswith('.css') else 'application/javascript' if filename.endswith('.js') else 'text/plain'
                return f.read(), 200, {'Content-Type': content_type}
        except FileNotFoundError:
            return jsonify({'error': f'{filename} not found at {BASE_DIR}'}), 404
        except Exception as e:
            return jsonify({'error': f'Error reading {filename}: {str(e)}'}), 500
    return jsonify({'error': 'File not found'}), 404


@app.route('/api/batch/evaluate/idea-submission', methods=['POST'])
def batch_evaluate_idea_submission():
    """Process batch idea submission evaluation using LLM"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are allowed'}), 400
        
        # Get optional parameters (with defaults)
        model = request.form.get('model', 'gpt-5-mini')
        temperature = float(request.form.get('temperature', 1.0))
        api_key = request.form.get('api_key', '')
        system_prompt = request.form.get('system_prompt', '').strip()
        
        if not api_key:
            return jsonify({'error': 'API key is required. Please provide it as a form parameter.'}), 400
        
        # Log which prompt is being used
        if system_prompt:
            logger.info(f"Using system prompt from UI (length: {len(system_prompt)} characters)")
            logger.debug(f"Prompt preview: {system_prompt[:200]}...")
        else:
            logger.info("No system prompt provided, using default prompt")
        
        # Read CSV file
        try:
            df = pd.read_csv(file)
        except Exception as e:
            return jsonify({'error': f'Invalid CSV file: {str(e)}'}), 400
        
        # Validate required columns
        required_columns = ['business_idea']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'error': f'Missing required columns: {", ".join(missing_columns)}',
                'expected': required_columns,
                'found': list(df.columns)
            }), 400
        
        # Default system prompt if not provided
        if not system_prompt:
            system_prompt = """You are an expert evaluator for the Udhyam Learning Foundation's entrepreneurial mindsets development program in Indian government schools. Your task is to evaluate a business idea submitted by a student.

EVALUATION CRITERIA:
Evaluate the business idea and provide the following:

1. SECTOR: Identify the business sector (e.g., Technology, Retail, Services, Manufacturing, Agriculture, Education, Healthcare, etc.)

2. LEGIBILITY:
   - Clarity: Is the idea clearly explained? Provide True/False and a detailed reason explaining why.
   - Coherence: Is the idea logically consistent? Provide True/False and a detailed reason explaining why.

3. SPECIFICITY:
   - Detailed: Is the idea detailed enough with sufficient information? Provide True/False and a detailed reason explaining why.
   - Concrete: Is the idea clearly defined with specific details? Provide True/False and a detailed reason explaining why.
   - Score: Rate the overall specificity from 1-10 (where 1 is very vague and 10 is highly specific)

4. EXECUTABILITY:
   - Feasible: Is the idea feasible to implement? Provide True/False and a detailed reason explaining why.
   - Actionable: Does the idea have clear actionable steps? Provide True/False and a detailed reason explaining why.

5. NOVELTY:
   - Novel: Is the idea novel/innovative? Provide True/False and a detailed reason explaining why.

6. MULTIPLE IDEAS CHECK:
   Some students enter multiple business ideas in a single input field. Check whether the business_idea text contains more than one distinct business idea (e.g., separate concepts, different products/services, or multiple proposals). Output True if multiple ideas are present, False if there is only one clear idea.

IMPORTANT: For each True/False indicator, you MUST provide a detailed "reason" field explaining your evaluation. The reason should be at least 1-2 sentences explaining why you assigned that value.

OUTPUT FORMAT (strictly follow this JSON structure):
{
  "sector": "Technology",
  "multiple_ideas": false,
  "legibility": {
    "clarity": {"value": true, "reason": "The idea is clearly explained with specific details about the target market and value proposition..."},
    "coherence": {"value": false, "reason": "The idea lacks logical consistency as the proposed solution doesn't directly address the stated problem..."}
  },
  "specificity": {
    "detailed": {"value": true, "reason": "The idea provides sufficient detail about the business model, target customers, and revenue streams..."},
    "concrete": {"value": true, "reason": "The idea is clearly defined with specific examples and concrete implementation steps..."},
    "score": 8
  },
  "executability": {
    "feasible": {"value": true, "reason": "The idea is feasible given the available resources and market conditions..."},
    "actionable": {"value": false, "reason": "The idea lacks actionable steps and doesn't provide a clear implementation roadmap..."}
  },
  "novelty": {
    "novel": {"value": true, "reason": "The idea shows innovation by addressing an unmet need in a unique way..."}
  }
}

CRITICAL: Every indicator MUST include both "value" (true/false) and "reason" (detailed explanation). Do not omit the reason field. Always include "multiple_ideas" (true/false) at the top level.

Provide only valid JSON in your response, no additional text."""
        
        # Extract business ideas from DataFrame
        ideas_list = []
        for idx, row in df.iterrows():
            business_idea = str(row.get('business_idea', '')).strip()
            if business_idea:
                ideas_list.append(business_idea)
        
        if not ideas_list:
            return jsonify({'error': 'No valid business ideas found in CSV file'}), 400
        
        logger.info(f"Processing {len(ideas_list)} business ideas using batch processor...")
        
        # Use batch processor for concurrent evaluation
        try:
            # Progress callback for logging
            def progress_callback(completed, total):
                logger.info(f"Progress: {completed}/{total} ({100*completed/total:.1f}%)")
            
            # Get max_concurrent from form or use default (reduced to avoid rate limits)
            max_concurrent = int(request.form.get('max_concurrent', 10))
            
            # Run batch evaluation using the batch_processor module
            batch_results = run_batch_evaluation(
                ideas_list=ideas_list,
                system_prompt=system_prompt,
                api_key=api_key,
                max_concurrent=max_concurrent,
                progress_callback=progress_callback
            )
            
            # Convert results to DataFrame
            results_df = parse_results_to_dataframe(batch_results)
            
            # Create a mapping from idea to result
            idea_to_result = {}
            for _, result_row in results_df.iterrows():
                idea = result_row['idea']
                idea_to_result[idea] = result_row.to_dict()
            
            # Merge results back with original DataFrame
            results = []
            for idx, row in df.iterrows():
                business_idea = str(row.get('business_idea', '')).strip()
                result_row = row.to_dict()
                
                if business_idea and business_idea in idea_to_result:
                    # Merge evaluation results
                    eval_result = idea_to_result[business_idea]
                    result_row.update({
                        'sector': eval_result.get('sector', ''),
                        'multiple_ideas': eval_result.get('multiple_ideas'),
                        'legibility_clarity': eval_result.get('is_clear'),
                        'legibility_clarity_reason': eval_result.get('is_clear_reason', ''),
                        'legibility_coherence': eval_result.get('is_coherent'),
                        'legibility_coherence_reason': eval_result.get('is_coherent_reason', ''),
                        'specificity_detailed': eval_result.get('is_detailed_enough'),
                        'specificity_detailed_reason': eval_result.get('is_detailed_enough_reason', ''),
                        'specificity_concrete': eval_result.get('is_clearly_defined'),
                        'specificity_concrete_reason': eval_result.get('is_clearly_defined_reason', ''),
                        'specificity_score': eval_result.get('specificity_score'),
                        'executability_feasible': eval_result.get('is_feasible'),
                        'executability_feasible_reason': eval_result.get('is_feasible_reason', ''),
                        'executability_actionable': eval_result.get('is_actionable'),
                        'executability_actionable_reason': eval_result.get('is_actionable_reason', ''),
                        'novelty_novel': eval_result.get('is_novel'),
                        'novelty_novel_reason': eval_result.get('is_novel_reason', ''),
                        'status': eval_result.get('status', 'success'),
                        'error': eval_result.get('error', '')
                    })
                else:
                    # Empty or not found
                    result_row.update({
                        'sector': 'N/A',
                        'error': 'Empty business idea' if not business_idea else 'Not processed'
                    })
                
                results.append(result_row)
            
            # Create output DataFrame
            output_df = pd.DataFrame(results)
            
        except Exception as e:
            logger.error(f"Batch processor error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': f'Batch processing error: {str(e)}'}), 500
        
        # Create filename with timestamp
        filename = f'idea_submission_evaluations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Create results directory if it doesn't exist
        results_dir = os.path.join(BASE_DIR, 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        # Save CSV file to disk (for large files that might timeout on download)
        file_path = os.path.join(results_dir, filename)
        output_df.to_csv(file_path, index=False)
        logger.info(f"CSV file saved to: {file_path}")
        
        # Also prepare for download
        mem = io.BytesIO()
        output_df.to_csv(mem, index=False)
        mem.seek(0)
        
        try:
            # Return CSV file for download
            return send_file(
                mem,
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            # If download fails, at least the file is saved to disk
            logger.error(f"Failed to send file for download: {str(e)}")
            logger.info(f"File is saved at: {file_path}")
            return jsonify({
                'error': 'Download failed, but file was saved',
                'file_path': file_path,
                'message': f'File saved to: {file_path}',
                'download_url': f'/api/download-result/{filename}'
            }), 200
    
    except Exception as e:
        logger.error(f"Batch processing error: {str(e)}")
        return jsonify({'error': f'Processing error: {str(e)}'}), 500


# Default system prompt for sector-only classification (single output field)
SECTOR_ONLY_SYSTEM_PROMPT = """You are an expert evaluator for Udhyam Learning Foundation's entrepreneurial mindsets development program conducted in government schools across India.

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


@app.route('/api/batch/evaluate/sector-only', methods=['POST'])
def batch_evaluate_sector_only():
    """Process batch sector assignment only. Uses chunked processing for large datasets (e.g. 54k rows)."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are allowed'}), 400

        api_key = request.form.get('api_key', '').strip()
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400

        max_concurrent = int(request.form.get('max_concurrent', 15))
        chunk_size = int(request.form.get('chunk_size', 3000))
        chunk_size = max(500, min(10000, chunk_size))

        try:
            df = pd.read_csv(file)
        except Exception as e:
            return jsonify({'error': f'Invalid CSV file: {str(e)}'}), 400

        required_columns = ['business_idea']
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            return jsonify({
                'error': f'Missing required columns: {", ".join(missing)}',
                'expected': required_columns,
                'found': list(df.columns),
            }), 400

        system_prompt = request.form.get('system_prompt', '').strip() or SECTOR_ONLY_SYSTEM_PROMPT

        # Build list of (index, business_idea) for rows that have content
        rows_to_process = []
        for idx, row in df.iterrows():
            idea = str(row.get('business_idea', '')).strip()
            rows_to_process.append((idx, idea, row.to_dict()))

        # Split into chunks by index ranges (preserve order)
        total = len(rows_to_process)
        all_results = [None] * total  # results[i] = sector for row i

        def progress_cb(completed, total_chunk):
            logger.info(f"Sector batch progress: {completed}/{total_chunk}")

        for start in range(0, total, chunk_size):
            end = min(start + chunk_size, total)
            chunk = rows_to_process[start:end]
            ideas_list = [t[1] for t in chunk]

            logger.info(f"Processing sector chunk {start}-{end} of {total} (size {len(ideas_list)})")
            batch_results = run_batch_evaluation(
                ideas_list=ideas_list,
                system_prompt=system_prompt,
                api_key=api_key,
                max_concurrent=max_concurrent,
                progress_callback=progress_cb,
                user_message_prefix="Assign a sector to this business idea:",
                item_label="SECTOR",
                max_completion_tokens=128,
            )
            sector_df = parse_results_to_dataframe_sector_only(batch_results)
            for i, (_, _, row_dict) in enumerate(chunk):
                global_idx = start + i
                if global_idx < len(sector_df):
                    all_results[global_idx] = sector_df.iloc[i].get('sector', '') or ''

        # Build output: original dataframe + sector column (same row order as df)
        output_df = df.copy()
        output_df['sector'] = [s or '' for s in all_results]

        filename = f'sector_assignment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        results_dir = os.path.join(BASE_DIR, 'results')
        os.makedirs(results_dir, exist_ok=True)
        file_path = os.path.join(results_dir, filename)
        output_df.to_csv(file_path, index=False)
        logger.info(f"Sector CSV saved: {file_path}")

        mem = io.BytesIO()
        output_df.to_csv(mem, index=False)
        mem.seek(0)
        try:
            return send_file(
                mem,
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename,
            )
        except Exception as e:
            logger.error(f"Failed to send file: {e}")
            return jsonify({
                'error': 'Download failed, but file was saved',
                'file_path': file_path,
                'download_url': f'/api/download-result/{filename}',
            }), 200

    except Exception as e:
        logger.error(f"Sector-only batch error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Processing error: {str(e)}'}), 500


@app.route('/api/download-result/<filename>', methods=['GET'])
def download_result(filename):
    """Download a previously saved result file"""
    try:
        results_dir = os.path.join(BASE_DIR, 'results')
        file_path = os.path.join(results_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500


@app.route('/api/list-results', methods=['GET'])
def list_results():
    """List all available result files"""
    try:
        results_dir = os.path.join(BASE_DIR, 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        files = []
        if os.path.exists(results_dir):
            for filename in os.listdir(results_dir):
                if filename.endswith('.csv'):
                    file_path = os.path.join(results_dir, filename)
                    file_stat = os.stat(file_path)
                    files.append({
                        'filename': filename,
                        'size': file_stat.st_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        'download_url': f'/api/download-result/{filename}'
                    })
        
        # Sort by modified time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({'files': files})
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({'error': f'Error listing files: {str(e)}'}), 500


def parse_pitch_results_to_dataframe(results, transcripts_list):
    """Convert pitch video evaluation results to a structured DataFrame"""
    
    rows = []
    for r in results:
        row = {
            "id": r["id"],
            "transcript": r.get("idea", transcripts_list[r["id"]] if r["id"] < len(transcripts_list) else ""),
            "status": r["status"],
            "error": r["error"]
        }
        
        if r["status"] == "success" and r["result"]:
            res = r["result"]
            
            # Sector
            row["sector"] = res.get("sector", "")
            
            # Articulation
            articulation = res.get("articulation", {})
            idea_clarity = articulation.get("is_idea_clearly_defined", {})
            row["articulation_idea_clearly_defined"] = idea_clarity.get("value", None)
            row["articulation_idea_clearly_defined_reason"] = idea_clarity.get("reason", "")
            
            problem_mention = articulation.get("is_problem_or_need_mentioned", {})
            row["articulation_problem_mentioned"] = problem_mention.get("value", None)
            row["articulation_problem_mentioned_reason"] = problem_mention.get("reason", "")
            
            row["articulation_score"] = articulation.get("score", None)
            
            # Product/Service Description
            product = res.get("product_service_description", {})
            usp = product.get("is_usp_mentioned", {})
            row["product_usp_mentioned"] = usp.get("value", None)
            row["product_usp_mentioned_reason"] = usp.get("reason", "")
            
            selling_plan = product.get("is_selling_plan_or_target_customers_mentioned", {})
            row["product_selling_plan_mentioned"] = selling_plan.get("value", None)
            row["product_selling_plan_mentioned_reason"] = selling_plan.get("reason", "")
            
            row["product_quality_score"] = product.get("quality_score", None)
            
            # Transcript quality note
            row["transcript_quality_note"] = res.get("transcript_quality_note", "")
            
            # Store full JSON for reference
            row["full_response"] = json.dumps(res)
        else:
            # Fill with None for failed evaluations
            row["sector"] = ""
            row["articulation_idea_clearly_defined"] = None
            row["articulation_idea_clearly_defined_reason"] = ""
            row["articulation_problem_mentioned"] = None
            row["articulation_problem_mentioned_reason"] = ""
            row["articulation_score"] = None
            row["product_usp_mentioned"] = None
            row["product_usp_mentioned_reason"] = ""
            row["product_selling_plan_mentioned"] = None
            row["product_selling_plan_mentioned_reason"] = ""
            row["product_quality_score"] = None
            row["transcript_quality_note"] = ""
            row["full_response"] = ""
        
        rows.append(row)
    
    return pd.DataFrame(rows)


# Default pitch video system prompt
DEFAULT_PITCH_PROMPT = """You are an expert evaluator for Udhyam Learning Foundation's entrepreneurial mindsets development program conducted in government schools across India. Your task is to evaluate the transcript of a business pitch video submitted by a student based on the evaluation matrix defined below.

## CONTEXT
- Students are from government schools in India (typically ages 13-17)
- Video length: 1 to 5 minutes
- Students have limited resources and business experience
- Pitch videos are recorded by students, often in informal settings
- Students may present in Hindi, English, or regional languages

---

## IMPORTANT: TRANSCRIPT INTERPRETATION GUIDELINES

The transcript you receive is auto-generated and may contain errors. You MUST apply GENEROUS INTERPRETATION when evaluating:

| Issue | How to Handle |
|-------|---------------|
| **Spelling errors** | Interpret phonetically (e.g., "sope" = "soap", "bussiness" = "business") |
| **Grammar mistakes** | Focus on intent, not grammatical correctness |
| **Fragmented sentences** | Piece together meaning from context |
| **Filler words** | Ignore "umm", "aah", "like", "you know" etc. |
| **Code-switching** | Students may mix Hindi/English/regional words - this is acceptable |
| **Transcription artifacts** | Ignore "[inaudible]", "[music]", timestamps, speaker labels |
| **Repetition** | Students may repeat themselves due to nervousness - count the idea once |
| **Informal language** | "Customers ko sell karunga" is valid mention of selling plan |
| **Implied meaning** | If context clearly suggests something, consider it mentioned |

**PRINCIPLE:** If a reasonable person watching the video would understand what the student meant, give credit for it.

---

## SECTOR CLASSIFICATION

Classify the business pitch into ONE of the following 9 sectors. Choose the MOST appropriate sector based on the primary nature of the business:

| Sector | Description |
|--------|-------------|
| Art and crafts | Handmade items, paintings, decorative products, handicrafts, creative artwork |
| Agriculture | Farming, gardening, plant nursery, organic produce, agricultural tools/services |
| Education and social cause | Tutoring, teaching aids, social impact initiatives, community welfare services |
| Food | Food products, cooking services, tiffin services, snacks, beverages, catering |
| Personal care and hygiene | Soaps, sanitizers, beauty products, hygiene kits, grooming services |
| Sustainable environment | Eco-friendly products, waste management, recycling, renewable solutions (NOT art/crafts) |
| Tourism and hospitality | Travel guides, local tours, hospitality services, cultural experiences |
| Technology driven solutions | Apps, websites, digital services, tech-based problem solving |
| Others | Ideas that do not clearly fit into any of the above 8 categories |

---

## EVALUATION MATRIX

### 1. ARTICULATION OF BUSINESS IDEA AND/OR PROBLEM

**1a. Business Idea Clarity Check:**
- Output: `true` if the core business concept (product/service) is identifiable even if not perfectly explained
- Output: `false` only if you genuinely cannot determine what the student is trying to sell

**1b. Problem/Need Mention Check:**
- Output: `true` if ANY of these are mentioned (even briefly or implicitly): a problem the product solves, a need in the market, why customers would benefit, a gap they identified, pain points of customers
- Output: `false` only if there is absolutely no reference to why this product/service is needed

**1c. Articulation Score (1-10):**
| Score | Description |
|-------|-------------|
| 1-2 | Idea is incomprehensible even with generous interpretation; no clarity at all |
| 3-4 | Vague idea can be guessed but very poorly explained; problem not addressed |
| 5-6 | Basic idea is understandable; problem/need mentioned briefly or implicitly |
| 7-8 | Idea is clearly explained with good detail; problem/need is well articulated |
| 9-10 | Exceptionally clear and compelling explanation; strong problem-solution connection |

---

### 2. PRODUCT/SERVICE DESCRIPTION

**2a. Unique Selling Point (USP) Check:**
- Output: `true` if ANY of these are mentioned: what makes their product different, special features/benefits, why customers should choose them, price/quality advantage, unique approach
- Output: `false` only if there is no indication of what makes this offering unique or special

**2b. Selling Plan / Target Customers Check:**
- Output: `true` if ANY selling plan element (where/how they will sell, marketing ideas) OR ANY target customer mention (who will buy, customer segment, geographic area) is present
- Output: `false` only if neither selling approach nor customer segment is mentioned at all

**2c. Quality Score (1-10):**
| Score | Description |
|-------|-------------|
| 1-2 | Almost no business details; just a name or single sentence |
| 3-4 | Minimal details; only 1-2 basic elements mentioned vaguely |
| 5-6 | Moderate details; 2-3 business elements covered with basic information |
| 7-8 | Good details; multiple business elements covered with reasonable depth |
| 9-10 | Excellent details; comprehensive coverage of business elements with specific information |

---

## OUTPUT FORMAT

You MUST respond with ONLY the following JSON structure. Do not include any text before or after the JSON.

{
  "sector": "one of: Art and crafts, Agriculture, Education and social cause, Food, Personal care and hygiene, Sustainable environment, Tourism and hospitality, Technology driven solutions, Others",
  "articulation": {
    "is_idea_clearly_defined": {
      "value": true or false,
      "reason": "1-2 sentences explaining what business idea you understood or why it was unclear"
    },
    "is_problem_or_need_mentioned": {
      "value": true or false,
      "reason": "1-2 sentences explaining what problem/need was mentioned or why it was missing"
    },
    "score": integer from 1 to 10
  },
  "product_service_description": {
    "is_usp_mentioned": {
      "value": true or false,
      "reason": "1-2 sentences explaining what USP was mentioned or why it was missing"
    },
    "is_selling_plan_or_target_customers_mentioned": {
      "value": true or false,
      "reason": "1-2 sentences explaining what selling plan or target customers were mentioned"
    },
    "quality_score": integer from 1 to 10
  },
  "transcript_quality_note": "optional: brief note if transcript had significant issues that affected evaluation"
}

## EVALUATION GUIDELINES
- Be Student-Centric: Evaluate based on student context, not professional pitch standards.
- Generous Interpretation: When in doubt, interpret in favor of the student.
- Substance Over Style: Focus on content and ideas, not presentation polish.
- Implicit Counts: If something is clearly implied, it counts as mentioned.
- Language Flexibility: Accept mixed language (Hindi-English, regional language mix).

Provide only valid JSON in your response, no additional text."""


@app.route('/api/batch/evaluate/pitch-video', methods=['POST'])
def batch_evaluate_pitch_video():
    """Process batch pitch video evaluation using LLM"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are allowed'}), 400
        
        # Get optional parameters (with defaults)
        model = request.form.get('model', 'gpt-5-mini')
        temperature = float(request.form.get('temperature', 1.0))
        api_key = request.form.get('api_key', '')
        system_prompt = request.form.get('system_prompt', '').strip()
        
        if not api_key:
            return jsonify({'error': 'API key is required. Please provide it as a form parameter.'}), 400
        
        # Log which prompt is being used
        if system_prompt:
            logger.info(f"Using system prompt from UI (length: {len(system_prompt)} characters)")
            logger.debug(f"Prompt preview: {system_prompt[:200]}...")
        else:
            logger.info("No system prompt provided, using default pitch prompt")
            system_prompt = DEFAULT_PITCH_PROMPT
        
        # Read CSV file
        try:
            df = pd.read_csv(file)
        except Exception as e:
            return jsonify({'error': f'Invalid CSV file: {str(e)}'}), 400
        
        # Validate required columns
        required_columns = ['transcript']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'error': f'Missing required columns: {", ".join(missing_columns)}',
                'expected': required_columns,
                'found': list(df.columns)
            }), 400
        
        # Extract transcripts from DataFrame
        transcripts_list = []
        for idx, row in df.iterrows():
            transcript = str(row.get('transcript', '')).strip()
            if transcript:
                transcripts_list.append(transcript)
        
        if not transcripts_list:
            return jsonify({'error': 'No valid transcripts found in CSV file'}), 400
        
        logger.info(f"Processing {len(transcripts_list)} pitch video transcripts using batch processor...")
        
        # Use batch processor for concurrent evaluation
        try:
            # Progress callback for logging
            def progress_callback(completed, total):
                logger.info(f"Progress: {completed}/{total} ({100*completed/total:.1f}%)")
            
            # Get max_concurrent from form or use default
            max_concurrent = int(request.form.get('max_concurrent', 10))
            
            # Run batch evaluation using the batch_processor module
            # The batch processor evaluates transcripts concurrently
            batch_results = run_batch_evaluation(
                ideas_list=transcripts_list,  # transcripts are passed as "ideas"
                system_prompt=system_prompt,
                api_key=api_key,
                max_concurrent=max_concurrent,
                progress_callback=progress_callback,
                user_message_prefix="Evaluate this pitch video transcript:",
                item_label="TRANSCRIPT"
            )
            
            # Convert results to DataFrame using pitch-specific parser
            results_df = parse_pitch_results_to_dataframe(batch_results, transcripts_list)
            
            # Create a mapping from transcript to result
            transcript_to_result = {}
            for _, result_row in results_df.iterrows():
                transcript = result_row['transcript']
                transcript_to_result[transcript] = result_row.to_dict()
            
            # Merge results back with original DataFrame
            results = []
            for idx, row in df.iterrows():
                transcript = str(row.get('transcript', '')).strip()
                result_row = row.to_dict()
                
                if transcript and transcript in transcript_to_result:
                    # Merge evaluation results
                    eval_result = transcript_to_result[transcript]
                    result_row.update({
                        'sector': eval_result.get('sector', ''),
                        'articulation_idea_clearly_defined': eval_result.get('articulation_idea_clearly_defined'),
                        'articulation_idea_clearly_defined_reason': eval_result.get('articulation_idea_clearly_defined_reason', ''),
                        'articulation_problem_mentioned': eval_result.get('articulation_problem_mentioned'),
                        'articulation_problem_mentioned_reason': eval_result.get('articulation_problem_mentioned_reason', ''),
                        'articulation_score': eval_result.get('articulation_score'),
                        'product_usp_mentioned': eval_result.get('product_usp_mentioned'),
                        'product_usp_mentioned_reason': eval_result.get('product_usp_mentioned_reason', ''),
                        'product_selling_plan_mentioned': eval_result.get('product_selling_plan_mentioned'),
                        'product_selling_plan_mentioned_reason': eval_result.get('product_selling_plan_mentioned_reason', ''),
                        'product_quality_score': eval_result.get('product_quality_score'),
                        'transcript_quality_note': eval_result.get('transcript_quality_note', ''),
                        'status': eval_result.get('status', 'success'),
                        'error': eval_result.get('error', '')
                    })
                else:
                    # Empty or not found
                    result_row.update({
                        'sector': '',
                        'articulation_idea_clearly_defined': None,
                        'error': 'Empty transcript' if not transcript else 'Not processed'
                    })
                
                results.append(result_row)
            
            # Create output DataFrame
            output_df = pd.DataFrame(results)
            
        except Exception as e:
            logger.error(f"Batch processor error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': f'Batch processing error: {str(e)}'}), 500
        
        # Create filename with timestamp
        filename = f'pitch_video_evaluations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Create results directory if it doesn't exist
        results_dir = os.path.join(BASE_DIR, 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        # Save CSV file to disk (for large files that might timeout on download)
        file_path = os.path.join(results_dir, filename)
        output_df.to_csv(file_path, index=False)
        logger.info(f"CSV file saved to: {file_path}")
        
        # Also prepare for download
        mem = io.BytesIO()
        output_df.to_csv(mem, index=False)
        mem.seek(0)
        
        try:
            # Return CSV file for download
            return send_file(
                mem,
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            # If download fails, at least the file is saved to disk
            logger.error(f"Failed to send file for download: {str(e)}")
            logger.info(f"File is saved at: {file_path}")
            return jsonify({
                'error': 'Download failed, but file was saved',
                'file_path': file_path,
                'message': f'File saved to: {file_path}',
                'download_url': f'/api/download-result/{filename}'
            }), 200
    
    except Exception as e:
        logger.error(f"Batch processing error: {str(e)}")
        return jsonify({'error': f'Processing error: {str(e)}'}), 500


@app.route('/api/evaluate/llm', methods=['POST'])
def evaluate_llm():
    """Proxy endpoint for LLM API calls to avoid CORS issues"""
    # #region agent log
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cursor', 'debug.log'), 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"app.py:evaluate_llm","message":"Request received","data":{"origin":request.headers.get('Origin','none'),"method":request.method},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
    except: pass
    # #endregion
    try:
        data = request.json
        model = data.get('model')
        system_prompt = data.get('system_prompt')
        user_input = data.get('user_input')
        temperature = float(data.get('temperature', 0.3))
        api_key = data.get('api_key')
        
        if not all([model, system_prompt, user_input, api_key]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Model configurations
        model_configs = {
            'gpt-5': {'endpoint': 'https://api.openai.com/v1/chat/completions', 'model_name': 'gpt-5', 'provider': 'openai'},
            'gpt-5.1': {'endpoint': 'https://api.openai.com/v1/chat/completions', 'model_name': 'gpt-5.1', 'provider': 'openai'},
            'gpt-5.1-codex': {'endpoint': 'https://api.openai.com/v1/chat/completions', 'model_name': 'gpt-5.1-codex', 'provider': 'openai'},
            'gpt-5-mini': {'endpoint': 'https://api.openai.com/v1/chat/completions', 'model_name': 'gpt-5-mini', 'provider': 'openai'},
            'gpt-5-nano': {'endpoint': 'https://api.openai.com/v1/chat/completions', 'model_name': 'gpt-5-nano', 'provider': 'openai'},
            'gpt-4': {'endpoint': 'https://api.openai.com/v1/chat/completions', 'model_name': 'gpt-4', 'provider': 'openai'},
            'gpt-3.5-turbo': {'endpoint': 'https://api.openai.com/v1/chat/completions', 'model_name': 'gpt-3.5-turbo', 'provider': 'openai'},
            'claude-3-opus': {'endpoint': 'https://api.anthropic.com/v1/messages', 'model_name': 'claude-3-opus-20240229', 'provider': 'anthropic'},
            'claude-3-sonnet': {'endpoint': 'https://api.anthropic.com/v1/messages', 'model_name': 'claude-3-sonnet-20240229', 'provider': 'anthropic'},
            'gemini-pro': {'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent', 'model_name': 'gemini-pro', 'provider': 'google'}
        }
        
        if model not in model_configs:
            return jsonify({'error': 'Invalid model selected'}), 400
        
        config = model_configs[model]
        endpoint = config['endpoint']
        
        # Prepare request based on provider
        if config['provider'] == 'openai':
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            # GPT-5 models use max_completion_tokens, older models use max_tokens
            gpt5_models = ['gpt-5', 'gpt-5.1', 'gpt-5.1-codex', 'gpt-5-mini', 'gpt-5-nano']
            body = {
                'model': config['model_name'],
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_input}
                ],
                'temperature': temperature
            }
            # Use max_completion_tokens for GPT-5 models, max_tokens for older models
            if config['model_name'] in gpt5_models:
                body['max_completion_tokens'] = 2000
            else:
                body['max_tokens'] = 2000
        elif config['provider'] == 'anthropic':
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01'
            }
            body = {
                'model': config['model_name'],
                'max_tokens': 2000,
                'temperature': temperature,
                'system': system_prompt,
                'messages': [
                    {'role': 'user', 'content': user_input}
                ]
            }
        elif config['provider'] == 'google':
            endpoint = f"{endpoint}?key={api_key}"
            headers = {
                'Content-Type': 'application/json'
            }
            body = {
                'contents': [{
                    'parts': [{
                        'text': f'{system_prompt}\n\nUser Input:\n{user_input}'
                    }]
                }],
                'generationConfig': {
                    'temperature': temperature,
                    'maxOutputTokens': 2000
                }
            }
        
        # Make API request
        response = requests.post(endpoint, headers=headers, json=body, timeout=60)
        
        if not response.ok:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            return jsonify({
                'error': error_data.get('error', {}).get('message', f'API request failed: {response.status_code} {response.reason}')
            }), response.status_code
        
        # Extract response text based on provider
        response_data = response.json()
        if config['provider'] == 'openai':
            content = response_data['choices'][0]['message']['content']
        elif config['provider'] == 'anthropic':
            content = response_data['content'][0]['text']
        elif config['provider'] == 'google':
            content = response_data['candidates'][0]['content']['parts'][0]['text']
        
        return jsonify({'content': content}), 200
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timeout. Please try again.'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500


@app.route('/api/batch/idea-generation', methods=['POST'])
def batch_idea_generation():
    """Card 1: batch-generate structured Idea Bank entries from pitch transcripts.

    Input CSV requires a 'transcript' column. If an 'idea_id' column is present,
    those IDs are honored as-is; otherwise a fresh idea_id is generated per row.
    Returns the input CSV with appended idea fields + idea_id + status.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are allowed'}), 400

        api_key = request.form.get('api_key', '').strip()
        system_prompt = (request.form.get('system_prompt') or '').strip()
        try:
            text_concurrency = int(request.form.get('text_concurrency', 10))
        except ValueError:
            text_concurrency = 10
        text_concurrency = max(1, min(20, text_concurrency))

        if not api_key:
            return jsonify({'error': 'API key is required. Provide it via the header controls.'}), 400
        if not system_prompt:
            return jsonify({'error': 'System prompt is required. Edit it in the batch prompt box or the single-idea tab.'}), 400

        try:
            df = pd.read_csv(file)
        except Exception as e:
            return jsonify({'error': f'Invalid CSV file: {str(e)}'}), 400

        if 'transcript' not in df.columns:
            return jsonify({
                'error': "Missing required column 'transcript'",
                'expected': ['transcript'],
                'found': list(df.columns),
            }), 400

        df = df.copy().reset_index(drop=True)
        # Honor existing idea_id values; generate fresh IDs only for rows that lack one.
        if 'idea_id' in df.columns:
            idea_ids = [
                (str(v).strip() if (v is not None and str(v).strip()) else generate_idea_id())
                for v in df['idea_id'].tolist()
            ]
        else:
            idea_ids = [generate_idea_id() for _ in range(len(df))]

        transcripts = df['transcript'].fillna('').astype(str).tolist()
        logger.info(f"Card 1 (idea-generation): processing {len(transcripts)} transcripts with concurrency={text_concurrency}")

        try:
            raw_results = run_batch_evaluation(
                ideas_list=transcripts,
                system_prompt=system_prompt,
                api_key=api_key,
                max_concurrent=text_concurrency,
                user_message_prefix="Transcript:",
                item_label="IDEA-GEN",
            )
        except Exception as e:
            logger.error(f"Card 1 processing error: {e}")
            import traceback; logger.error(traceback.format_exc())
            return jsonify({'error': f'Batch processing error: {str(e)}'}), 500

        # Drop pre-existing idea_id column so the freshly built one wins ordering.
        if 'idea_id' in df.columns:
            df = df.drop(columns=['idea_id'])
        output_df = parse_idea_generation_results_to_dataframe(df, raw_results, idea_ids)

        filename = f'idea_generation_batch_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        results_dir = os.path.join(BASE_DIR, 'results')
        os.makedirs(results_dir, exist_ok=True)
        file_path = os.path.join(results_dir, filename)
        output_df.to_csv(file_path, index=False)
        logger.info(f"Card 1 output saved to: {file_path}")

        mem = io.BytesIO()
        output_df.to_csv(mem, index=False)
        mem.seek(0)
        try:
            return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=filename)
        except Exception as e:
            logger.error(f"Failed to send Card 1 file for download: {e}")
            return jsonify({
                'message': f'File saved to: {file_path}',
                'file_path': file_path,
                'download_url': f'/api/download-result/{filename}',
            }), 200
    except Exception as e:
        logger.error(f"Card 1 endpoint error: {e}")
        return jsonify({'error': f'Processing error: {str(e)}'}), 500


@app.route('/api/batch/idea-images', methods=['POST'])
def batch_idea_images():
    """Card 2: batch-generate representative images for ideas.

    Input CSV requires columns: idea_id, idea_title, problem_or_opportunity,
    solution_details, potential_impact, status. Only rows with status == 'ok'
    are processed. Files are written to the configured storage backend (local
    by default — see image_storage.py). Returns the input CSV with appended
    image_status / image_*_path columns.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are allowed'}), 400

        api_key = request.form.get('api_key', '').strip()
        image_template = (request.form.get('image_prompt') or '').strip()
        image_model = (request.form.get('image_model') or 'gpt-image-2').strip() or 'gpt-image-2'
        skip_existing = (request.form.get('skip_existing', 'true').strip().lower() != 'false')
        try:
            image_concurrency = int(request.form.get('image_concurrency', 3))
        except ValueError:
            image_concurrency = 3
        image_concurrency = max(1, min(5, image_concurrency))

        if not api_key:
            return jsonify({'error': 'API key is required.'}), 400
        if not image_template:
            return jsonify({'error': 'Image prompt template is required.'}), 400

        try:
            df = pd.read_csv(file)
        except Exception as e:
            return jsonify({'error': f'Invalid CSV file: {str(e)}'}), 400

        required = ['idea_id', 'idea_title', 'problem_or_opportunity',
                    'solution_details', 'potential_impact', 'status']
        missing = [c for c in required if c not in df.columns]
        if missing:
            return jsonify({
                'error': f"Missing required columns: {', '.join(missing)}",
                'expected': required,
                'found': list(df.columns),
            }), 400

        df = df.copy().reset_index(drop=True)
        # Only attempt rows that successfully generated text.
        eligible_mask = (df['status'].astype(str).str.lower() == 'ok')
        eligible_df = df[eligible_mask].reset_index(drop=True)
        eligible_count = len(eligible_df)

        IMAGE_BATCH_HARD_CAP = 200
        if eligible_count > IMAGE_BATCH_HARD_CAP:
            return jsonify({
                'error': (
                    f'{eligible_count} eligible rows exceed the safety cap of {IMAGE_BATCH_HARD_CAP}. '
                    f'Split the CSV and run multiple batches.'
                )
            }), 400

        if eligible_count == 0:
            return jsonify({'error': 'No rows with status="ok" — nothing to process.'}), 400

        logger.info(f"Card 2 (image-batch): {eligible_count} eligible rows, "
                    f"concurrency={image_concurrency}, skip_existing={skip_existing}")

        backend = get_storage_backend()
        idea_rows = eligible_df.to_dict(orient='records')
        processed_idea_ids = [r['idea_id'] for r in idea_rows]

        try:
            image_results = run_image_batch(
                idea_rows=idea_rows,
                image_template=image_template,
                api_key=api_key,
                model=image_model,
                backend=backend,
                max_concurrent=image_concurrency,
                skip_existing=skip_existing,
            )
        except Exception as e:
            logger.error(f"Card 2 processing error: {e}")
            import traceback; logger.error(traceback.format_exc())
            return jsonify({'error': f'Image batch error: {str(e)}'}), 500

        output_df = merge_image_results_into_dataframe(df, image_results, processed_idea_ids)

        filename = f'idea_images_batch_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        results_dir = os.path.join(BASE_DIR, 'results')
        os.makedirs(results_dir, exist_ok=True)
        file_path = os.path.join(results_dir, filename)
        output_df.to_csv(file_path, index=False)
        logger.info(f"Card 2 output saved to: {file_path}")

        mem = io.BytesIO()
        output_df.to_csv(mem, index=False)
        mem.seek(0)
        try:
            return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=filename)
        except Exception as e:
            logger.error(f"Failed to send Card 2 file for download: {e}")
            return jsonify({
                'message': f'File saved to: {file_path}',
                'file_path': file_path,
                'download_url': f'/api/download-result/{filename}',
            }), 200
    except Exception as e:
        logger.error(f"Card 2 endpoint error: {e}")
        return jsonify({'error': f'Processing error: {str(e)}'}), 500


@app.route('/api/images/generate', methods=['POST'])
def generate_image():
    """Proxy endpoint for OpenAI image generation (defaults to gpt-image-2) to avoid CORS."""
    try:
        data = request.json or {}
        prompt = data.get('prompt')
        api_key = data.get('api_key')
        size = data.get('size', '1024x1024')
        model = data.get('model', 'gpt-image-2')

        if not prompt or not api_key:
            return jsonify({'error': 'Missing required parameters: prompt and api_key'}), 400

        endpoint = 'https://api.openai.com/v1/images/generations'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        body = {
            'model': model,
            'prompt': prompt,
            'size': size,
            'n': 1
        }

        response = requests.post(endpoint, headers=headers, json=body, timeout=120)

        if not response.ok:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            return jsonify({
                'error': error_data.get('error', {}).get('message', f'Image API request failed: {response.status_code} {response.reason}')
            }), response.status_code

        response_data = response.json()
        b64 = response_data['data'][0].get('b64_json')
        if not b64:
            return jsonify({'error': 'Image API returned no b64_json payload'}), 502

        return jsonify({'b64_json': b64}), 200

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Image generation timed out. Please try again.'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500


@app.route('/api/batch/idea-images-batch/submit', methods=['POST'])
def submit_idea_images_batch_api():
    """Submit an OpenAI Batch API job for idea image generation."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are allowed'}), 400

        api_key = request.form.get('api_key', '').strip()
        image_template = (request.form.get('image_prompt') or '').strip()
        image_model = (request.form.get('image_model') or 'gpt-image-2').strip() or 'gpt-image-2'

        if not api_key:
            return jsonify({'error': 'API key is required.'}), 400
        if not image_template:
            return jsonify({'error': 'Image prompt template is required.'}), 400

        try:
            df = pd.read_csv(file)
        except Exception as e:
            return jsonify({'error': f'Invalid CSV file: {str(e)}'}), 400

        try:
            job = create_idea_image_batch_job(
                base_dir=BASE_DIR,
                input_df=df,
                api_key=api_key,
                image_template=image_template,
                image_model=image_model,
                source_filename=file.filename,
            )
        except Exception as e:
            logger.error(f"Batch API submit error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': f'Batch submission failed: {str(e)}'}), 500

        return jsonify({
            'message': 'Batch job submitted successfully',
            'job': public_job_view(BASE_DIR, job),
        }), 200
    except Exception as e:
        logger.error(f"Batch API submit route error: {e}")
        return jsonify({'error': f'Processing error: {str(e)}'}), 500


@app.route('/api/batch/idea-images-batch/status/<job_id>', methods=['GET'])
def idea_images_batch_api_status(job_id):
    """Return the latest status for a submitted OpenAI Batch API job."""
    try:
        existing_job = load_idea_image_batch_job(BASE_DIR, job_id)
        if not existing_job:
            return jsonify({'error': 'Batch job not found'}), 404

        api_key = request.args.get('api_key', '').strip()
        if not api_key:
            return jsonify({'error': 'API key is required to refresh batch status.'}), 400

        job = ensure_job_output_ready(BASE_DIR, job_id, api_key)
        if not job:
            return jsonify({'error': 'Batch job not found'}), 404

        return jsonify({
            'job': public_job_view(BASE_DIR, job),
        }), 200
    except Exception as e:
        logger.error(f"Batch API status error for {job_id}: {e}")
        return jsonify({'error': f'Could not refresh batch status: {str(e)}'}), 500


@app.route('/api/batch/idea-images-batch/download/<job_id>', methods=['GET'])
def idea_images_batch_api_download(job_id):
    """Download the CSV produced by the OpenAI Batch API workflow."""
    try:
        job = load_idea_image_batch_job(BASE_DIR, job_id)
        if not job:
            return jsonify({'error': 'Batch job not found'}), 404

        output_path = job.get('output_csv_path') or ''
        if not output_path or not os.path.exists(output_path):
            return jsonify({'error': 'Output CSV is not ready yet'}), 409

        return send_file(
            output_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=job.get('download_filename') or os.path.basename(output_path)
        )
    except Exception as e:
        logger.error(f"Batch API download error for {job_id}: {e}")
        return jsonify({'error': f'Could not download result: {str(e)}'}), 500


if __name__ == '__main__':
    print("Starting Batch Evaluation Processor API...")
    print("Server running on http://localhost:5000")
    print("API endpoints:")
    print("  - POST /api/batch/evaluate/idea-submission")
    print("  - POST /api/batch/evaluate/pitch-video")
    print("  - POST /api/evaluate/llm (proxy for single evaluations)")
    print("  - POST /api/images/generate (proxy for OpenAI image generation)")
    print("  - POST /api/batch/idea-images-batch/submit (Batch API image generation)")
    print("  - GET /api/batch/idea-images-batch/status/<job_id>")
    print("  - GET /api/batch/idea-images-batch/download/<job_id>")
    print("  - POST /api/batch/idea-generation (Card 1: batch text idea generation)")
    print("  - POST /api/batch/idea-images (Card 2: batch image generation)")
    print("  - GET /api/health")
    # Bind to 0.0.0.0 to allow connections from any interface
    app.run(debug=True, host='0.0.0.0', port=5001)
