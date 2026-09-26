await boot();
const out = [];
window.__nhLog = [];
G.SAVE.flags['cut:saint0'] = 1; G.SAVE.flags['cut:enforcer'] = 1;
async function forced(roomId, tx, move, n, dodge) {
  G.tp(roomId, tx, roomId === 'NH7' ? 10 : 12); G.step(20);
  const B = G.boss; B.activate && B.activate(); G.step(200);
  let hits = 0;
  for (let k = 0; k < n; k++) {
    G.P.hp = G.D.maxHp; window.__nhLog = [];
    B.x = G.P.x + 80; B.face = -1; B.state = 'idle'; B.cool = 5;
    if (B.kind === 'saint0') { B.startAttack(move); } else { B.start(move); }
    let rolled = false;
    for (let f = 0; f < 150 && B.state === 'attack'; f++) {
      const w = B.kind === 'saint0' ? B.win(B.anim.tag) : [4, 7];
      if (dodge && !rolled && B.anim.i === w[0] - 1 && B.anim.t > 30) { rolled = true; G.P.face = 1; G.step(1, [], ['roll']); continue; }
      G.step(1);
    }
    G.step(20);
    if (window.__nhLog.length) hits++;
  }
  return hits;
}
out.push(['saint thrust stand', await forced('NH7', 10, 'thrust', 6, false), 'dodge', await forced('NH7', 10, 'thrust', 6, true)]);
out.push(['saint sweep stand', await forced('NH7', 10, 'sweep', 6, false), 'dodge', await forced('NH7', 10, 'sweep', 6, true)]);
out.push(['enforcer bash stand', await forced('NH5', 8, 'bash', 6, false), 'dodge', await forced('NH5', 8, 'bash', 6, true)]);
out.push(['enforcer sweep stand', await forced('NH5', 8, 'sweep', 6, false), 'dodge', await forced('NH5', 8, 'sweep', 6, true)]);
out.push(['enforcer stomp stand', await forced('NH5', 8, 'stomp', 6, false)]);
return out;
