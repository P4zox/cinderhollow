// ------------------------------------------------------------------ EXPANSION 3 · agent SBX: the Deadward (Necropolis) + the Buried Road (Dunes)
// Rooms NV8-NV16 and DU9-DU18 (tools/regions/84_sb.py). This file: lore pages sb_*, the two trial charms (Headsman's Hood,
// Scarab Wing), decor props (`xsb`, sheets xsb_nv / xsb_du / xsb_tall), backdrop paintings (room kwarg xsb_paint -> xsb_big,
// painted once into the back layer), the Last Oasis sky + still pool, the golden scarab, puzzle hints, barred-door hints.
// Every top-level name is prefixed sb/SBX (all region files share one scope).
const SBX = { roomRef: null, hint: {}, wrong: {}, mir: 0, mirRot: null, barT: 0, paintTries: 0 };
const SB_GHOST = '140,190,255', SB_SUN = '255,200,120';

// ================================================================== lore (the Hallow Chronicle)
try {
  Object.assign(LORE_PAGES, {
    sb_1: { region: 'necropolis', title: 'The Mourners’ Gate', text: 'Here the living stopped. Past this gate the dead of Vael kept their own watch, in ranks, as they had in life.\nMourners were paid to weep at the gate and no farther. Their tears are cut into the stone, so the weeping would not end when the wages did.' },
    sb_2: { region: 'necropolis', title: 'The Last King’s Bier', text: 'King Vael had this bier raised before he died, and had himself carved lying on it with his sword on his breast, so that the city would grow used to the sight.\nIt never did. The great bell was hung beneath it so its voice would reach the stone king first. From the throne above, it is said, he listened to his own funeral every hour, and could not stop it.' },
    sb_3: { region: 'necropolis', title: 'Roll of the Charnel Guard', text: 'Headsmen, chain-bearers and the bell-guard slept here in tiers, boots on, axes racked where a hand could find them in the dark.\nThe last entry in the roll is not a name. It reads: None relieved. We keep the watch.' },
    sb_4: { region: 'necropolis', title: 'The Dirge of Kings', text: 'The dirge was rung for kings alone: six strokes, as the slab by the door is cut.\nA bell that hangs low speaks low. The mark set lowest on the stave is the bell that hangs deepest; the mark set highest is the bell nearest the roof. Ring them left to right, as the mourners walk.' },
    sb_5: { region: 'necropolis', title: 'The Twelfth Niche', text: 'Beneath the throne lie the eleven kings before Vael, crowns still on, their names worn away by the hands of pilgrims.\nVael came down here the night the Pale Root rose. He left the twelfth niche empty. He meant it for himself. He never came back to fill it.' },
    sb_12: { region: 'necropolis', title: 'The Headsman\u2019s Drain', text: 'Under the Headsman\u2019s Yard the city kept a drain for what the block let fall. It runs to the old bell-pits and no farther.\nThe undercroft was never swept. The executioners said the dead should be allowed to leave the way they came, a little at a time.' },
    sb_6: { region: 'dunes', title: 'The Buried Road', text: 'The caravans came down this road with salt, linen and the dead of far cities, who paid in gold to lie near the sun-kings.\nThe sand took the road a little at a time. The last caravan did not turn back. Scarabs nest in its wagons now, and some of them are gold.' },
    sb_7: { region: 'dunes', title: 'The Last Oasis', text: 'The sun-kings kept one pool the sand was forbidden to touch. Here they came to watch the evening, which they held to be a death that always returns.\nFar above, the true sun still sets. Its light falls down a shaft of glass a thousand feet deep and arrives here as evening, every evening, on water that has never learned it is underground.' },
    sb_8: { region: 'dunes', title: 'The Seal', text: 'Speak the king’s titles as the painters set them in the hall above, from the door inward, and the seal will know its master.\nIt is patient with strangers. It was built to be.' },
    sb_9: { region: 'dunes', title: 'The Nameless King', text: 'This king’s name was struck from every wall, every jar and every list. Even his coffin was left blank.\nThe priests who did it buried him all the same, under a dune, with bread for the road and a seed for the far side. Whatever he had done, they could not let him go hungry.' },
    sb_10: { region: 'dunes', title: 'The Sun-Spire', text: 'The spire is the tip of the sun-kings’ first temple. The rest lies under the sand, room after room, every door facing east.\nEach dawn the priests climbed it to catch the first light in the gilded disc. The disc still burns. No one has told it the priests are gone.' },
    sb_11: { region: 'dunes', title: 'Carrying Noon', text: 'Noon is carried, not waited for.\nTurn the mirrors until the light walks from the roof to the door. Each turn moves it an eighth of the sky.' },
  });
} catch (e) { console.warn('sb lore', e); }

