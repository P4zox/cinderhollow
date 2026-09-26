// ------------------------------------------------------------------ THE CRIMSON MANOR (agent C)
// A vampiric noble estate past Kalden's Vigil (biome `crimson`): blood rain on black stone, candlelit halls, portraits whose
// eyes follow you, crypt-cellars of wine and blood. Gate: a blood veil (the ash-veil '%' mechanic, re-skinned) — Ember Dash.
// Hazards: blood pools (sap HP/FP, slow), crimson downpours in the Court (shelter under balconies), swinging chandeliers,
// portrait ambushes. Enemies: cm_servant, cm_hound, cm_gargoyle. Mini-boss: the Butler (CM6). Boss: Countess Sanguine (CM7;
// phase 2 floods the ballroom with a sea of blood). Every top-level name is prefixed cm/CM (all region files share one scope).
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
    rain: null, streaks: [], poolT: 0, rainHint: false, veilHint: false, flood: null, back0: null });
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
    const e = cmChandPos(ch), n = Math.max(1, Math.floor(ch.len / 4));
    for (let i = 0; i <= n; i++) { const t = i / n, x = lerp(ch.px, e.x, t), y = lerp(ch.py, e.y, t); g.fillStyle = i % 2 ? '#1a1418' : '#4a3e44'; g.fillRect(Math.round(x), Math.round(y), 1, 2); }
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
  if (room.id === 'CM7' && CM.flood && CM.flood.k > 0) { g.fillStyle = `rgba(40,0,8,${0.04 * CM.flood.k})`; g.fillRect(0, 0, W, H); }
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

// ================================================================== COUNTESS SANGUINE (CM7) — rapier, blood whip, bats, lances, doubles
// Phase 2 (50%): her gown becomes a torrent of blood, blood wings; the ballroom floods (sea of blood, tides), aerial dives + rain.
BOSS_INFO.sanguine = { name: 'Countess Sanguine', hp: 3200, cinders: 16000, reward: ['w:sanguine_rapier', 'sp:crimson_rite', 'c_countess'],
  quote: '“Every guest leaves something behind. Most leave everything.”' };
