// Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
// Cursor-swarm build INSIDE an embedded page: every heading, paragraph, table row, chip and card is
// drawn and typed by cursor "agents" as the Framer page scrolls. Only runs with ?swarm=1 inside a frame
// (used on the /video page). The parent page sends {type:"gt-view", top, vh, atBottom} so we know which
// part of this page is on screen.
(function boot() {
  'use strict';
  if (window.parent === window) return;
  if (!document.body) { document.addEventListener('DOMContentLoaded', boot); return; }
  const SPEED = 2.2, LINE = 0.86, N = 10;
  const NAMES = ['Ari', 'Bex', 'Cal', 'Dot', 'Eon', 'Fox', 'Gem', 'Hex', 'Ivo', 'Jet'];
  const COLORS = ['#ff5c8a', '#34d399', '#38bdf8', '#facc15', '#fb923c', '#a78bfa', '#f43f5e', '#2dd4bf', '#60a5fa', '#e879f9'];
  const ACC = '#22d3ee', MONO = "'JetBrains Mono', ui-monospace, Menlo, monospace";
  const st = document.createElement('style');
  st.textContent = '[data-sw="h"]{clip-path:inset(0 100% 100% 0)!important}' +
    '[data-sw="f"]{background-color:transparent!important;background-image:none!important;border-color:transparent!important;box-shadow:none!important;outline-color:transparent!important}';
  document.head.appendChild(st);

  let view = null, viewAt = 0;
  window.addEventListener('message', (e) => {
    const d = e.data;
    if (d && d.type === 'gt-view') { view = { top: d.top, vh: d.vh, bottom: !!d.atBottom }; viewAt = performance.now(); }
  });

  // ---- what to build -------------------------------------------------------------------------
  const MEDIA = new Set(['IMG', 'CANVAS', 'IFRAME', 'SELECT', 'INPUT', 'BUTTON', 'TEXTAREA', 'VIDEO', 'svg', 'SVG']);
  const ROW = new Set(['TR', 'LI', 'DT', 'DD', 'FIGURE', 'LABEL', 'SUMMARY']);
  const SKIP = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'BR']);
  const map = new Map();   // el -> job
  const jobs = [];
  let canvas = null;
  const hasText = (el) => { for (const n of el.childNodes) if (n.nodeType === 3 && n.textContent.trim()) return true; return false; };
  const framed = (cs) => {
    const bg = cs.backgroundColor;
    const hasBg = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
    const bd = cs.borderTopStyle !== 'none' && (parseFloat(cs.borderTopWidth) || 0) + (parseFloat(cs.borderLeftWidth) || 0) > 0;
    return hasBg || bd;
  };
  const add = (el, kind, frame) => {
    const job = { el, kind, frame, state: 0, chars: (el.textContent || '').length, p: 0, doneAt: 0 };
    map.set(el, job);
    el.setAttribute('data-sw', kind === 'leaf' ? 'h' : 'f');
    jobs.push(job);
    return job;
  };
  const scan = (el, frame) => {
    for (const c of el.children) {
      if (c === canvas || SKIP.has(c.tagName)) continue;
      const known = map.get(c);
      if (known) { if (known.kind === 'frame') scan(c, known); continue; }
      const cs = getComputedStyle(c);
      if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      const r = c.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) { if (c.children.length) scan(c, frame); continue; }
      const tag = c.tagName;
      if (ROW.has(tag) || MEDIA.has(tag) || hasText(c) || !c.children.length) { add(c, 'leaf', frame); continue; }
      if (framed(cs)) scan(c, add(c, 'frame', frame));
      else scan(c, frame);
    }
  };
  let pend = false;
  const collect = () => { pend = false; scan(document.querySelector('main') || document.body, null); };
  collect();
  new MutationObserver(() => { if (!pend) { pend = true; requestAnimationFrame(collect); } })
    .observe(document.body, { childList: true, subtree: true });

  // ---- agents --------------------------------------------------------------------------------
  canvas = document.createElement('canvas');
  canvas.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none;z-index:2147483647';
  document.body.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const arrow = new Path2D('M0 0 L0 15.5 L4.2 11.6 L7.1 18 L9.6 16.9 L6.8 10.7 L12.4 10.7 Z');
  const agents = [];
  for (let i = 0; i < N; i++) agents.push({ x: 0, y: 0, vx: 0, vy: 0, tx: 0, ty: 0, k: 300, vis: 0, vt: 0, job: null, phase: 'idle', t0: 0, beam: false, idleAt: 0, color: COLORS[i], name: NAMES[i] });
  const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  const finish = (a, now) => {
    const j = a.job;
    if (j) { j.el.removeAttribute('data-sw'); j.el.style.clipPath = ''; j.state = 2; j.doneAt = now; }
    a.job = null; a.phase = 'idle'; a.beam = false; a.idleAt = now;
  };

  let last = performance.now(), frameNo = 0, cw = 0, chh = 0, ctop = -1;
  const tick = (now) => {
    requestAnimationFrame(tick);
    const dt = Math.min(0.05, Math.max(0.001, (now - last) / 1000));
    last = now; frameNo++;
    // without a parent telling us the view (e.g. opened directly), treat the frame itself as the view
    const v = view && now - viewAt < 4000 ? view : { top: 0, vh: window.innerHeight, bottom: false };
    const visTop = -v.top, vh = v.vh;
    const lineY = v.bottom ? Infinity : visTop + vh * LINE;
    const W = document.documentElement.clientWidth;
    if (W !== cw || vh !== chh) { cw = W; chh = vh; canvas.width = Math.round(W * dpr); canvas.height = Math.round(vh * dpr); canvas.style.width = W + 'px'; canvas.style.height = vh + 'px'; }
    const ct = Math.max(0, Math.round(visTop));
    if (ct !== ctop) { ctop = ct; canvas.style.top = ct + 'px'; }

    // hand out work: in page order, only after the enclosing frame is built
    if (frameNo % 2 === 0) {
      const free = agents.filter((a) => !a.job);
      for (const j of jobs) {
        if (!free.length) break;
        if (j.state !== 0) continue;
        if (j.frame && j.frame.state !== 2) continue;
        if (!j.el.isConnected) { j.state = 2; continue; }
        const r = j.el.getBoundingClientRect();
        if (r.top >= lineY) continue;
        if (r.bottom < visTop - 40) { j.el.removeAttribute('data-sw'); j.state = 2; continue; }
        let bi = 0, bd = Infinity;
        free.forEach((a, i) => { const d = (a.x - r.left) ** 2 + (a.y - r.top) ** 2; if (d < bd) { bd = d; bi = i; } });
        const a = free.splice(bi, 1)[0];
        if (a.vis < 0.05) { a.x = Math.max(0, r.left - 60); a.y = Math.min(r.top, visTop + vh * 0.9); a.vx = a.vy = 0; }
        j.state = 1; j.p = 0; a.job = j; a.phase = 'travel'; a.t0 = now;
      }
    }

    for (const a of agents) {
      const j = a.job;
      if (!j) { a.vt = now - a.idleAt > 350 ? 0 : 1; a.tx = a.x; a.ty = a.y; a.k = 200; continue; }
      a.vt = 1;
      const r = j.el.getBoundingClientRect();
      if (a.phase === 'travel') {
        a.tx = r.left; a.ty = r.top; a.k = 260;
        if (Math.hypot(a.x - r.left, a.y - r.top) < 12 || now - a.t0 > 650 / SPEED) { a.phase = 'draw'; a.t0 = now; }
      } else if (a.phase === 'draw') {
        const t = Math.min(1, (now - a.t0) / (340 / SPEED)), e = ease(t);
        j.p = e; a.tx = r.left + r.width * e; a.ty = r.top + r.height * e; a.k = 1100;
        if (t >= 1) {
          if (j.kind === 'frame') finish(a, now);
          else { j.el.setAttribute('data-sw', 'x'); j.el.style.clipPath = 'inset(0 100% 0 0)'; a.phase = hasText(j.el) || j.chars ? 'type' : 'fill'; a.beam = a.phase === 'type'; a.t0 = now; }
        }
      } else {
        const dur = a.phase === 'type' ? Math.min(1500, Math.max(260, j.chars * 14)) / SPEED : 380 / SPEED;
        const t = Math.min(1, (now - a.t0) / dur), e = a.phase === 'type' ? t : ease(t);
        j.el.style.clipPath = 'inset(-4px ' + (100 - e * 100) + '% -4px -4px)';
        a.tx = r.left + r.width * e + 3; a.ty = r.top + Math.min(r.height, 28) * 0.5; a.k = 1100;
        if (t >= 1) finish(a, now);
      }
    }
    for (const a of agents) {
      const K = Math.min(2200, a.k * 1.3), D = 2 * Math.sqrt(K) * 0.92, h = dt / 2;
      for (let s = 0; s < 2; s++) { a.vx += ((a.tx - a.x) * K - a.vx * D) * h; a.vy += ((a.ty - a.y) * K - a.vy * D) * h; a.x += a.vx * h; a.y += a.vy * h; }
      a.vis += (a.vt - a.vis) * Math.min(1, dt * (a.vt < a.vis ? 7 : 9));
    }

    // draw (canvas covers only the visible part of this page)
    ctx.setTransform(dpr, 0, 0, dpr, 0, -ct * dpr);
    ctx.clearRect(0, ct, W, vh);
    ctx.lineWidth = 1;
    for (const j of jobs) {
      if (j.state === 0) continue;
      const fade = j.state === 2 ? Math.max(0, 1 - (now - j.doneAt) / 420) : 1;
      if (fade <= 0) continue;
      const r = j.el.getBoundingClientRect();
      if (r.bottom < ct - 20 || r.top > ct + vh + 20) continue;
      const w = r.width * j.p, hh = r.height * j.p, x0 = Math.round(r.left) + 0.5, y0 = Math.round(r.top) + 0.5;
      ctx.globalAlpha = fade; ctx.strokeStyle = ACC;
      ctx.strokeRect(x0, y0, Math.round(w), Math.round(hh));
      ctx.fillStyle = '#fff';
      for (const [cx, cy] of [[x0, y0], [x0 + w, y0], [x0, y0 + hh], [x0 + w, y0 + hh]]) { ctx.fillRect(cx - 2, cy - 2, 4, 4); ctx.strokeRect(cx - 2, cy - 2, 4, 4); }
      if (j.state === 1 && r.width > 60) {
        const lab = Math.round(r.width) + ' × ' + Math.round(r.height);
        ctx.font = '600 9px ' + MONO; const tw = ctx.measureText(lab).width;
        ctx.fillStyle = '#0e6f7c'; ctx.fillRect(x0 + w / 2 - tw / 2 - 5, y0 + hh + 6, tw + 10, 14);
        ctx.fillStyle = '#e6fdff'; ctx.fillText(lab, x0 + w / 2 - tw / 2, y0 + hh + 16);
      }
    }
    for (const a of agents) {
      if (a.vis < 0.02) continue;
      ctx.globalAlpha = a.vis;
      ctx.save(); ctx.translate(a.x, a.y);
      if (a.beam) {
        ctx.strokeStyle = a.color; ctx.lineWidth = 2; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(-3, -7); ctx.lineTo(3, -7); ctx.moveTo(0, -7); ctx.lineTo(0, 7); ctx.moveTo(-3, 7); ctx.lineTo(3, 7); ctx.stroke();
      } else {
        ctx.fillStyle = a.color; ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.2; ctx.fill(arrow); ctx.stroke(arrow);
      }
      ctx.restore();
      ctx.font = '700 9px ' + MONO; const tw = ctx.measureText(a.name).width;
      const bx = a.x + (a.beam ? 6 : 9), by = a.y + (a.beam ? 9 : 17);
      ctx.fillStyle = a.color; ctx.beginPath(); ctx.roundRect ? ctx.roundRect(bx, by, tw + 10, 14, 7) : ctx.rect(bx, by, tw + 10, 14); ctx.fill();
      ctx.fillStyle = '#0b0d12'; ctx.fillText(a.name, bx + 5, by + 10);
    }
    ctx.globalAlpha = 1;
  };
  requestAnimationFrame(tick);
})();
