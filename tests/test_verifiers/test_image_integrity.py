import io
import numpy as np
from PIL import Image
from veriflow.verifiers.image_integrity import analyze_image_integrity
from veriflow.schemas import ImageIntegritySignals


def _make_test_image(size=(64, 64), noise=True) -> bytes:
    """Create a test image with optional camera-like noise."""
    if noise:
        arr = np.random.randint(100, 200, (*size, 3), dtype=np.uint8)
    else:
        arr = np.full((*size, 3), 128, dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def test_analyze_returns_signals():
    image_bytes = _make_test_image()
    result = analyze_image_integrity(image_bytes)
    assert isinstance(result, ImageIntegritySignals)
    assert 0.0 <= result.fft_ai_score <= 1.0
    assert 0.0 <= result.ela_manipulation_score <= 1.0
    assert 0.0 <= result.noise_consistency <= 1.0


def test_uniform_image_flags_low_noise():
    """A perfectly uniform image has no natural noise — suspicious."""
    image_bytes = _make_test_image(noise=False)
    result = analyze_image_integrity(image_bytes)
    assert result.noise_consistency > 0.8
