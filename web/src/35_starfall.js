// ------------------------------------------------------------------ THE STARFALL CRATER (agent SF) + Moonstep (global triple jump)
// Where a star fell and killed the old gods: black glass plains, floating shards, a shattered observatory, constellations
// overhead. Rooms SF1–SF9 (tools/regions/75_starfall.py), entered from X4 (a Cinder Slam wakes the fallen star's shard stair).
// Tiles: '+' starlight (low gravity inside), '?' star-glass (solid, too smooth to cling to).
// Enemies: sf_pilgrim, sf_golem (shatters into shards), sf_wisp (comet). Bosses: the Orrery Sentinel (SF5), Astrel (SF7).
// Every top-level name is prefixed sf/SF (all region files share one scope). Art: art/gen_starfall*.py.

// ================================================================== biome
Object.assign(AREAS, { starfall: { name: 'The Starfall Crater', ambient: 0.3, amb: 'mote', tint: '#05060f', map: '#3c4a78' } });
Object.assign(SCALES, { starfall: [0, 2, 4, 7, 11] });   // lydian-ish bells: cold, bright, uneasy
Object.assign(ROOTS, { starfall: 61.74 });
Object.assign(PCOL, { star: '215,232,255', nebula: '170,130,255', glass: '140,170,230' });
const SF_T_STAR = 60, SF_T_GLASS = 61;
const sfIn = () => room && room.def.biome === 'starfall';
const sfSfx = {
  chime: (p = 1) => { tone(1318 * p, 0.9, 0.06, 'sine', 1); tone(1976 * p, 0.7, 0.04, 'triangle', 1, 0.05); tone(2637 * p, 0.5, 0.03, 'sine', 1, 0.1); },
  glass: () => { noise(0.3, 5200, 2, 0.22, 'highpass', 0.6); tone(2400, 0.25, 0.05, 'triangle', 0.6); tone(3100, 0.18, 0.03, 'sine', 0.7, 0.04); },
  shatter: () => { noise(0.6, 4200, 1.2, 0.35, 'highpass', 0.4); noise(0.4, 900, 0.7, 0.3, 'bandpass', 0.5); tone(1800, 0.3, 0.05, 'triangle', 0.4); },
  hum: () => { tone(98, 1.4, 0.12, 'sine', 1.02); tone(147, 1.2, 0.06, 'triangle', 1.01); },
  fall: () => { tone(2200, 0.7, 0.05, 'sine', 0.25); noise(0.7, 3000, 0.9, 0.18, 'bandpass', 0.3); },
  boom: () => { noise(0.8, 220, 0.8, 0.7, 'lowpass', 0.4); tone(55, 0.8, 0.35, 'sine', 0.5); tone(1400, 0.5, 0.04, 'triangle', 0.5); },
  beam: () => { tone(880, 1.0, 0.05, 'sawtooth', 1.3); noise(1.0, 2600, 1.4, 0.15, 'bandpass', 1.5); },
  well: () => { tone(70, 1.6, 0.18, 'sine', 0.6); noise(1.4, 400, 0.8, 0.2, 'lowpass', 0.5); },
  whoosh: () => noise(0.25, 2800, 1.2, 0.2, 'bandpass', 0.35),
};
Object.assign(ITEMS, {
  moonstep: { name: 'Moonstep', icon: 'i_moonstep', sheet: 'ui_icons5', desc: 'A splinter of the fallen star, light as a held breath. You can jump once more in midair — a third jump, on starlight.' },
});
Object.assign(LORE, {
  sf_shrine: ['A slab of black glass. Something wrote on it while it was still molten:', '“We asked the sky for a god that would not rot. It sent one down. It did not ask which gods it should keep.”'],
  sf_astrel: ['A single sword-cut in the crater glass, perfectly straight, a hundred paces long:', '“She fell so that nothing else would. Then she stayed, so that nothing would climb back up.”'],
  sf_lastlight: ['Star-glass, still faintly warm. The words are written backwards, as if from the other side:', '“The old gods were a garden. I was the frost. Forgive me — I only meant to keep the dark from growing.” — A.'],
  sf_obs: ['A brass plate on the great telescope:', '“Nine of us watched the sky every night for four hundred years. On the last night, the sky watched back.”'],
});

// ================================================================== tiles
// '+' starlight: open air with a slow, rising shimmer; inside it you fall gently and leap higher
registerTile('+', SF_T_STAR, { draw(ctx, sh, px, py, x, y, R, back) {
  back.fillStyle = 'rgba(120,150,255,0.05)'; back.fillRect(px, py, 16, 16);
  if (hash2(x * 3, y * 7) < 0.18) { back.fillStyle = 'rgba(220,235,255,0.45)'; back.fillRect(px + Math.floor(hash2(x, y) * 14) + 1, py + Math.floor(hash2(y, x) * 14) + 1, 1, 1); }
} });
// '?' star-glass: solid, glossy, too smooth to cling to
function sfMask(R, x, y) {
  const air = (xx, yy) => !isSolidT(tileAtR(R, xx, yy));
  return (air(x, y - 1) ? 1 : 0) | (air(x + 1, y) ? 2 : 0) | (air(x, y + 1) ? 4 : 0) | (air(x - 1, y) ? 8 : 0);
}
registerTile('?', SF_T_GLASS, { solid: true, draw(ctx, sh, px, py, x, y, R) {
  const gs = sheet('sf_glass');
  const m = sfMask(R, x, y);
  if (gs.ok) drawTile(ctx, gs, m + (hash2(x + 3, y * 5) < 0.3 ? 16 : 0), px, py);
  else {
    drawTile(ctx, sh, m, px, py);
    ctx.fillStyle = 'rgba(120,160,255,0.22)'; ctx.fillRect(px, py, 16, 16);
    ctx.fillStyle = 'rgba(220,235,255,0.5)'; for (let i = 0; i < 16; i += 5) ctx.fillRect(px + i, py + 15 - i, 2, 1);
  }
} });

// ================================================================== Moonstep: a third jump, anywhere
const SFM = { armed: false, used: false, trail: 0 };
function sfMoonstepFx() {
  spawnFx(fxOr('sf_moonstep', 'dust'), P.x, P.y + 2, P.face, null, { bottom: true });
  sfSfx.chime(1 + rand(-0.03, 0.03));
  for (let i = 0; i < 16; i++) { const a = (i / 16) * Math.PI * 2; particles.push({ x: P.x + Math.cos(a) * 6, y: P.y + Math.sin(a) * 2, vx: Math.cos(a) * rand(40, 80), vy: Math.sin(a) * rand(10, 30) + 20, life: rand(0.35, 0.6), kind: i % 3 ? 'star' : 'nebula' }); }
  SFM.trail = 0.45;
}
HOOKS.update.push(dt => {
  if (!P || !SAVE || !SAVE.items.moonstep) return;
  if (P.ground || P.state === 'dead') { SFM.armed = false; SFM.used = false; return; }
  if (SFM.armed && P.airJumps === 0) {   // the engine just spent our air jump: this was the Moonstep
    SFM.armed = false; SFM.used = true;
    if (P.vy < -150) { P.vy = -JUMP_V * 0.95; sfMoonstepFx(); }
  }
  if (!SFM.armed && !SFM.used && P.airJumps === 0 && P.state !== 'hook') { SFM.armed = true; P.airJumps = 1; }
  if (SFM.trail > 0) {
    SFM.trail -= dt;
    if (Math.random() < 0.8) particles.push({ x: P.x + rand(-4, 4), y: P.y - rand(0, 22), vx: rand(-8, 8), vy: rand(10, 30), life: 0.45, kind: Math.random() < 0.6 ? 'star' : 'nebula' });
    addLight(P.x, P.y - 12, 36, '190,210,255', 0.6);
  }
});
HOOKS.render.push(() => {   // a faint starlit afterimage while the third jump carries you
  if (!P || SFM.trail <= 0) return;
  drawSprite(sheet('player'), P.anim.frame, P.x, P.y + 4, P.face, { alpha: SFM.trail * 0.6, flash: 1, flashColor: '#bcd4ff' });
});

// ================================================================== starlight gravity + star-glass (tile keyed, any room)
const SF_LOWG = 0.4;   // fraction of gravity cancelled inside starlight
function sfInStar(x, y) { return tileAt(Math.floor(x / TILE), Math.floor(y / TILE)) === SF_T_STAR; }
HOOKS.update.push(dt => {
  if (!P || !room || P.state === 'dead') return;
  // starlight: gentler fall, higher leaps
  if (!P.ground && !['hook', 'slam', 'wall', 'glide', 'rest', 'plunge'].includes(P.state) && !(P.state === 'roll' && P.airRoll) && sfInStar(P.x, P.y - 13)) {
    P.vy -= (P.vy < 0 ? GRAV_UP : GRAV_DN) * SF_LOWG * dt;
    if (P.vy > 170) P.vy = approach(P.vy, 170, 900 * dt);
    if (Math.random() < 0.25) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(0, 24), vx: 0, vy: -rand(8, 20), life: 0.6, kind: 'star' });
  }
  // star-glass: no purchase for claws
  if (P.state === 'wall' && P.wallDir) {
    const tx = Math.floor((P.x + P.wallDir * (P.w / 2 + 1)) / TILE);
    if (tileAt(tx, Math.floor((P.y - 8) / TILE)) === SF_T_GLASS || tileAt(tx, Math.floor((P.y - 20) / TILE)) === SF_T_GLASS) {
      P.wallDir = 0; setP('air', 'jump_fall', false);
      if (!SAVE.hints.sfglass) { SAVE.hints.sfglass = 1; toast('The star-glass is too smooth to cling to.', 3); }
      if (Math.random() < 0.3) particles.push({ x: P.x + rand(-4, 4), y: P.y - rand(4, 20), vx: 0, vy: rand(-10, 10), life: 0.3, kind: 'glass' });
    }
  }
});

// ================================================================== the sky: nebula + constellations over the parallax
// constellations in sky units (x 0..1 across a 512-wide band, y px from the top), lines between star indices
const SF_CONST = {
  hunter: { name: 'The Hunter', stars: [[0.10, 30], [0.14, 44], [0.12, 62], [0.19, 58], [0.23, 40], [0.17, 78], [0.08, 80], [0.26, 24], [0.29, 52]],
    lines: [[0, 1], [1, 2], [1, 3], [3, 4], [2, 5], [2, 6], [4, 7], [4, 8], [7, 8]] },
  serpent: { name: 'The Serpent', stars: [[0.40, 70], [0.44, 58], [0.49, 62], [0.53, 50], [0.57, 36], [0.62, 40], [0.66, 30], [0.70, 34], [0.73, 26]],
    lines: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8]] },
  crown: { name: 'The Crown', stars: [[0.80, 60], [0.83, 44], [0.86, 52], [0.89, 38], [0.92, 52], [0.95, 44], [0.98, 60]],
    lines: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [0, 6]] },
};
const SF_SKY_STARS = (() => { const a = []; for (let i = 0; i < 90; i++) a.push([hash2(i, 11), hash2(i, 13) * 150, hash2(i, 17)]); return a; })();
const SFSKY = { focus: null, k: 0, rot: 0, flare: 0 };   // the arena drives focus/flare; rot = slow sky drift
function sfDrawConstellation(c, ox, oy, w, alpha, scale = 1, bright = 0) {
  const P2 = c.stars.map(([u, v]) => [ox + u * w, oy + v * scale]);
  g.globalCompositeOperation = 'lighter';
  g.strokeStyle = `rgba(150,180,255,${0.22 * alpha + 0.4 * bright})`; g.lineWidth = 1;
  g.beginPath();
  for (const [a, b] of c.lines) { g.moveTo(Math.round(P2[a][0]) + 0.5, Math.round(P2[a][1]) + 0.5); g.lineTo(Math.round(P2[b][0]) + 0.5, Math.round(P2[b][1]) + 0.5); }
  g.stroke();
  P2.forEach(([x, y], i) => {
    const tw = 0.6 + 0.4 * Math.sin(time * (1.3 + (i % 3) * 0.7) + i * 1.7);
    g.fillStyle = `rgba(230,240,255,${Math.min(1, (0.55 * alpha + bright) * tw)})`;
    g.fillRect(Math.round(x), Math.round(y), 1, 1);
    if (bright > 0.2 || i % 3 === 0) { g.fillStyle = `rgba(190,210,255,${0.35 * (alpha * 0.6 + bright) * tw})`; g.fillRect(Math.round(x) - 1, Math.round(y), 3, 1); g.fillRect(Math.round(x), Math.round(y) - 1, 1, 3); }
  });
  g.globalCompositeOperation = 'source-over';
}
function sfLayer(sh, fac, vfac) {
  if (!sh.ok) return;
  const t = sh.tag('loop'), f = sh.frames[t.from + (Math.floor(time * 6) % (t.to - t.from + 1))];
  const ox = -((cam.x * fac) % f.w + f.w) % f.w, oy = Math.round(clamp(-cam.y * vfac, -(f.h - H) - 20, 20));
  for (let x = Math.round(ox); x < W; x += f.w) g.drawImage(sh.img, f.x, f.y, f.w, f.h, x, oy + (H - f.h), f.w, f.h);
}
const sfParallaxBase = drawParallax;
drawParallax = function () {
  if (!room || room.def.biome !== 'starfall') return sfParallaxBase();
  g.fillStyle = AREAS.starfall.tint; g.fillRect(0, 0, W, H);
  sfLayer(sheet('bg_starfall_far'), 0.06, 0.02);
  // twinkling field + constellations drift with the sky
  const drift = SFSKY.rot, ox = -((cam.x * 0.04 + drift) % 512 + 512) % 512, oy = Math.round(clamp(-cam.y * 0.015, -30, 10));
  g.globalCompositeOperation = 'lighter';
  for (const [u, v, s] of SF_SKY_STARS) {
    const tw = 0.5 + 0.5 * Math.sin(time * (0.8 + s * 2) + s * 40);
    g.fillStyle = `rgba(210,225,255,${0.25 + 0.5 * tw * s})`;
    for (const bx of [ox, ox + 512]) { const x = Math.round(bx + u * 512); if (x >= 0 && x < W) g.fillRect(x, Math.round(oy + v), 1, 1); }
  }
  g.globalCompositeOperation = 'source-over';
  for (const [k, c] of Object.entries(SF_CONST)) {
    const foc = SFSKY.focus === k ? SFSKY.k : 0, dim = SFSKY.focus && SFSKY.focus !== k ? 0.45 : 1;
    for (const bx of [ox, ox + 512, ox - 512]) sfDrawConstellation(c, bx, oy, 512, 0.7 * dim, 1, foc * (0.6 + 0.4 * SFSKY.flare));
  }
  sfLayer(sheet('bg_starfall_mid'), 0.3, 0.08);
};

