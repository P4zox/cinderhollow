// every foe type: summon beside you in the flat arena, let it fight for a few seconds, hit it, no errors
await new Promise(r=>setTimeout(r,300));
const T = G.trn, out = []; const errs = []; const ce = console.error; console.error = (...a) => { errs.push(String(a[0] && a[0].stack || a[0]).split('\n').slice(0,2).join(' | ').slice(0,200)); ce(...a); };
T.start(); G.step(5); T.goto('TR2'); G.step(5);
for (const E of T.enemies()) {
  errs.length = 0; let r;
  try {
    T.clear(); G.step(2); G.P.x = 20 * 16; G.P.face = 1; G.step(2);
    const n = T.spawn(E.type, 1); const e = G.enemies.find(q => q.type === E.type);
    if (!e) { out.push('NONE ' + E.type); continue; }
    const hp0 = e.hp; let hurt = 0, states = new Set();
    for (let i = 0; i < 240; i++) { const p = G.P.hp; const d = e.x - G.P.x; G.step(2, Math.abs(d) > 30 ? [d < 0 ? 'left' : 'right'] : [], i > 120 && i % 5 === 0 ? ['attack'] : []); if (G.P.hp < p) hurt++; G.P.hp = 9999; states.add(e.state); if (G.state !== 'play') G.step(1, [], ['pause']); }
    r = `${errs.length ? 'ERR ' : 'OK  '}${E.type.padEnd(20)} hurt=${hurt} dmg=${Math.round(hp0 - Math.max(0, e.hp))}${e.alive ? '' : ' (killed)'} states=${[...states].slice(0, 6).join(',')}${errs.length ? ' ' + errs[0] : ''}`;
  } catch (ex) { r = `EXC ${E.type} ${ex.message}`; }
  out.push(r);
}
// the other test modes
T.clear(); G.step(2); T.goto('TR1'); G.step(5);
const dm = G.enemies.find(e => e.dummy); G.P.x = dm.x - 24; G.P.face = 1;
for (let i = 0; i < 30; i++) G.step(4, [], ['attack']);
G.step(10);
out.push(`dummy: alive=${dm.alive} hp=${dm.hp}/${dm.maxHp} total=${Math.round(dm.total)} last=${dm.lastDmg} dps=${Math.round(dm.dps)}`);
G.sk.ev("TRN.ohk = true"); G.step(4, [], ['attack']); G.step(20); out.push(`one-hit on dummy: last=${dm.lastDmg} alive=${dm.alive}`); G.sk.ev("TRN.ohk = false");
T.spawn('hollow_soldier', 3); G.sk.ev('TRN.freeze = true'); const xs = G.enemies.filter(e => !e.dummy).map(e => Math.round(e.x)); G.step(120); const xs2 = G.enemies.filter(e => !e.dummy).map(e => Math.round(e.x));
out.push(`freeze: ${xs.join(',')} -> ${xs2.join(',')}`); G.sk.ev('TRN.freeze = false'); G.step(120); out.push(`unfrozen: -> ${G.enemies.filter(e => !e.dummy).map(e => Math.round(e.x)).join(',')}`);
const t0 = G.sk.ev('time'); G.sk.ev('TRN.ts = 0.5'); G.step(60); out.push(`time x0.5: 60 frames -> ${(G.sk.ev('time') - t0).toFixed(2)} s of game time`); G.sk.ev('TRN.ts = 1');
G.sk.ev('TRN.hitbox = true'); G.step(2, [], ['attack']); G.step(3); await snap('hitboxes'); G.sk.ev('TRN.hitbox = false');
return out;
