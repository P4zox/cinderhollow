// ------------------------------------------------------------------ THE CRIMSON MANOR (agent C)
// A vampiric noble estate past Kalden's Vigil (biome `crimson`): blood rain on black stone, candlelit halls, portraits whose
// eyes follow you, crypt-cellars of wine and blood. Gate: a blood veil (the ash-veil '%' mechanic, re-skinned) — Ember Dash.
// Hazards: blood pools (sap HP/FP, slow), crimson downpours in the Court (shelter under balconies), swinging chandeliers,
// portrait ambushes. Enemies: cm_servant, cm_hound, cm_gargoyle. Mini-boss: the Butler (CM6). Boss: Countess Sanguine (CM7;
// phase 2 tears the ballroom open to a red sky). Every top-level name is prefixed cm/CM (all region files share one scope).
Object.assign(AREAS, { crimson: { name: 'The Crimson Manor', ambient: 0.58, amb: 'dust', tint: '#0a0508', map: '#7a2232' } });
Object.assign(SCALES, { crimson: [0, 2, 3, 7, 8] });
Object.assign(ROOTS, { crimson: 55 });

const CM_RED = ['#1a0306', '#3a060c', '#5e0a14', '#8a1420', '#b8222c', '#e04a4a', '#ff9a8a'];
const cmIn = () => room && room.def.biome === 'crimson';
const cmSfx = {
  drip: () => { tone(900 + rand(-200, 200), 0.08, 0.03, 'sine', 0.5); },
  splash: (v = 1) => { noise(0.35, 600, 0.7, 0.3 * v, 'lowpass', 0.5); noise(0.2, 2200, 1, 0.08 * v, 'highpass'); },
  creak: () => { tone(160 + rand(-20, 20), 0.5, 0.05, 'sawtooth', 1.3); noise(0.4, 500, 3, 0.05, 'bandpass', 1.4); },
  chime: () => { [1318, 1760, 2093].forEach((f, i) => tone(f, 0.6, 0.03, 'sine', 1, i * 0.05)); },
  bats: () => { for (let i = 0; i < 5; i++) tone(2400 + rand(-600, 600), 0.06, 0.02, 'square', 1.4, i * 0.05); noise(0.5, 3000, 1.5, 0.12, 'bandpass', 0.6); },
  lance: () => { noise(0.25, 900, 0.8, 0.35, 'bandpass', 2.2); tone(110, 0.3, 0.12, 'sawtooth', 2); },
  gurgle: () => { noise(0.8, 300, 1.5, 0.12, 'lowpass', 0.6); },
  rumble: () => { noise(1.6, 120, 0.6, 0.35, 'lowpass', 0.5); },
  whip: () => { noise(0.18, 3200, 1.2, 0.3, 'bandpass', 0.3); tone(600, 0.12, 0.05, 'triangle', 0.4); },
  rip: () => { noise(0.4, 1800, 0.8, 0.3, 'bandpass', 0.4); tone(220, 0.3, 0.06, 'sawtooth', 0.6); },
  knife: () => { tone(2600, 0.1, 0.04, 'triangle', 0.7); noise(0.1, 4000, 2, 0.08, 'highpass'); },
  wave: () => { noise(1.4, 260, 0.7, 0.4, 'lowpass', 1.6); noise(0.9, 900, 0.8, 0.12, 'bandpass', 0.5); },
};

// ================================================================== music: a slow minor-key waltz (a frantic one for the bosses)
// The engine's generic score keeps its drone; its note layer is held off (MUSIC.nextNote) while we play the waltz on MUSIC.gain.
const CM_WALTZ = [   // [bass root, chord (semitones over A3), melody (per beat, null = hold)]
  [0, [0, 3, 7], [12, null, 11]], [5, [5, 8, 12], [12, 8, 5]], [7, [7, 11, 14], [11, null, 7]], [0, [0, 3, 7], [12, null, null]],
  [8, [8, 12, 15], [15, 12, 8]], [5, [5, 8, 12], [17, 15, 12]], [7, [7, 11, 14], [14, 11, 7]], [0, [0, 3, 7], [12, null, null]],
  [0, [0, 3, 7], [7, 3, 0]], [-2, [10, 14, 17], [10, 14, 17]], [-4, [8, 12, 15], [15, null, 12]], [-5, [7, 11, 14], [11, null, null]],
  [-7, [5, 8, 12], [8, 12, 17]], [0, [0, 3, 7], [19, null, 15]], [-5, [7, 11, 14], [14, 11, 7]], [0, [0, 3, 7], [12, null, null]],
];
const CMM = { next: 0, beat: 0, mode: null };
function cmMusicMode() {
  if (!room || !cmIn() || muted || !AC || typeof MUSIC === 'undefined' || !MUSIC.gain) return null;
  if (state === 'title' || state === 'dead' || state === 'ending' || state === 'cine') return null;
  if (boss && (boss.kind === 'sanguine' || boss.kind === 'butler') && (boss.active || boss.cutting) && boss.alive) return boss.kind === 'sanguine' && boss.phase === 2 ? 'boss2' : 'boss';
  return 'waltz';
}
function cmMusicTick() {
  const mode = cmMusicMode();
  if (mode !== CMM.mode) { CMM.mode = mode; CMM.beat = 0; CMM.next = AC ? AC.currentTime + 0.3 : 0; }
  if (!mode) return;
  MUSIC.nextNote = AC.currentTime + 0.5;                              // hold the generic note layer
  if (mode !== 'waltz' && MUSIC.mode === 'boss' && MUSIC.nodes.length) stopDrone();   // its boss drone is in another key
  const fast = mode !== 'waltz', beatLen = mode === 'boss2' ? 0.3 : fast ? 0.34 : 0.62, out = MUSIC.gain;
  const A = 55, f = (base, n) => base * Math.pow(2, n / 12);
  while (CMM.next < AC.currentTime + 0.12) {
    const d = Math.max(0, CMM.next - AC.currentTime), bar = CM_WALTZ[Math.floor(CMM.beat / 3) % CM_WALTZ.length], b = CMM.beat % 3;
    if (b === 0) {
      tone(f(A * 2, bar[0]), beatLen * 1.8, fast ? 0.07 : 0.05, fast ? 'sawtooth' : 'triangle', 1, d, out);
      if (fast) { noise(0.22, 140, 0.8, 0.18, 'lowpass'); tone(f(A, bar[0]), beatLen * 1.2, 0.08, 'sine', 0.6, d, out); }
    } else for (const n of bar[1]) tone(f(A * 4, n), beatLen * 0.7, fast ? 0.012 : 0.014, fast ? 'square' : 'sine', 1, d, out);
    const m = bar[2][b];
    if (m !== null) {
      const hold = bar[2].slice(b + 1).filter(v => v === null).length + 1, oct = mode === 'boss2' ? 4 : fast ? 8 : 8;
      tone(f(A * oct, m), beatLen * hold * 0.95, fast ? 0.026 : 0.032, fast ? 'sawtooth' : 'triangle', 1, d, out);
      if (!fast) tone(f(A * oct * 2, m), beatLen * hold * 0.6, 0.008, 'sine', 1, d + 0.02, out);
      if (mode === 'boss2' && b === 1) tone(f(A * 16, m + 12), 0.12, 0.01, 'square', 1, d, out);
    }
    CMM.beat++; CMM.next += beatLen;
  }
}

// ================================================================== per-room state
const CM = { roomObj: null };
function cmReset() {
  Object.assign(CM, { roomObj: room, pools: [], chands: [], ports: [], shots: [], lances: [], waves: [], drops: [], bats: [], splats: [],
    rain: null, streaks: [], poolT: 0, rainHint: false, veilHint: false, col: null, back0: null, lines: [], debris: [], held: null });
}
function cmEnsure() { if (CM.roomObj !== room) cmReset(); }
function cmFloorY(x, y0) {   // first solid/platform top at or below y0
  for (let y = Math.max(0, y0); y < room.ph; y += 4) { const t = tileAt(Math.floor(x / TILE), Math.floor(y / TILE)); if (isSolidT(t) || t === T_PLAT) return Math.floor(y / TILE) * TILE; }
  return null;
}
function cmSheltered(x, y) {   // solid stone overhead (the rain runs through iron balconies and gratings)
  const tx = Math.floor(x / TILE);
  for (let ty = Math.floor((y - 28) / TILE); ty >= 0; ty--) if (isSolidT(tileAt(tx, ty))) return true;
  return false;
}
function cmSap(dt, hpRate, fpRate, why) {   // pools / rain: slow drain that never kills outright; Blood Vial turns it into a draught
  if (P.state === 'dead' || SETTINGS.god) return;
  if (charmOn('c_bloodvial')) { P.hp = Math.min(D.maxHp, P.hp + hpRate * 0.35 * dt); return; }
  P.hp = Math.max(1, P.hp - hpRate * NGP.dmg * dt); P.fp = Math.max(0, P.fp - fpRate * dt);
  P.flash = Math.max(P.flash, 0.25);
  if (Math.random() < dt * 8) particles.push({ x: P.x + rand(-5, 5), y: P.y - rand(2, 24), vx: rand(-10, 10), vy: rand(10, 30), g: 120, life: 0.5, kind: 'blood' });
  if (!SAVE.hints['cm_' + why]) { SAVE.hints['cm_' + why] = 1; toast(why === 'pool' ? 'The blood drinks from you. Get out of the pool.' : 'The blood rain burns. Shelter under the balconies until it passes.', 3.5); }
}

// ================================================================== interiors: wallpaper, lancet windows (the sky shows through), wainscot
function cmPaneMask(sh, f) {   // transparent pixels NOT reachable from the frame border = glass panes
  const c = document.createElement('canvas'); c.width = f.w; c.height = f.h; const x = c.getContext('2d');
  x.drawImage(sh.img, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h);
  let d; try { d = x.getImageData(0, 0, f.w, f.h); } catch (e) { return null; }
  const a = d.data, seen = new Uint8Array(f.w * f.h), st = [];
  for (let i = 0; i < f.w; i++) { st.push(i, (f.h - 1) * f.w + i); }
  for (let j = 0; j < f.h; j++) { st.push(j * f.w, j * f.w + f.w - 1); }
  while (st.length) { const i = st.pop(); if (seen[i] || a[i * 4 + 3] > 0) continue; seen[i] = 1; const px = i % f.w, py = (i / f.w) | 0;
    if (px > 0) st.push(i - 1); if (px < f.w - 1) st.push(i + 1); if (py > 0) st.push(i - f.w); if (py < f.h - 1) st.push(i + f.w); }
  const m = document.createElement('canvas'); m.width = f.w; m.height = f.h; const mx = m.getContext('2d'), md = mx.createImageData(f.w, f.h);
  let any = false;
  for (let i = 0; i < f.w * f.h; i++) if (!seen[i] && a[i * 4 + 3] === 0) { md.data[i * 4 + 3] = 255; any = true; }
  mx.putImageData(md, 0, 0);
  return any ? m : null;
}
function cmBuildInterior(R) {
  const sh = sheet('cm_interior'), def = R.def;
  if (!sh.ok || !def.indoor) return;
  if (!sh._img || !sh.img.complete || !sh.img.naturalWidth) return;
  const c = document.createElement('canvas'); c.width = R.pw; c.height = R.ph; const x = c.getContext('2d'); x.imageSmoothingEnabled = false;
  const fr = n => sh.has(n) ? sh.frames[sh.first(n)] : null, air = (tx, ty) => !isSolidT(tileAtR(R, tx, ty));
  const cellar = def.id === 'CM5', paper = cellar ? null : fr('paper');
  if (cellar) {   // bare vaulted stone, no wallpaper and no windows down here
    const ts = tileSheet(def.biome);
    for (let ty = 0; ty < R.h; ty++) for (let tx = 0; tx < R.w; tx++) drawTile(x, ts, hash2(tx * 3, ty * 7) < 0.3 ? 16 : 0, tx * TILE, ty * TILE);
    x.fillStyle = 'rgba(6,2,6,0.55)'; x.fillRect(0, 0, R.pw, R.ph);
  }
  if (paper) for (let yy = 0; yy < R.ph; yy += paper.h) for (let xx = 0; xx < R.pw; xx += paper.w) x.drawImage(sh.img, paper.x, paper.y, paper.w, paper.h, xx, yy, paper.w, paper.h);
  // floors: air cell above a solid/platform cell (wainscot + furniture line)
  const floorTop = tx => { for (let ty = R.h - 1; ty > 0; ty--) if (air(tx, ty - 1) && !air(tx, ty)) return ty * TILE; return null; };
  const win = cellar ? null : fr('window'), pil = fr('pilaster'), wain = cellar ? null : fr('wainscot');
  const mask = win ? (sh._cmMask !== undefined ? sh._cmMask : (sh._cmMask = cmPaneMask(sh, win))) : null;
  const step = def.id === 'CM7' ? 8 : 9;
  for (let tx = 3; tx < R.w - 3; tx += step) {
    const fy = floorTop(tx + 2); if (fy === null) continue;
    // a window needs a clear wall area 4 tiles wide and ~7 tall above the wainscot
    const top = fy - (win ? win.h : 128) + 8;
    let clear = win && top > TILE * 2;
    for (let ty = Math.floor(top / TILE); clear && ty < fy / TILE; ty++) for (let k = 0; k < 4; k++) if (!air(tx + k, ty)) clear = false;
    if (clear) {
      const wx = (tx + 2) * TILE - Math.floor(win.w / 2), wy = fy - win.h;
      if (mask) { x.globalCompositeOperation = 'destination-out'; x.drawImage(mask, wx, wy); x.globalCompositeOperation = 'source-over'; }
      x.drawImage(sh.img, win.x, win.y, win.w, win.h, wx, wy, win.w, win.h);
    } else if (pil) {
      let ok = true; for (let ty = Math.floor((fy - pil.h) / TILE); ty < fy / TILE; ty++) if (ty >= 0 && !air(tx + 2, ty)) ok = false;
      if (ok) x.drawImage(sh.img, pil.x, pil.y, pil.w, pil.h, (tx + 2) * TILE + 8 - Math.floor(pil.w / 2), fy - pil.h, pil.w, pil.h);
    }
  }
  if (wain) for (let tx = 0; tx < R.w; tx++) for (let ty = 1; ty < R.h; ty++) {
    if (!(air(tx, ty - 1) && !air(tx, ty))) continue;
    const sx = wain.x + ((tx * TILE) % wain.w);
    x.drawImage(sh.img, sx, wain.y, TILE, wain.h, tx * TILE, ty * TILE - wain.h, TILE, wain.h);
  }
  // soft shadow where the walls meet the room, then the decor tiles (chains, drapes, candles, goblets)
  const ts = tileSheet(def.biome);
  for (let ty = 0; ty < R.h; ty++) for (let tx = 0; tx < R.w; tx++) {
    if (!air(tx, ty)) { x.clearRect(tx * TILE, ty * TILE, TILE, TILE); continue; }
    let d = 9; for (let yy = -2; yy <= 2; yy++) for (let xx = -2; xx <= 2; xx++) if (!air(tx + xx, ty + yy)) d = Math.min(d, Math.max(Math.abs(xx), Math.abs(yy)));
    if (d <= 2) { x.fillStyle = `rgba(4,1,4,${d === 1 ? 0.5 : 0.25})`; x.fillRect(tx * TILE, ty * TILE, TILE, TILE); }
    const deco = { x: 42, r: 43, k: 44, b: 45 }[def.map[ty][tx]];
    if (deco !== undefined) drawTile(x, ts, deco, tx * TILE, ty * TILE);
  }
  R.back = c;
}

