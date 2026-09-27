// ------------------------------------------------------------------ Expansion 3 kit systems (agent KS): doors & hidden passages,
// trials, gauntlets, vista benches, lore pages (the Hallow Chronicle), completion data. Placed from room files with
// spawns=[{t:'sys', kind:'door'|'passage'|'trial'|'trial_goal'|'gauntlet'|'bench'|'lore', x, y, ...}] — see docs/KIT_API.md § Systems.
// Save data lives under SAVE.x3 (created lazily so old saves load); per-object "done" state uses SAVE.flags['x3:<room>:<id>'].

const SYS = { trial: null, gaunt: null, vista: null, warp: null, reader: null, result: null, gBanner: null, reveal: null, portents: [],
              goals: {}, later: [], doorLock: null, relayer: false, watch: new Set(), watchT: 0, run: 0, duck: 0 };
const LORE_PAGES = {};   // id -> { region: '<biome>', title, text }   (region agents fill this; ids '<agent>_<n>')
// proving-room pages (test: true keeps them out of completion totals)
Object.assign(LORE_PAGES, {
  ks_1: { region: 'spire', test: true, title: 'The Proving Tablet', text: 'Cut into the tablet in a mason’s square hand:\n“Every road in the Hallow was once a door. We only forgot which ones.”' },
  ks_2: { region: 'spire', test: true, title: 'A View Kept for the Weary', text: 'Someone carved a bench here and set it facing the long hall, so the tired could look at how far they had come instead of how far was left.\nThe seat is worn in two places, side by side.' },
  ks_3: { region: 'spire', test: true, title: 'Behind the Sealed Stone', text: 'A pilgrim’s last page, folded small:\n“They walled the chapel up when the storm came. I rested at the shrine and waited, and the wall remembered me. It opened on its own. Tell the others the stone is patient.”' },
});
function x3() {
  const X = SAVE.x3 || (SAVE.x3 = {});
  for (const k of ['t', 'trials', 'vistas', 'lore', 'gaunt', 'seen']) X[k] = X[k] || {};
  return X;
}
const sysKey = (rid, id) => `x3:${rid}:${id}`;
const SYS_SKINS = ['stone', 'wood', 'metal', 'crystal', 'neon'];
const SYS_BIOME_SKIN = { ramparts: 'stone', catacombs: 'stone', cathedral: 'stone', mire: 'wood', crown: 'stone', archives: 'wood', hoarfrost: 'crystal',
  spire: 'stone', deep: 'metal', hermit: 'wood', ember: 'metal', thornveil: 'wood', barrows: 'stone', crimson: 'wood', necropolis: 'stone', dunes: 'stone',
  starfall: 'crystal', neohallow: 'neon', lastfield: 'wood' };
const SYS_GLOW = { stone: '255,200,120', wood: '255,184,104', metal: '255,146,72', crystal: '150,205,255', neon: '90,230,255' };
function sysSkin(s, def) { return SYS_SKINS.includes(s.skin) ? s.skin : SYS_BIOME_SKIN[def.biome] || (def.biome && def.biome.startsWith('neohallow') ? 'neon' : 'stone'); }
ICON_SHEETS.push('sys_icons', 'sys_micons');
Object.assign(PCOL, { x3_seed: '246,226,160', x3_wheat: '232,196,110', x3_rune: '255,214,130', x3_neon: '110,230,255' });
const sysSfx = {
  chime: (k = 1) => [784, 1175, 1568].forEach((f, i) => tone(f * k, 1.6, 0.06, 'triangle', 1, i * 0.11)),
  creak: () => { noise(0.5, 700, 1.2, 0.18, 'bandpass', 0.45); tone(92, 0.35, 0.12, 'sine', 0.7, 0.3); },
  hatch: () => { noise(0.18, 420, 0.8, 0.3, 'lowpass'); tone(70, 0.3, 0.2, 'square', 0.6, 0.05); },
  ladder: () => [0, 0.14, 0.28].forEach(d => setTimeout(() => noise(0.06, 900, 1, 0.12, 'bandpass'), d * 1000)),
  portal: () => { tone(220, 0.8, 0.07, 'sine', 3); tone(330, 0.8, 0.05, 'triangle', 2.5, 0.05); noise(0.7, 2200, 0.6, 0.15, 'bandpass', 0.3); },
  rewind: () => { tone(1320, 0.22, 0.07, 'triangle', 0.25); noise(0.2, 2600, 0.8, 0.18, 'bandpass', 0.3); },
  begin: () => { [392, 523, 784].forEach((f, i) => tone(f, 1.4, 0.07, 'sine', 1, i * 0.06)); noise(0.5, 3000, 0.5, 0.08, 'highpass'); },
  done: () => [523, 659, 784, 1046, 1318].forEach((f, i) => tone(f, 1.1, 0.08, 'triangle', 1, i * 0.09)),
  page: () => { noise(0.14, 3400, 0.7, 0.14, 'highpass'); noise(0.1, 2200, 0.9, 0.08, 'bandpass', 1.4); },
  sit: () => { noise(0.35, 380, 0.6, 0.12, 'lowpass'); tone(196, 1.2, 0.04, 'sine'); },
  portent: () => { noise(0.6, 260, 0.7, 0.22, 'lowpass', 2.2); tone(110, 0.6, 0.06, 'sawtooth', 1.8); },
  wave: () => { tone(98, 1.0, 0.18, 'sawtooth', 0.8); tone(147, 1.0, 0.1, 'square', 0.8, 0.02); noise(0.6, 200, 0.8, 0.4, 'lowpass', 0.5); },
};
// a challenge marker's call, by look
const SYS_CALL = {
  banner: () => { noise(0.4, 900, 0.5, 0.2, 'bandpass', 0.4); [0, 0.32, 0.64].forEach(d => tone(62, 0.3, 0.3, 'sine', 0.5, d)); },
  bell: () => { [196, 247, 294].forEach((f, i) => tone(f, 3, 0.14, 'sine', 1, i * 0.04)); tone(98, 3.2, 0.14, 'triangle'); },
  stake: () => { noise(0.5, 300, 0.7, 0.4, 'lowpass', 0.4); tone(55, 0.8, 0.25, 'sine', 0.6); },
  whistle: () => { tone(1760, 0.5, 0.07, 'sine', 1.3); tone(2350, 0.4, 0.05, 'sine', 1.2, 0.35); },
  horn: () => { tone(110, 1.6, 0.16, 'sawtooth', 1.02); tone(165, 1.5, 0.08, 'sawtooth', 1.01, 0.1); },
  idol: () => { tone(73, 1.8, 0.2, 'sine', 0.9); noise(1.2, 600, 0.6, 0.15, 'bandpass', 0.4); },
  stones: () => { [0, 0.2, 0.4].forEach(d => { noise(0.3, 240, 0.8, 0.4, 'lowpass', 0.5); tone(60 - d * 20, 0.4, 0.2, 'sine', 0.6, d); }); },
  drum: () => [0, 0.22, 0.44, 0.58, 0.72].forEach(d => { tone(70, 0.3, 0.32, 'sine', 0.5, d); noise(0.12, 300, 0.9, 0.25, 'lowpass'); }),
  rack: () => { noise(0.3, 3000, 1.5, 0.2, 'bandpass', 0.6); tone(880, 0.4, 0.06, 'triangle', 0.7); },
  terminal: () => { [880, 1175, 1760].forEach((f, i) => tone(f, 0.12, 0.06, 'square', 1, i * 0.1)); tone(55, 0.8, 0.12, 'sawtooth', 1.5, 0.3); },
};
function sysDraw(sh, tag, i, x, y, face = 1, opt = {}) {
  if (!sh || !sh.ok || !sh.has(tag)) return false;
  const t = sh.tag(tag); drawSprite(sh, t.from + clamp(i, 0, t.to - t.from), x, y, face, { bottom: true, ...opt }); return true;
}
const sysLoop = (sh, tag, fps = 8) => { if (!sh.ok || !sh.has(tag)) return 0; const t = sh.tag(tag); return Math.floor(time * fps) % (t.to - t.from + 1); };
const sysEase = k => k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
function sysFmt(t) { if (t === undefined || t === null) return '—'; const m = Math.floor(t / 60), s = t - m * 60; return `${m}:${s < 10 ? '0' : ''}${s.toFixed(2)}`; }
function sysLater(sec, fn) { SYS.later.push({ t: sec, fn }); }   // game-time delay (pauses with the game)
function sysNear(p, rx = 14, ry = 24) { return Math.abs(P.x - p.x) < rx && Math.abs(P.y - p.y) < ry; }
function sysFindSpawn(def, kind, id) { return (def && def.spawns || []).find(q => q.t === 'sys' && q.kind === kind && q.id === id) || null; }
function sysNeedsMet(needs) { return !needs || needs.every(n => n === 'start' || SAVE.items[n]); }
function sysNeedName(n) { return (ITEMS[n] && ITEMS[n].name) || n; }

// every sys spawn goes through one dispatcher
const SYS_KIND = {};
SPAWNS.sys = (s, c) => { const f = SYS_KIND[s.kind]; if (f) f(s, c); else console.warn('unknown sys kind', s.kind, c.id); };

