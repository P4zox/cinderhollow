// ------------------------------------------------------------------ THORNVEIL WOOD (agent T)
// The Root's first seedlings, grown into a dark primeval forest above the Ossuary. Optional early region (after
// Gravetusk): the way in is a crack in C2's vault, climbed with the Hound's Talon.
// Tiles: '(' thorn bramble (id 35, hurts), ')' thorn wall (id 36, solid until slashed apart).
// Mechanics: drifting fog banks that hide what's inside them, spore pods that drop blinding spore clouds,
// rope-roots on the Root Hook rings (optional secrets), the thorn hatch shortcut (TV7 lever -> TV2).
// Enemies: tv_husk (antlered husk), tv_hound (thorn-hound), tv_wisp (spore-wisp).
// Bosses: the Thorn Coven (mini, TV4, three witches as `parts`) and the Antlered Warden (TV8).
// Rooms: tools/regions/70_thornveil.py. Art: art/gen_thornveil*.py, art/thornveil_*.py.
// Every top-level name is prefixed tv/TV (all region files share one scope).
Object.assign(AREAS, { thornveil: { name: 'Thornveil Wood', ambient: 0.46, amb: 'spore', tint: '#07100d', map: '#3f6a44' } });
Object.assign(SCALES, { thornveil: [0, 2, 3, 7, 8] });
Object.assign(ROOTS, { thornveil: 43.65 });
Object.assign(PCOL, { tv_leaf: '74,112,66', tv_mote: '150,255,190', tv_spore: '120,230,150', tv_thorn: '150,110,80' });
Object.assign(LORE, {
  tv1: ['A cairn of mossy stones, a deer skull set on top. Pale ribbons are knotted through its antlers:',
        '“The first seeds of the Root fell here, before there was a Hallow. They grew wild, and something grew to keep them.”'],
  tv2: ['A grave marker grown over with bark. Only a few words can be read beneath the moss:',
        '“We came to cut the old wood for the Root’s cradle. The wood came to us instead.”'],
  tv3: ['An antlered skull on a thorn-bound post. Ribbons for every name, and far too many ribbons:',
        '“The Warden takes no tithe but this: that you leave the way you came, or not at all.”'],
});

const TV_T_BRAMBLE = 35, TV_T_THORNWALL = 36;
const tvIn = () => room && room.def.biome === 'thornveil';
const TVR = { roomObj: null };
function tvReset() {
  Object.assign(TVR, { roomObj: room, dirty: false, spores: [], thorns: [], wakeT: 0, walls: [], fogs: [], pods: [], clumps: [], clouds: [], back: [], hatch: null, hints: {}, brT: 0, orbs: [], rootLines: [],
    tvWalls: [], trails: [] });
}
function tvEnsure() { if (TVR.roomObj !== room) tvReset(); }
const tvSfx = {
  rustle: () => { noise(0.35, 1800, 0.7, 0.18, 'bandpass', 0.8); },
  cut: () => { noise(0.18, 2600, 1.2, 0.3, 'highpass', 0.5); tone(220, 0.12, 0.06, 'sawtooth', 0.6); },
  snap: () => { noise(0.5, 900, 0.6, 0.45, 'lowpass', 0.4); tone(110, 0.3, 0.12, 'triangle', 0.5); },
  pop: () => { noise(0.3, 600, 1.0, 0.3, 'bandpass', 0.3); tone(330, 0.15, 0.06, 'sine', 0.4); },
  creak: () => { tone(70, 0.9, 0.12, 'sawtooth', 1.4); noise(0.8, 300, 0.8, 0.2, 'bandpass', 0.6); },
  chant: (p = 1) => { [196, 233, 294].forEach((f, i) => tone(f * p, 1.4, 0.05, 'sine', 1.02, i * 0.12)); },
  roots: () => { noise(0.7, 180, 0.7, 0.55, 'lowpass', 0.35); tone(55, 0.7, 0.2, 'sawtooth', 0.6); },
  spirit: () => { tone(880, 0.5, 0.05, 'sine', 1.5); tone(1320, 0.4, 0.03, 'sine', 1.3, 0.05); },
  bellow: () => { tone(62, 1.6, 0.26, 'sawtooth', 0.7); tone(93, 1.4, 0.14, 'triangle', 0.8); noise(1.2, 240, 0.6, 0.35, 'lowpass', 0.6); },
};

// ================================================================== tiles
function tvHaz() { return sheet('tv_hazards'); }
function tvWallCut(def, x, y) {   // walls are cut as a whole column run; the flag is keyed on the run's top cell
  let y0 = y; while (y0 > 0 && def.map[y0 - 1][x] === ')') y0--;
  return !!(SAVE && SAVE.flags[`tvcut:${def.id}:${x},${y0}`]);
}
registerTile('(', TV_T_BRAMBLE, { draw(ctx, sh, px, py, x, y, R) {
  const hs = tvHaz(); if (!hs.ok) { ctx.fillStyle = '#3a2218'; ctx.fillRect(px + 2, py + 6, 12, 10); return; }
  const t = hs.tag('bramble'), f = hs.frames[t.from + Math.floor(hash2(x * 3, y * 7) * 3)];
  ctx.drawImage(hs.img, f.x, f.y, f.w, f.h, px - 4, py - 8, f.w, f.h);
} });
registerTile(')', TV_T_THORNWALL, { solid: true, draw(ctx, sh, px, py, x, y, R, back) {
  if (tvWallCut(R.def, x, y)) return;
  drawTile(back, sh, 38 + Math.floor(hash2(x, y) * 4), px, py);   // the forest behind the thorns
  const hs = tvHaz(); if (!hs.ok) { ctx.fillStyle = '#4a2a1c'; ctx.fillRect(px + 3, py, 10, 16); return; }
  const up = y > 0 && R.def.map[y - 1][x] === ')', dn = y + 1 < R.h && R.def.map[y + 1][x] === ')';
  const tag = !up ? 'wall_top' : !dn ? 'wall_bot' : 'wall_mid', t = hs.tag(tag);
  const f = hs.frames[t.from + ((x + y) % (t.to - t.from + 1))];
  ctx.drawImage(hs.img, f.x, f.y, f.w, f.h, px - 4, py - 8, f.w, f.h);
} });

// ================================================================== decor
const TV_DECO = { idol: ['tv_idol', 'v0'], ribbons: ['tv_ribbons', 'loop'], fern: ['tv_fern', 'idle'], shroom: ['tv_shroom', 'idle'], vine: ['tv_vine', 'loop'] };
SPAWNS.tv_prop = (s, c) => {
  tvEnsure();
  if (s.back) { TVR.back.push({ sh: 'tv_tree', tag: 'v' + (s.v || 0), x: c.cx, y: c.fy }); return; }
  const d = TV_DECO[s.kind]; if (!d) return;
  const sh = sheet(d[0]), tag = s.kind === 'idol' ? 'v' + (s.v || 0) : d[1];
  const p = { type: 'tv_' + s.kind, x: c.cx, y: s.kind === 'vine' ? s.y * TILE : c.fy, face: s.flip ? -1 : 1, sh, anim: new Anim(sh, tag, true) };
  p.anim.t = rand(0, 500);
  if (s.kind === 'shroom') p.update = () => addLight(p.x, p.y - 10, 42 + Math.sin(time * 2 + p.x) * 3, '120,255,170', 0.7);
  if (s.kind === 'idol') p.update = () => { if ((s.v || 0) === 1) addLight(p.x + 2, p.y - 36, 24, '120,255,170', 0.45); };
  if (s.kind === 'vine') p.draw = () => drawSprite(sh, p.anim.frame, p.x, p.y, 1, { pivot: [8, 0] });
  props.push(p);
};
function tvPaintBack() {   // giant trees behind the play space, painted into the room's cached back layer
  if (!room || !room.back) return;
  const bx = room.back.getContext('2d');
  for (const t of TVR.back) {
    const sh = sheet(t.sh); if (!sh.ok) continue;
    const f = sh.frames[sh.first(t.tag)];
    bx.save(); bx.globalAlpha = 0.92; bx.drawImage(sh.img, f.x, f.y, f.w, f.h, Math.round(t.x - f.w / 2), Math.round(t.y - f.h + 12), f.w, f.h); bx.restore();
  }
}
function tvRerender() { renderRoomLayers(room); tvPaintBack(); }

// ================================================================== thorn walls (slash them apart)
function tvSetupWalls(def) {
  for (let x = 0; x < def.w; x++) for (let y = 0; y < def.h; y++) {
    if (def.map[y][x] !== ')' || (y > 0 && def.map[y - 1][x] === ')')) continue;
    let y1 = y; while (y1 + 1 < def.h && def.map[y1 + 1][x] === ')') y1++;
    const key = `tvcut:${def.id}:${x},${y}`;
    if (SAVE.flags[key]) { for (let yy = y; yy <= y1; yy++) room.grid[yy * room.w + x] = T_EMPTY; TVR.dirty = true; continue; }
    const w = { x, y0: y, y1, key, hp: 3, shakeT: 0 };
    const p = { type: 'tv_thornwall', x: x * TILE + 8, y: (y1 + 1) * TILE, face: 1, anim: { update() {} }, wall: w,
      hurtbox: () => w.cut ? null : rect(x * TILE - 2, y * TILE, x * TILE + 18, (y1 + 1) * TILE),
      onHit: info => tvHitWall(w, info), draw() {}, update(dt) { w.shakeT = Math.max(0, w.shakeT - dt); } };
    w.prop = p; TVR.walls.push(w); props.push(p);
  }
}
function tvHitWall(w, info) {
  if (w.cut) return;
  if (info.kind === 'spell' || info.kind === 'env') { spawnFx('hit', info.x, info.y, info.dir); return; }   // only blades part the thorns
  w.hp -= info.kind === 'heavy' || info.big ? 2 : 1; w.shakeT = 0.25;
  tvSfx.rustle(); sfx.hit(); hitstop = Math.max(hitstop, 0.04);
  for (let i = 0; i < 8; i++) particles.push({ x: info.x + rand(-4, 4), y: info.y + rand(-10, 10), vx: -info.dir * rand(20, 90) + rand(-20, 20), vy: -rand(20, 90), g: 300, life: rand(0.4, 0.8), kind: i % 2 ? 'tv_thorn' : 'tv_leaf' });
  if (w.hp > 0) return;
  w.cut = true; SAVE.flags[w.key] = 1; tvSfx.cut(); tvSfx.snap(); shake = Math.max(shake, 3);
  for (let yy = w.y0; yy <= w.y1; yy++) {
    room.grid[yy * room.w + w.x] = T_EMPTY;
    for (let i = 0; i < 10; i++) particles.push({ x: w.x * TILE + rand(0, 16), y: yy * TILE + rand(0, 16), vx: rand(-80, 80), vy: -rand(10, 110), g: 320, life: rand(0.6, 1.2), kind: i % 3 ? 'tv_thorn' : 'tv_leaf' });
  }
  tvRerender();
  props = props.filter(p => p !== w.prop);
  if (!SAVE.hints.tvcut) { SAVE.hints.tvcut = 1; toast('The thorns part under the blade.', 2.4); }
  saveGame();
}

