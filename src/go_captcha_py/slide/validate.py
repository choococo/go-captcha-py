"""Slide captcha validation, ported from go-captcha/v2/slide/validate.go."""

from __future__ import annotations


def validate(sx: int, sy: int, dx: int, dy: int, padding: int) -> bool:
    """Check whether the user's slide position matches the target notch.

    Mirrors slide.Validate: the target is a (padding*2) square around (dx, dy).
    """
    new_x = padding * 2
    new_y = padding * 2
    new_dx = dx - padding
    new_dy = dy - padding

    return sx >= new_dx and sx <= new_dx + new_x and sy >= new_dy and sy <= new_dy + new_y


def check_point(sx: int, sy: int, dx: int, dy: int, padding: int) -> bool:
    """Deprecated alias kept for parity with Go < 2.1.0."""
    return validate(sx, sy, dx, dy, padding)
