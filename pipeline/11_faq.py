# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Builds docs/data/faq.json for the 'Ask GroundTwin' help box (no live AI, no server).
Facts come from PROJECT_EXPLAINED.txt (verified-facts section) and CLAUDE.md; every number is read from docs/data/*.json."""
import json
from common import SITE_DATA

OFFICIAL, RESULT, METHOD = 'Official source', 'Our result', 'Our method'
L = dict(  # official pages, each checked to open (HTTP 200 and the right page title) on 15 Nov 2026
    minirf=('NASA: Mini-RF', 'https://science.nasa.gov/mission/lro/mini-rf/'),
    lro=('NASA: Lunar Reconnaissance Orbiter', 'https://science.nasa.gov/mission/lro/'),
    pds=('PDS Geosciences: LRO data', 'https://pds-geosciences.wustl.edu/missions/lro/'),
    diviner=('PDS Geosciences: Diviner', 'https://pds-geosciences.wustl.edu/missions/lro/diviner.htm'),
    lola=('PDS Geosciences: LOLA', 'https://pds-geosciences.wustl.edu/missions/lro/lola.htm'),
    rcm=('CSA: RADARSAT Constellation Mission', 'https://www.asc-csa.gc.ca/eng/satellites/radarsat/'),
    rcm_ard=('RCM CEOS-ARD open data (AWS registry)', 'https://registry.opendata.aws/rcm-ceos-ard/'),
    iau=('IAU / USGS Gazetteer of Planetary Nomenclature', 'https://planetarynames.wr.usgs.gov'),
    nae=('NASA Planetary Analog Explorer', 'https://science.nasa.gov/solar-system/analog-explorer/'),
    tadp=('USGS Terrestrial Analog Data Portal', 'https://tadp.astrogeology.usgs.gov'),
    usgs_analogs=('USGS: Terrestrial Analogs', 'https://www.usgs.gov/science/science-explorer/planetary-science/terrestrial-analogs'),
    gpm=('NASA GPM', 'https://gpm.nasa.gov'),
    earthdata=('NASA Earthdata Search', 'https://search.earthdata.nasa.gov'),
    worldview=('NASA Worldview', 'https://worldview.earthdata.nasa.gov'),
    gibs=('NASA GIBS', 'https://gibs.earthdata.nasa.gov'),
    lcross=('NASA: LCROSS', 'https://science.nasa.gov/mission/lcross/'),
    artemis=('NASA: Artemis', 'https://www.nasa.gov/artemis/'),
    nisar=('NASA: NISAR', 'https://science.nasa.gov/mission/nisar/'),
    cop_dem=('Copernicus DEM (Copernicus Data Space)', 'https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM'),
    s2=('ESA: Sentinel-2', 'https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-2/'),
    spudis=('Spudis et al. 2013, JGR Planets (doi:10.1002/jgre.20156)', 'https://doi.org/10.1002/jgre.20156'),
    github=('GroundTwin code on GitHub', 'https://github.com/zhureswe/groundtwin'),
)


def load(name):
    return json.loads((SITE_DATA / f'{name}.json').read_text(encoding='utf-8'))


def pct(x, d=1):
    return f'{x * 100:.{d}f}%'


def build():
    e, m, v, b = load('earth_cpr'), load('moon_targets'), load('validation'), load('blind_test')
    g, r, p, w, sc, T = load('mangystau'), load('references'), load('polarimetry'), load('wavelength'), load('showcase'), load('targets')
    C, PC = e['classes'], p['earth']['classes']
    craters = [t for t in m['targets'] if t['ies'] is not None]
    sh = next(t for t in m['targets'] if t['name'] == 'Shackleton')
    cab = next(t for t in m['targets'] if t['name'] == 'Cabeus')
    lab = lambda tk: T['targets'][tk]['label']
    mgs_ref = next(x for x in r['rows'] if x['place'].startswith('Mangystau'))
    ex = load('explanations')
    tp = lambda x: f"top {x:.1f}%" if x >= 0.1 else f"top {x:.3f}%"
    top_line = lambda tk: '; '.join(f"{x['rank']}. {x['region']} (S {x['S']:.2f}, rank #{e['position']:,} of {e['n_cells']:,}, {tp(e['top_percent'])} of land cells)"
                                    for x, e in zip(sc['top'][tk], ex['top'][tk]))
    card = {c['key']: c for c in sc['cards']}
    gold = {t['target']: t for t in p['moon']['targets'] if t['target'] in p['golden_case']['moon']}
    lim = list(w['rcm']['h_cm_at_filter_limits'].items())

    q = []
    add = lambda question, kw, answer, label, links=(), section=None: q.append(dict(
        q=question, keywords=kw, a=answer, label=label, links=[dict(text=L[k][0], url=L[k][1]) for k in links], section=section))

    # --- about the project
    add('What is GroundTwin?', ['what', 'groundtwin', 'about', 'project', 'idea'],
        "GroundTwin is Earth's ground truth for the Moon and Mars. Lunar radar can mistake rocks for ice; we measure the same "
        'kind of radar signal on Earth, where we know the answer, and use it to read the Moon. It also maps Earth places that '
        'resemble the Moon and Mars, and tests Mangystau in Kazakhstan as a field twin of Mars.', METHOD, section='#home')
    add('Do you build a radar?', ['build', 'radar', 'satellite', 'own'],
        'No. The radars already fly: Canada\'s RCM satellites over Earth and the Mini-RF radar on NASA\'s LRO over the Moon. '
        'We download their open data, our code computes the numbers, and the website shows them.', METHOD, ['rcm', 'minirf'])
    add('Why does a Moon base need ice?', ['ice', 'water', 'base', 'why', 'fuel', 'oxygen'],
        'Ice is water: drinking water, oxygen to breathe and rocket fuel (hydrogen and oxygen). Shipping water from Earth is very '
        'expensive, so a base should be near ice. NASA has named 9 candidate Artemis III regions near the lunar south pole (October 2024).',
        OFFICIAL, ['artemis'])
    add('Was water really found on the Moon?', ['lcross', 'cabeus', 'water', 'found', 'impact'],
        'On 9 October 2009 NASA\'s LCROSS mission crashed a rocket stage into Cabeus crater and found water in the ejected plume.',
        OFFICIAL, ['lcross'])
    add('What is an analog site?', ['analog', 'analogue', 'definition', 'training'],
        'An Earth place that resembles the Moon or Mars in some way, used to test rovers, instruments and spacesuits. No place on '
        'Earth matches in everything, so the key question is: similar in what, and how much?', METHOD)
    add('Who is GroundTwin for?', ['audience', 'users', 'who', 'for'],
        'Landing-site teams at agencies and companies, engineers testing rovers and instruments, analog researchers, and students. '
        'It is free, open and needs no login.', METHOD)

    # --- radar
    add('What is CPR?', ['cpr', 'circular', 'polarization', 'ratio', 'twist'],
        'CPR (circular polarization ratio) = echo that kept the same "twist" ÷ echo whose twist flipped. Smooth ground flips the twist '
        '(low CPR); rocks and ice keep part of it (high CPR). So high CPR means rocks OR ice.', METHOD, ['minirf'], '#radar')
    add('Why does radar confuse ice and rocks?', ['confuse', 'rocks', 'rock', 'ice', 'debate', 'problem'],
        'Both rough rocks and ice keep the twist of the radar wave, so both give high CPR. Spudis et al. (2013) found "anomalous" '
        'polar craters bright only inside; other scientists (Eke et al. 2014) showed rough slopes and rocks can also be bright. '
        'The debate is not settled.', OFFICIAL, ['spudis'], '#radar')
    add('Why RCM and Mini-RF?', ['rcm', 'mini-rf', 'minirf', 'compact', 'hybrid', 'same'],
        'Canada\'s RCM and NASA\'s Mini-RF both use compact (hybrid) polarimetry, so they measure the same CPR. On Earth we know where '
        f"glaciers, rock fields and plains are. RCM is C-band ({w['rcm']['wavelength_cm']} cm); Mini-RF is S-band "
        f"({w['minirf']['wavelength_cm']} cm, incidence {w['minirf']['incidence_deg']:.0f}°).", OFFICIAL, ['rcm', 'minirf'], '#radar')
    add('What CPR did you measure on Earth?', ['earth', 'cpr', 'result', 'glacier', 'smooth', 'ruler'],
        f"Median CPR by class from real RCM scenes ({len(e['sites'])} sites, {e['convention']}): smooth ground {C['smooth']['median']:.2f}, "
        f"rock fields {C['rough_rock']['median']:.2f}, glacier ice {C['ice']['median']:.2f}. The order smooth < rock < ice holds.",
        RESULT, ['rcm_ard'], '#radar')
    add('What is the Ice Evidence Score?', ['ies', 'score', 'evidence', 'clues', 'three'],
        f"An evidence score from 0 to 3 for each crater: +1 if CPR inside / outside > {m['ratio_threshold']} (Mini-RF), +1 if the floor "
        f"slope is below the median of all craters ({m['slope_threshold_deg']:.2f}°, LOLA), +1 if Tmax < {m['cold_threshold_k']} K (Diviner). "
        'It means "consistent with ice", not a probability and not proof.', METHOD, ['minirf', 'lola', 'diviner'], '#radar')
    add('Which lunar craters score highest?', ['crater', 'craters', 'best', 'highest', 'shackleton', 'moon', 'result'],
        f"{sum(t['ies'] >= 2 for t in craters)} of {len(craters)} craters have at least 2 of 3 clues: "
        + ', '.join(t['name'] for t in craters if t['ies'] >= 2)
        + f". Shackleton: CPR inside {sh['cpr_in']:.2f} vs outside {sh['cpr_out']:.2f}, Tmax {sh['tmax_k']:.0f} K, score {sh['ies']}/3. "
        + f"Cabeus fails the cold clue (median Tmax {cab['tmax_k']:.0f} K) although {cab['frac_floor_below_110k'] * 100:.0f}% of its floor stays below "
        f"{m['cold_threshold_k']} K; LCROSS found water there. Mountains (Mons Malapert, Mons Mouton) are not scored.", RESULT, ['minirf', 'diviner', 'lola', 'lcross'], '#radar')
    add('Did you prove there is ice on the Moon?', ['prove', 'proof', 'confirmed', 'probability', 'sure'],
        'No. We show which places are consistent with ice. Every score is an evidence score 0–3, never a probability.', METHOD, section='#radar')
    add('What are DOP and the m-χ method?', ['dop', 'chi', 'm-chi', 'polarization', 'degree', 'ellipticity', 'alpha'],
        'm is the degree of polarization (DOP) and χ the ellipticity angle, both computed from compact-pol Stokes parameters. '
        'We do not compute the Cloude–Pottier α angle, because it needs full (4-channel) polarimetry.', METHOD, section='#radar')
    add('Does the CPR > 1 and DOP < 0.13 test find ice?', ['criterion', 'dop', '0.13', 'sinha', 'chandrayaan', 'lava'],
        f"In our C-band RCM data it barely separates ice from lava: cells passing both tests — ice {pct(PC['ice']['frac_criterion'])}, "
        f"lava/rock {pct(PC['rough_rock']['frac_criterion'])}, smooth {pct(PC['smooth']['frac_criterion'], 2)}. On the Moon: "
        + '; '.join(f"{k} floor {pct(t['inside']['frac_criterion'], 2)} vs outside {pct(t['outside']['frac_criterion'], 2)}" for k, t in gold.items())
        + f". χ separates the classes better (median smooth {PC['smooth']['chi_median_of_sites_deg']:.0f}°, rock "
        f"{PC['rough_rock']['chi_median_of_sites_deg']:.0f}°, ice {PC['ice']['chi_median_of_sites_deg']:.0f}°). One radar clue is not enough. "
        'The criterion is from Sinha et al. (2026), npj Space Exploration, doi:10.1038/s44453-026-00038-9 (Chandrayaan-2 DFSAR, L-band), so the wavelength differs.', RESULT, section='#radar')
    add('Why do wavelengths matter?', ['wavelength', 'band', 'rayleigh', 'c-band', 's-band', 'roughness'],
        f"Radar is most sensitive to roughness near its wavelength. Rayleigh threshold h = λ/(8 cos θ): RCM {lim[0][1]}–{lim[1][1]} cm "
        f"({lim[0][0]}–{lim[1][0]}°), Mini-RF {w['minirf']['h_cm']} cm. So we compare the order of classes and the inside/outside "
        'contrast, not exact CPR values. No C-to-S conversion factor is claimed.', RESULT, section='#method')
    add('Why are Devon Island and Haughton not in the radar ruler?', ['devon', 'haughton', 'penny', 'missing', 'scene'],
        'Our code found no usable open RCM scene for ' + ', '.join(s.replace('_', ' ').title() for s in e['sites_without_usable_scene'])
        + '. We calibrate on Canadian glaciers (Columbia, Clemenceau, Wapta), lava fields (Nisga\'a, Edziza), dunes and plains instead.',
        RESULT, ['rcm_ard'])
    add('What do recent missions say about lunar ice?', ['shadowcam', 'danuri', 'recent', '2026', 'news'],
        'ShadowCam (NASA, on Korea\'s Danuri) found no broad surface deposits above 20–30% ice, only small 20–50 m patches above 10% '
        '(University of Hawaiʻi, 2026). Chandrayaan-2 DFSAR suggested possible subsurface ice in 4 doubly shadowed craters '
        '(Sinha et al. (2026), npj Space Exploration, doi:10.1038/s44453-026-00038-9).', OFFICIAL)

    # --- analog engine
    add('How does the Analog Engine work?', ['analog', 'engine', 'similarity', 'formula', 'score', 'percentile'],
        f"Each of {sc['n_cells']:,} land cells (0.5°) gets percentiles p for 7 features: dryness, no plants, day–night swing, cold, dust, "
        'rough terrain, elevation. Each target has a profile t, each mission mode has weights w: s_i = 1 − |p_i − t_i|, '
        'S = Σ w_i s_i / Σ w_i. The browser computes S live.', METHOD, ['gpm', 'earthdata'], '#explore')
    add('How do I use the Explore Earth page?', ['explore', 'map', 'use', 'how', 'click', 'mode'],
        'Choose a target (Moon south pole, Mars Gale or Jezero) and a mission mode. The map recolours; click any land cell to see '
        'its score, a radar chart against the target, what matches and what differs. The Top 10 list is clickable.', METHOD, section='#explore')
    add('What are the mission modes?', ['modes', 'science', 'operations', 'construction', 'resources', 'weights'],
        'Science, Rover operations, Base construction, Ice & resources. Each changes the feature weights (for example roughness '
        'matters most for rovers, cold for resources). All weights are in targets.json and on the site.', METHOD, section='#explore')
    add('Which places are most like the Moon?', ['moon', 'top', 'best', 'places', 'twin'],
        f"Top 5 by formula for {lab('moon_south_pole')} (Science mode): {top_line('moon_south_pole')}.", RESULT, section='#explore')
    add('Which places are most like Mars?', ['mars', 'top', 'best', 'places', 'gale', 'jezero'],
        f"Top 5 by formula for {lab(sc['mars_target'])} (Science mode): {top_line(sc['mars_target'])}. {sc['mars_choice_reason']}",
        RESULT, section='#explore')
    add('How did you validate the Analog Engine?', ['validation', 'lift', 'test', 'check', 'known'],
        f"With {len(v['known_sites'])} known analog sites (NASA Planetary Analog Explorer, USGS). Lift = share in the top 10% ÷ 0.10. "
        f"Science mode: Moon ×{v['lift']['moon_south_pole']['science']} (p {v['p_values']['moon_south_pole']['science']}), "
        f"Gale ×{v['lift']['mars_gale']['science']}, Jezero ×{v['lift']['mars_jezero']['science']} — weak. Average rank is clearly better "
        f"than random (~50%): Gale top {v['mean_top_percent']['mars_gale']['science']}% (p {v['mean_top_percent_p']['mars_gale']['science']}), "
        f"Jezero top {v['mean_top_percent']['mars_jezero']['science']}% (p {v['mean_top_percent_p']['mars_jezero']['science']}).",
        RESULT, ['nae', 'tadp'], '#method')
    add('What is the blind test?', ['blind', 'leave-one-out', 'recognised', 'loo'],
        f"Each known site is hidden, a profile is built from the others, and we check if the hidden site lands in the top 10%. "
        f"Mars analogs: recognised {b['groups']['mars']['recognised']} of {b['groups']['mars']['total']} (chance ≈ "
        f"{b['groups']['mars']['expected_by_chance']}, p = {b['groups']['mars']['p_value_binomial']}). All analogs: "
        f"{b['groups']['all']['recognised']} of {b['groups']['all']['total']}. Caveat: several sites cluster in the US Southwest.",
        RESULT, section='#method')
    add('Where do the known analog sites come from?', ['known', 'sites', 'source', 'usgs', 'nasa', 'catalog'],
        'NASA Planetary Analog Explorer and the USGS Terrestrial Analog Data Portal, plus reference sites (MDRS, San Rafael Swell, '
        'Devon Island, Haughton). Coordinates are from Wikipedia or the USGS API, recorded per site.', OFFICIAL, ['nae', 'tadp'])
    add('What about Cinder Lake and Meteor Crater?', ['cinder', 'meteor', 'arizona', 'apollo', 'artemis', 'training'],
        'USGS blasted the Cinder Lake Crater Field in the late 1960s as a lunar training site for Apollo astronauts; USGS says it is '
        'used today to train and test Artemis astronauts. NASA astronauts also trained at Meteor Crater. In our engine (Moon, Science): '
        + '; '.join(f"{x['place']} S {x['S']:.2f}, rank #{x['position']:,}, top {x['top_percent']}% of land cells" for x in card['moon_reference']['rows'])
        + ' — they were chosen for crater geology, which our 7 features do not measure.', OFFICIAL, ['usgs_analogs'], '#explore')
    add('What about MDRS in Utah?', ['mdrs', 'utah', 'san rafael', 'mars society'],
        'MDRS is a Mars Society station for Mars-mission training (not a NASA station); Utah is in the NASA Planetary Analog Explorer. '
        f"For {lab(sc['mars_target'])}: " + '; '.join(f"{x['place']} S {x['S']:.2f}, rank #{x['position']:,}, top {x['top_percent']}% of land cells" for x in card['mars_reference']['rows']) + '.',
        RESULT, ['nae'], '#explore')

    # --- Mangystau
    add('Why Mangystau?', ['mangystau', 'kazakhstan', 'why', 'tethys'],
        'Mangystau is the floor of the ancient Tethys Sea: layered sedimentary rocks (Bozzhyra, Sherkala), salt flats (Tuzbair), '
        'stone concretions (Torysh) and the Karagiye Depression about 132 m below sea level, in a dry land with almost no plants. '
        'We found no scientific study of it as a Mars analog — only travel writing.', OFFICIAL, section='#mangystau')
    add('How Mars-like is Mangystau by your numbers?', ['mangystau', 'rank', 'score', 'result', 'top'],
        f"Mangystau ranks #{card['mangystau']['rows'][0]['position']:,} of {sc['n_cells']:,}, in the top {g['rank_vs_mars']['mars_gale']}% of Earth's land cells for Gale and top {g['rank_vs_mars']['mars_jezero']}% "
        f"for Jezero (Science mode). Against Gale: S {mgs_ref['mars_gale']['S']}, cosine {mgs_ref['mars_gale']['cosine']}. It ranks above "
        'the Utah and Devon references in our table.', RESULT, section='#mangystau')
    add('How is Mangystau NOT like Mars?', ['different', 'not', 'unlike', 'blueberries', 'concretions'],
        'Torysh concretions are metres across and sandstone; Opportunity\'s "blueberries" are millimetres and hematite. Tethys was a '
        'sea; Gale and Jezero held lakes. Earth has air, warmth, occasional rain and life, and the ages differ.', METHOD, section='#mangystau')
    add('What data did you use for Mangystau?', ['mangystau', 'data', 'dem', 'sentinel', 'salt'],
        f"Copernicus DEM (elevation, slopes), NASA MODIS (day–night temperature, NDVI), NASA GPM (rain), Sentinel-2 (true colour and an "
        f"approximate SWIR salt index). Region averages: {g['region_stats']['precip_mm_yr']:.0f} mm rain per year, max NDVI "
        f"{g['region_stats']['ndvi_max']:.2f}.", RESULT, ['cop_dem', 's2', 'gpm'], '#mangystau')

    # --- data
    add('Which NASA data do you use?', ['nasa', 'data', 'datasets', 'lro', 'modis'],
        'LRO Mini-RF (lunar radar), LRO Diviner (temperature), LRO LOLA (topography), MODIS (temperature, vegetation, dust), '
        'GPM IMERG (rain), and the NASA GIBS Blue Marble basemap.', OFFICIAL, ['lro', 'pds', 'gpm', 'gibs'], '#method')
    add('Which CSA and ESA data do you use?', ['csa', 'esa', 'canada', 'copernicus', 'rcm', 'sentinel'],
        'CSA: RADARSAT Constellation Mission compact-pol images (open CEOS-ARD). ESA Copernicus: Sentinel-2 imagery and Copernicus DEM. '
        'Also USGS GMTED2010 elevation.', OFFICIAL, ['rcm', 'rcm_ard', 's2', 'cop_dem'], '#method')
    add('Where do crater coordinates come from?', ['coordinates', 'iau', 'gazetteer', 'crater'],
        'From the IAU Gazetteer of Planetary Nomenclature (USGS). Earth site coordinates come from official or recorded sources '
        '(CGNDB, Wikipedia, OpenStreetMap, USGS), listed with each site.', OFFICIAL, ['iau'])
    add('Can I explore the raw data myself?', ['raw', 'download', 'earthdata', 'worldview'],
        'Yes: NASA Earthdata Search and Worldview give the Earth data; PDS Geosciences gives the LRO data; the RCM archive is open on AWS.',
        OFFICIAL, ['earthdata', 'worldview', 'pds', 'rcm_ard'])

    # --- limits, team, AI
    add('What can Earth never reproduce?', ['limits', 'limitations', 'gravity', 'vacuum', 'radiation', 'cannot'],
        'Gravity six times lower (Moon) or almost three times lower (Mars), vacuum or very thin air, no protection from space '
        'radiation, and sharp lunar dust. Also: different radar wavelengths, cleaner Earth ice, a coarse 0.5° grid and target '
        'profiles chosen by the team.', METHOD, section='#method')
    add('What is next for GroundTwin?', ['future', 'next', 'roadmap', 'nisar', 'plans'],
        'More reference sites and craters, an S-band Earth reference from NISAR (NASA and ISRO, wavelength close to Mini-RF), a paper '
        'with a DOI, and a Kazakh and Russian version for schools.', METHOD, ['nisar'])
    add('Who made GroundTwin?', ['team', 'who', 'code influence', 'authors', 'members'],
        'Team Code Influence from Kazakhstan, for the NASA Space Apps Challenge 2026. The code is open on GitHub (zhureswe/groundtwin).',
        METHOD, ['github'], '#about')
    add('How did you use AI?', ['ai', 'claude', 'artificial', 'intelligence', 'chatgpt'],
        'We used Claude (Anthropic) to help write Python and HTML/JavaScript code, debug, and edit English text. The concept, the choice '
        'of sites and data, all checks and interpretation, and the design are our own. No AI-generated images or videos are used. '
        'This help box is not a live AI: it searches prepared answers.', METHOD, section='#about')
    add('Is this an AI model that predicts ice?', ['model', 'trained', 'machine learning', 'predict', 'neural'],
        'No. GroundTwin uses a transparent similarity formula and an evidence score, both checked against known sites. Nothing is a '
        'trained AI model.', METHOD, section='#method')
    add('Is the code open? How do I run it?', ['code', 'open', 'github', 'run', 'license', 'pipeline'],
        'Yes, MIT licence. Python scripts pipeline/01–11 recompute every number; the static site in /docs reads only their JSON output.',
        METHOD, ['github'])
    add('How do I compare two places?', ['compare', 'comparison', 'versus', 'side by side', 'two places'],
        'Type "compare A and B" or "A vs B" with two places of the same kind: two lunar targets (e.g. Shackleton and Faustini), two '
        'Earth radar sites (e.g. Columbia Icefield and Edziza Lava Field) or two analog places (e.g. Mangystau and San Rafael Swell). '
        'The table uses numbers from our data files.', METHOD)
    add('Is GroundTwin endorsed by NASA?', ['endorsed', 'official', 'nasa', 'affiliated'],
        'No. GroundTwin uses open NASA, CSA, ESA and USGS data but is not endorsed by NASA or any space agency.', METHOD, section='#about')
    return q


def main():
    q = build()
    popular = ['What is GroundTwin?', 'What is CPR?', 'What is the Ice Evidence Score?', 'Which lunar craters score highest?',
               'How does the Analog Engine work?', 'Why Mangystau?', 'How do I compare two places?', 'Which NASA data do you use?', 'How did you use AI?']
    assert all(p in {x['q'] for x in q} for p in popular)
    out = dict(demo=False, note='Answers prepared with AI assistance from our verified data', popular=popular, items=q)
    (SITE_DATA / 'faq.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    print(len(q), 'answers')


if __name__ == '__main__':
    main()