// ================================================================== room setup
HOOKS.enter.push(def => {
  cmEnsure(); CMM.lastRoom = def.id;
  if (def.biome !== 'crimson') return;
  cmBuildInterior(room);
  CM.back0 = room.back;
  const vs = sheet('cm_bloodveil');
  for (const p of props) if (p.type === 'veil' && vs.ok) { p.sh = vs; p.anim = new Anim(vs, 'loop', true); p.cmVeil = true; }
  if (def.rain) CM.rain = { cfg: def.rain, st: 'calm', t: rand(def.rain.every[0] * 0.6, def.rain.every[1] * 0.8), k: 0 };
  if (def.id === 'CM1' && !SAVE.items.emberdash) setTimeout(() => { if (room && room.id === 'CM1') toast('Warm air, and the smell of iron. Something red moves in the dark ahead.', 3.5); }, 1200);
  if (def.id === 'CM7') cmBallroomSetup();
});
HOOKS.death.push(() => { CM.shots = []; CM.lances = []; CM.waves = []; CM.drops = []; });

// ---- decor props
const CM_DECO = { candelabra: ['cm_candelabra', 'loop'], statue: ['cm_statue', null], carriage: ['cm_carriage', 'idle'], coffin: ['cm_coffin', null],
  winerack: ['cm_winerack', 'idle'], barrel: ['cm_barrel', 'idle'], table: ['cm_table', 'idle'], sconce: ['cm_sconce', 'loop'], fountain: ['cm_fountain', 'loop'] };
function cmProp(type, x, y, shName, tag, extra = {}) {
  const sh = sheet(shName);
  const t = tag && sh.has(tag) ? tag : (Object.keys(sh.tags)[0] || 'idle');
  return { type: 'cm_' + type, x, y, face: 1, sh, anim: new Anim(sh, t, true), ...extra };
}
SPAWNS.cm_prop = (s, c) => {
  cmEnsure();
  const d = CM_DECO[s.kind]; if (!d) return;
  const p = cmProp(s.kind, c.cx, c.fy, d[0], s.sub || d[1]);
  p.anim.t = rand(0, 400);
  const glow = { candelabra: [0, -34, 60, 0.9], sconce: [0, -16, 44, 0.8], fountain: [0, -22, 40, 0.35], table: [0, -26, 40, 0.6] }[s.kind];
  if (glow) p.update = () => addLight(p.x + glow[0], p.y + glow[1], glow[2] + Math.sin(time * 9 + p.x) * 2, s.kind === 'fountain' ? '200,40,50' : '255,170,100', glow[3]);
  if (!p.sh.ok) p.draw = () => {};
  props.push(p);
};

// ---- lore: portraits (eyes follow you; some tear open), diaries
const CM_LORE = {
  cm_countess: ['A young woman in a crimson gown, painted with loving care. The plaque reads: “Lady Ysmay Vermeil, on the night of her first ball.”', 'Someone has scratched out the year.'],
  cm_count: ['A stern lord in black. “Count Aurelan Vermeil, Keeper of the Root’s Tithe.”', 'The canvas is cut across the throat. Neatly, as if with a rapier.'],
  cm_hunter: ['A hunter in black leather, a silver crest on his breast. “Ser Caddoc, who came to end the Countess — and stayed to serve her.”', 'His eyes have been painted over in red.'],
  cm_widow: ['A woman in mourning, veiled. The plaque has been pried away.', 'The painted hands hold a rapier where a rosary used to be.'],
  cm_gallery_a: ['The Countess again, older now, though her face has not aged a day.', 'Behind her the painter set a hundred empty chairs.'],
  cm_child: ['A pale child in white lace. “Our little Rosalind, the Root’s last blessing.”', 'The frame is warm to the touch.'],
  cm_vestibule: ['An empty frame. The canvas inside it is blank, as if its lady simply stepped out.', 'Beyond the doors, a waltz keeps time for no one.'],
  cm_diary1: ['A household ledger, the last pages.', '“The Root no longer answers the tithe. My lord says grace can be drawn from other vessels.”', '“Tonight we dine on the stable boys.” The rest is written in a different, more elegant hand.'],
  cm_diary2: ['A guest list for the Crimson Ball.', 'Every name has been struck through but the last line, which is left blank.', 'Beneath it, in fresh ink: “The next to arrive.”'],
  cm_diary3: ['The butler’s cellar book.', '“Vintage of the Hallow, bottled the year the Root fell. Madam takes it warm.”', '“Keep the hounds fed and the pools full. Never open the ballroom doors from within.”'],
};
function cmLore(key) { startDialogue((CM_LORE[key] || ['…']).map(t => ({ t, lore: true })), null); }
SPAWNS.cm_diary = (s, c) => {
  cmEnsure();
  const p = cmProp('diary', c.cx, c.fy, 'cm_lectern', 'loop');
  p.update = () => addLight(p.x + 4, p.y - 22, 38 + Math.sin(time * 10) * 2, '255,180,110', 0.75);
  p.prompt = () => 'Read'; p.interact = () => cmLore(s.lore);
  props.push(p);
};
SPAWNS.cm_portrait = (s, c) => {
  cmEnsure();
  const key = `${c.id}:${c.key}:amb`, torn = s.subj === 'torn' || (s.ambush && killed.has(key));
  const p = cmProp('portrait', c.cx, c.fy, 'cm_portrait', torn ? 'torn' : s.subj);
  Object.assign(p, { subj: s.subj, ambush: !!s.ambush, key, state: torn ? 'torn' : 'idle', lore: s.lore, eyeK: 0 });
  p.anim.loop = true;
  p.update = dt => cmPortraitUpdate(p, dt);
  p.draw = () => cmPortraitDraw(p);
  CM.ports.push(p); props.push(p);
  if (s.lore) {   // interaction checks |p.y - P.y| < 24, so the plaque's reading spot sits on the floor under the painting
    const fy = cmFloorY(c.cx, c.fy) ?? c.fy;
    const calm = () => !(boss && boss.alive && (boss.active || boss.cutting));
    props.push({ type: 'cm_plaque', x: c.cx, y: fy, face: 1, anim: { update() {} }, draw() {}, prompt: () => (calm() ? 'Examine' : null), interact: () => { if (calm()) cmLore(s.lore); } });
  }
};
function cmPortraitUpdate(p, dt) {
  const near = Math.abs(P.x - p.x) < 130 && P.y > p.y - 20 && P.y < p.y + 140;
  p.eyeK = approach(p.eyeK, near && p.state === 'idle' ? 1 : 0, dt * 2);
  if (p.ambush && p.state === 'idle' && Math.abs(P.x - p.x) < 44 && P.y > p.y && P.y < p.y + 120 && P.state !== 'dead') {
    p.state = 'tear'; if (p.sh.has('tear')) p.anim.set('tear', false); p.t = 0; cmSfx.rip(); shake = Math.max(shake, 2);
  }
  if (p.state === 'tear') {
    p.t += dt;
    if (p.t > 0.45 && !p.spawned) {
      p.spawned = true;
      const fy = cmFloorY(p.x, p.y) ?? p.y + 64;
      const e = makeEnemy('cm_servant', p.x, p.y - 8, p.key); e.cmEmerge(fy); enemies.push(e);
      for (let i = 0; i < 16; i++) particles.push({ x: p.x + rand(-10, 10), y: p.y - rand(6, 34), vx: rand(-60, 60), vy: rand(-40, 60), g: 300, life: rand(0.4, 0.8), kind: 'blood' });
    }
    if (p.spawned && (p.anim.done || !p.sh.has('tear'))) { p.state = 'torn'; if (p.sh.has('torn')) p.anim.set('torn', true); }
  }
}
function cmPortraitDraw(p) {
  if (!p.sh.ok) { g.fillStyle = '#3a2a1a'; g.fillRect(Math.round(p.x) - 16, Math.round(p.y) - 40, 32, 40); return; }
  drawSprite(p.sh, p.anim.frame, p.x, p.y, 1, { bottom: true });
  if (p.state !== 'idle' || p.subj === 'torn') return;
  // the eyes: dim sockets that glow and follow you as you pass
  const k = 0.25 + 0.75 * p.eyeK, ox = p.x - 16, oy = p.y - 40;
  for (const [ex, ey] of [[13, 15], [18, 15]]) {
    const wx = ox + ex, wy = oy + ey, dx = clamp(Math.round((P.x - wx) / 60), -1, 1) * (p.eyeK > 0.3 ? 1 : 0);
    g.fillStyle = `rgba(255,60,50,${k})`; g.fillRect(Math.round(wx + dx * 0.5), Math.round(wy), 1, 1);
    if (p.eyeK > 0.5) addLight(wx, wy, 8, '255,40,40', 0.5 * p.eyeK);
  }
}

// ================================================================== blood pools
SPAWNS.cm_pool = (s, c) => {
  cmEnsure();
  CM.pools.push({ x0: s.x * TILE + 1, x1: (s.x + (s.w || 2)) * TILE - 1, y: c.fy, seed: rand(0, 9), bub: [] });
};
function cmUpdatePools(dt) {
  for (const pl of CM.pools) {
    const inP = P.x > pl.x0 && P.x < pl.x1 && P.y > pl.y - 14 && P.y <= pl.y + 1 && P.state !== 'dead';
    if (inP) {
      cmSap(dt, 5, 7, 'pool');
      if (P.state !== 'roll' && P.ground) P.pushVx = (P.pushVx || 0) - P.vx * 0.35;
      if (Math.abs(P.vx) > 20 && Math.random() < dt * 10) particles.push({ x: P.x + rand(-4, 4), y: pl.y - 10, vx: -P.vx * 0.2 + rand(-20, 20), vy: -rand(30, 70), g: 400, life: 0.4, kind: 'blood' });
      if (!pl.wasIn) cmSfx.splash(0.5);
    }
    pl.wasIn = inP;
    if (Math.random() < dt * 1.2) pl.bub.push({ x: rand(pl.x0 + 3, pl.x1 - 3), t: 0 });
    for (const b of pl.bub) b.t += dt;
    pl.bub = pl.bub.filter(b => b.t < 0.8);
    addLight((pl.x0 + pl.x1) / 2, pl.y - 10, (pl.x1 - pl.x0) * 0.6 + 10, '190,30,40', 0.35);
  }
}
function cmDrawPools() {
  for (const pl of CM.pools) {
    const w = pl.x1 - pl.x0, x = Math.round(pl.x0), top = Math.round(pl.y - 11);
    g.fillStyle = 'rgba(40,2,8,0.92)'; g.fillRect(x, top, w, pl.y - top);
    g.fillStyle = 'rgba(96,6,16,0.9)'; g.fillRect(x, top, w, 2);
    for (let i = 0; i < w; i += 2) { const o = Math.sin(time * 2.2 + (x + i) * 0.3 + pl.seed); g.fillStyle = o > 0.55 ? 'rgba(200,50,60,0.85)' : 'rgba(140,16,28,0.8)'; g.fillRect(x + i, top + (o > 0.2 ? 0 : 1), 2, 1); }
    for (const b of pl.bub) { const r = b.t < 0.5 ? 1 : 2; g.fillStyle = `rgba(220,70,80,${1 - b.t})`; g.fillRect(Math.round(b.x) - r + 1, top - (b.t < 0.5 ? 1 : 0), r, 1); }
  }
}

// ================================================================== the crimson downpour (the Court)
function cmUpdateRain(dt) {
  const r = CM.rain; if (!r) return;
  r.t -= dt;
  if (r.st === 'calm' && r.t <= 0) { r.st = 'warn'; r.t = 1.4; cmSfx.rumble(); if (!CM.rainHint && !SAVE.hints.cm_rainwarn) { CM.rainHint = true; SAVE.hints.cm_rainwarn = 1; toast('The sky darkens. Find shelter.', 2.4); } }
  else if (r.st === 'warn' && r.t <= 0) { r.st = 'pour'; r.t = r.cfg.dur; cmSfx.gurgle(); }
  else if (r.st === 'pour' && r.t <= 0) { r.st = 'calm'; r.t = rand(r.cfg.every[0], r.cfg.every[1]); }
  r.k = approach(r.k, r.st === 'pour' ? 1 : r.st === 'warn' ? 0.45 : 0, dt * 1.6);
  if (r.st === 'pour' && P.state !== 'dead' && !['rest', 'rise'].includes(P.state) && !cmSheltered(P.x, P.y)) cmSap(dt, 9, 4, 'rain');
  // splashes where the rain lands near the camera
  const n = (r.st === 'pour' ? 14 : 3) * dt;
  if (Math.random() < n) {
    const x = cam.x + rand(0, W), y = cmFloorY(x, Math.max(0, cam.y - 20));
    if (y !== null && !cmSheltered(x, y) && y < cam.y + H + 20) particles.push({ x, y: y - 1, vx: rand(-20, 20), vy: -rand(20, 50), g: 300, life: 0.3, kind: 'blood' });
  }
}
function cmDrawRain() {   // screen space
  const r = CM.rain; if (!r) return;
  const n = 70 + Math.round(r.k * 110), slant = 0.18;
  for (let i = 0; i < n; i++) {
    const sp = 280 + hash2(i, 3) * 160 + r.k * 80, len = 5 + Math.floor(hash2(i, 5) * 6 + r.k * 4);
    const sx = hash2(i, 7) * (W + 80) - 40, yy = ((hash2(i, 11) * 400 + time * sp) % (H + 40)) - 20, xx = sx + time * sp * slant;
    const x = ((xx % (W + 80)) + W + 80) % (W + 80) - 40;
    g.fillStyle = `rgba(${150 + Math.round(r.k * 60)},${24 + Math.round(hash2(i, 9) * 20)},${34},${0.16 + hash2(i, 13) * 0.2 + r.k * 0.18})`;
    for (let k = 0; k < len; k++) g.fillRect(Math.round(x + k * slant), Math.round(yy + k), 1, 1);
  }
  if (r.k > 0.02) { g.fillStyle = `rgba(90,0,10,${0.16 * r.k})`; g.fillRect(0, 0, W, H); }
}

