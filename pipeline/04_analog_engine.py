# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Analog Engine: 0.5-degree land grid of 7 physical features (NASA data via Earth Engine) -> percentiles,
similarity S to Moon/Mars target profiles, top-10 places per target and mode, Mangystau rank."""
import json
import numpy as np
from scipy.stats import rankdata
from common import DATA, RAW, SITE_DATA, YEARS, ee_init

CELL = 0.5
LAT_N, LAT_S = 90, -60          # Antarctica excluded (polar data quality, no land-analog interest for this grid)
W, H = int(360 / CELL), int((LAT_N - LAT_S) / CELL)
FEATURES = ['aridity', 'barren', 'thermal_range', 'cold', 'dust', 'roughness', 'elevation']
SIGN = dict(aridity=-1, barren=-1, thermal_range=1, cold=-1, dust=1, roughness=1, elevation=1)  # extreme direction
NODATA = -9999
MIN_SEP_KM = 600                # top-10 places kept at least this far apart (same rule as the website)
SOURCES = dict(
    aridity='NASA GPM IMERG V07 monthly precipitation, mean annual total (mm)',
    barren='MODIS MOD13A2 NDVI, yearly maximum averaged',
    thermal_range='MODIS MOD11A2 LST day minus night, mean (K)',
    cold='MODIS MOD11A2 LST night, 5th percentile (K)',
    dust='MODIS MOD08_M3 AOD 550 nm, Dark Target + Deep Blue combined, mean',
    roughness='USGS GMTED2010 (std of elevation within 7.5-arcsec cells), cell mean (m)',
    elevation='USGS GMTED2010 mean elevation (m)',
    land='MODIS MCD12Q1 2020 LC_Type1 != 17 (water), majority at 0.5 deg',
)


def ee_layers(ee):
    y0, y1 = f'{YEARS[0]}-01-01', f'{YEARS[1] + 1}-01-01'
    lst = ee.ImageCollection('MODIS/061/MOD11A2').filterDate(y0, y1)
    ndvi_years = ee.List.sequence(*YEARS).map(lambda y: ee.ImageCollection('MODIS/061/MOD13A2').select('NDVI')
                                              .filter(ee.Filter.calendarRange(y, y, 'year')).max())
    gmted = ee.Image('USGS/GMTED2010_FULL')
    return dict(
        aridity=ee.ImageCollection('NASA/GPM_L3/IMERG_MONTHLY_V07').filterDate(y0, y1).select('precipitation').mean().multiply(24 * 365.25),
        barren=ee.ImageCollection(ndvi_years).mean().multiply(0.0001),
        thermal_range=lst.map(lambda i: i.select('LST_Day_1km').subtract(i.select('LST_Night_1km'))).mean().multiply(0.02),
        cold=lst.select('LST_Night_1km').reduce(ee.Reducer.percentile([5])).multiply(0.02),
        dust=ee.ImageCollection('MODIS/061/MOD08_M3').filterDate(y0, y1).select('AOD_550_Dark_Target_Deep_Blue_Combined_Mean_Mean').mean().multiply(0.001),
        roughness=gmted.select('std'),
        elevation=gmted.select('mea'),
        land=ee.ImageCollection('MODIS/061/MCD12Q1').filterDate('2020-01-01', '2021-01-01').first().select('LC_Type1').neq(17),
    )


def fetch(ee, img):
    grid = dict(dimensions=dict(width=W, height=H), crsCode='EPSG:4326',
                affineTransform=dict(scaleX=CELL, shearX=0, translateX=-180, shearY=0, scaleY=-CELL, translateY=LAT_N))
    a = ee.data.computePixels(dict(expression=img.rename('v').unmask(NODATA).toFloat(), fileFormat='NUMPY_NDARRAY', grid=grid))['v']
    return np.where(a == NODATA, np.nan, a.astype('f8'))


def build_grid():
    cache = RAW / 'analog_raw.npz'
    if cache.exists():
        return dict(np.load(cache))
    ee = ee_init()
    raw = {}
    for k, img in ee_layers(ee).items():
        raw[k] = fetch(ee, img)
        print(f'{k}: valid {np.isfinite(raw[k]).mean():.2f}', flush=True)
    np.savez_compressed(cache, **raw)
    return raw


def percentiles(raw):
    lon = -180 + CELL / 2 + CELL * np.arange(W)
    lat = LAT_N - CELL / 2 - CELL * np.arange(H)
    LON, LAT = np.meshgrid(lon, lat)
    land = raw['land'] == 1
    core = land & np.isfinite(raw['thermal_range']) & np.isfinite(raw['aridity']) & np.isfinite(raw['elevation'])
    p, imputed = {}, {}
    for f in FEATURES:
        v = raw[f][core] * SIGN[f]
        ok = np.isfinite(v)
        q = np.full(v.shape, 0.5)               # missing values -> neutral percentile, counted below
        q[ok] = (rankdata(v[ok]) - 1) / (ok.sum() - 1)
        p[f], imputed[f] = q, int((~ok).sum())
    return LON[core], LAT[core], p, imputed, {f: raw[f][core] for f in FEATURES}


def haversine(lat1, lon1, lat2, lon2):
    r = np.radians
    a = np.sin(r(lat2 - lat1) / 2) ** 2 + np.cos(r(lat1)) * np.cos(r(lat2)) * np.sin(r(lon2 - lon1) / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def similarity(P, profile, weights):
    t = np.array([profile[f] for f in FEATURES])
    w = np.array([weights.get(f, 0) for f in FEATURES])
    return ((1 - np.abs(P - t)) * w).sum(1) / w.sum()


def top_rank(S):
    """Fraction of land cells with a higher score (0 = best cell on Earth)."""
    return 1 - (rankdata(S, method='max') - 1) / (len(S) - 1)


def top_places(S, lon, lat, n=10):
    picked = []
    for i in np.argsort(-S):
        if all(haversine(lat[i], lon[i], lat[j], lon[j]) > MIN_SEP_KM for j in picked):
            picked.append(i)
        if len(picked) == n:
            break
    return picked


def cell_index(lon, lat, qlon, qlat):
    """Index of the land cell containing (qlat, qlon), else the nearest land cell."""
    d = haversine(qlat, qlon, lat, lon)
    return int(np.argmin(d))


def main():
    raw = build_grid()
    lon, lat, p, imputed, values = percentiles(raw)
    P = np.stack([p[f] for f in FEATURES], 1)
    print(f'land cells: {len(lon)}; imputed (missing -> 0.5): {imputed}')
    T = json.loads((SITE_DATA / 'targets.json').read_text())

    cells = [[round(float(a), 2), round(float(b), 2)] + [round(float(x), 3) for x in row] for a, b, row in zip(lon, lat, P)]
    (SITE_DATA / 'analog_grid.json').write_text(json.dumps(dict(
        demo=False, cell_deg=CELL, features=FEATURES, cells=cells, sources=SOURCES, period=f'{YEARS[0]}-{YEARS[1]}',
        lat_range=[LAT_S, LAT_N], antarctica='excluded', imputed_missing_to_0_5=imputed), separators=(',', ':')))

    mgs = json.loads((SITE_DATA / 'mangystau.json').read_text(encoding='utf-8'))
    mgs_cells = sorted({cell_index(lon, lat, s['lon'], s['lat']) for s in mgs['places']})
    top, mgs_rank = {}, {}
    for tk, t in T['targets'].items():
        top[tk], mgs_rank[tk] = {}, {}
        for mk, m in T['modes'].items():
            S = similarity(P, t['profile'], m['weights'])
            R = top_rank(S)
            top[tk][mk] = [dict(rank=k + 1, lon=round(float(lon[i]), 2), lat=round(float(lat[i]), 2), S=round(float(S[i]), 3),
                                **{f: round(float(p[f][i]), 3) for f in FEATURES}) for k, i in enumerate(top_places(S, lon, lat))]
            mgs_rank[tk][mk] = dict(best_top_percent=round(float(R[mgs_cells].min() * 100), 1),
                                    median_top_percent=round(float(np.median(R[mgs_cells]) * 100), 1))
    out = dict(demo=False, min_separation_km=MIN_SEP_KM, n_cells=len(lon), top10=top,
               mangystau=dict(cells=[[float(lon[i]), float(lat[i])] for i in mgs_cells], rank=mgs_rank))
    (DATA / 'analog_top.json').write_text(json.dumps(out, indent=1))
    (SITE_DATA / 'analog_top.json').write_text(json.dumps(out, separators=(',', ':')))

    mgs['rank_vs_mars'] = {k: mgs_rank[k]['science']['median_top_percent'] for k in ('mars_gale', 'mars_jezero')}
    mgs['rank_note'] = ('Median over the 0.5-deg cells containing the six sites, Science mode: "top X%" of Earth land cells. '
                        'All modes: docs/data/analog_top.json -> mangystau.rank')
    (SITE_DATA / 'mangystau.json').write_text(json.dumps(mgs, indent=1, ensure_ascii=False), encoding='utf-8')
    for tk in T['targets']:
        print(tk, 'Mangystau science:', mgs_rank[tk]['science'], '| #1:', top[tk]['science'][0])


if __name__ == '__main__':
    main()
