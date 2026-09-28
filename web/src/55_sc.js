// ------------------------------------------------------------------ EXPANSION 3 — agent SC: Starfall Crater, NEO-HALLOW, The Ember, The Hermit's Hollow
// Rooms: tools/regions/85_sc.py (SF10–SF19, NH8–NH17, E4–E7, H2–H4). Art: art/gen_xsc*.py -> assets xsc_*.
// Decor + region mechanics are `t:'xsc'` spawns (XS_KIND below); kit/sys objects come from 42_kit.js / 43_systems.js.
// Mechanics: gravity wells (Starfall), meteor stepping stones (kit `phase` drawn as meteors), steam vents, maglev cars
// (kit movers that surface from the data stream), billboards / glitch slabs (kit phases), the Glitch Run's beat, the
// Lens Array's etched light-paths, the Firewall's wiring, one-way shortcut doors, painted vista backdrops.
// Charms (trial rewards): c_x3_moon Moonlit Stride · c_x3_glitch Glitch Driver · c_x3_flame Heart of the First Flame.
// Every top-level name is prefixed xs / XS (all region files share one scope).

const XS = { roomObj: null, wells: [], steams: [], props: [], beat: null, lensTurns: 0, lensHint: 0, fireFlips: 0, fireHint: 0, bakeT: 0, baked: false,
  moon: 0, glitch: null, meteorT: 0, trialAttempts: -1 };
const xsIn = (...b) => !!room && b.includes(room.def.biome);
const xsR = (x, y, w, h, c) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
const xsSh = n => sheet(n);
function xsDraw(name, tag, i, x, y, face = 1, opt = {}) {   // a frame of a tagged sheet, anchored bottom-centre; false if not loaded
  const sh = sheet(name); if (!sh.ok || !sh.has(tag)) return false;
  const t = sh.tag(tag), f = t.from + (((i % (t.to - t.from + 1)) + (t.to - t.from + 1)) % (t.to - t.from + 1));
  drawSprite(sh, f, x, y, face, { bottom: true, ...opt }); return true;
}
const xsLoop = (name, tag, fps, seed = 0) => { const sh = sheet(name); if (!sh.ok || !sh.has(tag)) return 0; const t = sh.tag(tag); return Math.floor(time * fps + seed) % (t.to - t.from + 1); };
function xsLineP(x0, y0, x1, y1, c, a = 1) {   // pixel-clean line
  const n = Math.max(1, Math.ceil(Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)))); g.fillStyle = c; g.globalAlpha = a;
  for (let i = 0; i <= n; i++) g.fillRect(Math.round(lerp(x0, x1, i / n)), Math.round(lerp(y0, y1, i / n)), 1, 1);
  g.globalAlpha = 1;
}
const xsVis = (x, y, m = 80) => x > cam.x - m && x < cam.x + W + m && y > cam.y - m && y < cam.y + H + m;
const xsSfx = {
  impact: (v = 1) => { noise(0.35, 700, 0.8, 0.28 * v, 'lowpass', 0.5); tone(80, 0.3, 0.12 * v, 'sine', 0.5); tone(1800, 0.25, 0.03 * v, 'triangle', 0.6); },
  whistle: (v = 1) => tone(2400, 0.5, 0.025 * v, 'sine', 0.35),
  crumble: (v = 1) => { noise(0.3, 1600, 1, 0.14 * v, 'bandpass', 0.6); tone(300, 0.2, 0.03 * v, 'triangle', 0.5); },
  hiss: (v = 1) => noise(0.5, 3200, 1.2, 0.1 * v, 'highpass', 1.1),
  steam: (v = 1) => { noise(0.9, 2400, 0.9, 0.2 * v, 'bandpass', 1.4); noise(0.4, 400, 0.8, 0.08 * v, 'lowpass'); },
  chime: (f = 1) => { tone(1568 * f, 1.4, 0.03, 'sine', 1.002); tone(2093 * f, 1.1, 0.02, 'sine'); tone(3136 * f, 0.7, 0.012, 'triangle'); },
  tick: hi => tone(hi ? 1760 : 1175, 0.05, 0.035, 'square', hi ? 1.2 : 0.9),
  hum: () => { tone(120, 0.6, 0.04, 'sine', 1.01); tone(180, 0.5, 0.02, 'triangle'); },
};

// ================================================================== lore (the Hallow Chronicle)
Object.assign(LORE_PAGES, {
  sc_1: { region: 'starfall', title: 'The Stargazer\'s Seat', text: 'Nine astronomers kept the dome. Eight of them are named on the lintel. The ninth name has been chiselled away, carefully, by someone who knew the letters.\nThey came up this road every night for four hundred years to count the falling lights. On clear nights they counted to a thousand before dawn. On the last night they counted one, and it was enough.' },
  sc_2: { region: 'starfall', title: 'A Pilgrim\'s Tally', text: 'Scratched on a shard of glass, in a hand that grew worse line by line:\nNine days on the road. The stones fall where they please, but they cool. Step on them while they still glow and they hold you. Wait, and they break.\nI have learned to walk on falling stars. I do not think I will learn anything else.' },
  sc_3: { region: 'starfall', title: 'The Fallen Star', text: 'The star did not burn out when it struck. It is burning still, under the plain, and the glass around it is only the ground remembering the heat.\nThe pilgrims called it the Heart of the Sky and came to warm their hands on it. The heart does not warm hands. It takes the warmth out of them, slowly, and gives back light.' },
  sc_4: { region: 'starfall', title: 'The Astronomer\'s Slate', text: 'Chalk on black slate, the last lesson:\nThe lens in the roof gathers what the sky gives. Turn the lower lenses to send it where it is needed. The old paths are still in the stone; where the light has run a thousand times, the wall remembers.\nWest, then east, then down. One lamp at a time. The reliquary opens for patience, not for strength.' },
  sc_5: { region: 'starfall', title: 'The Crater Edge', text: 'From the rim the whole crater lies open: the black glass plain, the shattered observatory, the heart of the fall still breathing its cold blue light.\nThey say the old gods were a garden, and the star was the frost. If that is so, then this is the garden\'s last morning, and it has lasted a thousand years.' },
  sc_6: { region: 'starfall', title: 'The Comet\'s Heart', text: 'A second light followed the star down, and no one counted it.\nIt lodged here in the spire\'s crown and went on burning with nothing to burn. When Astrel stood guard below, she would climb up to sit beside it, the pilgrims said, and speak to it as to a sister.\nThe comet does not answer. It is only very old, and very far from home.' },
  sc_7: { region: 'neohallow', title: 'Courier, Unfinished Delivery', text: 'Message buffer, recovered from a dead courier on the rooftop. The timestamp is four hundred years in the future and eleven minutes ago:\nPACKAGE 7 OF 9 — "ROOT SAMPLE, FOSSIL, DO NOT OPEN" — recipient not found — recipient never existed — recipient is you?\nDELIVERY FAILED. RETRYING. RETRYING. RETRYING.' },
  sc_8: { region: 'neohallow', title: 'dev_notes_final_FINAL(3).txt', text: 'TODO: lore for this room.\nTODO: fix the knight clipping into the Megablock stairs (won\'t fix: he likes it there).\nTODO: the hollows keep asking what year it is. Stop answering them. It only makes it worse.\nNOTE TO SELF: the seed in the chest is real. Everything else in this room is a placeholder, including, possibly, me.' },
  sc_9: { region: 'neohallow', title: 'FIREWALL — Maintenance Card', text: 'VAULT ACCESS: all four barriers must be open at once.\nEach terminal throws two barriers. The cables show which. Throwing a terminal twice undoes it.\nIf you are reading this, you are not authorised. Please continue anyway; nobody has been authorised for three hundred years.' },
  sc_10: { region: 'neohallow', title: 'Neon Skyline', text: 'From the roof the city goes on until the rain hides it. Cars cross the sky in rivers of light. Every window is lit and none of them has anyone behind it.\nFar out, where the towers thin, the Pale Root still stands, petrified, a grey spine through the neon. They built the city on its bones, and never once looked up.' },
  sc_11: { region: 'ember', title: 'The Cinder Road', text: 'A road-stone, worn smooth by bare feet:\nThis is the last road. Every shrine along it was lit by someone who meant to come back.\nThe first still holds an ember. The second, ash. The third, only the shape where the fire was. Count them as you pass, and walk softly: there are not many left who remember how to light them.' },
  sc_12: { region: 'ember', title: 'The Cinder Tree', text: 'Before the Hollow there was a tree, and before the tree there was a seed of the First Flame, dropped by a careless god.\nIt grew in fire instead of light. When the Hallow went grey, the Cinder Tree was the only thing that did not notice. It burns inside still, patiently, as if the rest of the world were only late.' },
  sc_13: { region: 'ember', title: 'The Last Hearth', text: 'Someone keeps this fire. The wood is always fresh, the ash always swept, the bench always free. No one has ever seen them.\nSit. Warm your hands. It is the only warm place left in the Hallow, and it asks nothing of you.\nWhen you rise, the fire will be exactly as high as it was. That is the only promise it makes, and it has never broken it.' },
  sc_14: { region: 'hermit', title: 'The Hidden Path', text: 'Cairns in the fog, each stone set by the same patient hand. Prayer flags, faded past colour.\nOswin walked this path every evening for sixty years, to sit in his garden and listen to the chimes. He said the wind told him who was coming, long before they came.\nIt told him about you, too. He waited anyway.' },
  sc_15: { region: 'hermit', title: 'The Hermit\'s Garden', text: 'Sage, bitterroot, ash-thyme, a row of something no one else has a name for. Wind chimes of old sword-steel, tuned by ear.\nOswin was a knight once, the story goes, and hung up his blade because it had never taught him anything. The garden taught him patience. The chimes taught him to listen.\nHe would want you to sit a while. He would not say so.' },
  sc_16: { region: 'hermit', title: 'Oswin\'s Stash', text: 'Under the floorboards: a jar of seeds, a whetstone worn to a sliver, a little bag of shards wrapped in a child\'s drawing of the Pale Root.\nA note, in a careful, shaking hand: For whoever beats me. I knew it would be someone. Take what is useful. Leave the drawing.' },
});