// starlight columns + rising motes over '+' cells
const SFR = { roomObj: null, stars: [], props: [] };
HOOKS.enter.push(def => {
  SFR.roomObj = room; SFR.stars = [];
  for (let y = 0; y < def.h; y++) for (let x = 0; x < def.w; x++) if (def.map[y][x] === '+') SFR.stars.push([x, y]);
  if (def.biome !== 'starfall') return;
  if (def.id === 'SF1' && !SAVE.hints.sf1) { SAVE.hints.sf1 = 1; setTimeout(() => { if (room && room.id === 'SF1') toast('Starlight pools here. Inside it you fall softly and leap higher.', 4); }, 1200); }
});
HOOKS.update.push(dt => {
  if (!room || !SFR.stars.length) return;
  for (let k = 0; k < 3; k++) {
    const [x, y] = SFR.stars[irand(0, SFR.stars.length - 1)];
    const px = x * TILE + rand(0, 16), py = y * TILE + rand(0, 16);
    if (px < cam.x - 10 || px > cam.x + W + 10 || py < cam.y - 10 || py > cam.y + H + 10) continue;
    particles.push({ x: px, y: py, vx: rand(-2, 2), vy: -rand(6, 16), life: rand(1, 2), kind: Math.random() < 0.8 ? 'star' : 'nebula' });
  }
});

// ================================================================== decor props
const SF_DECO = { shard: ['sf_shard', 'loop', 1], arch: ['sf_arch', 'idle', 0], godbone: ['sf_godbone', 'idle', 0], spire: ['sf_spire', 'loop', 0],
  idol: ['sf_idol', 'idle', 0], telescope: ['sf_telescope', 'idle', 0], lens: ['sf_lens', 'loop', 0], orrering: ['sf_orrering', 'loop', 0] };
SPAWNS.sf_prop = (s, c) => {
  const d = SF_DECO[s.kind]; if (!d) return;
  const sh = sheet(d[0]);
  const p = { type: 'sf_' + s.kind, x: c.cx, y: c.fy, face: s.face || 1, sh, anim: new Anim(sh, sh.has(d[1]) ? d[1] : Object.keys(sh.tags)[0] || d[1], true), float: d[2], seed: rand(0, 6) };
  p.anim.t = rand(0, 500);
  p.update = () => {
    if (s.kind === 'lens') addLight(p.x, p.y - 30, 48, '170,200,255', 0.8);
    else if (s.kind === 'spire') addLight(p.x, p.y - 18, 34, '150,180,255', 0.55);
    else if (s.kind === 'shard') addLight(p.x, p.y - 10 + Math.sin(time + p.seed) * 3, 26, '170,190,255', 0.4);
    else if (s.kind === 'telescope') addLight(p.x + 10, p.y - 40, 30, '200,220,255', 0.4);
  };
  p.draw = () => {
    if (!sh.ok) return;
    const bob = p.float ? Math.round(Math.sin(time * 0.9 + p.seed) * 3) : 0;
    drawSprite(sh, p.anim.frame, p.x, p.y + bob, p.face, { bottom: true });
  };
  if (s.kind === 'telescope') { p.interact = () => readGrave('sf_obs'); p.prompt = () => 'Read'; }
  props.push(p);
};

// ================================================================== X4: the fallen star under the glass, and its shard stair
const SF_STAIR = [[8, 6, 8], [5, 2, 4], [2, 6, 8]];   // X4 rows / col ranges, bottom to top
const SFX4 = { cairn: null, prev: null, rise: 0, hint: 0 };
const sfStairUp = () => !!SAVE.flags['sf:stair'];
SPAWNS.sf_cairn = (s, c) => {
  const sh = sheet('sf_cairn');
  const p = { type: 'sf_cairn', x: c.cx, y: c.fy, face: 1, sh, anim: new Anim(sh, sfStairUp() ? 'open' : 'idle', true) };
  p.update = () => {
    const up = sfStairUp();
    addLight(p.x, p.y - 8, up ? 60 : 30 + 6 * Math.sin(time * 2), '170,200,255', up ? 0.9 : 0.55);
    if (Math.random() < (up ? 0.3 : 0.06)) particles.push({ x: p.x + rand(-14, 14), y: p.y - rand(2, 10), vx: 0, vy: -rand(8, 24), life: rand(0.6, 1.2), kind: 'star' });
    if (p.anim.tag === 'crack' && p.anim.done) p.anim.set('open', true);
  };
  p.draw = () => { if (sh.ok) drawSprite(sh, p.anim.frame, p.x, p.y, 1, { bottom: true }); else { g.fillStyle = '#1a1c2e'; g.fillRect(Math.round(p.x) - 14, Math.round(p.y) - 8, 28, 8); g.fillStyle = '#bcd4ff'; g.fillRect(Math.round(p.x) - 2, Math.round(p.y) - 6, 4, 3); } };
  props.push(p); SFX4.cairn = p; SFX4.rise = sfStairUp() ? 1 : 0;
  // until the star wakes, the night presses down over the shrine: nothing climbs out of X4's sky
  room.dyn.push({ x0: 0, x1: room.pw, y0: -96, y1: 0, on: () => !sfStairUp(), sfCeil: true });
  SF_STAIR.forEach(([row, c0, c1], i) => {
    const y0 = row * TILE, pl = { x0: c0 * TILE, x1: (c1 + 1) * TILE, y0, y1: y0 + 6, oneway: true, on: () => sfStairUp() && SFX4.rise >= 1 && P.drop <= 0 && P.y <= y0 + 0.5 };
    room.dyn.push(pl);
    const ssh = sheet('sf_stair');
    props.push({ type: 'sf_stair', x: (pl.x0 + pl.x1) / 2, y: y0, face: 1, sh: ssh, anim: new Anim(ssh, 'loop', true), i,
      update() { if (sfStairUp()) addLight(this.x, this.y + 2, 30, '170,200,255', 0.5 * Math.min(1, SFX4.rise * 3 - i)); },
      draw() {
        if (!sfStairUp()) return;
        const k = clamp(SFX4.rise * 3 - i, 0, 1); if (k <= 0) return;
        const e = 1 - Math.pow(1 - k, 3), x = lerp(p.x, this.x, e), y = lerp(p.y - 6, this.y, e) + (k >= 1 ? Math.round(Math.sin(time * 1.3 + i) * 0.6) : 0);
        if (ssh.ok) drawSprite(ssh, this.anim.frame, x, y + 8, 1, { bottom: true, alpha: 0.4 + 0.6 * e });
        else { g.fillStyle = '#2a3056'; g.fillRect(Math.round(x) - 24, Math.round(y), 48, 5); g.fillStyle = '#bcd4ff'; g.fillRect(Math.round(x) - 24, Math.round(y), 48, 1); }
      } });
  });
};
function sfWakeStair() {
  SAVE.flags['sf:stair'] = 1; saveGame(); SFX4.rise = 0;
  const p = SFX4.cairn; if (p) p.anim.set('crack', false);
  shake = 9; flashScreen = 0.5; sfSfx.shatter(); sfSfx.hum(); setTimeout(() => sfSfx.chime(0.75), 400);
  if (p) for (let i = 0; i < 40; i++) particles.push({ x: p.x + rand(-16, 16), y: p.y - rand(0, 10), vx: rand(-90, 90), vy: -rand(40, 180), g: 200, life: rand(0.6, 1.4), kind: i % 2 ? 'glass' : 'star' });
  toast('The glass breaks. The fallen star wakes — its shards climb toward the sky.', 4.5);
}
HOOKS.update.push(dt => {
  if (!room || room.id !== 'X4' || !SFX4.cairn || !props.includes(SFX4.cairn)) { SFX4.prev = P ? P.state : null; return; }
  const p = SFX4.cairn, near = Math.abs(P.x - p.x) < 20;
  if (!sfStairUp()) {
    if (SFX4.prev === 'slam' && P.state !== 'slam' && near && P.ground) sfWakeStair();
    if (near && P.ground && (SFX4.hint -= dt) <= 0) { SFX4.hint = 12; sfSfx.hum(); toast(SAVE.items.slam ? 'The glass hums beneath your feet. Something below wants to be struck — hard, from above.' : 'The glass hums beneath your feet. A star lies under it, sealed in.', 3.6); }
  } else if (SFX4.rise < 1) { SFX4.rise = Math.min(1, SFX4.rise + dt * 0.8); if (Math.random() < 0.5) particles.push({ x: p.x + rand(-10, 10), y: p.y - rand(0, 40), vx: 0, vy: -rand(40, 90), life: 0.6, kind: 'star' }); }
  SFX4.prev = P.state;
});

// ================================================================== enemies
Object.assign(ENEMY, {
  sf_pilgrim: { hp: 150, cinders: 170, speed: 30, aggro: 170, range: 54, poise: 25, stance: 90, dmg: { attack: 40 }, cool: [0.9, 1.7], lunge: { attack: 90 } },
  sf_golem: { hp: 520, cinders: 380, speed: 20, aggro: 150, range: 60, poise: 999, stance: 240, dmg: { smash: 58 }, cool: [1.3, 2.1], elite: true, lunge: { smash: 30 } },
  sf_wisp: { hp: 70, cinders: 80, speed: 62, aggro: 190, range: 110, poise: 10, stance: 30, dmg: { dive: 30 }, cool: [1.4, 2.4], flying: true },
});
Object.assign(ATTACK_TAGS, { sf_pilgrim: ['attack'], sf_golem: ['smash'], sf_wisp: ['dive'] });
function sfShard(x, y, vx, vy, dmg) {
  projectiles.push({ owner: 'enemy', kind: 'sf_shard', x, y, vx, vy, g: 380, dmg: dmg * NGP.dmg, life: 1.6, r: 3, t: 0, id: ++hazardId, sh: 'fx_sf_shard' });
}
ENEMY_CLASSES.sf_golem = class extends Enemy {
  updateAttack(dt) {
    const an = this.anim, w = metaWindows(this.sh, 'smash')[0];
    if (w && an.changed && an.i === w.active[0]) {
      shake = Math.max(shake, 5); sfSfx.glass(); const q = metaRect(this.sh, this, w.hit), px = this.face > 0 ? q.x1 - 8 : q.x0 + 8;
      spawnFx('shockwave', px, this.y, 1); for (let i = 0; i < 10; i++) particles.push({ x: px + rand(-10, 10), y: this.y - 2, vx: rand(-80, 80), vy: -rand(30, 120), g: 400, life: 0.6, kind: 'glass' });
    }
    super.updateAttack(dt);
  }
  die(info) {
    super.die(info);
    sfSfx.shatter(); shake = Math.max(shake, 6);
    const n = 7; for (let k = 0; k < n; k++) { const a = -Math.PI / 2 + (k - (n - 1) / 2) * 0.32; sfShard(this.x, this.y - 26, Math.cos(a) * 170, Math.sin(a) * 220, this.cfg.dmg.smash * 0.45); }
    for (let i = 0; i < 30; i++) particles.push({ x: this.x + rand(-14, 14), y: this.y - rand(0, 44), vx: rand(-100, 100), vy: -rand(20, 150), g: 380, life: rand(0.5, 1.1), kind: i % 3 ? 'glass' : 'star' });
  }
  draw() { super.draw(); if (this.alive) addLight(this.x, this.y - 26, 52, '150,180,255', 0.7); }
};
ENEMY_CLASSES.sf_pilgrim = class extends Enemy {
  draw() { super.draw(); if (this.alive) { addLight(this.x + this.face * 10, this.y - 34, 44, '200,215,255', 0.8); addLight(this.x, this.y - 18, 34, '150,170,230', 0.45); } }
};

