import json
import os
import time
from google import genai
from google.genai import types, errors
from veriflow.schemas import ClaimSet, RawSignals, TrustProfile

_client = None

AGGREGATE_PROMPT = """You are a verification aggregator. You receive extracted claims, their logical relationship, and raw verification signals. Your job is to reason about all evidence and produce a trust assessment.

Guidelines for weighing signals:
- Metadata contradictions (GPS location, timestamps) are hard machine evidence — weight heavily
- Web corroboration from credible sources (Reuters, AP, Wikipedia) is strong
- Web results from unknown blogs or social media are weak
- Image forensics (FFT, ELA, noise) are indicative but not conclusive alone
- Cross-modal mismatch (caption doesn't match image) is a strong red flag
- Provenance matches (image found elsewhere in different context) are near-conclusive for recycling
- The logical formula tells you how claims relate: if formula is "c1 AND c2" then ALL must hold; if "c1 OR c2" then at least one suffices

Claim set:
{claim_set}

Raw verification signals:
{signals}

Cross-modal check result:
{cross_modal}

Respond with ONLY valid JSON:
{{
  "per_claim": [
    {{"claim_id": "c1", "status": "supported|refuted|uncertain", "confidence": 0.0-1.0, "key_evidence": [{{"url": "...", "title": "...", "snippet": "...", "relevance_score": 0.0-1.0, "source_type": "..."}}], "reasoning": "..."}}
  ],
  "overall_confidence": 0.0-1.0,
  "verdict": "likely_authentic|likely_manipulated|uncertain|insufficient_data",
  "red_flags": ["plain language flag 1", "..."],
  "evidence_summary": "2-3 sentence summary"
}}
"""


def _gemini_generate(client, model, contents, config, retries=4):
    """Call generate_content with exponential backoff on 503/429."""
    delay = 10
    for attempt in range(retries):
        try:
            return client.models.generate_content(model=model, contents=contents, config=config)
        except (errors.ServerError, errors.ClientError) as e:
            if attempt == retries - 1:
                raise
            print(f"Gemini {e.__class__.__name__} — retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def aggregate(
    claim_set: ClaimSet,
    raw_signals: list[RawSignals],
    depth: str = "quick",
    model: str = "gemini-2.5-flash",
) -> TrustProfile:
    """Aggregate all signals into a TrustProfile.

    This is LLM Call 2 in the pipeline. No fixed weight formula —
    the LLM reasons about signal importance based on guidelines.
    """
    if not claim_set.claims:
        return TrustProfile(
            claims=[],
            formula="",
            per_claim=[],
            overall_confidence=0.0,
            verdict="insufficient_data",
            red_flags=[],
            evidence_summary="No claims to verify",
            depth=depth,
        )

    client = _get_client()

    cross_modal_str = "None"
    if claim_set.cross_modal_check:
        cross_modal_str = (
            f"Match: {claim_set.cross_modal_check.match}, "
            f"Reason: {claim_set.cross_modal_check.reason}"
        )

    prompt = AGGREGATE_PROMPT.format(
        claim_set=claim_set.model_dump_json(indent=2),
        signals=json.dumps([s.model_dump() for s in raw_signals], indent=2),
        cross_modal=cross_modal_str,
    )

    response = _gemini_generate(
        client, model, prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        # Gemini occasionally emits bare \u in URLs; escape them before parsing
        import re
        cleaned = re.sub(r'\\u(?![0-9a-fA-F]{4})', r'\\\\u', response.text)
        result = json.loads(cleaned)
    return TrustProfile(
        claims=claim_set.claims,
        formula=claim_set.formula,
        per_claim=result["per_claim"],
        overall_confidence=result["overall_confidence"],
        verdict=result["verdict"],
        red_flags=result["red_flags"],
        evidence_summary=result["evidence_summary"],
        depth=depth,
    )
