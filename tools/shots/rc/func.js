// RC mechanics: the sluice puzzle (wrong + right), the egg -> Ember Hatchling, the spell in a fight, gauntlets, gates, charms
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.talon = 1; const S = window.__sys, X = G.xrc, log = [];
const wait = n => { for (let i = 0; i < n; i++) G.step(1); };
// ---- Slag Sluices
G.tp('D13', 30, 4); wait(30); await snap('f_sluice_0');
const Q = () => X.XRC.sluice, st = () => Q().molds.map(m => m.st[0]).join('') + ' m' + Q().measures;
X.pour(1); wait(200); log.push('grave first: ' + st());
X.pour(0); wait(200); log.push('flame before ox (cracks): ' + st());
X.pour(2); wait(200); log.push('ox: ' + st());
X.pour(3); wait(60); log.push('spent? ' + st());
X.quench(); wait(30); log.push('quenched: ' + st());
X.pour(2); wait(200); await snap('f_sluice_ox'); X.pour(3); wait(200); X.pour(0); wait(220); log.push('ox,hammer,flame: ' + st() + ' solved ' + Q().solved + ' flag ' + G.SAVE.flags['x3:D13:sluice']);
await snap('f_sluice_solved');
// climb the stair: floor -> ox -> hammer -> flame -> reliquary ledge
G.tp('D13', 12, 16); wait(20); log.push('standing on the ox at ' + (G.P.y / 16).toFixed(1) + ' ground ' + G.P.ground);
G.tp('D13', 3, 7); wait(20); const sh0 = G.SAVE.shards; const rel = G.props.find(p => p.type === 'xrc_reliquary'); rel.interact(); wait(30);
log.push('reliquary: shards ' + sh0 + ' -> ' + G.SAVE.shards);
G.tp('D10', 30, 11); wait(10); G.tp('D13', 30, 4); wait(20); log.push('re-entry keeps the stair: ' + st());
// ---- the egg
G.tp('LF1', 100, 17); wait(40); await snap('f_egg_0');
X.hatch(); for (let k = 0; k < 6; k++) { wait(30); await snap('f_egg_' + (k + 1)); }
wait(200); log.push('spell owned: ' + G.SAVE.spellsOwned.includes('ember_hatchling') + ' eq ' + G.SAVE.spellsEq.join(',') + ' flag ' + G.SAVE.flags['xrc:egg'] + ' state ' + G.state);
for (let i = 0; i < 5 && G.state !== 'play'; i++) { G.step(1, [], ['interact']); wait(10); G.step(1, [], ['pause']); wait(10); }
// ---- the cub in a fight
G.SAVE.spell = 'ember_hatchling'; if (!G.SAVE.spellsEq.includes('ember_hatchling')) G.SAVE.spellsEq.unshift('ember_hatchling');
G.tp('D10', 20, 11); wait(20); G.P.fp = 999;
const e0 = G.enemies.filter(e => e.alive).map(e => e.type + ':' + e.hp);
G.step(1, [], ['cast']); wait(30); await snap('f_cub_1');
for (let i = 0; i < 12; i++) { wait(20); if (i === 5) await snap('f_cub_2'); }
log.push('cub: ' + JSON.stringify(e0) + ' -> ' + JSON.stringify(G.enemies.map(e => e.type + ':' + e.hp)) + ' cub ' + !!X.XRC.cub);
wait(400); log.push('after 10 s cub gone: ' + !X.XRC.cub);
// ---- gauntlets
for (const [r, x, y] of [['D14', 22, 10], ['D15', 19, 12], ['X10', 34, 11]]) {
  G.tp(r, x, y); wait(40); G.step(1, [], ['interact']); wait(30);
  let waves = 0, names = [];
  for (let w = 0; w < 3; w++) {
    for (let i = 0; i < 300 && S.SYS.gaunt && S.SYS.gaunt.state !== 'wave'; i++) G.step(1);
    wait(90); names.push(G.enemies.filter(e => e.alive && e.x3g).map(e => e.type).join('+'));
    if (w === 2) await snap('f_gaunt_' + r);
    for (const e of G.enemies) if (e.alive && e.x3g) e.die({ dir: 1 });
    waves++; wait(90);
  }
  wait(400);
  log.push(`${r}: ${names.join(' | ')} cleared ${G.SAVE.flags['x3:' + r + ':g1']} es ${G.SAVE.inv.emberstone || 0} shards ${G.SAVE.shards}`);
}
// ---- the one-way shortcut gates
for (const [r, lx, ly, gid] of [['SP11', 37, 3, 'sg'], ['SP13', 8, 45, 'stg'], ['D12', 58, 7, 'bg'], ['X9', 50, 11, 'pg']]) {
  G.tp(r, lx, ly); wait(20); const b = S.kitOn ? S.kitOn(gid) : null;
  G.step(1, [], ['interact']); wait(60);
  const k = X.kit(); log.push(`${r} gate ${gid}: ${JSON.stringify(k.byId[gid] && { open: k.byId[gid].on ?? k.byId[gid].open })} flag ${G.SAVE.flags['x3:' + r + ':' + gid]}`);
}
return log;
