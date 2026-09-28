// ------------------------------------------------------------------ Skill tree screen (agent ST, skill tree redesign)
// Overrides the shrine menu's `tree` screen (menuInput / renderMenu in 08_ui.js). Builds only from the node data in
// 57_skills.js (docs/SKILLTREE_CONTRACT.md "Data format"): SKILLS nodes with x/y/req/excl/key/cls/icon/stat,
// SKILL_BRANCHES, skillLearnable(), learnSkill(), skillBuildSummary(). Everything degrades gracefully when one is missing.
//   Pages: the Constellation (the five branches radiating from the ember, plus the Wayfarer ring when it sits around
//   them) and the Arsenal (one mastery per weapon class). A Wayfarer page appears only if its nodes would collide.
//   Camera: pans and zooms smoothly (overview / detail); follows the cursor; drag, wheel, right stick, triggers.
//   Input: arrows / D-pad / left stick move between nodes spatially; confirm twice to learn (the first press arms it);
//   Tab·Q / RB·LB switch page; Z / LT·RT zoom; B / Y toggles the build summary; mouse hover selects, click arms/learns.
// Art: node icons `sk_<id>` in sk_icons (+ desaturated twins in sk_icons_dim), node frames in sk_frames (art/gen_skills.py).
ICON_SHEETS.push('sk_icons');

const ST_MAIN = ['blade', 'ash', 'veil', 'blood', 'flame'];
const ST_BR = {   // fallbacks when SKILL_BRANCHES lacks an entry
  blade: { name: 'Blade', color: '#cdd3e2' }, ash: { name: 'Ash', color: '#8fb0e8' }, veil: { name: 'Veil', color: '#a99be0' },
  blood: { name: 'Blood', color: '#e0505e' }, flame: { name: 'Flame', color: '#f39a48' }, arsenal: { name: 'Arsenal', color: '#e6c77a' },
  way: { name: 'Wayfarer', color: '#8fd8b0' },
};
const ST_CLS_ORDER = ['sword', 'dagger', 'great', 'spear', 'katana', 'staff', 'shield', 'twin', 'scythe', 'whip'];
const ST_CLS_NAME = { sword: 'Straight Sword', dagger: 'Dagger', great: 'Great Weapon', spear: 'Spear', katana: 'Katana', staff: 'Staff',
                      shield: 'Sword & Shield', twin: 'Twinblades', scythe: 'Scythe', whip: 'Whip', mirror: 'Mirror Blade' };
const ST_VP = { x: 0, y: 24, w: 258, h: 178 };            // the part of the field left of the detail panel
const ST_PANEL = { x: 262, y: 27, w: 117, h: 176 };
const ST_R = { n: 12.5, f: 12.5, k: 15, m: 12.5 };           // node radius at zoom 1 (low-res px), matches sk_frames
const ST = { page: 0, sel: null, cam: { x: 0, y: 0, z: 1 }, tgt: { x: 0, y: 0 }, zi: 1, lastT: -1, drag: null, hover: null, arm: null, armT: 0,
             summary: false, fx: [], ptrT: 0, padPrev: new Set(), hits: [], deny: null, msg: null, tex: null, dust: null, L: null, sig: '', keyNav: false, M: null };

// ---- data access (all tolerant of a partial 57_skills.js)
const stNode = id => SKILLS.find(s => s.id === id);
const stLearned = id => SAVE.skills.includes(id);
function stBranch(br) {
  const B = (typeof SKILL_BRANCHES !== 'undefined' && SKILL_BRANCHES.find(b => b.id === br)) || {};
  const F = ST_BR[br] || { name: br ? br[0].toUpperCase() + br.slice(1) : 'Skill', color: UIC.gold };
  return { id: br, name: B.name || F.name, color: B.color || F.color, desc: B.desc || '' };
}
function stRgb(hex) { const h = (hex || '#e6c77a').replace('#', ''); const v = h.length === 3 ? h.split('').map(c => c + c).join('') : h; return [0, 2, 4].map(i => parseInt(v.slice(i, i + 2), 16)).join(','); }
function stPts() { try { return skillPoints(); } catch (e) { return 0; } }
function stEquippedCls() {
  if (typeof wcls === 'function') { try { return wcls(); } catch (e) {} }
  const c = (typeof WEAPON_CLASS !== 'undefined' && WEAPON_CLASS[SAVE.weapon]) || 'sword';
  return c === 'mirror' ? (SAVE.lastCls || 'sword') : c;
}
function stState(n) {   // 'learned' | 'sealed' | 'avail' | 'locked'
  if (stLearned(n.id)) return 'learned';
  if ((n.excl || []).some(stLearned)) return 'sealed';
  if ((n.req || []).every(stLearned) && !(n.item && !(SAVE.items || {})[n.item])) return 'avail';
  return 'locked';
}
function stCan(n) {   // { ok, why }
  if (typeof skillLearnable === 'function') { try { const r = skillLearnable(n.id); if (r && typeof r === 'object') return { ok: !!r.ok, why: r.why || '' }; return { ok: !!r, why: '' }; } catch (e) {} }
  const s = stState(n);
  if (s === 'learned') return { ok: false, why: 'Already learned' };
  if (s === 'sealed') return { ok: false, why: `Sealed: you chose ${stNode(n.excl.find(stLearned)).name}` };
  if (s === 'locked') return { ok: false, why: 'Requires ' + (n.req || []).filter(r => !stLearned(r)).map(r => (stNode(r) || { name: r }).name).join(', ') };
  if (stPts() < n.cost) return { ok: false, why: `Needs ${n.cost} point${n.cost === 1 ? '' : 's'}` };
  return { ok: true, why: '' };
}

// ---- layout: normalise SK's tree units into low-res px at zoom 1, split into pages
function stSig() { return SKILLS.map(s => `${s.id}:${s.br}:${s.x}:${s.y}`).join('|'); }
function stLayout() {
  const sig = stSig(); if (ST.L && ST.sig === sig) return ST.L;
  ST.sig = sig;
  const main = SKILLS.filter(s => s.br !== 'arsenal' && s.br !== 'way'), way = SKILLS.filter(s => s.br === 'way'), ars = SKILLS.filter(s => s.br === 'arsenal');
  const num = v => (typeof v === 'number' && isFinite(v) ? v : 0);
  // spacing unit: the median requirement-link length (else the median nearest-neighbour distance)
  const dist = (a, b) => Math.hypot(num(a.x) - num(b.x), num(a.y) - num(b.y));
  const nn = arr => arr.map(a => Math.min(...arr.filter(b => b !== a).map(b => dist(a, b)).filter(d => d > 1e-6), 1e9)).filter(d => d < 1e9);
  const median = v => { if (!v.length) return 1; const s = [...v].sort((a, b) => a - b); return s[s.length >> 1]; };
  const links = []; for (const s of main.concat(way)) for (const r of s.req || []) { const p = stNode(r); if (p && p.br !== 'arsenal') links.push(dist(s, p)); }
  const mainNN = nn(main.concat(way));
  const unit = links.length ? median(links.filter(d => d > 1e-6)) : median(mainNN);
  const minNN = mainNN.length ? Math.min(...mainNN) : unit;
  let k = 36 / (unit || 1); if (minNN * k < 28) k = Math.min(28 / (minNN || 1), k * 1.5);
  // centre: where the main branches' roots converge (their mean), else the origin
  const roots = main.filter(s => !(s.req || []).length);
  const C = roots.length >= 3 ? { x: roots.reduce((a, s) => a + num(s.x), 0) / roots.length, y: roots.reduce((a, s) => a + num(s.y), 0) / roots.length } : { x: 0, y: 0 };
  // wayfarer: on the constellation when it doesn't collide with the branches, else on its own page
  const wayApart = way.length && main.length && way.some(w => main.some(m => dist(w, m) < unit * 0.55));
  const mk = (id, name, nodes, place) => {
    const pos = {}; for (const s of nodes) pos[s.id] = place(s);
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (const s of nodes) { const p = pos[s.id], r = ST_R[stKind(s)]; x0 = Math.min(x0, p.x - r); y0 = Math.min(y0, p.y - r); x1 = Math.max(x1, p.x + r); y1 = Math.max(y1, p.y + r); }
    if (!nodes.length) { x0 = y0 = -40; x1 = y1 = 40; }
    return { id, name, nodes, pos, b: { x0, y0, x1, y1 } };
  };
  const radial = s => ({ x: (num(s.x) - C.x) * k, y: (num(s.y) - C.y) * k });
  const pages = [];
  const treeNodes = wayApart ? main : main.concat(way);
  if (treeNodes.length) pages.push(mk('tree', 'Constellation', treeNodes, radial));
  if (ars.length) {   // the Arsenal: a gallery of weapon-class masteries, 5 to a row
    const order = [...ars].sort((a, b) => stClsRank(a) - stClsRank(b) || SKILLS.indexOf(a) - SKILLS.indexOf(b));
    const cols = Math.min(5, order.length), rows = Math.ceil(order.length / cols), gx = 50, gy = 70;
    const P2 = mk('arsenal', 'Arsenal', order, s => { const i = order.indexOf(s), r = Math.floor(i / cols), c = i % cols, nr = Math.min(cols, order.length - r * cols); return { x: (c - (nr - 1) / 2) * gx, y: (r - (rows - 1) / 2) * gy + 4 }; });
    P2.gallery = true; pages.push(P2);
  }
  if (wayApart) {
    const wc = { x: way.reduce((a, s) => a + num(s.x), 0) / way.length, y: way.reduce((a, s) => a + num(s.y), 0) / way.length };
    pages.push(mk('way', 'Wayfarer', way, s => ({ x: (num(s.x) - wc.x) * k, y: (num(s.y) - wc.y) * k })));
  }
  // per-page extras: branch directions and label anchors, the wayfarer ring radius
  for (const pg of pages) {
    pg.unit = 33; pg.brs = {};
    if (pg.id !== 'tree') continue;
    for (const br of ST_MAIN.concat(SKILL_BRANCH_IDS().filter(b => !ST_MAIN.includes(b) && b !== 'arsenal' && b !== 'way'))) {
      const ns = pg.nodes.filter(s => s.br === br); if (!ns.length) continue;
      let mx = 0, my = 0; for (const s of ns) { mx += pg.pos[s.id].x; my += pg.pos[s.id].y; } mx /= ns.length; my /= ns.length;
      const ang = Math.atan2(my, mx), far = Math.max(...ns.map(s => pg.pos[s.id].x * Math.cos(ang) + pg.pos[s.id].y * Math.sin(ang)));
      const key = ns.find(s => s.key), kp = key ? pg.pos[key.id] : { x: Math.cos(ang) * far, y: Math.sin(ang) * far };
      pg.brs[br] = { ang, cx: mx, cy: my, far, kx: kp.x, ky: kp.y, key: key && key.id, ext: Math.max(40, ...ns.map(s => Math.hypot(pg.pos[s.id].x - mx, pg.pos[s.id].y - my))) };
    }
    const wn = pg.nodes.filter(s => s.br === 'way');
    if (wn.length >= 4) {
      const rs = wn.map(s => Math.hypot(pg.pos[s.id].x, pg.pos[s.id].y)), mr = rs.reduce((a, b) => a + b, 0) / rs.length;
      if (rs.every(r => Math.abs(r - mr) < mr * 0.18)) pg.ring = mr;
    }
    pg.b.x0 -= 12; pg.b.x1 += 12; pg.b.y0 -= 14; pg.b.y1 += pg.ring ? 30 : 14;
    pg.tiers = [...new Set(pg.nodes.filter(s => ST_MAIN.includes(s.br)).map(s => Math.round(Math.hypot(pg.pos[s.id].x, pg.pos[s.id].y) / 8) * 8))].sort((a, b) => a - b);
  }
  ST.L = pages;
  return pages;
}
function SKILL_BRANCH_IDS() { const L = []; for (const s of SKILLS) if (!L.includes(s.br)) L.push(s.br); return L; }
function stClsRank(s) { const i = ST_CLS_ORDER.indexOf(s.cls); return i < 0 ? 99 : i; }
function stKind(s) { return s.key ? 'k' : s.br === 'arsenal' ? 'm' : (s.excl || []).length ? 'f' : 'n'; }
function stPage() { const L = stLayout(); ST.page = clamp(ST.page, 0, Math.max(0, L.length - 1)); return L[ST.page]; }
function stZooms(pg) {   // overview (whole page) / middle / detail; snapped so icons land on whole device pixels
  const fit = Math.min(ST_VP.w / (pg.b.x1 - pg.b.x0 + 16), (ST_VP.h - 10) / (pg.b.y1 - pg.b.y0 + 12));
  if (fit >= 0.92) return [1];
  const snap = z => (scale >= 2 ? Math.max(1, Math.floor(z * scale + 0.08)) / scale : z);
  const sf = snap(Math.max(0.22, fit)), lo = sf > fit * 1.02 ? Math.max(0.22, fit) : sf, mid = snap(0.66);
  return mid > lo + 0.1 && mid < 0.9 ? [lo, mid, 1] : [lo, 1];
}

