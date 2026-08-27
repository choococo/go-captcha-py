"""Click captcha generator, ported from go-captcha/v2/click/click.go."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from ..base.helper import parse_hex_color
from ..base.imagedata import JPEGImageData, PNGImageData
from ..base.option import RangeVal, Size
from ..base.randgen import (
    perm,
    rand_hex_color,
    rand_image,
    rand_index,
    rand_int_fast,
    rand_string,
)
from .dot import DRAW_TYPE_IMAGE, DRAW_TYPE_STRING, Dot, DrawDot
from .draw import DrawImage, DrawImageParams
from .options import Options, Resources

MODE_TEXT = 0
MODE_SHAPE = 1


class CaptchaError(Exception):
    """Click captcha generation error."""


EMPTY_SHAPES_ERR = "no shapes provided"
EMPTY_CHARACTER_ERR = "no character provided"
CHAR_RANGE_LEN_ERR = "character length must be greater than rangeLen.Max"
SHAPES_RANGE_LEN_ERR = "total number of shapes must be greater than rangeLen.Max"
SHAPES_TYPE_ERR = "shape must be an image type"
EMPTY_BACKGROUND_IMAGE_ERR = "no background image"


@dataclass(slots=True)
class CaptchaData:
    """Generated captcha: verify dots + master image + thumb image."""

    dots: dict[int, Dot]
    master_image: JPEGImageData
    thumb_image: PNGImageData

    def get_data(self) -> dict[int, Dot]:
        """Verification dots (kept server-side; never sent to the client)."""
        return self.dots

    def get_master_image(self) -> JPEGImageData:
        """Main captcha image."""
        return self.master_image

    def get_thumb_image(self) -> PNGImageData:
        """Thumbnail captcha image."""
        return self.thumb_image


class Captcha:
    """Click captcha implementation (captcha struct in click.go)."""

    def __init__(
        self, mode: int = MODE_TEXT, opts: Options | None = None, resources: Resources | None = None
    ) -> None:
        self.mode = mode
        self.opts = opts if opts is not None else Options()
        self.resources = resources if resources is not None else Resources()
        self._draw = DrawImage()

        if mode == MODE_SHAPE:
            # shape-mode specific defaults (newWithMode)
            self.opts.thumb_bg_distort = 1  # DistortLevel1
            self.opts.range_size = RangeVal(24, 30)
            self.opts.range_thumb_size = RangeVal(14, 20)

    # ------------------------------------------------------------------

    def generate(self) -> CaptchaData:
        """Generate a captcha. Raises CaptchaError on invalid config."""
        if self.mode == MODE_SHAPE:
            return self._generate_with_shape()
        return self._generate_with_text()

    # ------------------------------------------------------------------

    def _generate_with_shape(self) -> CaptchaData:
        self._check()
        shapes = self._gen_shapes()

        dots = self._gen_dots(self.opts.image_size, self.opts.range_size, shapes, 10)
        verify_dots, verify_shapes = self._range_check_dots(dots)
        thumb_dots = self._gen_dots(self.opts.thumb_image_size, self.opts.range_thumb_size, verify_shapes, 0)

        master_image = self._gen_master_image(self.opts.image_size, dots)
        thumb_image = self._gen_thumb_image(self.opts.thumb_image_size, thumb_dots)

        return CaptchaData(
            dots=verify_dots, master_image=JPEGImageData(master_image), thumb_image=PNGImageData(thumb_image)
        )

    def _generate_with_text(self) -> CaptchaData:
        self._check()
        chars = self._gen_chars()

        dots = self._gen_dots(self.opts.image_size, self.opts.range_size, chars, 10)
        verify_dots, verify_values = self._range_check_dots(dots)
        thumb_dots = self._gen_dots(self.opts.thumb_image_size, self.opts.range_thumb_size, verify_values, 0)

        master_image = self._gen_master_image(self.opts.image_size, dots)
        thumb_image = self._gen_thumb_image(self.opts.thumb_image_size, thumb_dots)

        return CaptchaData(
            dots=verify_dots, master_image=JPEGImageData(master_image), thumb_image=PNGImageData(thumb_image)
        )

    # ------------------------------------------------------------------

    def _gen_chars(self) -> list[str]:
        length = rand_int_fast(self.opts.range_len.min, self.opts.range_len.max)
        chars = self._gen_rand_unique(length, self.resources.chars)
        if not chars:
            raise CaptchaError(EMPTY_CHARACTER_ERR)
        return chars

    def _gen_shapes(self) -> list[str]:
        length = rand_int_fast(self.opts.range_len.min, self.opts.range_len.max)
        shapes = self._gen_rand_unique(length, self.resources.shapes)
        if not shapes:
            raise CaptchaError(EMPTY_SHAPES_ERR)
        return shapes

    @staticmethod
    def _gen_rand_unique(length: int, pool: list[str]) -> list[str]:
        """Random unique picks from pool (genRandShape / genRandChar)."""
        out: list[str] = []
        guard = 0
        while len(out) < length and guard < length * 50:
            guard += 1
            value = rand_string(pool)
            if value and value not in out:
                out.append(value)
        return out

    def _gen_dots(self, image_size: Size, size: RangeVal, values: list[str], padding: int) -> dict[int, Dot]:
        """Scatter dots over the image area. Mirrors genDots."""
        dots: dict[int, Dot] = {}
        width = image_size.width
        height = image_size.height
        if padding > 0:
            width -= padding
            height -= padding

        length = len(values)
        for i, value in enumerate(values):
            rand_angle = self._rand_angle()
            rand_color = rand_hex_color(self.opts.range_colors)
            rand_color2 = rand_hex_color(self.opts.range_thumb_colors)
            rand_size = rand_int_fast(size.min, size.max)
            c_height = rand_size
            c_width = rand_size

            if self.mode == MODE_TEXT and len(value) > 1:
                c_width = rand_size * len(value)
                if rand_angle > 0:
                    surplus = c_width - rand_size
                    ra = rand_angle % 90
                    pr = surplus / 90
                    r = max(ra * pr, 1)
                    c_height = c_height + int(r)
                    c_width = c_width + int(r)

            dy = 10
            w = width // length
            rd = abs(w - c_width)
            xx = (i * w) + rand_int_fast(0, max(int(rd), 1))
            yy = rand_int_fast(dy, height + c_height)

            # Clamp with the ACTUAL glyph box (c_width covers multi-char
            # seeds like "002"/"mm1") so nothing is ever cut by the canvas
            # edge. Upstream Go clamps assuming a single char, which lets
            # wide glyphs overflow the right edge.
            x = int(min(max(xx, dy), max(width - dy - (padding * 2) - c_width, dy)))
            y = int(min(max(yy, c_height + dy), height + (c_height // 2) - (padding * 2)))

            dot = Dot(
                index=i,
                x=x,
                y=y - c_height,
                size=rand_size,
                width=c_width,
                height=c_height,
                angle=rand_angle,
                color=rand_color,
                color2=rand_color2,
            )
            if self.mode == MODE_SHAPE:
                dot.shape = value
            else:
                dot.text = value
            dots[i] = dot
        return dots

    def _range_check_dots(self, dots: dict[int, Dot]) -> tuple[dict[int, Dot], list[str]]:
        """Pick the random verification subset. Mirrors rangeCheckDots."""
        rs = perm(len(dots))
        chk_dots: dict[int, Dot] = {}
        count = rand_int_fast(self.opts.range_verify_len.min, self.opts.range_verify_len.max)
        if self.opts.disabled_range_verify_len:
            count = len(rs)
        values: list[str] = []

        for i, value in enumerate(rs):
            if not self.opts.disabled_range_verify_len and i >= count:
                break
            dot = dots[value]
            dot.index = i
            chk_dots[i] = dot
            values.append(dot.shape if self.mode == MODE_SHAPE else dot.text)
        return chk_dots, values

    def _gen_master_image(self, size: Size, dots: dict[int, Dot]) -> Image.Image:
        draw_dots: list[DrawDot] = []
        background = rand_image(self.resources.backgrounds)
        for i in range(len(dots)):
            dot = dots[i]
            draw_dot = DrawDot(
                dot=dot,
                x=dot.x,
                y=dot.y,
                width=dot.width,
                height=dot.height,
                angle=dot.angle,
                color=self._ensure_contrast(dot.color, dot, background),
                size=dot.size,
                font_dpi=self.opts.font_dpi,
            )
            if self.mode == MODE_SHAPE:
                draw_dot.draw_type = DRAW_TYPE_IMAGE
                draw_dot.image = self.resources.shape_maps.get(dot.shape)
                draw_dot.use_original_color = self.opts.use_shape_original_color
            else:
                draw_dot.draw_type = DRAW_TYPE_STRING
                draw_dot.text = dot.text
                fonts = self.resources.fonts
                draw_dot.font = fonts[rand_index(len(fonts))] if fonts else None
            draw_dots.append(draw_dot)

        return self._draw.draw_with_nrgba(
            DrawImageParams(
                width=size.width,
                height=size.height,
                background=background,
                alpha=self.opts.image_alpha,
                captcha_draw_dots=draw_dots,
                show_shadow=self.opts.display_shadow,
                shadow_color=self.opts.shadow_color,
                shadow_point=(self.opts.shadow_point.x, self.opts.shadow_point.y),
            )
        )

    def _ensure_contrast(
        self,
        color: str,
        dot: Dot,
        background: Image.Image | None,
        min_contrast: float = 60.0,
    ) -> str:
        """Re-pick the dot color when it blends into the underlying background.

        The upstream Go lib can drop light glyphs on light photos; measuring
        the luminance delta at the dot position keeps every character legible.
        """
        if background is None or not color:
            return color
        fg = parse_hex_color(color)
        if fg is None:
            return color
        fg_lum = 0.299 * fg[0] + 0.587 * fg[1] + 0.114 * fg[2]

        bg_gray = background.convert("L")
        box = (
            max(0, dot.x),
            max(0, dot.y),
            min(background.size[0], dot.x + max(dot.width, 8)),
            min(background.size[1], dot.y + max(dot.height, 8)),
        )
        if box[2] <= box[0] or box[3] <= box[1]:
            return color
        region = bg_gray.crop(box)
        histogram = region.histogram()
        total = sum(histogram) or 1
        mean = sum(i * n for i, n in enumerate(histogram)) / total
        if abs(fg_lum - mean) >= min_contrast:
            return color

        # pick the palette color with the strongest contrast against this spot;
        # fall back to black/white which always maximizes the luminance delta
        best, best_delta = color, abs(fg_lum - mean)
        for cand in (*self.opts.range_colors, "#ffffff", "#000000"):
            c = parse_hex_color(cand)
            if c is None:
                continue
            lum = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
            if abs(lum - mean) > best_delta:
                best, best_delta = cand, abs(lum - mean)
        return best

    def _gen_thumb_image(self, size: Size, dots: dict[int, Dot]) -> Image.Image:
        draw_dots: list[DrawDot] = []
        width = size.width // max(len(dots), 1)
        import random as _random

        for i in range(len(dots)):
            dot = dots[i]
            length = 1
            if self.mode == MODE_TEXT:
                length = len(dot.text)

            dx = int(max(width * i + width // max(dot.width, 1), 8))
            dy = size.height // 2 + dot.size // 2 - _random.randint(0, max(size.height // 16 * length, 1))

            draw_dot = DrawDot(
                dot=dot,
                x=dx,
                y=dy,
                angle=dot.angle,
                color=dot.color2,
                size=dot.size,
                width=dot.width,
                height=dot.height,
                font_dpi=self.opts.font_dpi,
            )
            if self.mode == MODE_SHAPE:
                draw_dot.draw_type = DRAW_TYPE_IMAGE
                draw_dot.image = self.resources.shape_maps.get(dot.shape)
                draw_dot.use_original_color = self.opts.use_shape_original_color
            else:
                draw_dot.draw_type = DRAW_TYPE_STRING
                draw_dot.text = dot.text
                fonts = self.resources.fonts
                draw_dot.font = fonts[rand_index(len(fonts))] if fonts else None
            draw_dots.append(draw_dot)

        params = DrawImageParams(
            width=size.width,
            height=size.height,
            captcha_draw_dots=draw_dots,
            background_distort=self._rand_distort_with_level(self.opts.thumb_bg_distort),
            background_circles_num=self.opts.thumb_bg_circles_num,
            background_slim_line_num=self.opts.thumb_bg_slim_line_num,
            thumb_disturb_alpha=self.opts.thumb_disturb_alpha,
        )

        if self.resources.thumb_backgrounds:
            params.background = rand_image(self.resources.thumb_backgrounds)

        m_text_colors = [parse_hex_color(c) or (0, 0, 0, 255) for c in self.opts.range_thumb_colors]
        bg_colors = [parse_hex_color(c) or (255, 255, 255, 255) for c in self.opts.range_thumb_bg_colors]

        if self.opts.use_shape_original_color or self.opts.is_thumb_non_deform_ability:
            return self._draw.draw_with_nrgba2(params, m_text_colors, bg_colors)
        return self._draw.draw_with_palette(params, m_text_colors, bg_colors)

    # ------------------------------------------------------------------

    def _check(self) -> None:
        if self.mode == MODE_TEXT:
            if len(self.resources.chars) < self.opts.range_len.max:
                raise CaptchaError(CHAR_RANGE_LEN_ERR)
            if not self.resources.backgrounds:
                raise CaptchaError(EMPTY_BACKGROUND_IMAGE_ERR)
            return
        if self.mode == MODE_SHAPE:
            if len(self.resources.shapes) < self.opts.range_len.max:
                raise CaptchaError(SHAPES_RANGE_LEN_ERR)
            for img in self.resources.shape_maps.values():
                if img is None:
                    raise CaptchaError(SHAPES_TYPE_ERR)
            if not self.resources.backgrounds:
                raise CaptchaError(EMPTY_BACKGROUND_IMAGE_ERR)
            return
        raise CaptchaError(EMPTY_BACKGROUND_IMAGE_ERR)

    def _rand_distort_with_level(self, level: int) -> int:
        if level == 1:
            return rand_int_fast(240, 320)
        elif level == 2:
            return rand_int_fast(180, 240)
        elif level == 3:
            return rand_int_fast(120, 180)
        elif level == 4:
            return rand_int_fast(100, 160)
        elif level == 5:
            return rand_int_fast(80, 140)
        return 0

    def _rand_angle(self) -> int:
        angles = self.opts.range_angle_pos
        index = rand_index(len(angles))
        if index < 0:
            return 0
        angle = angles[index]
        return rand_int_fast(angle.min, angle.max)
