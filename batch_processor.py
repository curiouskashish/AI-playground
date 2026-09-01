import asyncio
import json
import pandas as pd
import httpx
from typing import List, Dict, Callable, Optional
import time
from concurrent.futures import ThreadPoolExecutor
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# OpenAI API endpoint
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Global timing tracker
timing_tracker = {
    "active_requests": 0,
    "max_concurrent": 0,
    "request_times": [],
    "batch_start": None
}

def parse_json_response(content: str) -> Dict:
    """Parse JSON from LLM response with multiple fallback strategies"""
    if not content or not content.strip():
        raise ValueError("Empty response content")
    
    # Try direct JSON parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Try extracting JSON from markdown code blocks
    import re
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try finding JSON object in the text
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Last resort: try to fix common JSON issues
    # Remove leading/trailing whitespace and non-JSON text
    cleaned = content.strip()
    # Remove any text before first {
    start_idx = cleaned.find('{')
    if start_idx >= 0:
        cleaned = cleaned[start_idx:]
    # Remove any text after last }
    end_idx = cleaned.rfind('}')
    if end_idx >= 0:
        cleaned = cleaned[:end_idx + 1]
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse JSON from response. Content preview: {content[:500]}")

async def evaluate_single_idea_httpx(
    client: httpx.AsyncClient,
    idea: str,
    idea_id: int,
    system_prompt: str,
    api_key: str,
    semaphore: asyncio.Semaphore,
    max_retries: int = 3,
    user_message_prefix: str = "Evaluate this business idea:",
    item_label: str = "IDEA",
    max_completion_tokens: int = 2048
) -> Dict:
    """Evaluate a single item using httpx with retry logic and better error handling
    
    Args:
        client: httpx AsyncClient for making requests
        idea: The text content to evaluate (business idea or transcript)
        idea_id: ID for tracking/logging
        system_prompt: System prompt for the LLM
        api_key: OpenAI API key
        semaphore: Semaphore for concurrency control
        max_retries: Number of retry attempts
        user_message_prefix: Prefix for the user message (e.g., "Evaluate this business idea:" or "Evaluate this pitch video transcript:")
        item_label: Label for logging (e.g., "IDEA" or "TRANSCRIPT")
        max_completion_tokens: Max tokens in LLM response (smaller for sector-only)
    """
    async with semaphore:
        # Track concurrent requests
        timing_tracker["active_requests"] += 1
        if timing_tracker["active_requests"] > timing_tracker["max_concurrent"]:
            timing_tracker["max_concurrent"] = timing_tracker["active_requests"]
        
        request_start = time.time()
        if timing_tracker["batch_start"]:
            relative_start = request_start - timing_tracker["batch_start"]
            logger.info(f"[{item_label} {idea_id:2d}] STARTED at +{relative_start:.2f}s (Active: {timing_tracker['active_requests']})")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-5-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{user_message_prefix}\n\n{idea}"}
            ],
            "temperature": 1,
            "max_completion_tokens": max_completion_tokens,
            "response_format": {"type": "json_object"}
        }
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(max_retries):
            try:
                # Exponential backoff: wait 1s, 2s, 4s
                if attempt > 0:
                    wait_time = 2 ** (attempt - 1)
                    logger.warning(f"[{item_label} {idea_id:2d}] Retry attempt {attempt + 1}/{max_retries} after {wait_time}s wait")
                    await asyncio.sleep(wait_time)
                
                # Make the actual HTTP request
                response = await client.post(
                    OPENAI_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=90.0  # Increased timeout
                )
                
                # Check for rate limiting or server errors
                if response.status_code == 429:
                    # Rate limited - wait longer
                    retry_after = int(response.headers.get('Retry-After', 10))
                    logger.warning(f"[{item_label} {idea_id:2d}] Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                
                # Parse response
                try:
                    response_data = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"[{item_label} {idea_id:2d}] Response is not valid JSON: {response.text[:500]}")
                    last_error = f"API response not JSON: {str(e)}"
                    continue
                
                # Extract content
                if "choices" not in response_data or not response_data["choices"]:
                    logger.error(f"[{item_label} {idea_id:2d}] No choices in response: {response_data}")
                    last_error = "No choices in API response"
                    continue
                
                choice = response_data["choices"][0]
                
                # Check for finish_reason to understand why content might be empty
                finish_reason = choice.get("finish_reason", "unknown")
                if finish_reason != "stop":
                    logger.warning(f"[{item_label} {idea_id:2d}] Finish reason: {finish_reason} (may indicate incomplete response)")
                
                # Check if message exists
                if "message" not in choice:
                    logger.error(f"[{item_label} {idea_id:2d}] No message in choice: {choice}")
                    last_error = f"No message in response (finish_reason: {finish_reason})"
                    if attempt < max_retries - 1:
                        continue
                    break
                
                # Get content - handle None, empty string, or missing key
                message = choice["message"]
                content = message.get("content")
                
                # Handle None or empty content
                if content is None:
                    content = ""
                
                if not content or not str(content).strip():
                    # Log the full response structure for debugging
                    logger.error(f"[{item_label} {idea_id:2d}] Empty or None content in response")
                    logger.error(f"[{item_label} {idea_id:2d}] Message object: {json.dumps(message, indent=2)}")
                    logger.error(f"[{item_label} {idea_id:2d}] Finish reason: {finish_reason}")
                    logger.error(f"[{item_label} {idea_id:2d}] Full response keys: {list(response_data.keys())}")
                    
                    # Check if there's an error message in the response
                    if "error" in response_data:
                        error_msg = response_data["error"]
                        last_error = f"API error: {error_msg.get('message', str(error_msg))}"
                    elif finish_reason == "length":
                        # Response was cut off due to length - increase tokens and retry
                        logger.warning(f"[{item_label} {idea_id:2d}] Response cut off due to length, increasing tokens and retrying")
                        payload["max_completion_tokens"] = 4096  # Increase significantly
                        last_error = f"Response cut off (finish_reason: length)"
                        if attempt < max_retries - 1:
                            continue
                    elif finish_reason == "content_filter":
                        # Content was filtered - retry with different approach
                        logger.warning(f"[{item_label} {idea_id:2d}] Content filtered, retrying")
                        last_error = f"Content filtered by API (finish_reason: content_filter)"
                        if attempt < max_retries - 1:
                            continue
                    else:
                        last_error = f"Empty content in API response (finish_reason: {finish_reason})"
                        # Always retry for empty content (unless it's the last attempt)
                        if attempt < max_retries - 1:
                            logger.warning(f"[{item_label} {idea_id:2d}] Retrying due to empty content")
                            continue
                        else:
                            break
                
                # Parse JSON with improved error handling
                try:
                    result_json = parse_json_response(content)
                except ValueError as e:
                    logger.error(f"[{item_label} {idea_id:2d}] JSON parse error: {e}")
                    logger.error(f"[{item_label} {idea_id:2d}] Raw content: {content[:1000]}")
                    last_error = f"JSON parsing error: {str(e)}"
                    continue
                
                # Success!
                request_elapsed = time.time() - request_start
                timing_tracker["request_times"].append(request_elapsed)
                timing_tracker["active_requests"] -= 1
                
                if timing_tracker["batch_start"]:
                    relative_end = time.time() - timing_tracker["batch_start"]
                    logger.info(f"[{item_label} {idea_id:2d}] COMPLETED at +{relative_end:.2f}s (Took {request_elapsed:.2f}s, Active: {timing_tracker['active_requests']})")
                
                return {
                    "id": idea_id,
                    "idea": idea,
                    "result": result_json,
                    "status": "success",
                    "error": None
                }
                
            except httpx.HTTPStatusError as e:
                request_elapsed = time.time() - request_start
                error_text = e.response.text[:500] if hasattr(e.response, 'text') else str(e)
                logger.error(f"[{item_label} {idea_id:2d}] HTTP {e.response.status_code} on attempt {attempt + 1}: {error_text}")
                last_error = f"HTTP {e.response.status_code}: {error_text[:200]}"
                
                # Don't retry on client errors (4xx) except 429
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    break
                    
            except httpx.TimeoutException as e:
                logger.warning(f"[{item_label} {idea_id:2d}] Timeout on attempt {attempt + 1}")
                last_error = f"Request timeout: {str(e)}"
                
            except Exception as e:
                request_elapsed = time.time() - request_start
                logger.error(f"[{item_label} {idea_id:2d}] Exception on attempt {attempt + 1}: {type(e).__name__}: {e}")
                last_error = f"{type(e).__name__}: {str(e)}"
        
        # All retries failed
        timing_tracker["active_requests"] -= 1
        logger.error(f"[{item_label} {idea_id:2d}] FAILED after {max_retries} attempts: {last_error}")
        return {
            "id": idea_id,
            "idea": idea,
            "result": None,
            "status": "error",
            "error": last_error or "Unknown error after retries"
        }