// ================================================================== trial charms
try {
  registerGear({ charms: {
    c_x3_hood: { name: 'Headsman’s Hood', desc: 'The black hood of the Deadward’s executioners. Roll through a blow at the last instant and time stalls around you for a heartbeat.' },
    c_x3_scarab: { name: 'Scarab Wing', desc: 'A gilded wing-case from the foot of the sandfall. Land from any height and move at once: no stagger, no pause.' },
  } }, 'xsb_icons');
} catch (e) { console.warn('sb charms', e); }
// Scarab Wing: the landing pose is skipped (any fall, any height)
HOOKS.update.push(dt => {
  if (!P || !charmOn('c_x3_scarab')) return;
  if (P.state === 'land' && P.ground) { const m = Math.abs(P.vx) > 5 || inputX() ? 'run' : 'idle'; setP(m, m, true); }
});
// Headsman's Hood: a blow negated in the first instants of a roll stalls time: a short global hitch, then every foe
// runs slow for a second (W's slow wrapper, so bosses and enemies of every class slow the same way)
SBX.hoodCd = 0;
HOOKS.update.push(dt => { if (SBX.hoodCd > 0) SBX.hoodCd -= dt; if (SBX.hoodT > 0) SBX.hoodT -= dt; });
(HOOKS.negated = HOOKS.negated || []).push((dmg, dir, opt) => {
  if (!charmOn('c_x3_hood') || P.state !== 'roll' || SBX.hoodCd > 0) return;
  if (!P.anim || P.anim.i > 2) return;                       // only a roll begun at the last moment
  SBX.hoodCd = 3; SBX.hoodT = 1;
  slowmo = Math.max(slowmo, 0.22); hitstop = Math.max(hitstop, 0.05); flashScreen = Math.max(flashScreen, 0.12);
  tone(196, 0.9, 0.08, 'sine', 0.5); tone(98, 1.1, 0.1, 'triangle', 0.6); noise(0.5, 400, 0.5, 0.15, 'lowpass', 0.5);
  for (const t of targets()) { if (t.prop || !t.update) continue; t._slowT = Math.max(t._slowT || 0, 1.0); if (typeof wSlowWrap === 'function') wSlowWrap(t); }
  for (let i = 0; i < 12; i++) particles.push({ x: P.x + rand(-12, 12), y: P.y - rand(0, 26), vx: rand(-30, 30), vy: -rand(5, 30), life: rand(0.5, 1), kind: 'nvghost' });
});
HOOKS.renderTop.push(() => {
  if (!(SBX.hoodT > 0)) return;
  const a = Math.min(1, SBX.hoodT * 2) * 0.16;
  g.fillStyle = `rgba(40,60,110,${a})`; g.fillRect(0, 0, W, H);
});

