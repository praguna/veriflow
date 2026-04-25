import io
from pathlib import Path
from PIL import Image
from mcp.server.fastmcp import FastMCP
from veriflow.pipeline import quick_verify, deep_verify
from veriflow.decomposer import decompose
from veriflow.connectors.image import extract_exif

mcp = FastMCP("veriflow", json_response=True)

_MAX_SIDE = 1024
_JPEG_QUALITY = 85


def _load_image(image_path: str | None) -> bytes | None:
    if not image_path:
        return None
    raw = Path(image_path).read_bytes()
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img.thumbnail((_MAX_SIDE, _MAX_SIDE), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=_JPEG_QUALITY, optimize=True)
    return buf.getvalue()


@mcp.tool()
def veriflow_quick(
    text: str | None = None,
    image_path: str | None = None,
    document_file_path: str | None = None,
    url: str | None = None,
) -> str:
    """Quick content verification (~6-8s). Checks text, images, PDFs, or URLs against
    web search, EXIF metadata, and image forensics.

    For images: ask the user for the local file path (e.g. /Users/name/Downloads/photo.jpg)
    and pass it as image_path. Do NOT attempt to encode images as base64.
    For PDFs: pass the local file path as document_file_path.
    For web articles: pass the URL."""
    profile = quick_verify(
        text=text,
        image_bytes=_load_image(image_path),
        file_path=document_file_path,
        url=url,
    )
    return profile.model_dump_json(indent=2)


@mcp.tool()
def veriflow_deep(
    text: str | None = None,
    image_path: str | None = None,
    document_file_path: str | None = None,
    url: str | None = None,
) -> str:
    """Deep content verification (~10-15s). Everything in veriflow_quick PLUS
    reverse image search to detect if the image appeared before in a different context.

    For images: ask the user for the local file path (e.g. /Users/name/Downloads/photo.jpg)
    and pass it as image_path. Do NOT attempt to encode images as base64.
    For PDFs: pass the local file path as document_file_path.
    For web articles: pass the URL."""
    profile = deep_verify(
        text=text,
        image_bytes=_load_image(image_path),
        file_path=document_file_path,
        url=url,
    )
    return profile.model_dump_json(indent=2)


@mcp.tool()
def veriflow_extract(
    text: str | None = None,
    image_path: str | None = None,
    document_file_path: str | None = None,
    url: str | None = None,
) -> str:
    """Extract and list claims without verifying them. Returns atomic claims, logical
    formula, cross-modal check, and risk hint. Useful to preview what would be verified
    before deciding whether to run veriflow_quick or veriflow_deep.

    For images: ask the user for the local file path (e.g. /Users/name/Downloads/photo.jpg)
    and pass it as image_path. Do NOT attempt to encode images as base64."""
    image_bytes = _load_image(image_path)
    exif_data = extract_exif(image_bytes) if image_bytes else None
    claim_set = decompose(text=text, image_bytes=image_bytes, exif_data=exif_data)
    return claim_set.model_dump_json(indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