// ================================================================== flags that start a clock (hidden passages)
// SAVE.x3.t[flag] = play time when the flag was first seen set; SAVE.x3.restAt = play time of the last shrine rest
for (const r of ROOMS) for (const s of r.spawns || []) if (s.t === 'sys' && s.cond && (s.cond.flag || typeof s.cond === 'string')) SYS.watch.add(s.cond.flag || s.cond);
function sysWatchFlags() { const X = x3(); for (const f of SYS.watch) if (SAVE.flags[f] && X.t[f] === undefined) X.t[f] = SAVE.playTime; }
function sysFlagTime(flag) { SYS.watch.add(flag); sysWatchFlags(); return x3().t[flag]; }
function sysCond(c) {
  if (!c) return true;
  if (typeof c === 'string') c = { flag: c };
  if (c.flag && !SAVE.flags[c.flag]) return false;
  if (c.item && !SAVE.items[c.item]) return false;
  if (c.flag && (c.restAfter || c.minTime)) {
    const t0 = sysFlagTime(c.flag), X = x3();
    const rested = c.restAfter && X.restAt !== undefined && X.restAt > t0, waited = c.minTime && SAVE.playTime - t0 >= c.minTime;
    if (!rested && !waited) return false;
  }
  return true;
}
HOOKS.rest.push(() => { sysWatchFlags(); x3().restAt = SAVE.playTime; });

// ================================================================== doors (generalised NEO-HALLOW warp): a pair of doors in two rooms
const SYS_DOOR_VERB = { arch: 'Pass through', crack: 'Squeeze through', hatch: 'Descend', ladder: 'Climb', portal: 'Step through' };
function sysDoorFace(s, def) {
  if (s.face === 1 || s.face === -1) return s.face;
  return s.x < def.w / 2 ? 1 : -1;   // face into the room
}
SYS_KIND.door = (s, c) => {
  const look = SYS_DOOR_VERB[s.look] ? s.look : 'arch', skin = sysSkin(s, c.def), sh = sheet('sys_door');
  const p = { type: 'sys_door', x: c.cx, y: c.fy, face: sysDoorFace(s, c.def), s, look, skin, sh, anim: { update() {} }, glow: 0 };
  p.prompt = () => (s.auto || SYS.warp) ? null : SYS_DOOR_VERB[look];
  p.interact = () => sysUseDoor(p);
  p.update = dt => {
    const near = sysNear(p, 12, 24);
    p.glow = approach(p.glow, near ? 1 : 0, dt * 3);
    if (look === 'portal') { addLight(p.x, p.y - 26, 58 + Math.sin(time * 5) * 5, SYS_GLOW[skin], 0.85); if (Math.random() < 0.25) particles.push({ x: p.x + rand(-9, 9), y: p.y - rand(6, 44), vx: rand(-12, 12), vy: -rand(4, 20), life: 0.6, kind: skin === 'neon' ? 'x3_neon' : 'x3_rune' }); }
    else if (look === 'crack') addLight(p.x, p.y - 22, 30, SYS_GLOW[skin], 0.35 + 0.3 * p.glow);
    else if (p.glow > 0.05) addLight(p.x, p.y - 24, 36, SYS_GLOW[skin], 0.4 * p.glow);
    const L = SYS.doorLock;
    if (L && L.room === room.id && L.id === s.id && Math.abs(P.x - p.x) > 18) SYS.doorLock = null;
    if (s.auto && !SYS.warp && !(SYS.doorLock && SYS.doorLock.room === room.id && SYS.doorLock.id === s.id) && P.state !== 'dead' && Math.abs(P.x - p.x) < 7 && P.y > p.y - 40 && P.y <= p.y + 2) sysUseDoor(p);
  };
  p.draw = () => {
    const tag = `${look}_${skin}`, fr = look === 'portal' ? sysLoop(sh, tag, 10) : 0;
    const yy = look === 'hatch' ? p.y + 8 : p.y;
    if (!sysDraw(sh, tag, fr, p.x, yy, 1)) {   // fallback: a dark doorway with a lit rim
      g.fillStyle = 'rgba(6,4,10,0.85)'; g.fillRect(Math.round(p.x) - 9, Math.round(p.y) - 34, 18, 34);
      g.fillStyle = `rgba(${SYS_GLOW[skin]},0.7)`; g.fillRect(Math.round(p.x) - 10, Math.round(p.y) - 35, 20, 1);
    }
    if (p.glow > 0.02 && look !== 'hatch') {   // a soft rim of light while you stand at it
      g.save(); g.globalAlpha = 0.18 * p.glow; g.globalCompositeOperation = 'lighter'; g.fillStyle = `rgb(${SYS_GLOW[skin]})`;
      g.fillRect(Math.round(p.x) - 8, Math.round(p.y) - 32, 16, 32); g.restore();
    }
  };
  props.push(p);
};
function sysUseDoor(p) {
  if (SYS.warp || fadePhase) return;
  const s = p.s, to = ROOM_BY[s.to], tgt = to && sysFindSpawn(to, 'door', s.toId || s.id);
  if (!tgt) { toast('It will not open.'); sfx.deny(); return; }
  if (SYS.trial) sysTrialAbort('You left the trial');
  SYS.warp = { t: 0, p, to: s.to, toId: s.toId || s.id, look: p.look, skin: p.skin };
  P.vx = 0; if (!['idle', 'run', 'land'].includes(P.state)) setP('idle', 'idle', true);
  ({ arch: sysSfx.creak, crack: sfx.crumble, hatch: sysSfx.hatch, ladder: sysSfx.ladder, portal: sysSfx.portal })[p.look]();
}
function sysUpdateWarp(dt) {
  const w = SYS.warp; if (!w) return;
  w.t += dt; P.ctrlLock = 0.12; P.inv = Math.max(P.inv, 0.35); P.vx = 0;
  P.x = lerp(P.x, w.p.x, Math.min(1, dt * 12));
  if (w.p.look === 'crack' && Math.random() < 0.4) particles.push({ x: w.p.x + rand(-6, 6), y: w.p.y - rand(4, 36), vx: rand(-20, 20), vy: rand(-10, 30), g: 200, life: 0.5, kind: 'dust' });
  if (w.t >= 0.24 && !w.fading) { w.fading = true; fadeTo(() => sysArrive(w)); }
}
// the nearest cell of a room (def, not built) where the player can stand: open body cells + ground below. Arrival safety net.
function sysStandCell(def, tx, ty) {
  const cellT = (x, y) => (x < 0 || y < 0 || x >= def.w || y >= def.h) ? T_SOLID : cellType(def.map[y][x]);
  const ok = (x, y) => !isSolidT(cellT(x, y)) && !isSolidT(cellT(x, y - 1)) && cellT(x, y) !== T_SPIKE && (isSolidT(cellT(x, y + 1)) || cellT(x, y + 1) === T_PLAT);
  if (ok(tx, ty)) return [tx, ty];
  for (let r = 1; r <= 6; r++) for (let dy = -r; dy <= r; dy++) for (const dx of [0, -r, r, ...Array.from({ length: 2 * r - 1 }, (_, i) => i - r + 1)]) {
    if (Math.max(Math.abs(dx), Math.abs(dy)) !== r) continue;
    if (ok(tx + dx, ty + dy)) return [tx + dx, ty + dy];
  }
  return [tx, ty];
}
function sysArrive(w) {
  const def = ROOM_BY[w.to], tgt = sysFindSpawn(def, 'door', w.toId);
  const [cx, cy] = sysStandCell(def, tgt.x, tgt.y);
  SYS.warp = null;
  enterRoom(w.to, cx * TILE + 8, (cy + 1) * TILE, {});
  P.vx = P.vy = 0; P.face = sysDoorFace(tgt, def); setP('idle', 'idle', true); P.ground = true; P.inv = Math.max(P.inv, 0.4);
  updateCamera(0, true);
  SYS.doorLock = { room: w.to, id: w.toId };
  x3().seen['door:' + w.to + ':' + w.toId] = 1;
  if (w.look === 'portal') { flashScreen = 0.35; shake = 3; for (let i = 0; i < 18; i++) particles.push({ x: P.x + rand(-8, 8), y: P.y - rand(0, 30), vx: rand(-60, 60), vy: -rand(10, 70), life: rand(0.4, 0.8), kind: w.skin === 'neon' ? 'x3_neon' : 'x3_rune' }); }
  saveGame();
}

