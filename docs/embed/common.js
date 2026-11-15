// Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
// Shared helpers for the embeddable pages in docs/embed/. All numbers come from docs/data/*.json.
'use strict';
(() => {
  const params = new URLSearchParams(location.search);
  if (params.get('embed') === '1') {
    document.documentElement.classList.add('is-embed');   // hide header/footer inside Framer
    // Tell the Framer page how tall we are, so the frame grows to fit and the page (not the frame) scrolls.
    if (window.parent !== window) {
      let lastH = 0;
      const send = () => { const b = document.body, h = Math.ceil(b.getBoundingClientRect().bottom + window.scrollY + (parseFloat(getComputedStyle(b).marginBottom) || 0)); if (Math.abs(h - lastH) > 2) { lastH = h; window.parent.postMessage({ type: 'gt-height', h, page: location.pathname }, '*'); } };
      const go = () => { send(); if (window.ResizeObserver) new ResizeObserver(send).observe(document.body); setInterval(send, 1500); };
      if (document.body) go(); else document.addEventListener('DOMContentLoaded', go);
    }
  } else {   // standalone page: add the Ask GroundTwin guide (inside Framer it is added once for the whole site)
    const s = document.createElement('script'); s.src = '../assets/ask.js'; s.defer = true; document.head.appendChild(s);
  }
  const FEAT = { aridity: 'Dry', barren: 'No plants', thermal_range: 'Day–night swing', cold: 'Cold', dust: 'Dust', roughness: 'Rough terrain', elevation: 'High altitude' };
  const TREK = { moon: ['NASA Moon Trek', 'https://trek.nasa.gov/moon/'], mars: ['NASA Mars Trek', 'https://trek.nasa.gov/mars/'] };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const fmt = (x, d = 2) => (x == null || isNaN(x)) ? '–' : Number(x).toFixed(d);
  const topPct = (x) => `top ${x >= 0.1 ? Number(x).toFixed(1) : Number(x).toFixed(3)}% of land cells`;
  const ll = (lat, lon) => `${Math.abs(lat).toFixed(2)}°${lat >= 0 ? 'N' : 'S'}, ${Math.abs(lon).toFixed(2)}°${lon >= 0 ? 'E' : 'W'}`;
  const body = (tk) => (tk.startsWith('moon') ? 'moon' : 'mars');
  const load = (name) => fetch(`../data/${name}.json`, { cache: 'no-store' }).then((r) => { if (!r.ok) throw new Error(`data/${name}.json: HTTP ${r.status}`); return r.json(); });
  const gearth = (lat, lon) => `https://earth.google.com/web/@${lat},${lon},800a,60000d,35y,0h,0t,0r`;
  const buttons = (lat, lon, tk, label = '') => {
    const t = TREK[body(tk)];
    return `<div class="e-btns"><a class="e-btn" href="${gearth(lat, lon)}" target="_blank" rel="noopener">Open in Google Earth${label ? ` · ${esc(label)}` : ''} ↗</a>` +
      `<a class="e-btn ${body(tk)}" href="${t[1]}" target="_blank" rel="noopener">Open in ${t[0]} ↗</a></div>`;
  };
  // 7 criteria as bars: filled = the place's percentile, tick = the target profile value
  const bars = (feats, prof) => `<div class="e-bars">${Object.keys(FEAT).map((k) => {
    const s = 1 - Math.abs(feats[k] - prof[k]), cls = s >= 0.8 ? 'yes' : s >= 0.5 ? 'part' : 'no';
    return `<div class="e-bar ${cls}"><span class="e-bar-l">${FEAT[k]}</span><span class="e-bar-t" role="img" aria-label="${FEAT[k]}: place ${fmt(feats[k])}, target ${fmt(prof[k])}">
      <i style="width:${(feats[k] * 100).toFixed(1)}%"></i><b style="left:${(prof[k] * 100).toFixed(1)}%"></b></span><span class="e-bar-v">${fmt(feats[k])}</span></div>`;
  }).join('')}<div class="e-bar-key"><span><i class="k-fill"></i>place percentile</span><span><i class="k-tick"></i>target profile</span></div></div>`;
  const chips = (x) => [['match_features', 'yes', '✓', 'Matches'], ['partly_features', 'part', '≈', 'Partly'], ['differ_features', 'no', '≠', 'Differs']]
    .map(([k, c, sym, lab]) => `<div class="e-chiprow"><span class="e-chiplab">${lab}</span>${(x[k] || []).map((f) => `<span class="chip ${c}">${sym} ${FEAT[f]}</span>`).join('') || '<span class="muted small">—</span>'}</div>`).join('');
  // plain-language reasons from the numbers: p = how extreme the place is on Earth (0–1), t = what the target needs
  const WHAT = { aridity: ['drier', 'dry'], barren: ['barer (fewer plants)', 'bare of plants'], thermal_range: ['bigger day–night temperature swing', 'big day–night swings'],
    cold: ['colder nights', 'cold'], dust: ['dustier air', 'dusty'], roughness: ['rougher terrain', 'rough terrain'], elevation: ['higher ground', 'high ground'] };
  const WHY = { aridity: 'water and rain change soils and radar echoes, so analogs must be dry', barren: 'plants hide the bare rock and soil that instruments need to see',
    thermal_range: 'equipment must survive large temperature swings', cold: 'cold matters for ice-related tests', dust: 'dust tests seals, solar panels and rover wheels',
    roughness: 'rough ground tests rover driving and landing hazards', elevation: 'thinner air is a little closer to space conditions' };
  const reasons = (f, prof, w) => {
    const pct = (x) => Math.round(x * 100);
    const items = Object.keys(FEAT).map((k) => ({ k, p: f[k], t: prof[k], s: 1 - Math.abs(f[k] - prof[k]), w: w[k] || 0 }));
    const good = items.filter((i) => i.s >= 0.8).sort((a, b) => b.w * b.s - a.w * a.s);
    const bad = items.filter((i) => i.s < 0.8).sort((a, b) => b.w * (1 - b.s) - a.w * (1 - a.s));
    const fit = good.slice(0, 3).map((i) => `<li><b>${FEAT[i.k]}:</b> ${WHAT[i.k][0]} than ${pct(i.p)}% of Earth's land; the target needs ${pct(i.t)}% — close (${WHY[i.k]}).</li>`);
    const miss = bad.slice(0, 3).map((i) => i.p < i.t
      ? `<li><b>${FEAT[i.k]}:</b> not ${WHAT[i.k][1]} enough — ${WHAT[i.k][0]} than only ${pct(i.p)}% of land, but the target needs ${pct(i.t)}%${i.w >= 2 ? ' (heavily weighted for this mission need)' : ''}.</li>`
      : `<li><b>${FEAT[i.k]}:</b> too extreme — ${WHAT[i.k][0]} than ${pct(i.p)}% of land, while the target needs only ${pct(i.t)}%${i.w >= 2 ? ' (heavily weighted for this mission need)' : ''}.</li>`);
    return `<div class="why"><p><b style="color:var(--yes)">Why it fits</b></p><ul>${fit.join('') || '<li>No criterion is a close match.</li>'}</ul>
      <p><b style="color:var(--no)">Why it doesn't fit</b></p><ul>${miss.join('') || '<li>No weak criteria — all seven are close to the target.</li>'}</ul></div>`;
  };
  window.GTE = { FEAT, TREK, esc, fmt, topPct, ll, body, load, gearth, buttons, bars, chips, reasons };
})();
