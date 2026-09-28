// ------------------------------------------------------------------ EXPANSION 3 — agent SA: Thornveil Wood, Drowned Barrows, Crimson Manor
// New rooms (tools/regions/83_sa.py): TV9–TV16, DB10–DB17, CM9–CM17. Art: art/gen_xsa*.py -> assets/xsa_*.
// One spawn kind `xsa` (kind = prop | skins | flies | motes | shaft | sign | rite | …) dresses and wires them.
// Trial charms: c_x3_thorn (Thornstep Ring: three airborne attacks per jump), c_x3_lung (Drowned Lung: double breath,
// swim 25% faster). Every top-level name is prefixed sa/SA (all region files share one scope).
const SA = { roomObj: null };
function saReset() {
  Object.assign(SA, { roomObj: room, back: [], skins: [], flies: [], motes: [], shafts: [], signs: [], rites: [], fronts: [],
    snares: [], tides: [], pearls: [], leaks: [], wheels: [], gazes: [], books: [], keygates: [], pianos: [], bubbles: [], hint: {},
    flood: null, tgates: [], fpaint: [], glass: false });
}
function saEnsure() { if (SA.roomObj !== room) saReset(); }
const saIn = () => !!(room && room.def.x3 && /^(TV|DB|CM)\d/.test(room.def.id));
const saSfx = {
  snap: () => { noise(0.25, 1800, 1.2, 0.35, 'highpass', 0.4); tone(160, 0.2, 0.12, 'square', 0.5); },
  unseal: () => { noise(1.1, 300, 0.7, 0.35, 'lowpass', 0.6); [262, 330, 392].forEach((f, i) => tone(f, 1.6, 0.05, 'sine', 1, 0.3 + i * 0.12)); },
  creak: () => { tone(80, 0.8, 0.1, 'sawtooth', 1.3); noise(0.6, 400, 0.7, 0.18, 'bandpass', 0.6); },
  drip: () => tone(rand(900, 1400), 0.06, 0.02, 'sine', 1.8),
  key: () => { [880, 1175, 1568].forEach((f, i) => tone(f, 0.5, 0.05, 'triangle', 1, i * 0.07)); },
  jam: () => { noise(0.3, 500, 0.8, 0.2, 'lowpass', 0.5); tone(90, 0.25, 0.08, 'square', 0.7); },
};

// ================================================================== lore (the Hallow Chronicle)
Object.assign(LORE_PAGES, {
  sa_1: { region: 'thornveil', title: 'The Mother Oak', text: 'Before the Root was a root, it was a seed, and the seed fell here.\nThe first wardens slept under this oak and woke with moss in their hair. They were told nothing, and they understood. A tree that old does not speak. It only waits for you to stop speaking.' },
  sa_2: { region: 'thornveil', title: 'The Elder’s Heart', text: 'A hollow in the roots of the Elder, lined with old ribbons gone grey.\nHunters left a ribbon here for every deer they did not kill. The oldest ones are knotted around the bones of hunters.' },
  sa_3: { region: 'thornveil', title: 'A Trapper’s Tally', text: 'Notches cut into a strip of bark, a dozen to a row, and at the end a single line:\n“The snares are empty again. Something walks the trail at night and opens them. It leaves the bait.”' },
  sa_4: { region: 'thornveil', title: 'The Witches’ Receipt', text: 'A recipe in three hands.\n“Moss from a grave. Sap from the Elder, taken on a night without wind. One thorn from the Warden’s crown.”\nThe last ingredient has been underlined until the page tore: “Do not ask him for it.”' },
  sa_5: { region: 'barrows', title: 'The Pearl Lagoon', text: 'Light comes down here from somewhere no one has found.\nThe tide-keepers said the pearls are breaths the drowned did not need, and that each one holds a word. They listened for a hundred years. They heard only the sea.' },
  sa_6: { region: 'barrows', title: 'The Sluice-Keeper’s Plaque', text: 'Cast in bronze, green with salt. Three basins, three wheels, and a warning:\n“A wheel will not turn against the water standing over it. Open each gate from dry ground, and let the flood run on ahead of you.”' },
  sa_7: { region: 'barrows', title: 'The Drowned Bell', text: 'No one opened this well. It was sealed from the inside.\nThe bell at the bottom has no tongue. Something rings it anyway, once a year, on the night the tide comes highest. The tide-keepers wrote down the day. Then they stopped writing.' },
  sa_8: { region: 'barrows', title: 'The Sunken Nave', text: 'The Cathedral’s first nave, before it was built again higher up.\nWhen the black water came, the congregation did not leave. They sang until the water was over their heads, and then they went on singing.' },
  sa_9: { region: 'crimson', title: 'The Moonlit Conservatory', text: 'The Countess kept roses under glass so they would never feel the rain.\nThey died anyway, all on the same night. The piano has played for them ever since, the same waltz, a little slower every year.' },
  sa_10: { region: 'crimson', title: 'The Count’s Study', text: 'The Count’s last letter, never sent:\n“The Root has stopped answering the tithe, so I have stopped paying it. My lady says grace can be drawn from other vessels. I have locked the study. Let her find the keys if she wants my name on it.”' },
  sa_11: { region: 'crimson', title: 'Behind the Bookcase', text: 'A servants’ passage no servant was meant to know about.\nOn the wall, in chalk, the same five words in a dozen hands: “She hears you in here.”' },
  sa_12: { region: 'crimson', title: 'The Portrait Riddle', text: 'A brass plate under the family portrait:\n“We are painted in the order we were taken. Look where my eyes look, and call us down.”' },
});

// ================================================================== gear: the trial charms and the study keys
registerGear({
  charms: {
    c_x3_thorn: { name: 'Thornstep Ring', desc: 'A ring of braided bramble from the end of the Bramble Sprint. You can make three strikes in the air before you touch ground, instead of two.' },
    c_x3_lung: { name: 'Drowned Lung', desc: 'Something the Breathless Dive gave back. You hold your breath twice as long underwater and swim a quarter faster.' },
  },
  items: {
    xsa_key1: { name: 'Silver Study Key', icon: 'xsa_key1', sheet: 'xsa_icons', desc: 'A small silver key with a V worked into the bow. One of three to the Count’s study.' },
    xsa_key2: { name: 'Portrait Key', icon: 'xsa_key2', sheet: 'xsa_icons', desc: 'A key that was hidden in the frame of a portrait. One of three to the Count’s study.' },
    xsa_key3: { name: 'Rook’s Key', icon: 'xsa_key3', sheet: 'xsa_icons', desc: 'A black iron key from a rooftop nest. One of three to the Count’s study.' },
  },
}, 'xsa_icons');
// Thornstep Ring: the airborne-attack chain allows three. airAtkStart/airRefund are plain functions in 04_player.js, wrapped here.
{
  const aStart = airAtkStart, aRefund = airRefund;
  const chain = () => charmOn('c_x3_thorn') ? 3 : AIR_CHAIN;
  airAtkStart = function () { if (chain() === AIR_CHAIN) return aStart(); P.airN = (P.airN || 0) + 1; if (P.airN >= chain()) { P.airLock = true; P.airCd = AIR_CD; P.airDenied = false; } };
  airRefund = function () { if (chain() === AIR_CHAIN) return aRefund(); if (P.airN > 0) P.airN--; if (P.airN < chain()) P.airLock = false; };
}
// Drowned Lung: breath x2 (stacks with the Drowned Gill), and a quarter more swim speed through the swim targets' pull
if (typeof dbBreathMax === 'function') {
  const bm = dbBreathMax;
  dbBreathMax = function () { return bm() * (charmOn('c_x3_lung') ? 2 : 1); };
}
HOOKS.update.push(() => {
  if (typeof DBS === 'undefined' || !DBS.inWater || !P || P.state !== 'swim' || !charmOn('c_x3_lung') || !SAVE.items.tidebreath) return;
  const ax = inputX(), ay = (held.has('down') ? 1 : 0) - (held.has('up') ? 1 : 0) || (held.has('jump') ? -1 : 0);
  DBS.pullX += ax * DB_SWIM_V * 0.25; DBS.pullY += ay * DB_SWIM_V * 0.9 * 0.25;
});

