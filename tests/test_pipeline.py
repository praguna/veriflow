import json
from unittest.mock import patch, MagicMock
from veriflow.pipeline import quick_verify
from veriflow.schemas import TrustProfile


def test_quick_verify_text():
    decompose_response = MagicMock()
    decompose_response.text = json.dumps({
        "claims": [{"id": "c1", "text": "Paris is capital of France", "modality": "text", "source": "user_text"}],
        "formula": "c1",
        "cross_modal_check": None,
        "input_risk_hint": "low",
    })

    tavily_results = {"results": [
        {"url": "https://en.wikipedia.org/wiki/Paris", "title": "Paris", "content": "Paris is the capital of France", "score": 0.95},
    ]}

    aggregate_response = MagicMock()
    aggregate_response.text = json.dumps({
        "per_claim": [{"claim_id": "c1", "status": "supported", "confidence": 0.95, "key_evidence": [], "reasoning": "Well established fact"}],
        "overall_confidence": 0.95,
        "verdict": "likely_authentic",
        "red_flags": [],
        "evidence_summary": "Claim is well supported",
    })

    with patch("veriflow.decomposer._get_client") as mock_decompose, \
         patch("veriflow.verifiers.web._get_client") as mock_tavily, \
         patch("veriflow.aggregator._get_client") as mock_aggregate:

        mock_decompose.return_value.models.generate_content.return_value = decompose_response
        mock_tavily.return_value.search.return_value = tavily_results
        mock_aggregate.return_value.models.generate_content.return_value = aggregate_response

        profile = quick_verify(text="Paris is the capital of France")

    assert isinstance(profile, TrustProfile)
    assert profile.verdict == "likely_authentic"
    assert profile.depth == "quick"
