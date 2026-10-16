// contact-sheet snapshots of one type's fatality in a real boss arena (+ before / after) and on a regular foe.
// window.__type (default longsword), window.__arena ([room, kind, x, y]), window.__at (fatality-clock ms to capture)
G.SAVE.flags['sc:seal'] = 1;
const TYPE = window.__type || 'longsword', AR = window.__arena || ['K4', 'omen', 6, 10];
const AT = window.__at || [60, 220, 380, 520, 560, 640, 760, 850, 880, 960, 1100, 1250, 1400, 1560];
const pos = {}, out = { type: TYPE, arena: AR[1] };
const shoot = async n => { E('bannerMsg = null; toasts.length = 0; areaCard = null; render()'); pos[n] = E('[Math.round((P.x - cam.x) * scale + ox), Math.round((P.y - cam.y) * scale + oy), scale]'); await snap(n); };
async function run(tag, setup) {
  W().reset(TYPE, 1); if (window.__prep) E(window.__prep); setup(); if (window.__prep) E(window.__prep); E('clearBuffer(); held.clear(); updateCamera(0, true); FAT.cine.name = null');
  await shoot(`${tag}_before`);
  W().tap('heavy', 1);
  if (E('P.state') !== 'fatality') return 'no start: ' + E('P.state');
  let i = 0, fr = 0;
  while (E('!!FAT.on') && fr++ < 600) { const t = E('FAT.on.t'); if (i < AT.length && t >= AT[i]) { await shoot(`${tag}_${String(i).padStart(2, '0')}_${AT[i]}`); i++; } W().frame(1); }
  W().frame(30); await shoot(`${tag}_after`);
  return E('FAT.last');
}
// 1. the boss arena
const [r, k, x, y] = AR;
delete G.SAVE.flags['boss:' + k]; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + k] = 1;
G.tp(r, x, y); W().frame(2);
const b = G.boss;
for (let i = 0; i < 300 && !b.active; i++) { E(`P.x += ${b.x < G.P.x ? -2 : 2}`); W().frame(1); }
W().frame(200);
out.boss = await run('boss', () => {
  E(`window.__q = (boss.parts || [boss]).filter(p => p.alive !== false && typeof p.stagger === 'function')[0] || boss; __q.stagger();`);
  for (let i = 0; i < 40; i++) { W().frame(1); if (E(`(() => { const q = __q; if (!q.critable()) return false; const side = P.x < q.x ? -1 : 1; P.y = q.floor ?? q.y; P.vy = 0; P.ground = true; P.x = q.x + side * Math.min((q.critRange || 34) - 8, 40); P.face = -side; P.state = 'idle'; P.anim.set('idle', true); return critTarget() === q; })()`)) break; }
});
// 2. a regular foe in its own room
G.SAVE.flags['boss:' + k] = 1; G.tp(r, x, y); W().frame(5);
out.foe = await run('foe', () => {
  E(`enemies = []; P.x = boss ? P.x : P.x; const e = makeEnemy('${window.__foe || 'hollow_soldier'}', P.x + P.face * 30, P.y, 'fx_snap'); enemies.push(e); e.breakStance(); window.__e = e;`); W().frame(3);
});
out.pos = pos;
return out;
