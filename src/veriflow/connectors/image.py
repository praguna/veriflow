import io
from PIL import Image
from PIL.ExifTags import TAGS


def load_image(image_bytes: bytes) -> dict:
    """Load image bytes and detect format."""
    img = Image.open(io.BytesIO(image_bytes))
    mime_map = {"PNG": "image/png", "JPEG": "image/jpeg", "GIF": "image/gif", "WEBP": "image/webp"}
    mime_type = mime_map.get(img.format, f"image/{img.format.lower()}" if img.format else "image/unknown")
    return {"image_bytes": image_bytes, "mime_type": mime_type, "size": img.size}


def extract_exif(image_bytes: bytes) -> dict:
    """Extract EXIF metadata from an image."""
    img = Image.open(io.BytesIO(image_bytes))
    exif_data = img.getexif()
    if not exif_data:
        return {}
    return {TAGS.get(k, k): str(v) for k, v in exif_data.items()}