// ================================================================== charms (trial rewards)
registerGear({ charms: {
  c_x3_moon: { name: 'Moonlit Stride', desc: 'Starlight clings to your heels. Your leaps hang longer at their height, and you run a little faster.', iconSheet: 'xsc_icons' },
  c_x3_glitch: { name: 'Glitch Driver', desc: 'A fault in the world, kept in a charm. Your air dash carries 35% further and leaves afterimages that cut whatever they touch.', iconSheet: 'xsc_icons' },
  c_x3_flame: { name: 'Heart of the First Flame', desc: 'The hottest thing in the Hallow, cupped in your hand. Every spell and weapon art comes back 30% sooner.', iconSheet: 'xsc_icons' },
} });
// Heart of the First Flame: every cooldown 30% shorter (cdBase is looked up by name, so the timer and its HUD sweep agree)
{ const _cdBase = cdBase; cdBase = function (kind, id) { return _cdBase(kind, id) * (charmOn('c_x3_flame') ? 0.7 : 1); }; }
HOOKS.update.push(dt => {
  if (!P || P.state === 'dead' || !SAVE) return;
  // Moonlit Stride: a floatier apex, +8% run speed
  if (charmOn('c_x3_moon')) {
    if (!P.ground && P.state === 'air' && Math.abs(P.vy) < 70) P.vy -= (P.vy > 0 ? GRAV_DN : GRAV_UP) * 0.22 * dt;
    const ax = (held.has('right') ? 1 : 0) - (held.has('left') ? 1 : 0);
    if (ax && (P.state === 'run' || P.state === 'air') && Math.sign(P.vx) === ax && Math.abs(P.vx) > MAXV * 0.8) P.pushVx = (P.pushVx || 0) + ax * MAXV * 0.08;
    if (!P.ground && Math.abs(P.vy) < 70 && Math.random() < 0.3) particles.push({ x: P.x + rand(-5, 5), y: P.y - rand(0, 6), vx: 0, vy: rand(5, 15), life: 0.4, kind: 'star' });
  }
  // Glitch Driver: the air dash holds its last dashing frame ~35% longer and drops cutting afterimages
  if (charmOn('c_x3_glitch') && P.state === 'roll' && P.airRoll) {
    const G = XS.glitch && XS.glitch.anim === P.anim && XS.glitch.tag === P.anim.tag ? XS.glitch : (XS.glitch = { anim: P.anim, tag: P.anim.tag, ext: 0.32, t: 0 });
    if (P.anim.i >= Math.min(6, P.anim.n - 2) && G.ext > 0) { P.anim.hold(); G.ext -= dt; P.vx = P.face * 225; P.vy = 0; }
    if ((G.t -= dt) <= 0 && P.anim.i <= 6) {
      G.t = 0.05;
      projectiles.push({ owner: 'player', face: P.face, t: 0, hits: new Set(), kind: 'xs_glitch', x: P.x, y: P.y - 14, vx: 0, vy: 0, dmg: D.light * 0.35, life: 0.28, r: 9, pierce: true, static: true, poise: 8, xsGlitch: true, f: P.anim.frame, pf: P.face });
    }
  } else if (XS.glitch && P.state !== 'roll') XS.glitch = null;
});
HOOKS.render.push(() => {   // the Glitch Driver's afterimages: RGB-split silhouettes of the dash
  const sh = sheet('player'); if (!sh.ok) return;
  for (const pr of projectiles) if (pr.xsGlitch && pr.life > 0) {
    const a = Math.max(0, pr.life / 0.28);
    drawGlow(() => {
      drawSprite(sh, pr.f, pr.x - 2, pr.y + 14, pr.pf, { alpha: 0.35 * a, flash: 1, flashColor: '#ff3fc0' });
      drawSprite(sh, pr.f, pr.x + 2, pr.y + 14, pr.pf, { alpha: 0.35 * a, flash: 1, flashColor: '#3fe0ff' });
    });
  }
});

// ================================================================== decor + mechanics dispatcher
const XS_KIND = {};
SPAWNS.xsc = (s, c) => { const f = XS_KIND[s.kind]; if (f) { try { f(s, c); } catch (e) { console.error('xsc', s.kind, e); } } };
function xsEnsure() { if (XS.roomObj === room) return; Object.assign(XS, { roomObj: room, wells: [], steams: [], props: [], beat: null, bakes: [], baked: false, bakeT: 0 }); }
function xsProp(s, c, o) {   // a decor prop at the spawn's cell (x = centre, y = floor)
  xsEnsure();
  const p = { type: 'xs_' + s.kind, x: c.cx, y: c.fy, face: s.face || 1, s, anim: { update() {} }, draw() {}, seed: hash2(s.x * 7 + 1, s.y * 13 + 3) * 10, ...o };
  props.push(p); XS.props.push(p); return p;
}
function xsBake(fn) { xsEnsure(); XS.bakes.push(fn); }   // static art painted once into the room's back/front layers
function xsRunBakes() {
  if (XS.baked || !XS.bakes.length || !room.back) return;
  const bx = room.back.getContext('2d'), fx = room.front.getContext('2d');
  const G0 = g; try { for (const f of XS.bakes) f(bx, fx); } finally { g = G0; }
  XS.baked = true;
}

// ---------------------------------------------------------------- shared little decor
XS_KIND.glassgrass = (s, c) => xsProp(s, c, { draw() {
  const p = this; if (!xsVis(p.x, p.y)) return;
  if (xsDraw('xsc_s', 'glassgrass', Math.floor(p.seed) % 2, p.x, p.y + 1, p.seed > 5 ? 1 : -1)) return;
  for (let i = 0; i < 5; i++) { const h = 3 + ((p.seed * 7 + i * 3) % 6 | 0), x = p.x - 6 + i * 3; xsR(x, p.y - h, 1, h, i % 2 ? '#5a88c8' : '#34508a'); xsR(x, p.y - h, 1, 1, '#dce8ff'); }
} });
XS_KIND.grass = (s, c) => xsProp(s, c, { draw() {
  const p = this; if (!xsVis(p.x, p.y)) return;
  if (xsDraw('xsc_s', 'grass', Math.floor(p.seed) % 2, p.x, p.y + 1, 1)) return;
  for (let i = 0; i < 7; i++) { const h = 2 + ((p.seed * 5 + i * 7) % 5 | 0), sway = Math.round(Math.sin(time * 1.4 + i + p.seed) * 0.8); xsLineP(p.x - 7 + i * 2, p.y, p.x - 7 + i * 2 + sway, p.y - h, i % 3 ? '#4a5a3c' : '#6e7a4a'); }
} });