// ================================================================== elite foes for the gauntlets (a named, heavier kin of a region foe)
function saElite(type, base, cfg) {
  Object.assign(ENEMY, { [type]: { ...ENEMY[base], ...cfg, elite: true } });
  if (ATTACK_TAGS[base]) ATTACK_TAGS[type] = ATTACK_TAGS[base];
  const Base = ENEMY_CLASSES[base] || Enemy;
  ENEMY_CLASSES[type] = class extends Base {
    constructor(t, x, y, key) {
      super(base, x, y, key);
      this.type = type; this.cfg = tierCfg(ENEMY[type]); this.hp = this.maxHp = Math.round(this.cfg.hp * NGP.hp); this.eliteName = cfg.name;
    }
    draw() {
      super.draw();
      if (this.alive) { addLight(this.x, this.y - this.h * 0.7, 30, cfg.glow || '255,90,70', 0.5); if (Math.random() < 0.15) particles.push({ x: this.x + rand(-8, 8), y: this.y - rand(4, this.h), vx: 0, vy: -rand(8, 20), life: 0.6, kind: cfg.pk || 'ember' }); }
    }
  };
}
if (ENEMY.tv_husk) saElite('xsa_elder_husk', 'tv_husk', { name: 'Elder Husk', hp: 620, cinders: 900, poise: 60, stance: 220, speed: 36, glow: '140,255,160', pk: 'tv_mote' });
if (ENEMY.cm_servant) saElite('xsa_head_butler', 'cm_servant', { name: 'The Steward', hp: 700, cinders: 1100, poise: 55, stance: 230, speed: 44, glow: '255,70,80', pk: 'blood' });

// ================================================================== spawn dispatcher
const SA_KIND = {};
SPAWNS.xsa = (s, c) => { saEnsure(); const f = SA_KIND[s.kind]; if (f) { try { f(s, c); } catch (e) { console.warn('xsa', s.kind, e); } } };
// props hung from the top of their cell (the rest stand on the floor of theirs)
const SA_HANG = new Set(['rootcurtain', 'herbs', 'chainlamp', 'laundry', 'bigbell']);
// lights per prop tag: [dx, dy, r, rgb, k, flicker]
const SA_LIGHT = {
  fungus: [0, -12, 46, '120,255,190', 0.75], cauldron: [0, -18, 50, '140,255,120', 0.8, 1], skullpost: [0, -30, 18, '150,255,190', 0.3],
  lamp_db: [0, -30, 60, '110,230,210', 0.85, 1], pearlclam: [0, -8, 30, '200,240,255', 0.6], candles_db: [0, -10, 40, '130,240,220', 0.7, 1],
  saint: [0, -150, 70, '140,220,230', 0.5], candelabra2: [0, -40, 60, '255,170,100', 0.9, 1], piano: [0, -30, 40, '255,200,150', 0.35],
  lamp_cm: [0, -28, 54, '255,160,110', 0.85, 1], hearth: [0, -16, 70, '255,130,70', 0.9, 1], desk: [8, -30, 36, '255,190,120', 0.7, 1],
};
SA_KIND.prop = (s, c) => {
  const shName = s.sheet || 'xsa_tv', x = c.cx + (s.dx || 0) - (s.half ? 8 : 0), y = c.fy + (s.dy || 0);
  if (s.back) { SA.back.push({ sh: shName, tag: s.tag, x, y, flip: s.flip, alpha: s.alpha }); return; }
  const sh = sheet(shName), hang = SA_HANG.has(s.tag);
  const p = { type: 'xsa_' + s.tag, x, y: hang ? s.y * TILE + (s.dy || 0) : y, face: s.flip ? -1 : 1, sh, anim: new Anim(sh, s.tag, true), s };
  p.anim.t = rand(0, 900);
  p.draw = () => {
    if (!sh.ok || !sh.has(s.tag)) { g.fillStyle = '#2a2a24'; g.fillRect(Math.round(p.x) - 5, Math.round(p.y) - (hang ? 0 : 12), 10, 12); return; }
    drawSprite(sh, p.anim.frame, p.x, p.y, p.face, hang ? { pivot: [Math.floor(sh.fw / 2), 0] } : { bottom: true, alpha: s.alpha });
  };
  const L = SA_LIGHT[s.tag];
  if (L) { p.update = () => addLight(p.x + L[0] * p.face, p.y + L[1], L[2], L[3], L[4], L[5] ? LX_FLICKER : undefined); p.glow = !!s.glow; }
  if (s.tag === 'snare') saSnare(p, s);
  if (s.tag === 'bigbell') saBigBell(p);
  props.push(p);
  if (s.front) { props.splice(props.indexOf(p), 1); SA.fronts.push(p); }
};
// back-layer painting (giant trees, root arches, the Elder, the Mother Oak, windows): once per build, repainted after re-renders
function saPaintBack() {
  if (!room || !room.back || !SA.back.length) return;
  const bx = room.back.getContext('2d');
  for (const t of SA.back) {
    const sh = sheet(t.sh); if (!sh.ok || !sh.has(t.tag) || !sh.img.complete) continue;
    const f = sh.frames[sh.first(t.tag)];
    bx.save(); bx.globalAlpha = t.alpha ?? 0.95;
    if (t.flip) { bx.translate(Math.round(t.x), 0); bx.scale(-1, 1); bx.drawImage(sh.img, f.x, f.y, f.w, f.h, -Math.floor(f.w / 2), Math.round(t.y - f.h), f.w, f.h); }
    else bx.drawImage(sh.img, f.x, f.y, f.w, f.h, Math.round(t.x - f.w / 2), Math.round(t.y - f.h), f.w, f.h);
    bx.restore();
  }
}