// ================================================================== hidden passages: solid rock until a condition holds, checked on room entry
SYS_KIND.passage = (s, c) => {
  const w = s.w || 1, h = s.h || 3, key = sysKey(c.id, s.id || `p${s.x}_${s.y}`), open = sysCond(s.cond), X = x3();
  const cells = []; for (let yy = s.y - h + 1; yy <= s.y; yy++) for (let xx = s.x; xx < s.x + w; xx++) if (xx >= 0 && yy >= 0 && xx < room.w && yy < room.h) cells.push([xx, yy]);
  const p = { type: 'sys_passage', x: (s.x + w / 2) * TILE, y: (s.y + 1) * TILE, face: 1, s, key, open, cells, w, h, anim: { update() {} },
              wind: s.wind || (s.x < c.def.w / 2 ? 1 : -1), drift: s.drift || 'ember', hinted: !!(s.cond && SAVE.flags[s.cond.flag || s.cond]) };
  if (!open) { for (const [x, y] of cells) room.grid[y * room.w + x] = T_SOLID; SYS.relayer = true; }
  else if (!X.seen[key]) { X.seen[key] = 1; SYS.reveal = { p, t: 0 }; }
  p.update = dt => {
    if (!p.open) return;
    const cx = p.x, cy = p.y - h * TILE / 2;
    addLight(cx, cy, 52 + w * 8, s.light || '255,214,150', 0.7);
    if (Math.random() < 0.35 + w * 0.1) {   // seeds / embers riding the warm draught through the gap
      const kind = p.drift === 'seed' ? (Math.random() < 0.5 ? 'x3_seed' : 'x3_wheat') : p.drift;
      particles.push({ x: cx - p.wind * rand(4, 14), y: p.y - rand(4, h * TILE - 4), vx: p.wind * rand(30, 70), vy: rand(-14, 8), life: rand(1.2, 2.4), kind, pet: p.drift === 'seed' });
    }
    if (overlap(playerHurtbox(), rect(s.x * TILE, (s.y - h + 1) * TILE, (s.x + w) * TILE, (s.y + 1) * TILE))) X.seen[key + ':thru'] = 1;
  };
  p.draw = () => {
    if (p.open || !p.hinted || s.hint === false) return;
    // the rock remembers: a hairline crack with a thread of light (the condition's flag is set, the time isn't right yet)
    const x0 = s.x * TILE + (w * TILE) / 2, y0 = (s.y - h + 1) * TILE + 3, k = 0.35 + 0.25 * Math.sin(time * 2.2);
    g.fillStyle = `rgba(255,214,150,${k})`;
    for (let i = 0; i < h * TILE - 6; i++) g.fillRect(Math.round(x0 + Math.sin(i * 0.7 + s.x) * 2 + (hash2(i, s.y) - 0.5) * 2), y0 + i, 1, 1);
    addLight(x0, y0 + h * 8, 20, '255,214,150', 0.3);
  };
  props.push(p);
};
function sysUpdateReveal(dt) {
  const R = SYS.reveal; if (!R) return;
  const p = R.p, t0 = R.t; R.t += dt;
  if (t0 < 0.3 && R.t >= 0.3) { sfx.crumble(); shake = Math.max(shake, 5); }
  if (t0 < 0.9 && R.t >= 0.9) sysSfx.chime(0.9);
  if (R.t > 0.3 && R.t < 1.1 && Math.random() < 0.6) for (const [x, y] of p.cells) if (Math.random() < 0.3) particles.push({ x: x * TILE + rand(0, 16), y: y * TILE + rand(0, 16), vx: rand(-40, 40) + p.wind * 30, vy: -rand(0, 60), g: 420, life: rand(0.5, 1), kind: 'rock' });
  if (R.t > 2) SYS.reveal = null;
}