// ================================================================== STARFALL
// ---- gravity wells: a splinter of the star drags whatever leaps past it (the player only, while airborne)
XS_KIND.well = (s, c) => {
  const w = { x: c.cx, y: s.y * TILE + 8, R: (s.r || 5) * TILE, k: s.k || 1 };
  const p = xsProp(s, c, { x: w.x, y: w.y, glow: true, well: w, update(dt) {
    addLight(w.x, w.y, 44 + Math.sin(time * 3 + this.seed) * 4, '170,190,255', 0.75);
    if (xsVis(w.x, w.y) && Math.random() < 0.5) { const a = rand(0, 6.28), d = w.R * rand(0.6, 1); particles.push({ x: w.x + Math.cos(a) * d, y: w.y + Math.sin(a) * d, vx: -Math.cos(a) * d * 1.3, vy: -Math.sin(a) * d * 1.3, life: 0.7, kind: Math.random() < 0.7 ? 'star' : 'nebula' }); }
  }, draw() {
    if (!xsVis(w.x, w.y)) return;
    const pull = XS.wellPull === w ? 1 : 0.4;
    for (let k = 0; k < 3; k++) {   // contracting rings: the pull, made visible
      const r = w.R * (1 - ((time * 0.6 + k / 3 + this.seed) % 1));
      g.globalAlpha = 0.18 * pull * (r / w.R); g.strokeStyle = '#a8c8ff'; g.lineWidth = 1; g.beginPath(); g.ellipse(Math.round(w.x) + 0.5, Math.round(w.y) + 0.5, r, r * 0.9, 0, 0, 6.29); g.stroke();
    }
    g.globalAlpha = 1;
    const bob = Math.round(Math.sin(time * 1.3 + this.seed) * 2);
    if (!xsDraw('xsc_s', 'wellshard', xsLoop('xsc_s', 'wellshard', 8, this.seed), w.x, w.y + 12 + bob)) {
      xsR(w.x - 2, w.y - 7 + bob, 4, 14, '#5a88c8'); xsR(w.x - 1, w.y - 9 + bob, 2, 18, '#a8d8ff'); xsR(w.x, w.y - 5 + bob, 1, 6, '#ffffff');
    }
  } });
  XS.wells.push(w);
};
HOOKS.update.push(dt => {
  XS.wellPull = null;
  if (!room || !XS.wells.length || XS.roomObj !== room || !P || P.ground || ['hook', 'rest', 'dead', 'wall', 'slam'].includes(P.state)) return;
  for (const w of XS.wells) {
    const dx = w.x - P.x, dy = w.y - (P.y - 13), d = Math.hypot(dx, dy);
    if (d > w.R || d < 8) continue;
    const k = (1 - d / w.R) * w.k;
    P.pushVx = (P.pushVx || 0) + (dx / d) * 150 * k;
    P.vy += (dy / d) * 900 * k * dt;
    XS.wellPull = w;
  }
});
// ---- meteors: kit `phase` slabs with look:'meteor' fall out of the sky, cool into stepping stones, then crack apart
function xsMeteorDraw(o) {
  const X = o.d.x0, Y = o.d.y0, w = o.w, cx = X + w / 2;
  if (!xsVis(cx, Y, 260)) return;
  const on = o.solidNow;
  if (o.xsWas === undefined) o.xsWas = on;
  if (on && !o.xsWas && KIT.t > 0.2) {   // impact!
    if (xsVis(cx, Y, 40)) { xsSfx.impact(0.8); shake = Math.max(shake, 2); }
    for (let i = 0; i < 14; i++) particles.push({ x: cx + rand(-w / 2, w / 2), y: Y, vx: rand(-90, 90), vy: -rand(40, 160), g: 400, life: rand(0.4, 0.8), kind: i % 3 ? 'glass' : 'star' });
    o.xsHit = 0.5;
  } else if (!on && o.xsWas && KIT.t > 0.2) {
    if (xsVis(cx, Y, 40)) xsSfx.crumble(0.8);
    for (let i = 0; i < 12; i++) particles.push({ x: cx + rand(-w / 2, w / 2), y: Y + rand(0, 8), vx: rand(-30, 30), vy: rand(-20, 40), g: 300, life: rand(0.5, 1), kind: 'glass' });
  }
  o.xsWas = on; o.xsHit = Math.max(0, (o.xsHit || 0) - 1 / 60);
  if (on) {
    const warm = o.xsHit, crack = o.warnK || 0, j = crack > 0.4 ? Math.round(rand(-1, 1) * crack) : 0;
    if (!xsDraw('xsc_s', 'meteor', crack > 0.5 ? 2 : crack > 0.01 ? 1 : 0, cx + j, Y + 12, 1, { flash: warm * 0.8, flashColor: '#dce8ff' })) {
      xsR(X + 1 + j, Y, w - 2, 9, '#141a2e'); xsR(X + 3 + j, Y - 2, w - 6, 3, '#1e2a48'); xsR(X + 2 + j, Y + 1, w - 4, 1, '#5a88c8');
      for (let i = 4; i < w - 4; i += 5) xsR(X + i + j, Y + 3 + (i % 3), 2, 1, crack > 0.3 ? '#ffffff' : '#a8d8ff');
    }
    addLight(cx, Y + 2, 30 + warm * 40, '170,200,255', 0.5 + warm);
  } else {   // the next one, falling: a streak from the upper left onto its slot
    const period = o.spec.period || 2, on0 = (o.spec.on || [0, 0.5])[0], off = o.spec.offset || 0;
    const k = (((KIT.t / period + off) % 1) + 1) % 1; let left = (on0 - k) * period; if (left < 0) left += period;
    if (left < 0.9) {
      const u = left / 0.9, fx0 = cx - u * 150, fy0 = Y - u * 240;
      if (left < 0.85 && o.xsWhistle !== Math.floor(KIT.t / period)) { o.xsWhistle = Math.floor(KIT.t / period); if (xsVis(cx, Y, 30)) xsSfx.whistle(0.5); }
      drawGlow(() => {
        for (let t = 0; t < 10; t++) xsR(fx0 - t * 3, fy0 - t * 5, t < 2 ? 3 : 2, t < 2 ? 3 : 2, t < 3 ? '#ffffff' : t < 6 ? '#a8d8ff' : '#5a70c8');
        g.globalAlpha = 0.25 + 0.3 * (1 - u); xsR(X + 2, Y, w - 4, 1, '#a8d8ff'); g.globalAlpha = 1;   // where it will land
      });
      addLight(fx0, fy0, 40, '190,210,255', 0.9);
    } else { g.globalAlpha = 0.18; for (let x = X; x < X + w; x += 3) xsR(x, Y, 1, 1, '#a8d8ff'); g.globalAlpha = 1; }
  }
}
// ---- the ambient sky: meteors crossing over the crater (world-space streaks near the top of the view)
XS_KIND.meteorfall = (s, c) => xsProp(s, c, { streaks: [], heavy: false, draw() { xsDrawStreaks(this, 0.012); } });
XS_KIND.meteorshower = (s, c) => xsProp(s, c, { streaks: [], heavy: true, draw() { xsDrawStreaks(this, 0.07); } });
function xsDrawStreaks(p, rate) {
  if (Math.random() < rate) p.streaks.push({ x: cam.x + rand(-40, W + 120), y: cam.y + rand(-20, H * 0.45), vx: -rand(160, 260), vy: rand(90, 150), life: rand(0.5, 1.2), t: 0, big: Math.random() < 0.12 });
  drawGlow(() => {
    for (const q of p.streaks) {
      q.t += 1 / 60; q.x += q.vx / 60; q.y += q.vy / 60;
      const a = Math.min(1, q.t * 4) * Math.max(0, 1 - q.t / q.life), n = q.big ? 22 : 12, sp = Math.hypot(q.vx, q.vy);
      for (let i = 0; i < n; i++) { g.globalAlpha = a * (1 - i / n); xsR(q.x - q.vx / sp * i * 2, q.y - q.vy / sp * i * 2, i < 2 && q.big ? 2 : 1, 1, i < 3 ? '#ffffff' : '#a8c8ff'); }
      if (q.big) addLight(q.x, q.y, 50, '200,220,255', a * 0.7, { shadow: false });
    }
    g.globalAlpha = 1;
  });
  p.streaks = p.streaks.filter(q => q.t < q.life);
}
XS_KIND.crater = (s, c) => xsProp(s, c, { update() { addLight(this.x, this.y - 2, 26, '120,150,255', 0.35); }, draw() {
  const p = this; if (!xsVis(p.x, p.y)) return;
  g.globalAlpha = 0.9; xsR(p.x - 10, p.y - 1, 20, 1, '#060812'); xsR(p.x - 7, p.y - 2, 14, 1, '#0b0f22');
  g.globalAlpha = 0.6 + 0.2 * Math.sin(time * 1.5 + p.seed); xsR(p.x - 11, p.y - 2, 2, 1, '#5a88c8'); xsR(p.x + 9, p.y - 2, 2, 1, '#5a88c8'); xsR(p.x - 4, p.y - 1, 8, 1, '#34508a'); g.globalAlpha = 1;
} });
XS_KIND.emberrock = (s, c) => xsProp(s, c, { update() { addLight(this.x, this.y - 6, 22, '150,160,255', 0.4); }, draw() {
  const p = this; if (!xsVis(p.x, p.y)) return;
  if (xsDraw('xsc_s', 'emberrock', 0, p.x, p.y + 1, p.face)) return;
  xsR(p.x - 6, p.y - 7, 12, 7, '#141a2e'); xsR(p.x - 4, p.y - 9, 8, 2, '#1e2a48'); xsR(p.x - 3, p.y - 5, 1, 3, '#a882ff'); xsR(p.x + 2, p.y - 6, 2, 1, '#a8d8ff');
} });
XS_KIND.wayshrine = (s, c) => xsProp(s, c, { update() { addLight(this.x, this.y - 22, 40, '190,210,255', 0.7, LX_FLICKER); if (Math.random() < 0.05) particles.push({ x: this.x + rand(-2, 2), y: this.y - 22, vx: 0, vy: -rand(5, 12), life: 1, kind: 'star' }); }, draw() {
  const p = this; if (!xsVis(p.x, p.y)) return;
  if (xsDraw('xsc_s', 'wayshrine', 0, p.x, p.y + 1, 1)) return;
  xsR(p.x - 3, p.y - 18, 6, 18, '#2a2e40'); xsR(p.x - 5, p.y - 20, 10, 3, '#3a3e55'); xsR(p.x - 2, p.y - 25, 4, 5, '#a8d8ff'); xsR(p.x - 1, p.y - 24, 2, 3, '#ffffff');
} });
XS_KIND.dome = (s, c) => xsProp(s, c, { update() { addLight(this.x + 10, this.y - 50, 50, '170,190,255', 0.35); }, draw() {
  const p = this; if (!xsVis(p.x, p.y, 120)) return;
  if (xsDraw('xsc_l', 'dome', 0, p.x, p.y + 1, 1)) return;
  g.fillStyle = '#10142a'; g.beginPath(); g.arc(p.x, p.y - 8, 44, Math.PI, 0); g.fill(); xsR(p.x - 46, p.y - 8, 92, 8, '#161a30');
  for (let a = 0; a < 7; a++) { const t = Math.PI + a / 6 * Math.PI; xsLineP(p.x, p.y - 8, p.x + Math.cos(t) * 44, p.y - 8 + Math.sin(t) * 44, '#2a3050'); }
} });
XS_KIND.fallenstar = (s, c) => xsProp(s, c, { glow: false, update() {
  const p = this, pulse = 0.75 + 0.25 * Math.sin(time * 0.9);
  addLight(p.x, p.y - 60, 180 * pulse, '150,180,255', 1.1, { shadow: false }); addLight(p.x, p.y - 20, 70, '210,225,255', 0.9);
  if (Math.random() < 0.6) particles.push({ x: p.x + rand(-40, 40), y: p.y - rand(0, 60), vx: rand(-6, 6), vy: -rand(10, 30), life: rand(1.2, 2.4), kind: Math.random() < 0.75 ? 'star' : 'nebula' });
}, draw() {
  const p = this; if (!xsVis(p.x, p.y, 200)) return;
  if (xsDraw('xsc_l', 'fallenstar', xsLoop('xsc_l', 'fallenstar', 5), p.x, p.y + 4, 1)) return;
  drawGlow(() => {
    g.fillStyle = '#34508a'; g.beginPath(); g.moveTo(p.x - 30, p.y); g.lineTo(p.x - 8, p.y - 96); g.lineTo(p.x + 14, p.y - 70); g.lineTo(p.x + 34, p.y); g.fill();
    g.fillStyle = '#a8d8ff'; g.beginPath(); g.moveTo(p.x - 12, p.y); g.lineTo(p.x - 6, p.y - 80); g.lineTo(p.x + 6, p.y - 60); g.lineTo(p.x + 12, p.y); g.fill();
  });
} });
XS_KIND.craterglow = (s, c) => xsProp(s, c, { update() {
  const p = this; addLight(p.x, room.ph + 20, 260, '150,180,255', 0.9, { shadow: false });
  if (Math.random() < 0.5) particles.push({ x: cam.x + rand(0, W), y: room.ph - rand(0, 10), vx: rand(-4, 4), vy: -rand(20, 45), life: rand(2, 3.5), kind: Math.random() < 0.8 ? 'star' : 'nebula' });
} });
XS_KIND.comet = (s, c) => xsProp(s, c, { y: s.y * TILE + 8, update() {
  const p = this; addLight(p.x, p.y, 110 + Math.sin(time * 2) * 10, '190,210,255', 1.1, { shadow: false });
  if (Math.random() < 0.4) particles.push({ x: p.x + rand(-10, 10), y: p.y + rand(-10, 10), vx: rand(-20, 20), vy: rand(-20, 20), life: 0.8, kind: 'star' });
}, draw() {
  const p = this, bob = Math.sin(time * 0.8) * 2;
  drawGlow(() => {
    if (xsDraw('xsc_l', 'comet', xsLoop('xsc_l', 'comet', 6), p.x, p.y + 64 + bob, 1)) return;
    g.fillStyle = '#a8d8ff'; g.beginPath(); g.arc(p.x, p.y + bob, 10, 0, 6.29); g.fill(); g.fillStyle = '#ffffff'; g.beginPath(); g.arc(p.x, p.y + bob, 5, 0, 6.29); g.fill();
  });
  for (let i = 0; i < 5; i++) { const a = time * (0.6 + i * 0.13) + i * 1.3, r = 22 + i * 4; xsR(p.x + Math.cos(a) * r, p.y + bob + Math.sin(a) * r * 0.5, 2, 2, i % 2 ? '#a8d8ff' : '#5a88c8'); }
} });
XS_KIND.reflect = (s, c) => xsProp(s, c, { draw() {   // stars mirrored in the canyon's glass walls: a slow sparkle on visible star-glass
  if (Math.random() > 0.5) return;
  const tx = Math.floor((cam.x + rand(0, W)) / TILE), ty = Math.floor((cam.y + rand(0, H)) / TILE);
  if (tileAt(tx, ty) === SF_T_GLASS) particles.push({ x: tx * TILE + rand(2, 14), y: ty * TILE + rand(2, 14), vx: 0, vy: 0, life: 0.5, kind: 'star' });
} });
// ---- the Lens Array: faint etched veins show where the light once ran; a hint after three fruitless attempts
XS_KIND.veins = (s, c) => xsProp(s, c, { draw() {
  const pulse = 0.14 + 0.08 * Math.sin(time * 0.8);
  drawGlow(() => {
    (s.paths || []).forEach((path, k) => {
      const lit = typeof KIT !== 'undefined' && KIT.byId['s' + (k + 1)] && KIT.byId['s' + (k + 1)].active;
      for (let i = 0; i + 1 < path.length; i++) {
        const [x0, y0] = path[i], [x1, y1] = path[i + 1];
        xsLineP(x0 * TILE + 8, y0 * TILE + 8 + 3, x1 * TILE + 8, y1 * TILE + 8 + 3, lit ? '#dce8ff' : '#6a8ad8', lit ? 0.5 : pulse);
      }
    });
  });
} });
XS_KIND.lenshint = (s, c) => { xsEnsure(); XS.lensTurns = 0; XS.lensHint = 0; };
// ---- boss-sealed passages (Astrel's east wall, the Hollow's floor, Oswin's west wall): when the guardian falls in the room,
// the passage opens there and then (sys passages are otherwise only evaluated on room entry)
HOOKS.update.push(() => {
  if (!room || !['SF7', 'E3', 'H1'].includes(room.id) || (XS.passT = (XS.passT || 0) + 1) % 20) return;
  for (const p of props) if (p.type === 'sys_passage' && !p.open && p.s.cond && typeof sysCond === 'function' && sysCond(p.s.cond)) {
    p.open = true; for (const [x, y] of p.cells) room.grid[y * room.w + x] = T_EMPTY;
    renderRoomLayers(room); XS.baked = false;
    if (typeof SYS !== 'undefined') { SYS.reveal = { p, t: 0 }; if (typeof x3 === 'function') x3().seen[p.key] = 1; }
  }
});

