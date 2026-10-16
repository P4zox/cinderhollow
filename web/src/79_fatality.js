// ------------------------------------------------------------------ v16 FATALITIES: the shared framework (agent `fatality`, docs/v16/fatality.md)
// K on a critable foe (the same foes and range J's riposte uses: critTarget()) plays the FATALITY of the weapon type in
// hand. J keeps the quick riposte. Either one consumes the stagger (onCritStart -> critDone): once per stagger.
//  * fatalityRegister(type, def): each weapon file registers its choreography (steps on the fatality's own clock, ms).
//  * Damage: bosses 5.0 x AR in shares (the steps' `hit` weights, normalised), regular foes executed outright if their HP
//    <= 12 x AR, else 8 x AR. AR = outgoing(D.light, 1) x Riposte Mastery x Executioner x D.W.crit (as the riposte).
//    Every beat is a crit blow (no stagger bonus, no procs, no strike hooks: Boss Cores only tint the colour).
//  * The player is invulnerable and can't be interrupted; the target's owner (the boss object, also for multi-body bosses)
//    is HELD: its update is replaced by a stand-in for the fatality (no attacks, no movement); afterwards its own update
//    returns and its stagger timer continues (crit blows cut it to <= 0.45 s, as the riposte does).
//  * Cinematic layer: letterbox bars, the world darkened (not the player / target / effects), weapon-coloured vignette and
//    flashes, slow-mo + hitstop + shake on the beats, a low boom, the fatality's name in the title font, a small camera
//    punch-in on the final image (HUD untouched).
//  * VFX toolkit (FATFX): auraBlade, slashLine, crescent, shockwave, groundCrack, pillar, sparkBurst, emberBurst,
//    soulWisps, afterimage, speedLines, impactFlash -- crisp 1-px pixel art into the glow layer.
//  * A generic fallback fatality for any type without its own; a "Fatality" row in every type's Move List.
// Hooks in from this file (wrappers + HOOKS); the only edit elsewhere is HOOKS.renderMid in 09_main.js's renderWorld.

const FAT = { defs: {}, on: null, fx: [], parts: [], log: [], last: null, n: 0, dimmed: [], zoomAmt: 0.055,
  cine: { bars: 0, dark: 0, vig: 0, flash: 0, zoom: 0, kick: 0, name: null, col: '255,230,190' } };
const FAT_BOSS = 5.0, FAT_REG = 8.0, FAT_EXEC = 12.0;
const FAT_TYPES = ['longsword', 'katana', 'greatsword', 'maul', 'sns', 'dual', 'spear', 'staff', 'whip', 'saxe', 'bow', 'fist', 'scythe', 'bell'];
// the fallback's colour per type (a registered def brings its own `col`)
const FAT_COL = { longsword: '255,220,160', katana: '205,225,255', greatsword: '255,160,80', maul: '255,205,130', sns: '255,215,120',
  dual: '235,70,80', spear: '170,210,255', staff: '190,235,215', whip: '150,195,255', saxe: '255,170,80', bow: '255,145,60',
  fist: '255,125,60', scythe: '205,185,255', bell: '240,212,150' };
const FAT_CINE = { bars: 1, dark: 0.5, vig: 1, zoom: 1 };   // a def's `cine` overrides these (0 turns a layer off)
if (!HOOKS.renderMid) HOOKS.renderMid = [];   // 09_main.js: after the terrain / props, before any body is drawn

// ================================================================== colours / easing / pixels
function fatRGB(c) {
  if (!c) return '255,230,190';
  if (Array.isArray(c)) return c.join(',');
  if (c[0] === '#') { const s = c.length === 4 ? c.slice(1).split('').map(q => q + q).join('') : c.slice(1, 7); return [0, 2, 4].map(i => parseInt(s.slice(i, i + 2), 16)).join(','); }
  return c;
}
function fatMix(a, b, k) { const A = fatRGB(a).split(',').map(Number), B = fatRGB(b).split(',').map(Number); return A.map((v, i) => Math.round(v + (B[i] - v) * k)).join(','); }
const fatHot = c => fatMix(c, '255,255,255', 0.78), fatLite = c => fatMix(c, '255,255,255', 0.42), fatDeep = c => fatMix(c, '0,0,0', 0.5);
const FAT_EASE = { linear: k => k, out: k => 1 - (1 - k) * (1 - k), in: k => k * k, inout: k => k < 0.5 ? 2 * k * k : 1 - 2 * (1 - k) * (1 - k),
  snap: k => 1 - Math.pow(1 - k, 4), back: k => { const s = 1.6; return 1 + (s + 1) * Math.pow(k - 1, 3) + s * Math.pow(k - 1, 2); } };