// ================================================================== trials
function sysTrialKey(rid, s) { return `${rid}:${s.id}`; }
function sysTrialRec(key) { const T = x3().trials; return T[key] || (T[key] = { best: null, clears: 0, gold: false, got: false }); }
SYS_KIND.trial = (s, c) => {
  const skin = sysSkin(s, c.def), sh = sheet('sys_trial'), key = sysTrialKey(c.id, s);
  const p = { type: 'sys_sigil', x: c.cx, y: c.fy, face: 1, s, key, skin, sh, room: c.id, anim: { update() {} }, pulse: 0, needs: s.needs || c.def.needs };
  p.prompt = () => {
    if (SYS.trial) return SYS.trial.p === p ? 'Restart the trial' : null;
    return sysNeedsMet(p.needs) ? (sysTrialRec(key).clears ? 'Run the trial again' : 'Begin the trial') : 'Sealed';
  };
  p.interact = () => {
    if (!sysNeedsMet(p.needs)) { sfx.deny(); toast(`The sigil does not answer. It asks for ${p.needs.filter(n => !SAVE.items[n] && n !== 'start').map(sysNeedName).join(', ')}.`, 3.5); return; }
    sysTrialStart(p);
  };
  p.update = dt => {
    const on = SYS.trial && SYS.trial.p === p;
    p.pulse = approach(p.pulse, on ? 1 : 0, dt * 2.5);
    addLight(p.x, p.y - 10, 34 + 20 * p.pulse, SYS_GLOW[skin], 0.45 + 0.4 * p.pulse);
    if (Math.random() < 0.08 + 0.3 * p.pulse) particles.push({ x: p.x + rand(-10, 10), y: p.y - rand(2, 8), vx: 0, vy: -rand(12, 30), life: rand(0.5, 1), kind: skin === 'neon' ? 'x3_neon' : 'x3_rune' });
  };
  p.draw = () => {
    const on = SYS.trial && SYS.trial.p === p, rec = x3().trials[key];
    if (!sysDraw(sh, 'sigil_' + skin, on || (rec && rec.gold) ? 1 : 0, p.x, p.y)) { g.fillStyle = '#b08a3a'; g.fillRect(Math.round(p.x) - 10, Math.round(p.y) - 3, 20, 3); }
    if (p.pulse > 0.02) {   // a ring of runes turning over the sigil while the trial runs
      g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = `rgba(${SYS_GLOW[skin]},${0.55 * p.pulse})`;
      for (let i = 0; i < 12; i++) { const a = time * 1.4 + i / 12 * 6.283; g.fillRect(Math.round(p.x + Math.cos(a) * 14), Math.round(p.y - 5 + Math.sin(a) * 3), 1, 1); }
      g.restore();
    }
  };
  props.push(p);
};
SYS_KIND.trial_goal = (s, c) => {
  const skin = sysSkin(s, c.def), sh = sheet('sys_trial'), tspec = sysFindSpawn(c.def, 'trial', s.trial), key = sysTrialKey(c.id, { id: s.trial });
  const rec = x3().trials[key];
  const p = { type: 'sys_goal', x: c.cx, y: c.fy, face: 1, s, key, skin, sh, anim: { update() {} }, open: !!(rec && rec.got), openT: rec && rec.got ? 9 : -1, tspec };
  SYS.goals[s.trial] = p;
  p.update = dt => {
    const run = SYS.trial && SYS.trial.key === key;
    if (p.openT >= 0) p.openT += dt;
    addLight(p.x, p.y - 14, run ? 60 + Math.sin(time * 6) * 6 : 34, SYS_GLOW[skin], run ? 0.95 : 0.5);
    if (run && Math.random() < 0.5) particles.push({ x: p.x + rand(-4, 4), y: p.y - rand(18, 60), vx: 0, vy: -rand(20, 50), life: 0.7, kind: 'gold' });   // a beacon over the goal
    if (run && !SYS.trial.done && overlap(playerHurtbox(), rect(p.x - 12, p.y - 26, p.x + 12, p.y))) sysTrialComplete(p);
  };
  p.draw = () => {
    const fr = p.openT < 0 ? 0 : Math.min(3, 1 + Math.floor(p.openT / 0.09));
    if (!sysDraw(sh, 'goal_' + skin, fr, p.x, p.y)) { g.fillStyle = '#8a6a3a'; g.fillRect(Math.round(p.x) - 9, Math.round(p.y) - 14, 18, 14); }
    const r = x3().trials[key];
    if (r && r.gold) { g.fillStyle = `rgba(255,222,130,${0.75 + 0.25 * Math.sin(time * 4)})`; const y = Math.round(p.y - 34 + Math.sin(time * 2) * 1.5); g.fillRect(Math.round(p.x), y - 2, 1, 5); g.fillRect(Math.round(p.x) - 2, y, 5, 1); }
  };
  props.push(p);
};
function sysAirReset() { P.airN = 0; P.airLock = false; P.airDenied = false; P.smashN = 0; P.smashLock = false; P.smashDenied = false; P.airDash = true; P.airJumps = SAVE.items.wings ? 1 : 0; P.pogoed = false; }
function sysTrialStart(p) {
  if (SYS.gaunt) { sfx.deny(); toast('Not while the gauntlet runs'); return; }
  const restart = SYS.trial && SYS.trial.p === p;
  SYS.trial = { p, s: p.s, key: p.key, room: room.id, t: 0, armed: true, attempts: restart ? SYS.trial.attempts + 1 : 1, hp: P.hp, fp: D.maxFp, killed0: new Set(killed), flash: 1, done: false };
  P.st = D.maxSt; P.fp = D.maxFp; P.x = p.x; P.vx = 0; sysAirReset();
  setP('idle', 'idle', true); sysKitReset();
  sysSfx.begin(); flashScreen = Math.max(flashScreen, 0.25); areaCard = null;
  for (let i = 0; i < 20; i++) { const a = i / 20 * 6.283; particles.push({ x: p.x + Math.cos(a) * 6, y: p.y - 4, vx: Math.cos(a) * rand(40, 90), vy: -rand(10, 60), life: rand(0.5, 0.9), kind: 'x3_rune' }); }
  if (!restart) toast(`${sysTrialName(p.s)} · par ${sysFmt(p.s.par || 60)}`, 2.6);
}
function sysTrialName(s) { return s.name || `Trial of the ${s.region || (AREAS[room.def.biome] ? AREAS[room.def.biome].name.replace(/^The /, '') : 'Hallow')}`; }
function sysTrialReset(why) {
  const T = SYS.trial; if (!T || T.done) return;
  if (fadePhase === 1) { fadeCb = null; fadePhase = 0; fadeT = 0; }   // a hazard began its own respawn fade: the trial takes over
  const p = T.p;
  P.x = p.x; P.y = p.y; P.vx = P.vy = 0; P.hook = null; P.inv = 0.4; P.flash = 0; P.rot = 0; P.rotT = 0; P.hp = T.hp; P.st = D.maxSt; P.fp = Math.max(P.fp, T.fp);
  P.wallDir = 0; P.dj = false; P.ctrlLock = 0; P.ground = true; sysAirReset(); setP('idle', 'idle', true);
  projectiles = projectiles.filter(q => q.owner === 'player'); hazards = [];
  for (const k of [...killed]) if (!T.killed0.has(k)) killed.delete(k);
  sysRespawnEnemies(); sysKitReset();
  T.t = 0; T.armed = true; T.attempts++; T.flash = 1; T.why = why;
  updateCamera(0, true); flashScreen = Math.max(flashScreen, 0.18); hitstop = 0; shake = 0; sysSfx.rewind();
  for (let i = 0; i < 14; i++) particles.push({ x: p.x + rand(-10, 10), y: p.y - rand(0, 26), vx: rand(-30, 30), vy: -rand(10, 50), life: rand(0.4, 0.8), kind: 'x3_rune' });
}
function sysTrialAbort(msg) { if (!SYS.trial) return; SYS.trial = null; if (msg) toast(msg, 2); }
function sysTrialComplete(goal) {
  const T = SYS.trial, s = T.s, par = s.par || 60, rec = sysTrialRec(T.key), time_ = T.t, first = !rec.got;
  T.done = true; SYS.trial = null;
  const gold = time_ <= par, firstGold = gold && !rec.gold, newBest = rec.best === null || time_ < rec.best;
  rec.clears++; if (newBest) rec.best = Math.round(time_ * 100) / 100; if (gold) rec.gold = true;
  sysSfx.done(); flashScreen = Math.max(flashScreen, 0.3); shake = 3;
  if (first) {
    rec.got = true; goal.open = true; goal.openT = 0; sfx.gate();
    if (s.reward) sysLater(3.3, () => { if (room && room.id === T.room) grantItem(s.reward, goal.x, goal.y - 20); else grantItem(s.reward); });
  }
  if (firstGold) sysLater(first ? 1.4 : 0.3, () => gainCinders(s.bonus || 300, goal.x, goal.y - 20));
  SYS.result = { t: 0, time: time_, par, gold, firstGold, newBest, best: rec.best, first, name: sysTrialName(s), attempts: T.attempts };
  for (let i = 0; i < 30; i++) particles.push({ x: goal.x + rand(-8, 8), y: goal.y - rand(4, 24), vx: rand(-90, 90), vy: -rand(30, 160), g: 200, life: rand(0.6, 1.3), kind: gold ? 'gold' : 'x3_rune' });
  saveGame();
}
function sysUpdateTrial(dt) {
  const T = SYS.trial; if (!T) return;
  if (room.id !== T.room) { sysTrialAbort('The trial is abandoned'); return; }
  T.flash = Math.max(0, T.flash - dt * 2.5);
  if (T.armed) { if (Math.abs(P.x - T.p.x) > 10 || !P.ground || Math.abs(P.vx) > 20) T.armed = false; }
  else T.t += dt;
  if (P.hp < T.hp - 0.01) {   // no HP is ever lost in a trial; a real blow (not a slow drain) sends you back
    const big = T.hp - P.hp > D.maxHp * 0.015; P.hp = T.hp;
    if (big) { sysTrialReset('hazard'); return; }
  }
  if (P.y > room.ph + 6 || P.y < -40) sysTrialReset('fall');
}
// any blow inside a trial: straight back to the sigil, no damage (parries, blocks and i-frames still work as usual)
{
  const _hurt = hurtPlayer;
  hurtPlayer = function (dmg, dir, id, opt = {}) {
    const T = SYS.trial;
    if (T && !T.done && P && P.state !== 'dead' && playing() && !SETTINGS.god && !(P.inv > 0) && !iframes()
        && !(opt.parryable && P.state === 'parry' && P.parryWin > 0 && dir === -P.face) && !(isBlocking() && dir === -P.face)) {
      if (id !== undefined && id === P.lastHit) return false;
      P.lastHit = id; sysTrialReset('hit'); return true;
    }
    if (SYS.vista && !SYS.vista.standing) return false;   // a vista bench is a safe spot
    return _hurt.apply(this, arguments);
  };
  const _spike = spikeHurt;
  spikeHurt = function () { if (SYS.trial && !SYS.trial.done && P.state !== 'dead') { sysTrialReset('spikes'); return; } return _spike.apply(this, arguments); };
}
HOOKS.death.push(() => {
  if (SYS.trial && !SYS.trial.done) {   // something killed outright (direct HP loss): undo it, reset instead
    P.state = 'idle'; P.deadT = 0; slowmo = 0; P.hp = SYS.trial.hp; sysTrialReset('hazard'); return;
  }
  if (SYS.gaunt) { SYS.gaunt.dead = true; }
});
function sysRespawnEnemies() {   // bring back the room's foes that died during this attempt (map chars and enemy spawns)
  const def = room.def, have = new Set(enemies.filter(e => !e.gone && e.alive).map(e => e.key));
  enemies = enemies.filter(e => e.alive || !e.key || killed.has(e.key));
  for (let y = 0; y < def.h; y++) for (let x = 0; x < def.w; x++) {
    const ch = def.map[y][x], key = `${def.id}:${x},${y}`;
    if (ENEMY_CHARS[ch] && !have.has(key) && !killed.has(key)) enemies.push(makeEnemy(ENEMY_CHARS[ch], x * TILE + 8, (y + 1) * TILE, key));
  }
  spawnDefEnemies(def, have);
}
// KM's kit objects (docs/KIT_API.md § Mechanics): reset movers/crumbles/rising floors; open/close gates by id
function sysKitReset() {
  if (typeof kitReset === 'function') { try { kitReset(room.id); } catch (e) { console.error(e); } return; }
  for (const p of props) if (p.kit && typeof p.reset === 'function') p.reset();
}
function sysGate(id, open) {
  if (typeof kitForce === 'function') { kitForce(id, !!open); return; }   // KM: a forced consumer state (true = open)
  for (const p of props) if (p.id === id && (p.kit || p.type === 'kit_gate' || p.kind === 'gate')) {
    if (typeof p.setOpen === 'function') p.setOpen(open);
    else if (typeof p.set === 'function') p.set(open);
    else if (typeof p.toggle === 'function' && !!p.open !== open) p.toggle();
    else p.open = open;
  }
}

// ================================================================== gauntlets: opt-in arenas behind a challenge marker
const SYS_GAUNT_VERB = { banner: 'Raise the banner', bell: 'Ring the bell', stake: 'Grasp the stake', whistle: 'Blow the whistle', horn: 'Sound the horn',
  idol: 'Touch the idol', stones: 'Kneel at the stones', drum: 'Strike the drum', rack: 'Take up a blade', terminal: 'Run the program' };