// ================================================================== skins: repaint solid cells in the front layer (bark, leaves, slates, glass…)
SA_KIND.skins = s => { for (const q of s.list || []) SA.skins.push({ look: q[0], x: q[1], y: q[2], w: q[3], h: q[4] }); };
const SA_SKIN_COL = {
  bark: ['#1c1510', '#2d2118', '#3e2d1f', '#55402b', '#6b8a4a'], elder: ['#1a130e', '#2a1f16', '#3b2b1d', '#503b27', '#7aa05a'],
  leaves: ['#07120b', '#10231a', '#1b3a25', '#2c5a35', '#4f8a4a'], slate: ['#0c0a10', '#1b1822', '#2a2533', '#3d3649', '#6a3040'],
  glass: ['#0a0c14', '#1a2230', '#2c3a52', '#6a86a8', '#c8dcf0'], brick: ['#140b0c', '#241315', '#361c1e', '#4a2628', '#6a3a36'],
  tomb: ['#081012', '#10201f', '#1a302e', '#284644', '#4a7a70'],
};
function saPaintSkins() {
  if (!room || !room.front || !SA.skins.length) return;
  const fx = room.front.getContext('2d'), ts = tileSheet(room.def.biome), sk = sheet('xsa_skin');
  for (const q of SA.skins) {
    const C = SA_SKIN_COL[q.look] || SA_SKIN_COL.bark;
    for (let ty = q.y; ty < q.y + q.h; ty++) for (let tx = q.x; tx < q.x + q.w; tx++) {
      if (!isSolidT(room.grid[ty * room.w + tx])) continue;
      const px = tx * TILE, py = ty * TILE, L = tx === q.x || !isSolidT(tileAt(tx - 1, ty)), R = tx === q.x + q.w - 1 || !isSolidT(tileAt(tx + 1, ty));
      const top = ty === q.y || !isSolidT(tileAt(tx, ty - 1)), bot = !isSolidT(tileAt(tx, ty + 1));
      const tag = q.look + (L && R ? '' : L ? '_l' : R ? '_r' : '') ;
      if (sk.ok && sk.img.complete && (sk.has(tag) || sk.has(q.look))) {
        const t = sk.has(tag) ? tag : q.look, T = sk.tag(t), f = sk.frames[T.from + Math.floor(hash2(tx * 7, ty * 3) * (T.to - T.from + 1))];
        fx.clearRect(px, py, TILE, TILE); fx.drawImage(sk.img, f.x, f.y, f.w, f.h, px, py, TILE, TILE);
      } else {   // procedural fallback
        fx.fillStyle = C[1]; fx.fillRect(px, py, TILE, TILE);
        for (let i = 0; i < 6; i++) { fx.fillStyle = C[2 + (i % 2)]; fx.fillRect(px + Math.floor(hash2(tx * 13 + i, ty * 5) * 14), py + Math.floor(hash2(tx, ty * 11 + i) * 12), 2, 4); }
        if (L) { fx.fillStyle = C[0]; fx.fillRect(px, py, 2, TILE); }
        if (R) { fx.fillStyle = C[3]; fx.fillRect(px + 14, py, 2, TILE); }
      }
      if (top && q.look !== 'leaves' && q.look !== 'glass') { fx.fillStyle = C[4]; fx.fillRect(px, py, TILE, 2); fx.fillStyle = C[3]; fx.fillRect(px + 2, py + 2, TILE - 4, 1); }
      if (bot && q.look === 'leaves') { fx.fillStyle = C[2]; for (let i = 0; i < 4; i++) fx.fillRect(px + i * 4 + 1, py + TILE, 2, 2 + Math.floor(hash2(tx + i, ty) * 4)); }
    }
  }
}
function saRepaint() { saPaintBack(); saPaintSkins(); saPaintFront(); if (SA.glass) saPaintGlass(); }
// thorn walls (TV), broken walls and every other re-render rebuild the layers: paint over them again
{ const rrl = renderRoomLayers; renderRoomLayers = function (R) { rrl(R); if (R === room && SA.roomObj === room && saIn()) saRepaint(); }; }
if (typeof tvRerender === 'function') { const rr = tvRerender; tvRerender = function () { rr(); if (saIn()) saRepaint(); }; }

// ================================================================== ambient life: fireflies, drifting motes, light shafts
SA_KIND.flies = s => { for (let i = 0; i < (s.n || 12); i++) SA.flies.push({ x: (s.x - s.w / 2 + Math.random() * s.w) * TILE, y: (s.y - s.h / 2 + Math.random() * s.h) * TILE, ph: rand(0, 6.3), sp: rand(0.4, 1.1), a: s, col: s.col || '210,255,140' }); };
SA_KIND.motes = s => { for (let i = 0; i < (s.n || 12); i++) SA.motes.push({ x: (s.x - s.w / 2 + Math.random() * s.w) * TILE, y: (s.y - s.h / 2 + Math.random() * s.h) * TILE, vx: rand(-4, 4), vy: rand(-6, 2), ph: rand(0, 6.3), a: s, col: s.col || '170,255,200' }); };
SA_KIND.shaft = s => SA.shafts.push({ x: (s.x - s.w / 2) * TILE, y: (s.y - s.h / 2) * TILE, w: s.w * TILE, h: s.h * TILE, col: s.col || '220,240,255', a: s.a ?? 0.1, lean: s.lean ?? 0.35 });
function saUpdateAmbient(dt) {
  for (const f of SA.flies) {
    f.ph += dt * f.sp; const A = f.a;
    f.x += Math.cos(f.ph * 1.3) * 10 * dt + Math.sin(time * 0.7 + f.ph) * 4 * dt; f.y += Math.sin(f.ph * 1.7) * 8 * dt;
    const x0 = (A.x - A.w / 2) * TILE, x1 = (A.x + A.w / 2) * TILE, y0 = (A.y - A.h / 2) * TILE, y1 = (A.y + A.h / 2) * TILE;
    if (f.x < x0) f.x += (x1 - x0); if (f.x > x1) f.x -= (x1 - x0); if (f.y < y0) f.y = y1; if (f.y > y1) f.y = y0;
    if (SYS && SYS.vista && Math.hypot(f.x - P.x, f.y - P.y) < 60) f.x += (f.x - P.x) * 0.2 * dt;
  }
  for (const m of SA.motes) {
    m.ph += dt; m.x += (m.vx + Math.sin(m.ph) * 3) * dt; m.y += (m.vy + Math.cos(m.ph * 0.7) * 2) * dt; const A = m.a;
    const x0 = (A.x - A.w / 2) * TILE, x1 = (A.x + A.w / 2) * TILE, y0 = (A.y - A.h / 2) * TILE, y1 = (A.y + A.h / 2) * TILE;
    if (m.x < x0) m.x = x1; if (m.x > x1) m.x = x0; if (m.y < y0) m.y = y1; if (m.y > y1) m.y = y0;
  }
}
function saDrawAmbient() {
  const inView = (x, y, pad = 40) => x > cam.x - pad && x < cam.x + W + pad && y > cam.y - pad && y < cam.y + H + pad;
  drawGlow(() => {
    for (const q of SA.shafts) {
      if (!inView(q.x + q.w / 2, q.y + q.h / 2, q.w + q.h)) continue;
      const k = 0.75 + 0.25 * Math.sin(time * 0.6 + q.x * 0.01);
      for (let i = 0; i < q.h; i += 2) {
        const fall = i / q.h, a = q.a * k * (1 - fall * 0.85);
        g.fillStyle = `rgba(${q.col},${a.toFixed(3)})`;
        g.fillRect(Math.round(q.x + i * q.lean), Math.round(q.y + i), Math.round(q.w * (0.8 + fall * 0.4)), 2);
      }
    }
    for (const f of SA.flies) {
      if (!inView(f.x, f.y)) continue;
      const b = 0.5 + 0.5 * Math.sin(time * 3 * f.sp + f.ph * 3);
      if (b < 0.15) continue;
      g.fillStyle = `rgba(${f.col},${(0.35 + 0.65 * b).toFixed(2)})`; g.fillRect(Math.round(f.x), Math.round(f.y), 1, 1);
      if (b > 0.7) { g.fillStyle = `rgba(${f.col},0.25)`; g.fillRect(Math.round(f.x) - 1, Math.round(f.y), 3, 1); g.fillRect(Math.round(f.x), Math.round(f.y) - 1, 1, 3); addLight(f.x, f.y, 12, f.col, 0.35 * b); }
    }
    for (const m of SA.motes) {
      if (!inView(m.x, m.y)) continue;
      g.fillStyle = `rgba(${m.col},${(0.25 + 0.2 * Math.sin(m.ph * 2)).toFixed(2)})`; g.fillRect(Math.round(m.x), Math.round(m.y), 1, 1);
    }
  });
}

