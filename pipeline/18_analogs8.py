# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""The 8 places of the Analogs page (version B, chosen by Aruna; same as the globe and the Framer site):
  famous — 4 famous field analogs from famous_analogs.json: Atacama, Death Valley, Devon Island, Utah;
  ours   — Mangystau (famous_analogs.json) + the formula's best places from country_top.json: Moon #1, Moon #2, Mars #1.
All scores come from those files (Analog Engine, Science weights) -> docs/data/analogs8.json."""
import json
from common import SITE_DATA

FAMOUS = ['atacama', 'death-valley', 'devon-island', 'utah']
OURS_TOP = dict(moon_south_pole=2, mars_gale=1)        # how many country_top places per target


def load(name):
    return json.loads((SITE_DATA / f'{name}.json').read_text(encoding='utf-8'))


def from_famous(s):
    v = s['targets'][s['primary']]
    return dict(id=s['id'], name=s['name'], country=s['country'], target=s['primary'], lat=s['lat'], lon=s['lon'], coord_source=s['coord_source'],
                tag=s['tag'], blurb=s['blurb'], features=s['features'], profile=v['profile'], match=v['match'], partly=v['partly'],
                differ=v['differ'], **{k: v[k] for k in ('S', 'position', 'n_cells', 'top_percent')})


def from_country_top(r, tk):
    return dict(name=f"{r['province']}, {r['country']}", country=r['country'], target=tk, lat=r['lat'], lon=r['lon'],
                coord_source='0.5° grid cell centre; place name: GeoNames (country_top.json)', near=r['near'],
                **{k: r[k] for k in ('S', 'position', 'n_cells', 'top_percent', 'features', 'profile', 'match', 'partly', 'differ')})


def main():
    fam, ct = load('famous_analogs'), load('country_top')
    sites = {s['id']: s for s in fam['sites']}
    famous = [from_famous(sites[i]) for i in FAMOUS]
    ours = [from_famous(sites['mangystau'])] + [from_country_top(r, tk) for tk, k in OURS_TOP.items() for r in ct['top'][tk][:k]]
    out = dict(demo=False, mode='science', n_cells=fam['n_cells'],
               rule_famous='Famous field analogs used for Moon and Mars training and tests, each scored on its own 0.5° cell for its main target '
                           '(famous_analogs.json).',
               rule_ours='Mangystau, our Kazakhstan case study (mean of its 6 site cells), and the formula\'s best places by S: the two best Moon '
                         'cells and the best Mars cell, one per country, at least 600 km apart (country_top.json).',
               famous=famous, ours=ours)
    (SITE_DATA / 'analogs8.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    for x in famous + ours:
        print(f"{x['name']:34s} {x['target']:16s} S {x['S']}  #{x['position']}  top {x['top_percent']}%")


if __name__ == '__main__':
    main()