// ================================================================== swinging chandeliers
SPAWNS.cm_chandelier = (s, c) => {
  cmEnsure();
  const ch = { px: s.x * TILE + 8, py: s.y * TILE, len: s.len || 60, amp: (s.swing || 0) * Math.PI / 180, period: s.period || 3.2, ph: s.phase || 0,
               t: 0, big: !!s.big, id: ++hazardId, ang: 0, lastSide: 0, red: 0 };
  CM.chands.push(ch);
};
function cmChandPos(ch) { return { x: ch.px + Math.sin(ch.ang) * ch.len, y: ch.py + Math.cos(ch.ang) * ch.len }; }
function cmUpdateChands(dt) {
  for (const ch of CM.chands) {
    if (ch.gone || ch.fall) continue;
    ch.t += dt;
    ch.ang = ch.amp ? ch.amp * Math.sin((ch.t / ch.period + ch.ph) * Math.PI * 2) : Math.sin(ch.t * 0.8 + ch.px) * 0.02;
    const e = cmChandPos(ch), cx = e.x + Math.sin(ch.ang) * 24, cy = e.y + Math.cos(ch.ang) * 24;
    addLight(cx, cy, ch.big ? 90 : 64, ch.red > 0.5 ? '240,120,100' : '255,180,110', 0.9);
    if (!ch.amp) continue;
    const side = Math.sign(Math.cos((ch.t / ch.period + ch.ph) * Math.PI * 2));
    if (side !== ch.lastSide) { ch.lastSide = side; if (Math.abs(P.x - ch.px) < 220) cmSfx.creak(); }
    const hb = rect(cx - 17, cy - 10, cx + 17, cy + 16);
    if (overlap(hb, playerHurtbox())) {
      const v = Math.cos((ch.t / ch.period + ch.ph) * Math.PI * 2);
      if (hurtPlayer(30 * NGP.dmg, v >= 0 ? 1 : -1, ch.id * 10 + Math.floor(ch.t / (ch.period / 2)), {})) { P.vx = (v >= 0 ? 1 : -1) * 170; P.vy = -120; }
    }
    for (const en of enemies) if (en.alive && !en.cfg.flying && overlap(hb, en.hurtbox() || hb) && (en.cmChT || 0) < time) { en.cmChT = time + 1; en.hit({ dmg: 40, poise: 40, dir: Math.sign(Math.cos((ch.t / ch.period + ch.ph) * Math.PI * 2)) || 1, kind: 'env', x: en.x, y: en.y - 14 }); }
  }
}
function cmDrawChands() {
  const sh = sheet('cm_chandelier');
  for (const ch of CM.chands) {
    if (ch.gone) continue;
    const e0 = cmChandPos(ch), e = ch.fall ? { x: e0.x, y: e0.y + ch.fall.y } : e0, n = Math.max(1, Math.floor(ch.len / 4));
    if (!ch.fall) for (let i = 0; i <= n; i++) { const t = i / n, x = lerp(ch.px, e.x, t), y = lerp(ch.py, e.y, t); g.fillStyle = i % 2 ? '#1a1418' : '#4a3e44'; g.fillRect(Math.round(x), Math.round(y), 1, 2); }
    if (sh.ok) {
      const t = sh.tag('loop'), f = t.from + (Math.floor(time * 7 + ch.px) % (t.to - t.from + 1));
      drawSprite(sh, f, e.x, e.y, 1, { pivot: [Math.floor(sh.fw / 2), 0], rot: -ch.ang, flash: ch.red > 0 ? ch.red * 0.35 : 0, flashColor: '#ff2030' });
    } else { g.fillStyle = '#6a5a40'; g.fillRect(Math.round(e.x) - 14, Math.round(e.y) + 16, 28, 6); }
  }
}

// ================================================================== projectiles + ground hazards shared by the manor's foes
function cmShot(o) { const s = { g: 0, r: 3, life: 3, t: 0, id: ++hazardId, kind: 'knife', ...o }; CM.shots.push(s); return s; }
function cmUpdateShots(dt) {
  for (const s of CM.shots) {
    s.t += dt; s.life -= dt; s.vy += s.g * dt; s.x += s.vx * dt; s.y += s.vy * dt;
    if (s.kind === 'knife') addLight(s.x, s.y, 16, '220,220,240', 0.4);
    if (overlap(rect(s.x - s.r, s.y - s.r, s.x + s.r, s.y + s.r), playerHurtbox())) {
      if (hurtPlayer(s.dmg, sign(s.vx), s.id, { src: s.src, parryable: s.parry })) { s.life = 0; spawnFx('hit', s.x, s.y, sign(s.vx)); continue; }
    }
    if (solidAtPx(s.x, s.y) || s.life <= 0) {
      s.life = 0;
      if (s.kind === 'knife') { cmSfx.knife(); for (let i = 0; i < 4; i++) particles.push({ x: s.x, y: s.y, vx: rand(-50, 50), vy: -rand(20, 70), g: 300, life: 0.35, kind: 'spark' }); }
    }
  }
  CM.shots = CM.shots.filter(s => s.life > 0);
}
function cmDrawShots() {
  for (const s of CM.shots) {
    if (s.kind === 'spike') {
      const a = Math.atan2(s.vy, s.vx), c = Math.cos(a), sn = Math.sin(a);
      for (let k = -6; k <= 5; k++) { g.fillStyle = k > 3 ? '#ffb0a8' : k > -2 ? '#e0303c' : '#8a1020'; g.fillRect(Math.round(s.x + c * k), Math.round(s.y + sn * k), 1, 1); if (k < 2 && k > -4) g.fillRect(Math.round(s.x + c * k - sn), Math.round(s.y + sn * k + c), 1, 1); }
      addLight(s.x, s.y, 18, '255,50,50', 0.5); continue;
    }
    if (s.kind !== 'knife') continue;
    const a = Math.atan2(s.vy, s.vx), c = Math.cos(a), sn = Math.sin(a);
    for (let k = -4; k <= 4; k++) { g.fillStyle = k > 1 ? '#f0f0ff' : k > -2 ? '#b8b8cc' : '#3a2a30'; g.fillRect(Math.round(s.x + c * k), Math.round(s.y + sn * k), 1, 1); }
  }
}
// blood lance: a spike of hardened blood bursts from the floor after a readable warning
function cmLance(x, y, opt = {}) {
  const l = { x, y, t: 0, warn: opt.warn ?? 0.75, life: 0.32, h: opt.h ?? 58, w: opt.w ?? 12, dmg: opt.dmg ?? 32, id: ++hazardId, src: opt.src || null, boss: !!opt.boss };
  CM.lances.push(l); return l;
}
function cmUpdateLances(dt) {
  for (const l of CM.lances) {
    l.t += dt;
    if (l.t < l.warn) { if (Math.random() < dt * 30) particles.push({ x: l.x + rand(-5, 5), y: l.y - 1, vx: rand(-10, 10), vy: -rand(10, 40), g: 200, life: 0.3, kind: 'blood' }); addLight(l.x, l.y - 4, 16 + 16 * l.t / l.warn, '220,40,50', 0.6); continue; }
    if (!l.burst) { l.burst = true; cmSfx.lance(); shake = Math.max(shake, 2.5); for (let i = 0; i < 10; i++) particles.push({ x: l.x, y: l.y - rand(0, l.h), vx: rand(-60, 60), vy: -rand(20, 120), g: 380, life: rand(0.3, 0.6), kind: 'blood' }); }
    const k = l.t - l.warn;
    if (k < l.life * 0.8 && overlap(rect(l.x - l.w / 2, l.y - l.h, l.x + l.w / 2, l.y), playerHurtbox())) hurtPlayer((l.boss ? BOSS_DMG : 1) * l.dmg * NGP.dmg, sign(P.x - l.x), l.id, { src: l.src });
    addLight(l.x, l.y - l.h / 2, 40, '230,50,60', 0.9);
  }
  CM.lances = CM.lances.filter(l => l.t < l.warn + l.life + 0.25);
}
function cmDrawLances() {
  const fs = fxSheet('cm_lance');
  for (const l of CM.lances) {
    const x = Math.round(l.x), y = Math.round(l.y);
    if (l.t < l.warn) {   // warning: a bubbling slit in the floor, brightening
      const k = l.t / l.warn, w = 4 + Math.round(8 * k);
      g.fillStyle = `rgba(60,0,8,${0.5 + 0.4 * k})`; g.fillRect(x - w, y - 2, w * 2, 2);
      g.fillStyle = `rgba(230,60,70,${0.4 + 0.6 * k * (0.6 + 0.4 * Math.sin(time * 40))})`; g.fillRect(x - Math.round(w * 0.6), y - 2, Math.round(w * 1.2), 1);
      if (k > 0.5) { g.fillStyle = `rgba(200,40,50,${0.2 * k})`; g.fillRect(x - 1, y - l.h, 2, l.h); }
      continue;
    }
    const k = (l.t - l.warn) / l.life, rise = Math.min(1, k * 5), fade = k > 0.75 ? Math.max(0, 1 - (k - 0.75) * 4) : 1;
    if (fs.ok) {
      const t = fs.tag(Object.keys(fs.tags)[0]), n = t.to - t.from + 1;
      drawSprite(fs, t.from + Math.min(n - 1, Math.floor(k * n)), x, y, 1, { bottom: true, alpha: fade });
    } else {
      const h = Math.round(l.h * rise);
      for (let j = 0; j < h; j++) { const w = Math.max(1, Math.round((l.w / 2) * (1 - j / h) + 0.5)); g.fillStyle = j > h - 6 ? `rgba(255,170,160,${fade})` : j % 5 === 0 ? `rgba(120,8,20,${fade})` : `rgba(190,28,40,${fade})`; g.fillRect(x - w, y - j - 1, w * 2, 1); }
    }
  }
}
// low travelling blood waves (landing splashes, the phase-2 tide): jump or roll through them
function cmWave(x, y, dir, opt = {}) { const w = { x, y, dir, v: opt.v ?? 170, h: opt.h ?? 14, w: opt.w ?? 16, dmg: opt.dmg ?? 24, life: opt.life ?? 2.2, t: 0, id: ++hazardId, src: opt.src || null, big: !!opt.big, tele: opt.tele || 0 }; CM.waves.push(w); return w; }
function cmUpdateWaves(dt, L = 0, R = room.pw) {
  for (const w of CM.waves) {
    w.t += dt;
    if (w.t < w.tele) { if (Math.random() < dt * 20) particles.push({ x: w.x + rand(-6, 6), y: w.y - rand(0, 10), vx: 0, vy: -rand(20, 60), g: 200, life: 0.4, kind: 'blood' }); continue; }
    w.x += w.dir * w.v * dt; w.life -= dt;
    if (w.x < L - 20 || w.x > R + 20) w.life = 0;
    if (overlap(rect(w.x - w.w / 2, w.y - w.h, w.x + w.w / 2, w.y), playerHurtbox())) hurtPlayer(BOSS_DMG * w.dmg * NGP.dmg, w.dir, w.id, { src: w.src });
    if (Math.random() < dt * 30) particles.push({ x: w.x + rand(-w.w / 2, w.w / 2), y: w.y - rand(0, w.h), vx: w.dir * rand(10, 60), vy: -rand(20, 80), g: 400, life: 0.4, kind: 'blood' });
    addLight(w.x, w.y - w.h / 2, 30 + w.h, '220,40,50', 0.5);
  }
  CM.waves = CM.waves.filter(w => w.life > 0);
}
function cmDrawWaves() {
  for (const w of CM.waves) {
    const x = Math.round(w.x), y = Math.round(w.y);
    if (w.t < w.tele) {   // the swell gathering at the wall
      const k = w.t / w.tele, h = Math.round(w.h * 0.6 * k);
      g.fillStyle = `rgba(150,14,26,${0.5 + 0.4 * k})`; g.fillRect(x - 10, y - h, 20, h);
      g.fillStyle = `rgba(255,120,110,${k * (0.5 + 0.5 * Math.sin(time * 30))})`; g.fillRect(x - 10, y - h, 20, 1);
      continue;
    }
    for (let i = -w.w; i <= w.w; i++) {
      const u = i / w.w, h = Math.round(w.h * Math.max(0, 1 - u * u) * (1 + 0.25 * (u * w.dir)));
      if (h <= 0) continue;
      g.fillStyle = 'rgba(120,8,20,0.92)'; g.fillRect(x + i, y - h, 1, h);
      g.fillStyle = 'rgba(210,50,60,0.95)'; g.fillRect(x + i, y - h, 1, 2);
      if ((i + Math.floor(time * 20)) % 5 === 0) { g.fillStyle = 'rgba(255,170,160,0.9)'; g.fillRect(x + i, y - h, 1, 1); }
    }
  }
}
// bat swarms (teleports): pure visuals, a cloud of little bats streaming from A to B
function cmBatSwarm(x0, y0, x1, y1, n = 16, dur = 0.5) {
  for (let i = 0; i < n; i++) CM.bats.push({ x0: x0 + rand(-12, 12), y0: y0 - rand(10, 60), x1: x1 + rand(-10, 10), y1: y1 - rand(10, 60), t: -rand(0, 0.18), dur: dur * rand(0.8, 1.2), wob: rand(0, 6), amp: rand(8, 26) });
  cmSfx.bats();
}
function cmUpdateBats(dt) { for (const b of CM.bats) b.t += dt; CM.bats = CM.bats.filter(b => b.t < b.dur); }
function cmDrawBats() {
  const bs = fxSheet('cm_bat');
  for (const b of CM.bats) {
    if (b.t < 0) continue;
    const k = b.t / b.dur, e = k * k * (3 - 2 * k), x = lerp(b.x0, b.x1, e), y = lerp(b.y0, b.y1, e) - Math.sin(k * Math.PI) * b.amp + Math.sin(time * 20 + b.wob) * 2;
    if (bs.ok) { const t = bs.tag(Object.keys(bs.tags)[0]), n = t.to - t.from + 1; drawSprite(bs, t.from + Math.floor(time * 18 + b.wob) % n, x, y, b.x1 > b.x0 ? 1 : -1, { center: true }); }
    else { const f = Math.floor(time * 18 + b.wob) % 2; g.fillStyle = '#12060a'; g.fillRect(Math.round(x) - 2, Math.round(y) - f, 2, 1); g.fillRect(Math.round(x) + 1, Math.round(y) - f, 2, 1); g.fillRect(Math.round(x), Math.round(y), 1, 1); g.fillStyle = '#ff4040'; g.fillRect(Math.round(x), Math.round(y), 1, 1); }
  }
}