// ================================================================== signs: a line of text the first time you stand at a spot
SA_KIND.sign = (s, c) => SA.signs.push({ x: c.cx, y: c.fy, text: s.text, key: `xsa:sign:${c.id}:${s.x},${s.y}` });
// ================================================================== Thornveil: snares on the Hunter's Trail, the coven's rite
// a rusted jaw trap: steps on it snap it shut (hurts, holds you a moment); it creaks open again after a while
function saSnare(p, s) {
  p.shut = 0; p.anim = { update() {}, frame: 0 };
  const sh = p.sh;
  p.draw = () => { if (sh.ok && sh.has('snare')) drawSprite(sh, sh.first('snare') + (p.shut > 0 ? 1 : 0), p.x, p.y, 1, { bottom: true }); else { g.fillStyle = '#5a4a3a'; g.fillRect(Math.round(p.x) - 7, Math.round(p.y) - 3, 14, 3); } };
  p.update = dt => {
    if (p.shut > 0) { p.shut -= dt; if (p.shut <= 0) saSfx.creak(); return; }
    if (P.state !== 'dead' && P.ground && Math.abs(P.x - p.x) < 7 && Math.abs(P.y - p.y) < 3 && P.inv <= 0) {
      p.shut = 4; saSfx.snap(); shake = Math.max(shake, 2);
      if (hurtPlayer(Math.round(D.maxHp * 0.07 + 6), P.face, 'xsa_snare' + Math.floor(time), { src: 'snare', hazard: true })) { P.vx = 0; P.ctrlLock = Math.max(P.ctrlLock || 0, 0.35); }
    }
    for (const e of enemies) if (e.alive && !e.cfg.flying && Math.abs(e.x - p.x) < 7 && Math.abs(e.y - p.y) < 3 && p.shut <= 0) {
      p.shut = 4; saSfx.snap(); e.hit({ dmg: Math.round(e.maxHp * 0.15 + 5), poise: 40, dir: 1, kind: 'env', x: e.x, y: e.y - 8, quiet: true });
    }
  };
  p.hurtbox = () => p.shut > 0 ? null : rect(p.x - 7, p.y - 6, p.x + 7, p.y);
  p.onHit = () => { if (p.shut > 0) return; p.shut = 4; saSfx.snap(); spawnFx('hit', p.x, p.y - 4, 1); };   // strike it to spring it safely
}
// the coven's rite: while its gauntlet runs, thorns rise around the circle and roots erupt under whoever stands still
SA_KIND.rite = (s, c) => SA.rites.push({ x0: s.x * TILE, x1: (s.x + s.w) * TILE, floor: c.fy, g: s.gauntlet, k: 0, t: 2 });
function saUpdateRites(dt) {
  for (const r of SA.rites) {
    const on = !!(SYS.gaunt && SYS.gaunt.s && SYS.gaunt.s.id === r.g);
    r.k = approach(r.k, on ? 1 : 0, dt * (on ? 0.8 : 0.5));
    if (!on) continue;
    r.t -= dt;
    if (r.t <= 0 && typeof tvRootSpike === 'function' && P.state !== 'dead') {
      r.t = rand(2.6, 4.2);
      tvRootSpike(clamp(P.x + rand(-10, 10), r.x0 + 16, r.x1 - 16), r.floor, 0.9, Math.round(BOSS_DMG * 22 * NGP.dmg), { name: 'thorns' });
    }
  }
}
function saDrawRites() {
  for (const r of SA.rites) {
    if (r.k <= 0.01) continue;
    const hs = typeof tvHaz === 'function' ? tvHaz() : null;
    for (let x = r.x0 + 4; x < r.x1 - 4; x += 12) {
      const h = Math.round((10 + 10 * hash2(x, 3)) * r.k), y = r.floor;
      g.fillStyle = '#2a1a10'; g.fillRect(Math.round(x), y - h, 3, h); g.fillStyle = '#4a2e18'; g.fillRect(Math.round(x) + 1, y - h, 1, h);
      g.fillStyle = '#6a4a2a'; g.fillRect(Math.round(x) - 1, y - h + 3, 1, 1); g.fillRect(Math.round(x) + 3, y - h + 6, 1, 1);
    }
    if (hs && hs.ok) { const t = hs.tag('bramble'); for (let x = r.x0; x < r.x1; x += 22) drawSprite(hs, t.from + (Math.floor(x / 22) % 3), x + 8, r.floor + 2, 1, { bottom: true, alpha: r.k * 0.9 }); }
  }
}

// ================================================================== the thorn curtain (TV13 -> TV16): the ash-veil mechanic in bramble
function saReskinVeils() {
  if (room.def.biome !== 'thornveil') return;
  const vs = sheet('xsa_thornveil');
  for (const p of props) if (p.type === 'veil' && vs.ok) { p.sh = vs; p.anim = new Anim(vs, 'loop', true); }
}

