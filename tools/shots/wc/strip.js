// WC: frame-by-frame strips of one swing per class (ribbon over time) + an air->down attack landing (dust, squash)
await boot(); G.giveArmory(); G.grantTechniques(); G.SETTINGS.god = 1;
const F = G.feel, ev = F.ev, crops = {}, out = [];
const WPN = window.__wpn || { sword: 'longsword', great: 'greatsword', katana: 'katana', whip: 'headsman_chain', staff: 'quarterstaff', scythe: 'antler_scythe' };
const until = (fn, n = 90) => { for (let i = 0; i < n && !fn(); i++) G.step(1); };
const A = () => ev('ATK[P.state]');
const shot = async n => { await snap(n); crops[n] = ev('[Math.round((P.x - cam.x) * 3), Math.round((P.y - cam.y) * 3)]'); };
for (const [cls, id] of Object.entries(WPN)) {
  G.SAVE.weapon = id; ev('refreshDerived()'); await ev('feelWsheet().img.decode()').catch(() => {});
  G.tp('R1', 20, 10); G.step(30); G.P.face = 1;
  const which = window.__heavy ? 'heavy' : 'attack';
  G.step(1, [], [which]); until(() => A() && G.P.anim.i >= A().active[0] - 1);
  for (let k = 0; k < 7; k++) { await shot(`${cls}_${k}`); G.step(2); }
  out.push(cls + ' ' + ev('FEEL.trail.length'));
}
if (!window.__heavy) {   // landing after a down attack
  G.SAVE.weapon = 'longsword'; ev('refreshDerived()'); G.tp('R1', 20, 10); G.step(30);
  G.step(1, [], ['jump']); G.step(14); G.step(1, ['down'], ['attack']); until(() => G.P.ground, 120);
  for (let k = 0; k < 5; k++) { await shot(`zland_${k}`); out.push('sq ' + F.FEEL.sq.toFixed(2) + ' ky ' + F.FEEL.ky.toFixed(2)); G.step(2); }
}
return { out, crops };
