import json
import os
import time
from google import genai
from google.genai import types, errors
from veriflow.schemas import ClaimSet

_client = None

DECOMPOSE_PROMPT = """You are a claim decomposition engine. Analyze the provided content and extract all verifiable factual claims.

For each claim:
- Give it a sequential id: "c1", "c2", etc.
- Extract the atomic factual statement
- Tag its modality: "text" (from written text), "visual" (from image content), "metadata" (from file metadata), "cross_modal" (comparing text vs image)
- Tag its source: where in the input it came from

Also produce:
- A logical formula connecting claims (e.g. "c1 AND c2 AND c3" if all must hold, "c1 AND (c2 OR c3)" if alternatives exist)
- If both text and image are provided: a cross_modal_check assessing whether the text description matches the image content
- An input_risk_hint: "low" (routine claims), "medium" (unusual claims), "high" (extraordinary claims or signs of manipulation)

Return ONLY valid JSON matching this schema:
{
  "claims": [{"id": "c1", "text": "...", "modality": "text|visual|metadata|cross_modal", "source": "..."}],
  "formula": "c1 AND c2",
  "cross_modal_check": {"match": true/false, "reason": "..."} or null,
  "input_risk_hint": "low|medium|high"
}

Skip opinions, questions, and vague statements. Only include claims that can be verified against external evidence.
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


def decompose(
    text: str | None = None,
    image_bytes: bytes | None = None,
    mime_type: str = "image/jpeg",
    exif_data: dict | None = None,
    model: str = "gemini-2.5-flash",
) -> ClaimSet:
    """Decompose input into atomic claims with logical formula.

    This is LLM Call 1 in the pipeline. Based on SAFE (DeepMind, 2024)
    decompose-then-verify approach + TRUST Agents (2026) logical formula output.
    """
    if not text and not image_bytes:
        return ClaimSet(claims=[], formula="", input_risk_hint="low")

    client = _get_client()
    contents: list = [DECOMPOSE_PROMPT]

    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

    if text:
        contents.append(f"Text content:\n{text}")

    if exif_data:
        contents.append(f"Image metadata (EXIF):\n{json.dumps(exif_data)}")

    response = _gemini_generate(
        client, model, contents,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    raw = json.loads(response.text)
    return ClaimSet(**raw)
