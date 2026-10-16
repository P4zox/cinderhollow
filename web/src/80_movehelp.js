// ------------------------------------------------------------------ MOVEHELP: combo hints (HUD, top right) + the full Move List panel
// (agent `movehelp`, docs/movehelp.md). Reads every type's `combos` list (76_mech_*.js / 78_mech_*.js, + the Fatality row
// from 79_fatality.js) and maps each entry to the MOVE IDS it plays, step by step ("paths"):
//  * auto: the entry's input is parsed ("J J K", "air ↓J", "L → J", "J J (pause) J" ...) and walked through the move
//    rows' `next` routes from the type's neutral moves (T.light[0], T.K, T.air, T.down, T.up, T.rollJ, T.counter);
//  * MH_MAP[type][entry name] overrides it where the input names a state or a custom handler decides ("Iai → J",
//    "Demon: K", "hold K", "block → K" ...): 'KEY=node KEY=node ...' (see mhSpec). null = not a move (a passive / rule).
// Nodes are move ids (ATK) or pseudo nodes: @roll (in / just out of the dodge), @guard (blocking), @parry (the parry
// stance), @counter (a parry / block just landed: the counter window), @plunge (the falling slam), @air / @root.
// The HUD asks "where am I now" (mhNodes) and lists the next step of every path passing through that node, plus the
// node's own `next` routes; ranks gate both. The panel draws the entries grouped, with key glyphs, numbers from the
// final move row and a looping preview of the path's animation tags (player sheet + weapon overlay).
const MH = { built: {}, nodes: [], show: [], alpha: 0, live: -9, press: -9, ctxT: -9, ctxSig: '', last: null, head: '', test: null };
if (SETTINGS.combohint === undefined) SETTINGS.combohint = 1;
const MH_KEYS = { J: 'attack', K: 'heavy', I: 'parry', L: 'roll', '↑': 'up', '↓': 'down' };
// contexts: a ctx entry's first step only counts while its context holds (and the root list shows after it changes)
const MH_CTX = {
  sheathed: () => !!P.sheathed, drawn: () => !P.sheathed,
  demon: () => !!P.demon, arch: () => !!P.arch,
  swift: () => !(typeof ftIron === 'function' && ftIron()), iron: () => !!(typeof ftIron === 'function' && ftIron()),
  axe: () => !!P.sxAxe, blade: () => !P.sxAxe,
};
const MH_CTX_OF = { Swift: 'swift', Iron: 'iron', Axe: 'axe', Demon: 'demon', Archdemon: 'arch' };
const MH_TYPE_CTX = { katana: ['sheathed'], dual: ['demon', 'arch'], fist: ['iron'], saxe: ['axe'] };   // the "non-default" contexts per type

// ================================================================== parsing an input string into steps
// a step: { b: 'J'|'K'|'I'|'L', air, up, down, hold, pause, late, tap, ann: [...] }; returns null when a word isn't understood
function mhParse(s) {
  const out = [], words = String(s).replace(/→/g, ' ').replace(/\s+/g, ' ').trim().split(' ');
  let mod = {};
  for (let i = 0; i < words.length; i++) {
    const w = words[i]; if (!w) continue;
    if (w === 'hold') { mod.hold = true; continue; }
    if (w === 'air') { mod.air = true; continue; }
    if (w === '(pause)' || w === '(beat)') { mod.pause = true; continue; }
    const m = /^(·)?(↑|↓)?([JKIL])$/.exec(w);
    if (m) { out.push({ b: m[3], ...mod, up: m[2] === '↑', down: m[2] === '↓', late: !!m[1], ann: [] }); mod = {}; continue; }
    const r = /^×(\d)$/.exec(w);
    if (r && out.length) { const p = out[out.length - 1]; for (let k = 1; k < +r[1]; k++) out.push({ ...p, ann: [] }); continue; }
    if (out.length && /^\(/.test(w)) {   // "(sheathed)", "(tap)", "(parry)", "(on the flash)" ... annotate the step before
      let a = w; while (!/\)$/.test(a) && i + 1 < words.length) a += ' ' + words[++i];
      out[out.length - 1].ann.push(a.replace(/[()]/g, '')); continue;
    }
    if (out.length && w === 'forward') { out[out.length - 1].ann.push('forward'); continue; }
    return null;
  }
  return out.length ? out : null;
}
// the glyph parts a step is drawn with: ['hold', 'K'], ['air', '↓', 'J'], ['pause', 'J'] (words are small text, keys boxed)
function mhParts(st) {
  const p = [];
  if (st.pause) p.push('pause');
  if (st.air) p.push('air');
  if (st.hold) p.push('hold');
  if (st.up) p.push('↑'); if (st.down) p.push('↓');
  p.push(st.b);
  if (st.late) p.push('late');
  if (st.tap) p.push('tap');
  return p;
}
// a key token of MH_MAP: 'hold.K', 'air.↓J', 'pause.J', '↑J', 'late.J', 'K' (+ '+' joins two keys pressed together: 'I+J')
function mhTok(tok) {
  const p = []; for (const w of tok.split('.')) { if (/^[↑↓][JKIL]$/.test(w)) p.push(w[0], w[1]); else if (/^[JKIL](\+[JKIL])+$/.test(w)) w.split('+').forEach((k, i) => { if (i) p.push('+'); p.push(k); }); else p.push(w); }
  return p;
}

