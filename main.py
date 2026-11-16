# "Bear Market, Rocket Ride" — ai-excited-01 candidate image (preview only)
#
# The joke, drawn literally: it is a Bitcoin bear market, so a big brown bear
# is asleep on his bed — and a rocket is hauling the whole bed up to the moon,
# tied on with golden ropes. The bear does not care. He is asleep.
#
# Stdlib-only Python 3.13. Deterministic: running this file twice writes
# byte-identical PNGs. 1024x1024, no network, no external assets.
#
#   python3 main.py            -> writes /output/entry.png
#   MAKEFUN_OUTPUT_DIR=out python3 main.py   -> writes out/entry.png

import math
import os
import random
import struct
import zlib

W, H = 1024, 1024
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

# ---------------------------------------------------------------- canvas
# Flat RGB bytearray canvas; all drawing goes through these helpers.

canvas = bytearray(W * H * 3)


def _idx(x, y):
    return (y * W + x) * 3


def put(x, y, r, g, b):
    """Opaque pixel, silently clipped."""
    if 0 <= x < W and 0 <= y < H:
        i = _idx(x, y)
        canvas[i] = r
        canvas[i + 1] = g
        canvas[i + 2] = b


def blend(x, y, r, g, b, a):
    """Alpha-blend a pixel (a in 0..1), silently clipped."""
    if 0 <= x < W and 0 <= y < H and a > 0:
        i = _idx(x, y)
        canvas[i] = int(canvas[i] * (1 - a) + r * a)
        canvas[i + 1] = int(canvas[i + 1] * (1 - a) + g * a)
        canvas[i + 2] = int(canvas[i + 2] * (1 - a) + b * a)


def fill_rect(x0, y0, x1, y1, col, a=1.0):
    x0, x1 = sorted((int(x0), int(x1)))
    y0, y1 = sorted((int(y0), int(y1)))
    x0 = max(x0, 0)
    y0 = max(y0, 0)
    x1 = min(x1, W - 1)
    y1 = min(y1, H - 1)
    if a >= 1.0:
        row = bytes(col) * (x1 - x0 + 1)
        for y in range(y0, y1 + 1):
            i = _idx(x0, y)
            canvas[i:i + len(row)] = row
    else:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                blend(x, y, col[0], col[1], col[2], a)


def circle(cx, cy, r, col, a=1.0):
    r = int(r)
    for y in range(int(cy) - r, int(cy) + r + 1):
        dy = y - cy
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        for x in range(int(cx) - dx, int(cx) + dx + 1):
            if a >= 1.0:
                put(x, y, col[0], col[1], col[2])
            else:
                blend(x, y, col[0], col[1], col[2], a)


def ellipse(cx, cy, rx, ry, col, a=1.0):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        t = (y - cy) / ry
        if abs(t) > 1:
            continue
        dx = int(rx * math.sqrt(1 - t * t))
        for x in range(int(cx) - dx, int(cx) + dx + 1):
            if a >= 1.0:
                put(x, y, col[0], col[1], col[2])
            else:
                blend(x, y, col[0], col[1], col[2], a)


