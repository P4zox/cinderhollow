await boot();
G.SAVE.flags['cut:sanguine'] = 1; G.SAVE.flags['cutp2:sanguine'] = 1;
G.tp('CM7', 6, 14); G.step(30, ['right']);
const B = G.boss, P = G.P, log = [];
for (let i = 0; i < 60 && !B.active; i++) G.step(5);
log.push({ fogOn: G.props.filter(p => p.type === 'fog').map(p => p.on()) });
B.hp = Math.floor(B.maxHp * 0.5) - 5; B.state = 'idle'; B.cool = 0.1;
for (let i = 0; i < 300 && !(B.phase === 2 && B.state !== 'transform'); i++) G.step(1);
// tide: stand still in the middle, count damage
window.__cm.CM.waves = []; B.x = 620; B.state = 'idle'; B.cool = 999; B.tideT = 0; P.x = 300; P.hp = G.D.maxHp;
let tide = 0; for (let k = 0; k < 260; k++) { G.step(1); P.x = 300; if (k === 90 || k === 110) await snap('tide_' + k); }
tide = Math.round(G.D.maxHp - P.hp);
// tide dodged by jumping
window.__cm.CM.waves = []; B.tideT = 0; P.hp = G.D.maxHp; let jumped = false;
for (let k = 0; k < 260; k++) {
  const w = window.__cm.CM.waves[0];
  const near = w && w.t > w.tele && Math.abs(w.x - P.x) < 46 && !jumped;
  if (near) { jumped = true; G.step(1, [], ['jump']); G.step(10, ['jump']); k += 10; } else G.step(1);
}
log.push({ tide, tideJumped: Math.round(G.D.maxHp - P.hp) });
// roll through a lunge
P.hp = G.D.maxHp; B.x = 420; B.state = 'idle'; B.alt = 0; P.x = 320; P.face = 1; window.__cm.force('lunge');
let rolled = false; for (let k = 0; k < 90; k++) { if (!rolled && B.anim.i >= 3) { rolled = true; G.step(1, [], ['roll']); } else G.step(1); }
log.push({ lungeRolled: Math.round(G.D.maxHp - P.hp) });
// death
P.hp = G.D.maxHp;
B.state = 'idle'; B.alt = 0; B.hp = 1; B.hit({ dmg: 50, poise: 0, dir: 1, x: B.x, y: B.y - 40 });
log.push({ alive: B.alive, flag: G.SAVE.flags['boss:sanguine'] });
for (let k = 0; k < 12; k++) { P.hp = G.D.maxHp; G.step(60); if (k === 2) await snap('death_a'); }
await snap('death_b');
log.push({ weapons: Object.keys(G.SAVE.weapons), charms: G.SAVE.charms, spells: G.SAVE.spellsOwned, fog: G.props.filter(p => p.type === 'fog').map(p => p.on()), state: G.state });
// walk out west through the antechamber door
P.x = 60; for (let k = 0; k < 120 && G.room === 'CM7'; k++) G.step(2, ['left']);
log.push({ exitRoom: G.room });
return log;
