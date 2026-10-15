// per type: what the skill tree's hooks can see (kinds, steps, charged, multi-hit, I button, dodge)
const out = E(`(() => { const r = {};
  for (const ty of MV.order) { const T = MV.types[ty], ms = Object.values(MV.defs).filter(d => d.type === ty);
    r[ty] = { moves: ms.length, heavy: ms.filter(d => d.kind === 'heavy').map(d => d.id).join(','), step0: ms.filter(d => d.step === 0).map(d => d.id).join(','),
      multi: ms.filter(d => d.n > 1).length, stamFn: ms.filter(d => typeof d.stam === 'function').map(d=>d.id).join(','), onI: !!T.onI, counter: !!T.counter, parryUpd: !!T.parryUpdate,
      dodge: JSON.stringify(typeof T.dodge === 'function' ? 'fn' : T.dodge || 'roll'), onL: !!T.onL, rollJ: typeof T.rollJ, speed: !!T.speed, hurt: !!T.hurt, guardCost: !!T.guardCost, regen: !!T.regenMul, K: T.K, onK: !!T.onK };
  } return r; })()`);
return out;