// ================================================================== shared boss helpers
// a sheet mux: tags live on several strips (astrel / astrel_b / astrel_c, and astrel2* in phase 2); same Anim interface
class SfAnim {
  constructor(tagSheet) { this.ts = tagSheet; this.a = null; this.sheet = null; }
  set(tag, loop = true, speed = 1) {
    if (!(tag in this.ts.map)) tag = this.ts.fallback;
    const s = this.ts.sheetFor(tag);
    if (!this.a || this.sheet !== s) { this.sheet = s; this.a = new Anim(s, tag, loop, speed); } else this.a.set(tag, loop, speed);
    return this;
  }
  update(dt) { this.a.update(dt); }
  hold() { this.a.hold(); }
  ms(i) { return this.a.ms(i); }
  total() { return this.a.total(); }
  get frame() { return this.a.frame; } get tag() { return this.a.tag; } get n() { return this.a.n; }
  get i() { return this.a.i; } set i(v) { this.a.i = v; }
  get t() { return this.a.t; } set t(v) { this.a.t = v; }
  get done() { return this.a.done; } set done(v) { this.a.done = v; }
  get changed() { return this.a.changed; } set changed(v) { this.a.changed = v; }
  get speed() { return this.a.speed; } set speed(v) { this.a.speed = v; }
}
const sfDmg = (d, b) => BOSS_DMG * d * NGP.dmg * (b && b.phase >= 3 ? 1.25 : b && b.phase === 2 ? 1.17 : 1);
function sfMark(x, y, life, w = 16, col = '190,210,255') { SFA.marks.push({ x, y, life, max: life, w, col }); }
// a star falls onto (x, floor) after `delay`; marked on the ground first
function sfFallingStar(x, floor, delay, dmg, b) {
  sfMark(x, floor, delay + 0.05, 22);
  const h = { x, y: floor, w: 26, h: 34, dmg: sfDmg(dmg, b), id: ++hazardId, life: delay + 0.6, t: 0, sfStar: true, delay0: delay,
    active: h => h.t > h.delay0 && h.t < h.delay0 + 0.12,
    update: h => { if (h.t > h.delay0 && !h.boom) { h.boom = true; spawnFx('sf_burst', x, floor, 1, null, { bottom: true }); sfSfx.boom(); shake = Math.max(shake, 3); for (let i = 0; i < 10; i++) particles.push({ x: x + rand(-8, 8), y: floor - 2, vx: rand(-90, 90), vy: -rand(40, 150), g: 380, life: 0.6, kind: i % 2 ? 'star' : 'glass' }); } } };
  hazards.push(h);
  setTimeout(() => sfSfx.fall(), Math.max(0, delay - 0.45) * 1000);
  return h;
}
// a starlight wave running along the floor
function sfWave(x, floor, dir, dmg, b, speed = 170) {
  hazards.push({ x, y: floor, vx: dir * speed, w: 16, h: 14, dmg: sfDmg(dmg, b), id: ++hazardId, life: 1.6, t: 0, dir, sfWave: true });
  const h = hazards[hazards.length - 1];
  h.update = (hh, dt) => { hh.x += hh.vx * (dt || 1 / 60); if (Math.random() < 0.5) particles.push({ x: hh.x + rand(-4, 4), y: floor - rand(0, 8), vx: 0, vy: -rand(20, 50), life: 0.4, kind: 'star' }); if (solidAtPx(hh.x + dir * 8, floor - 4) || !solidAtPx(hh.x, floor + 2)) hh.life = 0; };
}

