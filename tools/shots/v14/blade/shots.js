// in-game frames of the new blade moves (real inputs; snapshots at the impact). Run with tools/shots/wm/run.sh
const st = () => G.P.state;
const shotAt = async (type, rank, script, id, at, name) => {
  W().reset(type, rank); arena(); W().reset(type, rank); E('D.maxSt = 1e6; P.st = 1e6'); W().dummy(30);
  for (const s of script) { if (s === 'sheathed') E('P.sheathed = true'); else if (s === 'jump') { W().down('jump'); W().frame(6); W().up('jump'); } else if (s[0] === 'w') W().frame(+s.slice(1)); else if (s.startsWith('hK')) { W().down('heavy'); W().frame(Math.round(+s.slice(2) / 16.67)); W().up('heavy'); } else W().tap({ J: 'attack', K: 'heavy', I: 'parry', L: 'roll' }[s]); }
  for (let i = 0; i < 120 && !(st() === id && E('P.mvT') >= at); i++) W().frame(1);
  E('hitstop = 0'); G.step(0); await snap(name); return name + ':' + st() + '@' + Math.round(E('P.mvT'));
};
const out = [];
out.push(await shotAt('longsword', 1, ['J', 'w12', 'K'], 'ls_jk', 290, 'ls_jk'));
out.push(await shotAt('longsword', 1, ['L', 'w14', 'K'], 'ls_rollk', 260, 'ls_rollk'));
out.push(await shotAt('longsword', 1, ['jump', 'J', 'w14', 'J'], 'ls_air2', 170, 'ls_air2'));
out.push(await shotAt('longsword', 2, ['J', 'w12', 'J', 'w40', 'J'], 'ls_wheel', 240, 'ls_wheel'));
out.push(await shotAt('katana', 1, ['sheathed', 'J'], 'kt_draw', 140, 'kt_draw'));
out.push(await shotAt('katana', 1, ['J', 'w14', 'J', 'w14', 'K'], 'kt_jjk', 260, 'kt_jjk'));
out.push(await shotAt('katana', 1, ['sheathed', 'K', 'w14', 'J'], 'kt_tsubame', 120, 'kt_tsubame'));
out.push(await shotAt('katana', 2, ['sheathed', 'hK560', 'w6', 'K'], 'kt_turn', 180, 'kt_turn'));
return out;
