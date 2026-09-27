// ------------------------------------------------------------------ EXPANSION 3, agent RB: the new rooms of the Weeping Mire (M7–M14),
// the Ashen Archives (A8–A16) and the Hoarfrost Aqueduct (HF8–HF15). Rooms: tools/regions/81_rb.py. Art: art/gen_xrb.py (xrb_*).
// This file adds: the decor spawn 'xrb' (painted backdrops, props, live fog/pages/snow/aurora), water ambushes ('xrb_ambush'),
// the ink abyss tile '9', the Index Room's books ('xrb_books'), freezing locks ('xrb_freeze'), falling icicles that freeze into
// footholds ('xrb_icicle'), puzzle hints ('xrb_hint'), the Chronicle pages rb_*, and the Archives/Hoarfrost trial charms.
// Every top-level name is prefixed rb/RB/xrb: all region files share one scope.

// ================================================================== the Hallow Chronicle: pages found in these rooms
Object.assign(LORE_PAGES, {
  rb_1: { region: 'mire', title: 'A Letter, Never Sent', text: 'Folded under a candle stub, the seal unbroken on the inside:\n“Brother. The Mire took the road and the road took the men. I kept the lantern lit for eleven nights and no boat came.\nI am going on to the chapel. If the ferryman returns, tell him the debt is paid. Tell him I paid it standing.\n— K.”\nThe wax is Ser Kalden’s. The hand is steadier than the man who wrote it could have been.' },
  rb_2: { region: 'mire', title: 'The Fisherman’s Rest', text: 'The old fisher of the Grove sat here every dusk and counted the lights on the water. Some nights there were more than there were lanterns.\nHe said the drowned keep lanterns too, and that you may rest beside them, so long as you do not answer when they call you by name.' },
  rb_3: { region: 'mire', title: 'Valve House Standing Orders', text: 'Cut into a slate by the gantry:\nOne wheel high, one wheel low. Turn either and the water turns.\nHigh water floats the barges to the upper door. Low water opens the sluice to the reeds.\nDo not open the sluice while the barges are up. We lost Oren that way.' },
  rb_4: { region: 'archives', title: 'Marginalia on the Unwritten', text: 'In the margin of a psalter, very small:\n“It is not a book. It is what a book becomes when no one is left to read it and it goes on writing anyway.\nI have heard it at night through the floors, the pen scratching. It asks for names. It does not need them; it wants to be the one to say them.\nIf you read this, do not sign your work.”' },
  rb_5: { region: 'archives', title: 'The Scribe’s Word', text: 'Carved into the lectern before the wall of runes:\n“The door keeps a word, and the word is four runes long. I wrote the runes on four leaves and pinned them where I worked, one leaf to a room, and numbered them so the order would outlive my memory.\nStrike the runes on this wall as the leaves are numbered, first to last. The wall forgives one mistake. It forgets the rest.”' },
  rb_6: { region: 'archives', title: 'An Index Card', text: 'On a lectern, pinned under glass:\nFOLIO OF THE UNWRITTEN — withdrawn from the stacks.\nShelved in three parts: 3 · 9 · 14.\nPull the three together and the case will open. Pull any other and the shelf will set them back.' },
  rb_7: { region: 'archives', title: 'Rain on the Glass', text: 'A reading-desk book, the last page dated:\n“The rain has not stopped since the Root broke through the east wing. The windows are the only clean thing left. I come here to read by them because the candles in the stacks have started to burn violet.\nToday a page turned by itself. I did not look at what was written.”' },
  rb_8: { region: 'archives', title: 'The Censor', text: 'A robed skeleton, a ring of keys still at its belt, a page pressed flat under its hand:\n“Every book in this room was withdrawn for our safety. I have read them all, for our safety. I will stay with them, for our safety.\nThe door has no handle on this side. I had it made that way.”' },
  rb_9: { region: 'hoarfrost', title: 'Under the Aurora', text: 'Scratched into the bench’s rime with a knife-point:\n“The reservoir froze in one night, all the way down. The fish are still in it, looking up.\nThe sky does this every winter now, green and slow, as if something above the clouds is breathing on a cold glass. My brother says it is the Root’s light. I say it is the last of the summer, leaving.”' },
  rb_10: { region: 'hoarfrost', title: 'Aqueduct Milestone', text: 'A worn stone, the old league-marks just legible:\nTO THE CITY, NINE LEAGUES. TO THE SEA, NONE.\nBelow it, newer and cruder: The water stopped. We stayed to mend it. We are still mending it.' },
  rb_11: { region: 'hoarfrost', title: 'Lockkeeper’s Tablet', text: 'Three fires, three locks, three pipes, painted in soot along the wall:\nThe top lock’s fire thaws the top lock. The second fire in the upper hall runs its pipe all the way down, to the deepest lock. The fire on the middle landing thaws the middle.\nKeep your feet on ice. Water here does not forgive.' },
});

// ================================================================== charms (trial rewards)
if (typeof ICON_SHEETS !== 'undefined' && !ICON_SHEETS.includes('xrb_icons')) ICON_SHEETS.push('xrb_icons');
registerGear({ charms: {
  c_x3_ink: { name: 'Inkbound Grapple', iconSheet: 'xrb_icons', desc: 'A coil of golden root soaked black in the Archives’ ink. The Root Hook reaches 30% farther and reels you in faster.' },
  c_x3_rime: { name: 'Rime Heart', iconSheet: 'xrb_icons', desc: 'A heart of frost around a coal that will not go out. Foes your Ember Dash passes through are chilled to the bone.' },
} }, 'xrb_icons');
// Inkbound Grapple: a longer throw (retry at 1.3× range when the normal one finds nothing) and a faster reel
{
  const _rbTryHook = tryHook;
  tryHook = function () {
    if (_rbTryHook.apply(this, arguments)) return true;
    if (!charmOn('c_x3_ink') || !SAVE.items.hook || !room.hooks || !room.hooks.length) return false;
    let best = null, bd = 1e9;
    for (const h of room.hooks) {
      const dx = h.x - P.x, dy = h.y - (P.y - 20), d = Math.hypot(dx, dy);
      if (d > HOOK_RANGE * 1.3 || dy > 30) continue;
      const score = d - (Math.sign(dx) === P.face ? 40 : 0);
      if (score < bd && lineOfSight(P.x, P.y - 22, h.x, h.y + 6)) { bd = score; best = h; }
    }
    if (!best) return false;
    const dx = P.x - best.x, dy = (P.y - 34) - best.y;
    P.hook = { h: best, len: clamp(Math.hypot(dx, dy), 38, 96), ang: Math.atan2(dx, dy), av: 0, zip: true };
    setP('hook', pHas('hook_throw') ? 'hook_throw' : 'jump_up', false);
    sfx.shoot(); tone(660, 0.15, 0.05, 'triangle', 1.5); tone(330, 0.2, 0.04, 'sine', 1.2);
    return true;
  };
}
HOOKS.update.push(dt => {
  if (!P || !P.hook || !P.hook.zip || !P.hook.h || !charmOn('c_x3_ink')) return;
  const H = P.hook, dx = P.x - H.h.x, dy = (P.y - 34) - H.h.y, d = Math.hypot(dx, dy);
  if (d > H.len + 4) { const k = Math.min(1, 200 * dt / d); const nx = P.x - dx * k, ny = P.y - dy * k; if (!solidAtPx(nx, ny - 13)) { P.x = nx; P.y = ny; } }
  if (Math.random() < 0.4) particles.push({ x: P.x + rand(-3, 3), y: P.y - 20, vx: 0, vy: rand(-10, 10), life: 0.35, kind: 'ink' });
});
// Rime Heart: the Ember Dash chills whatever it passes through (frost buildup + a slow), once per dash
const RB_RIME = { hit: new Set(), on: false };
HOOKS.update.push(() => {
  if (!P || !charmOn('c_x3_rime') || !SAVE.items.emberdash) return;
  if (P.state !== 'roll') { if (RB_RIME.on) { RB_RIME.on = false; RB_RIME.hit.clear(); } return; }
  RB_RIME.on = true;
  const me = playerHurtbox();
  for (const t of targets()) {
    if (t.prop || RB_RIME.hit.has(t)) continue;
    const hb = t.hurtbox && t.hurtbox(); if (!hb || !overlap(me, hb)) continue;
    RB_RIME.hit.add(t);
    if (typeof WSTATUS !== 'undefined') WSTATUS.frost(t, t.boss ? 22 : 45);
    t._slowT = Math.max(t._slowT || 0, t.boss ? 0.8 : 1.8); if (typeof wSlowWrap === 'function') wSlowWrap(t);
    const cx = (hb.x0 + hb.x1) / 2, cy = (hb.y0 + hb.y1) / 2;
    for (let i = 0; i < 10; i++) particles.push({ x: cx + rand(-6, 6), y: cy + rand(-10, 10), vx: rand(-60, 60), vy: -rand(10, 70), g: 200, life: rand(0.4, 0.8), kind: 'frost' });
    tone(1760, 0.18, 0.05, 'triangle', 0.6);
  }
});