// ================================================================== decor props ('xsb')
// kind -> [sheet, tag, variants(0 = none), light(prop) or null, hang]
const SB_DECO = {
  lamppost: ['xsb_nv', 'lamppost'], headstone: ['xsb_nv', 'headstone', 2], tombchest: ['xsb_nv', 'tombchest', 2], mourner: ['xsb_nv', 'mourner'],
  cage: ['xsb_nv', 'cage', 0, true], rack: ['xsb_nv', 'rack'], dummy: ['xsb_nv', 'dummy'], bunk: ['xsb_nv', 'bunk'], drum: ['xsb_nv', 'drum'],
  axestump: ['xsb_nv', 'axestump'], kingskull: ['xsb_nv', 'kingskull', 2],
  jars: ['xsb_du', 'jars', 2], crates: ['xsb_du', 'crates'], banner_du: ['xsb_du', 'banner_du'], reeds: ['xsb_du', 'reeds', 3],
  scarabidol: ['xsb_du', 'scarabidol'], hoard: ['xsb_du', 'hoard'], sarcophagus: ['xsb_du', 'sarcophagus', 2], brazier_du: ['xsb_du', 'brazier_du'],
  statue_du: ['xsb_du', 'statue_du'],
  palm: ['xsb_tall', 'palm', 3], palmdead: ['xsb_tall', 'palmdead'], obelisk: ['xsb_tall', 'obelisk'], ruincol: ['xsb_tall', 'ruincol', 2],
};
const SB_LIGHT = {
  lamppost: p => { for (const s of [-1, 1]) addLight(p.x + s * 9 * p.face, p.y - 44, 46, SB_GHOST, 0.75, LX_FLICKER); },
  headstone: p => { if (p.v === 1) addLight(p.x + 9 * p.face, p.y - 9, 22, SB_GHOST, 0.5, LX_FLICKER); },
  tombchest: p => { if (p.v === 1) { addLight(p.x - 16 * p.face, p.y - 26, 26, SB_GHOST, 0.55, LX_FLICKER); addLight(p.x + 16 * p.face, p.y - 26, 26, SB_GHOST, 0.55, LX_FLICKER); } },
  mourner: p => addLight(p.x + 2, p.y - 38, 16, SB_GHOST, 0.3),
  kingskull: p => addLight(p.x, p.y - 20, 30, p.v ? SB_GHOST : '255,210,120', 0.45),
  scarabidol: p => addLight(p.x, p.y - 38, 34, '255,200,90', 0.7),
  hoard: p => addLight(p.x, p.y - 10, 40, '255,210,110', 0.5),
  brazier_du: p => { addLight(p.x, p.y - 30, 70, '255,170,80', 0.95, LX_FLICKER); if (Math.random() < 0.2) particles.push({ x: p.x + rand(-5, 5), y: p.y - 30, vx: rand(-5, 5), vy: -rand(15, 35), life: rand(0.4, 0.8), kind: 'fire' }); },
  obelisk: p => addLight(p.x, p.y - 92, 26, '255,220,140', 0.5),
  statue_du: p => addLight(p.x + 4 * p.face, p.y - 40, 10, '255,190,90', 0.5),
};
// stand decor on whatever surface lies under its cell (rock, a thin floor, or a dune's slope line)
function sbGroundY(x, y0) {
  for (let y = y0; y < y0 + 4 * TILE && y < room.ph; y++) {
    const t = tileAt(Math.floor(x / TILE), Math.floor(y / TILE));
    if (typeof DU_T_SLOPE !== 'undefined' && t === DU_T_SLOPE) { const h = duSlopeY(room, x); if (h && h.y <= y + 1) return Math.round(h.y); }
    if (isSolidT(t) || t === T_PLAT) return Math.floor(y / TILE) * TILE;
  }
  return y0;
}
SPAWNS.xsb = (s, c) => {
  if (s.kind === 'dropmark') return sbDropmark(s, c);
  if (s.kind === 'sunshaft') return sbSunshaft(s, c);
  const d = SB_DECO[s.kind]; if (!d) return;
  const [shn, tag0, nv, hang] = d, sh = sheet(shn), v = nv ? ((s.v || 0) % nv) : 0, tag = v ? tag0 + v : tag0;
  const face = s.face || 1;
  let y = hang ? (() => { let t = s.y * TILE; while (t > 0 && !solidAtPx(c.cx, t - 1)) t -= TILE; return t; })() : sbGroundY(c.cx, s.y * TILE);
  const p = { type: 'xsb_' + s.kind, x: c.cx + (s.dx || 0), y, face, v, sh, hang, anim: sh.ok && sh.has(tag) ? new Anim(sh, tag, true) : { update() {}, frame: 0 } };
  if (p.anim.t !== undefined) p.anim.t = rand(0, 400);
  const L = SB_LIGHT[s.kind];
  if (L) p.update = () => L(p);
  p.draw = () => { if (sh.ok && sh.has(tag)) drawSprite(sh, p.anim.frame, p.x, p.y, face, hang ? { pivot: [Math.floor(sh.fw / 2), 0] } : { bottom: true }); };
  props.push(p);
};
// the ↓+Space marker over thin floors that are real ways on
function sbDropmark(s, c) {
  const p = { type: 'xsb_drop', x: c.cx, y: c.fy, face: 1, anim: { update() {} }, shown: false,
    update() {
      const on = P.ground && Math.abs(P.x - this.x) < 26 && Math.abs(P.y - this.y) < 4;
      if (on && !this.shown) { this.shown = true; toast(matchMedia('(pointer: coarse)').matches ? 'Hold ▼ and press Jump to drop through' : 'Hold ↓ and press Space to drop through', 3); }
      if (!on && Math.abs(P.x - this.x) > 80) this.shown = false;
    },
    draw() {
      const a = 0.4 + 0.3 * Math.sin(time * 4), X = Math.round(this.x), Y = Math.round(this.y - 14 + Math.sin(time * 4) * 1.5);
      const col = room.def.biome === 'dunes' ? '255,226,160' : '160,205,255';
      g.fillStyle = `rgba(${col},${a})`; g.fillRect(X - 1, Y - 5, 2, 5); g.fillRect(X - 3, Y, 6, 1); g.fillRect(X - 2, Y + 1, 4, 1); g.fillRect(X - 1, Y + 2, 2, 1);
      addLight(this.x, this.y - 12, 18, col, 0.35);
    } };
  props.push(p);
}
// a column of sunlight falling from a hole in the roof
function sbSunshaft(s, c) {
  let top = s.y * TILE; while (top > 0 && !solidAtPx(c.cx, top - 1)) top -= TILE;
  const bot = sbGroundY(c.cx, s.y * TILE);
  props.push({ type: 'xsb_shaft', x: c.cx, y: bot, face: 1, anim: { update() {} },
    update() { addLight(this.x, top + 16, 34, '255,226,160', 0.4, { shadow: false }); addLight(this.x, bot - 8, 38, '255,214,140', 0.35, { shadow: false }); },
    draw() {
      const draw = () => {
        g.save(); g.globalCompositeOperation = 'lighter';
        for (let i = 0; i < 3; i++) { const w = 10 + i * 7, a = 0.07 - i * 0.018 + 0.015 * Math.sin(time * 0.8 + i); g.fillStyle = `rgba(255,220,150,${a})`; g.fillRect(Math.round(this.x - w / 2), top, w, bot - top); }
        for (let k = 0; k < 6; k++) { const yy = top + ((time * 18 + k * 37) % (bot - top)), xx = this.x + Math.sin(time * 0.9 + k * 2) * 8; g.fillStyle = 'rgba(255,240,200,0.6)'; g.fillRect(Math.round(xx), Math.round(yy), 1, 1); }
        g.restore();
      };
      if (typeof drawGlow === 'function') drawGlow(draw); else draw();
    } });
}