// ================================================================== the arena director: constellations, gravity, marks
const SFA = { marks: [], grav: 0, banner: null, monos: [], shade: 0 };
function sfArenaReset() { SFA.marks = []; SFA.grav = 0; SFA.banner = null; SFA.monos = []; SFA.shade = 0; SFSKY.focus = null; SFSKY.k = 0; SFSKY.flare = 0; }
HOOKS.enter.push(() => sfArenaReset());
HOOKS.death.push(() => sfArenaReset());
HOOKS.update.push(dt => {
  for (const m of SFA.marks) m.life -= dt; SFA.marks = SFA.marks.filter(m => m.life > 0);
  if (SFA.banner && (SFA.banner.t += dt) > 3) SFA.banner = null;
  // constellation gravity (arena-wide, airborne player only)
  if (P && SFA.grav && !P.ground && !['hook', 'slam', 'wall', 'glide', 'rest', 'plunge', 'dead'].includes(P.state) && !(P.state === 'roll' && P.airRoll)) {
    P.vy += (P.vy < 0 ? GRAV_UP : GRAV_DN) * SFA.grav * dt;
    if (SFA.grav < 0 && P.vy > 190) P.vy = approach(P.vy, 190, 900 * dt);
  }
});
HOOKS.render.push(() => {
  if (!room) return;
  for (const m of SFA.marks) {   // floor warnings: a ring of starlight tightening
    const k = 1 - m.life / m.max, a = 0.4 + 0.5 * k;
    g.fillStyle = `rgba(${m.col},${a * (0.6 + 0.4 * Math.sin(time * 30))})`;
    const w = Math.round(m.w * (1.3 - 0.5 * k));
    g.fillRect(Math.round(m.x - w / 2), Math.round(m.y) - 1, w, 1); g.fillRect(Math.round(m.x) - 1, Math.round(m.y) - 3, 2, 2);
    addLight(m.x, m.y - 4, 18 + 12 * k, m.col, 0.6);
  }
  for (const h of hazards) if (h.sfDraw) h.sfDraw(h);
  for (const h of hazards) if (h.sfWave) { const s = fxSheet('sf_wave'); if (s.ok) { const t = s.tag('sf_wave'); drawSprite(s, t.from + Math.floor(time * 14) % (t.to - t.from + 1), h.x, h.y, h.dir, { bottom: true }); } addLight(h.x, h.y - 6, 30, '170,200,255', 0.8); }
  for (const h of hazards) if (h.sfStar && !h.boom) {   // the star on its way down
    const s = fxSheet('sf_star'), k = clamp(h.t / h.delay0, 0, 1), y = lerp(h.y - 230, h.y - 4, k * k);
    if (k > 0.35 && s.ok) { const t = s.tag('sf_star'); drawSprite(s, t.from + Math.floor(time * 16) % 4, h.x + (1 - k) * 30, y, 1, { bottom: true }); addLight(h.x + (1 - k) * 30, y - 6, 40, '200,220,255', 0.9); }
  }
  for (const mo of SFA.monos) sfDrawMonolith(mo);
});
HOOKS.renderTop.push(() => {
  if (!SFA.banner || state !== 'play') return;
  const t = SFA.banner.t, a = clamp(Math.min(t / 0.5, (3 - t) / 0.6), 0, 1);
  text(SFA.banner.name, W / 2, 34, 9, '#c6d8ff', 'center', { alpha: a, spacing: 3, weight: 500 });
  text(SFA.banner.sub, W / 2, 44, 5.5, '#8ea4d8', 'center', { alpha: a * 0.9 });
});
function sfDrawMonolith(mo) {   // an obsidian slab risen from the glass; star cracks glow brighter as the nova builds
  const top = Math.round(mo.floor - mo.h * mo.k), x0 = Math.round(mo.x - mo.w / 2), hh = Math.round(mo.floor - top);
  if (hh <= 0) return;
  g.fillStyle = '#0b0d1c'; g.fillRect(x0, top, mo.w, hh);
  g.fillStyle = '#1b2244'; g.fillRect(x0 + 2, top + 2, Math.round(mo.w * 0.45), hh - 2);
  g.fillStyle = '#3a4a88'; g.fillRect(x0 + 1, top, 1, hh); g.fillRect(x0, top, mo.w, 1);
  g.fillStyle = '#8fa4e8'; g.fillRect(x0 + 1, top, Math.round(mo.w * 0.6), 1);
  g.fillStyle = '#05050b'; g.fillRect(x0 + mo.w - 1, top, 1, hh); g.fillRect(x0 - 1, top, 1, hh);
  const glow = 0.5 + 0.5 * Math.sin(time * 6);
  g.fillStyle = `rgba(200,220,255,${0.5 + 0.4 * glow})`;
  for (let y = top + 5, i = 0; y < mo.floor - 3; y += 7, i++) g.fillRect(x0 + 6 + (i % 3) * 3, y, 1, 4);
  addLight(mo.x, top + 10, 30, '170,200,255', 0.6);
}
// ================================================================== ASTREL, THE FALLEN STAR (SF7) — the hardest optional boss save one
BOSS_INFO.astrel = { name: 'Astrel, the Fallen Star', hp: 4800, cinders: 26000, reward: ['moonstep', 'w:starblade', 'c_star'], quote: '“I fell so that nothing else would.”' };
const SF_ASTREL_TAGS = { map: { idle: '', walk: '', dash: '', counter: '', riposte: '', stagger: '', kneel: '', getup: '', combo: '_b', thrust: '_b', upslash: '_b', leap: '_c', cast: '_c', nova: '_c', death: '_c' }, fallback: 'idle' };
const SF_AD = { combo: [36, 38, 50], thrust: [54], upslash: [46], riposte: [54], leap: [52], dash: 36, line: 30, star: 32, arrow: 30, serpent: 32, pillar: 38, well: 46, wave: 26 };
const SF_CONS_NAME = { hunter: ['THE HUNTER', 'Arrows fall from the sky'], serpent: ['THE SERPENT', 'The sky grows light — the serpent coils'], crown: ['THE CROWN', 'The sky grows heavy — pillars rise'] };
class Astrel extends BossBase {
  constructor(x, y) {
    super('astrel', x, y);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.astrel.hp * NGP.hp);
    const self = this;
    this.anim = new SfAnim({ map: SF_ASTREL_TAGS.map, fallback: 'idle', sheetFor(tag) {
      const meta = ASSETS.astrel_meta, suf = SF_ASTREL_TAGS.map[tag];
      let s = sheet((self.phase >= 2 ? 'astrel2' : 'astrel') + suf, { meta });
      if (!s.ok) s = sheet('astrel' + suf, { meta });
      return s;
    } });
    this.anim.set('kneel', true);
    this.sh = { ok: true, has: t => t in SF_ASTREL_TAGS.map, meta: ASSETS.astrel_meta };
    this.state = 'dormant'; this.stanceMax = 330; this.critRange = 46; this.face = -1; this.hidden = false;
    this.ghosts = []; this.log = []; this.cool = 1; this.counterCool = 2.5; this.castCool = 5; this.wellCool = 7; this.leapCool = 2; this.dashCool = 1.2;
    this.cons = null; this.consI = -1; this.consT = 0; this.hazT = 3; this.rotT = 0; this.airT = 0; this.readFx = 0; this.feint = 0; this.chainN = 0;
    this.nova = null; this.novaCool = 0; this.desperate = false; this.meta = ASSETS.astrel_meta || { hurtbox: [54, 30, 15, 57], attacks: {} };
  }
  get L() { return 3 * TILE; }
  get R() { return 46 * TILE - 16; }
  get mid() { return (this.L + this.R) / 2; }
  get spd() { return this.phase >= 3 ? 1.22 : this.phase === 2 ? 1.12 : 1; }
  wake() { return P.ground && P.x > 4 * TILE && P.x < room.pw - 3 * TILE; }
  hurtbox() {
    if (!this.alive || this.hidden) return null;
    const s = this.anim.sheet; return s && s.ok ? metaRect(s, this, this.meta.hurtbox) : rect(this.x - 7, this.y - 56, this.x + 7, this.y);
  }
  canStagger() { return !this.air && !['dash', 'nova', 'intro', 'counter'].includes(this.state) && !(this.state === 'attack' && this.atk === 'leap'); }
  play(tag, loop = false, speed = 1) { this.anim.set(tag, loop, speed * this.spd); }
  stagger() { super.stagger(); this.play('stagger', false, 0.7); this.air = null; this.y = this.floor; this.dsh = null; }
  onParried() { if (this.stanceImmune > 0 || this.state === 'stagger') return; this.stance += 110; if (this.stance >= this.stanceMax && this.canStagger()) this.stagger(); }
  note(k) { this.log.push({ k, t: time }); this.lastMove = k; this.lastMoveT = time; }
  count(k, w = 2.5) { let n = 0; for (const e of this.log) if (e.k === k && time - e.t < w) n++; return n; }
  readPlayer(dt) {
    const s = P.state;
    if (ATK[s] && s !== this.seenAtk) { this.seenAtk = s; this.note(ATK[s].kind === 'heavy' ? 'heavy' : !P.ground ? 'air' : 'light'); }
    if (!ATK[s]) this.seenAtk = null;
    if (s !== this.lastPS) { if (s === 'roll') this.note('roll'); else if (s === 'cast') this.note('spell'); else if (s === 'heal') this.note('heal'); else if (s === 'art') this.note('art'); this.lastPS = s; }
    this.airT = P.ground ? 0 : this.airT + dt;
    if (this.log.length > 40) this.log = this.log.filter(e => time - e.t < 4);
  }
  tell() { this.readFx = 0.4; sfSfx.chime(1.4); }
  // ------------------------------------------------------------ update
  update(dt) {
    this.commonUpdate(dt); this.anim.update(dt);
    for (const gh of this.ghosts) gh.life -= dt; this.ghosts = this.ghosts.filter(gh => gh.life > 0);
    this.readFx -= dt;
    if (!this.active) { this.facePlayerIdle(); if (!this.cutting && this.wake()) this.activate(); return; }
    if (this.introT > 0) {   // (no cutscene: already seen) she rises from her knee
      this.introT -= dt; if (this.state !== 'intro') { this.state = 'intro'; this.play('getup'); this.startArena(); }
      if (this.anim.done) this.anim.hold();
      if (this.introT <= 0) { this.state = 'idle'; this.play('idle', true); this.cool = 0.5; }
      return;
    }
    if (this.state !== 'dead') { this.readPlayer(dt); this.director(dt); }
    for (const k of ['counterCool', 'castCool', 'wellCool', 'leapCool', 'dashCool', 'novaCool']) this[k] -= dt;
    const d = Math.abs(P.x - this.x);
    switch (this.state) {
      case 'idle': case 'walk': {
        this.facePlayer(); this.cool -= dt;
        if (P.state === 'dead') { this.stand(); break; }
        if (this.pendingNova) { this.pendingNova = false; this.enterPhase3(); break; }
        if (this.desperate && this.novaCool <= 0 && this.phase >= 3) { this.startNova(false); break; }
        if (this.reactive(d)) break;
        if (this.cool <= 0) { this.decide(d); break; }
        if (d > 100) { if (this.state !== 'walk') { this.state = 'walk'; this.play('walk', true); } this.x += this.face * 70 * this.spd * dt; }
        else this.stand();
        break;
      }
      case 'approach': {
        this.facePlayer(); this.t -= dt; this.x += this.face * 118 * this.spd * dt;
        if (d < 72 || this.t <= 0) this.start(this.next || 'combo');
        break;
      }
      case 'attack': this.updateAttack(dt); break;
      case 'dash': this.updateDash(dt); break;
      case 'counter': {
        this.facePlayer(); this.t -= dt;
        if (Math.random() < 0.3) particles.push({ x: this.x + this.face * rand(4, 10), y: this.y - rand(20, 60), vx: 0, vy: -rand(4, 12), life: 0.4, kind: 'star' });
        if (this.t <= 0) { if (this.deflected || d > 80) this.startDash(); else this.start('combo'); }
        break;
      }
      case 'cast': this.updateCast(dt); break;
      case 'nova': this.updateNova(dt); break;
      case 'rest':
        this.t -= dt; if (Math.random() < 0.2) particles.push({ x: this.x + rand(-6, 6), y: this.y - rand(20, 40), vx: 0, vy: -rand(6, 14), life: 0.6, kind: 'star' });
        if (this.t <= 0) { this.state = 'idle'; this.play('idle', true); this.cool = 0.2; }
        break;
      case 'stagger':
        this.t -= dt;
        if (this.anim.i === this.anim.n - 1 && this.t > 0.3) this.anim.hold();
        if (this.anim.done || this.t <= 0) {
          if (this.pendingPhase) this.enterPhase2(); else { this.state = 'idle'; this.play('idle', true); this.cool = 0.25; }
        }
        break;
      case 'dead':
        if (Math.random() < 0.5) particles.push({ x: this.x + rand(-12, 12), y: this.y - rand(0, 60), vx: rand(-10, 10), vy: -rand(15, 45), life: rand(1, 2), kind: Math.random() < 0.7 ? 'star' : 'nebula' });
        if (this.anim.done) this.anim.hold();
        break;
    }
    // phase gates
    if (this.alive && this.state !== 'nova') {
      if (this.phase === 1 && this.hp <= this.maxHp * 0.5 && !this.pendingPhase) {
        if (['attack', 'stagger', 'dash', 'cast', 'counter'].includes(this.state)) this.pendingPhase = true; else this.enterPhase2();
      }
      if (this.phase === 2 && this.hp <= this.maxHp * 0.2 && !this.pendingNova && !this.pendingPhase) {
        if (['attack', 'stagger', 'dash', 'cast', 'counter'].includes(this.state)) this.pendingNova = true; else this.enterPhase3();
      }
      if (this.pendingPhase && ['idle', 'walk'].includes(this.state)) this.enterPhase2();
    }
    if (!this.air && this.state !== 'nova') this.y = this.floor;
    this.x = clamp(this.x, this.L, this.R);
    this.ambient(dt);
  }
  facePlayerIdle() { if (!this.cutting) this.face = P.x < this.x ? -1 : 1; }
  stand() { if (this.state !== 'idle' || this.anim.tag !== 'idle') { this.state = 'idle'; this.play('idle', true); } }
  ambient() {
    addLight(this.x, this.y - 40, this.phase >= 2 ? 96 : 80, '180,200,255', this.state === 'rest' ? 0.5 : 0.95);
    if (!this.hidden && this.alive && Math.random() < (this.phase >= 2 ? 0.5 : 0.3)) particles.push({ x: this.x + rand(-10, 10), y: this.y - rand(20, 64), vx: rand(-6, 6), vy: -rand(6, 20), life: rand(0.5, 1), kind: Math.random() < 0.75 ? 'star' : 'nebula' });
  }
  // ------------------------------------------------------------ reading you
  reactive(d) {
    if (this.cool > 0.45) return false;
    if (P.state === 'heal' && d < 190) { this.tell(); if (d < 110) this.start('thrust'); else this.startDash(); return true; }   // you drink, she comes
    if (ATK[P.state] && ATK[P.state].kind === 'heavy' && P.charge > 0.08 && d < 140) { this.tell(); this.start('thrust'); return true; }   // you wind up, she cuts it short
    return false;
  }
  decide(d) {
    const p = this.phase;
    if (this.count('light', 1.6) >= 2 && d < 90 && this.counterCool <= 0) { this.tell(); return this.startCounter(); }
    if (this.count('spell', 2.2) >= 1 && d > 90 && this.dashCool <= 0) { this.tell(); return this.startDash(); }
    if (this.airT > 0.18 && d < 100 && P.y < this.y - 22) { this.tell(); return this.start('upslash'); }
    if (this.count('roll', 2.5) >= 2) this.feint = 0.35;   // you roll on reflex: she waits it out
    let w;
    if (d < 75) w = { combo: 3, thrust: 1, upslash: 0.4, counter: this.counterCool <= 0 ? 0.7 : 0, dash: 0.5, leap: 0.3 };
    else if (d < 170) w = { thrust: 2.2, dash: this.dashCool <= 0 ? 1.8 : 0.3, leap: this.leapCool <= 0 ? 1.2 : 0, approach: 0.8, cast: this.castCool <= 0 ? (p >= 2 ? 1.2 : 0.8) : 0, well: p >= 2 && this.wellCool <= 0 ? 1 : 0 };
    else w = { dash: this.dashCool <= 0 ? 2.4 : 0.6, leap: this.leapCool <= 0 ? 1.4 : 0, cast: this.castCool <= 0 ? 1.4 : 0, well: p >= 2 && this.wellCool <= 0 ? 1.2 : 0, approach: 1 };
    // the mirror: she answers your last move with her own version of it
    if (this.lastMove && time - this.lastMoveT < 3) {
      const m = { light: 'combo', heavy: 'thrust', air: 'leap', spell: 'cast', art: 'dash', roll: 'dash', heal: 'thrust' }[this.lastMove];
      if (w[m] !== undefined && w[m] > 0) { w[m] *= 2.2; if (Math.random() < 0.25) this.tell(); }
    }
    if (w[this.last]) w[this.last] *= 0.35;
    const e = Object.entries(w).filter(([, v]) => v > 0);
    let r = Math.random() * e.reduce((a, [, v]) => a + v, 0), m = e[0][0];
    for (const [k, v] of e) if ((r -= v) <= 0) { m = k; break; }
    this.last = m;
    if (m === 'counter') return this.startCounter();
    if (m === 'dash') return this.startDash();
    if (m === 'cast') return this.startCast('rain');
    if (m === 'well') return this.startCast('well');
    if (m === 'approach') { this.state = 'approach'; this.play('walk', true, 1.5); this.t = 0.9; this.next = Math.random() < 0.7 ? 'combo' : 'thrust'; return; }
    this.start(m);
  }
  // ------------------------------------------------------------ sword strings
  start(m) {
    this.facePlayer(); this.atk = m; this.last = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {}; this.air = null;
    this.state = 'attack'; this.play(m, false);
    const wins = metaWindows(this.anim.sheet, m); this.firstActive = wins.length ? wins[0].active[0] : 3;
    this.hold = ({ combo: 0.1, thrust: 0.22, upslash: 0.08, riposte: 0.02, leap: 0 }[m] || 0) + (this.feint || 0) * (m === 'riposte' ? 0 : 1) - (this.phase >= 3 ? 0.05 : 0);
    this.hold = Math.max(0, this.hold); this.feint = 0; this.glinted = false;
    if (m === 'leap') this.leapCool = this.phase >= 2 ? 3.2 : 4.5;
  }
  updateAttack(dt) {
    const an = this.anim, a = this.atk, wins = metaWindows(an.sheet, a);
    if (a === 'leap') return this.updateLeap(dt, wins);
    if (an.i < this.firstActive - 1) this.facePlayer();
    // the readable beat: she holds the frame before each string's first cut while the blade flares
    if (an.i === this.firstActive - 1 && this.hold > 0) {
      this.hold -= dt; an.t = Math.min(an.t, 5);
      if (!this.glinted) { this.glinted = true; const t = metaPoint(an.sheet, this, [72, 30]); spawnFx('telegraph', t.x, t.y, this.face); sfx.glint(); }
    } else if (!this.glinted && an.i === Math.max(0, this.firstActive - 1)) { this.glinted = true; spawnFx('telegraph', this.x + this.face * 14, this.y - 40, this.face); sfx.glint(); }
    const dmgs = SF_AD[a] || [40];
    wins.forEach((w, wi) => {
      if (an.i < w.active[0] || an.i > w.active[1]) return;
      if (an.changed && an.i === w.active[0]) { sfx.bossSwing(); sfSfx.whoosh(); if (a === 'thrust') { spawnFx('telegraph', this.x + this.face * 60, this.y - 40, this.face); } }
      if (a === 'combo') this.x += this.face * 70 * this.spd * dt;
      if (a === 'thrust') this.x += this.face * 380 * dt;
      if (a === 'riposte') this.x += this.face * 90 * dt;
      if (this.hitIds.has(wi) || !w.hit) return;
      const r = metaRect(an.sheet, this, w.hit);
      if (this.face > 0) r.x0 = Math.min(r.x0, this.x); else r.x1 = Math.max(r.x1, this.x);   // the whole arc, back to her hand
      if (overlap(r, playerHurtbox()) && hurtPlayer(sfDmg(dmgs[wi] ?? dmgs[0], this), P.x < this.x ? -1 : 1, this.atkId * 10 + wi, { parryable: a !== 'upslash', src: this })) this.hitIds.add(wi);
    });
    // phase 2+: the great falling-star cut leaves an echo of starlight that cuts again
    if (a === 'combo' && this.phase >= 2 && an.changed && an.i === 11) sfWave(this.x + this.face * 40, this.floor, this.face, SF_AD.wave, this, 190);
    if (an.done) this.endString();
  }
  endString() {
    const a = this.atk, d = Math.abs(P.x - this.x), p = this.phase;
    this.atk = null;
    if (this.pendingPhase) return this.enterPhase2();
    if (this.pendingNova) { this.pendingNova = false; return this.enterPhase3(); }
    if (this.chainN < (p >= 3 ? 2 : 1)) {
      this.chainN++;
      const r = Math.random(), c = p >= 2 ? 0.6 : 0.3;
      if (a === 'combo' && r < c) return d < 130 ? this.start('thrust') : this.startDash();
      if (a === 'thrust' && r < c) return this.airT > 0.1 ? this.start('upslash') : d < 70 ? this.start('combo') : this.startDash();
      if (a === 'riposte' && r < 0.5) return this.startDash();
      if (a === 'upslash' && r < c) return this.start('leap');
    }
    this.chainN = 0;
    this.state = 'idle'; this.play('idle', true);
    this.cool = p >= 3 ? rand(0.12, 0.35) : p === 2 ? rand(0.2, 0.45) : rand(0.4, 0.8);
  }
  // the leap: up out of reach, a held beat at the top right above you, then a plunge that splits the glass
  updateLeap(dt, wins) {
    const an = this.anim, w = wins[0] || { active: [7, 8], hit: [62, 50, 34, 38] };
    if (!this.air && an.i >= 3 && an.i < 7 && !this.fired.up) {
      this.fired.up = true; this.air = { x0: this.x, tx: clamp(P.x, this.L + 16, this.R - 16), t: 0, T: 0.42, top: 96, hold: this.phase >= 3 ? 0.18 : 0.3 };
      sfx.jump(); sfSfx.whoosh(); spawnFx('dust', this.x, this.floor, this.face);
    }
    if (this.air && !this.air.down) {
      const A = this.air; A.t += dt; const k = Math.min(1, A.t / A.T);
      this.x = lerp(A.x0, A.tx, 1 - Math.pow(1 - k, 2)); this.y = this.floor - Math.sin(k * Math.PI / 2) * A.top;
      if (an.i >= 6) { an.i = 6; an.t = Math.min(an.t, 5); }
      if (k >= 1) {
        A.hold -= dt; this.facePlayer();
        if (!this.glinted) { this.glinted = true; spawnFx('telegraph', this.x, this.y - 50, this.face); sfx.glint(); sfMark(this.x, this.floor, 0.35, 30); }
        if (Math.random() < 0.6) particles.push({ x: this.x + rand(-8, 8), y: this.y - rand(0, 40), vx: 0, vy: rand(10, 40), life: 0.4, kind: 'star' });
        if (A.hold <= 0) { A.down = true; an.i = 7; an.t = 0; an.changed = true; sfx.bossSwing(); }
      }
      return;
    }
    if (this.air && this.air.down) {
      this.y = Math.min(this.floor, this.y + 620 * dt);
      if (an.i > 7) { an.i = 7; an.t = Math.min(an.t, 5); }
      if (!this.hitIds.has(0)) { const r = metaRect(an.sheet, this, w.hit); if (overlap(r, playerHurtbox()) && hurtPlayer(sfDmg(SF_AD.leap[0], this), P.x < this.x ? -1 : 1, this.atkId * 10, { parryable: false, src: this })) this.hitIds.add(0); }
      this.ghosts.push({ f: an.frame, x: this.x, y: this.y, face: this.face, life: 0.18, sh: an.sheet });
      if (this.y >= this.floor) {
        this.y = this.floor; this.air = null; an.i = 8; an.t = 0;
        shake = 9; sfSfx.boom(); spawnFx('sf_burst', this.x, this.floor, 1, null, { bottom: true }); spawnFx('shockwave', this.x, this.floor, 1);
        if (!this.hitIds.has(0) && Math.abs(P.x - this.x) < 30 && P.y > this.floor - 30) { if (hurtPlayer(sfDmg(SF_AD.leap[0], this), P.x < this.x ? -1 : 1, this.atkId * 10, { src: this })) this.hitIds.add(0); }
        for (const dd of [-1, 1]) sfWave(this.x + dd * 14, this.floor, dd, SF_AD.wave, this, this.phase >= 2 ? 200 : 165);
        for (let i = 0; i < 20; i++) particles.push({ x: this.x + rand(-20, 20), y: this.floor - 2, vx: rand(-120, 120), vy: -rand(30, 150), g: 400, life: 0.7, kind: i % 2 ? 'glass' : 'star' });
      }
      return;
    }
    if (an.done) this.endString();
  }
  // ------------------------------------------------------------ starlight dash (straight through you; the path detonates)
  startDash() {
    this.facePlayer(); this.state = 'dash'; this.play('dash', false); this.dashCool = this.phase >= 2 ? 1.6 : 2.4; this.atkId = ++hazardId;
    const through = clamp(P.x + this.face * 74, this.L + 8, this.R - 8);
    this.dsh = { t: 0, phase: 'wind', x0: this.x, to: Math.abs(through - this.x) < 50 ? clamp(this.x + this.face * 140, this.L + 8, this.R - 8) : through, wind: this.phase >= 3 ? 0.22 : 0.32, hit: false };
    spawnFx('telegraph', this.x + this.face * 10, this.y - 40, this.face); sfx.glint();
  }
  updateDash(dt) {
    const D_ = this.dsh, an = this.anim; if (!D_) { this.state = 'idle'; return; }
    D_.t += dt;
    if (D_.phase === 'wind') {
      an.i = 0; an.t = Math.min(an.t, 5);
      if (Math.random() < 0.6) particles.push({ x: this.x - this.face * rand(4, 16), y: this.y - rand(10, 50), vx: -this.face * rand(20, 60), vy: 0, life: 0.3, kind: 'star' });
      if (D_.t >= D_.wind) { D_.phase = 'go'; D_.x0 = this.x; sfSfx.whoosh(); an.i = 1; an.t = 0; this.face = D_.to > this.x ? 1 : -1; }
      return;
    }
    if (D_.phase === 'go') {
      if (an.i > 4) { an.i = 1; }
      const step = 600 * dt, dir = Math.sign(D_.to - this.x);
      this.x = Math.abs(D_.to - this.x) <= step ? D_.to : this.x + dir * step;
      this.ghosts.push({ f: an.frame, x: this.x, y: this.y, face: this.face, life: 0.25, sh: an.sheet });
      if (!D_.hit && overlap(rect(this.x - 10, this.y - 50, this.x + 10, this.y), playerHurtbox())) { if (hurtPlayer(sfDmg(SF_AD.dash, this), this.face, this.atkId, { src: this })) D_.hit = true; }
      if (this.x === D_.to) {
        D_.phase = 'rec'; D_.t = 0; an.i = 5; an.t = 0;
        const x0 = Math.min(D_.x0, this.x), x1 = Math.max(D_.x0, this.x), fl = this.floor, delay = this.phase >= 2 ? 0.38 : 0.5, b = this;
        const h = { x: (x0 + x1) / 2, y: fl - 8, w: x1 - x0, h: 40, dmg: sfDmg(SF_AD.line, this), id: ++hazardId, life: delay + 0.3, t: 0,
          active: h => h.t > delay && h.t < delay + 0.14,
          update: h => { if (h.t > delay && !h.boom) { h.boom = true; sfSfx.glass(); shake = Math.max(shake, 3); for (let x = x0; x < x1; x += 10) particles.push({ x, y: fl - rand(10, 40), vx: rand(-20, 20), vy: -rand(10, 60), life: 0.5, kind: 'star' }); } },
          sfDraw: h => {
            const k = clamp(h.t / delay, 0, 1), y = Math.round(fl - 26); g.globalCompositeOperation = 'lighter';
            if (!h.boom) { g.fillStyle = `rgba(150,180,255,${0.3 + 0.6 * k * (0.6 + 0.4 * Math.sin(time * 40))})`; g.fillRect(Math.round(x0), y, Math.round(x1 - x0), 1); for (let x = x0 + ((time * 90) % 12); x < x1; x += 12) { g.fillStyle = 'rgba(230,240,255,0.9)'; g.fillRect(Math.round(x), y - 1, 1, 3); } }
            else { const a = Math.max(0, 1 - (h.t - delay) * 4); g.fillStyle = `rgba(230,240,255,${a})`; g.fillRect(Math.round(x0), y - 1, Math.round(x1 - x0), 3); g.fillStyle = `rgba(120,150,255,${a * 0.5})`; g.fillRect(Math.round(x0), y - 6, Math.round(x1 - x0), 13); }
            g.globalCompositeOperation = 'source-over'; addLight((x0 + x1) / 2, fl - 26, 40, '170,200,255', 0.6);
          } };
        hazards.push(h);
      }
      return;
    }
    if (D_.t > 0.26) { this.dsh = null; this.facePlayer(); this.state = 'idle'; this.play('idle', true); this.cool = this.phase >= 2 ? rand(0.15, 0.4) : rand(0.3, 0.6);
      if (this.phase >= 2 && Math.abs(P.x - this.x) < 80 && Math.random() < 0.45) this.start('combo'); }
  }
  // ------------------------------------------------------------ the mirror stance
  startCounter() { this.state = 'counter'; this.play('counter', true); this.t = rand(0.8, 1.2); this.counterCool = this.phase >= 2 ? 4 : 5.5; this.deflected = false; this.facePlayer(); spawnFx('telegraph', this.x + this.face * 6, this.y - 56, this.face); sfSfx.chime(0.8); }
  // ------------------------------------------------------------ casts: falling stars, gravity wells
  startCast(kind) {
    this.state = 'cast'; this.castKind = kind; this.play('cast', false, kind === 'well' ? 1.2 : 1); this.fired = {}; this.facePlayer();
    if (kind === 'rain') this.castCool = this.phase >= 2 ? 5 : 7; else this.wellCool = 9;
    sfx.charge(); spawnFx('telegraph', this.x, this.y - 80, this.face);
  }
  updateCast(dt) {
    const an = this.anim;
    if (an.i >= 4) addLight(this.x + this.face * 2, this.y - 86, 50, '200,220,255', 1);
    if (an.i >= 5 && !this.fired.go) {
      this.fired.go = true; flashScreen = Math.max(flashScreen, 0.15);
      if (this.castKind === 'rain') {
        const n = [3, 5, 6][this.phase - 1], sp = 36;
        for (let k = 0; k < n; k++) { const x = clamp(P.x + (k - (n - 1) / 2) * sp + rand(-6, 6), this.L, this.R); sfFallingStar(x, this.floor, 0.85 + k * 0.16, SF_AD.star, this); }
        sfSfx.chime(0.6);
      } else this.spawnWell(clamp(P.x + (Math.random() < 0.5 ? -1 : 1) * rand(20, 50), this.L + 20, this.R - 20));
    }
    if (an.done) { this.state = 'idle'; this.play('idle', true); this.cool = this.phase >= 2 ? rand(0.2, 0.5) : rand(0.4, 0.8); }
  }
  spawnWell(x) {
    const b = this, fl = this.floor, y = fl - 26, T = 2.6;
    sfSfx.well();
    const h = { x, y: fl, w: 60, h: 56, dmg: sfDmg(SF_AD.well, this), id: ++hazardId, life: T + 0.5, t: 0,
      active: h => h.t > T && h.t < T + 0.14,
      update: (h, dt) => {
        if (h.t < T) {   // the pull: stronger the closer you stand
          const dx = x - P.x, dd = Math.abs(dx);
          if (dd < 170 && P.state !== 'dead' && state === 'play') P.pushVx = (P.pushVx || 0) + Math.sign(dx) * 78 * (1 - dd / 170) * Math.min(1, h.t / 0.4);
          if (Math.random() < 0.8) { const a = rand(0, 6.28), r = rand(20, 50); particles.push({ x: x + Math.cos(a) * r, y: y + Math.sin(a) * r * 0.8, vx: -Math.cos(a) * r * 1.2, vy: -Math.sin(a) * r, life: 0.6, kind: Math.random() < 0.5 ? 'nebula' : 'star' }); }
        } else if (!h.boom) { h.boom = true; sfSfx.boom(); shake = Math.max(shake, 6); flashScreen = Math.max(flashScreen, 0.2); spawnFx('sf_burst', x, fl, 1, null, { bottom: true, speed: 0.8 }); for (let i = 0; i < 24; i++) { const a = rand(0, 6.28); particles.push({ x, y, vx: Math.cos(a) * rand(60, 160), vy: Math.sin(a) * rand(60, 160), life: 0.5, kind: 'star' }); } }
      },
      sfDraw: h => {
        if (h.boom) return;
        const s = fxSheet('sf_well'), k = Math.min(1, h.t / 0.4), pre = h.t > T - 0.5;
        if (s.ok) { const t = s.tag('sf_well'); drawSprite(s, t.from + Math.floor(time * 12) % (t.to - t.from + 1), x, y, 1, { center: true, alpha: k * (pre ? 0.7 + 0.3 * Math.sin(time * 40) : 0.9) }); }
        addLight(x, y, 60, pre ? '230,220,255' : '150,120,255', 0.9);
      } };
    hazards.push(h);
  }
  // ------------------------------------------------------------ the constellations
  startArena() { if (this.cons) return; this.consI = -1; this.nextCons(); }
  nextCons() {
    const order = this.phase >= 2 ? ['crown', 'hunter', 'serpent'] : ['hunter', 'serpent'];
    this.consI = (this.consI + 1) % order.length; this.cons = order[this.consI];
    this.consT = [22, 16, 12][this.phase - 1]; this.rotT = 1.6; this.hazT = 2.4; SFSKY.k = 0;
    SFA.grav = this.cons === 'serpent' ? -0.3 : this.cons === 'crown' ? 0.24 : 0;
    SFA.banner = { name: SF_CONS_NAME[this.cons][0], sub: SF_CONS_NAME[this.cons][1], t: 0 };
    sfSfx.chime(this.cons === 'crown' ? 0.5 : this.cons === 'serpent' ? 0.66 : 0.8); noise(1.2, 900, 0.5, 0.15, 'bandpass', 2);
  }
  director(dt) {
    if (!this.cons) return;
    SFSKY.focus = this.cons; SFSKY.k = approach(SFSKY.k, 1, dt * 1.2); SFSKY.flare = approach(SFSKY.flare, this.state === 'nova' ? 1 : 0.3, dt);
    if (this.rotT > 0) { this.rotT -= dt; SFSKY.rot += dt * 220 * Math.sin(Math.PI * clamp(this.rotT / 1.6, 0, 1)); } else SFSKY.rot += dt * 3;
    if (this.state === 'nova' || this.state === 'dead') return;
    this.consT -= dt; if (this.consT <= 0) this.nextCons();
    this.hazT -= dt;
    if (this.hazT <= 0 && this.rotT <= 0) {
      const p = this.phase - 1;
      if (this.cons === 'hunter') { this.hunterVolley(); this.hazT = [3.6, 2.5, 2.0][p]; }
      else if (this.cons === 'serpent') { this.serpent(); this.hazT = [6.2, 4.6, 3.8][p]; }
      else { this.crownPillars(); this.hazT = [5.2, 4.0, 3.3][p]; }
    }
  }
  hunterVolley() {
    const n = [2, 3, 4][this.phase - 1], fl = this.floor;
    for (let k = 0; k < n; k++) {
      const sx = clamp(P.x + rand(-150, 150), this.L - 40, this.R + 40), sy = fl - 230 - rand(0, 30);
      const lead = P.vx * 0.35, tx = clamp(P.x + lead + (k - (n - 1) / 2) * 26, this.L, this.R), ty = fl - 12;
      const a = Math.atan2(ty - sy, tx - sx), sp = 430, tele = 0.75 + k * 0.2;
      const h = { x: sx, y: sy, w: 8, h: 8, dmg: sfDmg(SF_AD.arrow, this), id: ++hazardId, life: tele + 1.4, t: 0,
        active: h => h.t > tele && !h.dead,
        update: (h, dt) => {
          if (h.t <= tele) return;
          if (!h.shot) { h.shot = true; sfSfx.whoosh(); }
          h.x += Math.cos(a) * sp * (dt || 1 / 60); h.y += Math.sin(a) * sp * (dt || 1 / 60);
          if (Math.random() < 0.7) particles.push({ x: h.x, y: h.y - 4, vx: 0, vy: 0, life: 0.25, kind: 'star' });
          if (h.y > fl - 2 || solidAtPx(h.x, h.y - 4)) { h.dead = true; h.life = 0; spawnFx('sf_burst', h.x, Math.min(fl, h.y), 1, null, { bottom: true, speed: 1.6 }); }
        },
        sfDraw: h => {
          if (h.t <= tele) {   // the aim line: faint, then bright just before it flies
            const k = h.t / tele; g.globalCompositeOperation = 'lighter';
            g.strokeStyle = `rgba(160,190,255,${0.12 + 0.45 * k * k})`; g.lineWidth = 1; g.beginPath(); g.moveTo(sx, sy); g.lineTo(sx + Math.cos(a) * 320, sy + Math.sin(a) * 320); g.stroke();
            g.globalCompositeOperation = 'source-over'; addLight(sx, sy, 20, '200,220,255', 0.8); return;
          }
          const s = fxSheet('sf_arrow'); if (s.ok) drawRotated(s, s.tag('sf_arrow').from + Math.floor(time * 16) % 2, h.x, h.y - 4, a);
          addLight(h.x, h.y - 4, 30, '200,220,255', 0.8);
        } };
      hazards.push(h);
    }
  }
  serpent() {
    const fl = this.floor, dir = Math.random() < 0.5 ? 1 : -1, x0 = dir > 0 ? this.L - 60 : this.R + 60, sp = [150, 175, 200][this.phase - 1];
    const seg = 13, gap = 11, amp = 13, base = 26, ph0 = rand(0, 6.28), b = this;
    const yAt = (x, t) => fl - base - amp * Math.sin(x * 0.035 + ph0 + t * 1.6);
    sfSfx.beam();
    const h = { x: x0, y: fl, w: 1, h: 1, dmg: sfDmg(SF_AD.serpent, this), id: ++hazardId, life: 7, t: 0, segs: [],
      active: () => false,
      update: (h, dt) => {
        const hx = x0 + dir * sp * Math.max(0, h.t - 0.8);
        h.segs = [];
        for (let i = 0; i < seg; i++) { const x = hx - dir * i * gap; h.segs.push([x, yAt(x, h.t), i === 0 ? 7 : 5.5 - i * 0.2]); }
        if (h.t > 0.8) for (const [x, y, r] of h.segs) {
          if (x < b.L - 30 || x > b.R + 30) continue;
          if (overlap(rect(x - r, y - r, x + r, y + r), playerHurtbox()) && hurtPlayer(h.dmg, dir, h.id, { src: b })) break;
        }
        if ((dir > 0 && hx - seg * gap > b.R + 60) || (dir < 0 && hx + seg * gap < b.L - 60)) h.life = 0;
      },
      sfDraw: h => {
        if (h.t < 0.8) { const k = h.t / 0.8; sfMark(clamp(x0 + dir * 80, b.L, b.R), fl, 0.05, 30); g.fillStyle = `rgba(200,220,255,${0.4 * k})`; g.fillRect(Math.round(clamp(x0 + dir * 60, b.L, b.R) - 1), Math.round(fl - base - amp), 2, amp * 2); return; }
        g.globalCompositeOperation = 'lighter';
        for (let i = h.segs.length - 1; i >= 0; i--) {
          const [x, y, r] = h.segs[i];
          g.fillStyle = `rgba(110,140,255,0.35)`; g.beginPath(); g.arc(Math.round(x), Math.round(y), r + 2, 0, 6.3); g.fill();
          g.fillStyle = i === 0 ? 'rgba(255,255,255,0.95)' : 'rgba(200,215,255,0.85)'; g.beginPath(); g.arc(Math.round(x), Math.round(y), Math.max(1.5, r * 0.55), 0, 6.3); g.fill();
          if (i < h.segs.length - 1) { const [x2, y2] = h.segs[i + 1]; g.strokeStyle = 'rgba(150,180,255,0.6)'; g.lineWidth = 1; g.beginPath(); g.moveTo(x, y); g.lineTo(x2, y2); g.stroke(); }
        }
        g.globalCompositeOperation = 'source-over';
        const [hx, hy] = h.segs[0]; addLight(hx, hy, 50, '200,215,255', 1); g.fillStyle = '#05050b'; g.fillRect(Math.round(hx + dir * 2), Math.round(hy - 2), 1, 1);
      } };
    hazards.push(h);
  }
  crownPillars() {
    const fl = this.floor, n = [4, 5, 6][this.phase - 1], span = this.R - this.L, off = rand(0, 1), safe = irand(0, n - 1);
    for (let k = 0; k < n; k++) {
      if (k === safe && this.phase < 3) continue;
      const x = clamp(this.L + span * ((k + off) / n), this.L, this.R), delay = 0.75 + (k % 2) * 0.25;
      sfMark(x, fl, delay, 20, '255,235,190');
      hazards.push({ x, y: fl, w: 18, h: 120, dmg: sfDmg(SF_AD.pillar, this), id: ++hazardId, life: 5, delay, fx: null,
        onStart: h => { h.fx = spawnFx('sf_pillar', h.x, fl, 1, null, { bottom: true }); if (!h.fx) h.life = 0; else if (h.fx.anim) { h.fx.anim.i = 2; h.fx.anim.t = 0; } sfx.pillar(); shake = Math.max(shake, 2); },
        update: h => { if (!h.fx || h.fx.anim.done) { h.life = 0; return; } if (h.fx.anim.i >= 2 && h.fx.anim.i <= 5) addLight(h.x, fl - 50, 60, '220,230,255', 0.9); },
        active: h => h.fx && h.fx.anim.i >= 2 && h.fx.anim.i <= 5 });
    }
  }
  // ------------------------------------------------------------ phases
  enterPhase2() {
    this.phase = 2; this.pendingPhase = false; this.stance = 0; this.air = null; this.y = this.floor;
    this.state = 'idle'; this.play('idle', true); this.cool = 0.8; this.facePlayer();
    flashScreen = 0.7; shake = 10; sfSfx.shatter(); sfSfx.chime(0.5);
    for (let i = 0; i < 50; i++) particles.push({ x: this.x + rand(-30, 30), y: this.y - rand(0, 80), vx: rand(-80, 80), vy: -rand(20, 120), life: rand(0.6, 1.4), kind: i % 3 ? 'star' : 'nebula' });
    this.consI = -1; this.nextCons();
    bossPhase2Scene(this);
  }
  enterPhase3() {
    this.phase = 3; this.stance = 0; this.air = null; this.dsh = null; this.facePlayer();
    hazards = hazards.filter(h => h.sfStar);   // the sky holds its breath
    const b = this;
    if (!SAVE.flags['cutp3:astrel']) {
      SAVE.flags['cutp3:astrel'] = 1;
      playCutscene([
        { pan: { x: b.x, y: b.y - 50 }, dur: 0.5 },
        act(() => { b.play('nova', true); flashScreen = 0.6; shake = 8; sfSfx.hum(); }),
        say('Astrel', 'I remember how I burned.', { dur: 2.0 }),
        act(() => { SFSKY.flare = 1; sfSfx.chime(0.45); }), wait(0.5),
        { pan: { x: P.x, y: P.y - 30 }, dur: 0.4 },
      ], () => { if (b.alive) b.startNova(true); });
    } else this.startNova(true);
  }
  startNova(first) {
    if (!this.alive || boss !== this) return;
    hazards = []; SFA.marks = [];
    this.state = 'nova'; this.play('nova', true); this.air = null; this.dsh = null;
    this.nova = { t: 0, st: 'rise', T: first ? 10 : 8.5, dmg: 0, need: this.maxHp * 0.075, x0: this.x, rainT: 1.5 };
    SFA.banner = { name: 'SUPERNOVA', sub: 'Strike the star down — or hide from its light', t: 0 };
    sfSfx.hum(); sfx.charge();
    const fl = this.floor;
    SFA.monos = [this.L + 64, this.R - 64].map(x => {
      const mo = { x, floor: fl, w: 22, h: 60, k: 0 };
      room.dyn.push({ x0: x - 11, x1: x + 11, y0: fl - 60, y1: fl, on: () => mo.k > 0.95 && SFA.monos.includes(mo), sfMono: true });
      return mo;
    });
  }
  updateNova(dt) {
    const N = this.nova, fl = this.floor; N.t += dt;
    for (const mo of SFA.monos) mo.k = approach(mo.k, N.st === 'fall' || N.st === 'done' ? 0 : 1, dt * (N.st === 'fall' || N.st === 'done' ? 0.8 : 1.4));
    if (N.st === 'rise') {
      const k = Math.min(1, N.t / 1.1); this.x = lerp(N.x0, this.mid, k); this.y = fl - 70 * Math.sin(k * Math.PI / 2); this.air = { nova: true };
      if (k >= 1) { N.st = 'charge'; N.t = 0; }
      return;
    }
    if (N.st === 'charge') {
      this.y = fl - 70 + Math.sin(time * 2) * 2;
      const k = N.t / N.T;
      addLight(this.x, this.y - 30, 60 + 140 * k, '220,230,255', 1);
      if (Math.random() < 0.6 + k) { const a = rand(0, 6.28), r = rand(60, 140) * (1 - k * 0.5); particles.push({ x: this.x + Math.cos(a) * r, y: this.y - 30 + Math.sin(a) * r, vx: -Math.cos(a) * r * 1.4, vy: -Math.sin(a) * r * 1.4, life: 0.7, kind: Math.random() < 0.7 ? 'star' : 'nebula' }); }
      if ((N.rainT -= dt) <= 0 && N.t < N.T - 2) { N.rainT = 1.5; sfFallingStar(clamp(P.x + rand(-40, 40), this.L, this.R), fl, 0.9, SF_AD.star, this); }
      if (Math.floor(N.t) !== Math.floor(N.t - dt)) tone(220 + 60 * Math.floor(N.t), 0.3, 0.06, 'triangle', 1.2);
      if (N.dmg >= N.need) {   // struck down: she falls, burning out
        N.st = 'fall'; N.t = 0; flashScreen = 0.6; shake = 10; sfSfx.shatter(); toast('The star falls!', 2);
        SFA.banner = { name: 'THE STAR FALLS', sub: 'Strike now', t: 0 };
        return;
      }
      if (N.t >= N.T) {   // SUPERNOVA
        N.st = 'blast'; N.t = 0; flashScreen = 1; shake = 16; hitstop = 0.12; sfSfx.boom(); sfx.roar(); noise(1.5, 3000, 0.5, 0.6, 'highpass', 0.3);
        const cover = SFA.monos.some(mo => mo.k > 0.9 && (mo.x - this.x) * (P.x - mo.x) > 0 && Math.abs(P.x - mo.x) < 70 && P.y > fl - mo.h + 12);
        if (cover) { toast('The monolith drinks the light.', 2.2); hurtPlayer(sfDmg(10, this), P.x < this.x ? -1 : 1, ++hazardId, { src: this }); }
        else { P.inv = 0; hurtPlayer(D.maxHp * 0.82 * NGP.dmg, P.x < this.x ? -1 : 1, ++hazardId, { src: this }); }
        for (let i = 0; i < 80; i++) { const a = rand(0, 6.28); particles.push({ x: this.x, y: this.y - 30, vx: Math.cos(a) * rand(80, 320), vy: Math.sin(a) * rand(80, 320), life: rand(0.5, 1.2), kind: i % 3 ? 'star' : 'nebula' }); }
      }
      return;
    }
    if (N.st === 'blast') {
      if (N.t > 0.6) { N.st = 'fall'; N.t = 0; this.exhaust = true; }
      return;
    }
    if (N.st === 'fall') {
      this.y = Math.min(fl, this.y + 300 * dt);
      if (this.y >= fl) {
        this.y = fl; this.air = null; N.st = 'done'; shake = 6; sfSfx.boom(); spawnFx('sf_burst', this.x, fl, 1, null, { bottom: true });
        this.desperate = true; this.novaCool = 36; this.nova = null; SFSKY.flare = 0.3;
        setTimeout(() => { SFA.monos = []; room.dyn = room.dyn.filter(d => !d.sfMono); }, 1400);
        if (this.exhaust) { this.exhaust = false; this.state = 'rest'; this.play('kneel', true); this.t = 1.6; }
        else { this.state = 'idle'; this.stanceImmune = 0; this.stance = this.stanceMax; this.stagger(); this.t = 3.2; }
        if (this.cons) this.hazT = 3;
      }
    }
  }
  // ------------------------------------------------------------ being hit
  hit(info) {
    if (!this.alive) return;
    if (!this.active) { this.activate(); return; }
    if (this.hidden || this.state === 'intro') return;
    if (this.state === 'dash' && this.dsh && this.dsh.phase === 'go') return;
    if (this.state === 'counter' && !info.crit) {
      if (info.melee) {   // your own blow, turned back on you
        sfx.parry(); hitstop = 0.16; shake = 4; sfSfx.chime(1.2);
        spawnFx(fxOr('parry_flash', 'parry_spark'), this.x + this.face * 12, this.y - 36, this.face, null, { tint: '#bcd4ff' });
        if (P.state !== 'dead') { setP('hurt', 'hurt'); P.vx = -P.face * 150; P.st = Math.max(0, P.st - 22); P.combo = 0; }
        this.start('riposte'); return;
      }
      if (!this.deflected) { this.deflected = true; sfSfx.glass(); spawnFx(fxOr('parry_flash', 'parry_spark'), info.x, info.y, -info.dir, null, { tint: '#bcd4ff' }); }
      return;
    }
    if (this.state === 'nova' && this.nova && this.nova.st === 'charge') { this.nova.dmg += info.dmg; this.flash = 1; }
    if (this.state === 'rest') info = { ...info, dmg: info.dmg * 1.3 };
    super.hit(info);
  }
  die() {
    this.state = 'dead'; this.play('death', false, 0.8); this.air = null; this.y = this.floor; this.dsh = null; this.nova = null;
    hazards = []; projectiles = projectiles.filter(p => p.owner === 'player'); SFA.marks = []; SFA.grav = 0; SFA.monos = []; room.dyn = room.dyn.filter(d => !d.sfMono);
    shake = 12; hitstop = 0.3; slowmo = 1.8; flashScreen = 0.8; sfSfx.shatter(); sfx.felled();
    SFSKY.focus = null; SFA.banner = null;
    victoryBanner = { text: 'THE FALLEN STAR SETS', t: 0 };
    this.rewards();
    setTimeout(() => { if (room && room.id === 'SF7') toast('Starlight gathers at your feet. You feel lighter than air.', 4); }, 9000);
  }
  // ------------------------------------------------------------ drawing
  draw() {
    for (const gh of this.ghosts) drawSprite(gh.sh, gh.f, gh.x, gh.y, gh.face, { alpha: gh.life * 2.2, flash: 1, flashColor: this.phase >= 2 ? '#e0e8ff' : '#8ea8ff' });
    if (this.hidden) return;
    const s = this.anim.sheet;
    if (!s || !s.ok) { g.fillStyle = '#2a3056'; g.fillRect(Math.round(this.x - 7), Math.round(this.y - 58), 14, 58); return; }
    const opt = this.flash > 0 ? { flash: this.flash * 0.6, flashColor: '#dfe8ff' } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#c6d8ff' } :
      this.state === 'nova' && this.nova && this.nova.st === 'charge' ? { flash: 0.2 + 0.5 * (this.nova.t / this.nova.T) * (0.6 + 0.4 * Math.sin(time * 18)), flashColor: '#ffffff' } : {};
    drawSprite(s, this.anim.frame, this.x, this.y, this.face, opt);
    if (this.readFx > 0) {   // the read: a glint crosses her mask
      const hx = this.x + this.face * 3, hy = this.y - 55;
      g.fillStyle = `rgba(255,255,255,${Math.min(1, this.readFx * 3)})`; g.fillRect(Math.round(hx) - 2, Math.round(hy), 5, 1); g.fillRect(Math.round(hx), Math.round(hy) - 2, 1, 5);
      addLight(hx, hy, 24, '230,240,255', 1);
    }
    if (this.critable()) { g.fillStyle = '#c6d8ff'; const y = Math.round(this.y - 70 + Math.sin(time * 8) * 1.5); g.fillRect(Math.round(this.x) - 1, y, 3, 3); g.fillRect(Math.round(this.x), y - 1, 1, 5); g.fillRect(Math.round(this.x) - 2, y + 1, 5, 1); }
    if (this.nova && this.nova.st === 'charge') {   // the countdown: a ring of stars going dark one by one
      const N = this.nova, left = Math.ceil(N.T - N.t), cx = this.x, cy = this.y - 30, R = 26;
      for (let i = 0; i < Math.ceil(N.T); i++) { const a = -Math.PI / 2 + i / Math.ceil(N.T) * 6.283, on = i < left; g.fillStyle = on ? '#ffffff' : '#2a3056'; g.fillRect(Math.round(cx + Math.cos(a) * R), Math.round(cy + Math.sin(a) * R), on ? 2 : 1, on ? 2 : 1); }
      const need = clamp(N.dmg / N.need, 0, 1); g.fillStyle = 'rgba(10,10,20,0.8)'; g.fillRect(Math.round(cx - 16), Math.round(cy + R + 6), 32, 3); g.fillStyle = '#c6d8ff'; g.fillRect(Math.round(cx - 16), Math.round(cy + R + 6), Math.round(32 * need), 3);
    }
  }
}
BOSS_SPAWN.astrel = (cx, fy) => new Astrel(cx, fy);
BOSS_CUTS.astrel = b => [
  act(() => { b.hidden = true; b.face = -1; b.play('kneel', true); }),
  { pan: { x: b.x, y: b.floor - 90 }, dur: 1.0 },
  { dur: 1.1, tween: (dt, k) => { const x = b.x + (1 - k) * 120, y = lerp(b.floor - 260, b.floor - 20, k * k); for (let i = 0; i < 4; i++) particles.push({ x: x + rand(-3, 3), y: y + rand(-3, 3), vx: rand(20, 60), vy: -rand(40, 90), life: 0.5, kind: i % 2 ? 'star' : 'nebula' }); addLight(x, y, 60, '220,230,255', 1); } },
  act(() => { b.hidden = false; shake = 12; flashScreen = 0.9; sfSfx.boom(); spawnFx('sf_burst', b.x, b.floor, 1, null, { bottom: true }); for (let i = 0; i < 40; i++) particles.push({ x: b.x + rand(-20, 20), y: b.floor - rand(0, 10), vx: rand(-140, 140), vy: -rand(40, 200), g: 380, life: rand(0.6, 1.2), kind: i % 2 ? 'glass' : 'star' }); }),
  wait(0.8),
  say('', 'A star fell here, and the old gods with it. It never left.'),
  act(() => { b.play('getup', false); sfSfx.hum(); }), wait(1.0),
  act(() => { b.facePlayer(); SFSKY.focus = 'hunter'; SFSKY.k = 0.2; SFSKY.flare = 1; sfSfx.chime(0.7); }),
  say('Astrel', 'You climbed so far to touch the sky. I fell so far to keep it shut.'),
  act(() => { b.play('counter', true); sfx.glint(); flashScreen = 0.3; }), wait(0.7),
];
PHASE2_LINES.astrel = ['Astrel', 'Read the sky with me, little light. Every star I name is a blade.'];
// the arena starts turning once the fight is on (the cutscene path ends with bossCutsceneStart's callback)
HOOKS.update.push(() => { if (boss && boss.kind === 'astrel' && boss.active && boss.alive && !boss.cons && !boss.cutting) boss.startArena(); });