// ================================================================== main update / render hooks
HOOKS.update.push(dt => {
  if (!cmIn()) return;
  cmEnsure();
  cmUpdatePools(dt); cmUpdateRain(dt); cmUpdateChands(dt); cmUpdateShots(dt); cmUpdateLances(dt); cmUpdateBats(dt);
  const B = boss && boss.alive && boss.active ? boss : null;
  cmUpdateWaves(dt, B ? B.L : 0, B ? B.R : room.pw);
  for (const p of props) if (p.cmVeil) { addLight(p.x, p.y - p.h / 2, 46, '220,40,50', 0.8); if (Math.random() < dt * 6) particles.push({ x: p.x + rand(-6, 6), y: p.y - rand(0, p.h), vx: 0, vy: rand(20, 50), life: 0.6, kind: 'blood' }); }
  if (room.id === 'CM1' && !SAVE.items.emberdash && !CM.veilHint && P.x > 3 * TILE && P.x < 7 * TILE) { CM.veilHint = true; toast('A curtain of living blood, hard as glass. Only something that burns could pass through it.', 4); }
  if (room.id === 'CM7') cmBallroomUpdate(dt);
});
HOOKS.render.push(() => {
  if (!cmIn()) return;
  cmDrawPools(); cmDrawChands(); cmDrawLances(); cmDrawWaves(); cmDrawShots(); cmDrawBats();
  if (room.id === 'CM7') cmBallroomDraw();
});
HOOKS.renderTop.push(() => {
  try { cmMusicTick(); } catch (e) {}
  if (!cmIn()) return;
  if (CM.rain) cmDrawRain();
  if (room.id === 'CM7' && CM.col && CM.col.k > 0) { const r0 = CM.rain; CM.rain = { k: boss && boss.alive ? 0.6 : 0.3 }; cmDrawRain(); CM.rain = r0; }
});

// ================================================================== enemies
Object.assign(ENEMY, {
  cm_servant: { hp: 150, cinders: 190, speed: 36, aggro: 180, range: 150, poise: 22, stance: 80, dmg: { slash: 24, lunge: 32 }, cool: [0.7, 1.4], lunge: { slash: 70 } },
  cm_hound: { hp: 120, cinders: 150, speed: 118, aggro: 210, range: 110, poise: 14, stance: 55, dmg: { bite: 28 }, cool: [1.0, 1.8] },
  cm_gargoyle: { hp: 85, cinders: 130, speed: 92, aggro: 180, range: 130, poise: 8, stance: 32, dmg: { dive: 26 }, cool: [1.4, 2.4], flying: true },
});
Object.assign(ATTACK_TAGS, { cm_servant: ['slash', 'lunge'], cm_hound: ['bite'], cm_gargoyle: ['dive'] });
const CM_LIVE = ['hurt', 'stagger', 'parried', 'dead'];
function cmPre(e, dt) {   // Enemy.update's bookkeeping, so our brains can run their own switch
  e.flash = Math.max(0, e.flash - dt * 5); e.poise = Math.max(0, e.poise - dt * 12); e.stance = Math.max(0, e.stance - dt * 6);
  e.bleed = Math.max(0, e.bleed - dt * 6); e.dmgT -= dt;
  if (e.rotT > 0) { e.rotT -= dt; e.hp -= e.maxHp * 0.025 * dt; if (e.hp <= 0) { e.die({ dir: 0 }); return false; } }
  e.anim.update(dt);
  if (!e.aggro && e.canSee()) { e.aggro = true; e.cool = Math.max(e.cool, 0.4); }
  if (e.aggro && (Math.abs(e.dist()) > e.cfg.aggro * 1.9 || Math.abs(P.y - e.y) > 170 || P.state === 'dead')) { e.lostT += dt; if (e.lostT > 2.5) { e.aggro = false; e.lostT = 0; } } else e.lostT = 0;
  e.cool -= dt;
  return true;
}

// ---- manor servant: knives, a leaping stab from mid range; some wait inside the portraits
class CmServant extends Enemy {
  cmEmerge(fy) { this.state = 'emerge'; this.emergeFy = fy; this.aggro = true; this.vy = 40; this.facePlayer(); this.anim.set(this.sh.has('emerge') ? 'emerge' : 'idle', false); this.anim.i = 0; }
  update(dt) {
    if (this.state === 'emerge') {
      this.flash = Math.max(0, this.flash - dt * 5);
      this.vy = Math.min(this.vy + 800 * dt, 400); moveBody(this, dt); this.clampRoom();
      if (!this.ground) { this.anim.i = 0; this.anim.t = 0; } else this.anim.update(dt);
      if (this.ground && (this.anim.done || !this.sh.has('emerge'))) { this.setA('idle', 'idle'); this.cool = 0.35; }
      return;
    }
    if (CM_LIVE.includes(this.state)) return super.update(dt);
    if (!cmPre(this, dt)) return;
    const dx = this.dist(), adx = Math.abs(dx), dy = P.y - this.y;
    switch (this.state) {
      case 'idle': case 'walk': {
        if (!this.aggro) { this.patrol(dt); break; }
        this.facePlayer();
        if (this.cool <= 0 && adx < 44 && Math.abs(dy) < 30) { this.startAttack('slash'); break; }
        if (this.cool <= 0 && adx > 72 && adx < 150 && Math.abs(dy) < 24 && this.ground && this.canSee() && ledgeAhead({ x: this.x + this.face * 60, y: this.y, w: this.w }, this.face)) { this.startAttack('lunge'); break; }
        this.walk(adx > 40 ? sign(dx) : 0, dt, adx > 110 ? 1.2 : 1);
        break;
      }
      case 'attack': {
        const an = this.anim, w = metaWindows(this.sh, 'lunge')[0];
        if (this.atk === 'lunge' && an.changed && w && an.i === w.active[0]) { this.vx = this.face * 230; this.vy = -150; this.ground = false; }
        this.updateAttack(dt);
        if (this.atk === 'lunge' && w && an.i >= w.active[0] && !this.ground) this.vx = approach(this.vx, this.face * 200, 400 * dt);
        break;
      }
    }
    if (this.alive) addLight(this.x + this.face * 3, this.y - 30, 14, '255,50,50', 0.35);
  }
}
// ---- blood hound: runs you down, a long lunging bite, then wheels away
class CmHound extends Enemy {
  update(dt) {
    if (CM_LIVE.includes(this.state)) return super.update(dt);
    if (!cmPre(this, dt)) return;
    const dx = this.dist(), adx = Math.abs(dx), dy = P.y - this.y;
    switch (this.state) {
      case 'idle': case 'walk': {
        if (!this.aggro) { this.patrol(dt); break; }
        this.facePlayer();
        if (this.backT > 0) { this.backT -= dt; this.walk(-sign(dx), dt, 0.8); this.face = sign(dx); break; }
        if (this.cool <= 0 && adx < 96 && adx > 20 && Math.abs(dy) < 26 && this.ground && ledgeAhead({ x: this.x + this.face * 50, y: this.y, w: this.w }, this.face)) { this.startAttack('bite'); break; }
        this.walk(adx > 30 ? sign(dx) : 0, dt, 1);
        break;
      }
      case 'attack': {
        const an = this.anim, w = metaWindows(this.sh, 'bite')[0];
        if (an.changed && w && an.i === w.active[0]) { this.vx = this.face * 240; this.vy = -110; this.ground = false; }
        if (an.i < (w ? w.active[0] : 4)) this.vx *= Math.pow(0.001, dt);
        this.updateAttack(dt);
        if (this.state === 'idle') this.backT = rand(0.4, 0.8);
        break;
      }
    }
    if (this.alive) addLight(this.x + this.face * 14, this.y - 16, 14, '255,40,40', 0.3);
  }
}
// ---- gargoyle-bat: sleeps like stone on the facade, wakes, circles, dives
class CmGargoyle extends Enemy {
  constructor(type, x, y, key) { super(type, x, y, key); this.orb = rand(0, 6.28); this.orbR = rand(50, 80); }
  perch(fy) { this.state = 'perch'; this.y = fy - 17; this.hy = this.y; this.anim.set(this.sh.has('perch') ? 'perch' : 'fly', true); this.anim.t = rand(0, 400); this.face = Math.random() < 0.5 ? -1 : 1; }
  hit(info) { if (this.state === 'perch') this.wake(); super.hit(info); }
  hurtbox() { const m = this.sh.meta; if (this.state === 'perch' && this.alive && m && m.perch && m.perch.hurtbox) return metaRect(this.sh, this, m.perch.hurtbox); return super.hurtbox(); }
  wake() { if (this.state !== 'perch') return; this.state = 'wake'; this.anim.set(this.sh.has('wake') ? 'wake' : 'fly', false); this.vy = -70; this.aggro = true; tone(1400, 0.2, 0.04, 'sawtooth', 0.6); sfx.crumble(); }
  updateFlying(dt) {
    const c = this.cfg; this.t += dt; this.cool -= dt;
    const clampFly = () => { this.x = clamp(this.x, 10, room.pw - 10); this.y = clamp(this.y, 14, room.ph - 10); };
    switch (this.state) {
      case 'perch':
        if (Math.abs(P.x - this.x) < 90 && Math.abs(P.y - this.y) < 80) this.wake();
        return;
      case 'wake':
        this.y += this.vy * dt; this.vy = approach(this.vy, -20, 200 * dt); this.facePlayer();
        if (this.anim.done || !this.sh.has('wake')) { this.state = 'idle'; this.anim.set('fly', true); this.cool = rand(0.6, 1.4); }
        break;
      case 'idle': case 'walk': {
        if (this.anim.tag !== 'fly') this.anim.set('fly', true);
        if (!this.aggro && this.canSee()) this.aggro = true;
        let tx = this.home, ty = this.hy + Math.sin(this.t * 2) * 8;
        if (this.aggro) { const a = this.t * 1.3 + this.orb; tx = P.x + Math.cos(a) * this.orbR; ty = P.y - 60 + Math.sin(a * 1.6) * 12; this.face = sign(P.x - this.x); }
        this.vx = approach(this.vx, clamp((tx - this.x) * 2, -c.speed, c.speed), 240 * dt);
        this.vy = approach(this.vy, clamp((ty - this.y) * 2, -c.speed, c.speed), 240 * dt);
        this.x += this.vx * dt; this.y += this.vy * dt; clampFly();
        if (solidAtPx(this.x, this.y)) { this.x -= this.vx * dt; this.y -= this.vy * dt; this.vx *= -0.5; this.vy *= -0.5; }
        if (this.aggro && this.cool <= 0 && (CM.diveT || 0) < time && Math.abs(P.x - this.x) < 140 && P.y > this.y + 16 && lineOfSight(this.x, this.y, P.x, P.y - 14)) {
          this.startAttack('dive'); CM.diveT = time + 0.8; this.diveAt = { x: P.x, y: P.y - 12 }; this.vx *= 0.2; this.vy *= 0.2;
        }
        break;
      }
      case 'attack': {
        const an = this.anim, w = metaWindows(this.sh, 'dive')[0] || { active: [2, 4] };
        if (an.i < w.active[0]) { this.vx *= Math.pow(0.02, dt); this.vy = approach(this.vy, -30, 200 * dt); this.face = sign(this.diveAt.x - this.x); if (an.changed && an.i === Math.max(0, w.active[0] - 1)) spawnFx('telegraph', this.x + this.face * 6, this.y - 6, this.face); }
        else if (an.i <= w.active[1]) {
          if (!this.dv) { const a = Math.atan2(this.diveAt.y - this.y, this.diveAt.x - this.x); this.dv = { x: Math.cos(a), y: Math.sin(a) }; sfx.swing(); }
          this.vx = this.dv.x * 240; this.vy = this.dv.y * 240;
          if (!this.hitIds.has(0) && overlap(this.hurtbox(), playerHurtbox()) && hurtPlayer(c.dmg.dive * NGP.dmg, sign(this.vx), this.atkId, { parryable: true, src: this })) this.hitIds.add(0);
          if (an.i === w.active[1] && an.t > an.ms() * 0.7 && this.y < this.diveAt.y && Math.hypot(this.diveAt.x - this.x, this.diveAt.y - this.y) > 14) an.t = 0;
        } else { this.vy = approach(this.vy, -140, 600 * dt); this.vx *= Math.pow(0.3, dt); }
        this.x += this.vx * dt; this.y += this.vy * dt; clampFly();
        if (solidAtPx(this.x, this.y + 6)) { this.y -= 6; this.vy = -120; }
        if (an.done) { this.dv = null; this.state = 'idle'; this.anim.set('fly', true); this.cool = rand(...c.cool); }
        break;
      }
      case 'hurt':
        this.vx *= Math.pow(0.05, dt); this.vy *= Math.pow(0.05, dt); this.x += this.vx * dt; this.y += this.vy * dt; clampFly();
        if (this.anim.done) { this.state = 'idle'; this.anim.set('fly', true); this.cool = Math.max(this.cool, 0.5); }
        break;
      case 'stagger': case 'parried':
        this.t -= dt * 2; this.y += 30 * dt; clampFly(); if (this.anim.done) this.anim.hold();
        if (this.t <= 0 || this.t > 100) { this.state = 'idle'; this.anim.set('fly', true); this.cool = 0.6; this.t = 0; }
        break;
    }
    if (this.state !== 'perch') addLight(this.x, this.y - 4, 16, '255,50,50', 0.3);
  }
}
Object.assign(ENEMY_CLASSES, { cm_servant: CmServant, cm_hound: CmHound, cm_gargoyle: CmGargoyle });
function cmPerchSpawn(s, c, onlyMissing) {
  const have = new Set(enemies.map(e => e.key));
  for (let k = 0; k < (s.n || 2); k++) {
    const key = `${c.key}:${k}`; if (killed.has(key) || (onlyMissing && have.has(key))) continue;
    const e = makeEnemy('cm_gargoyle', c.cx + (k - ((s.n || 2) - 1) / 2) * 22, c.fy, key);
    e.perch(c.fy); enemies.push(e);
  }
}
SPAWNS.cm_perch = (s, c) => { cmEnsure(); cmPerchSpawn(s, c, false); };
HOOKS.rest.push(() => {
  if (!cmIn()) return;
  (room.def.spawns || []).forEach((s, i) => { if (s.t === 'cm_perch') cmPerchSpawn(s, { cx: s.x * TILE + 8, fy: (s.y + 1) * TILE, key: `${room.id}:sp${i}` }, true); });
});

// ================================================================== THE BUTLER (mini-boss, CM6)
BOSS_INFO.butler = { name: 'Vesper, the Butler', hp: 1500, cinders: 6500, reward: ['w:carving_knife', 'emberstone'],
  quote: 'Four hundred years of service, and not one guest ever left unattended.' };