// ================================================================== backdrop paintings (xsb_paint: [[tag, tileX, standRow], ...])
function sbPaintRoom(R) {
  const list = R.def.xsb_paint; if (!list || R.sbPainted) return true;
  const sh = sheet('xsb_big'); if (!sh.ok) { R.sbPainted = true; return true; }
  const img = sh.img; if (!img.complete || !img.naturalWidth) return false;
  const ctx = R.back.getContext('2d');
  for (const [tag, tx, ty] of list) {
    if (!sh.has(tag)) continue;
    const f = sh.frames[sh.first(tag)];
    ctx.drawImage(img, f.x, f.y, f.w, f.h, Math.round(tx * TILE + 8 - f.w / 2), (ty + 1) * TILE - f.h, f.w, f.h);
  }
  if (R.def.id === 'DU11') sbInkTitles(R, ctx);
  R.sbPainted = true; return true;
}
// the Pharaoh's titles, inked into the four cartouches with the very runes the Seal's tablets carry
const SB_TITLES = [2, 5, 0, 7];
function sbInkTitles(R, ctx) {
  const sh = sheet('kit_parts'), ent = (R.def.xsb_paint || []).find(q => q[0] === 'titles'); if (!ent || !sh.ok || !sh.has('glyph_lit')) return;
  const img = sh.img; if (!img.complete) return;
  const x0 = ent[1] * TILE + 8 - 96, y0 = (ent[2] + 1) * TILE - 128;
  SB_TITLES.forEach((sym, i) => {
    const f = sh.frames[sh.first('glyph') + sym], cx = x0 + 26 + i * 46, cy = y0 + 63;
    ctx.drawImage(img, f.x, f.y, f.w, f.h, cx - f.w / 2, cy - f.h / 2, f.w, f.h);
  });
}

