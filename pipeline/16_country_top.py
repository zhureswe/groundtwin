# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Top 5 per target with one place per country: same Analog Engine score S (Science weights, targets.json profiles),
cells at least 600 km apart, and no country twice. Country, province and nearest town from GeoNames
(offline, python package reverse_geocoder) -> docs/data/country_top.json."""
import json
import math
from pathlib import Path

import reverse_geocoder as rg

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs' / 'data'
MATCH, DIFFER, MIN_SEP_KM = 0.8, 0.5, 600
TARGETS = ('moon_south_pole', 'mars_gale')
COUNTRY = dict(CN='China', MN='Mongolia', IN='India', AR='Argentina', NA='Namibia', DZ='Algeria', EG='Egypt', TD='Chad',
               MA='Morocco', CL='Chile', PE='Peru', BO='Bolivia', US='USA', IR='Iran', AF='Afghanistan', PK='Pakistan',
               SA='Saudi Arabia', LY='Libya', SD='Sudan', NE='Niger', ML='Mali', MR='Mauritania', KZ='Kazakhstan',
               UZ='Uzbekistan', TM='Turkmenistan', AU='Australia', OM='Oman', YE='Yemen', JO='Jordan', TJ='Tajikistan', KG='Kyrgyzstan')
# GeoNames province names that are outdated or too long for a card
ADMIN = {'Xinjiang Uygur Zizhiqu': 'Xinjiang', 'Govi-Altay': 'Govi-Altai', 'Souss-Massa-Draa': 'Drâa-Tafilalet',
         'Tibet Autonomous Region': 'Tibet', 'Inner Mongolia': 'Inner Mongolia'}


def hav(lat1, lon1, lat2, lon2):
    r = math.radians
    a = math.sin(r(lat2 - lat1) / 2) ** 2 + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(r(lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))


def main():
    grid = json.loads((DATA / 'analog_grid.json').read_text(encoding='utf-8'))
    tg = json.loads((DATA / 'targets.json').read_text(encoding='utf-8'))
    feats, cells = grid['features'], grid['cells']          # cells: [lon, lat, *percentiles]
    w = tg['modes']['science']['weights']
    wsum = sum(w[f] for f in feats)
    n = len(cells)
    out = {}
    for t in TARGETS:
        prof = tg['targets'][t]['profile']
        scored = sorted(((sum((1 - abs(c[2 + i] - prof[f])) * w[f] for i, f in enumerate(feats)) / wsum, c) for c in cells),
                        key=lambda x: -x[0])
        head = scored[:4000]
        geo = rg.search([(c[1], c[0]) for _, c in head], mode=1, verbose=False)
        picked, used = [], set()
        for (S, c), g in zip(head, geo):
            if any(hav(c[1], c[0], p['lat'], p['lon']) <= MIN_SEP_KM for p in picked) or g['cc'] in used:
                continue
            vec = dict(zip(feats, c[2:]))
            s = {f: 1 - abs(vec[f] - prof[f]) for f in feats}
            pos = 1 + sum(1 for x, _ in scored if x > S + 1e-12)
            admin = 'Ladakh' if g['name'] == 'Leh' else ADMIN.get(g['admin1'], g['admin1'])
            picked.append(dict(rank=len(picked) + 1, lat=c[1], lon=c[0], S=round(S, 3), position=pos, n_cells=n,
                               top_percent=round(pos / n * 100, 3), country=COUNTRY.get(g['cc'], g['cc']), cc=g['cc'],
                               province=admin, near=g['name'], features={f: round(vec[f], 3) for f in feats}, profile=prof,
                               match=[f for f in feats if s[f] >= MATCH], partly=[f for f in feats if DIFFER <= s[f] < MATCH],
                               differ=[f for f in feats if s[f] < DIFFER]))
            used.add(g['cc'])
            if len(picked) == 5:
                break
        out[t] = picked
        print(t, [(p['province'], p['country'], p['near'], p['S'], p['position']) for p in picked])
    res = dict(demo=False, mode='science', n_cells=n, min_separation_km=MIN_SEP_KM,
               rule='Best-scoring 0.5-deg land cell per country, cells at least 600 km apart, Science weights. '
                    'Rank = 1 + number of land cells with a higher S.',
               names='Country, province and nearest town: GeoNames via the reverse_geocoder package (offline).', top=out)
    (DATA / 'country_top.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
