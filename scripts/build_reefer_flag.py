#!/usr/bin/env python3
"""Turn the site logo into a flying flag (assets/the-reefer/flag-900.webp).

The logo already sits on black, so it is the flag: this script ripples the cloth, shades the
folds, frays the fly edge and leaves the rest transparent. The home page hero flies it from
the mast of the ship drawn in build_national.py. Re-run after the logo changes.

Usage: python3 scripts/build_reefer_flag.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'assets/the-reefer/logo-960.jpg'
OUT = ROOT / 'assets/the-reefer/flag-900.webp'
W, H, PAD = 900, 600, 70  # cloth size and the room above and below for the ripple


def main():
    logo = np.asarray(Image.open(SRC).convert('RGB').resize((W, H), Image.LANCZOS), dtype=np.float32)
    rng = np.random.default_rng(420)
    out_h = H + 2 * PAD
    ys, xs = np.mgrid[0:out_h, 0:W].astype(np.float32)
    u = xs / W  # 0 at the hoist (mast side), 1 at the fly
    phase = u * 2 * np.pi * 1.55 + 0.4 + (ys / out_h) * 0.9
    amp = PAD * 0.78 * (0.12 + 0.88 * u)  # the hoist is tied down; the fly moves most
    lift = amp * np.sin(phase) - 14 * u * u  # the fly end sags a little
    sy = ys - PAD - lift
    # Cloth pulled across a ripple looks narrower where it turns away from the viewer.
    squeeze = 1 + 0.035 * np.cos(phase) * u
    sx = np.clip(xs * squeeze, 0, W - 1)
    inside = (sy >= 0) & (sy <= H - 1)
    syc = np.clip(sy, 0, H - 1)
    x0, y0 = sx.astype(np.int32), syc.astype(np.int32)
    x1, y1 = np.minimum(x0 + 1, W - 1), np.minimum(y0 + 1, H - 1)
    fx, fy = (sx - x0)[..., None], (syc - y0)[..., None]
    img = (logo[y0, x0] * (1 - fx) * (1 - fy) + logo[y0, x1] * fx * (1 - fy)
           + logo[y1, x0] * (1 - fx) * fy + logo[y1, x1] * fx * fy)
    # Light from the upper left: slopes facing it brighten, the far side of each fold darkens.
    slope = np.cos(phase) * (0.12 + 0.88 * u)
    shade = 1.0 + 0.42 * slope
    sheen = np.clip(slope, 0, 1) ** 2 * 46  # a little moonlight on the black cloth
    img = np.clip(img * shade[..., None] + sheen[..., None] * np.array([0.75, 0.9, 1.0]), 0, 255)
    # Frayed fly edge: notches and a few tears, deeper toward the corners.
    v = np.clip(sy / H, 0, 1)
    row = np.arange(out_h)
    ragged = (np.interp(row, np.linspace(0, out_h, 34), rng.uniform(0, 1, 34))
              + 0.5 * np.interp(row, np.linspace(0, out_h, 120), rng.uniform(0, 1, 120)))
    edge = W - 6 - 22 * ragged[:, None] - 26 * (np.abs(v - 0.5) * 2) ** 3
    alpha = inside & (xs < edge)
    for cy, depth, width in ((0.22, 70, 7), (0.61, 95, 9), (0.83, 55, 6)):  # tears in from the fly
        tear = (np.abs(v - cy) * H < width * (xs - (W - depth)) / depth) & (xs > W - depth)
        alpha &= ~tear
    a = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    flag = Image.fromarray(img.astype(np.uint8)).convert('RGBA')
    flag.putalpha(a)
    flag.save(OUT, 'WEBP', quality=84, method=6)
    print(f'Built {OUT.relative_to(ROOT)}: {flag.size[0]}x{flag.size[1]}, {OUT.stat().st_size // 1024} KB')


if __name__ == '__main__':
    main()