// ================================================================== fog banks: whatever is inside stays hidden until you are close
SPAWNS.tv_fog = (s, c) => { tvEnsure(); TVR.fogs.push({ x0: s.x * TILE, y0: s.y * TILE, x1: (s.x + s.w) * TILE, y1: (s.y + s.h) * TILE, seed: rand(0, 100), k: 1 }); };
const TV_FOGC = document.createElement('canvas'); TV_FOGC.width = W; TV_FOGC.height = H;
const TV_FOGX = TV_FOGC.getContext('2d'); TV_FOGX.imageSmoothingEnabled = false;
function tvDrawFog() {
  const fs = sheet('tv_fog');
  const puffs = TVR.clouds.filter(c => c.fog > 0);
  if ((!TVR.fogs.length && !puffs.length) || !fs.ok) return;
  const f = fs.frames[0], cx = Math.round(cam.x), cy = Math.round(cam.y);
  const X = TV_FOGX;
  X.setTransform(1, 0, 0, 1, 0, 0); X.globalCompositeOperation = 'source-over'; X.globalAlpha = 1; X.clearRect(0, 0, W, H);
  const layer = (b, spd, alpha, oy) => {
    X.globalAlpha = alpha;
    const off = ((time * spd + b.seed * 7) % f.w + f.w) % f.w;
    for (let y = b.y0 - 16 + oy; y < b.y1 + 8; y += f.h - 24) for (let x = b.x0 - f.w + off - 16; x < b.x1 + 16; x += f.w) {
      if (x + f.w < cx || x > cx + W || y + f.h < cy || y > cy + H) continue;
      X.drawImage(fs.img, f.x, f.y, f.w, f.h, Math.round(x - cx), Math.round(y - cy), f.w, f.h);
    }
  };
  for (const b of TVR.fogs) {
    if (b.x1 < cx - 40 || b.x0 > cx + W + 40 || b.y1 < cy - 40 || b.y0 > cy + H + 40) continue;
    layer(b, 6, 0.9 * b.k, 0); layer(b, -4, 0.7 * b.k, 10);
    // soft left/right edges
    X.globalCompositeOperation = 'destination-out'; X.globalAlpha = 1;
    for (const [e, d] of [[b.x0, 1], [b.x1, -1]]) {
      const gr = X.createLinearGradient(e - cx - d * 10, 0, e - cx + d * 30, 0);
      gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
      X.fillStyle = gr; X.fillRect(d > 0 ? e - cx - 60 : e - cx - 30, b.y0 - cy - 30, 90, b.y1 - b.y0 + 60);
    }
    X.globalCompositeOperation = 'source-over';
  }
  for (const c of puffs) {   // spore clouds thicken into blinding puffs
    X.globalAlpha = Math.min(1, c.fog) * 0.9;
    for (let k = 0; k < 3; k++) X.drawImage(fs.img, f.x, f.y, f.w, f.h, Math.round(c.x - 64 + (k - 1) * 22 - cx), Math.round(c.y - 44 - k * 6 - cy), f.w, f.h);
  }
  // you can always see around yourself
  X.globalCompositeOperation = 'destination-out'; X.globalAlpha = 1;
  const px = P.x - cx, py = P.y - 14 - cy, gr = X.createRadialGradient(px, py, 14, px, py, 64);
  gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(0.45, 'rgba(0,0,0,0.85)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
  X.fillStyle = gr; X.fillRect(px - 70, py - 70, 140, 140);
  X.globalCompositeOperation = 'source-over';
  g.drawImage(TV_FOGC, cx, cy);
}

// ================================================================== spore pods: drop a blinding, stinging cloud when you pass below
SPAWNS.tv_pod = (s, c) => {
  tvEnsure();
  const sh = sheet('tv_pod'), p = { type: 'tv_pod', x: c.cx, y: s.y * TILE, face: 1, sh, anim: new Anim(sh, 'idle', true), st: 'idle', t: 0 };
  p.draw = () => drawSprite(sh, p.anim.frame, p.x, p.y, 1, { pivot: [12, 0] });
  p.update = dt => tvUpdatePod(p, dt);
  TVR.pods.push(p); props.push(p);
};
function tvUpdatePod(p, dt) {
  p.t -= dt;
  if (p.st === 'idle') {
    addLight(p.x, p.y + 17, 22, '120,255,170', 0.45);
    if (P.state !== 'dead' && Math.abs(P.x - p.x) < 30 && P.y > p.y + 20 && P.y - p.y < 190 && lineOfSight(p.x, p.y + 26, P.x, P.y - 20)) { p.st = 'shake'; p.t = 0.55; p.anim.set('shake', true); tvSfx.rustle(); }
  } else if (p.st === 'shake') {
    addLight(p.x, p.y + 17, 30, '120,255,170', 0.7);
    if (p.t <= 0) { p.st = 'burst'; p.anim.set('burst', false); tvSfx.pop(); TVR.clumps.push({ x: p.x, y: p.y + 24, vy: 30, id: ++hazardId }); }
  } else if (p.st === 'burst') {
    if (p.anim.done) { p.st = 'empty'; p.t = 7; p.anim.set('empty', true); }
  } else if (p.st === 'empty') {
    if (p.t <= 0) { p.st = 'regrow'; p.anim.set('regrow', false); }
  } else if (p.st === 'regrow' && p.anim.done) { p.st = 'idle'; p.anim.set('idle', true); }
}
function tvSporeK() { return 1; }   // hook for a future thorn-ward effect (c_moss is Mossheart regen, defined by G)
function tvUpdateSpores(dt) {
  for (const c of TVR.clumps) {
    c.vy = Math.min(c.vy + 520 * dt, 360); c.y += c.vy * dt;
    if (Math.random() < 0.6) particles.push({ x: c.x + rand(-3, 3), y: c.y, vx: rand(-10, 10), vy: -rand(0, 20), life: 0.4, kind: 'tv_spore' });
    addLight(c.x, c.y, 20, '120,255,170', 0.6);
    if (overlap(rect(c.x - 5, c.y - 5, c.x + 5, c.y + 5), playerHurtbox())) { hurtPlayer(14 * tvSporeK(), sign(P.x - c.x), c.id, { src: 'spore' }); tvSporeCloud(c.x, P.y); c.dead = true; }
    else if (solidAtPx(c.x, c.y + 4) || c.y > room.ph) { tvSporeCloud(c.x, Math.floor((c.y + 4) / TILE) * TILE); c.dead = true; }
  }
  TVR.clumps = TVR.clumps.filter(c => !c.dead);
  for (const c of TVR.clouds) {
    c.life -= dt; c.fog = Math.min(c.fog + dt * 3, c.life / 1.2, 1);
    if (Math.random() < 0.5) particles.push({ x: c.x + rand(-22, 22), y: c.y - rand(0, 30), vx: rand(-8, 8), vy: -rand(4, 16), life: 1, kind: 'tv_spore' });
    if (c.life > 0.4 && overlap(rect(c.x - 22, c.y - 36, c.x + 22, c.y), playerHurtbox())) hurtPlayer(7 * tvSporeK(), sign(P.x - c.x) || 1, c.id * 100 + Math.floor(c.life * 2), { src: 'spore' });
  }
  TVR.clouds = TVR.clouds.filter(c => c.life > 0);
}
function tvSporeCloud(x, y) {
  TVR.clouds.push({ x, y, life: 3.2, fog: 0, id: ++hazardId });
  spawnFx(fxOr('tv_cloud', 'dust'), x, y, 1, null, { bottom: true });
  for (let i = 0; i < 18; i++) particles.push({ x: x + rand(-8, 8), y: y - rand(0, 10), vx: rand(-70, 70), vy: -rand(10, 60), g: 30, life: rand(0.6, 1.3), kind: 'tv_spore' });
  tvSfx.pop();
}
function tvDrawClumps() {
  for (const c of TVR.clumps) { const x = Math.round(c.x), y = Math.round(c.y); g.fillStyle = '#20432b'; g.fillRect(x - 3, y - 3, 6, 6); g.fillStyle = '#5fe08e'; g.fillRect(x - 2, y - 2, 3, 3); g.fillStyle = '#b4ffd0'; g.fillRect(x - 1, y - 2, 1, 1); }
}

// ================================================================== brambles
function tvBrambleRects(b) {   // bramble cells overlapping a body
  const out = [];
  for (let ty = Math.floor((b.y - b.h) / TILE); ty <= Math.floor((b.y - 1) / TILE); ty++)
    for (let tx = Math.floor((b.x - b.w / 2) / TILE); tx <= Math.floor((b.x + b.w / 2) / TILE); tx++)
      if (tileAt(tx, ty) === TV_T_BRAMBLE) { const r = rect(tx * TILE + 2, ty * TILE + 5, tx * TILE + 14, ty * TILE + 16); if (overlap(r, rect(b.x - b.w / 2, b.y - b.h, b.x + b.w / 2, b.y))) out.push([tx, ty]); }
  return out;
}
function tvUpdateBrambles(dt) {
  const pb = { x: P.x, y: P.y, w: 10, h: 25 };
  const hits = P.state === 'dead' ? [] : tvBrambleRects(pb);
  if (hits.length) {
    const [tx] = hits[0];
    if (hurtPlayer(Math.round(D.maxHp * 0.08 * tvSporeK() + 4), P.x < tx * TILE + 8 ? -1 : 1, 'tvbr' + Math.floor(time / 0.7), { src: 'bramble' })) {
      P.vy = Math.min(P.vy, -170); tvSfx.rustle();
      for (let i = 0; i < 6; i++) particles.push({ x: P.x + rand(-5, 5), y: P.y - rand(2, 12), vx: rand(-50, 50), vy: -rand(20, 70), g: 300, life: 0.5, kind: 'blood' });
    }
  }
  // pogo off brambles with a downward strike (like spikes)
  if (P.state && P.anim.tag === 'attack_down' && !P.pogoed && P.anim.i >= 1 && P.anim.i <= 3) {
    for (const dx of [-6, 0, 6]) { const t = tileAt(Math.floor((P.x + dx) / TILE), Math.floor((P.y + 10) / TILE)); if (t === TV_T_BRAMBLE) { pogo(); tvSfx.rustle(); break; } }
  }
  // foes that stumble into brambles get torn too (the hounds are made of them)
  TVR.brT -= dt;
  if (TVR.brT <= 0) {
    TVR.brT = 0.8;
    for (const e of enemies) if (e.alive && !e.cfg.flying && e.type !== 'tv_hound' && tvBrambleRects({ x: e.x, y: e.y, w: e.w, h: e.h }).length) e.hit({ dmg: Math.round(e.maxHp * 0.06 + 3), poise: 0, dir: -e.face, kind: 'env', x: e.x, y: e.y - 8, quiet: true });
  }
}

// ================================================================== rope-roots on the hook rings (drawn from the ceiling above each ring)
function tvDrawRopeRoots() {
  if (!room.hooks) return;
  for (const h of room.hooks) {
    let top = h.y - 8; while (top > 0 && !solidAtPx(h.x, top - 1)) top -= 4;
    const n = Math.max(2, Math.floor((h.y - 6 - top) / 3));
    for (let i = 0; i <= n; i++) {
      const k = i / n, x = h.x + Math.sin(time * 1.3 + h.x * 0.1) * 2.5 * k * (1 - k) * 2, y = top + (h.y - 6 - top) * k;
      g.fillStyle = i % 5 === 2 ? '#2c5a35' : '#3a2c21'; g.fillRect(Math.round(x), Math.round(y), 2, 3);
      g.fillStyle = '#4e3c2c'; g.fillRect(Math.round(x), Math.round(y), 1, 3);
    }
  }
}

// ================================================================== TV7: the thorn hatch (lever) -- the shortcut down to the Mossgrave shrine
SPAWNS.tv_hatch = (s, c) => {
  tvEnsure();
  const sh = sheet('tv_hatch'), open = !!SAVE.flags['lever:' + c.id];
  const H_ = { x0: s.x * TILE, x1: (s.x + (s.w || 3)) * TILE, y: s.y * TILE, open, sh, anim: new Anim(sh, open ? 'open' : 'closed', false) };
  if (open) H_.anim.i = H_.anim.n - 1, H_.anim.done = true;
  TVR.hatch = H_;
  room.dyn.push({ x0: H_.x0, x1: H_.x1, y0: H_.y, y1: H_.y + TILE, on: () => !H_.open });
  props.push({ type: 'tv_hatch', x: (H_.x0 + H_.x1) / 2, y: H_.y, face: 1, sh, anim: H_.anim,
    update() { if (!H_.open && SAVE.flags['lever:' + room.id]) tvOpenHatch(H_); },
    draw() { if (H_.open && H_.anim.done) return; drawSprite(sh, H_.anim.frame, (H_.x0 + H_.x1) / 2, H_.y + 16, 1, { bottom: true }); } });
};
function tvOpenHatch(H_) {
  H_.open = true; H_.anim.set('open', false); tvSfx.snap(); tvSfx.creak(); shake = Math.max(shake, 4);
  for (let i = 0; i < 24; i++) particles.push({ x: rand(H_.x0, H_.x1), y: H_.y + rand(0, 8), vx: rand(-60, 60), vy: -rand(20, 120), g: 320, life: rand(0.6, 1.2), kind: i % 2 ? 'tv_thorn' : 'tv_leaf' });
  setTimeout(() => toast('The thorn lattice unknots. A way opens down to the Mossgrave shrine.', 3.5), 400);
}

// ================================================================== boss fog walls that reach the ceiling
SPAWNS.tv_gate = (s, c) => {
  if (SAVE.flags['boss:' + s.kind]) return;
  const x = s.x * TILE + 8, top = (s.top ?? 1) * TILE, fy = c.fy, sh = sheet('prop_fog');
  const on = () => boss && boss.kind === s.kind && boss.alive && (boss.active || !!s.exit);
  const p = { type: 'tv_gate', x, y: fy, face: 1, sh, anim: new Anim(sh, 'loop', true), on,
    update() { if (on()) { addLight(x, fy - 40, 50, '170,255,200', 0.5); if (Math.random() < 0.1) particles.push({ x: x + rand(-6, 6), y: rand(top, fy), vx: 0, vy: -rand(5, 15), life: 1, kind: 'tv_mote' }); } },
    draw() { if (!on() || !sh.ok) return; for (let yy = fy; yy > top + 1; yy -= sh.fh) drawSprite(sh, p.anim.frame, x, yy, 1, { bottom: true, alpha: 0.8 }); } };
  props.push(p);
  room.dyn.push({ x0: x - 8, x1: x + 8, y0: top, y1: fy, on });
};

// ================================================================== the Ossuary crack (C2): pale ribbons and spirit-light spilling down
function tvC2Crack() {
  if (!room || room.id !== 'C2') return;
  const x0 = 1 * TILE, x1 = 4 * TILE;
  addLight((x0 + x1) / 2, 30, 40, '120,255,170', 0.55);
  if (Math.random() < 0.08) particles.push({ x: rand(x0 + 2, x1 - 2), y: 30, vx: rand(-4, 4), vy: rand(8, 20), life: rand(2, 4), kind: 'tv_mote' });
  if (Math.random() < 0.03) particles.push({ x: rand(x0 + 2, x1 - 2), y: 30, vx: rand(-6, 6), vy: rand(10, 25), life: rand(3, 5), kind: 'tv_leaf' });
}
function tvDrawC2Crack() {
  if (!room || room.id !== 'C2') return;
  for (let k = 0; k < 3; k++) {   // ribbons trailing down out of the crack
    const bx = 1.5 * TILE + k * 14, L = 18 + k * 7;
    for (let i = 0; i < L; i++) { const x = bx + Math.sin(time * 1.4 + i * 0.25 + k) * (1 + i * 0.07); g.fillStyle = i < 4 ? '#e2dccb' : i < L * 0.7 ? '#bcb6a4' : '#8f8a7c'; g.fillRect(Math.round(x), 32 + i, 1, 1); }
  }
  for (let i = 0; i < 4; i++) { g.fillStyle = i % 2 ? '#2c5a35' : '#3e7440'; g.fillRect(TILE + 2 + i * 11, 32, 3, 2 + (i % 3)); }   // moss lipping the crack
}

// ================================================================== room setup + hooks
HOOKS.enter.push(def => {
  tvEnsure();
  if (def.biome !== 'thornveil') {
    if (def.id === 'C2') TVR.hints.c2 = false;
    return;
  }
  tvSetupWalls(def);
  if (TVR.dirty) renderRoomLayers(room);
  tvPaintBack();
  for (const p of props) if (p.type === 'candle') p.update = () => addLight(p.x, p.y - 6, 34 + Math.sin(time * 3 + p.x) * 2, '120,255,170', 0.6);   // glowing fungus
  if (def.id === 'TV1' && !SAVE.hints.tv_in) { SAVE.hints.tv_in = 1; setTimeout(() => toast('Cold, green air spills down the shaft. The smell of moss and old rain.', 3.5), 900); }
});
HOOKS.update.push(dt => {
  if (!room) return;
  tvEnsure();
  if (room.id === 'C2') {
    tvC2Crack();
    if (!TVR.hints.c2 && P.x < 6 * TILE && P.y > 6 * TILE && !SAVE.visited.TV1) {
      TVR.hints.c2 = true;
      toast(SAVE.items.talon ? 'Pale ribbons drift down from a crack in the vault. Cold green air, and the smell of a forest.'
                             : 'Pale ribbons drift down from a crack high in the vault. Far too high to climb bare-handed.', 4.2);
    }
  }
  if (!tvIn()) return;
  // ambient: falling leaves and drifting spirit-motes instead of spores
  for (const p of particles) if (p.amb && !p.tvk) { p.tvk = 1; if (Math.random() < 0.55) { p.kind = 'tv_leaf'; p.vy = rand(6, 16); p.vx = rand(-6, 6); p.pet = true; } else { p.kind = 'tv_mote'; p.vy = -rand(2, 8); } }
  tvUpdateBrambles(dt); tvUpdateSpores(dt); tvUpdateSporeShots(dt);
  if (TVR.hatch && room.id === 'TV7' && !TVR.hatch.open && !TVR.hints.hatch && P.y > 10 * TILE + 4) { TVR.hints.hatch = true; toast('A lattice of thorns seals the way, knotted from above.', 3); }
  if (room.id === 'TV7' && !TVR.hints.lever && !SAVE.flags['lever:TV7'] && Math.abs(P.x - 25.5 * TILE) < 40 && P.y < 11 * TILE) { TVR.hints.lever = true; toast('A root-lever, bound to the lattice in the floor.', 2.5); }
  tvUpdateBoss(dt);
});
HOOKS.render.push(() => {
  if (room && room.id === 'C2') tvDrawC2Crack();
  if (!tvIn()) return;
  tvDrawRopeRoots(); tvDrawClumps(); tvDrawSporeShots(); tvDrawBossFx(); tvDrawFog();
});
HOOKS.rest.push(() => { if (!tvIn()) return; for (const p of TVR.pods) { p.st = 'idle'; p.anim.set('idle', true); } });

// ================================================================== enemies
Object.assign(ENEMY, {
  tv_husk: { hp: 150, cinders: 95, speed: 30, aggro: 150, range: 46, poise: 25, stance: 80, dmg: { slash: 32, ram: 38 }, cool: [0.8, 1.6], lunge: { slash: 60, ram: 210 } },
  tv_hound: { hp: 105, cinders: 90, speed: 92, aggro: 170, range: 74, poise: 16, stance: 55, dmg: { pounce: 30 }, cool: [0.8, 1.4], leap: [230, -150] },
  tv_wisp: { hp: 60, cinders: 70, speed: 46, aggro: 190, range: 170, poise: 8, stance: 30, dmg: { spore: 22, dive: 20 }, cool: [2.2, 3.2], flying: true, ranged: 'tv_spore' },
});
Object.assign(ATTACK_TAGS, { tv_husk: ['slash', 'ram'], tv_hound: ['pounce'], tv_wisp: ['cast'] });
// the husk: a wandering, antlered hollow. The ram is telegraphed with a head-lowering pause and a green eye-glint.
ENEMY_CLASSES.tv_husk = class extends Enemy {
  draw() { super.draw(); if (this.alive) addLight(this.x + this.face * 6, this.y - 34, 16, '120,255,170', 0.35); }
};
ENEMY_CLASSES.tv_hound = class extends Enemy {
  draw() { super.draw(); if (this.alive && Math.random() < 0.03) particles.push({ x: this.x + rand(-10, 10), y: this.y - rand(4, 16), vx: 0, vy: -rand(4, 12), life: 0.6, kind: 'tv_leaf' }); }
};
// the spore-wisp: drifts in the fog and looses slow, seeking spore puffs that burst into stinging clouds
ENEMY_CLASSES.tv_wisp = class extends Enemy {
  updateFlying(dt) {
    if (this.state === 'attack' && this.atk === 'cast') {
      const c = this.cfg; this.cool -= dt;
      this.vx *= Math.pow(0.05, dt); this.vy *= Math.pow(0.05, dt); this.x += this.vx * dt; this.y += this.vy * dt; this.facePlayer();
      const sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn.cast;
      if (this.anim.i >= 2 && !this.spawned) addLight(this.x, this.y, 20 + this.anim.i * 3, '120,255,170', 0.8);
      if (!this.spawned && this.anim.i >= (sp ? sp.frame : 5)) {
        this.spawned = true; const at = sp ? metaPoint(this.sh, this, sp.at) : { x: this.x + this.face * 6, y: this.y };
        const a = Math.atan2(P.y - 14 - at.y, P.x - at.x);
        TVR.spores.push({ x: at.x, y: at.y, vx: Math.cos(a) * 95, vy: Math.sin(a) * 95, dmg: c.dmg.spore * NGP.dmg, life: 3.2, t: 0, id: ++hazardId });
        tvSfx.pop();
      }
      if (this.anim.done) { this.setA('idle', 'fly'); this.cool = rand(...c.cool); }
      addLight(this.x, this.y, 24, '120,255,170', 0.5);
      return;
    }
    super.updateFlying(dt);
  }
};
// spore puffs: slow, lightly seeking; they burst into a stinging cloud where they land or hit
function tvUpdateSporeShots(dt) {
  for (const b of TVR.spores) {
    b.t += dt; b.life -= dt;
    if (b.life > 0.3) {
      const a = Math.atan2(P.y - 16 - b.y, P.x - b.x), cur = Math.atan2(b.vy, b.vx);
      let d = a - cur; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI;
      const na = cur + clamp(d, -1.1 * dt, 1.1 * dt), sp = Math.hypot(b.vx, b.vy); b.vx = Math.cos(na) * sp; b.vy = Math.sin(na) * sp;
    }
    b.x += b.vx * dt; b.y += b.vy * dt;
    addLight(b.x, b.y, 22, '120,255,170', 0.7);
    if (Math.random() < 0.4) particles.push({ x: b.x, y: b.y, vx: rand(-10, 10), vy: rand(-10, 10), life: 0.4, kind: 'tv_spore' });
    if (overlap(rect(b.x - 4, b.y - 4, b.x + 4, b.y + 4), playerHurtbox())) { if (hurtPlayer(b.dmg * tvSporeK(), sign(b.vx), b.id, { src: 'spore' })) { b.life = 0; tvSporeCloud(b.x, P.y); } }
    else if (solidAtPx(b.x, b.y) || b.life <= 0) { b.life = 0; const gy = spGroundYTv(b.x, b.y - 6); tvSporeCloud(b.x, gy); }
  }
  TVR.spores = TVR.spores.filter(b => b.life > 0);
}
function spGroundYTv(x, y0) { for (let y = Math.max(0, y0); y < room.ph; y += 4) if (isSolidT(tileAt(Math.floor(x / TILE), Math.floor(y / TILE)))) return Math.floor(y / TILE) * TILE; return y0; }
function tvDrawSporeShots() {
  const fs = fxSheet('tv_spore');
  for (const b of TVR.spores) {
    if (fs.ok) { const t = fs.tag(Object.keys(fs.tags)[0]); drawSprite(fs, t.from + Math.floor(b.t * 10) % (t.to - t.from + 1), b.x, b.y, 1, { center: true }); continue; }
    const x = Math.round(b.x), y = Math.round(b.y); g.fillStyle = '#2f9a5e'; g.fillRect(x - 3, y - 3, 6, 6); g.fillStyle = '#b4ffd0'; g.fillRect(x - 1, y - 1, 2, 2);
  }
}


// ================================================================== shared boss hazards: root spikes, thorn darts, thorn walls, spirit orbs, root waves
const tvBD = (d, b) => BOSS_DMG * d * NGP.dmg * (b && b.phase === 2 ? 1.1 : 1) * ((b && b.dmgK) || 1);
function tvRootSpike(x, floor, delay, dmg, src) {   // green crack (telegraph) -> a thorned root erupts
  const id = ++hazardId;
  hazards.push({ x, y: floor, w: 16, h: 58, dmg: tvBD(dmg, src), id, life: 3, delay, fx: null,
    onStart: h => { h.fx = spawnFx(fxOr('tv_rootspike', 'root_spike', 'pillar'), h.x, h.y, 1, null, { bottom: true }); if (!h.fx) h.life = 0; },
    update: h => {
      if (!h.fx || h.fx.anim.done) { h.life = 0; return; }
      if (h.fx.anim.changed && h.fx.anim.i === 0) tvSfx.rustle();
      if (h.fx.anim.changed && h.fx.anim.i === 3) { shake = Math.max(shake, 3); tvSfx.roots(); for (let i = 0; i < 8; i++) particles.push({ x: h.x + rand(-6, 6), y: h.y - 2, vx: rand(-80, 80), vy: -rand(40, 140), g: 400, life: 0.7, kind: 'rock' }); }
      if (h.fx.anim.i <= 2) addLight(h.x, h.y - 4, 26, '120,255,170', 0.7);
    },
    active: h => h.fx && h.fx.anim.i >= 3 && h.fx.anim.i <= 5 });
}
function tvThorn(x, y, ang, spd, dmg, src, grav = 60) {
  TVR.thorns.push({ x, y, vx: Math.cos(ang) * spd, vy: Math.sin(ang) * spd, g: grav, dmg: tvBD(dmg, src), id: ++hazardId, life: 2.6, t: 0 });
}
function tvUpdateThorns(dt) {
  for (const t of TVR.thorns) {
    t.t += dt; t.life -= dt; t.vy += t.g * dt; t.x += t.vx * dt; t.y += t.vy * dt;
    if (Math.random() < 0.3) particles.push({ x: t.x, y: t.y, vx: 0, vy: 0, life: 0.25, kind: 'tv_mote' });
    if (overlap(rect(t.x - 4, t.y - 3, t.x + 4, t.y + 3), playerHurtbox()) && hurtPlayer(t.dmg, sign(t.vx), t.id, { src: boss })) t.life = 0;
    else if (solidAtPx(t.x, t.y) || solidDynAt(t.x, t.y)) { t.life = 0; for (let i = 0; i < 4; i++) particles.push({ x: t.x, y: t.y, vx: rand(-40, 40), vy: -rand(10, 60), g: 300, life: 0.4, kind: 'tv_thorn' }); }
  }
  TVR.thorns = TVR.thorns.filter(t => t.life > 0);
}
function tvDrawThorns() {
  const s = fxSheet('tv_thorn');
  for (const t of TVR.thorns) {
    if (s.ok) drawRotated(s, s.first('tv_thorn') + (Math.floor(t.t * 12) % 2), t.x, t.y, Math.atan2(t.vy, t.vx));
    else { g.fillStyle = '#5fe08e'; g.fillRect(Math.round(t.x) - 2, Math.round(t.y) - 1, 4, 2); }
    addLight(t.x, t.y, 16, '120,255,170', 0.5);
  }
}
// summoned thorn walls: low barriers (jumpable, 2 cuts) that bristle -- touching them hurts
function tvSummonWall(x, floor, src, life = 5.5) {
  const w = { x, floor, t: 0, life, st: 'rise', hp: 2, id: ++hazardId, src };
  w.fx = spawnFx(fxOr('tv_wall'), x, floor, 1, null, { bottom: true });
  w.dyn = { x0: x - 7, x1: x + 7, y0: floor - 40, y1: floor, on: () => w.st !== 'gone' && w.t > 0.18 && w.st !== 'wither' };
  room.dyn.push(w.dyn);
  w.prop = { type: 'tv_bwall', x, y: floor, face: 1, anim: { update() {} }, draw() {}, hurtbox: () => (w.st === 'idle' || (w.st === 'rise' && w.t > 0.18)) ? rect(x - 8, floor - 42, x + 8, floor) : null,
    onHit: info => { if (info.kind === 'spell') return; w.hp -= info.kind === 'heavy' || info.big ? 2 : 1; tvSfx.rustle(); sfx.hit(); for (let i = 0; i < 6; i++) particles.push({ x, y: floor - rand(4, 36), vx: -info.dir * rand(20, 80), vy: -rand(20, 80), g: 300, life: 0.5, kind: 'tv_thorn' }); if (w.hp <= 0) tvWitherWall(w, true); } };
  props.push(w.prop);
  TVR.tvWalls.push(w); tvSfx.roots(); shake = Math.max(shake, 2);
  // never trap the player inside: nudge them out of a wall that rises on top of them
  if (Math.abs(P.x - x) < 12 && P.y > floor - 44) P.x = x + (P.x < x ? -13 : 13);
  return w;
}
function tvWitherWall(w, cut) {
  if (w.st === 'wither' || w.st === 'gone') return;
  w.st = 'wither'; w.t = 0; props = props.filter(p => p !== w.prop);
  if (w.fx) w.fx.kill = true;
  w.fx = spawnFx(fxOr('tv_wall'), w.x, w.floor, 1, null, { bottom: true });
  if (w.fx) { w.fx.anim.set('wither', false); }
  if (cut) { tvSfx.cut(); for (let i = 0; i < 12; i++) particles.push({ x: w.x + rand(-6, 6), y: w.floor - rand(0, 40), vx: rand(-90, 90), vy: -rand(20, 120), g: 320, life: rand(0.5, 1), kind: 'tv_thorn' }); }
}
function tvUpdateWalls(dt) {
  for (const w of TVR.tvWalls) {
    w.t += dt;
    if (w.st === 'rise' && w.fx && w.fx.anim.done) { w.st = 'idle'; w.fx = spawnFx(fxOr('tv_wall'), w.x, w.floor, 1, null, { bottom: true, loop: true }); if (w.fx) w.fx.anim.set('idle', true); }
    if (w.st === 'idle' && w.t > w.life) tvWitherWall(w, false);
    if (w.st === 'wither' && (!w.fx || w.fx.anim.done || w.t > 1)) { w.st = 'gone'; if (w.fx) w.fx.kill = true; }
    if ((w.st === 'idle' || (w.st === 'rise' && w.t > 0.18)) && overlap(rect(w.x - 9, w.floor - 40, w.x + 9, w.floor), playerHurtbox())) {
      if (hurtPlayer(tvBD(14, w.src), P.x < w.x ? -1 : 1, 'tvw' + w.id + Math.floor(w.t), { src: w.src })) P.vx = (P.x < w.x ? -1 : 1) * 120;
    }
  }
  TVR.tvWalls = TVR.tvWalls.filter(w => w.st !== 'gone');
}
function tvClearWalls() { for (const w of TVR.tvWalls) tvWitherWall(w, false); }
// phase 2: spirit-light storms (orbs fall from the canopy onto marked spots) and root waves along the floor
function tvOrb(x, floor, delay, src) { TVR.orbs.push({ x, floor, delay, y: -20, vy: 0, id: ++hazardId, src }); }
function tvUpdateOrbs(dt) {
  for (const o of TVR.orbs) {
    if (o.delay > 0) { o.delay -= dt; continue; }
    o.vy = Math.min(o.vy + 700 * dt, 420); o.y += o.vy * dt; addLight(o.x, o.y, 26, '120,255,170', 0.8);
    if (overlap(rect(o.x - 5, o.y - 5, o.x + 5, o.y + 5), playerHurtbox())) { hurtPlayer(tvBD(28, o.src), sign(P.x - o.x), o.id, { src: o.src }); o.dead = true; }
    if (o.y >= o.floor - 4) {
      o.dead = true; spawnFx(fxOr('tv_burst', 'hit'), o.x, o.floor - 8, 1); tvSfx.spirit(); shake = Math.max(shake, 2);
      if (overlap(rect(o.x - 14, o.floor - 20, o.x + 14, o.floor), playerHurtbox())) hurtPlayer(tvBD(24, o.src), sign(P.x - o.x), o.id, { src: o.src });
      for (let i = 0; i < 8; i++) particles.push({ x: o.x, y: o.floor - 2, vx: rand(-70, 70), vy: -rand(20, 90), g: 200, life: 0.6, kind: 'tv_mote' });
    }
  }
  TVR.orbs = TVR.orbs.filter(o => !o.dead);
}
function tvDrawOrbs() {
  const s = fxSheet('tv_orb');
  for (const o of TVR.orbs) {
    const warn = o.delay > 0 || o.y < o.floor - 60, k = 0.5 + 0.5 * Math.sin(time * 18);
    if (warn) { g.fillStyle = `rgba(95,224,142,${0.3 + 0.35 * k})`; g.beginPath(); g.ellipse(Math.round(o.x), o.floor - 1, 12, 2.5, 0, 0, 6.3); g.fill(); addLight(o.x, o.floor - 4, 22, '120,255,170', 0.4); }
    if (o.delay <= 0) { if (s.ok) drawSprite(s, s.first('tv_orb') + Math.floor(time * 12) % 4, o.x, o.y, 1, { center: true }); else { g.fillStyle = '#b4ffd0'; g.fillRect(Math.round(o.x) - 3, Math.round(o.y) - 3, 6, 6); } }
  }
}
function tvRootWave(x, floor, dir, src, spd = 150) { TVR.rootLines.push({ x, floor, dir, spd, life: 3.2, id: ++hazardId, src }); }
function tvUpdateRootWaves(dt) {
  for (const w of TVR.rootLines) {
    w.x += w.dir * w.spd * dt; w.life -= dt;
    if (w.x < 8 || w.x > room.pw - 8 || solidAtPx(w.x + w.dir * 6, w.floor - 4)) w.life = 0;
    if (Math.random() < 0.7) particles.push({ x: w.x + rand(-4, 4), y: w.floor - rand(0, 4), vx: -w.dir * rand(10, 40), vy: -rand(20, 70), g: 300, life: 0.45, kind: Math.random() < 0.5 ? 'tv_thorn' : 'rock' });
    if (overlap(rect(w.x - 7, w.floor - 14, w.x + 7, w.floor), playerHurtbox())) hurtPlayer(tvBD(24, w.src), w.dir, w.id, { src: w.src });
    addLight(w.x, w.floor - 6, 24, '120,255,170', 0.5);
  }
  TVR.rootLines = TVR.rootLines.filter(w => w.life > 0);
}
function tvDrawRootWaves() {
  for (const w of TVR.rootLines) {
    const x = Math.round(w.x), y = Math.round(w.floor);
    for (let k = 0; k < 4; k++) { const h = 6 + ((k * 5 + Math.floor(time * 24)) % 8), xx = x - 6 + k * 4 - w.dir * 2; g.fillStyle = '#3a2c21'; g.fillRect(xx, y - h, 2, h); g.fillStyle = '#6e4a38'; g.fillRect(xx, y - h, 1, h - 2); g.fillStyle = '#a3806a'; g.fillRect(xx, y - h - 1, 1, 1); }
    g.fillStyle = '#5fe08e'; g.fillRect(x - 1, y - 3, 2, 2);
  }
}
// the sinking Warden's path: a bulge of roots churning along the floor
function tvDrawTrails() {
  for (const t of TVR.trails) {
    const x = Math.round(t.x), y = t.floor;
    for (let k = -3; k <= 3; k++) { const h = Math.max(1, 6 - Math.abs(k) * 1.6 + Math.sin(time * 20 + k) * 1.5); g.fillStyle = k % 2 ? '#2a2018' : '#3a2c21'; g.fillRect(x + k * 3, Math.round(y - h), 3, Math.round(h)); }
    g.fillStyle = '#5fe08e'; g.fillRect(x - 1, y - 7, 2, 1);
  }
}
function tvUpdateBoss(dt) { tvUpdateThorns(dt); tvUpdateWalls(dt); tvUpdateOrbs(dt); tvUpdateRootWaves(dt); }
function tvDrawBossFx() { tvDrawTrails(); tvDrawRootWaves(); tvDrawThorns(); tvDrawOrbs(); tvDrawBossArena(); }
function tvClearBossFx() { TVR.thorns = []; TVR.orbs = []; TVR.rootLines = []; TVR.trails = []; tvClearWalls(); hazards = []; }

// ================================================================== THE THORN COVEN (mini-boss, TV4): three witches fought together
BOSS_INFO.coven = { name: 'The Thorn Coven', hp: 1500, cinders: 3600, reward: ['sp:bramble_snare', 'emberstone'], quote: 'Three who tend the briars. Three who never let go.' };
const TV_COVEN = [
  { name: 'The Briar Mother', sheet: 'coven', w: { strike: 2.2, summon: 1.4, cast: 0.6, blink: 0.5 }, prefer: 46 },
  { name: 'The Moss Maiden', sheet: 'coven_b', w: { cast: 2.0, blink: 1.2, strike: 0.7, summon: 0.6 }, prefer: 120 },
  { name: 'The Ribbon Crone', sheet: 'coven_c', w: { summon: 2.0, cast: 1.2, blink: 0.8, strike: 0.6 }, prefer: 90 },
];
const TV_COVEN_DMG = { strike: 34, bolt: 22, spike: 30, tide: 22 };
class TvWitch extends BossBase {
  constructor(coven, x, y, idx) {
    super('coven', x, y);
    const C_ = TV_COVEN[idx];
    this.coven = coven; this.idx = idx; this.cfg = C_; this.name = C_.name;
    this.sh = sheet(C_.sheet, { meta: ASSETS.coven_meta }); this.anim = new Anim(this.sh, 'chant', true); this.anim.t = rand(0, 500);
    this.hp = this.maxHp = this.displayHp = Math.round(500 * NGP.hp); this.stanceMax = 170; this.critRange = 48;
    this.state = 'idle'; this.cool = 1.2 + idx * 0.7; this.face = -1; this.vx = 0; this.speedK = 1;
  }
  get L() { return 3 * TILE + 10; }
  get R() { return 33 * TILE - 10; }
  activate() { this.coven.activate(); }
  canStagger() { return this.state !== 'blink' && !(this.state === 'attack' && this.anim.i >= 5); }
  hurtbox() { if (!this.alive || this.state === 'blink' && this.anim.i >= 3 && this.anim.i <= 7) return null; const m = this.sh.meta; return m ? metaRect(this.sh, this, m.hurtbox) : rect(this.x - 8, this.y - 50, this.x + 8, this.y); }
  hit(info) { if (this.state === 'chant' && !info.crit) info = { ...info, dmg: info.dmg * 1.3 }; super.hit(info); this.coven.onPartHit(this); }
  stagger() { super.stagger(); this.anim.set('stagger', false, 1); }
  setA(tag, loop = false, speed = this.speedK) { this.anim.set(this.sh.has(tag) ? tag : 'idle', loop, speed); }
  die() {
    this.state = 'dead'; this.setA('death', false, 1); sfx.roar(); shake = 6; slowmo = 0.4; flashScreen = 0.25; tvSfx.chant(0.7);
    const rest = this.coven.parts.filter(q => q !== this && q.alive);
    for (const q of rest) { q.enraged = true; q.speedK = 1.2; q.stance = 0; spawnFx(fxOr('tv_burst', 'roar_ring'), q.x, q.y - 40, 1); }
    if (rest.length) toast(rest.length === 2 ? 'The coven shrieks. The briars grow wild.' : `${rest[0].name} is alone now, and furious.`, 3);
  }
  start(m) {
    this.facePlayer(); this.atk = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = false; this.coven.busy = this;
    if (m === 'blink') { this.state = 'blink'; this.setA('blink'); return; }
    this.state = 'attack'; this.setA(m);
  }
  pick() {
    const d = Math.abs(P.x - this.x), w = { ...this.cfg.w };
    if (d > 80) w.strike *= 0.15; else w.strike *= 1.8;
    if (d < 40) w.blink *= 2;
    if (this.last) w[this.last] *= 0.3;
    const e = Object.entries(w); let r = Math.random() * e.reduce((a, [, v]) => a + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return 'cast';
  }
  update(dt) {
    this.commonUpdate(dt); this.anim.update(dt);
    const an = this.anim;
    if (this.state === 'dead') { if (an.done) { an.hold(); if (!this.gone) { this.gone = true; spawnFx(fxOr('tv_burst', 'dust'), this.x, this.y - 20, 1); } } return; }
    if (!this.active) { this.facePlayer(); return; }
    if (this.coven.introT > 0) return;
    const d = Math.abs(P.x - this.x);
    switch (this.state) {
      case 'idle': case 'walk': {
        this.facePlayer(); this.cool -= dt * this.speedK;
        if (P.state === 'dead') { this.setWalk(0, dt); break; }
        const busy = this.coven.busy && this.coven.busy !== this && this.coven.busy.alive && ['attack', 'blink', 'chant'].includes(this.coven.busy.state);
        if (this.cool <= 0 && (!busy || this.enraged)) { const m = this.pick(); this.last = m; this.start(m); break; }
        // surround the player: each sister walks to her own slot (near side, far side, back line)
        const tx = this.coven.slotX(this);
        let want = Math.abs(tx - this.x) > 14 ? sign(tx - this.x) : 0;
        for (const q of this.coven.parts) if (q !== this && q.alive && Math.abs(q.x - this.x) < 14 && Math.abs(tx - this.x) < 20) want = sign(this.x - q.x) || 1;
        this.setWalk(want, dt);
        break;
      }
      case 'attack': this.updateAttack(dt); break;
      case 'blink': this.updateBlink(dt); break;
      case 'chant': this.t -= dt; if (this.t <= 0) { this.state = 'idle'; this.setA('idle', true); this.cool = rand(0.6, 1.2); } break;
      case 'stagger':
        this.t -= dt; if (an.i === an.n - 1 && this.t > 0.3) an.hold();
        if (an.done || this.t <= 0) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.5; }
        break;
    }
    this.x = clamp(this.x, this.L, this.R);
  }
  setWalk(dir, dt) {
    const want = dir ? 'walk' : 'idle';
    if (this.state !== want || this.anim.tag !== want) { this.state = want; this.setA(want, true, dir ? this.speedK : 1); }
    this.x = clamp(this.x + dir * 34 * this.speedK * dt, this.L, this.R);
  }
  updateAttack(dt) {
    const an = this.anim, a = this.atk, sh = this.sh, M = sh.meta || {};
    const tel = M.telegraph && M.telegraph[a];
    if (tel && an.changed && an.i === tel.frame) { const p = metaPoint(sh, this, tel.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); tvSfx.chant(1 + this.idx * 0.12); }
    if (an.i < 4) this.facePlayer();
    if (a === 'strike') {
      for (const w of metaWindows(sh, 'strike')) if (an.i >= w.active[0] && an.i <= w.active[1]) {
        if (an.changed && an.i === w.active[0]) { sfx.swing(); this.x = clamp(this.x + this.face * 14, this.L, this.R); }
        if (!this.hitIds.has(0) && overlap(metaRect(sh, this, w.hit), playerHurtbox()) && hurtPlayer(tvBD(TV_COVEN_DMG.strike) * (this.enraged ? 1.1 : 1), this.face, this.atkId, { parryable: true, src: this })) this.hitIds.add(0);
      }
    }
    const sp = M.spawn && M.spawn[a];
    if (sp && !this.fired && an.i >= sp.frame) {
      this.fired = true; const at = metaPoint(sh, this, sp.at);
      if (a === 'cast') {
        const ang = Math.atan2(P.y - 14 - at.y, P.x - at.x), n = this.enraged ? 3 : 1;
        for (let k = 0; k < n; k++) tvThorn(at.x, at.y, ang + (k - (n - 1) / 2) * 0.2, 175, TV_COVEN_DMG.bolt, this, 30);
        tvSfx.spirit(); sfx.shoot();
      } else if (a === 'summon') {
        tvSfx.roots(); shake = Math.max(shake, 3);
        const x0 = clamp(P.x + P.vx * 0.25, 2 * TILE + 10, 34 * TILE - 10);
        tvRootSpike(x0, this.floor, 0.05, TV_COVEN_DMG.spike, this);
        if (this.enraged) { tvRootSpike(clamp(x0 - 36, 40, 34 * TILE - 10), this.floor, 0.3, TV_COVEN_DMG.spike, this); tvRootSpike(clamp(x0 + 36, 40, 34 * TILE - 10), this.floor, 0.3, TV_COVEN_DMG.spike, this); }
      }
    }
    if (an.done) { this.state = 'idle'; this.setA('idle', true); this.cool = this.enraged ? rand(0.5, 1.0) : rand(1.2, 2.0); }
  }
  updateBlink(dt) {
    const an = this.anim;
    if (an.changed && an.i === 1) { tvSfx.rustle(); for (let i = 0; i < 10; i++) particles.push({ x: this.x + rand(-10, 10), y: this.floor - rand(0, 20), vx: rand(-30, 30), vy: -rand(10, 50), life: 0.8, kind: 'tv_leaf' }); }
    if (an.changed && an.i === 5) {   // move while hidden: to a spot away from the sisters, never inside a wall or past the fog
      const side = Math.random() < 0.5 ? -1 : 1;
      let nx = clamp(P.x + side * rand(70, 130), this.L + 10, this.R - 10);
      if (Math.abs(nx - P.x) < 50) nx = clamp(P.x - side * 90, this.L + 10, this.R - 10);
      this.x = nx; this.facePlayer(); tvSfx.rustle();
    }
    if (an.done) { this.state = 'idle'; this.setA('idle', true); this.cool = rand(0.3, 0.8); }
  }
  critable() { return this.state === 'stagger' && this.anim.i >= 1 && !this.critDone; }
  draw() {
    if (this.gone && this.anim.done) return;
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' }
      : this.enraged ? { flash: 0.1 + 0.07 * Math.sin(time * 9), flashColor: '#5fe08e' } : {};
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    if (this.critable()) { g.fillStyle = '#ffd070'; const y = Math.round(this.y - 66 + Math.sin(time * 8) * 1.5); g.fillRect(Math.round(this.x) - 1, y, 3, 3); g.fillRect(Math.round(this.x), y - 1, 1, 5); g.fillRect(Math.round(this.x) - 2, y + 1, 5, 1); }
    if (this.alive && this.active) {
      const w = 30, x = Math.round(this.x - w / 2), y = Math.round(this.y - 64);
      g.fillStyle = 'rgba(10,6,8,0.8)'; g.fillRect(x - 1, y - 1, w + 2, 4);
      g.fillStyle = this.enraged ? '#3fae6a' : '#2f7a4a'; g.fillRect(x, y, Math.max(0, w * this.hp / this.maxHp), 2);
    }
    if (this.alive) { addLight(this.x + this.face * 10, this.y - 50, 44, '120,255,170', this.state === 'chant' ? 0.9 : 0.55); addLight(this.x, this.y - 26, 40, '200,230,210', 0.35); }
  }
}
class TvCoven extends BossBase {
  constructor(x, y) {
    super('coven', x, y);
    this.parts = [new TvWitch(this, x - 40, y, 0), new TvWitch(this, x + 4, y, 1), new TvWitch(this, x + 48, y, 2)];
    this.hp = this.maxHp = this.displayHp = this.parts.reduce((s, q) => s + q.maxHp, 0);
    this.sh = sheet('coven'); this.state = 'dormant'; this.ritualT = 9; this.busy = null;
    const parts = this.parts;
    this.anim = { i: 0, n: 2, done: false, tag: 'idle', get frame() { return 0; }, update(dt) {}, set(tag, loop) { for (const q of parts) if (q.alive) q.setA(tag, loop); } };
  }
  get alive() { return this.state !== 'dead'; }
  hurtbox() { return null; }
  canStagger() { return false; }
  onPartHit() { this.hp = this.parts.reduce((s, q) => s + Math.max(0, q.hp), 0); const hit = this.parts.filter(q => q.dmgT > 0); this.dmgShown = hit.reduce((s, q) => s + q.dmgShown, 0); this.dmgT = Math.max(...this.parts.map(q => q.dmgT)); }
  facePlayer() { for (const q of this.parts) if (q.alive) q.facePlayer(); }
  slotX(w) {   // slots around the player (near side, far side, back line), matched to the sisters left-to-right so they never cross
    const alive = this.parts.filter(q => q.alive), lead = alive.reduce((a, q) => Math.abs(q.x - P.x) < Math.abs(a.x - P.x) ? q : a, alive[0]);
    const side = sign(lead.x - P.x) || -1, L = w.L + 6, R = w.R - 6;
    const offs = [[side * 52], [side * 52, -side * 104], [side * 52, -side * 104, side * 150]][alive.length - 1];
    const tx = offs.map(o => { let x = P.x + o; if (x < L || x > R) x = P.x - o; return clamp(x, L, R); }).sort((a, b) => a - b);
    const order = [...alive].sort((a, b) => a.x - b.x);
    return tx[Math.max(0, order.indexOf(w))];
  }
  update(dt) {
    this.flash = 0; this.dmgT -= dt;
    const alive = this.parts.filter(q => q.alive);
    this.x = alive.length ? alive.reduce((s, q) => s + q.x, 0) / alive.length : this.x; this.camX = this.x;
    this.hp = this.parts.reduce((s, q) => s + Math.max(0, q.hp), 0);
    this.displayHp += (this.hp - this.displayHp) * Math.min(1, dt * (this.dmgT > 1.4 ? 0 : 3));
    for (const q of this.parts) { q.active = this.active; q.update(dt); }
    if (!this.active) { if (!this.cutting && P.x < 31 * TILE && P.ground && this.state !== 'dead' && P.state !== 'dead') this.activate(); return; }
    if (this.introT > 0) { this.introT -= dt; if (this.introT <= 0) this.state = 'idle'; }
    // the ritual: while two or more live, they chant together and a tide of brambles rolls out from each of them (jump it)
    if (alive.length >= 2 && this.state !== 'dead') {
      this.ritualT -= dt;
      if (this.ritualT <= 0 && alive.every(q => ['idle', 'walk'].includes(q.state))) {
        this.ritualT = alive.length === 3 ? rand(12, 15) : rand(9, 12);
        for (const q of alive) { q.state = 'chant'; q.setA('chant', true); q.t = 1.7; q.facePlayer(); }
        toast('The coven chants. The briars stir beneath you.', 2.2); tvSfx.chant(0.9);
        for (const q of alive) for (let k = 0; k < 2; k++) setTimeout(() => { if (boss === this && q.alive && q.state === 'chant') { for (const dd of [-1, 1]) tvRootWave(q.x + dd * 10, q.floor, dd, q, 135); tvSfx.roots(); shake = Math.max(shake, 3); } }, 900 + k * 650);
      }
    }
    if (this.state !== 'dead' && !alive.length && this.parts.every(q => q.anim.done)) this.die();
  }
  die() {
    this.state = 'dead'; this.anim.i = 1;
    tvClearBossFx(); shake = 8; hitstop = 0.2; slowmo = 1.0; flashScreen = 0.4; sfx.felled();
    victoryBanner = { text: 'THE COVEN IS UNBOUND', t: 0 };
    this.rewards();
  }
  draw() { for (const q of this.parts) q.draw(); }
}
BOSS_SPAWN.coven = (cx, fy) => sheet('coven').ok ? new TvCoven(cx, fy) : null;
BOSS_CUTS.coven = b => [
  act(() => { for (const q of b.parts) { q.face = -1; q.setA('chant', true); } }),
  { pan: { x: b.x, y: b.y - 50 }, dur: 1.2 },
  say('', 'Three figures in bark and bramble stand in a ring, chanting to the roots.'),
  act(() => { tvSfx.chant(0.8); for (const q of b.parts) { q.facePlayer(); q.setA('summon', false); } }), wait(0.9),
  act(() => { shake = 5; sfx.roar(); for (const q of b.parts) { spawnFx(fxOr('tv_burst', 'roar_ring'), q.x, q.y - 40, 1); q.setA('idle', true); } }), wait(0.6),
  { do: () => { for (const q of b.parts) { q.state = 'idle'; q.setA('idle', true); } }, always: true },
];

// ================================================================== THE ANTLERED WARDEN (TV8)
BOSS_INFO.warden = { name: 'The Antlered Warden', hp: 2000, cinders: 9000, reward: ['w:antler_scythe', 'c_antler', 'shard'],
  quote: '“Leave the way you came, or not at all.”' };
const TV_WD = { sweep: 44, thrust: 48, erupt: 38, volley: 22, charge: 46, rise: 42 };
class TvWarden extends BossBase {
  constructor(x, y) {
    super('warden', x, y);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.warden.hp * NGP.hp);
    const meta = ASSETS.warden_meta;
    this.sheets = [sheet('warden', { meta }), sheet('warden_p2', { meta })];
    this.sh = this.sheets[0]; this.anim = new Anim(this.sh, 'idle', true); this.state = 'dormant';
    this.stanceMax = 360; this.critRange = 70; this.cool = 1; this.last = null; this.speed = 1; this.face = -1; this.hidden = false; this.stormT = 4; this.waveT = 6;
    this.chain = 0;
  }
  get L() { return 3 * TILE + 34; }            // the fog wall stands at column 2
  get R() { return 47 * TILE - 40; }           // the east wall is column 47 (room for the staff and antlers)
  get fd() { return (P.x - this.x) * this.face; }
  pt(key) { const m = this.sh.meta, f = m && m.points && m.points[this.anim.tag]; const q = f && f[Math.min(this.anim.i, f.length - 1)]; return q && q[key] ? metaPoint(this.sh, this, q[key]) : { x: this.x, y: this.y - 100 }; }
  setA(tag, loop = false, speed = this.speed) { this.anim.set(this.sh.has(tag) ? tag : 'idle', loop, speed); }
  hurtbox() { if (!this.alive || this.hidden || this.state === 'dormant') return null; if (this.state === 'sink' && this.anim.i >= 5) return null; if (this.state === 'rise' && this.anim.i <= 2) return null; const m = this.sh.meta; return m ? metaRect(this.sh, this, m.hurtbox) : rect(this.x - 18, this.y - 110, this.x + 18, this.y); }
  hit(info) { if (this.hidden) return; super.hit(info); }
  canStagger() { return !this.hidden && !['sink', 'rise', 'charge', 'roar'].includes(this.state); }
  activate() { if (this.active || this.cutting) return; super.activate(); if (this.active && !this.cutting) { this.state = 'idle'; this.setA('roar'); tvSfx.bellow(); } }
  critable() { return this.state === 'stagger' && this.anim.i >= 1 && !this.critDone; }
  stagger() { super.stagger(); this.hidden = false; TVR.trails = []; }
  coolFor() { return this.phase === 1 ? rand(0.9, 1.4) : rand(0.5, 0.95); }
  update(dt) {
    this.commonUpdate(dt);
    const an = this.anim; an.update(dt);
    if (!this.active) { if (this.state === 'dormant') { this.face = -1; if (!this.cutting && P.x > 7 * TILE && P.x < 40 * TILE && P.ground && P.state !== 'dead') this.activate(); } return; }
    if (this.introT > 0) { this.introT -= dt; if (an.done) an.hold(); if (this.introT <= 0) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.6; } return; }
    switch (this.state) {
      case 'idle': {
        if (an.tag !== 'idle' && an.done) this.setA('idle', true);
        this.facePlayer(); this.cool -= dt;
        if (P.state === 'dead') break;
        if (this.pendingPhase) { this.enterPhase2(); break; }
        if (this.cool <= 0) this.choose();
        break;
      }
      case 'walk': {
        this.facePlayer(); this.t -= dt; this.cool -= dt;
        this.x = clamp(this.x + this.face * 44 * this.speed * dt, this.L, this.R);
        if (an.changed && an.i % 4 === 1) sfx.step();
        const d = Math.abs(P.x - this.x);
        if (this.t <= 0 || d < 90) { this.state = 'idle'; this.setA('idle', true); this.cool = Math.min(this.cool, 0.2); }
        break;
      }
      case 'attack': this.updateAttack(dt); break;
      case 'cprep': this.updateChargePrep(dt); break;
      case 'charge': this.updateCharge(dt); break;
      case 'cend': if (an.done) this.after('charge'); break;
      case 'sink': this.updateSink(dt); break;
      case 'under': this.updateUnder(dt); break;
      case 'rise': this.updateRise(dt); break;
      case 'roar': if (an.changed && an.i === 3) { tvSfx.bellow(); shake = 10; flashScreen = 0.3; spawnFx(fxOr('tv_burst', 'roar_ring'), this.x + this.face * 20, this.y - 110, 1); } if (an.done) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.5; this.stanceImmune = 0; } break;
      case 'stagger':
        this.t -= dt; if (an.i === an.n - 1 && this.t > 0.3) an.hold();
        if (an.done || this.t <= 0) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.4; }
        break;
      case 'dead':
        if (Math.random() < 0.6) particles.push({ x: this.x + rand(-30, 30), y: this.y - rand(0, 120), vx: rand(-10, 10), vy: -rand(15, 45), life: rand(1, 2), kind: Math.random() < 0.5 ? 'tv_mote' : 'tv_leaf' });
        if (an.done) an.hold();
        break;
    }
    if (this.alive && this.phase === 1 && this.hp <= this.maxHp * 0.5) this.pendingPhase = true;
    if (this.phase === 2 && this.alive && !this.hidden) this.updateForest(dt);
    this.x = clamp(this.x, this.L, this.R);
  }
  // ---------------------------------------------------------------- choice
  choose() {
    const fd = this.fd, d = Math.abs(P.x - this.x), p2 = this.phase === 2;
    let w;
    if (fd < -10 && d < 90) w = { sweep: 1.2, sink: 1.4, erupt: 0.8 };                            // behind him: turn and sweep, or vanish
    else if (d < 110) w = { sweep: 2.4, thrust: 0.8, erupt: 1.0, sink: 0.6, summon: p2 ? 0.9 : 0.4 };
    else if (d < 190) w = { thrust: 2.2, volley: 1.2, erupt: 1.2, charge: 0.9, summon: 0.7, walk: 0.8 };
    else w = { charge: 2.0, volley: 1.6, erupt: 1.0, sink: 1.2, walk: 1.0, summon: 0.6 };
    if (this.last && w[this.last]) w[this.last] *= 0.25;
    const e = Object.entries(w); let r = Math.random() * e.reduce((s, [, v]) => s + v, 0), m = e[0][0];
    for (const [k, v] of e) if ((r -= v) <= 0) { m = k; break; }
    this.last = m; this.chain = 0; this.begin(m);
  }
  begin(m) {
    this.facePlayer(); this.atk = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {};
    if (m === 'walk') { this.state = 'walk'; this.setA('walk', true); this.t = rand(0.8, 1.3); return; }
    if (m === 'charge') { this.state = 'cprep'; this.setA('charge_prep'); return; }
    if (m === 'sink') { this.state = 'sink'; this.setA('sink'); return; }
    this.state = 'attack'; this.setA(m);
  }
  after(m) {
    const p2 = this.phase === 2, maxC = p2 ? 2 : 1;
    if (!this.pendingPhase && this.chain < maxC && Math.random() < (p2 ? 0.55 : 0.3) && P.state !== 'dead') {
      this.chain++; const d = Math.abs(P.x - this.x);
      const next = m === 'sweep' ? (d < 150 ? 'thrust' : 'erupt') : m === 'thrust' ? (d < 110 ? 'sweep' : 'volley') : m === 'charge' ? 'erupt' : m === 'rise' ? (p2 ? 'erupt' : 'sweep') : 'volley';
      this.last = next; return this.begin(next);
    }
    this.chain = 0; this.state = 'idle'; this.setA('idle', true); this.cool = this.coolFor();
  }
  // ---------------------------------------------------------------- tag-driven attacks: sweep / thrust / erupt / volley / summon
  telegraph() {
    const tel = this.sh.meta && this.sh.meta.telegraph && this.sh.meta.telegraph[this.anim.tag];
    if (tel && this.anim.changed && this.anim.i === tel.frame) { const p = metaPoint(this.sh, this, tel.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); tvSfx.spirit(); }
  }
  meleeWindow(tag, dmg, parry) {
    for (const w of metaWindows(this.sh, tag)) if (this.anim.i >= w.active[0] && this.anim.i <= w.active[1]) {
      if (this.anim.changed && this.anim.i === w.active[0]) sfx.bossSwing();
      if (!this.hitIds.has(0) && overlap(metaRect(this.sh, this, w.hit), playerHurtbox()) && hurtPlayer(tvBD(dmg, this), P.x < this.x ? -1 : 1, this.atkId, { parryable: parry, src: this })) this.hitIds.add(0);
    }
  }
  updateAttack(dt) {
    const an = this.anim, a = this.atk, p2 = this.phase === 2;
    this.telegraph();
    if (an.i < 4) this.facePlayer();
    if (a === 'sweep') { this.meleeWindow('sweep', TV_WD.sweep, true); if (an.changed && an.i === 5) { shake = 4; for (let i = 0; i < 12; i++) particles.push({ x: this.x + this.face * rand(20, 100), y: this.floor - rand(0, 4), vx: this.face * rand(60, 160), vy: -rand(10, 60), g: 300, life: 0.5, kind: 'tv_leaf' }); } }
    if (a === 'thrust') {
      if (an.i >= 5 && an.i <= 6) this.x = clamp(this.x + this.face * 170 * dt, this.L, this.R);
      this.meleeWindow('thrust', TV_WD.thrust, true);
    }
    if (a === 'erupt') {
      this.meleeWindow('erupt', TV_WD.erupt * 0.6, false);
      if (an.changed && an.i === 6 && !this.fired.e) {
        this.fired.e = true; shake = 9; sfx.boom(); tvSfx.roots();
        const bp = metaPoint(this.sh, this, this.sh.meta.spawn.erupt.at);
        spawnFx('shockwave', bp.x, this.floor, 1);
        const px = clamp(P.x + P.vx * 0.1, this.L - 10, this.R + 10);
        if (!p2) { tvRootSpike(px, this.floor, 0.18, TV_WD.erupt, this); tvRootSpike(clamp(px + sign(P.x - this.x) * 44, this.L, this.R), this.floor, 0.45, TV_WD.erupt, this); }
        else { for (let k = 0; k < 5; k++) tvRootSpike(clamp(bp.x + this.face * (40 + k * 34), 40, 47 * TILE - 20), this.floor, 0.05 + k * 0.16, TV_WD.erupt, this); tvRootSpike(px, this.floor, 0.5, TV_WD.erupt, this); }
      }
    }
    if (a === 'volley' && an.changed && an.i === 6 && !this.fired.v) {
      this.fired.v = true; const at = metaPoint(this.sh, this, this.sh.meta.spawn.volley.at);
      const base = Math.atan2(P.y - 16 - at.y, P.x - at.x), n = p2 ? 7 : 5;
      for (let k = 0; k < n; k++) tvThorn(at.x, at.y, base + (k - (n - 1) / 2) * 0.13, 230, TV_WD.volley, this, 90);
      sfx.shoot(); tvSfx.spirit(); shake = 3;
      if (p2) setTimeout(() => { if (boss === this && this.alive && !this.hidden) { const b2 = Math.atan2(P.y - 16 - at.y, P.x - at.x); for (let k = 0; k < 4; k++) tvThorn(at.x, at.y, b2 + (k - 1.5) * 0.18, 250, TV_WD.volley, this, 90); } }, 380);
    }
    if (a === 'summon' && an.changed && an.i === 6 && !this.fired.s) {
      this.fired.s = true; flashScreen = 0.2; tvSfx.chant(0.6);
      const n = 2, spots = [];
      const behind = clamp(P.x + (P.x < this.x ? -56 : 56), this.L + 8, this.R - 8);
      spots.push(behind);
      while (spots.length < n) { const x = rand(this.L + 20, this.R - 20); if (Math.abs(x - P.x) > 48 && Math.abs(x - this.x) > 40 && spots.every(s => Math.abs(s - x) > 40)) spots.push(x); }
      for (const x of spots) if (Math.abs(x - this.x) > 30) tvSummonWall(x, this.floor, this, p2 ? 6.5 : 5.5);
    }
    if (an.done) this.after(a);
  }
  // ---------------------------------------------------------------- antler charge
  updateChargePrep(dt) {
    const an = this.anim;
    this.telegraph(); if (an.i < 5) this.facePlayer();
    if (an.changed && an.i >= 3) { sfx.step(); for (let i = 0; i < 6; i++) particles.push({ x: this.x - this.face * rand(10, 30), y: this.floor - 2, vx: -this.face * rand(40, 120), vy: -rand(10, 60), g: 300, life: 0.5, kind: 'rock' }); }
    if (an.done) { this.state = 'charge'; this.setA('charge', true); this.cT = 0; this.goal = this.face > 0 ? Math.min(this.R, P.x + 130) : Math.max(this.L, P.x - 130); tvSfx.bellow(); shake = 5; }
  }
  updateCharge(dt) {
    this.cT += dt;
    const v = 300 * (this.phase === 2 ? 1.12 : 1), nx = this.x + this.face * v * dt;
    if (this.anim.changed && this.anim.i % 2 === 0) { shake = Math.max(shake, 3); sfx.step(); }
    if (Math.random() < 0.8) particles.push({ x: this.x - this.face * rand(10, 40), y: this.floor - rand(0, 4), vx: -this.face * rand(60, 160), vy: -rand(10, 60), g: 300, life: 0.5, kind: Math.random() < 0.5 ? 'rock' : 'tv_leaf' });
    this.meleeWindow('charge', TV_WD.charge, false);
    const done = (this.face > 0 && (nx >= this.goal || nx >= this.R)) || (this.face < 0 && (nx <= this.goal || nx <= this.L)) || this.cT > 1.8;
    this.x = clamp(nx, this.L, this.R);
    if (done) {
      if (this.x <= this.L + 1 || this.x >= this.R - 1) { shake = 10; sfx.boom(); tvSfx.creak(); for (let i = 0; i < 14; i++) particles.push({ x: this.x + this.face * 40, y: this.floor - rand(20, 140), vx: -this.face * rand(20, 80), vy: rand(-40, 40), g: 400, life: 1, kind: i % 2 ? 'rock' : 'tv_leaf' }); }
      this.state = 'cend'; this.setA('charge_end');
      if (this.phase === 2) for (const dd of [-1, 1]) tvRootWave(this.x + dd * 20, this.floor, dd, this, 160);
    }
  }
  // ---------------------------------------------------------------- stepping between trees: sink into the roots, travel under the floor, rise beside you
  updateSink(dt) {
    const an = this.anim;
    if (an.changed && an.i === 2) { tvSfx.roots(); tvSfx.rustle(); }
    if (an.i >= 2 && Math.random() < 0.7) particles.push({ x: this.x + rand(-30, 30), y: this.floor - rand(0, 10), vx: rand(-40, 40), vy: -rand(20, 80), g: 200, life: 0.7, kind: Math.random() < 0.5 ? 'tv_leaf' : 'rock' });
    if (an.done) {
      this.hidden = true; this.state = 'under'; this.t = this.phase === 2 ? 0.75 : 0.95;
      const side = P.x > (this.L + this.R) / 2 ? -1 : 1;
      this.dest = clamp(P.x + side * rand(46, 70), this.L + 10, this.R - 10);
      if (Math.abs(this.dest - P.x) < 40) this.dest = clamp(P.x - side * 60, this.L + 10, this.R - 10);
      TVR.trails = [{ x: this.x, floor: this.floor }];
      spawnFx(fxOr('tv_burst', 'dust'), this.x, this.floor - 10, 1);
    }
  }
  updateUnder(dt) {
    this.t -= dt;
    const tr = TVR.trails[0];
    if (tr) { tr.x = approach(tr.x, this.dest, 260 * dt); if (Math.random() < 0.9) particles.push({ x: tr.x + rand(-8, 8), y: this.floor - 2, vx: rand(-30, 30), vy: -rand(20, 70), g: 300, life: 0.5, kind: Math.random() < 0.6 ? 'rock' : 'tv_leaf' }); if (Math.random() < 0.3) shake = Math.max(shake, 1.5); }
    if (this.t <= 0 && (!tr || Math.abs(tr.x - this.dest) < 2)) {
      this.x = this.dest; TVR.trails = []; this.hidden = false; this.facePlayer();
      this.state = 'rise'; this.setA('rise'); this.hitIds = new Set(); this.atkId = ++hazardId; tvSfx.roots(); shake = 6;
      spawnFx(fxOr('tv_burst', 'dust'), this.x, this.floor - 10, 1);
    }
  }
  updateRise(dt) {
    const an = this.anim;
    this.telegraph();
    if (an.i <= 4) this.facePlayer();
    this.meleeWindow('rise', TV_WD.rise, true);
    if (an.done) this.after('rise');
  }
  // ---------------------------------------------------------------- phase 2: the forest wakes
  enterPhase2() {
    this.phase = 2; this.speed = 1.18; this.pendingPhase = false; this.stance = 0; this.stanceImmune = 3;
    if (this.sheets[1].ok) { const a = this.anim; this.sh = this.sheets[1]; this.anim = new Anim(this.sh, a.tag, a.loop, a.speed); }
    this.state = 'roar'; this.setA('roar', false, 1); this.facePlayer(); tvClearWalls();
    TVR.wakeT = 0; bossPhase2Scene(this);
  }
  updateForest(dt) {
    TVR.wakeT = (TVR.wakeT || 0) + dt;
    this.stormT -= dt; this.waveT -= dt;
    if (this.stormT <= 0 && ['idle', 'walk', 'attack'].includes(this.state)) {   // spirit-light storm: orbs on marked spots, one near you
      this.stormT = rand(4.2, 6.0); const n = irand(3, 5);
      tvOrb(clamp(P.x + P.vx * 0.3, this.L - 10, this.R + 10), this.floor, 0.8, this);
      for (let k = 1; k < n; k++) tvOrb(rand(this.L, this.R), this.floor, 0.8 + k * 0.22, this);
      tvSfx.spirit();
    }
    if (this.waveT <= 0 && this.state === 'idle') {                                  // roots rolling across the grove floor (jump them)
      this.waveT = rand(6.5, 9); const dir = P.x > this.x ? 1 : -1;
      tvRootWave(dir > 0 ? this.L - 12 : this.R + 12, this.floor, dir, this, 140); tvSfx.roots();
    }
  }
  die() {
    this.state = 'dead'; this.hidden = false; this.setA('death', false, 1); tvClearBossFx();
    shake = 12; hitstop = 0.3; slowmo = 1.6; flashScreen = 0.5; tvSfx.bellow(); sfx.felled();
    victoryBanner = { text: 'THE WARDEN SLEEPS', t: 0 };
    setTimeout(() => { if (room && room.id === 'TV8') toast('The grove falls still. Somewhere, a root lets go of the way back.', 4); }, 3200);
    this.rewards();
  }
  draw() {
    if (this.hidden || this.state === 'dormant' && !this.sh.ok) return;
    const opt = this.flash > 0 ? { flash: this.flash * 0.6, flashColor: '#dff5e4' } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' } : {};
    if (this.state === 'cprep' && this.anim.i >= 4) { opt.flash = Math.max(opt.flash || 0, 0.1 + 0.08 * Math.sin(time * 30)); opt.flashColor = opt.flashColor || '#b4ffd0'; }
    if (!this.sh.ok) { g.fillStyle = '#2a2018'; g.fillRect(Math.round(this.x - 16), Math.round(this.y - 120), 32, 120); return; }
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    if (this.critable()) { g.fillStyle = '#ffd070'; const y = Math.round(this.y - 130 + Math.sin(time * 8) * 1.5); g.fillRect(Math.round(this.x) - 1, y, 3, 3); g.fillRect(Math.round(this.x), y - 1, 1, 5); g.fillRect(Math.round(this.x) - 2, y + 1, 5, 1); }
    if (this.alive) {
      const e = this.pt('eye'), t = this.pt('tip'), h = this.pt('heart');
      addLight(this.x, this.y - 70, 130, '150,210,180', 0.42); addLight(e.x, e.y, this.phase === 2 ? 30 : 20, '120,255,170', 0.9); addLight(t.x, t.y, 40, '120,255,170', 0.8); addLight(h.x, h.y, this.phase === 2 ? 60 : 36, '120,255,170', 0.6);
    }
    if (this.state === 'cprep' && this.anim.i >= 4) { const x0 = this.x + this.face * 60; for (let s = 0; s < 160; s += 6) { g.fillStyle = `rgba(150,255,190,${0.3 * (1 - s / 160)})`; g.fillRect(Math.round(x0 + this.face * s), this.floor - 2, 4, 1); } }
  }
}
BOSS_SPAWN.warden = (cx, fy) => sheet('warden').ok ? new TvWarden(cx, fy) : null;
BOSS_CUTS.warden = b => [
  act(() => { b.face = -1; b.anim.set('idle', true); b.anim.speed = 0.2; }),
  { pan: { x: b.x - 40, y: b.floor - 70 }, dur: 1.4 },
  say('', 'Among the first trees of the Root, something stands that is not a tree.'),
  act(() => { b.anim.speed = 1; holdAnim(b, 'roar'); tvSfx.creak(); }), wait(0.5),
  act(() => { tvSfx.bellow(); shake = 10; flashScreen = 0.3; spawnFx(fxOr('tv_burst', 'roar_ring'), b.x - 20, b.y - 110, 1); for (let i = 0; i < 30; i++) particles.push({ x: b.x + rand(-60, 60), y: b.floor - rand(40, 150), vx: rand(-20, 20), vy: rand(20, 60), life: 2, kind: 'tv_leaf' }); }), wait(1.1),
  say('The Antlered Warden', 'Leave the way you came… or not at all.'),
];
PHASE2_LINES.warden = ['', 'The forest wakes. Every root in the grove turns toward you.'];
// phase 2 arena: roots crawling across the walls and floor, a green wash
function tvDrawBossArena() {
  const b = boss;
  if (!b || b.kind !== 'warden' || !b.active || b.phase < 2 || !b.alive) return;
  const k = Math.min(1, (TVR.wakeT || 0) / 2);
  g.fillStyle = `rgba(40,120,70,${0.05 * k})`; g.fillRect(cam.x, cam.y, W, H);
  for (let i = 0; i < 12; i++) {
    const x0 = (i * 67) % room.pw, len = 30 + (i % 4) * 14;
    for (let s = 0; s < len * k; s += 2) { const x = x0 + s, y = b.floor - 1 - Math.abs(Math.sin(s * 0.12 + i + time * 0.8)) * 5; g.fillStyle = s % 6 ? '#2a2018' : '#3e7440'; g.fillRect(Math.round(x), Math.round(y), 2, 1); }
  }
}

// ---- debug helpers for tests
if (window.__game) Object.assign(window.__game, { TVR, tileAt: (x, y) => tileAt(x, y), tvRoom: () => room, tvSpawnWall: x => tvSummonWall(x, boss ? boss.floor : P.y, boss) });