// ================================================================== shared state (per room)
const XRB = { roomObj: null, fg: [], areas: [], ambush: [], hints: [], books: null, freeze: [], feet: [], stuck: 0, wet: 0, notes: [], drops: undefined };
const xrbMine = def => def && /^(M(7|8|9|1[0-4])|A([89]|1[0-6])|HF([89]|1[0-5]))$/.test(def.id);
function xrbEnsure() { if (XRB.roomObj !== room) Object.assign(XRB, { roomObj: room, fg: [], areas: [], ambush: [], hints: [], books: null, freeze: [], feet: [], stuck: 0, wet: 0, notes: [], wrongs: 0, drops: undefined, aurora: null }); }
const xrbSh = n => sheet(n);
function xrbFrame(sh, tag, i = 0) { if (!sh.ok || !sh.has(tag)) return -1; const t = sh.tag(tag); return t.from + (((i % (t.to - t.from + 1)) + (t.to - t.from + 1)) % (t.to - t.from + 1)); }
function xrbLoop(sh, tag, fps, seed = 0) { if (!sh.ok || !sh.has(tag)) return -1; const t = sh.tag(tag), n = t.to - t.from + 1; return t.from + (Math.floor(time * fps + seed) % n); }
// a tiny 3x5 pixel font for numerals drawn in the world (book spines, leaf numbers)
const XRB_DIG = { 0: '111101101101111', 1: '010110010010111', 2: '111001111100111', 3: '111001111001111', 4: '101101111001001', 5: '111100111001111',
  6: '111100111101111', 7: '111001010010010', 8: '111101111101111', 9: '111101111001111', I: '010010010010010', V: '101101101101010' };
function xrbGlyph(str, x, y, col) {
  g.fillStyle = col; let cx = Math.round(x);
  for (const ch of String(str)) { const m = XRB_DIG[ch]; if (m) for (let i = 0; i < 15; i++) if (m[i] === '1') g.fillRect(cx + (i % 3), Math.round(y) + Math.floor(i / 3), 1, 1); cx += 4; }
}
const xrbRoman = n => ['', 'I', 'II', 'III', 'IV', 'V'][n] || String(n);

// ================================================================== painted layers: drawn into the room's cached canvases
// back: big scenery behind the terrain (trees, the hut, arches, shelves, backdrops). front: bookcase faces over solid stacks.
function xrbPaint(R) {
  const def = R.def; if (!def.spawns || !xrbMine(def)) return;
  const bx = R.back.getContext('2d'), fx2 = R.front.getContext('2d');
  const blit = (ctx, sh, fr, x, y, o = {}) => {   // x,y: bottom centre
    if (fr < 0 || !sh.ok) return; const f = sh.frames[fr];
    ctx.save(); ctx.globalAlpha = o.alpha ?? 1;
    if (o.flip) { ctx.translate(Math.round(x), 0); ctx.scale(-1, 1); ctx.drawImage(sh.img, f.x, f.y, f.w, f.h, -Math.floor(f.w / 2), Math.round(y) - f.h, f.w, f.h); }
    else ctx.drawImage(sh.img, f.x, f.y, f.w, f.h, Math.round(x) - Math.floor(f.w / 2), Math.round(y) - f.h, f.w, f.h);
    ctx.restore();
  };
  const piece = (ctx, name, px, py, a = 1) => { const sh = xrbSh('xrb_ashelf'), fr = xrbFrame(sh, name); if (fr < 0) { ctx.fillStyle = '#2b201a'; ctx.fillRect(px, py, 16, 16); return; } const f = sh.frames[fr]; ctx.globalAlpha = a; ctx.drawImage(sh.img, f.x, f.y, 16, 16, px, py, 16, 16); ctx.globalAlpha = 1; };
  const bookcase = (ctx, x0, y0, w, h, a, broken, seed) => {   // w, h in tiles, top-left tile
    for (let yy = 0; yy < h; yy++) for (let xx = 0; xx < w; xx++) {
      const L = xx === 0, Rr = xx === w - 1, top = yy === 0, bot = yy === h - 1;
      let n = top ? (broken ? 'bk' : L ? 'tl' : Rr ? 'tr' : 't') : bot ? (L ? 'bl' : Rr ? 'br' : 'b') : L ? 'l' : Rr ? 'r' : 'm' + Math.floor(hash2(x0 + xx + seed, y0 + yy) * 4);
      if (w === 1 && !top && !bot) n = 'm' + Math.floor(hash2(x0 + seed, y0 + yy) * 4);
      piece(ctx, n, (x0 + xx) * TILE, (y0 + yy) * TILE, a);
    }
  };
  const order = def.spawns.filter(s => s.t === 'xrb').sort((a, b) => (/backdrop/.test(b.d) ? 1 : 0) - (/backdrop/.test(a.d) ? 1 : 0));   // backdrops first
  for (const s of order) {
    const cx = s.x * TILE + 8 + (s.ox || 0), fy = (s.y + 1) * TILE + (s.oy || 0);
    switch (s.d) {
      case 'm_tree': blit(bx, xrbSh('xrb_mtree'), xrbFrame(xrbSh('xrb_mtree'), 't' + (s.v || 0)), cx, fy + 4, { flip: s.flip, alpha: 0.95 }); break;
      case 'm_bigtree': blit(bx, xrbSh('xrb_mbig'), xrbFrame(xrbSh('xrb_mbig'), 'idle'), cx, fy + 4); break;
      case 'm_pump': blit(bx, xrbSh('xrb_mprop'), xrbFrame(xrbSh('xrb_mprop'), 'pump'), cx, fy); break;
      case 'm_net': blit(bx, xrbSh('xrb_mprop'), xrbFrame(xrbSh('xrb_mprop'), 'net'), cx, fy); break;
      case 'a_shelf': bookcase(bx, s.x, s.y - (s.h || 4) + 1, s.w || 2, s.h || 4, 0.9, false, s.x * 7); break;
      case 'a_stack': bookcase(fx2, s.x, s.r0, s.w || 3, s.r1 - s.r0 + 1, 1, !!s.broken, s.x * 13 + s.r0); break;
      case 'a_codex': blit(bx, xrbSh('xrb_acodex'), xrbFrame(xrbSh('xrb_acodex'), 'idle'), cx + 8, fy + 60); break;
      case 'a_window': blit(bx, xrbSh('xrb_awin'), xrbFrame(xrbSh('xrb_awin'), 'idle'), cx, fy + 2); break;
      case 'a_mural': blit(bx, xrbSh('xrb_amural'), xrbFrame(xrbSh('xrb_amural'), 'idle'), cx, fy + 16, { alpha: 0.9 }); break;
      case 'a_falseshelf': if (!SAVE.flags[brokenKey(def, s.x + 1, s.y)]) blit(fx2, xrbSh('xrb_aprop'), xrbFrame(xrbSh('xrb_aprop'), 'falseshelf'), cx, fy); break;
      case 'f_arch': blit(bx, xrbSh('xrb_fbig'), xrbFrame(xrbSh('xrb_fbig'), 'arch'), cx, fy + 2, { alpha: 0.95 }); break;
      case 'f_arch2': blit(bx, xrbSh('xrb_fbig'), xrbFrame(xrbSh('xrb_fbig'), 'arch2'), cx, fy, { alpha: 0.85 }); break;
      case 'f_statue': blit(bx, xrbSh('xrb_fbig'), xrbFrame(xrbSh('xrb_fbig'), 'statue'), cx, fy); break;
      case 'f_pump': blit(bx, xrbSh('xrb_fbig'), xrbFrame(xrbSh('xrb_fbig'), 'pump'), cx, fy, { flip: s.v === 1 }); break;
      case 'm_hut': blit(bx, xrbSh('xrb_mhut'), xrbFrame(xrbSh('xrb_mhut'), 'idle'), cx, fy); break;
      case 'm_pipes': case 'f_pipes': xrbPipes(bx, s, def.biome); break;
      case 'f_bigfall': xrbBigFall(bx, s); break;
      case 'm_backdrop': case 'a_backdrop': xrbBackdrop(bx, R, s); break;
    }
  }
}
// edge dressing, painted once per room build over the terrain: rime and icicle fringes (Hoarfrost), hanging roots and moss
// (Mire), cobwebs and ink drips (Archives). Deterministic per cell, so a room always looks the same.
function xrbDress(R) {
  const def = R.def, fx2 = R.front.getContext('2d'), b = def.biome;
  const sol = (x, y) => isSolidT(tileAtR(R, x, y)), inR = (x, y) => x >= 0 && y >= 0 && x < R.w && y < R.h;
  for (let y = 0; y < R.h; y++) for (let x = 0; x < R.w; x++) {
    if (!isSolidT(R.grid[y * R.w + x]) || !inR(x, y + 1) || sol(x, y + 1)) continue;   // an underside with air below
    const px = x * TILE, py = (y + 1) * TILE, h = hash2(x * 3 + 11, y * 7 + 5);
    if (b === 'hoarfrost') {
      fx2.fillStyle = 'rgba(200,232,248,0.55)'; fx2.fillRect(px, py - 1, 16, 1);
      for (let i = 0; i < 4; i++) { const hh = hash2(x * 5 + i, y), L = Math.floor(hh * hh * 8); if (L < 2) continue; const ix = px + 2 + i * 4;
        fx2.fillStyle = '#0e2236'; fx2.fillRect(ix - 1, py, 3, L); fx2.fillStyle = '#82c6dc'; fx2.fillRect(ix, py, 1, L); fx2.fillStyle = '#e6fbff'; fx2.fillRect(ix, py, 1, 1); }
    } else if (b === 'mire') {
      if (h < 0.55) for (let i = 0; i < 3; i++) { const hh = hash2(x + i * 13, y * 3), L = 3 + Math.floor(hh * 12), ix = px + 2 + i * 5 + Math.floor(hh * 3);
        if (hh < 0.3) continue;
        fx2.fillStyle = hh > 0.7 ? '#34442c' : '#241c14'; fx2.fillRect(ix, py, 1, L); if (hh > 0.55) { fx2.fillStyle = '#46583a'; fx2.fillRect(ix + 1, py + 2, 1, L - 3); } }
    } else if (b === 'archives') {
      if (h < 0.18) { fx2.fillStyle = 'rgba(40,28,70,0.9)'; const L = 3 + Math.floor(h * 30); fx2.fillRect(px + 7, py, 1, L); fx2.fillStyle = 'rgba(120,90,200,0.8)'; fx2.fillRect(px + 7, py + L, 1, 1); }
      const cw = (dx) => {   // a cobweb in an inner corner: ceiling above, wall at the side
        if (!sol(x + dx, y + 1)) return; const cx0 = dx < 0 ? px : px + 16;
        fx2.strokeStyle = 'rgba(200,190,170,0.22)'; fx2.lineWidth = 1; fx2.beginPath();
        for (let k = 1; k <= 3; k++) { fx2.moveTo(cx0 - dx * 0, py + k * 3); fx2.lineTo(cx0 - dx * k * 3 * 1, py); }
        fx2.moveTo(cx0, py); fx2.lineTo(cx0 - dx * 10, py + 10); fx2.stroke();
      };
      if (h > 0.6) { cw(-1); cw(1); }
    }
  }
}
{ const _rbRRL = renderRoomLayers; renderRoomLayers = function (R) { _rbRRL.apply(this, arguments); try { if (R && R.back) { xrbPaint(R); if (xrbMine(R.def)) xrbDress(R); } } catch (e) { console.error(e); } }; }

