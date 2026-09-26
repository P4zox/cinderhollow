// Dying to a boss: respawn at the shrine, the boss is back at full health with no repeat intro, fog down until it wakes.
await boot(); G.give({ stats: { vig: 10 } });
const out = [];
for (const [kind, room, tx, ty, shrine] of [['executioners', 'NV5', 30, 10, 'NV2'], ['vael', 'NV7', 40, 12, 'NV6']]) {
  delete G.SAVE.flags['boss:' + kind]; G.SAVE.flags['cut:' + kind] = 1; G.SAVE.shrine = shrine;
  G.tp(room, tx, ty); const b = G.boss; b.activate(); G.step(5);
  for (let i = 0; i < 3000 && G.state !== 'dead'; i++) { const t = (b.parts || [b])[0]; G.step(1, Math.abs(t.x - G.P.x) > 40 ? [t.x < G.P.x ? 'left' : 'right'] : []); }
  const died = G.state === 'dead';
  for (let i = 0; i < 400 && G.state !== 'play'; i++) G.step(5);
  const at = G.room;
  G.tp(room, tx, ty); G.step(10);
  const b2 = G.boss;
  out.push(`${kind}: died ${died}, respawned in ${at} (shrine ${shrine}), boss back ${!!b2 && b2 !== b} hp ${b2 && Math.round(b2.hp)}/${b2 && b2.maxHp} active ${b2 && b2.active} state ${G.state}`);
}
return out;
