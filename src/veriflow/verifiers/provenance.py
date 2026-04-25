import io
import os
import base64
import httpx
from PIL import Image
from veriflow.schemas import Evidence

SERPAPI_URL = "https://serpapi.com/search"
IMGBB_URL = "https://api.imgbb.com/1/upload"
_MAX_SIDE = 1024
_JPEG_QUALITY = 85


def _compress(image_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((_MAX_SIDE, _MAX_SIDE), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=_JPEG_QUALITY, optimize=True)
    return buf.getvalue()


def _upload_to_imgbb(image_bytes: bytes) -> str:
    """Upload image to ImgBB and return the public URL."""
    api_key = os.environ.get("IMGBB_API_KEY")
    if not api_key:
        raise RuntimeError("IMGBB_API_KEY not set")

    b64 = base64.b64encode(image_bytes).decode()
    response = httpx.post(
        IMGBB_URL,
        params={"key": api_key},
        data={"image": b64},
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()["data"]["url"]


def _search_reverse_image(image_url: str) -> dict:
    """Call SerpAPI Google Reverse Image Search with a public image URL."""
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        return {"image_results": []}

    response = httpx.get(
        SERPAPI_URL,
        params={"engine": "google_reverse_image", "image_url": image_url, "api_key": api_key},
        timeout=20.0,
    )
    response.raise_for_status()
    return response.json()


def verify_provenance(image_bytes: bytes) -> list[Evidence]:
    """Check if an image has appeared before via reverse image search.

    Only runs in deep_verify mode. Uploads to Imgur to get a public URL,
    then queries SerpAPI google_reverse_image.
    Returns list of prior appearances with context.
    """
    if not os.environ.get("IMGBB_API_KEY") or not os.environ.get("SERPAPI_KEY"):
        return []

    compressed = _compress(image_bytes)
    image_url = _upload_to_imgbb(compressed)
    data = _search_reverse_image(image_url)

    results = data.get("image_results", [])
    return [
        Evidence(
            url=r.get("link", ""),
            title=r.get("title", ""),
            snippet=r.get("snippet", f"Reverse image match: {r.get('displayed_link', '')}"),
            relevance_score=1.0 / (i + 1),
            source_type="provenance",
        )
        for i, r in enumerate(results)
        if r.get("link")
    ]
