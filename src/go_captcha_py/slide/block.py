"""Slide captcha block data, ported from go-captcha/v2/slide/block.go."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class Block:
    """Slide captcha verification data.

    JSON field names match the Go struct tags for frontend compatibility.
    x/y = notch (target) position on the master image; dx/dy = tile start
    position (left edge for basic mode).
    """

    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    angle: int = 0
    # deprecated aliases kept for Go < 2.1.0 JSON parity
    tile_x: int = 0
    tile_y: int = 0
    dx: int = 0
    dy: int = 0

    def to_dict(self) -> dict:
        """Serialize with the Go JSON field names."""
        return asdict(self)
