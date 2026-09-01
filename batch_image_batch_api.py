import base64
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import requests

from batch_processor import (
    crop_to_variants,
    generate_idea_id,
    merge_image_results_into_dataframe,
    run_image_batch,
    substitute_image_placeholders,
)
from image_storage import get_storage_backend


MODULE_NAME = "Image generation for Ideas using Batch API"


def _results_dir(base_dir: str) -> str:
    return os.path.join(base_dir, "results")


def _jobs_root(base_dir: str) -> str:
    return os.path.join(_results_dir(base_dir), "idea_image_batch_api_jobs")


def _ensure_job_dirs(base_dir: str) -> None:
    os.makedirs(_results_dir(base_dir), exist_ok=True)
    os.makedirs(_jobs_root(base_dir), exist_ok=True)


def _job_dir(base_dir: str, job_id: str) -> str:
    return os.path.join(_jobs_root(base_dir), job_id)


def _job_json_path(base_dir: str, job_id: str) -> str:
    return os.path.join(_job_dir(base_dir, job_id), "job.json")


def _source_csv_path(base_dir: str, job_id: str) -> str:
    return os.path.join(_job_dir(base_dir, job_id), "source.csv")


def _input_jsonl_path(base_dir: str, job_id: str) -> str:
    return os.path.join(_job_dir(base_dir, job_id), "input.jsonl")


def _output_csv_path(base_dir: str, job_id: str) -> str:
    return os.path.join(_job_dir(base_dir, job_id), "output.csv")


def _download_filename(job_id: str) -> str:
    return f"idea_images_batch_api_{job_id}.csv"


def _save_json(path: str, payload: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_job(base_dir: str, job_id: str) -> Optional[Dict]:
    path = _job_json_path(base_dir, job_id)
    if not os.path.exists(path):
        return None
    return _load_json(path)


def save_job(base_dir: str, job: Dict) -> Dict:
    _ensure_job_dirs(base_dir)
    job_id = job["job_id"]
    os.makedirs(_job_dir(base_dir, job_id), exist_ok=True)
    job["updated_at"] = datetime.now().isoformat()
    _save_json(_job_json_path(base_dir, job_id), job)
    return job


def _required_columns() -> List[str]:
    return [
        "idea_id",
        "idea_title",
        "problem_or_opportunity",
        "solution_details",
        "potential_impact",
        "status",
    ]


def validate_input_dataframe(df: pd.DataFrame) -> None:
    missing = [c for c in _required_columns() if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(missing)}"
        )


def _eligible_mask(df: pd.DataFrame) -> pd.Series:
    return df["status"].astype(str).str.lower().eq("ok")


def _resolved_prompt(template: str, row: Dict) -> str:
    return substitute_image_placeholders(template, row)


def _make_batch_request_line(custom_id: str, model: str, prompt: str) -> Dict:
    return {
        "custom_id": custom_id,
        "model": model,
        "prompt": prompt,
        "size": "1024x1024",
        "n": 1,
    }


def create_idea_image_batch_job(
    base_dir: str,
    input_df: pd.DataFrame,
    api_key: str,
    image_template: str,
    image_model: str,
    source_filename: str,
) -> Dict:
    validate_input_dataframe(input_df)
    _ensure_job_dirs(base_dir)

    job_id = f"ideaimg_{uuid.uuid4().hex[:12]}"
    job_dir = _job_dir(base_dir, job_id)
    os.makedirs(job_dir, exist_ok=True)

    source_csv = _source_csv_path(base_dir, job_id)
    input_jsonl = _input_jsonl_path(base_dir, job_id)
    output_csv = _output_csv_path(base_dir, job_id)

    df = input_df.copy().reset_index(drop=True)
    df.to_csv(source_csv, index=False)

    eligible = df[_eligible_mask(df)].copy().reset_index(drop=True)
    if eligible.empty:
        raise ValueError("No rows with status='ok' found in the CSV.")

    input_rows: List[Dict] = []
    for idx, row in eligible.iterrows():
        row_dict = row.to_dict()
        idea_id = str(row_dict.get("idea_id") or "").strip()
        if not idea_id:
            idea_id = generate_idea_id()
        row_dict["idea_id"] = idea_id
        prompt = _resolved_prompt(image_template, row_dict)
        input_rows.append({
            "row_index": int(idx),
            "idea_id": idea_id,
            "prompt": prompt,
            "row": row_dict,
        })

    with open(input_jsonl, "w", encoding="utf-8") as f:
        for item in input_rows:
            f.write(json.dumps(_make_batch_request_line(item["idea_id"], image_model, item["prompt"]), ensure_ascii=False))
            f.write("\n")

    image_results = run_image_batch(
        idea_rows=[item["row"] for item in input_rows],
        image_template=image_template,
        api_key=api_key,
        model=image_model,
        backend=get_storage_backend(),
        max_concurrent=3,
        skip_existing=True,
    )

    job = {
        "job_id": job_id,
        "module": MODULE_NAME,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "source_filename": source_filename,
        "image_model": image_model,
        "image_template": image_template,
        "source_csv_path": source_csv,
        "input_jsonl_path": input_jsonl,
        "output_csv_path": output_csv,
        "download_filename": _download_filename(job_id),
        "input_row_count": int(len(df)),
        "eligible_row_count": int(len(eligible)),
        "input_rows": input_rows,
        "batch": {
            "id": f"local_{job_id}",
            "status": "completed",
            "input_file_id": None,
            "output_file_id": None,
            "error_file_id": None,
            "request_counts": {
                "total": int(len(image_results)),
                "completed": int(sum(1 for r in image_results if (r.get("image_status") or "").lower() == "ok")),
                "failed": int(sum(1 for r in image_results if (r.get("image_status") or "").lower() == "error")),
            },
            "created_at": None,
            "expires_at": None,
        },
        "materialized": True,
        "download_ready": True,
        "error": None,
    }

    out_df = merge_image_results_into_dataframe(df, image_results, [item["idea_id"] for item in input_rows])
    out_df["batch_job_id"] = job["job_id"]
    out_df["batch_status"] = job["batch"].get("status") or ""
    out_df["batch_request_counts"] = json.dumps(job["batch"].get("request_counts", {}), ensure_ascii=False)
    out_df.to_csv(output_csv, index=False)

    job["download_url"] = f"/api/batch/idea-images-batch/download/{job['job_id']}"
    return save_job(base_dir, job)


