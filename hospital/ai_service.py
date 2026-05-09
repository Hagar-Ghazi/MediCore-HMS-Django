"""
MediCore HMS — Ollama AI Service
─────────────────────────────────────────────────────────────────────
Encapsulates all communication with a locally-running Ollama instance
Design principles
  • Zero cloud dependency uses the Ollama HTTP API directly (requests)
  • Returns a structured OllamaResult dataclass so the caller never
    has to parse raw JSON
  • All errors are caught here the caller decides what to do with them
  • Latency is measured and returned for telemetry storage
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional
import requests
from django.conf import settings

logger = logging.getLogger(__name__)



# Response contract 

@dataclass
class OllamaResult:
    """
    Structured result returned by run_diagnosis()
    Regardless of success or failure the caller always receives
    a fully-populated object no uncaught exceptions bubble up
    """
    success:    bool
    diagnosis:  str              = ""
    confidence: float            = 0.0  
    token_count: int             = 0
    latency_ms: int              = 0
    model_used: str              = ""
    error:      Optional[str]    = None


# Prompt template 

_SYSTEM_PROMPT = """You are a clinical decision-support AI embedded in a
Hospital Management System. Your role is to analyse a patient's reported
symptoms and return a concise, structured JSON assessment.

Rules:
1. Respond ONLY with valid JSON — no markdown fences, no extra text.
2. The JSON must contain exactly these keys:
   - "diagnosis"   : string  — most likely preliminary diagnosis (≤ 120 chars)
   - "confidence"  : float   — your confidence level between 0.0 and 1.0
   - "urgency"     : string  — one of "LOW", "MODERATE", "HIGH", "CRITICAL"
   - "notes"       : string  — brief clinical notes or recommended next steps
3. This is a decision-support tool only. Always recommend professional review."""

_USER_TEMPLATE = """Patient reported symptoms / reason for visit:
\"\"\"{reason}\"\"\"

Provide your structured JSON assessment."""




# Core inference function
def run_diagnosis(reason: str) -> OllamaResult:
    """
    Send the patient's reason/symptoms to the local Ollama model and
    parse the structured response

    Parameters
    ----------
    reason : str
        The patient's free-text reason for the appointment

    Returns
    -------
    OllamaResult
        Always returns an OllamaResult never raises
    """
    base_url   = settings.OLLAMA_BASE_URL.rstrip("/")
    model      = settings.OLLAMA_MODEL
    timeout    = settings.OLLAMA_TIMEOUT
    endpoint   = f"{base_url}/api/chat"

    payload = {
        "model":  model,
        "stream": False,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": _USER_TEMPLATE.format(reason=reason)},
        ],
        "options": {
            "temperature": 0.2,   # low temp → deterministic medical responses
            "num_predict": 300,
        },
    }

    t_start = time.monotonic()



    try:
        logger.info("[Ollama] Sending diagnosis request | model=%s", model)

        response = requests.post(
            endpoint,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()

        latency_ms = int((time.monotonic() - t_start) * 1000)
        data       = response.json()

        # Extract the raw text content from the response
        raw_content = (
            data.get("message", {}).get("content", "")
            or data.get("response", "")
        ).strip()

        # Strip markdown code fences if the model wraps JSON in them
        if raw_content.startswith("```"):
            lines = raw_content.splitlines()
            raw_content = "\n".join(
                line for line in lines
                if not line.startswith("```")
            ).strip()



        # Parse the JSON payload from the model
        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError:
            # Model didn't return valid JSON — treat as a soft failure
            logger.warning("[Ollama] Non-JSON response received: %s", raw_content[:200])
            return OllamaResult(
                success    = False,
                latency_ms = latency_ms,
                model_used = model,
                token_count = data.get("eval_count", 0),
                error      = f"Model returned non-JSON output: {raw_content[:200]}",
            )

        # Extract token usage from Ollama's metadata fields
        token_count = (
            data.get("eval_count", 0)
            + data.get("prompt_eval_count", 0)
        )

        diagnosis  = str(parsed.get("diagnosis", "Assessment unavailable"))[:255]
        confidence = float(parsed.get("confidence", 0.0))
        confidence = max(0.0, min(1.0, confidence))   # clamp to [0, 1]

        logger.info(
            "[Ollama] SUCCESS | diagnosis=%s | confidence=%.2f | tokens=%d | latency=%dms",
            diagnosis, confidence, token_count, latency_ms,
        )

        return OllamaResult(
            success     = True,
            diagnosis   = diagnosis,
            confidence  = confidence,
            token_count = token_count,
            latency_ms  = latency_ms,
            model_used  = model,
        )

    except requests.exceptions.ConnectionError as exc:
        latency_ms = int((time.monotonic() - t_start) * 1000)
        msg = (
            "Cannot reach Ollama. Is it running? "
            f"Check OLLAMA_BASE_URL={base_url}. Error: {exc}"
        )
        logger.error("[Ollama] ConnectionError — %s", msg)
        return OllamaResult(
            success    = False,
            latency_ms = latency_ms,
            model_used = model,
            error      = msg,
        )

    except requests.exceptions.Timeout as exc:
        latency_ms = int((time.monotonic() - t_start) * 1000)
        msg = f"Ollama request timed out after {timeout}s. Error: {exc}"
        logger.error("[Ollama] Timeout — %s", msg)
        return OllamaResult(
            success    = False,
            latency_ms = latency_ms,
            model_used = model,
            error      = msg,
        )

    except requests.exceptions.HTTPError as exc:
        latency_ms = int((time.monotonic() - t_start) * 1000)
        msg = f"Ollama HTTP error {exc.response.status_code}: {exc}"
        logger.error("[Ollama] HTTPError — %s", msg)
        return OllamaResult(
            success    = False,
            latency_ms = latency_ms,
            model_used = model,
            error      = msg,
        )

    except Exception as exc:  # broad safety net never crash the web server
        latency_ms = int((time.monotonic() - t_start) * 1000)
        msg = f"Unexpected error during AI inference: {exc}"
        logger.exception("[Ollama] Unexpected error")
        return OllamaResult(
            success    = False,
            latency_ms = latency_ms,
            model_used = model,
            error      = msg,
        )
