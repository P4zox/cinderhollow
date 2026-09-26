await boot(); G.grantTechniques(); const o=[];
G.tp('M4', 38, 8); G.step(20); await snap('d0_m4');
for (let i=0;i<30;i++){ G.step(3,['right']); } o.push(['walk', G.room, Math.round(G.P.x/16), Math.round(G.P.y/16), G.P.state].join(' '));
await snap('d1_after_walk');
G.tp('M4', 42, 12); G.step(20); o.push(['inpit', G.room, Math.round(G.P.x/16), Math.round(G.P.y/16), G.P.ground].join(' ')); await snap('d2_pit');
G.step(2,['down'],['jump']); for (let i=0;i<40;i++) G.step(3); o.push(['dropped', G.room, Math.round(G.P.x/16), Math.round(G.P.y/16), G.P.state, G.P.hp].join(' ')); await snap('d3_d1');
// climb back up
for (let i=0;i<60 && G.room==='D1';i++){ G.step(3, [], i%8==0?['jump']:[]); } o.push(['climb', G.room, Math.round(G.P.x/16), Math.round(G.P.y/16)].join(' ')); await snap('d4_back');
return o;
