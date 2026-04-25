from concurrent.futures import ThreadPoolExecutor
from veriflow.schemas import Claim, ClaimSet, RawSignals, TrustProfile
from veriflow.decomposer import decompose
from veriflow.verifiers.web import verify_web
from veriflow.verifiers.metadata import verify_metadata
from veriflow.verifiers.image_integrity import analyze_image_integrity
from veriflow.verifiers.provenance import verify_provenance
from veriflow.aggregator import aggregate
from veriflow.connectors.image import extract_exif
from veriflow.connectors.pdf import extract_pdf_content
from veriflow.connectors.url import fetch_url_content


def _collect_signals(
    claim: Claim,
    image_bytes: bytes | None,
    exif_data: dict | None,
    deep: bool,
) -> RawSignals:
    """Collect all verification signals for a single claim. No LLM calls."""
    web_results = verify_web(claim)

    image_integrity = None
    if image_bytes:
        image_integrity = analyze_image_integrity(image_bytes, has_exif=bool(exif_data))

    metadata_results = verify_metadata(exif_data or {})

    provenance = None
    if deep and image_bytes:
        provenance = verify_provenance(image_bytes)

    return RawSignals(
        claim_id=claim.id,
        web_results=web_results,
        exif_data=metadata_results if exif_data else None,
        image_integrity=image_integrity,
        provenance=provenance,
    )


def _run_pipeline(
    text: str | None = None,
    image_bytes: bytes | None = None,
    mime_type: str = "image/jpeg",
    file_path: str | None = None,
    url: str | None = None,
    deep: bool = False,
    model: str = "gemini-2.5-flash",
) -> TrustProfile:
    """Core pipeline: Decompose → Verify (parallel) → Aggregate.

    2 LLM calls total regardless of claim count.
    Based on SAFE (DeepMind, 2024) decompose-then-verify architecture.
    """
    # Step 0: Connectors — normalize input (no LLM)
    if file_path:
        content = extract_pdf_content(file_path)
        text = (text or "") + "\n" + content["text"]
        if not image_bytes and content["images"]:
            image_bytes = content["images"][0]["image_bytes"]
            mime_type = content["images"][0]["mime_type"]

    if url:
        content = fetch_url_content(url)
        text = (text or "") + "\n" + content["text"]

    exif_data = None
    if image_bytes:
        exif_data = extract_exif(image_bytes)

    # Step 1: Decompose (LLM call 1)
    claim_set = decompose(
        text=text,
        image_bytes=image_bytes,
        mime_type=mime_type,
        exif_data=exif_data,
        model=model,
    )

    if not claim_set.claims:
        return aggregate(claim_set, [], depth="deep" if deep else "quick", model=model)

    # Step 2: Verify all claims in parallel (no LLM calls)
    with ThreadPoolExecutor(max_workers=min(len(claim_set.claims), 8)) as pool:
        futures = [
            pool.submit(_collect_signals, claim, image_bytes, exif_data, deep)
            for claim in claim_set.claims
        ]
        raw_signals = [f.result() for f in futures]

    # Step 3: Aggregate (LLM call 2)
    return aggregate(claim_set, raw_signals, depth="deep" if deep else "quick", model=model)


def quick_verify(
    text: str | None = None,
    image_bytes: bytes | None = None,
    mime_type: str = "image/jpeg",
    file_path: str | None = None,
    url: str | None = None,
    model: str = "gemini-2.5-flash",
) -> TrustProfile:
    """Quick verification (~6-8s). Web search + EXIF + image forensics."""
    return _run_pipeline(
        text=text, image_bytes=image_bytes, mime_type=mime_type,
        file_path=file_path, url=url, deep=False, model=model,
    )


def deep_verify(
    text: str | None = None,
    image_bytes: bytes | None = None,
    mime_type: str = "image/jpeg",
    file_path: str | None = None,
    url: str | None = None,
    model: str = "gemini-2.5-flash",
) -> TrustProfile:
    """Deep verification (~10-15s). Everything in quick + reverse image search."""
    return _run_pipeline(
        text=text, image_bytes=image_bytes, mime_type=mime_type,
        file_path=file_path, url=url, deep=True, model=model,
    )