// ================================================================== the Last Oasis: a sunset sky and a still pool
function sbDrawSky() {
  const sh = sheet('xsb_sky');
  g.fillStyle = '#2a1030'; g.fillRect(0, 0, W, H);
  if (!sh.ok) return;
  const lay = (tag, fac, vfac) => {
    const f = sh.frames[sh.first(tag)];
    const ox = -((cam.x * fac) % f.w + f.w) % f.w, oy = Math.round(clamp(-cam.y * vfac, -(f.h - H) - 20, 20));
    for (let x = Math.round(ox); x < W; x += f.w) g.drawImage(sh.img, f.x, f.y, f.w, f.h, x, oy + (H - f.h), f.w, f.h);
  };
  lay('far', 0.04, 0.02); lay('mid', 0.16, 0.06);
}
try {
  if (typeof drawParallax === 'function') {
    const sbPar = drawParallax;
    drawParallax = function () { if (room && room.def && room.def.xsb_sky) return sbDrawSky(); return sbPar.apply(this, arguments); };   // eslint-disable-line no-func-assign
  }
} catch (e) { console.warn('sb sky', e); }
SPAWNS.xsb_pool = (s, c) => {
  const x0 = s.x * TILE, x1 = x0 + (s.w || 8) * TILE, y = s.y * TILE + 5, y1 = (s.y + 1) * TILE;
  const SK = ['#f8c858', '#ee9a34', '#d86a2a', '#b8402e', '#922a36', '#6a1c3c'];
  props.push({ type: 'xsb_pool', x: (x0 + x1) / 2, y: y1, face: 1, anim: { update() {} }, ripple: 0, lastX: 0,
    update(dt) {
      addLight((x0 + x1) / 2, y, 70, '255,170,110', 0.35, { shadow: false });
      if (P.x > x0 && P.x < x1 && P.ground && P.y >= y1 - 1) {
        if (Math.abs(P.x - this.lastX) > 6) { this.lastX = P.x; this.ripple = 1; for (let i = 0; i < 3; i++) particles.push({ x: P.x + rand(-5, 5), y: y + 1, vx: rand(-30, 30), vy: -rand(20, 50), g: 300, life: 0.4, kind: 'spark' }); }
      }
      this.ripple = Math.max(0, this.ripple - (dt || 1 / 60));
    },
    draw() {
      for (let yy = y; yy < y1; yy++) {
        const d = (yy - y) / (y1 - y);
        for (let x = x0; x < x1; x += 2) {
          const k = Math.min(SK.length - 1, Math.floor(d * 4 + ((x * 7 + yy * 3) % 4) * 0.2));
          g.fillStyle = SK[SK.length - 1 - k]; g.fillRect(x, yy, 2, 1);
        }
      }
      g.save(); g.globalAlpha = 0.75;   // the sun's road across the water, shimmering
      for (let yy = y + 1; yy < y1; yy += 2) { const w = 10 + Math.sin(time * 2 + yy) * 4; g.fillStyle = '#fff0a8'; g.fillRect(Math.round((x0 + x1) / 2 + 20 - w / 2 + Math.sin(time * 3 + yy * 0.7) * 2), yy, Math.round(w), 1); }
      g.restore();
      g.fillStyle = 'rgba(255,236,190,0.8)'; g.fillRect(x0, y, x1 - x0, 1);
      if (this.ripple > 0) { g.fillStyle = `rgba(255,240,210,${this.ripple * 0.7})`; const r = (1 - this.ripple) * 18; g.fillRect(Math.round(P.x - r), y + 2, Math.round(r * 2), 1); }
      for (let i = 0; i < 4; i++) { const gx = x0 + ((time * 9 + i * 53) % (x1 - x0)); g.fillStyle = 'rgba(255,250,230,0.8)'; g.fillRect(Math.round(gx), y + 1 + (i % 3) * 3, 2, 1); }
    } });
};