// ================================================================== auto: walk an entry's steps through the move rows
function mhRoute(id, b, o = {}) {
  const A = ATK[id]; if (!A || !A.mv) return null;
  const r = A.mv.next && A.mv.next[b];
  let nx = null;
  try { nx = typeof r === 'function' ? r({ b, t: A.mv.total - 1, at: P ? P.clk || 0 : 0, peek: true, after: o.pause ? 200 : undefined }, A) : r; } catch (e) { nx = null; }
  if (nx && typeof nx === 'object') nx = nx.id;
  return typeof nx === 'string' ? nx : null;
}
function mhRootMove(T, st) {
  if (st.air) { if (st.b === 'J') return st.down ? T.down : T.air; if (st.b === 'K' && !T.onAirK) return '@plunge'; return null; }
  if (st.b === 'J' && st.up) return T.up || null;
  if (st.b === 'J' && !st.hold) return T.light[0];   // (a type's onJ only takes the J J (pause) J / special presses)
  if (st.b === 'K' && !st.hold && !T.onK) return T.K;
  if (st.b === 'L') return '@roll';
  if (st.b === 'I' && !T.onI) return st.ann.includes('parry') || !st.ann.length ? '@parry' : null;
  return null;
}
function mhAuto(type, steps, ctx) {
  const T = MV.types[type]; if (!T || !steps) return null;
  const nodes = []; let cur = null;
  for (const st of steps) {
    if (st.ann.some(a => !['parry', 'tap', 'timed'].includes(a)) || st.late || st.tap) return null;
    let nx = null;
    if (cur === null) nx = ctx && (T.light0 || T.onK) && !st.air ? null : mhRootMove(T, st);
    else if (cur === '@roll') {
      if (st.b === 'J' && !st.hold) { let r = T.rollJ; try { if (typeof r === 'function') r = r({ kind: (typeof T.dodge === 'object' && T.dodge && T.dodge.kind) || 'roll', perfect: false, t: 200, total: 400 }); } catch (e) { r = null; } nx = r && typeof r === 'object' ? r.id : r; }
    } else if (cur === '@parry') { if (st.b === 'J') { try { nx = T.counter ? T.counter() : null; } catch (e) { nx = null; } } }
    else if (cur[0] !== '@') {
      if (st.hold) return null;
      nx = mhRoute(cur, st.b, st);
      if (st.pause && nx === mhRoute(cur, st.b)) return null;   // the pause must change the route, else a handler decides
      if (nx === '@J') nx = steps[0].air ? null : T.light[0];   // (a route that reads P.ground can't be walked from here)
      else if (nx === '@K') nx = T.onK ? null : T.K;
      else if (nx && nx[0] === '@') nx = null;
    }
    if (!nx || (nx[0] !== '@' && !ATK[nx])) return null;
    nodes.push(nx); cur = nx;
  }
  return nodes;
}

// ================================================================== build the paths of a type
// MH_MAP spec: 'KEY=node KEY=node' (KEY: J K I L ↑J ↓J hold.K air.J pause.J late.J tap.I ...; '>node' starts the path at
// a node without a key, e.g. '>kt_iai J=kt_tsubame'); { p, ctx, alt } objects; arrays = alternatives; null = no move.
function mhSpec(type, e, spec) {
  const alts = Array.isArray(spec) ? spec : [spec], out = [];
  for (const sp of alts) {
    const o = typeof sp === 'string' ? { p: sp } : sp; if (!o || !o.p) continue;
    const steps = []; let from = null;
    for (const tok of o.p.trim().split(/\s+/)) {
      if (tok[0] === '>') { from = tok.slice(1); continue; }
      const i = tok.lastIndexOf('='), k = tok.slice(0, i), n = tok.slice(i + 1);
      steps.push({ parts: mhTok(k), node: n });
    }
    out.push({ e, type, from, steps, ctx: o.ctx || null, name: o.name || null, stepNames: o.names && o.names.length === steps.length ? o.names : null, src: 'map' });
  }
  return out;
}
function mhBuild(type) {
  if (MH.built[type]) return MH.built[type];
  const T = MV.types[type]; if (!T) return null;
  const map = MH_MAP[type] || {}, paths = [], unres = [], rows = [];
  for (const e of T.combos || []) {
    const row = { e, paths: [], none: false };
    if (e.fatality) { row.fatal = true; rows.push(row); continue; }
    if (Object.prototype.hasOwnProperty.call(map, e.name)) {
      const spec = map[e.name];
      if (spec === null) row.none = true; else row.paths = mhSpec(type, e, spec);
    } else {
      // "a  /  b": alternatives (names "A  /  B" split alike when they match up)
      const ins = e.input.split(/\s{2}\/\s{2}/), nms = e.name.split(/\s+\/\s+/);
      for (let a = 0; a < ins.length; a++) {
        let s = ins[a].trim(), ctx = null;
        const cm = /^(Swift|Iron|Axe|Demon|Archdemon):\s*/.exec(s); if (cm) { ctx = MH_CTX_OF[cm[1]]; s = s.slice(cm[0].length); }
        const st = mhParse(s), nodes = mhAuto(type, st, ctx);
        if (!nodes) continue;
        row.paths.push({ e, type, from: null, ctx, name: ins.length === nms.length ? nms[a] : null, steps: st.map((x, i) => ({ parts: mhParts(x), node: nodes[i] })), src: 'auto' });
      }
      if (!row.paths.length) unres.push(e.name);
    }
    // multi-name entries ("Strike · Butt strike · Low sweep · Overhead"): one name per step
    const nm = e.name.split(' · ');
    for (const p of row.paths) if (!p.stepNames && nm.length > 1 && nm.length === p.steps.length) p.stepNames = nm;
    paths.push(...row.paths); rows.push(row);
  }
  // the name of a move id: the entry whose path ends there (shortest first), else the entry it's a step of
  const names = {};
  const sorted = paths.slice().sort((a, b) => a.steps.length - b.steps.length);
  for (const p of sorted) { const L = p.steps[p.steps.length - 1]; if (L.node[0] !== '@' && !names[L.node]) names[L.node] = { name: p.stepNames ? p.stepNames[p.steps.length - 1] : p.name || p.e.name, rank: p.e.rank || 1 }; }
  // (a middle step: the first entry in the Move List's own order that passes through it -- the designers list the main chain first)
  for (const p of paths) p.steps.forEach((s, i) => { if (s.node[0] !== '@' && !names[s.node]) names[s.node] = { name: p.stepNames ? p.stepNames[i] : p.name || p.e.name, step: p.stepNames ? 0 : i + 1, of: p.steps.length, rank: p.e.rank || 1 }; });
  return (MH.built[type] = { type, paths, rows, names, unres });
}
function mhReset() { MH.built = {}; }
HOOKS.enter.push(() => { for (const t of Object.keys(MH.built)) { const B = MH.built[t]; if (B.rows.length !== (MV.types[t].combos || []).length) delete MH.built[t]; } });

// ================================================================== the override table
const MH_MAP = {};