function cmMakeButler(x, y) {
  const B = new MetaBoss('butler', x, y, {
    sheets: ['butler', 'butler_p2'], stanceMax: 240, walkSpeed: 32, prefer: 60, p2at: 0.5, p2speed: 1.2, p2tag: 'flourish', critRange: 56,
    introTag: 'idle', cool1: [0.8, 1.3], cool2: [0.5, 0.9], victory: 'THE SERVICE ENDS', deathParticle: 'blood',
    weights(d, p2) {
      const behind = (P.x - this.x) * this.face < 0;
      if (behind && d < 80) return { flourish: 3, vanish: 1 };
      if (d < 64) return { slash: 3, flourish: p2 ? 1.4 : 0.8, backstep: 1, thrust: 0.6, vanish: p2 ? 0.8 : 0.3 };
      if (d < 150) return { thrust: 2.4, serve: 1.4, vanish: p2 ? 1.4 : 0.8, walk: 1 };
      return { serve: 2, vanish: p2 ? 1.8 : 1.1, walk: 1.6, thrust: 0.6 };
    },
    chains: { slash(d) { return d < 70 ? 'thrust' : 'serve'; }, backstep: 'serve', serve(d) { return d < 130 ? 'thrust' : null; }, thrust: 'slash', flourish: 'slash' },
    moves: {
      slash: { dmg: [30, 34], step: 50, parry: true, fx: 'cm_slash' },
      thrust: { dmg: [42], parry: true, on: { 4() { this.cmDash = { v: this.face * 330, t: 0.24 }; sfx.bossSwing(); } } },
      serve: { dmg: [], spawn(at) {
        const n = this.phase === 2 ? 5 : 3, base = Math.atan2(P.y - 14 - at.y, P.x - at.x);
        for (let k = 0; k < n; k++) { const a = base + (k - (n - 1) / 2) * 0.17; cmShot({ x: at.x, y: at.y, vx: Math.cos(a) * 250, vy: Math.sin(a) * 250, dmg: BOSS_DMG * 22 * NGP.dmg, src: this, life: 2 }); }
        cmSfx.knife(); sfx.shoot();
      } },
      flourish: { dmg: [38], shake: 4, on: { 5() { cmSfx.bats(); for (let i = 0; i < 20; i++) { const a = rand(0, 6.28); CM.bats.push({ x0: this.x, y0: this.y - 30, x1: this.x + Math.cos(a) * 70, y1: this.y - 30 + Math.sin(a) * 40, t: -rand(0, 0.1), dur: 0.5, wob: rand(0, 6), amp: 6 }); } } } },
      vanish: { dmg: [], on: {
        2() { cmBatSwarm(this.x, this.y, this.cmBlinkX(), this.y, 14, 0.4); },
        4() { this.x = this.cmBlinkX(); this.facePlayer(); },
        7() { this.cmNext = Math.abs(P.x - this.x) < 70 ? 'slash' : 'thrust'; },
      } },
    },
    wake() { return P.x > 3 * TILE + 8 && P.x < 25 * TILE; },
    ambient(dt) {
      addLight(this.x, this.y - 44, 50, '255,190,150', 0.4);
      if (this.cmDash) { this.cmDash.t -= dt; this.x = clamp(this.x + this.cmDash.v * dt, this.L, this.R); if (this.cmDash.t <= 0 || this.state !== 'attack') this.cmDash = null; }
      if (this.cmNext && this.state === 'idle' && this.alive) { const m = this.cmNext; this.cmNext = null; this.start(m); }
      if (this.phase === 2 && this.alive && Math.random() < dt * 3) particles.push({ x: this.x + rand(-10, 10), y: this.y - rand(20, 60), vx: 0, vy: rand(10, 30), life: 0.6, kind: 'blood' });
    },
    onPhase2() { toast('His coat-tails tear open into wings. The service grows impatient.', 3); shake = 6; sfx.roar(); cmSfx.bats(); },
    onDeath() { CM.shots = []; victoryBanner = { text: 'THE SERVICE ENDS', t: 0 }; cmBatSwarm(this.x, this.y, this.x, this.y - 140, 24, 1.2); },
  });
  B.cmBlinkX = function () {   // behind your back, never past a fog wall; cornered -> in front of you instead
    let tx = clamp(P.x - P.face * 52, this.L + 12, this.R - 12);
    if (Math.abs(tx - P.x) < 36) tx = clamp(P.x + P.face * 60, this.L + 12, this.R - 12);
    return tx;
  };
  Object.defineProperty(B, 'L', { get() { return 2 * TILE + 18; } });
  Object.defineProperty(B, 'R', { get() { return 25 * TILE - 18; } });
  B.hurtbox = function () {
    if (!this.alive) return null;
    if (this.state === 'attack' && this.atk === 'vanish' && this.anim.i >= 2 && this.anim.i <= 5) return null;   // a cloud of bats
    const m = this.sh.meta; return m && m.hurtbox ? metaRect(this.sh, this, m.hurtbox) : rect(this.x - 10, this.y - 60, this.x + 10, this.y);
  };
  const base = B.canStagger.bind(B);
  B.canStagger = function () { return base() && !(this.state === 'attack' && this.atk === 'vanish'); };
  return B;
}
BOSS_SPAWN.butler = (cx, fy) => cmMakeButler(cx, fy);
BOSS_CUTS.butler = b => [
  act(() => { b.face = 1; b.anim.set('idle', true); }),
  bossPan(b, 40, 1.2),
  say('', 'Someone is laying the long table for a supper that never comes.'),
  act(() => { b.facePlayer(); cmSfx.chime(); }), wait(0.5),
  say('The Butler', 'Madam is not receiving guests. I shall see you out.'),
  act(() => { holdAnim(b, 'flourish'); cmSfx.bats(); cmBatSwarm(b.x, b.y, b.x + rand(-40, 40), b.y - 20, 16, 0.8); shake = 4; }), wait(1.1),
];
PHASE2_LINES.butler = ['The Butler', 'Forgive me, Madam. I must be less… courteous.'];

// ================================================================== COUNTESS SANGUINE, THE VAMPIRE QUEEN-KNIGHT (CM7)
// Phase 1: blood-blade combos of 3-5 cuts, blood-charge dashes, sneak attacks out of a bat swarm, blood lances, the
// Crimson Requiem (a string of near-instant charges across the whole hall, each flagged by a blood-line flash) and a
// blood-drain grab that heals her (interrupt the wind-up with hits, or mash to break free once caught).
// Phase 2 (50%): she tears the ballroom apart -- the vault and the upper walls shatter and fall, the red sky and the manor's
// towers show through, blood rain, falling masonry; blood wings: dives, spike volleys, longer requiems, harder combos.
BOSS_INFO.sanguine = { name: 'Countess Sanguine', hp: 3200, cinders: 16000, reward: ['w:sanguine_rapier', 'sp:crimson_rite', 'c_countess'],
  quote: '“Every guest leaves something behind. Most leave everything.”' };
const CM_SG = { slash1: 30, slash2: 30, thrust: 34, spin: 30, overhead: 44, charge: 40, chargeend: 30, req: 32, lance: 30, drain: 15, bite: 18,
  dive: 44, spike: 20, drop: 22, debris: 30, shock: 24 };
const CM_COMBOS1 = [['slash1', 'slash2', 'thrust'], ['slash1', 'slash2', 'spin'], ['thrust', 'slash2', 'overhead'], ['slash2', 'slash1', 'thrust', 'overhead']];
const CM_COMBOS2 = [['slash1', 'slash2', 'thrust', 'overhead'], ['slash1', 'spin', 'slash2', 'thrust', 'overhead'], ['thrust', 'slash2', 'slash1', 'spin'],
  ['slash2', 'slash1', 'spin', 'thrust', 'overhead']];
