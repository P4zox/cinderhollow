await boot(); const o=[];
G.tp('M4', 45, 10); G.step(30); await snap('e0_m4');
for (let i=0;i<40 && G.room==='M4';i++) G.step(3,['left']);
o.push(['fell', G.room, Math.round(G.P.x/16), Math.round(G.P.y/16), G.P.state, Math.round(G.P.hp)].join(' '));
for (let i=0;i<20;i++) G.step(3); await snap('e1_d1');
// climb back: talon (wall-jump) only, then wings only
for (const [lab, items] of [['talon', {talon:1}], ['wings', {wings:1}], ['none', {}]]) {
  G.SAVE.items.talon = items.talon||0; G.SAVE.items.wings = items.wings||0;
  G.tp('D1', 10, 1); G.step(10); let ok = false;
  for (let i=0;i<300 && !ok;i++) {
    const t = i % 16; const dir = (Math.floor(i/16) % 2) ? 'left' : 'right';
    G.step(2, [dir], t===0||t===6 ? ['jump'] : []);
    if (G.room === 'M4' && G.P.ground && G.P.y <= 11*16) ok = true;
  }
  o.push(lab+': back up '+ok+' '+G.room+' '+Math.round(G.P.x/16)+','+Math.round(G.P.y/16));
}
return o;