// ================================================================== where the player is now, and what comes next
function mhIsMove(id) { return !!(id && ATK[id] && ATK[id].mv); }
function mhNodes() {
  const n = [], s = P.state, clk = P.clk || 0;
  if (s) n.push(s);
  if (s === 'roll' || (P.dgEnd && clk - P.dgEnd.t < 0.25)) n.push('@roll');
  if (s === 'parry' || P.gcT > 0) n.push('@parry');
  if (P.gcT > 0) n.push('@counter');
  if (s === 'guard' || s === 'block') n.push('@guard');
  if (s === 'plunge') n.push('@plunge');
  if (!mhIsMove(s) && P.mvChain && clk - P.mvChain.t < 0.3) n.push(P.mvChain.id);   // a press now still continues the chain
  return n;
}
function mhCtxOk(c) { if (!c) return true; const f = MH_CTX[c]; try { return f ? !!f() : true; } catch (e) { return true; } }
function mhRankOk(id, rank) { const A = ATK[id]; return !(A && A.mv && A.mv.rank && A.mv.rank > rank); }
// the order hints are listed in: J, K, I, L; a plain press before its held / timed variants
function mhOrd(parts) { const k = parts.filter(p => /^[JKIL]$/.test(p)); const b = k.length ? 'JKIL'.indexOf(k[k.length - 1]) : 4; return b * 10 + (parts.length > 1 ? 1 + parts.length : 0); }
// the hint list at the current moment: [{ parts, name, sub, dest, fin }]; o.nodes / o.type / o.root to ask about any spot
function mhCands(o = {}) {
  const type = o.type || mvType(), B = mhBuild(type); if (!B) return [];
  const rank = o.rank || mvRank(type), nodes = o.nodes || mhNodes(), out = new Map();
  const add = c => { const k = c.parts.join('.'); const was = out.get(k); if (!was || (c.fin && !was.fin && was.dest === c.dest)) out.set(k, c); };
  const nameOf = (p, i) => (p.stepNames ? p.stepNames[i] : p.name || p.e.name);
  const lab = (p, i) => {   // the final step of a path: its own name; a middle step: the name its move is known by
    const fin = i === p.steps.length - 1 || !!(p.steps[i + 1] && p.steps[i + 1].parts.includes('release')), d = p.steps[i].node, N = B.names[d];   // a hold before its release reads as the move
    if (fin || p.stepNames || !N) return { name: nameOf(p, i), fin, sub: fin || p.stepNames ? '' : `${i + 1}/${p.steps.length}` };
    return { name: N.name, fin: !N.step, sub: N.step ? `${N.step}/${N.of}` : '' };
  };
  for (const node of nodes) {
    for (const p of B.paths) {
      if ((p.e.rank || 1) > rank) continue;
      const idx = [];
      if (p.from === node) idx.push(-1);
      p.steps.forEach((st, i) => { if (st.node === node && i < p.steps.length - 1) idx.push(i); });
      for (const i of idx) {
        if (p.ctx && (i === -1 || !mhIsMove(node)) && !mhCtxOk(p.ctx)) continue;   // a context only gates the start
        const nx = p.steps[i + 1]; if (!nx || !mhRankOk(nx.node, rank)) continue;
        add({ parts: nx.parts, dest: nx.node, ...lab(p, i + 1), e: p.e });
      }
    }
    if (mhIsMove(node)) for (const b of ['J', 'K', 'I']) {   // the move row's own routes (what the engine will really do)
      const d = mhRoute(node, b);
      if (!d || d[0] === '@' || !mhIsMove(d) || !mhRankOk(d, rank) || out.has(b)) continue;
      const N = B.names[d]; if (!N) continue;
      add({ parts: [b], dest: d, name: N.name, fin: !N.step, sub: N.step ? `${N.step}/${N.of}` : '' });
    }
  }
  // free (no chain running): in the air, the air moves; just after a stance / mode change, that context's moves
  if (o.root || (!out.size && !o.noRoot)) {
    const air = o.air !== undefined ? o.air : !P.ground, ctxFresh = o.root || (P.clk || 0) - MH.ctxT < 1.6;
    for (const p of B.paths) {
      if ((p.e.rank || 1) > rank || p.from) continue;
      const st = p.steps[0], isAir = st.parts.includes('air');
      if (air ? !isAir : (isAir || !p.ctx || !ctxFresh || !(MH_TYPE_CTX[type] || []).includes(p.ctx))) continue;
      if (!mhCtxOk(p.ctx) || !mhRankOk(st.node, rank)) continue;
      const L0 = lab(p, 0); if (p.ctx && !L0.fin && !p.stepNames) { L0.name = p.name || p.e.name; L0.sub = ''; }   // a context's own chain by its own name (Demon chain)
      add({ parts: st.parts, dest: st.node, ...L0, e: p.e });
    }
  }
  return [...out.values()].sort((a, b) => mhOrd(a.parts) - mhOrd(b.parts)).slice(0, o.max || 5);
}
// the heading over the list: where you are
const MH_PSEUDO = { '@roll': 'Dodge', '@parry': 'Parry', '@counter': 'Counter', '@guard': 'Guard', '@plunge': 'Plunge' };
const MH_CTX_NAME = { sheathed: 'Sheathed', demon: 'Demon Mode', arch: 'Archdemon', iron: 'Iron style', swift: 'Swift style', axe: 'Axe mode', blade: 'Blade mode' };
function mhHead(type) {
  const B = mhBuild(type), nodes = mhNodes();
  for (const n of nodes) { if (mhIsMove(n) && B.names[n]) { const N = B.names[n]; return N.name + (N.step ? `  ${N.step}/${N.of}` : ''); } if (MH_PSEUDO[n]) return MH_PSEUDO[n]; }
  if (!P.ground) return 'Airborne';
  for (const c of MH_TYPE_CTX[type] || []) if (mhCtxOk(c)) return MH_CTX_NAME[c] || c;
  return '';
}
function mhSig(type) { return (MH_TYPE_CTX[type] || []).map(c => (mhCtxOk(c) ? 1 : 0)).join(''); }
function mhFatal() { try { return typeof fatReady === 'function' && fatReady(); } catch (e) { return false; } }

