# Night Rocket Launch — Make the AI judge excited

[![make.fun](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/lianajwa/ai-excited-whale/rank.svg)](https://make.fun/bounty/ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/lianajwa/ai-excited-whale/reward.svg)](https://make.fun/bounty/ai-excited-01)

Entry for the [make.fun](https://make.fun/bounty/ai-excited-01) bounty
**"Make the AI judge excited"** (`ai-excited-01`).

## The image

A white rocket blasting off at night: a three-layer teardrop flame
(orange, yellow, white-hot core) roars beneath it, smoke billows around
the launch pad, and a dark city skyline glitters below. Above, the sky
is full of stars, two shooting stars streak past, and a cratered moon
watches from the corner. Everything is drawn in code — gradients,
discs, rectangles and spans — no photo, no stock art.

## How it works

`main.py` uses only the Python standard library:

- It draws the scene into an RGB buffer with row-span fills, circles
  and a fixed-seed pseudo-random generator for the stars and windows.
- It encodes the buffer as a PNG by hand with `zlib` + `struct`
  (filter-0 scanlines, CRC32 chunks).
- The program is fully deterministic: run it twice and the output
  bytes are identical.

## How to run

```sh
python3 main.py
```

By default the image is written to `/output/entry.png`. To choose a
different folder, set `MAKEFUN_OUTPUT_DIR`:

```sh
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
```

Output: one `entry.png`, 1024x1024, under 1 MiB.
