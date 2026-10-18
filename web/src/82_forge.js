// ------------------------------------------------------------------ v17 — agent AREA: THE COLD FORGE (+ THE ASHEN THRESHOLD)
// Rooms: tools/regions/86_forge.py (CF1–CF13, CT1–CT2; E6's grate). Contract: docs/v17/FORGE_CONTRACT.md, notes for BOSS/FOES:
// docs/v17/forge_area.md. Art: art/gen_forge_env.py (tiles_forge, tiles_threshold, bg_forge_far/mid, bg_threshold_far/mid,
// cfa_s / cfa_m / cfa_furnace / cfa_doors / cfa_coals / cfa_gate / cfa_guard / cfa_bellows sheets).
// This file adds: the `forge` and `threshold` biomes (AREAS, music, lighting/grade, map colour, region card, kit/sys
// skins, tiers), the anvil mechanic (a heavy or finisher blow rings an anvil; its ring lifts the iron shutters keyed to it
// for a few seconds), hearth vents that flare across floors on the bellows' beat, the bellows' gusts, still black water,
// the two Unforged mini-arenas (seals), the Ledger Room puzzle, the Great Furnace and its doors (cfFurnaceOpen: the way to
// World 2 opens once the Hearthkeeper's Core is taken), the Ashen Threshold and its shut gate (CT_GATE, the World 2 hook),
// the Last Hearth's grate in E6 and its fire burning low after the furnace opens, lore pages cfa_1…cfa_13 and NPC lines.
// Every top-level name is prefixed cfa / CFA.

// ================================================================== biomes
Object.assign(AREAS, {
  forge: { name: 'The Cold Forge', ambient: 0.5, amb: 'dust', tint: '#05070a', map: '#46546a', lx: { amb: '158,172,206', lvl: 1.0 } },
  threshold: { name: 'The Ashen Threshold', ambient: 0.3, amb: 'dust', tint: '#7c8796', map: '#9aa4b2', lx: { amb: '206,212,224', lvl: 0.86 } },
});
Object.assign(SCALES, { forge: [0, 1, 5, 7, 8], threshold: [0, 2, 5, 7, 9] });
Object.assign(ROOTS, { forge: 41.2, threshold: 49 });
if (typeof MAP_COLS !== 'undefined') Object.assign(MAP_COLS, { forge: '#46546a', threshold: '#9aa4b2' });
if (typeof LX_BOOST !== 'undefined') Object.assign(LX_BOOST, { forge: 2.0, threshold: 1.0 });   // v17 shading: forge lifted (it measured a mean of ~10/255)
if (typeof GFX_MOOD !== 'undefined') Object.assign(GFX_MOOD, { forge: [[0.9, 0.96, 1.12], [1.02, 1.0, 0.98], 0.82, 1.08], threshold: [[0.95, 0.97, 1.05], [1.02, 1.02, 1.03], 0.66, 1.0] });
if (typeof BIOME_TIER !== 'undefined') Object.assign(BIOME_TIER, { forge: { hp: 1.85, dmg: 1.5, cin: 1.7 }, threshold: { hp: 1.85, dmg: 1.5, cin: 1.7 } });
if (typeof KIT_SKIN_OF !== 'undefined') Object.assign(KIT_SKIN_OF, { forge: 'iron', threshold: 'stone' });
if (typeof SYS_BIOME_SKIN !== 'undefined') Object.assign(SYS_BIOME_SKIN, { forge: 'metal', threshold: 'stone' });
Object.assign(PCOL, { cfa_soot: '22,24,30', cfa_cold: '200,214,236', cfa_steam: '196,206,214', cfa_ash: '214,220,228', cfa_spark: '255,214,150' });
const cfaIn = () => !!(room && (room.def.biome === 'forge' || room.def.biome === 'threshold'));
const cfaForge = () => !!(room && room.def.biome === 'forge');

// ================================================================== lore (Hallow Chronicle)
Object.assign(LORE_PAGES, {
  cfa_1: { region: 'forge', title: 'The Apprentice', text: 'A smith’s apprentice, by the burns on his hands. He came down through the grate with a lamp and a list.\nThe list reads: Find out why the forge went cold. Find the keeper. Ask him to light it again.\nThe lamp is out. The list is not finished.' },
  cfa_2: { region: 'forge', title: 'Chalk on the Flue', text: 'Scratched into the soot, low, the way you write when you are sitting down and cannot get up:\nThe fire up there is not the forge’s fire. It is only a promise someone keeps.\nDown here they stopped keeping it.' },
  cfa_3: { region: 'forge', title: 'The Rack-Master’s Tally', text: 'Racks one to forty: blades for the Hallow’s host, hilted, unquenched.\nRacks forty to four hundred: the same.\nNot one of them was ever carried out. The host they were made for was already ash when the last was hung.' },
  cfa_4: { region: 'forge', title: 'The Reject Pile', text: 'Every blade that cracked in the quench was thrown here. The smiths said a blade that breaks has told you a lie, and you do not keep liars.\nThe pile has been moving for a long time. It has taught itself to hold a sword.' },
  cfa_5: { region: 'forge', title: 'The Quench', text: 'Hot iron plunged into still water: that is how a blade learns to be hard.\nThe cisterns have not been warm in an age. They remember every blade anyway. Sometimes, when you stand very still, they hiss.' },
  cfa_6: { region: 'forge', title: 'The Quenchmaster', text: 'He kept the water. He tasted it every morning for iron and for salt, and wrote down what it said.\nThe last line in his book is only: It has gone still. I am going in to ask it why.' },
  cfa_7: { region: 'forge', title: 'On the Bellows', text: 'Stamped in an iron plate by the stair:\nThe bellows breathe for the fire, and the fire breathes for the Hallow. Strike the anvil and the shutters hear it.\nSomeone has scratched underneath: The fire is out. They are still breathing. Who for?' },
  cfa_8: { region: 'forge', title: 'Tempering', text: 'A blade is tempered by heating it again, gently, after the quench, so that it will bend before it breaks.\nThe ones that came down here were not tempered. They were only made to remember.' },
  cfa_9: { region: 'forge', title: 'The Great Anvil', text: 'The first sword of the Hallow was beaten on this anvil, by a smith with no name, in front of a fire no one had to keep.\nThe keeper came later. The keeper always comes later.' },
  cfa_10: { region: 'forge', title: 'The Forge-Master’s Ledger', text: 'Every blade begins as the Ox: the raw bar, heavy and patient. Then the Flame, which softens it. Then the Hammer, which tells it what to be.\nOx, flame, hammer. Practise it on the small anvils until your arm knows the order before you do.' },
  cfa_11: { region: 'threshold', title: 'Behind the Furnace', text: 'The furnace was never the forge’s heart. It was a door, and the fire was the lock.\nThe keeper did not guard the fire. He was the fire, stood in a doorway so that nothing on the other side would come through.\nNothing has. Not yet.' },
  cfa_12: { region: 'threshold', title: 'The Last Gate', text: 'From the causeway the gate looks close. It is not. The longer you walk toward it the larger it becomes, and it does not seem to get nearer.\nThere is light behind it with no sun to make it. Ash falls upward here, as if the world beyond were breathing in.' },
  cfa_13: { region: 'threshold', title: 'Carved at the Causeway', text: 'In a hand older than the Hallow’s:\nWe built the forge at the edge of the world, so that whatever was made here would be the first thing to meet whatever came.\nWe never learned what would come. We only learned to keep the fire lit.' },
});

// ================================================================== sound
const cfaSfx = {
  ring: (note = 0, k = 1) => {   // a struck anvil: inharmonic partials, a long cold tail
    const f = 392 * Math.pow(2, [0, 2, -5, 3, -7][note % 5] / 12);
    for (const [m, v, d] of [[1, 0.14, 2.6], [2.76, 0.07, 1.8], [5.4, 0.045, 1.2], [8.93, 0.03, 0.8], [0.5, 0.05, 2.0]]) tone(f * m, d * k, v * k, 'sine', 0.998);
    noise(0.06, 5200, 2, 0.25 * k, 'highpass');
  },
  great: () => { for (const [f, v, d] of [[65.4, 0.22, 4.5], [98, 0.12, 3.8], [180.5, 0.08, 3], [353, 0.05, 2.4], [583, 0.03, 1.8]]) tone(f, d, v, 'sine', 0.996); noise(0.1, 3000, 1.5, 0.3, 'bandpass'); },
  clank: () => { tone(220, 0.12, 0.08, 'square', 0.6); noise(0.08, 2600, 1.4, 0.18, 'bandpass'); },
  tick: (hi = false) => tone(hi ? 1480 : 1180, 0.05, 0.035, 'triangle', 0.9),
  grind: (v = 1) => { noise(1.4, 120, 0.7, 0.35 * v, 'lowpass', 0.8); tone(41, 1.4, 0.12 * v, 'sawtooth', 1.04); noise(1.0, 900, 3, 0.05 * v, 'bandpass', 1.3); },
  slam: () => { noise(0.4, 160, 0.8, 0.5, 'lowpass'); tone(55, 0.5, 0.25, 'square', 0.5); },
  hiss: (v = 1) => noise(0.6, 3600, 0.7, 0.12 * v, 'highpass', 0.6),
  roar: (v = 1) => { noise(0.5, 420, 0.6, 0.32 * v, 'lowpass', 1.4); noise(0.35, 1300, 0.8, 0.1 * v, 'bandpass', 0.7); },
  breath: (v = 1) => { noise(1.1, 260, 0.6, 0.22 * v, 'lowpass', 1.6); tone(70, 0.9, 0.05 * v, 'triangle', 1.3); },
  creak: () => { tone(140 + rand(-20, 20), 0.45, 0.04, 'sawtooth', 1.25); noise(0.35, 500, 3, 0.04, 'bandpass', 1.3); },
  drip: () => { tone(1100 + rand(-180, 180), 0.09, 0.025, 'sine', 0.55); },
  chime: () => [523, 659, 784, 1046].forEach((f, i) => tone(f, 1.6, 0.05, 'sine', 1, i * 0.12)),
  wrong: () => { tone(185, 0.6, 0.08, 'sawtooth', 0.8); tone(196, 0.6, 0.08, 'sawtooth', 0.8); },
  bars: () => { noise(0.5, 300, 0.8, 0.4, 'lowpass'); tone(110, 0.3, 0.15, 'square', 0.6); tone(740, 0.5, 0.04, 'triangle', 0.97, 0.05); },
  wind: () => noise(2.6, 500, 0.5, 0.06, 'bandpass', 0.7),
  gate: () => { for (const [f, v] of [[49, 0.2], [73.4, 0.1], [98, 0.08]]) tone(f, 5, v, 'sine', 1); noise(2.5, 200, 0.5, 0.1, 'lowpass'); },
};