// ================================================================== NEO-HALLOW
const XS_NEON = ['255,60,190', '80,210,255', '255,160,60', '90,255,210'];
const XS_NEONC = ['#ff3fc0', '#3fe0ff', '#ffb050', '#5affd2'];
XS_KIND.vending = (s, c) => xsProp(s, c, { update() { addLight(this.x, this.y - 18, 36, XS_NEON[(this.seed | 0) % 2], 0.7); }, draw() {
  const p = this; if (!xsVis(p.x, p.y)) return;
  if (xsDraw('xsc_m', 'vending', Math.floor(time * 2 + p.seed) % 2, p.x, p.y + 1, p.face)) return;
  xsR(p.x - 8, p.y - 30, 16, 30, '#161c33'); xsR(p.x - 6, p.y - 27, 12, 16, (p.seed | 0) % 2 ? '#13a3c9' : '#c21d97'); xsR(p.x - 5, p.y - 26, 10, 1, '#f2feff');
  xsR(p.x - 6, p.y - 8, 12, 4, '#070913');
} });
XS_KIND.dumpster = (s, c) => xsProp(s, c, { draw() {
  const p = this; if (!xsVis(p.x, p.y)) return;
  if (xsDraw('xsc_s', 'dumpster', 0, p.x, p.y + 1, p.face)) return;
  xsR(p.x - 12, p.y - 12, 24, 12, '#1c2a24'); xsR(p.x - 13, p.y - 13, 26, 2, '#2a3a32'); xsR(p.x - 10, p.y - 8, 20, 1, '#0e1612');
} });
XS_KIND.puddles = (s, c) => xsProp(s, c, { draw() {   // wet asphalt: rippling neon reflections along the floor
  const p = this, x0 = s.x * TILE, x1 = x0 + (s.w || 20) * TILE;
  for (let x = x0; x < x1; x += 11) {
    if (x < cam.x - 20 || x > cam.x + W + 20) continue;
    const k = hash2(x, 3), w = 6 + (k * 10 | 0); if (k < 0.3) continue;
    g.globalAlpha = 0.28; xsR(x, p.y - 1, w, 1, k < 0.55 ? '#3fe0ff' : k < 0.8 ? '#ff3fc0' : '#b8f6ff');
    const rp = (time * 2 + k * 9) % 1; g.globalAlpha = 0.2 * (1 - rp); xsR(x + w / 2 - rp * w / 2, p.y - 1, Math.max(1, rp * w), 1, '#f2feff');
  }
  g.globalAlpha = 1;
} });
XS_KIND.cables = (s, c) => xsProp(s, c, { draw() {   // sagging power lines
  const x0 = s.x * TILE + 8, x1 = (s.x1 || s.x + 10) * TILE + 8, y = s.y * TILE, sag = (s.sag || 3) * 4;
  if (x1 < cam.x || x0 > cam.x + W || y > cam.y + H + 20 || y + sag < cam.y - 10) return;
  for (let k = 0; k < 2; k++) {
    const yy = y + k * 5, n = Math.ceil((x1 - x0) / 2);
    g.fillStyle = k ? '#0b0d18' : '#161c2c';
    for (let i = 0; i <= n; i++) { const t = i / n, xx = x0 + (x1 - x0) * t; if (xx < cam.x - 2 || xx > cam.x + W + 2) continue; g.fillRect(Math.round(xx), Math.round(yy + Math.sin(t * Math.PI) * sag * (1 + k * 0.4)), 1, 1); }
  }
} });
XS_KIND.neonstrip = (s, c) => xsProp(s, c, { glow: true, update() { const p = this; for (let i = 0; i < (s.w || 4); i += 6) addLight(s.x * TILE + i * TILE / 1 + 8, (s.y + 1) * TILE + 3, 26, XS_NEON[s.c || 0], 0.35); }, draw() {
  const x0 = s.x * TILE, w = (s.w || 4) * TILE, y = (s.y + 1) * TILE + 2;
  if (x0 + w < cam.x || x0 > cam.x + W) return;
  const fl = hash2(Math.floor(time * 5), s.x) < 0.03 ? 0.4 : 1;
  g.globalAlpha = 0.35 * fl; xsR(x0, y - 1, w, 3, XS_NEONC[s.c || 0]); g.globalAlpha = fl; xsR(x0, y, w, 1, XS_NEONC[s.c || 0]); g.globalAlpha = 1;
} });
XS_KIND.windows = (s, c) => {   // lit windows: on building faces (solid cells) outdoors, or far apartments on back walls indoors
  const rx = s.rx ?? s.x, ry = s.ry ?? s.y, w = s.w || 4, h = s.h || 4;
  xsBake((bx, fx) => {
    const ctx = room.def.indoor ? bx : fx;
    for (let ty = ry; ty < ry + h; ty++) for (let tx = rx; tx < rx + w; tx++) {
      if (tx < 0 || ty < 0 || tx >= room.w || ty >= room.h) continue;
      const solid = isSolidT(room.grid[ty * room.w + tx]);
      if (room.def.indoor ? solid : !solid) continue;
      for (let k = 0; k < 2; k++) {
        const r = hash2(tx * 3 + k, ty * 5 + 11); if (r < (room.def.indoor ? 0.55 : 0.35)) continue;
        const col = r < 0.8 ? '#ffb050' : r < 0.9 ? '#3fe0ff' : '#ff9fe2';
        ctx.globalAlpha = room.def.indoor ? 0.22 : 0.55; ctx.fillStyle = col; ctx.fillRect(tx * TILE + 3 + k * 7, ty * TILE + 4, 4, 5);
        ctx.globalAlpha = room.def.indoor ? 0.12 : 0.3; ctx.fillStyle = '#fff0d0'; ctx.fillRect(tx * TILE + 3 + k * 7, ty * TILE + 4, 4, 1);
      }
    }
    ctx.globalAlpha = 1;
  });
};
XS_KIND.pipes = (s, c) => xsBake((bx, fx) => {   // pipes along the tunnel roof
  const y0 = s.y * TILE, x0 = s.x * TILE, x1 = x0 + (s.w || 10) * TILE;
  for (const [dy, a, b] of [[0, '#26263e', '#3c3c5c'], [6, '#1a1a2c', '#2e2e48']]) {
    fx.fillStyle = a; fx.fillRect(x0, y0 + dy, x1 - x0, 4); fx.fillStyle = b; fx.fillRect(x0, y0 + dy, x1 - x0, 1);
    for (let x = x0 + 12; x < x1; x += 40) { fx.fillStyle = '#44446a'; fx.fillRect(x, y0 + dy - 1, 3, 6); }
  }
});
XS_KIND.warnstripes = (s, c) => xsBake((bx, fx) => {
  const y = (s.y + 1) * TILE, x0 = s.x * TILE, x1 = x0 + (s.w || 4) * TILE;
  for (let x = x0; x < x1; x += 4) { fx.fillStyle = (x / 4) % 2 ? '#c8a020' : '#141424'; fx.fillRect(x, y, 4, 2); }
});
XS_KIND.railing = (s, c) => xsBake((bx, fx) => {
  const y = (s.y + 1) * TILE, x0 = s.x * TILE, x1 = x0 + (s.w || 4) * TILE;
  bx.fillStyle = '#34416a'; bx.fillRect(x0, y - 10, x1 - x0, 1); bx.fillStyle = '#222b4a'; bx.fillRect(x0, y - 5, x1 - x0, 1);
  for (let x = x0 + 2; x < x1; x += 8) { bx.fillStyle = '#2a3354'; bx.fillRect(x, y - 10, 1, 10); }
});
XS_KIND.hazardlamp = (s, c) => xsProp(s, c, { y: s.y * TILE + 2, update() { const a = time * 5 + this.seed; addLight(this.x + Math.cos(a) * 20, this.y + 12, 40, '255,170,40', 0.5 + 0.3 * Math.max(0, Math.cos(a))); }, draw() {
  xsR(this.x - 3, this.y - 2, 6, 5, '#26263e'); drawGlow(() => xsR(this.x - 2, this.y + 2, 4, 3, Math.cos(time * 5 + this.seed) > 0 ? '#ffb040' : '#a06010'));
} });
XS_KIND.alarmlamp = (s, c) => xsProp(s, c, { y: s.y * TILE + 2, update() {
  const on = typeof SYS !== 'undefined' && SYS.gaunt, a = time * (on ? 9 : 2) + this.seed;
  addLight(this.x + Math.cos(a) * 30, this.y + 20, on ? 70 : 30, on ? '255,40,60' : '255,120,60', on ? 0.9 * Math.max(0.2, Math.cos(a)) : 0.3);
}, draw() {
  const on = typeof SYS !== 'undefined' && SYS.gaunt;
  xsR(this.x - 4, this.y - 2, 8, 4, '#26263e'); drawGlow(() => xsR(this.x - 3, this.y + 2, 6, 3, on && Math.floor(time * 6) % 2 ? '#ff2a40' : '#6a1020'));
} });
SAFE_CHECKS.push((x, y) => !!room && XS.roomObj === room && XS.steams.some(v => Math.abs(x - v.x) < 20 && y <= v.y + 2 && y >= v.y - v.h));
// never keep a respawn point on a meteor stone or a maglev car (a kit slab under both feet, no tile): it is gone by the time you respawn
SAFE_CHECKS.push((x, y) => {
  if (!room || !room.def.x3 || !P || Math.abs(P.x - x) > 1 || Math.abs(P.y - y) > 1) return false;   // only the spot you stand on
  const ty = Math.floor((y + 1) / TILE), ok = t => t === T_PLAT || isSolidT(t);
  return !ok(tileAt(Math.floor((x - 4) / TILE), ty)) && !ok(tileAt(Math.floor((x + 4) / TILE), ty));
});
XS_KIND.steam = (s, c) => {   // a vent that blasts steam upward on a timer (hurts: hurtPlayer, so trials catch it)
  const v = { x: c.cx, y: c.fy, period: s.period || 3, phase: s.phase || 0, on: s.on || 1.0, warn: 0.6, h: (s.h || 3.5) * TILE, id: ++hazardId, prev: 'off' };
  xsEnsure(); XS.steams.push(v);
  xsProp(s, c, { vent: v, update() {
    const k = (((NHR.t || time) + v.phase) % v.period + v.period) % v.period, st = k < v.on ? 'on' : k > v.period - v.warn ? 'warn' : 'off', vis = xsVis(v.x, v.y, 30);
    if (st !== v.prev) { if (st === 'on' && vis) xsSfx.steam(0.8); if (st === 'warn' && vis) xsSfx.hiss(0.5); v.prev = st; }
    v.st = st;
    if (st === 'on') {
      for (let i = 0; i < 4; i++) particles.push({ x: v.x + rand(-5, 5), y: v.y - rand(0, 10), vx: rand(-15, 15), vy: -rand(120, 220), life: rand(0.3, 0.6), kind: 'dust' });
      if (overlap(rect(v.x - 7, v.y - v.h, v.x + 7, v.y), playerHurtbox())) hurtPlayer(26 * NGP.dmg, P.x < v.x ? -1 : 1, v.id * 1000 + Math.floor(((NHR.t || time) + v.phase) / v.period), {});
    } else if (st === 'warn' && Math.random() < 0.4) particles.push({ x: v.x + rand(-3, 3), y: v.y - 2, vx: rand(-10, 10), vy: -rand(10, 30), life: 0.4, kind: 'dust' });
  }, draw() {
    xsR(v.x - 7, v.y - 3, 14, 3, '#26263e'); xsR(v.x - 5, v.y - 3, 10, 1, v.st === 'warn' ? '#ffb040' : '#3c3c5c');
    if (v.st === 'on') { g.globalAlpha = 0.35; g.fillStyle = '#d8e2f0'; for (let i = 0; i < 6; i++) { const yy = v.y - ((time * 260 + i * 17) % v.h); g.fillRect(Math.round(v.x - 4 - (v.y - yy) / 14), Math.round(yy), 8 + (v.y - yy) / 7, 4); } g.globalAlpha = 1; }
  } });
};
XS_KIND.holo = (s, c) => xsProp(s, c, { glow: true, update() { addLight(this.x, this.y - (s.small ? 20 : 60), s.small ? 50 : 110, '80,210,255', 0.55 + 0.15 * Math.sin(time * 3)); }, draw() {
  const p = this, big = !s.small, H0 = big ? 120 : 40, W0 = big ? 70 : 40, fl = hash2(Math.floor(time * 9), p.seed) < 0.05 ? 0.3 : 1;
  if (!xsVis(p.x, p.y - H0 / 2, H0)) return;
  // a projected figure: the knight of the old Hallow, turning slowly (hard light, scanlines)
  const top = p.y - H0 - 6, t = time * 0.6 + p.seed;
  g.globalAlpha = 0.12 * fl; g.fillStyle = '#13a3c9'; g.beginPath(); g.moveTo(p.x - 4, p.y); g.lineTo(p.x - W0 / 2, top); g.lineTo(p.x + W0 / 2, top); g.lineTo(p.x + 4, p.y); g.fill();
  const sh = sheet('player');
  if (sh.ok && big) { g.globalAlpha = 0.6 * fl; drawSprite(sh, sh.first ? sh.first('idle') : 0, p.x, top + H0 * 0.9, Math.sin(t) > 0 ? 1 : -1, { flash: 1, flashColor: '#3fe0ff' }); }
  else { g.globalAlpha = 0.6 * fl; xsR(p.x - 8, top + 8, 16, 18, '#3fe0ff'); xsR(p.x - 5, top + 10, 10, 3, '#b8f6ff'); }
  g.globalAlpha = 0.3 * fl; for (let y = top; y < p.y; y += 3) xsR(p.x - W0 / 2, y + ((time * 20) % 3), W0, 1, '#b8f6ff');
  g.globalAlpha = 1;
  xsR(p.x - 6, p.y - 3, 12, 3, '#26263e'); xsR(p.x - 4, p.y - 3, 8, 1, '#3fe0ff');
} });
XS_KIND.datastream = (s, c) => xsProp(s, c, { glow: true, draw() {   // glyphs streaming along the abyss surface
  const x0 = s.x * TILE, x1 = x0 + (s.w || 10) * TILE, y = (s.y + 1) * TILE;
  for (let i = 0; i < 40; i++) {
    const x = x0 + (((hash2(i, 7) * (x1 - x0)) + time * (30 + hash2(i, 3) * 60)) % (x1 - x0)); if (x < cam.x || x > cam.x + W) continue;
    g.globalAlpha = 0.5; xsR(x, y + 3 + (hash2(i, 5) * 20 | 0), hash2(i, 9) < 0.5 ? 2 : 1, 1, hash2(i, 11) < 0.2 ? '#ff3fc0' : '#3fe0ff');
  }
  g.globalAlpha = 1;
} });
XS_KIND.watertower = (s, c) => xsProp(s, c, { draw() {
  const p = this; if (!xsVis(p.x, p.y, 60)) return;
  if (xsDraw('xsc_m', 'watertower', 0, p.x, p.y + 1, 1)) return;
  xsR(p.x - 14, p.y - 44, 28, 26, '#161c33'); xsR(p.x - 15, p.y - 46, 30, 3, '#222b4a'); for (const dx of [-12, 10]) xsR(p.x + dx, p.y - 18, 2, 18, '#0d1120');
} });
XS_KIND.skytraffic = (s, c) => xsProp(s, c, { cars: [], draw() {   // flying cars in lanes across the sky (vista)
  const p = this;
  if (Math.random() < 0.08) { const d = Math.random() < 0.5 ? 1 : -1, lane = irand(0, 3); p.cars.push({ x: d > 0 ? cam.x - 20 : cam.x + W + 20, y: cam.y + 18 + lane * 14 + rand(-2, 2), vx: d * rand(60, 130), c: Math.random() < 0.5 ? 0 : 1 }); }
  drawGlow(() => {
    for (const q of p.cars) {
      q.x += q.vx / 60; const d = Math.sign(q.vx);
      g.globalAlpha = 0.9; xsR(q.x, q.y, 3, 1, q.c ? '#ffe0a0' : '#ff3fc0'); g.globalAlpha = 0.35; xsR(q.x - d * 10, q.y, 10, 1, q.c ? '#ffb050' : '#c21d97');
    }
    g.globalAlpha = 1;
  });
  p.cars = p.cars.filter(q => q.x > cam.x - 60 && q.x < cam.x + W + 60);
} });
XS_KIND.gratehint = (s, c) => xsProp(s, c, { draw() {
  const p = this, near = Math.abs(P.x - p.x) < 28 && Math.abs(P.y - p.y) < (s.down ? 20 : 90);
  if (!near) return;
  drawGlow(() => {
    const a = 0.5 + 0.3 * Math.sin(time * 5), y = s.down ? p.y + 4 : p.y - 6;
    g.globalAlpha = a; for (let i = 0; i < 3; i++) xsR(p.x + 7 - i, s.down ? y + i : y - i, 2 * i + 1 + 0, 1, '#3fe0ff'); g.globalAlpha = 1;
  });
  if (s.down && P.ground && Math.abs(P.y - p.y) < 4) { XS.gratePrompt = time; }
} });
HOOKS.hud.push(() => {
  if (XS.gratePrompt && time - XS.gratePrompt < 0.1 && state === 'play') {
    const sx = P.x - cam.x, sy = P.y - cam.y - 40, label = '↓ + Jump: drop through', tw = textW(label, 6) + 10;
    box(sx - tw / 2, sy - 8, tw, 11, 0.7); text(label, sx, sy, 6, '#b8f6ff', 'center');
  }
});
// ---- the Firewall: coloured cables from each terminal to the barriers it throws (the clue), and a gentle hint
XS_KIND.wiring = (s, c) => xsProp(s, c, { glow: true, draw() {
  const L = s.links || {}, cols = ['#3fe0ff', '#ff3fc0', '#ffb050', '#5affd2'];
  Object.keys(L).forEach((id, k) => {
    const [lx, gates] = L[id], on = typeof KIT !== 'undefined' && KIT.byId[id] && KIT.byId[id].active;
    const y = 11 * TILE + 1 + k * 2, a = on ? 0.9 : 0.45;
    xsLineP(lx * TILE + 8, 10 * TILE, lx * TILE + 8, y, cols[k], a);
    for (const gx of gates) { xsLineP(lx * TILE + 8, y, gx * TILE + 8 + (k - 1.5), y, cols[k], a); xsLineP(gx * TILE + 8 + (k - 1.5), y, gx * TILE + 8 + (k - 1.5), y + 5, cols[k], a); }
    xsR(lx * TILE + 6, 10 * TILE - 3, 5, 2, cols[k]);   // the terminal's colour tag
  });
} });
XS_KIND.firehint = (s, c) => { xsEnsure(); XS.fireFlips = 0; XS.fireHint = 0; };
// ---- the Glitch Run's beat: a metronome at the top of the screen, ticks on each half-bar
XS_KIND.beat = (s, c) => { xsEnsure(); XS.beat = { period: s.period || 1.6, last: -1 }; };
HOOKS.update.push(() => {
  const B = XS.beat; if (!B || XS.roomObj !== room || typeof KIT === 'undefined') return;
  const h = Math.floor(KIT.t / (B.period / 2));
  if (h !== B.last) { B.last = h; xsSfx.tick(h % 2 === 0); }
});
HOOKS.renderTop.push(() => {
  const B = XS.beat; if (!B || XS.roomObj !== room || typeof KIT === 'undefined' || state !== 'play') return;
  const k = (KIT.t / B.period) % 1, x = W / 2, y = 14;
  for (let i = 0; i < 2; i++) {
    const on = (k < 0.5) === (i === 0), c = i === 0 ? '#3fe0ff' : '#ff3fc0';
    g.globalAlpha = on ? 0.95 : 0.25; xsR(x - 26 + i * 30, y, 22, 3, c);
    if (on) { const f = 1 - ((k % 0.5) / 0.5); g.globalAlpha = 0.5 * f; xsR(x - 26 + i * 30, y + 4, Math.round(22 * f), 1, c); }
  }
  g.globalAlpha = 1;
});
// ---- the Dev Room: a desk, a T-posing placeholder, missing textures, and the room tearing a little
XS_KIND.devdesk = (s, c) => xsProp(s, c, { update() { addLight(this.x + 4, this.y - 20, 40, '120,255,160', 0.7); }, draw() {
  const p = this;
  if (!xsDraw('xsc_m', 'devdesk', Math.floor(time * 3) % 2, p.x, p.y + 1, 1)) { xsR(p.x - 14, p.y - 12, 28, 3, '#3a3020'); xsR(p.x - 12, p.y - 9, 2, 9, '#2a2016'); xsR(p.x + 10, p.y - 9, 2, 9, '#2a2016'); xsR(p.x - 4, p.y - 24, 16, 12, '#1a1a1a'); }
  drawGlow(() => { for (let i = 0; i < 4; i++) { const w = 3 + (hash2(i, Math.floor(time * 2)) * 8 | 0); xsR(p.x - 2, p.y - 22 + i * 2, w, 1, '#5aff8a'); } });
} });
XS_KIND.tpose = (s, c) => xsProp(s, c, { draw() {
  const p = this, sh = sheet('hollow_soldier');
  if (sh.ok) drawSprite(sh, 0, p.x, p.y, -1, { bottom: true, flash: 0.6, flashColor: '#ff00ff' });
  else { xsR(p.x - 12, p.y - 22, 24, 3, '#c21d97'); xsR(p.x - 2, p.y - 28, 4, 28, '#c21d97'); }
  if (Math.abs(P.x - p.x) < 50) { g.globalAlpha = 0.8; text('npc_placeholder_03', p.x, p.y - 36, 5, '#ff9fe2', 'center'); g.globalAlpha = 1; }
} });
XS_KIND.missingtex = (s, c) => xsProp(s, c, { x: s.x * TILE, y: s.y * TILE, draw() {
  const p = this, w = (s.w || 1) * TILE, h = (s.h || 1) * TILE;
  for (let y = 0; y < h; y += 8) for (let x = 0; x < w; x += 8) xsR(p.x + x, p.y + y, 8, 8, ((x + y) / 8) % 2 ? '#000000' : (Math.floor(time * 2) % 5 ? '#ff00ff' : '#00ffff'));
} });
XS_KIND.glitchroom = (s, c) => xsProp(s, c, { draw() {
  if (Math.random() < 0.06) { const y = cam.y + rand(0, H), hh = irand(1, 4); g.globalAlpha = 0.35; xsR(cam.x, y, W, hh, Math.random() < 0.5 ? '#ff3fc0' : '#3fe0ff'); g.globalAlpha = 1; }
} });

