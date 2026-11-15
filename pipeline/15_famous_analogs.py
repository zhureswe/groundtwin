# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Famous field analogs (the ten places on the first version of the site) scored with our own Analog Engine:
the 0.5-deg cell that contains each site in docs/data/analog_grid.json, the target profiles and Science weights in
targets.json, the same similarity S and 'top X%' as 04_analog_engine / 13_explanations -> docs/data/famous_analogs.json."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs' / 'data'
MATCH, DIFFER = 0.8, 0.5
TARGETS = ('moon_south_pole', 'mars_gale')

# name, country, tag, targets shown first, blurb (text of the first site version), lat, lon, coordinate source
SITES = [
    ('atacama', 'Atacama Desert', 'Chile', 'MARS · rovers, life detection', 'mars_gale',
     'One of the driest places on Earth. NASA tests rover drills and life-detection instruments here before sending them to Mars.',
     -24.5, -69.25, 'Wikipedia: Atacama Desert (as in validation.json)'),
    ('death-valley', 'Death Valley', 'USA', 'MARS · salts, geology', 'mars_gale',
     'A hot, hyper-arid basin with salt flats and alluvial fans, used to study how water and salt shaped Martian terrain.',
     36.24694444, -116.81694444, 'Wikipedia: Death Valley (as in validation.json)'),
    ('devon-island', 'Devon Island', 'Canada', 'MOON & MARS · craters, EVA', 'mars_gale',
     'A polar desert around the Haughton impact crater, home of the long-running Haughton-Mars Project field station.',
     75.38333333, -89.66666667, 'Wikipedia: Haughton impact crater (as in validation.json)'),
    ('hawaii', 'Hawaiʻi lava fields', 'USA', 'MOON · rovers, habitats', 'moon_south_pole',
     'Fresh basalt, lava tubes and volcanic ash make Hawaiʻi a test ground for lunar rovers and habitat simulations.',
     19.42109747, -155.28676243, 'Wikipedia: Kīlauea (as in validation.json)'),
    ('lanzarote', 'Lanzarote', 'Spain', 'MOON & MARS · astronaut training', 'moon_south_pole',
     'Volcanic landscapes where ESA’s PANGAEA course trains astronauts to read planetary geology in the field.',
     28.99417, -13.79333, 'Wikipedia: Timanfaya National Park'),
    ('rio-tinto', 'Río Tinto', 'Spain', 'MARS · minerals, life', 'mars_gale',
     'An acidic, iron-rich river whose minerals and microbes resemble the chemistry of ancient Martian waters.',
     37.72, -6.56, 'Peña de Hierro near Nerva, the NASA MARTE drill site (approximate)'),
    ('mcmurdo', 'McMurdo Dry Valleys', 'Antarctica', 'MARS · cold, ice', 'mars_gale',
     'Cold, windy and almost without precipitation, the closest Earth gets to the frozen, dry Martian surface.',
     -77.5, 162.0, 'Wikipedia: McMurdo Dry Valleys (approximate)'),
    ('utah', 'Utah desert', 'USA', 'MARS · crew simulations', 'mars_gale',
     'Red sedimentary desert around the Mars Desert Research Station, where crews rehearse long Mars missions.',
     38.40645833, -110.79190278, 'Wikipedia: Mars Desert Research Station (as in validation.json)'),
    ('iceland', 'Iceland lava fields', 'Iceland', 'MOON · geology training', 'moon_south_pole',
     'Apollo astronauts trained here in the 1960s, learning to read volcanic rock before walking on the Moon.',
     65.033, -16.783, 'Wikipedia: Askja (as in validation.json)'),
    ('mangystau', 'Mangystau', 'Kazakhstan', 'MARS · our case study', 'mars_gale',
     'The floor of the vanished Tethys Ocean: layered rock, salt flats and stone concretions. Our own case study, scored on NASA data, not looks.',
     None, None, 'showcase.json (6 sites)'),
]


def hav(lat1, lon1, lat2, lon2):
    r = math.radians
    a = math.sin(r(lat2 - lat1) / 2) ** 2 + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(r(lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))


