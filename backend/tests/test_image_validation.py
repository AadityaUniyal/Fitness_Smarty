"""
Unit Tests for Image Upload Validation

Tests magic bytes verification, file size limits, and dimension
constraints in the ImageProcessor to prevent spoofed uploads.
"""

import io
import pytest
from PIL import Image as PILImage


def _make_processor():
    from app.image_processor import ImageProcessor
    return ImageProcessor()


def _make_jpeg_bytes(width=640, height=480) -> bytes:
    """Generate valid JPEG bytes."""
    img = PILImage.new("RGB", (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_png_bytes(width=640, height=480) -> bytes:
    """Generate valid PNG bytes."""
    img = PILImage.new("RGBA", (width, height), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestMagicBytesValidation:
    """Files must have correct magic bytes, not just extensions."""

    def test_valid_jpeg_passes(self):
        proc = _make_processor()
        result = proc.validate_image(_make_jpeg_bytes())
        assert result["valid"] is True
        assert result["format"] == "JPEG"

    def test_valid_png_passes(self):
        proc = _make_processor()
        result = proc.validate_image(_make_png_bytes())
        assert result["valid"] is True
        assert result["format"] == "PNG"

    def test_fake_image_rejected(self):
        """A text file with wrong extension should be rejected."""
        from app.image_processor import ImageValidationError

        proc = _make_processor()
        fake_bytes = b"This is not an image file at all." * 100
        with pytest.raises(ImageValidationError, match="signature"):
            proc.validate_image(fake_bytes)

    def test_gif_magic_rejected(self):
        """GIF files (GIF89a) should be rejected — not in allowed formats."""
        from app.image_processor import ImageValidationError

        proc = _make_processor()
        # GIF89a magic bytes + minimal padding
        gif_bytes = b"GIF89a" + b"\x00" * 2000
        with pytest.raises(ImageValidationError, match="signature"):
            proc.validate_image(gif_bytes)


class TestFileSizeLimits:
    """File size must be within bounds."""

    def test_too_small_rejected(self):
        from app.image_processor import ImageValidationError

        proc = _make_processor()
        tiny = b"\xff\xd8\xff" + b"\x00" * 100  # Valid magic but too small
        with pytest.raises(ImageValidationError, match="too small"):
            proc.validate_image(tiny)

    def test_large_valid_image_passes(self):
        proc = _make_processor()
        # Large but within 8MB limit
        result = proc.validate_image(_make_jpeg_bytes(1920, 1080))
        assert result["valid"] is True


class TestDimensionLimits:
    """Image dimensions must be within configured bounds."""

    def test_normal_dimensions_pass(self):
        proc = _make_processor()
        result = proc.validate_image(_make_jpeg_bytes(800, 600))
        assert result["valid"] is True
        assert result["width"] == 800
        assert result["height"] == 600
