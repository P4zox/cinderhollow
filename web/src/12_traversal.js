// ------------------------------------------------------------------ traversal techniques: Root Hook, Ember Dash, Gale Cloak, Cinder Slam
Object.assign(ITEMS, {
  hook: { name: 'Root Hook', icon: 'i_hook', sheet: 'ui_icons2', desc: 'A living golden root that seeks anchors. Press H (or C) near a golden ring to grapple and swing; jump to let go.' },
  emberdash: { name: 'Ember Dash', icon: 'i_emberdash', sheet: 'ui_icons2', desc: 'Your roll burns through ash. Roll into an ash veil to pass through it, untouchable.' },
  gale: { name: 'Gale Cloak', icon: 'i_gale', sheet: 'ui_icons2', desc: 'Your cape catches the wind. Hold jump while falling to glide; ride updrafts upward.' },
  slam: { name: 'Cinder Slam', icon: 'i_slam', sheet: 'ui_icons2', desc: 'In the air, hold S and press K to slam down. Shatters cracked floors and hurls foes aside.' },
});
const TECHNIQUES = ['hook', 'emberdash', 'gale', 'slam'];
const HOOK_RANGE = 130;

// ---- map features: built by enterRoom from '@' hooks, '%' veils, '|' updrafts, 'Y' cracked floors
function buildTraversalProps(def) {
  room.hooks = []; room.veils = []; room.updrafts = [];
  const runs = (ch, cb) => {
    for (let x = 0; x < def.w; x++) for (let y = 0; y < def.h; y++) {
      if (def.map[y][x] !== ch || (y > 0 && def.map[y - 1][x] === ch)) continue;
      let y1 = y; while (y1 + 1 < def.h && def.map[y1 + 1][x] === ch) y1++;
      cb(x, y, y1);
    }
  };
  for (let y = 0; y < def.h; y++) for (let x = 0; x < def.w; x++) if (def.map[y][x] === '@') {
    const h = { x: x * TILE + 8, y: y * TILE + 8 }; room.hooks.push(h);
    props.push({ type: 'hookpoint', x: h.x, y: h.y + 8, face: 1, sh: sheet('prop_hookpoint'), anim: new Anim(sheet('prop_hookpoint'), 'loop', true), hook: h });
  }
  runs('%', (x, y0, y1) => {
    const v = { x0: x * TILE, x1: x * TILE + TILE, y0: y0 * TILE, y1: (y1 + 1) * TILE };
    room.veils.push(v);
    room.dyn.push({ ...v, veil: true, on: () => !phasing() });
    props.push({ type: 'veil', x: x * TILE + 8, y: (y1 + 1) * TILE, face: 1, sh: sheet('prop_ashveil'), anim: new Anim(sheet('prop_ashveil'), 'loop', true), h: (y1 - y0 + 1) * TILE });
  });
  runs('|', (x, y0, y1) => {
    const u = { x0: x * TILE, x1: x * TILE + TILE, y0: y0 * TILE, y1: (y1 + 1) * TILE };
    room.updrafts.push(u);
    props.push({ type: 'updraft', x: x * TILE + 8, y: (y1 + 1) * TILE, face: 1, sh: sheet('prop_updraft'), anim: new Anim(sheet('prop_updraft'), 'loop', true), h: (y1 - y0 + 1) * TILE });
  });
}
function phasing() { return P && SAVE.items.emberdash && P.state === 'roll' && P.anim.i <= 6; }
function inUpdraft(b) { return room.updrafts && room.updrafts.some(u => b.x > u.x0 - 2 && b.x < u.x1 + 2 && b.y - 10 > u.y0 - 40 && b.y - 10 < u.y1); }
function drawTallProp(p) {   // veils / updrafts tile their sprite up the whole column
  if (!p.sh.ok) { g.fillStyle = p.type === 'veil' ? 'rgba(120,110,110,0.45)' : 'rgba(200,220,255,0.15)'; g.fillRect(p.x - 8, p.y - p.h, 16, p.h); return; }
  const fh = p.sh.fh;
  for (let yy = p.y; yy > p.y - p.h + 1; yy -= fh) drawSprite(p.sh, p.anim.frame, p.x, yy, 1, { bottom: true, alpha: p.type === 'veil' ? 0.9 : 0.7 });
}

