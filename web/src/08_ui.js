// ------------------------------------------------------------------ UI: hi-res HUD, menus, map, screens
let scale = 1, ox = 0, oy = 0;
function resize() {
  const dpr = window.devicePixelRatio || 1;
  const box = view.parentElement.getBoundingClientRect();
  view.width = Math.round(box.width * dpr); view.height = Math.round(box.height * dpr);
  view.style.width = box.width + 'px'; view.style.height = box.height + 'px';
  scale = Math.min(view.width / W, view.height / H);
  if (scale >= 2) scale = Math.floor(scale);
  ox = Math.round((view.width - W * scale) / 2); oy = Math.round((view.height - H * scale) / 2);
}
addEventListener('resize', resize);
try { new ResizeObserver(() => resize()).observe(view.parentElement); } catch (e) {}
function text(str, x, y, size, color, align = 'left', opts = {}) {
  vctx.font = `${opts.weight || 600} ${Math.round(size * scale)}px ${FONT}`;
  vctx.textAlign = align; vctx.textBaseline = 'alphabetic';
  if (opts.spacing && 'letterSpacing' in vctx) vctx.letterSpacing = `${opts.spacing * scale}px`;
  vctx.globalAlpha = opts.alpha ?? 1;
  if (opts.shadow !== false) { vctx.fillStyle = 'rgba(0,0,0,0.8)'; vctx.fillText(str, ox + (x + 0.6) * scale, oy + (y + 0.6) * scale); }
  vctx.fillStyle = color; vctx.fillText(str, ox + x * scale, oy + y * scale);
  vctx.globalAlpha = 1;
  if ('letterSpacing' in vctx) vctx.letterSpacing = '0px';
}
function textW(str, size, weight = 600) { vctx.font = `${weight} ${Math.round(size * scale)}px ${FONT}`; return vctx.measureText(str).width / scale; }
function wrap(str, maxW, size) {
  const words = str.split(' '), lines = []; let cur = '';
  for (const w of words) { const t = cur ? cur + ' ' + w : w; if (textW(t, size, 400) > maxW && cur) { lines.push(cur); cur = w; } else cur = t; }
  if (cur) lines.push(cur); return lines;
}
function box(x, y, w, h, a = 0.85, border = '#6d5a3a') {
  vctx.fillStyle = `rgba(8,6,12,${a})`; vctx.fillRect(ox + x * scale, oy + y * scale, w * scale, h * scale);
  vctx.strokeStyle = border; vctx.lineWidth = Math.max(1, scale * 0.5);
  vctx.strokeRect(ox + x * scale + 0.5, oy + y * scale + 0.5, w * scale - 1, h * scale - 1);
}
function bar(x, y, w, h, frac, ghost, color, back = '#120c10') {
  const X = ox + x * scale, Y = oy + y * scale, Wd = w * scale, Hd = h * scale, b = Math.max(1, Math.round(scale * 0.6));
  vctx.fillStyle = '#6d5a3a'; vctx.fillRect(X - b, Y - b, Wd + 2 * b, Hd + 2 * b);
  vctx.fillStyle = back; vctx.fillRect(X, Y, Wd, Hd);
  if (ghost > frac) { vctx.fillStyle = '#d8b25a'; vctx.fillRect(X, Y, Wd * clamp(ghost, 0, 1), Hd); }
  vctx.fillStyle = color; vctx.fillRect(X, Y, Wd * clamp(frac, 0, 1), Hd);
  vctx.fillStyle = 'rgba(255,255,255,0.14)'; vctx.fillRect(X, Y, Wd * clamp(frac, 0, 1), Math.max(1, Hd * 0.3));
}
const ICON_SHEETS = ['ui_icons', 'ui_icons2', 'ui_icons3', 'ui_icons4'];   // later sheets may be pushed by region files
function icon(name, x, y, size = 16, alpha = 1) {
  let sh = null;
  for (const n of ICON_SHEETS) { const s2 = sheet(n); if (s2.ok && s2.has(name)) { sh = s2; break; } }
  if (!sh) sh = sheet('ui_icons');
  if (sh.ok && sh.has(name)) {
    const f = sh.frames[sh.first(name)];
    vctx.globalAlpha = alpha; vctx.imageSmoothingEnabled = false;
    vctx.drawImage(sh.img, f.x, f.y, f.w, f.h, ox + x * scale, oy + y * scale, size * scale, size * scale);
    vctx.globalAlpha = 1; return;
  }
  // missing icon: a small gold rune (diamond with a spark) instead of a flat square
  const cx = ox + (x + size / 2) * scale, cy = oy + (y + size / 2) * scale, r = size * 0.36 * scale;
  vctx.globalAlpha = alpha; vctx.strokeStyle = '#b08a3a'; vctx.lineWidth = Math.max(1, size * 0.08 * scale);
  vctx.beginPath(); vctx.moveTo(cx, cy - r); vctx.lineTo(cx + r, cy); vctx.lineTo(cx, cy + r); vctx.lineTo(cx - r, cy); vctx.closePath(); vctx.stroke();
  vctx.fillStyle = '#e6c77a'; vctx.fillRect(cx - r * 0.25, cy - r * 0.25, r * 0.5, r * 0.5); vctx.globalAlpha = 1;
}
function nodeFrame(x, y, alpha = 1) {
  const sh = sheet('ui_frame');
  if (!sh.ok) { box(x, y, 24, 24, 0.9 * alpha); return; }
  const f = sh.frames[0]; vctx.globalAlpha = alpha;
  vctx.drawImage(sh.img, f.x, f.y, f.w, f.h, ox + x * scale, oy + y * scale, 24 * scale, 24 * scale); vctx.globalAlpha = 1;
}
function band(alpha, y = 80, h = 64) {
  const y0 = oy + y * scale, hh = h * scale;
  const gr = vctx.createLinearGradient(0, y0, 0, y0 + hh);
  gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(0.3, `rgba(0,0,0,${0.8 * alpha})`);
  gr.addColorStop(0.7, `rgba(0,0,0,${0.8 * alpha})`); gr.addColorStop(1, 'rgba(0,0,0,0)');
  vctx.fillStyle = gr; vctx.fillRect(ox, y0, W * scale, hh);
}

