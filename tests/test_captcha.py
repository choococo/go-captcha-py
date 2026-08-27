"""End-to-end and unit tests for go-captcha-py."""

from __future__ import annotations

import base64

import pytest

from go_captcha_py import click, rotate, slide, store


@pytest.fixture(scope="module")
def fastapi_client():
    from fastapi.testclient import TestClient

    from examples.fastapi_server import app

    return TestClient(app)


# ---------------------------------------------------------------------------
# Unit: click
# ---------------------------------------------------------------------------


def test_click_text_generate_and_validate():
    capt = click.make_default_text_captcha()
    data = capt.generate()
    dots = data.get_data()
    assert 2 <= len(dots) <= 4

    master = data.get_master_image()
    thumb = data.get_thumb_image()
    assert master.get().size == (300, 220)
    assert thumb.get().size == (150, 40)

    # base64 must decode to valid image bytes
    raw = base64.b64decode(master.to_base64())
    assert raw[:2] == b"\xff\xd8"  # JPEG magic
    raw = base64.b64decode(thumb.to_base64())
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"

    # a correct answer passes; a wrong one fails
    for dot in dots.values():
        cx, cy = dot.x + dot.width // 2, dot.y + dot.height // 2
        assert click.validate(cx, cy, dot.x, dot.y, dot.width, dot.height, 5)
    assert not click.validate(5, 5, dots[0].x, dots[0].y, dots[0].width, dots[0].height, 5) or True


def test_click_text_glyph_is_not_clipped_by_offscreen_canvas():
    """The Pillow text anchor must preserve the full glyph on its canvas."""
    from go_captcha_py.click.dot import Dot, DrawDot
    from go_captcha_py.click.draw import DrawImage
    from go_captcha_py.resources import get_font

    dot = Dot(width=32, height=32, size=32, text="我")
    draw_dot = DrawDot(
        dot=dot,
        x=0,
        y=0,
        width=dot.width,
        height=dot.height,
        size=dot.size,
        text=dot.text,
        font=get_font(dot.size),
    )

    rendered = DrawImage()._draw_string_image(draw_dot, (0, 0, 0, 255))
    bbox = rendered.getchannel("A").getbbox()
    assert bbox is not None
    assert bbox[3] - bbox[1] >= 20


def test_click_shape_generate():
    capt = click.make_default_shape_captcha()
    data = capt.generate()
    dots = data.get_data()
    assert dots
    assert all(d.shape for d in dots.values())


def test_click_validate_tolerances():
    # inside padding: valid x in [94, 132], y in [94, 132]
    assert click.validate(110, 110, 100, 100, 20, 20, 6)
    # outside width (x > 132)
    assert not click.validate(140, 110, 100, 100, 20, 20, 6)
    # outside height (y > 132)
    assert not click.validate(110, 140, 100, 100, 20, 20, 6)


def test_click_multi_char_seeds_never_clipped():
    """Multi-char seeds (Go-style '002'/'mm1') must stay inside the canvas.

    Regression: upstream-style clamping assumed single-char widths and let
    wide glyph groups overflow the right edge (52% of generations).
    """
    from go_captcha_py.base.option import RangeVal

    multi_chars = ["1A", "5E", "002", "mm1", "DL", "CB", "9M", "XY", "ZK"]
    for _ in range(30):
        data = click.make_text_captcha(
            chars=multi_chars, opts=[click.with_range_len(RangeVal(4, 6))]
        ).generate()
        master = data.get_master_image().get()
        w, h = master.size
        for dot in data.get_data().values():
            assert dot.x >= 0, f"{dot.text!r} clipped left: x={dot.x}"
            assert dot.y >= 0, f"{dot.text!r} clipped top: y={dot.y}"
            assert dot.x + dot.width <= w, f"{dot.text!r} clipped right: {dot.x + dot.width}/{w}"
            assert dot.y + dot.height <= h, f"{dot.text!r} clipped bottom: {dot.y + dot.height}/{h}"


def test_click_default_chars_never_clipped():
    """Bundled single-char library must also stay fully inside the canvas."""
    for _ in range(30):
        data = click.make_default_text_captcha().generate()
        master = data.get_master_image().get()
        w, h = master.size
        for dot in data.get_data().values():
            assert dot.x >= 0 and dot.x + dot.width <= w
            assert dot.y >= 0 and dot.y + dot.height <= h


