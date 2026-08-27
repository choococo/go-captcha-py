"""FastAPI example server for go-captcha-py.

Demonstrates integrating the library into a real backend:
- GET  /captcha/click       → {captcha_id, image_base64, thumb_base64}
- POST /captcha/click/verify
- GET  /captcha/slide       → {captcha_id, image_base64, tile_base64, tile_x, tile_y}
- POST /captcha/slide/verify
- GET  /captcha/rotate      → {captcha_id, image_base64, thumb_base64}
- POST /captcha/rotate/verify

Run:
    uv run --extra fastapi uvicorn examples.fastapi_server:app --port 9000 --reload

The generation/validation logic below is framework-agnostic — in your own
project just `from go_captcha_py import click, slide, rotate, store`.
"""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from go_captcha_py import click, rotate, slide, store

# Debug mode exposes the answer in generation responses for automated E2E
# tests only. NEVER enable in production.
DEBUG = os.environ.get("GOCAPTCHA_DEBUG") == "1"

app = FastAPI(title="go-captcha-py example server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# one captcha instance each; generation is cheap and thread-safe
click_text_capt = click.make_default_text_captcha()
click_shape_capt = click.make_default_shape_captcha()
slide_capt = slide.make_default_captcha()
drag_capt = slide.make_default_drag_drop_captcha()
rotate_capt = rotate.make_default_captcha()

# pending answers keyed by captcha id; swap for a Redis-backed Store in prod
mem_store = store.MemoryStore(ttl=600)

CLICK_PADDING = 5  # px tolerance around each dot
SLIDE_PADDING = 3  # px tolerance around the notch
ROTATE_PADDING = 6  # degree tolerance


# ---------------------------------------------------------------------------
# Click
# ---------------------------------------------------------------------------


@app.get("/captcha/click")
def get_click_captcha(shape: bool = False) -> dict:
    """Generate a click captcha (text or shape mode)."""
    capt = click_shape_capt if shape else click_text_capt
    data = capt.generate()

    captcha_id = store.gen_key()
    mem_store.set(captcha_id, data.get_data())

    resp = {
        "captcha_id": captcha_id,
        "image_base64": data.get_master_image().to_base64(),
        "thumb_base64": data.get_thumb_image().to_base64(),
    }
    if DEBUG:
        resp["answer"] = [
            {"x": d.x + d.width // 2, "y": d.y + d.height // 2} for d in data.get_data().values()
        ]
    return resp


@app.post("/captcha/click/verify")
def verify_click_captcha(
    dots: Annotated[str, Form()],
    captcha_id: Annotated[str, Form()],
) -> dict:
    """Verify clicked dots. `dots` format: 'x1,y1;x2,y2;...' (px, image coords)."""
    answer = mem_store.pop(captcha_id)
    if answer is None:
        raise HTTPException(status_code=403, detail="captcha expired or not found")

    try:
        points = [(int(p.split(",")[0]), int(p.split(",")[1])) for p in dots.split(";") if p.strip()]
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="invalid dots format") from None

    if len(points) != len(answer):
        return {"code": 1, "message": "wrong number of dots", "captcha_verified": False}

    for i, (sx, sy) in enumerate(points):
        dot = answer[i]
        if not click.validate(sx, sy, dot.x, dot.y, dot.width, dot.height, CLICK_PADDING):
            return {"code": 1, "message": "verification failed", "captcha_verified": False}

    return {"code": 0, "message": "ok", "captcha_verified": True}


# ---------------------------------------------------------------------------
# Slide / drag-drop
# ---------------------------------------------------------------------------


@app.get("/captcha/slide")
def get_slide_captcha(drag: bool = False) -> dict:
    """Generate a slide captcha (basic or drag-drop mode)."""
    capt = drag_capt if drag else slide_capt
    data = capt.generate()

    captcha_id = store.gen_key()
    mem_store.set(captcha_id, data.get_data())

    block = data.get_data()
    resp = {
        "captcha_id": captcha_id,
        "image_base64": data.get_master_image().to_base64(),
        "tile_base64": data.get_tile_image().to_base64(),
        # tile start position (client offsets from here)
        "tile_x": block.dx,
        "tile_y": block.dy,
    }
    if DEBUG:
        resp["answer"] = {"x": block.x, "y": block.y}
    return resp


@app.post("/captcha/slide/verify")
def verify_slide_captcha(
    point: Annotated[str, Form()],
    captcha_id: Annotated[str, Form()],
) -> dict:
    """Verify slide position. `point` format: 'x,y' (tile top-left, image coords)."""
    block = mem_store.pop(captcha_id)
    if block is None:
        raise HTTPException(status_code=403, detail="captcha expired or not found")

    try:
        sx_s, sy_s = point.split(",")
        sx, sy = int(sx_s), int(sy_s)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid point format") from None

    ok = slide.validate(sx, sy, block.x, block.y, SLIDE_PADDING)
    return {
        "code": 0 if ok else 1,
        "message": "ok" if ok else "verification failed",
        "captcha_verified": ok,
    }


# ---------------------------------------------------------------------------
# Rotate
# ---------------------------------------------------------------------------


@app.get("/captcha/rotate")
def get_rotate_captcha() -> dict:
    """Generate a rotate captcha."""
    data = rotate_capt.generate()

    captcha_id = store.gen_key()
    mem_store.set(captcha_id, data.get_data())

    resp = {
        "captcha_id": captcha_id,
        "image_base64": data.get_master_image().to_base64(),
        "thumb_base64": data.get_thumb_image().to_base64(),
        # sizes the frontend needs for correct centering:
        # config.size = master square size, data.thumbSize = actual thumb size
        "size": data.get_data().parent_width,
        "thumb_size": data.get_data().width,
    }
    if DEBUG:
        resp["answer"] = {"angle": data.get_data().angle}
    return resp


@app.post("/captcha/rotate/verify")
def verify_rotate_captcha(
    angle: Annotated[int, Form()],
    captcha_id: Annotated[str, Form()],
) -> dict:
    """Verify rotate angle (degrees)."""
    block = mem_store.pop(captcha_id)
    if block is None:
        raise HTTPException(status_code=403, detail="captcha expired or not found")

    ok = rotate.validate(angle, block.angle, ROTATE_PADDING)
    return {
        "code": 0 if ok else 1,
        "message": "ok" if ok else "verification failed",
        "captcha_verified": ok,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