const fatEase = (n, k) => (FAT_EASE[n] || FAT_EASE.out)(clamp(k, 0, 1));
const FAT_BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5].map(v => (v + 0.5) / 16);
const fatDith = (x, y, a) => a > FAT_BAYER[((y & 3) << 2) | (x & 3)];   // ordered-dither: keep this pixel at coverage a?
function fatHash(x, y) { let h = (x * 374761393 + y * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
function fatRng(seed) { let s = (seed * 2654435761) >>> 0 || 1; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
// a crisp 1-px line (pixels below clipY are skipped: blades that bite the floor)
function fatLine(x0, y0, x1, y1, clipY) {
  const dx = x1 - x0, dy = y1 - y0, n = Math.max(1, Math.ceil(Math.max(Math.abs(dx), Math.abs(dy))));
  let px = null, py = null;
  for (let i = 0; i <= n; i++) {
    const x = Math.round(x0 + dx * i / n), y = Math.round(y0 + dy * i / n);
    if (x === px && y === py) continue; px = x; py = y;
    if (clipY !== undefined && y > clipY) continue;
    g.fillRect(x, y, 1, 1);
  }
}
// a convex polygon, scanline-filled on whole pixels (no anti-aliased edges). pts: [[x, y], ...]
function fatPoly(pts, clipY) {
  let y0 = Infinity, y1 = -Infinity;
  for (const p of pts) { if (p[1] < y0) y0 = p[1]; if (p[1] > y1) y1 = p[1]; }
  y0 = Math.ceil(y0 - 0.5); y1 = Math.floor(y1 - 0.5); if (clipY !== undefined) y1 = Math.min(y1, clipY);
  const n = pts.length;
  for (let y = y0; y <= y1; y++) {
    const yc = y + 0.5; let xl = Infinity, xr = -Infinity;
    for (let i = 0; i < n; i++) {
      const a = pts[i], b = pts[(i + 1) % n];
      if ((a[1] <= yc && b[1] > yc) || (b[1] <= yc && a[1] > yc)) { const x = a[0] + (yc - a[1]) / (b[1] - a[1]) * (b[0] - a[0]); if (x < xl) xl = x; if (x > xr) xr = x; }
    }
    if (xr > xl) { const xa = Math.round(xl), xb = Math.round(xr); if (xb > xa) g.fillRect(xa, y, xb - xa, 1); }
  }
}
// rasterise a box: fn(x, y) -> palette index (0 = empty); same-index runs on a row become one fillRect
function fatRaster(x0, y0, x1, y1, fn, pal) {
  x0 = Math.floor(x0); y0 = Math.floor(y0); x1 = Math.ceil(x1); y1 = Math.ceil(y1);
  for (let y = y0; y <= y1; y++) {
    let run = 0, rx = 0;
    for (let x = x0; x <= x1 + 1; x++) {
      const v = x <= x1 ? fn(x, y) : 0;
      if (v !== run) { if (run) { g.fillStyle = pal[run]; g.fillRect(rx, y, x - rx, 1); } run = v; rx = x; }
    }
  }
}
function fatEllipse(cx, cy, rx, ry, clipY) {   // 1-px outline
  const n = Math.max(8, Math.ceil(Math.PI * (rx + ry) * 1.2));
  let px = null, py = null;
  for (let i = 0; i < n; i++) {
    const a = i / n * 6.2832, x = Math.round(cx + Math.cos(a) * rx), y = Math.round(cy + Math.sin(a) * ry);
    if (x === px && y === py) continue; px = x; py = y;
    if (clipY !== undefined && y > clipY) continue;
    g.fillRect(x, y, 1, 1);
  }
}
// facing-space angle (0 = forward, -90 = up, +90 = down) -> world radians
const fatAng = (deg, face) => { const r = deg * Math.PI / 180; return face > 0 ? r : Math.PI - r; };

// ================================================================== registration
function fatalityRegister(type, def) {
  if (!def || !Array.isArray(def.steps)) throw new Error('fatalityRegister(' + type + '): def.steps missing');
  def.type = type; def.dur = def.dur || 1500; def.name = def.name || 'Fatality';
  def.steps = def.steps.map(s => ({ ...s, at: s.at || 0 })).sort((a, b) => a.at - b.at);
  FAT.defs[type] = def;
  return def;
}
// the generic fallback (built per start: it reads the type's own tags from the move tables)
function fatTagOf(id) { try { return ATK[id] && ATK[id].mv ? mvResolve(ATK[id]).tag : null; } catch (e) { return null; } }
function fatFallback(type) {
  const T = MV.types[type] || {}, M = MOVESETS[type] || {};
  let cId = null; try { cId = T.counter ? T.counter() : null; } catch (e) {}
  const t1 = (cId && fatTagOf(cId)) || fatTagOf(M.combo && M.combo[0]) || 'riposte', hId = T.K || M.heavy, t2 = fatTagOf(hId) || 'heavy';
  // land the big beat on the heavy tag's own hit frame
  let k2 = 0.45; try { const R = mvResolve(ATK[hId]); if (R && R.tTot) k2 = clamp(R.tHit / R.tTot, 0.2, 0.7); } catch (e) {}
  const s2 = 560, span2 = 760, hit2 = Math.round(s2 + span2 * k2);
  return { type, fallback: true, name: 'Last Rite', col: FAT_COL[type] || '255,220,160', tag: t1, dur: s2 + span2 + 60,
    steps: [
      { at: 0, move: { gap: 8, dur: 110 }, anim: t1, span: s2 },
      { at: 60, fx: 'afterimage', o: { dur: 160, every: 40, alpha: 0.32, life: 0.22 } },
      { at: Math.round(s2 * 0.5), hit: 1.4, stop: 0.06, shake: 4, flash: 0.15 },
      { at: Math.round(s2 * 0.5), fx: 'crescent', o: { anchor: 'player', dy: -18, r: 30, thick: 9, a0: 120, a1: -60, grow: 70, linger: 160, shatter: 180, shards: 10 } },
      { at: Math.round(s2 * 0.5), fx: 'sparkBurst', o: { n: 10 } },
      { at: s2, anim: t2, span: span2 },
      { at: s2 + 40, fx: 'speedLines', o: { dur: 220, n: 10 } },
      { at: hit2 - 40, fx: 'auraBlade', o: { dy: -20, len: 46, w: 6, keys: [[0, -120, 0.2], [40, -110, 1], [90, 60, 1, 'snap'], [260, 64, 0]] } },
      { at: hit2, hit: 3.6, slow: 0.35, stop: 0.12, shake: 9, flash: 0.45, boom: true, name: true },
      { at: hit2, fx: 'impactFlash', o: { r: 34 } },
      { at: hit2, fx: 'shockwave', o: { anchor: 'ground', r1: 70, sq: 0.25, rings: 2 } },
      { at: hit2, fx: 'pillar', o: { w: 12, dur: 520 } },
      { at: hit2, fx: 'sparkBurst', o: { n: 22, spd: 220 } },
      { at: hit2 + 20, fx: 'emberBurst', o: { n: 16 } },
    ] };
}
function fatDef(type) { return FAT.defs[type] || fatFallback(type); }

// ================================================================== target helpers
function fatOwner(t) {
  if (typeof boss !== 'undefined' && boss && (t === boss || (boss.parts && boss.parts.includes(t)))) return boss;
  return t;
}
const fatAlive = t => !!t && t.alive !== false && !(t.hp <= 0);
function fatHB(F) {
  const t = F.target; let hb = null;
  try { hb = t && t.hurtbox && t.hurtbox(); } catch (e) {}
  if (hb) F.hbLast = hb;
  return hb || F.hbLast || rect(F.x0 + F.face0 * 20 - 8, F.y0 - 30, F.x0 + F.face0 * 20 + 8, F.y0);
}
function fatTC(F) { const hb = fatHB(F); return { x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, top: hb.y0, floor: Math.max(hb.y1, F.y0), hb }; }
// the target may be moved only if it is a small foe (never a boss / boss part / elite / prop)
const fatSmall = t => !!t && !t.boss && !t.prop && !(t.cfg && t.cfg.elite) && (typeof boss === 'undefined' || !boss || fatOwner(t) !== boss);
// hold an object: its own update is replaced by fatHeld for the fatality (instance override, restored after)
function fatHold(o, F) {
  if (!o || o._fatHold) return;
  const own = Object.prototype.hasOwnProperty.call(o, 'update') ? o.update : undefined;
  o._fatHold = { own, F };
  o.update = function (dt) { fatHeld(this, dt); };
}
function fatRelease(o) {
  if (!o || !o._fatHold) return;
  const h = o._fatHold; delete o._fatHold;
  if (h.own) o.update = h.own; else delete o.update;
  if (h.lifted) { o.ground = false; if (o.vy !== undefined) o.vy = Math.max(o.vy || 0, 0); }
}
function fatHeld(o, dt) {}   // the stand-in update: nothing acts (flash decay and target motion run in fatHoldTick)
function fatHoldTick(F, dt) {
  const raw = slowmo > 0 ? dt / 0.35 : dt, list = [F.target, F.owner].concat(F.owner && F.owner.parts || []);
  for (const o of list) if (o && o.flash > 0) o.flash = Math.max(0, o.flash - raw * 8);
  const o = F.target, m = F.tm;
  if (!m || !o || !fatAlive(o)) return;
  // small-foe motion: lift / knockback / pin / drop on the fatality clock
  const k = m.dur > 0 ? fatEase(m.ease || 'out', (F.t - m.t0) / m.dur) : 1;
  const ox = lerp(m.fx, m.tx, k), oy = lerp(m.fy, m.ty, k);
  const nx = F.tx0 + F.face0 * ox, ny = F.ty0 - oy;
  if (!solidAtPx(nx, ny - 6) && !solidAtPx(nx, ny - Math.min(20, o.h || 20))) o.x = nx;
  if (!solidAtPx(o.x, ny - (o.h || 20))) o.y = ny;
  if (oy > 0.5 && o._fatHold) o._fatHold.lifted = true;
  if (o.vx !== undefined) o.vx = 0; if (o.vy !== undefined) o.vy = 0;
}
// move a small foe: { lift: px up, knock: px away (facing dir), dur, ease } (bosses never move); { pin: true } freezes it
// where it is; { drop: true } lets it fall back to its start height
function fatTargetMove(F, m) {
  const t = F.target; if (!fatSmall(t) || !fatAlive(t)) return;
  const cur = F.tm ? { x: lerp(F.tm.fx, F.tm.tx, fatEase(F.tm.ease || 'out', (F.t - F.tm.t0) / Math.max(1, F.tm.dur))), y: lerp(F.tm.fy, F.tm.ty, fatEase(F.tm.ease || 'out', (F.t - F.tm.t0) / Math.max(1, F.tm.dur))) } : { x: 0, y: 0 };
  if (m.pin) { F.tm = { fx: cur.x, fy: cur.y, tx: cur.x, ty: cur.y, t0: F.t, dur: 0 }; return; }
  F.tm = { fx: cur.x, fy: cur.y, tx: m.knock !== undefined ? cur.x + m.knock : cur.x, ty: m.drop ? 0 : m.lift !== undefined ? m.lift : cur.y,
    t0: F.t, dur: m.dur ?? (m.drop ? 140 : 180), ease: m.ease || (m.drop ? 'in' : 'out') };
}

// ================================================================== starting
function fatReady() {
  return !!(P && D && P.ground && !FAT.on && typeof state !== 'undefined' && state === 'play' && P.state !== 'dead' && critTarget());
}
function fatalityStart(tIn) {
  const t = tIn || critTarget(); if (!t || FAT.on || !P || P.state === 'dead') return false;
  const type = mvType(), def = fatDef(type), owner = fatOwner(t);
  const isBoss = !!(t.boss || owner === boss);
  const hb = t.hurtbox && t.hurtbox(), cx = hb ? (hb.x0 + hb.x1) / 2 : t.x;
  P.face = cx > P.x ? 1 : cx < P.x ? -1 : P.face;
  t.onCritStart && t.onCritStart();
  // colour: the weapon's, pulled toward the Boss Core's when one is socketed (visual only)
  let core = null; try { const c = typeof crCur === 'function' ? crCur() : null; if (c) core = fatRGB(typeof crColNow === 'function' ? crColNow(c) : c.col); } catch (e) {}
  const base = fatRGB(def.col || FAT_COL[type]), col = core ? fatMix(base, core, 0.7) : base;
  P.mvQ = null; P.mvQ2 = null; P.mvCarry = null; P.mvChain = null; P.hitSet = new Set(); P.crit = t; P.vx = 0; P.combo = 0;
  setP('fatality', 'idle', false, 0);
  // damage (computed in the fatality state, so no move's own bonuses ride along)
  const mods = (has('riposte_mastery') ? 1.5 : 1) * (D.W.crit || 1) * (has('executioner') ? 1.3 : 1) * (typeof skillOn === 'function' && skillOn('m_dagger') ? 1.25 : 1);
  const unit = outgoing(D.light, 1, 'melee') * mods;
  const steps = def.steps.map(s => ({ ...s }));
  const shareSum = steps.reduce((s, q) => s + (q.hit > 0 ? q.hit : 0), 0);
  const F = { def, type, name: def.name, t: 0, dur: def.dur, si: 0, steps, target: t, owner, boss: isBoss, small: fatSmall(t),
    x0: P.x, y0: P.y, face0: P.face, face: P.face, col, base, core, unit, shareSum, shares: 0, dealt: 0, beats: [],
    hp0: P.hp, thp0: t.hp, tx0: t.x, ty0: t.y, mv: null, seg: null, ghost: null, cine: { ...FAT_CINE, ...(def.cine || {}) }, n: ++FAT.n };
  if (isBoss) { F.total = unit * FAT_BOSS; F.exec = false; }
  else { F.exec = t.hp <= unit * FAT_EXEC; F.total = F.exec ? t.hp : unit * FAT_REG; }
  F.mv = { fx: 0, fy: 0, tx: 0, ty: 0, t0: 0, dur: 0, ease: 'out' };
  F.animAts = steps.filter(s => s.anim).map(s => s.at);
  F.seg = fatSeg(F, [def.tag].concat(def.tags || []), 0, def.span || (F.animAts.find(a => a > 0) ?? F.dur));
  F.x = P.x; F.y = P.y;
  fatHelpers(F);
  fatHold(owner, F); if (owner !== t) fatHold(t, F);   // a part that updates itself is held too
  fatDimOthers(F);
  FAT.on = F; FAT.cine.col = col; FAT.cine.name = null;
  try { tone(98, 0.55, 0.12, 'sine', 0.5); noise(0.35, 700, 0.6, 0.18, 'bandpass', 0.3); } catch (e) {}
  if (def.start) def.start(F);
  fatUpdateState(F, 0);   // steps at 0 run now, the first frame is already posed
  return true;
}
// F's helper methods (for steps' fns and a def's draw / tick / start)
function fatHelpers(F) {
  F.fx = (k, o = {}) => fatSpawn(F, k, o);
  F.tc = () => fatTC(F);
  F.shoulder = () => ({ x: P.x - F.face * 1, y: P.y - 19 });
  F.tip = (mode = 'a') => {   // the weapon tip in world space (or the shoulder + 18 px along the facing)
    try { const ws = typeof feelWsheet === 'function' ? feelWsheet() : null, tp = ws && feelTip(ws, P.anim.frame, mode); if (tp) return { x: ws.native === P.face ? P.x + tp.dx : P.x - tp.dx, y: P.y + tp.dy }; } catch (e) {}
    return { x: P.x + F.face * 18, y: P.y - 18 };
  };
  F.aura = (a = 0.25, spread = 1) => { if (typeof mvAura === 'function') mvAura(`rgb(${F.col})`, a, spread); };
  F.light = (x, y, r, k = 1) => addLight(x, y, r, F.col, k);
}
// an animation segment: the first tag the sheet has, time-mapped over `span` ms of the fatality clock
function fatSeg(F, tags, at, span) {
  const list = tags.filter(Boolean);
  const tag = list.find(x => pHas(x)) || ['riposte', 'attack3', 'idle'].find(x => pHas(x)) || 'idle';
  const sh = pSheet(), tg = sh.ok && sh.tag(tag), cum = [0];
  if (tg) for (let i = tg.from; i <= tg.to; i++) cum.push(cum[cum.length - 1] + (sh.frames[i].ms || 100)); else cum.push(100);
  P.anim.set(tag, false, 0);
  return { tag, at, span: Math.max(1, span), cum, n: cum.length - 1, tot: cum[cum.length - 1], real: tag === list[0], hold: false };
}

// ================================================================== the state (04_player's default branch: MV_STATES)
MV_STATES.fatality = function (dt, ax, grav) {
  const F = FAT.on;
  if (!F) { P.vx = 0; grav(); setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); return; }
  fatUpdateState(F, dt, grav);
};
MV_STATES.fatality.inv = () => true;   // mvIframes(): invulnerable throughout
function fatUpdateState(F, dt, grav) {
  F.t += dt * 1000;
  while (F.si < F.steps.length && F.steps[F.si].at <= F.t) { const s = F.steps[F.si++]; try { fatStep(F, s); } catch (e) { console.error('fatality step', e); } }
  if (FAT.on !== F) return;
  fatAnimFrame(F);
  if (dt > 0) fatMoveFrame(F, dt, grav);
  if (F.ghost && F.t <= F.ghost.until && F.t - F.ghost.last >= F.ghost.every) { F.ghost.last = F.t; mvAfterimage(F.ghost.col, F.ghost.life, F.ghost.alpha); }
  if (F.def.tick) try { F.def.tick(F, dt); } catch (e) { console.error(e); }
  F.x = P.x; F.y = P.y;
  if (F.t >= F.dur) fatEnd(F);
}
function fatAnimFrame(F) {
  const s = F.seg, an = P.anim; if (!s) return;
  if (an.tag !== s.tag) an.set(s.tag, false, 0);
  const tau = clamp((F.t - s.at) / s.span, 0, 0.9999) * s.tot;
  let i = 0; while (i < s.n - 1 && tau >= s.cum[i + 1]) i++;
  if (i !== an.i) { an.i = i; an.changed = true; }
  an.t = Math.min(tau - s.cum[i], an.ms(i) - 0.01); an.speed = 0; an.done = false;
}
function fatMoveFrame(F, dt, grav) {
  const m = F.mv, k = m.dur > 0 ? fatEase(m.ease, (F.t - m.t0) / m.dur) : 1;
  const ox = lerp(m.fx, m.tx, k), oy = lerp(m.fy, m.ty, k);
  P.vx = (F.x0 + F.face0 * ox - P.x) / dt;
  if (Math.abs(oy) > 0.25 || Math.abs(m.fy) > 0.25 || !P.ground) {
    if (Math.abs(oy) > 0.25 || Math.abs(m.ty) > 0.25) { P.vy = (F.y0 + oy - P.y) / dt; P.ground = false; }
    else grav();
  } else grav();
}
function fatStep(F, s) {
  if (s.move) {
    const m = s.move, cur = { x: (P.x - F.x0) * F.face0, y: P.y - F.y0 };
    let gx = cur.x, gy = cur.y;
    if (m.dx !== undefined) gx = m.dx;
    if (m.gap !== undefined || m.through !== undefined || m.tx !== undefined) {
      const hb = fatHB(F), near = F.face0 > 0 ? hb.x0 : hb.x1, far = F.face0 > 0 ? hb.x1 : hb.x0, c = (hb.x0 + hb.x1) / 2;
      if (m.gap !== undefined) gx = clamp((near - F.x0) * F.face0 - m.gap, cur.x - 10, cur.x + 60);
      if (m.through !== undefined) gx = (far - F.x0) * F.face0 + m.through;
      if (m.tx !== undefined) gx = (c - F.x0) * F.face0 + m.tx;
    }
    if (m.dy !== undefined) gy = m.dy;
    F.mv = { fx: cur.x, fy: cur.y, tx: gx, ty: gy, t0: s.at, dur: m.dur ?? 120, ease: m.ease || 'out' };
  }
  if (s.anim) {
    const next = F.animAts.find(a => a > s.at);
    F.seg = fatSeg(F, [].concat(s.anim), s.at, s.span || ((next ?? F.dur) - s.at));
  }
  if (s.face) {
    if (s.face === 'target') { const c = fatTC(F); F.face = c.x >= P.x ? 1 : -1; } else F.face = s.face < 0 ? -F.face : F.face;
    P.face = F.face;
  }
  if (s.target) fatTargetMove(F, s.target);
  if (s.ghosts) F.ghost = { until: s.at + (s.ghosts.dur || 200), every: s.ghosts.every || 35, last: -1e9, col: s.ghosts.col || `rgb(${fatLite(F.col)})`, life: s.ghosts.life || 0.3, alpha: s.ghosts.alpha || 0.5 };
  if (s.cine) Object.assign(F.cine, s.cine);
  if (s.fx) fatSpawn(F, s.fx, s.o || {});
  if (s.sfx) { try { if (typeof s.sfx === 'function') s.sfx(F); else if (sfx[s.sfx]) sfx[s.sfx](); else if (s.sfx === 'boom') fatBoom(); } catch (e) {} }
  if (s.hit !== undefined) fatBeat(F, s);
  else fatFeel(F, s, false);
  if (s.name) fatName(F);
  if (s.call) s.call(F, s);
}
// ---- a damage beat
function fatBeat(F, s) {
  const t = F.target, share = Math.max(0, s.hit || 0);
  F.shares += share;
  const last = F.shares >= F.shareSum - 1e-6;
  if (fatAlive(t) && (share > 0 || last)) {
    let dmg = F.shareSum > 0 ? F.total * share / F.shareSum : F.total;
    if (F.exec) dmg = last ? Math.max(1, t.hp) + 1 : Math.min(dmg, Math.max(0, t.hp - 1));
    const hb = fatHB(F), x = clamp(s.x !== undefined ? P.x + F.face * s.x : (hb.x0 + hb.x1) / 2, hb.x0, hb.x1), y = s.hy !== undefined ? lerp(hb.y0, hb.y1, s.hy) : (hb.y0 + hb.y1) / 2;
    const before = t.hp;
    if (dmg > 0) t.hit({ dmg, poise: 0, dir: F.face, kind: 'crit', x, y, melee: true, big: true, crit: true, fatality: true });
    if (F.exec && last && fatAlive(t) && t.hp > 0) { t.hp = 0; try { t.die ? t.die({ dir: F.face }) : null; } catch (e) {} }
    const got = Math.max(0, before - Math.max(0, t.hp));
    F.dealt += got; F.beats.push({ at: Math.round(F.t), share, dmg: Math.round(dmg), got: Math.round(got) });
    if (!fatAlive(t)) fatTargetDied(F);
  }
  fatFeel(F, s, true, last);
}
function fatFeel(F, s, beat, last) {
  const stop = s.stop ?? (beat ? (last ? 0.13 : 0.06) : 0);
  if (stop > 0) hitstop = Math.max(hitstop, stop);
  if (s.slow) slowmo = Math.max(slowmo, s.slow);
  const sh = s.shake ?? (beat ? (last ? 9 : 4) : 0); if (sh) shake = Math.max(shake, sh);
  const fl = s.flash ?? (beat ? (last ? 0.45 : 0.15) : 0); if (fl) FAT.cine.flash = Math.max(FAT.cine.flash, fl);
  if (beat || s.kick) { FAT.cine.kick = Math.max(FAT.cine.kick, s.zoom ?? (last ? 1 : 0.45)); if (typeof feelKick === 'function') feelKick(F.face * (s.kick ?? (last ? 2.4 : 1.2)), s.kickY ?? (last ? 1 : 0)); }
  if (s.boom) fatBoom();
  if (beat) { try { (last ? sfx.crit : sfx.bigHit)(); } catch (e) {} }
  const c = fatTC(F); if (beat) addLight(c.x, c.y, last ? 90 : 50, F.col, last ? 0.75 : 0.45);
}
function fatBoom() {
  try { tone(41, 1.1, 0.55, 'sine', 0.55); noise(0.7, 120, 0.7, 0.75, 'lowpass', 0.35); tone(82, 0.4, 0.16, 'triangle', 0.5); } catch (e) {}
}
function fatName(F) { FAT.cine.name = { text: F.name, col: F.col, t0: time, life: 1.9 }; }
function fatTargetDied(F) {
  // a dead target / boss is let go at once so its death (rewards, banners) plays; a dead part of a living duo keeps
  // the other body held
  if (F.owner === F.target || !fatAlive(F.owner) || (F.owner.alive === false)) fatRelease(F.owner);
  fatRelease(F.target);
}
function fatEnd(F, aborted) {
  if (FAT.on !== F) return;
  // whatever share never came out (a def without beats, an early end) lands now
  if (!aborted && F.shares < F.shareSum - 1e-6) fatBeat(F, { hit: F.shareSum - F.shares, stop: 0, shake: 0, flash: 0 });
  if (!aborted && F.shareSum <= 0) fatBeat(F, { hit: 0, stop: 0, shake: 0, flash: 0 });
  fatRelease(F.owner); if (F.target !== F.owner) fatRelease(F.target);
  FAT.on = null; FAT.last = { type: F.type, name: F.name, boss: F.boss, exec: F.exec, unit: F.unit, total: F.total, dealt: F.dealt, beats: F.beats, aborted: !!aborted, dur: F.t, thp0: F.thp0, thp1: F.target ? F.target.hp : null };
  FAT.log.push(FAT.last); if (FAT.log.length > 40) FAT.log.shift();
  if (P.hp < F.hp0) P.hp = F.hp0;
  if (!aborted) {
    if (has('riposte_mastery')) P.hp = Math.min(D.maxHp, P.hp + Math.round(D.maxHp * 0.05));
    if (has('executioner')) P.st = Math.min(D.maxSt, P.st + 30);
  }
  P.crit = null; P.vx = 0; if (P.vy < 0) P.vy = 0;
  if (P.state === 'fatality') setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground);
  if (F.def.end) try { F.def.end(F, !!aborted); } catch (e) {}
}
function fatAbort() { if (FAT.on) fatEnd(FAT.on, true); }

// ---- the world darkens except the player / target / effects: others are drawn through a brightness filter
function fatDimOthers(F) {
  const list = [];
  for (const e of enemies) if (e !== F.target && e !== F.owner && e.alive) list.push(e);
  if (typeof boss !== 'undefined' && boss && boss !== F.owner) list.push(boss);
  if (F.owner && Array.isArray(F.owner.parts)) for (const p of F.owner.parts) if (p !== F.target && p.alive !== false) list.push(p);   // the duo's other body
  for (const e of list) {
    if (e._fatDim) continue;
    const own = Object.prototype.hasOwnProperty.call(e, 'draw') ? e.draw : undefined, base = own || Object.getPrototypeOf(e).draw;
    if (typeof base !== 'function') continue;
    e._fatDim = { own };
    e.draw = function () {
      const k = FAT.cine.dark; if (k < 0.02 || !('filter' in g)) return base.apply(this, arguments);
      const f0 = g.filter; g.filter = `brightness(${(1 - k).toFixed(2)})`;
      try { return base.apply(this, arguments); } finally { g.filter = f0; }
    };
    FAT.dimmed.push(e);
  }
}
function fatUndim() { for (const e of FAT.dimmed) { if (!e._fatDim) continue; const o = e._fatDim; delete e._fatDim; if (o.own) e.draw = o.own; else delete e.draw; } FAT.dimmed = []; }

// ================================================================== VFX toolkit
// Every effect: { k, o, F, t (ms), life (ms), x, y }. Anchors (o.anchor): 'target' (hurtbox centre, default), 'ground'
// (the target's feet line), 'player' (feet), 'start' (where the fatality began), 'tip' (the weapon tip), or fn(F) ->
// {x, y}; o.dx (along the facing) / o.dy offset it; o.follow re-anchors every frame. o.col overrides the colour.
function fatAnchor(F, o) {
  const a = o.anchor || 'target'; let p;
  if (typeof a === 'function') p = a(F);
  else if (a === 'player') p = { x: P.x, y: P.y };
  else if (a === 'start') p = { x: F.x0, y: F.y0 };
  else if (a === 'tip') p = F.tip();
  else if (a === 'shoulder') p = F.shoulder();
  else { const c = fatTC(F); p = { x: c.x, y: a === 'ground' ? c.floor : a === 'top' ? c.top : c.y }; }
  return { x: p.x + (o.dx || 0) * F.face, y: p.y + (o.dy || 0) };
}
function fatSpawn(F, k, o = {}) {
  const def = typeof k === 'function' ? { custom: k } : FATFX[k];
  if (!def) { console.warn('fatality fx?', k); return null; }
  const p = fatAnchor(F, o);
  const e = { k: typeof k === 'function' ? 'custom' : k, o, F, t: 0, x: p.x, y: p.y, face: F.face, col: fatRGB(o.col || F.col), life: o.life ?? 400, fn: def.custom };
  if (def.init) def.init(e);
  if (def.spawnOnly) return e;   // emitters (bursts) only spawn particles
  FAT.fx.push(e); return e;
}
function fatPart(p) { if (FAT.parts.length > 260) FAT.parts.shift(); FAT.parts.push(p); return p; }
const fatSpark = (x, y, vx, vy, col, life, gr) => { if (typeof feelSpark === 'function') feelSpark(x, y, vx, vy, col, life, gr); else fatPart({ k: 'spark', x, y, vx, vy, col, life, max: life, g: gr }); };

const FATFX = {
  // a huge translucent blade silhouette swung round a pivot (default: the shoulder, following the player).
  // keys: [[ms, angle, alpha, ease], ...] (facing-space degrees: 0 forward, -90 up, 90 down); len (px from r0), w, r0,
  // floor (clip at the feet line), ghosts (outline copies along the recent arc), fade (ms)
  auraBlade: {
    init(e) {
      const o = e.o; e.o = { anchor: 'player', dy: -19, follow: true, ...o }; e.keys = o.keys || [[0, o.a0 ?? -120, 1], [o.dur ?? 120, o.a1 ?? 60, 1, 'snap']];
      e.life = o.life ?? (e.keys[e.keys.length - 1][0] + (o.hold ?? 0)); e.hist = [];
    },
    at(e, t) {
      const K = e.keys; if (t <= K[0][0]) return { a: K[0][1], al: K[0][2] ?? 1 };
      for (let i = 1; i < K.length; i++) if (t <= K[i][0]) { const k = fatEase(K[i][3] || 'inout', (t - K[i - 1][0]) / Math.max(1, K[i][0] - K[i - 1][0])); return { a: lerp(K[i - 1][1], K[i][1], k), al: lerp(K[i - 1][2] ?? 1, K[i][2] ?? 1, k) }; }
      const L = K[K.length - 1]; return { a: L[1], al: L[2] ?? 1 };
    },
    update(e) { const s = this.at(e, e.t); e.hist.unshift(s.a); if (e.hist.length > 7) e.hist.pop(); },
    glow(e) {
      const o = e.o, s = this.at(e, e.t), fade = o.fade ? clamp((e.life - e.t) / o.fade, 0, 1) : 1, al = s.al * fade * (o.a ?? 1);
      if (al <= 0.01) return;
      const len = o.len ?? 58, w = o.w ?? 7, r0 = o.r0 ?? 5, clipY = o.floor === false ? undefined : Math.round(e.F.y0 + (o.floorDy || 0));
      const blade = (deg, a, fill) => {
        const r = fatAng(deg, e.face), ux = Math.cos(r), uy = Math.sin(r), nx = -uy, ny = ux;
        const P0 = [e.x + ux * r0, e.y + uy * r0], M = [e.x + ux * (r0 + len * 0.22), e.y + uy * (r0 + len * 0.22)], T = [e.x + ux * (r0 + len), e.y + uy * (r0 + len)];
        const hw = w / 2, mw = w * 0.58;
        const pts = [[P0[0] - nx * hw, P0[1] - ny * hw], [M[0] - nx * mw, M[1] - ny * mw], T, [M[0] + nx * mw, M[1] + ny * mw], [P0[0] + nx * hw, P0[1] + ny * hw]];
        if (fill) { g.fillStyle = `rgba(${e.col},${0.34 * a})`; fatPoly(pts, clipY); g.fillStyle = `rgba(${fatLite(e.col)},${0.16 * a})`; fatPoly(pts.map(q => [lerp(P0[0] + ux * len * 0.45, q[0], 0.55), lerp(P0[1] + uy * len * 0.45, q[1], 0.55)]), clipY); }
        g.fillStyle = `rgba(${fatLite(e.col)},${0.85 * a})`;
        fatLine(pts[0][0], pts[0][1], pts[1][0], pts[1][1], clipY); fatLine(pts[1][0], pts[1][1], T[0], T[1], clipY);
        fatLine(pts[4][0], pts[4][1], pts[3][0], pts[3][1], clipY); fatLine(pts[3][0], pts[3][1], T[0], T[1], clipY);
        if (fill) {
          g.fillStyle = `rgba(${fatHot(e.col)},${0.75 * a})`;   // the fuller
          fatLine(P0[0] + ux, P0[1] + uy, P0[0] + ux * len * 0.82, P0[1] + uy * len * 0.82, clipY);
          g.fillStyle = `rgba(${fatLite(e.col)},${0.7 * a})`;   // the guard
          fatLine(P0[0] - nx * w * 1.2, P0[1] - ny * w * 1.2, P0[0] + nx * w * 1.2, P0[1] + ny * w * 1.2, clipY);
        }
        return T;
      };
      if (o.ghosts !== 0) for (let i = e.hist.length - 1; i >= 1; i--) if (Math.abs(e.hist[i] - s.a) > 4) blade(e.hist[i], al * 0.4 * (1 - i / e.hist.length), false);
      const T = blade(s.a, al, true);
      if (T[1] <= (clipY ?? 1e9)) { if (typeof mvStar === 'function') mvStar(T[0], T[1], 3, fatHot(e.col), al); }
      addLight(e.x + (T[0] - e.x) * 0.5, e.y + (T[1] - e.y) * 0.5, 60, e.col, 0.45 * al);
    },
  },
  // a long thin line of light across a large span: draws in (grow), holds (hold), then bursts into pale light (burst)
  // o: len, ang (deg, 0 = level), grow, hold, burst, thick, sparks, from ('back' grows from behind the player's side)
  slashLine: {
    init(e) { const o = e.o; e.g = o.grow ?? 70; e.h = o.hold ?? 380; e.b = o.burst ?? 260; e.life = e.g + e.h + e.b; e.len = o.len ?? 340; e.fired = false; },
    ends(e) { const r = (e.o.ang || 0) * Math.PI / 180, ux = Math.cos(r) * e.face, uy = Math.sin(r), L = e.len / 2; return [e.x - ux * L, e.y - uy * L, e.x + ux * L, e.y + uy * L]; },
    update(e) {
      if (!e.fired && e.t >= e.g + e.h) {
        e.fired = true; const [x0, y0, x1, y1] = this.ends(e), n = e.o.sparks ?? 22;
        for (let i = 0; i < n; i++) { const k = Math.random(), x = lerp(x0, x1, k), y = lerp(y0, y1, k); fatSpark(x, y, (Math.random() - 0.5) * 60, -40 - Math.random() * 120 * (Math.random() < 0.5 ? 1 : -0.6), i % 2 ? fatHot(e.col) : e.col, 0.25 + Math.random() * 0.25, 120); }
        addLight(e.x, e.y, 140, e.col, 0.8);
      }
    },
    glow(e) {
      const [x0, y0, x1, y1] = this.ends(e), th = e.o.thick ?? 1;
      if (e.t < e.g + e.h) {
        const k = fatEase('snap', e.t / e.g), xe = lerp(x0, x1, k), ye = lerp(y0, y1, k), fl = e.t > e.g ? 0.85 + 0.15 * Math.sin(e.t * 0.08) : 1;
        g.fillStyle = `rgba(${e.col},${0.45 * fl})`; fatLine(x0, y0 - 1 - (th > 1 ? 1 : 0), xe, ye - 1 - (th > 1 ? 1 : 0)); fatLine(x0, y0 + 1 + (th > 1 ? 1 : 0), xe, ye + 1 + (th > 1 ? 1 : 0));
        g.fillStyle = `rgba(${fatHot(e.col)},${fl})`; fatLine(x0, y0, xe, ye); if (th > 1) { fatLine(x0, y0 - 1, xe, ye - 1); fatLine(x0, y0 + 1, xe, ye + 1); }
        if (typeof mvStar === 'function') mvStar(xe, ye, 4, fatHot(e.col), 1);
        addLight(e.x, e.y, 100, e.col, 0.45);
        return;
      }
      // burst: the line widens, breaks into segments that drift apart and dissolve
      const k = (e.t - e.g - e.h) / e.b, dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L, nx = -uy, ny = ux;
      const n = Math.ceil(L / 12), w = 1 + Math.round(3 * (1 - k) * (k < 0.25 ? k / 0.25 : 1));
      for (let i = 0; i < n; i++) {
        const s0 = i * 12, s1 = s0 + 12 * (1 - k * 0.8), off = (fatHash(i, e.F.n) - 0.5) * 22 * k, a = (1 - k);
        if (fatHash(i * 7, 3) < k * 0.9) continue;
        const ax = x0 + ux * s0 + nx * off, ay = y0 + uy * s0 + ny * off, bx = x0 + ux * s1 + nx * off, by = y0 + uy * s1 + ny * off;
        g.fillStyle = `rgba(${fatLite(e.col)},${0.6 * a})`; for (let j = 1; j < w; j++) { fatLine(ax + nx * j, ay + ny * j, bx + nx * j, by + ny * j); fatLine(ax - nx * j, ay - ny * j, bx - nx * j, by - ny * j); }
        g.fillStyle = `rgba(${fatHot(e.col)},${a})`; fatLine(ax, ay, bx, by);
      }
      addLight(e.x, e.y, 120 * (1 - k) + 20, e.col, 0.6 * (1 - k));
    },
  },
  // a big arc smear round a pivot: sweeps open from a0 (tail) to a1 (head) in `grow`, lingers, then shatters to shards
  // o: r, thick, a0, a1 (facing-space deg), sq (y squash), grow, linger, shatter, shards
  crescent: {
    init(e) {
      const o = e.o; e.o = { anchor: 'player', dy: -19, ...o }; const p = fatAnchor(e.F, e.o); e.x = p.x; e.y = p.y;
      e.gr = o.grow ?? 80; e.li = o.linger ?? 420; e.sh = o.shatter ?? 320; e.life = e.gr + e.li + e.sh; e.shards = null;
      e.r = o.r ?? 60; e.th = o.thick ?? 16; e.a0 = o.a0 ?? -130; e.a1 = o.a1 ?? 60; e.sq = o.sq ?? 1;
    },
    update(e, dt) {
      if (!e.shards && e.t >= e.gr + e.li) {
        e.shards = []; const n = e.o.shards ?? 24, R = fatRng(e.F.n * 31 + 7);
        for (let i = 0; i < n; i++) {
          const u = 0.15 + R() * 0.85, a = fatAng(lerp(e.a0, e.a1, u), e.face), rr = e.r - R() * e.th * 0.8;
          const x = e.x + Math.cos(a) * rr, y = e.y + Math.sin(a) * rr * e.sq, sp = 30 + R() * 70;
          e.shards.push({ x, y, vx: Math.cos(a) * sp + (R() - 0.5) * 30, vy: Math.sin(a) * sp * e.sq - 20 - R() * 30, s: 1 + Math.floor(R() * 3), r: R() * 6, vr: (R() - 0.5) * 12 });
        }
        for (let i = 0; i < 10; i++) { const a = fatAng(lerp(e.a0, e.a1, Math.random()), e.face); fatSpark(e.x + Math.cos(a) * e.r, e.y + Math.sin(a) * e.r * e.sq, Math.cos(a) * 120, Math.sin(a) * 120, fatHot(e.col), 0.22, 160); }
        addLight(e.x, e.y, e.r * 1.6, e.col, 0.6);
      }
      if (e.shards) for (const s of e.shards) { s.vy += 160 * dt; s.x += s.vx * dt; s.y += s.vy * dt; s.r += s.vr * dt; s.vx *= Math.pow(0.4, dt); }
    },
    glow(e) {
      const pal = [null, `rgba(${fatHot(e.col)},0.95)`, `rgba(${fatLite(e.col)},0.75)`, `rgba(${e.col},0.5)`];
      if (!e.shards) {
        const grow = fatEase('snap', e.t / e.gr), fade = e.t > e.gr ? 1 - (e.t - e.gr) / e.li * 0.45 : 1;
        const cur = grow, span = e.a1 - e.a0, mid = (e.a0 + e.a1) / 2, R = e.r, f = e.face, cx = e.x, cy = e.y, th = e.th, sq = e.sq, clipY = e.o.floor ? e.F.y0 : 1e9;
        fatRaster(cx - R - 1, cy - R * sq - 1, cx + R + 1, Math.min(cy + R * sq + 1, clipY), (x, y) => {
          const ex = (x + 0.5 - cx) * f, ey = (y + 0.5 - cy) / sq, rho = Math.hypot(ex, ey); if (rho > R + 0.6 || rho < R - th - 1) return 0;
          let th0 = Math.atan2(ey, ex) * 57.2958; while (th0 - mid > 180) th0 -= 360; while (th0 - mid < -180) th0 += 360;
          const u = (th0 - e.a0) / span; if (u < 0 || u > cur) return 0;
          const uu = cur > 0 ? u / cur : 0, w = th * (uu < 0.85 ? Math.pow(uu / 0.85, 0.85) : 1 - (uu - 0.85) / 0.15 * 0.45), d = R - rho;
          if (d < -0.6 || d > w) return 0;
          if (uu < 0.3 && !fatDith(x, y, uu / 0.3 * 0.9 * fade)) return 0;
          if (!fatDith(x, y, fade + 0.15)) return 0;
          return d < 1.1 ? 1 : d < w * 0.42 ? 2 : 3;
        }, pal);
        addLight(cx, cy, R * 1.3, e.col, 0.4 * fade);
        return;
      }
      const k = (e.t - e.gr - e.li) / e.sh;
      for (const s of e.shards) {
        if (!fatDith(Math.round(s.x), Math.round(s.y), 1 - k)) continue;
        const c = Math.cos(s.r), sn = Math.sin(s.r), z = s.s + 0.5;
        g.fillStyle = s.s > 1 ? `rgba(${fatLite(e.col)},${0.9 * (1 - k)})` : `rgba(${fatHot(e.col)},${1 - k})`;
        fatPoly([[s.x + c * z, s.y + sn * z], [s.x - sn * z * 0.6, s.y + c * z * 0.6], [s.x - c * z, s.y - sn * z]]);
        g.fillRect(Math.round(s.x), Math.round(s.y), 1, 1);
      }
    },
  },
  // expanding rings: o: r0, r1, dur, rings, gap (ms), sq (0.25 = flat ground ring), thick (1 | 2)
  shockwave: {
    init(e) { const o = e.o; e.n = o.rings ?? 2; e.gap = o.gap ?? 90; e.d = o.dur ?? 420; e.life = e.d + (e.n - 1) * e.gap; },
    glow(e) {
      const o = e.o, sq = o.sq ?? 1, r0 = o.r0 ?? 4, r1 = o.r1 ?? 90, clip = sq < 0.6 ? undefined : undefined;
      for (let i = 0; i < e.n; i++) {
        const t = e.t - i * e.gap; if (t < 0 || t > e.d) continue;
        const k = t / e.d, r = lerp(r0, r1 * (1 - i * 0.18), fatEase('snap', k)), a = (1 - k) * (i ? 0.7 : 1);
        g.fillStyle = `rgba(${fatHot(e.col)},${a})`; fatEllipse(e.x, e.y, r, r * sq, clip);
        if ((o.thick ?? 2) > 1) { g.fillStyle = `rgba(${e.col},${a * 0.6})`; fatEllipse(e.x, e.y, Math.max(1, r - 1.5), Math.max(1, (r - 1.5) * sq), clip); }
      }
      addLight(e.x, e.y, (o.r1 ?? 90) * 0.7, e.col, 0.35 * (1 - e.t / e.life));
    },
  },
  // molten cracks running along the floor from the anchor: o: len (each side), branches, dur, both, col (default ember)
  groundCrack: {
    init(e) {
      const o = e.o; e.o = { anchor: 'ground', ...o }; const p = fatAnchor(e.F, e.o); e.x = Math.round(p.x); e.y = Math.round(p.y);
      e.life = o.dur ?? 1100; e.col = fatRGB(o.col || '255,150,60'); const R = fatRng(e.F.n * 13 + Math.round(e.x)), L = o.len ?? 60;
      e.lines = [];
      for (const sd of (o.both === false ? [e.face] : [-1, 1])) {
        let x = e.x, y = e.y + 1, d = 0; const pts = [[x, y, 0]];
        while (d < L) { const st = 3 + Math.floor(R() * 5); x += sd * st; d += st; y = clamp(y + (R() < 0.4 ? (R() < 0.5 ? 1 : -1) : 0), e.y + 1, e.y + 5); pts.push([x, y, d / L]);
          if (R() < (o.branches ?? 5) / 14) { let bx = x, by = y; const bp = [[bx, by, d / L]]; for (let j = 0; j < 3; j++) { bx += sd * (1 + Math.floor(R() * 3)); by += 1 + Math.floor(R() * 2); bp.push([bx, by, d / L + j * 0.05]); } e.lines.push(bp); } }
        e.lines.push(pts);
      }
    },
    draw(e, glow) {
      const k = e.t / e.life, reveal = clamp(e.t / 140, 0, 1), cool = clamp((e.t - 200) / (e.life - 200), 0, 1);
      for (const pts of e.lines) for (let i = 1; i < pts.length; i++) {
        const [ax, ay, ad] = pts[i - 1], [bx, by] = pts[i]; if (ad > reveal) break;
        if (glow) { if (cool >= 1) continue; g.fillStyle = `rgba(${cool < 0.35 ? fatHot(e.col) : e.col},${(1 - cool) * (1 - ad * 0.5)})`; fatLine(ax, ay, bx, by); }
        else { if (!fatDith(ax, ay, 1 - k * k)) continue; g.fillStyle = 'rgba(14,10,10,0.85)'; fatLine(ax, ay + 1, bx, by + 1); }
      }
      if (glow) addLight(e.x, e.y, 50, e.col, 0.45 * (1 - cool));
    },
    glow(e) { this.draw(e, true); }, lit(e) { this.draw(e, false); },
  },
  // a pillar of light from the anchor's floor up past the top of the view: o: w, h, grow, dur
  pillar: {
    init(e) { const o = e.o; e.o = { anchor: 'ground', ...o }; const p = fatAnchor(e.F, e.o); e.x = p.x; e.y = p.y; e.life = o.dur ?? 600; },
    glow(e) {
      const o = e.o, gr = o.grow ?? 70, k = e.t / e.life, top = Math.min(e.y - (o.h ?? 400), cam.y - 8);
      const wk = e.t < gr ? fatEase('snap', e.t / gr) : 1 - fatEase('in', (e.t - gr) / (e.life - gr)) * 0.92, w = Math.max(1, (o.w ?? 16) * wk), a = e.t < gr ? 1 : 1 - k * 0.6;
      const x0 = Math.round(e.x - w / 2), x1 = Math.round(e.x + w / 2), H = e.y - top;
      for (let x = x0; x <= x1; x++) {
        const d = Math.abs(x + 0.5 - e.x) / (w / 2 + 0.5), c = d < 0.2 ? fatHot(e.col) : d < 0.55 ? fatLite(e.col) : e.col;
        if (d >= 0.55 && !fatDith(x, 0, 0.6)) continue;
        g.fillStyle = `rgba(${c},${a * (d < 0.55 ? 0.9 : 0.5)})`; g.fillRect(x, Math.round(top + H * 0.25), 1, Math.round(H * 0.75));
        for (let y = Math.round(top); y < top + H * 0.25; y++) if (fatDith(x, y, (y - top) / (H * 0.25))) g.fillRect(x, y, 1, 1);
      }
      addLight(e.x, e.y - 20, 80, e.col, 0.7 * a); addLight(e.x, e.y - 90, 60, e.col, 0.4 * a);
    },
  },
  // emitters: o.n, o.spd, o.dir (deg, facing space) + o.arc (deg) for a cone, o.col
  sparkBurst: { spawnOnly: true, init(e) {
    const o = e.o, n = o.n ?? 16, spd = o.spd ?? 170;
    for (let i = 0; i < n; i++) { const a = o.dir !== undefined ? fatAng(o.dir + (Math.random() - 0.5) * (o.arc ?? 90), e.face) : Math.random() * 6.2832, v = spd * (0.4 + Math.random() * 0.6); fatSpark(e.x, e.y, Math.cos(a) * v, Math.sin(a) * v, i % 3 ? e.col : fatHot(e.col), 0.14 + Math.random() * 0.2, 260); }
  } },
  emberBurst: { spawnOnly: true, init(e) {
    const o = e.o, n = o.n ?? 14, c = fatRGB(o.col || fatMix(e.col, '255,140,50', 0.5));
    for (let i = 0; i < n; i++) fatPart({ k: 'ember', x: e.x + (Math.random() - 0.5) * (o.w ?? 24), y: e.y - Math.random() * (o.h ?? 10), vx: (Math.random() - 0.5) * (o.spd ?? 60), vy: -20 - Math.random() * (o.rise ?? 70), col: c, life: 0.6 + Math.random() * 0.7, max: 1.3, g: -10, ph: Math.random() * 6 });
  } },
  // wisps that rise out of the anchor and stream into a destination: o.to = 'tip' | 'player' | 'target' | fn(F) -> {x, y};
  // o.from = 'target' (random points in the hurtbox, default) | 'ring' (a ring of radius o.r round the anchor: a gathering)
  soulWisps: { spawnOnly: true, init(e) {
    const o = e.o, n = o.n ?? 8, F = e.F, hb = fatHB(F);
    for (let i = 0; i < n; i++) {
      let x, y;
      if (o.from === 'ring') { const a = Math.random() * 6.2832, r = (o.r ?? 40) * (0.7 + Math.random() * 0.3); x = e.x + Math.cos(a) * r; y = e.y + Math.sin(a) * r * 0.7; }
      else { x = lerp(hb.x0, hb.x1, Math.random()); y = lerp(hb.y0, hb.y1, 0.2 + Math.random() * 0.6); }
      fatPart({ k: 'wisp', x, y, vx: (Math.random() - 0.5) * 20, vy: -10 - Math.random() * 20, col: e.col, life: (o.dur ?? 800) / 1000, max: (o.dur ?? 800) / 1000, delay: i * (o.stagger ?? 30) / 1000, rise: (o.rise ?? 260) / 1000, to: o.to || 'tip', F, trail: [], ph: Math.random() * 6 });
    }
  } },
  // player ghosts: one now, or a trail (o.dur ms, every o.every ms)
  afterimage: { spawnOnly: true, init(e) {
    const o = e.o, col = o.col || `rgb(${fatLite(e.col)})`;
    if (o.dur) e.F.ghost = { until: e.F.t + o.dur, every: o.every || 35, last: -1e9, col, life: o.life || 0.3, alpha: o.alpha || 0.5 };
    else if (typeof mvAfterimage === 'function') mvAfterimage(col, o.life || 0.3, o.alpha || 0.55);
  } },
  // streaks rushing past (opposite to the facing, or o.dir): o.n, o.dur, o.band ([y0, y1] relative to the anchor), o.len
  speedLines: {
    init(e) { const o = e.o; e.o = { anchor: 'player', ...o }; e.life = o.dur ?? 260; const R = fatRng(e.F.n * 7 + 3), b = o.band || [-40, 4];
      e.lines = []; for (let i = 0; i < (o.n ?? 12); i++) e.lines.push({ y: b[0] + R() * (b[1] - b[0]), x: (R() - 0.3) * 260, l: 14 + R() * 40, v: 500 + R() * 400, d: R() * 0.3 }); },
    glow(e) {
      const dir = -(e.o.dir ?? e.face), k = e.t / e.life;
      for (const L of e.lines) { const t = e.t / 1000 - L.d; if (t < 0) continue; const x = Math.round(e.x + (L.x + dir * L.v * t)), y = Math.round(e.y + L.y);
        g.fillStyle = `rgba(${fatLite(e.col)},${0.7 * (1 - k)})`; g.fillRect(dir > 0 ? x - L.l : x, y, Math.round(L.l), 1); }
    },
  },
  // a bright 4-point star burst at the anchor: o.r, o.dur
  impactFlash: {
    init(e) { e.life = e.o.dur ?? 160; },
    glow(e) {
      const k = e.t / e.life, r = (e.o.r ?? 30) * (1 - k * 0.6), a = 1 - k, x = Math.round(e.x), y = Math.round(e.y);
      g.fillStyle = `rgba(${fatHot(e.col)},${a})`; g.fillRect(x - Math.round(r), y, Math.round(r) * 2 + 1, 1); g.fillRect(x, y - Math.round(r * 0.7), 1, Math.round(r * 1.4) + 1);
      g.fillStyle = `rgba(${fatLite(e.col)},${a * 0.8})`; const d = Math.round(r * 0.3); fatLine(x - d, y - d, x + d, y + d); fatLine(x - d, y + d, x + d, y - d);
      const c = Math.max(1, Math.round(4 * (1 - k))); g.fillStyle = `rgba(255,255,255,${a})`; fatPoly([[x + 0.5, y - c + 0.5], [x + c + 0.5, y + 0.5], [x + 0.5, y + c + 0.5], [x - c + 0.5, y + 0.5]]);
      addLight(x, y, (e.o.r ?? 30) * 2.2, e.col, 0.9 * a);
    },
  },
};
const fatFxNames = () => Object.keys(FATFX);

// ---- per-frame: effects, particles, the cinematic values
// while a fatality plays, a hit only pulses the target pale (flash <= 0.28) instead of turning it solid white: the
// fatality's own effects carry the impact, and the boss's white silhouette used to swallow them (v16 demo review)
const FAT_FLASH_CAP = 0.28;
HOOKS.update.push(() => {
  const F = FAT.on; if (!F) return;
  for (const t of [F.target, F.owner].concat(F.owner && F.owner.parts || [])) if (t && t.flash > FAT_FLASH_CAP) t.flash = FAT_FLASH_CAP;
});
HOOKS.update.push(dt => {
  const ms = dt * 1000;
  for (const e of FAT.fx) {
    e.t += ms;
    if (e.o.follow) { const p = fatAnchor(e.F, e.o); e.x = p.x; e.y = p.y; }
    const def = FATFX[e.k]; if (def && def.update) def.update(e, dt);
  }
  if (FAT.fx.length) FAT.fx = FAT.fx.filter(e => e.t < e.life);
  for (const p of FAT.parts) {
    if (p.delay > 0) { p.delay -= dt; continue; }
    p.life -= dt;
    if (p.k === 'wisp') {
      const age = p.max - p.life; p.trail.unshift([p.x, p.y]); if (p.trail.length > 6) p.trail.pop();
      if (age < p.rise) { p.vy -= 40 * dt; p.x += (p.vx + Math.sin(time * 9 + p.ph) * 18) * dt; p.y += p.vy * dt; }
      else {
        const d = typeof p.to === 'function' ? p.to(p.F) : p.to === 'player' ? { x: P.x, y: P.y - 16 } : p.to === 'target' ? fatTC(p.F) : p.F.tip();
        const dx = d.x - p.x, dy = d.y - p.y, L = Math.hypot(dx, dy) || 1, sp = 120 + (age - p.rise) * 600;
        if (L < 4) { p.life = 0; fatSpark(d.x, d.y, (Math.random() - 0.5) * 60, -40, fatHot(p.col), 0.15, 0); continue; }
        p.x += dx / L * Math.min(L, sp * dt); p.y += dy / L * Math.min(L, sp * dt);
      }
    } else { p.vy += (p.g || 0) * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.vx *= Math.pow(0.5, dt); }
  }
  if (FAT.parts.length) FAT.parts = FAT.parts.filter(p => p.life > 0);
  // cinematic layers ease toward the running fatality's targets (or out to 0)
  const F = FAT.on, C = FAT.cine, out = !F || F.t > F.dur - 200;
  const want = k => (out ? 0 : F.cine[k] || 0), rate = (k, v) => { const w = want(k); C[k] = approach(C[k], w, dt * (w > C[k] ? v : 3.2)); };
  rate('bars', 6.5); rate('dark', 5); rate('vig', 5); rate('zoom', 4);
  C.flash = Math.max(0, C.flash - dt * 3.2); C.kick = Math.max(0, C.kick - dt * 2.6);
  if (!F && C.dark <= 0 && FAT.dimmed.length) fatUndim();
  // can't be hurt, can't be interrupted
  if (F) {
    if (P.hp < F.hp0) P.hp = F.hp0;
    fatHoldTick(F, dt);
    if (P.state !== 'fatality' && P.state !== 'dead') { setP('fatality', F.seg ? F.seg.tag : 'idle', false, 0); fatAnimFrame(F); }
    addLight(P.x, P.y - 16, 40, F.col, 0.3);
  }
});
HOOKS.enter.push(() => { fatAbort(); FAT.fx = []; FAT.parts = []; fatUndim(); Object.assign(FAT.cine, { bars: 0, dark: 0, vig: 0, flash: 0, zoom: 0, kick: 0, name: null }); });

// ---- drawing
HOOKS.renderMid.push(() => {   // world space, after the terrain and props, before any body
  const k = FAT.cine.dark; if (k < 0.01) return;
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over';
  g.fillStyle = `rgba(4,3,8,${(k * 0.92).toFixed(3)})`; g.fillRect(0, 0, W, H); g.restore();
  if (typeof LX !== 'undefined' && LX.on) { gFx.save(); gFx.setTransform(1, 0, 0, 1, 0, 0); gFx.globalCompositeOperation = 'destination-out'; gFx.fillStyle = `rgba(0,0,0,${k.toFixed(3)})`; gFx.fillRect(0, 0, W, H); gFx.restore(); }
});
HOOKS.render.push(() => {   // world space, after the bodies: the effects (lit parts first, then the glow layer)
  if (!P) return;
  for (const e of FAT.fx) { const d = FATFX[e.k]; if (d && d.lit) d.lit(e); }
  const F = FAT.on;
  if (F && F.def.drawLit) try { F.def.drawLit(F, F.t); } catch (err) { console.error(err); }
  if (!FAT.fx.length && !FAT.parts.length && !F) return;
  drawGlow(() => {
    const op = g.globalCompositeOperation; g.globalCompositeOperation = 'lighter';
    try {
      for (const e of FAT.fx) {
        if (e.fn) { try { e.fn(g, e.t, e.F, e); } catch (err) { console.error(err); } continue; }
        const d = FATFX[e.k]; if (d && d.glow) d.glow(e);
      }
      for (const p of FAT.parts) {
        if (p.delay > 0) continue;
        const a = clamp(p.life / (p.max * 0.4), 0, 1);
        if (p.k === 'wisp') {
          for (let i = p.trail.length - 1; i >= 1; i--) { g.fillStyle = `rgba(${p.col},${a * 0.5 * (1 - i / p.trail.length)})`; g.fillRect(Math.round(p.trail[i][0]), Math.round(p.trail[i][1]), 1, 1); }
          g.fillStyle = `rgba(${fatHot(p.col)},${a})`; g.fillRect(Math.round(p.x), Math.round(p.y), 1, 1); g.fillStyle = `rgba(${p.col},${a * 0.5})`; g.fillRect(Math.round(p.x) - 1, Math.round(p.y), 3, 1);
        } else if (p.k === 'ember') {
          if (Math.sin(time * 20 + p.ph) < -0.6) continue;
          g.fillStyle = `rgba(${p.col},${a})`; g.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
        } else { g.fillStyle = `rgba(${p.col},${a})`; g.fillRect(Math.round(p.x), Math.round(p.y), 1, 1); }
      }
      if (F && F.def.draw) F.def.draw(F, F.t);
    } catch (err) { console.error(err); } finally { g.globalCompositeOperation = op; }
  });
});
HOOKS.renderTop.push(() => {   // screen space, over the lit scene: letterbox, coloured vignette, the colour flash
  const C = FAT.cine; if (C.bars < 0.01 && C.vig < 0.01 && C.flash < 0.01) return;
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1;
  const col = C.col;
  if (C.vig > 0.01) {
    const vg = g.createRadialGradient(W / 2, H / 2, 70, W / 2, H / 2, 230);
    vg.addColorStop(0, `rgba(${fatDeep(col)},0)`); vg.addColorStop(1, `rgba(${fatDeep(col)},${(0.55 * C.vig).toFixed(3)})`);
    g.fillStyle = vg; g.fillRect(0, 0, W, H);
  }
  if (C.flash > 0.01) { g.globalCompositeOperation = 'lighter'; g.fillStyle = `rgba(${col},${(C.flash * 0.42).toFixed(3)})`; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over'; }
  if (C.bars > 0.01) {
    const h = Math.round(17 * fatEase('out', C.bars));
    g.fillStyle = '#030206'; g.fillRect(0, 0, W, h); g.fillRect(0, H - h, W, h);
    g.fillStyle = `rgba(${col},${(0.28 * C.bars).toFixed(3)})`; g.fillRect(0, h, W, 1); g.fillRect(0, H - h - 1, W, 1);
  }
  g.restore();
});
HOOKS.hud.push(() => {   // the fatality's name, in the title font, under the top bar
  const c = FAT.cine.name; if (!c) return;
  const t = time - c.t0, a = clamp(Math.min(t / 0.22, (c.life - t) / 0.55), 0, 1);
  if (t > c.life) { FAT.cine.name = null; return; }
  const nm = c.text.toUpperCase(), sp = 2.2 + 1.2 * clamp(t / c.life, 0, 1), size = 9, y = 38, hi = fatMix(c.col, '255,244,220', 0.6);
  text(nm, W / 2, y, size, `rgb(${hi})`, 'center', { alpha: a * 0.95, spacing: sp, weight: 500 });
  const tw = (textW(nm, size, 500) + nm.length * sp) / 2 + 6, lw = 44 * clamp(t * 3, 0, 1);
  if (typeof uiFade === 'function') { uiFade(W / 2 + tw, W / 2 + tw + lw, y - 3.2, hi, 0.75 * a); uiFade(W / 2 - tw, W / 2 - tw - lw, y - 3.2, hi, 0.75 * a); }
  if (typeof uiDiamond === 'function') { uiDiamond(W / 2 + tw - 2, y - 3, 1.2, `rgb(${hi})`, a); uiDiamond(W / 2 - tw + 2, y - 3, 1.2, `rgb(${hi})`, a); }
});
// camera punch-in: the finished world image (before the HUD) is re-blitted a few % larger round the action
{
  const _pw = presentWorld;
  presentWorld = function () {
    _pw.apply(this, arguments);
    const C = FAT.cine, z = FAT.zoomAmt * clamp(C.zoom * 0.45 + C.kick * 0.55, 0, 1) * (typeof feelShake === 'function' ? feelShake() : 1);
    if (z < 0.003 || !P || typeof state === 'undefined' || state !== 'play') return;
    const F = FAT.on, tc = F ? fatTC(F) : null, mx = tc ? (P.x + tc.x) / 2 : P.x, my = tc ? (P.y - 20 + tc.y) / 2 : P.y - 20;
    const k = 1 + z, w = W * scale, h = H * scale, sw = w / k, sh = h / k;
    const fx = clamp((mx - cam.x) / W, 0, 1), fy = clamp((my - cam.y) / H, 0, 1);
    const sx = clamp(ox + fx * w - fx * sw, ox, ox + w - sw), sy = clamp(oy + fy * h - fy * sh, oy, oy + h - sh);
    const sm = vctx.imageSmoothingEnabled; vctx.imageSmoothingEnabled = !!SETTINGS.shaders;
    try { vctx.drawImage(view, sx, sy, sw, sh, ox, oy, w, h); } finally { vctx.imageSmoothingEnabled = sm; }
  };
}
// the camera leans toward the midpoint of the player and the target while it plays
{
  const _uc = updateCamera;
  updateCamera = function (dt, snap) {
    _uc.apply(this, arguments);
    const F = FAT.on; if (!F || snap || !room) return;
    const c = fatTC(F), tx = clamp((P.x + c.x) / 2 - W / 2, 0, Math.max(0, room.pw - W)), ty = clamp(Math.min(P.y, c.floor) - 30 - H / 2 - 10, 0, Math.max(0, room.ph - H));
    cam.x += (tx - cam.x) * Math.min(1, dt * 5); cam.y += (ty - cam.y) * Math.min(1, dt * 3);
  };
}

// ================================================================== a K latched mid-move
// The move's own push can carry a staggered foe past the crit range before the move ends (the spear's thrust slides it
// ~20 px), so the latched K would play the type's J -> K instead. A latched K reaches FAT_LATCH_PX further and steps in.
const FAT_LATCH_PX = 36;
function fatLatchTarget() {
  if (!P || !D || !P.ground || FAT.on || typeof state === 'undefined' || state !== 'play' || P.state === 'dead') return null;
  let best = null, bd = 1e9;
  for (const t of targets()) {
    if (!t.critable || !t.critable()) continue;
    const ad = Math.abs(t.x - P.x);
    if (ad >= (t.critRange || 34) + FAT_LATCH_PX || Math.abs(t.y - P.y) >= 30 || ad >= bd) continue;
    best = t; bd = ad;
  }
  return best;
}
function fatStepIn(t) {   // close inside the crit range (a quick step with an afterimage); false when a wall is in the way
  const r = (t.critRange || 34) - 8, dx = t.x - P.x; if (Math.abs(dx) < r + 8) return true;
  const dir = Math.sign(dx), goal = t.x - dir * r;
  for (let x = P.x; dir * (goal - x) > 0; x += dir * 2) if (solidAtPx(x + dir * 6, P.y - 6) || solidAtPx(x + dir * 6, P.y - 20)) return false;
  try { ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: 0.22, col: '#c8d0e8' }); } catch (e) {}
  P.x = goal; P.face = dir; return true;
}

