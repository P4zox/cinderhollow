// Dodgeability: a player who rolls on each telegraph takes far fewer hits than one who just stands and swings.
await boot(); G.give({ stats: { vig: 60, end: 60 } });
const out = []; window.__nvLog = [];
const trial = async (kind, room, tx, roll) => {
  delete G.SAVE.flags['boss:' + kind]; G.SAVE.flags['cut:' + kind] = 1; G.SAVE.flags['cutp2:vael'] = 1;
  G.tp(room, tx, room === 'NV7' ? 12 : 10); const b = G.boss; b.activate(); G.step(5);
  let hits = 0, atks = 0, lastAtk = null;
  for (let i = 0; i < 1500; i++) {
    const parts = (b.parts || [b]).filter(q => q.alive !== false && q.x !== undefined);
    const near = parts.sort((a, c) => Math.abs(a.x - G.P.x) - Math.abs(c.x - G.P.x))[0] || b;
    const d = near.x < G.P.x ? 'left' : 'right';
    let tap = [];
    const hold = Math.abs(near.x - G.P.x) > 70 ? [d] : [];
    if (roll) for (const q of parts) if (q.state === 'attack' && q.anim && q.anim.changed) {
      const w = (q.sh.meta.attacks || {})[q.atk]; const win = w ? (w.windows ? w.windows : [w]) : [];
      if (win.some(x => x.active[0] - 1 === q.anim.i) && Math.abs(q.x - G.P.x) < 180) tap = ['roll'];
    }
    for (const q of parts) if (q.state === 'attack' && q.atkId !== q.__seen) { q.__seen = q.atkId; atks++; }
    const prev = G.P.hp; G.step(1, tap.length ? [d] : hold, tap.length ? tap : (!roll && i % 20 === 0 && !hold.length ? ['attack'] : []));
    if (G.P.hp < prev) hits++;
    G.P.hp = 9999; G.P.st = 999;
  }
  const log = window.__nvLog.splice(0); return `${kind} ${roll ? 'ROLLING' : 'standing'}: ${hits} hits over ${atks} attacks ` + JSON.stringify(log);
};
out.push(await trial('executioners', 'NV5', 20, false));
out.push(await trial('executioners', 'NV5', 20, true));
out.push(await trial('vael', 'NV7', 30, false));
out.push(await trial('vael', 'NV7', 30, true));
return out;
