# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
# Score maps for the "Breakdown" view on the analog detail pages: our score S (Science weights)
# for every 0.5 deg land cell in the same 4 deg region as the satellite images. Uses analog_grid.json + targets.json.
import json, math, os
from PIL import Image, ImageDraw
D = 'docs/data'; OUT = 'docs/assets/img/bd'; os.makedirs(OUT, exist_ok=True)
g = json.load(open(f'{D}/analog_grid.json')); T = json.load(open(f'{D}/targets.json'))
F = g['features']; W = T['modes']['science']['weights']
cells = {(round(c[1], 2), round(c[0], 2)): c[2:] for c in g['cells']}
COL = {'moon': (79, 209, 232), 'mars': (255, 106, 61)}
def S(p, prof): return sum(W[f] * (1 - abs(p[i] - prof[f])) for i, f in enumerate(F)) / sum(W.values())
def ctr(x): return math.floor(x / 0.5) * 0.5 + 0.25
def render(target, lat, lon, px=360):
    prof = T['targets'][target]['profile']; col = COL['moon' if target.startswith('moon') else 'mars']
    dlat = 4.0; dlon = dlat / max(0.2, math.cos(math.radians(lat)))
    w, n = lon - dlon / 2, lat + dlat / 2
    im = Image.new('RGBA', (px, px), (6, 9, 16, 255)); d = ImageDraw.Draw(im)
    la0, la1 = ctr(lat - dlat / 2), ctr(lat + dlat / 2); lo0, lo1 = ctr(lon - dlon / 2), ctr(lon + dlon / 2)
    la = la0
    while la <= la1 + 1e-9:
        lo = lo0
        while lo <= lo1 + 1e-9:
            p = cells.get((round(la, 2), round(((lo + 180) % 360) - 180, 2)))
            x0 = (lo - 0.25 - w) / dlon * px; x1 = (lo + 0.25 - w) / dlon * px
            y0 = (n - (la + 0.25)) / dlat * px; y1 = (n - (la - 0.25)) / dlat * px
            if p is not None:
                s = S(p, prof); k = max(0.0, min(1.0, (s - 0.45) / 0.5)) ** 1.4
                c = tuple(int(14 + (col[i] - 14) * k) for i in range(3))
                d.rectangle([x0, y0, x1, y1], fill=c + (255,), outline=(255, 255, 255, 28))
            lo += 0.5
        la += 0.5
    cl, co = ctr(lat), ctr(lon)
    d.rectangle([(co - 0.25 - w) / dlon * px, (n - (cl + 0.25)) / dlat * px, (co + 0.25 - w) / dlon * px, (n - (cl - 0.25)) / dlat * px], outline=(255, 255, 255, 255), width=3)
    name = f"{target}_{lat:.2f}_{lon:.2f}.png"; im.convert('RGB').save(f'{OUT}/{name}', optimize=True)
    pc = cells.get((round(cl, 2), round(co, 2)))
    return name, (round(S(pc, prof), 3) if pc else None)
done = []
fa = json.load(open(f'{D}/famous_analogs.json'))
for f in fa['sites']:
    if f['scored']: done.append((f['id'],) + render(f['primary'], f['lat'], f['lon']) + (f['targets'][f['primary']]['S'],))
ct = json.load(open(f'{D}/country_top.json'))
for tk, rows in ct['top'].items():
    for r in rows: done.append((r['province'],) + render(tk, r['lat'], r['lon']) + (r['S'],))
sc = json.load(open(f'{D}/showcase.json'))
for c in sc['cards']:
    s0 = c['sites'][0]; done.append((c['key'],) + render(c['target'], s0['lat'], s0['lon']) + (None,))
for x in done: print(x)
