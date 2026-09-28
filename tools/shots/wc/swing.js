// WC: mid-swing screenshots per class (combo finisher, heavy, air attack) against a foe, plus hitstop / kick readings
await boot(); G.giveArmory(); G.grantTechniques(); G.SETTINGS.god = 1;
const F = G.feel, ev = F.ev, out = [];
const WPN = { sword: 'longsword', dagger: 'dagger', great: 'greatsword', spear: 'spear', katana: 'katana', staff: 'quarterstaff', shield: 'knight_shield', twin: 'twinfangs', scythe: 'antler_scythe', whip: 'headsman_chain' };
const only = (window.__only || Object.keys(WPN));
const foe = (type, dx) => ev(`(() => { for (const e of enemies) e.gone = true; enemies = enemies.filter(e => !e.gone); const e = new Enemy('${type}', P.x + P.face * ${dx}, P.y, 'wc_' + Math.random()); e.hp = e.maxHp = 99999; e.cool = 99; e.cfg = { ...e.cfg, stance: 1e9, poise: 1e9 }; enemies.push(e); return e.type; })()`);
const until = (fn, n = 90) => { for (let i = 0; i < n && !fn(); i++) G.step(1); };
const A = () => ev('ATK[P.state]');
const crops = {}; const shot = async n => { await snap(n); crops[n] = ev('[Math.round((P.x - cam.x) * 3), Math.round((P.y - cam.y) * 3)]'); };
for (const cls of only) {
  const id = WPN[cls]; G.SAVE.weapon = id; ev('refreshDerived()'); await ev('feelWsheet().img.decode()').catch(() => {});
  G.tp('R1', 20, 10); G.step(30); G.P.face = 1;
  foe(cls === 'great' ? 'grave_knight' : cls === 'staff' ? 'hf_golem' : 'hollow_soldier', 30);
  G.step(2);
  // combo to the finisher, snap its active frame
  const combo = ev('moveset().combo');
  let hs = [];
  for (let k = 0; k < combo.length; k++) {
    G.step(1, [], ['attack']);
    until(() => A() && G.P.anim.i >= A().active[0]);
    G.step(1); hs.push(+ev('hitstop').toFixed(3));
    if (k === combo.length - 1) { G.step(1); await shot(`${cls}_a_fin`); out.push(`${cls} fin state=${G.P.state} i=${G.P.anim.i} kick=${F.FEEL.kx.toFixed(2)},${F.FEEL.ky.toFixed(2)} trail=${F.FEEL.trail.length} sparks=${F.FEEL.sparks.length}`); }
    until(() => A() && G.P.anim.i > A().active[1]);
  }
  out.push(`${cls} combo hitstops ${hs.join(' ')}`);
  until(() => !A(), 120); G.step(20);
  // heavy (tap = uncharged) mid-swing
  G.step(1, [], ['heavy']); until(() => A() && G.P.anim.i >= A().active[0]); G.step(1); const hh = +ev('hitstop').toFixed(3); G.step(1);
  await shot(`${cls}_b_heavy`); out.push(`${cls} heavy ${G.P.state} hitstop=${hh}`);
  until(() => !A(), 120); G.step(30);
  // air attack mid-swing
  G.step(1, [], ['jump']); G.step(10); G.step(1, [], ['attack']); until(() => A() && G.P.anim.i >= A().active[0], 40); G.step(1);
  await shot(`${cls}_c_air`); out.push(`${cls} air ${G.P.state} ground=${G.P.ground}`);
  until(() => G.P.ground, 120); const sq = F.FEEL.sq; G.step(1); await shot(`${cls}_d_land`); out.push(`${cls} land sq=${sq.toFixed(2)}`);
  G.step(30);
}
return { out, crops };
