await boot();
G.SAVE.flags['cut:sanguine'] = 1;
G.tp('CM7', 6, 14); G.step(30, ['right']);
const B = G.boss, P = G.P, log = [];
for (let i = 0; i < 60 && !B.active; i++) G.step(5);
G.step(170);
B.hp = Math.floor(B.maxHp * 0.5) - 5; B.state = 'idle'; B.cool = 0.1; P.x = 250;
for (let i = 0; i < 400 && B.phase !== 2; i++) G.step(1);
let n = 0;
for (let i = 0; i < 90; i++) { G.step(3); P.hp = G.D.maxHp; if (G.state === 'cut' && i % 6 === 0) await snap('c_' + String(n++).padStart(2, '0')); if (G.state !== 'cut' && i > 20) break; }
for (let i = 0; i < 40; i++) { G.step(3); P.hp = G.D.maxHp; if (i % 10 === 0) await snap('c_' + String(n++).padStart(2, '0')); }
log.push({ phase: B.phase, col: window.__cm.CM.col && window.__cm.CM.col.k, state: G.state, sheet: B.sh.name });
// every phase-2 move at both arena edges
const res = {};
for (const m of ['fly', 'requiem', 'charge', 'sneak', 'combo', 'grab']) for (const [lab, px] of [['L', 40], ['R', 665]]) {
  window.__cm.CM.held = null; P.hp = G.D.maxHp; P.inv = 0; P.x = px; P.y = 240; B.alt = 0; B.hidden = false; B.x = lab === 'L' ? 200 : 500; B.state = 'idle'; B.cool = 99; B.skyCd = 0; B.reqCd = 0; B.grabCd = 0;
  window.__cm.force(m); let mn = 1e9, mx = -1e9, top = 1e9, hits = 0, hp = P.hp;
  for (let k = 0; k < 420; k++) { G.step(1); B.cool = Math.max(B.cool, 50); P.x = window.__cm.CM.held ? P.x : px; mn = Math.min(mn, B.x); mx = Math.max(mx, B.x); top = Math.min(top, B.y - 112); if (P.hp < hp) hits++; hp = P.hp = Math.max(P.hp, 60); if (m === 'fly' && lab === 'L' && k % 70 === 30) await snap('c_fly_' + k); }
  res[m + lab] = [Math.round(mn), Math.round(mx), Math.round(top), hits];
}
log.push(res, { L: B.L, R: B.R, ceilingY: 32 });
// requiem: dodge by rolling when a line goes live nearby
window.__cm.CM.held = null; P.hp = G.D.maxHp; P.x = 330; B.state = 'idle'; B.alt = 0; B.x = 500; B.reqCd = 0; window.__cm.force('requiem');
let hitsR = 0, lastHp = P.hp, rolls = 0;
for (let k = 0; k < 420; k++) {
  const c = B.req && B.req.cur; let act = null;
  if (c && c.t >= c.warn - 0.07 && c.t < c.warn && !c.reacted) { c.reacted = true; act = 'roll'; rolls++; }
  G.step(1, [], act ? [act] : []); if (P.hp < lastHp) hitsR++; lastHp = P.hp; if (B.state !== 'requiem' && k > 30) break;
}
log.push({ requiemRolled: { hits: hitsR, rolls } });
// death + rewards + fog + walking out through the ruin
B.state = 'idle'; B.alt = 0; B.hidden = false; B.hp = 1; B.hit({ dmg: 50, poise: 0, dir: 1, x: B.x, y: B.y - 40 });
for (let k = 0; k < 10; k++) { P.hp = G.D.maxHp; G.step(60); }
await snap('c_zdead');
log.push({ alive: B.alive, flag: G.SAVE.flags['boss:sanguine'], fog: G.props.filter(p => p.type === 'fog').map(p => p.on()) });
P.x = 100; P.y = 240; for (let k = 0; k < 120 && G.room === 'CM7'; k++) G.step(2, ['left']);
log.push({ exit: G.room });
G.tp('CM7', 20, 14); G.step(60); await snap('c_zrevisit'); log.push({ revisitCol: window.__cm.CM.col && window.__cm.CM.col.k });
return log;
