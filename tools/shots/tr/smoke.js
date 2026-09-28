await new Promise(r=>setTimeout(r,500));
const T = G.trn, out = [];
T.start(); G.step(30);
out.push('state ' + G.state + ' room ' + G.room + ' P ' + Math.round(G.P.x) + ',' + Math.round(G.P.y));
await snap('room1');
G.P.x = 30*16; G.step(20); await snap('room1b');
G.P.x = 40*16; G.step(20); await snap('room1c');
T.goto('TR2'); G.step(20); await snap('room2');
for (let t = 0; t < 6; t++) { T.open(t); G.step(2); out.push('tab ' + t + ' rows ' + T.rows(t).length); await snap('tab' + t); }
G.step(1, [], ['pause']); out.push('after esc ' + G.state);
return out;
