# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Creates DEMO JSON files for the GroundTwin website so the interface works before real results exist.

Every file gets "demo": true and the website shows a yellow DEMO banner while any demo file is loaded.
The real pipeline (pipeline/01-05) must OVERWRITE these files with the same structure and "demo": false.
Never submit the project with demo numbers.
"""
import json, math, os, random
import numpy as np
from global_land_mask import globe

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'data')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(42)
random.seed(42)

def dump(name, obj):
    with open(os.path.join(OUT, name), 'w') as f:
        json.dump(obj, f, separators=(',', ':'))
    print('wrote', name)

# ---------- 1. Earth radar reference (same schema as notebook 01 output) ----------
def site(name, cls, lon, lat, med, spread):
    vals = np.clip(rng.lognormal(math.log(med), spread, 4000), 0, 3)
    return dict(site=name, cls=cls, lon=lon, lat=lat, date='2025-02-10', scene='DEMO', winter=True,
                inc_mean=42.0, n_cells=int(vals.size), median=float(np.median(vals)),
                p25=float(np.percentile(vals, 25)), p75=float(np.percentile(vals, 75)),
                frac_gt1=float((vals > 1).mean()),
                hist=np.histogram(np.clip(vals, 0, 2), bins=40, range=(0, 2))[0].tolist())
sites = [
    site('regina_plain', 'smooth', -104.60, 50.55, 0.24, 0.25),
    site('great_sand_hills', 'smooth', -109.30, 50.45, 0.29, 0.28),
    site('athabasca_dunes', 'smooth', -108.75, 59.08, 0.33, 0.3),
    site('nisgaa_lava_bed', 'rough_rock', -128.97, 55.17, 0.58, 0.3),
    site('edziza_lava_field', 'rough_rock', -130.65, 57.70, 0.66, 0.32),
    site('haughton_crater', 'rough_rock', -89.68, 75.38, 0.52, 0.3),
    site('columbia_icefield', 'ice', -117.33, 52.17, 0.78, 0.35),
    site('penny_ice_cap', 'ice', -66.00, 67.25, 0.95, 0.35),
    site('devon_ice_cap', 'ice', -82.00, 75.25, 1.08, 0.35),
]
classes = {}
for c in ['smooth', 'rough_rock', 'ice']:
    s = [x for x in sites if x['cls'] == c]
    classes[c] = dict(median=float(np.mean([x['median'] for x in s])), p25=float(np.mean([x['p25'] for x in s])),
                      p75=float(np.mean([x['p75'] for x in s])), frac_gt1=float(np.mean([x['frac_gt1'] for x in s])),
                      n=sum(x['n_cells'] for x in s))
dump('earth_cpr.json', dict(demo=True, convention='CPR = RR/RL (demo)', look=5, inc_range=[30, 60],
     credit='RADARSAT Constellation Mission Imagery (c) Government of Canada (2025). RADARSAT is an official mark of the Canadian Space Agency.',
     sites=sites, classes=classes))

# ---------- 2. Moon targets (APPROXIMATE positions; replace from IAU Gazetteer) ----------
moon = [
    # name, region type, lat, lon(east), cpr_in, cpr_out, tmax_k, slope_deg
    ('Shackleton', 'PSR crater', -89.67, 129.8, 0.92, 0.61, 88, 6.5),
    ('Haworth', 'Artemis III region / PSR', -87.4, -5.0, 1.05, 0.58, 72, 5.1),
    ('Shoemaker', 'PSR crater', -88.1, 44.9, 0.88, 0.70, 65, 4.2),
    ('Faustini', 'PSR crater', -87.3, 77.0, 0.81, 0.66, 70, 4.8),
    ('Cabeus', 'PSR crater (LCROSS impact)', -85.3, -42.1, 0.97, 0.64, 60, 5.6),
    ('de Gerlache', 'Artemis III region / PSR', -88.5, -87.1, 0.74, 0.69, 95, 7.9),
    ('Sverdrup', 'PSR crater', -88.5, -152.0, 0.71, 0.62, 98, 6.9),
    ('Nobile', 'Artemis III region / PSR', -85.2, 53.5, 0.83, 0.79, 90, 8.4),
    ('Malapert Massif', 'Artemis III region (sunlit)', -86.0, -2.0, 0.58, 0.56, 210, 12.0),
]
slopes = np.median([m[7] for m in moon])
targets = []
for name, kind, lat, lon, ci, co, t, sl in moon:
    clues = dict(radar=bool(ci / co > 1.2), smooth=bool(sl < slopes), cold=bool(t < 110))
    targets.append(dict(name=name, kind=kind, lat=lat, lon=lon, cpr_in=ci, cpr_out=co, tmax_k=t,
                        slope_deg=sl, clues=clues, ies=int(sum(clues.values())),
                        source='DEMO values (approximate positions)'))
dump('moon_targets.json', dict(demo=True, band='Mini-RF S-band (12.6 cm)', ratio_threshold=1.2,
     cold_threshold_k=110, slope_threshold_deg=float(slopes), targets=targets))

# ---------- 3. Analog engine grid (2 deg demo; real = 0.5 deg) ----------
FEATURES = ['aridity', 'barren', 'thermal_range', 'cold', 'dust', 'roughness', 'elevation']
step = 2.0
cells = []
lats = np.arange(-58 + step / 2, 84, step)
lons = np.arange(-180 + step / 2, 180, step)
raw = []
for la in lats:
    for lo in lons:
        if not globe.is_land(la, lo):
            continue
        # crude demo physics: deserts near +-25 deg, cold at high lat, dust near Sahara/Central Asia
        arid = math.exp(-((abs(la) - 25) / 12) ** 2) + 0.4 * rng.random()
        if -20 < lo < 60 and 10 < la < 50: arid += 0.6
        if -75 < lo < -66 and -30 < la < -18: arid += 0.9   # Atacama
        barren = arid * 0.8 + 0.25 * rng.random() + (0.6 if abs(la) > 65 else 0)
        thermal = arid * 0.7 + 0.3 * rng.random()
        cold = (abs(la) / 80) ** 1.5 + 0.2 * rng.random()
        dust = arid * 0.7 + (0.5 if (-20 < lo < 80 and 10 < la < 50) else 0) + 0.2 * rng.random()
        rough = 0.3 * rng.random() + (0.6 if (60 < lo < 100 and 25 < la < 45) or (-80 < lo < -65 and -40 < la < 0) else 0)
        elev = rough * 0.8 + 0.3 * rng.random()
        raw.append((la, lo, [arid, barren, thermal, cold, dust, rough, elev]))
vals = np.array([r[2] for r in raw])
pct = np.argsort(np.argsort(vals, axis=0), axis=0) / (len(vals) - 1)
for (la, lo, _), p in zip(raw, pct):
    cells.append([round(float(lo), 2), round(float(la), 2)] + [round(float(x), 3) for x in p])
dump('analog_grid.json', dict(demo=True, cell_deg=step, features=FEATURES, cells=cells))

dump('targets.json', dict(
    demo=False,
    note='Starting profiles and weights chosen by the team; documented on the Method page. Edit freely.',
    features={
        'aridity': 'Low yearly precipitation (NASA GPM IMERG)',
        'barren': 'No vegetation (MODIS NDVI, inverted)',
        'thermal_range': 'Day-night surface temperature swing (MODIS LST)',
        'cold': 'Cold nights (MODIS LST night, 5th percentile, inverted)',
        'dust': 'Airborne dust (MODIS aerosol optical depth)',
        'roughness': 'Terrain roughness (DEM)',
        'elevation': 'High elevation, thinner air (DEM)'},
    targets={
        'moon_south_pole': dict(label='Moon - south pole base', profile=dict(aridity=1, barren=1, thermal_range=1, cold=1, dust=0.3, roughness=0.8, elevation=0.7),
            cannot=['1/6 gravity', 'hard vacuum', 'space radiation', 'sharp, never-weathered regolith']),
        'mars_jezero': dict(label='Mars - Jezero crater (ancient lake delta)', profile=dict(aridity=1, barren=1, thermal_range=0.9, cold=0.7, dust=0.9, roughness=0.4, elevation=0.6),
            cannot=['3/8 gravity', 'air <1% of Earth pressure', 'space radiation', 'perchlorate soils']),
        'mars_gale': dict(label='Mars - Gale crater (layered lake sediments)', profile=dict(aridity=1, barren=1, thermal_range=0.9, cold=0.7, dust=0.8, roughness=0.7, elevation=0.6),
            cannot=['3/8 gravity', 'air <1% of Earth pressure', 'space radiation', 'billions of years of history'])},
    modes={
        'science': dict(label='Science', weights=dict(aridity=3, barren=3, thermal_range=1, cold=1, dust=1, roughness=1, elevation=0.5)),
        'operations': dict(label='Rover operations', weights=dict(aridity=1, barren=1, thermal_range=1, cold=1, dust=2, roughness=3, elevation=0.5)),
        'construction': dict(label='Base construction', weights=dict(aridity=1, barren=1, thermal_range=2, cold=2, dust=1, roughness=3, elevation=0.5)),
        'resources': dict(label='Ice & resources', weights=dict(aridity=1, barren=1, thermal_range=1, cold=3, dust=0.5, roughness=1, elevation=1))}))

# ---------- 4. Validation ----------
known = [('Atacama Desert', -24.5, -69.25), ('Death Valley', 36.5, -117.0), ('Haughton crater', 75.38, -89.68),
         ('Mauna Kea', 19.82, -155.47), ('Rio Tinto', 37.7, -6.6), ('Mars Desert Research Station, Utah', 38.41, -110.79),
         ('Mojave Desert', 35.0, -116.0), ('Danakil Depression', 14.2, 40.3), ('Pilbara', -21.0, 119.0), ('Svalbard', 78.2, 16.0)]
dump('validation.json', dict(demo=True, top_fraction=0.10,
     lift={'moon_south_pole': {'science': 3.1, 'operations': 2.2, 'construction': 2.4, 'resources': 2.0},
           'mars_jezero': {'science': 3.6, 'operations': 2.5, 'construction': 2.1, 'resources': 1.7},
           'mars_gale': {'science': 3.4, 'operations': 2.7, 'construction': 2.3, 'resources': 1.8}},
     p_value=0.003, known_sites=[dict(name=n, lat=a, lon=o) for n, a, o in known]))

# ---------- 5. Mangystau (Mars Field Twin) ----------
# No coordinates in demo: real ones come from OpenStreetMap / Wikipedia with coord_source (pipeline/03_mangystau_field.py).
MGS_FEATURES = ['elevation_m', 'slope_deg', 'lst_range_k', 'ndvi_max', 'precip_mm_yr', 'salt_index']
places = ['Torysh (Valley of Balls)', 'Bozzhyra', 'Tuzbair sor', 'Karagiye Depression', 'Sherkala']
dump('mangystau.json', dict(demo=True,
     places=[dict(name=n, lat=None, lon=None, coord_source=None, **{f: None for f in MGS_FEATURES}) for n in places],
     region_stats={}, rank_vs_mars=dict(mars_gale=None, mars_jezero=None), images=[],
     images_note='Put Sentinel-2 views in assets/img/mangystau_*.png and list them as {file, caption}'))