// ---- HUD
let areaCard = null, bannerMsg = null;
function banner(title, desc, ic) { bannerMsg = { title, desc, icon: ic, t: 0 }; }
function cdOverlay(kind, id, x, y) {   // a dark sweep drains off the icon as the cooldown runs out; the seconds sit on top
  const f = cdFrac(kind, id), fl = P.cdFlash && P.cdFlash.kind === kind ? Math.max(0, 1 - (time - P.cdFlash.t) * 3) : 0;
  if (f <= 0) { if (P['cdWas' + kind]) { P['cdWas' + kind] = 0; P['cdPing' + kind] = time; } const k = Math.max(0, 1 - (time - (P['cdPing' + kind] || -9)) * 3); if (k > 0) { vctx.fillStyle = `rgba(255,230,160,${0.45 * k})`; vctx.fillRect(ox + x * scale, oy + y * scale, 16 * scale, 16 * scale); } return; }
  P['cdWas' + kind] = 1;
  const h = 16 * f;
  vctx.fillStyle = `rgba(6,4,10,${0.72 + 0.2 * fl})`; vctx.fillRect(ox + x * scale, oy + (y + 16 - h) * scale, 16 * scale, h * scale);
  const L = cdLeft(kind, id); text(L >= 1 ? String(Math.ceil(L)) : L.toFixed(1), x + 8, y + 11, 6.5, fl > 0 ? '#ff9a80' : '#f1e6c8', 'center', { weight: 700 });
}
function renderHUD() {
  const hpW = clamp(D.maxHp * 0.42, 60, 170), fpW = clamp(D.maxFp * 0.8, 40, 140), stW = clamp(D.maxSt * 0.9, 50, 150);
  bar(10, 9, hpW, 3.5, P.hp / D.maxHp, P.displayHp / D.maxHp, '#a3222a');
  bar(10, 15.5, fpW, 2.5, P.fp / D.maxFp, 0, '#2f5fb3');
  bar(10, 21, stW, 2.5, Math.max(0, P.st) / D.maxSt, 0, '#3f8f4a');
  // flasks + spell
  icon('flask_red', 10, 192, 14, P.flasksR ? 1 : 0.35); text(String(P.flasksR), 25, 204, 7, '#e8dcc0');
  icon('flask_blue', 34, 192, 14, P.flasksB ? 1 : 0.35); text(String(P.flasksB), 49, 204, 7, '#e8dcc0');
  if (SAVE.spell && spellKnown(SAVE.spell)) {
    nodeFrame(58, 187, 1); icon(SPELLS[SAVE.spell].icon, 62, 191, 16);
    text(`${keysOf('cast')[0] || 'U'} · ${spellCost(SAVE.spell)}`, 84, 204, 5.5, '#8fb0e8', 'left', { weight: 500 });
    cdOverlay('spell', SAVE.spell, 62, 191);
  }
  if (SAVE.art) { nodeFrame(104, 187, 1); icon('a_' + SAVE.art, 108, 191, 16); text(`${keysOf('art')[0] || 'O'} · ${ARTS[SAVE.art].fp}`, 130, 204, 5.5, '#e6c77a', 'left', { weight: 500 }); cdOverlay('art', SAVE.art, 108, 191); }
  // statuses
  let sy = 28;
  if (P.rot > 0 || P.rotT > 0) { bar(10, sy, 40, 2, P.rotT > 0 ? P.rotT / 9 : P.rot / 100, 0, P.rotT > 0 ? '#6a9a30' : '#4a6a28'); text(P.rotT > 0 ? 'ROT' : 'rot', 54, sy + 3, 5, '#9ac860', 'left'); sy += 6; }
  if (P.cryT > 0) { text(`War Cry ${Math.ceil(P.cryT)}`, 10, sy + 6, 5.5, '#ffd070', 'left'); sy += 8; }
  if (P.fireT > 0) { text(`Cinder Blade ${Math.ceil(P.fireT)}`, 10, sy + 6, 5.5, '#ff9a50', 'left'); sy += 8; }
  // cinders
  const cx = W - 10;
  icon('cinder', cx - 62, 8, 12);
  text(String(SAVE.cinders), cx, 18, 8, cinderFlash > 0 ? '#ffe2a0' : '#e8dcc0', 'right');
  if (cinderFlash > 0 && cinderGain) text('+' + cinderGain, cx, 28, 6, '#e6c77a', 'right', { alpha: clamp(cinderFlash, 0, 1) });
  if (SAVE.remnant) text('Lost cinders await you', cx, 37, 5, '#c07060', 'right', { weight: 400, alpha: 0.8 });
  // prompts
  const pr = nearbyPrompt();
  if (pr && state === 'play') {
    const sx = P.x - cam.x, sy = P.y - cam.y - 38;
    const ik = keysOf('interact')[0] || 'E', kw = textW(ik, 6.5) + 5;
    const tw = kw + textW(pr, 6.5) + 13;
    box(sx - tw / 2, sy - 8, tw, 11, 0.7);
    text(ik, sx - tw / 2 + 5, sy, 6.5, '#e6c77a', 'left'); text(pr, sx - tw / 2 + 8 + kw, sy, 6.5, '#e8dcc0', 'left', { weight: 500 });
  }
  // boss bar
  if (boss && boss.active && (boss.alive || boss.anim.i < boss.anim.n - 1)) {
    const bx = 156, by = 203, bw = 216;
    text(boss.name, bx, by - 3, 6.5, boss.phase >= 2 ? '#f0c872' : '#e8dcc0', 'left', { spacing: 0.3 });
    if (boss.dmgT > 0 && boss.dmgShown >= 1) text(String(Math.round(boss.dmgShown)), bx + bw, by - 3, 6, '#e8dcc0', 'right');
    bar(bx, by, bw, 3, boss.hp / boss.maxHp, boss.displayHp / boss.maxHp, '#8a1a1a');
  }
  // popups (world)
  if (SETTINGS.numbers) for (const p of popups) text(p.v, p.x - cam.x, p.y - cam.y, 5.5, p.color, 'center', { alpha: clamp(p.life * 2, 0, 1), weight: 700 });
  // toasts
  toasts.forEach((t, i) => {
    const a = clamp(Math.min(t.t * 4, t.life * 2), 0, 1), y = (boss && boss.active && boss.alive ? 186 : 203) - (toasts.length - 1 - i) * 11;
    const msg = padText(t.msg), w = textW(msg, 6.5, 500) + 16; box(W / 2 - w / 2, y - 8, w, 11, 0.65 * a, `rgba(109,90,58,${a})`);
    text(msg, W / 2, y, 6.5, '#e8dcc0', 'center', { alpha: a, weight: 500 });
  });
  // area title card: the big cinematic one on a region's first visit (29_ui2.js), the small one on later entries
  renderRegionCard();
  if (areaCard && !bossBanner && !(regionCard && regionCard.t > 0)) {
    const t = areaCard.t, a = clamp(Math.min(t, 3.6 - t) * 1.4, 0, 1), nm = areaCard.name.toUpperCase();
    const size = uiFit(nm, 330, 13, 8, 500);
    text(nm, W / 2, 60, size, '#e6c77a', 'center', { alpha: a, spacing: 2.5, weight: 500 });
    const lw = (textW(nm, size, 500) + nm.length * 2.5) * 0.3 * clamp(t * 1.5, 0, 1);
    uiDiamond(W / 2, 64.5, 1.3, '#e6c77a', a); uiFade(W / 2 + 4, W / 2 + 4 + lw, 64.3, UI_RGB.gold, 0.7 * a); uiFade(W / 2 - 4, W / 2 - 4 - lw, 64.3, UI_RGB.gold, 0.7 * a);
    if (areaCard.sub) text(areaCard.sub, W / 2, 75, 6.5, '#c9bda2', 'center', { alpha: a, weight: 400 });
  }
  if (bossBanner) {
    const t = bossBanner.t, a = clamp(Math.min(t, 3 - t) * 1.6, 0, 1);
    band(a * 0.6, 50, 50); text(bossBanner.name, W / 2, 74, 12, '#e6c77a', 'center', { alpha: a, spacing: 1.5, weight: 500 });
    const q = boss && BOSS_INFO[boss.kind] && BOSS_INFO[boss.kind].quote; if (q) text(q, W / 2, 86, 6.5, '#c9bda2', 'center', { alpha: a, weight: 400 });
  }
  if (victoryBanner) {
    const t = victoryBanner.t, a = clamp(Math.min(t / 1.2, (5 - t) * 1.2), 0, 1);
    band(a); text(victoryBanner.text, W / 2, 116, 20, '#e6b85c', 'center', { alpha: a, spacing: 3, weight: 500 });
  }
  if (bannerMsg) {
    const t = bannerMsg.t, a = clamp(Math.min(t * 3, (3.8 - t) * 2), 0, 1);
    const lines = wrap(bannerMsg.desc, 200, 6.5), h = 26 + lines.length * 9;
    vctx.globalAlpha = a; box(W / 2 - 115, 30, 230, h, 0.9); vctx.globalAlpha = 1;
    icon(bannerMsg.icon, W / 2 - 108, 36, 16, a);
    text(bannerMsg.title, W / 2 - 86, 47, 9, '#e6c77a', 'left', { alpha: a });
    lines.forEach((l, i) => text(l, W / 2 - 86, 60 + i * 9, 6.5, '#d8cdb4', 'left', { alpha: a, weight: 400 }));
  }
  if (P.empower > 0) text('Empowered', 10, 34, 6, '#ffd070', 'left', { alpha: clamp(P.empower, 0, 1) });
}

