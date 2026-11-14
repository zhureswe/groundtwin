# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Showcase: top-5 Earth cells by formula for the Moon and for one Mars target, plus three highlighted cards
(Moon training reference, Mars training reference, Mangystau) with their honest rank among all land cells."""
import importlib
import json
import numpy as np
from common import SITE_DATA, ee_init

ae = importlib.import_module('04_analog_engine')
val = importlib.import_module('05_validation')
ref = importlib.import_module('06_references')
MODE, N_TOP = 'science', 5
MOON, MARS_CHOICES = 'moon_south_pole', ('mars_gale', 'mars_jezero')
MATCH, DIFFER = 0.8, 0.5            # same thresholds as the website place card
ADMIN = 'FAO GAUL 2015 level 1 (FAO/GAUL/2015/level1 in Google Earth Engine)'
USGS_ANALOGS = 'https://www.usgs.gov/science/science-explorer/planetary-science/terrestrial-analogs'

CARDS = [
    dict(key='moon_reference', title='Moon training reference: Cinder Lake Crater Field / Meteor Crater, Arizona', target=MOON,
         sites=[('Cinder Lake Crater Field', 35.30657, -111.50482,
                 'USGS, Cinder Lake Crater Field UAS DEMs 2023-2024 (catalog.data.gov), centre of bounding box'),
                ('Meteor Crater', 35.02806, -111.02333, 'Wikipedia: https://en.wikipedia.org/wiki/Meteor_Crater')],
         facts=['Cinder Lake Crater Field: craters blasted by the USGS in the late 1960s as a lunar analog training site '
                'for Apollo astronauts (USGS data release, catalog.data.gov); today used to train and test Artemis '
                'astronauts and their field equipment (USGS: ' + USGS_ANALOGS + ').',
                'Meteor Crater: a real impact crater where NASA astronauts trained for the Apollo missions in the 1960s-70s '
                '(Wikipedia: Meteor Crater).'],
         not_like=['It was chosen for crater shapes and geology training, which our 7 climate/terrain features do not measure']),
    dict(key='mars_reference', title='Mars training reference: MDRS / San Rafael Swell, Utah', target=None,
         sites=[(s[0], s[3], s[4], s[5]) for s in val.SITES if s[0] in ('Mars Desert Research Station (Utah)', 'San Rafael Swell (Utah)')],
         facts=['MDRS is a Mars Society station for Mars-mission training (not a NASA station).',
                'Utah is in the NASA Planetary Analog Explorer catalogue.'],
         not_like=[]),
    dict(key='mangystau', title='Our site: Mangystau, Kazakhstan', target=None, sites=None,
         facts=['Floor of the ancient Tethys Sea: layered sedimentary rocks (Bozzhyra, Sherkala), salt flats (Tuzbair), '
                'stone concretions (Torysh); the Karagiye Depression is about 132 m below sea level.'],
         not_like=['Torysh concretions are metres across and made of sandstone; the Opportunity "blueberries" are millimetres '
                   'across and made of hematite', 'Tethys was a sea; Gale and Jezero held lakes',
                   'Earth has air, warmth, occasional rain and life']),
]


def admin_names(ee, cells):
    fc = ee.FeatureCollection('FAO/GAUL/2015/level1')
    out = []
    for lon, lat in cells:
        f = fc.filterBounds(ee.Geometry.Point([lon, lat])).first()
        try:
            p = ee.Feature(f).toDictionary(['ADM0_NAME', 'ADM1_NAME']).getInfo()
            out.append(f"{p['ADM1_NAME']}, {p['ADM0_NAME']}")
        except Exception:
            out.append(None)   # cell centre falls outside the GAUL polygons (coast, lake)
    return out


def features_verdict(vec, profile):
    s = {f: 1 - abs(v - profile[f]) for f, v in zip(ae.FEATURES, vec)}
    return [f for f in ae.FEATURES if s[f] >= MATCH], [f for f in ae.FEATURES if s[f] < DIFFER]


def card_row(name, cells, P, S, R, profile, prof_vec):
    vec = P[cells].mean(0)
    match, differ = features_verdict(vec, profile)
    pos = np.argsort(-S).argsort()
    return dict(place=name, n_cells=len(cells), S=round(float(S[cells].mean()), 3), cosine=round(ref.cosine(vec, prof_vec), 3),
                top_percent=round(float(np.median(R[cells]) * 100), 1), position=int(np.median(pos[cells])) + 1,
                matches=match, differs=differ, features={f: round(float(v), 3) for f, v in zip(ae.FEATURES, vec)})


def main():
    lon, lat, P = val.load_grid()
    T = json.loads((SITE_DATA / 'targets.json').read_text())
    v = json.loads((SITE_DATA / 'validation.json').read_text())
    mgs = json.loads((SITE_DATA / 'mangystau.json').read_text(encoding='utf-8'))
    w = T['modes'][MODE]['weights']
    mars = min(MARS_CHOICES, key=lambda t: v['mean_top_percent'][t][MODE])
    why = (f"{T['targets'][mars]['label']} is shown because known Mars analog sites rank better for it in our validation "
           f"(Science mode: average rank top {v['mean_top_percent'][mars][MODE]}%, p = {v['mean_top_percent_p'][mars][MODE]}; "
           + '; '.join(f"{T['targets'][t]['label'].split(' (')[0]}: top {v['mean_top_percent'][t][MODE]}%" for t in MARS_CHOICES if t != mars)
           + '), and its layered lake sediments are the Mars feature that Mangystau is compared with.')
    ee = ee_init()
    out = dict(demo=False, mode=MODE, n_cells=int(len(lon)), mars_target=mars, mars_choice_reason=why,
               selection='Top cells by the similarity formula S only (no manual choice), at least '
                         f'{ae.MIN_SEP_KM} km apart. Region names: {ADMIN}.', top={}, cards=[])
    for tk in (MOON, mars):
        S = ae.similarity(P, T['targets'][tk]['profile'], w)
        idx = ae.top_places(S, lon, lat, N_TOP)
        names = admin_names(ee, [(float(lon[i]), float(lat[i])) for i in idx])
        out['top'][tk] = [dict(rank=r + 1, lon=float(lon[i]), lat=float(lat[i]), S=round(float(S[i]), 3), region=n,
                               matches=features_verdict(P[i], T['targets'][tk]['profile'])[0],
                               differs=features_verdict(P[i], T['targets'][tk]['profile'])[1])
                          for r, (i, n) in enumerate(zip(idx, names))]
        print(tk, [(x['region'], x['S']) for x in out['top'][tk]])
    for c in CARDS:
        tk = c['target'] or mars
        prof = T['targets'][tk]['profile']
        S = ae.similarity(P, prof, w)
        R = ae.top_rank(S)
        pv = np.array([prof[f] for f in ae.FEATURES])
        if c['sites'] is None:
            rows = [card_row('Mangystau (6 sites)', sorted({ae.cell_index(lon, lat, p['lon'], p['lat']) for p in mgs['places']}),
                             P, S, R, prof, pv)]
            coords = [dict(name=p['name'], lat=p['lat'], lon=p['lon'], coord_source=p['coord_source']) for p in mgs['places']]
        else:
            rows = [card_row(n, [ae.cell_index(lon, lat, lo, la)], P, S, R, prof, pv) for n, la, lo, _ in c['sites']]
            coords = [dict(name=n, lat=la, lon=lo, coord_source=src) for n, la, lo, src in c['sites']]
        out['cards'].append(dict(key=c['key'], title=c['title'], target=tk, rows=rows, sites=coords,
                                 facts=c['facts'], not_like=c['not_like'] + T['targets'][tk]['cannot'][:2],
                                 in_top=any(r['position'] <= N_TOP for r in rows)))
        print(c['key'], [(r['place'], r['S'], r['cosine'], r['top_percent'], r['position']) for r in rows])
    (SITE_DATA / 'showcase.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    print(why)


if __name__ == '__main__':
    main()
