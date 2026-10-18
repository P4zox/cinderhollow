// ------------------------------------------------------------------ Cheats › Teleport to a room
// Esc › Settings › Cheats (test) › Teleport: every unique room of the world (test and training rooms left out), grouped
// by region, plus four quick lists (Vistas, Secrets, Bosses, Shrines). ←→ group, ↑↓ room, Enter goes there. You land
// on the room's shrine, bench or start mark, else on the safe floor nearest its middle. Like the other cheats, using it
// in a real journey marks the save ✦ Cheated (68_integrity.js).
CHEAT_ROWS.push({ k: 'tp', label: 'Teleport to a room', desc: 'Jump to any room: every region, secret, vista, boss arena and shrine.' });

const TP = { groups: null };
function tpTags(d) {
  const t = [];
  if ((d.spawns || []).some(s => s.t === 'boss')) t.push('boss');
  if (d.shrine) t.push('shrine');
  if (d.vista) t.push('vista');
  if (d.secret) t.push('secret');
  return t;
}
function tpGroups() {
  if (TP.groups) return TP.groups;
  const rooms = ROOMS.filter(d => !d.test && !/^T\d|^TR\d/.test(d.id) && AREAS[d.biome]);
  const regions = [], by = {};
  for (const d of rooms) { if (!by[d.biome]) { by[d.biome] = []; regions.push(d.biome); } by[d.biome].push(d); }
  const quick = [['Vistas', 'vista'], ['Secrets', 'secret'], ['Bosses', 'boss'], ['Shrines', 'shrine']]
    .map(([name, tag]) => ({ name, quick: true, rooms: rooms.filter(d => tpTags(d).includes(tag)) })).filter(g => g.rooms.length);
  TP.groups = quick.concat(regions.map(b => ({ name: AREAS[b].name, rooms: by[b] })));
  return TP.groups;
}
// where to stand: the shrine, then a bench, then the start mark 'P', else the safe floor nearest the room's middle
function tpSpot(def) {
  for (const ch of ['S', 'P']) for (let y = 0; y < def.h; y++) { const x = def.map[y].indexOf(ch); if (x >= 0) return [x * TILE + 8, (y + 1) * TILE]; }
  const b = (def.spawns || []).find(s => s.kind === 'bench'); if (b) return [b.x * TILE + 8, (b.y + 1) * TILE];
  return null;
}
function tpSafeFloor() {   // run after enterRoom: the built room's tiles say what is solid
  const free = (x, y) => x >= 0 && y >= 0 && x < room.def.w && y < room.def.h && !isSolidT(tileAt(x, y)) && tileAt(x, y) !== T_SPIKE && tileAt(x, y) !== T_SPIKE_D;
  const floor = (x, y) => y + 1 < room.def.h && (isSolidT(tileAt(x, y + 1)) || tileAt(x, y + 1) === T_PLAT);
  const cx = room.def.w / 2, cy = room.def.h / 2; let best = null, bd = 1e9;
  for (let y = 1; y < room.def.h - 1; y++) for (let x = 1; x < room.def.w - 1; x++) {
    if (!free(x, y) || !free(x, y - 1) || !floor(x, y)) continue;
    if (typeof unsafeAt === 'function' && unsafeAt(x * TILE + 8, (y + 1) * TILE)) continue;
    const dd = Math.abs(x - cx) + Math.abs(y - cy) * 0.6; if (dd < bd) { bd = dd; best = [x * TILE + 8, (y + 1) * TILE]; }
  }
  return best;
}
function tpGo(def) {
  if (typeof markCheated === 'function') markCheated();
  menu = null; state = 'play'; clearBuffer(); boss = null;
  // it's a cheat: the room's own requirements come with it (a flooded room needs Tidebreath, or you float out of it)
  for (const k of def.needs || []) if (SAVE.items[k] === undefined || !SAVE.items[k]) SAVE.items[k] = 1;
  if (def.map.some(r => r.includes('"'))) SAVE.items.tidebreath = 1;
  const s = tpSpot(def);
  enterRoom(def.id, s ? s[0] : 64, s ? s[1] : 64, { card: true });
  if (!s) { const f = tpSafeFloor(); if (f) { P.x = f[0]; P.y = f[1]; P.safe = { x: f[0], y: f[1] }; } }
  P.vx = 0; P.vy = 0; P.inv = Math.max(P.inv || 0, 1.0); setP('idle', 'idle', true); updateCamera(0, true);
  SAVE.visited[def.id] = 1; sfx.kindle(); toast('Teleported · ' + def.name, 2.5);
}