// ================================================================== THE EMBER
XS_KIND.deadshrine = (s, c) => xsProp(s, c, { n: s.n || 0, update() {
  const p = this, heat = [0.9, 0.45, 0.2, 0][p.n] || 0;
  if (heat) addLight(p.x, p.y - 14, 26 + 20 * heat, '255,120,50', heat * (0.7 + 0.3 * Math.sin(time * 3 + p.seed)), LX_FLICKER);
  if (heat && Math.random() < 0.05 * heat) particles.push({ x: p.x + rand(-3, 3), y: p.y - 14, vx: rand(-3, 3), vy: -rand(10, 20), life: 1, kind: 'ember' });
}, draw() {
  const p = this; if (!xsVis(p.x, p.y)) return;
  if (xsDraw('xsc_m', 'deadshrine', p.n, p.x, p.y + 1, 1)) return;
  xsR(p.x - 8, p.y - 4, 16, 4, '#2a2220'); xsR(p.x - 5, p.y - 22, 10, 18, '#1c1614'); xsR(p.x - 7, p.y - 25, 14, 4, '#2e2622');
  xsR(p.x - 3, p.y - 14, 6, 5, '#0c0808'); if (p.n < 2) xsR(p.x - 1, p.y - 11, 2, 2, p.n ? '#8a3010' : '#ff7a2a');
} });
XS_KIND.ashpile = (s, c) => xsProp(s, c, { draw() {
  const p = this; if (!xsVis(p.x, p.y)) return;
  if (xsDraw('xsc_s', 'ashpile', Math.floor(p.seed) % 2, p.x, p.y + 1, p.face)) return;
  for (let i = 0; i < 6; i++) xsR(p.x - 10 + i * 2, p.y - Math.round(Math.sin((i + 0.5) / 6 * Math.PI) * 5), 20 - i * 4 > 2 ? 3 : 2, 6, i % 2 ? '#3a3230' : '#4a4038');
  if (Math.sin(time * 2 + p.seed) > 0.7) xsR(p.x - 2, p.y - 3, 1, 1, '#ff7a2a');
} });
XS_KIND.embercrack = (s, c) => xsProp(s, c, { update() { addLight(this.x, this.y - 2, 34, '255,110,40', 0.55 + 0.15 * Math.sin(time * 2 + this.seed)); if (Math.random() < 0.06) particles.push({ x: this.x + rand(-10, 10), y: this.y - 1, vx: 0, vy: -rand(10, 30), life: 1.2, kind: 'ember' }); }, draw() {
  const p = this; if (!xsVis(p.x, p.y)) return;
  drawGlow(() => { const a = 0.6 + 0.3 * Math.sin(time * 2 + p.seed); g.globalAlpha = a; for (let i = -12; i <= 12; i += 2) xsR(p.x + i, p.y - 1 - (Math.abs(i) % 4 === 0 ? 1 : 0), 2, 1, Math.abs(i) < 5 ? '#ffd080' : '#ff6a20'); g.globalAlpha = 1; });
} });
XS_KIND.deadtree = (s, c) => xsProp(s, c, { draw() {
  const p = this; if (!xsVis(p.x, p.y, 60)) return;
  if (xsDraw('xsc_m', 'deadtree', Math.floor(p.seed) % 2, p.x, p.y + 1, p.face)) return;
  xsR(p.x - 2, p.y - 40, 4, 40, '#140e0c'); xsLineP(p.x, p.y - 30, p.x - 14, p.y - 44, '#140e0c'); xsLineP(p.x, p.y - 24, p.x + 12, p.y - 38, '#140e0c'); xsLineP(p.x + 1, p.y - 36, p.x + 6, p.y - 50, '#140e0c');
} });
XS_KIND.fallenroad = (s, c) => xsProp(s, c, { draw() {
  const p = this; if (!xsVis(p.x, p.y)) return;
  for (let i = 0; i < 6; i++) xsR(p.x - 30 + i * 11 + (i > 2 ? 22 : 0), p.y - 2 - (i % 2), 5, 2, '#3a302a');
  g.globalAlpha = 0.5 + 0.2 * Math.sin(time * 1.5); drawGlow(() => xsR(p.x - 22, p.y + 30, 44, 2, '#ff6a20')); g.globalAlpha = 1;
} });
XS_KIND.embertree = (s, c) => xsProp(s, c, { update() {
  const p = this, pulse = 0.8 + 0.2 * Math.sin(time * 1.1);
  addLight(p.x, p.y - 70, 170 * pulse, '255,120,50', 1.0, { shadow: false }); addLight(p.x, p.y - 30, 60, '255,180,90', 0.8, LX_FLICKER);
  if (Math.random() < 0.7) particles.push({ x: p.x + rand(-50, 50), y: p.y - rand(20, 110), vx: rand(-8, 8), vy: -rand(15, 40), life: rand(1.5, 3), kind: Math.random() < 0.8 ? 'ember' : 'ash' });
}, draw() {
  const p = this; if (!xsVis(p.x, p.y, 220)) return;
  if (xsDraw('xsc_l', 'embertree', xsLoop('xsc_l', 'embertree', 4), p.x, p.y + 1, 1)) return;
  xsR(p.x - 8, p.y - 90, 16, 90, '#1a100c'); drawGlow(() => { for (let y = 10; y < 90; y += 7) xsR(p.x - 2 + Math.sin(y) * 3, p.y - y, 2, 5, '#ff7a2a'); });
} });
XS_KIND.hearthstone = (s, c) => xsProp(s, c, { update() { addLight(this.x, this.y + 4, 28, '255,110,40', 0.35 + 0.15 * Math.sin(time * 1.7)); }, draw() {
  const p = this; if (!xsVis(p.x, p.y)) return;
  drawGlow(() => { g.globalAlpha = 0.5 + 0.3 * Math.sin(time * 1.7); xsLineP(p.x - 18, p.y + 3, p.x - 4, p.y + 8, '#ff7a2a'); xsLineP(p.x - 4, p.y + 8, p.x + 6, p.y + 2, '#ff7a2a'); xsLineP(p.x + 6, p.y + 2, p.x + 18, p.y + 7, '#ffb040'); g.globalAlpha = 1; });
} });
XS_KIND.ruins = (s, c) => xsBake((bx) => {   // broken basalt colonnades in the dark behind the ash (baked into the back layer)
  const R = room, W0 = R.w, H0 = R.h, solid = (x, y) => x < 0 || y < 0 || x >= W0 || y >= H0 || isSolidT(R.grid[y * W0 + x]);
  for (let tx = 3 + (hash2(R.w, 7) * 5 | 0); tx < W0 - 2; tx += 7 + (hash2(tx, 3) * 6 | 0)) {
    let fy = -1; for (let y = H0 - 2; y > 1; y--) if (!solid(tx, y) && solid(tx, y + 1)) { fy = y; break; }
    if (fy < 0) continue;
    let top = fy; while (top > 0 && !solid(tx, top - 1) && fy - top < 14) top--;
    const h = Math.max(3, Math.floor((fy - top) * (0.45 + hash2(tx, 5) * 0.55))), x0 = tx * TILE + 3, yb = (fy + 1) * TILE, yt = yb - h * TILE;
    bx.globalAlpha = 0.75;
    bx.fillStyle = '#140d0a'; bx.fillRect(x0, yt, 10, yb - yt);
    bx.fillStyle = '#20150f'; bx.fillRect(x0, yt, 3, yb - yt);
    for (let y = yt + 6; y < yb; y += 11) { bx.fillStyle = '#0b0706'; bx.fillRect(x0, y, 10, 1); }
    bx.fillStyle = '#1c130e'; bx.fillRect(x0 - 3, yb - 4, 16, 4);                 // plinth
    if (hash2(tx, 9) < 0.5) { bx.fillStyle = '#1c130e'; bx.fillRect(x0 - 2, yt - 3, 14, 3); }   // capital
    else for (let i = 0; i < 4; i++) { bx.fillStyle = '#140d0a'; bx.fillRect(x0 + i * 3, yt - 2 - (hash2(tx, i) * 4 | 0), 3, 3); }   // broken top
    bx.fillStyle = 'rgba(255,110,40,0.35)'; bx.fillRect(x0 + 9, yt + 2, 1, yb - yt - 4);   // ember-lit edge
    bx.globalAlpha = 1;
  }
});
XS_KIND.ashfall = (s, c) => xsProp(s, c, { update() {   // ash sifting down out of cracks in the roof
  if (Math.random() < 0.5) particles.push({ x: cam.x + rand(0, W), y: cam.y - 4, vx: rand(-6, 6), vy: rand(8, 20), life: rand(4, 7), kind: Math.random() < 0.85 ? 'ash' : 'ember' });
} });
XS_KIND.hearth = (s, c) => xsProp(s, c, { update() {
  const p = this; addLight(p.x, p.y - 16, 150 + Math.sin(time * 7) * 8 + Math.sin(time * 19) * 4, '255,160,80', 1.15, LX_FLICKER);
  if (Math.random() < 0.5) particles.push({ x: p.x + rand(-6, 6), y: p.y - rand(10, 18), vx: rand(-6, 6), vy: -rand(20, 45), life: rand(0.5, 1.1), kind: 'fire' });
  if (Math.random() < 0.08) particles.push({ x: p.x + rand(-4, 4), y: p.y - 30, vx: rand(-4, 4), vy: -rand(8, 16), life: 2.5, kind: 'ember' });
}, draw() {
  const p = this;
  if (xsDraw('xsc_m', 'hearth', xsLoop('xsc_m', 'hearth', 10), p.x, p.y + 1, 1)) return;
  xsR(p.x - 20, p.y - 34, 40, 34, '#3a2e28'); xsR(p.x - 13, p.y - 22, 26, 22, '#140c0a');
  drawGlow(() => { for (let i = 0; i < 5; i++) { const h = 8 + Math.sin(time * 9 + i * 2) * 4; xsR(p.x - 9 + i * 4, p.y - 4 - h, 3, h, i % 2 ? '#ff7a2a' : '#ffd080'); } });
} });
for (const k of ['rug', 'embershelf', 'hangingpots', 'firewood', 'shelves', 'jars', 'stonelantern', 'pine', 'herbs']) {
  XS_KIND[k] = (s, c) => xsProp(s, c, { y: k === 'hangingpots' ? s.y * TILE : c.fy, update() {
    if (k === 'stonelantern') addLight(this.x, this.y - 12, 44, '255,200,130', 0.8, LX_FLICKER);
  }, draw() {
    const p = this; if (!xsVis(p.x, p.y, 60)) return;
    const big = { shelves: 1, stonelantern: 0, pine: 1, herbs: 0 }[k];
    if (xsDraw(big ? 'xsc_m' : 'xsc_s', k, 0, p.x, p.y + (k === 'hangingpots' ? 30 : 1), p.face)) return;
    if (k === 'rug') { xsR(p.x - 16, p.y - 1, 32, 1, '#6e2a24'); xsR(p.x - 14, p.y - 1, 28, 1, '#8a3a2c'); }
    else if (k === 'herbs') for (let i = 0; i < (s.w || 3) * 4; i++) xsR(p.x - 8 + i * 4 % ((s.w || 3) * 16), p.y - 4 - (i % 3), 2, 4 + (i % 3), i % 2 ? '#4a6a3a' : '#6e8a4a');
    else if (k === 'pine') { for (let i = 0; i < 5; i++) xsR(p.x - (5 - i) * 2, p.y - 8 - i * 6, (5 - i) * 4, 5, '#1c2a20'); xsR(p.x - 1, p.y - 8, 2, 8, '#2a1c14'); }
    else if (k === 'stonelantern') { xsR(p.x - 4, p.y - 6, 8, 6, '#4a4640'); xsR(p.x - 5, p.y - 16, 10, 10, '#5a5650'); xsR(p.x - 3, p.y - 13, 6, 4, '#ffcc80'); xsR(p.x - 7, p.y - 19, 14, 3, '#3a3630'); }
    else { xsR(p.x - 8, p.y - 12, 16, 12, '#3a2618'); xsR(p.x - 7, p.y - 11, 14, 1, '#5e4028'); }
  } });
}

