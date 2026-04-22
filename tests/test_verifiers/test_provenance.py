from unittest.mock import patch
from veriflow.verifiers.provenance import verify_provenance
from veriflow.schemas import Evidence


def test_verify_provenance_found():
    fake_response = {
        "visual_matches": [
            {"position": 1, "title": "Reuters: Turkey earthquake 2023", "link": "https://reuters.com/turkey", "thumbnail": "..."},
        ]
    }

    with patch("veriflow.verifiers.provenance._search_reverse_image", return_value=fake_response):
        results = verify_provenance(b"fake-image-bytes")

    assert len(results) == 1
    assert results[0].source_type == "provenance"
    assert "Reuters" in results[0].title


def test_verify_provenance_not_found():
    with patch("veriflow.verifiers.provenance._search_reverse_image", return_value={"visual_matches": []}):
        results = verify_provenance(b"fake-image-bytes")

    assert results == []