class CmSanguine extends BossBase {
  constructor(x, y) {
    super('sanguine', x, y);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.sanguine.hp * NGP.hp);
    const meta = ASSETS.sanguine_meta;
    this.sheets = [sheet('sanguine', { meta }), sheet('sanguine_p2', { meta })];
    this.sh = this.sheets[0]; this.anim = new Anim(this.sh, 'idle'); this.state = 'dormant'; this.face = -1;
    this.stanceMax = 320; this.critRange = 80; this.alt = 0; this.cool = 1; this.q = []; this.combo = []; this.hidden = false; this.last = null;
    this.reqCd = 6; this.grabCd = 4; this.skyCd = 0; this.dirT = 4; this.after = [];
  }
  get L() { return 2 * TILE + 30; }
  get R() { return room.pw - TILE - 30; }
  get maxAlt() { return this.floor - (2 * TILE + 118); }
  ambient() { if (this.alive && !this.hidden) addLight(this.x, this.y - 70, 90, '230,80,80', 0.7); }
  fm(tag = this.anim.tag, i = this.anim.i) { const m = this.sh.meta, f = m && m.frames && m.frames[tag]; return f ? f[Math.min(i, f.length - 1)] : null; }
  mpt(key, fb) { const f = this.fm(); return f && f[key] ? metaPoint(this.sh, this, f[key]) : fb; }
  hurtbox() {
    if (!this.alive || this.hidden || (this.state === 'dormant' && !this.active)) return null;
    const f = this.fm(); if (f && f.hb) return metaRect(this.sh, this, f.hb);
    return rect(this.x - 16, this.y - 106, this.x + 16, this.y);
  }
  hit(info) {
    if (this.hidden) return;
    const hp0 = this.hp;
    super.hit(info);
    if (this.state === 'attack' && this.atk === 'grab' && this.anim.i < 4 && this.alive) {   // interrupt the drain grab
      this.grabDmg = (this.grabDmg || 0) + (hp0 - this.hp) + (info.kind === 'heavy' ? 40 : 0);
      if (this.grabDmg >= 90 * NGP.hp) this.flinch('Interrupted!');
    }
  }
  canStagger() { return !this.hidden && this.alt < 4 && ['idle', 'walk', 'attack', 'recover', 'charge'].includes(this.state); }
  setA(tag, loop = false, speed = 1) { this.anim.set(this.sh.has(tag) ? tag : 'idle', loop, speed * (this.phase === 2 ? 1.1 : 1)); }
  later(t, fn) { this.q.push({ t, fn }); }
  wakeCheck() { return P.x > 3 * TILE + 8 && P.x < this.R && P.state !== 'dead'; }
  dmg(k) { return BOSS_DMG * CM_SG[k] * (this.phase === 2 ? 1.1 : 1) * NGP.dmg; }
  flinch(msg) {
    this.state = 'recover'; this.t = 1.1; this.combo = []; this.setA('stagger'); this.anim.speed = 0.8; sfx.glint();
    spawnFx(fxOr('parry_flash', 'parry_spark'), this.x, this.y - 70, this.face); if (msg) toast(msg, 1.4);
  }
  update(dt) {
    this.commonUpdate(dt);
    const an = this.anim; an.update(dt);
    if (!this.active) { if (!this.cutting && this.wakeCheck()) this.activate(); if (!this.cutting) this.facePlayer(); return; }
    if (this.introT > 0) { this.introT -= dt; if (this.introT <= 0) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.6; } }
    if (this.alive) { for (const e of this.q) { e.t -= dt; if (e.t <= 0 && !e.done) { e.done = true; e.fn(); } } this.q = this.q.filter(e => !e.done); }
    this.skyCd -= dt; this.reqCd -= dt; this.grabCd -= dt;
    for (const a of this.after) a.t -= dt; this.after = this.after.filter(a => a.t > 0);
    switch (this.state) {
      case 'idle':
        this.cool -= dt;
        if (an.tag !== 'idle' && an.tag !== 'fly') this.setA(this.alt > 4 ? 'fly' : 'idle', true);
        if (P.state === 'dead') break;
        this.facePlayer();
        if (this.cool <= 0) this.choose();
        break;
      case 'walk': {
        this.t -= dt; this.cool -= dt; this.facePlayer();
        const d = Math.abs(P.x - this.x), dir = d > this.want ? this.face : -this.face;
        this.x = clamp(this.x + dir * 72 * this.speed * dt, this.L, this.R);
        if (this.t <= 0 || Math.abs(d - this.want) < 14) { this.state = 'idle'; this.cool = Math.min(this.cool, 0.1); }
        break;
      }
      case 'attack': this.updateAttack(dt); break;
      case 'charge': this.updateCharge(dt); break;
      case 'vanish':
        if (an.done || !this.sh.has('vanish')) { this.hidden = true; this.state = this.batNext || 'bats'; this.t = 0.4; }
        break;
      case 'bats':
        this.t -= dt;
        if (this.t <= 0) { this.x = this.batTo; this.hidden = false; this.facePlayer(); this.state = 'appear'; this.setA('appear', false, 1.25); }
        break;
      case 'appear':
        if (an.done || !this.sh.has('appear')) this.startCombo(this.phase === 2 ? ['thrust', 'slash2', 'slash1'] : ['thrust', 'slash2'], 1.3);
        break;
      case 'requiem': this.updateRequiem(dt); break;
      case 'drain': this.updateDrain(dt); break;
      case 'recover':
        this.t -= dt;
        if (this.t <= 0) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.3; }
        break;
      case 'takeoff':
        this.alt = approach(this.alt, this.hoverAlt, 240 * dt); this.facePlayer();
        if (this.alt >= this.hoverAlt - 1) { this.state = 'hover'; this.t = rand(0.35, 0.6); }
        break;
      case 'hover': {
        this.t -= dt; this.facePlayer();
        this.x = approach(this.x, clamp(P.x - this.face * 80, this.L + 16, this.R - 16), 140 * dt);
        this.alt = approach(this.alt, this.hoverAlt + Math.sin(time * 3) * 4, 60 * dt);
        if (this.t <= 0) this.airMove();
        break;
      }
      case 'diveprep':
        this.t -= dt; this.face = this.diveTo < this.x ? -1 : 1;
        if (this.t <= 0) { this.state = 'dive'; this.diveV = null; sfx.bossSwing(); }
        break;
      case 'dive': {
        if (!this.diveV) { const dx = this.diveTo - this.x, dy = this.alt, d = Math.hypot(dx, dy) || 1; this.diveV = { x: dx / d * 470, y: dy / d * 470 }; }
        this.x = clamp(this.x + this.diveV.x * dt, this.L, this.R); this.alt = Math.max(0, this.alt - this.diveV.y * dt);
        if (Math.abs(this.x - (this.lastAfterX ?? -1e9)) > 24) { this.lastAfterX = this.x; this.after.push({ x: this.x, y: this.floor - this.alt, f: an.frame, face: this.face, t: 0.18 }); }
        const w = metaWindows(this.sh, 'dive')[0], r = w && w.hit ? metaRect(this.sh, this, w.hit) : rect(this.x - 22, this.y - 70, this.x + 30, this.y);
        if (!this.hitIds.has(0) && (overlap(r, playerHurtbox()) || overlap(this.hurtbox() || r, playerHurtbox())) && hurtPlayer(this.dmg('dive'), this.face, this.atkId, { src: this })) this.hitIds.add(0);
        if (this.alt <= 0 || (this.x <= this.L + 0.5 && this.diveV.x < 0) || (this.x >= this.R - 0.5 && this.diveV.x > 0)) this.land(true);
        break;
      }
      case 'volley': {
        const sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn.volley;
        this.facePlayer();
        if (!this.fired && an.i >= (sp ? sp.frame : 4)) { this.fired = true; this.spikeVolley(sp ? metaPoint(this.sh, this, sp.at) : { x: this.x, y: this.y - 100 }); }
        if (an.done || !this.sh.has('volley')) { this.state = 'hover'; this.t = 0.3; this.setA('fly', true); }
        break;
      }
      case 'airrain':
        this.t -= dt; this.x = approach(this.x, clamp(P.x - this.face * 40, this.L + 20, this.R - 20), 60 * dt);
        if (!this.fired && this.t < 1.6) { this.fired = true; this.rainVolley(9); }
        if (this.fired && !this.fired2 && this.t < 0.7) { this.fired2 = true; this.rainVolley(8); }
        if (this.t <= 0) { this.state = 'hover'; this.t = 0.2; this.setA('fly', true); }
        break;
      case 'descend':
        this.alt = Math.max(0, this.alt - 180 * dt);
        if (this.alt <= 0) this.land(false);
        break;
      case 'transform':
        this.tT += dt;
        if (Math.random() < 0.9) particles.push({ x: this.x + rand(-30, 30), y: this.y - rand(0, 100), vx: rand(-40, 40), vy: -rand(20, 90), g: 60, life: rand(0.6, 1.2), kind: 'blood' });
        if (this.tT > 0.9 && (an.done || !this.sh.has('transform'))) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.4; this.skyCd = 1.5; this.reqCd = 3; }
        break;
      case 'stagger':
        this.t -= dt;
        if (an.i === an.n - 1 && this.t > 0.3) an.hold();
        if (an.done || this.t <= 0) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.35; }
        break;
      case 'dead':
        this.alt = Math.max(0, this.alt - 200 * dt);
        if (Math.random() < 0.6) particles.push({ x: this.x + rand(-30, 30), y: this.y - rand(0, 90), vx: rand(-10, 10), vy: -rand(10, 40), life: rand(0.8, 1.6), kind: 'blood' });
        if (an.done) an.hold();
        break;
    }
    if (this.alive && this.phase === 1 && this.hp <= this.maxHp * 0.5) this.pendingPhase = true;
    if (this.pendingPhase && this.alive && ['idle', 'walk', 'recover'].includes(this.state) && this.alt <= 0 && !CM.held) { this.pendingPhase = false; this.enterPhase2(); }
    if (this.phase === 2 && this.alive && this.state !== 'transform') this.director(dt);
    this.x = clamp(this.x, this.L, this.R);
    this.alt = clamp(this.alt, 0, this.maxAlt);
    this.y = this.floor - this.alt;
    this.camX = this.x;
    if (this.alive && this.active && !this.hidden) addLight(this.x, this.y - 70, 70, '230,60,70', 0.45);
  }
  // ---------------------------------------------------------------- choice
  choose() {
    if (this.pendingPhase) return;
    const d = Math.abs(P.x - this.x), p2 = this.phase === 2;
    let w;
    if (d < 100) w = { combo: 3.2, grab: this.grabCd > 0 ? 0 : 1.3, sneak: 0.5, walkback: 0.4 };
    else if (d < 220) w = { charge: 2.4, combo: 1.2, sneak: 1.2, lances: 1.0, grab: this.grabCd > 0 ? 0 : 0.5 };
    else w = { charge: 2.6, lances: 1.6, sneak: 1.4, walk: 0.6 };
    if ((this.hp < this.maxHp * 0.75 || p2) && this.reqCd <= 0) w.requiem = p2 ? 2.0 : 1.4;
    if (p2) { w.fly = this.skyCd > 0 ? 0 : 1.8; w.charge = (w.charge || 0) + 0.6; }
    if (w[this.last]) w[this.last] *= 0.25;
    const e = Object.entries(w).filter(([, v]) => v > 0); let r = Math.random() * e.reduce((s, [, v]) => s + v, 0), m = e[0][0];
    for (const [k, v] of e) if ((r -= v) <= 0) { m = k; break; }
    this.last = m; this.begin(m);
  }
  begin(m) {
    this.facePlayer(); this.atk = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = false; this.fired2 = false; this.combo = [];
    if (m === 'walk') { this.state = 'walk'; this.want = 110; this.setA('walk', true); this.t = rand(0.5, 0.9); return; }
    if (m === 'walkback') { this.state = 'walk'; this.want = 160; this.setA('walk', true); this.t = 0.5; return; }
    if (m === 'combo') { const L = this.phase === 2 ? CM_COMBOS2 : CM_COMBOS1; return this.startCombo(L[Math.floor(Math.random() * L.length)].slice()); }
    if (m === 'sneak') { this.state = 'vanish'; this.batNext = 'bats'; this.setA('vanish', false, 1.2); this.batTo = this.blinkX(); cmBatSwarm(this.x, this.y, this.batTo, this.y, 26, 0.45); return; }
    if (m === 'charge') return this.startCharge();
    if (m === 'requiem') return this.startRequiem();
    if (m === 'grab') { this.grabCd = rand(7, 10); this.grabDmg = 0; this.state = 'attack'; this.tag = 'grab'; this.setA('grab'); return; }
    if (m === 'lances') { this.state = 'attack'; this.tag = 'cast'; this.setA('cast'); return; }
    if (m === 'fly') { this.state = 'takeoff'; this.setA('fly', true); this.hoverAlt = rand(36, 50); /* low enough that the camera, which follows you on the floor, keeps her in view */ this.airN = 1 + (Math.random() < 0.6 ? 1 : 0); this.didRain = false; this.didVolley = false; cmSfx.bats(); sfx.jump(); return; }
  }
  startCombo(list, speed = 1) {
    this.combo = list; this.comboSpeed = speed; this.chainN = 0;
    this.nextCut();
  }
  nextCut() {
    const tag = this.combo.shift();
    if (!tag) { this.state = 'idle'; this.setA('idle', true); this.cool = this.phase === 1 ? rand(0.8, 1.3) : rand(0.45, 0.85); return; }
    this.facePlayer(); this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = false;
    this.state = 'attack'; this.atk = 'cut'; this.tag = tag; this.setA(tag, false, (this.comboSpeed || 1) * (this.chainN++ ? 1.08 : 1));
  }
  blinkX() {
    let tx = clamp(P.x - P.face * 70, this.L + 10, this.R - 10);
    if (Math.abs(tx - P.x) < 50) tx = clamp(P.x + P.face * 90, this.L + 10, this.R - 10);
    return tx;
  }
  // ---------------------------------------------------------------- grounded cuts, lances, the grab (meta windows)
  updateAttack(dt) {
    const an = this.anim, sh = this.sh, tag = this.tag, wins = metaWindows(sh, tag);
    const first = wins.length ? wins[0].active[0] : 4;
    if (an.i < first) this.facePlayer();
    const tel = sh.meta && sh.meta.telegraph && sh.meta.telegraph[tag];
    if (tel && an.changed && an.i === tel.frame) { const p = metaPoint(sh, this, tel.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); }
    const d = Math.abs(P.x - this.x);
    // close the distance during the wind-up (she presses you), lunge a little into each cut
    if (this.atk === 'cut') {
      if (an.i < first && d > 70) this.x = clamp(this.x + this.face * 95 * dt, this.L, this.R);
      else if (an.i >= first && an.i <= (wins[0] ? wins[0].active[1] : first) && d > 30) this.x = clamp(this.x + this.face * (tag === 'thrust' ? 280 : 110) * dt, this.L, this.R);
      if (an.changed && an.i === first) sfx.bossSwing();
    }
    if (tag === 'grab') return this.updateGrab(dt, wins);
    wins.forEach((w, wi) => {
      if (an.i < w.active[0] || an.i > w.active[1] || this.hitIds.has(wi) || !w.hit) return;
      if (overlap(metaRect(sh, this, w.hit), playerHurtbox()) && hurtPlayer(this.dmg(tag), P.x < this.x ? -1 : 1, this.atkId * 10 + wi, { parryable: tag !== 'overhead', src: this })) this.hitIds.add(wi);
    });
    if (tag === 'overhead') {
      const sp = sh.meta && sh.meta.spawn && sh.meta.spawn.overhead;
      if (!this.fired && an.i >= (sp ? sp.frame : 6)) {
        this.fired = true; const at = sp ? metaPoint(sh, this, sp.at) : { x: this.x + this.face * 50 };
        const x = clamp(at.x, this.L - 20, this.R + 20);
        shake = 9; sfx.boom(); spawnFx('shockwave', x, this.floor, 1);
        for (const dd of [-1, 1]) cmWave(x + dd * 10, this.floor, dd, { dmg: CM_SG.shock, h: 14, v: 200, life: 1.5, src: this });
        for (let i = 0; i < 18; i++) particles.push({ x, y: this.floor - 2, vx: rand(-120, 120), vy: -rand(60, 200), g: 420, life: rand(0.4, 0.9), kind: i % 3 ? 'blood' : 'rock' });
        if (this.phase === 2) for (let k = 1; k <= 3; k++) this.later(k * 0.12, () => cmLance(clamp(x + this.face * k * 44, this.L - 16, this.R + 16), this.floor, { dmg: CM_SG.lance, boss: true, src: this, warn: 0.55 }));
      }
    }
    if (tag === 'cast') {
      const sp = sh.meta && sh.meta.spawn && sh.meta.spawn.cast;
      if (!this.fired && an.i >= (sp ? sp.frame : 4)) { this.fired = true; this.castLances(); }
      if (an.i >= 1 && an.i < (sp ? sp.frame : 4)) { const h = this.mpt('off', { x: this.x, y: this.y - 80 }); addLight(h.x, h.y, 24 + an.i * 6, '230,40,50', 0.9); }
    }
    if (an.done) {
      if (this.combo.length && !this.pendingPhase) return this.nextCut();
      this.state = 'idle'; this.setA('idle', true);
      this.cool = this.phase === 1 ? rand(0.8, 1.3) : rand(0.45, 0.85);
    }
  }
  castLances() {
    const p2 = this.phase === 2, pattern = Math.random() < 0.5 ? 'march' : 'track';
    if (pattern === 'march') {
      const dir = sign(P.x - this.x);
      for (let k = 0; k < (p2 ? 9 : 7); k++) { const x = this.x + dir * (50 + k * 40); if (x < this.L - 10 || x > this.R + 10) break; this.later(k * 0.1, () => cmLance(clamp(x, this.L - 16, this.R + 16), this.floor, { dmg: CM_SG.lance, boss: true, src: this, warn: 0.62 })); }
    } else {
      for (let k = 0; k < (p2 ? 4 : 3); k++) this.later(k * 0.4, () => { if (this.alive) cmLance(clamp(P.x + P.vx * 0.25, this.L - 16, this.R + 16), this.floor, { dmg: CM_SG.lance, boss: true, src: this, warn: 0.68 }); });
    }
    cmSfx.gurgle(); shake = Math.max(shake, 3);
  }
  // ---------------------------------------------------------------- blood charge: a flagged, straight dash; brakes into a rising cut
  startCharge() {
    const dir = sign(P.x - this.x), dist = clamp(Math.abs(P.x - this.x) + 100, 170, 360);
    this.chTo = clamp(this.x + dir * dist, this.L, this.R); this.face = dir;
    this.state = 'charge'; this.tag = 'charge'; this.setA('charge'); this.hitIds = new Set(); this.atkId = ++hazardId;
    CM.lines.push({ x0: this.x, y0: this.floor - 18, x1: this.chTo, y1: this.floor - 18, t: 0, warn: 0.5, life: 0.75, w: 3 });
    cmSfx.whip(); sfx.charge();
  }
  updateCharge(dt) {
    const an = this.anim;
    if (an.i < 2) { this.facePlayer(); this.face = sign(this.chTo - this.x) || this.face; return; }
    if (an.i >= 4 && an.t > an.ms() * 0.6) { an.i = 2; an.t = 0; }
    const v = (this.phase === 2 ? 620 : 560) * dt, dir = sign(this.chTo - this.x);
    this.x = Math.abs(this.chTo - this.x) <= v ? this.chTo : this.x + dir * v;
    if (Math.abs(this.x - (this.lastAfterX ?? -1e9)) > 30) { this.lastAfterX = this.x; this.after.push({ x: this.x, y: this.y, f: an.frame, face: this.face, t: 0.2 }); }
    if (Math.random() < 0.9) particles.push({ x: this.x - this.face * 20, y: this.floor - rand(2, 40), vx: -this.face * rand(30, 90), vy: -rand(0, 30), g: 100, life: 0.4, kind: 'blood' });
    const w = metaWindows(this.sh, 'charge')[0], hb = playerHurtbox();
    const r = w && w.hit ? metaRect(this.sh, this, w.hit) : rect(this.x, this.y - 50, this.x + this.face * 90, this.y);
    if (!this.hitIds.has(0) && (overlap(r, hb) || overlap(this.hurtbox() || r, hb)) && hurtPlayer(this.dmg('charge'), this.face, this.atkId, { src: this })) { this.hitIds.add(0); P.vx = this.face * 200; }
    if (this.x === this.chTo || this.x <= this.L || this.x >= this.R) { this.combo = []; this.tag = 'chargeend'; this.state = 'attack'; this.atk = 'cut'; this.atkId = ++hazardId; this.hitIds = new Set(); this.setA('chargeend'); this.facePlayer(); shake = Math.max(shake, 3); }
  }
  // ---------------------------------------------------------------- the drain grab
  updateGrab(dt, wins) {
    const an = this.anim, w = wins[0] || { active: [4, 5] };
    if (an.i <= 3) { const h = this.mpt('off', { x: this.x - this.face * 10, y: this.y - 80 }); addLight(h.x, h.y, 30, '255,40,40', 0.9); if (Math.random() < 0.6) particles.push({ x: h.x + rand(-4, 4), y: h.y + rand(-4, 4), vx: 0, vy: -rand(10, 30), life: 0.3, kind: 'blood' }); }
    if (an.i >= w.active[0] && an.i <= w.active[1]) {
      if (an.changed && an.i === w.active[0]) { sfx.bossSwing(); cmSfx.whip(); }
      this.x = clamp(this.x + this.face * 260 * dt, this.L, this.R);
      // a claw of living blood lashes from her hand down to your height
      const h = this.mpt('off', { x: this.x + this.face * 30, y: this.y - 80 }), tip = { x: h.x + this.face * 26, y: this.floor - 14 };
      this.claw = { h, tip, t: 0.12 };
      const r = rect(Math.min(h.x, tip.x + this.face * 10), tip.y - 24, Math.max(h.x, tip.x + this.face * 10), this.floor);
      if (!CM.held && P.state !== 'dead' && P.inv <= 0 && !iframes() && overlap(r, playerHurtbox())) return this.startDrain();
    }
    if (an.done) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.6; }
  }
  startDrain() {
    this.state = 'drain'; this.setA('drain', true); this.drT = 0; this.drained = 0; this.struggle = 0;
    CM.held = { b: this, prev: new Set(held) };
    hurtPlayer(this.dmg('bite'), this.face, ++hazardId, { src: this }); P.inv = 0;
    cmSfx.splash(1); shake = 5; hitstop = 0.12;
    if (!SAVE.hints.cm_drain) { SAVE.hints.cm_drain = 1; toast('She drinks! Mash attack / jump to break free.', 3); }
  }
  updateDrain(dt) {
    this.drT += dt;
    if (P.state === 'dead') { CM.held = null; this.state = 'idle'; this.setA('idle', true); this.cool = 1; return; }
    const d = Math.min(P.hp - 1, this.dmg('drain') * dt);
    if (d > 0) { P.hp -= d; this.drained += d; }
    const heal = Math.min(this.maxHp * 0.08 - this.drained * 0 - (this.healed || 0), d * 2.6);
    if (heal > 0) { this.hp = Math.min(this.maxHp, this.hp + heal); this.healed = (this.healed || 0) + heal; }
    const hand = this.mpt('off', { x: this.x + this.face * 30, y: this.y - 80 });
    if (Math.random() < 0.8) particles.push({ x: P.x + rand(-3, 3), y: P.y - rand(14, 22), vx: (hand.x - P.x) * 1.5, vy: (hand.y - 10 - P.y) * 1.2 - 30, life: 0.5, kind: 'blood' });
    addLight(P.x, P.y - 16, 40, '255,40,40', 0.8);
    if (this.struggle >= 6 || this.drT > 2.6) {
      const escaped = this.struggle >= 6;
      CM.held = null; setP('air', 'jump_fall', false); P.vx = -this.face * 170; P.vy = -170; P.inv = 0.7;
      if (escaped) { this.flinch('Broke free!'); } else { hurtPlayer(this.dmg('bite'), -this.face, ++hazardId, { src: this }); this.state = 'idle'; this.setA('idle', true); this.cool = 0.8; }
      this.healed = 0;
    }
  }
  holdPlayer() {   // called from the update hook (after the player's own update): she holds you up by the throat
    const H = CM.held; if (!H || H.b !== this) return;
    for (const a of ['attack', 'jump', 'roll', 'heavy', 'left', 'right']) { if (held.has(a) && !H.prev.has(a)) this.struggle++; }
    H.prev = new Set(held);
    const hand = this.mpt('off', { x: this.x + this.face * 30, y: this.y - 80 });
    P.x = hand.x + this.face * 3; P.y = Math.min(this.floor, hand.y + 26); P.vx = 0; P.vy = 0; P.ground = false;
    if (P.state !== 'hurt') setP('hurt', 'hurt'); P.anim.i = 0; P.anim.t = 0; P.face = -this.face;
    if (this.struggle > 0) { shake = Math.max(shake, 1); }
  }
  // ---------------------------------------------------------------- the Crimson Requiem: instant charges across the whole hall
  startRequiem() {
    this.reqCd = this.phase === 2 ? rand(9, 12) : rand(12, 15);
    const n = this.phase === 2 ? 6 : 4;
    this.req = { n, i: 0, t: 0.35, cur: null, warn: this.phase === 2 ? 0.46 : 0.56 };
    this.state = 'vanish'; this.batNext = 'requiem'; this.setA('vanish', false, 1.3);
    cmBatSwarm(this.x, this.y, room.pw / 2, this.floor - 60, 30, 0.6); cmSfx.chime();
    if (!SAVE.hints.cm_req) { SAVE.hints.cm_req = 1; toast('Watch the blood lines. Roll through the charge — or leap it.', 3.5); }
  }
  updateRequiem(dt) {
    const R = this.req; R.t -= dt;
    if (!R.cur && R.t <= 0) {
      if (R.i >= R.n) { this.hidden = false; this.x = clamp(P.x + (P.x < room.pw / 2 ? 110 : -110), this.L, this.R); this.alt = 0; this.facePlayer(); this.state = 'appear2'; this.setA('appear'); this.state = 'recover'; this.t = 1.1; return; }
      // pick a lane: horizontal along the floor (jump or roll), or (phase 2 / later cuts) a diagonal plunge at your spot
      const diag = (this.phase === 2 && R.i % 2 === 1) || (this.phase === 1 && R.i === R.n - 1);
      let c;
      if (!diag) {
        const fromL = R.i % 2 === 0 ? P.x > room.pw / 2 : P.x <= room.pw / 2;
        c = { diag: false, x0: fromL ? this.L : this.R, x1: fromL ? this.R : this.L, a0: 0, a1: 0 };
      } else {
        const fromL = P.x > room.pw / 2, tx = clamp(P.x + P.vx * 0.15, this.L + 10, this.R - 10);
        c = { diag: true, x0: fromL ? this.L : this.R, x1: tx, a0: this.maxAlt, a1: 0 };
      }
      c.t = 0; c.id = ++hazardId; c.warn = R.warn; c.dur = c.diag ? 0.2 : 0.17;
      CM.lines.push({ x0: c.x0, y0: this.floor - 18 - c.a0, x1: c.x1, y1: this.floor - 18 - c.a1, t: 0, warn: c.warn, life: c.warn + c.dur + 0.15, w: 4 });
      cmSfx.whip();
      R.cur = c; R.i++;
    }
    const c = R.cur; if (!c) return;
    c.t += dt;
    if (c.t < c.warn) { this.hidden = true; return; }
    const k = Math.min(1, (c.t - c.warn) / c.dur), px = this.x, pa = this.alt;
    this.hidden = false; this.face = sign(c.x1 - c.x0) || 1;
    if (this.anim.tag !== (c.diag && this.sh.has('dive') ? 'dive' : 'charge')) { this.setA(c.diag && this.sh.has('dive') ? 'dive' : 'charge'); this.anim.i = c.diag ? 4 : 2; sfx.bossSwing(); }
    this.x = lerp(c.x0, c.x1, k); this.alt = lerp(c.a0, c.a1, k); this.y = this.floor - this.alt;
    if (Math.abs(this.x - (this.lastAfterX ?? -1e9)) > 34) { this.lastAfterX = this.x; this.after.push({ x: this.x, y: this.floor - this.alt, f: this.anim.frame, face: this.face, t: 0.22 }); }
    // the swept body: a band along the path, low along the floor (clear it with a well-timed jump) or the plunge line
    const hb = playerHurtbox(), band = c.diag ? 14 : 0;
    const sw = c.diag ? rect(Math.min(px, this.x) - 14, this.floor - Math.max(pa, this.alt) - 20, Math.max(px, this.x) + 14, this.floor - Math.min(pa, this.alt) + 2)
                      : rect(Math.min(px, this.x) - 24, this.floor - 34, Math.max(px, this.x) + 24, this.floor);
    if (!this.hitIds.has(c.id) && overlap(sw, hb)) {
      let hitp = true;
      if (c.diag) { const t = clamp(((P.x - c.x0) * (c.x1 - c.x0)) / Math.max(1, (c.x1 - c.x0) ** 2), 0, 1), ly = this.floor - lerp(c.a0, c.a1, t), lx = lerp(c.x0, c.x1, t); hitp = Math.hypot(P.x - lx, (P.y - 13) - ly) < 22 + band; }
      if (hitp && hurtPlayer(this.dmg('req'), this.face, c.id, { src: this })) this.hitIds.add(c.id);
    }
    if (k >= 1) {
      shake = Math.max(shake, c.diag ? 6 : 3); cmSfx.splash(0.7);
      for (let i = 0; i < 12; i++) particles.push({ x: this.x, y: this.floor - this.alt - rand(0, 40), vx: -this.face * rand(40, 140), vy: -rand(20, 120), g: 380, life: rand(0.3, 0.7), kind: 'blood' });
      R.cur = null; R.t = this.phase === 2 ? 0.16 : 0.26; this.hidden = true;
    }
  }
  // ---------------------------------------------------------------- phase 2: the wings
  airMove() {
    if (!this.didVolley && Math.random() < 0.6) { this.didVolley = true; this.state = 'volley'; this.fired = false; this.setA('volley'); cmSfx.bats(); return; }
    if (this.airN > 0) { this.airN--; return this.startDive(); }
    if (!this.didRain && Math.random() < 0.5) { this.didRain = true; this.state = 'airrain'; this.t = 2.2; this.fired = false; this.fired2 = false; this.setA(this.sh.has('volley') ? 'volley' : 'fly'); return; }
    this.state = 'descend'; this.setA('fly', true);
  }
  startDive() {
    this.atkId = ++hazardId; this.hitIds = new Set();
    this.diveTo = clamp(P.x + P.vx * 0.2, this.L + 10, this.R - 10);
    this.state = 'diveprep'; this.t = 0.5; this.setA('dive'); this.anim.speed = 0.6;
    CM.lines.push({ x0: this.x, y0: this.y - 40, x1: this.diveTo, y1: this.floor - 8, t: 0, warn: 0.5, life: 0.7, w: 3 });
    spawnFx('telegraph', this.x + this.face * 20, this.y - 70, this.face); sfx.glint();
  }
  spikeVolley(at) {
    const base = Math.atan2(P.y - 14 - at.y, P.x - at.x), n = this.hp < this.maxHp * 0.25 ? 9 : 7;
    for (let k = 0; k < n; k++) { const a = base + (k - (n - 1) / 2) * 0.16; cmShot({ kind: 'spike', x: at.x, y: at.y, vx: Math.cos(a) * 250, vy: Math.sin(a) * 250, dmg: this.dmg('spike'), src: this, life: 2.2, r: 3 }); }
    cmSfx.lance(); shake = Math.max(shake, 3);
  }
  land(dived) {
    this.alt = 0; this.skyCd = rand(4, 7);
    shake = dived ? 9 : 3; sfx.boom(); cmSfx.splash(dived ? 1.2 : 0.6);
    if (dived) { for (const dd of [-1, 1]) cmWave(this.x + dd * 14, this.floor, dd, { dmg: CM_SG.shock, h: 13, v: 200, life: 1.5, src: this }); for (let i = 0; i < 26; i++) particles.push({ x: this.x + rand(-20, 20), y: this.floor - 2, vx: rand(-130, 130), vy: -rand(40, 180), g: 420, life: rand(0.4, 0.9), kind: i % 4 ? 'blood' : 'rock' }); }
    this.state = 'recover'; this.t = dived ? 0.8 : 0.25; this.setA(this.sh.has('land') ? 'land' : 'idle');
  }
  rainVolley(n) {
    for (let k = 0; k < n; k++) CM.drops.push({ x: clamp(k === 0 ? P.x : P.x + rand(-160, 160), this.L - 10, this.R + 10), t: -k * 0.06, warn: 0.85, fall: 0.22, id: ++hazardId, y: this.floor });
    cmSfx.gurgle();
  }
  director(dt) {   // phase 2: the broken hall keeps falling in, and the red sky rains blood
    if (!CM.col || CM.col.k < 1 || P.state === 'dead' || CM.held || this.state === 'requiem') return;
    this.dirT -= dt;
    if (this.dirT > 0) return;
    this.dirT = rand(2.8, 4.2) * (this.hp < this.maxHp * 0.25 ? 0.8 : 1);
    if (Math.random() < 0.55) for (let k = 0; k < (Math.random() < 0.5 ? 2 : 3); k++) cmDebris(clamp(k === 0 ? P.x : P.x + rand(-140, 140), this.L, this.R), this.floor, k * 0.25);
    else for (let k = 0; k < 4; k++) CM.drops.push({ x: clamp(k === 0 ? P.x : P.x + rand(-120, 120), this.L - 10, this.R + 10), t: -k * 0.12, warn: 0.9, fall: 0.22, id: ++hazardId, y: this.floor });
  }
  // ---------------------------------------------------------------- phase change: she tears the ballroom apart
  enterPhase2() {
    this.phase = 2; this.speed = 1.12; this.stance = 0; this.hidden = false; this.combo = [];
    this.state = 'transform'; this.tT = 0; this.facePlayer();
    CM.lances = []; CM.waves = []; CM.drops = []; CM.lines = [];
    if (this.sheets[1].ok) this.sh = this.sheets[1];
    this.setA(this.sh.has('transform') ? 'transform' : 'idle', !this.sh.has('transform'));
    cmCollapseBegin(this.x, this.y - 80);
    shake = 10; flashScreen = 0.5; sfx.roar(); cmSfx.rumble();
    bossPhase2Scene(this);
  }
  die() {
    this.state = 'dead'; this.hidden = false; this.combo = []; this.alt = Math.min(this.alt, 60);
    if (CM.held) { CM.held = null; setP('air', 'jump_fall', false); P.inv = 0.5; }
    this.setA(this.sh.has('death') ? 'death' : 'stagger'); this.anim.speed = 1;
    CM.lances = []; CM.waves = []; CM.drops = []; CM.shots = []; CM.lines = []; CM.debris = [];
    hazards = []; shake = 12; hitstop = 0.3; slowmo = 1.6; flashScreen = 0.6; sfx.roar(); sfx.felled();
    victoryBanner = { text: 'THE LAST DANCE ENDS', t: 0 };
    this.rewards();
  }
  stagger() {
    if (CM.held && CM.held.b === this) { CM.held = null; setP('air', 'jump_fall', false); P.inv = 0.5; }
    this.alt = 0; this.hidden = false; this.combo = []; super.stagger(); this.anim.set(this.sh.has('stagger') ? 'stagger' : 'idle', false, 1);
  }
  draw() {
    for (const a of this.after) if (this.sh.ok) drawSprite(this.sh, a.f, a.x, a.y, a.face, { alpha: 0.32 * Math.min(1, a.t / 0.22), flash: 0.85, flashColor: '#8a0c1c' });
    if (this.claw && (this.claw.t -= 1 / 60) > 0 || this.state === 'drain') {
      const h = this.mpt('off', { x: this.x + this.face * 30, y: this.y - 80 }), tip = this.state === 'drain' ? { x: P.x, y: P.y - 20 } : this.claw.tip;
      for (let k = 0; k <= 12; k++) { const t = k / 12, x = lerp(h.x, tip.x, t) + Math.sin(t * 7 + time * 30) * (1 - t) * 1.5, y = lerp(h.y, tip.y, t) + Math.sin(t * Math.PI) * 6;
        g.fillStyle = k > 9 ? '#ff8078' : '#b01426'; g.fillRect(Math.round(x), Math.round(y), 2, 2); }
      addLight(tip.x, tip.y, 26, '255,50,50', 0.7);
    }
    if (this.hidden || (this.state === 'dormant' && !this.sh.ok)) return;
    if (!this.sh.ok) { g.fillStyle = '#6a1020'; g.fillRect(Math.round(this.x - 16), Math.round(this.y - 106), 32, 106); return; }
    const pulse = this.state === 'attack' && this.tag === 'grab' && this.anim.i <= 3;
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' }
      : this.state === 'diveprep' || pulse || (this.state === 'charge' && this.anim.i < 2) ? { flash: 0.25 + 0.2 * Math.sin(time * 30), flashColor: '#ff3040' } : {};
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    if (this.alt > 6) { g.fillStyle = 'rgba(20,0,4,0.35)'; g.beginPath(); g.ellipse(Math.round(this.x), this.floor - 1, 18 + this.alt * 0.05, 2, 0, 0, 6.3); g.fill(); }
  }
}
BOSS_SPAWN.sanguine = (cx, fy) => new CmSanguine(cx, fy);
BOSS_CUTS.sanguine = b => [
  act(() => { b.anim.set('idle', true); b.face = 1; cmSfx.chime(); }),
  bossPan(b, 60, 1.6),
  say('', 'Beneath the chandeliers, a queen in black steel keeps the ball for no one.'),
  act(() => { b.face = P.x < b.x ? -1 : 1; holdAnim(b, 'bow'); }), wait(1.3),
  say('Countess Sanguine', 'A guest. How long it has been since anyone came to my ball uninvited.'),
  say('Countess Sanguine', 'Kneel, and I will drink you gently. Stand, and I will drink you anyway.'),
  act(() => { b.anim.set('idle', true); for (const c of CM.chands) c.red = 1; shake = 6; flashScreen = 0.3; cmSfx.gurgle(); for (let i = 0; i < 36; i++) particles.push({ x: b.x + rand(-30, 30), y: b.y - rand(0, 110), vx: rand(-20, 20), vy: -rand(20, 60), life: rand(0.8, 1.6), kind: 'blood' }); }), wait(1.1),
];
PHASE2_LINES.sanguine = ['Countess Sanguine', 'This house was a cage. Let it fall — and let the sky bleed with me.'];

