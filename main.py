#!/usr/bin/env python3
"""Generate an exciting night rocket-launch image as a 1024x1024 PNG.

Standard library only. The image is drawn into an RGB buffer with
row-span fills and simple disc/gradient helpers, then encoded by hand
with zlib + struct (filter-0 scanlines). Fully deterministic: every run
produces identical bytes.
"""

import os
import struct
import zlib

W = 1024
H = 1024


# ---------------------------------------------------------------------------
# Deterministic pseudo-random numbers (fixed-seed LCG, no time/random use)
# ---------------------------------------------------------------------------
class Rng:
    def __init__(self, seed):
        self.s = seed

    def next(self, n):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s % n


# ---------------------------------------------------------------------------
# Pixel buffer and drawing helpers
# ---------------------------------------------------------------------------
buf = bytearray(W * H * 3)


def span(y, x0, x1, color):
    """Fill one horizontal run on row y with an RGB color tuple."""
    if y < 0 or y >= H:
        return
    if x0 < 0:
        x0 = 0
    if x1 >= W:
        x1 = W - 1
    if x1 < x0:
        return
    n = x1 - x0 + 1
    off = (y * W + x0) * 3
    buf[off:off + n * 3] = bytes(color) * n


def rect(x0, y0, x1, y1, color):
    for y in range(max(0, y0), min(H, y1 + 1)):
        span(y, x0, x1, color)


def disc(cx, cy, r, color):
    """Filled circle via row spans."""
    for y in range(cy - r, cy + r + 1):
        dy = y - cy
        dx = int((r * r - dy * dy) ** 0.5)
        span(y, cx - dx, cx + dx, color)


def lerp(a, b, t):
    return a + int((b - a) * t)


def blend(c1, c2, t):
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


# ---------------------------------------------------------------------------
# Scene: night rocket launch
# ---------------------------------------------------------------------------
def draw_sky():
    top = (6, 10, 38)
    mid = (24, 24, 72)
    low = (96, 46, 58)
    for y in range(H):
        if y < 560:
            t = y / 560.0
            c = blend(top, mid, t)
        else:
            t = (y - 560) / 464.0
            c = blend(mid, low, t)
        span(y, 0, W - 1, c)


def draw_stars(rng):
    for _ in range(260):
        x = rng.next(W)
        y = rng.next(620)
        b = 150 + rng.next(106)
        warm = rng.next(3) == 0
        c = (b, b, b - 30) if warm else (b - 25, b - 20, b)
        span(y, x, x, c)
        if rng.next(4) == 0:
            span(y, x + 1, x + 1, c)
            span(y + 1, x, x, c)


def draw_meteors():
    # Two shooting stars streaking across the upper sky.
    for x0, y0, length in ((180, 120, 90), (640, 90, 70)):
        for i in range(length):
            x = x0 + i
            y = y0 + i // 2
            fade = 255 - int(200 * i / length)
            span(y, x, x, (fade, fade, 240))
        disc(x0, y0, 3, (255, 255, 255))


def draw_moon():
    disc(838, 138, 58, (238, 232, 205))
    disc(838, 138, 50, (248, 244, 224))
    disc(822, 126, 9, (216, 208, 182))
    disc(856, 152, 12, (220, 212, 186))
    disc(846, 118, 6, (222, 214, 188))


def draw_launch_glow():
    # Warm halo behind the flame column, biggest first. Colours are
    # kept close together so it reads as a soft halo, not rings.
    for r, c in ((250, (58, 30, 26)), (200, (86, 42, 28)),
                 (150, (118, 56, 30)), (105, (150, 72, 32))):
        disc(512, 690, r, c)


