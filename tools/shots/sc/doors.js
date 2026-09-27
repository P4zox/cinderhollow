// every SC door pair, both ways; the shortcut doors are sealed from the old side until used from the new wing
await boot(); G.grantTechniques(); G.SETTINGS.god = 1;
const out = [];
const use = () => { G.step(1, [], ['interact']); for (let i = 0; i < 120 && (window.__sys.SYS.warp || G.state !== 'play'); i++) G.step(1); G.step(20); };
const pairs = [['SF3', 8, 12, 'SF10'], ['SF6', 7, 48, 'SF11'], ['SF4', 16, 12, 'SF12'], ['SF11', 104, 2, 'SF17'], ['NH2', 9, 12, 'NH9'], ['E2', 41, 10, 'E4'], ['E1', 15, 22, 'E5'], ['E5', 85, 3, 'E6'], ['H3', 6, 10, 'H4']];
for (const [a, x, y, b] of pairs) {
  G.tp(a, x, y); G.step(20); use(); const r1 = G.room;
  let back = '';
  if (r1 === a) { back = '(sealed)'; }
  else { use(); back = G.room; }
  out.push(`${a} -> ${r1} -> ${back}`);
}
// now open the sealed ones from the wing side, then try again from the old side
for (const [b, x, y, a] of [['SF11', 104, 26, 'SF6'], ['SF12', 17, 17, 'SF4'], ['E5', 108, 27, 'E1']]) {
  G.tp(b, x, y); G.step(20); use(); const r1 = G.room; use(); out.push(`from wing ${b} -> ${r1} -> ${G.room}`);
}
for (const [a, x, y] of [['SF6', 7, 48], ['SF4', 16, 12], ['E1', 15, 22]]) { G.tp(a, x, y); G.step(20); use(); out.push(`${a} now -> ${G.room}`); }
return out;
