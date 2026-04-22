import base64
from mcp.server.fastmcp import FastMCP
from veriflow.pipeline import quick_verify, deep_verify
from veriflow.decomposer import decompose
from veriflow.connectors.image import extract_exif

mcp = FastMCP("veriflow", json_response=True)


@mcp.tool()
def veriflow_quick(
    text: str | None = None,
    image_base64: str | None = None,
    file_path: str | None = None,
    url: str | None = None,
) -> str:
    """Quick content verification (~6-8s). Extracts claims from text/image/PDF/URL,
    checks them against web search, EXIF metadata, and image forensics.
    Returns a trust profile with verdicts, confidence, red flags, and evidence.
    Use for routine checks."""
    image_bytes = base64.b64decode(image_base64) if image_base64 else None
    profile = quick_verify(text=text, image_bytes=image_bytes, file_path=file_path, url=url)
    return profile.model_dump_json(indent=2)


@mcp.tool()
def veriflow_deep(
    text: str | None = None,
    image_base64: str | None = None,
    file_path: str | None = None,
    url: str | None = None,
) -> str:
    """Deep content verification (~10-15s). Everything in quick_verify PLUS
    reverse image search to check if the image has appeared before in a
    different context. Use when image provenance matters or user needs
    thorough verification."""
    image_bytes = base64.b64decode(image_base64) if image_base64 else None
    profile = deep_verify(text=text, image_bytes=image_bytes, file_path=file_path, url=url)
    return profile.model_dump_json(indent=2)


@mcp.tool()
def veriflow_extract(
    text: str | None = None,
    image_base64: str | None = None,
    file_path: str | None = None,
    url: str | None = None,
) -> str:
    """Extract claims without verifying them. Returns atomic claims, logical
    formula, cross-modal check, and risk hint. Use to inspect what claims
    would be verified, or to decide whether to run quick vs deep verification
    based on the risk hint."""
    image_bytes = base64.b64decode(image_base64) if image_base64 else None
    exif_data = extract_exif(image_bytes) if image_bytes else None
    claim_set = decompose(text=text, image_bytes=image_bytes, exif_data=exif_data)
    return claim_set.model_dump_json(indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
