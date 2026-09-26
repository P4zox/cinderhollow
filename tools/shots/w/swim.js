// agent W: swim / tread bodies (Tidebreath swimming by agent B) in an injected pool in the test chamber
await boot(); G.giveArmory(); G.give({ items: { tidebreath: 1 }, weapon: 'longsword' });
window.__db.pool('T0', 2, 20, 8, 16);
const P = () => G.P, out = [], pos = {};
const shot = async n => { pos[n] = [Math.round(P().x - window.__db.cam.x), Math.round(P().y - window.__db.cam.y)]; await snap(n); };
G.tp('T0', 10, 16); G.step(260); for (const e of G.enemies) e.die({ dir: 1 });
out.push(`state=${P().state} tag=${P().anim.tag} deep=${window.__db.deep(P().x, P().y - 8)}`);
for (let i = 0; i < 40; i++) { G.step(1, ['right']); if (i === 20) await shot('swim_right'); } out.push('swim right: ' + P().state + '/' + P().anim.tag + ':' + P().anim.i);
for (let i = 0; i < 40; i++) { G.step(1, ['left']); if (i === 20) await shot('swim_left'); } out.push('swim left: ' + P().anim.tag + ' face=' + P().face);
for (const w of ['greatsword', 'knight_shield', 'gravechain', 'twinfangs']) { G.give({ weapon: w }); for (let i = 0; i < 14; i++) G.step(1, ['right']); await shot('swim_' + w); }
G.give({ weapon: 'longsword' });
for (let i = 0; i < 160; i++) { G.step(1, ['up']); } for (let i = 0; i < 30; i++) G.step(1); out.push('surface: ' + P().state + '/' + P().anim.tag); await shot('tread');
out.push(JSON.stringify(pos));
return out.join('\n');