// ---- Root Hook
function tryHook() {
  if (!SAVE.items.hook || !room.hooks || !room.hooks.length) return false;
  let best = null, bd = 1e9;
  for (const h of room.hooks) {
    const dx = h.x - P.x, dy = h.y - (P.y - 20), d = Math.hypot(dx, dy);
    if (d > HOOK_RANGE || dy > 30) continue;
    const score = d - (Math.sign(dx) === P.face ? 40 : 0);
    if (score < bd && lineOfSight(P.x, P.y - 22, h.x, h.y + 6)) { bd = score; best = h; }
  }
  if (!best) return false;
  const dx = P.x - best.x, dy = (P.y - 34) - best.y;
  P.hook = { h: best, len: clamp(Math.hypot(dx, dy), 38, 96), ang: Math.atan2(dx, dy), av: 0, zip: true };
  setP('hook', pHas('hook_throw') ? 'hook_throw' : 'jump_up', false);
  sfx.shoot(); tone(660, 0.15, 0.05, 'triangle', 1.5);
  return true;
}
function updateHook(dt) {
  const H = P.hook, h = H.h;
  const dx = P.x - h.x, dy = (P.y - 34) - h.y, d = Math.hypot(dx, dy);
  if (H.zip) {   // reel in until we're at rope length
    H.ang = Math.atan2(dx, dy);
    if (d > H.len + 2) { const k = Math.min(1, 380 * dt / d); P.x -= dx * k; P.y -= dy * k; }
    else { H.zip = false; H.av = clamp((P.vx * Math.cos(H.ang)) / H.len, -3, 3); if (pHas('hook_swing')) P.anim.set('hook_swing', true); }
  } else {
    const ax = inputX();
    H.av += (-(900 / H.len) * Math.sin(H.ang) + ax * 3.2 * Math.cos(H.ang)) * dt;   // pendulum + pumping
    H.av *= Math.pow(0.8, dt); H.av = clamp(H.av, -4.2, 4.2);
    H.ang += H.av * dt;
    const nx = h.x + Math.sin(H.ang) * H.len, ny = h.y + Math.cos(H.ang) * H.len + 34;
    const bx = { x: nx, y: ny, w: P.w, h: P.h };
    let blocked = false;
    for (const xx of [nx - 4, nx + 4]) for (const yy of [ny - 2, ny - 13, ny - 24]) if (solidAtPx(xx, yy)) blocked = true;
    if (blocked) { H.av *= -0.3; } else { P.vx = (nx - P.x) / dt; P.vy = (ny - P.y) / dt; P.x = nx; P.y = ny; }
    if (Math.abs(H.av) > 0.2) P.face = H.av * Math.cos(H.ang) > 0 ? 1 : -1;
  }
  P.ground = false;
  if (Math.random() < 0.3) particles.push({ x: lerp(P.x, h.x, Math.random()), y: lerp(P.y - 26, h.y, Math.random()), vx: 0, vy: 0, life: 0.3, kind: 'gold' });
  if (take('jump') || take('hook')) releaseHook(true);
  else if (peek('roll')) { releaseHook(false); }
}
function releaseHook(boost) {
  const H = P.hook; P.hook = null;
  if (boost && H && !H.zip) { const tv = H.av * H.len; P.vx = clamp(tv * Math.cos(H.ang), -260, 260); P.vy = Math.min(-tv * Math.sin(H.ang) * 0.9, 0) - 160; }
  else if (boost) P.vy = -200;
  P.airDash = true; if (SAVE.items.wings) P.airJumps = 1;
  setP('air', 'jump_up', false); sfx.jump();
}
function drawHookLine() {
  if (!P || P.state !== 'hook' || !P.hook) return;
  const h = P.hook.h, x0 = P.x + P.face * 4, y0 = P.y - 33;
  const n = Math.ceil(Math.hypot(h.x - x0, h.y - y0) / 3);
  for (let i = 0; i <= n; i++) {
    const t = i / n, x = lerp(x0, h.x, t), y = lerp(y0, h.y, t) + Math.sin(t * Math.PI) * (P.hook.zip ? 4 : 1.5);
    g.fillStyle = i % 3 ? '#b88a3a' : '#ffd77a'; g.fillRect(Math.round(x), Math.round(y), 1, 1);
  }
  addLight(h.x, h.y, 30, '255,210,120', 0.8);
}