async def process_ideas_batch(
    ideas_list: List[str],
    system_prompt: str,
    api_key: str,
    max_concurrent: int = 10,  # Reduced default to avoid rate limits
    progress_callback: Optional[Callable[[int, int], None]] = None,
    user_message_prefix: str = "Evaluate this business idea:",
    item_label: str = "IDEA",
    max_completion_tokens: int = 2048
) -> List[Dict]:
    """Process all items with controlled concurrency using httpx for true async HTTP
    
    Args:
        ideas_list: List of text items to evaluate (business ideas or transcripts)
        system_prompt: System prompt for the LLM
        api_key: OpenAI API key
        max_concurrent: Maximum number of concurrent API requests
        progress_callback: Optional callback function(completed, total) for progress updates
        user_message_prefix: Prefix for the user message sent to LLM
        item_label: Label for logging (e.g., "IDEA" or "TRANSCRIPT")
        max_completion_tokens: Max tokens in LLM response (e.g. 128 for sector-only)
    """
    
    # Reset timing tracker
    timing_tracker["active_requests"] = 0
    timing_tracker["max_concurrent"] = 0
    timing_tracker["request_times"] = []
    timing_tracker["batch_start"] = time.time()
    
    total = len(ideas_list)
    logger.info(f"=" * 60)
    logger.info(f"Starting batch processing of {total} {item_label.lower()}s with max_concurrent={max_concurrent}")
    logger.info(f"=" * 60)
    
    # Create semaphore for rate limiting
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Track progress
    completed_count = {"count": 0}
    lock = asyncio.Lock()
    
    # Configure httpx client with connection pooling - CRITICAL for concurrency
    limits = httpx.Limits(
        max_keepalive_connections=max_concurrent * 2,
        max_connections=max_concurrent * 2 + 10
    )
    
    async with httpx.AsyncClient(
        limits=limits,
        timeout=httpx.Timeout(60.0, connect=10.0)
    ) as client:
        
        async def evaluate_with_progress(idea: str, idea_id: int) -> Dict:
            result = await evaluate_single_idea_httpx(
                client=client,
                idea=idea,
                idea_id=idea_id,
                system_prompt=system_prompt,
                api_key=api_key,
                semaphore=semaphore,
                max_retries=3,
                user_message_prefix=user_message_prefix,
                item_label=item_label,
                max_completion_tokens=max_completion_tokens
            )
            
            # Update progress
            async with lock:
                completed_count["count"] += 1
                current = completed_count["count"]
                if progress_callback:
                    try:
                        progress_callback(current, total)
                    except:
                        pass
            
            return result
        
        # Create all tasks IMMEDIATELY - this is critical for concurrency
        logger.info(f"Creating {total} tasks...")
        tasks = [
            asyncio.create_task(evaluate_with_progress(idea, idx))
            for idx, idea in enumerate(ideas_list)
        ]
        
        logger.info(f"All {len(tasks)} tasks created. Starting concurrent execution...")
        logger.info(f"Expected behavior: Multiple 'STARTED' messages should appear almost simultaneously")
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - timing_tracker["batch_start"]
        avg_time = elapsed / total if total > 0 else 0
        avg_request_time = sum(timing_tracker["request_times"]) / len(timing_tracker["request_times"]) if timing_tracker["request_times"] else 0
        
        logger.info(f"=" * 60)
        logger.info(f"BATCH COMPLETE:")
        logger.info(f"  Total time: {elapsed:.2f}s")
        logger.info(f"  Average per idea: {avg_time:.2f}s")
        logger.info(f"  Average request time: {avg_request_time:.2f}s")
        logger.info(f"  Max concurrent requests: {timing_tracker['max_concurrent']}")
        logger.info(f"  Expected time if sequential: {avg_request_time * total:.2f}s")
        logger.info(f"  Speedup: {avg_request_time * total / elapsed:.2f}x" if elapsed > 0 else "  Speedup: N/A")
        logger.info(f"=" * 60)
    
    # Handle any exceptions that were returned
    processed_results = []
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                "id": idx,
                "idea": ideas_list[idx],
                "result": None,
                "status": "error",
                "error": str(result)
            })
        else:
            processed_results.append(result)
    
    # Sort by original ID to maintain order
    processed_results.sort(key=lambda x: x["id"])
    return processed_results