// ================================================================== the HUD: state per frame (update) + drawing (hud)
function mhHidden() {
  return !SETTINGS.combohint || typeof state === 'undefined' || state !== 'play' || !P || !D || P.state === 'dead'
    || (typeof FAT !== 'undefined' && FAT.on);
}
function mhTick(dt) {
  if (mhHidden()) { MH.alpha = Math.max(0, MH.alpha - dt * 6); if (!SETTINGS.combohint) MH.show = []; return; }
  const type = mvType(), clk = P.clk || 0, sig = type + ':' + mhSig(type);
  if (sig !== MH.ctxSig) { if (MH.ctxSig && MH.ctxSig.split(':')[0] === type) MH.ctxT = clk; MH.ctxSig = sig; }
  let c = [], head = '';
  if (mhFatal()) {
    let nm = 'Last Rite'; try { nm = fatDef(type).name; } catch (e) {}
    c = [{ parts: ['K'], name: 'Fatality: ' + nm, fin: true, fatal: true }, { parts: ['J'], name: 'Riposte', fin: true }]; head = 'Staggered';
  } else if (clk - MH.press < 3) { c = mhCands(); head = mhHead(type); }
  const busy = mhIsMove(P.state) || ['roll', 'parry', 'guard', 'block', 'plunge'].includes(P.state) || P.gcT > 0 || (P.mvChain && clk - P.mvChain.t < 0.3) || !P.ground || clk - MH.ctxT < 1.6;
  if (c.length && (busy || c[0].fatal)) {
    const key = c.map(x => x.parts.join('.') + x.name).join('|');
    if (key !== MH.key) { MH.key = key; MH.t0 = clk; }
    MH.show = c; MH.head = head; MH.live = clk; MH.fatal = !!c[0].fatal;
  }
  const want = MH.show.length && clk - MH.live < (MH.fatal ? 0.2 : 1.2) ? 1 : 0;
  MH.alpha = want ? Math.min(1, MH.alpha + dt * 8) : Math.max(0, MH.alpha - dt * 3);
  if (!MH.alpha && !want) { MH.show = []; MH.key = ''; }
}
HOOKS.update.push(dt => { try { mhTick(dt); } catch (e) { MH.err = String(e); } });
HOOKS.enter.push(() => { MH.show = []; MH.alpha = 0; MH.key = ''; });
{ const _ph = onPressHook; onPressHook = (a, repeat) => { if (!repeat && ['attack', 'heavy', 'parry', 'roll', 'jump'].includes(a) && P) MH.press = P.clk || 0; return _ph(a, repeat); }; }

// a key cap (boxed) with its own alpha; returns its width. label = the bound key's name
function mhKeyCap(label, x, y, sz, a, o = {}) {
  const w = Math.max(sz + 2.6, textW(label, sz, 700) + 4.2), h = sz + 2.4, X = ox + x * scale, Y = oy + (y - sz * 0.92 - 1) * scale;
  vctx.globalAlpha = a;
  vctx.fillStyle = o.hot ? 'rgba(70,46,18,0.95)' : 'rgba(26,20,16,0.92)'; vctx.fillRect(X, Y, w * scale, h * scale);
  vctx.fillStyle = 'rgba(255,230,170,0.10)'; vctx.fillRect(X, Y, w * scale, Math.max(1, scale * 0.6));   // top bevel
  vctx.strokeStyle = o.dim ? '#4a3e2c' : o.hot ? '#ffd27a' : '#9a7a3e'; vctx.lineWidth = Math.max(1, scale * 0.5);
  vctx.strokeRect(X + 0.5, Y + 0.5, w * scale - 1, h * scale - 1);
  vctx.globalAlpha = 1;
  text(label, x + w / 2, y + 0.1, sz, o.dim ? UIC.faint : o.hot ? '#fff0c8' : UIC.gold, 'center', { shadow: false, weight: 700, alpha: a });
  return w;
}
function mhKeyName(k) {
  if (!MH_KEYS[k]) return k;
  try { const b = keysOf(MH_KEYS[k])[0]; return b || k; } catch (e) { return k; }
}
const MH_WORD = { pause: '(pause)', late: 'late', hold: 'hold', air: 'air', tap: 'tap', release: 'release', perfect: 'perfect', moving: 'moving', still: 'still' };
// a key sequence (parts) drawn left to right from x; returns the width (measure only when o.measure)
function mhGlyphs(parts, x, y, sz, a, o = {}) {
  let w = 0;
  for (const p of parts) {
    if (p === '+') { if (!o.measure) text('+', x + w + 0.6, y, sz * 0.9, UIC.faint, 'left', { weight: 500, shadow: false, alpha: a }); w += textW('+', sz * 0.9, 500) + 1.4; continue; }
    if (/^[JKIL↑↓]$/.test(p)) {
      const lab = mhKeyName(p);
      if (o.measure) w += Math.max(sz + 2.6, textW(lab, sz, 700) + 4.2) + 1.2;
      else w += mhKeyCap(lab, x + w, y, sz, a, o) + 1.2;
      continue;
    }
    const s = MH_WORD[p] || p, fs = sz * 0.82;
    if (!o.measure) text(s, x + w, y - 0.2, fs, o.wordCol || UIC.muted, 'left', { weight: 500, shadow: false, alpha: a });
    w += textW(s, fs, 500) + 1.6;
  }
  return Math.max(0, w - 1.2);
}
function mhHud() {
  if (MH.alpha <= 0.01 || !MH.show.length || mhHidden()) return;
  if ((typeof areaCard !== 'undefined' && areaCard) || (typeof regionCard !== 'undefined' && regionCard && regionCard.t > 0 && regionCard.t < 4)) return;
  const a = MH.alpha, L = MH.show, sz = 4.4, rh = 8.2, x1 = W - 8, clk = P.clk || 0;
  let y0 = SAVE.remnant ? 44 : 34;   // under the cinders (and the lost-cinders line)
  if (typeof bannerMsg !== 'undefined' && bannerMsg) { try { y0 = Math.max(y0, 30 + 26 + wrap(bannerMsg.desc, 200, 6.5).length * 9 + 8); } catch (e) {} }   // under a pickup banner
  const gw = Math.max(...L.map(c => mhGlyphs(c.parts, 0, 0, sz, 1, { measure: true }))), nw = Math.max(...L.map(c => textW(c.name, 4.8, 600) + (c.sub ? textW(c.sub, 3.8, 500) + 3 : 0)));
  const hw = MH.head ? textW(MH.head.toUpperCase(), 3.8, 600) + MH.head.length * 0.7 : 0;
  const bw = Math.max(gw + nw + 12, hw + 10), x0 = x1 - bw, hh = MH.head ? 7 : 2, bh = hh + L.length * rh + 3;
  // the plate: dark, fading out to the left; a gold hairline over it
  const X0 = ox + (x0 - 14) * scale, X1 = ox + (x1 + 3) * scale, g = vctx.createLinearGradient(X0, 0, X1, 0);
  g.addColorStop(0, 'rgba(6,4,9,0)'); g.addColorStop(0.2, `rgba(6,4,9,${0.72 * a})`); g.addColorStop(1, `rgba(6,4,9,${0.86 * a})`);
  vctx.fillStyle = g; vctx.fillRect(X0, oy + (y0 - 5) * scale, X1 - X0, (bh + 5) * scale);
  uiFade(x1 + 3, x0 - 8, y0 - 5, MH.fatal ? '255,120,90' : UI_RGB.gold, 0.75 * a);
  uiDiamond(x1 + 3, y0 - 4.8, 1.2, MH.fatal ? '#ff8a6a' : UIC.gold, a);
  if (MH.head) text(MH.head.toUpperCase(), x1, y0 + 0.6, 3.8, MH.fatal ? '#ff9a7a' : UIC.dim, 'right', { weight: 600, spacing: 0.7, alpha: a });
  L.forEach((c, i) => {
    const k = clamp((clk - MH.t0) * 16 - i * 0.45, 0, 1), y = y0 + hh + 4.6 + i * rh, dx = (1 - k) * 5, aa = a * k;
    if (aa <= 0.01) return;
    const hot = !!c.fatal;
    if (hot) { const p = 0.5 + 0.5 * Math.sin(clk * 7); vctx.fillStyle = `rgba(255,110,70,${(0.10 + 0.08 * p) * aa})`; vctx.fillRect(ox + (x0 - 2) * scale, oy + (y - 6) * scale, (bw + 4) * scale, rh * scale); }
    const cw = mhGlyphs(c.parts, 0, 0, sz, 1, { measure: true });
    mhGlyphs(c.parts, x0 + 2 + gw - cw + dx, y, sz, aa, { hot });   // keys right-aligned against the names
    const nx = x0 + 5 + gw + dx;
    text(c.name, nx, y, 4.8, hot ? '#ffd8b0' : c.fin ? UIC.hi : UIC.text, 'left', { weight: 600, alpha: aa });
    if (c.sub) text(c.sub, nx + textW(c.name, 4.8, 600) + 3, y, 3.8, UIC.faint, 'left', { weight: 500, alpha: aa });
  });
}
HOOKS.hud.push(() => { try { mhHud(); } catch (e) { MH.err = String(e); } });

