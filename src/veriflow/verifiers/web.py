import os
from tavily import TavilyClient
from veriflow.schemas import Claim, Evidence

_client = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    return _client


def verify_web(claim: Claim, max_results: int = 5) -> list[Evidence]:
    """Search the web for evidence supporting or refuting a claim."""
    client = _get_client()
    response = client.search(query=claim.text, max_results=max_results)
    return [
        Evidence(
            url=r["url"],
            title=r.get("title", ""),
            snippet=r.get("content", ""),
            relevance_score=r.get("score", 0.0),
            source_type="web",
        )
        for r in response.get("results", [])
    ]
