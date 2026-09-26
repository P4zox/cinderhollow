await boot();
G.SAVE.flags['cut:sanguine'] = 1;
G.tp('CM7', 6, 14); G.step(30, ['right']);
const B = G.boss, P = G.P, log = [];
for (let i = 0; i < 60 && !B.active; i++) G.step(5);
G.step(170);
for (const [dir, lab] of [['right', 'toward'], ['left', 'away']]) {
  window.__cm.CM.held = null; P.hp = G.D.maxHp; P.inv = 0; B.x = 400; B.state = 'idle'; P.x = 345; P.y = 240; setTimeout; B.face = -1; B.grabCd = 0; P.face = dir === 'right' ? 1 : -1;
  window.__cm.force('grab'); let rolled = false, caught = false;
  for (let k = 0; k < 70; k++) { if (!rolled && B.anim.i >= 3) { rolled = true; G.step(1, [dir], ['roll']); log.push(`${lab} roll ps=${P.state}`); } else G.step(1, rolled && k < 40 ? [dir] : []); B.cool = 50; if (B.state === 'drain') { caught = true; log.push(`caught k=${k} px=${Math.round(P.x)} bx=${Math.round(B.x)} ps=${P.state} ai=${P.anim.i}`); break; } }
  log.push(lab + ': ' + (caught ? 'CAUGHT' : 'dodged'));
}
return log;
