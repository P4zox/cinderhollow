G.SAVE.items.emberdash = 1; G.SETTINGS.god = 1; G.tp('NV15', 20, 12); for (let i = 0; i < 4; i++) { G.step(20); settle(); }
const P = () => G.P, out = [];
let side = -1, tap = 0;
let ph = 0;
const f = i => { const p = P(); const L = side < 0 ? 'left' : 'right';
    if (ph === 0) { if (p.x > 283) return [['left'], []]; ph = 1; return [['left', 'jump'], ['jump']]; }
    if (p.y < 60) return [['left'], []];
    if (p.state === 'wall' && tap <= 0) { side = -side; tap = 8; return [[side < 0 ? 'left' : 'right', 'jump'], ['jump']]; }
    tap--; return [p.vy < 0 ? [L, 'jump'] : [L], []]; };
for (let i = 0; i < 200; i++) { const inp = f(i); G.step(1, inp[0], inp[1]); if (i % 5 === 0) out.push(i + ' ' + P().state + ' ' + (P().x|0) + ',' + (P().y|0)); }
return out.join(' | ');
