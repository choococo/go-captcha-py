"""Click captcha drawing engine, ported from go-captcha/v2/click/draw.go.

Renders the master image (characters / shapes scattered over a background)
and the thumbnail image (verification targets over a disturbed background).
"""

from __future__ import annotations

import math
import random as _random

from PIL import Image, ImageDraw

from ..base.helper import (
    calc_margin_blank_area,
    create_nrgba_canvas,
    parse_hex_color,
    tint_image,
)
from ..base.randgen import (
    format_alpha,
    is_chinese_char,
    rand_int_fast,
)
from .dot import DRAW_TYPE_IMAGE, DrawDot


def _contrast_stroke(
    text_color: tuple[int, int, int, int], size: int
) -> tuple[int, tuple[int, int, int, int]]:
    """Stroke width + inverse-luminance stroke color for a text color.

    Light glyphs get a dark outline, dark glyphs a light one — so the
    character edge always contrasts with whatever it overlaps.
    """
    lum = 0.299 * text_color[0] + 0.587 * text_color[1] + 0.114 * text_color[2]
    stroke_color = (17, 17, 17, 255) if lum > 140 else (255, 255, 255, 255)
    width = max(1, round(size / 14))
    return width, stroke_color


class DrawImageParams:
    """Parameters for drawing a click captcha image (master or thumb)."""

    __slots__ = (
        "alpha",
        "background",
        "background_circles_num",
        "background_distort",
        "background_slim_line_num",
        "captcha_draw_dots",
        "height",
        "shadow_color",
        "shadow_point",
        "show_shadow",
        "thumb_disturb_alpha",
        "width",
    )

    def __init__(
        self,
        width: int,
        height: int,
        captcha_draw_dots: list[DrawDot],
        background: Image.Image | None = None,
        background_distort: int = 0,
        background_circles_num: int = 0,
        background_slim_line_num: int = 0,
        alpha: float = 1.0,
        show_shadow: bool = False,
        shadow_color: str = "",
        shadow_point: tuple[int, int] = (0, 0),
        thumb_disturb_alpha: float = 1.0,
    ) -> None:
        self.width = width
        self.height = height
        self.background = background
        self.background_distort = background_distort
        self.background_circles_num = background_circles_num
        self.background_slim_line_num = background_slim_line_num
        self.alpha = alpha
        self.captcha_draw_dots = captcha_draw_dots
        self.show_shadow = show_shadow
        self.shadow_color = shadow_color
        self.shadow_point = shadow_point
        self.thumb_disturb_alpha = thumb_disturb_alpha