// ---- shrine menus
let menu = null;   // {screen, sel, ...}
const SHRINE_OPTS = ['Level Up', 'Skill Tree', 'Flasks', 'Travel', 'Rebirth', 'Leave'];
function openShrineMenu(p) { menu = { screen: 'shrine', sel: 0, shrine: p }; state = 'menu'; clearBuffer(); }
function closeMenu() {
  menu = null; state = 'play'; clearBuffer();
  if (P.state === 'rest') setP('rise', pHas('rise') ? 'rise' : 'idle', false);
}
function skillPoints() { return skillBudget() - skillSpent(); }   // 57_skills.js: floor((level - 1) / 2) + Memory Shards - spent
function menuInput(a) {
  if (!menu) return;
  if (menu.screen === 'pause') return pauseInput(a);
  if (menu.screen === 'shop') return shopInput(a);
  if (menu.screen === 'forge') return forgeInput(a);
  const M = menu, conf = ['confirm', 'interact', 'attack', 'jump'].includes(a), back = ['pause', 'back', 'heavy', 'roll'].includes(a);
  const nav = d => { M.sel = (M.sel + d + M.n) % M.n; sfx.menu(); };
  if (M.screen === 'shrine') {
    M.n = SHRINE_OPTS.length;
    if (a === 'up') nav(-1); else if (a === 'down') nav(1);
    else if (back) closeMenu();
    else if (conf) {
      sfx.menu(); const o = SHRINE_OPTS[M.sel];
      if (o === 'Level Up') menu = { screen: 'level', sel: 0, alloc: { ...SAVE.stats }, prev: M };
      else if (o === 'Skill Tree') menu = { screen: 'tree', br: 0, t: 0, prev: M };
      else if (o === 'Flasks') menu = { screen: 'flasks', prev: M };
      else if (o === 'Travel') menu = travelOpen(M);
      else if (o === 'Rebirth') {
        skillRespec('tear');   // 57_skills.js (the Ashwright also offers one free respec per journey)
      }
      else closeMenu();
    }
  } else if (M.screen === 'level') {
    M.n = STATS.length + 1;
    const lvl = levelOf(M.alloc), spentCost = levelsCost(levelOf(SAVE.stats), lvl);
    if (a === 'up') nav(-1); else if (a === 'down') nav(1);
    else if ((a === 'right' || (conf && M.sel < STATS.length)) && M.sel < STATS.length) {
      const c = levelCost(lvl);
      if (spentCost + c <= SAVE.cinders && M.alloc[STATS[M.sel].k] < 99) { M.alloc[STATS[M.sel].k]++; sfx.menu(); } else sfx.deny();
    } else if (a === 'left' && M.sel < STATS.length) {
      const k = STATS[M.sel].k; if (M.alloc[k] > SAVE.stats[k]) { M.alloc[k]--; sfx.menu(); } else sfx.deny();
    } else if (conf && M.sel === STATS.length) {
      if (lvl > levelOf(SAVE.stats)) {
        SAVE.cinders -= spentCost; SAVE.stats = { ...M.alloc }; refreshDerived(); P.hp = D.maxHp; P.fp = D.maxFp; P.st = D.maxSt;
        sfx.levelup(); spawnFx(fxOr('levelup', 'heal'), P.x, P.y, 1); flashScreen = 0.2; saveGame();
        toast(`Level ${lvl} reached · ${skillPoints()} skill point${skillPoints() === 1 ? '' : 's'} available`);
      }
      menu = M.prev;
    } else if (back) menu = M.prev;
  } else if (M.screen === 'flasks') {
    const n = flaskMax();
    if (a === 'left' && SAVE.flaskBlue < n) { SAVE.flaskBlue++; sfx.menu(); }
    else if (a === 'right' && SAVE.flaskBlue > 0) { SAVE.flaskBlue--; sfx.menu(); }
    else if (back || conf) { refillFlasks(); saveGame(); menu = M.prev; }
  } else if (M.screen === 'travel') travelInput(M, a);
}
function levelsCost(from, to) { let s = 0; for (let L = from; L < to; L++) s += levelCost(L); return s; }