def run_batch_evaluation(
    ideas_list: List[str],
    system_prompt: str,
    api_key: str,
    max_concurrent: int = 10,  # Reduced default to avoid rate limits
    progress_callback: Optional[Callable[[int, int], None]] = None,
    user_message_prefix: str = "Evaluate this business idea:",
    item_label: str = "IDEA",
    max_completion_tokens: int = 2048
) -> List[Dict]:
    """
    Synchronous wrapper for async batch processing.
    
    Args:
        ideas_list: List of text items to evaluate (business ideas or transcripts)
        system_prompt: System prompt for the LLM
        api_key: OpenAI API key
        max_concurrent: Maximum number of concurrent API requests (default: 10)
        progress_callback: Optional callback function(completed, total) for progress updates
        user_message_prefix: Prefix for the user message sent to LLM (e.g., "Evaluate this business idea:" or "Evaluate this pitch video transcript:")
        item_label: Label for logging (e.g., "IDEA" or "TRANSCRIPT")
        max_completion_tokens: Max tokens in LLM response (e.g. 128 for sector-only)
    
    Returns:
        List of evaluation results
    """
    
    def run_in_thread():
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                process_ideas_batch(
                    ideas_list=ideas_list,
                    system_prompt=system_prompt,
                    api_key=api_key,
                    max_concurrent=max_concurrent,
                    progress_callback=progress_callback,
                    user_message_prefix=user_message_prefix,
                    item_label=item_label,
                    max_completion_tokens=max_completion_tokens
                )
            )
        finally:
            loop.close()
    
    # Run in a separate thread to avoid event loop conflicts
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_thread)
        return future.result()