// ---- Gale Cloak glide
function canGlide() { return SAVE.items.gale && P.state === 'air' && held.has('jump') && P.vy > 20 && !P.dj; }
function updateGlide(dt) {
  const ax = inputX();
  P.vx = approach(P.vx, ax * (charmOn('c_feather') ? 150 : 135), 520 * dt);
  if (ax) P.face = ax;
  const up = inUpdraft(P);
  const fe = charmOn('c_feather');   // Stormcrow Feather: longer, floatier glides
  P.vy = approach(P.vy, up ? -170 : fe ? 26 : 42, (up ? 900 : 1100) * dt);
  if (Math.random() < 0.3) spawnFx(fxOr('gale', 'dust'), P.x - P.face * 8, P.y - 20, P.face);
  if (up && Math.random() < 0.5) particles.push({ x: P.x + rand(-8, 8), y: P.y + rand(-4, 8), vx: 0, vy: -rand(40, 90), life: 0.4, kind: 'dust' });
  if (!held.has('jump') || P.ground) setP(P.ground ? 'land' : 'air', P.ground ? (pHas('land') ? 'land' : 'idle') : 'jump_fall', false);
  else if (take('roll') && P.airDash) { doRoll(ax); }
}

// ---- Cinder Slam
function startSlam() {
  P.vx = 0; P.vy = -80; P.slamT = 0;
  setP('slam', pHas('slam_dive') ? 'slam_dive' : 'attack_down', true);
  sfx.heavySwing(); spend(18);
}
function updateSlam(dt) {
  P.slamT += dt;
  if (P.slamT > 0.08) P.vy = Math.min(P.vy + 2400 * dt, 520);
  if (Math.random() < 0.8) particles.push({ x: P.x + rand(-5, 5), y: P.y - rand(0, 20), vx: rand(-10, 10), vy: -rand(20, 60), life: 0.35, kind: 'fire' });
}
function slamImpact() {
  smashLanded();
  shake = 10; hitstop = 0.09; sfx.boom(); sfx.crumble();
  spawnFx(fxOr('slam_impact', 'shockwave'), P.x, P.y, 1, null, { bottom: true });
  const r = rect(P.x - 58, P.y - 30, P.x + 58, P.y + 2);
  for (const t of targets()) { const hb = hbOf(t); if (hb && overlap(r, hb)) t.hit({ dmg: outgoing(D.heavy, 1.8, 'melee'), poise: 80, dir: t.x > P.x ? 1 : -1, kind: 'heavy', x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, melee: true, big: true }); }
  for (let i = 0; i < 26; i++) particles.push({ x: P.x + rand(-40, 40), y: P.y - rand(0, 6), vx: rand(-110, 110), vy: -rand(40, 160), g: 420, life: rand(0.5, 1), kind: Math.random() < 0.5 ? 'rock' : 'fire' });
  // shatter cracked floors under and around the impact
  const tx0 = Math.floor((P.x - 22) / TILE), tx1 = Math.floor((P.x + 22) / TILE), ty0 = Math.floor((P.y + 1) / TILE);
  let broke = false;
  for (let ty = ty0; ty <= ty0 + 2; ty++) for (let tx = tx0; tx <= tx1; tx++) {
    if (tx < 0 || ty < 0 || tx >= room.w || ty >= room.h) continue;
    const t = room.grid[ty * room.w + tx];
    if (t === T_CRACK || t === T_BREAK) { breakCrackCluster(tx, ty); broke = true; }
  }
  if (broke) { P.ground = false; P.vy = 60; toast('The floor gives way'); }
  setP(broke ? 'air' : 'land', broke ? 'jump_fall' : (pHas('slam_land') ? 'slam_land' : 'land'), false);
}
function breakCrackCluster(tx0, ty0) {
  const stack = [[tx0, ty0]], seen = new Set();
  while (stack.length) {
    const [x, y] = stack.pop(), k = x + ',' + y;
    if (seen.has(k) || x < 0 || y < 0 || x >= room.w || y >= room.h) continue;
    const t = room.grid[y * room.w + x]; if (t !== T_CRACK && t !== T_BREAK) continue;
    seen.add(k); room.grid[y * room.w + x] = T_EMPTY; SAVE.flags[brokenKey(room.def, x, y)] = 1;
    for (let i = 0; i < 8; i++) particles.push({ x: x * TILE + rand(0, 16), y: y * TILE + rand(0, 16), vx: rand(-80, 80), vy: -rand(20, 120), g: 420, life: rand(0.6, 1.2), kind: 'rock' });
    stack.push([x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]);
  }
  renderRoomLayers(room); saveGame();
}