function renderMenu() {
  const M = menu; if (!M) return;
  if (M.screen === 'pause') return renderPauseMenu();
  if (M.screen === 'shop') return renderShop();
  if (M.screen === 'forge') return renderForge();
  vctx.fillStyle = 'rgba(5,4,8,0.55)'; vctx.fillRect(ox, oy, W * scale, H * scale);
  if (M.screen === 'shrine') {
    vctx.fillStyle = 'rgba(5,4,8,0.75)'; vctx.fillRect(ox, oy, W * scale, H * scale);
    const here = room.id, hb = shrineBoss(here);
    text((M.shrine.name || 'Shrine').toUpperCase(), W / 2, 22, 9, '#e6c77a', 'center', { spacing: 2 });
    vctx.fillStyle = '#6d5a3a'; vctx.fillRect(ox + (W / 2 - 70) * scale, oy + 26 * scale, 140 * scale, Math.max(1, scale * 0.5));
    text(`${room.def.name}  ·  ${AREAS[room.def.biome].name}`, W / 2, 35, 5.8, '#9a8f78', 'center', { weight: 400 });
    box(16, 42, 106, 134);
    SHRINE_OPTS.forEach((o, i) => {
      const y = 62 + i * 19, sel = i === M.sel;
      if (sel) { vctx.fillStyle = 'rgba(176,138,58,0.2)'; vctx.fillRect(ox + 21 * scale, oy + (y - 11) * scale, 96 * scale, 15 * scale); vctx.fillStyle = '#b08a3a'; vctx.fillRect(ox + 21 * scale, oy + (y - 11) * scale, Math.max(1, scale * 0.6), 15 * scale); }
      text(o, 69, y, 7.5, sel ? '#f5e3b0' : '#b8ab90', 'center', { weight: sel ? 600 : 400 });
    });
    // status card
    const pts = skillPoints();
    box(128, 42, 240, 34, 0.85);
    text(`Level ${levelOf(SAVE.stats)}`, 136, 54, 7.5, '#e8dcc0', 'left', { weight: 600 });
    text(`Cinders ${SAVE.cinders}`, 136, 67, 6.3, '#e6c77a', 'left', { weight: 500 });
    text(`Next level ${levelCost(levelOf(SAVE.stats))}`, 214, 54, 6, '#b8ab90', 'left', { weight: 400 });
    text(`Skill points ${pts}`, 214, 67, 6.3, pts > 0 ? '#ffd070' : '#b8ab90', 'left', { weight: 500 });
    text(`Pale Tears ${SAVE.inv.tear || 0}`, 300, 54, 6, '#b8ab90', 'left', { weight: 400 });
    text(`Flasks ${SAVE.flaskBase}`, 300, 67, 6, '#b8ab90', 'left', { weight: 400 });
    // local map around this shrine: this region's explored rooms plus direct neighbours
    box(128, 80, 240, 96, 0.85);
    const adj = roomAdj(), vis = mapVisible(), near = vis.filter(r => r.biome === room.def.biome || r.id === here || (adj[here] || []).includes(r.id));
    const F = mapFrame(near, 134, 86, 228, 84, 40, 20);
    drawMapRooms(near, F, { here, alpha: 0.4, labelSize: 4.5 });
    for (const r of near) {
      if (r.shrine && SAVE.shrines.includes(r.id)) { const p = shrinePos(r.id); icon('shrine', F.X(p.x) - 4, F.Y(p.y) - 6, 8, r.id === here ? 1 : 0.7); }
      if (r.boss && MAIN_BOSSES.has(r.boss) && SAVE.visited[r.id]) drawBossMark(F.X(r.gx + r.w / 2) - 4, F.Y(r.gy + r.h / 2) - 4, !!SAVE.flags['boss:' + r.boss]);
    }
    const sp = shrinePos(here), sx = F.X(sp.x), sy = F.Y(sp.y), rr = 7 + Math.sin(time * 6) * 1.2;
    vctx.strokeStyle = '#ffd070'; vctx.lineWidth = Math.max(1, scale * 0.6); vctx.beginPath(); vctx.arc(ox + sx * scale, oy + (sy - 2) * scale, rr * scale, 0, 6.3); vctx.stroke();
    if (hb) text(hb.done ? `${hb.name} — vanquished` : `A great foe waits nearby: ${hb.name}`, 248, 173, 5.6, hb.done ? '#8a8070' : '#e06050', 'center', { weight: 500 });
    text('↑↓ choose · E / Enter confirm · Esc leave', W / 2, 206, 5.3, '#7f745f', 'center', { weight: 400 });
  } else if (M.screen === 'level') {
    const lvl = levelOf(M.alloc), cost = levelsCost(levelOf(SAVE.stats), lvl), d = derive(M.alloc, skillSet()), d0 = D;
    box(20, 22, 344, 172);
    text('LEVEL UP', 34, 38, 9, '#e6c77a', 'left', { spacing: 1.5 });
    text(`Level ${levelOf(SAVE.stats)} → ${lvl}`, 34, 52, 7, '#e8dcc0');
    text(`Cinders held ${SAVE.cinders}`, 34, 64, 6.5, '#e8dcc0', 'left', { weight: 400 });
    text(`Cost ${cost}   ·   Next +1: ${levelCost(lvl)}`, 34, 74, 6.5, cost + levelCost(lvl) <= SAVE.cinders ? '#e6c77a' : '#a08070', 'left', { weight: 400 });
    STATS.forEach((s, i) => {
      const y = 94 + i * 12, sel = i === M.sel, up = M.alloc[s.k] > SAVE.stats[s.k];
      if (sel) { vctx.fillStyle = 'rgba(176,138,58,0.18)'; vctx.fillRect(ox + 30 * scale, oy + (y - 9) * scale, 150 * scale, 12 * scale); }
      text(s.name, 36, y, 7, sel ? '#f5e3b0' : '#c9bda2', 'left', { weight: sel ? 600 : 500 });
      text((sel ? '◂ ' : '') + M.alloc[s.k] + (sel ? ' ▸' : ''), 172, y, 7, up ? '#7fd08a' : '#e8dcc0', 'right');
    });
    const cy = 94 + STATS.length * 12, cs = M.sel === STATS.length;
    if (cs) { vctx.fillStyle = 'rgba(176,138,58,0.25)'; vctx.fillRect(ox + 30 * scale, oy + (cy - 9) * scale, 150 * scale, 12 * scale); }
    text('Confirm', 105, cy, 7.5, cs ? '#f5e3b0' : '#b8ab90', 'center');
    const rows = [['HP', d0.maxHp, d.maxHp], ['FP', d0.maxFp, d.maxFp], ['Stamina', d0.maxSt, d.maxSt], ['Light attack', Math.round(d0.light), Math.round(d.light)],
                  ['Heavy attack', Math.round(d0.heavy * 2), Math.round(d.heavy * 2)], ['Spell power', Math.round(d0.spell * 100), Math.round(d.spell * 100)]];
    rows.forEach(([n, a, b], i) => {
      const y = 94 + i * 12;
      text(n, 214, y, 6.5, '#b8ab90', 'left', { weight: 400 });
      text(String(a), 306, y, 6.5, '#e8dcc0', 'right'); text('→', 316, y, 6.5, '#8a7f6a', 'center');
      text(String(b), 350, y, 6.5, b > a ? '#7fd08a' : '#e8dcc0', 'right');
    });
    if (M.sel < STATS.length) text(STATS[M.sel].desc, 214, 172, 6, '#c9bda2', 'left', { weight: 400 });
    text('↑↓ stat · ←→ adjust · confirm to commit · Esc back', 34, 188, 5.5, '#8a7f6a', 'left', { weight: 400 });
  } else if (M.screen === 'flasks') {
    box(92, 60, 200, 96);
    text('FLASK ALLOTMENT', W / 2, 78, 8, '#e6c77a', 'center', { spacing: 1 });
    const n = flaskMax(), r = Math.max(0, n - SAVE.flaskBlue - (has('crimson_pact') ? 1 : 0));   // 57: Crimson Pact
    icon('flask_red', 130, 92, 20); text(String(r), 140, 128, 10, '#e8dcc0', 'center');
    icon('flask_blue', 234, 92, 20); text(String(SAVE.flaskBlue), 244, 128, 10, '#e8dcc0', 'center');
    text('◂  ▸', W / 2, 108, 9, '#b8ab90', 'center');
    text('Crimson restores HP · Azure restores FP', W / 2, 146, 6, '#b8ab90', 'center', { weight: 400 });
  } else if (M.screen === 'travel') {
    renderTravel(M);
  }
}

// ---- map
const MAP_COLS = { ramparts: '#6a6070', catacombs: '#5a5040', cathedral: '#8a8070', mire: '#4a5a38', crown: '#9a9080', archives: '#6a5030',
                   hoarfrost: '#4a6a80', spire: '#505a78', deep: '#8a4020', hermit: '#6a5a40', ember: '#7a2a1a' };