// ================================================================== music: the forge is cold and slow; the threshold opens up
// The generic drone keeps going (SCALES/ROOTS above); its bell layer is held (MUSIC.nextNote) while this plays on MUSIC.gain.
const CFAM = { next: 0, beat: 0, mode: null, bar: 0 };
function cfaMusicMode() {
  if (!room || !cfaIn() || muted || !AC || typeof MUSIC === 'undefined' || !MUSIC.gain) return null;
  if (state === 'title' || state === 'dead' || state === 'ending' || state === 'cine') return null;
  if (boss && boss.active && boss.alive) return null;   // the boss fight's score is the boss's own
  if (room.def.biome === 'threshold') return room.def.vista || (typeof SYS !== 'undefined' && SYS.vista) ? 'vista' : 'threshold';
  return typeof SYS !== 'undefined' && SYS.vista ? 'vista' : 'forge';
}
function cfaMusicTick() {
  const mode = cfaMusicMode();
  if (mode !== CFAM.mode) { CFAM.mode = mode; CFAM.beat = 0; CFAM.next = AC ? AC.currentTime + 0.4 : 0; }
  if (!mode) return;
  MUSIC.nextNote = AC.currentTime + 0.5;
  const out = MUSIC.gain, f = (b, n) => b * Math.pow(2, n / 12);
  while (CFAM.next < AC.currentTime + 0.12) {
    const d = Math.max(0, CFAM.next - AC.currentTime), b = CFAM.beat;
    if (mode === 'forge') {
      // 8-beat bars of 0.9 s: a far anvil on 1 (and a ghost on 6), a low two-note bell figure, sparse high glints
      const root = ROOTS.forge * 4, fig = [[0, 7], [5, 8], [0, 1], [-2, 5]][Math.floor(b / 8) % 4];
      if (b % 8 === 0) { for (const [m, v, du] of [[1, 0.03, 2.4], [2.76, 0.014, 1.6], [5.4, 0.008, 1]]) tone(f(root * 2, fig[0]) * m, du, v, 'sine', 0.998, d, out); tone(f(root / 2, fig[0]), 3.4, 0.05, 'triangle', 1, d, out); }
      if (b % 8 === 3) tone(f(root, fig[1]), 2.6, 0.03, 'sine', 1, d, out);
      if (b % 8 === 5 && Math.random() < 0.6) { tone(f(root * 2, fig[0]) * 2.76, 1.2, 0.006, 'sine', 0.998, d, out); }
      if (b % 16 === 12 && Math.random() < 0.5) tone(f(root * 4, [0, 3, 7, 12][irand(0, 3)] + fig[0]), 2.2, 0.012, 'sine', 1, d, out);
      CFAM.next += 0.9;
    } else {
      // the threshold: open fifths, slow and bright, rising; ambient only (no beat) on the vista
      const root = ROOTS.threshold * 4, chords = [[0, 7, 14], [5, 12, 16], [-3, 4, 12], [2, 9, 14]], ch = chords[Math.floor(b / 4) % 4];
      if (b % 4 === 0) { ch.forEach((n, i) => tone(f(root, n), 5.5, mode === 'vista' ? 0.014 : 0.018, 'sine', 1, d + i * 0.25, out)); tone(f(root / 2, ch[0]), 6, 0.035, 'triangle', 1, d, out); }
      if (mode !== 'vista' && b % 4 === 2 && Math.random() < 0.7) tone(f(root * 2, ch[irand(0, 2)] + 12), 2.4, 0.01, 'sine', 1, d, out);
      CFAM.next += 1.4;
    }
    CFAM.beat++;
  }
}
HOOKS.renderTop.push(() => { try { cfaMusicTick(); } catch (e) {} });

// ================================================================== per-room state
const CFA = { roomObj: null };
const CFA_KIND = {};
let cfaHid = 0;
function cfaReset() {
  Object.assign(CFA, { roomObj: room, t: 0, anvils: [], shut: {}, vents: [], bellows: [], gusts: [], seals: [], rings: [], back: [], front: [],
    baked: false, backRef: null, frontRef: null, still: null, ripples: [], ledger: null, furnace: null, drops: [], soot: [], steams: [], hint: CFA.hint || {},
    prompt: 0, later: [], vlx: [] });
  if (typeof cfArena !== 'undefined') cfArena.bellows.length = 0;
}
function cfaEnsure() { if (CFA.roomObj !== room) cfaReset(); }
const cfaVis = (x, y, m = 40) => x > cam.x - m && x < cam.x + W + m && y > cam.y - m && y < cam.y + H + m;
const cfaR = (x, y, w, h, c) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h)); };
function cfaProp(s, c, o = {}) {
  const p = { type: 'cfa_' + s.kind, x: c.cx, y: c.fy, face: s.face || 1, s, seed: hash2(s.x * 7 + 3, s.y * 13 + 1), anim: { update() {} }, ...o };
  props.push(p); return p;
}
// a frame of one of the forge sheets, bottom-centre anchored; false when the art is missing (callers draw a fallback)
function cfaSpr(name, tag, i, x, y, face = 1, opt = {}) {
  const sh = sheet(name); if (!sh.ok || !sh.has(tag)) return false;
  const t = sh.tag(tag), n = t.to - t.from + 1; drawSprite(sh, t.from + ((i % n) + n) % n, x, y, face, { bottom: true, ...opt }); return true;
}
function cfaFrames(name, tag) { const sh = sheet(name); if (!sh.ok || !sh.has(tag)) return 0; const t = sh.tag(tag); return t.to - t.from + 1; }
// paint a sheet frame straight into the room's back (or front) canvas, once (the canvases are rebuilt when a floor breaks)
function cfaPaint(ctx, name, tag, i, x, y, face = 1) {
  const sh = sheet(name); if (!sh.ok || !sh.has(tag)) return true;
  const img = sh.img; if (!img.complete || !img.naturalWidth) return false;
  const f = sh.frames[sh.first(tag) + i], X = Math.round(x - f.w / 2), Y = Math.round(y - f.h);
  ctx.save();
  if (face < 0) { ctx.translate(X * 2 + f.w, 0); ctx.scale(-1, 1); }
  ctx.drawImage(img, f.x, f.y, f.w, f.h, X, Y, f.w, f.h); ctx.restore(); return true;
}
function cfaBake() {
  if (!room || CFA.roomObj !== room) return;
  if (CFA.baked && room.back === CFA.backRef && room.front === CFA.frontRef) return;
  const bx = room.back.getContext('2d'), fx2 = room.front.getContext('2d');
  for (const q of [...CFA.back, ...CFA.front]) { const sh = sheet(q.sh); if (sh.ok && sh.has(q.tag) && !(sh.img.complete && sh.img.naturalWidth)) return; }   // not decoded yet: next frame
  for (const q of CFA.back) q.fn ? q.fn(bx) : cfaPaint(bx, q.sh, q.tag, q.i || 0, q.x, q.y, q.face || 1);
  for (const q of CFA.front) q.fn ? q.fn(fx2) : cfaPaint(fx2, q.sh, q.tag, q.i || 0, q.x, q.y, q.face || 1);
  CFA.baked = true; CFA.backRef = room.back; CFA.frontRef = room.front;
}