def parse_results_to_dataframe(results: List[Dict]) -> pd.DataFrame:
    """Convert evaluation results to a structured DataFrame"""
    
    rows = []
    for r in results:
        row = {
            "id": r["id"],
            "idea": r["idea"],
            "status": r["status"],
            "error": r["error"]
        }
        
        if r["status"] == "success" and r["result"]:
            res = r["result"]
            
            # Sector
            row["sector"] = res.get("sector", "")
            
            # Multiple ideas (top-level boolean)
            multi = res.get("multiple_ideas")
            if multi is None:
                multi = res.get("has_multiple_ideas")
            row["multiple_ideas"] = multi
            
            # Legibility (prompt uses "clarity" and "coherence"; fallback to is_clear/is_coherent)
            legibility = res.get("legibility", {})
            clarity_obj = legibility.get("clarity") or legibility.get("is_clear") or {}
            coherence_obj = legibility.get("coherence") or legibility.get("is_coherent") or {}
            row["is_clear"] = clarity_obj.get("value", None)
            row["is_clear_reason"] = clarity_obj.get("reason", "")
            row["is_coherent"] = coherence_obj.get("value", None)
            row["is_coherent_reason"] = coherence_obj.get("reason", "")
            
            # Specificity (prompt uses "detailed", "concrete", "score"; fallback to old keys)
            specificity = res.get("specificity", {})
            detailed_obj = specificity.get("detailed") or specificity.get("is_detailed_enough") or {}
            concrete_obj = specificity.get("concrete") or specificity.get("is_clearly_defined") or {}
            row["is_detailed_enough"] = detailed_obj.get("value", None)
            row["is_detailed_enough_reason"] = detailed_obj.get("reason", "")
            row["is_clearly_defined"] = concrete_obj.get("value", None)
            row["is_clearly_defined_reason"] = concrete_obj.get("reason", "")
            row["specificity_score"] = specificity.get("score", None)
            
            # Executability (prompt uses "feasible" and "actionable"; fallback to is_*)
            executability = res.get("executability", {})
            feasible_obj = executability.get("feasible") or executability.get("is_feasible") or {}
            actionable_obj = executability.get("actionable") or executability.get("is_actionable") or {}
            row["is_feasible"] = feasible_obj.get("value", None)
            row["is_feasible_reason"] = feasible_obj.get("reason", "")
            row["is_actionable"] = actionable_obj.get("value", None)
            row["is_actionable_reason"] = actionable_obj.get("reason", "")
            
            # Novelty (prompt uses "novel"; fallback to is_novel)
            novelty = res.get("novelty", {})
            novel_obj = novelty.get("novel") or novelty.get("is_novel") or {}
            row["is_novel"] = novel_obj.get("value", None)
            row["is_novel_reason"] = novel_obj.get("reason", "")
            
            # Store full JSON for reference
            row["full_response"] = json.dumps(res)
        else:
            # Fill with None for failed evaluations
            row["sector"] = None
            row["multiple_ideas"] = None
            row["is_clear"] = None
            row["is_clear_reason"] = ""
            row["is_coherent"] = None
            row["is_coherent_reason"] = ""
            row["is_clearly_defined"] = None
            row["is_clearly_defined_reason"] = ""
            row["is_detailed_enough"] = None
            row["is_detailed_enough_reason"] = ""
            row["specificity_score"] = None
            row["is_feasible"] = None
            row["is_feasible_reason"] = ""
            row["is_actionable"] = None
            row["is_actionable_reason"] = ""
            row["is_novel"] = None
            row["is_novel_reason"] = ""
            row["full_response"] = ""
        
        rows.append(row)
    
    return pd.DataFrame(rows)


