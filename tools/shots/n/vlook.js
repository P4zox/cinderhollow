window.__errs = []; console.error = (...a) => { if (window.__errs.length < 5) window.__errs.push(String(a[0] && a[0].stack || a[0]).slice(0, 300)); };
await boot(); G.give({ stats: { vig: 60 } });
for (const k of ['boss:vael']) delete G.SAVE.flags[k]; G.SAVE.flags['cut:vael'] = 1; G.SAVE.flags['cutp2:vael'] = 1; delete G.SAVE.flags['cutp3:vael'];
G.tp('NV7', 30, 12); const b = G.boss; b.activate(); G.step(5);
const seen = {};
const run = async (n, tag) => { for (let i = 0; i < n; i++) { G.step(1, Math.abs(b.x - G.P.x) > 110 ? [b.x < G.P.x ? 'left' : 'right'] : []); G.P.hp = 9999;
  if (G.state === 'cut') { await snap(`vl_${tag}_cut_${i}`); for (let k = 0; k < 600 && G.state === 'cut'; k++) { G.step(2); if (k % 60 === 30) await snap(`vl_${tag}_cut_${i}_${k}`); } }
  const key = b.state === 'attack' ? b.atk : null; if (key && !seen[tag + key] && b.anim.i >= 3) { seen[tag + key] = 1; await snap(`vl_${tag}_${key}`); } } };
await run(900, 'p1');
b.hp = b.maxHp * 0.6; await run(900, 'p2');
b.hp = b.maxHp * 0.25; await run(1200, 'p3');
return [Object.keys(seen).join(','), JSON.stringify(window.__errs)];