// the Drowned Bell: no tongue, but it answers a blade
function saBigBell(p) {
  p.ring = 0;
  const draw = p.draw; p.draw = () => { g.save(); const a = Math.sin(time * 7) * 0.08 * p.ring; g.translate(p.x, p.y); g.rotate(a); g.translate(-p.x, -p.y); draw(); g.restore(); };
  p.update = dt => { p.ring = Math.max(0, p.ring - dt * 0.3); if (p.ring > 0) addLight(p.x, p.y + 50, 60, '120,230,210', 0.6 * p.ring); };
  p.hurtbox = () => rect(p.x - 22, p.y + 20, p.x + 22, p.y + 72);
  p.onHit = () => { if (p.ring > 0.6) return; p.ring = 1; if (typeof dbSfx !== 'undefined') dbSfx.toll(0.8); shake = Math.max(shake, 3);
    for (let i = 0; i < 20; i++) particles.push({ x: p.x + rand(-20, 20), y: p.y + rand(30, 70), vx: rand(-30, 30), vy: -rand(20, 60), life: 1.2, kind: 'db_bubble' }); };
}
// paint a sprite over solid cells of the front layer (the Drowned Saint's body is solid stone; this makes it look like her)
SA_KIND.frontpaint = (s, c) => SA.fpaint = (SA.fpaint || []).concat([{ ...s, bx: c.cx, by: c.fy + (s.dy || 0) }]);
function saPaintFront() {
  for (const q of SA.fpaint || []) {
    const sh = sheet(q.sheet); if (!sh.ok || !sh.img.complete) continue;
    const f = sh.frames[sh.first(q.tag)], fx = room.front.getContext('2d'), [rx, ry, rw, rh] = q.rect;
    fx.save(); fx.beginPath();
    for (let ty = ry; ty < ry + rh; ty++) for (let tx = rx; tx < rx + rw; tx++) if (isSolidT(room.grid[ty * room.w + tx])) fx.rect(tx * TILE, ty * TILE, TILE, TILE);
    fx.clip(); fx.drawImage(sh.img, f.x, f.y, f.w, f.h, Math.round(q.bx - f.w / 2), Math.round(q.by - f.h), f.w, f.h); fx.restore();
  }
}

// ================================================================== reach helpers: the updraft stand-ins for swimming (tools/reach.py) never exist in play
SA_KIND.reachhelp = s => { SA.rh = (SA.rh || []).concat(s.ids || []); };
function saDropReachHelpers() {
  if (!SA.rh || !SA.rh.length || typeof KIT === 'undefined') return;
  const ids = new Set(SA.rh), gone = KIT.objs.filter(o => o.id && ids.has(o.id));
  KIT.objs = KIT.objs.filter(o => !gone.includes(o)); for (const id of ids) delete KIT.byId[id];
  props = props.filter(p => !gone.includes(p));
}

// ================================================================== Barrows: drips from the vault, bubbles and pearls in the water
SA_KIND.leak = (s, c) => SA.leaks.push({ x: c.cx + rand(-4, 4), y: s.y * TILE, t: rand(0, 1.5), drops: [], pool: !!s.pool, stream: !!s.pool });
SA_KIND.bubbles = s => { for (let i = 0; i < (s.n || 12); i++) SA.bubbles.push({ x: (s.x - s.w / 2 + Math.random() * s.w) * TILE, y: (s.y - s.h / 2 + Math.random() * s.h) * TILE, a: s, v: rand(8, 22), ph: rand(0, 6.3) }); };
SA_KIND.pearls = s => { for (let i = 0; i < (s.n || 12); i++) SA.pearls.push({ x: (s.x - s.w / 2 + Math.random() * s.w) * TILE, y: (s.y - s.h / 2 + Math.random() * s.h) * TILE, a: s, v: rand(3, 9), ph: rand(0, 6.3), r: Math.random() < 0.3 ? 2 : 1 }); };
SA_KIND.petals = s => { for (let i = 0; i < (s.n || 12); i++) SA.pearls.push({ x: (s.x - s.w / 2 + Math.random() * s.w) * TILE, y: (s.y - s.h / 2 + Math.random() * s.h) * TILE, a: s, v: -rand(4, 10), ph: rand(0, 6.3), r: 1, petal: true }); };
const saWet = (x, y) => typeof dbDeepAt === 'function' && dbDeepAt(x, y);
function saUpdateWater(dt) {
  for (const L of SA.leaks) {
    L.t -= dt;
    if (L.t <= 0) { L.t = L.stream ? rand(0.05, 0.12) : rand(0.8, 2.4); L.drops.push({ x: L.x + rand(-1, 1), y: L.y + 2, vy: L.stream ? 60 : 0 }); }
    for (const d of L.drops) {
      d.vy += 520 * dt; d.y += d.vy * dt;
      if (solidAtPx(d.x, d.y) || saWet(d.x, d.y)) { d.dead = true; if (!L.stream || Math.random() < 0.2) { for (let i = 0; i < 2; i++) particles.push({ x: d.x, y: d.y - 2, vx: rand(-30, 30), vy: -rand(20, 50), g: 400, life: 0.3, kind: 'db_foam' }); if (!L.stream && Math.abs(d.x - P.x) < 200 && Math.random() < 0.5) saSfx.drip(); } }
    }
    L.drops = L.drops.filter(d => !d.dead);
  }
  for (const b of SA.bubbles) {
    b.ph += dt; b.y -= b.v * dt; b.x += Math.sin(b.ph * 2) * 6 * dt;
    if (!saWet(b.x, b.y) || b.y < (b.a.y - b.a.h / 2) * TILE) { b.y = (b.a.y + b.a.h / 2) * TILE - rand(0, 16); b.x = (b.a.x - b.a.w / 2 + Math.random() * b.a.w) * TILE; }
  }
  for (const q of SA.pearls) {
    q.ph += dt; q.y -= q.v * dt; q.x += Math.sin(q.ph * (q.petal ? 1.3 : 0.8)) * (q.petal ? 14 : 5) * dt;
    const A = q.a, y0 = (A.y - A.h / 2) * TILE, y1 = (A.y + A.h / 2) * TILE;
    if (q.y < y0) { q.y = y1; q.x = (A.x - A.w / 2 + Math.random() * A.w) * TILE; } if (q.y > y1) { q.y = y0; q.x = (A.x - A.w / 2 + Math.random() * A.w) * TILE; }
  }
}
function saDrawWater() {
  g.fillStyle = 'rgba(150,220,215,0.7)';
  for (const L of SA.leaks) {
    for (const d of L.drops) g.fillRect(Math.round(d.x), Math.round(d.y), 1, L.stream ? 3 : 2);
    if (L.stream && L.drops.length) { g.fillStyle = 'rgba(120,200,200,0.18)'; const d0 = L.drops[0]; g.fillRect(Math.round(L.x), L.y, 1, Math.max(0, Math.round(d0.y - L.y))); g.fillStyle = 'rgba(150,220,215,0.7)'; }
  }
  for (const b of SA.bubbles) { if (!saWet(b.x, b.y)) continue; g.fillStyle = 'rgba(190,240,235,0.55)'; g.fillRect(Math.round(b.x), Math.round(b.y), 1, 1); if (Math.sin(b.ph) > 0.6) { g.fillRect(Math.round(b.x) + 1, Math.round(b.y) - 1, 1, 1); } }
  drawGlow(() => {
    for (const q of SA.pearls) {
      if (q.petal) { g.fillStyle = `rgba(150,30,50,${0.5 + 0.3 * Math.sin(q.ph)})`; g.fillRect(Math.round(q.x), Math.round(q.y), 2, 1); continue; }
      const b = 0.6 + 0.4 * Math.sin(q.ph * 2);
      g.fillStyle = `rgba(235,250,255,${(0.5 + 0.5 * b).toFixed(2)})`; g.fillRect(Math.round(q.x), Math.round(q.y), q.r, q.r);
      if (q.r > 1) { g.fillStyle = 'rgba(200,240,255,0.25)'; g.fillRect(Math.round(q.x) - 1, Math.round(q.y), 4, 1); g.fillRect(Math.round(q.x), Math.round(q.y) - 1, 1, 4); addLight(q.x, q.y, 16, '200,240,255', 0.35 * b); }
    }
  });
}

