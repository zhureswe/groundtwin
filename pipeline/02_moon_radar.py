# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Moon Radar Twin: lunar south-pole targets (IAU Gazetteer) + Mini-RF CPR, Diviner Tmax, LOLA slope."""
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
RAW, DATA = ROOT / 'raw', ROOT / 'data'
IAU_SHP = RAW / 'iau' / 'MOON_nomenclature_center_pts.shp'
IAU_SOURCE = ('IAU Gazetteer of Planetary Nomenclature, MOON_nomenclature_center_pts '
              '(https://planetarynames.wr.usgs.gov)')

PSR_CRATERS = ['Shackleton', 'Haworth', 'Shoemaker', 'Faustini', 'Cabeus', 'de Gerlache', 'Sverdrup', 'Nobile']
# Artemis III candidate regions (NASA, Oct 2024) are not IAU features; we tie each to its named IAU anchor.
ARTEMIS_REGIONS = {
    'Peak near Cabeus B': 'Cabeus B', 'Haworth': 'Haworth', 'Malapert Massif': 'Mons Malapert',
    'Mons Mouton Plateau': 'Mons Mouton', 'Mons Mouton': 'Mons Mouton', 'Nobile Rim 1': 'Nobile',
    'Nobile Rim 2': 'Nobile', 'de Gerlache Rim 2': 'de Gerlache', 'Slater Plain': 'Slater',
}


def build_targets():
    g = gpd.read_file(IAU_SHP).set_index('name')
    rows = [dict(target=n, kind='psr_crater', iau_feature=n) for n in PSR_CRATERS]
    rows += [dict(target=r, kind='artemis_iii_region', iau_feature=a) for r, a in ARTEMIS_REGIONS.items()]
    for r in rows:
        f = g.loc[r['iau_feature']]
        r.update(lat=round(f.center_lat, 4), lon_east=round(f.center_lon, 4),
                 lon=round((f.center_lon + 180) % 360 - 180, 4), diameter_km=round(f.diameter, 2),
                 feature_type=f.type, iau_link=f.link, source=IAU_SOURCE)
        if r['kind'] == 'artemis_iii_region':
            r['note'] = 'region centre not in IAU Gazetteer; coordinates are those of the IAU anchor feature'
    df = gpd.pd.DataFrame(rows)
    df.to_csv(DATA / 'moon_targets.csv', index=False)
    return df


if __name__ == '__main__':
    print(build_targets()[['target', 'kind', 'iau_feature', 'lat', 'lon', 'diameter_km']].to_string())