function xrbPipes(ctx, s, biome) {   // a run of old pipes along a wall: horizontal main + drops, rivets, rime or moss
  const x0 = s.x * TILE, x1 = (s.x + (s.w || 8)) * TILE, y = s.y * TILE + 4, frost = biome === 'hoarfrost';
  const c = frost ? ['#10151d', '#253040', '#3b4a60', '#6a7c94'] : ['#0f0d0a', '#2a241a', '#3e3526', '#5a4c34'];
  const main = (yy, th) => { ctx.fillStyle = c[0]; ctx.fillRect(x0, yy - 1, x1 - x0, th + 2); ctx.fillStyle = c[1]; ctx.fillRect(x0, yy, x1 - x0, th); ctx.fillStyle = c[3]; ctx.fillRect(x0, yy + 1, x1 - x0, 1); ctx.fillStyle = c[2]; ctx.fillRect(x0, yy + 2, x1 - x0, 1); };
  main(y, 6); if (s.v !== 1) main(y + 12, 4);
  for (let x = x0 + 12; x < x1 - 8; x += 40 + ((x * 7) % 24)) {
    ctx.fillStyle = c[0]; ctx.fillRect(x - 3, y - 2, 8, 10); ctx.fillStyle = c[2]; ctx.fillRect(x - 2, y - 1, 6, 8); ctx.fillStyle = c[3]; ctx.fillRect(x - 2, y - 1, 6, 1);
    const L = 24 + ((x * 13) % 56); ctx.fillStyle = c[0]; ctx.fillRect(x - 1, y + 6, 4, L); ctx.fillStyle = c[1]; ctx.fillRect(x, y + 6, 2, L); ctx.fillStyle = c[3]; ctx.fillRect(x, y + 6, 1, L);
    if (frost) { ctx.fillStyle = '#cfe8f4'; for (let k = 0; k < 3; k++) ctx.fillRect(x + k - 1, y + 6 + L, 1, 3 + k * 2); }
    else { ctx.fillStyle = '#34442c'; for (let k = 0; k < 5; k++) ctx.fillRect(x - 2 + k, y + 5, 1, 2 + (k * 3) % 5); }
  }
  if (frost) { ctx.fillStyle = 'rgba(214,236,248,0.85)'; for (let x = x0; x < x1; x += 2) if (hash2(x, y) < 0.7) ctx.fillRect(x, y - 1, 2, 1); }
}
function xrbBigFall(ctx, s) {   // the Frozen Falls: four columns of the old waterfall art side by side, from `top` down to the pool
  const sh = sheet('hf_icefall'); if (!sh.ok) return;
  const top = (s.top || 2) * TILE, bot = (s.y + 1) * TILE, cx = s.x * TILE + 8;
  for (let c = -2; c <= 1; c++) {
    const x = cx + c * 28 + 14, f0 = sh.frames[sh.first('top')], fm = sh.frames[sh.first('mid') + ((c + 2) % 3)], fb = sh.frames[sh.first('bottom')];
    ctx.globalAlpha = c === -2 || c === 1 ? 0.7 : 0.9;
    ctx.drawImage(sh.img, f0.x, f0.y, f0.w, f0.h, x - 16, top, f0.w, f0.h);
    for (let y = top + f0.h; y < bot - fb.h; y += fm.h) ctx.drawImage(sh.img, fm.x, fm.y, fm.w, Math.min(fm.h, bot - fb.h - y), x - 16, y, fm.w, Math.min(fm.h, bot - fb.h - y));
    ctx.drawImage(sh.img, fb.x, fb.y, fb.w, fb.h, x - 16, bot - fb.h, fb.w, fb.h);
  }
  ctx.globalAlpha = 1;
}
// vista backdrops: a painted night beyond the room (replaces the faded back wall in the open part of the room)
function xrbBackdrop(ctx, R, s) {
  const W0 = R.pw, H0 = R.ph, mire = s.scene === 'mire';
  const air = (x, y) => !isSolidT(R.grid[y * R.w + x]);
  // clear the back wall where the room is open, keep it hugging the terrain
  for (let y = 0; y < R.h; y++) for (let x = 0; x < R.w; x++) {
    if (!air(x, y)) continue;
    let near = false; for (let yy = -1; yy <= 1 && !near; yy++) for (let xx = -1; xx <= 1; xx++) { const t = tileAtR(R, x + xx, y + yy); if (isSolidT(t)) { near = true; break; } }
    if (!near) ctx.clearRect(x * TILE, y * TILE, TILE, TILE);
  }
  ctx.save(); ctx.globalCompositeOperation = 'destination-over';   // behind whatever back wall remains
  if (mire) {
    // moonlit fog over the marsh: sky gradient, the moon, far dead trees, low mist banks
    const gr = ctx.createLinearGradient(0, 0, 0, H0); gr.addColorStop(0, '#0a120f'); gr.addColorStop(0.55, '#1b2a22'); gr.addColorStop(1, '#2c3a2c');
    const mx = W0 * 0.72, my = H0 * 0.22;
    // far trees, then the moon halo, then the sky (destination-over: nearest first)
    ctx.fillStyle = '#101812';
    for (let i = 0; i < 9; i++) { const x = (i * 71 + 23) % W0, h = 60 + (i * 37) % 70; ctx.fillRect(x, H0 * 0.62 - h, 3, h); for (let k = 0; k < 4; k++) { const by = H0 * 0.62 - h + 8 + k * 12, d = (k % 2 ? 1 : -1) * (8 + k * 3); ctx.fillRect(Math.min(x, x + d), by, Math.abs(d), 1); } }
    ctx.fillStyle = '#14201a'; ctx.fillRect(0, H0 * 0.62, W0, H0 * 0.4);
    ctx.fillStyle = '#d8e0c0'; ctx.beginPath(); ctx.arc(mx, my, 13, 0, 7); ctx.fill();
    const hl = ctx.createRadialGradient(mx, my, 10, mx, my, 110); hl.addColorStop(0, 'rgba(200,220,170,0.4)'); hl.addColorStop(1, 'rgba(200,220,170,0)');
    ctx.fillStyle = hl; ctx.fillRect(0, 0, W0, H0);
    ctx.fillStyle = gr; ctx.fillRect(0, 0, W0, H0);
  } else {
    // a rain-dark sky over the Hallow and the Pale Root far off, seen through the Reading Nook's window
    ctx.fillStyle = '#1a1826'; ctx.beginPath(); ctx.moveTo(W0 * 0.55, H0 * 0.7); ctx.bezierCurveTo(W0 * 0.62, H0 * 0.35, W0 * 0.7, H0 * 0.2, W0 * 0.78, 0); ctx.lineTo(W0 * 0.84, 0); ctx.bezierCurveTo(W0 * 0.76, H0 * 0.25, W0 * 0.7, H0 * 0.5, W0 * 0.66, H0 * 0.7); ctx.fill();
    ctx.fillStyle = '#12101c'; ctx.fillRect(0, H0 * 0.66, W0, H0);
    for (let i = 0; i < 14; i++) { ctx.fillStyle = i % 3 ? '#0d0c16' : '#16141f'; const x = i * 40 - 10, h = 18 + (i * 29) % 40; ctx.fillRect(x, H0 * 0.66 - h, 22 + (i * 7) % 16, h); }
    const gr = ctx.createLinearGradient(0, 0, 0, H0); gr.addColorStop(0, '#0b0a14'); gr.addColorStop(0.6, '#241f36'); gr.addColorStop(1, '#3a2c3a');
    ctx.fillStyle = gr; ctx.fillRect(0, 0, W0, H0);
  }
  ctx.restore();
}