{ const _ss = settingsSubInput;
  settingsSubInput = function (M, a) {   // eslint-disable-line no-func-assign
    const S = M.sub, conf = ['confirm', 'interact', 'attack', 'jump'].includes(a);
    if (S && S.kind === 'cheats' && conf && CHEAT_ROWS[S.sel] && CHEAT_ROWS[S.sel].k === 'tp') {
      M.sub = { kind: 'tp', g: 0, sel: 0, off: 0, back: S }; sfx.menu(); return;
    }
    if (!S || S.kind !== 'tp') return _ss.apply(this, arguments);
    const G = tpGroups(), grp = G[S.g], n = grp.rooms.length;
    if (['pause', 'back', 'heavy'].includes(a)) { M.sub = S.back; sfx.menu(); return; }
    if (a === 'left' || a === 'right') { S.g = (S.g + (a === 'left' ? G.length - 1 : 1)) % G.length; S.sel = 0; S.off = 0; sfx.menu(); return; }
    if (a === 'up') { S.sel = (S.sel + n - 1) % n; sfx.menu(); return; }
    if (a === 'down') { S.sel = (S.sel + 1) % n; sfx.menu(); return; }
    if (conf && grp.rooms[S.sel]) tpGo(grp.rooms[S.sel]);
  }; }
{ const _rs = renderSettingsSub;
  renderSettingsSub = function (M) {   // eslint-disable-line no-func-assign
    const S = M.sub; if (!S || S.kind !== 'tp') return _rs.apply(this, arguments);
    const G = tpGroups(), grp = G[S.g], rows = grp.rooms, vis = 10, rh = 13, px = 46, pw = 292, top = 44;
    uiBackdrop(0.9); uiStrips();
    uiTitle('TELEPORT', 17, 9);
    text('◂  ' + grp.name + (grp.quick ? '  (all regions)' : '') + '  ▸', W / 2, 32, 6.6, UIC.gold, 'center', { weight: 600 });
    text(`${S.g + 1} / ${G.length}`, px + pw - 4, 32, 5, '#8a7f6a', 'right');
    uiHit(px, 25, 40, 11, () => {}, () => uiAct('left')); uiHit(px + pw - 40, 25, 40, 11, () => {}, () => uiAct('right'));
    S.off = clamp(S.off, Math.max(0, S.sel - vis + 1), Math.min(S.sel, Math.max(0, rows.length - vis)));
    panel(px, top, pw, 8 + vis * rh);
    const TAGC = { boss: '#e07060', shrine: '#ffd070', vista: '#9fd0ff', secret: '#c79bff' };
    for (let r = 0; r < vis && S.off + r < rows.length; r++) {
      const i = S.off + r, d = rows[i], y = top + 14 + r * rh, sel = i === S.sel;
      if (sel) uiSel(px + 4, y - 9, pw - 8, rh - 1);
      uiHit(px + 4, y - 9, pw - 8, rh - 1, () => { S.sel = i; }, () => { S.sel = i; uiAct('confirm'); });
      text(d.id, px + 12, y, 5.4, sel ? '#f5e3b0' : '#8a7f6a', 'left', { weight: 600 });
      text(d.name + (grp.quick ? '  ·  ' + AREAS[d.biome].name : ''), px + 44, y, 6.2, sel ? '#f5e3b0' : '#d8cdb4', 'left', { weight: sel ? 600 : 400 });
      let tx = px + pw - 10;
      for (const t of tpTags(d).reverse()) { text(t, tx, y, 4.8, TAGC[t], 'right', { weight: 600, spacing: 0.6 }); tx -= 26; }
    }
    if (rows.length > vis) text(`${S.sel + 1} / ${rows.length}`, px + pw / 2, top + 18 + vis * rh, 5, '#8a7f6a', 'center');
    uiFooter([['←→', 'region'], ['↑↓', 'room'], ['Enter', 'go'], ['Esc', 'back']]);
  }; }
Object.assign(window.__game, { tp_groups: tpGroups, tp_go: id => tpGo(ROOM_BY[id]) });
