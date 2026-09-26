await boot(); G.grantTechniques(); G.give({ items: { talon: 1 } }); const o = [];
G.SAVE.flags['boss:scarab'] = 1; G.SAVE.flags['boss:pharaoh'] = 1;
const pos = () => [G.room, Math.round(G.P.x/16*10)/10, Math.round(G.P.y/16*10)/10, G.P.state, Math.round(G.P.hp)].join(' ');
// god mode so enemies don't interfere with traversal checks
G.SAVE.settingsGod = 1;
async function walk(dir, maxSteps, stopRoom, label) {
  const key = dir > 0 ? 'right' : 'left'; let lastX = G.P.x, stuck = 0, start = G.room;
  for (let i = 0; i < maxSteps; i++) {
    for (const e of G.enemies) if (e.alive) { e.hp = 0; e.state = 'dead'; }
    const sand = G.P.duSand >= 0 && G.P.duSand > 6;
    const jmp = stuck > 6 || sand;
    G.step(2, [key, ...(jmp ? ['jump'] : [])], jmp ? ['jump'] : []);
    if (G.P.hp < 60) { o.push(label + ' lowhp ' + pos()); G.P.hp = G.D.maxHp; }
    if (Math.abs(G.P.x - lastX) < 0.5) stuck++; else stuck = 0;
    lastX = G.P.x;
    if (G.room !== start && (!stopRoom || G.room === stopRoom)) { o.push(label + ' -> ' + pos() + ' i' + i); return true; }
  }
  o.push(label + ' FAIL ' + pos()); await snap('fail_' + label); return false;
}
G.tp('DU2', 3, 10); G.step(10);
await walk(1, 600, 'DU3', 'DU2 east');
await walk(1, 900, 'DU4', 'DU3 east');
G.tp('DU3', 60, 14); G.step(5); G.P.hp = G.D.maxHp;
await walk(-1, 900, 'DU2', 'DU3 west');
await walk(-1, 600, 'DU1', 'DU2 west');
G.tp('DU5', 68, 11); G.step(5);
await walk(-1, 900, 'DU6', 'DU5 west');
await walk(-1, 600, 'DU7', 'DU6 west');
G.tp('DU7', 20, 17); G.step(5);
await walk(1, 600, 'DU6', 'DU7 east');
await walk(1, 600, 'DU5', 'DU6 east');
await walk(1, 900, 'DU4', 'DU5 east');
return o;