const CM_SG = { flurry: 24, lunge: 40, whip: 34, lance: 30, dbl: 28, dive: 46, drop: 22, splash: 22, tide: 26 };
class CmSanguine extends BossBase {
  constructor(x, y) {
    super('sanguine', x, y);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.sanguine.hp * NGP.hp);
    const meta = ASSETS.sanguine_meta;
    this.sheets = [sheet('sanguine', { meta }), sheet('sanguine_p2', { meta })];
    this.sh = this.sheets[0]; this.anim = new Anim(this.sh, 'idle'); this.state = 'dormant'; this.face = -1;
    this.stanceMax = 300; this.critRange = 72; this.alt = 0; this.cool = 1; this.q = []; this.dbl = []; this.hidden = false; this.last = null; this.airN = 0; this.skyCd = 0;
    this.whip = null; this.tideT = 6;
  }
  get L() { return 2 * TILE + 26; }
  get R() { return room.pw - TILE - 26; }
  get maxAlt() { return this.floor - (2 * TILE + 100); }
  fm(tag = this.anim.tag, i = this.anim.i) { const m = this.sh.meta, f = m && m.frames && m.frames[tag]; return f ? f[Math.min(i, f.length - 1)] : null; }
  mpt(key, fb) { const f = this.fm(); return f && f[key] ? metaPoint(this.sh, this, f[key]) : fb; }
  hurtbox() {
    if (!this.alive || this.hidden || this.state === 'dormant' && !this.active) return null;
    const f = this.fm(); if (f && f.hb) return metaRect(this.sh, this, f.hb);
    return rect(this.x - 12, this.y - 84, this.x + 12, this.y);
  }
  hit(info) { if (this.hidden) return; super.hit(info); }
  canStagger() { return !this.hidden && this.alt < 4 && ['idle', 'walk', 'attack', 'recover'].includes(this.state) && this.atk !== 'transform'; }
  setA(tag, loop = false, speed = 1) { this.anim.set(this.sh.has(tag) ? tag : 'idle', loop, speed * (this.phase === 2 ? 1.12 : 1)); }
  later(t, fn) { this.q.push({ t, fn }); }
  wakeCheck() { return P.x > 3 * TILE + 8 && P.x < this.R && P.state !== 'dead'; }
  activate() { if (this.active || this.cutting) return; super.activate(); }
  update(dt) {
    this.commonUpdate(dt);
    const an = this.anim; an.update(dt);
    if (!this.active) { if (!this.cutting && this.wakeCheck()) this.activate(); if (!this.cutting) this.facePlayer(); return; }
    if (this.introT > 0) { this.introT -= dt; if (this.introT <= 0) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.6; } }
    if (this.alive) { for (const e of this.q) { e.t -= dt; if (e.t <= 0 && !e.done) { e.done = true; e.fn(); } } this.q = this.q.filter(e => !e.done); }
    this.skyCd -= dt;
    switch (this.state) {
      case 'idle': {
        this.cool -= dt;
        if (an.tag !== 'idle' && an.tag !== 'fly') this.setA(this.alt > 4 ? 'fly' : 'idle', true);
        if (P.state === 'dead') break;
        this.facePlayer();
        if (this.cool <= 0) this.choose();
        break;
      }
      case 'walk': {
        this.t -= dt; this.cool -= dt; this.facePlayer();
        const d = Math.abs(P.x - this.x), dir = d > this.want ? this.face : -this.face;
        this.x = clamp(this.x + dir * 64 * this.speed * dt, this.L, this.R);
        if (this.t <= 0 || Math.abs(d - this.want) < 14) { this.state = 'idle'; this.cool = Math.min(this.cool, 0.15); }
        break;
      }
      case 'attack': this.updateAttack(dt); break;
      case 'vanish':
        if (an.done || !this.sh.has('vanish')) { this.hidden = true; this.state = 'bats'; this.t = 0.42; }
        break;
      case 'bats':
        this.t -= dt;
        if (this.t <= 0) { this.x = this.batTo; this.hidden = false; this.facePlayer(); this.state = 'appear'; this.setA('appear'); }
        break;
      case 'appear':
        if (an.done || !this.sh.has('appear')) { const d = Math.abs(P.x - this.x); this.begin(d < 80 ? 'flurry' : this.phase === 2 && Math.random() < 0.4 ? 'whip' : 'lunge', true); }
        break;
      case 'takeoff':
        this.alt = approach(this.alt, this.hoverAlt, 220 * dt); this.facePlayer();
        if (this.alt >= this.hoverAlt - 1) { this.state = 'hover'; this.t = rand(0.5, 0.8); }
        break;
      case 'hover': {
        this.t -= dt; this.facePlayer();
        const tx = clamp(P.x - this.face * 70, this.L + 20, this.R - 20);
        this.x = approach(this.x, tx, 110 * dt); this.alt = approach(this.alt, this.hoverAlt + Math.sin(time * 3) * 4, 60 * dt);
        if (this.t <= 0) this.airMove();
        break;
      }
      case 'diveprep':
        this.t -= dt; this.face = this.diveTo.x < this.x ? -1 : 1;
        if (this.t <= 0) { this.state = 'dive'; this.diveV = null; sfx.bossSwing(); }
        break;
      case 'dive': {
        if (!this.diveV) { const dx = this.diveTo.x - this.x, dy = this.alt, d = Math.hypot(dx, dy) || 1; this.diveV = { x: dx / d * 430, y: dy / d * 430 }; }
        this.x = clamp(this.x + this.diveV.x * dt, this.L, this.R); this.alt = Math.max(0, this.alt - this.diveV.y * dt);
        const f = this.fm(), r = f && f.hit ? metaRect(this.sh, this, f.hit) : rect(this.x - 22, this.y - 70, this.x + 22, this.y);
        if (!this.hitIds.has(0) && overlap(r, playerHurtbox()) && hurtPlayer(BOSS_DMG * CM_SG.dive * NGP.dmg, this.face, this.atkId, { src: this })) this.hitIds.add(0);
        if (this.alt <= 0 || (this.x <= this.L + 0.5 && this.diveV.x < 0) || (this.x >= this.R - 0.5 && this.diveV.x > 0)) this.land(true);
        break;
      }
      case 'recover':
        this.t -= dt;
        if (this.t <= 0 && (an.done || an.loop)) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.25; }
        break;
      case 'descend':
        this.alt = Math.max(0, this.alt - 160 * dt);
        if (this.alt <= 0) this.land(false);
        break;
      case 'fall':
        this.alt = Math.max(0, this.alt - 260 * dt);
        if (this.alt <= 0) { shake = 6; sfx.boom(); cmSfx.splash(); this.state = 'idle'; this.stagger(); }
        break;
      case 'transform': this.updateTransform(dt); break;
      case 'stagger':
        this.t -= dt;
        if (an.i === an.n - 1 && this.t > 0.3) an.hold();
        if (an.done || this.t <= 0) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.35; }
        break;
      case 'dead':
        this.alt = Math.max(0, this.alt - 200 * dt);
        if (Math.random() < 0.6) particles.push({ x: this.x + rand(-30, 30), y: this.y - rand(0, 80), vx: rand(-10, 10), vy: -rand(10, 40), life: rand(0.8, 1.6), kind: 'blood' });
        if (an.done) an.hold();
        break;
    }
    this.updateDoubles(dt);
    if (this.whip && this.state !== 'attack') this.whip = null;
    if (this.alive && this.phase === 1 && this.hp <= this.maxHp * 0.5) this.pendingPhase = true;
    if (this.pendingPhase && this.alive && ['idle', 'walk', 'recover'].includes(this.state) && this.alt <= 0 && !this.dbl.length) { this.pendingPhase = false; this.enterPhase2(); }
    if (this.phase === 2 && this.alive) this.tideDirector(dt);
    this.x = clamp(this.x, this.L, this.R);
    this.alt = clamp(this.alt, 0, this.maxAlt);
    this.y = this.floor - this.alt;
    this.camX = this.x;
    if (this.alive && this.active && !this.hidden) addLight(this.x, this.y - 60, 60, '230,60,70', 0.45);
  }
  // ---------------------------------------------------------------- choice
  choose() {
    if (this.pendingPhase) return;
    const d = Math.abs(P.x - this.x), p2 = this.phase === 2;
    let w;
    if (d < 62) w = { flurry: 3, whip: 1.2, batport: 0.8, walkback: 0.6 };
    else if (d < 170) w = { lunge: 2.4, whip: 2.2, lances: 1.0, batport: 1.0, walk: 0.5 };
    else w = { lunge: 1.6, lances: 2.0, batport: 1.4, walk: 1.2 };
    if (this.hp < this.maxHp * 0.8 || p2) w.dance = this.danceCd > time ? 0 : 1.2;
    if (p2) { w.fly = this.skyCd > 0 ? 0 : 2.2; w.lances = (w.lances || 0) + 0.6; }
    if (w[this.last]) w[this.last] *= 0.25;
    const e = Object.entries(w).filter(([, v]) => v > 0); let r = Math.random() * e.reduce((s, [, v]) => s + v, 0), m = e[0][0];
    for (const [k, v] of e) if ((r -= v) <= 0) { m = k; break; }
    this.last = m; this.begin(m);
  }
  begin(m, chained) {
    this.facePlayer(); this.atk = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {}; this.lungeV = 0; this.whip = null;
    if (m === 'walk') { this.state = 'walk'; this.want = 90; this.setA('walk', true); this.t = rand(0.6, 1.0); return; }
    if (m === 'walkback') { this.state = 'walk'; this.want = 150; this.setA('walk', true); this.t = 0.6; return; }
    if (m === 'batport') { this.state = 'vanish'; this.setA('vanish'); this.batTo = this.blinkX(); cmBatSwarm(this.x, this.y, this.batTo, this.y, 22, 0.5); return; }
    if (m === 'fly') { this.state = 'takeoff'; this.setA('fly', true); this.hoverAlt = rand(78, 96); this.airN = Math.random() < 0.5 ? 2 : 1; cmSfx.bats(); sfx.jump(); return; }
    if (m === 'dance') { this.danceCd = time + 9; }
    const tag = { flurry: 'flurry', lunge: 'lunge', whip: 'whip', lances: 'cast', dance: 'dance' }[m] || m;
    this.state = 'attack'; this.tag = tag; this.setA(tag);
    if (chained) this.anim.speed *= 1.15;
  }
  blinkX() {
    let tx = clamp(P.x - P.face * 64, this.L + 10, this.R - 10);
    if (Math.abs(tx - P.x) < 44) tx = clamp(P.x + P.face * 80, this.L + 10, this.R - 10);
    return tx;
  }
  // ---------------------------------------------------------------- grounded attacks (meta windows)
  updateAttack(dt) {
    const an = this.anim, sh = this.sh, m = this.atk, tag = this.tag, wins = metaWindows(sh, tag);
    const first = wins.length ? wins[0].active[0] : 4;
    if (an.i < first - 1 && m !== 'lunge') this.facePlayer();
    if (m === 'lunge' && an.i < first - 1) this.facePlayer();
    const tel = sh.meta && sh.meta.telegraph && sh.meta.telegraph[tag];
    if (tel && an.changed && an.i === tel.frame) { const p = metaPoint(sh, this, tel.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); }
    else if (!tel && an.changed && an.i === Math.max(0, first - 2) && ['flurry', 'lunge', 'whip'].includes(m)) { spawnFx('telegraph', this.x + this.face * 18, this.y - 62, this.face); sfx.glint(); }
    // the lunge: a straight dash during the active frames, fixed direction, clamped to the arena
    if (m === 'lunge') {
      if (an.changed && an.i === first) { this.lungeV = this.face * (this.phase === 2 ? 420 : 380); sfx.bossSwing(); }
      if (this.lungeV && an.i <= (wins[0] ? wins[0].active[1] : first + 2)) {
        const nx = clamp(this.x + this.lungeV * dt, this.L, this.R);
        if ((this.x - P.x) * this.face > 60) this.lungeV *= Math.pow(0.001, dt);   // already well past you: brake
        this.x = nx;
        if (Math.random() < 0.8) particles.push({ x: this.x - this.face * 16, y: this.y - rand(4, 50), vx: -this.face * rand(20, 60), vy: rand(-10, 10), life: 0.35, kind: 'blood' });
      }
    }
    if (m !== 'whip') wins.forEach((w, wi) => {
      if (an.i < w.active[0] || an.i > w.active[1] || this.hitIds.has(wi) || !w.hit) return;
      if (an.changed && an.i === w.active[0] && m === 'flurry') { sfx.swing(); const q = metaRect(sh, this, w.hit); spawnFx(fxOr('cm_thrust', 'hit'), (q.x0 + q.x1) / 2, (q.y0 + q.y1) / 2, this.face); }
      const r = metaRect(sh, this, w.hit);
      if (overlap(r, playerHurtbox())) {
        const dmg = (m === 'flurry' ? CM_SG.flurry : m === 'lunge' ? CM_SG.lunge : 30) * (this.phase === 2 ? 1.1 : 1) * NGP.dmg;
        if (hurtPlayer(BOSS_DMG * dmg, P.x < this.x ? -1 : 1, this.atkId * 10 + wi, { parryable: m !== 'dance', src: this })) this.hitIds.add(wi);
      }
    });
    if (m === 'whip') this.updateWhip(dt, wins);
    if (m === 'lances') {
      const sp = sh.meta && sh.meta.spawn && sh.meta.spawn.cast;
      if (!this.fired.cast && an.i >= (sp ? sp.frame : 6)) { this.fired.cast = true; this.castLances(); }
      if (an.i >= 3 && an.i <= (sp ? sp.frame : 6)) { const h = this.mpt('off', { x: this.x - this.face * 8, y: this.y - 60 }); addLight(h.x, h.y, 24 + an.i * 4, '230,40,50', 0.9); if (Math.random() < 0.6) particles.push({ x: h.x + rand(-6, 6), y: h.y + rand(-6, 6), vx: 0, vy: rand(-20, 20), life: 0.3, kind: 'blood' }); }
    }
    if (m === 'dance') {
      const sp = sh.meta && sh.meta.spawn && sh.meta.spawn.dance;
      if (!this.fired.dance && an.i >= (sp ? sp.frame : 5)) { this.fired.dance = true; this.summonDoubles(); }
    }
    if (an.done) {
      this.whip = null;
      if (m === 'dance') { this.state = 'idle'; this.cool = 2.2; this.setA('idle', true); return; }
      if (this.pendingPhase) { this.state = 'idle'; this.cool = 0; this.setA('idle', true); return; }
      const d = Math.abs(P.x - this.x);
      if (this.chain < (this.phase === 2 ? 2 : 1) && Math.random() < (this.phase === 2 ? 0.55 : 0.3)) {
        const nx = m === 'flurry' ? (d < 90 ? 'whip' : 'lunge') : m === 'lunge' ? (d < 80 ? 'flurry' : 'whip') : m === 'whip' ? (d > 110 ? 'lunge' : 'flurry') : null;
        if (nx) { this.chain++; return this.begin(nx, true); }
      }
      this.chain = 0; this.state = 'idle'; this.setA('idle', true);
      this.cool = this.phase === 1 ? rand(0.9, 1.4) : rand(0.55, 0.95);
    }
  }
  // blood whip: code-drawn lash from her hand, its reach growing over the swing; hits along the whole length
  updateWhip(dt, wins) {
    const an = this.anim, w = wins[0] || { active: [6, 8] }, hand = this.mpt('hand', { x: this.x + this.face * 14, y: this.y - 56 });
    const n = an.n, i = an.i + an.t / Math.max(1, an.ms());
    let reach = 0, lift = 0;
    if (i < w.active[0]) { reach = 26 + 6 * i; lift = -28 - 4 * i; }                         // raised, coiling behind her
    else if (i <= w.active[1] + 1) { const k = clamp((i - w.active[0]) / (w.active[1] + 1 - w.active[0]), 0, 1); reach = lerp(40, this.phase === 2 ? 150 : 132, Math.sqrt(k)); lift = lerp(-30, 44, k); }
    else { const k = clamp((i - w.active[1] - 1) / Math.max(1, n - w.active[1] - 1), 0, 1); reach = lerp(this.phase === 2 ? 150 : 132, 30, k); lift = lerp(44, 30, k); }
    if (an.changed && an.i === w.active[0]) cmSfx.whip();
    const pts = [], tipX = hand.x + this.face * reach, tipY = Math.min(this.floor - 3, hand.y + lift);
    const lash = i >= w.active[0] && i <= w.active[1] + 1.4;
    const c1x = hand.x + this.face * reach * 0.4, c1y = lash ? hand.y + 4 : hand.y - 18 - (i < w.active[0] ? 18 : 0);
    for (let k = 0; k <= 16; k++) { const t = k / 16, a = (1 - t) * (1 - t), b = 2 * (1 - t) * t, c = t * t; pts.push([a * hand.x + b * c1x + c * tipX, a * hand.y + b * c1y + c * tipY + Math.sin(t * 9 + time * 30) * (1 - t) * 1.2]); }
    this.whip = { pts, hot: lash };
    if (this.whip.hot && !this.hitIds.has(0)) {
      const hb = playerHurtbox();
      for (const [x, y] of pts.slice(4)) if (overlap(rect(x - 4, y - 4, x + 4, y + 4), hb)) { if (hurtPlayer(BOSS_DMG * CM_SG.whip * (this.phase === 2 ? 1.1 : 1) * NGP.dmg, this.face, this.atkId * 10, { src: this })) this.hitIds.add(0); break; }
    }
  }
  castLances() {
    const p2 = this.phase === 2, n = p2 ? 6 : 5, pattern = Math.random() < 0.5 ? 'march' : 'track';
    if (pattern === 'march') {   // a line of spikes marching from her toward you, and past you
      const dir = sign(P.x - this.x);
      for (let k = 0; k < n + 2; k++) { const x = this.x + dir * (44 + k * 38); if (x < this.L - 10 || x > this.R + 10) break; this.later(k * 0.11, () => cmLance(clamp(x, this.L - 16, this.R + 16), this.floor, { dmg: CM_SG.lance, boss: true, src: this, warn: 0.7 })); }
    } else {                     // three (four) that hunt you, a beat apart
      for (let k = 0; k < (p2 ? 4 : 3); k++) this.later(k * 0.42, () => { if (!this.alive) return; cmLance(clamp(P.x + P.vx * 0.25, this.L - 16, this.R + 16), this.floor, { dmg: CM_SG.lance, boss: true, src: this, warn: 0.72 }); });
    }
    cmSfx.gurgle(); shake = Math.max(shake, 2);
  }
  // ---------------------------------------------------------------- the dance: blood doubles strike from both sides, then she does
  summonDoubles() {
    const n = this.phase === 2 ? 3 : 2, sides = n === 3 ? [-1, 1, -1] : [-1, 1];
    sides.forEach((s, k) => {
      const x = clamp(P.x + s * (120 + k * 14), this.L, this.R);
      if (Math.abs(x - P.x) < 50) return;
      const sh = this.sh, an = new Anim(sh, sh.has('lunge') ? 'lunge' : 'idle', false); an.speed = 0; an.i = 0;
      this.dbl.push({ x, y: this.floor, face: P.x < x ? -1 : 1, an, delay: 0.7 + k * 0.42, t: 0, id: ++hazardId, hit: false, a: 0, v: 0 });
      cmBatSwarm(this.x, this.y, x, this.floor, 6, 0.4);
    });
    this.later(0.7 + n * 0.42 + 0.15, () => { if (this.alive && this.state === 'idle') { this.cool = 0; this.begin('lunge', true); } });
    cmSfx.chime(); shake = Math.max(shake, 3);
  }
  updateDoubles(dt) {
    for (const d of this.dbl) {
      d.t += dt; d.a = Math.min(1, d.a + dt * 3);
      if (d.t < d.delay) { d.face = P.x < d.x ? -1 : 1; if (d.t > d.delay - 0.35 && !d.warned) { d.warned = true; sfx.glint(); spawnFx('telegraph', d.x + d.face * 18, d.y - 62, d.face); } continue; }
      if (d.an.speed === 0) { d.an.speed = 1.1; d.an.i = 0; d.an.t = 0; }
      d.an.update(dt);
      const wins = metaWindows(this.sh, 'lunge'), w = wins[0] || { active: [5, 7], hit: null };
      if (d.an.i >= w.active[0] && d.an.i <= w.active[1]) {
        if (!d.v) { d.v = d.face * 400; sfx.bossSwing(); }
        d.x = clamp(d.x + d.v * dt, this.L, this.R);
        if (!d.hit) {
          const r = w.hit ? metaRect(this.sh, d, w.hit) : rect(d.x, d.y - 60, d.x + d.face * 60, d.y - 20);
          if (overlap(r, playerHurtbox()) && hurtPlayer(BOSS_DMG * CM_SG.dbl * NGP.dmg, d.face, d.id, { src: this })) d.hit = true;
        }
      }
      if (d.an.done) { d.gone = true; cmSfx.splash(0.6); for (let i = 0; i < 18; i++) particles.push({ x: d.x + rand(-10, 10), y: d.y - rand(0, 80), vx: rand(-60, 60), vy: -rand(0, 80), g: 300, life: rand(0.4, 0.8), kind: 'blood' }); }
    }
    this.dbl = this.dbl.filter(d => !d.gone);
    if (!this.alive) this.dbl = [];
  }
  // ---------------------------------------------------------------- phase 2: flight
  airMove() {
    const r = Math.random();
    if (this.airN > 0 && (r < 0.55 || this.didRain)) { this.airN--; this.startDive(); return; }
    if (!this.didRain) { this.didRain = true; this.state = 'attack'; this.atk = 'rain'; this.tag = 'rain'; this.fired = {}; this.hitIds = new Set(); this.setA('rain'); this.rainT = 0; this.rainDone = false; this.state = 'airrain'; return; }
    this.state = 'descend'; this.setA('fly', true);
  }
  startDive() {
    this.atkId = ++hazardId; this.hitIds = new Set();
    this.diveTo = { x: clamp(P.x + P.vx * 0.2, this.L + 10, this.R - 10) };
    this.state = 'diveprep'; this.t = 0.5; this.setA('dive'); this.anim.speed = 0.6;
    spawnFx('telegraph', this.x + this.face * 10, this.y - 50, this.face); sfx.glint();
  }
  land(dived) {
    this.alt = 0; this.didRain = false; this.skyCd = rand(5, 8);
    shake = dived ? 8 : 3; sfx.boom(); cmSfx.splash(dived ? 1.2 : 0.6);
    if (dived) { for (const dd of [-1, 1]) cmWave(this.x + dd * 14, this.floor, dd, { dmg: CM_SG.splash, h: 13, v: 190, life: 1.6, src: this }); for (let i = 0; i < 24; i++) particles.push({ x: this.x + rand(-20, 20), y: this.floor - 2, vx: rand(-120, 120), vy: -rand(40, 180), g: 420, life: rand(0.4, 0.9), kind: 'blood' }); }
    this.state = 'recover'; this.t = dived ? 0.85 : 0.3; this.setA(this.sh.has('land') ? 'land' : 'idle', !this.sh.has('land'));
  }
  // the rain: marks bloom on the floor around you, then heavy drops fall on them
  rainVolley(n) {
    for (let k = 0; k < n; k++) {
      const x = clamp(k === 0 ? P.x : P.x + rand(-150, 150), this.L - 10, this.R + 10);
      CM.drops.push({ x, t: -k * 0.06, warn: 0.85, fall: 0.22, id: ++hazardId, y: this.floor });
    }
    cmSfx.gurgle();
  }
  // ---------------------------------------------------------------- phase 2 transition: the gown dissolves, the ballroom floods
  enterPhase2() {
    this.phase = 2; this.speed = 1.12; this.stance = 0; this.hidden = false; this.dbl = [];
    this.state = 'transform'; this.tT = 0; this.facePlayer(); this.whip = null;
    CM.lances = []; CM.waves = []; CM.drops = [];
    if (this.sheets[1].ok) this.sh = this.sheets[1];
    this.setA(this.sh.has('transform') ? 'transform' : 'idle', !this.sh.has('transform'));
    cmFloodBegin(this);
    shake = 8; flashScreen = 0.5; sfx.roar(); cmSfx.gurgle();
    bossPhase2Scene(this);
  }
  updateTransform(dt) {
    this.tT += dt;
    if (Math.random() < 0.9) particles.push({ x: this.x + rand(-26, 26), y: this.y - rand(0, 90), vx: rand(-40, 40), vy: -rand(20, 90), g: 60, life: rand(0.6, 1.2), kind: 'blood' });
    if (this.tT > 0.9 && (this.anim.done || !this.sh.has('transform'))) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.5; this.skyCd = 2; this.tideT = 5; }
  }
  tideDirector(dt) {
    if (!CM.flood || CM.flood.k < 0.95 || P.state === 'dead') return;
    if (['diveprep', 'dive', 'airrain', 'transform', 'stagger'].includes(this.state) || this.dbl.length || (this.state === 'attack' && ['dance', 'lances'].includes(this.atk))) return;
    this.tideT -= dt;
    if (this.tideT > 0 || CM.waves.some(w => w.big)) return;
    this.tideT = rand(7.5, 10.5) * (this.hp < this.maxHp * 0.25 ? 0.8 : 1);
    const from = P.x < room.pw / 2 ? 1 : -1, x0 = from < 0 ? this.L - 20 : this.R + 20;
    cmWave(x0, this.floor, -from, { dmg: CM_SG.tide, h: 22, w: 22, v: 250, life: 4, big: true, tele: 1.1, src: this });
    cmSfx.wave();
    if (!SAVE.hints.cm_tide) { SAVE.hints.cm_tide = 1; toast('A tide of blood rises. Jump it, or roll through.', 3); }
  }
  die() {
    this.state = 'dead'; this.hidden = false; this.dbl = []; this.whip = null; this.alt = Math.min(this.alt, 60);
    this.setA(this.sh.has('death') ? 'death' : 'stagger'); this.anim.speed = 1;
    CM.lances = []; CM.waves = []; CM.drops = []; CM.shots = [];
    hazards = []; shake = 12; hitstop = 0.3; slowmo = 1.6; flashScreen = 0.6; sfx.roar(); sfx.felled();
    victoryBanner = { text: 'THE LAST DANCE ENDS', t: 0 };
    if (CM.flood) CM.flood.target = 0.35;
    this.rewards();
  }
  stagger() { this.alt = 0; this.hidden = false; this.whip = null; super.stagger(); this.anim.set(this.sh.has('stagger') ? 'stagger' : 'idle', false, 1); }
  draw() {
    for (const d of this.dbl) {   // blood doubles
      if (!this.sh.ok) continue;
      drawSprite(this.sh, d.an.frame, d.x, d.y, d.face, { alpha: 0.72 * d.a, flash: 0.75, flashColor: '#c01828' });
      addLight(d.x, d.y - 50, 40, '220,40,50', 0.5 * d.a);
    }
    if (this.whip) {
      const pts = this.whip.pts;
      for (let k = 0; k < pts.length - 1; k++) {
        const [x0, y0] = pts[k], [x1, y1] = pts[k + 1], n = Math.ceil(Math.hypot(x1 - x0, y1 - y0));
        for (let s = 0; s <= n; s++) { const x = Math.round(lerp(x0, x1, s / n)), y = Math.round(lerp(y0, y1, s / n)), th = k < 6 ? 2 : 1;
          g.fillStyle = '#3a0610'; g.fillRect(x, y, th, th + 1); g.fillStyle = this.whip.hot ? '#e0303c' : '#9a1622'; g.fillRect(x, y, th, th); }
      }
      const tip = pts[pts.length - 1]; if (this.whip.hot) { addLight(tip[0], tip[1], 26, '255,60,60', 0.8); g.fillStyle = '#ffb0a8'; g.fillRect(Math.round(tip[0]), Math.round(tip[1]), 1, 1); }
    }
    if (this.hidden || this.state === 'dormant' && !this.sh.ok) return;
    if (!this.sh.ok) { g.fillStyle = '#6a1020'; g.fillRect(Math.round(this.x - 12), Math.round(this.y - 86), 24, 86); return; }
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' } : this.state === 'diveprep' ? { flash: 0.3 + 0.2 * Math.sin(time * 30), flashColor: '#ff4050' } : {};
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    if (this.alt > 6 && CM.flood) { g.fillStyle = 'rgba(20,0,4,0.35)'; g.beginPath(); g.ellipse(Math.round(this.x), this.floor - 2, 16 + this.alt * 0.05, 2, 0, 0, 6.3); g.fill(); }
  }
}
// the airborne rain is its own little state (so the hover drift continues while it rains)
const _cmSgUpdate = CmSanguine.prototype.update;
CmSanguine.prototype.update = function (dt) {
  if (this.state === 'airrain' && this.active && this.alive) {
    const an = this.anim;
    this.rainT += dt;
    const tx = clamp(P.x - this.face * 40, this.L + 20, this.R - 20); this.x = approach(this.x, tx, 60 * dt);
    const sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn.rain;
    if (!this.fired.r1 && an.i >= (sp ? sp.frame : 5)) { this.fired.r1 = true; this.rainVolley(9); }
    if (!this.fired.r2 && this.fired.r1 && this.rainT > 1.3) { this.fired.r2 = true; this.rainVolley(8); }
    if (this.rainT > 2.2 && (an.done || !this.sh.has('rain'))) { this.state = 'hover'; this.t = 0.3; this.setA('fly', true); }
  }
  _cmSgUpdate.call(this, dt);
};
BOSS_SPAWN.sanguine = (cx, fy) => new CmSanguine(cx, fy);
BOSS_CUTS.sanguine = b => [
  act(() => { b.anim.set(b.sh.has('dance') ? 'dance' : 'idle', true); b.face = -1; cmSfx.chime(); }),
  bossPan(b, 50, 1.6),
  say('', 'In the empty ballroom, someone is still dancing.'),
  act(() => { holdAnim(b, 'bow'); b.face = P.x < b.x ? -1 : 1; }), wait(1.0),
  say('Countess Sanguine', 'A guest. How long it has been since anyone came to my ball uninvited.'),
  say('Countess Sanguine', 'Dance with me, little ember. Your heart keeps such lovely time.'),
  act(() => { b.anim.set('idle', true); for (const c of CM.chands) c.red = 1; shake = 5; flashScreen = 0.3; cmSfx.gurgle(); for (let i = 0; i < 30; i++) particles.push({ x: b.x + rand(-30, 30), y: b.y - rand(0, 90), vx: rand(-20, 20), vy: -rand(20, 60), life: rand(0.8, 1.6), kind: 'blood' }); }), wait(1.2),
];
PHASE2_LINES.sanguine = ['Countess Sanguine', 'Enough courtesy. Let the whole house bleed for us.'];

