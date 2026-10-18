// Shading phase 3: eye adaptation strips. Teleport bright -> dark and dark -> bright and capture the first second (frames 0..60).
//   SHOT_HTML=<build> node ../../shot.js expo.js <out>
await boot(); G.SETTINGS.god = 1;
const E = G.sk.ev;
E('window.requestAnimationFrame = () => 0');
Object.assign(G.SETTINGS, window.__shSet || {});
const world = async (n) => { E(`vctx.fillStyle = '#050407'; vctx.fillRect(0, 0, view.width, view.height); renderWorld(); presentWorld();`); await snap(n); };
const AT = [3, 9, 15, 21, 30, 39, 51, 63];   // frames after the teleport (the adaptation starts on the 3rd: the first two lack the room's lamps)
const out = [];
for (const [tag, a, b] of window.__exPairs || [['b2d', ['LF1', 56, 16], ['C10', 26, 10]], ['d2b', ['C10', 26, 10], ['DU10', 47, 22]], ['b2d2', ['X7', 41, 44], ['CM9', 42, 26]]]) {
  E('time = 100'); G.tp(...a);
  for (let i = 0; i < 200; i++) { G.step(1); G.enemies.length = 0; if (G.state !== 'play') G.step(1, [], ['pause']); }
  G.tp(...b); G.enemies.length = 0;
  E('fadeT = 0; fadePhase = 0');   // the strips show the world without the black fade over it
  for (let f = 0; f <= 63; f++) {
    if (f) G.step(1); G.enemies.length = 0;
    if (AT.includes(f)) { await world(`${tag}_f${String(f).padStart(2, '0')}`); out.push(`${tag} f${f} A=${G.GFX.eye ? G.GFX.eye.A.toFixed(3) : '-'}`); }
  }
}
return out;