const mapVisible = () => ROOMS.filter(r => SAVE.visited[r.id] && (!r.test || r.id === room.id));
// fit a set of rooms into a screen box (low-res coords); pads tiny sets so one room doesn't fill the screen
function mapFrame(rooms, bx, by, bw, bh, minW = 60, minH = 30) {
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const r of rooms.length ? rooms : [room.def]) { x0 = Math.min(x0, r.gx); y0 = Math.min(y0, r.gy); x1 = Math.max(x1, r.gx + r.w); y1 = Math.max(y1, r.gy + r.h); }
  const px = Math.max(0, minW - (x1 - x0)) / 2, py = Math.max(0, minH - (y1 - y0)) / 2; x0 -= px; x1 += px; y0 -= py; y1 += py;
  const sc = Math.min(bw / (x1 - x0), bh / (y1 - y0)), mx = bx + (bw - (x1 - x0) * sc) / 2, my = by + (bh - (y1 - y0) * sc) / 2;
  return { s: sc, X: gx => mx + (gx - x0) * sc, Y: gy => my + (gy - y0) * sc };
}
function drawMapRooms(rooms, F, o = {}) {
  const labels = {};
  for (const r of rooms) {
    const X = F.X(r.gx), Y = F.Y(r.gy), w = r.w * F.s, h = r.h * F.s;
    vctx.fillStyle = r.id === o.here ? '#8a6a3a' : (AREAS[r.biome] && AREAS[r.biome].map) || MAP_COLS[r.biome] || '#5a5560';
    vctx.globalAlpha = o.alpha ?? 0.55; vctx.fillRect(ox + X * scale, oy + Y * scale, w * scale, h * scale);
    vctx.globalAlpha = o.lineAlpha ?? 1; vctx.strokeStyle = '#c9bda2'; vctx.lineWidth = Math.max(1, scale * 0.4);
    vctx.strokeRect(ox + X * scale, oy + Y * scale, w * scale, h * scale); vctx.globalAlpha = 1;
    const L = labels[r.biome] || (labels[r.biome] = { x: 0, y: 0, n: 0 }); L.x += r.gx + r.w / 2; L.y += r.gy + r.h / 2; L.n++;
  }
  if (o.labels !== false) for (const [bio, L] of Object.entries(labels)) if (AREAS[bio]) text(AREAS[bio].name.replace(/^The /, ''), F.X(L.x / L.n), F.Y(L.y / L.n) + 2, o.labelSize || 5, '#e8dcc0', 'center', { alpha: 0.7, weight: 400 });
}
// where a room's shrine stands (global tile coords, centre of the cell)
const _shrineAt = {};
function shrinePos(id) {
  if (_shrineAt[id]) return _shrineAt[id];
  const d = ROOM_BY[id]; let p = { x: d.gx + d.w / 2, y: d.gy + d.h / 2 };
  for (let y = 0; y < d.h; y++) { const x = d.map[y].indexOf('S'); if (x >= 0) { p = { x: d.gx + x + 0.5, y: d.gy + y + 0.5 }; break; } }
  return (_shrineAt[id] = p);
}
// is this shrine the last one before a main boss? walk up to two rooms away (never past another shrine)
const MAIN_BOSSES = new Set(['hound', 'omen', 'vessel', 'kalden', 'sovereign', 'unwritten', 'twins', 'cindervane', 'colossus', 'oswin', 'first_ember', 'warden', 'choir', 'sanguine', 'vael', 'pharaoh', 'astrel', 'saint0', 'venn']);
let _roomAdj = null;
function roomAdj() {   // rooms joined by an actual opening (open cells on both sides of a shared edge)
  if (_roomAdj) return _roomAdj;
  _roomAdj = {};
  const open = (d, x, y) => !isSolidT(cellType(d.map[y][x]));
  for (const a of ROOMS) {
    const set = new Set();
    const probe = (x, y, dx, dy) => {
      if (!open(a, x, y)) return;
      const n = roomAtGlobal(a.gx + x + dx, a.gy + y + dy);
      if (n && n !== a && open(n, a.gx + x + dx - n.gx, a.gy + y + dy - n.gy)) set.add(n.id);
    };
    for (let y = 0; y < a.h; y++) { probe(0, y, -1, 0); probe(a.w - 1, y, 1, 0); }
    for (let x = 0; x < a.w; x++) { probe(x, 0, 0, -1); probe(x, a.h - 1, 0, 1); }
    _roomAdj[a.id] = [...set];
  }
  return _roomAdj;
}
function shrineBoss(id) {   // every main boss within two rooms (not past another shrine); summarised for the UI
  const adj = roomAdj(), seen = new Set([id]), found = []; let front = [id];
  for (let depth = 0; depth < 2; depth++) {
    const next = [];
    for (const rid of front) for (const n of adj[rid] || []) {
      if (seen.has(n)) continue; seen.add(n); const d = ROOM_BY[n];
      if (d.boss && MAIN_BOSSES.has(d.boss) && (SAVE.visited[n] || (!d.secret && d.biome === ROOM_BY[id].biome))) found.push(d.boss);
      else if (!d.shrine) next.push(n);
    }
    front = next;
  }
  if (!found.length) return null;
  const name = k => (BOSS_INFO[k] && BOSS_INFO[k].name.split(',')[0]) || 'Something vast';
  const alive = found.filter(k => !SAVE.flags['boss:' + k]);
  return { kinds: found, name: (alive.length ? alive : found).map(name).join('  ·  '), done: !alive.length };
}
function drawBossMark(x, y, done, size = 8) {
  const a = done ? 0.35 : 0.75 + 0.25 * Math.sin(time * 5);
  if (!done) { vctx.fillStyle = `rgba(190,30,30,${0.35 * a})`; vctx.beginPath(); vctx.arc(ox + (x + size / 2) * scale, oy + (y + size / 2) * scale, size * 0.75 * scale, 0, 6.3); vctx.fill(); }
  icon('skull', x, y, size, a);
}

// ---- world map (Expansion 3, agent KS): 3 zoom levels, pan (keys / stick / drag / wheel), room silhouettes, icons for
// shrines, trials, gauntlets, puzzles, vistas, secrets, doors and locked rooms, dotted door links, legend, region filter.
const MAPV = { z: 1, s: 1.1, cx: 0, cy: 0, tx: 0, ty: 0, filter: null, lastT: -1, drag: null };
const MAP_BOX = { x: 8, y: 25, w: 368, h: 161 };
const MAP_ICON = { shrine: 'shrine', trial: 'mx_trial', trialGold: 'mx_trial_gold', gaunt: 'mx_gaunt', gauntDone: 'mx_gaunt_done', puzzle: 'mx_puzzle',
                   vista: 'mx_vista', secret: 'mx_secret', door: 'mx_door', lock: 'mx_lock', passage: 'mx_passage' };
