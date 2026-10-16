// Funeral Peal snapshots: the wind-up, the crown hold, the impact, the rings rolling both ways (a foe each side, an arrow
// swallowed), the charged ring; plus the Esc/Arsenal card with the icon. PNGs in the outdir; crop with tools/shots/v17/bell/crop.py.
G.tp('K4', 6, 10); W().frame(240);
const shot = async n => { E(`hitstop = 0; areaCard = null; try { bannerMsg = null; } catch (e) {} toasts.length = 0; window.__fplCam = [Math.round((P.x - cam.x) / W * 1000), Math.round((P.y - cam.y) / H * 1000)]; render()`); await snap(n); };
const go = () => {
  W().reset('bell', 1);
  for (let j = 0; j < 90 && !G.P.ground; j++) W().frame(1);
  E('P.vx = 0; P.vy = 0; P.face = 1; P.belNotes = []; P.belBuff = {}; MV.later = []; P.cds = {}; projectiles.length = 0');
  E("enemies = enemies.filter(e => !e.wmDummy && !e.fplT)");
  E(`for (const dx of [56, -62]) { const e = makeEnemy('hollow_soldier', P.x + dx, P.y, 'fps' + dx); e.hp = e.maxHp = 30000; e.fplT = true; e.y = P.y; e.face = dx > 0 ? -1 : 1; e.update = function (dt) { this.anim && this.anim.update && this.anim.update(dt); }; enemies.push(e); }`);
  W().frame(4);
};
const frames = [];
go(); W().down('art'); W().frame(1); W().up('art');
for (let f = 1; f <= 60; f++) { W().frame(1); if ([6, 14, 20, 23, 27, 32, 38, 46].includes(f)) { await shot('tap_' + String(f).padStart(2, '0')); frames.push(f + ':' + E("P.state + '/' + P.anim.tag + '#' + P.anim.i")); } }
go();
W().down('art'); for (let f = 1; f <= 75; f++) { W().frame(1); if (f === 60) await shot('hold_crown'); } W().up('art');
for (let f = 1; f <= 40; f++) { if (f === 8) E("projectiles.push({ owner: 'enemy', kind: 'arrow', x: P.x + 120, y: P.y - 12, vx: -140, vy: 0, dmg: 10, life: 3, r: 3, t: 0, id: 99992 })"); W().frame(1); if ([10, 16, 22, 30].includes(f)) await shot('hold_' + String(f).padStart(2, '0')); }
return { cam: E('window.__fplCam'), frames, notes: E('belNotes().join("")') };