def draw_city(rng):
    # Dark skyline silhouette with lit windows.
    rect(0, 800, W - 1, H - 1, (8, 10, 22))
    x = -20
    while x < W:
        bw = 60 + rng.next(90)
        bh = 60 + rng.next(170)
        top = 800 - bh
        rect(x, top, x + bw, 800, (12, 14, 30))
        # Antenna on some buildings.
        if rng.next(3) == 0:
            rect(x + bw // 2 - 1, top - 26, x + bw // 2 + 1, top, (12, 14, 30))
            span(top - 28, x + bw // 2, x + bw // 2, (255, 90, 90))
        # Windows.
        for wy in range(top + 14, 792, 22):
            for wx in range(x + 10, x + bw - 8, 18):
                if rng.next(3) == 0:
                    warm = (255, 196, 90) if rng.next(4) else (150, 210, 255)
                    span(wy, wx, wx + 3, warm)
                    span(wy + 1, wx, wx + 3, warm)
        x += bw + 8


def draw_smoke(rng):
    # Billowing smoke around the launch pad, drawn before the rocket
    # so the rocket and flame sit on top of it.
    puffs = [(360, 760, 95), (430, 800, 120), (590, 800, 120),
             (660, 760, 95), (300, 820, 110), (720, 820, 110),
             (470, 830, 130), (550, 830, 130)]
    for cx, cy, r in puffs:
        disc(cx, cy, r, (150, 148, 152))
        disc(cx - 18, cy - 22, r - 34, (178, 176, 180))
    # A few bright lit puffs near the flame.
    for cx, cy, r in ((430, 700, 70), (594, 700, 70)):
        disc(cx, cy, r, (214, 150, 96))


def draw_rocket():
    cx = 512
    # Fins.
    rect(438, 560, 462, 640, (200, 60, 40))
    rect(562, 560, 586, 640, (200, 60, 40))
    # Body with a light centre stripe and shaded edges.
    rect(466, 330, 478, 620, (196, 200, 208))
    rect(479, 330, 545, 620, (242, 244, 248))
    rect(546, 330, 558, 620, (196, 200, 208))
    # Nose cone.
    for y in range(268, 330):
        t = (y - 268) / 62.0
        half = int(46 * t)
        span(y, cx - half, cx + half, (232, 60, 44))
    # Nose tip.
    disc(cx, 270, 6, (240, 90, 60))
    # Window.
    disc(cx, 420, 22, (40, 60, 90))
    disc(cx, 420, 16, (120, 200, 235))
    disc(cx - 5, 415, 5, (210, 240, 255))
    # Orange band near the base.
    rect(466, 540, 558, 566, (235, 110, 40))
    rect(466, 566, 558, 572, (180, 70, 30))
    # Base plate.
    rect(460, 620, 564, 632, (120, 122, 130))


def draw_flame():
    # Teardrop flame: outer orange, middle yellow, white-hot core.
    # Width is widest just under the rocket and tapers to a point.
    def width_at(y):
        # y runs 632..880: swell quickly just under the rocket, then
        # taper with a rounded curve to a soft point.
        if y < 680:
            return 36 + int((y - 632) * 1.3)
        t = min((y - 680) / 200.0, 1.0)
        return int(98 * (1.0 - t) ** 0.7 + 3)

    for y in range(632, 884):
        w = width_at(y)
        span(y, 512 - w, 512 + w, (235, 110, 20))
    for y in range(632, 856):
        w = int(width_at(y) * 0.68)
        span(y, 512 - w, 512 + w, (252, 190, 44))
    for y in range(632, 822):
        w = int(width_at(y) * 0.42)
        span(y, 512 - w, 512 + w, (255, 246, 196))


def draw_foreground_smoke(rng):
    # A few wisps drifting in front of the flame base.
    for cx, cy, r in ((380, 700, 46), (650, 720, 52), (330, 780, 60),
                      (700, 790, 58)):
        disc(cx, cy, r, (168, 166, 170))
        disc(cx - 10, cy - 12, r - 18, (196, 194, 198))


def draw_scene():
    rng = Rng(20261116)
    draw_sky()
    draw_stars(rng)
    draw_meteors()
    draw_moon()
    draw_launch_glow()
    draw_city(rng)
    draw_smoke(rng)
    draw_rocket()
    draw_flame()
    draw_foreground_smoke(rng)


# ---------------------------------------------------------------------------
# PNG encoding (filter-0 scanlines, zlib, CRC32)
# ---------------------------------------------------------------------------
def png_chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def encode_png(path):
    raw = bytearray()
    row_bytes = W * 3
    for y in range(H):
        raw.append(0)  # filter type 0 (None)
        raw += buf[y * row_bytes:(y + 1) * row_bytes]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", ihdr)
    png += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += png_chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    draw_scene()
    size = encode_png(os.path.join(out_dir, "entry.png"))
    print("wrote entry.png: %d bytes" % size)


if __name__ == "__main__":
    main()