// ================================================================== the golden scarab (Caravan Road): it leads you to its crack
SPAWNS.xsb_scarab = (s, c) => {
  if (SAVE.visited && SAVE.visited.DU18 && Math.random() < 0.6) return;
  const sh = sheet('xsb_bug'), crack = (s.crack || [s.x, s.x + 1]), cx = (crack[0] + crack[1] + 1) * TILE / 2;
  const b = { type: 'xsb_scarab', x: c.cx, y: c.fy, face: -1, sh, st: 'idle', t: rand(0, 2), anim: new Anim(sh, 'walk', true), a: 1,
    update(dt) {
      dt = dt || 1 / 60; this.t += dt; this.anim.update(dt);
      const near = Math.abs(P.x - this.x) < 110 && Math.abs(P.y - this.y) < 60;
      if (this.st === 'idle') { this.x += Math.sin(this.t * 1.3) * 6 * dt; this.face = Math.cos(this.t * 1.3) > 0 ? 1 : -1; if (near) { this.st = 'run'; if (!SAVE.hints.sb_scarab) { SAVE.hints.sb_scarab = 1; toast('A golden scarab scurries off through the sand…', 3); } } }
      else if (this.st === 'run') {
        const d = cx - this.x; this.face = Math.sign(d) || 1; this.x += Math.sign(d) * Math.min(Math.abs(d), 70 * dt);
        if (Math.abs(d) < 1) { this.st = 'dig'; this.anim.set('dig', false); sfx.dig ? sfx.dig() : noise(0.3, 900, 0.8, 0.12, 'bandpass', 1); }
      } else if (this.st === 'dig') { this.y += 14 * dt; this.a = Math.max(0, this.a - dt * 1.6); if (this.a <= 0) this.dead = true; }
      if (this.dead) { const i = props.indexOf(this); if (i >= 0) props.splice(i, 1); return; }
      addLight(this.x, this.y - 5, 18, '255,210,90', 0.55 * this.a);
      if (Math.random() < 0.05 * this.a) particles.push({ x: this.x + rand(-3, 3), y: this.y - 6, vx: 0, vy: -rand(5, 15), life: 0.5, kind: 'spark' });
    },
    draw() { if (sh.ok) drawSprite(sh, this.anim.frame, this.x, this.y, this.face, { bottom: true, alpha: this.a }); } };
  props.push(b);
};