// ---- hooks called from the player update
function traversalStart(ax) {
  if (peek('hook') && P.state !== 'hook') { take('hook'); if (tryHook()) return true; }
  if (!P.ground && SAVE.items.slam && held.has('down') && peek('heavy') && P.st > 0) { take('heavy'); if (!smashReady()) return true; smashStart(); startSlam(); return true; }
  return false;
}
function traversalUpdate(dt) {
  if (P.state === 'hook') { updateHook(dt); return 'skip-physics'; }
  if (P.state === 'glide') { updateGlide(dt); return true; }
  if (P.state === 'slam') { updateSlam(dt); return true; }
  if (canGlide()) { setP('glide', pHas('glide') ? 'glide' : 'jump_fall', true); return true; }
  return false;
}
function traversalAfterMove(landedFrom) {
  if (landedFrom === 'slam') slamImpact();
  // ember dash: burn through veils; if a dash ends inside a veil keep phasing until clear
  if (SAVE.items.emberdash && P.state === 'roll' && P.anim.i <= 6) {
    if (Math.random() < 0.6) particles.push({ x: P.x - P.face * rand(4, 14), y: P.y - rand(4, 22), vx: -P.face * rand(20, 60), vy: -rand(0, 30), life: 0.4, kind: 'ember' });
    if (P.anim.changed && P.anim.i === 1) spawnFx(fxOr('ember_dash', 'dust'), P.x - P.face * 12, P.y - 14, P.face);
    for (const v of room.veils || []) if (P.x + 5 > v.x0 && P.x - 5 < v.x1 && P.y > v.y0 && P.y - 26 < v.y1) {
      if (!v.burst || v.burst < time - 0.5) { v.burst = time; spawnFx(fxOr('veil_burst', 'dust'), (v.x0 + v.x1) / 2, v.y1, P.face, null, { bottom: true }); sfx.fire(); }
      if (P.anim.i >= 5) { P.anim.i = 5; P.anim.t = 0; }   // keep phasing while inside
    }
  }
}
function grantTechniques() { for (const t of TECHNIQUES) SAVE.items[t] = 1; saveGame(); sfx.levelup(); banner('Techniques', 'Root Hook (H), Ember Dash (roll into ash veils), Gale Cloak (hold jump while falling), Cinder Slam (S + K in the air). Plunge: K in the air. Backstep strike: roll away, then J.', 'shard'); }
// Stormcrow Feather: a second air dash (refreshes once the first air roll has finished)
HOOKS.update.push(() => {
  if (!P || !charmOn('c_feather')) return;
  if (P.ground) P.fDash = 1;
  else if (!P.airDash && P.fDash && P.state !== 'roll') { P.airDash = true; P.fDash = 0; }
});