// ================================================================== decor props (animated / lit), live areas (fog, pages, snow…)
const XRB_PROP = {   // d -> [sheet, tag, fps, light]
  m_reeds: ['xrb_mprop', s => 'reeds' + ((s.v || 0) % 2), 3.2], m_lily: ['xrb_mprop', 'lily'], m_mush: ['xrb_mprop', 'mush', 1.4, [30, '140,230,90', 0.55, -8]],
  m_lantpost: ['xrb_mprop', 'lantpost', 7, [70, '255,180,90', 0.9, -30, 7]], m_stilt: ['xrb_mprop', 'stilt'], m_boat: ['xrb_mprop', 'boat'],
  m_stakes: ['xrb_mprop', 'stakes'], m_sign: ['xrb_mprop', s => 'sign' + (s.v || 0)], m_table: ['xrb_mprop', 'table', 0, [26, '255,190,110', 0.7, -24, 6]],
  m_posts: ['xrb_mprop', 'posts'], m_valve: ['xrb_mprop', 'valve'], m_gauge: ['xrb_mprop', 'gauge'],
  m_moss: ['xrb_mprop', s => 'moss' + ((s.x + s.y) % 2), 0, null, 'hang'],
  a_books: ['xrb_aprop', s => 'books' + ((s.x + s.y) % 2)], a_candles: ['xrb_aprop', 'candles', 7, [40, '255,190,110', 0.8, -14, 3]],
  a_desk: ['xrb_aprop', 'desk', 0, [34, '255,190,110', 0.7, -26, 15]], a_card: ['xrb_aprop', 'card'],
  f_valve: ['xrb_fprop', 'valve'], f_crystal: ['xrb_fprop', s => 'crystal' + ((s.x + s.y) % 2), 0, [34, '140,200,255', 0.55, -14]],
  f_drift: ['xrb_fprop', 'drift'], f_gauge: ['xrb_fprop', 'gauge'], f_sign: ['xrb_fprop', s => 'sign' + (s.v || 0)],
};
SPAWNS.xrb = (s, c) => {
  xrbEnsure();
  const cx = c.cx + (s.ox || 0), fy = c.fy + (s.oy || 0);
  const P0 = XRB_PROP[s.d];
  if (P0) {
    const sh = sheet(P0[0]), tag = typeof P0[1] === 'function' ? P0[1](s) : P0[1], fps = P0[2] || 0, L = P0[3], hang = P0[4] === 'hang';
    const p = { type: 'xrb_' + s.d, x: cx, y: hang ? s.y * TILE : fy, face: s.flip ? -1 : 1, anim: { update() {} }, seed: hash2(s.x, s.y) * 10, fg: !!s.fg };
    p.draw = () => {
      if (p.fg && !SYS.vista) return;                     // foreground pieces are drawn after the player (render hook)
      xrbDrawProp(p, sh, tag, fps, hang);
    };
    p.drawFg = () => xrbDrawProp(p, sh, tag, fps, hang, true);
    if (L) p.update = () => addLight(p.x + (L[4] || 0) * p.face, p.y + L[3], L[0] + (fps ? Math.sin(time * 6 + p.seed) * 3 : 0), L[1], L[2], LX_FLICKER);
    props.push(p); if (p.fg) XRB.fg.push(p);
    if (s.d === 'm_reeds' && s.tall) p.tall = true;
    return;
  }
  // live areas and special pieces
  const A = { d: s.d, x0: s.x * TILE, y0: s.y * TILE, x1: (s.x + (s.w || 1)) * TILE, y1: (s.y + (s.h || 1)) * TILE, k: s.k ?? 1, s, seed: rand(0, 100) };
  switch (s.d) {
    case 'm_fog': case 'f_mist': case 'm_fireflies': case 'a_pages': case 'f_snow': case 'a_rain':
      A.parts = []; XRB.areas.push(A);
      props.push({ type: 'xrb_mist', x: A.x0, y: A.y1, anim: { update() {} }, draw() { if (SYS.vista) xrbDrawArea(A); } });
      break;
    case 'm_bigtree': props.push({ type: 'xrb_pods', x: cx, y: fy, anim: { update() {} }, draw() {}, update() {   // the Weeping Tree's spore pods glow and drift
      for (let i = 0; i < 6; i++) addLight(cx - 80 + i * 32, fy - 150 - (i % 3) * 30, 46, '150,230,100', 0.55, { flicker: true, shadow: false });
      if (Math.random() < 0.12) particles.push({ x: cx + rand(-90, 90), y: fy - rand(120, 230), vx: rand(-4, 4), vy: rand(4, 12), life: 3, kind: 'spore' });
    } }); break;
    case 'm_hut': props.push({ type: 'xrb_hutlight', x: cx, y: fy, anim: { update() {} }, draw() {}, update() { addLight(cx + 17, fy - 34, 80, '255,180,100', 0.9, LX_FLICKER); } }); break;
    case 'a_codex': props.push({ type: 'xrb_codex', x: cx, y: fy, anim: { update() {} }, glow: true, draw() {
      const sh = sheet('xrb_acodex'), fr = xrbLoop(sh, 'idle', 4); if (fr < 0) return;   // the glowing script, alive, over the painted book
      drawSprite(sh, fr, cx + 8, fy + 60, 1, { bottom: true, alpha: 0.14 + 0.06 * Math.sin(time * 1.3), blend: 'lighter' });
    }, update() { addLight(cx + 8, fy - 40, 100, '170,120,255', 0.4, { shadow: false }); if (Math.random() < 0.08) particles.push({ x: cx + rand(-60, 70), y: fy + rand(40, 64), vx: 0, vy: rand(10, 25), g: 30, life: 1.4, kind: 'ink' }); } }); break;
    case 'a_window': props.push({ type: 'xrb_winlight', x: cx, y: fy, anim: { update() {} }, draw() {}, update() { addLight(cx, fy - 64, 110, '150,160,220', 0.55, { shadow: false }); if (Math.random() < 0.02) { XRB.flash = 1; setTimeout(() => tone(55, 1.2, 0.05, 'sine', 0.9), 600); } } }); break;
    case 'a_note': {
      const p = { type: 'xrb_note', x: cx, y: fy - 4, anim: { update() {} }, n: s.n, sym: s.sym };
      p.draw = () => xrbDrawNote(p); p.update = () => { if (Math.abs(P.x - p.x) < 60 && Math.abs(P.y - p.y) < 50) addLight(p.x, p.y - 14, 26, '255,220,160', 0.5); };
      p.prompt = () => 'Read'; p.interact = () => toast(`A scribe’s leaf, numbered ${xrbRoman(s.n)}. One rune is drawn on it, very carefully.`, 3.2);
      props.push(p); break;
    }
    case 'a_chain': props.push({ type: 'xrb_chain', x: cx, y: s.y * TILE, anim: { update() {} }, draw() { xrbChain(cx, s.y * TILE, (s.y + (s.len || 6)) * TILE); } }); break;
    case 'a_rail': props.push({ type: 'xrb_rail', x: A.x0, y: A.y0, anim: { update() {} }, draw() { xrbRail(A.x0, A.x1, A.y0 + 10); } }); break;
    case 'f_rib': props.push({ type: 'xrb_rib', x: cx, y: fy, anim: { update() {} }, draw() { xrbRib(cx, s.y * TILE - 16, s.y * TILE + 88); } }); break;
    case 'f_frostpipe': props.push({ type: 'xrb_frostpipe', x: A.x0, y: A.y0, anim: { update() {} }, draw() { xrbFrostPipe(A); } }); break;
    case 'f_railing': props.push({ type: 'xrb_railing', x: A.x0, y: fy, anim: { update() {} }, draw() { xrbRailing(A.x0, A.x1, fy); } }); break;
    case 'f_reservoir': props.push({ type: 'xrb_reservoir', x: cx, y: fy, anim: { update() {} }, draw() {} }); break;
    case 'f_aurora': XRB.aurora = A; break;
    case 'f_lamp': break;
  }
};
function xrbDrawProp(p, sh, tag, fps, hang, fg) {
  const fr = fps ? xrbLoop(sh, tag, fps, p.seed) : xrbFrame(sh, tag);
  if (fr < 0) return;
  let alpha = 1;
  if (fg) {   // foreground reeds part around the player so you can see yourself (and what they were hiding)
    const d = Math.hypot(P.x - p.x, (P.y - 14) - (p.y - 20));
    alpha = clamp((d - 18) / 44, p.tall ? 0.15 : 0.25, 0.97);
  }
  drawSprite(sh, fr, p.x, p.y, p.face, hang ? { pivot: [24, 0], alpha } : { bottom: true, alpha });
  if (p.tall) drawSprite(sh, xrbLoop(sh, tag, fps, p.seed + 1), p.x + 10, p.y + 2, -p.face, { bottom: true, alpha: alpha * 0.9 });
}
function xrbDrawNote(p) {
  const sh = sheet('xrb_aprop'), fr = xrbFrame(sh, 'note');
  if (fr >= 0) drawSprite(sh, fr, p.x, p.y + 4, 1, { bottom: true });
  const ks = sheet('kit_parts');   // the rune: the same shape as on the Cipher Wall, inked small
  if (ks.ok && ks.has('glyph')) { const f = ks.frames[ks.first('glyph') + (p.sym % 8)]; g.save(); g.globalAlpha = 0.85; g.drawImage(ks.img, f.x, f.y, f.w, f.h, Math.round(p.x - 8), Math.round(p.y - 22), 16, 16); g.restore(); }
  const r = xrbRoman(p.n); xrbGlyph(r, p.x - r.length * 2 + 1, p.y - 7, '#3a2410');
}
function xrbChain(x, y0, y1) {
  for (let y = y0; y < y1; y += 4) { g.fillStyle = '#100e16'; g.fillRect(Math.round(x) - 1, y, 3, 3); g.fillStyle = (y / 4) % 2 ? '#524a5a' : '#383240'; g.fillRect(Math.round(x), y, 1, 2); }
}
function xrbRail(x0, x1, y) {
  g.fillStyle = '#0c0909'; g.fillRect(x0, y - 1, x1 - x0, 4); g.fillStyle = '#6e5624'; g.fillRect(x0, y, x1 - x0, 1); g.fillStyle = '#3a2b21'; g.fillRect(x0, y + 1, x1 - x0, 1);
  for (let x = x0 + 8; x < x1; x += 48) { g.fillStyle = '#0c0909'; g.fillRect(x - 1, y - 12, 3, 12); g.fillStyle = '#4c3829'; g.fillRect(x, y - 12, 1, 12); }
}
function xrbRib(x, y0, y1) {   // a riveted ring inside the conduit
  g.fillStyle = 'rgba(8,12,18,0.55)'; g.fillRect(Math.round(x) - 5, y0, 10, y1 - y0);
  g.fillStyle = 'rgba(70,86,108,0.5)'; g.fillRect(Math.round(x) - 4, y0, 2, y1 - y0);
  g.fillStyle = 'rgba(200,230,245,0.5)'; for (let y = y0 + 6; y < y1; y += 14) g.fillRect(Math.round(x) - 1, y, 2, 2);
}
function xrbFrostPipe(A) {   // inside the conduit / the lock shaft: frost feathers creeping along the walls
  const v = A.s.v === 1;
  for (let i = 0; i < (v ? 10 : 24); i++) {
    const h = hash2(i * 13, A.x0), x = A.x0 + h * (A.x1 - A.x0), top = hash2(i, 7) < 0.5, y = top ? A.y0 : A.y1 - 2;
    g.fillStyle = 'rgba(190,225,245,0.35)';
    for (let k = 0; k < 6; k++) g.fillRect(Math.round(x + k * (h < 0.5 ? 1 : -1)), Math.round(y + (top ? k : -k)), 1, 1);
  }
}
function xrbRailing(x0, x1, y) {
  g.fillStyle = '#0a0d14'; g.fillRect(x0, y - 14, x1 - x0, 3);
  g.fillStyle = '#3c465a'; g.fillRect(x0, y - 14, x1 - x0, 1);
  for (let x = x0 + 4; x < x1; x += 12) { g.fillStyle = '#0a0d14'; g.fillRect(x, y - 13, 3, 13); g.fillStyle = '#323b4e'; g.fillRect(x + 1, y - 13, 1, 13); g.fillStyle = '#dfeaf2'; g.fillRect(x, y - 15, 3, 1); }
}
// live areas: fog banks, fireflies, drifting pages, snowfall, mist, rain streaks on the window
function xrbDrawArea(A) {
  const t = time + A.seed, w = A.x1 - A.x0, h = A.y1 - A.y0;
  if (A.d === 'm_fog' || A.d === 'f_mist') {
    const col = A.d === 'm_fog' ? '150,175,140' : '200,225,240';
    for (let i = 0; i < Math.max(4, w / 40); i++) {
      const bx = A.x0 + (((i * 97 + t * (6 + (i % 3) * 3)) % (w + 120)) - 60), by = A.y0 + h * (0.35 + 0.5 * hash2(i, 3)) + Math.sin(t * 0.4 + i) * 4;
      const r = 40 + 30 * hash2(i, 9), gr = g.createRadialGradient(bx, by, 0, bx, by, r);
      gr.addColorStop(0, `rgba(${col},${0.09 * A.k})`); gr.addColorStop(1, `rgba(${col},0)`);
      g.fillStyle = gr; g.fillRect(bx - r, by - r, r * 2, r * 2);
    }
  } else if (A.d === 'm_fireflies') {
    for (let i = 0; i < Math.max(6, w / 24); i++) {
      const x = A.x0 + (hash2(i, 1) * w + Math.sin(t * 0.3 + i * 1.7) * 18), y = A.y0 + (hash2(i, 2) * h + Math.sin(t * 0.5 + i) * 10);
      const on = 0.5 + 0.5 * Math.sin(t * 2 + i * 2.3); if (on < 0.2) continue;
      drawGlow(() => { g.fillStyle = `rgba(210,255,120,${on})`; g.fillRect(Math.round(x), Math.round(y), 1, 1); });
      if (i % 3 === 0) addLight(x, y, 12, '190,255,110', 0.3 * on, { shadow: false });
    }
  } else if (A.d === 'a_pages') {
    for (let i = 0; i < Math.max(4, (w * h) / 9000) * A.k; i++) {
      const fall = (t * (10 + hash2(i, 4) * 12) + hash2(i, 5) * h) % h, x = A.x0 + hash2(i, 6) * w + Math.sin(t * 0.8 + i) * 14, y = A.y0 + fall;
      const tw = Math.sin(t * 3 + i * 1.3);
      g.fillStyle = tw > 0 ? '#c4b48c' : '#8a7c60'; g.fillRect(Math.round(x), Math.round(y), Math.max(1, Math.round(4 * Math.abs(tw))), 3);
      g.fillStyle = '#3c2c5c'; if (Math.abs(tw) > 0.6) g.fillRect(Math.round(x), Math.round(y) + 1, 2, 1);
    }
  } else if (A.d === 'f_snow') {
    g.fillStyle = 'rgba(230,242,250,0.75)';
    for (let i = 0; i < Math.max(10, (w * h) / 3000) * A.k; i++) {
      const y = A.y0 + ((t * (14 + hash2(i, 2) * 10) + hash2(i, 3) * h) % h), x = A.x0 + ((hash2(i, 4) * w + Math.sin(t * 0.7 + i) * 10 + t * 6) % w);
      g.fillRect(Math.round(x), Math.round(y), hash2(i, 8) < 0.2 ? 2 : 1, 1);
    }
  } else if (A.d === 'a_rain') {
    g.fillStyle = 'rgba(170,185,230,0.35)';
    for (let i = 0; i < w / 5; i++) { const y = A.y0 + ((t * 160 + hash2(i, 1) * h) % h), x = A.x0 + hash2(i, 2) * w + (y - A.y0) * 0.15; g.fillRect(Math.round(x), Math.round(y), 1, 5); }
    g.fillStyle = 'rgba(200,210,240,0.25)';   // drops running down the glass
    for (let i = 0; i < w / 14; i++) { const y = A.y0 + ((t * 18 * (0.6 + hash2(i, 3)) + hash2(i, 4) * h) % h); g.fillRect(Math.round(A.x0 + hash2(i, 5) * w), Math.round(y), 1, 3); }
    if (XRB.flash > 0) { g.fillStyle = `rgba(210,220,255,${0.25 * XRB.flash})`; g.fillRect(A.x0, A.y0, w, h); }
  }
}
function xrbRopes(s) {   // rope rails of the Rotwood bridges, sagging post to post
  for (const [a, b, row] of s.spans) {
    const x0 = a * TILE + 8, x1 = b * TILE + 8, y = row * TILE - 20;
    for (const dy of [0, 7]) {
      g.fillStyle = dy ? '#3a3222' : '#5a4e34';
      for (let x = x0; x <= x1; x += 1) { const k = (x - x0) / (x1 - x0), sag = Math.sin(k * Math.PI) * (8 + dy * 0.3); g.fillRect(x, Math.round(y + dy + sag), 1, 1); }
    }
  }
}
SPAWNS.xrb_ropes = (s) => props.push({ type: 'xrb_ropes', x: 0, y: 0, anim: { update() {} }, draw() { xrbRopes(s); } });

