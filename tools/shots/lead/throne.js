await boot(); const o = [];
G.SAVE.flags['boss:sovereign'] = 1; G.SAVE.ending = 'ash';
G.tp('X5', 40, 10); G.step(30);
o.push('room ' + G.room + ' ngp ' + (G.SAVE.ngp || 0));
// walk to the throne and interact
for (let i = 0; i < 40 && Math.abs(G.P.x - (44 * 16 + 8)) > 6; i++) G.step(3, [G.P.x < 44 * 16 + 8 ? 'right' : 'left']);
G.step(2, [], ['interact']); o.push('after interact: state ' + G.state);
await snap('throne_dialog');
for (let i = 0; i < 6 && G.state === 'dialog'; i++) { G.step(40); G.step(2, [], ['confirm']); }
o.push('after choosing sit: state ' + G.state);
G.step(200); o.push('after the fade: room ' + G.room + ' ngp ' + (G.SAVE.ngp || 0) + ' ending ' + G.SAVE.ending);
return o;
