# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Compact-polarimetry m-chi and degree of polarization (DOP):
Earth from RCM (rr, rl, rrrl) for the T1 sites; Moon from Mini-RF Stokes mosaics (m, S1, S4) for crater floors.
Tests the CPR > 1 and DOP < 0.13 criterion (Sinha et al. 2026, Chandrayaan-2 DFSAR) on both."""
import importlib
import json
import os
import numpy as np
import pyproj
import rioxarray as rxr
from shapely.geometry import box
from shapely.ops import transform
from common import DATA, RAW, SITE_DATA

earth = importlib.import_module('01_earth_radar')
moon = importlib.import_module('02_moon_radar')
os.environ['AWS_NO_SIGN_REQUEST'] = 'YES'

CPR_MIN, DOP_MAX = 1.0, 0.13
CONVENTION = ('Circular basis, block means (5x5) of RR, RL and the cross term RRRL = <E_R E_L*> (RCM band 1 = Re, band 2 = Im). '
              'S0 = RR + RL, S3 = RL - RR (opposite minus same sense), S1 = 2 Re, S2 = 2 Im; m = sqrt(S1^2+S2^2+S3^2)/S0; '
              'sin(2chi) = -S3/(m S0); CPR = (S0 - S3)/(S0 + S3) = RR/RL. Mini-RF: m = M mosaic, sin(2chi) = -S4/(m S1).')
GOLDEN = dict(earth=['columbia_icefield', 'clemenceau_icefield', 'edziza_lava_field', 'nisgaa_lava_bed'],
              moon=['Shackleton', 'Faustini'])


def summarise(cpr, m, s2c):
    ok = np.isfinite(cpr) & np.isfinite(m) & np.isfinite(s2c)
    cpr, m, s2c = cpr[ok], m[ok], s2c[ok]
    chi = np.degrees(np.arcsin(np.clip(s2c, -1, 1)) / 2)
    return dict(n=int(ok.sum()), cpr_median=float(np.median(cpr)), dop_median=float(np.median(m)),
                chi_median_deg=float(np.median(chi)), frac_cpr_gt1=float((cpr > CPR_MIN).mean()),
                frac_dop_lt013=float((m < DOP_MAX).mean()), frac_criterion=float(((cpr > CPR_MIN) & (m < DOP_MAX)).mean()))


def read_bands(url, bbox):
    da = rxr.open_rasterio(url, masked=True)
    tr = pyproj.Transformer.from_crs(4326, da.rio.crs, always_xy=True)
    return da.rio.clip_box(*transform(tr.transform, box(*bbox)).bounds).values.astype('f8')


def earth_site(s):
    bbox = earth.site_bbox(s['lon'], s['lat'], earth.SITES[s['site']][3])
    items = [i for i in earth.find_items(bbox) if i.properties['datetime'][:10] == s['date'] and 'rrrl' in i.assets]
    for it in items:
        try:
            rr, rl, inc = (earth.read_clip(it.assets[k].href, bbox) for k in ('rr', 'rl', 'local_inc_angle'))
            x = read_bands(it.assets['rrrl'].href, bbox)
        except Exception as e:
            print('   read failed', str(e)[:80]); continue
        n0 = min(a.shape[0] for a in (rr, rl, x[0], inc)); n1 = min(a.shape[1] for a in (rr, rl, x[0], inc))
        rr, rl, re, im, inc = rr[:n0, :n1], rl[:n0, :n1], x[0][:n0, :n1], x[1][:n0, :n1], inc[:n0, :n1]
        valid = np.isfinite(rr) & np.isfinite(rl) & np.isfinite(re) & np.isfinite(im) & (rr > 0) & (rl > 0)
        if valid.mean() < 0.6:   # same coverage rule as T1, before the incidence-angle filter
            continue
        valid &= (inc >= earth.INC_RANGE[0]) & (inc <= earth.INC_RANGE[1])
        RR, RL, RE, IM = (earth.block_mean(np.where(valid, a, np.nan)) for a in (rr, rl, re, im))
        if np.isfinite(RR / RL).sum() < 20:
            continue
        coh = np.hypot(RE, IM) / np.sqrt(RR * RL)
        S0, S3, S1, S2 = RR + RL, RL - RR, 2 * RE, 2 * IM
        m = np.sqrt(S1 ** 2 + S2 ** 2 + S3 ** 2) / S0
        out = summarise(RR / RL, m, -S3 / (m * S0))
        out.update(site=s['site'], cls=s['cls'], date=s['date'], coherence_median=float(np.nanmedian(coh)),
                   coherence_frac_gt1=float(np.nanmean(coh > 1)))
        return out
    return None


def moon_strips():
    rd = lambda k: np.fromfile(RAW / 'minirf' / f'{k}_128ppd_south80.img', dtype='<f4').reshape(moon.NROW, moon.NCOL)
    m, s1, s4, cpr = rd('m'), rd('s1'), rd('s4'), rd('cpr')
    bad = (m < 0) | (m > 1.5) | (s1 <= 0) | (cpr < 0) | (cpr > 10)
    return {k: np.where(bad, np.nan, v) for k, v in dict(m=m, s1=s1, s4=s4, cpr=cpr).items()}


def moon_target(t, dem, st):
    r = t['diameter_km'] / 2
    w = moon.window(dem, t['lat'], t['lon'], moon.OUT_R[1] * r)
    lat, lon = w['latlon']
    dist = moon.haversine(t['lat'], t['lon'], lat, lon)
    res = {}
    for zone, mask in (('inside', dist < moon.IN_R * r), ('outside', (dist > moon.OUT_R[0] * r) & (dist < moon.OUT_R[1] * r))):
        v = {k: moon.sample_cpr(a, lat[mask], lon[mask]) for k, a in st.items()}
        res[zone] = summarise(v['cpr'], v['m'], -v['s4'] / (v['m'] * v['s1']))
    cpr_check = (st['s1'] - st['s4']) / (st['s1'] + st['s4'])
    res['cpr_from_stokes_vs_mosaic_median_ratio'] = float(np.nanmedian(
        moon.sample_cpr(cpr_check, lat[dist < r], lon[dist < r]) / moon.sample_cpr(st['cpr'], lat[dist < r], lon[dist < r])))
    return dict(target=t['target'], tmax_in_k=t['tmax_in_k'], ies=t['ies'], **res)


def main():
    e = json.loads((DATA / 'earth_cpr.json').read_text())
    earth_rows = []
    for s in e['sites']:
        r = earth_site(s)
        if r:
            earth_rows.append(r)
            print(f"{r['site']:20s} {r['cls']:10s} CPR {r['cpr_median']:.2f} DOP {r['dop_median']:.2f} chi {r['chi_median_deg']:+.1f} "
                  f"CPR>1 {r['frac_cpr_gt1']:.0%} DOP<.13 {r['frac_dop_lt013']:.0%} both {r['frac_criterion']:.1%} coh {r['coherence_median']:.2f}", flush=True)
    classes = {}
    for c in ('smooth', 'rough_rock', 'ice'):
        rows = [r for r in earth_rows if r['cls'] == c]
        if rows:
            wsum = sum(r['n'] for r in rows)
            classes[c] = {k: sum(r[k] * r['n'] for r in rows) / wsum for k in ('frac_cpr_gt1', 'frac_dop_lt013', 'frac_criterion')}
            classes[c].update(dop_median_of_sites=float(np.median([r['dop_median'] for r in rows])),
                              chi_median_of_sites_deg=float(np.median([r['chi_median_deg'] for r in rows])), n=wsum)
    mt = json.loads((DATA / 'moon_targets.json').read_text())
    st, dem = moon_strips(), moon.load_lola()
    moon.check_lola_orientation(dem)
    moon_rows = [moon_target(t, dem, st) for t in mt['targets']]
    for r in moon_rows:
        i = r['inside']
        print(f"{r['target']:14s} in: CPR {i['cpr_median']:.2f} DOP {i['dop_median']:.2f} chi {i['chi_median_deg']:+.1f} "
              f"CPR>1 {i['frac_cpr_gt1']:.1%} DOP<.13 {i['frac_dop_lt013']:.1%} both {i['frac_criterion']:.2%} | out both {r['outside']['frac_criterion']:.2%}"
              f" | stokes/mosaic CPR {r['cpr_from_stokes_vs_mosaic_median_ratio']:.3f}")
    out = dict(demo=False, criterion=dict(cpr_min=CPR_MIN, dop_max=DOP_MAX,
               source='Sinha et al. 2026, npj Space Exploration (Chandrayaan-2 DFSAR, L-band); applied here to C-band (RCM) and S-band (Mini-RF)'),
               convention=CONVENTION, earth=dict(sites=earth_rows, classes=classes),
               moon=dict(targets=moon_rows, sources='LRO Mini-RF global mosaics 128 ppd: M (degree of polarization), S1, S4, CPR'),
               golden_case=GOLDEN,
               note='Fractions are of 5x5-block cells (Earth) or 80 m LOLA-grid samples of the 128 ppd Mini-RF mosaics (Moon).')
    (SITE_DATA / 'polarimetry.json').write_text(json.dumps(out, indent=1))
    (DATA / 'polarimetry.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
