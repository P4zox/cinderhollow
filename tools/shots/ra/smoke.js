await boot(); G.grantTechniques(); G.SAVE.items.wings = 1; G.SAVE.items.talon = 1;
const S = JSON.parse(window.__spots), out = [], errs = [];
window.addEventListener('error', e => errs.push(String(e.message)));
for (const [r, x, y] of S) {
  try { G.tp(r, x, y); for (let i = 0; i < 20; i++) { G.step(6, [['left', 'right'][i % 2]], i % 5 ? [] : ['attack']); G.P.hp = Math.max(G.P.hp, 60); if (G.state !== 'play') G.step(1, [], ['pause']); }
    out.push(r + ' ok ' + G.enemies.length + ' foes, props ' + G.props.length); }
  catch (e) { out.push(r + ' EXC ' + e.message + ' ' + (e.stack || '').split('\n')[1]); }
}
return { out, errs: errs.slice(0, 10) };
