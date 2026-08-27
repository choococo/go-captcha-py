"""Slide / drag-drop captcha module.

Usage:
    from go_captcha_py import slide

    capt = slide.make_default_captcha()
    data = capt.generate()
    block = data.get_data()                     # server-side answer (x, y ...)
    b64 = data.get_master_image().to_base64()   # send to frontend

    ok = slide.validate(sx, sy, dx, dy, padding)
"""

from .block import Block
from .builder import (
    Builder,
    make_captcha,
    make_default_captcha,
    make_default_drag_drop_captcha,
    make_drag_drop_captcha,
    new_builder,
)
from .captcha import MODE_BASIC, MODE_DRAG, Captcha, CaptchaData, CaptchaError
from .options import (
    DEAD_ZONE_DIRECTION_BOTTOM,
    DEAD_ZONE_DIRECTION_LEFT,
    DEAD_ZONE_DIRECTION_RIGHT,
    DEAD_ZONE_DIRECTION_TOP,
    GraphImage,
    Options,
    Resources,
    with_backgrounds,
    with_enable_graph_vertical_random,
    with_gen_graph_number,
    with_graph_images,
    with_image_alpha,
    with_image_size,
    with_range_dead_zone_directions,
    with_range_graph_angle_pos,
    with_range_graph_size,
)
from .validate import check_point, validate

__all__ = [
    "DEAD_ZONE_DIRECTION_BOTTOM",
    "DEAD_ZONE_DIRECTION_LEFT",
    "DEAD_ZONE_DIRECTION_RIGHT",
    "DEAD_ZONE_DIRECTION_TOP",
    "MODE_BASIC",
    "MODE_DRAG",
    "Block",
    "Builder",
    "Captcha",
    "CaptchaData",
    "CaptchaError",
    "GraphImage",
    "Options",
    "Resources",
    "check_point",
    "make_captcha",
    "make_default_captcha",
    "make_default_drag_drop_captcha",
    "make_drag_drop_captcha",
    "new_builder",
    "validate",
    "with_backgrounds",
    "with_enable_graph_vertical_random",
    "with_gen_graph_number",
    "with_graph_images",
    "with_image_alpha",
    "with_image_size",
    "with_range_dead_zone_directions",
    "with_range_graph_angle_pos",
    "with_range_graph_size",
]
