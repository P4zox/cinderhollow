await boot(); G.giveArmory(); G.grantTechniques(); const o = [];
G.step(20); G.P.y -= 140; G.P.vy = 0; G.P.ground = false; G.step(1);
let starts = 0, prev = G.P.state; const seq = [];
for (let k = 0; k < 6; k++) {
  { const n0 = G.P.airN || 0; G.step(1, [], ['attack']); if ((G.P.airN || 0) > n0) starts++; }
  for (let j = 0; j < 14; j++) { const n0 = G.P.airN || 0; G.step(1); G.P.vy = Math.min(G.P.vy, 40); if ((G.P.airN || 0) > n0) starts++; if (G.P.state !== prev) { seq.push(G.P.state + (G.P.ground ? '@g' : '')); } prev = G.P.state; }   // (WM: counted by the air limit's own counter -- a queued press restarts the air attack without leaving its state)
}
o.push('airborne whole time: ' + !G.P.ground + '  air attacks: ' + starts + '  lock=' + G.P.airLock, seq.join(' '));
// heavy (plunge) also blocked while locked
G.step(1, [], ['heavy']); G.step(3); o.push('heavy while locked -> ' + G.P.state);
for (let i = 0; i < 200 && !G.P.ground; i++) G.step(1);
o.push('landed; lock=' + G.P.airLock); G.step(10); o.push('0.17s later lock=' + G.P.airLock); G.step(10); o.push('0.33s later lock=' + G.P.airLock);
return o;