// ================================================================== the anvils
// An anvil rings on a heavy blow, a finisher, a plunge or a slam (light blows only clank). Its ring lifts every iron shutter
// keyed to it (kit gates by id) for `dur` seconds, with a ticking countdown; then they fall again. `seq` anvils (the Ledger
// Room) feed an ordered puzzle instead. The great anvil in the Anvil Court rings for nothing but itself.
function cfaHeavy(info) {
  if (!info) return false;
  if (info.kind === 'heavy' || info.big) return true;
  try { if (typeof isFinisher === 'function' && isFinisher(P.state)) return true; } catch (e) {}
  return P.state === 'plunge' || P.state === 'slam';
}
const CFA_MARK_COL = { hammer: '200,214,236', tongs: '200,214,236', flame: '255,170,90', ox: '214,200,170', crown: '230,224,210' };
function cfaRing(p) {
  p.ring = 1; p.cool = 0.45; CFA.rings.push({ x: p.x, y: p.y - (p.s.great ? 34 : p.s.small ? 12 : 18), t: 0, big: !!p.s.great, col: CFA_MARK_COL[p.s.mark] || '200,214,236' });
  if (p.s.great) { cfaSfx.great(); shake = Math.max(shake, 3); } else cfaSfx.ring(p.s.note || 0, p.s.small ? 0.7 : 1);
  for (let i = 0; i < 10; i++) particles.push({ x: p.x + rand(-8, 8), y: p.y - (p.s.small ? 10 : 16), vx: rand(-90, 90), vy: -rand(30, 120), g: 420, life: rand(0.3, 0.6), kind: 'cfa_spark' });
  for (const id of p.s.keys || []) cfaOpenShutter(id, p.s.dur || 6);
  if (p.s.seq) cfaLedgerHit(p);
  if (p.s.great && !SAVE.flags['cf:great']) { SAVE.flags['cf:great'] = 1; setTimeout(() => { if (room && room.id === 'CF7') toast('The great anvil answers with a note so low you feel it in your teeth. Somewhere in the forge, the shutters shiver.', 4.5); }, 600); }
  if (p.s.keys && p.s.keys.length && !SAVE.flags['cf:rang']) { SAVE.flags['cf:rang'] = 1; setTimeout(() => toast('The anvil rings. Somewhere an iron shutter answers — for a few breaths.', 3.6), 300); }
}
function cfaOpenShutter(id, dur) {
  if (!KIT.byId[id]) return;
  if (CFA.shut[id] && CFA.shut[id].perm) return;
  kitForce(id, true);
  CFA.shut[id] = { t: dur, total: dur, last: Math.ceil(dur) };
}
function cfaShutTick(dt) {
  for (const [id, S] of Object.entries(CFA.shut)) {
    if (S.perm) { kitForce(id, true); continue; }
    S.t -= dt;
    const o = KIT.byId[id];
    if (o && S.t > 0) {
      const step = S.t < 2 ? Math.ceil(S.t * 3) : Math.ceil(S.t);
      if (step !== S.last) { S.last = step; if (cfaVis(o.x, o.y, 120)) cfaSfx.tick(S.t < 2); }
    }
    if (S.t <= 0) { kitForce(id, null); delete CFA.shut[id]; }
  }
}
CFA_KIND.anvil = (s, c) => {
  const great = !!s.great, small = !!s.small, hw = great ? 30 : small ? 9 : 14, hh = great ? 34 : small ? 14 : 22;
  const p = cfaProp(s, c, { ring: 0, cool: 0, lit: 0 });
  p.hurtbox = () => rect(p.x - hw, p.y - hh, p.x + hw, p.y);
  p.onHit = info => {
    if (p.cool > 0) return;
    if (cfaHeavy(info)) cfaRing(p);
    else {
      p.cool = 0.15; cfaSfx.clank();
      for (let i = 0; i < 4; i++) particles.push({ x: p.x + rand(-6, 6), y: p.y - hh + 4, vx: rand(-60, 60), vy: -rand(20, 70), g: 420, life: 0.3, kind: 'cfa_spark' });
      if (!CFA.hint.light) { CFA.hint.light = 1; toast('The anvil only clanks. It wants a heavier blow — a heavy, a finisher, a plunge.', 3.6); }
    }
  };
  p.update = dt => {
    p.cool = Math.max(0, p.cool - dt); p.ring = Math.max(0, p.ring - dt * 0.8);
    const open = (s.keys || []).some(id => CFA.shut[id]);
    p.lit = approach(p.lit, open || p.ring > 0.2 || p.seqLit ? 1 : 0, dt * 3);
    if (p.ring > 0.05) addLight(p.x, p.y - hh, 50 + 60 * p.ring, CFA_MARK_COL[s.mark] || '200,214,236', 0.65 * p.ring);
  };
  p.draw = () => {
    if (!cfaVis(p.x, p.y, 60)) return;
    const tag = great ? null : small ? 'anvil_s' : 'anvil';
    const k = p.ring > 0.4 ? 1 : 0;
    if (great) { if (!cfaSpr('cfa_ganvil', 'idle', 0, p.x, p.y + 1)) cfaDrawAnvil(p.x, p.y, 2.2); }
    else if (!cfaSpr(small ? 'cfa_s' : 'cfa_m', tag, k, p.x, p.y + 1, p.face)) cfaDrawAnvil(p.x, p.y, small ? 0.7 : 1);
    if (s.mark && !great) cfaDrawMark(s.mark, p.x, p.y - (small ? 7 : 11), p.lit, small ? 1 : 1);
  };
  CFA.anvils.push(p);
};
function cfaDrawAnvil(x, y, k) {   // fallback (procedural) anvil
  const w = 28 * k, h = 18 * k;
  cfaR(x - w * 0.35, y - h * 0.45, w * 0.7, h * 0.45, '#131822');
  cfaR(x - w / 2, y - h, w, h * 0.32, '#1e2734'); cfaR(x - w / 2, y - h, w, 1, '#62748f');
  cfaR(x - w / 2 - 6 * k, y - h + 2, 6 * k, 3, '#18202b');
}
function cfaDrawMark(mark, x, y, lit, sc = 1) {   // the sign stamped on an anvil / a shutter's lintel
  if (cfaSpr('cfa_s', 'mark_' + mark, 0, x, y + 4)) {
    if (lit > 0.02) drawGlow(() => { g.globalAlpha = lit * 0.9; cfaSpr('cfa_s', 'mark_' + mark, 1, x, y + 4); g.globalAlpha = 1; });
    return;
  }
  const c = lit > 0.3 ? `rgb(${CFA_MARK_COL[mark]})` : '#415066';
  const R = (a, b, w, h) => cfaR(x + a, y + b, w, h, c);
  if (mark === 'hammer') { R(-3, -3, 6, 2); R(-1, -1, 2, 4); }
  else if (mark === 'tongs') { R(-3, -3, 1, 6); R(2, -3, 1, 6); R(-2, 0, 4, 1); }
  else if (mark === 'flame') { R(-1, -3, 2, 1); R(-2, -2, 4, 2); R(-1, 0, 2, 2); }
  else if (mark === 'ox') { R(-3, -3, 1, 2); R(2, -3, 1, 2); R(-2, -1, 4, 3); }
  else { R(-3, -1, 6, 3); R(-3, -3, 1, 2); R(0, -3, 1, 2); R(2, -3, 1, 2); }
}
CFA_KIND.mark = (s, c) => {   // over a shutter: the sign of the anvil that lifts it (glows while it's held open)
  const p = cfaProp(s, c, { y: s.y * TILE + 1, lit: 0 });
  p.update = dt => { const id = (KIT.objs.find(o => o.kind === 'gate' && Math.abs(o.x - p.x) < 9) || {}).id; p.lit = approach(p.lit, id && CFA.shut[id] ? 1 : 0, dt * 3); };
  p.draw = () => cfaDrawMark(s.mark, p.x, p.y + 6, p.lit);
};
// ---- the shutters: the kit's iron gates, drawn as riveted forge shutters with a countdown bar while held open
function cfaDrawShutter(o) {
  const X = o.x - 7, top = o.top, y1 = o.d.y1, S = CFA.shut[o.id];
  if (y1 - top > 1) {
    cfaR(X, top, 14, y1 - top, '#10151d');
    for (let y = y1 - 6; y > top; y -= 7) { cfaR(X, y, 14, 1, '#05070a'); cfaR(X, y + 1, 14, 1, '#252f3e'); }
    cfaR(X, top, 1, y1 - top, '#2d3849'); cfaR(X + 13, top, 1, y1 - top, '#06080b');
    for (let y = y1 - 4; y > top + 2; y -= 14) { cfaR(X + 3, y, 1, 1, '#4f6079'); cfaR(X + 10, y, 1, 1, '#4f6079'); }
    cfaR(X, y1 - 3, 14, 3, '#0a0d12'); for (let i = 0; i < 4; i++) cfaR(X + 1 + i * 4, y1 - 1, 2, 2, '#1e2734');   // the teeth
  }
  if (S && !S.perm) {   // the ring is fading: a cold bar under the lintel shrinks as the time runs out
    const k = clamp(S.t / S.total, 0, 1);
    drawGlow(() => { g.globalAlpha = 0.85; cfaR(X + 1, top - 2, 12 * k, 1, S.t < 2 && Math.floor(time * 8) % 2 ? '#ffffff' : '#b7c0cb'); g.globalAlpha = 1; });
  }
}
function cfaSkinShutters() {
  for (const o of KIT.objs) if (o.kind === 'gate' && o.skin !== 'neon') o.draw = () => cfaDrawShutter(o);
}