SYS_KIND.gauntlet = (s, c) => {
  const look = SYS_GAUNT_VERB[s.look] ? s.look : 'banner', sh = sheet('sys_gaunt'), key = sysKey(c.id, s.id);
  const p = { type: 'sys_gaunt', x: c.cx, y: c.fy, face: 1, s, key, look, sh, room: c.id, anim: { update() {} }, lit: !!SAVE.flags[key], flare: 0 };
  p.prompt = () => SYS.gaunt || SYS.trial ? null : p.lit ? 'Challenge again' : SYS_GAUNT_VERB[look];
  p.interact = () => sysGauntStart(p);
  p.update = dt => {
    p.flare = Math.max(0, p.flare - dt);
    const on = p.lit || (SYS.gaunt && SYS.gaunt.p === p);
    if (on) { addLight(p.x, p.y - 28, 46 + p.flare * 60, look === 'terminal' ? '90,230,255' : '255,170,90', 0.8 + p.flare * 0.4); if (Math.random() < 0.15) particles.push({ x: p.x + rand(-5, 5), y: p.y - rand(30, 44), vx: 0, vy: -rand(10, 25), life: 0.6, kind: look === 'terminal' ? 'x3_neon' : 'ember' }); }
    else addLight(p.x, p.y - 24, 22, '255,190,120', 0.25);
  };
  p.draw = () => {
    const on = p.lit || (SYS.gaunt && SYS.gaunt.p === p);
    if (!sysDraw(sh, look, on ? 1 : 0, p.x, p.y)) { g.fillStyle = on ? '#e6a050' : '#6a5030'; g.fillRect(Math.round(p.x) - 1, Math.round(p.y) - 40, 2, 40); g.fillRect(Math.round(p.x), Math.round(p.y) - 40, 12, 14); }
  };
  props.push(p);   // its gates are forced open from the enter hook (after the room's kit objects exist): never the only way on
};
function sysGauntStart(p) {
  if (SYS.gaunt || SYS.trial) return;
  const s = p.s, waves = (s.waves || []).filter(w => w && w.length);
  if (!waves.length) { toast('Nothing answers.'); return; }
  SYS.run++;
  SYS.gaunt = { p, s, key: p.key, room: room.id, waves, wave: -1, state: 'intro', t: 0, run: SYS.run, spawned: 0, total: 0 };
  p.flare = 1; (SYS_CALL[p.look] || SYS_CALL.banner)(); shake = 5; flashScreen = Math.max(flashScreen, 0.2);
  for (const id of s.gates || []) sysGate(id, false);
  SYS.gBanner = { title: (s.name || 'The Gauntlet').toUpperCase(), sub: `${waves.length} waves`, t: 0, dur: 2.2 }; areaCard = null; if (typeof regionCard !== 'undefined') regionCard = null;
}
function sysSpawnWave(G) {
  G.wave++; G.state = 'wave'; G.t = 0; G.spawned = 0;
  const W = G.waves[G.wave]; G.total = W.length;
  SYS.gBanner = { title: `WAVE ${G.wave + 1}`, sub: `of ${G.waves.length}`, t: 0, dur: 1.8 };
  sysSfx.wave();
  W.forEach((e, i) => SYS.portents.push({ e, x: e.x * TILE + 8, y: (e.y + 1) * TILE, t: -i * 0.18, run: G.run, done: false }));
}
function sysUpdateGaunt(dt) {
  const G = SYS.gaunt;
  for (const q of SYS.portents) {   // ash rises where a foe is about to stand, then it's there
    q.t += dt; if (q.t < 0) continue;
    if (Math.random() < 0.6) particles.push({ x: q.x + rand(-6, 6), y: q.y - rand(0, 6), vx: rand(-6, 6), vy: -rand(40, 90), life: 0.6, kind: 'ember' });
    addLight(q.x, q.y - 16, 30 + q.t * 30, '255,120,60', 0.7);
    if (q.t >= 0.75 && !q.done) {
      q.done = true;
      if (G && q.run === G.run && (ENEMY[q.e.type] || ENEMY_CLASSES[q.e.type])) {
        const en = makeEnemy(q.e.type, q.x, q.y, `x3g:${G.room}:${G.s.id}:${G.run}:${G.wave}:${G.spawned}`);
        en.aggro = true; en.x3g = G.run; en.cool = Math.max(en.cool, 0.6); enemies.push(en); G.spawned++;
        spawnFx('dust', q.x, q.y, 1); spawnFx(fxOr('death_ash', 'dust'), q.x, q.y, 1, null, { alpha: 0.7 }); sysSfx.portent();
      } else if (G && q.run === G.run) { console.warn('gauntlet: unknown enemy type', q.e.type); G.spawned++; }
    }
  }
  SYS.portents = SYS.portents.filter(q => !q.done);
  if (!G) return;
  if (room.id !== G.room || G.dead) { SYS.gaunt = null; SYS.portents = []; return; }
  G.t += dt;
  if (G.state === 'intro' && G.t > 1.6) sysSpawnWave(G);
  else if (G.state === 'wave') {
    const alive = enemies.filter(e => e.x3g === G.run && e.alive).length;
    G.alive = alive;
    if (G.spawned >= G.total && !alive && G.t > 1) { G.state = G.wave + 1 < G.waves.length ? 'rest' : 'won'; G.t = 0; if (G.state === 'rest') sysSfx.chime(0.75); }
  } else if (G.state === 'rest' && G.t > 1.4) sysSpawnWave(G);
  else if (G.state === 'won' && G.t > 0.6) sysGauntWin(G);
}
function sysGauntWin(G) {
  const s = G.s, first = !SAVE.flags[G.key];
  SYS.gaunt = null; G.p.lit = true; G.p.flare = 1.5; SAVE.flags[G.key] = 1;
  const X = x3(), rec = X.gaunt[G.key] || (X.gaunt[G.key] = { clears: 0 }); rec.clears++;
  for (const id of s.gates || []) sysGate(id, true);
  sfx.felled(); flashScreen = Math.max(flashScreen, 0.35); shake = 4;
  SYS.gBanner = { title: 'GAUNTLET CLEARED', sub: first ? (s.name || '') : 'The marker burns on', t: 0, dur: 3.4, big: true };
  if (first) (s.reward || []).forEach((id, i) => sysLater(3.2 + i * 1.7, () => { if (ITEMS[id]) grantItem(id, G.p.x, G.p.y - 30); else if (typeof id === 'number') gainCinders(id, G.p.x, G.p.y - 30); }));
  else sysLater(1, () => gainCinders(s.replay || 300 + 120 * G.waves.length, G.p.x, G.p.y - 30));
  saveGame();
}