def parse_results_to_dataframe_sector_only(results: List[Dict]) -> pd.DataFrame:
    """Convert sector-only evaluation results to a DataFrame (id, idea, sector, status, error)."""
    rows = []
    for r in results:
        row = {
            "id": r["id"],
            "idea": r["idea"],
            "status": r["status"],
            "error": r.get("error")
        }
        if r["status"] == "success" and r.get("result"):
            res = r["result"]
            row["sector"] = res.get("sector") or ""
        else:
            row["sector"] = ""
        rows.append(row)
    return pd.DataFrame(rows)


# ============================================================================
# IDEA GENERATION + IMAGE GENERATION (batch)
# ============================================================================

import secrets
import base64
from io import BytesIO

OPENAI_IMAGE_API_URL = "https://api.openai.com/v1/images/generations"

# Final display variants. Matches the single-idea page (image_generation.js).
IDEA_IMAGE_VARIANT_SIZES = {
    "large":  (197, 171),
    "medium": (156, 171),
    "small":  (116, 171),
}

# 64-char URL-safe alphabet for ID generation.
_NANOID_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"


def generate_idea_id() -> str:
    """Return a fresh idea ID, e.g. 'idea_V1StGXR8Z2'.
    10 chars from a 64-char alphabet → ~10^18 keyspace; collisions negligible.
    """
    return "idea_" + "".join(secrets.choice(_NANOID_ALPHABET) for _ in range(10))


def substitute_image_placeholders(template: str, idea_data: Dict) -> str:
    """Replace {{idea_title}} / {{problem_or_opportunity}} / {{solution_details}}
    / {{potential_impact}} in `template` with values from `idea_data`."""
    keys = ("idea_title", "problem_or_opportunity", "solution_details", "potential_impact")
    out = template or ""
    for k in keys:
        out = out.replace("{{" + k + "}}", str(idea_data.get(k) or ""))
    return out


def crop_to_variants(source_png_bytes: bytes) -> Dict[str, bytes]:
    """Build the three display variants from a single source PNG.

    Algorithm mirrors image_generation.js on the single-idea page:
      1. Center-crop the source to the LARGE target aspect (197:171), then
         downscale to exactly 197×171. That is the "large" variant.
      2. Side-crop the large image symmetrically to 156×171 (medium) and
         116×171 (small).
    """
    from PIL import Image  # local import — Pillow optional only for image flow

    source = Image.open(BytesIO(source_png_bytes)).convert("RGB")
    src_w, src_h = source.size

    target_w, target_h = IDEA_IMAGE_VARIANT_SIZES["large"]
    target_aspect = target_w / target_h
    src_aspect = src_w / src_h
    if src_aspect > target_aspect:
        # Source is wider than target — trim sides.
        crop_h = src_h
        crop_w = round(src_h * target_aspect)
        crop_x = (src_w - crop_w) // 2
        crop_y = 0
    else:
        # Source is taller (or square) — trim top/bottom.
        crop_w = src_w
        crop_h = round(src_w / target_aspect)
        crop_x = 0
        crop_y = (src_h - crop_h) // 2
    cropped = source.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
    large_img = cropped.resize((target_w, target_h), Image.LANCZOS)

    out: Dict[str, bytes] = {}
    for variant_key, (w, h) in IDEA_IMAGE_VARIANT_SIZES.items():
        trim = large_img.width - w
        left = trim // 2
        variant_img = large_img.crop((left, 0, left + w, h))
        buf = BytesIO()
        variant_img.save(buf, format="PNG", optimize=True)
        out[variant_key] = buf.getvalue()
    return out


