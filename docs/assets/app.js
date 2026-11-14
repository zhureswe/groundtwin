// Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
// All numbers come from docs/data/*.json (written by the Python pipeline). Nothing is hard-coded here.
'use strict';

const DATA = {};
const FILES = ['earth_cpr', 'moon_targets', 'analog_grid', 'targets', 'validation', 'mangystau', 'references', 'blind_test', 'polarimetry', 'wavelength', 'showcase', 'faq'];
const CLASS_COLOR = { smooth: '#8c9bab', rough_rock: '#f0a35e', ice: '#4fd1e8' };
const CLASS_NAME = { smooth: 'smooth ground', rough_rock: 'rock field', ice: 'glacier ice' };
const FEAT_NAME = { aridity: 'Dry', barren: 'No plants', thermal_range: 'Day–night swing', cold: 'Cold',
  dust: 'Dust', roughness: 'Rough terrain', elevation: 'High altitude' };
const IES_COLOR = ['#3a4354', '#2e6f86', '#3fa9c9', '#8beaff'];
const NA_COLOR = '#6b7486';   // targets where the crater-floor test does not apply (mountains)
const hasIes = (t) => t.ies != null;
const $ = (s) => document.querySelector(s);
const fmt = (x, d = 2) => (x == null || isNaN(x)) ? '–' : Number(x).toFixed(d);
const pretty = (s) => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
const isDemo = (k) => DATA[k] && DATA[k].demo;

async function loadAll() {
  await Promise.all(FILES.map(async (f) => {
    try {
      const r = await fetch(`data/${f}.json`, { cache: 'no-store' });
      DATA[f] = r.ok ? await r.json() : null;
    } catch (e) { DATA[f] = null; }
  }));
  if (FILES.some(isDemo)) $('#demo-banner').hidden = false;
}

/* ---------------- router ---------------- */
const rendered = {};
function show(page) {
  if (!document.querySelector(`[data-page="${page}"]`)) page = 'home';
  document.querySelectorAll('.page').forEach((p) => { p.hidden = p.dataset.page !== page; });
  document.querySelectorAll('#navlinks a').forEach((a) => a.classList.toggle('active', a.getAttribute('href') === '#' + page));
  $('#navlinks').classList.remove('open');
  window.scrollTo(0, 0);
  const fn = { home: renderHome, radar: renderRadar, explore: renderExplore, mangystau: renderMangystau, method: renderMethod }[page];
  if (fn && !rendered[page]) { rendered[page] = true; fn(); }
  if (page === 'explore' && MAP.map) setTimeout(() => MAP.map.invalidateSize(), 50);
}

/* ---------------- home ---------------- */
function renderHome() {
  const s = [];
  const e = DATA.earth_cpr, m = DATA.moon_targets, v = DATA.validation, g = DATA.mangystau;
  if (e) s.push([e.sites.length, 'Earth radar reference sites']);
  if (m) { const c = m.targets.filter(hasIes); s.push([`${c.filter((t) => t.ies >= 2).length} / ${c.length}`, 'lunar craters with ≥2 of 3 ice clues']); }
  if (v && v.mean_top_percent) s.push([`top ${fmt(v.mean_top_percent.mars_gale.science, 0)}%`,
    `average rank of known Mars analog sites for Gale (random places: ~50%, p = ${v.mean_top_percent_p.mars_gale.science})`]);
  if (g && g.rank_vs_mars && g.rank_vs_mars.mars_gale != null) s.push([`top ${fmt(g.rank_vs_mars.mars_gale, 0)}%`, 'of Earth for Mars · Gale: where Mangystau ranks']);
  $('#stats').innerHTML = s.map(([b, t]) => `<div class="stat"><b>${b}</b><span>${t}</span></div>`).join('');
}

/* ---------------- radar twin ---------------- */
let selCrater = null;
function renderRadar() {
  const m = DATA.moon_targets;
  if (!m) { $('#crater-card').innerHTML = '<p class="muted">moon_targets.json not found yet.</p>'; drawRuler(); return; }
  drawPolar(m);
  const best = [...m.targets].sort((x, y) => (y.ies ?? -1) - (x.ies ?? -1) || (y.cpr_in / y.cpr_out) - (x.cpr_in / x.cpr_out))[0];
  selectCrater(best.name);
  drawPolCheck();
}