// ================================================================== THE HERMIT'S HOLLOW
XS_KIND.fog = (s, c) => xsProp(s, c, { draw() {   // banks of fog drifting through the cleft
  const x0 = s.x * TILE, w = (s.w || 10) * TILE, y = c.fy, thin = s.thin;
  for (let i = 0; i < (thin ? 6 : 12); i++) {
    const k = hash2(i, s.x), xx = x0 + ((k * w + time * (6 + k * 8)) % w), yy = y - (thin ? 4 : 10) - hash2(i, 3) * (thin ? 8 : 26);
    if (xx < cam.x - 60 || xx > cam.x + W + 60) continue;
    g.globalAlpha = (thin ? 0.08 : 0.14) + 0.05 * Math.sin(time * 0.5 + i);
    g.fillStyle = '#c8c0b8'; g.beginPath(); g.ellipse(Math.round(xx), Math.round(yy), 26 + k * 20, 5 + k * 4, 0, 0, 6.29); g.fill();
  }
  g.globalAlpha = 1;
} });
XS_KIND.lantern = (s, c) => xsProp(s, c, { update() { addLight(this.x, this.y - 10, 46, '255,190,120', 0.8, LX_FLICKER); }, draw() {
  const p = this; if (!xsVis(p.x, p.y)) return;
  if (xsDraw('xsc_s', 'lantern', 0, p.x, p.y + 1, 1)) return;
  xsR(p.x, p.y - 14, 1, 14, '#2a1c14'); xsR(p.x - 3, p.y - 12, 6, 7, '#e8c890'); xsR(p.x - 2, p.y - 11, 4, 5, '#ffe0a0');
} });
XS_KIND.hut = (s, c) => xsProp(s, c, { update() { addLight(this.x + 2, this.y - 22, 40, '255,190,120', 0.7, LX_FLICKER); if (Math.random() < 0.05) particles.push({ x: this.x + 18, y: this.y - 64, vx: rand(2, 6), vy: -rand(8, 14), life: 3, kind: 'ash' }); }, draw() {
  const p = this; if (!xsVis(p.x, p.y, 100)) return;
  if (xsDraw('xsc_l', 'hut', 0, p.x, p.y + 1, 1)) return;
  xsR(p.x - 30, p.y - 36, 60, 36, '#3a2618'); g.fillStyle = '#2a1c14'; g.beginPath(); g.moveTo(p.x - 38, p.y - 34); g.lineTo(p.x, p.y - 60); g.lineTo(p.x + 38, p.y - 34); g.fill();
  xsR(p.x - 8, p.y - 24, 16, 24, '#140c08'); xsR(p.x + 14, p.y - 26, 8, 8, '#ffcc80');
} });
XS_KIND.chimes = (s, c) => xsProp(s, c, { y: s.y * TILE, last: 0, update() {
  const p = this, wind = Math.sin(time * 0.7 + p.seed) * 0.6 + Math.sin(time * 1.9) * 0.4;
  if (wind > 0.75 && time - p.last > 2.5 && xsVis(p.x, p.y, 20)) { p.last = time; const f = [1, 1.125, 1.25, 1.5][irand(0, 3)]; xsSfx.chime(f * 0.75); }
  addLight(p.x, p.y + 20, 18, '255,220,170', 0.25);
}, draw() {
  const p = this, sway = Math.sin(time * 0.7 + p.seed) * 3;
  if (xsDraw('xsc_m', 'chimes', xsLoop('xsc_m', 'chimes', 4, p.seed), p.x, p.y + 40, 1)) return;
  xsR(p.x - 8, p.y, 16, 1, '#5e4028');
  for (let i = 0; i < 5; i++) { const x = p.x - 7 + i * 3.5, l = 10 + (i % 3) * 5, o = sway * (0.6 + i * 0.12); xsLineP(x, p.y + 1, x + o, p.y + l, '#6a6258'); xsR(x + o - 1, p.y + l, 2, 5, '#b8b0a0'); }
} });

