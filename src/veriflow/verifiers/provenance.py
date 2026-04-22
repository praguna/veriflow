import os
import base64
import httpx
from veriflow.schemas import Evidence

SERPAPI_URL = "https://serpapi.com/search"


def _search_reverse_image(image_bytes: bytes) -> dict:
    """Call SerpAPI Google Lens for reverse image search."""
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        return {"visual_matches": []}

    b64 = base64.b64encode(image_bytes).decode()
    response = httpx.get(
        SERPAPI_URL,
        params={
            "engine": "google_lens",
            "image_content": b64,
            "api_key": api_key,
        },
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()


def verify_provenance(image_bytes: bytes) -> list[Evidence]:
    """Check if an image has appeared before via reverse image search.

    Only runs in deep_verify mode. Uses SerpAPI Google Lens.
    Returns list of prior appearances with context.
    """
    data = _search_reverse_image(image_bytes)
    matches = data.get("visual_matches", [])
    return [
        Evidence(
            url=m.get("link", ""),
            title=m.get("title", ""),
            snippet=f"Visual match found at position {m.get('position', '?')}",
            relevance_score=1.0 - (m.get("position", 10) / 10.0),
            source_type="provenance",
        )
        for m in matches
        if m.get("link")
    ]
