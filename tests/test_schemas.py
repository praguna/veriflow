from veriflow.schemas import (
    Claim, ClaimSet, CrossModalCheck, Evidence,
    RawSignals, ImageIntegritySignals, TrustProfile,
    ClaimVerdict,
)


def test_claim_creation():
    claim = Claim(id="c1", text="The Eiffel Tower is 330m tall", modality="text", source="user_text")
    assert claim.id == "c1"
    assert claim.modality == "text"


def test_claim_set_with_formula():
    c1 = Claim(id="c1", text="Earthquake hit Istanbul", modality="text", source="user_text")
    c2 = Claim(id="c2", text="Photo shows destruction", modality="visual", source="image")
    cs = ClaimSet(
        claims=[c1, c2],
        formula="c1 AND c2",
        cross_modal_check=CrossModalCheck(match=False, reason="Arabic signage vs Istanbul"),
        input_risk_hint="high",
    )
    assert len(cs.claims) == 2
    assert cs.formula == "c1 AND c2"
    assert cs.input_risk_hint == "high"


def test_image_integrity_signals():
    sig = ImageIntegritySignals(
        fft_ai_score=0.85,
        ela_manipulation_score=0.1,
        noise_consistency=0.92,
        has_exif=True,
    )
    assert sig.fft_ai_score == 0.85


def test_raw_signals():
    evidence = Evidence(url="https://ex.com", title="T", snippet="S", relevance_score=0.9, source_type="web")
    raw = RawSignals(
        claim_id="c1",
        web_results=[evidence],
        exif_data={"GPS": "37.57N, 36.93E", "DateTime": "2023:02:06"},
        image_integrity=None,
        provenance=None,
    )
    assert raw.claim_id == "c1"
    assert len(raw.web_results) == 1


def test_trust_profile():
    claim = Claim(id="c1", text="Test", modality="text", source="test")
    verdict = ClaimVerdict(
        claim_id="c1",
        status="refuted",
        confidence=0.85,
        key_evidence=[],
        reasoning="No sources found",
    )
    profile = TrustProfile(
        claims=[claim],
        formula="c1",
        per_claim=[verdict],
        overall_confidence=0.15,
        verdict="likely_manipulated",
        red_flags=["No corroborating sources"],
        evidence_summary="Claim not supported by any evidence",
        depth="quick",
    )
    assert profile.verdict == "likely_manipulated"
    assert profile.depth == "quick"