// the aurora over the Frostbitten Overlook: drawn right after the parallax, so the vista view has it too
{
  const _rbPar = drawParallax;
  drawParallax = function () {
    _rbPar.apply(this, arguments);
    if (!room || room.id !== 'HF14') return;
    const t = time * 0.25;
    drawGlow(() => {
    g.save(); g.globalCompositeOperation = 'lighter';
    for (let band = 0; band < 3; band++) {
      const base = 30 + band * 22, col = band === 1 ? [90, 230, 170] : band === 2 ? [120, 140, 255] : [80, 210, 200];
      for (let x = 0; x < W; x += 2) {
        const wx = x + cam.x * 0.05, y = base + Math.sin(wx * 0.012 + t + band) * 14 + Math.sin(wx * 0.031 - t * 1.6) * 6;
        const k = 0.5 + 0.5 * Math.sin(wx * 0.02 + t * 2 + band * 2), L = 30 + 26 * k;
        const gr = g.createLinearGradient(0, y, 0, y + L); gr.addColorStop(0, `rgba(${col},0)`); gr.addColorStop(0.3, `rgba(${col},${0.3 * k})`); gr.addColorStop(1, `rgba(${col},0)`);
        g.fillStyle = gr; g.fillRect(x, y, 2, L);
      }
    }
    g.restore();
    });
    g.fillStyle = 'rgba(230,240,255,0.8)';   // stars
    for (let i = 0; i < 60; i++) { const x = (hash2(i, 1) * W * 1.4 - cam.x * 0.03) % W, y = hash2(i, 2) * H * 0.55; if (Math.sin(time * 1.5 + i * 7) > -0.6) g.fillRect(Math.round((x + W) % W), Math.round(y), 1, 1); }
    // the still reservoir far below: a frozen lake catching the sky
    const ry = H * 0.8 - cam.y * 0.1;
    const lg2 = g.createLinearGradient(0, ry, 0, H); lg2.addColorStop(0, '#2a4a60'); lg2.addColorStop(0.2, '#162838'); lg2.addColorStop(1, '#070a12');
    g.fillStyle = lg2; g.fillRect(0, ry, W, H - ry);
    g.save(); g.globalCompositeOperation = 'lighter';
    for (let x = 0; x < W; x += 3) { const k = 0.5 + 0.5 * Math.sin(x * 0.03 + time * 0.3); g.fillStyle = `rgba(90,220,180,${0.08 * k})`; g.fillRect(x, ry + 2 + (x % 7), 3, 1); }
    g.restore();
  };
}