function drawPolCheck() {
  const d = DATA.polarimetry;
  if (!d) { $('#polcheck').innerHTML = '<p class="muted">polarimetry.json not found yet.</p>'; return; }
  const pct = (x, k = 1) => `${fmt(x * 100, k)}%`;
  const gold = new Set([...d.golden_case.earth, ...d.golden_case.moon]);
  const head = '<tr><th>Place</th><th>Radar</th><th>CPR</th><th>DOP m</th><th>χ</th><th>CPR&gt;1</th><th>DOP&lt;0.13</th><th>Both</th></tr>';
  const row = (name, radar, x, g) => `<tr${g ? ' class="gold"' : ''}><td>${name}</td><td class="small">${radar}</td><td>${fmt(x.cpr_median)}</td><td>${fmt(x.dop_median)}</td>
    <td>${fmt(x.chi_median_deg, 0)}°</td><td>${pct(x.frac_cpr_gt1, 0)}</td><td>${pct(x.frac_dop_lt013)}</td><td><b>${pct(x.frac_criterion)}</b></td></tr>`;
  const earth = d.earth.sites.map((s) => row(`${pretty(s.site)} <span class="muted small">(${CLASS_NAME[s.cls]})</span>`, 'RCM C-band', s, gold.has(s.site)));
  const moon = d.moon.targets.filter((t) => gold.has(t.target)).flatMap((t) => [
    row(`${t.target} floor`, 'Mini-RF S-band', t.inside, true), row(`${t.target} outside rim`, 'Mini-RF S-band', t.outside, false)]);
  $('#polcheck').innerHTML = `<table class="cmp"><thead>${head}</thead><tbody>${earth.join('')}${moon.join('')}</tbody></table>
    <p class="note">Shares are of radar cells passing each test. Criterion from ${d.criterion.source}. χ: ellipticity angle (negative = mostly single-bounce, positive = same-sense dominated). Highlighted rows: golden case (Earth ice and lava → Shackleton and Faustini). ${d.convention}</p>`;
}

function polarXY(lat, lon, cx, cy, R, maxColat) {
  const r = (90 + lat) / maxColat * R;              // lat is negative (south)
  const t = lon * Math.PI / 180;
  return [cx + r * Math.sin(t), cy - r * Math.cos(t)];
}

