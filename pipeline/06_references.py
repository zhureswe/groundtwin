# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Reference comparison: Mangystau vs Utah (MDRS, San Rafael Swell) vs Devon/Haughton against Mars Gale/Jezero
profiles (S, cosine similarity, rank among Earth land cells) + PCA map of known analogs in feature space."""
import importlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import DATA, SITE_DATA, SITE_IMG

ae = importlib.import_module('04_analog_engine')
val = importlib.import_module('05_validation')
MODE = 'science'
REFERENCES = ['Mars Desert Research Station (Utah)', 'San Rafael Swell (Utah)', 'Devon Island', 'Haughton impact crater']
MARS = ['mars_gale', 'mars_jezero']


def cosine(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def main():
    lon, lat, P = val.load_grid()
    T = json.loads((SITE_DATA / 'targets.json').read_text())
    mgs = json.loads((SITE_DATA / 'mangystau.json').read_text(encoding='utf-8'))
    w = T['modes'][MODE]['weights']
    R = {tk: ae.top_rank(ae.similarity(P, T['targets'][tk]['profile'], w)) for tk in MARS}
    prof = {tk: np.array([T['targets'][tk]['profile'][f] for f in ae.FEATURES]) for tk in T['targets']}

    sites = {s[0]: s for s in val.SITES}
    places = [('Mangystau (6 sites)', [ae.cell_index(lon, lat, p['lon'], p['lat']) for p in mgs['places']])]
    places += [(n, [ae.cell_index(lon, lat, sites[n][4], sites[n][3])]) for n in REFERENCES]
    rows = []
    for name, cells in places:
        cells = sorted(set(cells))
        vec = P[cells].mean(0)
        row = dict(place=name, n_cells=len(cells), features={f: round(float(v), 3) for f, v in zip(ae.FEATURES, vec)})
        for tk in MARS:
            S = ae.similarity(P[cells], T['targets'][tk]['profile'], w)
            row[tk] = dict(S=round(float(S.mean()), 3), cosine=round(cosine(vec, prof[tk]), 3),
                           top_percent=round(float(np.median(R[tk][cells]) * 100), 1))
        rows.append(row)
        print(name, {tk: row[tk] for tk in MARS})

    # PCA on all land cells (standardised percentiles)
    mu = P.mean(0)
    _, _, Vt = np.linalg.svd(P - mu, full_matrices=False)
    pc = lambda X: (np.atleast_2d(X) - mu) @ Vt[:2].T
    var = (np.linalg.svd(P - mu, compute_uv=False) ** 2)
    expl = (var / var.sum())[:2]
    fig, ax = plt.subplots(figsize=(8, 6.5))
    bg = pc(P[::7])
    ax.scatter(bg[:, 0], bg[:, 1], s=2, c='#c9ced6', alpha=0.35, label='Earth land cells (sample)', rasterized=True)
    pts, by_cell = [], {}
    for s in val.SITES:
        if s[1] != 'moon':
            by_cell.setdefault(ae.cell_index(lon, lat, s[4], s[3]), []).append(s[0])
    for c, names in by_cell.items():
        xy = pc(P[c])[0]
        ref = any(n in REFERENCES for n in names)
        label = ' / '.join(dict.fromkeys(n.split(' (')[0] for n in names))
        ax.scatter(*xy, s=46, c='#D9822B' if ref else '#5b6b80', edgecolor='k', zorder=3)
        ax.annotate(label, xy, fontsize=7, xytext=(4, 3), textcoords='offset points')
        pts.append(dict(name=label, pc1=round(float(xy[0]), 3), pc2=round(float(xy[1]), 3), reference=ref))
    m = pc(P[places[0][1]])
    ax.scatter(m[:, 0], m[:, 1], s=60, c='#E0473A', marker='D', edgecolor='k', zorder=4, label='Mangystau sites')
    for tk, mk in (('mars_gale', '*'), ('mars_jezero', 'P')):
        xy = pc(prof[tk])[0]
        ax.scatter(*xy, s=260, c='#4FB3D9', marker=mk, edgecolor='k', zorder=5, label=T['targets'][tk]['label'])
        pts.append(dict(name=T['targets'][tk]['label'], pc1=round(float(xy[0]), 3), pc2=round(float(xy[1]), 3), reference=False))
    ax.scatter([], [], s=46, c='#D9822B', edgecolor='k', label='Utah / Devon references')
    ax.scatter([], [], s=46, c='#5b6b80', edgecolor='k', label='Known analogs (NASA, USGS)')
    ax.set_xlabel(f'PC1 ({expl[0]:.0%} of variance)'); ax.set_ylabel(f'PC2 ({expl[1]:.0%} of variance)')
    ax.set_title('Feature space of Earth land cells (7 percentile features)')
    ax.legend(fontsize=7, loc='best'); fig.tight_layout()
    for path in (DATA / 'analog_pca.png', SITE_IMG / 'analog_pca.png'):
        fig.savefig(path, dpi=170)
    plt.close(fig)
    loadings = {f'pc{i + 1}': {f: round(float(v), 3) for f, v in zip(ae.FEATURES, Vt[i])} for i in range(2)}
    out = dict(demo=False, mode=MODE, rows=rows, pca=dict(explained_variance=[round(float(x), 3) for x in expl],
               loadings=loadings, points=pts, image='assets/img/analog_pca.png'),
               method='S and rank use Science-mode weights; cosine = cosine similarity between the mean percentile vector '
                      'of the place and the target profile; top_percent = median rank of the place cells among all land cells.')
    (SITE_DATA / 'references.json').write_text(json.dumps(out, indent=1))
    print('PCA explained', expl, loadings)


if __name__ == '__main__':
    main()