// ---- open / page / selection / camera
function stOpen(M) {
  M.st = true; ST.M = M; ST.fx = []; ST.openT = 0; ST.arm = null; ST.msg = null; ST.deny = null; ST.drag = null; ST.hover = null; ST.lastT = -1; ST.keyNav = false;
  const L = stLayout(); ST.page = clamp(ST.page, 0, Math.max(0, L.length - 1));
  if (!L.length) return;
  stSetPage(ST.page, true);
}
function stSetPage(i, first) {
  const L = stLayout(); if (!L.length) return;
  ST.page = (i + L.length) % L.length; const pg = L[ST.page];
  // cursor: the last learned node on the page, else its first available root, else its first node
  const learned = SAVE.skills.filter(id => pg.pos[id]);
  const pick = learned.length ? learned[learned.length - 1] : (pg.nodes.find(s => stState(s) === 'avail' && !(s.req || []).length) || pg.nodes.find(s => stState(s) === 'avail') || pg.nodes[0] || {}).id;
  ST.sel = pick; ST.arm = null;
  const Z = stZooms(pg);
  // a fresh tree opens on the whole constellation; a growing one on the middle zoom around the last node learned
  ST.zi = Z.length === 1 || pg.gallery ? Z.length - 1 : learned.length ? Math.min(1, Z.length - 1) : 0;
  ST.cam.z = Z[ST.zi];
  const p = pg.gallery || (ST.zi === 0 && Z.length > 1) ? { x: (pg.b.x0 + pg.b.x1) / 2, y: (pg.b.y0 + pg.b.y1) / 2 } : pg.pos[pick] || { x: 0, y: 0 };
  ST.tgt.x = ST.cam.x = p.x; ST.tgt.y = ST.cam.y = p.y;
  ST.cam.z = Z[ST.zi] * 0.9;
  if (!first) sfx.menu();
}
const stSX = x => ST_VP.x + ST_VP.w / 2 + (x - ST.cam.x) * ST.cam.z;
const stSY = y => ST_VP.y + ST_VP.h / 2 + (y - ST.cam.y) * ST.cam.z;
function stFollow(id, force) {   // keep the node inside the view (targets use the zoom we're heading to)
  const pg = stPage(), p = pg.pos[id]; if (!p || pg.gallery) return;
  const z = stZooms(pg)[ST.zi] || 1, mx = Math.min(46, ST_VP.w * 0.3) / z, my = Math.min(40, ST_VP.h * 0.3) / z, hw = ST_VP.w / 2 / z, hh = ST_VP.h / 2 / z;
  if (force) { ST.tgt.x = p.x; ST.tgt.y = p.y; return; }
  if (p.x < ST.tgt.x - hw + mx) ST.tgt.x = p.x + hw - mx; if (p.x > ST.tgt.x + hw - mx) ST.tgt.x = p.x - hw + mx;
  if (p.y < ST.tgt.y - hh + my) ST.tgt.y = p.y + hh - my; if (p.y > ST.tgt.y + hh - my) ST.tgt.y = p.y - hh + my;
}
function stClampCam(pg) {
  if (pg.gallery) { ST.tgt.x = (pg.b.x0 + pg.b.x1) / 2; ST.tgt.y = (pg.b.y0 + pg.b.y1) / 2; return; }
  const z = ST.cam.z, hw = ST_VP.w / 2 / z, hh = ST_VP.h / 2 / z, b = pg.b;
  const cl = (v, lo, hi) => (lo > hi ? (lo + hi) / 2 : clamp(v, lo, hi));
  ST.tgt.x = cl(ST.tgt.x, b.x0 - 20 + hw * 0.35, b.x1 + 20 - hw * 0.35); ST.tgt.y = cl(ST.tgt.y, b.y0 - 20 + hh * 0.35, b.y1 + 20 - hh * 0.35);
}
function stSelect(id, how) {
  if (!id || id === ST.sel) return;
  ST.sel = id; ST.arm = null; ST.msg = null;
  if (how !== 'mouse') { stFollow(id); sfx.menu(); }
}
function stZoom(dir, at) {
  const pg = stPage(), Z = stZooms(pg), zi = clamp(ST.zi + dir, 0, Z.length - 1);
  if (zi > 0 && ST.zi === 0 && !at && ST.sel && pg.pos[ST.sel]) at = pg.pos[ST.sel];
  if (zi === ST.zi) { sfx.deny(); return; }
  ST.zi = zi; sfx.menu();
  if (zi === 0 && Z.length > 1) { ST.tgt.x = (pg.b.x0 + pg.b.x1) / 2; ST.tgt.y = (pg.b.y0 + pg.b.y1) / 2; }
  else if (at) { ST.tgt.x = at.x; ST.tgt.y = at.y; }
  else if (ST.sel && pg.pos[ST.sel]) { ST.tgt.x = pg.pos[ST.sel].x; ST.tgt.y = pg.pos[ST.sel].y; }
}
function stMove(dir) {
  const pg = stPage(), D0 = { left: [-1, 0], right: [1, 0], up: [0, -1], down: [0, 1] }[dir];
  let cur = pg.pos[ST.sel];
  // cursor scrolled far out of view (mouse drag / right stick): start from the node nearest the view centre
  if (!cur || Math.abs(stSX(cur.x) - (ST_VP.x + ST_VP.w / 2)) > ST_VP.w / 2 + 4 || Math.abs(stSY(cur.y) - (ST_VP.y + ST_VP.h / 2)) > ST_VP.h / 2 + 4) {
    let best = null, bd = 1e9; for (const s of pg.nodes) { const p = pg.pos[s.id], d = Math.hypot(p.x - ST.cam.x, p.y - ST.cam.y); if (d < bd) { bd = d; best = s.id; } }
    if (best) { stSelect(best); ST.keyNav = true; } return;
  }
  let best = null, bs = 1e9;
  for (const s of pg.nodes) {
    if (s.id === ST.sel) continue;
    const p = pg.pos[s.id], dx = p.x - cur.x, dy = p.y - cur.y, along = dx * D0[0] + dy * D0[1], perp = Math.abs(dx * D0[1] - dy * D0[0]);
    if (along <= 3 || perp > along * 1.9) continue;
    const sc = along + perp * 2.1;
    if (sc < bs) { bs = sc; best = s.id; }
  }
  ST.keyNav = true;
  if (best) stSelect(best); else { sfx.deny(); ST.deny = { id: ST.sel, t: 0, soft: true }; }
}

// ---- learning: confirm once to arm, again to learn
function stConfirm(fromPointer) {
  const n = stNode(ST.sel); if (!n) return;
  const c = stCan(n);
  if (stLearned(n.id)) { sfx.menu(); ST.msg = { text: 'Already learned', t: 0 }; ST.arm = null; return; }
  if (!c.ok) { sfx.deny(); ST.deny = { id: n.id, t: 0 }; ST.msg = { text: c.why || (stLearned(n.id) ? 'Already learned' : 'Cannot learn this yet'), t: 0, bad: true }; ST.arm = null; return; }
  if (ST.arm !== n.id) { ST.arm = n.id; ST.armT = 0; sfx.glint(); return; }
  stLearn(n);
}
function stLearn(n) {
  const before = stLearned(n.id);
  if (typeof learnSkill === 'function') { try { learnSkill(n.id); } catch (e) { console.error(e); } }
  else if (!before) { SAVE.skills.push(n.id); refreshDerived(); if (n.id === 'iron_flask' && P) P.flasksR++; }
  ST.arm = null;
  if (!before && stLearned(n.id)) {
    if (typeof learnSkill !== 'function') sfx.levelup();
    ST.fx.push({ id: n.id, t: 0, key: !!n.key }); flashScreen = n.key ? 0.25 : 0.08;
    ST.msg = { text: n.key ? `Keystone awakened: ${n.name}` : `${n.name} learned`, t: 0 };
    ST.cache = null; saveGame();
  } else { sfx.deny(); ST.deny = { id: n.id, t: 0 }; }
}