// ================================================================== room hooks: paint, dunes ambience, hints
const SB_DU_AMB = { DU19: 0.28, DU9: 0.3, DU10: 0.22, DU11: 0.5, DU12: 0.3, DU13: 0.46, DU14: 0.52, DU15: 0.16, DU16: 0.36, DU17: 0.6, DU18: 0.5 };
try {
  if (typeof DU_OPEN !== 'undefined') for (const id of ['DU9', 'DU10', 'DU12', 'DU15', 'DU19']) DU_OPEN.add(id);
  if (typeof DU_AMB !== 'undefined') Object.assign(DU_AMB, SB_DU_AMB);
} catch (e) { console.warn('sb dunes', e); }
HOOKS.enter.push(def => {
  SBX.roomRef = room; SBX.hint = {}; SBX.mir = 0; SBX.mirRot = null; SBX.barT = 0; SBX.paintTries = 0;
  if (!def.x3 || !/^(NV|DU)\d/.test(def.id)) return;
  if (def.xsb_hall && !room.sbHall) sbHallBack(room);
  sbPaintRoom(room);
});
// tomb halls and crypts are closed rooms: their back wall is whole (no desert or city showing through), with a painted frieze
function sbHallBack(R) {
  const sh = tileSheet(R.def.biome); if (!sh.ok || !sh.img.complete) return;
  R.sbHall = true;
  const ctx = R.back.getContext('2d'), du = R.def.biome === 'dunes';
  for (let y = 0; y < R.h; y++) for (let x = 0; x < R.w; x++) {
    if (isSolidT(R.grid[y * R.w + x])) continue;
    drawTile(ctx, sh, 38 + Math.floor(hash2(x, y) * 4), x * TILE, y * TILE, 1);
    const deco = { x: 42, r: 43, k: 44, b: 45 }[R.def.map[y][x]];
    if (deco !== undefined) drawTile(ctx, sh, deco, x * TILE, y * TILE);
  }
  if (!du) return;
  for (let x = 0; x < R.pw; x++) {   // the frieze: gold and lapis bands two rows under the ceiling
    if (isSolidT(tileAtR(R, Math.floor(x / TILE), 2))) continue;
    ctx.fillStyle = '#a06818'; ctx.fillRect(x, 2 * TILE + 2, 1, 2); ctx.fillStyle = x % 12 < 6 ? '#203e80' : '#3a2208'; ctx.fillRect(x, 2 * TILE + 5, 1, 5);
    ctx.fillStyle = '#d09a2a'; if (x % 12 === 3) ctx.fillRect(x - 1, 2 * TILE + 6, 3, 3); ctx.fillStyle = '#6a4210'; ctx.fillRect(x, 2 * TILE + 11, 1, 1);
  }
}
// puzzle hints: a gentle nudge after three wrong tries (the Dirge, the Seal) or a lot of mirror turning (the Sun Dial)
const SB_SEQ_HINT = {
  NV12: ['dirge', 'The slab by the door: the lower a mark is cut, the lower its bell hangs. Six strokes, left to right.'],
  DU14: ['titles', 'The painted hall above names his titles in order, from the door inward. Touch the same four runes.'],
};
const SB_BARS = { NV10: { gate: 'bar', x: 40 }, DU10: { gate: 'bar', x: 5 } };   // loop-back gates: their lever is on the far (west) side
HOOKS.update.push(dt => {
  if (!room || SBX.roomRef !== room || !room.def.x3) return;
  const id = room.id;
  if (room.def.xsb_hall && !room.sbHall && SBX.paintTries < 600) sbHallBack(room);
  if (room.def.xsb_paint && !room.sbPainted && SBX.paintTries++ < 600) sbPaintRoom(room);
  if (typeof KIT === 'undefined' || KIT.roomObj !== room) return;
  const sq = SB_SEQ_HINT[id];
  if (sq) {
    const o = KIT.byId[sq[0]];
    if (o && !o.active) {
      const bad = o.bad > 0.7;
      if (bad && !SBX.wasBad) { SBX.wrong[id] = (SBX.wrong[id] || 0) + 1; if (SBX.wrong[id] === 3 || SBX.wrong[id] === 7) toast(sq[1], 5); }
      SBX.wasBad = bad;
    }
  }
  if (id === 'DU13') {
    const ms = ['M1', 'M2', 'M3', 'M4'].map(k => KIT.byId[k] && KIT.byId[k].rot);
    if (SBX.mirRot) ms.forEach((r, i) => { if (r !== SBX.mirRot[i]) SBX.mir++; });
    SBX.mirRot = ms;
    const so = KIT.byId.so;
    if (SBX.mir >= 14 && !SBX.hint.mir && so && !so.active) { SBX.hint.mir = 1; toast('Follow the light: down from the roof, across, then up and over to the socket above the door. The fourth mirror is a liar.', 6); }
  }
  const bar = SB_BARS[id];
  if (bar && P.ground) {   // at the barred gate from the wing side: say why it won't open from here
    const gate = KIT.byId[bar.gate], gx = (bar.x + 0.5) * TILE;
    if (gate && !gate.on && P.x > gx && P.x - gx < 40 && Math.abs(P.y - gate.y) < 6 && !SBX.hint.bar) { SBX.hint.bar = 1; toast('Barred from the other side.', 3); }
  }
});

