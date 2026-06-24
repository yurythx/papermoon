"""Image processing — SRP: this module only knows about bytes, not Django models."""

from __future__ import annotations

import io

from PIL import Image


class ImageProcessor:
    MAX_WIDTH = 1200
    QUALITY = 82

    @staticmethod
    def to_webp(data: bytes, max_width: int = 1200) -> bytes:
        """Convert image bytes to WebP, resizing proportionally if wider than max_width."""
        img = Image.open(io.BytesIO(data))

        # Convert palette/RGBA to RGB for WebP compatibility
        if img.mode in ("P", "RGBA"):
            img = img.convert("RGBA")  # type: ignore[assignment]
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # type: ignore[arg-type]
            img = background  # type: ignore[assignment]
        elif img.mode != "RGB":
            img = img.convert("RGB")  # type: ignore[assignment]

        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)  # type: ignore[assignment,attr-defined]

        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=ImageProcessor.QUALITY, method=6)
        return buf.getvalue()