// ---- before → after numbers: SK's stat() when present, else a derived-stats diff
function stStatRows(n) {
  const key = `${n.id}|${SAVE.skills.join(',')}|${levelOf(SAVE.stats)}|${SAVE.weapon}|${SAVE.charmsEq ? SAVE.charmsEq.join(',') : ''}`;
  if (ST.cache && ST.cache.key === key) return ST.cache.rows;
  const rows = stStatRowsRaw(n);
  ST.cache = { key, rows };
  return rows;
}
function stStatRowsRaw(n) {
  if (typeof n.stat === 'function') {
    let r = null;
    const keepS = SAVE.skills, keepD = D, had = keepS.includes(n.id);
    try {
      if (had) { SAVE.skills = keepS.filter(id => id !== n.id); D = derive(SAVE.stats, skillSet()); }
      r = n.stat();
    } catch (e) { r = null; } finally { SAVE.skills = keepS; D = keepD; }
    if (r == null) return [];
    const L = Array.isArray(r) ? r : [r], out = [];
    for (const q of L) {
      if (q == null) continue;
      if (typeof q === 'string' || typeof q === 'number') out.push({ line: String(q) });
      else if (Array.isArray(q)) out.push(q.length >= 3 ? { label: String(q[0]), a: q[1], b: q[2], lower: !!q[3] } : { line: q.join(' ') });
      else if (typeof q === 'object') {
        const a = q.from ?? q.a ?? q.before, b = q.to ?? q.b ?? q.after;
        out.push(a !== undefined || b !== undefined ? { label: String(q.label ?? q.name ?? q.k ?? ''), a, b, lower: !!(q.lower || q.lowerIsBetter) } : { line: String(q.text ?? q.label ?? '') });
      }
    }
    return out;
  }
  const rows = [];
  try {
    const had = stLearned(n.id), keep = SAVE.skills.slice();
    let d0, d1, f0, f1;
    try {
      SAVE.skills = keep.filter(id => id !== n.id); d0 = derive(SAVE.stats, skillSet()); f0 = flaskMax();
      SAVE.skills = keep.filter(id => id !== n.id).concat([n.id]); d1 = derive(SAVE.stats, skillSet()); f1 = flaskMax();
    } finally { SAVE.skills = keep; }
    const F = [['Max HP', 'maxHp', 0], ['Max FP', 'maxFp', 0], ['Stamina', 'maxSt', 0], ['Light attack', 'light', 0], ['Heavy attack', 'heavy', 0],
               ['Spell power', 'spell', 2], ['Cast speed', 'castSpeed', 2], ['Poise', 'poise', 0]];
    for (const [label, k, dp] of F) {
      const a = d0[k], b = d1[k]; if (typeof a !== 'number' || typeof b !== 'number' || Math.abs(a - b) < 1e-6) continue;
      const fmt = v => dp ? Math.round(v * 100) + '%' : String(Math.round(v));
      if (fmt(a) !== fmt(b)) rows.push({ label, a: fmt(a), b: fmt(b) });
    }
    if (f0 !== f1) rows.push({ label: 'Flask charges', a: f0, b: f1 });
    if (had) rows.forEach(r => (r.had = true));
  } catch (e) {}
  return rows;
}

// numbers where less is the gain (stamina costs, cooldowns, damage taken…) read green when they fall
function stLowerBetter(label) { const l = String(label || ''); return !/^max/i.test(l) && /(stamina$|stamina cost|charge time|cooldown$|^(spell|art) cooldown|taken|fade|while casting|during arts|\bFP$|cast time)/i.test(l); }

// ---- input
function stInput(M, a) {
  if (!M.st) stOpen(M);
  if (!stLayout().length) { if (['pause', 'back', 'heavy', 'roll', 'confirm'].includes(a)) menu = M.prev; return; }
  if (a === 'attack' && performance.now() - ST.ptrT < 400) return;   // the click that the pointer code already handled
  const conf = ['confirm', 'interact', 'attack', 'jump'].includes(a), back = ['pause', 'back', 'heavy', 'roll'].includes(a);
  if (back) {
    if (ST.arm) { ST.arm = null; sfx.menu(); return; }
    if (ST.summary && a !== 'pause') { ST.summary = false; sfx.menu(); return; }
    stClose(); menu = M.prev; sfx.menu(); return;
  }
  if (a === 'map') { stSetPage(ST.page + 1); return; }
  if (a === 'spell') { stSetPage(ST.page - 1); return; }
  if (ST.summary && (a === 'up' || a === 'down')) { ST.sumOff = Math.max(0, (ST.sumOff || 0) + (a === 'up' ? -1 : 1)); sfx.menu(); return; }
  if (['left', 'right', 'up', 'down'].includes(a)) { stMove(a); return; }
  if (conf) stConfirm();
}
function stClose() { ST.drag = null; ST.hover = null; ST.arm = null; try { view.style.cursor = ''; } catch (e) {} }
function stActive() { return state === 'menu' && menu && menu.screen === 'tree' && menu.st; }
{
  const _menuInput = menuInput, _renderMenu = renderMenu;
  menuInput = function (a) { if (menu && menu.screen === 'tree') return stInput(menu, a); return _menuInput(a); };
  renderMenu = function () { if (menu && menu.screen === 'tree') return stRender(menu); return _renderMenu(); };
}
// extra keys, only when nothing else is bound to them: Z / - / = zoom, B build summary
addEventListener('keydown', e => {
  if (!stActive() || e.repeat || KEY_CAPTURE || KEYMAP[e.code]) return;
  if (e.code === 'KeyZ') { const n = stZooms(stPage()).length; stZoom(ST.zi >= n - 1 ? -(n - 1) : 1); e.preventDefault(); }
  else if (e.code === 'Equal' || e.code === 'NumpadAdd') { stZoom(1); e.preventDefault(); }
  else if (e.code === 'Minus' || e.code === 'NumpadSubtract') { stZoom(-1); e.preventDefault(); }
  else if (e.code === 'KeyB') { ST.summary = !ST.summary; sfx.menu(); e.preventDefault(); }
});
// pointer: hover selects, click arms / learns, drag pans, wheel zooms; hit rects (tabs, buttons, footer) come first
function stPt(e) { const r = view.getBoundingClientRect(), k = view.width / (r.width || 1); return { x: ((e.clientX - r.left) * k - ox) / scale, y: ((e.clientY - r.top) * k - oy) / scale }; }
function stHitNode(p) {
  const pg = stPage(); if (!pg) return null;
  if (p.x > ST_PANEL.x - 2 || p.y < ST_VP.y || p.y > ST_VP.y + ST_VP.h) return null;
  let best = null, bd = 1e9;
  for (const s of pg.nodes) { const q = pg.pos[s.id], d = Math.hypot(stSX(q.x) - p.x, stSY(q.y) - p.y), r = (ST_R[stKind(s)] + 2) * ST.cam.z; if (d < r && d < bd) { bd = d; best = s.id; } }
  return best;
}
function stHitRect(p) { for (let i = ST.hits.length - 1; i >= 0; i--) { const h = ST.hits[i]; if (p.x >= h.x && p.x <= h.x + h.w && p.y >= h.y && p.y <= h.y + h.h) return h; } return null; }
view.addEventListener('pointerdown', e => {
  if (!stActive() || e.button !== 0) return;
  const p = stPt(e); ST.ptrT = performance.now();
  ST.drag = { x: p.x, y: p.y, cx: ST.tgt.x, cy: ST.tgt.y, moved: false, id: e.pointerId, touch: e.pointerType !== 'mouse' };
});
addEventListener('pointermove', e => {
  if (!stActive()) return;
  const p = stPt(e), Dg = ST.drag;
  if (Dg && Dg.id === e.pointerId) {
    if (!Dg.moved && Math.hypot(p.x - Dg.x, p.y - Dg.y) > 3) Dg.moved = true;
    if (Dg.moved) { ST.tgt.x = ST.cam.x = Dg.cx - (p.x - Dg.x) / ST.cam.z; ST.tgt.y = ST.cam.y = Dg.cy - (p.y - Dg.y) / ST.cam.z; ST.keyNav = false; }
    return;
  }
  if (e.pointerType === 'mouse') {
    const id = stHitNode(p); ST.hover = id; ST.hoverR = stHitRect(p);
    if (id && id !== ST.sel) { ST.keyNav = false; stSelect(id, 'mouse'); }
    try { view.style.cursor = id || ST.hoverR ? 'pointer' : Dg ? 'grabbing' : ''; } catch (err) {}
  }
});
addEventListener('pointerup', e => {
  const Dg = ST.drag; if (!Dg || Dg.id !== e.pointerId) return;
  ST.drag = null; ST.ptrT = performance.now();
  if (!stActive() || Dg.moved) return;
  const p = stPt(e), h = stHitRect(p);
  if (h) { h.fn(); return; }
  const id = stHitNode(p);
  if (!id) return;
  if (id !== ST.sel) { stSelect(id, Dg.touch ? 'touch' : 'mouse'); if (Dg.touch) sfx.menu(); return; }
  stConfirm(true);
});
addEventListener('pointercancel', () => { ST.drag = null; });
view.addEventListener('wheel', e => {
  if (!stActive()) return; e.preventDefault();
  if (Math.abs(e.deltaY) < 2) return;
  const p = stPt(e), dir = e.deltaY < 0 ? 1 : -1;
  if (ST.summary) { ST.sumOff = Math.max(0, (ST.sumOff || 0) - dir); return; }
  const at = dir > 0 && p.x < ST_PANEL.x ? { x: ST.cam.x + (p.x - ST_VP.x - ST_VP.w / 2) / ST.cam.z, y: ST.cam.y + (p.y - ST_VP.y - ST_VP.h / 2) / ST.cam.z } : null;
  const now = performance.now(); if (now - (ST.wheelT || 0) < 180) return; ST.wheelT = now;
  stZoom(dir, at);
}, { passive: false });
// controller extras (the fixed UI layout leaves these free): Y build summary, LT/RT zoom, right stick pans
function stPad(dt) {
  const gp = typeof padFind === 'function' ? padFind() : null; if (!gp) return;
  const down = new Set(); gp.buttons.forEach((b, i) => { if (b.pressed || b.value > 0.4) down.add(i); });
  const fresh = i => down.has(i) && !ST.padPrev.has(i);
  if (fresh(3)) { ST.summary = !ST.summary; sfx.menu(); }
  if (fresh(6)) stZoom(-1);
  if (fresh(7)) stZoom(1);
  ST.padPrev = down;
  const rx = gp.axes[2] || 0, ry = gp.axes[3] || 0;
  if (Math.hypot(rx, ry) > 0.25) { ST.tgt.x += rx * 190 * dt / ST.cam.z; ST.tgt.y += ry * 190 * dt / ST.cam.z; ST.keyNav = false; }
}

