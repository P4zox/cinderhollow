// SA: the stress sweep over every new room (random inputs, 600 frames each), errors collected
await boot(); G.grantTechniques(); G.SAVE.items.tidebreath = 1; G.SAVE.items.moonstep = 1; G.SAVE.items.talon = 1; G.giveArmory && G.giveArmory();
const spots = [['TV9', 104, 27], ['TV9', 20, 18], ['TV10', 40, 9], ['TV11', 10, 10], ['TV12', 8, 15], ['TV13', 15, 12], ['TV14', 12, 13], ['TV15', 3, 10], ['TV16', 8, 12],
  ['DB10', 88, 9], ['DB10', 40, 30], ['DB11', 5, 10], ['DB12', 20, 12], ['DB13', 3, 17], ['DB14', 9, 4], ['DB15', 32, 9], ['DB16', 3, 9], ['DB17', 13, 2],
  ['CM9', 20, 6], ['CM9', 20, 22], ['CM10', 12, 31], ['CM11', 15, 9], ['CM12', 3, 15], ['CM13', 20, 14], ['CM14', 12, 16], ['CM15', 16, 9], ['CM16', 9, 21], ['CM17', 5, 12],
  ['TV3', 17, 10], ['TV6', 8, 9], ['DB3', 10, 9], ['DB1', 7, 13], ['CM3', 17, 9], ['CM4', 49, 10], ['CM5', 50, 7]];
const acts = ['left', 'right', 'jump', 'attack', 'heavy', 'roll', 'parry', 'spell', 'art', 'hook', 'down', 'up', 'interact'];
const errs = []; window.addEventListener('error', e => errs.push(String(e.message)));
const out = [];
for (const [r, x, y] of spots) {
  try { G.tp(r, x, y); for (let i = 0; i < 120; i++) { const h = [acts[Math.floor(Math.random() * 4)]]; const t = Math.random() < 0.4 ? [acts[Math.floor(Math.random() * acts.length)]] : []; G.step(5, h, t);
      if (G.state === 'cut' || G.state === 'dialog' || G.state === 'menu' || G.state === 'cine' || G.state === 'reader') G.step(1, [], ['pause']); if (G.state === 'dead') G.step(200); G.P.hp = Math.max(G.P.hp, 50); } }
  catch (e) { out.push(r + ': ' + e.message + ' ' + (e.stack || '').split('\n')[1]); }
}
return { exc: out, errs: errs.slice(0, 10), fps: 'n/a' };
