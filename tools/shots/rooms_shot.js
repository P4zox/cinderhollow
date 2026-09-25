await boot(); G.SAVE.flags['sc:seal']=1;
const L = [["A6", 18, 14], ["A7", 8, 12], ["HF1", 3, 10], ["HF2", 16, 7], ["HF3", 9, 32], ["HF4", 18, 10], ["HF5", 16, 16], ["HF6", 24, 10], ["HF7", 19, 13], ["D1", 12, 10], ["D3", 32, 10], ["D4", 8, 30], ["D5", 24, 10], ["D6", 12, 30], ["D7", 12, 14], ["D8", 26, 14], ["H1", 20, 10], ["E1", 12, 22], ["E3", 24, 10]];
for (const [r,x,y] of L) { for (const k of Object.keys(G.SAVE.flags)) if (k.startsWith('cut')) {} ; G.tp(r,x,y); G.P.hp=99999; G.P.inv=99; G.step(40); if (G.state==='cut') G.step(1,[],['pause']); G.step(5); await snap('room_'+r); }
return 'ok';