// ---- drawing helpers
function stLine(x0, y0, x1, y1, color, w, a = 1, dash) {
  vctx.globalAlpha = a; vctx.strokeStyle = color; vctx.lineWidth = Math.max(1, w * scale); vctx.lineCap = 'round';
  if (dash) vctx.setLineDash(dash.map(v => v * scale)); vctx.beginPath(); vctx.moveTo(ox + x0 * scale, oy + y0 * scale); vctx.lineTo(ox + x1 * scale, oy + y1 * scale); vctx.stroke();
  if (dash) vctx.setLineDash([]); vctx.globalAlpha = 1; vctx.lineCap = 'butt';
}
function stGlow(x, y, r, rgb, a) {
  if (a <= 0.003 || r <= 0) return;
  const X = ox + x * scale, Y = oy + y * scale, g = vctx.createRadialGradient(X, Y, 0, X, Y, r * scale);
  g.addColorStop(0, `rgba(${rgb},${a})`); g.addColorStop(1, `rgba(${rgb},0)`);
  vctx.fillStyle = g; vctx.fillRect(X - r * scale, Y - r * scale, 2 * r * scale, 2 * r * scale);
}
function stCircle(x, y, r, color, w, a = 1, fill) {
  vctx.globalAlpha = a; vctx.beginPath(); vctx.arc(ox + x * scale, oy + y * scale, Math.max(0.5, r * scale), 0, Math.PI * 2);
  if (fill) { vctx.fillStyle = fill; vctx.fill(); }
  if (color) { vctx.strokeStyle = color; vctx.lineWidth = Math.max(1, w * scale); vctx.stroke(); }
  vctx.globalAlpha = 1;
}
function stSprite(sh, tag, cx, cy, size, a = 1) {   // draw a tagged frame centred at (cx, cy), `size` low-res px square
  if (!sh.ok || !sh.has(tag)) return false;
  const f = sh.frames[sh.first(tag)];
  const S2 = Math.round(size * scale);
  vctx.globalAlpha = a; vctx.imageSmoothingEnabled = S2 < f.w;
  vctx.drawImage(sh.img, f.x, f.y, f.w, f.h, Math.round(ox + cx * scale - S2 / 2), Math.round(oy + cy * scale - S2 / 2), S2, S2);
  vctx.globalAlpha = 1; vctx.imageSmoothingEnabled = false; return true;
}
function stIcon(n, cx, cy, size, st) {
  const nm = n.icon || 'sk_' + n.id, dim = st === 'locked' || st === 'sealed';
  if (dim && stSprite(sheet('sk_icons_dim'), nm.replace(/^sk_/, 'skd_'), cx, cy, size, st === 'sealed' ? 0.55 : 0.9)) return;
  const a = dim ? 0.3 : 1;
  if (stSprite(sheet('sk_icons'), nm, cx, cy, size, a)) return;
  let found = false; for (const s of ICON_SHEETS) { const q = sheet(s); if (q.ok && q.has(nm)) { found = true; break; } }
  const name = found ? nm : (() => { for (const s of ICON_SHEETS) { const q = sheet(s); if (q.ok && q.has(n.id)) return n.id; } return nm; })();
  icon(name, cx - size / 2, cy - size / 2, size, a);
}
function stFrame(n, st, cx, cy, z, sel) {   // pixel frame from sk_frames, or a vector stand-in
  const kind = stKind(n), lvl = st === 'learned' ? 2 : st === 'avail' ? 1 : 0, sh = sheet('sk_frames');
  if (stSprite(sh, `${kind}${lvl}`, cx, cy, 32 * z)) return;
  const r = ST_R[kind] * z, col = lvl === 2 ? '#e6b85c' : lvl === 1 ? '#8a6d36' : '#3b3440';
  stCircle(cx, cy, r - 1, null, 0, 1, 'rgba(10,8,12,0.95)');
  stCircle(cx, cy, r - 1, col, 1.3 * z);
  if (kind === 'k') for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4 + Math.PI / 8; stLine(cx + Math.cos(a) * r, cy + Math.sin(a) * r, cx + Math.cos(a) * (r + 3 * z), cy + Math.sin(a) * (r + 3 * z), col, 1 * z); }
  if (kind === 'f') { uiDiamond(cx - r - 1, cy, 2 * z, col); uiDiamond(cx + r + 1, cy, 2 * z, col); }
}

// ---- background: dark parchment (built once, low-res pixels) + drifting dust in world space
function stTexture() {
  if (ST.tex) return ST.tex;
  const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d'), im = x.createImageData(W, H);
  const grid = (n, seed) => { const g2 = []; for (let j = 0; j <= n + 1; j++) { g2.push([]); for (let i = 0; i <= n * 2 + 1; i++) g2[j].push(hash2(i + seed * 97, j + seed * 31)); } return g2; };
  const oct = [[6, 0.5, grid(6, 1)], [14, 0.28, grid(14, 2)], [36, 0.14, grid(36, 3)], [90, 0.08, grid(90, 4)]];
  const smp = (g2, n, u, v) => { const X = u * n * 2, Y = v * n, i = Math.floor(X), j = Math.floor(Y), fx = X - i, fy = Y - j, s = t => t * t * (3 - 2 * t);
    const a = lerp(g2[j][i], g2[j][i + 1], s(fx)), b = lerp(g2[j + 1][i], g2[j + 1][i + 1], s(fx)); return lerp(a, b, s(fy)); };
  for (let py = 0; py < H; py++) for (let px = 0; px < W; px++) {
    const u = px / W, v = py / H; let nz = 0; for (const [n, w, g2] of oct) nz += smp(g2, n, u, v) * w;
    const fib = hash2(px >> 1, py * 7) * 0.05 + (hash2(px * 3, py) > 0.985 ? 0.08 : 0);
    const dx = u - 0.5, dy = v - 0.5, vig = 1 - Math.min(1, (dx * dx * 1.2 + dy * dy * 2.2) * 1.6);
    const k = (0.35 + nz * 0.75 + fib) * (0.45 + 0.55 * vig), i = (py * W + px) * 4;
    im.data[i] = 9 + 26 * k; im.data[i + 1] = 7 + 19 * k; im.data[i + 2] = 8 + 13 * k; im.data[i + 3] = 255;
  }
  x.putImageData(im, 0, 0);
  const dust = []; for (let i = 0; i < 260; i++) dust.push({ x: (hash2(i, 7) - 0.5) * 900, y: (hash2(i, 13) - 0.5) * 700, s: hash2(i, 29), ph: hash2(i, 41) * 6.28 });
  ST.dust = dust;
  return (ST.tex = c);
}

// ---- render
function stRender(M) {
  if (!M.st) stOpen(M);
  const dt = ST.lastT < 0 ? 0 : clamp(time - ST.lastT, 0, 0.1); ST.lastT = time;
  const L = stLayout();
  vctx.fillStyle = '#07060a'; vctx.fillRect(ox, oy, W * scale, H * scale);
  if (!L.length) { text('The tree is silent.', W / 2, H / 2, 8, UIC.muted, 'center'); return; }
  const pg = stPage(), Z = stZooms(pg); ST.zi = clamp(ST.zi, 0, Z.length - 1);
  stPad(dt);
  // camera: eased pan + zoom
  if (ST.drag && ST.drag.moved) { /* the pointer drives the camera directly */ } else stClampCam(pg);
  const kk = dt ? 1 - Math.exp(-dt * 9) : 1; ST.zi = Math.min(ST.zi, Z.length - 1);
  ST.cam.z += (Z[ST.zi] - ST.cam.z) * (dt ? 1 - Math.exp(-dt * 10) : 1);
  if (Math.abs(ST.cam.z - Z[ST.zi]) < 0.002) ST.cam.z = Z[ST.zi];
  ST.cam.x += (ST.tgt.x - ST.cam.x) * kk; ST.cam.y += (ST.tgt.y - ST.cam.y) * kk;
  for (const f of ST.fx) f.t += dt; ST.fx = ST.fx.filter(f => f.t < 1.4);
  if (ST.deny) { ST.deny.t += dt; if (ST.deny.t > 0.4) ST.deny = null; }
  if (ST.msg) { ST.msg.t += dt; if (ST.msg.t > 2.6) ST.msg = null; }
  if (ST.arm) ST.armT += dt;
  ST.openT = (ST.openT || 0) + dt;
  ST.hits = [];
  const z = ST.cam.z, X = stSX, Y = stSY;

  // ---- parchment field
  vctx.imageSmoothingEnabled = false; vctx.drawImage(stTexture(), ox, oy, W * scale, H * scale);
  vctx.save(); vctx.beginPath(); vctx.rect(ox, oy + ST_VP.y * scale, W * scale, ST_VP.h * scale); vctx.clip();
  // dust motes (slight parallax)
  for (const d of ST.dust) {
    const sx = ST_VP.x + ST_VP.w / 2 + (d.x - ST.cam.x * 0.6) * z * 0.6, sy = ST_VP.y + ST_VP.h / 2 + (d.y - ST.cam.y * 0.6) * z * 0.6;
    if (sx < -2 || sx > W + 2 || sy < 20 || sy > H) continue;
    const a = (0.12 + 0.18 * d.s) * (0.6 + 0.4 * Math.sin(time * (0.8 + d.s) + d.ph));
    uiRect(sx, sy, d.s > 0.85 ? 1 : 0.6, d.s > 0.85 ? 1 : 0.6, d.s > 0.7 ? '#e6c77a' : '#a89a80', a);
  }
  if (pg.id === 'tree') stDrawTreeBack(pg, z);
  if (pg.gallery) stDrawGalleryBack(pg, z);
  stDrawEdges(pg, z);
  stDrawNodes(pg, z);
  stDrawForks(pg, z);
  stDrawCursor(pg, z);
  vctx.restore();

  // ---- chrome
  if (ST.summary) stSummarySheet();
  uiStrips();
  stHeader(pg, L);
  if (ST.summary) stSummary(); else stDetail(pg);
  stLegend(pg);
  stFooter();
  if (ST.openT < 0.3) { vctx.fillStyle = `rgba(5,4,8,${1 - ST.openT / 0.3})`; vctx.fillRect(ox, oy, W * scale, H * scale); }
}

