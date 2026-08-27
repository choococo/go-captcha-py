"""Click captcha module — text and shape (graphic) click modes.

Usage:
    from go_captcha_py import click

    capt = click.make_default_text_captcha()
    data = capt.generate()
    dots = data.get_data()                      # server-side answer
    b64 = data.get_master_image().to_base64()   # send to frontend

    ok = click.validate(sx, sy, dx, dy, w, h, padding)
"""

from .builder import (
    Builder,
    make_default_shape_captcha,
    make_default_text_captcha,
    make_shape_captcha,
    make_text_captcha,
    new_builder,
)
from .captcha import MODE_SHAPE, MODE_TEXT, Captcha, CaptchaData, CaptchaError
from .dot import Dot, DrawDot
from .options import (
    Options,
    Resources,
    with_backgrounds,
    with_chars,
    with_disabled_range_verify_len,
    with_display_shadow,
    with_fonts,
    with_image_alpha,
    with_image_size,
    with_is_thumb_non_deform_ability,
    with_range_angle_pos,
    with_range_colors,
    with_range_len,
    with_range_size,
    with_range_thumb_bg_colors,
    with_range_thumb_colors,
    with_range_thumb_size,
    with_range_verify_len,
    with_shadow_color,
    with_shadow_point,
    with_shapes,
    with_thumb_backgrounds,
    with_thumb_bg_circles_num,
    with_thumb_bg_distort,
    with_thumb_bg_slim_line_num,
    with_thumb_image_size,
    with_use_shape_original_color,
)
from .validate import check_point, validate

__all__ = [
    "MODE_SHAPE",
    "MODE_TEXT",
    "Builder",
    "Captcha",
    "CaptchaData",
    "CaptchaError",
    "Dot",
    "DrawDot",
    "Options",
    "Resources",
    "check_point",
    "make_default_shape_captcha",
    "make_default_text_captcha",
    "make_shape_captcha",
    "make_text_captcha",
    "new_builder",
    "validate",
    "with_backgrounds",
    "with_chars",
    "with_disabled_range_verify_len",
    "with_display_shadow",
    "with_fonts",
    "with_image_alpha",
    "with_image_size",
    "with_is_thumb_non_deform_ability",
    "with_range_angle_pos",
    "with_range_colors",
    "with_range_len",
    "with_range_size",
    "with_range_thumb_bg_colors",
    "with_range_thumb_colors",
    "with_range_thumb_size",
    "with_range_verify_len",
    "with_shadow_color",
    "with_shadow_point",
    "with_shapes",
    "with_thumb_backgrounds",
    "with_thumb_bg_circles_num",
    "with_thumb_bg_distort",
    "with_thumb_bg_slim_line_num",
    "with_thumb_image_size",
    "with_use_shape_original_color",
]
