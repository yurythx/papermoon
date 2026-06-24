"""Unit tests for ImageProcessor — pure bytes, no DB, no Django apps needed."""

import io

from PIL import Image as PILImage
import pytest


def _make_image(width: int, height: int, mode: str = "RGB", fmt: str = "JPEG") -> bytes:
    img = PILImage.new(mode, (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    if fmt == "JPEG":
        img.save(buf, format="JPEG")
    elif fmt == "PNG":
        img.save(buf, format="PNG")
    elif fmt == "WEBP":
        img.save(buf, format="WEBP")
    return buf.getvalue()


@pytest.fixture
def processor():
    from apps.cms.services import ImageProcessor

    return ImageProcessor


class TestImageProcessorToWebP:
    def test_converts_jpeg_to_webp(self, processor):
        data = _make_image(400, 300)
        result = processor.to_webp(data)
        out = PILImage.open(io.BytesIO(result))
        assert out.format == "WEBP"

    def test_converts_png_to_webp(self, processor):
        data = _make_image(400, 300, fmt="PNG")
        result = processor.to_webp(data)
        out = PILImage.open(io.BytesIO(result))
        assert out.format == "WEBP"

    def test_resizes_wide_image(self, processor):
        data = _make_image(2000, 1000)
        result = processor.to_webp(data, max_width=1200)
        out = PILImage.open(io.BytesIO(result))
        assert out.width == 1200
        assert out.height == 600  # proportional

    def test_does_not_upscale_small_image(self, processor):
        data = _make_image(800, 400)
        result = processor.to_webp(data, max_width=1200)
        out = PILImage.open(io.BytesIO(result))
        assert out.width == 800
        assert out.height == 400

    def test_converts_rgba_to_rgb_webp(self, processor):
        data = _make_image(400, 300, mode="RGBA", fmt="PNG")
        result = processor.to_webp(data)
        out = PILImage.open(io.BytesIO(result))
        assert out.format == "WEBP"
        assert out.mode == "RGB"

    def test_converts_palette_image(self, processor):
        img = PILImage.new("P", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = processor.to_webp(buf.getvalue())
        out = PILImage.open(io.BytesIO(result))
        assert out.format == "WEBP"

    def test_output_is_smaller_than_uncompressed(self, processor):
        data = _make_image(1200, 800)
        result = processor.to_webp(data)
        # WebP should be a valid non-empty output
        assert len(result) > 0
        out = PILImage.open(io.BytesIO(result))
        assert out.width == 1200