function stDrawTreeBack(pg, z) {
  const cx = stSX(0), cy = stSY(0), gold = UI_RGB.gold;
  // branch nebulae
  for (const [br, B] of Object.entries(pg.brs)) stGlow(stSX(B.cx), stSY(B.cy), B.ext * 1.5 * z, stRgb(stBranch(br).color), 0.075);
  stGlow(cx, cy, 70 * z, '255,170,80', 0.10);
  // arcane rings on the tiers, ticks on the outermost; a slow-turning outer rune ring
  const tiers = pg.tiers || [], kR = tiers.length ? tiers[tiers.length - 1] : 150;
  const rOut = pg.ring || kR + 40, wc = stRgb(stBranch('way').color);
  for (const r of [kR * 0.36, kR * 0.7, kR + 14]) stCircle(cx, cy, r * z, `rgba(${gold},1)`, 0.35, 0.07);
  // the outer ring (the Wayfarer's road when it sits there): a double band with turning ticks and runes
  stCircle(cx, cy, (rOut - 5) * z, `rgba(${gold},1)`, 0.4, 0.16);
  stCircle(cx, cy, (rOut + 5) * z, `rgba(${gold},1)`, 0.4, 0.16);
  if (pg.ring) stCircle(cx, cy, rOut * z, `rgba(${wc},1)`, 0.6, 0.22);
  const rot = time * 0.015;
  for (let i = 0; i < 96; i++) {
    const a = rot + i * Math.PI / 48, big = i % 8 === 0, r0 = (rOut + 5) * z, r1 = (rOut + (big ? 11 : 7.5)) * z;
    stLine(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0, cx + Math.cos(a) * r1, cy + Math.sin(a) * r1, `rgba(${gold},1)`, 0.35, big ? 0.3 : 0.13);
  }
  for (let i = 0; i < 16; i++) { const a = -rot * 1.3 + (i + 0.5) * Math.PI / 8; uiDiamond(cx + Math.cos(a) * (rOut - 9) * z, cy + Math.sin(a) * (rOut - 9) * z, 1 * Math.max(0.6, z), UIC.accent, 0.3); }
  // spokes from the ember to each branch root
  for (const s of pg.nodes) {
    if ((s.req || []).length || !ST_MAIN.includes(s.br)) continue;
    const p = pg.pos[s.id], d = Math.hypot(p.x, p.y) || 1, ux = p.x / d, uy = p.y / d, r = ST_R[stKind(s)] + 1;
    const lit = stLearned(s.id), c = stBranch(s.br).color;
    stLine(cx + ux * 13 * z, cy + uy * 13 * z, stSX(p.x - ux * r), stSY(p.y - uy * r), lit ? c : '#4a3e2c', lit ? 1.1 : 0.8, lit ? 0.85 : 0.6);
  }
  // the ember at the heart
  const pul = 0.5 + 0.5 * Math.sin(time * 2.2);
  stGlow(cx, cy, 22 * z, '255,150,60', 0.3 + 0.12 * pul);
  if (!stSprite(sheet('sk_frames'), 'core', cx, cy, 32 * z)) { stCircle(cx, cy, 9 * z, UIC.gold, 1, 0.9, 'rgba(30,16,8,0.95)'); uiDiamond(cx, cy, 4 * z, '#ffb050'); }
  // the Wayfarer's name on its road
  if (pg.ring) {
    const wy = cy + (rOut + 16) * z, nm = stBranch('way').name.toUpperCase(), sz = z < 0.5 ? 5.2 : 6;
    const got = pg.nodes.filter(q => q.br === 'way' && stLearned(q.id)).length, all = pg.nodes.filter(q => q.br === 'way').length;
    if (wy < ST_VP.y + ST_VP.h + 10) { text(nm, cx, wy, sz, stBranch('way').color, 'center', { spacing: 2, weight: 600, alpha: 0.9 }); text(`${got} / ${all}`, cx, wy + 6.5, 4.4, got ? UIC.muted : UIC.faint, 'center', { weight: 500 }); }
  }
  // branch name, keystone and investment, just beyond each keystone (screen-space, so it never sits on a node)
  for (const [br, B] of Object.entries(pg.brs)) {
    const b = stBranch(br), ns = pg.nodes.filter(q => q.br === br), got = ns.filter(q => stLearned(q.id)).length, key = B.key && stNode(B.key);
    const ux = Math.cos(B.ang), uy = Math.sin(B.ang), nm = b.name.toUpperCase(), sz = z < 0.5 ? 6 : 6.8;
    const small = z < 0.45, kn = key && !small ? key.name : '', kLit = key && stLearned(key.id), cnt = `${got}/${ns.length}`;
    const w = small ? textW(nm, sz) + nm.length * 2 + textW(cnt, 4.3, 500) + 6 : Math.max(textW(nm, sz) + nm.length * 2, kn ? textW(kn, 4.8, 600) + 4 : 0) + 4, h = small ? 8 : kn ? 22 : 15;
    // just past the keystone; branches that point sideways or down put it outside the Wayfarer ring instead (its nodes sit on it)
    const ext = Math.abs(ux) * w / 2 + Math.abs(uy) * h / 2, outside = pg.ring && uy > -0.8;
    const bx = outside ? stSX(0) : stSX(B.kx), by = outside ? stSY(0) : stSY(B.ky), d0 = outside ? (pg.ring + 6) * z + 5 : ST_R.k * z + (z < 0.5 ? 3 : 5);
    const lx = bx + ux * (d0 + ext), ly = by + uy * (d0 + ext) - h / 2 + 6;
    stGlow(lx, ly - 2, 24, stRgb(b.color), 0.10);
    if (small) {   // overview: NAME n/12 on one line
      const tw = textW(nm, sz) + nm.length * 2, x0 = lx - w / 2;
      text(nm, x0 + tw / 2, ly, sz, b.color, 'center', { spacing: 2, weight: 600 });
      text(cnt, x0 + tw + 4, ly, 4.3, got ? UIC.muted : UIC.faint, 'left', { weight: 500 });
      continue;
    }
    text(nm, lx, ly, sz, b.color, 'center', { spacing: 2, weight: 600 });
    const tw = textW(nm, sz) + nm.length * 2;
    uiFade(lx - tw / 2 - 3, lx - tw / 2 - 16, ly - sz * 0.35, stRgb(b.color), 0.6); uiFade(lx + tw / 2 + 1, lx + tw / 2 + 14, ly - sz * 0.35, stRgb(b.color), 0.6);
    if (kn) text(kn, lx, ly + 7, 4.8, kLit ? b.color : '#9a8f78', 'center', { weight: 600, alpha: kLit ? 1 : 0.9 });
    text(`${got} / ${ns.length}`, lx, ly + (kn ? 13.5 : 7), 4.3, got ? UIC.muted : UIC.faint, 'center', { weight: 500 });
  }
}
function stDrawGalleryBack(pg, z) {
  const cls = stEquippedCls();
  for (const s of pg.nodes) {
    const p = pg.pos[s.id], x = stSX(p.x), y = stSY(p.y), on = s.cls === cls, sel = s.id === ST.sel, w = 46, h = 62, x0 = x - w / 2, y0 = y - 27;
    // an alcove: dark niche, gold hairline, the class above and the mastery's name below
    const g = vctx.createLinearGradient(0, oy + y0 * scale, 0, oy + (y0 + h) * scale);
    g.addColorStop(0, on ? 'rgba(70,52,22,0.7)' : 'rgba(22,17,20,0.7)'); g.addColorStop(1, on ? 'rgba(30,22,12,0.7)' : 'rgba(10,8,11,0.7)');
    vctx.fillStyle = g; vctx.fillRect(ox + x0 * scale, oy + y0 * scale, w * scale, h * scale);
    vctx.strokeStyle = sel ? 'rgba(245,227,176,0.8)' : on ? 'rgba(230,199,122,0.6)' : 'rgba(109,90,58,0.45)'; vctx.lineWidth = Math.max(1, scale * 0.5);
    vctx.strokeRect(ox + x0 * scale + 0.5, oy + y0 * scale + 0.5, w * scale - 1, h * scale - 1);
    uiDiamond(x, y0, 1.6, on ? UIC.gold : '#5a4a30');
    if (on) stGlow(x, y, 28, UI_RGB.gold, 0.16 + 0.05 * Math.sin(time * 3));
    const cn = (ST_CLS_NAME[s.cls] || s.cls || '').toUpperCase();
    text(cn, x, y0 + 8, uiFit(cn, w - 4, 4, 3.2, 600), on ? '#8fd89a' : UIC.dim, 'center', { spacing: 0.6, weight: 600 });
    const nl = wrap(s.name, w - 6, 4.6).slice(0, 2);
    nl.forEach((l, i) => text(l, x, y0 + h - (nl.length > 1 ? 11 : 5) + i * 6, 4.6, stLearned(s.id) ? UIC.hi : UIC.muted, 'center', { weight: 500 }));
  }
  const wn = WEAPONS[SAVE.weapon] ? WEAPONS[SAVE.weapon].name : '';
  text('Each mastery wakes only while its weapon class is in your hand', ST_VP.x + ST_VP.w / 2, ST_VP.y + 12, 5, UIC.dim, 'center', { weight: 400 });
  if (wn) text(`In hand: ${wn} (${ST_CLS_NAME[cls] || cls})`, ST_VP.x + ST_VP.w / 2, ST_VP.y + 20, 4.8, '#8fd89a', 'center', { weight: 500 });
}
function stTrim(pa, pb, ra, rb) {   // segment between two node rims
  const dx = pb.x - pa.x, dy = pb.y - pa.y, d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
  return [pa.x + ux * ra, pa.y + uy * ra, pb.x - ux * rb, pb.y - uy * rb, d];
}
function stDrawEdges(pg, z) {
  const fxBy = {}; for (const f of ST.fx) fxBy[f.id] = f;
  for (const s of pg.nodes) {
    for (const r of s.req || []) {
      const p = stNode(r); if (!p || !pg.pos[r]) continue;
      const A = pg.pos[r], B = pg.pos[s.id], [x0, y0, x1, y1, d] = stTrim(A, B, ST_R[stKind(p)] + 1, ST_R[stKind(s)] + 1);
      const la = stLearned(r), lb = stLearned(s.id), st = stState(s), col = stBranch(s.br).color;
      if (pg.ring && s.br === 'way' && p.br === 'way') { stRingEdge(pg, A, B, ST_R[stKind(p)] + 1, ST_R[stKind(s)] + 1, la && lb ? 2 : la && st === 'avail' ? 1 : 0, col, z, fxBy[s.id]); continue; }
      const sx0 = stSX(x0), sy0 = stSY(y0), sx1 = stSX(x1), sy1 = stSY(y1);
      if (la && lb) {
        const f = fxBy[s.id], k = f ? clamp(f.t / 0.45, 0, 1) : 1;
        stLine(sx0, sy0, sx1, sy1, '#3a2c18', 2.2 * z, 0.9);
        stLine(sx0, sy0, sx0 + (sx1 - sx0) * k, sy0 + (sy1 - sy0) * k, col, 2.4 * z, 0.25);
        stLine(sx0, sy0, sx0 + (sx1 - sx0) * k, sy0 + (sy1 - sy0) * k, '#f0c870', 1.1 * z, 0.95);
        // an ember spark travels down each lit path
        const t = (time * 0.45 + hash2(s.id.length * 13, r.length * 7)) % 1;
        if (k >= 1) { const px = lerp(sx0, sx1, t), py = lerp(sy0, sy1, t); stGlow(px, py, 3 * z, '255,220,150', 0.55); }
      } else if (la && st === 'avail') {
        stLine(sx0, sy0, sx1, sy1, '#1a140e', 2 * z, 0.9);
        stLine(sx0, sy0, sx1, sy1, '#b08a3a', 0.9 * z, 0.75 + 0.2 * Math.sin(time * 3));
      } else {
        stLine(sx0, sy0, sx1, sy1, '#0c0a0e', 1.8 * z, 0.8);
        stLine(sx0, sy0, sx1, sy1, st === 'sealed' ? '#4a2226' : '#3d3428', 0.8 * z, 0.9);
      }
    }
  }
}
function stRingEdge(pg, A, B, ra, rb, lvl, col, z, f) {
  const R0 = pg.ring, a0 = Math.atan2(A.y, A.x), a1 = Math.atan2(B.y, B.x);
  let da = a1 - a0; while (da > Math.PI) da -= 2 * Math.PI; while (da < -Math.PI) da += 2 * Math.PI;
  const t0 = a0 + Math.sign(da) * ra / R0, t1 = a1 - Math.sign(da) * rb / R0, cx = ox + stSX(0) * scale, cy = oy + stSY(0) * scale, rr = R0 * z * scale;
  const k = f ? clamp(f.t / 0.45, 0, 1) : 1;
  const draw = (color, w, a, to) => { vctx.globalAlpha = a; vctx.strokeStyle = color; vctx.lineWidth = Math.max(1, w * scale); vctx.beginPath(); vctx.arc(cx, cy, rr, t0, to, da < 0); vctx.stroke(); vctx.globalAlpha = 1; };
  if (lvl === 2) { draw('#3a2c18', 2.2 * z, 0.9, t1); draw(col, 2.4 * z, 0.25, t0 + (t1 - t0) * k); draw('#f0c870', 1.1 * z, 0.95, t0 + (t1 - t0) * k); }
  else if (lvl === 1) { draw('#1a140e', 2 * z, 0.9, t1); draw('#b08a3a', 0.9 * z, 0.75 + 0.2 * Math.sin(time * 3), t1); }
  else { draw('#0c0a0e', 1.8 * z, 0.8, t1); draw('#3d3428', 0.8 * z, 0.9, t1); }
}
function stDrawForks(pg, z) {
  // every fork node wears a crimson link-stud on the rim facing its partner; the cursor on either one draws the
  // full "one or the other" arc (bowed away from the trunk between them) and rings the partner
  const done = new Set(), cur = stNode(ST.sel);
  for (const s of pg.nodes) for (const e of s.excl || []) {
    const o = stNode(e); if (!o || !pg.pos[e]) continue;
    const A = pg.pos[s.id], B = pg.pos[e], dx = B.x - A.x, dy = B.y - A.y, d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
    const chosen = stLearned(s.id), sealed = stLearned(e), r = ST_R[stKind(s)] + 1.6;
    const sx = stSX(A.x + ux * r), sy = stSY(A.y + uy * r);
    uiDiamond(sx, sy, 2.4 * Math.max(0.7, z), '#120a0c');
    uiDiamond(sx, sy, 1.8 * Math.max(0.7, z), chosen ? '#f0c870' : sealed ? '#5a2226' : '#d0606e');
    const key = [s.id, e].sort().join('|'); if (done.has(key)) continue; done.add(key);
    if (!cur || (cur.id !== s.id && cur.id !== e)) continue;
    // the arc: a quadratic bowed outward from the tree's heart
    const mx = (A.x + B.x) / 2, my = (A.y + B.y) / 2, ml = Math.hypot(mx, my) || 1, bow = pg.id === 'tree' ? d * 0.55 : d * 0.3;
    const cx = mx + (pg.id === 'tree' ? mx / ml : 0) * bow, cy = my + (pg.id === 'tree' ? my / ml : -1) * bow;
    const a0x = A.x + ((cx - A.x) / Math.hypot(cx - A.x, cy - A.y)) * (ST_R[stKind(s)] + 3), a0y = A.y + ((cy - A.y) / Math.hypot(cx - A.x, cy - A.y)) * (ST_R[stKind(s)] + 3);
    const b0x = B.x + ((cx - B.x) / Math.hypot(cx - B.x, cy - B.y)) * (ST_R[stKind(o)] + 3), b0y = B.y + ((cy - B.y) / Math.hypot(cx - B.x, cy - B.y)) * (ST_R[stKind(o)] + 3);
    const done2 = stLearned(s.id) || stLearned(e), col = done2 ? '#8a3a3a' : '#e08090';
    vctx.save(); vctx.setLineDash([1.6 * scale, 1.6 * scale]); vctx.lineDashOffset = -time * 6 * scale;
    vctx.strokeStyle = '#140a0c'; vctx.lineWidth = Math.max(1, 2 * z * scale); vctx.beginPath(); vctx.moveTo(ox + stSX(a0x) * scale, oy + stSY(a0y) * scale); vctx.quadraticCurveTo(ox + stSX(cx) * scale, oy + stSY(cy) * scale, ox + stSX(b0x) * scale, oy + stSY(b0y) * scale); vctx.stroke();
    vctx.strokeStyle = col; vctx.lineWidth = Math.max(1, 0.9 * z * scale); vctx.stroke(); vctx.restore();
    const px = 0.25 * a0x + 0.5 * cx + 0.25 * b0x, py = 0.25 * a0y + 0.5 * cy + 0.25 * b0y;
    uiDiamond(stSX(px), stSY(py), 5 * Math.max(0.75, z), 'rgba(14,8,10,0.96)'); uiDiamond(stSX(px), stSY(py), 5 * Math.max(0.75, z), col, 1, true);
    text('or', stSX(px), stSY(py) + 1.5 * Math.max(0.75, z), 4.2 * Math.max(0.75, z), done2 ? '#b07070' : '#ffd0d6', 'center', { weight: 700, shadow: false });
    const other = cur.id === s.id ? B : A, on = cur.id === s.id ? o : s, orr = ST_R[stKind(on)] * z + 3.5;
    stCircle(stSX(other.x), stSY(other.y), orr, col, 0.8, 0.5 + 0.35 * uiPulse(5));
  }
}
function stDrawNodes(pg, z) {
  const cls = stEquippedCls(), pts = stPts(), fxBy = {}; for (const f of ST.fx) fxBy[f.id] = f;
  const order = [...pg.nodes].sort((a, b) => (a.id === ST.sel) - (b.id === ST.sel));
  for (const s of order) {
    const p = pg.pos[s.id]; let x = stSX(p.x), y = stSY(p.y);
    if (x < -30 || x > W + 30 || y < ST_VP.y - 30 || y > ST_VP.y + ST_VP.h + 30) continue;
    const st = stState(s), kind = stKind(s), r = ST_R[kind] * z, col = stBranch(s.br).color, rgb = stRgb(col);
    const dn = ST.deny && ST.deny.id === s.id ? ST.deny : null; if (dn && !dn.soft) x += Math.sin(dn.t * 60) * 1.6 * (1 - dn.t / 0.4);
    const dormant = s.cls && st === 'learned' && s.cls !== cls;
    // halo
    if (st === 'learned') stGlow(x, y, r * (kind === 'k' ? 2.6 : 2), rgb, dormant ? 0.12 : kind === 'k' ? 0.42 : 0.28);
    else if (st === 'avail' && pts >= (s.cost || 0)) stGlow(x, y, r * 1.9, UI_RGB.gold, 0.1 + 0.1 * Math.sin(time * 3 + p.x * 0.05));
    if (kind === 'k' && st !== 'learned') stGlow(x, y, r * 2.2, rgb, 0.08);
    stFrame(s, st, x, y, z, s.id === ST.sel);
    stIcon(s, x, y, 16 * z, dormant ? 'avail' : st);
    if (st === 'sealed') {   // a crimson slash across the node
      stLine(x - r * 0.62, y - r * 0.62, x + r * 0.62, y + r * 0.62, '#1a0608', 2.6 * z, 0.9); stLine(x - r * 0.62, y - r * 0.62, x + r * 0.62, y + r * 0.62, '#c03040', 1.1 * z, 0.95);
    }
    if (dormant) stCircle(x, y, r - 1.2 * z, 'rgba(10,8,12,1)', 0, 0.45, 'rgba(10,8,12,0.45)');
    // cost pip (unlearned), bottom right
    if (st !== 'learned' && z > 0.55) {
      const cx = x + r * 0.78, cy = y + r * 0.78, ok = st === 'avail' && pts >= s.cost;
      stCircle(cx, cy, 3.1, ok ? '#e6c77a' : '#4a3e2c', 0.5, 1, 'rgba(12,9,8,0.96)');
      text(String(s.cost), cx, cy + 1.6, 4.4, ok ? '#ffd070' : st === 'avail' ? '#b8ab90' : '#6a6050', 'center', { weight: 700, shadow: false });
    }
    // learn burst
    const f = fxBy[s.id];
    if (f) {
      const k = f.t / 1.4, rr = r + (f.key ? 40 : 24) * Math.pow(k, 0.5);
      stCircle(x, y, rr, col, (1 - k) * 2, 1 - k); stCircle(x, y, rr * 0.7, '#fff0c0', (1 - k) * 1.2, (1 - k) * 0.8);
      stGlow(x, y, r * 3, '255,230,170', 0.5 * (1 - k));
      for (let i = 0; i < 10; i++) { const a = i * 0.628 + hash2(i, 3) * 0.5, d = r + 30 * k * (0.6 + hash2(i, 9) * 0.6); uiRect(x + Math.cos(a) * d, y + Math.sin(a) * d, 1, 1, i % 2 ? col : '#ffe0a0', 1 - k); }
    }
  }
}
function stDrawCursor(pg, z) {   // gold corner brackets that breathe; a name tag under the node
  const s = stNode(ST.sel); if (!s || !pg.pos[s.id]) return;
  const p = pg.pos[s.id], x = stSX(p.x), y = stSY(p.y), r = ST_R[stKind(s)] * z + 3 + uiPulse(5) * 1.2, arm = ST.arm === s.id;
  const c = arm ? '#fff0b8' : UIC.hi, L0 = 4;
  for (const [sx, sy] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
    stLine(x + sx * r, y + sy * r, x + sx * (r - L0), y + sy * r, c, 0.9, 0.95); stLine(x + sx * r, y + sy * r, x + sx * r, y + sy * (r - L0), c, 0.9, 0.95);
  }
  if (arm) { const k = (ST.armT * 1.3) % 1; stCircle(x, y, r + 2 + k * 8, '#ffe8a0', 1.1 * (1 - k), 1 - k); }
  if (!pg.gallery) {
    const nm = s.name, sz = 5.2, w = textW(nm, sz, 600) + 8, ty = y + ST_R[stKind(s)] * z + 11;
    const tx = clamp(x, ST_VP.x + w / 2 + 2, ST_PANEL.x - w / 2 - 4);
    vctx.fillStyle = 'rgba(8,6,10,0.88)'; vctx.fillRect(ox + (tx - w / 2) * scale, oy + (ty - 6.2) * scale, w * scale, 8.4 * scale);
    uiHair(tx - w / 2, ty + 2.2, w, UIC.line, 0.9);
    text(nm, tx, ty, sz, UIC.hi, 'center', { weight: 600 });
  }
}