// ================================================================== hearth vents (on the bellows' beat) and the bellows
// vents: a strip of floor grates x..x+w; every `period` s a flare runs across them (`wave` s from first to last cell),
// each cell burning `on` s. A warm glow and a hiss warn half a second before. The bellows exhale on the same clock.
CFA_KIND.vents = (s, c) => {
  const v = { x0: s.x * TILE, n: s.w || 4, y: c.fy, per: s.period || 3, wave: s.wave || 1, ph: s.phase || 0, on: s.on || 0.55, h: (s.h || 3) * TILE, id: ++cfaHid, lastHiss: -1, lastRoar: -1 };
  CFA.vents.push(v);
  const p = cfaProp(s, c, { glow: true, v });
  const cellK = (i, t) => { const k = ((t - v.ph - (i / Math.max(1, v.n - 1)) * v.wave) % v.per + v.per) % v.per; return k; };
  p.update = dt => {
    const t = CFA.t, vis = cfaVis(v.x0 + v.n * 8, v.y, 80);
    let lit = 0, lx = 0, any = false, warn = false;
    for (let i = 0; i < v.n; i++) {
      const k = cellK(i, t), cx = v.x0 + i * TILE + 8;
      if (k < v.on) {
        any = true; lit++; lx += cx;
        const hgt = v.h * Math.min(1, k / 0.08) * (1 - Math.max(0, (k - v.on * 0.6) / (v.on * 0.4)) * 0.6);
        if (Math.random() < 0.35) particles.push({ x: cx + rand(-5, 5), y: v.y - rand(0, hgt), vx: rand(-12, 12), vy: -rand(60, 140), life: rand(0.2, 0.45), kind: 'fire' });
        if (overlap(rect(cx - 7, v.y - hgt, cx + 7, v.y), playerHurtbox())) {
          const cyc = Math.floor((t - v.ph - (i / Math.max(1, v.n - 1)) * v.wave) / v.per);
          hurtPlayer(Math.round(24 * NGP.dmg), P.x < cx ? -1 : 1, v.id * 100000 + cyc, { hazard: true, fire: true, src: v, kit: 'vent' });
        }
      } else if (k > v.per - 0.5) warn = true;
    }
    const cyc = Math.floor((t - v.ph) / v.per);
    if (vis && warn && v.lastHiss !== cyc) { v.lastHiss = cyc; cfaSfx.hiss(0.6); }
    if (vis && any && v.lastRoar !== cyc) { v.lastRoar = cyc; cfaSfx.roar(0.8); }
    if (lit) addLight(lx / lit, v.y - 24, 40 + lit * 9, '255,130,50', 0.85);
    v.any = any; v.warn = warn;
  };
  p.draw = () => {
    if (!cfaVis(v.x0 + v.n * 8, v.y, 120)) return;
    const t = CFA.t;
    for (let i = 0; i < v.n; i++) {
      const x = v.x0 + i * TILE, k = cellK(i, t), hot = k < v.on ? 1 : k > v.per - 0.5 ? (k - (v.per - 0.5)) / 0.5 : Math.max(0, 1 - (k - v.on) / 0.8);
      if (!cfaSpr('cfa_s', 'vent', 0, x + 8, v.y + 2)) { cfaR(x + 1, v.y - 2, 14, 2, '#0a0d12'); for (let j = 0; j < 4; j++) cfaR(x + 2 + j * 4, v.y - 2, 2, 1, '#252f3e'); }
      if (hot > 0.02) drawGlow(() => {
        g.globalAlpha = Math.min(1, hot) * 0.9;
        for (let j = 0; j < 4; j++) cfaR(x + 2 + j * 4, v.y - 2, 2, 1, hot > 0.7 ? '#ffd27e' : '#c96a22');
        g.globalAlpha = 1;
        if (k < v.on) {   // the flare: tongues of fire, white-gold at the root, ragged dark tips; each column flickers
          const hgt = v.h * Math.min(1, k / 0.08) * (1 - Math.max(0, (k - v.on * 0.6) / (v.on * 0.4)) * 0.7);
          for (let col = 1; col < 15; col++) {
            const edge = 1 - Math.abs(col - 7.5) / 8, n = 0.5 + 0.5 * Math.sin(time * 31 + col * 2.3 + i * 5.1) * Math.sin(time * 13 + col * 0.7);
            const hh2 = Math.round(hgt * edge * (0.45 + 0.55 * n)); if (hh2 < 2) continue;
            const xx = x + col;
            for (let yy = 0; yy < hh2; yy++) {
              const f = yy / hh2;
              const c = f < 0.18 ? '#fff0c4' : f < 0.42 ? '#ffd27e' : f < 0.68 ? '#e88a30' : f < 0.88 ? '#a3531f' : '#5a311c';
              g.globalAlpha = f > 0.88 ? 0.55 : 0.95; g.fillStyle = c; g.fillRect(xx, v.y - 2 - yy, 1, 1);
            }
          }
          g.globalAlpha = 1;
        }
      });
    }
  };
};
// bellows: a great leather bellows hung on chains from the roof. It breathes on `period`; on the exhale it puffs soot from
// its nozzle and (with `gust`) pushes the player along the gallery. Arena bellows (CF8) hang slack and breathe slowly.
CFA_KIND.bellows = (s, c) => {
  const top = s.y * TILE, len = (s.len || 3) * TILE, b = { x: c.cx, top, y: top + len, per: s.period || 6, ph: s.phase || 0, gust: s.gust || null, arena: !!s.arena, k: 0, ex: 0, last: -1 };
  CFA.bellows.push(b);
  if (s.arena && typeof cfArena !== 'undefined') cfArena.bellows.push({ x: b.x, y: b.y + 64 });
  const p = cfaProp(s, c, { y: b.y + 72, b });
  p.update = dt => {
    const k = ((CFA.t - b.ph) % b.per + b.per) % b.per / b.per;   // 0..1 through the breath
    // inhale slowly (0 → 0.62), exhale hard (0.62 → 0.78), rest
    b.fill = k < 0.62 ? k / 0.62 : k < 0.78 ? 1 - (k - 0.62) / 0.16 : 0;
    b.ex = k >= 0.62 && k < 0.8 ? 1 : 0;
    const cyc = Math.floor((CFA.t - b.ph) / b.per);
    if (b.ex && b.last !== cyc) {
      b.last = cyc;
      if (cfaVis(b.x, b.y, 140)) { cfaSfx.breath(b.arena ? 0.5 : 1); if (Math.random() < 0.4) cfaSfx.creak(); }
      for (let i = 0; i < 18; i++) particles.push({ x: b.x + rand(-3, 3), y: b.y + 66, vx: rand(-50, 50) + (b.gust ? Math.sign(b.gust.vx) * rand(20, 90) : 0), vy: rand(20, 90), g: -10, life: rand(0.8, 1.6), kind: 'cfa_soot' });
    }
    if (b.gust && b.ex) {
      const G = b.gust, r = { x0: G.x * TILE, x1: (G.x + G.w) * TILE, y0: (G.y || 0) * TILE, y1: ((G.y || 0) + (G.h || 8)) * TILE };
      if (P.x > r.x0 && P.x < r.x1 && P.y - 12 > r.y0 && P.y - 12 < r.y1 && !['hook', 'rest', 'dead', 'rise'].includes(P.state)) P.pushVx = (P.pushVx || 0) + G.vx * (P.ground ? 1 : 1.15);
      if (Math.random() < 0.6) { const yy = rand(r.y0, r.y1); CFA.drops.push({ x: G.vx < 0 ? r.x1 : r.x0, y: yy, vx: G.vx * 2.4, life: rand(0.4, 0.8), len: rand(6, 14), streak: true }); }
    }
  };
  p.draw = () => {
    if (!cfaVis(b.x, b.y, 100)) return;
    // chains from the roof to the yoke
    for (const dx of [-9, 9]) for (let y = b.top; y < b.y; y += 3) { cfaR(b.x + dx - 1, y, 3, 1, '#0e1219'); cfaR(b.x + dx, y + 1, 1, 1, '#252f3e'); }
    const nf = cfaFrames('cfa_bellows', 'breath'), fi = nf ? Math.min(nf - 1, Math.round((b.fill || 0) * (nf - 1))) : 0;
    if (!cfaSpr('cfa_bellows', 'breath', fi, b.x, b.y + 72)) {
      const w = 22 + 12 * (b.fill || 0);
      cfaR(b.x - 18, b.y, 36, 4, '#131822');
      g.fillStyle = '#1d1a1b'; g.beginPath(); g.ellipse(b.x, b.y + 30, w / 2, 26, 0, 0, 6.29); g.fill();
      for (let i = 1; i < 6; i++) cfaR(b.x - w / 2 + 3, b.y + 6 + i * 8, w - 6, 1, '#3d2419');
      cfaR(b.x - 2, b.y + 56, 4, 14, '#0e1219');
    }
  };
};
// a cold draught's streaks (the bellows' gusts), drawn over everything in the gallery
function cfaDrawStreaks() {
  for (const q of CFA.drops) if (q.streak) { const a = Math.min(1, q.life * 3) * 0.35; g.fillStyle = `rgba(200,214,236,${a})`; const d = Math.sign(q.vx); for (let i = 0; i < q.len; i++) g.fillRect(Math.round(q.x - d * i), Math.round(q.y), 1, 1); }
}

// ================================================================== the Unforged's mini-arenas: iron bars that fall behind you
// A seal closes once you're inside and its foe stands; it lifts when the foe falls (for good: SAVE.flags[flag]).
CFA_KIND.seal = (s, c) => {
  const horiz = !!s.horiz, x0 = s.x * TILE, w = (s.w || 1) * TILE, h = (s.h || 3) * TILE;
  const r = horiz ? { x0, x1: x0 + w, y0: s.y * TILE + 4, y1: s.y * TILE + 12 } : { x0: x0 + 3, x1: x0 + 13, y0: c.fy - h, y1: c.fy };
  const S = { s, r, k: 0, closed: false, done: !!SAVE.flags[s.flag], horiz };
  CFA.seals.push(S);
  const d = { x0: r.x0, x1: r.x1, y0: r.y0, y1: r.y1, on: () => S.closed && S.k > 0.5 };
  room.dyn.push(d);
  const p = cfaProp(s, c, { S });
  p.update = dt => {
    const foes = enemies.filter(e => e.alive && (e.type === s.foe || e.cfType === s.foe));
    if (!S.done && !S.closed && foes.length) {
      const inside = horiz ? P.y > r.y1 + 3 * TILE && P.ground : P.x < r.x0 - 2.5 * TILE;
      if (inside) { S.closed = true; cfaSfx.bars(); shake = Math.max(shake, 4); toast('Iron bars slam down behind you.', 2.2); }
    }
    if (S.closed && !foes.length) {
      S.closed = false; S.done = true; SAVE.flags[s.flag] = 1; saveGame(); cfaSfx.bars(); cfaSfx.chime();
      if (s.gate) toast('The bars lift. The way back is open.', 2.6);
    }
    S.k = approach(S.k, S.closed ? 1 : 0, dt * (S.closed ? 6 : 1.5));
  };
  p.draw = () => {
    if (S.k < 0.02) return;
    if (horiz) { const n = Math.round(w / 4); for (let i = 0; i < n; i++) { const xx = r.x0 + i * 4 + 1; cfaR(xx, r.y0, 2, 8 * S.k, '#131822'); cfaR(xx, r.y0, 1, 8 * S.k, '#364356'); } cfaR(r.x0, r.y0 + 2, w, 2, '#0a0d12'); return; }
    const y1 = r.y0 + (r.y1 - r.y0) * S.k;
    for (const bx of [r.x0, r.x0 + 4, r.x0 + 8]) { cfaR(bx, r.y0, 2, y1 - r.y0, '#131822'); cfaR(bx, r.y0, 1, y1 - r.y0, '#364356'); cfaR(bx - 1, y1 - 3, 4, 3, '#0a0d12'); }
    cfaR(r.x0 - 2, r.y0, 14, 3, '#0e1219');
  };
};

// ================================================================== the Ledger Room: ox, flame, hammer
CFA_KIND.ledger = (s, c) => {
  CFA.ledger = { s, prog: 0, bad: 0, done: !!SAVE.flags[s.flag] };
  if (CFA.ledger.done) CFA.shut[s.gate] = { perm: true };
  cfaProp(s, c, { draw() {} });
};
function cfaLedgerHit(p) {
  const L = CFA.ledger; if (!L) return;
  if (L.done) { cfaSfx.chime(); return; }
  const want = L.s.order[L.prog];
  if (p.s.id === want) {
    L.prog++; p.seqLit = true;
    if (L.prog >= L.s.order.length) {
      L.done = true; SAVE.flags[L.s.flag] = 1; saveGame();
      CFA.later.push({ t: 0.5, fn: () => { cfaSfx.chime(); CFA.shut[L.s.gate] = { perm: true }; kitForce(L.s.gate, true); toast('The three notes hang in the air together. The reliquary’s shutter grinds up.', 4); } });
    }
  } else {
    cfaSfx.wrong(); L.prog = 0; L.bad++;
    for (const a of CFA.anvils) a.seqLit = false;
    if (L.bad >= 3 && !CFA.hint.ledger) { CFA.hint.ledger = 1; toast('The ledger on the stand: “Ox, then flame, then hammer.” Each small anvil bears its sign.', 5); }
  }
}

