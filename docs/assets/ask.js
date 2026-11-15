// Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
// "Ask GroundTwin" guide: prepared answers + keyword search + compare mode. Not a live AI: no API, no server.
// Use on any site with one line:  <script src="https://zhureswe.github.io/groundtwin/assets/ask.js" defer></script>
// Optional attributes: data-mode="page" (full-page, no launcher), data-site="https://…/" (where "Open on site" links go).
(() => {
  'use strict';
  if (window.__gtAsk) return; window.__gtAsk = true;
  const me = document.currentScript || [...document.scripts].find((s) => /assets\/ask\.js/.test(s.src));
  const BASE = new URL('../', me.src).href;                       // …/groundtwin/
  const SITE = (me.dataset.site || BASE + 'index.html');
  const PAGE_MODE = me.dataset.mode === 'page';
  const GITHUB = 'https://github.com/zhureswe/groundtwin';
  const FOOT = 'Not a live AI: it searches prepared answers written with AI assistance from our verified data.';
  const LABEL = { 'Official source': 'official', 'Our result': 'result', 'Our method': 'method' };
  const FEAT = { aridity: 'Dry', barren: 'No plants', thermal_range: 'Day–night swing', cold: 'Cold', dust: 'Dust', roughness: 'Rough terrain', elevation: 'High altitude' };
  const STOP = new Set('a an the is are was were do does did i you your we our of to in on for and or what how why which who where when it this that with can about there by be me tell'.split(' '));
  const D = {};
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const fmt = (x, d = 2) => (x == null || isNaN(x)) ? '–' : Number(x).toFixed(d);
  const topPct = (x) => x == null ? '–' : `top ${x >= 0.1 ? Number(x).toFixed(1) : Number(x).toFixed(3)}%`;
  const pretty = (s) => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  const norm = (s) => s.toLowerCase().replace(/\(.*?\)/g, '').replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
  const getJSON = (f) => fetch(`${BASE}data/${f}.json`, { cache: 'no-store' }).then((r) => (r.ok ? r.json() : null)).catch(() => null);

  /* ---------- DOM ---------- */
  const css = document.createElement('link'); css.rel = 'stylesheet'; css.href = BASE + 'assets/ask.css'; document.head.appendChild(css);
  if (!document.querySelector('link[href*="Space+Grotesk"]')) {
    const f = document.createElement('link'); f.rel = 'stylesheet';
    f.href = 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap';
    document.head.appendChild(f);
  }
  const root = document.createElement('div'); root.id = 'gt-ask-root'; root.className = PAGE_MODE ? 'gta-page' : '';
  root.innerHTML = `
    ${PAGE_MODE ? '' : `<button class="gta-launch" type="button" aria-expanded="false" aria-controls="gta-panel"><span class="gta-orb" aria-hidden="true">?</span><span class="gta-launch-t">Ask GroundTwin</span></button>`}
    <section class="gta-panel" id="gta-panel" role="dialog" aria-label="Ask GroundTwin" ${PAGE_MODE ? '' : 'hidden'}>
      <header class="gta-head"><span class="gta-orb" aria-hidden="true">?</span><div><b>Ask GroundTwin</b><span class="gta-sub">GroundTwin guide · prepared answers</span></div>
        ${PAGE_MODE ? '' : '<button class="gta-x" type="button" aria-label="Close">×</button>'}</header>
      <nav class="gta-cats" role="tablist" aria-label="Topics"></nav>
      <div class="gta-sugg" aria-label="Suggested questions"></div>
      <div class="gta-log" aria-live="polite"></div>
      <form class="gta-form"><input class="gta-in" placeholder="Ask a question, or “compare Mangystau and MDRS”" autocomplete="off" aria-label="Your question"><button class="gta-send" type="submit">Ask</button></form>
      <footer class="gta-foot">${FOOT}</footer>
    </section>`;
  const mount = () => { document.body.appendChild(root); if (!PAGE_MODE) document.documentElement.classList.add('gta-has-launch'); };   // reserve space for the launcher
  document.body ? mount() : document.addEventListener('DOMContentLoaded', mount);
  const $ = (s) => root.querySelector(s);

  const say = (html, who = 'bot') => {
    const d = document.createElement('div'); d.className = `gta-msg gta-${who}`; d.innerHTML = html;
    $('.gta-log').appendChild(d); $('.gta-log').scrollTop = 1e9; return d;
  };
  const chips = (qs) => `<div class="gta-chips">${qs.map((q) => `<button type="button" class="gta-chip" data-q="${esc(q)}">${esc(q)}</button>`).join('')}</div>`;
  const feedback = '<div class="gta-fb"><span>Helpful?</span><button type="button" aria-pressed="false" aria-label="Yes">👍</button><button type="button" aria-pressed="false" aria-label="No">👎</button></div>';
  const badge = (l) => `<span class="gta-badge gta-${LABEL[l] || 'method'}">${esc(l)}</span>`;

  /* ---------- search ---------- */
  function search(text) {
    const qn = text.toLowerCase(), toks = qn.split(/[^a-z0-9α-ωχ.\-]+/).filter((t) => t.length > 1 && !STOP.has(t));
    return D.faq.items.map((it) => {
      const kw = it.keywords, ql = it.q.toLowerCase();
      let s = kw.filter((k) => k.includes(' ') && qn.includes(k)).length * 3;
      toks.forEach((t) => {
        if (kw.some((k) => k === t || (t.length > 3 && (k.startsWith(t) || t.startsWith(k))))) s += 2;
        else if (ql.includes(t)) s += 1;
      });
      return [s, it];
    }).filter(([s]) => s >= 2).sort((a, b) => b[0] - a[0]);
  }

  function answer(it, related) {
    const site = it.section ? `<a class="gta-btn gta-site" href="${SITE}${it.section}" target="_blank" rel="noopener">Open on site →</a>` : '';
    say(`${badge(it.label)}<b class="gta-q">${esc(it.q)}</b><p>${esc(it.a)}</p>
      <div class="gta-links">${it.links.map((l) => `<a class="gta-btn" href="${l.url}" target="_blank" rel="noopener">${esc(l.text)} ↗</a>`).join('')}${site}</div>
      ${feedback}${related.length ? `<div class="gta-rel">Related</div>${chips(related)}` : ''}`);
  }

  /* ---------- compare ---------- */
  let ENT = null;
  async function entities() {
    if (ENT) return ENT;
    const [m, e, r, sc, ex, T] = await Promise.all(['moon_targets', 'earth_cpr', 'references', 'showcase', 'explanations', 'targets'].map(getJSON));
    D.targets = T; ENT = [];
    const tlab = (tk) => T.targets[tk].label.split(' (')[0];
    const analog = (name, feats, scores) => {
      const k = norm(name), old = ENT.find((x) => x.kind === 'Analog place' && norm(x.name) === k);
      if (old) { Object.assign(old.scores, scores); old.feats = old.feats || feats; return; }
      ENT.push({ kind: 'Analog place', name, feats, scores });
    };
    if (sc && ex) {
      sc.cards.forEach((c) => c.rows.forEach((row, i) => analog(row.place, row.features,
        { [c.target]: { S: row.S, cosine: row.cosine, position: row.position, top: ex.cards[c.key][i].top_percent } })));
      Object.entries(sc.top).forEach(([tk, rows]) => rows.forEach((row, i) => { const x = ex.top[tk][i];
        analog(`${row.region} (#${row.rank} ${tlab(tk)})`, x.features, { [tk]: { S: x.S, cosine: cosine(x.features, T.targets[tk].profile), position: x.position, top: x.top_percent } }); }));
      ENT.n = sc.n_cells;
    }
    if (r) r.rows.forEach((x) => analog(x.place, x.features, Object.fromEntries(['mars_gale', 'mars_jezero'].filter((tk) => x[tk])
      .map((tk) => [tk, { S: x[tk].S, cosine: x[tk].cosine, top: x[tk].top_percent }]))));
    if (m) m.targets.forEach((t) => ENT.push({ kind: 'Lunar target', name: t.name, rows: {
      'CPR inside / outside (Mini-RF)': `${fmt(t.cpr_in)} / ${fmt(t.cpr_out)}`, 'Contrast in/out': `×${fmt(t.cpr_in / t.cpr_out)}`,
      'Floor slope (LOLA)': `${fmt(t.slope_deg, 1)}°`, 'Median Tmax (Diviner)': `${Math.round(t.tmax_k)} K`,
      [`Floor colder than ${m.cold_threshold_k} K`]: t.frac_floor_below_110k != null ? `${fmt(t.frac_floor_below_110k * 100, 0)}%` : '–',
      'Evidence score (0–3)': t.ies != null ? `${t.ies}/3` : 'n/a (mountain)' } }));
    if (e) e.sites.forEach((s) => ENT.push({ kind: 'Earth radar site', name: pretty(s.site), rows: {
      'Class': { smooth: 'smooth ground', rough_rock: 'rock field', ice: 'glacier ice' }[s.cls], 'Median CPR (RCM)': fmt(s.median),
      'Middle 50%': `${fmt(s.p25)}–${fmt(s.p75)}`, 'Share CPR > 1': `${fmt(s.frac_gt1 * 100, 1)}%`, 'Scene date': s.date } }));
    return ENT;
  }
  function cosine(f, p) {
    const k = Object.keys(FEAT); let ab = 0, aa = 0, bb = 0;
    k.forEach((x) => { ab += f[x] * p[x]; aa += f[x] * f[x]; bb += p[x] * p[x]; });
    return ab / Math.sqrt(aa * bb);
  }
  function find(text, E) {
    const q = ` ${norm(text)} `, hits = [];
    const names = (e) => { const k = norm(e.name), w = k.split(' '); return w.length >= 3 ? [k, w.map((x) => x[0]).join('')] : [k]; };
    E.forEach((e) => names(e).forEach((n) => { const k = ` ${n} `; for (let i = q.indexOf(k); i >= 0; i = q.indexOf(k, i + 1)) hits.push([i, i + k.length, e]); }));
    const inside = ([s, f, e]) => hits.some(([s2, f2, o]) => o !== e && s2 <= s && f <= f2 && f2 - s2 > f - s);
    const seen = new Set();
    return hits.filter((h) => !inside(h)).sort((a, b) => a[0] - b[0]).map((h) => h[2]).filter((e) => !seen.has(e) && seen.add(e));
  }

  function compareAnalogs(a, b) {
    const T = D.targets.targets, common = Object.keys(a.scores).filter((tk) => b.scores[tk]);
    const tk = common[0], cells = ENT.n ? ` of ${ENT.n.toLocaleString('en')} land cells` : ' of land cells';
    const prof = tk ? T[tk].profile : null, keys = Object.keys(FEAT);
    const close = (f) => keys.filter((k) => prof && 1 - Math.abs(f[k] - prof[k]) >= 0.8).length;
    const rank = (s) => `${s.position ? `#${s.position.toLocaleString('en')} · ` : ''}${topPct(s.top)}`;
    const row = (lab, x, y, z = '') => `<tr><td>${lab}</td><td>${x}</td><td>${y}</td>${prof ? `<td class="gta-dim">${z}</td>` : ''}</tr>`;
    let html = `<div class="gta-table"><table><thead><tr><th>Criterion (percentile)</th><th>${esc(a.name)}</th><th>${esc(b.name)}</th>${prof ? '<th>Target</th>' : ''}</tr></thead><tbody>
      ${keys.map((k) => row(FEAT[k], fmt(a.feats[k]), fmt(b.feats[k]), prof ? fmt(prof[k]) : '')).join('')}`;
    const lines = [];
    if (tk) {
      const sa = a.scores[tk], sb = b.scores[tk], lab = T[tk].label.split(' (')[0];
      html += row(`<b>S vs ${esc(lab)}</b>`, `<b>${fmt(sa.S)}</b>`, `<b>${fmt(sb.S)}</b>`) + row('Cosine', fmt(sa.cosine), fmt(sb.cosine)) + row(`Rank${cells}`, rank(sa), rank(sb));
      const d = sa.S - sb.S;
      lines.push(Math.abs(d) < 0.01 ? `${a.name} and ${b.name} are about equally close to the ${lab} profile (S ${fmt(sa.S)} vs ${fmt(sb.S)}).`
        : `${d > 0 ? a.name : b.name} is closer to the ${lab} profile (S ${fmt(Math.max(sa.S, sb.S))} vs ${fmt(Math.min(sa.S, sb.S))}).`);
      lines.push(`${a.name} matches ${close(a.feats)} of 7 criteria closely (s ≥ 0.8); ${b.name} matches ${close(b.feats)}.`);
      lines.push(`By rank, ${a.name} is in the ${topPct(sa.top)} and ${b.name} in the ${topPct(sb.top)}${cells}.`);
    } else {
      const s = (x) => Object.entries(x.scores).map(([t, v]) => `S ${fmt(v.S)} vs ${T[t].label.split(' (')[0]} (${topPct(v.top)})`).join('; ');
      lines.push(`They were scored against different targets (${esc(a.name)}: ${s(a)}; ${esc(b.name)}: ${s(b)}), so their S values are not directly comparable — the criteria below are.`);
    }
    const big = keys.map((k) => [Math.abs(a.feats[k] - b.feats[k]), k]).sort((x, y) => y[0] - x[0])[0][1];
    lines.push(`The biggest difference is ${FEAT[big].toLowerCase()}: percentile ${fmt(a.feats[big])} vs ${fmt(b.feats[big])}.`);
    html += '</tbody></table></div>';
    const cannot = [...new Set((tk ? [tk] : Object.keys(a.scores)).flatMap((t) => T[t].cannot))];
    return `${html}<p>${lines.map(esc).join(' ')}</p><p class="gta-cannot"><b>What Earth cannot reproduce:</b> ${esc(cannot.join(', '))}.</p>`;
  }

  function compareRows(a, b) {
    const keys = [...new Set([...Object.keys(a.rows), ...Object.keys(b.rows)])];
    return `<div class="gta-table"><table><thead><tr><th></th><th>${esc(a.name)}</th><th>${esc(b.name)}</th></tr></thead><tbody>${keys.map((k) =>
      `<tr><td>${k}</td><td>${a.rows[k] ?? '–'}</td><td>${b.rows[k] ?? '–'}</td></tr>`).join('')}</tbody></table></div>`;
  }

  async function compare(a, b) {
    const E = await entities();
    const article = (k) => (/^[aeiou]/i.test(k) ? 'an' : 'a');
    if (a.kind !== b.kind) return say(`${badge('Our result')}<p>${esc(a.name)} is ${article(a.kind)} ${a.kind.toLowerCase()} and ${esc(b.name)} is ${article(b.kind)} ${b.kind.toLowerCase()}: they are measured differently, so they can't be compared side by side.</p>${pickerHTML(E)}`);
    say(`${badge('Our result')}<b class="gta-q">${esc(a.name)} vs ${esc(b.name)}</b>${a.kind === 'Analog place' ? compareAnalogs(a, b) : compareRows(a, b)}
      <p class="gta-dim">Numbers from our data files (showcase, explanations, references, moon_targets, earth_cpr, targets).</p>${feedback}`);
  }

  function pickerHTML(E) {
    const groups = [...new Set(E.map((e) => e.kind))];
    const opts = groups.map((g) => `<optgroup label="${g}s">${E.map((e, i) => e.kind === g ? `<option value="${i}">${esc(e.name)}</option>` : '').join('')}</optgroup>`).join('');
    return `<form class="gta-pick"><label>Place A<select name="a">${opts}</select></label><label>Place B<select name="b">${opts}</select></label><button class="gta-send" type="submit">Compare</button></form>`;
  }
  async function showPicker() {
    const E = await entities();
    const d = say(`${badge('Our method')}<b class="gta-q">Compare two places</b><p>Pick two places of the same kind, or type “compare A and B”.</p>${pickerHTML(E)}`);
    const sel = d.querySelectorAll('select'); if (sel[1] && sel[1].options.length > 1) sel[1].selectedIndex = 1;
  }

  /* ---------- flow ---------- */
  async function ask(text) {
    say(esc(text), 'me');
    if (/\bcompare\b|\bvs\.?\b|\bversus\b|difference between/i.test(text)) {
      const E = await entities(), f = find(text, E);
      if (f.length >= 2) return compare(f[0], f[1]);
      if (/^\s*compare( two places)?\s*\??\s*$/i.test(text) || f.length < 2) return showPicker();
    }
    const hits = search(text);
    if (!hits.length) return say(`<p><b>I don't know yet — try one of these:</b></p>${chips(D.faq.popular.slice(0, 6))}<p class="gta-dim">Or open an issue on <a href="${GITHUB}" target="_blank" rel="noopener">GitHub</a>.</p>`);
    answer(hits[0][1], hits.slice(1, 4).map(([, x]) => x.q));
  }

  let cat = null;
  function setCat(c) {
    cat = c;
    root.querySelectorAll('.gta-cat').forEach((b) => b.setAttribute('aria-selected', b.dataset.c === c));
    const qs = D.faq.items.filter((x) => x.cat === c).map((x) => x.q).slice(0, 6);
    if (c === 'Using the site' || c === 'Analogs') qs.splice(Math.min(qs.length, 5), 0, 'Compare two places');
    $('.gta-sugg').innerHTML = chips(qs.slice(0, 6));
  }

  let ready = null;
  function init() {
    return ready || (ready = getJSON('faq').then((f) => {
      if (!f) { say('<p>Sorry, the answers could not be loaded.</p>'); return; }
      D.faq = f;
      $('.gta-cats').innerHTML = f.categories.map((c) => `<button type="button" role="tab" class="gta-cat" data-c="${esc(c)}" aria-selected="false">${esc(c)}</button>`).join('');
      setCat(f.categories[0]);
      say(`<p>Hi! I'm the GroundTwin guide. Ask me about the project, the data or how to use the site.</p>`);
    }));
  }

  function open(on) {
    if (PAGE_MODE) return;
    $('.gta-panel').hidden = !on; $('.gta-launch').setAttribute('aria-expanded', on);
    root.classList.toggle('gta-open', on);
    if (on) { init(); setTimeout(() => $('.gta-in').focus(), 30); } else $('.gta-launch').focus();
  }

  const wire = () => {
    if (PAGE_MODE) init();
    else { $('.gta-launch').addEventListener('click', () => open($('.gta-panel').hidden)); $('.gta-x').addEventListener('click', () => open(false)); }
    root.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') open(false); });
    root.addEventListener('click', (ev) => {
      const c = ev.target.closest('.gta-cat'); if (c) return setCat(c.dataset.c);
      const q = ev.target.closest('[data-q]'); if (q) return q.dataset.q === 'Compare two places' ? (say('Compare two places', 'me'), showPicker()) : ask(q.dataset.q);
      const fb = ev.target.closest('.gta-fb button');
      if (fb) fb.parentElement.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', b === fb && b.getAttribute('aria-pressed') !== 'true'));
    });
    root.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      if (ev.target.classList.contains('gta-pick')) {
        const E = await entities(), a = E[ev.target.a.value], b = E[ev.target.b.value];
        if (a === b) return say('<p>Please pick two different places.</p>');
        say(esc(`compare ${a.name} and ${b.name}`), 'me'); return compare(a, b);
      }
      const inp = $('.gta-in'), q = inp.value.trim(); if (!q) return;
      inp.value = ''; await init(); ask(q);
    });
  };
  document.body ? wire() : document.addEventListener('DOMContentLoaded', wire);
  window.GroundTwinAsk = { open: () => open(true), close: () => open(false), ask: (q) => init().then(() => ask(q)) };
})();
