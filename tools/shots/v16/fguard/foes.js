// fguard: the three guard-group fatalities on regular foes with real input (K on a stance-broken foe):
// 8 x AR on a tough foe, the execute rule on a weak one, the spear hoist (target rides the tip, lands after), the variant
// chosen (hoist on small foes, vault on elites / bosses), invulnerability, clean end, acts after.
G.SAVE.flags['sc:seal'] = 1;
const out = {};
const runOut = (watch) => { let f = 0; while (E('!!FAT.on') && f++ < 500) { W().frame(1); if (watch) watch(f); } return f; };
G.SAVE.flags['boss:omen'] = 1;
for (const ty of ['sns', 'spear', 'bow']) {
  const res = {};
  for (const mode of ['tough', 'weak', 'elite']) {
    try {
      G.tp('K4', 6, 10); W().frame(30); W().reset(ty, 1); for (let j = 0; j < 60 && !G.P.ground; j++) W().frame(1);
      E(`enemies = []; const e = makeEnemy('hollow_soldier', P.x + 30, P.y, 'fg_${ty}_${mode}'); enemies.push(e); window.__t = e;
         if ('${mode}' === 'tough') e.hp = e.maxHp = 30000; if ('${mode}' === 'elite') { e.cfg = { ...e.cfg, elite: true }; e.hp = e.maxHp = 30000; }
         e.breakStance();`);
      W().frame(2);
      const t0 = E('({ x: __t.x, y: __t.y, hp: __t.hp })');
      E('clearBuffer(); held.clear()'); W().tap('heavy', 1);
      const r = { start: E('P.state') === 'fatality', variant: E('FAT.on && FAT.on.variant'), tag: E('P.anim.tag') };
      let maxLift = 0, inv = null, minPy = 1e9;
      runOut(f => {
        maxLift = Math.max(maxLift, E(`__t.alive !== false ? ${t0.y} - __t.y : 0`)); minPy = Math.min(minPy, E('P.y'));
        if (f === 25) inv = E(`(() => { const h = P.hp; hurtPlayer(9999, 1, 'x', {}); return P.hp === h; })()`);
      });
      W().frame(3);
      const L = E('FAT.last');
      r.ratio = +(L.dealt / L.unit).toFixed(2); r.exec = L.exec; r.beats = L.beats.map(b => b.got); r.inv = inv;
      r.maxLift = Math.round(maxLift); r.playerRose = Math.round(E('P.y') - minPy);
      r.dead = E('__t.alive === false || __t.hp <= 0');
      W().frame(40);
      r.landed = E('__t.alive === false || __t.ground !== false'); r.footY = Math.round(E('__t.y') - t0.y);
      r.end = E('P.state'); r.held = !!E('__t._fatHold');
      // acts after: a J starts an attack
      W().tap('attack', 1); W().frame(2); r.actsAfter = E('P.state') !== 'idle';
      res[mode] = r;
    } catch (e) { res[mode] = 'EXC ' + e.message; }
  }
  out[ty] = res;
}
out.pass = ['sns', 'spear', 'bow'].every(ty => { const r = out[ty]; return r.tough.start && Math.abs(r.tough.ratio - 8) < 0.05 && r.weak.exec && r.weak.dead && r.tough.end === 'idle' && r.tough.inv && !r.tough.held && r.tough.actsAfter; })
  && out.spear.tough.variant === 'hoist' && out.spear.tough.maxLift > 10 && out.spear.elite.variant === 'vault' && out.spear.elite.maxLift === 0 && out.spear.tough.landed;
return out;