function drawPolar(m) {
  const svg = $('#polar'), cx = 260, cy = 260, R = 215, maxC = 8.5;   // map edge = 81.5°S
  const edge = -90 + maxC;
  let h = `<circle cx="${cx}" cy="${cy}" r="${R}" fill="#0c1220" stroke="#243049"/>`;
  for (const lat of [-89, -88, -87, -86, -85, -84, -83, -82]) {
    const r = (90 + lat) / maxC * R;
    h += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#1d2840" stroke-dasharray="3 4"/>`;
    if (lat % 2 === 0) h += `<text x="${cx + 4}" y="${cy - r - 3}">${Math.abs(lat)}°S</text>`;
  }
  for (const [lon, lab] of [[0, '0°'], [90, '90°E'], [180, '180°'], [-90, '90°W']]) {
    const [x, y] = polarXY(edge, lon, cx, cy, R, maxC);
    h += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="#1d2840"/>`;
    const [lx, ly] = polarXY(edge + 0.6, lon, cx, cy, R, maxC);
    h += `<text x="${lx}" y="${ly + 4}" text-anchor="middle">${lab}</text>`;
  }
  h += `<circle cx="${cx}" cy="${cy}" r="2.5" fill="#93a0b5"/><text x="${cx - 6}" y="${cy + 16}" text-anchor="end">South Pole</text>`;
  m.targets.forEach((t) => {
    const [x, y] = polarXY(t.lat, t.lon, cx, cy, R, maxC);
    const rad = hasIes(t) ? 8 + t.ies * 2 : 7;
    const right = x >= cx;
    h += `<circle class="crater" data-name="${t.name}" cx="${x}" cy="${y}" r="${rad}" fill="${hasIes(t) ? IES_COLOR[t.ies] : NA_COLOR}" stroke="#0a0e16" stroke-width="1.5"><title>${t.name}: ${hasIes(t) ? t.ies + '/3' : 'n/a (not a crater)'}</title></circle>`;
    h += `<text class="lbl" x="${x + (right ? rad + 5 : -rad - 5)}" y="${y + 4}" text-anchor="${right ? 'start' : 'end'}">${t.name}</text>`;
  });
  if (m.demo) h += `<text x="${cx}" y="${cy + R - 14}" text-anchor="middle" style="fill:#f6c445;font-size:13px;font-weight:600">DEMO DATA</text>`;
  svg.innerHTML = h;
  svg.querySelectorAll('.crater').forEach((c) => c.addEventListener('click', () => selectCrater(c.dataset.name)));
  $('#polar-legend').innerHTML = [0, 1, 2, 3].map((i) => `<span><i style="background:${IES_COLOR[i]}"></i>${i}/3 ice clues</span>`).join('') +
    `<span><i style="background:${NA_COLOR}"></i>mountain (n/a)</span><span>Positions: polar view, ${Math.abs(edge)}°S to the pole</span>`;
}

function earthTwin(cpr) {
  const e = DATA.earth_cpr;
  if (!e) return null;
  return [...e.sites].sort((a, b) => Math.abs(a.median - cpr) - Math.abs(b.median - cpr))[0];
}

function selectCrater(name) {
  const m = DATA.moon_targets, t = m.targets.find((x) => x.name === name);
  selCrater = t;
  document.querySelectorAll('#polar .crater').forEach((c) => c.classList.toggle('sel', c.dataset.name === name));
  const ratio = t.cpr_in / t.cpr_out, scored = hasIes(t), c = t.clues || {};
  const verdict = !scored ? 'Not a crater — the floor-vs-surroundings test does not apply'
    : t.ies === 3 ? 'Strongly consistent with ice' : t.ies === 2 ? 'Possibly icy — needs more evidence' : 'More likely rocks, slopes or too warm';
  const tin = earthTwin(t.cpr_in), tout = earthTwin(t.cpr_out);
  const clue = (ok, title, sub) => `<div class="clue"><span class="ic ${!scored ? '' : ok ? 'ok' : 'bad'}">${!scored ? '·' : ok ? '✓' : '✕'}</span><div><b>${title}</b><span>${sub}</span></div></div>`;
  $('#crater-card').innerHTML = `
    <div class="card-h"><h3>${t.name}</h3><span class="muted small">${t.kind}</span></div>
    <div class="ies"><span class="score" style="color:${scored ? ['#93a0b5', '#5fb7cf', '#4fd1e8', '#8beaff'][t.ies] : NA_COLOR}">${scored ? t.ies + '/3' : 'n/a'}</span><span class="verdict">${verdict}</span></div>
    ${clue(c.radar, 'Radar clue — Mini-RF', `CPR inside ${fmt(t.cpr_in)} vs outside ${fmt(t.cpr_out)} (×${fmt(ratio)}; needs > ×${m.ratio_threshold}). Rocks would be bright outside too.`)}
    ${clue(c.smooth, 'Smooth floor — LOLA', `Median slope ${fmt(t.slope_deg, 1)}° (threshold ${fmt(m.slope_threshold_deg, 1)}°). Smooth ground makes rocks a less likely cause.`)}
    ${clue(c.cold, 'Cold trap — Diviner', `Max temperature ${Math.round(t.tmax_k)} K (water ice stays stable below ${m.cold_threshold_k} K).`)}
    ${tin ? `<div class="twin">The crater floor echoes like <b>${pretty(tin.site)}</b> (${CLASS_NAME[tin.cls]}).<br>
      Outside the rim it echoes like <b>${pretty(tout.site)}</b> (${CLASS_NAME[tout.cls]}).<br><span class="small">${twinStory(t, tin, tout)}</span></div>` : ''}
    <p class="note">Source: ${t.source}. "Consistent with ice" is not proof of ice.</p>`;
  drawRuler();
}

function twinStory(t, tin, tout) {
  if (tin.cls === tout.cls) return 'Inside and outside echo alike — the bright radar is not special to the cold floor, so it says little about ice.';
  if (tin.cls === 'ice' && t.ies >= 2) return 'An icy echo exactly where it is coldest — the pattern we would expect from buried ice.';
  if (tin.cls === 'ice') return 'The echo alone looks icy, but the other clues disagree — exactly why one clue is never enough.';
  return 'The floor echo matches rock or smooth ground on Earth, not glacier ice.';
}

function drawRuler() {
  const e = DATA.earth_cpr, svg = $('#ruler');
  if (!e) { svg.setAttribute('viewBox', '0 0 900 60'); svg.innerHTML = '<text x="10" y="30">earth_cpr.json not found yet.</text>'; return; }
  const order = { smooth: 0, rough_rock: 1, ice: 2 };
  const sites = [...e.sites].sort((a, b) => order[a.cls] - order[b.cls] || a.median - b.median);
  const L = 190, W = 880, top = 58, rowH = 30, xmax = 1.6;
  const H = top + sites.length * rowH + 40;
  const X = (v) => L + Math.min(v, xmax) / xmax * (W - L);
  let h = '';
  for (let v = 0; v <= xmax + 1e-9; v += 0.2) {
    h += `<line x1="${X(v)}" y1="${top - 10}" x2="${X(v)}" y2="${H - 30}" stroke="#1d2840"/>`;
    h += `<text x="${X(v)}" y="${H - 12}" text-anchor="middle">${v.toFixed(1)}</text>`;
  }
  h += `<text x="${L}" y="${H - 0}" style="font-size:11px">CPR (same-sense ÷ opposite-sense) →</text>`;
  sites.forEach((s, i) => {
    const y = top + i * rowH + rowH / 2, c = CLASS_COLOR[s.cls];
    h += `<text class="site-lbl" x="${L - 12}" y="${y + 4}" text-anchor="end">${pretty(s.site)}</text>`;
    h += `<line x1="${X(s.p25)}" y1="${y}" x2="${X(s.p75)}" y2="${y}" stroke="${c}" stroke-width="8" stroke-linecap="round" opacity=".55"/>`;
    h += `<circle cx="${X(s.median)}" cy="${y}" r="6" fill="${c}" stroke="#0a0e16" stroke-width="1.5"><title>${pretty(s.site)}: median ${fmt(s.median)}</title></circle>`;
  });
  if (selCrater) {
    const marks = [[selCrater.cpr_in, `${selCrater.name} floor (inside)`, '', top - 24], [selCrater.cpr_out, 'outside the rim', '5 4', top - 8]];
    for (const [v, lab, dash, ly] of marks) {
      const x = X(v), anchor = x > W - 220 ? 'end' : 'start', dx = anchor === 'end' ? -6 : 6;
      h += `<line x1="${x}" y1="${ly + 4}" x2="${x}" y2="${H - 30}" stroke="#ffffff" stroke-width="2" stroke-dasharray="${dash}"/>`;
      h += `<text x="${x + dx}" y="${ly}" text-anchor="${anchor}" style="fill:#fff;font-weight:600">${lab}: ${fmt(v)}</text>`;
    }
  }
  if (e.demo) h += `<text x="${L - 12}" y="${top - 24}" text-anchor="end" style="fill:#f6c445;font-weight:600">DEMO DATA</text>`;
  svg.setAttribute('viewBox', `0 0 ${W + 10} ${H + 6}`);
  svg.innerHTML = h;
  $('#ruler-note').innerHTML = `Bars: middle 50% of 100-m cells; dot: median. ${Object.entries(CLASS_COLOR).map(([k, c]) => `<span class="dot" style="background:${c}"></span>${CLASS_NAME[k]}`).join(' ')}.
    White lines: the selected lunar crater (Mini-RF). Wavelengths differ (RCM C-band ≈ 5.5 cm, Mini-RF S-band 12.6 cm), so read the <b>order</b>, not exact values. ${e.convention ? 'Channel convention: ' + e.convention + '.' : ''}`;
}

/* ---------------- explore ---------------- */
const MAP = { map: null, overlay: null, marker: null, known: null, idx: {}, scores: [], target: 'moon_south_pole', mode: 'science', chart: null };

function renderExplore() {
  const g = DATA.analog_grid, T = DATA.targets;
  if (!g || !T) { $('#place-card').innerHTML = '<p class="muted">analog_grid.json / targets.json not found yet.</p>'; return; }
  $('#target').innerHTML = Object.entries(T.targets).map(([k, t]) => `<option value="${k}">${t.label}</option>`).join('');
  $('#modes').innerHTML = Object.entries(T.modes).map(([k, m]) => `<button data-mode="${k}" class="${k === MAP.mode ? 'on' : ''}">${m.label}</button>`).join('');
  $('#target').addEventListener('change', (ev) => { MAP.target = ev.target.value; recompute(); });
  $('#modes').addEventListener('click', (ev) => {
    const b = ev.target.closest('button'); if (!b) return;
    MAP.mode = b.dataset.mode;
    $('#modes').querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b));
    recompute();
  });
  $('#known').addEventListener('change', drawKnown);

  const map = L.map('map', { worldCopyJump: false, minZoom: 1, maxZoom: 8, zoomSnap: 0.5, maxBounds: [[-85, -200], [85, 200]] }).setView([25, 20], 1.5);
  L.tileLayer('https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg',
    { attribution: 'Blue Marble imagery: NASA EOSDIS GIBS', maxNativeZoom: 8, maxZoom: 8, opacity: 0.55 }).addTo(map);
  MAP.map = map;
  g.cells.forEach((c, i) => { MAP.idx[cellKey(c[0], c[1])] = i; });
  map.on('click', (ev) => {
    const { lat, lng } = ev.latlng;
    const k = cellKey(lng, lat); const i = MAP.idx[k];
    if (i == null) { $('#place-card').innerHTML = '<p class="muted">No land cell here (ocean, or outside the grid).</p>'; return; }
    selectCell(i);
  });
  recompute();
  renderShowcase();
}

function renderShowcase() {
  const d = DATA.showcase, T = DATA.targets;
  if (!d || !T) return;
  const lab = (tk) => T.targets[tk].label;
  const chips = (fs, ok) => fs.map((f) => `<span class="chip ${ok ? 'yes' : 'no'}">${ok ? '✓' : '≠'} ${FEAT_NAME[f]}</span>`).join('');
  $('#sc-top').innerHTML = Object.entries(d.top).map(([tk, rows]) => `<div><b>${lab(tk)}</b><ol class="top10">${rows.map((r) =>
    `<li><span class="sc">${fmt(r.S)}</span>${r.region || 'Unnamed cell'} · ${ll(r.lat, r.lon)}<span class="near">${chips(r.matches, true)}${chips(r.differs, false)}</span></li>`).join('')}</ol></div>`).join('');
  $('#sc-note').innerHTML = `${d.selection} ${d.mars_choice_reason}`;
  $('#sc-cards').innerHTML = d.cards.map((c) => `<div class="card"><span class="tag ${c.target.startsWith('moon') ? 'ice' : 'mars'}">vs ${lab(c.target).split(' (')[0]}</span>
    <h3>${c.title}</h3>${c.rows.map((r) => `<p><b>${r.place}</b><br>S <b>${fmt(r.S)}</b> · cosine <b>${fmt(r.cosine)}</b> · rank <b>#${r.position.toLocaleString('en')}</b> of ${d.n_cells.toLocaleString('en')} (top ${fmt(r.top_percent, 1)}%)</p>
      <div class="chips">${chips(r.matches, true)}${chips(r.differs, false)}</div>`).join('')}
    <p class="small"><b>How it matches:</b> ${c.facts.join(' ')}</p>
    <p class="small"><b>How it doesn't:</b> ${c.not_like.join('; ')}.</p>
    <p class="note">${c.in_top ? 'In the top 5.' : 'Not in the top 5 — shown with its real rank.'} Coordinates: ${c.sites.map((s) => `${s.name} (${s.coord_source})`).join('; ')}.</p></div>`).join('');
}

function cellKey(lon, lat) {
  const s = DATA.analog_grid.cell_deg;
  return `${Math.floor((lon + 180) / s)},${Math.floor((lat + 90) / s)}`;
}

function scoreCell(c, T) {
  const prof = T.targets[MAP.target].profile, w = T.modes[MAP.mode].weights, f = DATA.analog_grid.features;
  let num = 0, den = 0; const parts = {};
  f.forEach((name, j) => {
    const s = 1 - Math.abs(c[2 + j] - prof[name]);
    parts[name] = s; num += (w[name] || 0) * s; den += (w[name] || 0);
  });
  return { S: den ? num / den : 0, parts };
}

function recompute() {
  const g = DATA.analog_grid, T = DATA.targets;
  MAP.scores = g.cells.map((c) => scoreCell(c, T).S);
  const sorted = [...MAP.scores].sort((a, b) => a - b);
  MAP.rank = MAP.scores.map((s) => lowerBound(sorted, s) / (sorted.length - 1));
  drawOverlay();
  drawTop10();
  drawKnown();
  const v = DATA.validation;
  const lift = v && v.lift[MAP.target] ? v.lift[MAP.target][MAP.mode] : null;
  const pv = (o) => (o && o[MAP.target] ? ` (p = ${o[MAP.target][MAP.mode]})` : '');
  const mr = v && v.mean_top_percent ? v.mean_top_percent[MAP.target][MAP.mode] : null;
  $('#lift-note').innerHTML = lift != null ? `Validation (${v.unique_cells_per_target ? v.unique_cells_per_target[MAP.target] + ' known-site cells' : 'known sites'}): Lift in the top ${Math.round(v.top_fraction * 100)}% = <b>×${fmt(lift, 2)}</b>${pv(v.p_values)}` +
    `${mr != null ? `; average rank top <b>${fmt(mr, 1)}%</b> (random ≈ 50%)${pv(v.mean_top_percent_p)}` : ''}.${v.demo ? ' <b style="color:#f6c445">DEMO</b>' : ''}` : '';
  if (MAP.sel != null) selectCell(MAP.sel, false);
}

function lowerBound(a, x) { let lo = 0, hi = a.length; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] < x) lo = m + 1; else hi = m; } return lo; }

function rampColor(r) {
  // r in [0,1] rank; below 0.5 transparent
  if (r < 0.5) return null;
  const stops = [[0.5, [18, 50, 74]], [0.8, [42, 143, 176]], [0.95, [79, 209, 232]], [1, [255, 255, 255]]];
  for (let i = 1; i < stops.length; i++) {
    if (r <= stops[i][0]) {
      const [a, ca] = stops[i - 1], [b, cb] = stops[i], t = (r - a) / (b - a);
      return ca.map((v, k) => Math.round(v + (cb[k] - v) * t));
    }
  }
  return [255, 255, 255];
}

function drawOverlay() {
  const g = DATA.analog_grid, s = g.cell_deg, W = 2048, H = 2048, LAT = 85.0511;
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  const ctx = cv.getContext('2d');
  const yOf = (lat) => { lat = Math.max(-LAT, Math.min(LAT, lat)); const r = lat * Math.PI / 180; return H / 2 - W / (2 * Math.PI) * Math.log(Math.tan(Math.PI / 4 + r / 2)); };
  const xOf = (lon) => (lon + 180) / 360 * W;
  g.cells.forEach((c, i) => {
    const col = rampColor(MAP.rank[i]); if (!col) return;
    const alpha = 0.35 + 0.6 * (MAP.rank[i] - 0.5) / 0.5;
    ctx.fillStyle = `rgba(${col[0]},${col[1]},${col[2]},${alpha.toFixed(2)})`;
    const x0 = xOf(c[0] - s / 2), x1 = xOf(c[0] + s / 2), y0 = yOf(c[1] + s / 2), y1 = yOf(c[1] - s / 2);
    ctx.fillRect(x0, y0, Math.max(1, x1 - x0 + 0.5), Math.max(1, y1 - y0 + 0.5));
  });
  if (g.demo) { ctx.fillStyle = 'rgba(246,196,69,.9)'; ctx.font = 'bold 40px sans-serif'; ctx.fillText('DEMO DATA', 40, H - 60); }
  const url = cv.toDataURL();
  if (MAP.overlay) MAP.overlay.setUrl(url);
  else MAP.overlay = L.imageOverlay(url, [[-LAT, -180], [LAT, 180]], { opacity: 1, interactive: false }).addTo(MAP.map);
}

function nearestKnown(lat, lon) {
  const v = DATA.validation; if (!v) return null;
  let best = null, bd = 1e9;
  v.known_sites.forEach((k) => {
    const d = haversine(lat, lon, k.lat, k.lon);
    if (d < bd) { bd = d; best = k; }
  });
  return bd < 400 ? { ...best, km: Math.round(bd) } : null;
}
function haversine(a1, o1, a2, o2) {
  const R = 6371, r = Math.PI / 180, da = (a2 - a1) * r, dob = (o2 - o1) * r;
  const h = Math.sin(da / 2) ** 2 + Math.cos(a1 * r) * Math.cos(a2 * r) * Math.sin(dob / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}
const ll = (lat, lon) => `${Math.abs(lat).toFixed(1)}°${lat >= 0 ? 'N' : 'S'}, ${Math.abs(lon).toFixed(1)}°${lon >= 0 ? 'E' : 'W'}`;

function drawTop10() {
  const g = DATA.analog_grid;
  const order = MAP.scores.map((s, i) => [s, i]).sort((a, b) => b[0] - a[0]);
  // keep top places at least ~3 cells apart so the list isn't one desert repeated
  const picked = [];
  for (const [s, i] of order) {
    const c = g.cells[i];
    if (picked.every((j) => haversine(c[1], c[0], g.cells[j][1], g.cells[j][0]) > 600)) picked.push(i);
    if (picked.length === 10) break;
  }
  $('#top10').innerHTML = picked.map((i) => {
    const c = g.cells[i], k = nearestKnown(c[1], c[0]);
    return `<li data-i="${i}"><span class="sc">${fmt(MAP.scores[i])}</span>${ll(c[1], c[0])}<span class="near">${k ? `near known analog: ${k.name}` : 'not in the known-analog list — candidate'}</span></li>`;
  }).join('');
  $('#top10').querySelectorAll('li').forEach((li) => li.addEventListener('click', () => {
    const i = +li.dataset.i, c = g.cells[i];
    MAP.map.flyTo([c[1], c[0]], 4, { duration: 0.8 }); selectCell(i);
  }));
}

function drawKnown() {
  if (MAP.known) { MAP.known.remove(); MAP.known = null; }
  const v = DATA.validation; if (!v || !$('#known').checked) return;
  MAP.known = L.layerGroup(v.known_sites.map((k) => {
    const i = MAP.idx[cellKey(k.lon, k.lat)];
    const top = i != null && MAP.rank[i] >= 1 - v.top_fraction;
    return L.circleMarker([k.lat, k.lon], { radius: 6, color: '#fff', weight: 2, fillColor: top ? '#6fcf97' : '#0a0e16', fillOpacity: 1 })
      .bindTooltip(`${k.name}${i != null ? ` — ${top ? 'in the top 10% ✓' : 'outside the top 10%'}` : ''}`);
  })).addTo(MAP.map);
}

function selectCell(i, move = true) {
  const g = DATA.analog_grid, T = DATA.targets, c = g.cells[i];
  MAP.sel = i;
  const { S, parts } = scoreCell(c, T);
  if (MAP.marker) MAP.marker.remove();
  MAP.marker = L.circleMarker([c[1], c[0]], { radius: 9, color: '#ffffff', weight: 3, fill: false }).addTo(MAP.map);
  const prof = T.targets[MAP.target].profile;
  const feats = g.features;
  const match = feats.filter((f) => parts[f] >= 0.8), diff = feats.filter((f) => parts[f] < 0.5);
  const k = nearestKnown(c[1], c[0]);
  $('#place-card').innerHTML = `
    <div class="place-h"><div><h3 style="margin:0">${ll(c[1], c[0])}</h3><span class="muted small">${k ? `${k.km} km from ${k.name}` : 'Top ' + Math.max(1, Math.round((1 - MAP.rank[i]) * 100)) + '% of Earth for this goal'}</span></div><span class="big">${fmt(S)}</span></div>
    <div class="radar-wrap"><canvas id="place-radar"></canvas></div>
    <div><b class="small">Matches</b><div class="chips">${match.map((f) => `<span class="chip yes">✓ ${FEAT_NAME[f]}</span>`).join('') || '<span class="muted small">—</span>'}</div></div>
    <div style="margin-top:8px"><b class="small">Differs</b><div class="chips">${diff.map((f) => `<span class="chip no">≠ ${FEAT_NAME[f]}</span>`).join('') || '<span class="muted small">—</span>'}</div></div>
    <div style="margin-top:8px"><b class="small">Earth can never reproduce</b><div class="chips">${T.targets[MAP.target].cannot.map((x) => `<span class="chip">${x}</span>`).join('')}</div></div>`;
  if (MAP.chart) MAP.chart.destroy();
  MAP.chart = new Chart($('#place-radar'), {
    type: 'radar',
    data: { labels: feats.map((f) => FEAT_NAME[f]), datasets: [
      { label: 'This place', data: feats.map((f, j) => c[2 + j]), borderColor: '#4fd1e8', backgroundColor: 'rgba(79,209,232,.25)', pointRadius: 2 },
      { label: T.targets[MAP.target].label, data: feats.map((f) => prof[f]), borderColor: '#ffffff', borderDash: [5, 4], backgroundColor: 'rgba(255,255,255,0)', pointRadius: 0 }] },
    options: { maintainAspectRatio: false, animation: false,
      scales: { r: { min: 0, max: 1, ticks: { display: false, stepSize: 0.25 }, grid: { color: '#243049' }, angleLines: { color: '#243049' }, pointLabels: { color: '#c3cddc', font: { size: 11 } } } },
      plugins: { legend: { labels: { color: '#c3cddc', boxWidth: 12 } } } } });
}

/* ---------------- mangystau ---------------- */
const MGS_FEATS = [['elevation_m', 'Mean elevation, m', 0], ['elevation_min_m', 'Lowest point, m', 0], ['slope_deg', 'Slope, °', 1], ['lst_range_k', 'Day–night swing, K', 1],
  ['ndvi_max', 'Max NDVI', 2], ['precip_mm_yr', 'Rain, mm/yr', 0], ['salt_index', 'Salt index*', 2]];

function renderMangystau() {
  const g = DATA.mangystau;
  if (!g) { $('#mgs-places').innerHTML = '<p class="muted">mangystau.json not found yet.</p>'; return; }
  const demo = g.demo ? ' <b style="color:#f6c445">DEMO</b>' : '';
  const r = g.rank_vs_mars || {};
  $('#mgs-rank').innerHTML = [['mars_gale', 'Mars · Gale crater'], ['mars_jezero', 'Mars · Jezero crater']].map(([k, lab]) =>
    `<div class="stat"><b>${r[k] != null ? `top ${fmt(r[k], 0)}%` : '–'}</b><span>of Earth's land cells for ${lab}: where Mangystau ranks in the Analog Engine${demo}</span></div>`).join('');
  const imgs = g.images || [];
  $('#mgs-images').innerHTML = imgs.length
    ? `<div class="figs">${imgs.map((i) => `<figure><img src="assets/img/${i.file}" alt="${i.caption}"><figcaption class="note">${i.caption}</figcaption></figure>`).join('')}</div>`
    : '<div class="placeholder">Sentinel-2 true-colour views of Mangystau will appear here.</div>';
  const row = (p) => `<tr><td>${p.name}${p.lat != null ? `<br><span class="muted small">${ll(p.lat, p.lon)}</span>` : ''}</td>${MGS_FEATS.map(([k, , d]) => `<td>${fmt(p[k], d)}</td>`).join('')}</tr>`;
  const stats = g.region_stats && Object.keys(g.region_stats).length ? row({ name: '<b>Whole region</b>', ...g.region_stats }) : '';
  $('#mgs-places').innerHTML = `<table class="cmp"><thead><tr><th>Site</th>${MGS_FEATS.map(([, lab]) => `<th>${lab}</th>`).join('')}</tr></thead>
    <tbody>${(g.places || []).map(row).join('')}${stats}</tbody></table>
    <p class="note">Copernicus DEM, NASA MODIS (LST, NDVI), NASA GPM IMERG, Sentinel-2. *Salt index from Sentinel-2 SWIR is approximate.
    ${(g.places || []).some((p) => p.coord_source) ? 'Coordinates: ' + [...new Set(g.places.map((p) => p.coord_source).filter(Boolean))].join('; ') + '.' : ''}${demo}</p>`;
  renderReferences();
}

function renderReferences() {
  const r = DATA.references;
  if (!r) { $('#mgs-refs').innerHTML = '<p class="muted">references.json not found yet.</p>'; return; }
  const T = DATA.targets ? DATA.targets.targets : {}, tks = ['mars_gale', 'mars_jezero'];
  const best = Object.fromEntries(tks.map((tk) => [tk, Math.min(...r.rows.map((x) => x[tk].top_percent))]));
  $('#mgs-refs').innerHTML = `<table class="cmp"><thead><tr><th>Place</th>${tks.map((tk) => `<th colspan="3">${T[tk] ? T[tk].label : tk}</th>`).join('')}</tr>
    <tr><th></th>${tks.map(() => '<th>S</th><th>Cosine</th><th>Rank on Earth</th>').join('')}</tr></thead>
    <tbody>${r.rows.map((x) => `<tr><td>${x.place}</td>${tks.map((tk) => `<td>${fmt(x[tk].S)}</td><td>${fmt(x[tk].cosine)}</td>
      <td class="${x[tk].top_percent === best[tk] ? 'yes' : ''}">top ${fmt(x[tk].top_percent, 1)}%</td>`).join('')}</tr>`).join('')}</tbody></table>
    <p class="note">${r.method}</p>
    <figure class="pca"><img src="${r.pca.image}" alt="PCA of Earth land cells with known analogs, Mangystau and Mars target profiles">
    <figcaption class="note">PCA of the 7 percentile features over all land cells: PC1 ${Math.round(r.pca.explained_variance[0] * 100)}% and PC2 ${Math.round(r.pca.explained_variance[1] * 100)}% of the variance. Points closer to the blue Mars profiles are more Mars-like by our features.</figcaption></figure>`;
}

/* ---------------- method ---------------- */
function renderMethod() {
  document.querySelectorAll('.tex').forEach((el) => { try { katex.render(el.dataset.tex, el, { displayMode: true, throwOnError: false }); } catch (e) { el.textContent = el.dataset.tex; } });
  const v = DATA.validation;
  if (v) {
    const P = v.p_values || {}, M = v.mean_top_percent || {}, MP = v.mean_top_percent_p || {};
    const rows = Object.entries(v.lift).map(([t, o]) => `<b>${DATA.targets ? DATA.targets.targets[t].label : t}</b>: ` +
      Object.entries(o).map(([m, x]) => `${m} Lift ×${fmt(x, 2)}${P[t] ? ` (p ${P[t][m]})` : ''}${M[t] ? `, avg top ${fmt(M[t][m], 1)}% (p ${MP[t][m]})` : ''}`).join('; '));
    $('#method-lift').innerHTML = `<span class="small">${rows.join('<br>')}${v.demo ? '<br><b style="color:#f6c445">DEMO</b>' : ''}</span>`;
  }
  const b = DATA.blind_test;
  if (b) {
    const g = (k, lab) => { const x = b.groups[k]; return `<b>${lab}: recognised ${x.recognised} of ${x.total}</b> (chance ≈ ${x.expected_by_chance}, p = ${x.p_value_binomial}); median rank top ${fmt(x.median_top_percent, 1)}%.`; };
    $('#method-blind').innerHTML = `<span class="small">${g('mars', 'Mars analogs')}<br>${g('all', 'All analogs')}<br>${b.method} Caveat: several known sites cluster in the US Southwest, which makes them easier to recognise from each other.</span>`;
  }
  const w = DATA.wavelength;
  if (w) {
    const lim = Object.entries(w.rcm.h_cm_at_filter_limits);
    $('#method-wave').innerHTML = `<p>Rayleigh smoothness threshold: surfaces with height variations below <i>h</i> look smooth to the radar.</p>
      <div class="table-wrap"><table class="cmp"><thead><tr><th>Radar</th><th>λ</th><th>Incidence θ</th><th>h</th></tr></thead><tbody>
      <tr><td>RCM (Earth), pixels used</td><td>${w.rcm.wavelength_cm} cm</td><td>${lim[0][0]}–${lim[1][0]}°</td><td>${fmt(lim[0][1])}–${fmt(lim[1][1])} cm</td></tr>
      ${w.rcm.sites.map((s) => `<tr><td class="small">RCM · ${pretty(s.site)} (scene mean)</td><td>${w.rcm.wavelength_cm} cm</td><td>${fmt(s.inc_mean_deg, 1)}°</td><td>${fmt(s.h_cm)} cm</td></tr>`).join('')}
      <tr><td>Mini-RF (Moon)</td><td>${w.minirf.wavelength_cm} cm</td><td>${w.minirf.incidence_deg}°</td><td><b>${fmt(w.minirf.h_cm)} cm</b></td></tr></tbody></table></div>
      <p class="note">${w.interpretation} ${w.note}</p>`;
  }
}

/* ---------------- boot ---------------- */
$('#menu').addEventListener('click', () => $('#navlinks').classList.toggle('open'));
window.addEventListener('hashchange', () => show(location.hash.slice(1) || 'home'));
loadAll().then(() => show(location.hash.slice(1) || 'home'));
