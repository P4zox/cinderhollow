// NH14 Security Lockdown: run the gauntlet (foes are struck down by the harness), check the shutter and rewards
await boot(); G.grantTechniques(); G.SETTINGS.god = 1;
G.tp('NH14', 18, 14); G.step(30); G.xs.clean();
const S = window.__sys.SYS, K = id => G.xs.KIT.byId[id], out = [];
out.push('shutter open before: ' + K('shut').on);
G.step(1, [], ['interact']); G.step(90);
out.push('running ' + !!S.gaunt + ' shutter ' + K('shut').on + ' enemies ' + G.enemies.filter(e => e.alive).length);
await snap('g14_a');
for (let w = 0; w < 8 && S.gaunt; w++) {
  for (let i = 0; i < 200 && G.enemies.filter(e => e.alive).length === 0 && S.gaunt; i++) G.step(1);
  out.push(`wave ${S.gaunt && S.gaunt.wave} foes ${G.enemies.filter(e => e.alive).map(e => e.type).join(',')}`);
  if (w === 1) await snap('g14_b');
  for (const e of G.enemies) if (e.alive) { e.hp = 0; e.die({ dir: 1 }); }
  G.step(120);
}
G.step(300); await new Promise(r => setTimeout(r, 600)); G.step(5);
out.push('done ' + !S.gaunt + ' flag ' + !!G.SAVE.flags['x3:NH14:lock'] + ' shutter ' + K('shut').on + ' inv ' + JSON.stringify(G.SAVE.inv) + ' shards ' + G.SAVE.shards);
return out;
