# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Eight places for the Analogs page, chosen only by the Analog Engine score S (Science weights):
  official — the 4 best-scoring known analog sites listed by NASA Planetary Analog Explorer or USGS (validation.json),
             each scored for its own body (Moon -> moon_south_pole, Mars -> mars_gale; 'any' -> the better of the two);
  found    — the 2 best Moon + 2 best Mars cells that are not near any listed site (>= 600 km), from 4 different
             countries, all >= 600 km apart.
Plus Mangystau (famous_analogs.json). Same grid and rule as 15/16 -> docs/data/analogs8.json."""
import importlib
import json

import reverse_geocoder as rg
from common import SITE_DATA

ct = importlib.import_module('16_country_top')
MATCH, DIFFER, SEP_KM = 0.8, 0.5, 600
BODY_TARGET = dict(moon='moon_south_pole', mars='mars_gale')
OFFICIAL_LISTS = ('NASA Planetary Analog Explorer', 'USGS')
COUNTRY = {**ct.COUNTRY, 'TR': 'Turkey', 'IS': 'Iceland', 'ES': 'Spain', 'CA': 'Canada'}


def load(name):
    return json.loads((SITE_DATA / f'{name}.json').read_text(encoding='utf-8'))


def main():
    grid, tg, val, fam = load('analog_grid'), load('targets'), load('validation'), load('famous_analogs')
    feats, cells, n = grid['features'], grid['cells'], len(grid['cells'])
    w = tg['modes']['science']['weights']
    S = {tk: [sum((1 - abs(c[2 + i] - tg['targets'][tk]['profile'][f])) * w[f] for i, f in enumerate(feats)) / sum(w.values())
              for c in cells] for tk in BODY_TARGET.values()}
    srt = {tk: sorted(v, reverse=True) for tk, v in S.items()}
    step = grid['cell_deg']
    index = {(round(c[0], 2), round(c[1], 2)): i for i, c in enumerate(cells)}
    cell_of = lambda lat, lon: index.get((round((lon // step) * step + step / 2, 2), round((lat // step) * step + step / 2, 2)))
    geo = lambda pts: rg.search(pts, mode=1, verbose=False)

    def card(i, tk, **extra):
        c, prof = cells[i], tg['targets'][tk]['profile']
        vec = dict(zip(feats, c[2:])); s = {f: 1 - abs(vec[f] - prof[f]) for f in feats}
        pos = 1 + sum(1 for x in srt[tk] if x > S[tk][i] + 1e-12)
        return dict(target=tk, cell=[c[1], c[0]], S=round(S[tk][i], 3), position=pos, n_cells=n, top_percent=round(pos / n * 100, 3),
                    features={f: round(vec[f], 3) for f in feats}, profile=prof, match=[f for f in feats if s[f] >= MATCH],
                    partly=[f for f in feats if DIFFER <= s[f] < MATCH], differ=[f for f in feats if s[f] < DIFFER], **extra)

    # official: listed sites, one card per grid cell
    listed = [k for k in val['known_sites'] if k['listed_by'].startswith(OFFICIAL_LISTS)]
    cand = {}
    for k in listed:
        i = cell_of(k['lat'], k['lon'])
        if i is None:
            continue
        tks = [BODY_TARGET[k['body']]] if k['body'] in BODY_TARGET else list(BODY_TARGET.values())
        tk = max(tks, key=lambda t: S[t][i])
        if i not in cand or S[tk][i] > cand[i][1]:
            cand[i] = (k, S[tk][i], tk)
    best = sorted(cand.items(), key=lambda x: -x[1][1])[:4]
    g = geo([(k['lat'], k['lon']) for _, (k, _, _) in best])
    official = [card(i, tk, name=k['name'], country=COUNTRY.get(gg['cc'], gg['cc']), lat=k['lat'], lon=k['lon'],
                     coord_source=k['coord_source'], listed_by=k['listed_by'].split(' (')[0])
                for (i, (k, _, tk)), gg in zip(best, g)]

    # found: not near any listed or famous site, distinct countries, >= 600 km apart
    known = [(k['lat'], k['lon']) for k in val['known_sites']] + [(s['lat'], s['lon']) for s in fam['sites']]
    found, used = [], set()
    for tk in ('moon_south_pole', 'mars_gale'):
        order = sorted(range(n), key=lambda i: -S[tk][i])[:4000]
        gg = geo([(cells[i][1], cells[i][0]) for i in order])
        got = 0
        for i, gi in zip(order, gg):
            lat, lon = cells[i][1], cells[i][0]
            if gi['cc'] in used or any(ct.hav(lat, lon, a, b) < SEP_KM for a, b in known) \
                    or any(ct.hav(lat, lon, f['lat'], f['lon']) < SEP_KM for f in found):
                continue
            prov = 'Ladakh' if gi['name'] == 'Leh' else ct.ADMIN.get(gi['admin1'], gi['admin1'])
            found.append(card(i, tk, name=f"Near {gi['name']}" + (f", {prov}" if prov and prov != gi['name'] else ''), country=COUNTRY.get(gi['cc'], gi['cc']), lat=lat, lon=lon,
                              coord_source='0.5° grid cell centre; names: GeoNames (reverse_geocoder)'))
            used.add(gi['cc']); got += 1
            if got == 2:
                break

    m = next(s for s in fam['sites'] if s['id'] == 'mangystau')
    mg = dict(name=m['name'], country=m['country'], target='mars_gale', lat=m['lat'], lon=m['lon'],
              **{k: m['targets']['mars_gale'][k] for k in ('S', 'position', 'n_cells', 'top_percent')})
    out = dict(demo=False, mode='science', n_cells=n, separation_km=SEP_KM,
               rule_official='Known analog sites listed by NASA Planetary Analog Explorer or USGS (validation.json), scored for their own body; '
                             "sites listed for any body get the better of Moon/Mars. Top 4 by S, one per grid cell.",
               rule_found=f'Best cells by S that are at least {SEP_KM} km from every listed or famous analog site: 2 for the Moon (south pole base) '
                          f'and 2 for Mars (Gale), from 4 different countries, at least {SEP_KM} km apart.',
               official=official, found=found, mangystau=mg)
    (SITE_DATA / 'analogs8.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    for x in official + found:
        print(f"{x['name']:40s} {x['country']:12s} {x['target']:16s} S {x['S']}  #{x['position']}  top {x['top_percent']}%")
    print('Mangystau', mg['S'], mg['position'], mg['top_percent'])


if __name__ == '__main__':
    main()