// ================================================================== decor and atmosphere
const CFA_DECO = {   // tag -> [sheet, back?, y offset]
  scrap: ['cfa_s', false], bucket: ['cfa_s', false], ingots: ['cfa_s', false], tongs_rack: ['cfa_m', true], trough_blades: ['cfa_s', false],
  quench_rack: ['cfa_m', true], slag_cart: ['cfa_m', false], ledger_desk: ['cfa_m', true], broken_rack: ['cfa_m', true], temper_rack: ['cfa_m', true],
  flue_mouth: ['cfa_m', true], pipe: ['cfa_m', false],
};
CFA_KIND.deco = (s, c) => {
  const D = CFA_DECO[s.tag] || ['cfa_s', false], back = s.back ?? D[1];
  (back ? CFA.back : CFA.front).push({ sh: D[0], tag: s.tag, x: c.cx, y: c.fy + 1, face: s.face || 1 });
};
CFA_KIND.pipe = (s, c) => CFA.front.push({ sh: 'cfa_m', tag: 'pipe', x: c.cx, y: c.fy + 1, face: s.face || 1 });
CFA_KIND.rack = (s, c) => (s.back === false ? CFA.front : CFA.back).push({ sh: 'cfa_rack', tag: s.small ? 'rack_s' : ['rack_a', 'rack_b', 'rack_c'][s.v || 0], x: c.cx, y: c.fy + 1, face: s.face || 1 });
CFA_KIND.tank = (s, c) => CFA.back.push({ sh: 'cfa_m', tag: 'tank', x: c.cx, y: c.fy + 1 });
CFA_KIND.heap = (s, c) => { for (let i = 0; i < (s.w || 4); i += 2) CFA.front.push({ sh: 'cfa_s', tag: 'heap', i: 0, x: (s.x + i) * TILE + 16, y: c.fy + 1, face: hash2(s.x + i, 3) < 0.5 ? 1 : -1 }); };
// soot sifting down out of the roof's cracks; a few motes of cold air
CFA_KIND.soot = (s, c) => { CFA.soot.push({ x0: s.x * TILE, x1: (s.x + (s.w || 10)) * TILE }); };
CFA_KIND.ashdrift = (s, c) => {   // pale ash dusting the floor tops (painted into the front layer)
  CFA.front.push({ fn: ctx => {
    for (let tx = s.x; tx < s.x + (s.w || 8); tx++) for (let ty = 1; ty < room.h; ty++) {
      if (isSolidT(tileAtR(room, tx, ty - 1)) || !isSolidT(tileAtR(room, tx, ty))) continue;
      for (let i = 0; i < 16; i++) if (hash2(tx * 16 + i, ty) < 0.55) { ctx.fillStyle = hash2(i, tx + ty) < 0.5 ? '#4f6079' : '#364356'; ctx.fillRect(tx * TILE + i, ty * TILE, 1, 1 + (hash2(tx + i, 7) < 0.25 ? 1 : 0)); }
    }
  } });
};
CFA_KIND.band = (s, c) => {   // an iron strap round the flue (back layer, between the walls)
  CFA.back.push({ fn: ctx => {
    const y = s.y * TILE;
    for (let x = s.x * TILE; x < (s.x + (s.w || 10)) * TILE; x++) {
      const tx = Math.floor(x / TILE); if (isSolidT(tileAtR(room, tx, s.y))) continue;
      ctx.fillStyle = '#0a0d12'; ctx.fillRect(x, y, 1, 6); ctx.fillStyle = '#1e2734'; ctx.fillRect(x, y, 1, 1);
      if (x % 10 === 3) { ctx.fillStyle = '#2d3849'; ctx.fillRect(x, y + 2, 1, 1); }
    }
  } });
};
// the grate in the Last Hearth (E6): iron bars over the cracked cells until Cinder Slam breaks them; cold air rises through
CFA_KIND.grate = (s, c) => {
  const p = cfaProp(s, c, { x: s.x * TILE, y: (s.y + 1) * TILE, w: (s.w || 4) * TILE });
  const broken = () => room.grid[(s.y + 1) * room.w + s.x] !== T_CRACK;
  p.update = dt => {
    if (broken()) { if (Math.random() < 0.08) particles.push({ x: p.x + rand(4, p.w - 4), y: p.y + 20, vx: rand(-4, 4), vy: -rand(8, 18), life: rand(1.5, 2.5), kind: 'cfa_cold' }); return; }
    if (Math.random() < 0.12) particles.push({ x: p.x + rand(2, p.w - 2), y: p.y + 2, vx: rand(-3, 3), vy: -rand(10, 24), life: rand(1.4, 2.4), kind: 'cfa_cold' });
    if (!CFA.hint.grate && Math.abs(P.x - (p.x + p.w / 2)) < 40 && P.ground && Math.abs(P.y - p.y) < 20) {
      CFA.hint.grate = 1; toast(SAVE.flags['cf:grate'] ? 'Cold air rises through the broken grate.' : 'Cold air rises through the grate beside the hearth. The floor under it rings hollow.', 4);
    }
  };
  p.draw = () => {
    const x0 = Math.round(p.x), y0 = p.y;
    if (broken()) {   // bent stubs at either end, the black pit beneath
      for (const [x, d] of [[x0 + 1, 1], [x0 + p.w - 3, -1]]) for (let i = 0; i < 6; i++) cfaR(x + d * Math.floor(i / 2), y0 + i, 2, 1, '#1d1a1b');
      return;
    }
    cfaR(x0, y0, p.w, 3, '#141213'); cfaR(x0, y0, p.w, 1, '#5a311c');
    for (let x = x0 + 2; x < x0 + p.w - 1; x += 5) { cfaR(x, y0, 2, 16, '#141213'); cfaR(x, y0, 1, 16, '#3d2419'); }
    cfaR(x0, y0 + 13, p.w, 3, '#0b0a0b');
  };
};
// the hearth's glow spilling down the crawl from the grate (the Ash Pit's only warmth)
CFA_KIND.hearthglow = (s, c) => cfaProp(s, c, { update() { addLight(this.x + 8, this.y - 28, 96, '255,150,70', 0.75, LX_FLICKER); addLight(this.x + 50, this.y - 16, 60, '255,130,60', 0.3); }, draw() {
  drawGlow(() => { g.globalAlpha = 0.07 + 0.02 * Math.sin(time * 6); g.fillStyle = '#e88a30'; g.beginPath(); g.moveTo(this.x - 8, this.y - 36); g.lineTo(this.x + 24, this.y - 36); g.lineTo(this.x + 70, this.y); g.lineTo(this.x - 8, this.y); g.fill(); g.globalAlpha = 1; });
} });
// the Flue's shaft of warm light from the grate at its top (the fires of the world above)
CFA_KIND.flueshaft = (s, c) => cfaProp(s, c, { y: TILE, update() {
  const x = this.x;
  addLight(x, 30, 120, '255,170,90', 0.9, LX_FLICKER);
  for (let i = 1; i < 6; i++) addLight(x + i * 4, 30 + i * 70, 110 - i * 10, '255,150,80', 0.6 - i * 0.09);
  if (Math.random() < 0.3) particles.push({ x: x + rand(-40, 40), y: rand(20, 300), vx: rand(-3, 3), vy: rand(4, 10), life: rand(3, 5), kind: 'dust' });
  if (Math.random() < 0.06) particles.push({ x: x + rand(-14, 14), y: 22, vx: rand(-6, 6), vy: rand(10, 30), life: rand(2, 4), kind: 'ember' });
}, draw() {
  const x = this.x;
  if (!cfaVis(x, 160, 300)) return;
  drawGlow(() => {
    g.globalAlpha = 0.05; g.fillStyle = '#e88a30';
    g.beginPath(); g.moveTo(x - 26, 18); g.lineTo(x + 26, 18); g.lineTo(x + 70, 520); g.lineTo(x - 50, 520); g.fill();
    g.globalAlpha = 0.04; g.fillStyle = '#ffd27e'; g.beginPath(); g.moveTo(x - 12, 18); g.lineTo(x + 12, 18); g.lineTo(x + 34, 360); g.lineTo(x - 24, 360); g.fill();
    g.globalAlpha = 1;
    // the grate at the top: bars against the fire
    cfaR(x - 40, 0, 80, 16, '#c96a22'); cfaR(x - 40, 0, 80, 6, '#f7ad4c');
    for (let xx = x - 40; xx < x + 40; xx += 6) cfaR(xx, 0, 3, 16, '#0b0a0b');
    cfaR(x - 40, 14, 80, 3, '#0b0a0b');
  });
} });
CFA_KIND.ventlight = (s, c) => { (CFA.vlx || (CFA.vlx = [])).push(c.cx); return cfaProp(s, c, { y: s.y * TILE, update() { addLight(this.x, this.y + 60, 90, '150,170,205', 0.35); }, draw() {
  if (!cfaVis(this.x, this.y + 80, 120)) return;
  if (!LX4.sh) drawGlow(() => { g.globalAlpha = 0.045; g.fillStyle = '#8f9aa8'; g.beginPath(); g.moveTo(this.x - 10, this.y); g.lineTo(this.x + 10, this.y); g.lineTo(this.x + 34, this.y + 170); g.lineTo(this.x - 30, this.y + 170); g.fill(); g.globalAlpha = 1; });
  cfaR(this.x - 10, this.y - 1, 20, 2, '#2d3849'); for (let i = 0; i < 5; i++) cfaR(this.x - 9 + i * 4, this.y - 1, 2, 2, '#4f6079');
} }); };
// drop-through gratings over holes (EXPANSION2 §0: a marker and a prompt) and the drains
CFA_KIND.dropmark = (s, c) => cfaProp(s, c, { draw() {
  const p = this, near = Math.abs(P.x - p.x) < 30 && Math.abs(P.y - p.y) < 22;
  if (!near) return;
  drawGlow(() => { const a = 0.45 + 0.3 * Math.sin(time * 5); g.globalAlpha = a; for (let i = 0; i < 3; i++) cfaR(p.x - 2 + i, p.y + 4 + i, 5 - 2 * i, 1, '#b7c0cb'); g.globalAlpha = 1; });
  if (P.ground && Math.abs(P.y - p.y) < 4) CFA.prompt = time;
} });
CFA_KIND.drainmark = (s, c) => cfaProp(s, c, { draw() {
  const p = this, y = s.up ? p.y - 4 : p.y + 1;
  for (const dx of [-24, 22]) { cfaR(p.x + dx, y, 2, 3, '#1e2734'); cfaR(p.x + dx, y, 2, 1, '#415066'); }   // the torn grate's hinges
  if (!s.up && Math.abs(P.x - p.x) < 40 && Math.abs(P.y - p.y) < 30) drawGlow(() => { g.globalAlpha = 0.35 + 0.2 * Math.sin(time * 4); for (let i = 0; i < 3; i++) cfaR(p.x - 2 + i, p.y + 6 + i, 5 - 2 * i, 1, '#8f9aa8'); g.globalAlpha = 1; });
} });
CFA_KIND.draughtmark = (s, c) => cfaProp(s, c, { update() { if (Math.random() < 0.1) CFA.drops.push({ x: this.x, y: this.y - rand(8, 72), vx: -rand(80, 160), life: rand(0.5, 1), len: rand(4, 10), streak: true }); }, draw() {} });
CFA_KIND.draught = (s, c) => cfaProp(s, c, { draw() {} });
CFA_KIND.crackhint = (s, c) => cfaProp(s, c, { update() {
  if (Math.random() < 0.05 && room.grid[(s.y + 1) * room.w + s.x] === T_CRACK) particles.push({ x: this.x + rand(-6, 10), y: this.y + 2, vx: rand(-3, 3), vy: -rand(6, 14), life: rand(1, 2), kind: 'cfa_cold' });
}, draw() {} });
// still black water: the Barrows' deep water, re-coloured black and mirror-still (no caustics); drips ring it
CFA_KIND.stillwater = (s, c) => { CFA.still = true; };
function cfaStillWater() {
  if (typeof DBW === 'undefined' || !DBW.mask || !DBW.cells.length) return;
  const w = room.w, h = room.h, m = DBW.mask, cv = document.createElement('canvas'); cv.width = w * TILE; cv.height = h * TILE;
  const x = cv.getContext('2d');
  for (const [tx, ty] of DBW.cells) {
    let d = 0; for (let k = 1; k <= 5 && ty - k >= 0 && m[(ty - k) * w + tx]; k++) d = k;
    x.fillStyle = `rgba(${5 - Math.min(d, 3)},${8 - Math.min(d, 4)},${12 - Math.min(d, 5)},${Math.min(0.88, 0.58 + d * 0.06)})`; x.fillRect(tx * TILE, ty * TILE, TILE, TILE);
  }
  CFA.surf = DBW.surf.slice(); DBW.surf = []; DBW.body = cv;
}
function cfaDrawStill() {
  if (!CFA.surf) return;
  for (const [tx, ty] of CFA.surf) {
    const px = tx * TILE, py = ty * TILE; if (!cfaVis(px, py, 20)) continue;
    g.fillStyle = 'rgba(124,142,168,0.42)'; g.fillRect(px, py, TILE, 1); g.fillStyle = 'rgba(62,76,96,0.18)'; g.fillRect(px, py + 2, TILE, 1);
    const k = (Math.floor(time * 0.7 + tx * 0.37) % 9);
    if (k === 0) { g.fillStyle = 'rgba(183,192,203,0.35)'; g.fillRect(px + ((tx * 5) % 10), py, 4, 1); }
  }
  for (const vx of CFA.vlx || []) for (const [tx, ty] of CFA.surf) {   // the cold vent light mirrored in the still water
    const px = tx * TILE + 8, d = Math.abs(px - vx); if (d > 34 || !cfaVis(px, ty * TILE, 30)) continue;
    const k = 1 - d / 34;
    for (let r = 1; r < 34; r += 2) { if (((r + tx) & 3) === 1) continue; g.fillStyle = `rgba(143,154,168,${(0.22 * k * (1 - r / 34)).toFixed(3)})`; g.fillRect(tx * TILE + ((r * 5 + tx * 3) % 12), ty * TILE + r, 4 + (r % 3), 1); }
  }
  if (Math.random() < 0.02 && CFA.surf.length) { const [tx, ty] = CFA.surf[irand(0, CFA.surf.length - 1)]; CFA.ripples.push({ x: tx * TILE + rand(2, 14), y: ty * TILE, t: 0 }); if (cfaVis(tx * TILE, ty * TILE)) cfaSfx.drip(); }
  for (const q of CFA.ripples) {
    q.t += 1 / 60; const r = q.t * 18, a = Math.max(0, 0.5 - q.t * 0.4);
    g.fillStyle = `rgba(143,154,168,${a})`; g.fillRect(Math.round(q.x - r), q.y, 2, 1); g.fillRect(Math.round(q.x + r - 1), q.y, 2, 1);
  }
  CFA.ripples = CFA.ripples.filter(q => q.t < 1.2);
}
// steam rising from the cisterns (where the Quench Wraiths come from): a hiss, then a breath of pale vapour
CFA_KIND.steam = (s, c) => { CFA.steams.push({ x: c.cx, y: c.fy, t: rand(0, 6), per: rand(5, 8) }); };
function cfaSteamTick(dt) {
  for (const q of CFA.steams) {
    q.t += dt; const k = q.t % q.per;
    if (k > q.per - 1.2 && k < q.per - 1.2 + dt && cfaVis(q.x, q.y)) cfaSfx.hiss(0.4);
    if (k > q.per - 1.2 && Math.random() < 0.35) particles.push({ x: q.x + rand(-10, 10), y: q.y - rand(0, 6), vx: rand(-6, 6), vy: -rand(14, 34), life: rand(0.5, 0.9), kind: 'cfa_steam' });
  }
}
CFA_KIND.slagriver = (s, c) => {   // the frozen slag fall in the chute: black glass with a last dull red vein (back layer)
  CFA.back.push({ fn: ctx => {
    for (let ty = s.y; ty < room.h - 1; ty++) for (let tx = s.x; tx < s.x + (s.w || 10); tx++) {
      if (isSolidT(tileAtR(room, tx, ty))) continue;
      const d = Math.abs(tx - (s.x + (s.w || 10) * (0.2 + 0.6 * ((ty - s.y) / room.h))));
      if (d > 3) continue;
      ctx.fillStyle = d < 1.5 ? 'rgba(8,8,10,0.75)' : 'rgba(10,12,16,0.45)'; ctx.fillRect(tx * TILE, ty * TILE, TILE, TILE);
      if (d < 0.8 && hash2(tx, ty) < 0.45) { ctx.fillStyle = '#3d2419'; ctx.fillRect(tx * TILE + 6 + Math.floor(hash2(ty, tx) * 4), ty * TILE, 1, TILE); }
    }
  } });
};
// threshold: ash drifting UP (the world beyond breathing in), the pale light through the broken arch
CFA_KIND.ashup = (s, c) => { CFA.ashup = { x0: s.x * TILE, x1: (s.x + (s.w || 20)) * TILE }; };
CFA_KIND.archlight = (s, c) => cfaProp(s, c, { update() { addLight(this.x, this.y - 40, 160, '220,226,236', 0.7); }, draw() {
  drawGlow(() => { g.globalAlpha = 0.06; g.fillStyle = '#dfe4ea'; g.beginPath(); g.moveTo(this.x + 60, this.y - 120); g.lineTo(this.x + 60, this.y); g.lineTo(this.x - 220, this.y); g.lineTo(this.x - 40, this.y - 120); g.fill(); g.globalAlpha = 1; });
} });
CFA_KIND.hall = (s, c) => {   // the Threshold's hall: dark slate wall, a broken arch opening east onto the ash-light
  CFA.back.push({ fn: ctx => {
    const x1 = s.w * TILE, top = 2 * TILE, bot = room.ph - 3 * TILE;
    for (let y = top; y < bot; y += 8) for (let x = 0; x < x1 + 40; x += 16) {
      const ox = (y / 8) % 2 ? 8 : 0, bx = x - ox;
      const ex = (bx + 8 - (x1 + 70)) / 170, ey = (y + 4 - bot) / ((bot - top) * 0.92), e = ex * ex + ey * ey - (hash2(bx, y) - 0.5) * 0.12;
      if (e < 1) continue;
      // v17 bg rollout C: the bricks crumble away toward the opening (fading over a band) instead of ending in a hard 16x8 staircase
      ctx.globalAlpha = Math.min(1, (e - 1) / 0.42) ** 0.8;
      const k = hash2(bx * 3, y * 7), light = Math.max(0, 1 - (x1 - bx) / 260);
      const v = Math.round(14 + k * 6 + light * 26), b = Math.round(v * 1.45);
      ctx.fillStyle = `rgb(${v},${Math.round(v * 1.18)},${b})`; ctx.fillRect(bx, y, 16, 8);
      ctx.fillStyle = 'rgba(4,5,8,0.9)'; ctx.fillRect(bx, y, 16, 1); ctx.fillRect(bx, y, 1, 8);
      ctx.fillStyle = `rgba(150,160,180,${0.08 + light * 0.25})`; ctx.fillRect(bx + 1, y + 1, 15, 1);
      ctx.globalAlpha = 1;
    }
  } });
};
CFA_KIND.furnacedoor = (s, c) => CFA.back.push({ sh: 'cfa_doors', tag: 'leaf', x: c.cx + 8, y: c.fy + 1 });
CFA_KIND.balustrade = (s, c) => {
  CFA.front.push({ fn: ctx => {
    const y = c.fy;
    for (let i = 0; i < (s.w || 40); i += 3) {
      const x = (s.x + i) * TILE + 6;
      ctx.fillStyle = '#4f6079'; ctx.fillRect(x, y - 13, 4, 13); ctx.fillStyle = '#7c8ea8'; ctx.fillRect(x, y - 13, 1, 13); ctx.fillStyle = '#62748f'; ctx.fillRect(x - 1, y - 15, 6, 2);
    }
    ctx.fillStyle = '#62748f'; ctx.fillRect(s.x * TILE, y - 11, (s.w || 40) * TILE, 2); ctx.fillStyle = '#8f9aa8'; ctx.fillRect(s.x * TILE, y - 11, (s.w || 40) * TILE, 1);
  } });
};
CFA_KIND.guardian = (s, c) => CFA.back.push({ sh: 'cfa_guard', tag: 'idle', x: c.cx, y: c.fy + 1, face: s.face || 1 });

