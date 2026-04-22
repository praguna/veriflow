from unittest.mock import patch
from veriflow.verifiers.web import verify_web
from veriflow.schemas import Claim, Evidence


def test_verify_web_returns_evidence():
    claim = Claim(id="c1", text="Eiffel Tower is 330m tall", modality="text", source="user_text")
    fake_results = {
        "results": [
            {"url": "https://en.wikipedia.org/wiki/Eiffel_Tower", "title": "Eiffel Tower", "content": "330 metres tall", "score": 0.95},
        ]
    }

    with patch("veriflow.verifiers.web._get_client") as mock:
        mock.return_value.search.return_value = fake_results
        results = verify_web(claim)

    assert len(results) == 1
    assert isinstance(results[0], Evidence)
    assert results[0].source_type == "web"


def test_verify_web_no_results():
    claim = Claim(id="c1", text="Nonsense xyz", modality="text", source="user_text")

    with patch("veriflow.verifiers.web._get_client") as mock:
        mock.return_value.search.return_value = {"results": []}
        results = verify_web(claim)

    assert results == []
