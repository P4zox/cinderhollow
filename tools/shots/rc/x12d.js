await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.talon = 1; delete G.SAVE.items.wings; const log = [];
const P = () => G.P, st = (h = [], t = []) => G.step(1, h, t);
G.tp('X12', 6, 28); for (let i = 0; i < 30; i++) st();
const tr = []; const rec = () => tr.push(`${(P().x/16).toFixed(1)},${(P().y/16).toFixed(1)}${P().state[0]}${P().state === 'hook' ? 'H' : ''}`);
st(['right', 'jump'], ['jump']);
for (let i = 0; i < 22; i++) { st(['right', 'jump']); if (i % 3 == 0) rec(); }
st(['right'], ['hook']); rec();
for (let i = 0; i < 90; i++) { st(['right']); if (i % 5 == 0) rec(); }
log.push(tr.join(' '));
return log;
