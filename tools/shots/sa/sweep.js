// SA: the stress sweep over every new room (random inputs, 600 frames each), errors collected
await boot(); G.grantTechniques(); G.SAVE.items.tidebreath = 1; G.SAVE.items.moonstep = 1; G.SAVE.items.talon = 1; G.giveArmory && G.giveArmory();
const spots = [['TV9', 100, 27], ['TV9', 20, 18], ['TV10', 40, 11], ['TV11', 30, 11], ['TV12', 8, 15], ['TV13', 15, 11], ['TV14', 14, 13], ['TV15', 3, 10], ['TV16', 8, 11],
  ['W4', 3, 50], ['DB10', 72, 10], ['DB10', 40, 30], ['DB11', 5, 10], ['DB12', 20, 9], ['DB13', 3, 17], ['DB14', 9, 4], ['DB15', 8, 10], ['DB16', 3, 9], ['DB17', 13, 3],
  ['CM9', 20, 7], ['CM9', 20, 26], ['CM10', 10, 29], ['CM11', 20, 11], ['CM12', 20, 10], ['CM13', 20, 15], ['CM14', 12, 15], ['CM15', 20, 11], ['CM16', 10, 16], ['CM17', 5, 11],
  ['TV2', 9, 10], ['TV5', 11, 23], ['DB3', 18, 9], ['DB1', 7, 13], ['DB4', 16, 11], ['CM4', 49, 10], ['CM8', 6, 10], ['K2', 39, 10]];
const acts = ['left', 'right', 'jump', 'attack', 'heavy', 'roll', 'parry', 'spell', 'art', 'hook', 'down', 'up', 'interact'];
const errs = []; window.addEventListener('error', e => errs.push(String(e.message)));
const out = [];
for (const [r, x, y] of spots) {
  try { G.tp(r, x, y); for (let i = 0; i < 120; i++) { const h = [acts[Math.floor(Math.random() * 4)]]; const t = Math.random() < 0.4 ? [acts[Math.floor(Math.random() * acts.length)]] : []; G.step(5, h, t);
      if (G.state === 'cut' || G.state === 'dialog' || G.state === 'menu' || G.state === 'cine' || G.state === 'reader') G.step(1, [], ['pause']); if (G.state === 'dead') G.step(200); G.P.hp = Math.max(G.P.hp, 50); } }
  catch (e) { out.push(r + ': ' + e.message + ' ' + (e.stack || '').split('\n')[1]); }
}
return { exc: out, errs: errs.slice(0, 10), fps: 'n/a' };