class ImageVerificationError(RuntimeError):
    """gpt-image-1 org-not-verified or similar — abort the whole batch."""


async def _call_image_gen_httpx(
    client: httpx.AsyncClient,
    prompt: str,
    api_key: str,
    model: str,
    semaphore: asyncio.Semaphore,
    max_retries: int = 2,
) -> bytes:
    """Call the configured image model and return raw PNG bytes."""
    async with semaphore:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "prompt": prompt,
            "size": "1024x1024",
            "n": 1,
        }
        last_error: Optional[str] = None
        for attempt in range(max_retries):
            try:
                response = await client.post(
                    OPENAI_IMAGE_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=180.0,
                )
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 10))
                    logger.warning(f"[IMAGE] Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                if response.status_code in (401, 403):
                    # Auth or org-verification failure — surface immediately so
                    # the orchestrator can abort the whole batch.
                    msg = response.text[:500]
                    raise ImageVerificationError(
                        f"Image API auth/verification failed ({response.status_code}): {msg}"
                    )
                response.raise_for_status()
                data = response.json()
                b64 = data.get("data", [{}])[0].get("b64_json")
                if not b64:
                    raise ValueError("Image API response missing b64_json payload")
                return base64.b64decode(b64)
            except ImageVerificationError:
                raise
            except httpx.HTTPStatusError as e:
                error_text = e.response.text[:500] if hasattr(e.response, "text") else str(e)
                last_error = f"HTTP {e.response.status_code}: {error_text[:200]}"
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    break
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError(last_error or "Image generation failed after retries")


def _image_keys_for_idea(idea_id: str) -> Dict[str, str]:
    return {
        "large":  f"ideas/{idea_id}/large.png",
        "medium": f"ideas/{idea_id}/medium.png",
        "small":  f"ideas/{idea_id}/small.png",
    }


async def _generate_and_store_image_for_row(
    client: httpx.AsyncClient,
    row: Dict,
    image_template: str,
    api_key: str,
    model: str,
    semaphore: asyncio.Semaphore,
    backend,
    skip_existing: bool,
    abort_event: asyncio.Event,
) -> Dict:
    """Generate + crop + upload all three variants for ONE idea row.

    Returns a status dict with image_status / image_error / image_*_path.
    Never raises (except in catastrophic situations); per-row errors land
    in the returned dict so the batch can continue.
    """
    idea_id = row.get("idea_id") or ""
    keys = _image_keys_for_idea(idea_id)
    empty_paths = {"image_large_path": "", "image_medium_path": "", "image_small_path": ""}

    if abort_event.is_set():
        return {"idea_id": idea_id, "image_status": "skipped",
                "image_error": "batch aborted before this row was processed",
                **empty_paths}

    if not idea_id:
        return {"idea_id": idea_id, "image_status": "error",
                "image_error": "Missing idea_id", **empty_paths}

    # Required text fields must be present to build a useful prompt.
    required_text_fields = ("idea_title", "problem_or_opportunity",
                            "solution_details", "potential_impact")
    if not all((row.get(f) or "").strip() for f in required_text_fields):
        return {"idea_id": idea_id, "image_status": "skipped",
                "image_error": "Missing one or more required idea fields",
                **empty_paths}

    if skip_existing and all(backend.exists(k) for k in keys.values()):
        logger.info(f"[IMAGE {idea_id}] All variants already exist — skipping")
        return {
            "idea_id": idea_id,
            "image_status": "skipped",
            "image_error": "files already exist",
            "image_large_path":  keys["large"],
            "image_medium_path": keys["medium"],
            "image_small_path":  keys["small"],
        }

    prompt = substitute_image_placeholders(image_template, row)

    # Generate the source PNG via the selected image model.
    try:
        source_png = await _call_image_gen_httpx(client, prompt, api_key, model, semaphore)
    except ImageVerificationError as e:
        # Signal the orchestrator to stop launching new work.
        abort_event.set()
        return {"idea_id": idea_id, "image_status": "error",
                "image_error": str(e), **empty_paths}
    except Exception as e:
        logger.error(f"[IMAGE {idea_id}] Generation failed: {e}")
        return {"idea_id": idea_id, "image_status": "error",
                "image_error": f"{type(e).__name__}: {e}", **empty_paths}

    # Crop with Pillow (CPU-bound, but small — no need for executor here).
    try:
        variants = crop_to_variants(source_png)
    except Exception as e:
        logger.error(f"[IMAGE {idea_id}] Cropping failed: {e}")
        return {"idea_id": idea_id, "image_status": "error",
                "image_error": f"Crop failed: {type(e).__name__}: {e}",
                **empty_paths}

    # Upload all three; roll back on partial failure.
    uploaded: List[str] = []
    try:
        for variant_key in ("large", "medium", "small"):
            stored_key = backend.put(keys[variant_key], variants[variant_key])
            uploaded.append(stored_key)
    except Exception as e:
        logger.error(f"[IMAGE {idea_id}] Upload failed, rolling back: {e}")
        for k in uploaded:
            try:
                backend.delete(k)
            except Exception:
                pass
        return {"idea_id": idea_id, "image_status": "error",
                "image_error": f"Upload failed: {type(e).__name__}: {e}",
                **empty_paths}

    logger.info(f"[IMAGE {idea_id}] Stored 3 variants")
    return {
        "idea_id": idea_id,
        "image_status": "ok",
        "image_error": None,
        "image_large_path":  keys["large"],
        "image_medium_path": keys["medium"],
        "image_small_path":  keys["small"],
    }


async def process_image_batch(
    idea_rows: List[Dict],
    image_template: str,
    api_key: str,
    model: str,
    backend,
    max_concurrent: int = 3,
    skip_existing: bool = True,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[Dict]:
    """Generate + store image variants for every row in `idea_rows`.

    `idea_rows` should be dicts holding idea_id and the four text fields.
    Returns results in the SAME ORDER as input.
    """
    total = len(idea_rows)
    logger.info("=" * 60)
    logger.info(f"Starting IMAGE batch: {total} rows, max_concurrent={max_concurrent}, skip_existing={skip_existing}")
    logger.info("=" * 60)

    semaphore = asyncio.Semaphore(max_concurrent)
    abort_event = asyncio.Event()
    completed = {"count": 0}
    lock = asyncio.Lock()

    limits = httpx.Limits(
        max_keepalive_connections=max_concurrent * 2,
        max_connections=max_concurrent * 2 + 5,
    )
    async with httpx.AsyncClient(
        limits=limits,
        timeout=httpx.Timeout(180.0, connect=10.0),
    ) as client:

        async def run_one(row: Dict, idx: int) -> Dict:
            result = await _generate_and_store_image_for_row(
                client=client,
                row=row,
                image_template=image_template,
                api_key=api_key,
                model=model,
                semaphore=semaphore,
                backend=backend,
                skip_existing=skip_existing,
                abort_event=abort_event,
            )
            result["_idx"] = idx
            async with lock:
                completed["count"] += 1
                if progress_callback:
                    try:
                        progress_callback(completed["count"], total)
                    except Exception:
                        pass
            return result

        tasks = [asyncio.create_task(run_one(row, i)) for i, row in enumerate(idea_rows)]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)

    # Normalize exceptions into error rows.
    out: List[Dict] = []
    empty_paths = {"image_large_path": "", "image_medium_path": "", "image_small_path": ""}
    for idx, gres in enumerate(gathered):
        if isinstance(gres, Exception):
            out.append({
                "idea_id": idea_rows[idx].get("idea_id") or "",
                "image_status": "error",
                "image_error": f"{type(gres).__name__}: {gres}",
                "_idx": idx,
                **empty_paths,
            })
        else:
            out.append(gres)
    out.sort(key=lambda r: r["_idx"])
    for r in out:
        r.pop("_idx", None)
    return out


def run_image_batch(
    idea_rows: List[Dict],
    image_template: str,
    api_key: str,
    model: str,
    backend,
    max_concurrent: int = 3,
    skip_existing: bool = True,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[Dict]:
    """Synchronous wrapper for `process_image_batch` — mirrors run_batch_evaluation."""
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                process_image_batch(
                    idea_rows=idea_rows,
                    image_template=image_template,
                    api_key=api_key,
                    model=model,
                    backend=backend,
                    max_concurrent=max_concurrent,
                    skip_existing=skip_existing,
                    progress_callback=progress_callback,
                )
            )
        finally:
            loop.close()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_thread)
        return future.result()


