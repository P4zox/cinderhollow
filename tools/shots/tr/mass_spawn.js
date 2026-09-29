// many foes at once: ×20 counts, several kinds in a row with the panel open, the cap, frame time with a full chamber
await new Promise(r => setTimeout(r, 300));
const T = G.trn, E = G.sk.ev, out = [];
const errs = []; window.addEventListener('error', e => errs.push(e.message));
T.start(); G.step(10);
E("trnGoto('TR2')"); G.step(10);
E("TRN.count = 20"); E("menu = { screen: 'trn', tab: 4, sel: 0 }; state = 'menu'");
const types = ['hollow_soldier', 'rot_crawler', 'gloom_wisp', 'hollow_archer', 'grave_knight'];
for (const t of types) { const n = E(`trnSpawnEnemy('${t}')`); out.push(`${t}: +${n} (state ${G.state}, alive ${E('trnFoesAlive()')})`); }
out.push('cap hit: ' + E("trnSpawnEnemy('hollow_soldier')") + ' more');
E("menu = null; state = 'play'"); G.SETTINGS.god = 1;
const xs = E("enemies.filter(e => e.trn).map(e => Math.round(e.x))"); out.push(`spread x: ${Math.min(...xs)}..${Math.max(...xs)} over room ${E('room.pw')}`);
await snap('mass');
const t0 = performance.now(); for (let i = 0; i < 300; i++) G.step(1, [], i % 10 === 0 ? ['attack'] : []); const ms = (performance.now() - t0) / 300;
out.push(`sim+render ${ms.toFixed(2)} ms/frame with ${E('trnFoesAlive()')} foes`);
E('trnClearFoes()'); out.push('after clear foes: ' + E('trnFoesAlive()'));
out.push('errors: ' + JSON.stringify(errs.slice(0, 3)));
return out;
