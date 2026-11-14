# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Moon Radar Twin: lunar south-pole targets (IAU Gazetteer) + Mini-RF CPR, Diviner Tmax, LOLA slope."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RAW, DATA = ROOT / 'raw', ROOT / 'data'
R_MOON = 1737.4  # km

IAU_SHP = RAW / 'iau' / 'MOON_nomenclature_center_pts.shp'
MINIRF = RAW / 'minirf' / 'cpr_128ppd_south80.img'
DIVINER = RAW / 'diviner' / 'dlre_prp_south.tab'
LOLA = RAW / 'lola' / 'ldem_80s_80m_float.img'

SOURCES = {
    'targets': 'IAU Gazetteer of Planetary Nomenclature, MOON_nomenclature_center_pts (https://planetarynames.wr.usgs.gov)',
    'cpr': 'LRO Mini-RF S-band global CPR mosaic 128 ppd, global_cpr_128ppd_simp_0c (PDS lro-l-mrflro-5-global-mosaic-v1)',
    'tmax': 'LRO Diviner Polar Resource Product, dlre_prp_south.tab (PDS urn:nasa:pds:lro_diviner_derived1, data_derived_prp)',
    'slope': 'LRO LOLA polar DEM ldem_80s_80m_float (PDS lro-l-lola-3-rdr-v1, lola_gdr/polar)',
}
PSR_CRATERS = ['Shackleton', 'Haworth', 'Shoemaker', 'Faustini', 'Cabeus', 'de Gerlache', 'Sverdrup', 'Nobile']
# Artemis III candidate regions (NASA, Oct 2024) are not IAU features; each is tied to its named IAU anchor.
ARTEMIS_REGIONS = {
    'Peak near Cabeus B': 'Cabeus B', 'Haworth': 'Haworth', 'Malapert Massif': 'Mons Malapert',
    'Mons Mouton Plateau': 'Mons Mouton', 'Mons Mouton': 'Mons Mouton', 'Nobile Rim 1': 'Nobile',
    'Nobile Rim 2': 'Nobile', 'de Gerlache Rim 2': 'de Gerlache', 'Slater Plain': 'Slater',
}
IN_R, OUT_R = 0.8, (1.2, 2.0)   # floor and surrounding ring, in crater radii
CPR_RATIO_MIN = 1.2             # IES: CPR_in / CPR_out threshold
TMAX_MAX = 110.0                # IES: K, water-ice cold-trap temperature

# Mini-RF strip: last 1280 lines of the 128 ppd simple-cylindrical mosaic (lat -80..-90)
PPD, NCOL, NROW, MISSING = 128, 46080, 1280, -1e300
# LOLA polar stereographic grid (dsmap_polar.cat)
N_LOLA, SCALE_LOLA = 7600, 0.08  # pixels, km/pixel
LON_SIGN = -1                    # verified against crater floors, see check_lola_orientation()


def haversine(lat0, lon0, lat, lon):
    p0, p, dl = np.radians(lat0), np.radians(lat), np.radians(lon - lon0)
    a = np.sin((p - p0) / 2) ** 2 + np.cos(p0) * np.cos(p) * np.sin(dl / 2) ** 2
    return 2 * R_MOON * np.arcsin(np.sqrt(a))


def stereo_xy(lat, lon):
    r = 2 * R_MOON * np.tan(np.radians(90 + lat) / 2)
    lam = np.radians(LON_SIGN * lon)
    return r * np.sin(lam), r * np.cos(lam)


def stereo_latlon(x, y):
    lat = -90 + np.degrees(2 * np.arctan(0.5 * np.hypot(x, y) / R_MOON))
    return lat, LON_SIGN * np.degrees(np.arctan2(x, y))


def build_targets():
    g = gpd.read_file(IAU_SHP).set_index('name')
    feats = list(dict.fromkeys(PSR_CRATERS + list(ARTEMIS_REGIONS.values())))
    rows = []
    for n in feats:
        f = g.loc[n]
        rows.append(dict(target=n, psr_crater=n in PSR_CRATERS,
                         artemis_regions=[r for r, a in ARTEMIS_REGIONS.items() if a == n],
                         feature_type=f.type, lat=round(f.center_lat, 4),
                         lon=round((f.center_lon + 180) % 360 - 180, 4), diameter_km=round(f.diameter, 2),
                         iau_link=f.link))
    df = pd.DataFrame(rows)
    df.assign(artemis_regions=df.artemis_regions.str.join('; '), source=SOURCES['targets']) \
      .to_csv(DATA / 'moon_targets.csv', index=False)
    return df


def load_lola():
    return np.memmap(LOLA, dtype='<f4', mode='r', shape=(N_LOLA, N_LOLA))