// ================================================================== Settings › Combo hints (On / Off, default On; saved with the settings)
// (just above "Save & quit": the rows before it keep their indices -- tools/shots/keys_test.js walks to Cheats by index)
{ const q = SETTING_ROWS.findIndex(r => r.k === 'quit'); if (!SETTING_ROWS.some(r => r.k === 'combohint')) SETTING_ROWS.splice(q < 0 ? SETTING_ROWS.length : q, 0, { k: 'combohint', label: 'Combo hints', toggle: true }); }

// ================================================================== the Move List panel (Esc › Equipment › Weapon › Mastery › Enter)
const MH_GROUPS = ['Light combos', 'Heavy & charge', 'Special (I) / stance', 'Dodge (L) follow-ups', 'Air', 'Mastery moves', 'Fatality'];
const MH_GROUP_SUB = { 'Light combos': 'J', 'Heavy & charge': 'K', 'Special (I) / stance': 'I', 'Dodge (L) follow-ups': 'L', Air: 'air', 'Mastery moves': 'II–V', Fatality: 'K' };
function mhGroupOf(e, row) {
  if (e.fatality) return 'Fatality';
  if ((+e.rank || 1) > 1) return 'Mastery moves';
  let s = String(e.input || '').replace(/^(Swift|Iron|Axe|Demon|Archdemon):\s*/, '');
  const p = row && row.paths[0], st0 = p && !p.from && p.steps[0];
  if (/^air\b/.test(s) || (st0 && st0.parts.includes('air'))) return 'Air';
  if (/^(L|perfect)\b|dodge|demon dash/.test(s) || (st0 && st0.node === '@roll')) return 'Dodge (L) follow-ups';
  if (/sheathed|Iai|block|parry|guard|brace|grapple|vault|Perform|notes|Ash|Ember|Gold|Shift|gauge|style|mid-combo/i.test(s) || /^(hold )?I\b/.test(s)) return 'Special (I) / stance';
  if (/^(hold K|release K|K\b|charged|strong|spin|double smash|lv3)/.test(s)) return 'Heavy & charge';
  if (/^(J|↑J|hold J|press)\b/.test(s) || /^↑J/.test(s)) return /^J (→ )?K\b|^J J (→ )?K\b/.test(s) && !/K.*J/.test(s) && false ? 'Heavy & charge' : 'Light combos';
  return 'Special (I) / stance';
}
// the type's list: [{ e, row, group, i }] in group order (entries keep their own order inside a group), + display lines
function mhList(type) {
  const B = mhBuild(type); if (!B) return { items: [], lines: [] };
  if (B.list) return B.list;
  const items = B.rows.map((row, i) => ({ e: row.e, row, group: mhGroupOf(row.e, row), i }));
  items.sort((a, b) => MH_GROUPS.indexOf(a.group) - MH_GROUPS.indexOf(b.group) || a.i - b.i);
  const lines = []; let g = null;
  items.forEach((it, k) => { if (it.group !== g) { g = it.group; lines.push({ head: g, n: items.filter(x => x.group === g).length }); } it.k = k; it.line = lines.length; lines.push({ it }); });
  return (B.list = { items, lines });
}
// an input string as glyph parts ("J J (pause) J" -> J J pause J, "Iai → J" -> Iai → J): keys boxed, words small
function mhInputParts(s) {
  const out = [];
  let str = String(s || '').replace(/\s{2}\/\s{2}/g, ' / ');
  const cm = /^(Swift|Iron|Axe|Demon|Archdemon):\s*/.exec(str); if (cm) str = str.slice(cm[0].length);
  for (let w of str.split(' ')) {
    if (!w) continue;
    const m = /^(·)?([↑↓])?([JKIL])$/.exec(w);
    if (m) { if (m[1]) out.push('late'); if (m[2]) out.push(m[2]); out.push(m[3]); continue; }
    if (w === '→') { out.push('→'); continue; }
    out.push(w.replace(/[()]/g, ''));
  }
  return { parts: out, ctx: cm ? cm[1] : null };
}
// glyph parts that also draw arrows / words; fits into maxW by shrinking (returns the width used)
function mhInputDraw(s, xr, y, maxW, a, o = {}) {
  const { parts, ctx } = mhInputParts(s);
  let sz = o.size || 4.4; const fit = () => mhGlyphs(parts, 0, 0, sz, 1, { measure: true }) + (ctx ? textW(ctx.toUpperCase(), 3.4, 700) + 4.5 : 0);
  while (sz > 3.3 && fit() > maxW) sz -= 0.2;
  const w = fit(); let x = o.align === 'left' ? xr : xr - w;
  if (ctx) { const cw = textW(ctx.toUpperCase(), 3.4, 700) + 3; uiRect(x, y - 3.9, cw, 4.9, 'rgba(120,60,40,0.45)'); text(ctx.toUpperCase(), x + cw / 2, y - 0.2, 3.4, '#f0b090', 'center', { weight: 700, shadow: false, alpha: a }); x += cw + 1.5; }
  mhGlyphs(parts, x, y, sz, a, { dim: o.dim, wordCol: o.dim ? UIC.faint : UIC.muted });
  return w;
}
// the final move of an entry (for the numbers and the preview): its first path's last real move
function mhEntryMoves(row) { const p = row && row.paths[0]; return p ? p.steps.map(s => s.node) : []; }
function mhFinal(row) { const ns = mhEntryMoves(row).filter(n => mhIsMove(n)); return ns[ns.length - 1] || null; }
function mhNumbers(id) {
  const d = MV.defs[id]; if (!d) return null;
  const r = n => Math.round(n * 100) / 100, out = [];
  if (d.noHit && !d.dmg) out.push(['DMG', '—']);
  else if (d.hits) { const all = d.hits.every(h => h === d.hits[0]); out.push(['DMG', all ? `${d.hits.length}×${r(d.hits[0])}` : `${r(d.hits.reduce((a, b) => a + b, 0))} (${d.hits.length} hits)`]); }
  else out.push(['DMG', (d.n > 1 ? `${d.n}×` : '') + r(d.dmg || 0)]);
  out.push(['POISE', String(Math.round(d.poise || 0))]);
  out.push(['STAM', typeof d.stam === 'number' ? String(Math.round(d.stam)) : 'varies']);
  if (d.wind < 1e8 && d.total < 1e8) out.push(['HIT AT', (d.wind / 1000).toFixed(2) + ' s'], ['RECOVER', (d.total / 1000).toFixed(2) + ' s']);
  else out.push(['HOLD', 'release']);
  return out;
}
// the animation tags of a path, in order (moves: their resolved tag; dodges, guards ... their poses)
function mhPoseTag(type, n) {
  const sh = pSheet(), T = MV.types[type] || {};
  if (mhIsMove(n)) { try { const t = mvResolve(ATK[n]).tag; return sh.has(t) ? t : null; } catch (e) { return null; } }
  const pick = l => l.find(t => sh.has(t)) || null;
  if (n === '@roll') { const dg = typeof T.dodge === 'function' ? (() => { try { return T.dodge(0); } catch (e) { return null; } })() : T.dodge; return pick([...((dg && dg.tags) || []), 'roll']); }
  if (n === '@guard') return pick(['sh_guard', 'gs_guard', 'sp_guard', 'guard', 'parry']);
  if (n === '@parry' || n === '@counter') return pick(['parry']);
  if (n === '@plunge') return pick(['plunge']);
  const al = { spdive: ['sp_jump'], vault: ['st_vault', 'double_jump'], brace: ['ml_brace', 'sh_guard'], grapple: ['wh_grapple', 'wh_1'] }[n];
  return al ? pick(al) : sh.has(n) ? n : null;
}
function mhPreviewSeq(type, row) {
  const p = row && row.paths[0], seq = [];
  if (p) {
    if (p.from) { const t = mhPoseTag(type, p.from); if (t) seq.push({ tag: t, air: false, k: -1 }); }
    p.steps.forEach((st, k) => { const t = mhPoseTag(type, st.node); if (t) seq.push({ tag: t, air: st.parts.includes('air') || (k > 0 && seq.length && seq[seq.length - 1].air && !MV.defs[st.node]?.down && !!(MV.defs[st.node] && (MV.defs[st.node].air || MV.defs[st.node].airCount))), k, loop: !!(MV.defs[st.node] && MV.defs[st.node].loop) }); });
  }
  if (row && row.fatal) { const T = MV.types[type] || {}; let c = null; try { c = T.counter ? T.counter() : null; } catch (e) {} const ids = [c, T.K].filter(x => mhIsMove(x)); for (const id of ids) { const t = mhPoseTag(type, id); if (t) seq.push({ tag: t, k: 0 }); } }
  return seq;
}
// the stage: a looping preview of the path (idle, each step's tag at its own speed, a held last frame)
function mhStage(type, row, x, y, w, h, t0) {
  const ps = sheet('player'), ws = sheet('wpn_' + WTYPE_INFO[type].weapon);
  // backdrop: a dark vault with a warm floor glow
  const X = ox + x * scale, Y = oy + y * scale, g = vctx.createLinearGradient(0, Y, 0, Y + h * scale);
  g.addColorStop(0, 'rgba(14,10,16,0.95)'); g.addColorStop(0.75, 'rgba(24,17,14,0.95)'); g.addColorStop(1, 'rgba(10,8,10,0.95)');
  vctx.fillStyle = g; vctx.fillRect(X, Y, w * scale, h * scale);
  const fy = y + h - 9, cx = x + w / 2 - 6;
  const R = vctx.createRadialGradient(ox + cx * scale, oy + fy * scale, 0, ox + cx * scale, oy + fy * scale, 54 * scale);
  R.addColorStop(0, 'rgba(230,170,90,0.20)'); R.addColorStop(1, 'rgba(230,170,90,0)'); vctx.fillStyle = R; vctx.fillRect(X, Y, w * scale, h * scale);
  uiFade(cx, x + 4, fy, UI_RGB.accent, 0.6); uiFade(cx, x + w - 4, fy, UI_RGB.accent, 0.6);
  vctx.strokeStyle = 'rgba(176,138,58,0.45)'; vctx.lineWidth = Math.max(1, scale * 0.5); vctx.strokeRect(X + 0.5, Y + 0.5, w * scale - 1, h * scale - 1);
  if (!ps.ok) { wmIcon(type, cx - 12, fy - 28, 24); return null; }
  const seq = mhPreviewSeq(type, row), idleMs = 520, segs = [];
  let tot = idleMs;
  for (const s of seq) { const d = Math.max(140, s.loop ? 720 : wmTagMs(ps, s.tag)); segs.push({ ...s, a: tot, d }); tot += d; }
  tot += seq.length ? 420 : 900;
  const ms = ((time - t0) * 1000) % tot;
  let f = null, lift = 0, cur = -1;
  if (ms < idleMs || !segs.length) f = wmFrameAt(ps, 'idle', (ms % wmTagMs(ps, 'idle')));
  else {
    const sg = segs.find(s => ms >= s.a && ms < s.a + s.d) || segs[segs.length - 1];
    const tm = Math.min(ms - sg.a, sg.d - 1);
    f = wmFrameAt(ps, sg.tag, sg.loop ? tm % wmTagMs(ps, sg.tag) : tm); cur = sg.k;
    if (ms >= sg.a + sg.d) f = ps.tag(sg.tag).to;
    if (sg.air) lift = 16;
  }
  const k = 1.5, by = fy - lift;
  vctx.save(); vctx.beginPath(); vctx.rect(X + 1, Y + 1, w * scale - 2, h * scale - 2); vctx.clip();
  uiRect(cx - 9 * k + lift * 0.2, fy - 0.6, 18 * k - lift * 0.4, 1.2, '#000', 0.35);
  const fa = row && row.locked ? 0.55 : 1;
  wmBlit(ps, f, cx, by, k, fa); if (ws.ok) wmBlit(ws, f, cx, by, k, fa);
  vctx.restore();
  return { cur, n: row && row.paths[0] ? row.paths[0].steps.length : 0 };
}
// a long "A · B · C · D" name that won't fit: "A … D"
function mhShort(name, maxW, size, min, weight = 600) {
  if (textW(name, min, weight) <= maxW) return name;
  const ps = String(name).split(' · '); return ps.length > 2 ? ps[0] + ' … ' + ps[ps.length - 1] : name;
}
function mhPanelOpen(S) { S.row = S.row || 0; S.top = 0; S.t0 = time; }
function mhPanelInput(M, a) {
  const S = M.mastery, n = WTYPES.length, L = mhList(WTYPES[S.sel]).items;
  if (['pause', 'back', 'heavy', 'roll'].includes(a)) { S.list = false; sfx.menu(); return; }
  if (a === 'up' || a === 'down') { if (!L.length) return; S.row = (S.row + (a === 'up' ? L.length - 1 : 1)) % L.length; S.t0 = time; sfx.menu(); return; }
  if (a === 'left' || a === 'right') { S.sel = (S.sel + (a === 'left' ? n - 1 : 1)) % n; S.row = 0; S.top = 0; S.t0 = time; sfx.menu(); return; }
  if (['confirm', 'interact', 'attack', 'jump'].includes(a)) { S.t0 = time; sfx.menu(); }   // replay the preview
}
function mhRenderPanel(M) {
  const S = M.mastery, t = WTYPES[S.sel], I = WTYPE_INFO[t], r = masteryRank(t), cur = wtype();
  const LS = mhList(t), L = LS.items, lines = LS.lines;
  if (S.t0 === undefined) S.t0 = time;
  S.row = clamp(S.row || 0, 0, Math.max(0, L.length - 1));
  panel(10, 29, 364, 175);
  // ---- header: icon, name, ◂ ▸, mastery, back button
  uiCell(17, 34, 15, { eq: t === cur }); wmIcon(t, 18.5, 35.5, 12);
  text('◂', 38, 45, 6, UIC.gold, 'center', { alpha: 0.6 + 0.4 * uiPulse(3) });
  uiHit(34, 36, 9, 11, null, () => uiAct('left'));
  text(I.name.toUpperCase(), 45, 43.2, 7.4, UIC.gold, 'left', { spacing: 1.1 });
  const nw = textW(I.name.toUpperCase(), 7.4) + I.name.length * 1.1;
  text('▸', 49 + nw, 45, 6, UIC.gold, 'center', { alpha: 0.6 + 0.4 * uiPulse(3) });
  uiHit(45 + nw, 36, 9, 11, null, () => uiAct('right'));
  text(`MOVE LIST  ·  ${L.length} moves  ·  ${S.sel + 1} / ${WTYPES.length}${t === cur ? '  ·  in hand' : ''}`, 45, 49.4, 3.9, UIC.faint, 'left', { weight: 600, spacing: 0.5 });
  text(`MASTERY ${WM_ROMAN[r - 1]}`, 300, 41.6, 4.8, r > 1 ? UIC.gold : UIC.muted, 'right', { weight: 600, spacing: 0.8 });
  wmPips(274, 46.2, r, { r: 1.3, gap: 3.9 });
  { const lab = '◂ MASTERY', lw = textW(lab, 4.4, 600) + 7; uiHit(366 - lw, 35, lw, 10, null, () => { S.list = false; sfx.menu(); });
    uiRect(366 - lw, 35, lw, 10, '#2a2016', 0.9); vctx.strokeStyle = '#6d5a3a'; vctx.lineWidth = Math.max(1, scale * 0.5); vctx.strokeRect(ox + (366 - lw) * scale + 0.5, oy + 35 * scale + 0.5, lw * scale - 1, 10 * scale - 1);
    text(lab, 366 - lw / 2, 41.8, 4.4, UIC.gold, 'center', { weight: 600, spacing: 0.6 }); }
  uiFade(16, 368, 53, UI_RGB.accent, 0.55);
  // ---- left: the grouped list
  const lx = 16, lw = 192, ly = 59, lh = 8.2, vis = Math.floor((199 - ly) / lh);
  const selLine = L[S.row] ? L[S.row].line : 0;
  if (selLine < S.top + 1) S.top = Math.max(0, selLine - 1 - (lines[selLine - 1] && lines[selLine - 1].head ? 0 : 0));
  if (lines[selLine - 1] && lines[selLine - 1].head && selLine - 1 < S.top) S.top = selLine - 1;
  if (selLine >= S.top + vis) S.top = selLine - vis + 1;
  S.top = clamp(S.top, 0, Math.max(0, lines.length - vis));
  for (let j = S.top; j < Math.min(lines.length, S.top + vis); j++) {
    const ln = lines[j], y = ly + (j - S.top) * lh;
    if (ln.head) {
      const H = ln.head.toUpperCase();
      text(H, lx, y + 0.8, 4.1, ln.head === 'Fatality' ? '#e8907a' : UIC.gold, 'left', { weight: 700, spacing: 0.9 });
      const hw = textW(H, 4.1, 700) + H.length * 0.9 + 3;
      text(String(ln.n), lx + hw, y + 0.8, 3.6, UIC.faint, 'left', { weight: 500 });
      uiFade(lx + hw + textW(String(ln.n), 3.6, 500) + 3, lx + lw, y - 0.8, UI_RGB.accent, 0.45);
      continue;
    }
    const it = ln.it, e = it.e, sel = it.k === S.row, got = r >= (+e.rank || 1);
    uiHit(lx - 3, y - 5.8, lw + 5, lh, () => { if (S.row !== it.k) { S.row = it.k; S.t0 = time; sfx.menu(); } }, () => { if (S.row !== it.k) { S.row = it.k; S.t0 = time; sfx.menu(); } });
    if (sel) uiSel(lx - 3, y - 5.8, lw + 5, lh);
    const rk = +e.rank || 1;
    if (rk > 1) { uiDiamond(lx + 1.5, y - 1.7, 1.4, got ? UIC.gold : '#3a3026'); if (!got) uiDiamond(lx + 1.5, y - 1.7, 1.4, '#6a5a3e', 0.9, true); text(WM_ROMAN[rk - 1], lx + 4.5, y, 3.6, got ? UIC.gold : UIC.faint, 'left', { weight: 700 }); }
    else uiDiamond(lx + 1.5, y - 1.7, 0.8, e.fatality ? '#c86a50' : '#5a4a30');
    const nx = lx + 13, name = mhShort(e.fatality ? 'Fatality' : e.name, 84, 4.9, 4.2);
    const nf = uiFit(name, 84, 4.9, 3.8, 600);
    text(name, nx, y, nf, sel ? UIC.hi : got ? UIC.text : UIC.faint, 'left', { weight: sel ? 700 : 600 });
    const used = textW(name, nf, 600);
    mhInputDraw(e.input, lx + lw, y, lw - 13 - used - 6, got ? 1 : 0.55, { dim: !got, size: 4.2 });
  }
  if (lines.length > vis) {
    const sx = lx + lw + 4, sy = ly - 6, sh = vis * lh;
    uiScroll(sx, sy, sh, S.top, vis, lines.length);
    uiHit(sx - 2, sy, 5, sh, null, () => { const f = clamp((UIM.y - sy) / sh, 0, 1); const ln = Math.round(f * (lines.length - 1)); let best = 0; for (const it of L) if (it.line <= ln) best = it.k; S.row = best; S.t0 = time; sfx.menu(); });
  }
  // ---- right: the selected move
  const it = L[S.row]; if (!it) { uiFooter([['↑↓', 'move'], ['←→', 'weapon'], ['Esc', 'back']]); return; }
  const e = it.e, row = it.row, got = r >= (+e.rank || 1), rx = 218, rw = 150;
  row.locked = !got;
  const st = mhStage(t, row, rx, 57, rw, 62, S.t0);
  // the path under the stage: each step's key, the one playing lit
  const p0 = row.paths[0];
  if (p0 && st) {
    let x = rx + 4; const y = 115.6;
    p0.steps.forEach((s, k) => {
      const parts = s.parts.filter(q => q !== 'tap'), hot = st.cur === k;
      if (k) { text('›', x + 0.6, y - 0.1, 4.4, UIC.faint, 'left', { shadow: false }); x += 3.6; }
      x += mhGlyphs(parts, x, y, 3.8, hot ? 1 : 0.62, { hot }) + 1.6;
    });
  }
  let y = 128;
  const nm = e.fatality ? (() => { try { return fatDef(t).name; } catch (er) { return 'Fatality'; } })() : e.name;
  { const mw = rw - (got ? 26 : 56), nm2 = mhShort(nm, mw, 6.6, 5.2); text(nm2, rx, y, uiFit(nm2, mw, 6.6, 4.6, 600), got ? UIC.hi : UIC.muted, 'left', { weight: 600 }); }
  const rk = +e.rank || 1;
  text(e.fatality ? 'FATALITY' : !got ? `LOCKED · MASTERY ${WM_ROMAN[rk - 1]}` : `RANK ${WM_ROMAN[rk - 1]}`, rx + rw, y, 3.9, !got ? '#e0907a' : rk > 1 ? UIC.gold : UIC.faint, 'right', { weight: 700, spacing: 0.6 });
  y += 8.4; mhInputDraw(e.input, rx, y, rw, 1, { align: 'left', size: 4.6 });
  y += 5.2; uiFade(rx, rx + rw, y, UI_RGB.accent, 0.4); y += 6.4;
  for (const l of wrap(String(e.desc || ''), rw, 4.7).slice(0, 4)) { text(l, rx, y, 4.7, got ? UIC.body : UIC.dim, 'left', { weight: 400 }); y += 6; }
  const fin = e.fatality ? null : mhFinal(row), nums = fin && mhNumbers(fin);
  // what it leads into (at your rank): the next presses from its last move
  const nx = fin && got ? mhCands({ type: t, nodes: [fin], rank: r, max: 3, air: false, noRoot: true }) : [];
  if (nx.length && y < 168) {
    y += 1.5; text('LEADS INTO', rx, y, 3.6, UIC.faint, 'left', { weight: 700, spacing: 0.7 }); y += 6.2;
    for (const c of nx) { if (y > 184) break; const gw2 = mhGlyphs(c.parts, rx + 2, y, 3.8, 0.9); text(c.name, rx + 5 + gw2, y, 4.4, UIC.text, 'left', { weight: 600 }); y += 6.4; }
  }
  if (nums) {
    let x = rx; const ny = 196.4;
    for (const [k2, v] of nums) {
      const w1 = textW(k2, 3.3, 700), w2 = textW(v, 4.4, 600), cw = Math.max(w1, w2) + 4.5;
      if (x + cw > rx + rw + 1) break;
      uiRect(x, ny - 10.6, cw - 1.5, 13, 'rgba(30,23,16,0.75)');
      text(k2, x + 1.6, ny - 6.4, 3.3, UIC.faint, 'left', { weight: 700, spacing: 0.3 });
      text(v, x + 1.6, ny, 4.4, got ? UIC.gold : UIC.dim, 'left', { weight: 600 });
      x += cw;
    }
  } else if (e.fatality) text('5× on bosses · executes weak foes', rx, 196.4, 4.4, UIC.muted, 'left', { weight: 500 });
  uiFooter([['↑↓', 'move'], ['←→', 'weapon'], ['Enter', 'replay'], ['Esc', 'back']]);
}
// the Mastery screen hands its list mode to the panel (29_ui2.js / 08b_menus.js call these by name)
{
  const _rms = renderMasteryScreen;
  renderMasteryScreen = function (M) { if (M && M.mastery && M.mastery.list) { try { return mhRenderPanel(M); } catch (e) { MH.err = String(e); console.error(e); } } return _rms.apply(this, arguments); };
  const _wsi = wmScreenInput;
  wmScreenInput = function (M, a) { if (M && M.mastery && M.mastery.list) return mhPanelInput(M, a); const r = _wsi.apply(this, arguments); if (M.mastery && M.mastery.list && M.mastery.t0 === undefined) mhPanelOpen(M.mastery); return r; };
}

if (typeof window !== 'undefined' && window.__game) window.__game.mh = { MH, MH_MAP, MH_CTX, build: mhBuild, parse: mhParse, reset: mhReset, cands: o => mhCands(o), nodes: () => mhNodes(), head: t => mhHead(t || mvType()), list: t => mhList(t), inputParts: mhInputParts, final: mhFinal, numbers: mhNumbers, seq: (t, row) => mhPreviewSeq(t, row) };
