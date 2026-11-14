# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Validation: Lift of known planetary analog sites in the top 10% of the Analog Engine map, with a random benchmark."""
import importlib
import json
import numpy as np
from common import DATA, RAW, SITE_DATA

ae = importlib.import_module('04_analog_engine')
TOP = 0.10
N_RANDOM = 1000
SEED = 42

NAE = 'NASA Planetary Analog Explorer (https://science.nasa.gov/solar-system/analog-explorer/)'
USGS = 'USGS Terrestrial Analog Data Portal (https://tadp.astrogeology.usgs.gov), terrestrial-analog-sites API'
REF = 'GroundTwin reference site (team plan)'
WIKI = 'Wikipedia: https://en.wikipedia.org/wiki/'
SITES = [  # name, body, listed by, lat, lon, coordinate source
    ('Medicine Lake Volcano (lava caves)', 'moon', NAE, 41.61095603, -121.55363546, WIKI + 'Medicine_Lake_Volcano'),
    ('Kilauea (basalt landscapes)', 'moon', NAE, 19.42109747, -155.28676243, WIKI + 'K%C4%ABlauea'),
    ('Askja (subsurface ice)', 'moon', NAE, 65.033, -16.783, WIKI + 'Askja'),
    ('Askja / Vikursundar (land ripples)', 'mars', NAE, 65.033, -16.783, WIKI + 'Askja'),
    ('Atacama Desert', 'mars', NAE, -24.5, -69.25, WIKI + 'Atacama_Desert'),
    ('Death Valley', 'mars', NAE, 36.24694444, -116.81694444, WIKI + 'Death_Valley'),
    ('Lake Salda', 'mars', NAE, 37.55, 29.68333333, WIKI + 'Lake_Salda'),
    ('Verde Valley', 'mars', NAE, 34.75305556, -112.02194444, WIKI + 'Verde_Valley'),
    ('Pisgah Lava Flow', 'any', USGS, 34.7412, -116.374, 'USGS TADP API'),
    ('Holuhraun Lava Flow', 'any', USGS, 64.9282, -16.5217, 'USGS TADP API'),
    ('Oskjuvatn', 'any', USGS, 65.01, -16.71, 'USGS TADP API'),
    ('Baugur', 'any', USGS, 64.85942, -16.85907, 'USGS TADP API'),
    ('Mars Desert Research Station (Utah)', 'mars', REF, 38.40645833, -110.79190278, WIKI + 'Mars_Desert_Research_Station'),
    ('San Rafael Swell (Utah)', 'mars', REF, 38.813, -110.855, WIKI + 'San_Rafael_Swell'),
    ('Devon Island', 'mars', REF, 75.25, -88.0, WIKI + 'Devon_Island'),
    ('Haughton impact crater', 'mars', REF, 75.38333333, -89.66666667, WIKI + 'Haughton_impact_crater'),
]
EXCLUDED = [
    'Gulkana Glacier (NASA Analog Explorer; analog of Enceladus, not Moon/Mars)',
    'Aden Crater (NASA Analog Explorer; analog of Venus, not Moon/Mars)',
    'Pilot Valley, Utah (NASA Analog Explorer, Mars): no coordinates found in Wikipedia or OpenStreetMap',
]
BODY = {'moon_south_pole': 'moon', 'mars_jezero': 'mars', 'mars_gale': 'mars'}


def load_grid():
    lon, lat, p, *_ = ae.percentiles(ae.build_grid())
    return lon, lat, np.stack([p[f] for f in ae.FEATURES], 1)


def site_cells(lon, lat):
    return [ae.cell_index(lon, lat, s[4], s[3]) for s in SITES]


def lift(R, cells):
    return float(np.mean(R[cells] <= TOP) / TOP)


def main():
    lon, lat, P = load_grid()
    T = json.loads((SITE_DATA / 'targets.json').read_text())
    cells = site_cells(lon, lat)
    rng = np.random.default_rng(SEED)
    out_lift, out_p, used, ranks = {}, {}, {}, {s[0]: {} for s in SITES}
    mean_rank, mean_rank_p = {}, {}
    for tk, t in T['targets'].items():
        sel = sorted({c for c, s in zip(cells, SITES) if s[1] in (BODY[tk], 'any')})   # unique cells
        used[tk] = len(sel)
        out_lift[tk], out_p[tk], mean_rank[tk], mean_rank_p[tk] = {}, {}, {}, {}
        for mk, m in T['modes'].items():
            R = ae.top_rank(ae.similarity(P, t['profile'], m['weights']))
            obs = lift(R, sel)
            draws = [rng.choice(len(R), len(sel), replace=False) for _ in range(N_RANDOM)]
            rand = np.array([lift(R, d) for d in draws])
            out_lift[tk][mk] = round(obs, 2)
            out_p[tk][mk] = round(float((np.sum(rand >= obs) + 1) / (N_RANDOM + 1)), 4)
            mr, rmr = float(R[sel].mean()), np.array([R[d].mean() for d in draws])
            mean_rank[tk][mk] = round(mr * 100, 1)
            mean_rank_p[tk][mk] = round(float((np.sum(rmr <= mr) + 1) / (N_RANDOM + 1)), 4)
            if mk == 'science':
                for c, s in zip(cells, SITES):
                    ranks[s[0]][tk] = round(float(R[c] * 100), 1)
        print(tk, 'unique cells', used[tk], 'lift', out_lift[tk], 'p', out_p[tk], '| mean top%', mean_rank[tk], 'p', mean_rank_p[tk])
    known = [dict(name=s[0], body=s[1], listed_by=s[2], lat=s[3], lon=s[4], coord_source=s[5],
                  top_percent_science=ranks[s[0]]) for s in SITES]
    best = max(((tk, mk) for tk in out_lift for mk in out_lift[tk]), key=lambda k: out_lift[k[0]][k[1]])
    out = dict(demo=False, top_fraction=TOP, lift=out_lift, p_values=out_p, p_value=out_p[best[0]][best[1]],
               p_value_note=f'p_value = for the highest Lift ({best[0]} / {best[1]}); all in p_values',
               mean_top_percent=mean_rank, mean_top_percent_p=mean_rank_p,
               mean_top_percent_note='Mean "top X%" of the known-site cells (random cells average about 50%); p = share of random sets with a mean as good or better.',
               n_random=N_RANDOM, unique_cells_per_target=used, known_sites=known, excluded=EXCLUDED,
               method='Lift = share of known-site cells in the top 10% of land cells / 0.10. Moon targets use Moon analogs, '
                      'Mars targets use Mars analogs; USGS sites without a target body count for both. Sites sharing a '
                      '0.5-deg cell count once. p = share of 1000 random sets of the same number of land cells with Lift >= observed.')
    (SITE_DATA / 'validation.json').write_text(json.dumps(out, indent=1))
    (DATA / 'validation.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