// ================================================================== dune slopes: step up onto the rock at the top of a slope
// A slope line ends exactly on a block's top edge, but a body on the slope stands a few pixels lower when its side
// reaches the block, so walking uphill stalled against a 2-4 px lip. Lift it onto the block (dunes rooms only).
HOOKS.update.push(dt => {
  if (!room || room.def.biome !== 'dunes' || !P || !P.duSlope || !P.ground) return;
  const dir = inputX(); if (!dir) return;
  const px = P.x + dir * ((P.w || 10) / 2 + 1), tx = Math.floor(px / TILE), ty = Math.floor((P.y - 1) / TILE);
  if (!isSolidT(tileAt(tx, ty)) || isSolidT(tileAt(tx, ty - 1)) || isSolidT(tileAt(tx, ty - 2))) return;
  const top = ty * TILE; if (P.y - top > 6 || P.y - top <= 0) return;
  P.y = top; P.x = dir > 0 ? tx * TILE + 0.5 : (tx + 1) * TILE - 0.5; P.vy = 0; P.duSlope = 0;
});

// ================================================================== respawn safety: never put the player back inside a hazard of these rooms
// (quicksand, a headsman's axe sweep, a bell walkway that tolls away)
try {
  SAFE_CHECKS.push((x, y) => {
    if (!room || !room.def.x3 || !/^(NV|DU)\d/.test(room.id)) return false;
    const tx = Math.floor(x / TILE), ty = Math.floor((y + 1) / TILE);
    for (let dx = -1; dx <= 1; dx++) {
      const t = tileAt(tx + dx, ty), t1 = tileAt(tx + dx, ty - 1);
      if (typeof DU_T_QS !== 'undefined' && (t === DU_T_QS || t1 === DU_T_QS)) return true;
      if (typeof NV_T_A !== 'undefined' && (t === NV_T_A || t === NV_T_B)) return true;
    }
    if (typeof NVR !== 'undefined' && NVR.walks && NVR.walks.some(w => !w.on && Math.abs(w.x - tx) <= 1 && w.y === ty)) return true;   // a walkway that is away right now
    if (typeof KIT !== 'undefined' && KIT.roomObj === room) for (const o of KIT.objs) {
      if (o.kind !== 'pendulum') continue;
      const L = (o.spec.len ?? 4) * TILE + 12;
      if (Math.hypot(x - o.x, (y - 13) - o.y) < L && y - 13 > o.y) return true;
    }
    return false;
  });
} catch (e) { console.warn('sb safe', e); }

// ================================================================== debug handle for the SB test scripts
if (window.__game) Object.assign(window.__game, { sb: SBX, sbHurt: d => hurtPlayer(d, 1, 'sbtest' + Math.random(), {}) });