// ================================================================== vista benches: sit, the camera pulls back, the music settles
SYS_KIND.bench = (s, c) => {
  const skin = sysSkin(s, c.def), sh = sheet('sys_bench'), key = sysKey(c.id, s.id || 'bench');
  const p = { type: 'sys_bench', x: c.cx, y: c.fy, face: s.face || 1, s, key, skin, sh, room: c.id, anim: { update() {} } };
  p.prompt = () => SYS.vista ? null : 'Sit';
  p.interact = () => sysSit(p);
  p.draw = () => { if (!sysDraw(sh, 'bench_' + skin, 0, p.x, p.y)) { g.fillStyle = '#5a4630'; g.fillRect(Math.round(p.x) - 14, Math.round(p.y) - 8, 28, 3); g.fillRect(Math.round(p.x) - 12, Math.round(p.y) - 5, 2, 5); g.fillRect(Math.round(p.x) + 10, Math.round(p.y) - 5, 2, 5); } };
  props.push(p);
};
function sysSit(p) {
  if (SYS.gaunt || SYS.trial || (boss && boss.active && boss.alive)) { sfx.deny(); return; }
  const s = p.s, X = x3(), first = !X.vistas[p.key];
  P.x = p.x; P.vx = P.vy = 0; P.face = s.face || (s.view ? (s.view[0] * TILE + 8 < p.x ? -1 : 1) : p.face);
  setP('rest', pHas('rest') ? 'rest' : 'idle', false); sysSfx.sit(); areaCard = null;
  // how far the view pulls back: fit the room (never past its walls), or the bench's own zoom
  // outdoor rooms have open sky above them, so the view may rise into it (the parallax fills it)
  const sky = room.def.indoor ? 0 : 160, zfit = Math.max(W / room.pw, H / (room.ph + sky)), zt = clamp(s.zoom || Math.max(zfit, 0.55), Math.max(zfit, 0.4), 1);
  const f = s.view ? { x: s.view[0] * TILE + 8, y: s.view[1] * TILE + 8 } : { x: room.pw / 2, y: room.ph / 2 };
  SYS.vista = { p, t: 0, k: 0, zt, f, sky, standing: false, first, lore: s.lore && LORE_PAGES[s.lore] ? s.lore : null };
  if (first) { X.vistas[p.key] = Math.round(SAVE.playTime); sysLater(1.5, () => toast('Vista found · ' + room.def.name, 3)); }
  if (SYS.vista.lore) sysLoreFound(SYS.vista.lore, true);
  saveGame();
}
function sysStand() {
  const V = SYS.vista; if (!V || V.standing) return;
  V.standing = true; V.st = 0;
  setP('rise', pHas('rise') ? 'rise' : 'idle', false);
}
function sysUpdateVista(dt) {
  const V = SYS.vista; if (!V) return;
  if (room.id !== V.p.room) { SYS.vista = null; return; }
  V.t += dt;
  if (!V.standing) {
    V.k = Math.min(1, V.k + dt / 1.5); P.inv = Math.max(P.inv, 0.3); P.vx = 0;
    if (P.state !== 'rest') sysStand();   // something else moved you
  } else { V.k = Math.max(0, V.k - dt / 0.8); if (V.k <= 0) SYS.vista = null; }
}
// the pulled-back view: drawn over the finished frame (screen space) with its own classic lighting, crossfaded in
const sysSave = document.createElement('canvas'); sysSave.width = W; sysSave.height = H; const sysSaveX = sysSave.getContext('2d');
const sysZoom = document.createElement('canvas'); sysZoom.width = W; sysZoom.height = H; const sysZoomX = sysZoom.getContext('2d');
const sysLC = document.createElement('canvas'); sysLC.width = W; sysLC.height = H; const sysLX = sysLC.getContext('2d');
function sysVistaView() {
  const V = SYS.vista; if (!V || V.k <= 0.002) return null;
  const e = sysEase(V.k), z = lerp(1, V.zt, e), vw = W / z, vh = H / z;
  let cx = lerp(cam.x + W / 2, V.f.x, e), cy = lerp(cam.y + H / 2, V.f.y, e);
  cx = room.pw > vw ? clamp(cx, vw / 2, room.pw - vw / 2) : room.pw / 2; cy = room.ph + V.sky > vh ? clamp(cy, vh / 2 - V.sky, room.ph - vh / 2) : room.ph / 2;
  return { z, x0: cx - vw / 2, y0: cy - vh / 2, a: clamp(V.k * 3.2, 0, 1), e };
}
function sysDrawVista() {
  const v = sysVistaView(); if (!v) return;
  const tgt = g.canvas;
  sysSaveX.clearRect(0, 0, W, H); sysSaveX.drawImage(tgt, 0, 0);
  const cam0 = { x: cam.x, y: cam.y };
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  cam.x = v.x0; cam.y = v.y0;
  try {
    drawParallax();
    g.setTransform(v.z, 0, 0, v.z, -v.x0 * v.z, -v.y0 * v.z); g.imageSmoothingEnabled = v.z < 0.999; g.imageSmoothingQuality = 'high';
    g.drawImage(room.back, 0, 0); g.drawImage(room.front, 0, 0);
    for (const p of props) if (p.type !== 'fog' && p.type !== 'veil') drawProp(p);
    for (const e of enemies) e.draw();
    drawSprite(sheet('player'), P.anim.frame, P.x, P.y, P.face, {});
    const ws = sheet('wpn_' + (SAVE.weapon || 'longsword')); drawSprite(ws.ok ? ws : sheet('wpn_longsword'), P.anim.frame, P.x, P.y, P.face, {});
    drawWater();
    for (const p of props) if (p.type === 'fog' || p.type === 'veil') drawProp(p);
    const saved = lights; lights = []; drawParticles(); lights = saved;
    // lighting: the classic darkness layer, scaled to the wider view
    g.setTransform(1, 0, 0, 1, 0, 0); g.imageSmoothingEnabled = false;
    const A = AREAS[room.def.biome] || AREAS.ramparts, amb = (A.ambient || 0.4) * lerp(0.9, 0.6, v.e);   // a view is lit for looking at
    sysLX.globalCompositeOperation = 'source-over'; sysLX.clearRect(0, 0, W, H); sysLX.fillStyle = `rgba(4,3,8,${amb})`; sysLX.fillRect(0, 0, W, H);
    sysLX.globalCompositeOperation = 'destination-out';
    const Ls = lights.concat([{ x: P.x, y: P.y - 16, r: 100, k: 0.9, color: '255,210,170' }]);
    for (const L of Ls) {
      const x = (L.x - v.x0) * v.z, y = (L.y - v.y0) * v.z, r = L.r * v.z; if (x < -r || x > W + r || y < -r || y > H + r) continue;
      const gr = sysLX.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, `rgba(0,0,0,${Math.min(1, L.k)})`); gr.addColorStop(1, 'rgba(0,0,0,0)');
      sysLX.fillStyle = gr; sysLX.fillRect(x - r, y - r, r * 2, r * 2);
    }
    g.drawImage(sysLC, 0, 0);
    const vg = g.createRadialGradient(W / 2, H / 2, 90, W / 2, H / 2, 250); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, `rgba(0,0,0,${0.35 + 0.25 * v.e})`);
    g.fillStyle = vg; g.fillRect(0, 0, W, H);
    // letterbox bars ease in: the frame reads as a view, not a menu
    const bh = Math.round(14 * v.e); if (bh > 0) { g.fillStyle = '#050407'; g.fillRect(0, 0, W, bh); g.fillRect(0, H - bh, W, bh); }
  } catch (e) { console.error(e); }
  cam.x = cam0.x; cam.y = cam0.y; g.restore();
  if (v.a < 1) {   // crossfade from the ordinary frame
    sysZoomX.clearRect(0, 0, W, H); sysZoomX.drawImage(tgt, 0, 0);
    g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, W, H); g.drawImage(sysSave, 0, 0); g.globalAlpha = v.a; g.drawImage(sysZoom, 0, 0); g.restore();
  }
}
HOOKS.renderTop.push(() => {
  if (SYS.vista) sysDrawVista();
  const w = SYS.warp;   // stepping into a portal: the light swallows the frame (neon ones glitch, like the NEO-HALLOW crack)
  if (w && w.look === 'portal') {
    const k = clamp(w.t / 0.24, 0, 1), x = Math.round(w.p.x - cam.x), y = Math.round(w.p.y - 26 - cam.y);
    if (w.skin === 'neon' && typeof nhGlitchScreen === 'function') nhGlitchScreen(k * 0.8, 3);
    g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'lighter';
    const gr = g.createRadialGradient(x, y, 0, x, y, 30 + k * 260); gr.addColorStop(0, `rgba(${SYS_GLOW[w.skin]},${0.9 * k})`); gr.addColorStop(1, `rgba(${SYS_GLOW[w.skin]},0)`);
    g.fillStyle = gr; g.fillRect(0, 0, W, H); g.restore();
  }
});
// the music settles to its ambient layer on a bench (and in vista rooms): the drone stays, the bells rest
{
  const _um = updateMusic;
  updateMusic = function () {
    _um.apply(this, arguments);
    const want = (SYS.vista && !SYS.vista.standing) ? 1 : room && room.def && room.def.vista && state === 'play' ? 0.7 : 0;
    SYS.duck = approach(SYS.duck, want, 0.02);
    if (!AC || !MUSIC.gain || SYS.duck <= 0 || !MUSIC.mode || MUSIC.mode === 'boss') return;
    MUSIC.gain.gain.setTargetAtTime((1 - 0.45 * SYS.duck) * 0.7 * SETTINGS.music + 0.0001, AC.currentTime, 0.8);
    if (SYS.duck > 0.6) MUSIC.nextNote = Math.max(MUSIC.nextNote, AC.currentTime + 1);
  };
}

