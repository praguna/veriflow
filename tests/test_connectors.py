import base64
from unittest.mock import patch, MagicMock
from veriflow.connectors.pdf import extract_pdf_content
from veriflow.connectors.url import fetch_url_content
from veriflow.connectors.image import load_image, extract_exif


def test_extract_pdf_content():
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Page one text."
    mock_page.get_images.return_value = []

    mock_doc = MagicMock()
    mock_doc.__iter__ = lambda self: iter([mock_page])
    mock_doc.__enter__ = lambda self: self
    mock_doc.__exit__ = lambda self, *a: None

    with patch("veriflow.connectors.pdf.pymupdf.open", return_value=mock_doc):
        result = extract_pdf_content("/fake/path.pdf")

    assert result["text"] == "Page one text."
    assert result["images"] == []


def test_fetch_url_content():
    mock_response = MagicMock()
    mock_response.text = "<html><body><p>Hello world</p></body></html>"
    mock_response.status_code = 200

    with patch("veriflow.connectors.url.httpx.get", return_value=mock_response):
        result = fetch_url_content("https://example.com")

    assert "Hello world" in result["text"]
    assert result["url"] == "https://example.com"


def test_load_image():
    png_1x1 = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )
    result = load_image(png_1x1)
    assert result["mime_type"] == "image/png"
    assert result["image_bytes"] == png_1x1
    assert result["size"] == (1, 1)