def parse_idea_generation_results_to_dataframe(
    input_df: pd.DataFrame,
    raw_results: List[Dict],
    idea_ids: List[str],
) -> pd.DataFrame:
    """Build the Card 1 output DataFrame.

    `input_df`   — original CSV (keeps all original columns).
    `raw_results`— list returned by process_ideas_batch (one per row).
    `idea_ids`   — parallel list of pre-assigned idea_ids.
    """
    def _join_list(v):
        if isinstance(v, list):
            return "|".join(str(x) for x in v)
        return str(v) if v is not None else ""

    out = input_df.copy().reset_index(drop=True)
    titles, problems, themes, categories, subcategories, solutions, impacts, statuses, reasons = (
        [], [], [], [], [], [], [], [], []
    )
    for raw, idea_id in zip(raw_results, idea_ids):
        if raw.get("status") == "success" and raw.get("result"):
            res = raw["result"] or {}
            if (res.get("status") or "").lower() == "unprocessable":
                statuses.append("unprocessable")
                reasons.append(res.get("reason") or "")
                titles.append(""); problems.append(""); themes.append("")
                categories.append(""); subcategories.append(""); solutions.append(""); impacts.append("")
            else:
                statuses.append("ok"); reasons.append("")
                titles.append(res.get("idea_title") or "")
                problems.append(res.get("problem_or_opportunity") or "")
                themes.append(_join_list(res.get("problem_opportunity_themes")))
                categories.append(_join_list(res.get("business_categories")))
                subcategories.append(_join_list(res.get("business_subcategories")))
                solutions.append(res.get("solution_details") or "")
                impacts.append(res.get("potential_impact") or "")
        else:
            statuses.append("error")
            reasons.append(raw.get("error") or "Unknown error")
            titles.append(""); problems.append(""); themes.append("")
            categories.append(""); subcategories.append(""); solutions.append(""); impacts.append("")

    out["idea_id"] = idea_ids
    out["idea_title"] = titles
    out["problem_or_opportunity"] = problems
    out["problem_opportunity_themes"] = themes
    out["business_categories"] = categories
    out["business_subcategories"] = subcategories
    out["solution_details"] = solutions
    out["potential_impact"] = impacts
    out["status"] = statuses
    out["status_reason"] = reasons
    # Move idea_id to the front for readability.
    cols = ["idea_id"] + [c for c in out.columns if c != "idea_id"]
    return out[cols]


