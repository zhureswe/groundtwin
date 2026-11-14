# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Earth Radar Twin: RCM compact-pol CPR over Canadian ground-truth sites (ice / rough rock / smooth)."""
import os, json, math, warnings
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import rioxarray as rxr, pyproj
from shapely.geometry import box
from shapely.ops import transform
from pystac_client import Client

warnings.filterwarnings('ignore')
os.environ['GDAL_DISABLE_READDIR_ON_OPEN'] = 'EMPTY_DIR'
os.environ['CPL_VSIL_CURL_ALLOWED_EXTENSIONS'] = '.tif'
os.environ['AWS_NO_SIGN_REQUEST'] = 'YES'

OUT = Path(__file__).resolve().parents[1] / 'data'
(OUT / 'site_maps').mkdir(parents=True, exist_ok=True)

# name: (class, lon, lat, half-size in degrees of latitude)
SITES = {
    'devon_ice_cap':     ('ice',        -82.00, 75.25, 0.02),
    'penny_ice_cap':     ('ice',        -66.00, 67.25, 0.02),
    'columbia_icefield': ('ice',       -117.33, 52.17, 0.015),
    'haughton_crater':   ('rough_rock', -89.68, 75.38, 0.02),
    'nisgaa_lava_bed':   ('rough_rock',-128.97, 55.17, 0.015),
    'edziza_lava_field': ('rough_rock',-130.65, 57.70, 0.015),
    'athabasca_dunes':   ('smooth',    -108.75, 59.08, 0.02),
    'great_sand_hills':  ('smooth',    -109.30, 50.45, 0.02),
    'regina_plain':      ('smooth',    -104.60, 50.55, 0.02),
}
CLASSES = ['smooth', 'rough_rock', 'ice']
COLORS = {'smooth': '#8C9BAB', 'rough_rock': '#D9822B', 'ice': '#4FB3D9'}
DATE_RANGE = '2024-01-01/2026-11-13'
WINTER = {12, 1, 2, 3}   # dry snow / frozen ground: less moisture effect
MAX_TRIES = 6
INC_RANGE = (30, 60)     # local incidence angle filter (Mini-RF ~48 deg)
LOOK = 5                 # 5x5 block averaging, reduces speckle
CREDIT = ('RADARSAT Constellation Mission Imagery (c) Government of Canada (2025). '
          'RADARSAT is an official mark of the Canadian Space Agency.')

cat = Client.open('https://www.eodms-sgdot.nrcan-rncan.gc.ca/search/')


def site_bbox(lon, lat, h):
    dlon = h / max(math.cos(math.radians(lat)), 0.15)
    return lon - dlon, lat - h, lon + dlon, lat + h


def read_clip(url, bbox):
    da = rxr.open_rasterio(url, masked=True)
    tr = pyproj.Transformer.from_crs(4326, da.rio.crs, always_xy=True)
    return da.rio.clip_box(*transform(tr.transform, box(*bbox)).bounds).squeeze().values.astype('float64')


