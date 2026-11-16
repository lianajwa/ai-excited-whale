# Bear Market, Rocket Ride

[![make.fun](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/lianajwa/ai-excited-whale/rank.svg)](https://make.fun/bounty/ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/lianajwa/ai-excited-whale/reward.svg)](https://make.fun/bounty/ai-excited-01)

One image for make.fun's "Make the AI judge excited" bounty
(`ai-excited-01`): a program that writes one image to `/output/entry.png`.

## The image

It is a Bitcoin bear market — so a big brown bear is asleep on his bed,
wearing a blue nightcap, "Zzz" floating up from his nose. A rocket is
hauling the whole bed up to the moon, the bed tied to the rocket with four
golden ropes. The bear does not care. He is asleep.

Behind him, the market he came from: a faint golden Bitcoin coin, a red
chart line diving down, and red candlesticks falling along the bottom. The
joke is literal — the bear of the bear market, carried off by a rocket.

## How to run

Stdlib-only Python 3.13, no network, no external assets. Deterministic:
two runs write byte-identical PNGs.

```sh
python3 main.py            # writes /output/entry.png
MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
```

Output: 1024x1024 PNG, well under the 1 MiB limit.
