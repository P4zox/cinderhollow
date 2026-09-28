const out = [];
const R = n => G.room === n || (NAV.fails.push('expected ' + n + ' got ' + G.room), false);
const D = { drop: false }, H = { drop: false, jump: true, hj: 2 };
// the Bellwalk: timed crossing (wait on each pillar for the toll)
function bellwalk() {
  let F = 0; const Rm = () => window.__sys.roomObj, cell = (x, y) => Rm().grid[y * Rm().w + x], Aon = () => cell(42, 14) !== 0;
  const st = (h = [], t = []) => { tick(h, t); F++; };
  const until = f => { let n = 0; while (F < f && n++ < 2000) st(); };
  const runTo = (x, dir) => { const d = dir < 0 ? 'left' : 'right'; for (let i = 0; i < 200 && (dir < 0 ? Pp().x > x : Pp().x < x); i++) st([d]); };
  const jump = (dir, hold = 28) => { const d = dir < 0 ? 'left' : 'right'; st([d, 'jump'], ['jump']); for (let i = 0; i < 90; i++) { st(i < hold ? [d, 'jump'] : [d]); if (Pp().ground && i > 3) break; } };
  const walkUp = (x, dir) => { const d = dir < 0 ? 'left' : 'right'; for (let i = 0; i < 200 && (dir < 0 ? Pp().x > x : Pp().x < x); i++) { if (i % 20 === 5) jump(dir, 6); else st([d]); } };
  let was = Aon(), Ta = -1; for (let i = 0; i < 600 && Ta < 0; i++) { st(); const a = Aon(); if (a && !was) Ta = F; was = a; }
  const T = 192;
  runTo(48 * 16 + 8, -1); runTo(43 * 16 + 8, -1); until(Ta + T - 15); jump(-1); walkUp(34 * 16 + 8, -1);
  const Ta2 = Ta + 2 * T; until(Ta2); runTo(30 * 16 + 8, -1); until(Ta2 + T - 15); jump(-1, 8); walkUp(19 * 16 + 8, -1);
  const Tb = Ta2 + 3 * T; until(Tb); jump(-1, 20); runTo(14 * 16 + 8, -1); until(Tb + T - 15); jump(-1, 20);
  return Pp().x < 8 * 16 && Pp().y < 15 * 16 || (NAV.fails.push('bellwalk at ' + ft().x.toFixed(1) + ',' + ft().y.toFixed(1)), false);
}
G.SAVE.flags['x3:NV12:dirge'] = 1; G.SAVE.flags['x3:NV12:gw'] = 1; G.SAVE.flags['x3:NV12:gc'] = 1;
G.tp('NV3', 10, 41); for (let i = 0; i < 4; i++) { G.step(10); settle(); }
const ok = path([
  [16, 41], () => dropThrough(), () => R('NV17'),
  [8, 54, { drop: false }], () => exitDir('left'), () => R('NV8'),
  // the Legion Yard up the shaft
  [3, 10], [3, 7], [3, 4], [3, 1], () => climbOut('NV8'), () => R('NV13'), [3, 12], [20, 12], [3, 12], () => dropThrough(), () => R('NV8'),
  [3, 10], () => exitDir('left'), () => R('NV9'),
  // down to the Bellwalk, across, the Dirge, up its well into the stair
  [57, 11], () => dropThrough(), () => R('NV11'), [57, 13, { drop: true }], [57, 10], [57, 7], [57, 4], [57, 1], () => climbOut('NV11'), () => R('NV9'), [57, 11],
  () => dropThrough(), () => R('NV11'), [57, 13, { drop: true }], [52, 13], () => bellwalk(), () => exitDir('left'), () => R('NV12'),
  [8, 13], [2, 13], [2, 10], [2, 7], [2, 4], [2, 1], () => climbOut('NV12'), () => R('NV10'), [18, 55],
  () => dropThrough(), () => R('NV12'), [2, 13, { drop: true }], [2, 10], [2, 7], [2, 4], [2, 1], () => climbOut('NV12'), () => R('NV10'),
  [18, 55], () => dropThrough(), () => R('NV12'), [2, 13, { drop: true }], [20, 13], [26, 13, { jump: true }], () => exitDir('right'), () => R('NV11'), [3, 13], () => exitDir('left'), () => R('NV12'),
  [2, 13], [2, 10], [2, 7], [2, 4], [2, 1], () => climbOut('NV12'), () => R('NV10'),
  [18, 55], [24, 52], [30, 49], [36, 52], [44, 55], () => exitDir('right'), () => R('NV9'), [4, 11], () => exitDir('left'), () => R('NV10'),
  // the east ledges, the Barracks, the barred alcove
  [36, 52], [31, 49], [33, 49], [36, 46], [34, 43], [38, 40], [45, 40], () => exitDir('right'), () => R('NV14'), [10, 10], [2, 10], () => exitDir('left'), () => R('NV10'),
  [40, 40], [38, 40], [35, 37], [32, 37], [29, 34], [30, 31], [33, 31], [36, 28], [38, 28], () => lever('left'), () => G.KIT.byId.bar.on || (NAV.fails.push('bar'), false),
  [44, 28], () => exitDir('right'), () => R('NV18'),
  [10, 28], [22, 24], [27, 24], [30, 21], [35, 21], [38, 18], [40, 18], [43, 15], [45, 15], [49, 12], [52, 9], [52, 6], [52, 3], [53, 0], () => climbOut('NV18'), () => R('NV4'), [15, 16],
  // and back: the Executioners have fallen now (for the summit's seal)
  () => { G.SAVE.flags['boss:executioners'] = 1; return true; },
  [15, 16], () => dropThrough(), () => R('NV18'), [52, 12, { drop: true }], [44, 15, D], [38, 18, D], [31, 21, D], [23, 24, D], [10, 28, D], () => exitDir('left'), () => R('NV10'),
  // west: the Headsman's Run, the chimney, the summit, the Ossuary, the Hollow Court
  [38, 28], [31, 31, H], [28, 34, D], [34, 37, H], [40, 40, H], [33, 43, H], [30, 49, H], [28, 49], [25, 46], [22, 46], [18, 43], [14, 43], [9, 40], [3, 40], () => exitDir('left'), () => R('NV15'),
  [50, 12], () => exitDir('right'), () => R('NV10'),
  [2, 40], () => chimney(8, 25, 'left'), [8, 25], [12, 25], [16, 22], [18, 22], [23, 22, { jump: true }], [27, 22], [30, 19], [32, 19], [35, 16], [33, 16], [29, 13], [31, 10], [31, 7], [8, 7], [2, 7], () => slam(true), [2, 12], () => exitDir('left'), () => R('NV16'),
  [8, 12], [13, 12], () => exitDir('right'), () => R('NV10'), [2, 12], () => chimney(8, 7, 'right'), [20, 7], [36, 7],
  () => { const p = G.KIT && window.__sys.roomObj; return true; },
  [43, 7], [43, 4], [43, 1], () => climbOut('NV10'), () => R('NV6'), [29, 14], () => dropThrough(), () => R('NV10'), [43, 7, { drop: true }],
  // down the stair and home through the street, the gate and the well
  [36, 7], [32, 10, { drop: true }], [28, 13, D], [31, 19, D], [26, 22, H], [31, 25, H], [38, 28, H], [31, 31, H], [28, 34, D], [34, 37, H], [40, 40, H], [33, 43, H], [37, 46, H], [30, 49, H], [36, 52, D], [44, 55, D],
  () => exitDir('right'), () => R('NV9'), [11, 8], [20, 11, D], [27, 8], [38, 11, D], [45, 8], [62, 11], () => exitDir('right'), () => R('NV8'), [40, 10], [46, 10], () => exitDir('right'), () => R('NV17'),
  [13, 51], [4, 48], [13, 45], [4, 42], [13, 39], [4, 36], [13, 33], [4, 30], [13, 27], [4, 24], [13, 21], [4, 18], [13, 15], [4, 12], [13, 9], [4, 6], [13, 3], () => climbOut('NV17'), () => R('NV3'), [10, 41],
]);
out.push('ok ' + ok, 'log ' + NAV.log.join(' '), 'fails ' + NAV.fails.join(' | '));
await snap('walk_nv_end');
return out;
