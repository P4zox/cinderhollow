await boot(); G.grantTechniques(); G.SAVE.items.talon = 1; G.SAVE.seenAreas = { thornveil: 1 };
const o = [];
for (const [x, y] of [[60, 5], [82, 10]]) {
  G.tp('TV9', x, y); G.SETTINGS.god = 0; G.P.hp = 99999; G.P.inv = 0;
  for (let f = 0; f < 18; f++) { for (const e of G.enemies) e.alive && e.die && e.die({ dir: 1 }); const h0 = G.P.hp; G.step(10); if (G.P.hp < h0) o.push(`${x},${y} f${f} -${h0 - G.P.hp} enemies ${G.enemies.filter(e => e.alive).map(e => e.type + '@' + (e.x / 16).toFixed(1) + ',' + (e.y / 16).toFixed(1))} pods ${G.props.filter(p => p.type === 'tv_pod').map(p => (p.x / 16).toFixed(1) + ',' + (p.y / 16).toFixed(1) + ':' + p.st)} proj ${G.props.length}`); }
}
return o;
