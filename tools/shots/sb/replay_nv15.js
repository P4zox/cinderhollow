G.SAVE.items.emberdash = 1; G.tp('NV15', 51, 12); for (let i = 0; i < 6; i++) { G.step(20); settle(); }
const plan = PLAN.split(' ').map(t => { const [h, tp] = t.split('!'); return [h === '_' ? [] : h.split('+'), tp ? tp.split('+') : []]; });
const out = []; const r0 = S.SYS.result;
for (let rep = 0; rep < 2; rep++) {
  G.step(1, [], ['interact']); G.step(1); const a0 = S.SYS.trial.attempts;
  let i = 0;
  for (; i < plan.length; i++) { G.step(1, plan[i][0], plan[i][1]); if (!S.SYS.trial || S.SYS.trial.attempts !== a0) break; if (i % 40 === 0) out.push(rep + ':' + i + ' ' + (G.P.x|0) + ',' + (G.P.y|0) + ' ' + G.P.state); }
  out.push('rep ' + rep + ' ended at ' + i + '/' + plan.length + ' trial ' + !!S.SYS.trial + ' why ' + (S.SYS.trial && S.SYS.trial.why) + ' pos ' + (G.P.x|0) + ',' + (G.P.y|0));
  for (let k = 0; k < 120 && S.SYS.trial; k++) G.step(1, ['left']);
  out.push('  after walk: result ' + JSON.stringify(S.SYS.result && S.SYS.result !== r0 && { t: S.SYS.result.time, gold: S.SYS.result.gold }) + ' pos ' + (G.P.x|0) + ',' + (G.P.y|0));
  if (S.SYS.result && S.SYS.result !== r0) break;
}
for (let i = 0; i < 260; i++) G.step(1);
out.push('charm ' + G.SAVE.charms.includes('c_x3_hood') + ' rec ' + JSON.stringify(S.x3().trials));
await snap('nv15_done');
return out;