// ---- header: points, page tabs, level
function stHeader(pg, L) {
  const pts = stPts();
  // points medallion (left)
  stGlow(18, 12, 14, '255,200,110', pts ? 0.25 + 0.1 * uiPulse(3) : 0.05);
  uiDiamond(18, 12, 6.5, pts ? '#3a2a12' : '#1a1612'); uiDiamond(18, 12, 6.5, pts ? UIC.gold : '#5a4a30', 1, true);
  text(String(pts), 18, 14.4, pts > 9 ? 6 : 7, pts ? '#ffe2a0' : UIC.faint, 'center', { weight: 700 });
  text('SKILL POINTS', 29, 10.5, 4.4, UIC.dim, 'left', { spacing: 1, weight: 600 });
  const spent = SAVE.skills.reduce((a, id) => a + ((stNode(id) || {}).cost || 0), 0);
  text(`${spent} spent · level ${levelOf(SAVE.stats)}`, 29, 17.5, 4.6, UIC.faint, 'left', { weight: 400 });
  // tabs (centre)
  const n = L.length, pitch = 80, x0 = 172 - pitch * (n - 1) / 2;
  L.forEach((P2, i) => {
    const x = x0 + i * pitch, sel = i === ST.page, nm = P2.name.toUpperCase(), tw = textW(nm, 6.2) + nm.length * 1.5;
    text(nm, x, 13, 6.2, sel ? UIC.hi : UIC.faint, 'center', { spacing: 1.5, weight: sel ? 600 : 500 });
    if (sel) { uiDiamond(x, 17.5, 1.2, UIC.gold); uiFade(x - 3, x - tw / 2 - 4, 17.3, UI_RGB.gold, 0.9); uiFade(x + 3, x + tw / 2 + 4, 17.3, UI_RGB.gold, 0.9); }
    ST.hits.push({ x: x - tw / 2 - 4, y: 4, w: tw + 8, h: 15, fn: () => { if (i !== ST.page) stSetPage(i); } });
    if (i < n - 1) uiDiamond(x + pitch / 2, 11, 0.9, '#5a4a30');
  });
  if (n > 1) {
    const w0 = textW(L[0].name.toUpperCase(), 6.2) + L[0].name.length * 1.5, w1 = textW(L[n - 1].name.toUpperCase(), 6.2) + L[n - 1].name.length * 1.5;
    if (kl('Q')) uiKey(PAD.active ? 'LB' : kl('Q'), x0 - w0 / 2 - 7, 13.5, { size: 4.6, align: 'right' });
    uiKey(PAD.active ? 'RB' : kl('Tab'), x0 + (n - 1) * pitch + w1 / 2 + 7, 13.5, { size: 4.6 });
  }
  // title (right)
  text('SKILL TREE', 372, 13, 7, UIC.gold, 'right', { spacing: 2.2, weight: 600 });
  const tw = textW('SKILL TREE', 7) + 10 * 2.2; uiFade(372 - tw - 3, 372 - tw - 40, 10.6, UI_RGB.accent, 0.7);
  const Zs = stZooms(pg), zl = Zs.length === 1 ? '' : ST.zi === 0 ? 'overview' : ST.zi === Zs.length - 1 ? 'close' : 'middle';
  if (zl) { text(zl, 372, 20.5, 4.4, UIC.faint, 'right', { weight: 400 }); for (let i = 0; i < Zs.length; i++) uiDiamond(372 - textW(zl, 4.4, 400) - 5 - (Zs.length - 1 - i) * 4.5, 19, i === ST.zi ? 1.4 : 0.9, i <= ST.zi ? UIC.gold : '#4a3e2c'); }
}