// ================================================================== the Hearth Below: the Great Furnace, the coals, the doors
// The furnace is painted into the back layer (its breast above the mouth is invisible solid terrain, tile '0'); its doors are
// solid cells (local x 48–53, rows 12–17) while SAVE.flags['w2:open'] is unset. cfArena is the BOSS hand-off (forge_area.md).
var cfArena = { coals: { x0: 608, x1: 768, y: 288 }, bellows: [], dark: 0, mouth: { x0: 768, x1: 832, y0: 192, y1: 288 }, wall: 816 };
function cfArenaDark(k) { cfArena.dark = clamp(k || 0, 0, 1); }
registerTile('0', 90, { solid: true, draw() {} });   // invisible solid: the furnace's breast, drawn by its sprite
const CFA_DOOR = { x0: 51, x1: 57, y0: 12, y1: 17 };
function cfaDoorCells(solid) {
  if (!room || room.id !== 'CF8') return;
  for (let y = CFA_DOOR.y0; y <= CFA_DOOR.y1; y++) for (let x = CFA_DOOR.x0; x <= CFA_DOOR.x1; x++) room.grid[y * room.w + x] = solid ? T_SOLID : T_EMPTY;
}
CFA_KIND.furnace = (s, c) => {
  const open = !!SAVE.flags['w2:open'];
  const F = CFA.furnace = { x: 800, y: 288, open, k: open ? 1 : 0, heat: open ? 0 : 1, bar: open ? 1 : 0, anim: null };
  CFA.back.push({ sh: 'cfa_furnace', tag: 'body', x: 800, y: 288 });
  if (!open) cfaDoorCells(true);
  const p = cfaProp(s, c, { x: 800, y: 288, glow: false });
  p.update = dt => {
    if (F.heat > 0.02) {
      addLight(800, 236, 70 * F.heat, '255,120,50', 0.55 * F.heat);
      if (Math.random() < 0.1 * F.heat) particles.push({ x: 800 + rand(-2, 2), y: rand(196, 286), vx: rand(-8, 8), vy: -rand(10, 30), life: 0.8, kind: 'ember' });
    }
    if (F.open && F.k > 0.9) { if (Math.random() < 0.15) particles.push({ x: rand(780, 920), y: rand(200, 286), vx: -rand(20, 50), vy: rand(-6, 6), life: rand(1, 2), kind: 'cfa_cold' }); }
  };
  p.draw = () => {
    if (!cfaVis(800, 240, 160)) return;
    const nf = cfaFrames('cfa_doors', 'open'), fi = Math.round(F.k * (nf - 1));
    if (!cfaSpr('cfa_doors', F.k > 0.001 ? 'open' : 'shut', F.k > 0.001 ? fi : 0, 800, 289)) {
      const w = 64 * (1 - F.k * 0.85);
      cfaR(768, 196, 64, 92, '#030405');
      cfaR(800 - 32, 196, w / 2, 92, '#10151d'); cfaR(832 - w / 2, 196, w / 2, 92, '#10151d');
    }
    if (F.k > 0.05) {   // open: the throat runs on east behind the doors, black, to the room's edge
      g.globalAlpha = Math.min(1, F.k * 1.4); cfaR(812, 206, 116, 82, '#020304'); cfaR(812, 204, 116, 2, '#0e1219');
      for (let i = 0; i < 12; i++) cfaR(812 + i * 10, 206, 1, 82, '#05070a'); g.globalAlpha = 1;
    }
    if (F.heat > 0.02) drawGlow(() => {   // the seam: heat that seals it
      g.globalAlpha = F.heat * (0.75 + 0.15 * Math.sin(time * 3)); cfaR(799, 200, 2, 86, '#e88a30'); cfaR(799, 214, 2, 60, '#ffd27e'); g.globalAlpha = 1;
    });
    if (F.bar < 0.99) {   // the great bar across the doors
      const by = 236 - F.bar * 70, a = 1 - F.bar;
      g.globalAlpha = a > 0.2 ? 1 : a * 5; if (!cfaSpr('cfa_doors', 'bar', 0, 800, by + 8)) { cfaR(756, by, 88, 6, '#06080b'); cfaR(756, by, 88, 1, '#364356'); } g.globalAlpha = 1;
    }
  };
};
CFA_KIND.coals = (s, c) => {
  const p = cfaProp(s, c, { x: (s.x + (s.w || 10) / 2) * TILE, y: c.fy, glow: true });
  p.update = dt => {
    const F = CFA.furnace, h = F ? F.heat : 1;
    if (h > 0.02) {
      addLight(p.x, p.y - 10, 150 * (0.6 + 0.4 * h), '255,130,55', 0.95 * h, LX_FLICKER);
      if (Math.random() < 0.35 * h) particles.push({ x: p.x + rand(-76, 76), y: p.y - 4, vx: rand(-8, 8), vy: -rand(20, 60), life: rand(0.8, 2.2), kind: 'ember' });
    }
  };
  p.draw = () => {
    if (!cfaVis(p.x, p.y, 120)) return;
    const h = CFA.furnace ? CFA.furnace.heat : 1, n = cfaFrames('cfa_coals', 'loop');
    if (h < 0.98 && !cfaSpr('cfa_coals', 'dead', 0, p.x, p.y + 1)) cfaR(p.x - 80, p.y - 6, 160, 6, '#141213');
    if (h > 0.02) drawGlow(() => { g.globalAlpha = h; if (!cfaSpr('cfa_coals', 'loop', Math.floor(time * 5), p.x, p.y + 1)) { for (let i = 0; i < 40; i++) cfaR(p.x - 78 + hash2(i, 1) * 156, p.y - 3 - hash2(i, 2) * 4, 3, 2, ['#a3531f', '#e88a30', '#ffd27e'][i % 3]); } g.globalAlpha = 1; });
  };
};
// The keeper's fire goes out and the doors unbar (called by BOSS once the Hearthkeeper's Core is taken; also on entry).
function cfFurnaceOpen() {
  SAVE.flags['w2:open'] = 1;
  if (!room || room.id !== 'CF8' || !CFA.furnace || CFA.furnace.open) { saveGame(); return; }
  const F = CFA.furnace; F.open = true;
  const go = () => {
    playCutscene([
      { pan: { x: 760, y: 220 }, dur: 1.2 },
      { dur: 2.2, tween: (dt, k) => { F.heat = 1 - k; } },
      { do() { cfaSfx.grind(1); shake = 4; } },
      { dur: 1.4, tween: (dt, k) => { F.bar = k; } },
      { do() { cfaSfx.slam(); shake = 6; for (let i = 0; i < 30; i++) particles.push({ x: rand(768, 832), y: rand(200, 286), vx: rand(-60, 60), vy: -rand(20, 80), g: 300, life: rand(0.6, 1.2), kind: 'rock' }); } },
      { do() { cfaSfx.grind(1.2); } },
      { dur: 2.6, tween: (dt, k) => { F.k = k * k * (3 - 2 * k); if (Math.random() < 0.6) particles.push({ x: rand(770, 830), y: rand(200, 286), vx: -rand(30, 90), vy: rand(-10, 10), life: rand(0.8, 1.6), kind: 'cfa_cold' }); } },
      { do() { cfaDoorCells(false); cfaSfx.wind(); }, always: true },
      { say: ['', 'The Great Furnace is cold. Its doors stand open on a draught from somewhere else.'], dur: 3.2 },
    ], () => { F.heat = 0; F.bar = 1; F.k = 1; cfaDoorCells(false); saveGame(); });
  };
  if (state === 'play') go(); else setTimeout(() => { if (room && room.id === 'CF8') go(); }, 800);
}