def block_mean(a, k=LOOK):
    h, w = (a.shape[0] // k) * k, (a.shape[1] // k) * k
    if h == 0 or w == 0:
        return np.full((1, 1), np.nan)
    return np.nanmean(a[:h, :w].reshape(h // k, k, w // k, k), axis=(1, 3))


def month(item):
    return int(item.properties['datetime'][5:7])


def find_items(bbox):
    s = cat.search(collections=['rcm-ard'], bbox=bbox, datetime=DATE_RANGE, limit=200, method='GET')
    items = sorted((i for i in s.items() if {'rr', 'rl'} <= i.assets.keys()),
                   key=lambda i: i.properties['datetime'], reverse=True)
    return [i for i in items if month(i) in WINTER] + [i for i in items if month(i) not in WINTER]


def process_site(name, cls, lon, lat, h):
    bbox = site_bbox(lon, lat, h)
    items = find_items(bbox)
    print(f'{name}: {len(items)} scenes found', flush=True)
    for it in items[:MAX_TRIES]:
        date = it.properties['datetime'][:10]
        try:
            rr, rl = (read_clip(it.assets[k].href, bbox) for k in ('rr', 'rl'))
        except Exception as e:
            print('   read failed:', str(e)[:80]); continue
        n0, n1 = min(rr.shape[0], rl.shape[0]), min(rr.shape[1], rl.shape[1])
        rr, rl = rr[:n0, :n1], rl[:n0, :n1]
        valid = np.isfinite(rr) & np.isfinite(rl) & (rr > 0) & (rl > 0)
        if valid.mean() < 0.6:
            print(f'   {date}: only {valid.mean():.0%} coverage, next'); continue
        inc_mean = None
        if 'local_inc_angle' in it.assets:
            try:
                inc = read_clip(it.assets['local_inc_angle'].href, bbox)[:n0, :n1]
                inc_mean = float(np.nanmean(inc))
                valid &= (inc >= INC_RANGE[0]) & (inc <= INC_RANGE[1])
            except Exception:
                pass
        rr, rl = np.where(valid, rr, np.nan), np.where(valid, rl, np.nan)
        ratio = block_mean(rr) / block_mean(rl)   # ratio of local means, like Mini-RF
        if np.isfinite(ratio).sum() < 20:
            print('   too few valid cells, next'); continue
        print(f'   using {date}, {np.isfinite(ratio).sum()} cells', flush=True)
        return dict(site=name, cls=cls, lon=lon, lat=lat, date=date,
                    scene=it.properties.get('order_key', it.id), inc_mean=inc_mean,
                    winter=month(it) in WINTER, ratio_map=ratio)
    print('   no usable scene')
    return None


def stats(c):
    return dict(median=float(np.median(c)), p25=float(np.percentile(c, 25)),
                p75=float(np.percentile(c, 75)), frac_gt1=float((c > 1).mean()), n=int(c.size))


def main():
    results = [r for n, s in SITES.items() if (r := process_site(n, *s))]
    print(f'\nUsable sites: {len(results)} / {len(SITES)}')

    # Convention check: smooth natural surfaces must have CPR < 1
    ref_pool = [r for r in results if r['cls'] == 'smooth'] or results
    ref = float(np.median([np.nanmedian(r['ratio_map']) for r in ref_pool]))
    flip = ref > 1
    for r in results:
        r['map'] = 1 / r['ratio_map'] if flip else r['ratio_map']
        r['cpr'] = r['map'][np.isfinite(r['map'])]
        r['stats'] = stats(r['cpr'])
    convention = 'CPR = RL/RR' if flip else 'CPR = RR/RL'
    print(f'Reference median RR/RL ({"smooth" if ref_pool is not results else "all"} sites) = {ref:.3f} -> {convention}')

    for r in sorted(results, key=lambda r: (CLASSES.index(r['cls']), r['site'])):
        s = r['stats']
        print(f"{r['cls']:11s} {r['site']:20s} {r['date']} winter={r['winter']!s:5s} "
              f"CPRmed={s['median']:.3f} >1={s['frac_gt1']:.0%} cells={s['n']}")

    ordered = [r for c in CLASSES for r in results if r['cls'] == c]
    fig, ax = plt.subplots(figsize=(9, 5))
    bp = ax.boxplot([r['cpr'] for r in ordered], patch_artist=True, showfliers=False)
    for p, r in zip(bp['boxes'], ordered):
        p.set_facecolor(COLORS[r['cls']])
    ax.set_xticks(range(1, len(ordered) + 1), [r['site'].replace('_', '\n') for r in ordered], fontsize=8)
    ax.axhline(1, ls='--', c='k', lw=1)
    ax.set_ylabel('CPR (same-sense / opposite-sense)')
    ax.set_title('Earth ground truth: RCM C-band CPR by surface class')
    for c in CLASSES:
        ax.plot([], [], 's', c=COLORS[c], label=c)
    ax.legend(); fig.tight_layout()
    fig.savefig(OUT / 'earth_cpr_by_class.png', dpi=200); plt.close(fig)

    for r in results:
        plt.figure(figsize=(4, 4)); plt.imshow(r['map'], cmap='magma', vmin=0, vmax=1.5)
        plt.colorbar(label='CPR', shrink=0.8); plt.title(f"{r['site']} ({r['cls']})\n{r['date']}"); plt.axis('off')
        plt.savefig(OUT / 'site_maps' / f"{r['site']}.png", dpi=150, bbox_inches='tight'); plt.close()

    summary = dict(
        convention=convention, reference_median_rr_over_rl=ref, look=LOOK, inc_range=list(INC_RANGE),
        date_range=DATE_RANGE, credit=CREDIT,
        source='RCM CEOS-ARD via EODMS STAC (collection rcm-ard), s3://rcm-ceos-ard',
        sites_without_usable_scene=sorted(set(SITES) - {r['site'] for r in results}),
        sites=[dict(site=r['site'], cls=r['cls'], lon=r['lon'], lat=r['lat'], date=r['date'], scene=r['scene'],
                    winter=r['winter'], inc_mean=r['inc_mean'], **r['stats'],
                    hist=np.histogram(np.clip(r['cpr'], 0, 2), bins=40, range=(0, 2))[0].tolist())
               for r in results],
        classes={c: stats(np.concatenate(sel)) for c in CLASSES
                 if (sel := [r['cpr'] for r in results if r['cls'] == c])},
    )
    (OUT / 'earth_cpr.json').write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary['classes'], indent=1))


if __name__ == '__main__':
    main()
