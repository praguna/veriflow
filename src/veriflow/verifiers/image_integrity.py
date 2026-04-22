"""Image integrity analysis using lightweight forensic techniques.

FFT spectral analysis: detects AI-generated images via frequency domain artifacts.
  - Well-documented in forensics literature. GAN/diffusion models leave periodic
    spectral peaks that natural photographs don't exhibit.

ELA (Error Level Analysis): detects spliced/edited regions.
  - Re-compress JPEG, compare error levels. Edited regions show different compression.
  - Standard forensic technique. Does NOT detect AI-generated images.

Noise consistency: detects composited images.
  - Real cameras produce uniform sensor noise. Spliced regions have different noise.
"""

import io
import numpy as np
from PIL import Image
from veriflow.schemas import ImageIntegritySignals


def _fft_ai_score(image: Image.Image) -> float:
    """Detect AI-generated images via frequency spectrum analysis.

    Computes 2D FFT, builds radial power spectrum, measures deviation
    from the smooth 1/f falloff expected in natural photographs.
    AI images show periodic bumps in the spectrum.
    """
    gray = np.array(image.convert("L"), dtype=np.float64)
    f_transform = np.fft.fft2(gray)
    f_shift = np.fft.fftshift(f_transform)
    magnitude = np.log1p(np.abs(f_shift))

    h, w = magnitude.shape
    cy, cx = h // 2, w // 2
    y, x = np.ogrid[:h, :w]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2).astype(int)
    max_r = min(cy, cx)

    radial_profile = np.zeros(max_r)
    for i in range(max_r):
        mask = r == i
        if mask.any():
            radial_profile[i] = magnitude[mask].mean()

    if len(radial_profile) < 10:
        return 0.5

    # Measure deviation from smooth falloff
    smoothed = np.convolve(radial_profile, np.ones(5) / 5, mode="same")
    deviation = np.abs(radial_profile - smoothed)
    score = float(np.mean(deviation) / (np.mean(radial_profile) + 1e-8))

    return float(min(score / 0.2, 1.0))


def _ela_score(image_bytes: bytes, quality: int = 90) -> float:
    """Error Level Analysis for detecting spliced/edited regions.

    Re-compress at known quality, compute difference. Authentic images
    show uniform error levels; edited regions show higher error.
    """
    original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    buf = io.BytesIO()
    original.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")

    diff = np.abs(
        np.array(original, dtype=np.float64) - np.array(recompressed, dtype=np.float64)
    )

    h, w = diff.shape[:2]
    block_size = 8
    block_means = []
    for i in range(0, h - block_size, block_size):
        for j in range(0, w - block_size, block_size):
            block = diff[i : i + block_size, j : j + block_size]
            block_means.append(block.mean())

    if not block_means:
        return 0.5

    variance = float(np.var(block_means))
    return float(min(variance / 100.0, 1.0))


def _noise_consistency(image: Image.Image) -> float:
    """Check if noise patterns are consistent across the image.

    Real camera photos have uniform sensor noise. Composited images
    have different noise profiles in different regions.
    Returns 0-1 where 1 = highly consistent (likely authentic).
    """
    gray = np.array(image.convert("L"), dtype=np.float64)
    h, w = gray.shape
    grid_size = max(h, w) // 4

    if grid_size < 8:
        return 0.5

    local_vars = []
    for i in range(0, h - grid_size, grid_size):
        for j in range(0, w - grid_size, grid_size):
            block = gray[i : i + grid_size, j : j + grid_size]
            # High-pass filter: subtract local mean to isolate noise
            kernel_size = 3
            from numpy.lib.stride_tricks import sliding_window_view

            padded = np.pad(block, kernel_size // 2, mode="reflect")
            windows = sliding_window_view(padded, (kernel_size, kernel_size))
            smoothed = windows.mean(axis=(-1, -2))
            noise = block - smoothed
            local_vars.append(float(np.var(noise)))

    if len(local_vars) < 2:
        return 0.5

    mean_var = np.mean(local_vars)
    if mean_var < 1e-8:
        return 1.0

    cv = float(np.std(local_vars) / mean_var)
    consistency = max(0.0, min(1.0, 1.0 - cv / 2.0))
    return consistency


def analyze_image_integrity(
    image_bytes: bytes, has_exif: bool = False
) -> ImageIntegritySignals:
    """Run all lightweight forensic checks on an image.

    Returns scores for:
    - fft_ai_score: likelihood of AI generation (higher = more likely AI)
    - ela_manipulation_score: likelihood of splicing/editing (higher = more likely edited)
    - noise_consistency: noise uniformity (higher = more consistent = likely authentic)
    - has_exif: whether EXIF metadata is present (absence is suspicious)
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return ImageIntegritySignals(
        fft_ai_score=_fft_ai_score(image),
        ela_manipulation_score=_ela_score(image_bytes),
        noise_consistency=_noise_consistency(image),
        has_exif=has_exif,
    )