// ================================================================== the ballroom: flood (sea of blood), the rain of phase 2
function cmBallroomSetup() {
  CM.flood = { k: 0, target: 0, t: 0, alt: null };
  if (SAVE.flags['boss:sanguine']) { CM.flood.k = CM.flood.target = 0.35; cmFloodBuildAlt(); }
}
function cmFloodBegin(b) {
  if (!CM.flood) CM.flood = { k: 0, target: 0, t: 0 };
  CM.flood.target = 1; cmFloodBuildAlt(); cmSfx.wave();
  for (const c of CM.chands) c.red = 1;
}
function cmFloodBuildAlt() {   // the back wall bleeds: streams of blood pour from every window and seam
  if (!CM.back0 || CM.flood.alt) return;
  const c = document.createElement('canvas'); c.width = room.pw; c.height = room.ph; const x = c.getContext('2d'); x.imageSmoothingEnabled = false;
  x.drawImage(CM.back0, 0, 0);
  x.globalCompositeOperation = 'source-atop'; x.fillStyle = 'rgba(12,0,4,0.42)'; x.fillRect(0, 0, room.pw, room.ph);
  for (let i = 0; i < 18; i++) {   // thin dark runnels down the walls (kept dark so she stays readable against them)
    const sx = Math.floor(hash2(i, 31) * room.pw), sy = 2 * TILE + Math.floor(hash2(i, 37) * 4 * TILE), len = 24 + Math.floor(hash2(i, 41) * 90);
    x.fillStyle = 'rgba(70,4,14,0.8)'; x.fillRect(sx, sy, 1, len);
    x.fillStyle = 'rgba(120,14,26,0.8)'; x.fillRect(sx, sy + len - 2, 1, 2);
  }
  x.globalCompositeOperation = 'source-over';
  CM.flood.alt = c;
}
function cmFloodAdvance() {   // real time, so the flood keeps rising during the phase-2 scene
  const F = CM.flood; if (!F) return;
  const dt = clamp(time - (F.lt ?? time), 0, 0.1); F.lt = time;
  F.k = approach(F.k, F.target, dt * (F.target > F.k ? 0.45 : 0.15));
  if (F.alt) room.back = F.k > 0.15 ? F.alt : CM.back0;
}
function cmBallroomUpdate(dt) {
  const F = CM.flood; if (!F) return;
  cmFloodAdvance();
  // rain of phase 2
  for (const d of CM.drops) {
    d.t += dt;
    if (d.t >= d.warn + d.fall && !d.hit) {
      d.hit = true; cmSfx.splash(0.4); shake = Math.max(shake, 1.5);
      for (let i = 0; i < 6; i++) particles.push({ x: d.x, y: d.y - 2, vx: rand(-60, 60), vy: -rand(30, 100), g: 400, life: 0.4, kind: 'blood' });
      if (overlap(rect(d.x - 7, d.y - 26, d.x + 7, d.y), playerHurtbox())) hurtPlayer(BOSS_DMG * CM_SG.drop * NGP.dmg, sign(P.x - d.x), d.id, { src: boss });
    }
  }
  CM.drops = CM.drops.filter(d => d.t < d.warn + d.fall + 0.1);
}
function cmBallroomDraw() {
  const F = CM.flood; if (!F) return;
  cmFloodAdvance();
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
  if (F.k <= 0.01) return;
  // the sea: a shallow crimson flood over the ballroom floor
  const depth = Math.round(9 * F.k), top = fl - depth, x0 = Math.floor(cam.x) - 2, x1 = Math.ceil(cam.x + W) + 2;
  g.fillStyle = 'rgba(60,0,10,0.9)'; g.fillRect(x0, top + 1, x1 - x0, fl - top + 2);
  for (let x = x0; x < x1; x += 2) {
    const o = Math.sin(time * 1.6 + x * 0.07) + 0.6 * Math.sin(time * 2.7 - x * 0.13);
    g.fillStyle = o > 0.9 ? 'rgba(220,70,80,0.95)' : o > 0 ? 'rgba(160,20,34,0.95)' : 'rgba(110,8,22,0.95)';
    g.fillRect(x, top + (o > 0.9 ? -1 : 0), 2, 1);
  }
  if (Math.random() < 0.25) particles.push({ x: rand(cam.x, cam.x + W), y: top, vx: 0, vy: -rand(10, 30), g: 100, life: 0.4, kind: 'blood' });
  // wading: ripples round your ankles and hers
  for (const e of [P, boss && boss.alive && boss.alt < 4 ? boss : null]) { if (!e) continue; const ph = (time * 2 + e.x * 0.01) % 1; g.strokeStyle = `rgba(230,90,100,${0.6 * (1 - ph)})`; g.lineWidth = 1; g.beginPath(); g.ellipse(Math.round(e.x), top + 1, 5 + ph * 10, 1.2 + ph, 0, 0, 6.3); g.stroke(); }
}

// ================================================================== debug handle (automated tests)
try { window.__cm = { CM, CMM, force(m) { if (boss && boss.begin) { boss.cool = 99; boss.begin(m); } else if (boss && boss.start) { boss.cool = 99; boss.start(m); } } }; } catch (e) {}