def load_minirf():
    a = np.fromfile(MINIRF, dtype='<f4').reshape(NROW, NCOL)
    return np.where((a > MISSING) & (a >= 0) & (a < 10), a, np.nan)


def load_diviner():
    cache = RAW / 'diviner' / 'prp_south_80.npz'
    if not cache.exists():
        df = pd.read_csv(DIVINER, skipinitialspace=True, usecols=['tri_clon', 'tri_clat', 'temp_max', 'temp_avg', 'ice_depth'])
        df = df[df.tri_clat < -79]
        np.savez(cache, **{c: df[c].to_numpy('f4') for c in df.columns})
    return dict(np.load(cache))


def check_lola_orientation(dem):
    """Crater centres must sit lower than their rims; prints mean floor-minus-rim height for both signs."""
    global LON_SIGN
    craters = [('Shackleton', -89.67, 129.78, 10.5), ('Cabeus', -85.33, -42.13, 50.3), ('Haworth', -87.45, -5.17, 25.7)]
    score = {}
    for s in (1, -1):
        LON_SIGN = s
        d = []
        for _, lat, lon, r in craters:
            w = window(dem, lat, lon, 1.5 * r)
            dist = haversine(lat, lon, *w['latlon'])
            d.append(np.nanmedian(w['h'][dist < 0.5 * r]) - np.nanmedian(w['h'][(dist > 1.1 * r) & (dist < 1.4 * r)]))
        score[s] = float(np.mean(d))
    LON_SIGN = min(score, key=score.get)
    print(f'LOLA orientation check (floor - rim, km): {score} -> LON_SIGN = {LON_SIGN}')
    return score


def window(dem, lat, lon, half_km):
    x, y = stereo_xy(lat, lon)
    ci, cj = x / SCALE_LOLA + N_LOLA / 2 - 0.5, y / SCALE_LOLA + N_LOLA / 2 - 0.5
    h = int(half_km / SCALE_LOLA) + 2
    i0, i1 = max(int(ci) - h, 0), min(int(ci) + h, N_LOLA)
    j0, j1 = max(int(cj) - h, 0), min(int(cj) + h, N_LOLA)
    ii, jj = np.meshgrid(np.arange(i0, i1), np.arange(j0, j1))
    xs, ys = (ii - N_LOLA / 2 + 0.5) * SCALE_LOLA, (jj - N_LOLA / 2 + 0.5) * SCALE_LOLA
    return dict(h=np.asarray(dem[j0:j1, i0:i1], dtype='f8'), latlon=stereo_latlon(xs, ys))


def slope_deg(h_km):
    gy, gx = np.gradient(h_km * 1000, SCALE_LOLA * 1000)
    return np.degrees(np.arctan(np.hypot(gx, gy)))


def sample_cpr(cpr, lat, lon):
    row = np.floor((-80 - lat) * PPD).astype(int)
    col = np.floor((lon + 180) * PPD).astype(int) % NCOL
    ok = (row >= 0) & (row < NROW)
    out = np.full(lat.shape, np.nan)
    out[ok] = cpr[row[ok], col[ok]]
    return out


def med(a):
    a = a[np.isfinite(a)]
    return float(np.median(a)) if a.size else None


def measure(t, dem, cpr, div):
    r = t.diameter_km / 2
    w = window(dem, t.lat, t.lon, OUT_R[1] * r)
    lat, lon = w['latlon']
    dist = haversine(t.lat, t.lon, lat, lon)
    inside, ring = dist < IN_R * r, (dist > OUT_R[0] * r) & (dist < OUT_R[1] * r)
    c, s = sample_cpr(cpr, lat, lon), slope_deg(w['h'])
    dd = haversine(t.lat, t.lon, div['tri_clat'], div['tri_clon'])
    din = dd < IN_R * r
    tmax, ice = div['temp_max'][din], div['ice_depth'][din]
    return dict(cpr_in=med(c[inside]), cpr_out=med(c[ring]),
                cpr_coverage_in=float(np.isfinite(c[inside]).mean()),
                slope_in_deg=med(s[inside]), slope_out_deg=med(s[ring]),
                tmax_in_k=med(tmax), tavg_in_k=med(div['temp_avg'][din]),
                frac_floor_tmax_below_110k=float((tmax < TMAX_MAX).mean()) if tmax.size else None,
                frac_floor_ice_stable_upper_3m=float((ice >= 0).mean()) if ice.size else None,
                n_diviner_floor=int(din.sum()))


