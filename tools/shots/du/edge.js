await boot(); G.grantTechniques(); const o = [];
async function arena(room, px, kind, moves, sides) {
  for (const side of sides) {
    G.SAVE.flags['boss:' + kind] = 0; G.SAVE.flags['cut:' + kind] = 1; G.SAVE.flags['cutp2:' + kind] = 1;
    G.tp(room, px, room === 'DU8' ? 14 : 11); G.step(5);
    const b = G.boss; b.activate(); G.step(200);
    const wallX = side < 0 ? b.L - 30 : b.R + 30;
    let oob = 0, maxDy = 0, minX = 1e9, maxX = -1e9;
    for (const ph of [1, 2]) {
      if (ph === 2) { b.hp = Math.round(b.maxHp * 0.45); G.step(60); for (let i = 0; i < 30 && G.state === 'cut'; i++) G.step(20); }
      for (const m of moves) {
        G.P.x = wallX; G.P.y = b.floor; b.x = side < 0 ? b.L + 10 : b.R - 10; b.facePlayer(); b.setS('idle', 'idle'); b.cool = 5; b.start(m);
        const seen = new Set(); for (let i = 0; i < 260; i++) { seen.add(b.state + ':' + b.anim.tag);
          G.P.x = wallX; G.P.hp = G.D.maxHp; G.step(1);
          minX = Math.min(minX, b.x); maxX = Math.max(maxX, b.x); maxDy = Math.max(maxDy, Math.abs(b.y - b.floor));
          if (b.x < b.L - 0.5 || b.x > b.R + 0.5) oob++;
        }
        if (side < 0 && ph === 2) o.push('  ' + m + ': ' + [...seen].slice(0, 6).join(' '));
      }
    }
    o.push(`${kind} side ${side}: L${Math.round(b.L)} R${Math.round(b.R)} x[${Math.round(minX)},${Math.round(maxX)}] oob=${oob} maxDy=${maxDy.toFixed(1)} P.x=${Math.round(G.P.x)} state=${b.state}`);
    await snap(kind + '_edge_' + side);
  }
}
await arena('DU8', 30, 'pharaoh', ['combo', 'lunge', 'slam', 'command', 'beam', 'coffin', 'summon', 'disc', 'backstep', 'strike', 'eyes', 'sink'], [-1, 1]);
await arena('DU6', 20, 'scarab', ['thrust', 'sweep', 'rear', 'burrow'], [-1, 1]);
return o;
