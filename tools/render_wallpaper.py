#!/usr/bin/env python3
"""Render the Homebrew "Ascension" wallpaper.

The AI-generated plate supplies atmosphere only: black void, the pale green
beam, the human silhouette, and the reflective floor. Every character of the
code rain is drawn deterministically with a real monospace font at the final
resolution, because image models render text as texture and the glyphs come
out as unreadable blobs.

Usage:
  render_wallpaper.py --plate PLATE.png --out OUT.jpg --width 3440 --height 1440
"""

from __future__ import annotations

import argparse
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_PATH = "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf"

ACCENT = (0, 255, 65)
BRIGHT = (94, 255, 176)
HEAD = (214, 255, 214)

BINARY = "01"
EXTRA = "0123456789ABCDEF{}[]()/\\<>;:.,*+-=_|"


def build_pool(rng: random.Random) -> str:
    return BINARY * 7 + EXTRA * 2


def find_geometry(plate: Image.Image) -> tuple[float, float]:
    """Return (beam_x_frac, horizon_y_frac) measured from the plate."""
    a = np.asarray(plate.convert("RGB"), dtype=np.float32).mean(axis=2)
    h, w = a.shape
    cx = int(np.argmax(a.mean(axis=0)))
    band = a[:, max(0, cx - int(0.06 * w)) : cx + int(0.06 * w)].mean(axis=1)
    hy = int(np.argmax(band))
    return cx / w, hy / h


def cover_resize(im: Image.Image, w: int, h: int) -> Image.Image:
    sw, sh = im.size
    scale = max(w / sw, h / sh)
    nw, nh = round(sw * scale), round(sh * scale)
    im = im.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return im.crop((left, top, left + w, top + h))


def center_mask(w: int, h: int, cx: int) -> np.ndarray:
    """1.0 at the beam column, falling to 0.0 across the side code fields."""
    x = np.arange(w, dtype=np.float32)
    d = np.abs(x - cx)
    inner = 0.022 * w
    outer = 0.070 * w
    t = np.clip((d - inner) / (outer - inner), 0.0, 1.0)
    fall = 0.5 * (1.0 + np.cos(np.pi * t))
    return np.repeat(fall[None, :], h, axis=0)


def screen(base: np.ndarray, layer: np.ndarray, strength: float = 1.0) -> np.ndarray:
    return 1.0 - (1.0 - base) * (1.0 - np.clip(layer * strength, 0.0, 1.0))


