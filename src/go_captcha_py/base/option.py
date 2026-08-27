"""Shared option value types, ported from go-captcha/v2/base/option."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Size:
    """Image size in pixels."""

    width: int
    height: int


@dataclass(slots=True)
class Point:
    """A 2D point."""

    x: int
    y: int


@dataclass(slots=True)
class RangeVal:
    """An inclusive [min, max] range."""

    min: int
    max: int


# Distortion levels for the click thumbnail background (option.go / default.go)
DISTORT_LEVEL_1 = 1
DISTORT_LEVEL_2 = 2
DISTORT_LEVEL_3 = 3
DISTORT_LEVEL_4 = 4
DISTORT_LEVEL_5 = 5

# JPEG save quality
QUALITY_NONE = 0
QUALITY_LOW = 40
QUALITY_MID = 60
QUALITY_HIGH = 80
QUALITY_MAX = 100
