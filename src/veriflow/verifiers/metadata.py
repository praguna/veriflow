EDITING_SOFTWARE = ["photoshop", "gimp", "lightroom", "affinity", "pixelmator", "snapseed"]


def verify_metadata(exif_data: dict) -> dict:
    """Extract verification-relevant signals from EXIF metadata.

    Returns structured metadata with flags for editing software detection.
    No LLM call — pure data extraction.
    """
    if not exif_data:
        return {
            "gps": None,
            "datetime": None,
            "camera": None,
            "software": None,
            "editing_software_detected": False,
            "has_metadata": False,
        }

    software = exif_data.get("Software", None)
    editing_detected = False
    if software:
        editing_detected = any(s in software.lower() for s in EDITING_SOFTWARE)

    return {
        "gps": exif_data.get("GPSInfo", None),
        "datetime": exif_data.get("DateTime", None),
        "camera": exif_data.get("Make", None),
        "software": software,
        "editing_software_detected": editing_detected,
        "has_metadata": bool(exif_data),
    }