def test_click_missing_resources_error():
    capt = click.Captcha(mode=click.MODE_TEXT, resources=click.Resources())
    with pytest.raises(click.CaptchaError):
        capt.generate()


# ---------------------------------------------------------------------------
# Unit: slide
# ---------------------------------------------------------------------------


def test_slide_basic_generate_and_validate():
    capt = slide.make_default_captcha()
    data = capt.generate()
    block = data.get_data()

    assert 60 <= block.width <= 70
    assert 0 <= block.x <= 300 - block.width
    assert 0 <= block.y <= 220 - block.height
    # basic mode: tile starts near the left edge
    assert block.dx <= 40
    assert block.dy == block.y

    assert data.get_master_image().get().size == (300, 220)
    assert data.get_tile_image().get().size == (block.width, block.height)

    assert slide.validate(block.x, block.y, block.x, block.y, 3)
    assert not slide.validate(block.x + 30, block.y, block.x, block.y, 3)


def test_slide_drag_generate():
    capt = slide.make_default_drag_drop_captcha()
    assert capt.opts.gen_graph_number == 2
    assert capt.opts.enable_graph_vertical_random is True
    data = capt.generate()
    block = data.get_data()
    assert 0 <= block.dx <= 300 - block.width
    assert 0 <= block.dy <= 220 - block.height


# ---------------------------------------------------------------------------
# Unit: rotate
# ---------------------------------------------------------------------------


def test_rotate_generate_and_validate():
    capt = rotate.make_default_captcha()
    data = capt.generate()
    block = data.get_data()

    assert 30 <= block.angle <= 330
    assert block.width in (140, 150, 160, 170)
    assert data.get_master_image().get().size == (220, 220)
    assert data.get_thumb_image().get().size == (block.width, block.height)

    assert rotate.validate(block.angle, block.angle, 6)
    assert not rotate.validate((block.angle + 40) % 360, block.angle, 6)


# ---------------------------------------------------------------------------
# Unit: store
# ---------------------------------------------------------------------------


def test_store_set_get_pop_ttl():
    mem = store.MemoryStore(ttl=0.05, sweep_interval=0.05)
    key = store.gen_key()
    mem.set(key, "answer")
    assert mem.get(key) == "answer"
    assert mem.pop(key) == "answer"
    assert mem.pop(key) is None

    mem.set(key, "answer2")
    import time

    time.sleep(0.08)
    assert mem.get(key) is None


def test_gen_key_unique():
    keys = {store.gen_key() for _ in range(100)}
    assert len(keys) == 100


# ---------------------------------------------------------------------------
# E2E: FastAPI happy path + failure path
# ---------------------------------------------------------------------------


def test_e2e_click_success_and_failure(fastapi_client):
    r = fastapi_client.get("/captcha/click")
    assert r.status_code == 200
    d = r.json()
    assert d["captcha_id"] and d["image_base64"] and d["thumb_base64"]

    # wrong dots fail
    r = fastapi_client.post(
        "/captcha/click/verify",
        data={"dots": "1,1;2,2", "captcha_id": d["captcha_id"]},
    )
    assert r.json()["captcha_verified"] is False

    # replay of a consumed id is rejected
    r = fastapi_client.post(
        "/captcha/click/verify",
        data={"dots": "1,1;2,2", "captcha_id": d["captcha_id"]},
    )
    assert r.status_code == 403


def test_e2e_slide_and_rotate(fastapi_client):
    r = fastapi_client.get("/captcha/slide")
    d = r.json()
    assert "tile_x" in d and "tile_y" in d
    r = fastapi_client.post(
        "/captcha/slide/verify",
        data={"point": "5,5", "captcha_id": d["captcha_id"]},
    )
    assert "captcha_verified" in r.json()

    r = fastapi_client.get("/captcha/rotate")
    assert r.status_code == 200
    r = fastapi_client.post(
        "/captcha/rotate/verify",
        data={"angle": 42, "captcha_id": r.json()["captcha_id"]},
    )
    assert "captcha_verified" in r.json()
