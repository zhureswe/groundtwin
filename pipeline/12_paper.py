# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Builds the research paper: paper/groundtwin_paper.template.md + numbers read from docs/data/*.json
-> paper/groundtwin_paper.md, .html, .pdf (headless Chrome) and paper/numbers.md (every number with its source file and key)."""
import json
import shutil
import subprocess
from pathlib import Path
from string import Template
import markdown
from common import ROOT, SITE_DATA

PAPER = ROOT / 'paper'
CHROME = Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
N, SRC = {}, {}


def load(name):
    return json.loads((SITE_DATA / f'{name}.json').read_text(encoding='utf-8'))


def put(key, value, source, fmt=None):
    N[key] = format(value, fmt) if fmt else str(value)
    SRC[key] = source


def collect():
    e, m, v, b = load('earth_cpr'), load('moon_targets'), load('validation'), load('blind_test')
    g, r, p, w, sc, ag, T = (load(k) for k in ('mangystau', 'references', 'polarimetry', 'wavelength', 'showcase', 'analog_grid', 'targets'))
    put('n_sites', len(e['sites']), 'earth_cpr.json: len(sites)')
    put('n_noscene', len(e['sites_without_usable_scene']), 'earth_cpr.json: sites_without_usable_scene')
    put('ref_rr_rl', e['reference_median_rr_over_rl'], 'earth_cpr.json: reference_median_rr_over_rl', '.3f')
    put('look', e['look'], 'earth_cpr.json: look')
    put('inc_lo', e['inc_range'][0], 'earth_cpr.json: inc_range'); put('inc_hi', e['inc_range'][1], 'earth_cpr.json: inc_range')
    for c in ('smooth', 'rough_rock', 'ice'):
        k = e['classes'][c]
        for f in ('median', 'p25', 'p75'):
            put(f'{c}_{f}', k[f], f'earth_cpr.json: classes.{c}.{f}', '.2f')
        put(f'{c}_gt1', k['frac_gt1'] * 100, f'earth_cpr.json: classes.{c}.frac_gt1 x100', '.1f')
        put(f'{c}_n', k['n'], f'earth_cpr.json: classes.{c}.n')
    for s in e['sites']:
        put(f"site_{s['site']}", s['median'], f"earth_cpr.json: sites[{s['site']}].median", '.2f')

    craters = [t for t in m['targets'] if t['ies'] is not None]
    put('n_targets', len(m['targets']), 'moon_targets.json: len(targets)')
    put('n_craters', len(craters), 'moon_targets.json: targets with ies != null')
    put('n_ies2', sum(t['ies'] >= 2 for t in craters), 'moon_targets.json: count ies >= 2')
    put('ies2_names', ', '.join(t['name'] for t in craters if t['ies'] >= 2), 'moon_targets.json: names with ies >= 2')
    put('ratio_thr', m['ratio_threshold'], 'moon_targets.json: ratio_threshold')
    put('cold_thr', m['cold_threshold_k'], 'moon_targets.json: cold_threshold_k')
    put('slope_thr', m['slope_threshold_deg'], 'moon_targets.json: slope_threshold_deg', '.2f')
    cin = [t['cpr_in'] for t in m['targets']]
    put('moon_cpr_min', min(cin), 'moon_targets.json: min(cpr_in)', '.2f'); put('moon_cpr_max', max(cin), 'moon_targets.json: max(cpr_in)', '.2f')
    for name in ('Shackleton', 'Faustini', 'Cabeus'):
        t = next(x for x in m['targets'] if x['name'] == name); k = name.lower()
        put(f'{k}_in', t['cpr_in'], f'moon_targets.json: {name}.cpr_in', '.2f'); put(f'{k}_out', t['cpr_out'], f'moon_targets.json: {name}.cpr_out', '.2f')
        put(f'{k}_ratio', t['cpr_in'] / t['cpr_out'], f'moon_targets.json: {name}.cpr_in / cpr_out', '.2f')
        put(f'{k}_tmax', t['tmax_k'], f'moon_targets.json: {name}.tmax_k', '.0f'); put(f'{k}_ies', t['ies'], f'moon_targets.json: {name}.ies')

    rows = [f"| {x['name']} | {x['cpr_in']:.2f} / {x['cpr_out']:.2f} | {x['slope_deg']:.1f}° | {x['tmax_k']:.0f} K "
            f"| {x['frac_floor_below_110k'] * 100:.0f}% | {x['ies'] if x['ies'] is not None else 'n/a'} |" for x in m['targets']]
    put('crater_table', chr(10).join(rows), 'moon_targets.json: targets[*] (cpr_in, cpr_out, slope_deg, tmax_k, frac_floor_below_110k, ies)')
    cab = next(x for x in m['targets'] if x['name'] == 'Cabeus')
    put('cabeus_cold', cab['frac_floor_below_110k'] * 100, 'moon_targets.json: Cabeus.frac_floor_below_110k x100', '.0f')
    PC = p['earth']['classes']
    for c in ('smooth', 'rough_rock', 'ice'):
        put(f'pol_{c}', PC[c]['frac_criterion'] * 100, f'polarimetry.json: earth.classes.{c}.frac_criterion x100', '.2f')
        put(f'chi_{c}', PC[c]['chi_median_of_sites_deg'], f'polarimetry.json: earth.classes.{c}.chi_median_of_sites_deg', '.0f')
        put(f'dop_{c}', PC[c]['dop_median_of_sites'], f'polarimetry.json: earth.classes.{c}.dop_median_of_sites', '.2f')
    for t in p['moon']['targets']:
        if t['target'] in p['golden_case']['moon']:
            k = t['target'].lower()
            put(f'pol_{k}_in', t['inside']['frac_criterion'] * 100, f"polarimetry.json: moon.targets[{t['target']}].inside.frac_criterion x100", '.2f')
            put(f'pol_{k}_out', t['outside']['frac_criterion'] * 100, f"polarimetry.json: moon.targets[{t['target']}].outside.frac_criterion x100", '.2f')
    coh = [s['coherence_median'] for s in p['earth']['sites']]
    put('coh_min', min(coh), 'polarimetry.json: min(earth.sites.coherence_median)', '.2f'); put('coh_max', max(coh), 'polarimetry.json: max(earth.sites.coherence_median)', '.2f')
    st = [t['cpr_from_stokes_vs_mosaic_median_ratio'] for t in p['moon']['targets']]
    put('stokes_ratio', min(st), 'polarimetry.json: min(moon.targets.cpr_from_stokes_vs_mosaic_median_ratio)', '.3f')

    lim = list(w['rcm']['h_cm_at_filter_limits'].items())
    put('h_rcm_lo', lim[0][1], 'wavelength.json: rcm.h_cm_at_filter_limits', '.2f'); put('h_rcm_hi', lim[1][1], 'wavelength.json: rcm.h_cm_at_filter_limits', '.2f')
    put('h_minirf', w['minirf']['h_cm'], 'wavelength.json: minirf.h_cm', '.2f')
    put('lam_rcm', w['rcm']['wavelength_cm'], 'wavelength.json: rcm.wavelength_cm'); put('lam_minirf', w['minirf']['wavelength_cm'], 'wavelength.json: minirf.wavelength_cm')
    put('inc_minirf', w['minirf']['incidence_deg'], 'wavelength.json: minirf.incidence_deg', '.0f')

    put('n_cells', f"{len(ag['cells']):,}", 'analog_grid.json: len(cells)')
    put('cell_deg', ag['cell_deg'], 'analog_grid.json: cell_deg')
    put('dust_imputed', f"{ag['imputed_missing_to_0_5']['dust']:,}", 'analog_grid.json: imputed_missing_to_0_5.dust')
    for tk in ('moon_south_pole', 'mars_gale', 'mars_jezero'):
        k = tk.split('_')[-1] if tk != 'moon_south_pole' else 'moon'
        put(f'lift_{k}', v['lift'][tk]['science'], f'validation.json: lift.{tk}.science', '.2f')
        put(f'liftp_{k}', v['p_values'][tk]['science'], f'validation.json: p_values.{tk}.science')
        put(f'mr_{k}', v['mean_top_percent'][tk]['science'], f'validation.json: mean_top_percent.{tk}.science')
        put(f'mrp_{k}', v['mean_top_percent_p'][tk]['science'], f'validation.json: mean_top_percent_p.{tk}.science')
        put(f'cells_{k}', v['unique_cells_per_target'][tk], f'validation.json: unique_cells_per_target.{tk}')
    put('lift_gale_constr', v['lift']['mars_gale']['construction'], 'validation.json: lift.mars_gale.construction', '.2f')
    put('liftp_gale_constr', v['p_values']['mars_gale']['construction'], 'validation.json: p_values.mars_gale.construction')
    put('n_known', len(v['known_sites']), 'validation.json: len(known_sites)')
    for gk in ('mars', 'all'):
        x = b['groups'][gk]
        put(f'bt_{gk}_k', x['recognised'], f'blind_test.json: groups.{gk}.recognised'); put(f'bt_{gk}_n', x['total'], f'blind_test.json: groups.{gk}.total')
        put(f'bt_{gk}_p', x['p_value_binomial'], f'blind_test.json: groups.{gk}.p_value_binomial')
        put(f'bt_{gk}_chance', x['expected_by_chance'], f'blind_test.json: groups.{gk}.expected_by_chance')
        put(f'bt_{gk}_med', x['median_top_percent'], f'blind_test.json: groups.{gk}.median_top_percent')

    put('mgs_gale', g['rank_vs_mars']['mars_gale'], 'mangystau.json: rank_vs_mars.mars_gale')
    put('mgs_jezero', g['rank_vs_mars']['mars_jezero'], 'mangystau.json: rank_vs_mars.mars_jezero')
    pl = {x['name'].split(' (')[0]: x for x in g['places']}
    put('karagiye_min', pl['Karagiye Depression']['elevation_min_m'], 'mangystau.json: places[Karagiye].elevation_min_m', '.0f')
    put('karyn_min', pl['Karynzharyk Depression']['elevation_min_m'], 'mangystau.json: places[Karynzharyk].elevation_min_m', '.0f')
    salt = [x['salt_index'] for x in g['places']]
    put('salt_min', min(salt), 'mangystau.json: min(places.salt_index)', '.2f'); put('salt_max', max(salt), 'mangystau.json: max(places.salt_index)', '.2f')
    rs = g['region_stats']
    put('mgs_rain', rs['precip_mm_yr'], 'mangystau.json: region_stats.precip_mm_yr', '.0f'); put('mgs_ndvi', rs['ndvi_max'], 'mangystau.json: region_stats.ndvi_max', '.2f')
    put('mgs_lst', rs['lst_range_k'], 'mangystau.json: region_stats.lst_range_k', '.1f')
    rows = []
    for x in r['rows']:
        rows.append(f"| {x['place']} | {x['mars_gale']['S']:.2f} | {x['mars_gale']['cosine']:.2f} | top {x['mars_gale']['top_percent']}% "
                    f"| {x['mars_jezero']['S']:.2f} | {x['mars_jezero']['cosine']:.2f} | top {x['mars_jezero']['top_percent']}% |")
    put('ref_table', '\n'.join(rows), 'references.json: rows[*].mars_gale / mars_jezero (S, cosine, top_percent)')
    put('pc1', round(r['pca']['explained_variance'][0] * 100), 'references.json: pca.explained_variance[0] x100')
    put('pc2', round(r['pca']['explained_variance'][1] * 100), 'references.json: pca.explained_variance[1] x100')
    for tk in ('moon_south_pole', sc['mars_target']):
        k = 'moon' if tk == 'moon_south_pole' else 'mars'
        put(f'top_{k}', '; '.join(f"{x['region']} ({abs(x['lat']):.2f}°{'N' if x['lat'] >= 0 else 'S'}, {abs(x['lon']):.2f}°{'E' if x['lon'] >= 0 else 'W'}, S = {x['S']:.3f})"
                                  for x in sc['top'][tk]), f'showcase.json: top.{tk}')
    put('mars_target', T['targets'][sc['mars_target']]['label'], 'showcase.json: mars_target')
    cards = {c['key']: c for c in sc['cards']}
    for row in cards['moon_reference']['rows'] + cards['mars_reference']['rows']:
        k = row['place'].split(' (')[0].lower().replace(' ', '_')
        put(f'card_{k}', f"S = {row['S']:.2f}, cosine {row['cosine']:.2f}, rank #{row['position']:,} (top {row['top_percent']}%)",
            f"showcase.json: cards[*].rows[{row['place']}]")


def build_pdf(md_text):
    body = markdown.markdown(md_text, extensions=['tables'])
    css = ('body{font-family:Georgia,"Times New Roman",serif;font-size:9.8pt;line-height:1.32;max-width:18cm;margin:auto;color:#111}'
           'h1{font-size:17pt;line-height:1.2;margin:0 0 4pt}h2{font-size:12.5pt;margin:12pt 0 4pt;border-bottom:1px solid #999}'
           'h3{font-size:11pt;margin:8pt 0 2pt}table{border-collapse:collapse;font-size:8.8pt;margin:6pt 0}'
           'td,th{border:1px solid #bbb;padding:2pt 5pt;text-align:left}img{max-width:100%;max-height:6.2cm;display:block;margin:4pt auto}'
           'p.cap,em.cap{font-size:9pt;color:#333}code{font-size:9pt}@page{size:A4;margin:1.3cm 1.4cm}')
    html = PAPER / 'groundtwin_paper.html'
    html.write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>GroundTwin paper</title><style>{css}</style></head>'
                    f'<body>{body}</body></html>', encoding='utf-8')
    pdf = PAPER / 'groundtwin_paper.pdf'
    subprocess.run([str(CHROME), '--headless=new', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={pdf}',
                    '--allow-file-access-from-files', html.as_uri()], check=True, capture_output=True)
    (ROOT / 'docs' / 'paper').mkdir(exist_ok=True)
    shutil.copy(pdf, ROOT / 'docs' / 'paper' / 'groundtwin_paper.pdf')


def main():
    collect()
    tpl = (PAPER / 'groundtwin_paper.template.md').read_text(encoding='utf-8')
    md_text = Template(tpl).substitute(N)            # fails loudly if a placeholder has no number
    used = sorted({k for k in N if f'${k}' in tpl or f'${{{k}}}' in tpl})
    (PAPER / 'groundtwin_paper.md').write_text(md_text, encoding='utf-8')
    build_pdf(md_text)
    lines = ['# Numbers in the paper and their source', '', 'Generated by pipeline/12_paper.py. Every number in the paper is '
             'substituted from these keys; files are in docs/data/.', '', '| Key | Value | Source (file: key) |', '|---|---|---|']
    lines += [f"| {k} | {N[k].replace(chr(10), ' / ').replace('|', '¦')} | {SRC[k]} |" for k in used]
    (PAPER / 'numbers.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{len(used)} numbers substituted; PDF written')


if __name__ == '__main__':
    main()
