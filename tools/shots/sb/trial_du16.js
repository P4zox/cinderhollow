G.tp('DU16', 5, 3); for (let i = 0; i < 6; i++) { G.step(20); settle(); }
TR.done0 = S.SYS.result; TR.room = 'DU16'; TR.home = [5 * 16 + 8, 5, 3];
const P = () => G.P;
const B = [[10, 14], [17, 4], [24, 11], [31, 16], [38, 7], [45, 2], [52, 10]], tg = y => { for (const [r, c] of B) if (y < (r + 1) * 16 + 28) return c * 16 + 8; return 248; };
const glide = (bias) => i => {
  const p = P(); if (p.ground && p.y < 100) return p.x < 13 * 16 ? [['right'], []] : (i % 6 === 0 ? [['down', 'jump'], ['jump']] : [['down'], []]);
  const z = [0, tg(p.y)];
  const tx = z[1] + bias, d = tx - p.x;
  const h = Math.abs(d) < 3 ? [] : d > 0 ? ['right'] : ['left'];
  return [h.concat(p.vy > 0 || !p.ground ? ['jump'] : []), []];
};
let r = null;
for (let t = 0; t < 12 && !(r && r.ok); t++) r = TR.run([], () => false, { fn: glide((t % 5) * 3 - 6), max: 1400 });
TR.log.push('fall ' + JSON.stringify(S.SYS.result && { t: S.SYS.result.time, gold: S.SYS.result.gold }) + ' at ' + (P().x / 16).toFixed(1) + ',' + (P().y / 16).toFixed(1) + ' why ' + (r && r.why));
for (let i = 0; i < 240; i++) G.step(1);
TR.log.push('charm ' + G.SAVE.charms.includes('c_x3_scarab'));
await snap('du16_goal');
// back up the updraft
for (let i = 0; i < 40; i++) G.step(1, ['right']);
G.step(1, ['right', 'jump'], ['jump']); for (let i = 0; i < 900 && P().y > 70; i++) G.step(1, ['right']);
TR.log.push('updraft top y ' + (P().y / 16).toFixed(1) + ' x ' + (P().x / 16).toFixed(1));
for (let i = 0; i < 90; i++) G.step(1, ['left']);
TR.log.push('landing ' + (P().x / 16).toFixed(1) + ',' + (P().y / 16).toFixed(1) + ' ground ' + P().ground);
await snap('du16_back');
return TR.log;