let _mapInfo = null, _mapDoors = null, _mapBounds = null;
function mapInfo() {   // static per-room map data from the room list (sys spawns), built once
  if (_mapInfo) return _mapInfo;
  _mapInfo = {}; _mapDoors = [];
  const doorOf = (d, id) => (d.spawns || []).find(q => q.t === 'sys' && q.kind === 'door' && q.id === id);
  for (const r of ROOMS) {
    const I = { trials: [], gaunts: [], benches: [], doors: [], passages: [] };
    for (const s of r.spawns || []) {
      if (s.t !== 'sys') continue;
      const at = { x: r.gx + s.x + 0.5, y: r.gy + s.y + 0.5, s };
      if (s.kind === 'trial') I.trials.push({ ...at, key: `${r.id}:${s.id}` });
      else if (s.kind === 'gauntlet') I.gaunts.push({ ...at, key: `x3:${r.id}:${s.id}` });
      else if (s.kind === 'bench') I.benches.push({ ...at, key: `x3:${r.id}:${s.id || 'bench'}` });
      else if (s.kind === 'passage') I.passages.push({ ...at, key: `x3:${r.id}:${s.id || `p${s.x}_${s.y}`}:thru` });
      else if (s.kind === 'door') {
        I.doors.push(at);
        const d2 = ROOM_BY[s.to], t = d2 && doorOf(d2, s.toId || s.id);
        if (t && (r.id < s.to || (r.id === s.to && s.id < (s.toId || s.id)))) _mapDoors.push({ a: r.id, b: s.to, x0: at.x, y0: at.y, x1: d2.gx + t.x + 0.5, y1: d2.gy + t.y + 0.5 });
      }
    }
    _mapInfo[r.id] = I;
  }
  return _mapInfo;
}
const _mapImg = {};
function mapRoomImg(r) {   // 1 px per tile silhouette of the room's open space (built once per room)
  if (_mapImg[r.id]) return _mapImg[r.id];
  const c = document.createElement('canvas'); c.width = r.w; c.height = r.h; const x = c.getContext('2d'), im = x.createImageData(r.w, r.h);
  const hex = mapColor(r), R = parseInt(hex.slice(1, 3), 16), G2 = parseInt(hex.slice(3, 5), 16), B = parseInt(hex.slice(5, 7), 16);
  for (let yy = 0; yy < r.h; yy++) for (let xx = 0; xx < r.w; xx++) {
    const t = cellType(r.map[yy][xx]), i = (yy * r.w + xx) * 4;
    if (isSolidT(t)) continue;
    const plat = t === T_PLAT, haz = t === T_SPIKE || t === T_SPIKE_D;
    im.data[i] = haz ? 170 : Math.min(255, R + (plat ? 70 : 34)); im.data[i + 1] = haz ? 70 : Math.min(255, G2 + (plat ? 60 : 30)); im.data[i + 2] = haz ? 60 : Math.min(255, B + (plat ? 40 : 26)); im.data[i + 3] = plat ? 255 : 215;
  }
  x.putImageData(im, 0, 0);
  return (_mapImg[r.id] = c);
}
function mapBounds(vis) {
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const r of vis.length ? vis : [room.def]) { x0 = Math.min(x0, r.gx); y0 = Math.min(y0, r.gy); x1 = Math.max(x1, r.gx + r.w); y1 = Math.max(y1, r.gy + r.h); }
  return { x0, y0, x1, y1 };
}
function mapScales(B) { const fit = Math.min(MAP_BOX.w / (B.x1 - B.x0 + 10), MAP_BOX.h / (B.y1 - B.y0 + 10)); return [Math.min(fit, 0.55), 1.1, 2.6]; }
function mapPlayerAt() { return { x: room.def.gx + P.x / TILE, y: room.def.gy + (P.y - 12) / TILE }; }
function mapOpen() {
  const p = mapPlayerAt(), B = mapBounds(mapVisible());
  MAPV.z = 1; MAPV.s = mapScales(B)[1]; MAPV.filter = null; MAPV.tx = MAPV.cx = p.x; MAPV.ty = MAPV.cy = p.y; MAPV.lastT = -1; MAPV.drag = null;
}
function mapRegions() { const L = []; for (const r of mapVisible()) if (!r.test && !L.includes(r.biome)) L.push(r.biome); return L; }
function mapInput(a) {   // routed from the onPressHook wrapper (43_systems.js); true = consumed
  if (a === 'confirm' || a === 'jump') { MAPV.z = MAPV.z >= 2 ? 0 : MAPV.z + 1; sfx.menu(); return true; }
  if (a === 'heavy' || a === 'roll') { if (MAPV.z > 0) { MAPV.z--; sfx.menu(); } else sfx.deny(); return true; }
  if (a === 'spell' || a === 'interact') {
    const L = [null, ...mapRegions()], i = L.indexOf(MAPV.filter); MAPV.filter = L[(i + 1) % L.length]; sfx.menu();
    const rs = mapVisible().filter(r => r.biome === MAPV.filter), c = rs.length ? mapBounds(rs) : null;
    const p = c ? { x: (c.x0 + c.x1) / 2, y: (c.y0 + c.y1) / 2 } : mapPlayerAt(); MAPV.tx = p.x; MAPV.ty = p.y;
    return true;
  }
  return ['left', 'right', 'up', 'down', 'attack'].includes(a);
}
view.addEventListener('pointerdown', e => { if (state === 'map') MAPV.drag = { x: e.clientX, y: e.clientY, tx: MAPV.tx, ty: MAPV.ty }; });
addEventListener('pointermove', e => {
  const Dg = MAPV.drag; if (!Dg || state !== 'map') return;
  const k = (window.devicePixelRatio || 1) / (scale * MAPV.s);
  MAPV.tx = MAPV.cx = Dg.tx - (e.clientX - Dg.x) * k; MAPV.ty = MAPV.cy = Dg.ty - (e.clientY - Dg.y) * k;
});
addEventListener('pointerup', () => { MAPV.drag = null; });
view.addEventListener('wheel', e => { if (state !== 'map') return; e.preventDefault(); const z = clamp(MAPV.z + (e.deltaY < 0 ? 1 : -1), 0, 2); if (z !== MAPV.z) { MAPV.z = z; sfx.menu(); } }, { passive: false });
function mapIcon(name, x, y, size, a = 1) { icon(name, x - size / 2, y - size / 2, size, a); }
function renderMap() {
  const dt = MAPV.lastT < 0 ? 0 : clamp(time - MAPV.lastT, 0, 0.1); MAPV.lastT = time;
  const vis = mapVisible(), B = mapBounds(vis), S = mapScales(B), I = mapInfo(), X3 = SAVE.x3 || {}, TR = X3.trials || {}, VS = X3.vistas || {}, SEEN = X3.seen || {};
  // ---- pan: held directions or the analog stick, eased; zoom eases toward its level
  let ax = (held.has('right') ? 1 : 0) - (held.has('left') ? 1 : 0), ay = (held.has('down') ? 1 : 0) - (held.has('up') ? 1 : 0);
  const gp = PAD.active && typeof padFind === 'function' ? padFind() : null;
  if (gp) { const sx = gp.axes[0] || 0, sy = gp.axes[1] || 0; if (Math.hypot(sx, sy) > 0.2) { ax = sx; ay = sy; } }
  const sp = 170 / MAPV.s;   // screen px per second, whatever the zoom
  MAPV.tx = clamp(MAPV.tx + ax * sp * dt, B.x0, B.x1); MAPV.ty = clamp(MAPV.ty + ay * sp * dt, B.y0, B.y1);
  const kk = 1 - Math.exp(-dt * 10);
  MAPV.s += (S[MAPV.z] - MAPV.s) * (1 - Math.exp(-dt * 9)); if (!dt) MAPV.s = S[MAPV.z];
  MAPV.cx += (MAPV.tx - MAPV.cx) * (dt ? kk : 1); MAPV.cy += (MAPV.ty - MAPV.cy) * (dt ? kk : 1);
  const s = MAPV.s, bx = MAP_BOX.x, by = MAP_BOX.y, bw = MAP_BOX.w, bh = MAP_BOX.h;
  const X = gx => bx + bw / 2 + (gx - MAPV.cx) * s, Y = gy => by + bh / 2 + (gy - MAPV.cy) * s;
  const vx0 = MAPV.cx - bw / 2 / s, vx1 = MAPV.cx + bw / 2 / s, vy0 = MAPV.cy - bh / 2 / s, vy1 = MAPV.cy + bh / 2 / s;
  uiBackdrop(0.97); uiStrips();
  uiTitle('THE SUNKEN HALLOW', 15, 8);
  panel(bx, by, bw, bh, 0.6);
  vctx.save(); vctx.beginPath(); vctx.rect(ox + (bx + 2) * scale, oy + (by + 2) * scale, (bw - 4) * scale, (bh - 4) * scale); vctx.clip();
  // ---- rooms: dark block + silhouette of the open space; filtered-out regions sink back
  const shown = vis.filter(r => r.gx < vx1 && r.gx + r.w > vx0 && r.gy < vy1 && r.gy + r.h > vy0);
  const dim = r => MAPV.filter && r.biome !== MAPV.filter;
  vctx.imageSmoothingEnabled = false;
  const labels = {};
  for (const r of shown) {
    const x = X(r.gx), y = Y(r.gy), w = r.w * s, h = r.h * s, a = dim(r) ? 0.18 : 1;
    vctx.globalAlpha = 0.5 * a; vctx.fillStyle = '#17121c'; vctx.fillRect(ox + x * scale, oy + y * scale, w * scale, h * scale);
    vctx.globalAlpha = (s < 0.7 ? 0.8 : 0.92) * a; vctx.drawImage(mapRoomImg(r), ox + x * scale, oy + y * scale, w * scale, h * scale);
    vctx.globalAlpha = (r.id === room.id ? 1 : 0.55) * a; vctx.strokeStyle = r.id === room.id ? '#ffd070' : '#c9bda2'; vctx.lineWidth = Math.max(1, scale * (r.id === room.id ? 0.6 : 0.35));
    vctx.strokeRect(ox + x * scale + 0.5, oy + y * scale + 0.5, w * scale - 1, h * scale - 1); vctx.globalAlpha = 1;
    if (!dim(r) && !r.test) { const L = labels[r.biome] || (labels[r.biome] = { x: 0, y: 0, n: 0 }); L.x += r.gx + r.w / 2; L.y += r.gy + r.h / 2; L.n++; }
  }
  // ---- door links: a dotted thread between the two doors (both rooms explored)
  const vset = new Set(vis.map(r => r.id));
  vctx.save(); vctx.setLineDash([1.5 * scale, 2 * scale]); vctx.lineWidth = Math.max(1, scale * 0.5);
  for (const d of _mapDoors) {
    if (!vset.has(d.a) || !vset.has(d.b)) continue;
    vctx.strokeStyle = `rgba(230,199,122,${MAPV.filter && ROOM_BY[d.a].biome !== MAPV.filter && ROOM_BY[d.b].biome !== MAPV.filter ? 0.15 : 0.7})`;
    vctx.beginPath(); vctx.moveTo(ox + X(d.x0) * scale, oy + Y(d.y0) * scale); vctx.lineTo(ox + X(d.x1) * scale, oy + Y(d.y1) * scale); vctx.stroke();
  }
  vctx.restore();
  // ---- icons: only the essentials at the widest zoom
  const isz = MAPV.z === 0 ? 7 : MAPV.z === 1 ? 7 : 9, detail = MAPV.z > 0;
  for (const r of shown) {
    const a = dim(r) ? 0.25 : 1, info = I[r.id];
    if (detail) {
      for (const d of info.doors) mapIcon(MAP_ICON.door, X(d.x), Y(d.y) - 1, isz - 1, 0.85 * a);
      for (const q of info.passages) if (SEEN[q.key]) mapIcon(MAP_ICON.passage, X(q.x), Y(q.y) - 1, isz - 1, a);
      for (const t of info.trials) { const rec = TR[t.key]; mapIcon(rec && rec.gold ? MAP_ICON.trialGold : MAP_ICON.trial, X(t.x), Y(t.y) - 1, isz, rec && rec.clears ? a : 0.8 * a); }
      for (const q of info.gaunts) mapIcon(SAVE.flags[q.key] ? MAP_ICON.gauntDone : MAP_ICON.gaunt, X(q.x), Y(q.y) - 1, isz, a);
      for (const b of info.benches) if (VS[b.key] !== undefined) mapIcon(MAP_ICON.vista, X(b.x), Y(b.y) - 1, isz, a);
      const cx = X(r.gx + r.w / 2), cy = Y(r.gy + r.h / 2);
      if (r.puzzle) mapIcon(MAP_ICON.puzzle, cx, cy, isz, a);
      if (r.secret) mapIcon(MAP_ICON.secret, r.puzzle ? cx + isz : cx, cy, isz, a);
    }
    if (r.needs && !r.needs.every(n => n === 'start' || SAVE.items[n])) mapIcon(MAP_ICON.lock, X(r.gx + r.w) - isz / 2 - 1, Y(r.gy) + isz / 2 + 1, isz, a);
    if (r.shrine && SAVE.shrines.includes(r.id)) { const p = shrinePos(r.id); icon('shrine', X(p.x) - 4, Y(p.y) - 6, 8, a); }
    if (r.boss && MAIN_BOSSES.has(r.boss)) drawBossMark(X(r.gx + r.w / 2) - 4, Y(r.gy + r.h / 2) - 4, !!SAVE.flags['boss:' + r.boss], 8);
    else if (r.boss && !SAVE.flags['boss:' + r.boss]) icon('skull', X(r.gx + r.w / 2) - 4, Y(r.gy + r.h / 2) - 4, 8, a);
  }
  if (MAPV.z < 2) for (const [bio, L] of Object.entries(labels)) if (AREAS[bio]) text(AREAS[bio].name.replace(/^The /, ''), X(L.x / L.n), Y(L.y / L.n) + 2, MAPV.z ? 5 : 4.6, '#e8dcc0', 'center', { alpha: 0.72, weight: 500 });
  if (SAVE.remnant && ROOM_BY[SAVE.remnant.room] && vset.has(SAVE.remnant.room)) {
    const R = ROOM_BY[SAVE.remnant.room], rx = X(R.gx + SAVE.remnant.x / TILE), ry = Y(R.gy + SAVE.remnant.y / TILE);
    vctx.fillStyle = '#ff8050'; vctx.fillRect(ox + (rx - 1) * scale, oy + (ry - 2) * scale, 2 * scale, 2 * scale);
  }
  const pp = mapPlayerAt(), px = X(pp.x), py = Y(pp.y);
  vctx.beginPath(); vctx.arc(ox + px * scale, oy + py * scale, (3 + Math.sin(time * 6)) * scale, 0, 6.3); vctx.fillStyle = 'rgba(255,90,70,0.22)'; vctx.fill();
  vctx.fillStyle = Math.sin(time * 8) > 0 ? '#ff5050' : '#ffd0a0'; vctx.fillRect(ox + (px - 1.5) * scale, oy + (py - 1.5) * scale, 3 * scale, 3 * scale);
  // crosshair + what lies under it, once you've panned away from yourself
  const off = Math.hypot(MAPV.cx - pp.x, MAPV.cy - pp.y) * s > 6, under = vis.find(r => MAPV.cx >= r.gx && MAPV.cx < r.gx + r.w && MAPV.cy >= r.gy && MAPV.cy < r.gy + r.h);
  if (off) { const cx = bx + bw / 2, cy = by + bh / 2; vctx.fillStyle = 'rgba(245,227,176,0.8)'; for (const [dx, dy, w, h] of [[-5, -0.25, 3, 0.5], [2, -0.25, 3, 0.5], [-0.25, -5, 0.5, 3], [-0.25, 2, 0.5, 3]]) vctx.fillRect(ox + (cx + dx) * scale, oy + (cy + dy) * scale, w * scale, h * scale); }
  vctx.restore();
  // ---- header: zoom pips (left), region filter (right); info line; legend; footer
  text('ZOOM', 14, 19, 4.4, UIC.faint, 'left', { spacing: 1, weight: 600 });
  for (let i = 0; i < 3; i++) uiDiamond(38 + i * 6, 17.6, i === MAPV.z ? 1.7 : 1.1, i <= MAPV.z ? UIC.gold : '#4a3e2c');
  const fl = MAPV.filter ? sysRegionName(MAPV.filter).replace(/^The /, '') : 'All regions';
  text(`◂ ${fl} ▸`, 370, 19, 5, MAPV.filter ? UIC.gold : UIC.muted, 'right', { weight: 600 });
  const R = off ? under : room.def;
  if (R) {
    const tr = (I[R.id] || { trials: [] }).trials.map(t => TR[t.key]).find(Boolean);
    const extra = tr && tr.best ? `   ·   trial best ${sysFmt(tr.best)}${tr.gold ? ' ✦' : ''}` : '';
    text(`${R.name}  ·  ${sysRegionName(R.biome)}${extra}`, W / 2, by + bh - 5, 5.4, off ? UIC.hi : '#c9bda2', 'center', { weight: 400 });
  }
  let lx = 14; const ly = 196;
  const leg = (ic, label, sz = 7) => { mapIcon(ic, lx + 3.5, ly - 2, sz); text(label, lx + 9, ly, 4.6, UIC.dim, 'left', { weight: 500 }); lx += 16 + textW(label, 4.6, 500); };
  leg('shrine', 'Shrine', 8); leg(MAP_ICON.trial, 'Trial'); leg(MAP_ICON.trialGold, 'Under par'); leg(MAP_ICON.gaunt, 'Gauntlet'); leg(MAP_ICON.puzzle, 'Puzzle');
  leg(MAP_ICON.vista, 'Vista'); leg(MAP_ICON.secret, 'Secret'); leg(MAP_ICON.door, 'Door'); leg(MAP_ICON.lock, 'Locked');
  uiFooter([['←↑↓→', 'pan'], ['Enter', 'zoom'], ['Q', 'region'], ['Tab', 'close']]);
}