def render_columns(
    w: int,
    h: int,
    horizon: int,
    rng: random.Random,
    *,
    font_scale: float,
    spacing: float,
    alpha_scale: float,
    blur: float,
) -> np.ndarray:
    """Return a float RGB layer (0..1) of crisp monospace code columns."""
    font_size = max(8, int(round(h * 0.018 * font_scale)))
    font = ImageFont.truetype(FONT_PATH, font_size)
    bbox = font.getbbox("0")
    glyph_w = bbox[2] - bbox[0]
    glyph_h = font_size
    step = max(glyph_w + 2, int(round(spacing)))
    pool = build_pool(rng)

    layer = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x = -step + rng.randint(0, step)
    while x < w:
        jitter = rng.randint(-1, 1)
        if rng.random() < 0.04:
            x += step
            continue
        trail = rng.randint(18, 78)
        head_y = rng.randint(-trail * glyph_h, h + trail * glyph_h // 3)
        base_alpha = alpha_scale * rng.uniform(0.28, 1.0)
        decay = rng.uniform(9.0, 30.0)
        col_shift = rng.uniform(-0.12, 0.12)
        for i in range(trail):
            y = head_y - i * glyph_h
            if y > h or y + glyph_h < 0:
                continue
            ch = pool[rng.randrange(len(pool))]
            if i == 0:
                color, a = HEAD, base_alpha
            elif i <= 3:
                color, a = BRIGHT, base_alpha * 0.92
            else:
                color, a = ACCENT, base_alpha * float(np.exp(-(i - 3) / decay))
            if a < 0.012:
                break
            r = int(min(255, max(0, color[0] * (1 + col_shift))))
            g = int(min(255, max(0, color[1] * (1 + col_shift))))
            b = int(min(255, max(0, color[2] * (1 + col_shift))))
            draw.text((x + jitter, y), ch, font=font, fill=(int(r * a), int(g * a), int(b * a)))
        x += step

    arr = np.asarray(layer, dtype=np.float32) / 255.0
    if blur > 0:
        img = Image.fromarray((arr * 255).astype(np.uint8), "RGB")
        img = img.filter(ImageFilter.GaussianBlur(blur))
        arr = np.asarray(img, dtype=np.float32) / 255.0
    return arr


def build(plate_path: str, out_path: str, w: int, h: int, seed: int, quality: int, png_out: str | None = None) -> None:
    rng = random.Random(seed)
    plate = Image.open(plate_path).convert("RGB")
    beam_frac, horizon_frac = find_geometry(plate)
    plate = cover_resize(plate, w, h)
    cx = int(beam_frac * w)
    horizon = int(horizon_frac * h)

    base = np.asarray(plate, dtype=np.float32) / 255.0

    # Replace the model's mushy side glyphs with smooth atmosphere.
    soft = plate.filter(ImageFilter.GaussianBlur(max(2.0, w * 0.004)))
    soft_arr = np.asarray(soft, dtype=np.float32) / 255.0 * 0.22
    mask = center_mask(w, h, cx)[:, :, None]
    base = base * mask + soft_arr * (1.0 - mask)

    # Deterministic code rain in three depth layers.
    far = render_columns(w, h, horizon, rng, font_scale=0.72, spacing=w * 0.0035,
                         alpha_scale=0.42, blur=max(1.2, h * 0.0022))
    mid = render_columns(w, h, horizon, rng, font_scale=0.90, spacing=w * 0.0052,
                         alpha_scale=0.80, blur=max(0.6, h * 0.0009))
    near = render_columns(w, h, horizon, rng, font_scale=1.10, spacing=w * 0.0078,
                          alpha_scale=1.0, blur=0.0)

    code = np.clip(far + mid + near, 0.0, 1.0)

    # Rest the eye: the rain dissolves toward the top of the frame.
    env = np.clip(np.arange(h, dtype=np.float32) / (0.10 * h), 0.0, 1.0) ** 1.2
    code *= env[:, None, None]

    # Keep the beam and the figure readable: fade the code out near the center.
    code = code * (1.0 - mask)

    # Floor: mirror the code below the horizon, blurred and heavily faded.
    refl = np.zeros_like(code)
    src = code[:horizon][::-1]
    refl[horizon:] = src[: h - horizon]
    refl_img = Image.fromarray((np.clip(refl, 0, 1) * 255).astype(np.uint8), "RGB")
    refl_img = refl_img.filter(ImageFilter.GaussianBlur(max(2.0, h * 0.007)))
    refl = np.asarray(refl_img, dtype=np.float32) / 255.0 * 0.30
    fade = np.linspace(1.0, 0.0, h - horizon, dtype=np.float32) ** 1.4
    refl[horizon:] *= fade[:, None, None]

    bloom = Image.fromarray((np.clip(code, 0, 1) * 255).astype(np.uint8), "RGB")
    bloom = bloom.filter(ImageFilter.GaussianBlur(max(2.0, h * 0.006)))
    bloom = np.asarray(bloom, dtype=np.float32) / 255.0

    out = screen(base, code)
    out = screen(out, bloom, 0.42)
    out = screen(out, refl)

    # Gentle vignette, then a touch of contrast to keep the blacks deep.
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    vig = np.clip(1.0 - 0.16 * np.clip(r - 0.55, 0, None) ** 1.5, 0.0, 1.0)
    out *= vig[:, :, None]
    out = np.clip((out - 0.5) * 1.06 + 0.5, 0.0, 1.0)

    Image.fromarray((out * 255).astype(np.uint8), "RGB").save(
        out_path, "JPEG", quality=quality, progressive=True, subsampling=0, optimize=True
    )
    if png_out:
        Image.fromarray((out * 255).astype(np.uint8), "RGB").save(png_out, "PNG", optimize=True)
    print(f"{out_path} {w}x{h} beam_x={cx} horizon={horizon}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plate", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument("--seed", type=int, default=20260909)
    ap.add_argument("--quality", type=int, default=93)
    ap.add_argument("--png-out", default=None, help="also write the render as a lossless PNG")
    a = ap.parse_args()
    build(a.plate, a.out, a.width, a.height, a.seed, a.quality, a.png_out)


if __name__ == "__main__":
    main()
