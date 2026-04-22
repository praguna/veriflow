import re
import httpx


def fetch_url_content(url: str, timeout: float = 10.0) -> dict:
    """Fetch a URL and return cleaned text content."""
    response = httpx.get(url, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    text = re.sub(r"<[^>]+>", " ", response.text)
    text = re.sub(r"\s+", " ", text).strip()
    return {"text": text, "url": url}