// ---- travel: see renderTravel / travelInput in 29_ui2.js (shrine list by region + zooming world map)

// ---- title / pause / death / ending
// keyboard quick reference (title screen + first page of Settings › Controls & techniques). Must match KEYMAP in 00_core.js.
// format: [keys, 'Name · detail · detail']
function controlsList() {   // built from the live key bindings, so the title screen and guide show the player's own keys
  const K = a => keysOf(a).join(' / ') || '—', o = a => keysOf(a)[0] || '—';
  return [[`${o('left')} ${o('right')}${keysOf('left')[1] ? ` / ${keysOf('left')[1]} ${keysOf('right')[1] || ''}` : ''}`, `Move · ${o('up')} / ${o('down')} aim up and down`, `Move · ${o('up')} / ${o('down')} aim`],
    [K('jump'), `Jump · hold for height · ${o('down')} + ${o('jump')} drops through thin floors`, 'Jump · hold higher'],
    [`${K('attack')} / click`, `Attack · combo · ${o('up')} strikes up · ${o('down')} in the air pogos`, 'Attack · combo'],
    [`${K('heavy')} / right-click`, 'Heavy · hold to charge · in the air: plunge', 'Heavy · hold to charge'],
    [K('roll'), 'Roll · invulnerable · in the air: dash', 'Roll · invulnerable'],
    [K('parry'), `Parry · then ${o('attack')} to riposte · shields: hold to block`, `Parry · then ${o('attack')} riposte`],
    [`${o('cast')} / ${o('spell')}`, `Spells · ${o('cast')} casts · ${o('spell')} switches spell`, 'Cast / switch spell'],
    [K('art'), 'Weapon art · hold to charge', 'Weapon art · hold to charge'],
    [`${o('heal')} / ${o('mana')}`, `Flasks · ${o('heal')} crimson (HP) · ${o('mana')} azure (FP)`, 'Crimson / azure flask'],
    [K('interact'), 'Interact · talk · pick up · rest at shrines', 'Interact · rest'],
    [K('hook'), 'Root Hook · grapple golden rings', 'Root Hook'],
    [`${o('down')} + ${o('heavy')}`, 'Cinder Slam · in the air', 'Cinder Slam (in the air)'],
    [`Esc${keysOf('pause').length ? ' / ' + K('pause') : ''}`, 'Menu · equipment, items, status, settings', 'Menu · keys in Settings'],
    [K('map'), 'Map', 'Map']];
}
let titleSel = 0;
function renderTitle() {
  vctx.fillStyle = 'rgba(6,4,10,0.55)'; vctx.fillRect(ox, oy, W * scale, H * scale);
  text('CINDERHOLLOW', W / 2, 52, 26, '#e6c77a', 'center', { spacing: 4, weight: 600 });
  text('Beneath the fallen Pale Root, the ash remembers.', W / 2, 68, 7, '#c9bda2', 'center', { weight: 400 });
  const sv = titleSave(), EN = (sv && sv.endings) || {}, nEnd = sv ? ['kindle', 'ash', 'true', 'venn'].filter(k => EN[k] || (k === 'true' && sv.flags && sv.flags.true_ending)).length : 0;
  if (sv && (sv.ngp || nEnd)) text(`Journey ${(sv.ngp || 0) + 1}  ·  Endings seen ${nEnd} / 4`, W / 2, 80, 5.8, '#9a8f78', 'center', { weight: 400 });
  const opts = titleOptions();
  opts.forEach((o, i) => {
    const y = 96 + i * 13, sel = i === titleSel;
    text((sel ? '— ' : '') + o + (sel ? ' —' : ''), W / 2, y, 8.5, sel ? '#f5e3b0' : '#9a8f78', 'center', { weight: sel ? 600 : 400 });
  });
  if (!matchMedia('(pointer: coarse)').matches) controlsList().forEach(([k, v], i, CONTROLS) => {
    const col = i % 2, row = Math.floor(i / 2), x = 70 + col * 170, y = 134 + row * 10;
    const short = CONTROLS[i][2] || v.split(' · ')[0];
    text(k, x, y, 5.5, '#e6c77a', 'right', { weight: 600 }); text(short, x + 6, y, uiFit(short, 150, 5.5, 4.5, 400), '#c9bda2', 'left', { weight: 400 });
  });
  if (!document.hasFocus() && !matchMedia('(pointer: coarse)').matches) text('Click the game to take control', W / 2, 210, 6, '#f1e6c8', 'center', { alpha: 0.6 + 0.4 * Math.sin(time * 3) });
}
let _ts = null, _tsT = -9;
function titleSave() { if (time - _tsT > 2) { _ts = loadGame(); _tsT = time; } return _ts; }
function titleOptions() { return hasSave() ? ['Continue', 'New Game'] : ['New Game']; }
function renderPause() {
  vctx.fillStyle = 'rgba(5,4,8,0.7)'; vctx.fillRect(ox, oy, W * scale, H * scale);
  text('PAUSED', W / 2, 40, 14, '#e8dcc0', 'center', { spacing: 3 });
  controlsList().forEach(([k, v], i) => { const y = 58 + i * 9; text(k, W / 2 - 10, y, 6, '#e6c77a', 'right'); text(v, W / 2, y, uiFit(v, 180, 6, 4.5, 400), '#c9bda2', 'left', { weight: 400 }); });
  text(`Level ${levelOf(SAVE.stats)} · Deaths ${SAVE.deaths} · ${fmtTime(SAVE.playTime)}`, W / 2, 184, 6.5, '#b8ab90', 'center', { weight: 400 });
  text('Esc resume · Backspace quit to title · N mute', W / 2, 198, 6, '#8a7f6a', 'center', { weight: 400 });
}
function fmtTime(s) { const m = Math.floor(s / 60), h = Math.floor(m / 60); return h ? `${h}h ${m % 60}m` : `${m}m ${Math.floor(s % 60)}s`; }
function renderDeath() {
  const a = clamp(stateT / 1.4, 0, 1);
  band(a);
  text('YOU DIED', W / 2, 116, 22 + a * 2, '#b3141e', 'center', { alpha: a, spacing: 4, weight: 500 });
}
function renderEnding() {
  const a = clamp(stateT / 2, 0, 1);
  vctx.fillStyle = `rgba(4,3,6,${0.85 * a})`; vctx.fillRect(ox, oy, W * scale, H * scale);
  const E = SAVE.ending, T = { kindle: ['THE ROOT REKINDLED', 'You sit upon the root throne, and the Pale Root glows again.', 'The Sunken Hallow is yours to wander.'],
    ash: ['THE ASH IS STILL', 'The last grace goes out. No one rules the Hallow now.', 'The Sunken Hallow is yours to wander.'],
    venn: ['THE EMBER UNBOUND', 'You carry the last flame of the Hallow.', 'Every other light has gone out.'] }[E] || ['THE ASH IS STILL', 'The Pale Sovereign falls, and the Root dims to embers.', 'The Sunken Hallow is yours to wander.'];
  text(T[0], W / 2, 60, 16, '#e6c77a', 'center', { alpha: a, spacing: 3 });
  const lines = [T[1], T[2], '',
    `Level ${levelOf(SAVE.stats)}   ·   Deaths ${SAVE.deaths}   ·   ${fmtTime(SAVE.playTime)}`, `Skills learned ${SAVE.skills.length} / ${skillMaxLearnable()}   ·   Secrets ${['C2s', 'K3s', 'H1', 'E1', 'A7'].filter(r => SAVE.visited[r]).length} / 5`,
    'To begin a new journey, sit upon the Pale Throne.', 'Thank you for playing Cinderhollow.'];
  lines.forEach((l, i) => text(l, W / 2, 86 + i * 12, 7, '#d8cdb4', 'center', { alpha: a, weight: 400 }));
  if (stateT > 2.5) text('Press Enter to keep exploring', W / 2, 190, 6.5, '#b8ab90', 'center', { alpha: clamp(stateT - 2.5, 0, 1) });
}

// fork partners exclude each other, so the most you can hold at once is fewer than the node count
function skillMaxLearnable() { return SKILLS.length - SKILLS.filter(k => k.excl && k.excl.length).length / 2; }