// ================================================================== lore pages and the Hallow Chronicle
const SYS_LORE_VERB = { stone: 'Read', corpse: 'Search', book: 'Read', tablet: 'Read', scroll: 'Read', none: 'Read' };
SYS_KIND.lore = (s, c) => {
  const look = SYS_LORE_VERB[s.look] ? s.look : 'stone', sh = sheet('sys_lore'), page = s.page;
  const p = { type: 'sys_lore', x: c.cx, y: c.fy, face: s.face || 1, s, look, sh, page, anim: { update() {} } };
  p.prompt = () => SYS_LORE_VERB[look];
  p.interact = () => sysOpenPage(page, { fromWorld: true });
  p.update = () => {
    const unread = page && !x3().lore[page];
    if (unread) { addLight(p.x, p.y - 12, 28, '255,220,150', 0.55 + 0.15 * Math.sin(time * 3)); if (Math.random() < 0.06) particles.push({ x: p.x + rand(-6, 6), y: p.y - rand(4, 16), vx: 0, vy: -rand(6, 16), life: 0.9, kind: 'gold' }); }
  };
  p.draw = () => { if (look === 'none') return; if (!sysDraw(sh, look, 0, p.x, p.y, p.face)) { g.fillStyle = '#6a6070'; g.fillRect(Math.round(p.x) - 6, Math.round(p.y) - 14, 12, 14); } };
  props.push(p);
};
function sysLoreFound(id, quiet) {
  const X = x3(); if (!id || X.lore[id] !== undefined) return false;
  X.lore[id] = Math.round(SAVE.playTime); saveGame();
  if (!quiet) toast('A page for the Hallow Chronicle', 2.6); else sysLater(2.6, () => toast('A page for the Hallow Chronicle', 2.6));
  return true;
}
function sysPageLines(pg, width = 236, size = 6) {   // paragraphs -> wrapped lines ('' marks a paragraph gap)
  const out = []; String(pg.text || '').split(/\n+/).forEach((para, i) => { if (i) out.push(''); out.push(...wrap(para.trim(), width, size)); });
  return out;
}
function sysOpenPage(id, opt = {}) {
  const pg = LORE_PAGES[id]; if (!pg) { toast('The words have worn away.'); return; }
  const fresh = sysLoreFound(id, true);
  SYS.reader = { id, pg, pi: 0, t: 0, fresh, back: state === 'menu' ? { state: 'menu', menu } : { state: 'play' } };
  if (state === 'menu') menu = null;
  state = 'sysread'; clearBuffer(); sysSfx.page();
}
function sysCloseReader() {
  const R = SYS.reader; if (!R) return;
  SYS.reader = null; clearBuffer(); sfx.menu();
  if (R.back.state === 'menu' && R.back.menu) { menu = R.back.menu; state = 'menu'; } else state = 'play';
}
function sysReaderInput(a) {
  const R = SYS.reader; if (!R) { state = 'play'; return; }
  const pages = Math.max(1, Math.ceil(sysPageLines(R.pg).length / SYS_READ_LINES));
  if (['pause', 'back', 'heavy', 'roll', 'map'].includes(a)) return sysCloseReader();
  if (a === 'left' && R.pi > 0) { R.pi--; sysSfx.page(); return; }
  if ((a === 'right' || ['confirm', 'interact', 'attack', 'jump'].includes(a)) && R.pi < pages - 1) { R.pi++; sysSfx.page(); return; }
  if (['confirm', 'interact', 'attack', 'jump'].includes(a)) sysCloseReader();
}
const SYS_READ_LINES = 12;
function sysRegionName(r) { return (AREAS[r] && AREAS[r].name) || r || 'The Hallow'; }
function sysRenderReader() {
  const R = SYS.reader; if (!R) return;
  if (R.t0 === undefined) R.t0 = time; R.t = time - R.t0;
  const a = clamp(R.t * 5, 0, 1), lines = sysPageLines(R.pg), pages = Math.max(1, Math.ceil(lines.length / SYS_READ_LINES));
  vctx.globalAlpha = a; uiBackdrop(0.78); vctx.globalAlpha = 1;
  const bx = 62, by = 26, bw = 260, bh = 162;
  panel(bx, by, bw, bh, 0.94 * a);
  icon('x3_page', bx + 10, by + 9, 16, a);
  text(R.pg.title || 'Untitled', bx + 32, by + 19, uiFit(R.pg.title || 'Untitled', bw - 44, 8, 5.5), UIC.gold, 'left', { alpha: a });
  text(`${sysRegionName(R.pg.region).toUpperCase()}  ·  HALLOW CHRONICLE`, bx + 32, by + 27.5, 4.5, UIC.dim, 'left', { alpha: a, spacing: 0.8, weight: 500 });
  uiFade(bx + 10, bx + bw - 10, by + 33, UI_RGB.accent, 0.6 * a);
  lines.slice(R.pi * SYS_READ_LINES, (R.pi + 1) * SYS_READ_LINES).forEach((l, i) => text(l, bx + 12, by + 46 + i * 8.6, 6, UIC.body, 'left', { alpha: a, weight: 400 }));
  if (pages > 1) pagesDots(bx + bw / 2, by + bh - 9, R.pi, pages, a);
  if (R.fresh) text('New page', bx + bw - 10, by + 19, 5, '#ffd070', 'right', { alpha: a * (0.7 + 0.3 * Math.sin(time * 4)), weight: 600 });
  uiFooter(pages > 1 ? [['←→', 'page'], ['Enter', R.pi < pages - 1 ? 'next' : 'close'], ['Esc', 'close']] : [['Enter', 'close']]);
}
function pagesDots(cx, y, i, n, a = 1) { for (let k = 0; k < n; k++) uiDiamond(cx - (n - 1) * 4 + k * 8, y, k === i ? 1.6 : 1.1, k === i ? UIC.gold : '#5a4a30', a); }
// the Chronicle in the inventory: found pages, grouped by region (story order of first discovery)
function sysLoreEntries() {
  const X = x3(), order = {}; let n = 0;
  for (const r of ROOMS) if (!(r.biome in order)) order[r.biome] = n++;
  return Object.keys(X.lore).filter(id => LORE_PAGES[id]).sort((a, b) => ((order[LORE_PAGES[a].region] ?? 99) - (order[LORE_PAGES[b].region] ?? 99)) || X.lore[a] - X.lore[b])
    .map(id => ({ kind: 'lore', id, name: LORE_PAGES[id].title || 'Untitled', icon: 'x3_page', desc: LORE_PAGES[id].text || '', region: LORE_PAGES[id].region }));
}
INV_CATS.push({ k: 'lore', name: 'Hallow Chronicle', icon: 'x3_lore', entries: sysLoreEntries, total: () => Object.values(LORE_PAGES).filter(p => !p.test).length });
{
  const _dd = drawDetail;
  drawDetail = function (e, px, py, pw, ph, cmp) {
    if (!e || e.kind !== 'lore') return _dd.apply(this, arguments);
    const x = px + 9, all = Object.keys(LORE_PAGES).filter(id => LORE_PAGES[id].region === e.region && !!LORE_PAGES[id].test === !!LORE_PAGES[e.id].test), got = all.filter(id => x3().lore[id] !== undefined).length;
    uiCell(x, py + 9, 26); icon('x3_page', x + 5, py + 14, 16);
    text(e.name, x + 33, py + 21, uiFit(e.name, pw - 50, 7.6, 5), UIC.gold);
    text(`${sysRegionName(e.region)}  ·  ${got} / ${all.length} pages`, x + 33, py + 30, 5, UIC.muted, 'left', { weight: 500 });
    uiHair(x, py + 39, pw - 18, UIC.line, 0.8);
    const L = sysPageLines(LORE_PAGES[e.id], pw - 20, 5.6); let y = py + 49;
    for (const l of L) { if (y > py + ph - 14) { text('…', x, y, 5.6, UIC.faint); break; } text(l, x, y, 5.6, UIC.body, 'left', { weight: 400 }); y += 7.4; }
    text(`${kl('Enter')} — read the page`, px + pw - 9, py + ph - 5, 4.8, UIC.faint, 'right', { weight: 400 });
  };
  const _inv = invInput;
  invInput = function (M, a) {
    if (!M.bar && ['confirm', 'interact', 'attack', 'jump'].includes(a)) {
      const C = INV_CATS[M.cat || 0];
      if (C && C.k === 'lore') { const e = catEntries(C)[M.isel || 0]; if (e) sysOpenPage(e.id); return; }
    }
    return _inv.apply(this, arguments);
  };
}

// ================================================================== completion (Status tab)
let _sysTotals = null;
function sysTotals() {   // static per-region totals from the room list (test rooms excluded)
  if (_sysTotals) return _sysTotals;
  const T = {}, add = (b, k, n = 1) => { const r = T[b] || (T[b] = { rooms: 0, trials: [], vistas: [], secrets: [], gaunts: [], lore: 0 }); if (typeof r[k] === 'number') r[k] += n; else r[k].push(n); };
  for (const r of ROOMS) {
    if (r.test) continue;
    add(r.biome, 'rooms');
    if (r.secret) add(r.biome, 'secrets', r.id);
    for (const s of r.spawns || []) {
      if (s.t !== 'sys') continue;
      if (s.kind === 'trial') add(r.biome, 'trials', sysTrialKey(r.id, s));
      if (s.kind === 'bench') add(r.biome, 'vistas', sysKey(r.id, s.id || 'bench'));
      if (s.kind === 'gauntlet') add(r.biome, 'gaunts', sysKey(r.id, s.id));
    }
  }
  return (_sysTotals = T);
}
function sysCompletion() {
  const T = sysTotals(), X = x3(), rows = [], tot = { rooms: [0, 0], trials: [0, 0, 0], vistas: [0, 0], secrets: [0, 0], gaunts: [0, 0], lore: [0, 0] };
  const loreBy = {}; for (const [id, pg] of Object.entries(LORE_PAGES)) { if (pg.test) continue; const b = loreBy[pg.region] || (loreBy[pg.region] = [0, 0]); b[1]++; if (X.lore[id] !== undefined) b[0]++; }
  const seen = new Set(); for (const r of ROOMS) if (!r.test && SAVE.visited[r.id]) seen.add(r.biome);
  for (const [b, t] of Object.entries(T)) {
    const vis = ROOMS.filter(r => r.biome === b && !r.test && SAVE.visited[r.id]).length;
    const row = { biome: b, name: sysRegionName(b), seen: seen.has(b),
      rooms: [vis, t.rooms], trials: [t.trials.filter(k => X.trials[k] && X.trials[k].clears).length, t.trials.length, t.trials.filter(k => X.trials[k] && X.trials[k].gold).length],
      vistas: [t.vistas.filter(k => X.vistas[k] !== undefined).length, t.vistas.length], secrets: [t.secrets.filter(id => SAVE.visited[id]).length, t.secrets.length],
      gaunts: [t.gaunts.filter(k => SAVE.flags[k]).length, t.gaunts.length], lore: loreBy[b] || [0, 0] };
    rows.push(row);
    for (const k of Object.keys(tot)) for (let i = 0; i < tot[k].length; i++) tot[k][i] += row[k][i] || 0;
  }
  for (const [b, v] of Object.entries(loreBy)) if (!T[b]) { tot.lore[0] += v[0]; tot.lore[1] += v[1]; }
  const found = tot.rooms[0] + tot.trials[0] + tot.trials[2] + tot.vistas[0] + tot.secrets[0] + tot.gaunts[0] + tot.lore[0];
  const all = tot.rooms[1] + tot.trials[1] * 2 + tot.vistas[1] + tot.secrets[1] + tot.gaunts[1] + tot.lore[1];
  return { rows, tot, pct: all ? Math.floor(found / all * 1000) / 10 : 0 };
}