def main():
    grid = json.loads((DATA / 'analog_grid.json').read_text(encoding='utf-8'))
    tg = json.loads((DATA / 'targets.json').read_text(encoding='utf-8'))
    sc = json.loads((DATA / 'showcase.json').read_text(encoding='utf-8'))
    feats = grid['features']
    cells = grid['cells']                       # [lon, lat, *percentiles]
    w = tg['modes']['science']['weights']
    wsum = sum(w[f] for f in feats)
    n = len(cells)

    def score(vec, prof):
        return sum((1 - abs(vec[f] - prof[f])) * w[f] for f in feats) / wsum

    allS = {t: sorted((score(dict(zip(feats, c[2:])), tg['targets'][t]['profile']) for c in cells), reverse=True) for t in TARGETS}

    def position(t, S):
        lo, hi = 0, n                          # number of cells with a strictly higher score
        arr = allS[t]
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] > S + 1e-12:
                lo = mid + 1
            else:
                hi = mid
        return lo + 1

    mg = next(c for c in sc['cards'] if c['key'] == 'mangystau')
    out = []
    for sid, name, country, tag, primary, blurb, lat, lon, src in SITES:
        row = dict(id=sid, name=name, country=country, tag=tag, primary=primary, blurb=blurb, coord_source=src)
        if sid == 'mangystau':
            vec = mg['rows'][0]['features']
            row.update(lat=mg['sites'][0]['lat'], lon=mg['sites'][0]['lon'], sites=mg['sites'], cell='mean of the 6 site cells')
        else:
            row.update(lat=lat, lon=lon)
            best = min(cells, key=lambda c: hav(lat, lon, c[1], c[0]))
            d = hav(lat, lon, best[1], best[0])
            # a site is scored only if its own 0.5-deg cell is a land cell of the grid
            inside = abs(best[1] - lat) <= 0.25 + 1e-9 and abs(best[0] - lon) <= 0.25 + 1e-9
            if not inside:
                row.update(scored=False, reason=('Antarctica is not in our grid' if lat < -60 else
                                                 f'its 0.5° cell is not a land cell of our grid (nearest land cell {d:.0f} km away)'))
                out.append(row)
                continue
            vec = dict(zip(feats, best[2:]))
            row.update(cell=[best[1], best[0]])
        row['scored'] = True
        row['features'] = {f: round(vec[f], 3) for f in feats}
        row['targets'] = {}
        for t in TARGETS:
            prof = tg['targets'][t]['profile']
            S = score(vec, prof)
            pos = position(t, S)
            s = {f: 1 - abs(vec[f] - prof[f]) for f in feats}
            row['targets'][t] = dict(S=round(S, 3), position=pos, n_cells=n, top_percent=round(pos / n * 100, 3), profile=prof,
                                     match=[f for f in feats if s[f] >= MATCH], partly=[f for f in feats if DIFFER <= s[f] < MATCH],
                                     differ=[f for f in feats if s[f] < DIFFER])
        if sid == 'mangystau':           # keep the exact Mangystau numbers already published (explanations.json)
            ex = json.loads((DATA / 'explanations.json').read_text(encoding='utf-8'))['cards']['mangystau'][0]
            row['targets']['mars_gale'].update(S=ex['S'], position=ex['position'], top_percent=ex['top_percent'],
                                               match=ex['match_features'], partly=ex['partly_features'], differ=ex['differ_features'])
        out.append(row)
    res = dict(demo=False, mode='science', n_cells=n, method=('Each site scored with the Analog Engine on its own 0.5-deg land cell '
               '(Mangystau: mean of its 6 site cells), Science weights, target profiles from targets.json. Match = s_i >= 0.8, '
               'differs = s_i < 0.5. Rank = 1 + number of land cells with a higher S.'), sites=out)
    (DATA / 'famous_analogs.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    for r in out:
        print(r['id'], r.get('scored'), r.get('reason', ''), {t: (v['S'], v['top_percent']) for t, v in r.get('targets', {}).items()})


if __name__ == '__main__':
    main()