// ================================================================== kit looks (drawn over KM's objects by `look`)
HOOKS.enter.push(def => {
  xsEnsure();
  if (typeof KIT === 'undefined') return;
  for (const o of KIT.objs) {
    const look = o.spec && o.spec.look; if (!look) continue;
    if (look === 'meteor' && o.kind === 'phase') o.draw = () => xsMeteorDraw(o);
    else if (look === 'maglev' && o.kind === 'mover') o.draw = () => xsMaglevDraw(o);
    else if (look === 'billboard' && o.kind === 'phase') o.draw = () => xsBillboardDraw(o);
    else if (look === 'glitch' && o.kind === 'phase') o.draw = () => xsGlitchDraw(o);
    else if (look === 'ghost') { o.draw = () => {}; o.tick = () => { o.solidNow = false; }; }
  }
});
function xsMaglevDraw(o) {
  const X = Math.round(o.d.x0), Y = Math.round(o.d.y0), w = o.w, lane = (o.spec.path && o.spec.path[0][1]) * TILE;
  if (X + w < cam.x - 10 || X > cam.x + W + 10) return;
  const surf = isSolidT(tileAt(Math.floor((X + w / 2) / TILE), 13)) ? 13 * TILE : 15 * TILE;   // the stream's surface, or a portal's top: the car hides below it
  if (Y >= surf) return;
  g.save(); g.beginPath(); g.rect(X - 4, Y - 20, w + 8, surf - (Y - 20)); g.clip();
  const vx = o.v || 0, dir = (o.spec.path[1][0] - o.spec.path[0][0]) > 0 ? 1 : -1;
  if (!xsDraw('xsc_m', 'maglev', 0, X + w / 2, Y + 18, dir)) {
    xsR(X, Y - 10, w, 10, '#222b4a'); xsR(X + 2, Y - 12, w - 4, 2, '#34416a'); xsR(X + 4, Y - 8, w - 8, 3, '#0b4d66'); xsR(X, Y, w, 3, '#161c33');
  }
  drawGlow(() => {
    for (let i = 6; i < w - 6; i += 8) xsR(X + i, Y - 7, 4, 1, '#b8f6ff');
    xsR(X + 2, Y + 3, w - 4, 1, Y < lane + 2 ? '#3fe0ff' : '#ff3fc0');
    xsR(dir > 0 ? X + w - 2 : X, Y - 5, 2, 2, '#ffe0a0');
  });
  g.restore();
  if (Y < surf) { addLight(X + w / 2, Y + 4, 50, '80,210,255', 0.5); if (Math.random() < 0.3) particles.push({ x: dir > 0 ? X : X + w, y: Y - 4, vx: -dir * rand(20, 50), vy: 0, life: 0.3, kind: 'nh_mote' }); }
}
function xsBillboardDraw(o) {
  const X = Math.round(o.d.x0), Y = Math.round(o.d.y0), w = o.w, on = o.solidNow, warn = o.warnK || 0;
  if (!xsVis(X + w / 2, Y, 60)) return;
  const v = (o.spec.id || '').length + (X >> 4), fl = warn > 0 && Math.floor(KIT.t * (10 + 14 * warn)) % 2;
  // the frame and its bracket are always there; the lit face is the floor
  xsR(X, Y, w, 3, '#222b4a'); xsR(X + 3, Y + 3, 2, 8, '#161c33'); xsR(X + w - 5, Y + 3, 2, 8, '#161c33');
  const face = () => {
    const C = [NH_MG, NH_CY, ['#3a1e06', '#7a4410', '#c87a20', '#ffb050', '#ffe0a0', '#fff']][v % 3];
    xsR(X + 1, Y - 18, w - 2, 18, C[1]); xsR(X + 2, Y - 17, w - 4, 16, C[2]);
    for (let i = 0; i < 3; i++) xsR(X + 4, Y - 14 + i * 4, (w - 8) * (0.4 + hash2(v, i) * 0.6), 2, C[4]);
    xsR(X + 1, Y - 18, w - 2, 1, C[5]);
  };
  if (on && !fl) { drawGlow(face); addLight(X + w / 2, Y - 8, 50, XS_NEON[v % 3], 0.65); }
  else { xsR(X + 1, Y - 18, w - 2, 18, '#0d1120'); xsR(X + 2, Y - 17, w - 4, 16, '#070913'); if (on) { g.globalAlpha = 0.5; drawGlow(face); g.globalAlpha = 1; } }
}
function xsGlitchDraw(o) {
  const X = Math.round(o.d.x0), Y = Math.round(o.d.y0), w = o.w, on = o.solidNow, warn = o.warnK || 0, gA = o.spec.group === 'gA';
  if (!xsVis(X + w / 2, Y, 40)) return;
  const C = gA ? NH_CY : NH_MG;
  if (on) {
    const j = warn > 0.3 ? Math.round(rand(-2, 2) * warn) : 0;
    drawGlow(() => {
      g.globalAlpha = 0.5; xsR(X + j - 1, Y, w, 7, C[2]); g.globalAlpha = 1;
      xsR(X + j, Y, w, 1, C[5]); xsR(X + j, Y + 1, w, 5, C[3]); xsR(X + j, Y + 6, w, 1, C[4]);
      if (warn > 0) { g.globalAlpha = warn; xsR(X - j + 2, Y + 2, w, 2, gA ? NH_MG[3] : NH_CY[3]); g.globalAlpha = 1; }
      for (let i = 2; i < w - 2; i += 4) if (hash2(i, Math.floor(time * 8)) < 0.5) xsR(X + i + j, Y + 3, 2, 1, C[5]);
    });
    addLight(X + w / 2, Y + 3, 28, gA ? '80,210,255' : '255,60,190', 0.5);
  } else { g.globalAlpha = 0.3; for (let x = X; x < X + w; x += 2) xsR(x, Y + (x % 4 ? 0 : 6), 1, 1, C[3]); g.globalAlpha = 1; }
}
// the glitch veils: in NEO-HALLOW an ash veil is a wall of corrupted data (same rules: burn through with the Ember Dash)
HOOKS.enter.push(def => {
  if (!def.biome.startsWith('neohallow')) return;
  for (const p of props) if (p.type === 'veil') p.draw = () => {
    const x = Math.round(p.x) - 8, top = p.y - p.h;
    if (!xsVis(p.x, p.y - p.h / 2, p.h)) return;
    drawGlow(() => {
      for (let y = top; y < p.y; y += 2) {
        const r = hash2(Math.floor(y / 2), Math.floor(time * 12 + p.x)), off = Math.floor(r * 6) - 3;
        g.globalAlpha = 0.45 + 0.3 * r; xsR(x + 4 + off, y, 8, 2, r < 0.3 ? '#ff3fc0' : r < 0.6 ? '#3fe0ff' : '#b8f6ff');
      }
      g.globalAlpha = 1;
    });
    addLight(p.x, p.y - p.h / 2, 50, '255,60,190', 0.45);
  };
});