// ================================================================== water ambushes: foes rise out of the rot (or the ink) when you pass
SPAWNS.xrb_ambush = (s, c) => {
  xrbEnsure();
  const key = c.key; if (killed.has(key)) return;
  XRB.ambush.push({ s, key, x: c.cx, fy: c.fy, done: false });
};
function xrbUpdateAmbush() {
  for (const A of XRB.ambush) {
    if (A.done || !P || P.state === 'dead') continue;
    if (Math.abs(P.x - A.x) > (A.s.r || 60) || Math.abs(P.y - A.fy) > 70) continue;
    if (SYS.vista) continue;
    A.done = true;
    const e = makeEnemy(A.s.type, A.x, A.fy, A.key); enemies.push(e);
    if (A.s.hide) continue;   // it was there all along, in the reeds
    if (A.s.rise === 'ink') { if (typeof ar2Burst === 'function') ar2Burst(A.x, A.fy); for (let i = 0; i < 10; i++) particles.push({ x: A.x + rand(-8, 8), y: A.fy - rand(0, 20), vx: rand(-50, 50), vy: -rand(30, 120), g: 300, life: 0.7, kind: 'ink' }); }
    else { spawnFx(fxOr('db_splash', 'dust'), A.x, A.fy + 10, 1, null, { bottom: true }); for (let i = 0; i < 14; i++) particles.push({ x: A.x + rand(-10, 10), y: A.fy + 8, vx: rand(-60, 60), vy: -rand(40, 150), g: 380, life: rand(0.5, 0.9), kind: 'spore' }); }
    noise(0.35, 700, 0.6, 0.3, 'lowpass', 0.5);
  }
}

// ================================================================== ink abyss ('9'): black ink over a stone bed; touching it throws you back
const RB_T_INK = 81;   // tile id: 81 after the agent file number, clear of the 8..69 region ranges
registerTile('9', RB_T_INK, { draw(ctx, sh, px, py, x, y, R) {
  const up = y > 0 && R.grid[(y - 1) * R.w + x] === RB_T_INK;
  ctx.fillStyle = '#07050d'; ctx.fillRect(px, py + (up ? 0 : 4), 16, up ? 16 : 12);
  ctx.fillStyle = '#140f22'; if (!up) ctx.fillRect(px, py + 4, 16, 2);
} });
function xrbInkAt(b) {   // feet sunk into an ink cell (a little below its surface)
  for (const xx of [b.x - 3, b.x + 3]) {
    const tx = Math.floor(xx / TILE), ty = Math.floor((b.y - 2) / TILE);
    if (tileAt(tx, ty) === RB_T_INK) { const up = tileAt(tx, ty - 1) === RB_T_INK; if (up || b.y - 2 > ty * TILE + 6) return true; }
  }
  return false;
}
function xrbUpdateInk() {
  if (!room.def.map.some(r => r.includes('9'))) return;
  if (P.state === 'dead' || fadePhase === 1) return;
  if (!xrbInkAt(P)) return;
  for (let i = 0; i < 16; i++) particles.push({ x: P.x + rand(-8, 8), y: P.y - rand(0, 10), vx: rand(-60, 60), vy: -rand(40, 140), g: 360, life: rand(0.5, 0.9), kind: 'ink' });
  noise(0.3, 500, 0.7, 0.3, 'lowpass', 0.5);
  if (P.inv > 0 && !SYS.trial) {   // invulnerable: no damage, but the ink still won't have you
    P.vx = P.vy = 0; fadeTo(() => { P.x = P.safe.x; P.y = P.safe.y; setP('idle', 'idle', true); updateCamera(0, true); });
    return;
  }
  spikeHurt();
}
function xrbDrawInk() {
  if (!room.def.map.some(r => r.includes('9'))) return;
  const x0 = Math.max(0, Math.floor(cam.x / TILE) - 1), x1 = Math.min(room.w, x0 + Math.ceil(W / TILE) + 3);
  const y0 = Math.max(0, Math.floor(cam.y / TILE) - 1), y1 = Math.min(room.h, y0 + Math.ceil(H / TILE) + 3);
  for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) {
    if (room.grid[y * room.w + x] !== RB_T_INK || (y > 0 && room.grid[(y - 1) * room.w + x] === RB_T_INK)) continue;
    const px = x * TILE, py = y * TILE;
    for (let i = 0; i < TILE; i += 2) { const w = Math.sin(time * 1.3 + (px + i) * 0.21) * 1.2; g.fillStyle = 'rgba(120,90,200,0.55)'; g.fillRect(px + i, Math.round(py + 4 + w), 2, 1); }
    if (Math.random() < 0.004) particles.push({ x: px + rand(2, 14), y: py + 4, vx: 0, vy: -rand(6, 14), life: 0.9, kind: 'ink' });
    if ((x + y) % 3 === 0) addLight(px + 8, py + 6, 22, '120,80,220', 0.28, { shadow: false });
  }
}