def polygon(points, col, a=1.0):
    """Scanline-filled polygon (any simple polygon)."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    y0, y1 = int(max(0, min(ys))), int(min(H - 1, max(ys)))
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, y1p = points[i]
            x2, y2p = points[(i + 1) % n]
            if (y1p <= y < y2p) or (y2p <= y < y1p):
                t = (y - y1p) / (y2p - y1p)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa, xb = int(math.ceil(xs[k])), int(math.floor(xs[k + 1]))
            for x in range(max(0, xa), min(W - 1, xb) + 1):
                if a >= 1.0:
                    put(x, y, col[0], col[1], col[2])
                else:
                    blend(x, y, col[0], col[1], col[2], a)


def thick_line(x0, y0, x1, y1, w, col, a=1.0):
    """A line drawn by stamping discs along it (smooth, round caps)."""
    dist = math.hypot(x1 - x0, y1 - y0)
    steps = max(1, int(dist))
    r = w / 2.0
    for s in range(steps + 1):
        t = s / steps
        circle(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, col, a)


def quad_bez(p0, p1, p2, steps=40):
    """Points along a quadratic bezier curve."""
    pts = []
    for s in range(steps + 1):
        t = s / steps
        mt = 1 - t
        pts.append((
            mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
            mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1],
        ))
    return pts


def rope(p0, p1, w, col, sag=26):
    """A slightly sagging golden rope: thick bezier with a darker edge line."""
    mx = (p0[0] + p1[0]) / 2
    my = (p0[1] + p1[1]) / 2 + sag
    pts = quad_bez(p0, (mx, my), p1)
    for i in range(len(pts) - 1):
        thick_line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                   w, col)
    # bright highlight thread along the middle of the rope
    for i in range(len(pts) - 1):
        thick_line(pts[i][0] - 1.5, pts[i][1] - 1.5,
                   pts[i + 1][0] - 1.5, pts[i + 1][1] - 1.5,
                   max(1.5, w * 0.28), (255, 232, 150))


def rounded_rect(x0, y0, x1, y1, r, col, a=1.0):
    fill_rect(x0 + r, y0, x1 - r, y1, col, a)
    fill_rect(x0, y0 + r, x1, y1 - r, col, a)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                   (x0 + r, y1 - r), (x1 - r, y1 - r)):
        circle(cx, cy, r, col, a)


def rot(px, py, ang, cx, cy):
    """Rotate point (px,py) by ang radians around (cx,cy)."""
    c, s = math.cos(ang), math.sin(ang)
    dx, dy = px - cx, py - cy
    return (cx + dx * c - dy * s, cy + dx * s + dy * c)


# ---------------------------------------------------------------- palette
INK = (12, 14, 40)
SKY_TOP = (9, 12, 46)
SKY_MID = (26, 22, 74)
SKY_LOW = (64, 32, 96)
MOON = (250, 244, 214)
MOON_HALO = (250, 244, 214)
GOLD = (232, 178, 44)
GOLD_DARK = (176, 124, 22)
GOLD_LIGHT = (255, 222, 120)
ROCKET_WHITE = (240, 242, 246)
ROCKET_RED = (224, 62, 48)
ROCKET_GREY = (176, 182, 196)
FLAME_OUT = (244, 110, 32)
FLAME_MID = (250, 178, 40)
FLAME_IN = (255, 240, 170)
WOOD = (122, 74, 38)
WOOD_DARK = (88, 50, 24)
MATTRESS = (245, 242, 232)
BLANKET = (42, 128, 160)
BLANKET_DARK = (28, 92, 122)
BEAR = (138, 90, 51)
BEAR_LIGHT = (182, 128, 74)
BEAR_DARK = (96, 60, 32)
CANDLE_RED = (206, 48, 48)
CANDLE_DARK = (150, 28, 28)
ZCOL = (190, 225, 255)

# ---------------------------------------------------------------- sky
def draw_sky(rng):
    for y in range(H):
        t = y / (H - 1)
        if t < 0.55:
            f = t / 0.55
            col = tuple(int(SKY_TOP[i] + (SKY_MID[i] - SKY_TOP[i]) * f)
                        for i in range(3))
        else:
            f = (t - 0.55) / 0.45
            col = tuple(int(SKY_MID[i] + (SKY_LOW[i] - SKY_MID[i]) * f)
                        for i in range(3))
        i = _idx(0, y)
        canvas[i:i + W * 3] = bytes(col) * W
    # stars: deterministic scatter, a few with sparkle crosses
    for _ in range(150):
        x = rng.uniform(0, W)
        y = rng.uniform(0, H * 0.62)
        b = rng.uniform(0.35, 1.0)
        r = 1 if rng.random() < 0.8 else 2
        col = (int(255 * b), int(250 * b), int(235 * b))
        circle(x, y, r, col, a=0.9)
        if rng.random() < 0.12:
            thick_line(x - 6, y, x + 6, y, 1.2, col, a=0.55)
            thick_line(x, y - 6, x, y + 6, 1.2, col, a=0.55)
    # shooting star, top right
    thick_line(700, 108, 828, 176, 2.0, (255, 255, 255), a=0.9)
    for k in range(6):
        t = k / 6
        circle(700 + (828 - 700) * t, 108 + (176 - 108) * t, 2.2,
               (255, 255, 255), a=0.8 * (1 - t))
    # moon with halo, top left
    circle(158, 138, 108, MOON_HALO, a=0.10)
    circle(158, 138, 88, MOON_HALO, a=0.12)
    circle(158, 138, 70, MOON)
    circle(138, 120, 11, (228, 220, 190))
    circle(178, 158, 15, (228, 220, 190))
    circle(168, 108, 7, (228, 220, 190))

# ------------------------------------------------- bear-market backdrop
def draw_z_blocky(cx, cy, s, col, w=6):
    """A blocky capital Z drawn with thick strokes (for the 'Zzz')."""
    x0, x1 = cx - s / 2, cx + s / 2
    y0, y1 = cy - s / 2, cy + s / 2
    thick_line(x0, y0, x1, y0, w, col)
    thick_line(x1, y0, x0, y1, w, col)
    thick_line(x0, y1, x1, y1, w, col)


def draw_b_blocky(cx, cy, s, col, w=7):
    """A blocky capital B drawn with thick strokes (for the coin)."""
    x0 = cx - s / 2
    x1 = cx + s / 2
    y0, y1 = cy - s / 2, cy + s / 2
    ym = cy
    thick_line(x0, y0, x0, y1, w, col)
    thick_line(x0, y0, x1 - s * 0.12, y0, w, col)
    thick_line(x0, ym, x1 - s * 0.12, ym, w, col)
    thick_line(x0, y1, x1 - s * 0.12, y1, w, col)
    thick_line(x1 - s * 0.12, y0, x1 - s * 0.12, ym, w, col)
    thick_line(x1 - s * 0.12, ym, x1 - s * 0.12, y1, w, col)


def draw_backdrop(rng):
    # Big faint Bitcoin coin, upper right — the market the bear came from.
    circle(852, 330, 118, GOLD, a=0.16)
    circle(852, 330, 104, GOLD_DARK, a=0.16)
    circle(852, 330, 96, GOLD, a=0.22)
    draw_b_blocky(852, 330, 92, GOLD_DARK, w=13)
    # A red chart line diving down across the lower sky.
    pts = [(40, 700), (180, 742), (300, 726), (430, 788), (560, 762),
           (690, 838), (820, 812), (940, 892)]
    for i in range(len(pts) - 1):
        thick_line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                   5, CANDLE_RED, a=0.75)
    # Falling red candlesticks along the bottom, getting lower to the right.
    base_y = 872
    for k in range(9):
        x = 78 + k * 104
        top = base_y + k * 7
        h = 34 + (k % 3) * 12
        wick = 3
        thick_line(x, top - 16, x, top + h + 14, wick, CANDLE_RED, a=0.8)
        fill_rect(x - 13, top, x + 13, top + h, CANDLE_RED, a=0.85)
        fill_rect(x - 13, top, x + 13, top + 7, CANDLE_DARK, a=0.85)

# ---------------------------------------------------------------- rocket
# The rocket flies up and slightly right, nose at about (560, 70).
RPIV = (512, 232)
RANG = -0.24  # lean to the right


def rpt(x, y):
    """Rocket-local point -> absolute point (rocket points up, -y).
    Local (0, 0) is the rocket pivot; local coords are offsets from it."""
    c, s = math.cos(RANG), math.sin(RANG)
    return (RPIV[0] + x * c - y * s, RPIV[1] + x * s + y * c)


def draw_rocket():
    # flame first (behind the body), three layered teardrops
    for pts, col in (
        ([(-30, 82), (-18, 132), (0, 208), (18, 132), (30, 82)],
         FLAME_OUT),
        ([(-20, 82), (-12, 116), (0, 168), (12, 116), (20, 82)],
         FLAME_MID),
        ([(-11, 82), (-7, 102), (0, 138), (7, 102), (11, 82)],
         FLAME_IN),
    ):
        polygon([rpt(x, y) for x, y in pts], col)
    # smoke puffs hugging the flame base
    for (lx, ly, lr, a) in ((-52, 96, 22, 0.5), (54, 104, 26, 0.45),
                            (-66, 128, 17, 0.4), (68, 134, 19, 0.4),
                            (-40, 138, 15, 0.35), (44, 146, 16, 0.35)):
        cx, cy = rpt(lx, ly)
        circle(cx, cy, lr, (200, 200, 212), a=a)
    # fins
    polygon([rpt(-30, 12), rpt(-30, 66), rpt(-66, 94), rpt(-30, 46)],
            ROCKET_RED)
    polygon([rpt(30, 12), rpt(30, 66), rpt(66, 94), rpt(30, 46)],
            ROCKET_RED)
    # body
    polygon([rpt(-30, -108), rpt(30, -108), rpt(30, 58), rpt(-30, 58)],
            ROCKET_WHITE)
    # grey shading stripe down the right side of the body
    polygon([rpt(16, -108), rpt(30, -108), rpt(30, 58), rpt(16, 58)],
            (214, 218, 228))
    # red band near the bottom of the body
    polygon([rpt(-30, 34), rpt(30, 34), rpt(30, 58), rpt(-30, 58)],
            ROCKET_RED)
    # nose cone
    polygon([rpt(-30, -108), rpt(30, -108), rpt(0, -172)], ROCKET_RED)
    # porthole window
    wx, wy = rpt(0, -52)
    circle(wx, wy, 18, (48, 130, 190))
    circle(wx, wy, 13, (120, 200, 240))
    circle(wx - 5, wy - 5, 5, (230, 248, 255))
    # engine nozzle
    polygon([rpt(-17, 58), rpt(17, 58), rpt(13, 82), rpt(-13, 82)],
            (52, 56, 72))
    # golden rope anchors on the engine ring
    for lx in (-22, 22):
        ax, ay = rpt(lx, 74)
        circle(ax, ay, 9, GOLD)
        circle(ax, ay, 4, GOLD_DARK)


# ------------------------------------------------------- bed and bear
# The bed hangs tilted under the rocket, headboard left, foot right.
BPIV = (512, 690)
BANG = 0.08


def bpt(x, y):
    return rot(x, y, BANG, BPIV[0], BPIV[1])


def _poly_local(pts, col, a=1.0):
    polygon([bpt(x, y) for x, y in pts], col, a)


def _circle_local(cx, cy, r, col, a=1.0):
    ax, ay = bpt(cx, cy)
    circle(ax, ay, r, col, a)


def _ellipse_local(cx, cy, rx, ry, col, a=1.0):
    ax, ay = bpt(cx, cy)
    ellipse(ax, ay, rx, ry, col, a)


def closed_eye(cx, cy, r):
    """A sleeping closed eye: a small upper arc, dark brown."""
    pts = []
    for k in range(13):
        ang = math.radians(200 + (340 - 200) * k / 12)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    for i in range(len(pts) - 1):
        ax, ay = bpt(pts[i][0], pts[i][1])
        bx, by = bpt(pts[i + 1][0], pts[i + 1][1])
        thick_line(ax, ay, bx, by, 5, BEAR_DARK)


def draw_bed_and_bear():
    # headboard
    _poly_local([(212, 580), (250, 580), (250, 690), (212, 690)], WOOD_DARK)
    _circle_local(231, 580, 19, WOOD_DARK)
    # legs
    _poly_local([(262, 745), (282, 745), (282, 778), (262, 778)], WOOD_DARK)
    _poly_local([(738, 745), (758, 745), (758, 778), (738, 778)], WOOD_DARK)
    # frame
    _poly_local([(232, 680), (792, 680), (792, 745), (232, 745)], WOOD)
    _poly_local([(232, 680), (792, 680), (792, 692), (232, 692)],
                WOOD_DARK)
    # mattress
    _poly_local([(240, 650), (784, 650), (784, 686), (240, 686)], MATTRESS)
    # pillow (head end, left)
    _poly_local([(262, 614), (402, 614), (402, 656), (262, 656)], (255, 255, 255))
    _poly_local([(262, 644), (402, 644), (402, 656), (262, 656)],
                (214, 210, 198))
    # blanket draped over the lower two-thirds, corner fluttering up
    _poly_local([(420, 650), (784, 650), (784, 686), (420, 686)], BLANKET)
    _poly_local([(420, 650), (784, 650), (784, 664), (420, 664)],
                BLANKET_DARK)
    _poly_local([(758, 652), (826, 596), (806, 664)], BLANKET)
    _poly_local([(758, 652), (826, 596), (800, 640)], BLANKET_DARK)
    # ---- the bear, asleep on his back, head on the pillow ----
    # body and belly
    _ellipse_local(552, 575, 180, 85, BEAR)
    _ellipse_local(575, 595, 130, 55, BEAR_LIGHT)
    # feet poking out at the foot of the bed
    _ellipse_local(700, 620, 30, 38, BEAR)
    _ellipse_local(740, 615, 28, 36, BEAR)
    _ellipse_local(700, 642, 12, 14, BEAR_LIGHT)
    _ellipse_local(740, 636, 11, 13, BEAR_LIGHT)
    # one paw draped on the belly, one arm flopped to the side
    _ellipse_local(610, 585, 44, 26, BEAR)
    _ellipse_local(455, 645, 38, 20, BEAR)
    # head, muzzle, nose
    _circle_local(350, 570, 68, BEAR)
    _ellipse_local(375, 592, 42, 30, BEAR_LIGHT)
    _ellipse_local(392, 578, 16, 11, (58, 34, 22))
    # ears
    _circle_local(300, 512, 22, BEAR)
    _circle_local(395, 505, 22, BEAR)
    _circle_local(300, 512, 11, BEAR_LIGHT)
    _circle_local(395, 505, 11, BEAR_LIGHT)
    # closed sleeping eyes
    closed_eye(330, 545, 12)
    closed_eye(368, 538, 12)
    # nightcap: bent blue cone with a white band and a pompom
    _poly_local([(292, 510), (392, 500), (360, 452), (318, 428),
                 (300, 470)], (58, 110, 190))
    _poly_local([(322, 478), (372, 470), (352, 448), (336, 462)],
                (240, 242, 246))
    _circle_local(316, 426, 13, (250, 250, 250))
    # golden rope cleats on the four bed corners
    for cx, cy in ((252, 668), (772, 668), (252, 730), (772, 730)):
        _circle_local(cx, cy, 9, GOLD)
        _circle_local(cx, cy, 4, GOLD_DARK)


def draw_ropes():
    """Four golden ropes from the rocket's engine ring to the bed corners."""
    left_anchor = rpt(-22, 74)
    right_anchor = rpt(22, 74)
    for cx, cy in ((252, 668), (252, 730)):
        rope(left_anchor, bpt(cx, cy), 7, GOLD, sag=30)
    for cx, cy in ((772, 668), (772, 730)):
        rope(right_anchor, bpt(cx, cy), 7, GOLD, sag=30)


