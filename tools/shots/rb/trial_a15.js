await boot(); G.SAVE.seenAreas = { archives: 1 }; G.give({ items: { talon: 1, hook: 1 } }); G.P.hp = 999;
const out = [];
const C = (dirs, pres, holds, hooks, rels = [0]) => { const o = []; for (const d of dirs) for (const p of pres) for (const h of holds) for (const k of hooks) for (const r of rels) o.push([d, p, h, -1, k, r]); return o; };
const HK = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32];
const moves = [
  { hookMove: 1, ring: [9, 18], cands: C([1], [0, 4, 8], [6, 12, 20], HK) },
  { hookMove: 1, ring: [17, 18], cands: C([1], [0, 10, 20, 30, 40, 50, 60], [6, 12], HK, [0, 10]) },
  { hookMove: 1, ring: [22, 13], cands: C([1], [0, 10, 20, 30, 40, 50, 60], [6, 12], HK, [0, 10]) },
  { hookMove: 1, ring: [31, 15], cands: C([1], [0, 10, 20, 30, 40, 50, 60], [6, 12], HK, [0, 10]) },
  { hookMove: 1, ring: [37, 12], cands: C([1], Array.from({ length: 34 }, (_, i) => i * 3), [6, 14], [2, 4, 6, 8, 10, 12, 14, 16, 20]) },
  { hookMove: 1, to: [43, 47, 19], cands: C([1], Array.from({ length: 34 }, (_, i) => i * 3), [6, 12, 20], [-1]) },
];
const res = await window.__solve('A15', 3, 28, moves);
return res;