// ================================================================== telegraph lines (charges, requiem, dives)
function cmUpdateLines(dt) { for (const l of CM.lines) l.t += dt; CM.lines = CM.lines.filter(l => l.t < l.life); }
function cmDrawLines() {
  for (const l of CM.lines) {
    const k = Math.min(1, l.t / l.warn), live = l.t >= l.warn, a = live ? Math.max(0, 1 - (l.t - l.warn) / (l.life - l.warn)) : 0.25 + 0.6 * k * (0.65 + 0.35 * Math.sin(time * 45));
    const n = Math.ceil(Math.hypot(l.x1 - l.x0, l.y1 - l.y0) / 2);
    for (let i = 0; i <= n; i++) {
      const t = i / n, x = Math.round(lerp(l.x0, l.x1, t)), y = Math.round(lerp(l.y0, l.y1, t));
      if (!live && (i + Math.floor(time * 30)) % 4 === 3) continue;
      g.fillStyle = live ? `rgba(255,120,110,${a})` : `rgba(200,20,40,${a * 0.8})`; g.fillRect(x, y - (live ? 1 : 0), 2, live ? 3 : 1);
      if (!live && k > 0.6) { g.fillStyle = `rgba(255,200,190,${(k - 0.6) * 1.5 * a})`; g.fillRect(x, y, 1, 1); }
    }
    if (!live) addLight(lerp(l.x0, l.x1, 0.5), lerp(l.y0, l.y1, 0.5), 60, '255,40,40', 0.3 + 0.4 * k);
  }
}