def _extract_image_b64_from_batch_line(line_obj: Dict) -> Optional[str]:
    response_obj = line_obj.get("response") or {}
    body = response_obj.get("body") if isinstance(response_obj, dict) else None
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except Exception:
            body = None
    if not isinstance(body, dict):
        body = response_obj if isinstance(response_obj, dict) else {}

    data = body.get("data") or []
    if isinstance(data, list) and data:
        first = data[0] or {}
        if isinstance(first, dict):
            return first.get("b64_json") or first.get("b64") or first.get("image_base64")
    return None


def _row_result_template(idea_id: str) -> Dict:
    return {
        "idea_id": idea_id,
        "image_status": "error",
        "image_error": "",
        "image_large_path": "",
        "image_medium_path": "",
        "image_small_path": "",
    }


def _finalize_output_rows(base_dir: str, job: Dict, api_key: str) -> List[Dict]:
    backend = get_storage_backend()
    by_id = {str(item["idea_id"]): item for item in job.get("input_rows", [])}
    results_by_id: Dict[str, Dict] = {}

    batch_id = job.get("batch", {}).get("id")
    if not batch_id:
        raise RuntimeError("Batch job has no OpenAI batch id")

    headers = {"Authorization": f"Bearer {api_key}"}
    batch_resp = requests.get(f"{OPENAI_BATCHES_URL}/{batch_id}", headers=headers, timeout=120)
    if not batch_resp.ok:
        error_data = batch_resp.json() if batch_resp.headers.get("content-type", "").startswith("application/json") else {}
        message = error_data.get("error", {}).get("message", batch_resp.text[:500])
        raise RuntimeError(f"Batch status fetch failed: {message}")
    batch_payload = batch_resp.json()
    job["batch"]["status"] = batch_payload.get("status", job["batch"].get("status"))
    job["batch"]["output_file_id"] = batch_payload.get("output_file_id") or job["batch"].get("output_file_id")
    job["batch"]["error_file_id"] = batch_payload.get("error_file_id") or job["batch"].get("error_file_id")
    job["batch"]["request_counts"] = batch_payload.get("request_counts", job["batch"].get("request_counts", {}))
    job["batch"]["completed_at"] = batch_payload.get("completed_at")
    job["batch"]["failed_at"] = batch_payload.get("failed_at")
    job["batch"]["cancelled_at"] = batch_payload.get("cancelled_at")
    job["batch"]["expired_at"] = batch_payload.get("expired_at")
    job["updated_at"] = datetime.now().isoformat()

    status = str(job["batch"].get("status") or "").lower()
    if status != "completed":
        return []

    output_file_id = job["batch"].get("output_file_id")
    if not output_file_id:
        raise RuntimeError("Batch completed without an output file id")

    output_resp = requests.get(f"{OPENAI_FILES_URL}/{output_file_id}/content", headers=headers, stream=True, timeout=300)
    if not output_resp.ok:
        message = output_resp.text[:500]
        raise RuntimeError(f"Batch output download failed: {message}")

    for raw_line in output_resp.iter_lines(decode_unicode=True):
        if not raw_line:
            continue
        line_obj = json.loads(raw_line)
        custom_id = str(line_obj.get("custom_id") or line_obj.get("id") or "").strip()
        if not custom_id:
            continue

        row_result = _row_result_template(custom_id)
        input_row = by_id.get(custom_id)
        if not input_row:
            row_result["image_error"] = "No matching input row found for batch result"
            results_by_id[custom_id] = row_result
            continue

        if line_obj.get("error"):
            err = line_obj["error"]
            row_result["image_error"] = err.get("message") if isinstance(err, dict) else str(err)
            results_by_id[custom_id] = row_result
            continue

        b64 = _extract_image_b64_from_batch_line(line_obj)
        if not b64:
            row_result["image_error"] = "Batch output did not include image data"
            results_by_id[custom_id] = row_result
            continue

        try:
            source_png = base64.b64decode(b64)
            variants = crop_to_variants(source_png)
            keys = {
                "large": f"ideas/{custom_id}/large.png",
                "medium": f"ideas/{custom_id}/medium.png",
                "small": f"ideas/{custom_id}/small.png",
            }
            for variant_name, key in keys.items():
                backend.put(key, variants[variant_name])
            row_result.update({
                "image_status": "ok",
                "image_error": "",
                "image_large_path": keys["large"],
                "image_medium_path": keys["medium"],
                "image_small_path": keys["small"],
            })
        except Exception as exc:
            row_result["image_error"] = f"{type(exc).__name__}: {exc}"

        results_by_id[custom_id] = row_result

    out_df = pd.read_csv(job["source_csv_path"]).copy().reset_index(drop=True)
    image_statuses: List[str] = []
    image_errors: List[str] = []
    large_paths: List[str] = []
    medium_paths: List[str] = []
    small_paths: List[str] = []

    for _, row in out_df.iterrows():
        idea_id = str(row.get("idea_id") or "").strip()
        if not idea_id:
            image_statuses.append("error")
            image_errors.append("Missing idea_id")
            large_paths.append("")
            medium_paths.append("")
            small_paths.append("")
            continue

        if str(row.get("status") or "").strip().lower() != "ok":
            image_statuses.append("skipped")
            image_errors.append("row skipped (status != ok in input CSV)")
            large_paths.append("")
            medium_paths.append("")
            small_paths.append("")
            continue

        result_row = results_by_id.get(idea_id)
        if not result_row:
            image_statuses.append("error")
            image_errors.append("No batch result found")
            large_paths.append("")
            medium_paths.append("")
            small_paths.append("")
            continue

        image_statuses.append(result_row.get("image_status") or "error")
        image_errors.append(result_row.get("image_error") or "")
        large_paths.append(result_row.get("image_large_path") or "")
        medium_paths.append(result_row.get("image_medium_path") or "")
        small_paths.append(result_row.get("image_small_path") or "")

    out_df["image_status"] = image_statuses
    out_df["image_error"] = image_errors
    out_df["image_large_path"] = large_paths
    out_df["image_medium_path"] = medium_paths
    out_df["image_small_path"] = small_paths
    out_df["batch_job_id"] = job["job_id"]
    out_df["batch_status"] = job["batch"].get("status") or ""
    out_df["batch_request_counts"] = json.dumps(job["batch"].get("request_counts", {}), ensure_ascii=False)

    out_df.to_csv(job["output_csv_path"], index=False)
    job["materialized"] = True
    job["download_ready"] = True
    job["download_url"] = f"/api/batch/idea-images-batch/download/{job['job_id']}"
    job["updated_at"] = datetime.now().isoformat()
    return save_job(base_dir, job), out_df