def merge_image_results_into_dataframe(
    input_df: pd.DataFrame,
    image_results: List[Dict],
    processed_idea_ids: List[str],
) -> pd.DataFrame:
    """Card 2: take the input DF (with idea_id) and merge per-row image columns.

    `image_results` is parallel to `processed_idea_ids` (only rows we actually
    attempted). Rows that were filtered out earlier (status != 'ok') get blank
    columns + image_status='skipped'.
    """
    by_id = {r["idea_id"]: r for r in image_results}
    out = input_df.copy().reset_index(drop=True)
    statuses, errors, large, medium, small = [], [], [], [], []
    for _, row in out.iterrows():
        iid = row.get("idea_id") or ""
        if iid in by_id:
            r = by_id[iid]
            statuses.append(r.get("image_status") or "")
            errors.append(r.get("image_error") or "")
            large.append(r.get("image_large_path") or "")
            medium.append(r.get("image_medium_path") or "")
            small.append(r.get("image_small_path") or "")
        else:
            statuses.append("skipped")
            errors.append("row skipped (status != ok in input CSV)")
            large.append(""); medium.append(""); small.append("")
    out["image_status"] = statuses
    out["image_error"] = errors
    out["image_large_path"] = large
    out["image_medium_path"] = medium
    out["image_small_path"] = small
    return out