// ---- detail panel
function stDetail(pg) {
  const P0 = ST_PANEL, s = stNode(ST.sel);
  panel(P0.x, P0.y, P0.w, P0.h, 0.94);
  stPanelTabs();
  if (!s) return;
  const x = P0.x + 7, w = P0.w - 14, st = stState(s), b = stBranch(s.br), kind = stKind(s), cls = stEquippedCls();
  let y = P0.y + 22;
  // kind line
  const kindTxt = kind === 'k' ? 'KEYSTONE' : kind === 'm' ? 'MASTERY' : kind === 'f' ? 'FORK' : s.br === 'way' ? 'TECHNIQUE' : 'PASSIVE';
  uiDiamond(x + 1.5, y - 1.7, 1.6, b.color);
  text(`${b.name.toUpperCase()} · ${kindTxt}`, x + 6, y, 4.5, b.color, 'left', { spacing: 0.9, weight: 600 });
  y += 5;
  // icon in its frame + name
  stGlow(x + 12, y + 12, 16, stRgb(b.color), st === 'learned' ? 0.3 : 0.08);
  stFrame(s, st === 'sealed' ? 'locked' : st, x + 12, y + 12, 1, false);
  stIcon(s, x + 12, y + 12, 16, st === 'sealed' ? 'locked' : st === 'locked' ? 'avail' : st);
  const nl = wrap(s.name, w - 30, 7).slice(0, 2), nsz = nl.length > 1 ? 6.4 : 7.2;
  nl.forEach((l, i) => text(l, x + 28, y + (nl.length > 1 ? 9 : 12) + i * 7.5, nsz, st === 'learned' ? UIC.hi : UIC.gold, 'left', { weight: 600 }));
  // state line
  const pts = stPts(), c = stCan(s);
  let stTxt, stCol;
  if (st === 'learned') { const dor = s.cls && s.cls !== cls; stTxt = dor ? 'Learned · dormant' : 'Learned'; stCol = dor ? UIC.dim : UIC.up; }
  else if (st === 'sealed') { stTxt = 'Sealed by your choice'; stCol = '#e07a70'; }
  else if (st === 'locked') { stTxt = `Locked · ${s.cost} pt${s.cost === 1 ? '' : 's'}`; stCol = UIC.faint; }
  else { stTxt = `${s.cost} point${s.cost === 1 ? '' : 's'}`; stCol = pts >= s.cost ? '#ffd070' : UIC.muted; }
  text(stTxt, x + 28, y + (nl.length > 1 ? 24.5 : 21), 5, stCol, 'left', { weight: 500 });
  y += 30;
  uiFade(x, x + w, y - 2, UI_RGB.accent, 0.55);
  // description
  const desc = wrap(s.desc || '', w, 5.5);
  y += 5;
  const maxY = P0.y + P0.h - 20;
  for (const l of desc) { if (y > maxY - 4) break; text(l, x, y, 5.5, UIC.body, 'left', { weight: 400 }); y += 7; }
  // numbers
  const rows = s.cls ? [] : stStatRows(s);
  if (rows.length && y < maxY - 12) {
    y += 2; uiHead(st === 'learned' ? 'without → with' : 'before → after', x, y + 2, w); y += 9;
    for (const r of rows) {
      if (y > maxY - 2) break;
      if (r.line) { text(r.line, x, y, 5.2, UIC.text, 'left', { weight: 500 }); y += 7; continue; }
      text(r.label, x, y, 5.1, UIC.muted, 'left', { weight: 400 });
      const bv = String(r.b ?? ''), av = String(r.a ?? ''), low = r.lower || stLowerBetter(r.label), better = low ? parseFloat(bv) < parseFloat(av) : parseFloat(bv) > parseFloat(av);
      const bw = textW(bv, 5.3, 700);
      text(bv, x + w, y, 5.3, isNaN(parseFloat(bv)) ? UIC.text : better ? UIC.up : UIC.down, 'right', { weight: 700 });
      text('→', x + w - bw - 5, y, 5, UIC.faint, 'center', { weight: 400 });
      text(av, x + w - bw - 9, y, 5.3, UIC.dim, 'right', { weight: 500 });
      y += 7;
    }
  }
  // relations: requirements, fork partner, weapon class
  const notes = [];
  for (const e of s.excl || []) { const o = stNode(e); if (o && !stLearned(e)) notes.push({ t: st === 'learned' ? `Seals ${o.name}` : `Fork · learning it seals ${o.name}`, c: '#d8a0a0' }); }
  if (s.cls) notes.push({ t: s.cls === cls ? `Active: ${ST_CLS_NAME[s.cls] || s.cls} equipped` : `Wakes with a ${ST_CLS_NAME[s.cls] || s.cls}`, c: s.cls === cls ? UIC.up : UIC.dim });
  const nl2 = notes.map(nt => ({ ...nt, L: wrap(nt.t, w, 5).slice(0, 2) })), nh = nl2.reduce((a, nt) => a + nt.L.length * 6.5, 0);
  let ny = Math.max(y + 3, maxY - nh + 5);
  for (const nt of nl2) for (const l of nt.L) { if (ny > maxY + 6) break; text(l, x, ny, 5, nt.c, 'left', { weight: 500 }); ny += 6.5; }
  // action bar
  const ay = P0.y + P0.h - 6;
  uiFade(x, x + w, ay - 9, UI_RGB.accent, 0.4);
  const btn = (label, key, col, fn) => {
    const kw = key ? uiKey(key, x, ay, { size: 4.8 }) + 3 : 0;
    text(label, x + kw, ay, 5.3, col, 'left', { weight: 600 });
    ST.hits.push({ x: P0.x, y: ay - 8, w: P0.w, h: 11, fn });
  };
  const K = kl('Enter');
  if (ST.msg && ST.msg.t < 2.2 && (ST.msg.bad || st === 'learned')) text(ST.msg.text, x, ay, 5.2, ST.msg.bad ? '#e8907a' : /learned$|awakened/.test(ST.msg.text) && ST.msg.text !== 'Already learned' ? UIC.up : UIC.muted, 'left', { weight: 600 });
  else if (ST.arm === s.id) btn(`Confirm · learn for ${s.cost}`, K, `rgba(255,236,180,${0.75 + 0.25 * uiPulse(8)})`, () => stConfirm(true));
  else if (c.ok) btn(`Learn · ${s.cost} point${s.cost === 1 ? '' : 's'}`, K, UIC.gold, () => stConfirm(true));
  else if (st !== 'learned') text(c.why || 'Not yet', x, ay, 5, UIC.faint, 'left', { weight: 400 });
  else text(s.cls && s.cls !== cls ? 'Dormant until that class is in hand' : 'Rebirth at a shrine to unlearn', x, ay, 4.8, UIC.faint, 'left', { weight: 400 });
}
function stPanelTabs() {
  const P0 = ST_PANEL, y = P0.y + 9, mid = P0.x + P0.w / 2;
  [['NODE', false], ['BUILD', true]].forEach(([nm, sum], i) => {
    const x = mid + (i ? 22 : -22), on = ST.summary === sum;
    text(nm, x, y, 4.8, on ? UIC.hi : UIC.faint, 'center', { spacing: 1.2, weight: on ? 600 : 500 });
    if (on) uiFade(x - 12, x + 12, y + 2.3, UI_RGB.gold, 0.8);
    ST.hits.push({ x: x - 16, y: y - 7, w: 32, h: 10, fn: () => { if (ST.summary !== sum) { ST.summary = sum; sfx.menu(); } } });
  });
  uiKey(PAD.active ? 'Y' : 'B', P0.x + P0.w - 6, y + 0.3, { size: 4.2, align: 'right', dim: true });
}