// ================================================================== the Last Gate (CT2) — the World 2 hook
// World 2 isn't built. When it is: give its first room an opening against CT2's east wall (rows 24–31, x 91), set
// SAVE.flags['w2:gate'] when the player earns it, and call cfWorld2Link() — it lifts the gate (drawn) and opens the wall.
const CT_GATE = { room: 'CT2', x: 83, y: 31, wall: { x: 91, y0: 24, y1: 31 }, flag: 'w2:gate' };
function cfWorld2Link() {
  // HOOK (World 2): not wired yet. Planned: if (SAVE.flags[CT_GATE.flag] && room.id === CT_GATE.room) open the cells
  // (CT_GATE.wall) in room.grid, animate the gate leaves apart (cfa_gate 'open'), and let checkRoomExit carry the player east.
  return !!SAVE.flags[CT_GATE.flag];
}
const CFA_GATE_LINES = [
  ['The gate is shut. It has no lock, no ring, no seam you could get a blade into.', 'Through the hairline of light down its middle comes a breath of air that smells of rain on hot stone. There is no rain in the Hallow.'],
  ['You lay your hand on the gate. It is warm from the other side.', 'Far off, beyond it, something vast turns over in its sleep.'],
  ['The grate-crown carved at the apex is the keeper’s. He was not guarding the forge from the world.', 'He was guarding the world from whatever made this gate.'],
];
CFA_KIND.gate2 = (s, c) => {
  CFA.back.push({ sh: 'cfa_gate', tag: 'shut', x: c.cx, y: c.fy + 1 });
  const p = cfaProp(s, c, { glow: true });
  p.update = () => { addLight(p.x, p.y - 150, 120, '236,240,246', 0.45 + 0.1 * Math.sin(time * 0.8)); };
  p.prompt = () => 'Touch the gate';
  p.interact = () => {
    const n = (SAVE.flags['cf:gatetouch'] || 0); SAVE.flags['cf:gatetouch'] = n + 1;
    cfaSfx.gate(); flashScreen = Math.max(flashScreen, 0.15);
    startDialogue(CFA_GATE_LINES[n % CFA_GATE_LINES.length].map(t => ({ t, lore: true })), null);
  };
  p.draw = () => {   // the hairline of light down the seam
    drawGlow(() => { g.globalAlpha = 0.6 + 0.2 * Math.sin(time * 1.3); cfaR(p.x, p.y - 300, 1, 296, '#dfe4ea'); g.globalAlpha = 1; });
  };
};

// ================================================================== room setup and the frame
SPAWNS.cfa = (s, c) => { cfaEnsure(); const f = CFA_KIND[s.kind]; if (f) f(s, c); };
const CFA_STANDIN = { cf_smith: 'hollow_soldier', cf_wraith: 'gloom_wisp', cf_hulk: 'rot_hulk', cf_mite: 'rot_crawler', cf_unforged: 'grave_knight' };
SPAWNS.cf_foe = (s, c) => {   // a forge foe: FOES' type once it exists, an old-roster stand-in until then
  if (killed.has(c.key)) return;
  const real = typeof ENEMY !== 'undefined' && ENEMY[s.type];
  const e = makeEnemy(real ? s.type : (CFA_STANDIN[s.type] || 'hollow_soldier'), c.cx, c.fy, c.key);
  e.cfType = s.type; enemies.push(e);
};
HOOKS.enter.push(def => {
  cfaEnsure();
  if (AREAS.forge) AREAS.forge.ambient = 0.5;
  cfArena.dark = 0;
  if (!cfaIn() && def.id !== 'E6') return;
  if (def.biome === 'forge' && !SAVE.flags['cf:seen']) SAVE.flags['cf:seen'] = 1;
  cfaSkinShutters();
  if (CFA.still) cfaStillWater();
  // the Reject Pile's shutter stays wedged open once the Unforged there has fallen
  if (def.id === 'CF4' && SAVE.flags['cf:unforged1']) CFA.shut.sB = { perm: true };
  for (const [id, S] of Object.entries(CFA.shut)) if (S.perm) kitForce(id, true);
  if (def.id === 'CF8' && SAVE.flags['w2:open'] && CFA.furnace && !CFA.furnace.open) { CFA.furnace.open = true; CFA.furnace.k = 1; CFA.furnace.heat = 0; CFA.furnace.bar = 1; cfaDoorCells(false); }
  if (def.id === 'CF1' && !SAVE.flags['cf:grate']) { SAVE.flags['cf:grate'] = 1; }
  if (def.id === 'CT1' && !SAVE.flags['cf:threshold']) { SAVE.flags['cf:threshold'] = 1; setTimeout(() => { if (room && room.id === 'CT1') toast('The air here has never been breathed by the Hallow.', 3.6); }, 1600); }
  cfaBake();
});
HOOKS.update.push(dt => {
  if (!room) return;
  if (CFA.roomObj !== room) { if (cfaIn()) cfaEnsure(); else return; }
  CFA.t += dt;
  if (!CFA.baked || room.back !== CFA.backRef || room.front !== CFA.frontRef) { CFA.baked = false; cfaBake(); }
  cfaShutTick(dt);
  for (const q of CFA.later) { q.t -= dt; if (q.t <= 0) { q.done = true; q.fn(); } }
  CFA.later = CFA.later.filter(q => !q.done);
  cfaSteamTick(dt);
  for (const q of CFA.drops) { q.x += q.vx * dt; q.life -= dt; }
  CFA.drops = CFA.drops.filter(q => q.life > 0);
  for (const r of CFA.rings) r.t += dt;
  CFA.rings = CFA.rings.filter(r => r.t < 1.4);
  if (cfaIn()) {
    for (const S of CFA.soot) if (Math.random() < 0.35) particles.push({ x: rand(Math.max(S.x0, cam.x), Math.min(S.x1, cam.x + W)), y: cam.y - 2 + (room.def.indoor ? 34 : 0), vx: rand(-4, 4), vy: rand(10, 24), life: rand(3, 6), kind: 'cfa_soot' });
    if (CFA.ashup && Math.random() < 0.6) particles.push({ x: rand(cam.x - 10, cam.x + W + 10), y: cam.y + H + 4, vx: rand(-6, 10), vy: -rand(8, 22), life: rand(6, 11), kind: 'cfa_ash' });
    // P3 darkness from the boss (cfArena.dark): the forge ambient deepens, only the hearth stays lit
    if (room.id === 'CF8' && AREAS.forge) AREAS.forge.ambient = 0.5 + 0.4 * cfArena.dark;
  }
});
HOOKS.render.push(() => {
  if (!room || CFA.roomObj !== room) return;
  if (CFA.surf) drawGlow(cfaDrawStill);
  cfaDrawStreaks();
  if (CFA.rings.length) drawGlow(() => {   // an anvil's ring made visible: pale arcs that open and fade
    for (const r of CFA.rings) {
      for (let k = 0; k < 3; k++) {
        const t = r.t - k * 0.12; if (t <= 0) continue;
        const R = (r.big ? 26 : 12) + t * (r.big ? 130 : 90), a = Math.max(0, 0.55 - t * 0.45) * (1 - k * 0.25);
        g.fillStyle = `rgba(${r.col},${a})`;
        for (let ang = 200; ang <= 340; ang += 4) { const rad = ang * Math.PI / 180; g.fillRect(Math.round(r.x + Math.cos(rad) * R), Math.round(r.y + Math.sin(rad) * R * 0.62), 1, 1); }
      }
    }
  });
});
HOOKS.hud.push(() => {
  if (CFA.prompt && time - CFA.prompt < 0.1 && state === 'play') {
    const sx = P.x - cam.x, sy = P.y - cam.y - 40, label = '↓ + Jump: drop through', tw = textW(label, 6) + 10;
    box(sx - tw / 2, sy - 8, tw, 11, 0.7); text(label, sx, sy, 6, '#dfe4ea', 'center');
  }
});
HOOKS.death.push(() => { cfArena.dark = 0; if (AREAS.forge) AREAS.forge.ambient = 0.5; for (const S of CFA.seals || []) S.closed = false; CFA.shut = Object.fromEntries(Object.entries(CFA.shut || {}).filter(([k, v]) => v.perm)); });
// the forge's parallax: each part of the forge has its own far/mid pair (art/gen_forge_bg.py, sheets cfa_bg_<theme>)
const CFA_BG = { CF1: 'flue', CF2: 'flue', CF3: 'flue', CF4: 'racks', CF9: 'racks', CF13: 'racks', CF5: 'cistern', CF10: 'cistern',
  CF6: 'bellows', CF7: 'court', CF11: 'court', CF12: 'court', CF8: 'hearth' };