class DrawImage:
    """Concrete drawing implementation (drawImage in draw.go)."""

    # ------------------------------------------------------------------
    # Master image
    # ------------------------------------------------------------------

    def draw_with_nrgba(self, params: DrawImageParams) -> Image.Image:
        """Draw the master image: dots over a randomly-cropped background.

        Mirrors DrawImage.DrawWithNRGBA.
        """
        dots = params.captcha_draw_dots
        cvs = create_nrgba_canvas(params.width, params.height, True)

        for dot in dots:
            dot_image, area = self._draw_dot_image(dot, params)
            min_x, min_y, max_x, max_y = area
            width = max_x - min_x
            height = max_y - min_y
            cvs.alpha_composite(
                dot_image.crop((min_x, min_y, max_x, max_y)),
                dest=(max(0, min(dot.x, params.width - width)), max(0, min(dot.y, params.height - height))),
            )
            dot.height = height
            dot.width = width
            dot.dot.height = height
            dot.dot.width = width

        img = params.background
        if img is not None:
            m = create_nrgba_canvas(params.width, params.height, True)
            m.paste(img.convert("RGB"), (0, 0), None)
            m.alpha_composite(cvs, dest=(0, 0))
            return m
        return cvs

    # ------------------------------------------------------------------
    # Thumbnail (palette path with background disturb)
    # ------------------------------------------------------------------

    def draw_with_palette(
        self,
        params: DrawImageParams,
        text_colors: list[tuple[int, int, int, int]],
        bg_colors: list[tuple[int, int, int, int]],
    ) -> Image.Image:
        """Draw the thumbnail with palette-quantized disturb effects.

        Mirrors DrawImage.DrawWithPalette: circles + slim lines + sine distort
        background, then dots on top.
        """
        dots = params.captcha_draw_dots
        disturb_alpha = format_alpha(params.thumb_disturb_alpha)
        n_bg_colors = [(r, g, b, disturb_alpha) for (r, g, b, _a) in bg_colors]

        cvs = create_nrgba_canvas(params.width, params.height, True)
        draw = ImageDraw.Draw(cvs)
        if params.background_circles_num > 0:
            self._random_fill_with_circles(
                draw, params.width, params.height, params.background_circles_num, 1, n_bg_colors
            )
        if params.background_slim_line_num > 0:
            self._random_draw_slim_line(
                draw, params.width, params.height, params.background_slim_line_num, n_bg_colors
            )

        for dot in dots:
            c_color = parse_hex_color(dot.color) or (0, 0, 0, 255)
            if dot.draw_type == DRAW_TYPE_IMAGE:
                dot_image = self._draw_shape_image(dot, c_color)
                dot_image = dot_image.rotate(dot.angle, resample=Image.BICUBIC, expand=True)
                cvs.alpha_composite(dot_image)
            else:
                self._draw_string(draw, dot, c_color)

        if params.background is not None:
            img = params.background
            m = create_nrgba_canvas(params.width, params.height, True)
            m.paste(img.convert("RGB"), (0, 0), None)
            cvs = self._distort(
                cvs, rand_int_fast(5, 10), params.background_distort or rand_int_fast(120, 200)
            )
            m.alpha_composite(cvs, dest=(0, 0))
            return m

        if params.background_distort > 0:
            cvs = self._distort(cvs, rand_int_fast(5, 10), params.background_distort)

        return cvs

    # ------------------------------------------------------------------
    # Thumbnail (NRGBA2 path: non-deform, keeps original colors)
    # ------------------------------------------------------------------

    def draw_with_nrgba2(
        self,
        params: DrawImageParams,
        text_colors: list[tuple[int, int, int, int]],
        bg_colors: list[tuple[int, int, int, int]],
    ) -> Image.Image:
        """Draw the thumbnail keeping dot colors/shape (non-deform path).

        Mirrors DrawImage.DrawWithNRGBA2.
        """
        dots = params.captcha_draw_dots
        disturb_alpha = format_alpha(params.thumb_disturb_alpha)
        n_bg_colors = [(r, g, b, disturb_alpha) for (r, g, b, _a) in bg_colors]

        ccvs = create_nrgba_canvas(params.width, params.height, True)
        if params.background is not None:
            img = params.background
            ccvs.paste(img.convert("RGB"), (0, 0), None)

        cvs = create_nrgba_canvas(params.width, params.height, True)
        draw = ImageDraw.Draw(cvs)
        if params.background_circles_num > 0:
            self._random_fill_with_circles(
                draw, params.width, params.height, params.background_circles_num, 1, n_bg_colors
            )
        if params.background_slim_line_num > 0:
            self._random_draw_slim_line(
                draw, params.width, params.height, params.background_slim_line_num, n_bg_colors
            )
        if params.background_distort > 0:
            cvs = self._distort(cvs, rand_int_fast(5, 10), params.background_distort)

        cvs_bounds_w = params.width
        width = cvs_bounds_w // max(len(dots), 1)
        for i, dot in enumerate(dots):
            c_color = parse_hex_color(dot.color) or (0, 0, 0, 255)
            if dot.draw_type == DRAW_TYPE_IMAGE:
                dot_image = self._draw_shape_image(dot, c_color)
                dot_image = dot_image.rotate(dot.angle, resample=Image.BICUBIC, expand=True)
                min_x, min_y, max_x, max_y = calc_margin_blank_area(dot_image)
                dot_image = dot_image.crop((min_x, min_y, max_x, max_y))
                dx = max(width * i, 8)
                dy = rand_int_fast(1, max(params.height - dot_image.size[1] - 4, 2))
                ccvs.alpha_composite(dot_image, dest=(dx, dy))
            else:
                c_image = self._draw_string_image(dot, c_color)
                c_image = c_image.rotate(dot.angle, resample=Image.BICUBIC, expand=True)
                min_x, min_y, max_x, max_y = calc_margin_blank_area(c_image)
                c_image = c_image.crop((min_x, min_y, max_x, max_y))
                b_w, b_h = c_image.size
                dx = max(width * i + width // max(b_w, 1), 8)
                dy = rand_int_fast(1, max(params.height - b_h - 4, 2))
                ccvs.alpha_composite(c_image, dest=(dx, dy))

        # merge disturb layer under the content layer
        merged = create_nrgba_canvas(params.width, params.height, True)
        merged.alpha_composite(cvs, dest=(0, 0))
        final = create_nrgba_canvas(params.width, params.height, True)
        final.alpha_composite(merged, dest=(0, 0))
        final.alpha_composite(ccvs, dest=(0, 0))
        return final

    # ------------------------------------------------------------------
    # Dot renderers
    # ------------------------------------------------------------------

    def _draw_dot_image(
        self, dot: DrawDot, params: DrawImageParams
    ) -> tuple[Image.Image, tuple[int, int, int, int]]:
        """Render one dot (char/shape + optional shadow), rotated.

        Returns (image, blank-area-rect). Mirrors DrawDotImage.
        """
        c_color = parse_hex_color(dot.color) or (0, 0, 0, 255)
        c_color = (c_color[0], c_color[1], c_color[2], format_alpha(params.alpha))

        if dot.draw_type == DRAW_TYPE_IMAGE:
            c_image = self._draw_shape_image(dot, c_color)
        else:
            c_image = self._draw_string_image(dot, c_color)

        shadow_color_hex = params.shadow_color or "#101010"
        s_color = parse_hex_color(shadow_color_hex) or (16, 16, 16, 255)

        cvs = create_nrgba_canvas(dot.width + 10, dot.height + 10, True)
        if params.show_shadow:
            if dot.draw_type == DRAW_TYPE_IMAGE:
                shadow_img = self._draw_shape_image(dot, s_color)
            else:
                shadow_img = self._draw_string_image(dot, s_color)
            cvs.alpha_composite(shadow_img, dest=(params.shadow_point[0], params.shadow_point[1]))
        cvs.alpha_composite(c_image, dest=(0, 0))
        cvs = cvs.rotate(dot.angle, resample=Image.BICUBIC, expand=True)

        area = calc_margin_blank_area(cvs)
        return cvs, area

    def _draw_string_image(self, dot: DrawDot, text_color: tuple[int, int, int, int]) -> Image.Image:
        """Render the dot text onto its own canvas. Mirrors DrawStringImage."""
        cvs = create_nrgba_canvas(dot.width + 10, dot.height + 10, True)
        draw = ImageDraw.Draw(cvs)
        self._draw_string(draw, dot, text_color, offset=True)
        return cvs

    def _draw_string(
        self,
        draw: ImageDraw.ImageDraw,
        dot: DrawDot,
        text_color: tuple[int, int, int, int],
        offset: bool = False,
    ) -> None:
        """Draw text with the dot's font/size; anchored like freetype.Pt in Go.

        Adds a contrasting stroke around the glyph so characters stay legible
        over busy photo backgrounds (stroke color = the luminance inverse of
        the text color).
        """
        text = dot.text or ""
        font = dot.font
        if font is None or font.size != dot.size:
            from ..resources import get_font

            font = get_font(dot.size)
        x = 10 if offset else dot.x
        y = (dot.height - 5) if offset else dot.y
        if is_chinese_char(text):
            y = dot.height if offset else dot.y
        stroke = _contrast_stroke(text_color, dot.size)
        if offset:
            # Go's freetype.DrawString uses a baseline point, while Pillow's
            # default text anchor treats the point as the glyph's top.  The
            # off-screen canvas is sized around the Go-style baseline, so use
            # Pillow's left-baseline anchor or most of the glyph is clipped.
            draw.text(
                (x, y),
                text,
                font=font,
                anchor="ls",
                fill=text_color,
                stroke_width=stroke[0],
                stroke_fill=stroke[1],
            )
        else:
            draw.text((x, y), text, font=font, fill=text_color, stroke_width=stroke[0], stroke_fill=stroke[1])

    def _draw_shape_image(self, dot: DrawDot, c_color: tuple[int, int, int, int]) -> Image.Image:
        """Scale the shape image to the dot size, tinted unless original color.

        Mirrors DrawShapeImage.
        """
        assert dot.image is not None
        cvs = create_nrgba_canvas(dot.width + 10, dot.height + 10, True)
        src = dot.image
        if src.mode != "RGBA":
            src = src.convert("RGBA")
        scaled = src.resize(
            (dot.width, dot.height), Image.BICUBIC if src.size != (dot.width, dot.height) else Image.NEAREST
        )
        if not dot.use_original_color:
            scaled = tint_image(scaled, c_color)
        cvs.alpha_composite(scaled, dest=(0, 0))
        return cvs

    # ------------------------------------------------------------------
    # Disturb helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _random_fill_with_circles(
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        n: int,
        max_radius: int,
        colors: list[tuple[int, int, int, int]],
    ) -> None:
        """Random small filled circles. Mirrors randomFillWithCircles."""
        for _ in range(n):
            co = colors[_random.randint(0, len(colors) - 1)] if colors else (0, 0, 0, 255)
            r = rand_int_fast(1, max_radius)
            cx = rand_int_fast(r, max(width - r, r + 1))
            cy = rand_int_fast(r, max(height - r, r + 1))
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=co)

    @staticmethod
    def _random_draw_slim_line(
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        num: int,
        colors: list[tuple[int, int, int, int]],
    ) -> None:
        """Random slim lines. Mirrors randomDrawSlimLine."""
        first = width // 10
        end = first * 9
        y = height // 3
        for i in range(num):
            x1 = _random.randint(0, max(first - 1, 0))
            x2 = _random.randint(0, max(first - 1, 0)) + end
            if i % 2 == 0:
                y1 = _random.randint(0, max(y - 1, 0)) + y * 2
                y2 = _random.randint(0, max(y - 1, 0))
            else:
                y1 = _random.randint(0, max(y - 1, 0)) + y * (i % 2)
                y2 = _random.randint(0, max(y - 1, 0)) + y * 2
            co = colors[_random.randint(0, len(colors) - 1)] if colors else (0, 0, 0, 255)
            draw.line((x1, y1, x2, y2), fill=co, width=1)

    @staticmethod
    def _distort(img: Image.Image, amplitude: float, frequency: float) -> Image.Image:
        """Sine-wave distort an image, mirroring canvas Distort.

        Go's Distort applies a sine wave along y as a function of x:
        dst(x, y) = src(x, y + amplitude*sin(2*pi*x/frequency)).
        """
        w, h = img.size
        src = img.load()
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dst = out.load()
        for x in range(w):
            shift = int(amplitude * math.sin(2.0 * math.pi * x / frequency))
            for y in range(h):
                sy = y + shift
                if 0 <= sy < h:
                    dst[x, y] = src[x, sy]
        return out