// ================================================================== HUD: trial timer, results card, gauntlet banners and counter
function sysHudPanel(x, y, w, h, a = 1) {
  vctx.globalAlpha = a; vctx.fillStyle = 'rgba(8,6,12,0.72)'; vctx.fillRect(ox + x * scale, oy + y * scale, w * scale, h * scale); vctx.globalAlpha = 1;
  uiFade(x + w / 2, x - 4, y, UI_RGB.gold, 0.8 * a); uiFade(x + w / 2, x + w + 4, y, UI_RGB.gold, 0.8 * a);
  uiFade(x + w / 2, x + 6, y + h, UI_RGB.accent, 0.5 * a); uiFade(x + w / 2, x + w - 6, y + h, UI_RGB.accent, 0.5 * a);
}
function sysRenderTrialHud() {
  const T = SYS.trial; if (!T || state !== 'play') return;
  const par = T.s.par || 60, rec = x3().trials[T.key], cx = W / 2, y = 5;
  sysHudPanel(cx - 62, y, 124, 27);
  icon('x3_trial', cx - 58, y + 3.5, 12, 0.9 + 0.1 * Math.sin(time * 4));
  const nm = sysTrialName(T.s).toUpperCase(); text(nm, cx - 43, y + 8.5, uiFit(nm, 98, 4.6, 3.6, 600), UIC.dim, 'left', { spacing: 0.8, weight: 600 });
  const over = T.t > par, col = T.flash > 0.35 ? '#ffffff' : T.armed ? UIC.muted : over ? '#d89070' : '#f5e3b0';
  text(sysFmt(T.t), cx - 43, y + 21, 10, col, 'left', { weight: 600 });
  text(`PAR ${sysFmt(par)}`, cx + 58, y + 14, 4.8, over ? UIC.faint : UIC.gold, 'right', { weight: 600, spacing: 0.4 });
  text(rec && rec.best ? `BEST ${sysFmt(rec.best)}` : `TRY ${T.attempts}`, cx + 58, y + 22, 4.6, UIC.faint, 'right', { weight: 500, spacing: 0.4 });
  if (T.armed && T.attempts === 1) text('Step off the sigil to start the clock', cx, y + 36, 5, UIC.muted, 'center', { weight: 400, alpha: 0.6 + 0.4 * Math.sin(time * 3) });
}
function sysRenderResult() {
  const R = SYS.result; if (!R) return;
  if (R.t0 === undefined) R.t0 = time; R.t = time - R.t0; if (R.t > 3.6) { SYS.result = null; return; }
  const a = clamp(Math.min(R.t * 3, (3.6 - R.t) * 2), 0, 1), cx = W / 2;
  band(a * 0.8, 58, 70);
  text(R.first ? 'TRIAL CONQUERED' : 'TRIAL COMPLETE', cx, 80, 11, '#e6c77a', 'center', { alpha: a, spacing: 2.4, weight: 500 });
  uiDiamond(cx, 85, 1.4, UIC.gold, a); uiFade(cx + 4, cx + 70, 84.8, UI_RGB.gold, 0.8 * a); uiFade(cx - 4, cx - 70, 84.8, UI_RGB.gold, 0.8 * a);
  text(sysFmt(R.time), cx, 102, 13, R.gold ? '#ffe39a' : '#e8dcc0', 'center', { alpha: a, weight: 600 });
  const bits = [R.gold ? `Under par ${sysFmt(R.par)}` : `Par ${sysFmt(R.par)}`, R.newBest ? 'New best' : `Best ${sysFmt(R.best)}`];
  text(bits.join('   ·   '), cx, 114, 5.8, R.gold ? UIC.gold : UIC.muted, 'center', { alpha: a, weight: 500 });
  if (R.gold) { const k = 0.7 + 0.3 * Math.sin(time * 5); uiDiamond(cx - 44, 99, 3.2, `rgba(255,222,130,${k})`, a); uiDiamond(cx + 44, 99, 3.2, `rgba(255,222,130,${k})`, a); }
  if (R.firstGold) text('A gold mark for the Chronicle', cx, 123, 5, '#ffd070', 'center', { alpha: a, weight: 400 });
}
function sysRenderGaunt() {
  const B = SYS.gBanner;
  if (B) {
    if (B.t0 === undefined) B.t0 = time; B.t = time - B.t0; if (B.t > B.dur) SYS.gBanner = null;
    else {
      const a = clamp(Math.min(B.t * 3, (B.dur - B.t) * 2), 0, 1), cx = W / 2, y = B.big ? 96 : 70;
      band(a * 0.7, y - 22, 40);
      const sz = B.big ? 14 : 12; text(B.title, cx, y, sz, '#e6c77a', 'center', { alpha: a, spacing: 2.6, weight: 500 });
      const lw = (textW(B.title, sz, 500) + B.title.length * 2.6) * 0.32 * clamp(B.t * 2, 0, 1);
      uiDiamond(cx, y + 5, 1.3, UIC.gold, a); uiFade(cx + 4, cx + 4 + lw, y + 4.8, UI_RGB.gold, 0.7 * a); uiFade(cx - 4, cx - 4 - lw, y + 4.8, UI_RGB.gold, 0.7 * a);
      if (B.sub) text(B.sub, cx, y + 14, 6, '#c9bda2', 'center', { alpha: a, weight: 400, spacing: 0.6 });
    }
  }
  const G = SYS.gaunt; if (!G || state !== 'play' || G.wave < 0) return;
  const cx = W / 2, y = 5, n = G.waves.length;
  sysHudPanel(cx - 46, y, 92, 18);
  icon('x3_gaunt', cx - 42, y + 3, 12);
  text(`WAVE ${G.wave + 1} / ${n}`, cx - 27, y + 11.5, 6.4, '#f5e3b0', 'left', { weight: 600, spacing: 0.6 });
  const left = G.state === 'wave' ? Math.max(G.alive || 0, G.total - G.spawned) : 0;
  for (let i = 0; i < Math.min(G.total, 8); i++) uiDiamond(cx + 18 + i * 4.2 - (Math.min(G.total, 8) - 1) * 0, y + 9, 1.3, i < left ? '#e06050' : '#4a3e2c');
}
HOOKS.hud.push(() => {
  if (state === 'sysread') return sysRenderReader();
  sysRenderTrialHud(); sysRenderResult(); sysRenderGaunt();
  const V = SYS.vista;   // a bench's lore, set in the lower third while you sit
  if (V && V.lore && state === 'play') {
    const a = clamp((V.t - 1.8) * 1.2, 0, 1) * clamp(V.standing ? V.k * 2 - 1 : 1, 0, 1); if (a <= 0) return;
    const pg = LORE_PAGES[V.lore], L = sysPageLines(pg, 300, 5.8).slice(0, 5), h = 22 + L.length * 7.6, y = 36;
    sysHudPanel(W / 2 - 162, y, 324, h, a);
    text(pg.title || '', W / 2, y + 11, 7, UIC.gold, 'center', { alpha: a });
    L.forEach((l, i) => text(l, W / 2, y + 22 + i * 7.6, 5.8, UIC.body, 'center', { alpha: a, weight: 400 }));
  }
  if (V && !V.standing && state === 'play' && V.t > 2.5) text('any key to stand', W / 2, H - 5, 4.6, UIC.faint, 'center', { alpha: 0.5, weight: 400 });
});

// ================================================================== per-frame, room entry, input routing
HOOKS.update.push(dt => {
  if ((SYS.watchT -= dt) <= 0) { SYS.watchT = 0.5; sysWatchFlags(); }
  if (SYS.later.length) { for (const L of SYS.later) L.t -= dt; const due = SYS.later.filter(L => L.t <= 0); SYS.later = SYS.later.filter(L => L.t > 0); for (const L of due) L.fn(); }
  sysUpdateWarp(dt); sysUpdateReveal(dt); sysUpdateTrial(dt); sysUpdateGaunt(dt); sysUpdateVista(dt);
});
HOOKS.enter.push(def => {
  if (SYS.relayer) { SYS.relayer = false; renderRoomLayers(room); }
  if (SYS.doorLock && SYS.doorLock.room !== def.id) SYS.doorLock = null;
  if (SYS.trial && SYS.trial.room !== def.id) sysTrialAbort('The trial is abandoned');
  if (SYS.gaunt && SYS.gaunt.room !== def.id) SYS.gaunt = null;
  SYS.portents = []; if (SYS.vista && SYS.vista.p.room !== def.id) SYS.vista = null;
  if (SYS.reveal && SYS.reveal.p && !props.includes(SYS.reveal.p)) SYS.reveal = null;
  // gauntlet gates start open (after every spawn in the room has been built)
  for (const s of def.spawns || []) if (s.t === 'sys' && s.kind === 'gauntlet') for (const id of s.gates || []) sysGate(id, true);
  sysWatchFlags();
});
{
  const _press = onPressHook;
  onPressHook = (a, repeat) => {
    if (state === 'sysread') { audio(); if (!repeat || ['left', 'right'].includes(a)) sysReaderInput(a); buffered.delete(a); return; }
    if (state === 'map' && typeof mapInput === 'function' && mapInput(a, repeat)) { buffered.delete(a); return; }
    if (state === 'play' && !repeat && SYS.vista && !SYS.vista.standing && SYS.vista.t > 0.5) { sysStand(); if (a !== 'pause' && a !== 'map') { buffered.delete(a); return; } }
    const was = state; _press(a, repeat);
    if (was === 'play' && state === 'map' && typeof mapOpen === 'function') mapOpen();
  };
}

// ---- debug hooks for the headless harness (tools/shots/ks)
window.__sys = { SYS, LORE_PAGES, get roomObj() { return room; }, get state() { return state; }, get menu() { return menu; }, get mapv() { return MAPV; }, x3: () => x3(), cond: sysCond, completion: sysCompletion, totals: () => { _sysTotals = null; return sysTotals(); },
  stand: sysStand, gate: sysGate, openPage: sysOpenPage, useDoor: id => { const p = props.find(q => q.type === 'sys_door' && q.s.id === id); if (p) sysUseDoor(p); return !!p; },
  spawn: s => SPAWNS.sys(s, { cx: s.x * TILE + 8, fy: (s.y + 1) * TILE, key: 'dbg', def: room.def, id: room.id }),
  prop: (type, id) => props.find(q => q.type === type && (id === undefined || q.s.id === id || q.s.trial === id)) };
