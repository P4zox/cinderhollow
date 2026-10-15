// v14 heavy: in-game snapshots of each new move at its hit frame (real inputs). Writes <outdir>/hv_<move>.png (POS: the player's feet on screen)
const cases = [
  ['greatsword', 1, 'gs_bash', [['down', 'attack'], 1, ['up', 'attack'], 10, ['down', 'heavy'], 1, ['up', 'heavy']]],
  ['greatsword', 1, 'gs_mcleave', [['tap', 'attack'], 30, ['tap', 'attack'], 30, ['tap', 'attack'], 10, ['tap', 'heavy']]],
  ['greatsword', 1, 'gs_retort', [['down', 'parry'], 10, ['eval', 'hurtPlayer(40, -1, 981, {})'], 10, ['tap', 'attack'], ['up', 'parry']]],
  ['greatsword', 3, 'gs_leap', [['down', 'heavy'], 55, ['tap', 'roll'], 5, ['tap', 'attack'], 20, ['up', 'heavy']]],
  ['maul', 1, 'ml_payback', [['tap', 'parry'], 10, ['eval', 'hurtPlayer(40, -1, 982, {})'], 5, ['tap', 'heavy']]],
  ['maul', 1, 'ml_jab', [['down', 'heavy'], 20, ['tap', 'attack'], 40, ['up', 'heavy']]],
  ['maul', 2, 'ml_pound', [['down', 'heavy'], 36, ['up', 'heavy'], 20, ['tap', 'heavy']]],
  ['maul', 4, 'ml_spike', [['down', 'jump'], 3, ['tap', 'attack'], 8, ['tap', 'attack'], 20, ['up', 'jump']]],
  // v14c
  ['greatsword', 1, 'gs_heave', [['down', 'heavy'], 60, ['up', 'heavy'], 5, ['tap', 'attack']]],
  ['greatsword', 1, 'gs_turn', [['tap', 'attack'], 10, ['tap', 'heavy'], 10, ['tap', 'attack']]],
  ['greatsword', 2, 'gs_split', [['tap', 'attack'], 45, ['tap', 'attack'], 45, ['tap', 'attack'], 15, ['tap', 'heavy'], 35, ['tap', 'heavy']]],
  ['maul', 1, 'ml_side', [['tap', 'attack'], 10, ['tap', 'heavy']]],
  ['maul', 1, 'ml_drop', [['tap', 'heavy'], 10, ['tap', 'attack']]],
  ['maul', 2, 'ml_backslam', [['tap', 'attack'], 10, ['tap', 'heavy'], 10, ['tap', 'heavy']]],
];
const shots = {}, POS = {};
for (const [type, rank, id, steps] of cases) {
  W().reset(type, rank); arena(); W().reset(type, rank); E('D.maxSt = 1e6; P.st = 1e6'); W().dummy(30, { tall: id === 'ml_spike' ? 90 : 40 });
  let snapped = false;
  const fr = async n => { for (let i = 0; i < n; i++) { W().frame(1); if (!snapped && E('P.state') === id && E('P.anim.i') >= E(`ATK['${id}'].active[0]`)) { snapped = true; hitstop = 0; E('areaCard = null; toasts.length = 0; render()'); POS[id] = E('[Math.round((P.x - cam.x) * scale + ox), Math.round((P.y - cam.y) * scale + oy), scale]'); await snap('hv_' + id); shots[id] = E('P.anim.tag + " f" + P.anim.i'); } } };
  for (const s of steps) {
    if (typeof s === 'number') { await fr(s); continue; }
    const [k, a] = s;
    if (k === 'down') W().down(a); else if (k === 'up') W().up(a); else if (k === 'eval') E(a); else { W().down(a); await fr(1); W().up(a); }
  }
  await fr(150);
  if (!snapped) shots[id] = 'NOT SEEN';
}
return { shots, POS };