// ================================================================== THE ORRERY SENTINEL (SF5, mini-boss)
BOSS_INFO.orrery = { name: 'The Orrery Sentinel', hp: 2000, cinders: 7000, reward: ['w:orrery_whip', 'shard'], quote: 'It still keeps the hours of a sky that fell.' };
const SF_OD = { planet: 18, orbit: 30, launch: 32, beam: 44, sweep: 40, slam: 52, wave: 24 };
class OrrerySentinel extends BossBase {
  constructor(x, y) {
    super('orrery', x, y);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.orrery.hp * NGP.hp);
    this.sh = sheet('orrery'); this.anim = new Anim(this.sh, 'idle', true); this.state = 'dormant'; this.stanceMax = 260; this.critRange = 60;
    this.hoverY = y - 4; this.y = this.hoverY; this.bob = 0; this.face = -1; this.cool = 1.2;
    this.planets = [0, 1, 2, 3].map(i => ({ a: i * Math.PI / 2, k: i, r: 40, out: 0, gone: false }));
    this.orbitR = 40; this.orbitSpd = 1.1; this.last = null; this.beams = [];
  }
  get L() { return 2 * TILE + 44; }
  get R() { return 38 * TILE - 44; }
  get core() { return { x: this.x + this.face * 6, y: this.y - 52 }; }
  wake() { return P.ground && P.x > 3 * TILE + 8; }
  canStagger() { return !['slam', 'rise'].includes(this.state); }
  hurtbox() { if (!this.alive) return null; return this.sh.ok && this.sh.meta ? metaRect(this.sh, this, this.sh.meta.hurtbox) : rect(this.x - 16, this.y - 70, this.x + 16, this.y - 8); }
  setA(st, tag, loop = false) { this.state = st; this.anim.set(this.sh.has(tag) ? tag : 'idle', loop, this.phase === 2 ? 1.15 : 1); }
  stagger() { super.stagger(); this.y = this.floor + 6; this.beams = []; }
  update(dt) {
    this.commonUpdate(dt); this.anim.update(dt); this.bob += dt;
    const p2 = this.phase === 2;
    this.orbitSpd = p2 ? 1.5 : 1.1;
    for (const pl of this.planets) { pl.a += dt * this.orbitSpd * (this.state === 'orbit' ? 1.9 : 1); pl.r = approach(pl.r, this.orbitR, dt * 90); }
    if (!this.active) { if (!this.cutting && this.wake()) this.activate(); this.y = this.hoverY + Math.sin(this.bob * 1.5) * 2; return; }
    if (this.introT > 0) { this.introT -= dt; if (this.state !== 'intro') this.setA('intro', 'charge'); if (this.anim.done) this.anim.hold(); if (this.introT <= 0) { this.setA('idle', 'idle', true); this.cool = 0.6; } return; }
    const dx = P.x - this.x, d = Math.abs(dx);
    this.planetContact();
    this.updateBeams(dt);
    switch (this.state) {
      case 'idle': {
        this.facePlayer(); this.cool -= dt;
        const want = P.x - Math.sign(dx || 1) * 80;
        this.x = approach(this.x, clamp(want, this.L, this.R), 42 * dt);
        this.y = approach(this.y, this.hoverY + Math.sin(this.bob * 1.5) * 3, 60 * dt);
        if (this.cool <= 0 && P.state !== 'dead') this.decide(d);
        break;
      }
      case 'orbit': {
        this.t -= dt; this.facePlayer();
        this.x = approach(this.x, clamp(P.x, this.L, this.R), 22 * dt);
        if (this.t < 0.6) this.orbitR = 40;
        if (this.t <= 0) { this.setA('idle', 'idle', true); this.cool = p2 ? rand(0.4, 0.8) : rand(0.7, 1.2); }
        break;
      }
      case 'charge': {   // eye beam: aim, lock, fire
        const an = this.anim, c = this.core;
        if (!this.aim) this.aim = { t: 0, locked: false, tx: P.x, ty: P.y - 12 };
        const A = this.aim; A.t += dt;
        if (!A.locked) { A.tx = P.x; A.ty = P.y - 12; this.facePlayer(); if (A.t > 0.6) { A.locked = true; sfx.glint(); } }
        if (an.done && !A.fired) {
          A.fired = true; const ang = Math.atan2(A.ty - c.y, A.tx - c.x);
          this.beams.push({ x: c.x, y: c.y, a: ang, da: (A.tx > c.x ? 1 : -1) * (p2 ? 0.28 : 0.18), t: 0, T: 0.5, id: ++hazardId, hit: false });
          sfSfx.beam(); shake = Math.max(shake, 4); flashScreen = Math.max(flashScreen, 0.15);
          this.t = p2 && !this.second ? 0.2 : 0.55;
        }
        if (A.fired) { this.t -= dt; if (this.t <= 0) { if (p2 && !this.second) { this.second = true; this.aim = null; this.setA('charge', 'charge'); this.anim.speed = 1.6; } else { this.second = false; this.aim = null; this.setA('idle', 'idle', true); this.cool = p2 ? rand(0.4, 0.8) : rand(0.7, 1.2); } } }
        break;
      }
      case 'sweep': this.updateMeta(dt, 'sweep', SF_OD.sweep); if (this.anim.done) { this.setA('idle', 'idle', true); this.cool = p2 ? rand(0.3, 0.7) : rand(0.6, 1.0); } break;
      case 'launch': {
        this.t -= dt; this.facePlayer();
        if (!this.fired && this.t < 0.35) { this.fired = true; this.launchPlanet(); if (p2) setTimeout(() => { if (boss === this && this.alive && this.state !== 'stagger') this.launchPlanet(); }, 420); }
        if (this.t <= 0) { this.setA('idle', 'idle', true); this.cool = p2 ? rand(0.4, 0.8) : rand(0.7, 1.1); }
        break;
      }
      case 'rise': {   // up and over you
        this.t += dt; const k = Math.min(1, this.t / 0.6);
        this.y = lerp(this.sy, this.floor - 96, 1 - Math.pow(1 - k, 2));
        this.x = approach(this.x, clamp(P.x, this.L, this.R), 260 * dt);
        if (this.t > 0.9) { sfx.glint(); spawnFx('telegraph', this.x, this.y - 60, 1); sfMark(this.x, this.floor, 0.3, 40, '255,220,160'); this.setA('slam', 'slam'); this.anim.i = 5; this.anim.t = 0; this.anim.changed = true; this.dropV = 0; this.hitIds = new Set(); this.atkId = ++hazardId; }
        break;
      }
      case 'slam': {
        const an = this.anim;
        if (this.y < this.floor + 8) { this.dropV += 1600 * dt; this.y = Math.min(this.floor + 8, this.y + this.dropV * dt); if (an.i > 5) { an.i = 5; an.t = 0; } this.updateMeta(dt, 'slam', SF_OD.slam, true);
          if (this.y >= this.floor + 8) { shake = 10; sfSfx.boom(); sfx.boom(); spawnFx('shockwave', this.x, this.floor, 1); for (const dd of [-1, 1]) sfWave(this.x + dd * 20, this.floor, dd, SF_OD.wave, this, 170); for (let i = 0; i < 16; i++) particles.push({ x: this.x + rand(-30, 30), y: this.floor - 2, vx: rand(-100, 100), vy: -rand(30, 140), g: 400, life: 0.6, kind: i % 2 ? 'rock' : 'star' }); this.t = 1.1; } }
        else { this.t -= dt; if (an.i >= an.n - 1) an.hold(); if (this.t <= 0) { this.setA('idle', 'idle', true); this.cool = 0.4; } }
        break;
      }
      case 'stagger':
        this.t -= dt; if (this.anim.done) this.anim.hold();
        if (this.t <= 0) { if (this.pendingPhase) this.enterPhase2(); else { this.setA('idle', 'idle', true); this.cool = 0.4; } }
        break;
      case 'dead':
        this.y = Math.min(this.floor + 8, this.y + 40 * dt);
        if (Math.random() < 0.4) particles.push({ x: this.x + rand(-20, 20), y: this.y - rand(20, 80), vx: 0, vy: -rand(10, 30), life: 1, kind: 'star' });
        if (this.anim.done) this.anim.hold();
        break;
    }
    if (this.phase === 1 && this.hp <= this.maxHp * 0.5 && this.alive && !this.pendingPhase) {
      if (['slam', 'rise', 'stagger', 'charge'].includes(this.state)) this.pendingPhase = true; else this.enterPhase2();
    }
    if (this.pendingPhase && this.state === 'idle') this.enterPhase2();
    this.x = clamp(this.x, this.L, this.R);
    addLight(this.core.x, this.core.y, 70, '200,215,255', 0.9);
  }
  decide(d) {
    const p2 = this.phase === 2;
    const w = { orbit: 1.4, beam: 1.6, sweep: d < 110 ? 2.2 : 0.4, launch: d > 90 ? 1.6 : 0.7, slam: p2 ? (d < 160 ? 1.8 : 1) : 0 };
    if (w[this.last]) w[this.last] *= 0.3;
    const e = Object.entries(w).filter(([, v]) => v > 0);
    let r = Math.random() * e.reduce((a, [, v]) => a + v, 0), m = e[0][0];
    for (const [k, v] of e) if ((r -= v) <= 0) { m = k; break; }
    this.last = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = false;
    if (m === 'orbit') { this.setA('orbit', 'charge'); this.t = 3.0; this.orbitR = 104; sfSfx.hum(); spawnFx('telegraph', this.core.x, this.core.y - 20, 1); sfx.glint(); }
    else if (m === 'beam') { this.setA('charge', 'charge'); this.aim = null; this.second = false; sfx.charge(); }
    else if (m === 'sweep') { this.setA('sweep', 'sweep'); spawnFx('telegraph', this.x, this.y - 30, 1); sfx.glint(); }
    else if (m === 'launch') { this.setA('launch', 'charge'); this.anim.speed = 1.4; this.t = 0.8; }
    else { this.state = 'rise'; this.t = 0; this.sy = this.y; this.anim.set('slam', false); sfSfx.whoosh(); }
  }
  updateMeta(dt, tag, dmg, keep) {
    const an = this.anim;
    for (const [wi, w] of metaWindows(this.sh, tag).entries()) {
      if (!keep && (an.i < w.active[0] || an.i > w.active[1])) continue;
      if (an.changed && an.i === w.active[0]) { sfx.bossSwing(); if (tag === 'sweep') sfSfx.whoosh(); }
      if (this.hitIds.has(wi)) continue;
      if (overlap(metaRect(this.sh, this, w.hit), playerHurtbox()) && hurtPlayer(sfDmg(dmg, this), P.x < this.x ? -1 : 1, this.atkId * 10 + wi, { src: this })) this.hitIds.add(wi);
    }
  }
  planetPos(pl) { const c = this.core, ry = this.orbitR > 60 ? 0.55 : 0.4; return { x: c.x + Math.cos(pl.a) * pl.r, y: c.y + Math.sin(pl.a) * pl.r * ry, z: Math.sin(pl.a) }; }
  planetContact() {
    if (this.state === 'stagger') return;
    for (const pl of this.planets) {
      if (pl.gone) continue;
      const q = this.planetPos(pl);
      if (overlap(rect(q.x - 5, q.y - 5, q.x + 5, q.y + 5), playerHurtbox())) { if (hurtPlayer(sfDmg(this.state === 'orbit' ? SF_OD.orbit : SF_OD.planet, this), P.x < q.x ? -1 : 1, 'orb' + pl.k + Math.floor(time * 2), { src: this })) break; }
    }
  }
  launchPlanet() {
    const pl = this.planets.find(q => !q.gone); if (!pl) return;
    pl.gone = true; const q = this.planetPos(pl), fl = this.floor, T = 0.8, b = this;
    const tx = clamp(P.x, this.L - 20, this.R + 20);
    sfSfx.whoosh();
    const h = { x: q.x, y: q.y + 6, w: 12, h: 12, vx: (tx - q.x) / T, vy: -150, dmg: sfDmg(SF_OD.launch, this), id: ++hazardId, life: 4, t: 0, bounces: 0, k: pl.k,
      update: (h, dt) => {
        h.vy += 520 * dt; h.x += h.vx * dt; h.y += h.vy * dt;
        if (h.y >= fl) { h.y = fl; h.vy = -h.vy * 0.62; h.bounces++; h.id = ++hazardId; shake = Math.max(shake, 2); sfx.land(); spawnFx('dust', h.x, fl, 1); if (h.bounces > 2) { h.life = 0; } }
        if (h.x < b.L - 40 || h.x > b.R + 40) h.vx = -h.vx;
        if (Math.random() < 0.5) particles.push({ x: h.x, y: h.y - 6, vx: 0, vy: 0, life: 0.3, kind: 'star' });
      },
      sfDraw: h => { const s = fxSheet('sf_planet'); if (s.ok) drawSprite(s, s.tag('planet').from + h.k % 4, h.x, h.y - 6, 1, { center: true }); addLight(h.x, h.y - 6, 26, '220,200,160', 0.7); } };
    hazards.push(h);
    setTimeout(() => { pl.gone = false; pl.r = 4; }, 3200);
  }
  updateBeams(dt) {
    const b = this;
    for (const bm of this.beams) {
      bm.t += dt; bm.a += bm.da * dt;
      if (bm.t > 0.05 && bm.t < bm.T) {
        const L = 420, ex = bm.x + Math.cos(bm.a) * L, ey = bm.y + Math.sin(bm.a) * L, hb = playerHurtbox(), px = (hb.x0 + hb.x1) / 2, py = (hb.y0 + hb.y1) / 2;
        const t = clamp(((px - bm.x) * (ex - bm.x) + (py - bm.y) * (ey - bm.y)) / (L * L), 0, 1), dd = Math.hypot(bm.x + (ex - bm.x) * t - px, bm.y + (ey - bm.y) * t - py);
        if (!bm.hit && dd < 9 && hurtPlayer(sfDmg(SF_OD.beam, this), Math.cos(bm.a) > 0 ? 1 : -1, bm.id, { src: this })) bm.hit = true;
      }
    }
    this.beams = this.beams.filter(bm => bm.t < bm.T + 0.2);
  }
  enterPhase2() {
    this.phase = 2; this.pendingPhase = false; this.stance = 0; flashScreen = 0.5; shake = 8; sfSfx.shatter();
    for (let i = 4; i < 6; i++) this.planets.push({ a: i * 1.05, k: i % 4, r: 4, gone: false });
    this.setA('idle', 'idle', true); this.cool = 0.8; this.y = this.hoverY;
    bossPhase2Scene(this);
  }
  die() {
    this.state = 'dead'; this.anim.set('death', false); this.beams = [];
    hazards = []; projectiles = projectiles.filter(p => p.owner === 'player');
    shake = 12; hitstop = 0.3; slowmo = 1.4; flashScreen = 0.6; sfSfx.shatter(); sfx.felled();
    for (const pl of this.planets) { const q = this.planetPos(pl); for (let i = 0; i < 8; i++) particles.push({ x: q.x, y: q.y, vx: rand(-80, 80), vy: -rand(20, 100), g: 300, life: 1, kind: 'star' }); }
    this.planets = [];
    victoryBanner = { text: 'THE ORRERY STILLS', t: 0 };
    this.rewards();
  }
  drawPlanets(front) {
    const s = fxSheet('sf_planet'); if (!s.ok) return;
    for (const pl of this.planets) {
      if (pl.gone) continue;
      const q = this.planetPos(pl); if ((q.z >= 0) !== front) continue;
      drawSprite(s, s.tag('planet').from + pl.k % 4, q.x, q.y, 1, { center: true, alpha: front ? 1 : 0.85 });
      if (this.state === 'orbit') addLight(q.x, q.y, 22, '220,210,180', 0.6);
    }
  }
  draw() {
    this.drawPlanets(false);
    const opt = this.flash > 0 ? { flash: this.flash * 0.6, flashColor: '#e8f0ff' } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' } : {};
    if (this.sh.ok) drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    else { g.fillStyle = '#8a6024'; g.beginPath(); g.arc(this.core.x, this.core.y, 14, 0, 6.3); g.fill(); }
    this.drawPlanets(true);
    // the ring sweep glows along the floor band while it's live
    if (this.state === 'sweep' && this.anim.i >= 3 && this.anim.i <= 7) { g.globalCompositeOperation = 'lighter'; g.fillStyle = 'rgba(255,210,140,0.35)'; g.fillRect(Math.round(this.x - 62), Math.round(this.y - 24), 124, 3); g.globalCompositeOperation = 'source-over'; addLight(this.x, this.y - 22, 70, '255,210,140', 0.8); }
    // beam: aim line, then the beam itself
    const c = this.core;
    if (this.state === 'charge' && this.aim && !this.aim.fired) {
      const a = Math.atan2(this.aim.ty - c.y, this.aim.tx - c.x), k = Math.min(1, this.aim.t / 0.8);
      g.globalCompositeOperation = 'lighter'; g.strokeStyle = `rgba(190,210,255,${this.aim.locked ? 0.5 + 0.4 * Math.sin(time * 40) : 0.15 + 0.25 * k})`; g.lineWidth = 1;
      g.beginPath(); g.moveTo(c.x, c.y); g.lineTo(c.x + Math.cos(a) * 420, c.y + Math.sin(a) * 420); g.stroke(); g.globalCompositeOperation = 'source-over';
      if (Math.random() < 0.5) particles.push({ x: c.x + rand(-4, 4) + this.face * 6, y: c.y + rand(-4, 4), vx: 0, vy: 0, life: 0.3, kind: 'star' });
    }
    for (const bm of this.beams) {
      if (bm.t > bm.T) continue;
      const ex = bm.x + Math.cos(bm.a) * 420, ey = bm.y + Math.sin(bm.a) * 420, w = bm.t < 0.08 ? 2 : 6 * (1 - bm.t / bm.T) + 2;
      g.globalCompositeOperation = 'lighter';
      g.strokeStyle = 'rgba(120,150,255,0.5)'; g.lineWidth = w + 4; g.beginPath(); g.moveTo(bm.x, bm.y); g.lineTo(ex, ey); g.stroke();
      g.strokeStyle = 'rgba(235,242,255,0.95)'; g.lineWidth = Math.max(1, w * 0.5); g.beginPath(); g.moveTo(bm.x, bm.y); g.lineTo(ex, ey); g.stroke();
      g.globalCompositeOperation = 'source-over'; g.lineWidth = 1;
      for (let i = 0; i < 6; i++) { const t = Math.random(); addLight(bm.x + (ex - bm.x) * t * 0.6, bm.y + (ey - bm.y) * t * 0.6, 30, '200,215,255', 0.8); }
    }
    if (this.critable()) { g.fillStyle = '#ffd070'; const y = Math.round(this.y - 90 + Math.sin(time * 8) * 1.5); g.fillRect(Math.round(this.x) - 1, y, 3, 3); g.fillRect(Math.round(this.x), y - 1, 1, 5); g.fillRect(Math.round(this.x) - 2, y + 1, 5, 1); }
  }
}
BOSS_SPAWN.orrery = (cx, fy) => new OrrerySentinel(cx, fy);
BOSS_CUTS.orrery = b => [
  act(() => { b.anim.set('stagger', false); b.anim.i = b.anim.n - 1; b.anim.done = true; b.y = b.floor + 6; b.orbitR = 4; }),
  bossPan(b, 50, 1.0),
  say('', 'A great orrery of bronze and starlight still keeps the hours of a sky that fell.'),
  { dur: 1.2, tween: (dt, k) => { b.y = lerp(b.floor + 6, b.hoverY, k); b.orbitR = lerp(4, 40, k); for (const pl of b.planets) pl.r = b.orbitR; } },
  act(() => { b.anim.set('charge', false); sfSfx.hum(); sfx.glint(); }), wait(0.9),
  act(() => { b.anim.set('idle', true); flashScreen = 0.3; sfSfx.chime(0.6); }), wait(0.3),
];
PHASE2_LINES.orrery = ['', 'Two more worlds wake and join its orbit.'];

// ================================================================== debug handle
try { window.__sf = { SFM, SFX4, SFR, SFSKY, SFA }; window.__sfSolid = (x, y) => solidAtPx(x, y); } catch (e) {}
