#!/usr/bin/env python3
"""Luminance stats for shading captures: stats.py <dir> [<dir2>] -> table (mean, p95, %>=245) per shot; with two dirs, before/after."""
import sys, os, json
import numpy as np
from PIL import Image

def stats(p):
    a = np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
    y = a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114
    mx = a.max(axis=2)
    return dict(mean=float(y.mean()), p50=float(np.percentile(y, 50)), p95=float(np.percentile(y, 95)), p99=float(np.percentile(y, 99)),
                clip=float((y >= 245).mean() * 100), chclip=float((mx >= 254).mean() * 100),
                # "cream flats": bright pixels that lost their colour (lum >= 170, chroma < 18% of max) - what the old shoulders made of lit stone
                cream=float(((y >= 170) & ((mx - a.min(axis=2)) < 0.18 * mx)).mean() * 100))

def table(dirs):
    names = sorted(f for f in os.listdir(dirs[0]) if f.endswith('.png'))
    res = {}
    for n in names:
        row = [stats(os.path.join(d, n)) if os.path.exists(os.path.join(d, n)) else None for d in dirs]
        res[n[:-4]] = row
    return res

if __name__ == '__main__':
    dirs = sys.argv[1:]
    res = table(dirs)
    if len(dirs) == 1:
        print(f"{'shot':22s} {'mean':>6s} {'p50':>6s} {'p95':>6s} {'p99':>6s} {'%>=245':>7s} {'%ch255':>7s}")
        for n, (s,) in res.items():
            print(f"{n:22s} {s['mean']:6.1f} {s['p50']:6.1f} {s['p95']:6.1f} {s['p99']:6.1f} {s['clip']:7.2f} {s['chclip']:7.2f}")
    else:
        print(f"| shot | mean before | mean after | p95 before | p95 after | % ≥245 before | % ≥245 after | % cream before | % cream after |")
        print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for n, (a, b) in res.items():
            if not b: continue
            print(f"| {n} | {a['mean']:.1f} | {b['mean']:.1f} | {a['p95']:.1f} | {b['p95']:.1f} | {a['clip']:.2f} | {b['clip']:.2f} | {a['cream']:.2f} | {b['cream']:.2f} |")
    json.dump(res, open(os.path.join(dirs[-1], '_stats.json'), 'w'), indent=1)
