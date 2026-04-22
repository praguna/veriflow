import json
from unittest.mock import patch, MagicMock
from veriflow.aggregator import aggregate
from veriflow.schemas import (
    Claim, ClaimSet, CrossModalCheck, Evidence,
    RawSignals, ImageIntegritySignals, TrustProfile,
)


def test_aggregate_produces_trust_profile():
    claim_set = ClaimSet(
        claims=[
            Claim(id="c1", text="Earthquake hit Istanbul", modality="text", source="caption"),
            Claim(id="c2", text="Photo shows destruction", modality="visual", source="image"),
        ],
        formula="c1 AND c2",
        cross_modal_check=CrossModalCheck(match=False, reason="Arabic signage vs Istanbul"),
        input_risk_hint="high",
    )

    raw_signals = [
        RawSignals(
            claim_id="c1",
            web_results=[],
            exif_data={"DateTime": "2023:02:06", "GPSInfo": "37.57N, 36.93E"},
            image_integrity=ImageIntegritySignals(
                fft_ai_score=0.1, ela_manipulation_score=0.05,
                noise_consistency=0.9, has_exif=True,
            ),
            provenance=None,
        ),
        RawSignals(
            claim_id="c2",
            web_results=[Evidence(
                url="https://reuters.com", title="Turkey quake 2023",
                snippet="Destruction in Kahramanmaras", relevance_score=0.9,
                source_type="web",
            )],
            exif_data=None,
            image_integrity=None,
            provenance=None,
        ),
    ]

    fake_response = MagicMock()
    fake_response.text = json.dumps({
        "per_claim": [
            {"claim_id": "c1", "status": "refuted", "confidence": 0.9, "key_evidence": [], "reasoning": "No earthquake reports in Istanbul Apr 2026"},
            {"claim_id": "c2", "status": "supported", "confidence": 0.85, "key_evidence": [], "reasoning": "Image consistent with earthquake damage"},
        ],
        "overall_confidence": 0.15,
        "verdict": "likely_manipulated",
        "red_flags": ["EXIF date 2023 contradicts claimed 2026", "GPS points to Kahramanmaras not Istanbul"],
        "evidence_summary": "Recycled image from 2023 Turkey earthquake",
    })

    with patch("veriflow.aggregator._get_client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = fake_response
        profile = aggregate(claim_set, raw_signals, depth="quick")

    assert isinstance(profile, TrustProfile)
    assert profile.verdict == "likely_manipulated"
    assert profile.depth == "quick"
    assert len(profile.red_flags) == 2


def test_aggregate_no_claims():
    claim_set = ClaimSet(claims=[], formula="", input_risk_hint="low")
    profile = aggregate(claim_set, [], depth="quick")
    assert profile.verdict == "insufficient_data"