def draw_motion(rng):
    # "Zzz" floating up from the sleeping bear
    for (cx, cy, s, w) in ((428, 472, 26, 6), (468, 418, 38, 7),
                           (516, 352, 52, 9)):
        draw_z_blocky(cx, cy, s, ZCOL, w=w)
    # rushing air: pale streaks and soft cloud puffs at the edges
    for (x0, y0, x1, y1) in ((28, 320, 130, 306), (60, 470, 150, 462),
                             (880, 560, 990, 548), (900, 210, 988, 200),
                             (40, 880, 150, 872)):
        thick_line(x0, y0, x1, y1, 3, (255, 255, 255), a=0.28)
    for (cx, cy, r) in ((120, 830, 26), (150, 842, 20), (95, 844, 16),
                        (905, 790, 24), (932, 802, 18)):
        circle(cx, cy, r, (210, 210, 224), a=0.30)


# ---------------------------------------------------------------- PNG out
def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw.extend(canvas[y * W * 3:(y + 1) * W * 3])

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    rng = random.Random(7)
    draw_sky(rng)
    draw_backdrop(rng)
    draw_rocket()
    draw_bed_and_bear()
    draw_ropes()
    draw_motion(rng)
    n = write_png(os.path.join(OUT, "entry.png"))
    print(f"wrote entry.png: {n} bytes")


if __name__ == "__main__":
    main()