// ================================================================== Tide Steps: the tide rises and falls on a cycle (the room's tide line, 31_barrows.js)
SA_KIND.tide = s => { SA.tides.push({ lo: room.def.tide, hi: room.def.tide_hi, per: room.def.tide_period || 16, t: 0 }); };
function saUpdateTides(dt) {
  if (!SA.tides.length || typeof DBW === 'undefined' || !DBW.tide) return;
  const T = SA.tides[0]; T.t += dt;
  // rise 40%, hold high 15%, fall 30%, hold low 15%: a readable rhythm with time to act at either extreme
  const k = (T.t % T.per) / T.per, e = x => x * x * (3 - 2 * x);
  const h = k < 0.4 ? e(k / 0.4) : k < 0.55 ? 1 : k < 0.85 ? 1 - e((k - 0.55) / 0.3) : 0;
  const y = (T.lo + (T.hi - T.lo) * h) * TILE + 2, was = DBW.tide.y;
  DBW.tide.target = y; DBW.tide.y = y; DBW.tide.speed = 0;
  if ((was < y) !== (T.lastDir || false) && Math.abs(was - y) > 0.05) { T.lastDir = was < y; if (T.lastDir) toast('The tide is going out.', 1.6); else toast('The tide is coming in.', 1.6); noise(2, 200, 0.6, 0.2, 'lowpass', 0.5); }
  if (Math.random() < 0.5) particles.push({ x: rand(cam.x, cam.x + W), y: y, vx: rand(-10, 10), vy: -rand(4, 12), life: 0.6, kind: 'db_foam' });
}

// ================================================================== The Floodgates: three basins, three wheels; a wheel won't turn under water
SA_KIND.floodgates = s => { SA.flood = { s, jams: 0, pipes: true }; };
function saFloodState(F) {   // each wheel toggles its pair; start state per basin
  const st = [...F.s.start];
  F.s.wheels.forEach((w, i) => { if (kitOn(w)) for (const b of F.s.pairs[i]) { const j = F.s.basins.indexOf(b); st[j] ^= 1; } });
  return st;
}
function saFloodSetup() {
  const F = SA.flood; if (!F) return;
  const apply = () => { const st = saFloodState(F); F.s.basins.forEach((b, i) => kitForce(b, !!st[i])); kitForce(F.s.drain, !st[2]); F.st = st; };
  apply(); F.apply = apply;
  for (const id of F.s.wheels) {
    const o = KIT.byId[id]; if (!o) continue;
    const wrapped = fn => info => {
      if (saWet(o.x, o.y - 8)) {   // the jam rule
        saSfx.jam(); o.hitT = 0.5; F.jams++;
        toast(F.jams >= 3 ? 'The keeper\'s plaque: turn a wheel only on dry ground. Each wheel swaps the water between the two basins its pipes run to.' : 'The wheel will not turn against the water standing over it.', F.jams >= 3 ? 5 : 2.4);
        return;
      }
      fn(info);
    };
    o.onHit = wrapped(o.onHit); o.interact = wrapped(o.interact);
  }
  props.unshift({ type: 'xsa_pipes', x: 0, y: 0, face: 1, anim: { update() {} }, draw: saDrawFloodPipes });
}
KIT.onChange.push(id => { const F = SA.flood; if (F && F.apply && SA.roomObj === room && F.s.wheels.includes(id)) { F.apply(); saSfx.creak(); shake = Math.max(shake, 2); } });
function saDrawFloodPipes() {   // the pipes on the wall: from each wheel to its two basins (the clue, in iron)
  const F = SA.flood; if (!F || !F.st) return;
  const bx = {}, y0 = 3 * TILE; for (const b of F.s.basins) bx[b] = KIT.byId[b] ? KIT.byId[b].x : 0;
  F.s.wheels.forEach((w, i) => {
    const o = KIT.byId[w]; if (!o) return; const lit = kitOn(w), c = lit ? '#b89a5a' : '#4a4640', hl = lit ? '#e8d09a' : '#6a655c';
    const yy = y0 - 8 + i * 4;
    for (const b of F.s.pairs[i]) {
      const x0 = Math.min(o.x, bx[b]), x1 = Math.max(o.x, bx[b]);
      g.fillStyle = c; g.fillRect(Math.round(x0), yy, Math.round(x1 - x0) + 2, 2); g.fillStyle = hl; g.fillRect(Math.round(x0), yy, Math.round(x1 - x0) + 2, 1);
      g.fillStyle = c; g.fillRect(Math.round(bx[b]), yy, 2, 4 * TILE - (yy - y0) + 8);
    }
    g.fillStyle = c; g.fillRect(Math.round(o.x) - 1, yy, 2, Math.round(o.y - yy) - 18);
  });
}

// ================================================================== trial gates: a gate that stays shut while a given trial runs (the Dive's way home)
SA_KIND.trialgate = s => (SA.tgates = SA.tgates || []).push(s);
function saUpdateTrialGates() { for (const s of SA.tgates || []) kitForce(s.gate, !(SYS.trial && SYS.trial.s && SYS.trial.s.id === s.trial)); }

