import json
from unittest.mock import patch, MagicMock
from veriflow.decomposer import decompose
from veriflow.schemas import ClaimSet


def test_decompose_text_only():
    fake_response = MagicMock()
    fake_response.text = json.dumps({
        "claims": [
            {"id": "c1", "text": "The Eiffel Tower is 330m tall", "modality": "text", "source": "user_text"},
            {"id": "c2", "text": "It was built in 1889", "modality": "text", "source": "user_text"},
        ],
        "formula": "c1 AND c2",
        "cross_modal_check": None,
        "input_risk_hint": "low",
    })

    with patch("veriflow.decomposer._get_client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = fake_response
        result = decompose(text="The Eiffel Tower is 330m tall and was built in 1889.")

    assert isinstance(result, ClaimSet)
    assert len(result.claims) == 2
    assert result.formula == "c1 AND c2"
    assert result.input_risk_hint == "low"


def test_decompose_with_image():
    fake_response = MagicMock()
    fake_response.text = json.dumps({
        "claims": [
            {"id": "c1", "text": "Earthquake hit Istanbul", "modality": "text", "source": "caption"},
            {"id": "c2", "text": "Building is destroyed", "modality": "visual", "source": "image"},
        ],
        "formula": "c1 AND c2",
        "cross_modal_check": {"match": False, "reason": "Signage in image is Arabic, not Turkish"},
        "input_risk_hint": "high",
    })

    with patch("veriflow.decomposer._get_client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = fake_response
        result = decompose(
            text="Earthquake hits Istanbul",
            image_bytes=b"fake-image",
            mime_type="image/jpeg",
        )

    assert len(result.claims) == 2
    assert result.cross_modal_check is not None
    assert result.cross_modal_check.match is False
    assert result.input_risk_hint == "high"


def test_decompose_empty_input():
    result = decompose()
    assert len(result.claims) == 0