// ================================================================== the Index Room: numbered books; pull exactly the ones on the card
SPAWNS.xrb_books = (s, c) => {
  xrbEnsure();
  const key = `x3:${c.id}:${s.id}`, solved = !!SAVE.flags[key];
  const B = { s, key, solved, books: [], wrongs: 0, resetT: 0 };
  XRB.books = B;
  const ys = s.ys || [s.y + 2, s.y + 5];
  for (let r = 0; r < s.rows; r++) for (let k = 0; k < s.cols; k++) {
    const n = r * s.cols + k + 1, bx = (s.x + k) * TILE + 8, by = (ys[r] + 1) * TILE - 6;   // books stand on a plank at the row's foot
    const b = { n, r, x: bx, y: by, out: solved && s.answer.includes(n), slide: 0, col: Math.floor(hash2(n, 3) * 6) };
    const pick = () => { let best = b, bd = 1e9; for (const q of B.books) if (q.r === b.r && Math.abs(q.x - P.x) < bd) { bd = Math.abs(q.x - P.x); best = q; } return best; };
    b.p = { type: 'xrb_book', x: bx, y: by, anim: { update() {} }, draw() {},
      hurtbox: () => B.solved || B.resetT > 0 ? null : rect(bx - 6, by - 20, bx + 6, by),
      onHit: info => { if (XRB.bookHitT === time) return; XRB.bookHitT = time; const q = pick(); xrbPullBook(B, Math.abs(q.x - P.x) < Math.abs(b.x - P.x) + 1 ? q : b); },
      prompt: () => B.solved ? null : pick().out ? 'Push back' : 'Pull', interact: () => xrbPullBook(B, pick()) };
    B.books.push(b); props.push(b.p);
  }
  B.ys = ys;
  props.push({ type: 'xrb_bookwall', x: s.x * TILE, y: s.y * TILE, anim: { update() {} }, draw: () => xrbDrawBooks(B) });
  if (solved) sysLater(0.05, () => kitForce(s.gate, true));
};
function xrbPullBook(B, b) {
  if (B.solved || B.resetT > 0) return;
  b.out = !b.out; sfx.hit(); noise(0.15, 1400, 0.8, 0.15, 'bandpass', 0.6);
  const ans = B.s.answer, outs = B.books.filter(q => q.out).map(q => q.n);
  if (b.out && !ans.includes(b.n)) {   // the wrong book: the shelf thinks about it, then slams everything home
    B.resetT = 0.7; B.wrongs++; XRB.wrongs = (XRB.wrongs || 0) + 1;
    setTimeout(() => { kitSfx.wrong(); shake = Math.max(shake, 2); }, 350);
    return;
  }
  if (outs.length === ans.length && ans.every(n => outs.includes(n))) {
    B.solved = true; SAVE.flags[B.key] = 1; saveGame();
    kitForce(B.s.gate, true); kitSfx.chime(); flashScreen = Math.max(flashScreen, 0.15); shake = 3;
    setTimeout(() => toast('Somewhere in the case, a catch gives. The shelf swings open.', 3), 400);
  }
}
function xrbDrawBooks(B) {
  const s = B.s, BOOKC = [['#2e1014', '#74302c'], ['#0e2024', '#2a5250'], ['#2e2412', '#74582a'], ['#22142e', '#553a66'], ['#241a14', '#5a4430'], ['#1a1a22', '#44444f']];
  for (let r = 0; r < s.rows; r++) {   // the case: dark back, a plank under each row
    const y = (B.ys[r] + 1) * TILE - 6;
    g.fillStyle = '#0c0909'; g.fillRect(s.x * TILE - 3, y - 28, s.cols * TILE + 6, 28);
    g.fillStyle = '#1f1714'; g.fillRect(s.x * TILE - 2, y - 27, s.cols * TILE + 4, 26);
    g.fillStyle = '#3a2b21'; g.fillRect(s.x * TILE - 4, y, s.cols * TILE + 8, 4); g.fillStyle = '#604733'; g.fillRect(s.x * TILE - 4, y, s.cols * TILE + 8, 1);
  }
  for (const b of B.books) {
    b.slide = approach(b.slide, b.out ? 5 : 0, 0.8);
    const c = BOOKC[b.col], x = Math.round(b.x - 6), y = Math.round(b.y - 22 + b.slide);
    g.fillStyle = '#08070a'; g.fillRect(x - 1, y - 1, 14, 24);
    g.fillStyle = c[0]; g.fillRect(x, y, 12, 22); g.fillStyle = c[1]; g.fillRect(x, y, 2, 22); g.fillRect(x, y + 3, 12, 1); g.fillRect(x, y + 18, 12, 1);
    g.fillStyle = '#e2d6b0'; g.fillRect(x + 2, y + 6, 8, 8);
    xrbGlyph(b.n, x + 7 - String(b.n).length * 2, y + 8, '#2a1c10');
    if (b.out) { g.fillStyle = 'rgba(255,220,150,0.25)'; g.fillRect(x, y, 12, 22); }
  }
}

// ================================================================== freezing locks: a brazier's heat thaws a block of ice into water
SPAWNS.xrb_freeze = (s, c) => {
  xrbEnsure();
  const L = { s, cells: [], frozen: null, k: 0 };
  for (let y = s.y; y < s.y + s.h; y++) for (let x = s.x; x < s.x + s.w; x++) L.cells.push([x, y]);
  XRB.freeze.push(L);
};
function xrbFreezeTarget(L) { return !kitOn(L.s.src); }   // unlit brazier = frozen
function xrbSetLock(L, frozen, animate) {
  L.frozen = frozen;
  const T_ICE_ = typeof T_ICE !== 'undefined' ? T_ICE : 10, T_FW = typeof T_FWATER !== 'undefined' ? T_FWATER : 11;
  for (const [x, y] of L.cells) room.grid[y * room.w + x] = frozen ? T_ICE_ : T_FW;
  if (frozen) {   // the ice closes over anyone inside it: lift them onto its top
    const top = L.s.y * TILE;
    for (const b of [P, ...enemies.filter(e => e.alive && !e.cfg.flying)]) {
      if (b.x > L.s.x * TILE - 4 && b.x < (L.s.x + L.s.w) * TILE + 4 && b.y > top && b.y - (b.h || 26) < (L.s.y + L.s.h) * TILE) { b.y = top; b.vy = Math.min(0, b.vy || 0); if (b === P) { P.ground = true; } }
    }
  }
  if (typeof HF !== 'undefined') {   // the Hoarfrost file draws freezing water from this list
    HF.water = [];
    for (let y = 0; y < room.h; y++) for (let x = 0; x < room.w; x++) if (room.grid[y * room.w + x] === T_FW) HF.water.push([x, y, y === 0 || room.grid[(y - 1) * room.w + x] !== T_FW]);
  }
  renderRoomLayers(room);
  if (animate) {
    const cx = (L.s.x + L.s.w / 2) * TILE, cy = (L.s.y + 0.5) * TILE;
    for (let i = 0; i < 26; i++) particles.push({ x: cx + rand(-L.s.w * 8, L.s.w * 8), y: cy + rand(-4, 20), vx: rand(-40, 40), vy: -rand(10, 80), g: 200, life: rand(0.5, 1), kind: 'frost' });
    if (frozen) { typeof hfSfx !== 'undefined' ? hfSfx.crack() : noise(0.3, 2600, 1.5, 0.25, 'bandpass'); tone(1320, 0.3, 0.05, 'triangle', 0.7); }
    else { noise(0.6, 900, 0.6, 0.25, 'lowpass', 0.5); tone(220, 0.5, 0.05, 'sine', 1.4); }
    shake = Math.max(shake, 2);
  }
}
function xrbUpdateFreeze(dt) {
  for (const L of XRB.freeze) {
    const want = xrbFreezeTarget(L);
    if (L.frozen === null) { xrbSetLock(L, want, false); continue; }
    if (want !== L.frozen) { L.k += dt; if (L.k > 0.35) { L.k = 0; xrbSetLock(L, want, true); } } else L.k = 0;
  }
  if (XRB.freeze.length && P) {   // "stuck in the water" counts as a wrong try (for the hint)
    const wet = typeof hfInWater === 'function' && hfInWater(P);
    XRB.wet = wet ? XRB.wet + dt : 0;
    if (XRB.wet > 1.6) { XRB.wet = -99; XRB.wrongs = (XRB.wrongs || 0) + 1; }
    if (!wet && XRB.wet < 0) XRB.wet = 0;
  }
}