// ================================================================== Crimson: the Portrait Riddle (the Countess's gaze)
SA_KIND.gaze = (s, c) => SA.gazes.push({ s, x: c.cx, y: s.y * TILE + 4, t: 0, fails: 0 });
const SA_SUBJ = ['a', 'b', 'c', 'd', 'e', 'a'];
function saGazeSetup() {
  for (const Gz of SA.gazes) {
    // the frames wear the manor's own portraits; their eyes burn red when lit
    const ps = sheet('cm_portrait');
    Gz.s.frames.forEach((id, i) => {
      const o = KIT.byId[id]; if (!o) return;
      o.draw = () => {
        const cy = o.spec.y * TILE + 4;
        if (ps.ok) drawSprite(ps, ps.first(SA_SUBJ[i % SA_SUBJ.length]), o.x, cy + 20, 1, { bottom: true, flash: o.wrongT > 0 ? o.wrongT * 0.7 : o.flash * 0.35, flashColor: o.wrongT > 0 ? '#ff3030' : '#fff2c0' });
        else { g.fillStyle = '#5a4020'; g.fillRect(o.x - 10, cy - 12, 20, 24); }
        const k = o.lit ? 1 : o.flash * 0.8;
        if (k > 0) { drawGlow(() => { g.fillStyle = `rgba(255,60,60,${k})`; g.fillRect(Math.round(o.x) - 4, Math.round(cy) - 5, 2, 1); g.fillRect(Math.round(o.x) + 2, Math.round(cy) - 5, 2, 1); }); addLight(o.x, cy - 3, 22, '255,80,80', 0.5 * k); }
      };
    });
    const q = KIT.byId[Gz.s.seq];
    if (q && q.hit) {
      const hit = q.hit;
      q.hit = m => { const was = q.prog; hit(m); if (!q.active && q.prog === 0 && (was > 0 || m.id !== q.order[0])) { Gz.fails++; if (Gz.fails >= 3) toast('Watch the Countess. Where her eyes rest, touch that portrait next.', 4); } };
    }
  }
}
function saDrawGaze() {
  for (const Gz of SA.gazes) {
    const q = KIT.byId[Gz.s.seq]; if (!q) continue;
    const ord = Gz.s.order, step = 1.3, cyc = ord.length * step + 2.2, t = time % cyc, i = Math.floor(t / step);
    const eyeY = Gz.y - 6;
    let tx = Gz.x, ty = eyeY + 2, on = false;
    if (!q.active && i < ord.length) { const o = KIT.byId[ord[i]]; if (o) { tx = o.x; ty = o.spec.y * TILE; on = true; } }
    const lk = (t % step) / step, glow = on ? Math.sin(Math.min(1, lk * 1.6) * Math.PI) : q.active ? 0.6 : 0.15;
    const dx = clamp((tx - Gz.x) / 60, -2, 2), dy = clamp((ty - eyeY) / 60, -1, 1);
    drawGlow(() => {
      g.fillStyle = `rgba(255,40,50,${(0.45 + 0.55 * glow).toFixed(2)})`;
      g.fillRect(Math.round(Gz.x - 5 + dx), Math.round(eyeY + dy), 2, 1); g.fillRect(Math.round(Gz.x + 3 + dx), Math.round(eyeY + dy), 2, 1);
      if (on && glow > 0.2) {   // a thread of red light along her gaze
        const n = Math.max(8, Math.hypot(tx - Gz.x, ty - eyeY) / 5);
        for (let k = 0; k < n; k++) { const f = k / n; if ((k + Math.floor(time * 12)) % 3) continue; g.fillStyle = `rgba(255,50,60,${(0.35 * glow * (1 - f * 0.5)).toFixed(2)})`; g.fillRect(Math.round(lerp(Gz.x, tx, f)), Math.round(lerp(eyeY, ty, f)), 1, 1); }
      }
    });
    addLight(Gz.x, eyeY, 24, '255,60,60', 0.35 + 0.4 * glow);
  }
}

// ================================================================== Crimson: the library's false bookcase (stands in the wall to CM17 until struck)
SA_KIND.bookcase = (s, c) => SA.books.push({ s, x: c.cx, y: c.fy, key: `x3:${c.id}:bookcase`, open: !!SAVE.flags[`x3:${c.id}:bookcase`], k: 0 });
function saBooksSetup() {
  for (const B of SA.books) {
    B.k = B.open ? 1 : 0;
    const cells = B.s.cells || [], shut = v => { for (const [x, y] of cells) room.grid[y * room.w + x] = v ? T_SOLID : T_EMPTY; };
    if (!B.open) shut(true);
    const sh = sheet('xsa_cm'), bx = cells.length ? cells[0][0] * TILE + 8 : B.x, by = cells.length ? (Math.max(...cells.map(q => q[1])) + 1) * TILE : B.y;
    props.push({ type: 'xsa_bookcase', x: bx, y: by, face: 1, anim: { update() {} }, hits: 0,
      draw() {
        const ox = Math.round(B.k * 20);
        if (B.k > 0.02) { g.fillStyle = 'rgba(6,2,4,0.92)'; g.fillRect(bx - 8, by - cells.length * TILE, 16, cells.length * TILE); }
        if (sh.ok && sh.has('bookcase')) drawSprite(sh, sh.first('bookcase'), bx - 4 - ox, by, 1, { bottom: true });
        else { g.fillStyle = '#3a2016'; g.fillRect(Math.round(bx) - 12 - ox, Math.round(by) - 44, 24, 44); }
      },
      hurtbox: () => B.open ? null : rect(bx - 16, by - 44, bx + 8, by),
      onHit() {   // a hollow knock, and on the third blow it swings aside on its hidden hinge
        this.hits++; noise(0.2, 300, 0.8, 0.25, 'lowpass', 0.4); tone(110, 0.2, 0.08, 'triangle', 0.7);
        if (this.hits >= 3 && !B.open) { B.open = true; SAVE.flags[B.key] = 1; shut(false); saSfx.creak(); shake = 3; toast('The bookcase swings aside on a hidden hinge.', 3); saveGame(); }
      } });
  }
}
function saUpdateBooks(dt) { for (const B of SA.books) B.k = approach(B.k, B.open ? 1 : 0, dt * 1.5); }

// ================================================================== Crimson: the Count's study gate (three keys) — a KM gate held shut until unlocked
SA_KIND.keygate = (s, c) => SA.keygates.push({ s, x: c.cx, y: c.fy, open: !!SAVE.flags[s.flag] });
function saKeygatesSetup() {
  for (const q of SA.keygates) {
    const keys = q.s.keys, gid = q.s.gate;
    kitForce(gid, q.open);
    const o = KIT.byId[gid], gx = (o ? o.x : q.x) + 12;
    props.push({ type: 'xsa_keylock', x: gx, y: q.y, face: 1, anim: { update() {} },
      prompt: () => q.open ? null : keys.every(k => SAVE.items[k]) ? 'Unlock' : 'Examine',
      interact: () => {
        if (q.open) return;
        const have = keys.filter(k => SAVE.items[k]).length;
        if (have < keys.length) { sfx.deny(); toast(have ? `The Count's study gate: three keyholes. ${have} of your keys fit${have === 1 ? 's' : ''}.` : 'A barred gate with three keyholes: the Count\'s study. The keys must be somewhere in the manor.', 3.5); return; }
        q.open = true; SAVE.flags[q.s.flag] = 1; kitForce(gid, true); saSfx.key(); saSfx.creak(); shake = 3; toast('Three keys turn. The study gate lifts.', 3); saveGame();
      },
      draw() {
        if (q.open) return;
        const x = Math.round(gx) - 12, y = Math.round(q.y) - 22;
        g.fillStyle = '#2a1818'; g.fillRect(x - 3, y, 6, 12); g.fillStyle = '#6a4a30'; g.fillRect(x - 2, y + 1, 4, 10);
        for (let i = 0; i < 3; i++) { const got = SAVE.items[keys[i]], ky = y + 2 + i * 3; g.fillStyle = got ? '#e8c070' : '#0a0808'; g.fillRect(x - 1, ky, 2, 2); if (got) addLight(x, ky + 1, 10, '255,200,120', 0.4); }
      } });
  }
}