function cfaLayer(sh, tag, fac, vfac) {
  if (!sh.ok || !sh.has(tag)) return false;
  const f = sh.frames[sh.first(tag)], ox = -((cam.x * fac) % f.w + f.w) % f.w, oy = Math.round(clamp(-cam.y * vfac, -(f.h - H) - 20, 20));
  for (let x = Math.round(ox); x < W; x += f.w) g.drawImage(sh.img, f.x, f.y, f.w, f.h, x, oy + (H - f.h), f.w, f.h);
  return true;
}
const cfaParallaxBase = drawParallax;
drawParallax = function () {
  const th = room && room.def.biome === 'forge' && CFA_BG[room.id], sh = th && sheet('cfa_bg_' + th);
  if (!sh || !sh.ok) cfaParallaxBase();
  else { g.fillStyle = AREAS.forge.tint; g.fillRect(0, 0, W, H); cfaLayer(sh, 'far', 0.08, 0.02); cfaLayer(sh, 'mid', 0.3, 0.08); }
  if (!room || room.def.biome !== 'forge') return;
  if (cfArena.dark > 0 && room.id === 'CF8') { g.fillStyle = `rgba(2,3,4,${0.75 * cfArena.dark})`; g.fillRect(0, 0, W, H); }
};

// ================================================================== the Last Hearth (E6): its fire burns low once the furnace is open
if (typeof XS_KIND !== 'undefined' && XS_KIND.hearth) {
  const cfaHearthBase = XS_KIND.hearth;
  XS_KIND.hearth = (s, c) => {
    cfaHearthBase(s, c);
    const p = props[props.length - 1]; if (!p || !SAVE.flags['w2:open']) return;
    // the promise is broken: a low red bed of embers, a small light, no roaring flame
    p.update = function () {
      addLight(this.x, this.y - 8, 60 + Math.sin(time * 3) * 4, '255,110,50', 0.6, LX_FLICKER);
      if (Math.random() < 0.08) particles.push({ x: this.x + rand(-6, 6), y: this.y - rand(4, 8), vx: rand(-4, 4), vy: -rand(8, 18), life: rand(0.6, 1.2), kind: 'ember' });
    };
    p.draw = function () {
      if (xsDraw('xsc_m', 'hearth', 0, this.x, this.y + 1, 1)) {   // the hearth sprite, then its fire banked to embers over it
        g.fillStyle = '#100907'; g.fillRect(Math.round(this.x - 13), Math.round(this.y - 23), 26, 21);   // the fire banked: black firebox
        g.fillStyle = '#1d1210'; for (let i = 0; i < 6; i++) g.fillRect(Math.round(this.x - 11 + i * 4), Math.round(this.y - 4 - (i % 2)), 3, 2);   // grey ash on the logs
        drawGlow(() => { for (let i = 0; i < 9; i++) { const f = 0.5 + 0.5 * Math.sin(time * 2 + i * 1.7); g.globalAlpha = 0.5 + 0.5 * f; cfaR(this.x - 10 + i * 2.4, this.y - 4 - (i % 3), 2, 1, i % 2 ? '#a3531f' : '#e86a2a'); } g.globalAlpha = 1; });
        return;
      }
      cfaR(this.x - 20, this.y - 34, 40, 34, '#3a2e28'); cfaR(this.x - 13, this.y - 22, 26, 22, '#140c0a');
      drawGlow(() => { for (let i = 0; i < 9; i++) cfaR(this.x - 10 + i * 2.4, this.y - 4 - (i % 3), 2, 2, i % 2 ? '#a3531f' : '#e86a2a'); });
    };
    if (!SAVE.flags['cf:lowfire']) { SAVE.flags['cf:lowfire'] = 1; setTimeout(() => { if (room && room.id === 'E6') toast('The Last Hearth has burned down to embers. No one is keeping it now.', 4); }, 1200); }
  };
}

// ================================================================== NPCs: Ashwright and Venn hear of the forge
if (typeof VENN_BEATS !== 'undefined') VENN_BEATS.push(['hearthkeeper', 'v_hearth', [
  'The Last Hearth has gone to embers. I felt it the way you feel a door close in another room.',
  'There was always someone keeping that fire. I never asked who. I think I didn’t want to know what it was keeping out.',
  'Whatever is past the furnace, Ashbound, it is older than the Root. Be careful what you open.']]);
const cfaNpcBase = npcScript;
npcScript = function (id) {
  const S = cfaNpcBase(id);
  if (id === 'venn' && SAVE.flags['cf:seen'] && !SAVE.flags['v_coldforge'] && !SAVE.flags['boss:hearthkeeper'] && Array.isArray(S) && S.length === 1) {
    return [
      { w: 'venn', t: 'You smell of cold iron. You went down under the Last Hearth.' },
      { w: 'venn', t: 'There is a forge down there that made the Hallow’s swords, before there was a Hallow to carry them. I thought it was a story.' },
      { w: 'venn', t: 'If its keeper is still awake, don’t make him angry. …No. You will anyway. Then make him tired.' },
      { do() { setF('v_coldforge'); } }];
  }
  if (id === 'ashwright' && Array.isArray(S)) {
    const ci = S.findIndex(q => q && q.choice); if (ci < 0) return S;
    const out = S.slice();
    if (SAVE.flags['cf:seen'] && !SAVE.flags['a_coldforge']) out.splice(ci, 0,
      { w: 'ashwright', t: '…That soot on you. That’s not mine. That’s the Cold Forge.' },
      { w: 'ashwright', t: 'I apprenticed under the Last Hearth, boy-high to the anvil. Then one morning the keeper banked the fire and told us all to go up and never come down.' },
      { do() { setF('a_coldforge'); } });
    if (SAVE.flags['boss:hearthkeeper'] && !SAVE.flags['a_keeper']) out.splice(out.findIndex(q => q && q.choice), 0,
      { w: 'ashwright', t: 'You beat the keeper. Hah. …Hah. I can’t decide if I want to shake your hand or hit you with it.' },
      { w: 'ashwright', t: 'He taught me to hold a hammer. Didn’t tell me why he never let the furnace go out. I suppose you know now.' },
      { do() { setF('a_keeper'); } });
    const ch = out.find(q => q && q.choice);
    if (ch && SAVE.flags['cf:seen'] && !ch.choice.some(c => c[0] === 'Ask about the Cold Forge')) {
      const li = ch.choice.findIndex(c => c[0] === 'Leave');
      ch.choice = ch.choice.slice(); ch.choice.splice(li < 0 ? ch.choice.length : li, 0, ['Ask about the Cold Forge', [
        { w: 'ashwright', t: 'Every blade in the Hallow was born down there. The anvils still ring if you hit ’em hard enough — the shutters were keyed to ’em, so no thief could get far.' },
        { w: 'ashwright', t: SAVE.flags['w2:open'] ? 'And the big furnace is cold. In all my years I never saw its doors. …What’s behind them? No, don’t tell me. I’m too old for it.' : 'The keeper never let us near the big furnace. Said it wasn’t a furnace. Said a lot of things, that one.' }]]);
    }
    return out;
  }
  return S;
};

// ================================================================== test hooks
if (typeof window !== 'undefined' && window.__game) window.__game.cf = {
  get CFA() { return CFA; }, get arena() { return cfArena; }, open: () => cfFurnaceOpen(), dark: k => cfArenaDark(k), CT_GATE,
  ring(id) { const a = CFA.anvils.find(p => p.s.id === id); if (a) cfaRing(a); return !!a; },
  door() { return room && room.id === 'CF8' ? room.grid[14 * room.w + 52] : null; },
  npc(id) { const S = npcScript(id); const flat = []; const walk = L => { for (const q of L) { if (q.t) flat.push((q.w || '') + ': ' + q.t); if (q.choice) for (const c of q.choice) { flat.push('> ' + c[0]); walk(c[1]); } } }; walk(S); return flat; },
  pages: () => Object.keys(LORE_PAGES).filter(k => k.startsWith('cfa_')),
};