// ---- build summary: investment per branch + keystones (right panel), SK's readable totals on a sheet over the field
function stSumLines() {
  let L = [];
  if (typeof skillBuildSummary === 'function') { try { L = skillBuildSummary() || []; } catch (e) { L = []; } }
  if (!Array.isArray(L)) L = [L];
  return L.map(q => typeof q === 'string' ? { t: q } : Array.isArray(q) ? { l: String(q[0]), v: String(q[1] ?? '') } : { l: String(q.label ?? q.name ?? q.k ?? ''), v: String(q.value ?? q.v ?? q.text ?? '') })
          .filter(q => !(q.t && /^keystone:/i.test(q.t)));
}
function stSummary() {
  const P0 = ST_PANEL; panel(P0.x, P0.y, P0.w, P0.h, 0.94); stPanelTabs();
  const x = P0.x + 7, w = P0.w - 14; let y = P0.y + 22;
  const brs = SKILL_BRANCH_IDS(), pts = stPts();
  const spent = SAVE.skills.reduce((a, id) => a + ((stNode(id) || {}).cost || 0), 0), total = SKILLS.reduce((a, s) => a + (s.cost || 0), 0);
  text(`${spent}`, x, y + 1, 9, UIC.gold, 'left', { weight: 600 });
  text('points spent', x + textW(`${spent}`, 9) + 3, y, 5, UIC.muted, 'left', { weight: 400 });
  text(`${pts} free`, x + w, y, 5, pts ? '#ffd070' : UIC.faint, 'right', { weight: 600 });
  y += 5; uiRect(x, y, w, 1.4, '#221c16'); uiRect(x, y, w * Math.min(1, spent / Math.max(1, total)), 1.4, UIC.accent);
  text(`of ${total} in the whole tree`, x + w, y + 6.5, 4.3, UIC.faint, 'right', { weight: 400 });
  y += 15;
  for (const br of brs) {
    const b = stBranch(br), ns = SKILLS.filter(s => s.br === br), tc = ns.reduce((a, s) => a + (s.cost || 0), 0), gc = ns.filter(s => stLearned(s.id)).reduce((a, s) => a + (s.cost || 0), 0);
    text(b.name, x, y + 3, 4.9, gc ? b.color : UIC.faint, 'left', { weight: 600 });
    const bx = x + 34, bw = w - 34 - 17;
    uiRect(bx, y, bw, 2.6, '#221c16'); if (tc && gc) uiRect(bx, y, bw * gc / tc, 2.6, b.color, 0.9);
    text(`${gc}/${tc}`, x + w, y + 3, 4.4, gc ? UIC.muted : UIC.faint, 'right', { weight: 500 });
    y += 7.5;
  }
  const keys = SKILLS.filter(s => s.key);
  y += 3; uiHead('Keystones', x, y + 2, w); y += 10;
  for (const k of keys) {
    const on = stLearned(k.id), c = stBranch(k.br).color;
    uiDiamond(x + 2, y - 1.7, 1.7, on ? c : '#3a3026'); if (!on) uiDiamond(x + 2, y - 1.7, 1.7, '#5a4a30', 1, true);
    text(k.name, x + 7, y, 5, on ? c : UIC.faint, 'left', { weight: on ? 600 : 400 });
    if (on) text('awake', x + w, y, 4.3, UIC.up, 'right', { weight: 500 });
    y += 6.8;
  }
}
function stSummarySheet() {   // the totals, two columns over the dimmed field; ↑↓ / wheel scroll
  const L = stSumLines(), x0 = ST_VP.x + 8, y0 = ST_VP.y + 6, w = ST_VP.w - 16, h = ST_VP.h - 22;
  vctx.fillStyle = 'rgba(6,5,8,0.82)'; vctx.fillRect(ox + ST_VP.x * scale, oy + ST_VP.y * scale, ST_VP.w * scale, ST_VP.h * scale);
  panel(x0, y0, w, h, 0.9);
  text('WHAT YOUR BUILD ADDS UP TO', x0 + w / 2, y0 + 12, 5.4, UIC.gold, 'center', { spacing: 1.2, weight: 600 });
  uiFade(x0 + w / 2 - 70, x0 + 10, y0 + 15, UI_RGB.accent, 0.5); uiFade(x0 + w / 2 + 70, x0 + w - 10, y0 + 15, UI_RGB.accent, 0.5);
  if (!L.length) { text(SAVE.skills.length ? 'Your skills shape every strike.' : 'Learn a skill to begin shaping your build.', x0 + w / 2, y0 + h / 2, 5.6, UIC.faint, 'center', { weight: 400 }); return; }
  const colW = (w - 18) / 2, lh = 7, rows = Math.floor((h - 26) / lh), perPage = rows * 2;
  ST.sumOff = clamp(ST.sumOff || 0, 0, Math.max(0, Math.ceil((L.length - perPage) / 2)));
  const start = ST.sumOff * 2;
  for (let i = 0; i < perPage && start + i < L.length; i++) {
    const q = L[start + i], c = Math.floor(i / rows), r = i % rows, x = x0 + 8 + c * (colW + 4), y = y0 + 25 + r * lh;
    if (q.t !== undefined) {
      const m = /^(.*?)\s([+\-−]\d+(?:\.\d+)?%?)$/.exec(q.t);
      if (m) { text(m[1], x, y, 5, UIC.body, 'left', { weight: 400 }); text(m[2], x + colW - 2, y, 5, m[2][0] === '+' ? UIC.up : '#9fd0e8', 'right', { weight: 600 }); }
      else { uiDiamond(x + 1.2, y - 1.7, 1.1, UIC.accent); text(q.t, x + 5, y, uiFit(q.t, colW - 6, 5, 4, 400), UIC.body, 'left', { weight: 400 }); }
    } else { text(q.l, x, y, 5, UIC.muted, 'left', { weight: 400 }); text(q.v, x + colW - 2, y, 5, UIC.up, 'right', { weight: 600 }); }
  }
  if (L.length > perPage) uiScroll(x0 + w - 4, y0 + 22, h - 28, ST.sumOff, rows, Math.ceil(L.length / 2));
}

// ---- legend + footer
function stLegend(pg) {
  if (pg.gallery || ST.summary) return;
  const labels = ['Learned', 'Available', 'Locked', 'Fork', 'Keystone'], tw = labels.reduce((a, l) => a + 12 + textW(l, 4.2, 500), 0) - 4;
  let x = 172 - tw / 2; const y = 27.5;
  const item = (draw, label) => { draw(x + 3, y - 1.6); text(label, x + 7.5, y, 4.2, UIC.faint, 'left', { weight: 500 }); x += 12 + textW(label, 4.2, 500); };
  item((cx, cy) => { stGlow(cx, cy, 5, UI_RGB.gold, 0.4); stCircle(cx, cy, 2.4, '#f0c870', 0.8, 1, '#3a2c18'); }, 'Learned');
  item((cx, cy) => stCircle(cx, cy, 2.4, '#b08a3a', 0.7, 1, '#140f0c'), 'Available');
  item((cx, cy) => stCircle(cx, cy, 2.4, '#3d3428', 0.7, 1, '#0c0a0e'), 'Locked');
  item((cx, cy) => { uiDiamond(cx, cy, 2.6, '#c0707a', 1, true); }, 'Fork');
  item((cx, cy) => { stCircle(cx, cy, 2.4, '#e6b85c', 0.7, 1, '#140f0c'); for (let i = 0; i < 4; i++) { const a = i * Math.PI / 2 + Math.PI / 4; stLine(cx + Math.cos(a) * 2.6, cy + Math.sin(a) * 2.6, cx + Math.cos(a) * 3.8, cy + Math.sin(a) * 3.8, '#e6b85c', 0.5); } }, 'Keystone');
  // zoom buttons (mouse / touch), bottom-right of the field
  const Z = stZooms(pg); if (Z.length < 2) return;
  [['−', -1], ['+', 1]].forEach(([g2, d], i) => {
    const bx = ST_VP.x + ST_VP.w - 24 + i * 11, by = 191, on = d < 0 ? ST.zi > 0 : ST.zi < Z.length - 1;
    uiRect(bx, by, 9, 9, 'rgba(14,11,12,0.9)'); vctx.strokeStyle = on ? '#8a6d36' : '#3a3026'; vctx.lineWidth = Math.max(1, scale * 0.5);
    vctx.strokeRect(ox + bx * scale + 0.5, oy + by * scale + 0.5, 9 * scale - 1, 9 * scale - 1);
    text(g2, bx + 4.5, by + 7, 7, on ? UIC.gold : '#4a3e2c', 'center', { weight: 600, shadow: false });
    ST.hits.push({ x: bx, y: by, w: 9, h: 9, fn: () => stZoom(d) });
  });
}
function stFooter() {
  const pad = PAD.active, touch = TOUCH_UI && !pad;
  const s = stNode(ST.sel), c = s ? stCan(s) : { ok: false };
  const items = touch ? [['Tap', 'select'], ['Tap', ST.arm ? 'confirm' : 'learn'], ['Drag', 'pan'], ['Esc', 'back']]
    : ST.summary ? [[pad ? 'D-pad' : '↑↓', 'scroll'], [pad ? 'Y' : 'B', 'close'], [kl('Esc'), 'back']]
    : [[pad ? 'D-pad' : '←↑↓→', 'move'], [kl('Enter'), ST.arm ? 'confirm' : 'learn'], [pad ? 'LT/RT' : 'Z', 'zoom'], [pad ? 'Y' : 'B', 'build'],
       ...(stLayout().length > 1 ? [[pad ? 'LB/RB' : kl('Q') ? 'Q/Tab' : 'Tab', 'page']] : []), [kl('Esc'), ST.arm ? 'cancel' : 'back']];
  const parts = items.map(([K, l]) => { const kw = Math.max(7.8, textW(K, 4.8, 600) + 5); return { K, l, kw, w: kw + 2.5 + textW(l, 5, 400) }; });
  const gap = 8, total = parts.reduce((a, p) => a + p.w, 0) + gap * (parts.length - 1); let x = W / 2 - total / 2; const y = 211;
  for (const p of parts) {
    uiKey(p.K, x, y, { size: 4.8 }); text(p.l, x + p.kw + 2.5, y, 5, UIC.faint, 'left', { weight: 400 });
    const act = { move: null, zoom: () => { const n = stZooms(stPage()).length; stZoom(ST.zi >= n - 1 ? -(n - 1) : 1); }, build: () => { ST.summary = !ST.summary; sfx.menu(); }, close: () => { ST.summary = false; sfx.menu(); }, page: () => stSetPage(ST.page + 1),
                  back: () => stInput(menu, 'back'), cancel: () => stInput(menu, 'back'), learn: () => stConfirm(true), confirm: () => stConfirm(true) }[p.l];
    if (act) ST.hits.push({ x, y: y - 7, w: p.w, h: 10, fn: act });
    x += p.w + gap;
  }
}

// ---- debug handles for headless tests (tools/shots/st)
if (typeof window !== 'undefined' && window.__game) window.__game.st = {
  ST, SKILLS, layout: () => stLayout(), get pts() { return stPts(); },
  open(page = 0) { ST.page = page; menu = { screen: 'tree', br: 0, t: 0, prev: { screen: 'shrine', sel: 1, shrine: { name: 'Shrine' } } }; state = 'menu'; stOpen(menu); },
  sel(id) { stSelect(id); }, zoom(d) { stZoom(d); }, page(i) { stSetPage(i); }, input(a) { menuInput(a); }, state: id => stState(stNode(id)), can: id => stCan(stNode(id)),
  pt(x, y) { return { sx: ox + x * scale, sy: oy + y * scale }; }, nodeScreen(id) { const pg = stPage(), p = pg.pos[id]; return p && { x: stSX(p.x), y: stSY(p.y) }; },
  reset() { ST.L = null; ST.sig = ''; }, hasIcon(n, sh = 'sk_icons') { const q = sheet(sh); return q.ok && q.has(n); },
};
