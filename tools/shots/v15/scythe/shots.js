// in-game frames of the scythe moves (real inputs; a snapshot at each impact). Run with tools/shots/wm/run.sh.
// Writes <out>/scy_*.png and returns the player's screen position for the montage (montage.py crops round it).
const st = () => G.P.state;
const shotAt = async (rank, souls, script, id, at, name, far = 34) => {
  W().reset('scythe', rank); arena(); W().reset('scythe', rank); E(`D.maxSt = 1e6; P.st = 1e6; P.scySouls = ${souls}; P.scyFade = 0`); W().dummy(far);
  for (const s of script) {
    if (s === 'jump') { W().down('jump'); W().frame(6); W().up('jump'); }
    else if (s[0] === 'w') W().frame(+s.slice(1));
    else if (s.startsWith('hK')) { W().down('heavy'); W().frame(Math.round(+s.slice(2) / 16.67)); W().up('heavy'); }
    else if (s === 'down') W().down('down'); else if (s === 'up') W().down('up');
    else W().tap({ J: 'attack', K: 'heavy', I: 'parry', L: 'roll' }[s], 2);
  }
  for (let i = 0; i < 150 && !(st() === id && (E('P.mvT') >= at || E('!ATK[P.state]'))); i++) W().frame(1);
  W().up('down'); W().up('up');
  E('hitstop = 0'); G.step(0); await snap(name);
  const sc = E('[(P.x - cam.x) * scale + ox, (P.y - cam.y) * scale + oy, scale, P.face]');
  return { name, st: st(), t: Math.round(E('P.mvT') || 0), sc };
};
const out = [];
out.push(await shotAt(1, 2, ['J'], 'scy_1', 175, 'scy_1'));
out.push(await shotAt(1, 2, ['J', 'w8', 'J'], 'scy_2', 175, 'scy_2'));
out.push(await shotAt(1, 2, ['J', 'w8', 'J', 'w8', 'J'], 'scy_3', 215, 'scy_3'));
out.push(await shotAt(1, 3, ['J', 'w8', 'J', 'w8', 'J', 'w8', 'J'], 'scy_4', 300, 'scy_4'));
out.push(await shotAt(1, 1, ['J', 'w8', 'K'], 'scy_hook', 215, 'scy_hook', 42));
out.push(await shotAt(1, 1, ['J', 'w8', 'J', 'w8', 'K'], 'scy_spiral', 360, 'scy_spiral'));
out.push(await shotAt(1, 0, ['K'], 'scy_heavy', 300, 'scy_heavy'));
out.push(await shotAt(1, 0, ['K', 'w8', 'K'], 'scy_twin', 280, 'scy_twin'));
out.push(await shotAt(1, 0, ['hK900'], 'scy_charged', 260, 'scy_charged'));
out.push(await shotAt(1, 3, ['hK300'], 'scy_reap', 340, 'scy_reap'));
out.push(await shotAt(1, 3, ['hK200'], 'scy_reap', 150, 'scy_reap_windup'));
out.push(await shotAt(1, 2, ['up', 'J'], 'scy_up', 200, 'scy_up', 24));
out.push(await shotAt(1, 1, ['L', 'w14', 'J'], 'scy_rollj', 160, 'scy_rollj', 110));
out.push(await shotAt(1, 1, ['L', 'w14', 'K'], 'scy_rollk', 220, 'scy_rollk', 110));
out.push(await shotAt(1, 2, ['I'], 'scy_hstep', 180, 'scy_hstep', 30));
out.push(await shotAt(2, 2, ['I', 'w6', 'J'], 'scy_backstab', 135, 'scy_backstab', 30));
out.push(await shotAt(2, 1, ['J', 'w8', 'J', 'w40', 'J'], 'scy_pend', 200, 'scy_pend'));
out.push(await shotAt(1, 2, ['jump', 'w4', 'J'], 'scy_air', 165, 'scy_air', 24));
out.push(await shotAt(1, 2, ['jump', 'w4', 'J', 'w8', 'J'], 'scy_dive', 165, 'scy_dive', 24));
out.push(await shotAt(1, 3, ['w2'], 'idle', 0, 'souls_idle'));
return out;
