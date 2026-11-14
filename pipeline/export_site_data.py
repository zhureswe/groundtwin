# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Copies real pipeline results (data/*.json) into the website data contract (docs/data/*.json, demo=false)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, SITE = ROOT / 'data', ROOT / 'docs' / 'data'


def load(name):
    return json.loads((DATA / name).read_text())


def dump(name, obj):
    (SITE / name).write_text(json.dumps(obj, separators=(',', ':')))
    print('wrote docs/data/' + name)


def earth():
    e = load('earth_cpr.json')
    for s in e['sites']:
        s['n_cells'] = s.pop('n')
    dump('earth_cpr.json', {'demo': False, **e})


def kind(t):
    k = 'PSR crater' if t['psr_crater'] else t['feature_type'].split(',')[0].replace('Satellite Feature', 'Crater')
    return k + (f" · Artemis III: {', '.join(t['artemis_regions'])}" if t['artemis_regions'] else '')


def moon():
    m = load('moon_targets.json')
    src = '; '.join(m['sources'][k] for k in ('cpr', 'tmax', 'slope'))
    targets = []
    for t in m['targets']:
        scored = t['ies'] is not None
        targets.append(dict(
            name=t['target'], kind=kind(t), lat=t['lat'], lon=t['lon'],
            cpr_in=t['cpr_in'], cpr_out=t['cpr_out'], tmax_k=t['tmax_in_k'], slope_deg=t['slope_in_deg'],
            frac_floor_below_110k=t['frac_floor_tmax_below_110k'], n_diviner_floor=t['n_diviner_floor'],
            clues=dict(radar=bool(t['ies_cpr']), smooth=bool(t['ies_smooth']), cold=bool(t['ies_cold'])) if scored else None,
            ies=int(t['ies']) if scored else None, source=src))
    dump('moon_targets.json', dict(demo=False, band='Mini-RF S-band (12.6 cm)', ratio_threshold=1.2,
                                   cold_threshold_k=110, slope_threshold_deg=m['slope_reference_deg'],
                                   coordinates=m['sources']['targets'],
                                   tmax_definition='median of the Diviner annual maximum temperature over the floor zone (r < 0.8 R); '
                                                   '"floor colder than 110 K" = share of those floor samples whose annual maximum stays below 110 K',
                                   targets=targets))


if __name__ == '__main__':
    earth()
    moon()