// ================================================================== inputs (J keeps the riposte; K on a critable foe = the fatality)
{
  const _mvN = mvNeutral;   // the neutral K press (04_player's canStart block, '@K' routes)
  mvNeutral = function (ax) {
    if (peek('heavy') && !peek('attack') && fatReady()) { take('heavy'); return fatalityStart() || true; }
    return _mvN.apply(this, arguments);
  };
  const _mvNK = mvNeutralK;   // direct heavy starts (the guard's K, startHeavy)
  mvNeutralK = function () { if (fatReady() && fatalityStart()) return true; return _mvNK.apply(this, arguments); };
  const _mvGK = mvGuardK;     // the shield's own K (slam) out of the guard
  mvGuardK = function () { if (fatReady() && fatalityStart()) return true; return _mvGK.apply(this, arguments); };
  const _mvPU = mvParryUpdate;   // K out of a parry (a parried foe is critable): the fatality before the type's I -> K
  mvParryUpdate = function (dt, ax) { if (peek('heavy') && fatReady()) { take('heavy'); if (fatalityStart()) return true; } return _mvPU.apply(this, arguments); };
  // K pressed during a move: it latches even on a finisher and leads to the fatality when the move ends
  const _mvR = mvRouted;
  mvRouted = function (A, b) { if (b === 'K' && (fatReady() || fatLatchTarget())) return true; return _mvR.apply(this, arguments); };
  const _mvNx = mvNext;
  mvNext = function (A, q) {
    if (q && q.b === 'K' && !q.peek) { if (fatReady()) return '@K'; const t = fatLatchTarget(); if (t && fatStepIn(t)) return '@K'; }
    return _mvNx.apply(this, arguments);
  };
  // invulnerable throughout: nothing reaches the player (blows, projectiles, spikes, a killing blow)
  const _hp = hurtPlayer;
  hurtPlayer = function () { if (FAT.on) return false; return _hp.apply(this, arguments); };
  const _sp = spikeHurt;
  spikeHurt = function () { if (FAT.on) return; return _sp.apply(this, arguments); };
  const _kp = killPlayer;
  killPlayer = function () { if (FAT.on) { P.hp = Math.max(1, FAT.on.hp0); return false; } return _kp.apply(this, arguments); };
}

// ================================================================== Move List: a "Fatality" row in every type's combos
function fatMoveRows() {
  for (const ty of Object.keys(MV.types)) {
    const T = MV.types[ty]; if (!Array.isArray(T.combos)) T.combos = [];
    if (T.combos.some(c => c && c.fatality)) continue;
    T.combos.push({ fatality: true, rank: 1, name: 'Fatality', input: 'K on a staggered foe',
      get desc() { const d = FAT.defs[ty]; return `${d ? d.name : 'Last Rite'}: an execution, 5× on bosses, kills weak foes.`; } });
  }
}
fatMoveRows();
HOOKS.enter.push(fatMoveRows);   // types registered later still get the row

if (typeof window !== 'undefined' && window.__game) window.__game.fat = { FAT, FATFX, start: fatalityStart, register: fatalityRegister, ready: fatReady, def: fatDef };