// ================================================================== puzzle hints (after three fruitless attempts)
if (typeof KIT !== 'undefined') KIT.onChange.push((id, value, obj) => {
  if (!room) return;
  if (room.id === 'SF15' && obj) {
    if (obj.kind === 'socket' && value) { XS.lensTurns = 0; return; }
    if (obj.kind === 'mirror') {
      XS.lensTurns++;
      if (XS.lensTurns >= 18 && !XS.lensHint) { XS.lensHint = 1; toast('Where the light has run a thousand times, the wall remembers. Follow the faint veins.', 5); }
    }
  }
  if (room.id === 'NH13' && obj && obj.kind === 'lever') {
    const all = ['G1', 'G2', 'G3', 'G4'].every(k => kitOn(k));
    if (!all && ++XS.fireFlips >= 6 && !XS.fireHint) { XS.fireHint = 1; toast('Follow the cables: each terminal throws the two barriers its colour runs to.', 5); }
  }
});

// ================================================================== vista backdrops (painted skies behind the benches)
const XS_BG = { W6: 'xsc_bg_meteor', SF16: 'xsc_bg_meteor', SF17: 'xsc_bg_crater', NH15: 'xsc_bg_skyline', H3: 'xsc_bg_garden', H2: 'xsc_bg_garden', E6: 'xsc_bg_hearth' };
const XS_CELLAR = { c: null };
function xsCellar() {   // Oswin's stash is under the floorboards: packed earth and roots behind it, not sky
  if (XS_CELLAR.c) return XS_CELLAR.c;
  const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d');
  x.fillStyle = '#120d0a'; x.fillRect(0, 0, W, H);
  for (let i = 0; i < 900; i++) { const px = hash2(i, 1) * W | 0, py = hash2(i, 2) * H | 0; x.fillStyle = hash2(i, 3) < 0.5 ? '#1a130e' : '#0c0806'; x.fillRect(px, py, 2 + (hash2(i, 4) * 4 | 0), 1 + (hash2(i, 5) * 2 | 0)); }
  for (let k = 0; k < 14; k++) { let px = hash2(k, 7) * W, py = 0; x.fillStyle = '#2a1c12'; for (let j = 0; j < 90; j++) { px += Math.sin(j * 0.2 + k) * 1.2; py += 1.4; x.fillRect(px | 0, py | 0, 1, 2); } }
  for (let y = 18; y < H; y += 26) { x.fillStyle = '#20160e'; x.fillRect(0, y, W, 3); x.fillStyle = '#2e2014'; x.fillRect(0, y, W, 1); }   // old boards
  return (XS_CELLAR.c = c);
}
const xsParallaxBase = drawParallax;
drawParallax = function () {
  if (room && room.id === 'H4') { g.drawImage(xsCellar(), 0, 0); return; }
  xsParallaxBase();
  const n = room && XS_BG[room.id]; if (!n) return;
  const sh = sheet(n); if (!sh.ok) return;
  for (const [tag, fac, vfac] of [['far', 0.05, 0.02], ['mid', 0.14, 0.05]]) {
    if (!sh.has(tag)) continue;
    const t = sh.tag(tag), f = sh.frames[t.from + Math.floor(time * 4) % (t.to - t.from + 1)];
    const ox = -((cam.x * fac) % f.w + f.w) % f.w, oy = Math.round(clamp(-cam.y * vfac, -(f.h - H) - 10, 10));
    for (let x = Math.round(ox); x < W; x += f.w) g.drawImage(sh.img, f.x, f.y, f.w, f.h, x, oy + (H - f.h), f.w, f.h);
  }
};

// ================================================================== housekeeping
HOOKS.enter.push(def => { xsEnsure(); XS.bakeT = 0; });
HOOKS.update.push(dt => { if (room && XS.roomObj === room && !XS.baked && XS.bakes.length) xsRunBakes(); });
// the First Flame's hearthstone must be slammed through on every attempt: cracked floors in trial rooms come back
function xsRestoreCracks() {
  if (!room || !room.def.trial) return;
  const def = room.def; let n = 0;
  for (let y = 0; y < def.h; y++) for (let x = 0; x < def.w; x++) if (def.map[y][x] === 'Y') {
    const k = brokenKey(def, x, y); if (SAVE.flags[k] || room.grid[y * def.w + x] !== T_CRACK) { delete SAVE.flags[k]; room.grid[y * def.w + x] = T_CRACK; n++; }
  }
  if (n) { renderRoomLayers(room); XS.baked = false; }
}
HOOKS.enter.push(def => { if (def.trial) xsRestoreCracks(); });
HOOKS.update.push(dt => {   // trials reset: region props with state follow the kit reset
  const T = typeof SYS !== 'undefined' && SYS.trial;
  if (T && T.attempts !== XS.trialAttempts) { XS.trialAttempts = T.attempts; xsRestoreCracks(); for (const o of (typeof KIT !== 'undefined' ? KIT.objs : [])) { o.xsWas = undefined; o.xsHit = 0; } }
  if (!T) XS.trialAttempts = -1;
});
if (typeof window !== 'undefined' && window.__game) window.__game.xs = {
  XS, get KIT() { return typeof KIT !== 'undefined' ? KIT : null }, get SYS() { return typeof SYS !== 'undefined' ? SYS : null },
  clean() { toasts.length = 0; areaCard = null; bannerMsg = null; if (window.__ui) window.__ui.regionCard = null; },
  get lights() { return lights.length; },
  hazardAt(tx, ty) { const t = tileAt(tx, ty); return t === T_SPIKE || (typeof NH_T_VOID !== 'undefined' && t === NH_T_VOID) || unsafeAt(tx * TILE + 8, (ty + 1) * TILE); },
  travel() { menu = travelOpen(null); state = 'menu'; },
  sheet(maxW = 2048) {   // whole-room render for contact sheets: the camera pans tile by tile, the pieces are stitched (then scaled to maxW)
    const c = document.createElement('canvas'); c.width = room.pw; c.height = room.ph; const X = c.getContext('2d'); shake = 0;
    const span = (full, v, m) => { if (full <= v) return [[(full - v) / 2, 0, full]]; const out = []; for (let a = 0; ; a += v - 2 * m) { const cp = Math.min(a, full - v); out.push([cp, cp === 0 ? 0 : cp + m, cp + v >= full ? full : cp + v - m]); if (cp >= full - v) break; } return out; };
    for (const [cy, y0, y1] of span(room.ph, H, 40)) for (const [cx, x0, x1] of span(room.pw, W, 60)) {
      cam.x = cx; cam.y = cy; renderWorld(); presentWorld();
      const a = Math.max(x0, 0), b = Math.max(y0, 0);
      X.drawImage(view, ox + (a - cx) * scale, oy + (b - cy) * scale, (x1 - a) * scale, (y1 - b) * scale, a, b, x1 - a, y1 - b);
    }
    if (c.width <= maxW) return c.toDataURL('image/png');
    const k = maxW / c.width, d = document.createElement('canvas'); d.width = maxW; d.height = Math.round(c.height * k);
    d.getContext('2d').drawImage(c, 0, 0, d.width, d.height); return d.toDataURL('image/png');
  },
};