// ================================================================== Crimson: the conservatory (its glass ribs over the moon, and the piano that plays itself)
SA_KIND.glasshouse = () => { SA.glass = true; };
function saPaintGlass() {
  if (!SA.glass || !room.back) return;
  const bx = room.back.getContext('2d'), w = room.pw, h = room.ph;
  bx.save();
  for (let x = 24; x < w; x += 48) {   // tall mullions and a pointed arch between each pair
    bx.fillStyle = 'rgba(20,16,26,0.9)'; bx.fillRect(x, 32, 3, h - 80);
    bx.fillStyle = 'rgba(90,80,110,0.5)'; bx.fillRect(x + 1, 32, 1, h - 80);
    bx.strokeStyle = 'rgba(30,24,38,0.85)'; bx.lineWidth = 2; bx.beginPath(); bx.moveTo(x + 1, 60); bx.quadraticCurveTo(x + 25, 30, x + 49, 60); bx.stroke();
  }
  for (let y = 80; y < h - 60; y += 44) { bx.fillStyle = 'rgba(20,16,26,0.7)'; bx.fillRect(16, y, w - 32, 2); }
  bx.fillStyle = 'rgba(180,190,230,0.05)'; for (let i = 0; i < 12; i++) bx.fillRect(Math.floor(hash2(i, 7) * w), 40, 1, h - 90);
  bx.restore();
}
SA_KIND.piano = (s, c) => SA.pianos.push({ x: c.cx, y: c.fy, t: 0, i: 0, keys: [] });
// a slow waltz in a minor key: [semitones from A3, beats]; one-two-three under a thin melody
const SA_WALTZ = [[12, 1], [15, 1], [19, 1], [17, 2], [15, 1], [14, 1], [12, 1], [10, 1], [12, 3], [7, 1], [10, 1], [14, 1], [12, 2], [10, 1], [8, 1], [7, 1], [5, 1], [7, 3],
                  [12, 1], [15, 1], [19, 1], [20, 2], [19, 1], [17, 1], [15, 1], [14, 1], [15, 3], [12, 1], [14, 1], [10, 1], [12, 3], [0, 3]];
function saUpdatePianos(dt) {
  for (const Pn of SA.pianos) {
    const d = Math.hypot(P.x - Pn.x, P.y - Pn.y), vol = clamp(1 - d / 380, 0, 1) * (SYS.vista ? 1.2 : 0.8);
    Pn.t -= dt; Pn.keys = Pn.keys.filter(k => (k.life -= dt) > 0);
    if (Pn.t > 0) continue;
    const [n, b] = SA_WALTZ[Pn.i % SA_WALTZ.length], beat = 0.62 + 0.05 * Math.sin(time * 0.1);
    Pn.i++; Pn.t = b * beat;
    if (vol <= 0.02) continue;
    const f = 220 * Math.pow(2, n / 12);
    tone(f, b * beat * 1.8, 0.035 * vol, 'triangle', 1, 0); tone(f * 2, b * beat, 0.01 * vol, 'sine', 1, 0.01);
    if (Pn.i % 3 === 1) { tone(110 * Math.pow(2, ((n % 12) - 12) / 12), beat * 2.6, 0.03 * vol, 'sine', 1, 0); }
    Pn.keys.push({ k: n % 14, life: 0.3 });
    particles.push({ x: Pn.x + rand(-10, 10), y: Pn.y - 30, vx: rand(-6, 6), vy: -rand(8, 16), life: 1.2, kind: 'mote' });
  }
}
function saDrawPianos() {   // keys dipping on their own
  for (const Pn of SA.pianos) for (const k of Pn.keys) { g.fillStyle = 'rgba(20,14,16,0.9)'; g.fillRect(Math.round(Pn.x) - 14 + k.k * 2, Math.round(Pn.y) - 17, 2, 2); }
}

// ================================================================== room setup and per-frame
HOOKS.enter.push(def => {
  saEnsure();
  if (!saIn() && !SA.signs.length) return;
  saReskinVeils();
  saRepaint();
  saDropReachHelpers(); saFloodSetup(); saGazeSetup(); saBooksSetup(); saKeygatesSetup();
  if (SA.back.length || SA.fpaint) { const need = SA.back.map(t => sheet(t.sh)).concat((SA.fpaint || []).map(q => sheet(q.sheet))).filter(s => s.ok && !s.img.complete); for (const s of need) s.img.addEventListener('load', () => { if (SA.roomObj === room) saRepaint(); }, { once: true }); }
  const ks = sheet('xsa_skin'); if (SA.skins.length && ks.ok && !ks.img.complete) ks.img.addEventListener('load', () => { if (SA.roomObj === room) saRepaint(); }, { once: true });
});
HOOKS.update.push(dt => {
  if (SA.roomObj !== room) return;
  saUpdateAmbient(dt); saUpdateRites(dt); saUpdateWater(dt); saUpdateTides(dt); saUpdateTrialGates();
  saUpdateBooks(dt); saUpdatePianos(dt);
  for (const q of SA.signs) if (!SAVE.flags[q.key] && Math.abs(P.x - q.x) < 20 && Math.abs(P.y - q.y) < 24) { SAVE.flags[q.key] = 1; toast(q.text, 3.5); }
  for (const p of SA.fronts) if (p.anim && p.anim.update) p.anim.update(dt);
});
HOOKS.render.push(() => {
  if (SA.roomObj !== room) return;
  saDrawRites(); saDrawWater(); saDrawGaze(); saDrawPianos();
  for (const p of SA.fronts) p.draw();
  saDrawAmbient();
});
// respawn safety (04_player.js SAFE_CHECKS): never set a spike respawn point on a snare, in the coven's rite or in deep water
if (typeof SAFE_CHECKS !== 'undefined') SAFE_CHECKS.push((x, y) => {
  if (SA.roomObj !== room || !saIn()) return false;
  for (const p of props) if (p.type === 'xsa_snare' && Math.abs(p.x - x) < 14 && Math.abs(p.y - y) < 8) return true;
  for (const r of SA.rites) if (r.k > 0.05 && x > r.x0 && x < r.x1) return true;
  return saWet(x, y - 3) && !SAVE.items.tidebreath;
});
// debug handle for the headless tests (tools/shots/sa)
if (typeof window !== 'undefined' && window.__game) window.__game.sa = { SA, KIT, kitOn, kitForce, get SYS() { return SYS; }, get room() { return room; }, wet: (x, y) => saWet(x, y), tileAt: (x, y) => tileAt(x, y), get DBS() { return typeof DBS !== 'undefined' ? DBS : null; }, get time() { return time; }, tideY: () => (typeof DBW !== 'undefined' && DBW.tide ? DBW.tide.y / 16 : null) };
