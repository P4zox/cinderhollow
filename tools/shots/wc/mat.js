// WC: impact sparks by material (target) and element (weapon), snapped two frames after the hit
await boot(); G.giveArmory(); G.grantTechniques(); G.SETTINGS.god = 1;
const F = G.feel, ev = F.ev, out = [], crops = {};
const foe = (type, dx) => ev(`(() => { for (const e of enemies) e.gone = true; enemies = enemies.filter(e => !e.gone); const e = new Enemy('${type}', P.x + P.face * ${dx}, P.y, 'wc_' + Math.random()); e.hp = e.maxHp = 99999; e.cool = 99; e.cfg = { ...e.cfg, stance: 1e9, poise: 1e9 }; enemies.push(e); return e.type; })()`);
const until = (fn, n = 90) => { for (let i = 0; i < n && !fn(); i++) G.step(1); };
const A = () => ev('ATK[P.state]');
const cases = [['longsword', 'grave_knight'], ['longsword', 'cm_gargoyle'], ['longsword', 'gloom_wisp'], ['longsword', 'rot_hulk'], ['longsword', 'hf_golem'],
  ['colossus_hammer', 'hollow_soldier'], ['frostbrand', 'hollow_soldier'], ['oathbrand', 'hollow_soldier'], ['kalden', 'hollow_soldier'], ['vael_greatsword', 'rot_hulk'], ['orrery_whip', 'grave_knight'], ['sanguine_rapier', 'rot_hulk']];
let i = 0;
for (const [w, t] of cases) {
  G.SAVE.weapon = w; ev('refreshDerived()'); await ev('feelWsheet().img.decode()').catch(() => {});
  G.tp('R1', 20, 10); G.step(30); G.P.face = 1; foe(t, 28); G.step(2);
  ev('FEEL.swingHit = 0');
  G.step(1, [], ['attack']); until(() => ev('FEEL.swingHit') > 0 || (A() && G.P.anim.i > A().active[1]), 40); for (let k = 0; k < 20 && ev('hitstop') > 0; k++) G.step(1); G.step(5);
  const nm = `m${String(i++).padStart(2, '0')}_${w}_${t}`; await snap(nm); crops[nm] = ev('[Math.round((P.x - cam.x) * 3), Math.round((P.y - cam.y) * 3)]');
  out.push(`${w} -> ${t}: mat=${ev('feelMat(enemies[0])')} sparks=${ev('FEEL.sparks.length')} flashes=${ev('FEEL.flashes.length')} parts=${ev('particles.filter(p=>!p.amb).map(p=>p.kind).join(",")').slice(0, 120)}`);
  G.step(40);
}
return { out, crops };
