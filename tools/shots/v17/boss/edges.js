// arena edges (EXPANSION2 §0): with the player pinned against the west fog wall and against the furnace doors, force
// every travelling move; the boss must stay between his bounds (x 64..794 in CF8) and on the floor line.
const out = { arena: E('window.__hk.arena()'), wake: E('window.__hk.wake()') };
const MV = { 1: ['slam', 'leap', 'grab', 'combo', 'sweep', 'backhand'], 2: ['spear', 'blade', 'chain'], 3: ['dark_lunge', 'flame_grab', 'ft_combo', 'bellows_lo'] };
const res = [];
for (const side of ['west', 'east']) for (const ph of [1, 2, 3]) for (const m of MV[ph]) {
  E(`(() => { const b = boss; b.phase = ${ph}; b.applySpeed(); b.stanceMax = 9999; b.tWin = 99; b.queue = []; b.weapon = null; b.cool = 99; hkClearAttacks();
    P.x = ${side === 'west' ? 'b.L - 40' : 'b.R + 24'}; P.y = b.floor; P.vx = 0; P.ground = true; setP('idle', 'idle', true);
    b.x = ${side === 'west' ? 'b.L + 60' : 'b.R - 60'}; b.face = P.x < b.x ? -1 : 1; b.setS('idle', 'idle'); b.begin('${m}'); })()`);
  let minX = 1e9, maxX = -1e9, maxAir = 0, offFloor = 0;
  for (let i = 0; i < 700; i++) {
    E(`window.__hk.frame(1); P.hp = D.maxHp; P.x = ${side === 'west' ? 'boss.L - 40' : 'boss.R + 24'};`);
    const s = E('({ x: boss.x, y: boss.y, f: boss.floor, st: boss.state, air: boss.airH || 0 })');
    minX = Math.min(minX, s.x); maxX = Math.max(maxX, s.x); maxAir = Math.max(maxAir, s.air);
    if (Math.abs(s.y + s.air - s.f) > 0.5) offFloor++;
    if (s.st === 'idle' && i > 5) { E('boss.cool = 99'); break; }
  }
  const L = E('boss.L'), R = E('boss.R');
  res.push(`${side} p${ph} ${m.padEnd(10)} x ${Math.round(minX)}..${Math.round(maxX)} in [${L},${R}] ${minX >= L - 0.5 && maxX <= R + 0.5 ? 'OK' : 'OUT'} air ${Math.round(maxAir)} offFloor ${offFloor}`);
}
out.res = res; out.errs = E('window.__hk.errs.slice(0, 6)');
return out;
