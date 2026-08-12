"""Image processing — SRP: this module only knows about bytes, not Django models."""

from __future__ import annotations

import io

from PIL import Image

ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_UPLOAD_BYTES = 8 * 1024 * 1024  # 8MB — plenty for a hero/gallery source image


class InvalidImageUploadError(ValueError):
    """Raised when an upload isn't a decodable image within the allowed limits."""


def validate_image_upload(content_type: str | None, size: int, data: bytes) -> None:
    """Reject uploads that aren't a real, size-bounded image before any DB write.

    Content-type is client-supplied and spoofable, so it's only a fast
    pre-filter — Image.open()/.verify() is what actually proves the bytes
    decode as an image. This closes off SVG (possible stored-XSS if ever
    served with an image/svg+xml content-type or linked directly) and any
    other non-image upload that convert_hero_to_webp (apps/cms/signals.py)
    would otherwise silently swallow and save as-is.
    """
    if size > MAX_IMAGE_UPLOAD_BYTES:
        raise InvalidImageUploadError(
            f"Arquivo maior que {MAX_IMAGE_UPLOAD_BYTES // (1024 * 1024)}MB."
        )
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise InvalidImageUploadError(
            f"Tipo de arquivo não suportado: {content_type or 'desconhecido'}."
        )
    try:
        Image.open(io.BytesIO(data)).verify()
    except Exception as exc:
        raise InvalidImageUploadError("Arquivo não é uma imagem válida.") from exc


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
