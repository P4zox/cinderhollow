const out = [];
const R = n => G.room === n || (NAV.fails.push('expected ' + n + ' got ' + G.room), false);
G.tp('DU8', 7, 14); for (let i = 0; i < 4; i++) { G.step(10); settle(); }
const ok = path([
  [3, 14], () => dropThrough(), () => R('DU10'),
  [2, 12], () => lever('left'), () => G.KIT.byId.bar.on || (NAV.fails.push('gate'), false),
  [8, 12], [12, 15], [10, 18], [9, 21],
  // the Last Oasis and the Nameless Tomb
  [5, 21], () => dropThrough(), () => R('DU15'), [5, 12, { drop: true }], [10, 12], () => slam(), () => R('DU17'),
  [6, 11], () => climbOut('DU17'), () => R('DU15'), [12, 12], [7, 12], [5, 9], [5, 6], [5, 3], [5, 0], () => climbOut('DU15'), () => R('DU10'), [5, 21],
  [9, 21], [22, 16], [34, 22], [37, 22], [40, 22], [42, 22],
  // the Tomb Entry Hall, the Seal, the Sinking Sands, the Sun Dial
  [45, 22], () => dropThrough(), () => R('DU11'), [9, 11, { drop: true }], [21, 11], () => dropThrough(), () => R('DU14'),
  [21, 16, { drop: true }], [21, 13], [21, 10], [21, 7], [21, 4], [21, 1], () => climbOut('DU14'), () => R('DU11'), [21, 11], [9, 11], [9, 8], [9, 5], [9, 2], () => climbOut('DU11'), () => R('DU10'), [45, 22], () => dropThrough(), () => R('DU11'), [9, 11, { drop: true }],
  [30, 11], [44, 11], () => exitDir('right'), () => R('DU12'),
  [13, 11], () => hop(16), () => hop(20), () => hop(25), () => hop(29), () => hop(33), () => hop(37), () => hop(41), () => hop(44), () => hop(48),
  [51, 11], () => dropThrough(), () => R('DU13'), [35, 17, { drop: true }], [35, 14], [35, 11], [35, 8], [35, 5], [35, 2], () => climbOut('DU13'), () => R('DU12'), [51, 11],
  [48, 11], () => hop(44), () => hop(41), () => hop(37), () => hop(33), () => hop(29), () => hop(25), () => hop(20), () => hop(16), () => hop(12),
  [3, 11], () => exitDir('left'), () => R('DU11'), [44, 11], () => exitDir('right'), () => R('DU12'),
  [8, 11], [8, 8], [8, 5], [8, 2], () => climbOut('DU12'), () => R('DU10'), [91, 22], () => dropThrough(), () => R('DU12'), [8, 11], [8, 8], [8, 5], [8, 2], () => climbOut('DU12'), () => R('DU10'), [91, 22],
  [95, 22], [100, 20], [105, 18], [116, 23], () => exitDir('right'), () => R('DU9'),
  // the Scarab Cache and the Sandfall Descent
  [4, 11], [15, 8], [26, 11], [28, 11], () => dropThrough(), () => R('DU18'), [8, 11, { drop: true }], [9, 8], [8, 5], [9, 2], [8, -1], () => climbOut('DU18'), () => R('DU9'), [27, 11],
  [31, 11], [42, 11], [45, 11], () => dropThrough(), () => R('DU16'), [5, 3], [5, 0], () => climbOut('DU16'), () => R('DU9'),
  [45, 11], [54, 11], [61, 11], () => exitDir('right'), () => R('DU19'),
  [8, 57], [13, 54], [10, 51], [13, 48], [10, 45], [13, 42], [10, 39], [13, 36], [10, 33], [13, 30], [10, 27], [13, 24], [10, 21], [13, 18], [10, 15], [13, 12], [12, 9], [8, 7], () => exitDir('left'), () => R('DU4'),
  // and back along the spine to the Sanctum
  [20, 35], () => exitDir('right'), () => R('DU19'), [10, 7], [12, 9], [11, 57, { drop: true }], () => exitDir('left'), () => R('DU9'),
  [54, 11], [42, 11], [31, 11], [26, 11], [15, 8], [4, 11], () => exitDir('left'), () => R('DU10'),
  [110, 23], [105, 18], [95, 22], [89, 22], [84, 22], [80, 22], [77, 21], [72, 20], [63, 17], [52, 21], [48, 22], [40, 22], [37, 22], [34, 22], [22, 16], [13, 21], [10, 18], [11, 15], [8, 12], [3, 12], [3, 9], [3, 6], [3, 3],
  () => climbOut('DU10'), () => R('DU8'),
]);
out.push('ok ' + ok, 'log ' + NAV.log.join(' '), 'fails ' + NAV.fails.join(' | '));
await snap('walk_du_end');
return out;
