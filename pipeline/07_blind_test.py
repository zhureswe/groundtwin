# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Blind leave-one-out test: hide each known analog cell, build a profile from the others (mean percentiles),
rank the hidden cell among all Earth land cells. 'Recognised' = in the top 10%."""
import importlib
import json
import numpy as np
from scipy.stats import binom
from common import SITE_DATA

ae = importlib.import_module('04_analog_engine')
val = importlib.import_module('05_validation')
TOP = 0.10
GROUPS = {'mars': ('mars', 'any'), 'all': ('moon', 'mars', 'any')}


def loo(P, cells, names):
    rows = []
    for h in cells:
        rest = [c for c in cells if c != h]
        R = ae.top_rank(1 - np.abs(P - P[rest].mean(0)).mean(1))   # equal-weight similarity to the leave-out profile
        rows.append(dict(sites=names[h], top_percent=round(float(R[h] * 100), 1), recognised=bool(R[h] <= TOP)))
    k, n = sum(r['recognised'] for r in rows), len(rows)
    return dict(recognised=k, total=n, p_value_binomial=round(float(binom.sf(k - 1, n, TOP)), 5),
                expected_by_chance=round(n * TOP, 1), median_top_percent=round(float(np.median([r['top_percent'] for r in rows])), 1),
                rows=sorted(rows, key=lambda r: r['top_percent']))


def main():
    lon, lat, P = val.load_grid()
    out = dict(demo=False, top_fraction=TOP, groups={},
               method='For each known-analog cell: profile = mean percentile vector of the other cells in the group, '
                      'similarity = 1 - mean |p - t| over 7 criteria (equal weights), rank among all land cells. '
                      'Recognised = top 10%. p = binomial probability of at least that many by chance (10% each). '
                      'Sites sharing a 0.5-deg cell count once.')
    for g, bodies in GROUPS.items():
        names = {}
        for s in val.SITES:
            if s[1] in bodies:
                names.setdefault(ae.cell_index(lon, lat, s[4], s[3]), []).append(s[0])
        res = loo(P, sorted(names), {c: ' / '.join(v) for c, v in names.items()})
        out['groups'][g] = res
        print(g, f"recognised {res['recognised']} of {res['total']} (chance {res['expected_by_chance']}, p = {res['p_value_binomial']}),"
                 f" median top {res['median_top_percent']}%")
        for r in res['rows']:
            print('   ', r['top_percent'], r['recognised'], r['sites'])
    (SITE_DATA / 'blind_test.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
