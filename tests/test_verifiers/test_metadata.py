from veriflow.verifiers.metadata import verify_metadata


def test_verify_metadata_with_gps():
    exif = {"GPSInfo": "37.57N, 36.93E", "DateTime": "2023:02:06 10:30:00", "Make": "Canon"}
    results = verify_metadata(exif)

    assert results["gps"] == "37.57N, 36.93E"
    assert results["datetime"] == "2023:02:06 10:30:00"
    assert results["camera"] == "Canon"


def test_verify_metadata_empty():
    results = verify_metadata({})
    assert results["gps"] is None
    assert results["datetime"] is None
    assert results["camera"] is None
    assert results["has_metadata"] is False


def test_verify_metadata_software_flag():
    exif = {"Software": "Adobe Photoshop CC 2024"}
    results = verify_metadata(exif)
    assert results["software"] == "Adobe Photoshop CC 2024"
    assert results["editing_software_detected"] is True