def refresh_idea_image_batch_job(base_dir: str, job_id: str, api_key: str) -> Dict:
    job = load_job(base_dir, job_id)
    if not job:
        raise ValueError(f"Job not found: {job_id}")

    if job.get("materialized") and os.path.exists(job.get("output_csv_path") or ""):
        return job

    return save_job(base_dir, job)


def public_job_view(base_dir: str, job: Dict) -> Dict:
    output_csv_exists = os.path.exists(job.get("output_csv_path") or "")
    return {
        "job_id": job.get("job_id"),
        "module": job.get("module"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "source_filename": job.get("source_filename"),
        "image_model": job.get("image_model"),
        "input_row_count": job.get("input_row_count"),
        "eligible_row_count": job.get("eligible_row_count"),
        "batch": job.get("batch", {}),
        "materialized": bool(job.get("materialized")),
        "download_ready": bool(job.get("download_ready") or output_csv_exists),
        "download_filename": job.get("download_filename"),
        "download_url": job.get("download_url") if (job.get("download_ready") or output_csv_exists) else None,
        "error": job.get("error"),
    }


def ensure_job_output_ready(base_dir: str, job_id: str, api_key: str) -> Dict:
    job = refresh_idea_image_batch_job(base_dir, job_id, api_key)
    if job and not job.get("download_url") and os.path.exists(job.get("output_csv_path") or ""):
        job["download_url"] = f"/api/batch/idea-images-batch/download/{job_id}"
        save_job(base_dir, job)
    return job


def output_csv_exists(base_dir: str, job_id: str) -> bool:
    job = load_job(base_dir, job_id)
    if not job:
        return False
    return os.path.exists(job.get("output_csv_path") or "")
