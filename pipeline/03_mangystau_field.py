# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Mars Field Twin: Mangystau (Kazakhstan) site and region statistics with Google Earth Engine."""
import json
import urllib.request
from common import SITE_DATA, SITE_IMG, YEARS, ee_init

ee = ee_init()
Y0, Y1 = (f'{YEARS[0]}-01-01', f'{YEARS[1] + 1}-01-01')
BUFFER_M = 5000
S2_DATES = ('2023-01-01', '2025-01-01')

WIKI, OSM = 'https://{}.wikipedia.org/wiki/{}', 'https://www.openstreetmap.org/{}/{}'
PLACES = [  # name, slug, lat, lon, coordinate source
    ('Torysh (Valley of Balls)', 'torysh', 44.3614, 51.5611, 'Wikipedia: ' + WIKI.format('en', 'Torysh')),
    ('Sherkala', 'sherkala', 44.25638889, 52.00611111, 'Wikipedia: ' + WIKI.format('en', 'Sherkala')),
    ('Karagiye Depression', 'karagiye', 43.40, 51.79, 'Wikipedia: ' + WIKI.format('en', 'Karagiye')),
    ('Karynzharyk Depression', 'karynzharyk', 42.91667, 54.41667, 'Wikipedia: ' + WIKI.format('ru', 'Карынжарык')),
    ('Bozzhyra', 'bozzhyra', 43.4045686, 54.0770414, 'OpenStreetMap: ' + OSM.format('node', 4282143923)),
    ('Tuzbair sor', 'tuzbair', 44.0011422, 53.2833108, 'OpenStreetMap: ' + OSM.format('relation', 5965693)),
]


def dem():
    col = ee.ImageCollection('COPERNICUS/DEM/GLO30_2024_1').select('DEM')
    d = col.mosaic().setDefaultProjection(col.first().projection())
    return d.rename('elevation_m').addBands(d.rename('elevation_min_m')).addBands(ee.Terrain.slope(d).rename('slope_deg'))


def lst_range():
    def f(i):
        return i.select('LST_Day_1km').subtract(i.select('LST_Night_1km')).multiply(0.02)
    return ee.ImageCollection('MODIS/061/MOD11A2').filterDate(Y0, Y1).map(f).mean().rename('lst_range_k')


def ndvi_max():
    years = ee.List.sequence(*YEARS)
    yearly = years.map(lambda y: ee.ImageCollection('MODIS/061/MOD13A2').select('NDVI')
                       .filter(ee.Filter.calendarRange(y, y, 'year')).max().multiply(0.0001))
    return ee.ImageCollection(yearly).mean().rename('ndvi_max')


def precip():
    # IMERG monthly 'precipitation' is a mean rate in mm/h -> mean annual total
    return ee.ImageCollection('NASA/GPM_L3/IMERG_MONTHLY_V07').filterDate(Y0, Y1).select('precipitation') \
        .mean().multiply(24 * 365.25).rename('precip_mm_yr')


def s2():
    def mask(i):
        scl = i.select('SCL')
        return i.updateMask(scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)))
    return ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterDate(*S2_DATES) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)).map(mask).median()


def salt_index(img):
    # SWIR normalized difference: carbonates/gypsum/salts absorb near 2.2 um (B12) -> higher values. Approximate.
    return img.normalizedDifference(['B11', 'B12']).rename('salt_index')


def land():
    return ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence').unmask(0).lt(50)


def stats(geom, scale_dem, land_only=False, with_min=True):
    reducers = [
        (dem().select(['elevation_m', 'slope_deg']), ee.Reducer.mean(), scale_dem),
        *([(dem().select('elevation_min_m'), ee.Reducer.min(), scale_dem)] if with_min else []),
        (lst_range(), ee.Reducer.mean(), 1000),
        (ndvi_max(), ee.Reducer.mean(), 1000),
        (precip(), ee.Reducer.mean(), 1000),
        (salt_index(s2()), ee.Reducer.mean(), max(scale_dem, 20)),
    ]
    out = {}
    for img, red, sc in reducers:
        img = img.updateMask(land()) if land_only else img
        d = img.reduceRegion(red, geom, sc, maxPixels=1e10, bestEffort=True).getInfo()
        out.update({k.removesuffix('_mean').removesuffix('_min'): v for k, v in d.items()})
    return {k: (round(v, 3) if v is not None else None) for k, v in out.items()}


def thumbnail(slug, lat, lon):
    region = ee.Geometry.Point(lon, lat).buffer(BUFFER_M).bounds()
    url = s2().visualize(bands=['B4', 'B3', 'B2'], min=0, max=7000, gamma=1.5).getThumbURL(
        dict(region=region, dimensions=800, format='png'))
    path = SITE_IMG / f'mangystau_{slug}.png'
    path.write_bytes(urllib.request.urlopen(url, timeout=120).read())
    return path.name


def main():
    SITE_IMG.mkdir(parents=True, exist_ok=True)
    places, images = [], []
    for name, slug, lat, lon, src in PLACES:
        s = stats(ee.Geometry.Point(lon, lat).buffer(BUFFER_M), 30)
        places.append(dict(name=name, lat=lat, lon=lon, coord_source=src, **s))
        images.append(dict(file=thumbnail(slug, lat, lon),
                           caption=f'{name} — Sentinel-2 true colour, median {S2_DATES[0][:4]}–{int(S2_DATES[1][:4]) - 1}, '
                                   f'{2 * BUFFER_M // 1000} km box. Contains modified Copernicus Sentinel data.'))
        print(name, s, flush=True)
    lats, lons = [p[2] for p in PLACES], [p[3] for p in PLACES]
    region = ee.Geometry.Rectangle([min(lons) - 0.3, min(lats) - 0.3, max(lons) + 0.3, max(lats) + 0.3])
    region_stats = stats(region, 300, land_only=True, with_min=False)
    print('region', region_stats)
    out = dict(
        demo=False, places=places, region_stats=region_stats,
        region_def=f'land pixels (JRC surface-water occurrence < 50%) in the bounding box of the six sites + 0.3 deg: '
                   f'{[round(min(lons) - 0.3, 2), round(min(lats) - 0.3, 2), round(max(lons) + 0.3, 2), round(max(lats) + 0.3, 2)]}',
        rank_vs_mars=dict(mars_gale=None, mars_jezero=None), rank_note='filled by pipeline/04_analog_engine.py',
        images=images,
        method=dict(
            site_buffer_m=BUFFER_M, period=f'{YEARS[0]}-{YEARS[1]}',
            elevation='Copernicus DEM GLO-30 (2024_1), mean (elevation_min_m = minimum in buffer; sites only)',
            slope_deg='Copernicus DEM GLO-30 (2024_1), mean slope', lst_range_k='MODIS MOD11A2 LST day minus night, mean',
            ndvi_max='MODIS MOD13A2 NDVI, yearly maximum averaged over the period',
            precip_mm_yr='NASA GPM IMERG V07 monthly, mean rate x 8766 h',
            salt_index=f'Sentinel-2 SR (B11-B12)/(B11+B12), cloud-masked median {S2_DATES[0][:4]}-{int(S2_DATES[1][:4]) - 1}; approximate'),
    )
    (SITE_DATA / 'mangystau.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
