await boot();
const out = [];
G.give({ items: { talon: 1, wings: 1 } });
// portal: C6 catwalk at row 22 cols 12-13 (stand row 21), wall at col 14 rows 19-21
G.tp('C6', 12, 21); G.step(20);
await snap('00_c6');
for (let i = 0; i < 6; i++) { G.P.face = 1; G.step(20, ['right'], ['attack']); G.step(20); }
out.push(['after hits', G.room, G.P.x, G.step(1).p]);
await snap('01_c6_broken');
for (let i = 0; i < 90 && G.room === 'C6'; i++) G.step(4, ['right']);
out.push(['after walk', G.room, G.step(1).p]);
for (let i = 0; i < 80; i++) G.step(1);
await snap('02_arrive');
out.push(['arrive', G.room, G.step(1).p]);
for (const r of ['NH1','NH2','NH3','NH4','NH5','NH6','NH7']) { G.tp(r, 8, 10); G.step(40); await snap('10_' + r); out.push([r, G.step(1).room]); }
return out;
