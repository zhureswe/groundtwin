# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Rayleigh smoothness threshold h = lambda / (8 cos theta) for RCM (real scene incidence angles) and Mini-RF."""
import json
import math
from common import DATA, SITE_DATA

RCM_CM, MINIRF_CM, MINIRF_INC = 5.55, 12.6, 48.0


def rayleigh(lam_cm, inc_deg):
    return lam_cm / (8 * math.cos(math.radians(inc_deg)))


def main():
    e = json.loads((DATA / 'earth_cpr.json').read_text())
    sites = [dict(site=s['site'], cls=s['cls'], inc_mean_deg=round(s['inc_mean'], 1), h_cm=round(rayleigh(RCM_CM, s['inc_mean']), 2))
             for s in e['sites']]
    lo, hi = e['inc_range']
    out = dict(demo=False, formula='h = lambda / (8 cos theta)',
               rcm=dict(wavelength_cm=RCM_CM, sites=sites, h_cm_at_filter_limits={str(lo): round(rayleigh(RCM_CM, lo), 2), str(hi): round(rayleigh(RCM_CM, hi), 2)}),
               minirf=dict(wavelength_cm=MINIRF_CM, incidence_deg=MINIRF_INC, h_cm=round(rayleigh(MINIRF_CM, MINIRF_INC), 2)),
               interpretation=('Surfaces with height variations below h look smooth to the radar. Mini-RF needs larger roughness '
                               'elements than RCM to look rough, so absolute CPR values are not compared across the two radars: '
                               'we compare the order of classes and the inside/outside contrast. This is an approximate '
                               'calibration; no conversion factor between C- and S-band CPR is claimed. A future step is an '
                               'S-band Earth reference, e.g. from NISAR.'),
               note='inc_mean_deg = mean local incidence angle over the site box before the 30-60 deg filter (from earth_cpr.json).')
    (SITE_DATA / 'wavelength.json').write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ('rcm', 'minirf')}, indent=1))


if __name__ == '__main__':
    main()
