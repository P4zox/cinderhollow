await boot(); G.SAVE.flags['cut:warden'] = 1;
G.tp('TV8', 12, 10); G.step(5);
for (let i = 0; i < 200 && !(G.boss && G.boss.active); i++) G.step(2, ['right']);
const b = G.boss; G.step(150); b.state = 'idle'; b.cool = 99;
b.hit({ dmg: b.hp - b.maxHp * 0.49, poise: 0, dir: -1, kind: 'light', x: b.x, y: b.y - 50 });
b.cool = 0; let t = 0;
for (let i = 0; i < 400 && G.state !== 'cut'; i++) { G.P.hp = 999; G.step(1); }
const out = { cut: G.state === 'cut' };
for (let i = 0, k = 0; i < 200 && G.state === 'cut'; i++) { G.step(6); t += 0.1; if (i % 6 === 2) await snap('x_' + String(k++).padStart(2, '0')); }
out.form = b.form; out.state = b.state; out.dur = +t.toFixed(1);
G.step(60); await snap('x_zz_after');
// second attempt: short version, no lines
return out;
