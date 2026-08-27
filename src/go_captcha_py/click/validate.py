"""Click captcha validation, ported from go-captcha/v2/click/validate.go."""

from __future__ import annotations


def validate(sx: int, sy: int, dx: int, dy: int, width: int, height: int, padding: int) -> bool:
    """Check whether a click point is within the target area.

    Mirrors click.Validate: the target rect is (dx, dy, width+2*padding,
    height+2*padding).
    """
    new_width = width + (padding * 2)
    new_height = height + (padding * 2)
    new_dx = int(max(dx, dx - padding))
    new_dy = int(max(dy, dy - padding))

    return sx >= new_dx and sx <= new_dx + new_width and sy >= new_dy and sy <= new_dy + new_height


def check_point(sx: int, sy: int, dx: int, dy: int, width: int, height: int, padding: int) -> bool:
    """Deprecated alias kept for parity with Go < 2.1.0."""
    return validate(sx, sy, dx, dy, width, height, padding)