def score(df):
    craters = df.feature_type.str.contains('Crater|Satellite')
    slope_ref = float(df.loc[craters, 'slope_in_deg'].median())
    df['cpr_ratio'] = df.cpr_in / df.cpr_out
    df['ies_cpr'] = (df.cpr_ratio > CPR_RATIO_MIN).astype(int)
    df['ies_smooth'] = (df.slope_in_deg < slope_ref).astype(int)
    df['ies_cold'] = (df.tmax_in_k < TMAX_MAX).astype(int)
    df['ies'] = (df.ies_cpr + df.ies_smooth + df.ies_cold).where(craters)
    return slope_ref


def plot_vs_earth(df):
    earth = json.loads((DATA / 'earth_cpr.json').read_text())['classes']
    colors = {'smooth': '#8C9BAB', 'rough_rock': '#D9822B', 'ice': '#4FB3D9'}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 5), gridspec_kw={'width_ratios': [1, 2.4]}, sharey=True)
    for i, (k, v) in enumerate(earth.items()):
        a1.add_patch(plt.Rectangle((i - 0.3, v['p25']), 0.6, v['p75'] - v['p25'], color=colors[k], alpha=0.8))
        a1.plot([i - 0.3, i + 0.3], [v['median']] * 2, 'k', lw=2)
    a1.set_xticks(range(len(earth)), list(earth)); a1.set_xlim(-0.6, len(earth) - 0.4)
    a1.set_title('Earth: RCM C-band (5.5 cm)\nmedian and IQR by class'); a1.set_ylabel('CPR')
    d = df.dropna(subset=['cpr_in']).sort_values('cpr_in')
    x = np.arange(len(d))
    a2.vlines(x, d.cpr_out, d.cpr_in, color='#999')
    a2.scatter(x, d.cpr_out, c='#8C9BAB', label='outside (1.2-2 R)', zorder=3)
    a2.scatter(x, d.cpr_in, c='#4FB3D9', edgecolor='k', label='inside (< 0.8 R)', zorder=3)
    a2.set_xticks(x, d.target, rotation=45, ha='right')
    a2.set_title('Moon: Mini-RF S-band (12.6 cm)\ncrater floor vs surroundings')
    for a in (a1, a2):
        a.axhline(1, ls='--', c='k', lw=0.8)
    a2.legend(); fig.tight_layout()
    fig.savefig(DATA / 'moon_vs_earth_cpr.png', dpi=200); plt.close(fig)


def plot_map(df, dem):
    step = 8
    h = np.asarray(dem[::step, ::step])
    ext = N_LOLA * SCALE_LOLA / 2
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(h, cmap='gray', extent=[-ext, ext, ext, -ext])
    for t in df.itertuples():
        x, y = stereo_xy(t.lat, t.lon)
        ax.add_patch(plt.Circle((x, y), t.diameter_km / 2, fill=False, ec='#4FB3D9' if t.psr_crater else '#D9822B', lw=1.5))
        ax.annotate(t.target, (x, y), color='w', fontsize=8, ha='center', va='center')
    ax.set_xlim(-ext, ext); ax.set_ylim(ext, -ext)
    ax.set_xlabel('km (polar stereographic)'); ax.set_title('Lunar south pole (LOLA elevation) - GroundTwin targets')
    fig.tight_layout(); fig.savefig(DATA / 'moon_south_pole_map.png', dpi=200); plt.close(fig)


def main():
    df = build_targets()
    dem = load_lola()
    orientation = check_lola_orientation(dem)
    cpr, div = load_minirf(), load_diviner()
    df = pd.concat([df, pd.DataFrame([measure(t, dem, cpr, div) for t in df.itertuples()])], axis=1)
    slope_ref = score(df)
    print(df[['target', 'cpr_in', 'cpr_out', 'cpr_ratio', 'slope_in_deg', 'tmax_in_k',
              'frac_floor_ice_stable_upper_3m', 'ies']].round(3).to_string())
    plot_vs_earth(df); plot_map(df, dem)
    out = dict(
        sources=SOURCES,
        method=dict(inside=f'< {IN_R} R', outside=f'{OUT_R[0]}-{OUT_R[1]} R', statistic='median',
                    ies=f'[CPR_in/CPR_out > {CPR_RATIO_MIN}] + [median floor slope < {slope_ref:.2f} deg '
                        f'(median over craters)] + [median floor Tmax < {TMAX_MAX} K]',
                    ies_applies_to='craters only (mountains: not applicable)',
                    interpretation='IES = compatible with ice, not proof of ice',
                    lola_orientation_check_km=orientation, lon_sign=LON_SIGN),
        slope_reference_deg=slope_ref,
        artemis_regions_note='Artemis III region centres are not IAU features; values are for the named IAU anchor.',
        targets=json.loads(df.to_json(orient='records')),
    )
    (DATA / 'moon_targets.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