// ================================================================== the collapse: the ballroom breaks open to the red sky
function cmBallroomSetup() {
  CM.col = null;
  if (SAVE.flags['boss:sanguine']) { cmCollapseBegin(room.pw / 2, 100, true); }
}
function cmJag(x, base, amp, seed) {   // a broken masonry line: big irregular steps with a little chipping
  const u = x / 28, i = Math.floor(u), f = u - i, a = hash2(i, seed), b = hash2(i + 1, seed), k = f < 0.7 ? a : lerp(a, b, (f - 0.7) / 0.3);
  return base + Math.round((k - 0.5) * amp * 1.6 + (hash2(x >> 1, seed + 9) - 0.5) * 3);
}
function cmCollapseBegin(cx, cy, instant) {
  if (CM.col || !room || room.id !== 'CM7') return;
  const mk = () => { const c = document.createElement('canvas'); c.width = room.pw; c.height = room.ph; const x = c.getContext('2d'); x.imageSmoothingEnabled = false; return [c, x]; };
  const ob = CM.back0 || room.back, of = room.front;
  // the ruin: the back wall survives only below a broken line (the sky shows above); the vault and the upper side walls are gone
  const [ab, abx] = mk(), [af, afx] = mk();
  abx.drawImage(ob, 0, 0); afx.drawImage(of, 0, 0);
  for (let x = 0; x < room.pw; x += 2) {
    const yb = cmJag(x, 9 * TILE + 4, 26, 3), yf = x < 2 * TILE || x > room.pw - 2 * TILE ? cmJag(x, 7 * TILE, 20, 5) : 2 * TILE + 2;
    abx.clearRect(x, 0, 2, yb); afx.clearRect(x, 0, 2, yf);
  }
  abx.globalCompositeOperation = 'source-atop'; abx.fillStyle = 'rgba(40,0,8,0.35)'; abx.fillRect(0, 0, room.pw, room.ph);
  for (let x = 0; x < room.pw; x++) {   // a burning red lip along every broken edge
    const yb = cmJag(x & ~1, 9 * TILE + 4, 26, 3);
    abx.fillStyle = 'rgba(150,40,44,0.8)'; abx.fillRect(x, yb, 1, 1); abx.fillStyle = 'rgba(70,8,16,0.8)'; abx.fillRect(x, yb + 1, 1, 1);
  }
  abx.globalCompositeOperation = 'source-over';
  const [wb, wbx] = mk(), [wf, wfx] = mk();
  wbx.drawImage(ob, 0, 0); wfx.drawImage(of, 0, 0);
  const C = CM.col = { k: 0, t: 0, lt: time, ab, af, wb, wbx, wf, wfx, ob, of, pieces: [], blocks: [] };
  // every 32x32 block that loses pixels becomes a falling piece; they break away in a wave from where she stands
  for (const [src, alt, layer] of [[ob, ab, 'b'], [of, af, 'f']]) {
    const sc = src.getContext ? src.getContext('2d') : null;
    for (let by = 0; by < 11 * TILE; by += 32) for (let bx = 0; bx < room.pw; bx += 32) {
      if (layer === 'f' && by > 9 * TILE) continue;
      const c = document.createElement('canvas'); c.width = 32; c.height = 32; const x = c.getContext('2d');
      x.drawImage(src, bx, by, 32, 32, 0, 0, 32, 32); x.globalCompositeOperation = 'destination-out'; x.drawImage(alt, bx, by, 32, 32, 0, 0, 32, 32);
      let any = false; try { const d = x.getImageData(0, 0, 32, 32).data; for (let i = 3; i < d.length; i += 16) if (d[i] > 0) { any = true; break; } } catch (e) { any = true; }
      // an irregular broken chunk rather than a square block
      x.globalCompositeOperation = 'destination-in'; x.beginPath();
      for (let k = 0; k < 7; k++) { const a = k / 7 * Math.PI * 2, r = 11 + hash2(bx + k, by) * 7; k ? x.lineTo(16 + Math.cos(a) * r, 16 + Math.sin(a) * r) : x.moveTo(16 + Math.cos(a) * r, 16 + Math.sin(a) * r); }
      x.closePath(); x.fill(); x.globalCompositeOperation = 'source-over';
      if (!any) continue;
      const dist = Math.hypot(bx + 16 - cx, by + 16 - cy);
      C.blocks.push({ layer, bx, by, img: c, delay: instant ? 0 : 0.15 + dist / 520 + hash2(bx, by) * 0.25, done: false });
    }
  }
  for (const ch of CM.chands) ch.fallAt = instant ? -1 : 0.4 + Math.abs(ch.px - cx) / 520;
  if (instant) { C.t = 99; cmCollapseAdvance(); }
}
function cmCollapseAdvance() {   // real time, so the hall keeps falling during the phase-2 scene
  const C = CM.col; if (!C) return;
  const dt = clamp(time - C.lt, 0, 0.1); C.lt = time; C.t += dt;
  let changed = false;
  for (const b of C.blocks) {
    if (b.done || C.t < b.delay) continue;
    b.done = true; changed = true;
    const [wx, alt] = b.layer === 'b' ? [C.wbx, C.ab] : [C.wfx, C.af];
    wx.clearRect(b.bx, b.by, 32, 32); wx.drawImage(alt, b.bx, b.by, 32, 32, b.bx, b.by, 32, 32);
    if (C.t < 50) C.pieces.push({ img: b.img, x: b.bx + 16, y: b.by + 16, vx: rand(-30, 30), vy: rand(-20, 30), r: 0, vr: rand(-3, 3), front: b.layer === 'f' });
  }
  if (changed) { room.back = C.wb; room.front = C.wf; }
  C.k = C.blocks.every(b => b.done) ? 1 : 0.5;
  const fl = 15 * TILE;
  for (const p of C.pieces) {
    p.vy += 620 * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.r += p.vr * dt;
    if (p.y > fl - 10 && !p.broke) {
      p.broke = true; shake = Math.max(shake, 3); if (Math.random() < 0.3) sfx.crumble();
      for (let i = 0; i < 8; i++) particles.push({ x: p.x + rand(-10, 10), y: fl - 2, vx: rand(-90, 90), vy: -rand(40, 160), g: 420, life: rand(0.4, 0.9), kind: i % 2 ? 'rock' : 'dust' });
    }
  }
  C.pieces = C.pieces.filter(p => !p.broke);
  for (const ch of CM.chands) if (ch.fallAt !== undefined && C.t > ch.fallAt && !ch.gone) {
    if (!ch.fall) ch.fall = { y: 0, vy: 0 };
    if (ch.fallAt < 0) { ch.gone = true; continue; }
    ch.fall.vy += 620 * dt; ch.fall.y += ch.fall.vy * dt;
    if (ch.py + ch.len + ch.fall.y > fl - 30) { ch.gone = true; shake = Math.max(shake, 6); sfx.crumble(); cmSfx.chime(); for (let i = 0; i < 20; i++) particles.push({ x: ch.px + rand(-20, 20), y: fl - 4, vx: rand(-120, 120), vy: -rand(40, 180), g: 420, life: rand(0.4, 1), kind: i % 3 ? 'spark' : 'fire' }); }
  }
}
function cmDrawCollapse() {
  const C = CM.col; if (!C) return;
  cmCollapseAdvance();
  for (const p of C.pieces) { g.save(); g.translate(Math.round(p.x), Math.round(p.y)); g.rotate(p.r); g.drawImage(p.img, -16, -16); g.restore(); }
}
// falling masonry from the broken walls (phase 2 director)
function cmDebris(x, fl, delay = 0) { CM.debris.push({ x, fl, t: -delay, warn: 0.9, fall: 0.3, id: ++hazardId, seed: Math.floor(rand(0, 99)) }); }
function cmUpdateDebris(dt) {
  for (const d of CM.debris) {
    d.t += dt;
    if (d.t >= d.warn + d.fall && !d.hit) {
      d.hit = true; shake = Math.max(shake, 4); sfx.crumble();
      for (let i = 0; i < 10; i++) particles.push({ x: d.x + rand(-8, 8), y: d.fl - 3, vx: rand(-100, 100), vy: -rand(40, 150), g: 420, life: rand(0.4, 0.8), kind: i % 2 ? 'rock' : 'dust' });
      if (overlap(rect(d.x - 13, d.fl - 30, d.x + 13, d.fl), playerHurtbox())) hurtPlayer(BOSS_DMG * CM_SG.debris * NGP.dmg, sign(P.x - d.x), d.id, { src: boss });
    }
  }
  CM.debris = CM.debris.filter(d => d.t < d.warn + d.fall + 0.1);
}
function cmDrawDebris() {
  const ts = tileSheet('crimson');
  for (const d of CM.debris) {
    if (d.t < 0) continue;
    if (d.t < d.warn) {
      const k = d.t / d.warn;
      g.fillStyle = `rgba(10,4,8,${0.25 + 0.5 * k})`; g.beginPath(); g.ellipse(Math.round(d.x), d.fl - 1, 5 + 9 * k, 2, 0, 0, 6.3); g.fill();
      if (Math.random() < 0.4) particles.push({ x: d.x + rand(-8, 8), y: cam.y + rand(0, 20), vx: 0, vy: rand(40, 90), g: 200, life: 0.8, kind: 'dust' });
    } else {
      const k = Math.min(1, (d.t - d.warn) / d.fall), y = lerp(cam.y - 30, d.fl - 12, k * k);
      g.save(); g.translate(Math.round(d.x), Math.round(y)); g.rotate(k * 2 + d.seed);
      drawTile(g, ts, d.seed % 2 ? 1 : 17, -12, -12); drawTile(g, ts, 3, -4, -6);
      g.restore();
    }
  }
}
function cmBallroomUpdate(dt) {
  cmUpdateLines(dt); cmUpdateDebris(dt);
  if (CM.held && boss && boss.holdPlayer) boss.holdPlayer();
  for (const d of CM.drops) {
    d.t += dt;
    if (d.t >= d.warn + d.fall && !d.hit) {
      d.hit = true; cmSfx.splash(0.4); shake = Math.max(shake, 1.5);
      for (let i = 0; i < 6; i++) particles.push({ x: d.x, y: d.y - 2, vx: rand(-60, 60), vy: -rand(30, 100), g: 400, life: 0.4, kind: 'blood' });
      if (overlap(rect(d.x - 7, d.y - 26, d.x + 7, d.y), playerHurtbox())) hurtPlayer(BOSS_DMG * CM_SG.drop * NGP.dmg, sign(P.x - d.x), d.id, { src: boss });
    }
  }
  CM.drops = CM.drops.filter(d => d.t < d.warn + d.fall + 0.1);
  if (CM.col && CM.col.k > 0) addLight(cam.x + W / 2, cam.y - 20, 260, '200,50,50', 0.55);
}
function cmBallroomDraw() {
  cmDrawCollapse(); cmDrawDebris(); cmDrawLines();
  const fl = 15 * TILE;
  for (const d of CM.drops) {
    if (d.t < 0) continue;
    if (d.t < d.warn) {
      const k = d.t / d.warn;
      g.fillStyle = `rgba(200,30,40,${0.3 + 0.5 * k})`; g.beginPath(); g.ellipse(Math.round(d.x), fl - 2, 3 + 6 * k, 1.5, 0, 0, 6.3); g.fill();
      g.fillStyle = `rgba(230,60,70,${0.12 + 0.2 * k})`; g.fillRect(Math.round(d.x), Math.round(cam.y), 1, Math.round(fl - cam.y));
    } else {
      const k = (d.t - d.warn) / d.fall, y = lerp(cam.y - 10, fl, k * k);
      g.fillStyle = '#e0303c'; g.fillRect(Math.round(d.x) - 1, Math.round(y) - 8, 3, 8); g.fillStyle = '#ffb0a8'; g.fillRect(Math.round(d.x), Math.round(y) - 2, 1, 2);
    }
  }
  // held in her grip: the struggle meter
  if (CM.held) { const n = Math.min(6, boss && boss.struggle || 0); for (let i = 0; i < 6; i++) { g.fillStyle = i < n ? '#ffd070' : 'rgba(80,20,20,0.8)'; g.fillRect(Math.round(P.x) - 10 + i * 3, Math.round(P.y) - 36, 2, 2); } }
}

// ================================================================== debug handle (automated tests)
try { window.__cm = { CM, CMM, force(m) { if (boss && boss.begin) { boss.cool = 99; boss.begin(m); } else if (boss && boss.start) { boss.cool = 99; boss.start(m); } } }; } catch (e) {}
