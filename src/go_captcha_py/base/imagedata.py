"""Captcha image data wrappers, ported from go-captcha/v2/base/imagedata.

JPEGImageData / PNGImageData lazily encode the underlying PIL image to bytes,
base64, data-URI or file output.
"""

from __future__ import annotations

import base64
import io
from typing import Literal

from PIL import Image

ImageFormat = Literal["JPEG", "PNG"]


class _BaseImageData:
    """Common behavior for JPEG/PNG captcha image data."""

    format: ImageFormat = "PNG"

    def __init__(self, image: Image.Image) -> None:
        self._image = image

    def get(self) -> Image.Image:
        """Return the underlying PIL image."""
        return self._image

    def _encode(self, quality: int | None = None) -> bytes:
        buf = io.BytesIO()
        img = self._image
        if self.format == "JPEG":
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            if quality is not None and quality > 0:
                img.save(buf, format="JPEG", quality=quality)
            else:
                img.save(buf, format="JPEG")
        else:
            img.save(buf, format="PNG")
        return buf.getvalue()

    def to_bytes(self) -> bytes:
        """Encode to raw image bytes."""
        return self._encode()

    def to_base64(self, quality: int | None = None) -> str:
        """Encode to a bare base64 string."""
        return base64.b64encode(self._encode(quality)).decode("ascii")

    def to_base64_data(self, quality: int | None = None) -> str:
        """Encode to a data URI (data:image/...;base64,...)."""
        mime = "image/jpeg" if self.format == "JPEG" else "image/png"
        return f"data:{mime};base64,{self.to_base64(quality)}"

    def save_to_file(self, filepath: str, quality: int | None = None) -> None:
        """Write the image to a file path."""
        with open(filepath, "wb") as f:
            f.write(self._encode(quality))

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<{self.__class__.__name__} size={self._image.size} format={self.format}>"


class JPEGImageData(_BaseImageData):
    """JPEG-encoded captcha image (click/slide master images)."""

    format: ImageFormat = "JPEG"

    def to_bytes_with_quality(self, quality: int) -> bytes:
        """Encode to JPEG bytes with an explicit quality (0-100)."""
        return self._encode(quality)

    def to_base64_with_quality(self, quality: int) -> str:
        """Bare base64 with an explicit quality (0-100)."""
        return self.to_base64(quality)

    def to_base64_data_with_quality(self, quality: int) -> str:
        """Data URI with an explicit quality (0-100)."""
        return self.to_base64_data(quality)


class PNGImageData(_BaseImageData):
    """PNG-encoded captcha image (thumbnails / tiles / rotate images)."""

    format: ImageFormat = "PNG"
