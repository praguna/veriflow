import pymupdf


def extract_pdf_content(path: str) -> dict:
    """Extract text and images from a PDF file."""
    texts = []
    images = []
    with pymupdf.open(path) as doc:
        for page in doc:
            texts.append(page.get_text())
            for img_info in page.get_images():
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                images.append({
                    "image_bytes": base_image["image"],
                    "mime_type": f"image/{base_image['ext']}",
                })
    return {"text": "\n".join(texts), "images": images}