// ================================================================== icicles that freeze into footholds where they land in water
SPAWNS.xrb_icicle = (s, c) => {
  xrbEnsure();
  if (typeof makeIcicle !== 'function') return;
  const p = makeIcicle(c.cx, s.y * TILE, true); p.regrow = true;
  const smash = p.smash;
  p.smash = y => {
    smash(y);
    if (!s.foot) return;
    // walk up from the landing through the freezing water: the foothold's top is the water's surface
    const tx = Math.floor(p.x / TILE); let ty = Math.floor((y - 1) / TILE), top = null;
    while (ty >= 0 && tileAt(tx, ty) === (typeof T_FWATER !== 'undefined' ? T_FWATER : 11)) { top = ty * TILE; ty--; }
    if (top === null) return;
    const F = { x: p.x, y0: top, y1: y, t: 7, life: 7 };
    F.d = { x0: p.x - 7, x1: p.x + 7, y0: top, y1: y, on: () => F.t > 0 };
    room.dyn.push(F.d); XRB.feet.push(F);
    tone(1760, 0.2, 0.05, 'triangle', 0.8);
  };
  props.push(p);
};
function xrbUpdateFeet(dt) {
  for (const F of XRB.feet) {
    if (F.t <= 0) continue;
    F.t -= dt;
    if (F.t <= 0) { if (typeof hfBurst === 'function') hfBurst(F.x, F.y0 + 4, 'frost', 10); typeof hfSfx !== 'undefined' && hfSfx.shatter(); }
  }
  XRB.feet = XRB.feet.filter(F => F.t > 0);
}
function xrbDrawFeet() {
  for (const F of XRB.feet) {
    const k = F.t < 1.2 ? (Math.floor(time * 12) % 2 ? 0.45 : 0.9) : 1, x = Math.round(F.x), y0 = Math.round(F.y0), h = Math.round(F.y1 - F.y0);
    g.globalAlpha = k;
    g.fillStyle = '#0e2236'; g.fillRect(x - 8, y0 - 1, 16, h + 1);
    g.fillStyle = '#3886a6'; g.fillRect(x - 7, y0, 14, h);
    g.fillStyle = '#82c6dc'; g.fillRect(x - 7, y0, 5, h); g.fillStyle = '#e6fbff'; g.fillRect(x - 7, y0, 14, 1); g.fillRect(x - 5, y0 + 2, 1, h - 4);
    g.globalAlpha = 1;
    addLight(x, y0 + 4, 22, '150,210,255', 0.35);
  }
}

// ================================================================== puzzle hints: after 3 wrong tries, a gentle word (once per visit)
SPAWNS.xrb_hint = (s) => { xrbEnsure(); XRB.hints.push({ s, shown: false, lastBad: 0 }); };
function xrbUpdateHints() {
  for (const Hn of XRB.hints) {
    if (Hn.shown) continue;
    if (Hn.s.seq) { const q = KIT.byId && KIT.byId[Hn.s.seq]; if (q) { if (q.active) { Hn.shown = true; continue; } if (q.bad > 0.7 && Hn.lastBad <= 0.7) XRB.wrongs = (XRB.wrongs || 0) + 1; Hn.lastBad = q.bad; } }
    if (Hn.s.books && XRB.books && XRB.books.solved) { Hn.shown = true; continue; }
    if ((XRB.wrongs || 0) >= 3) { Hn.shown = true; setTimeout(() => toast(Hn.s.text, 5.5), 700); }
  }
}

// ================================================================== room entry, update, render
HOOKS.enter.push(def => {
  if (!xrbMine(def) && !['M2', 'M4', 'A2', 'A5', 'HF2', 'HF6'].includes(def.id)) return;
  xrbEnsure();
  if (def.id === 'A11') for (const o of (KIT.objs || [])) if (o.kind === 'phase') o.draw = () => xrbDrawPage(o);   // loose pages, not planks
  if (def.trial) for (const p of props) if (p.type === 'hf_icicle') p.regrow = true;   // trial icicles grow back (and reset with the run)
  if (def.id === 'M12' && !SAVE.hints.rb_valve) { SAVE.hints.rb_valve = 1; setTimeout(() => toast('Two valve wheels. The water answers either one.', 3.5), 1200); }
  if (def.id === 'HF12' && !SAVE.hints.rb_icicle) { SAVE.hints.rb_icicle = 1; setTimeout(() => toast('Icicles that fall into the channel freeze where they land — for a while.', 4), 1200); }
});
function xrbDrawPage(o) {
  if (o.alpha <= 0.02 && o.solidNow) return;
  const blink = o.warnK > 0 && Math.floor(KIT.t * (8 + 10 * o.warnK)) % 2 === 1, X = Math.round(o.d.x0), Y = Math.round(o.d.y0), w = o.w;
  if (o.alpha > 0.02) {
    g.globalAlpha = o.alpha * (blink ? 0.4 : 1);
    for (let i = 0; i < w; i += 6) {   // overlapping sheets of parchment, fluttering at the edges
      const lift = Math.sin(time * 9 + i + X) * 1.2;
      g.fillStyle = '#6a5c44'; g.fillRect(X + i - 1, Y + 1 + lift, 9, 5);
      g.fillStyle = (i / 6) % 2 ? '#e2d6b0' : '#c4b48c'; g.fillRect(X + i, Y + lift, 8, 4);
      g.fillStyle = '#3c2c5c'; g.fillRect(X + i + 2, Y + 1 + lift, 4, 1); g.fillRect(X + i + 1, Y + 3 + lift, 5, 1);
    }
    g.globalAlpha = 1;
  } else {
    g.fillStyle = 'rgba(226,214,176,0.2)'; for (let x = X; x < X + w; x += 3) g.fillRect(x, Y + ((x >> 2) % 2), 1, 1);
  }
}
HOOKS.update.push(dt => {
  if (!room || !P || !xrbMine(room.def)) return;
  xrbEnsure();
  xrbUpdateAmbush(); xrbUpdateInk(); xrbUpdateFreeze(dt); xrbUpdateFeet(dt); xrbUpdateHints();
  if (room.def.trial && SYS.trial && P.ground && D) P.st = Math.max(P.st, D.maxSt);   // the sigil's warmth: a trial never runs you out of breath on the ground
  if (room.def.trial) {   // a trial reset (or a fresh start) puts every icicle back on the ceiling
    const tr = SYS.trial, key = tr ? tr.attempts : -1;
    if (key !== XRB.trialKey) { XRB.trialKey = key; if (tr) for (const p of props) if (p.type === 'hf_icicle' && p.st !== 'idle') { p.st = 'idle'; p.y = p.top; p.vy = 0; p.hitSet = new Set(); p.grow = 0; p.anim.set('idle', false); } }
  }
  const B = XRB.books;   // a wrong book: after a beat the shelf slams every pulled book home
  if (B && B.resetT > 0) { B.resetT -= dt; if (B.resetT <= 0.35 && B.books.some(q => q.out)) for (const q of B.books) q.out = false; if (B.resetT < 0) B.resetT = 0; }
  if (XRB.flash > 0) XRB.flash = Math.max(0, XRB.flash - dt * 2);
  // standing on thin boards at the room's floor edge: say how to drop through, once
  if (P.ground && !SAVE.hints.rb_drop) {
    const tx = Math.floor(P.x / TILE), ty = Math.floor((P.y + 1) / TILE);
    if (ty === room.h - 1 && tileAt(tx, ty) === T_PLAT) { SAVE.hints.rb_drop = 1; toast('Hold ↓ and press Space to drop through the boards', 3.5); }
  }
  // the Valve House's water is bog water: spores rise off it
  if (room.id === 'M12' && Math.random() < 0.2) { const L = KIT.byId && KIT.byId.lvl; if (L && L.sy !== undefined) particles.push({ x: rand(40, room.pw - 20), y: L.sy + 2, vx: 0, vy: -rand(6, 14), life: 1.4, kind: 'spore' }); }
});
function xrbDropMarks() {   // a small pulsing arrow over every run of thin boards in the room's bottom row: the way down
  if (XRB.drops === undefined) { XRB.drops = []; const y = room.h - 1, row = room.def.map[y]; for (let x = 0; x < room.w; x++) if (row[x] === '=' && (x === 0 || row[x - 1] !== '=')) { let x1 = x; while (x1 + 1 < room.w && row[x1 + 1] === '=') x1++; XRB.drops.push((x + x1 + 1) / 2 * TILE); } }
  for (const x of XRB.drops) {
    if (Math.abs(x - P.x) > 200) continue;
    const y = (room.h - 1) * TILE - 26 + Math.sin(time * 4) * 3, a = 0.45 + 0.35 * Math.sin(time * 4);
    drawGlow(() => { g.fillStyle = `rgba(255,214,120,${a})`; for (let i = 0; i < 4; i++) g.fillRect(Math.round(x - 4 + i), Math.round(y + i), 8 - i * 2, 1); g.fillRect(Math.round(x - 1), Math.round(y - 5), 2, 5); });
  }
}
HOOKS.render.push(() => {
  if (!room || !xrbMine(room.def)) return;
  xrbDrawInk(); xrbDrawFeet(); xrbDropMarks();
  if (room.id === 'M12') {   // tint the black tide green: this is the Mire's water
    for (let y = 0; y < room.h; y++) for (let x = 0; x < room.w; x++) if (room.grid[y * room.w + x] === 40) { g.fillStyle = 'rgba(70,110,40,0.3)'; g.fillRect(x * TILE, y * TILE, TILE, TILE); }
  }
  for (const p of XRB.fg) p.drawFg();
  for (const A of XRB.areas) xrbDrawArea(A);
});

// debug access for headless tests
if (typeof window !== 'undefined') window.__rb = { XRB, get kit() { return KIT; }, sim(n = 1, hold = [], tap = []) { tap.forEach(press); hold.forEach(a => held.add(a)); for (let i = 0; i < n; i++) update(1 / 60); hold.forEach(release); tap.forEach(a => { release(a); buffered.delete(a); }); }, pull: (n) => { const B = XRB.books; const b = B && B.books.find(q => q.n === n); if (b) xrbPullBook(B, b); return !!b; } };
