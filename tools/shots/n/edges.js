// Arena edges: pin the player against each wall/fog, force every move of every boss part; nothing may leave [L, R] or the floor.
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
await boot(); G.give({ stats: { vig: 60 } });
const out = [];
const check = (tag, b, list) => {
  let bad = [];
  for (const q of list) { if (q.alive === false) continue; if (q.x < b.L - 1 || q.x > b.R + 1) bad.push(`${q.name || q.kind}:x=${Math.round(q.x)}`); if (q.y > b.floor + 0.5) bad.push(`${q.name || q.kind}:y=${Math.round(q.y)}`); }
  return bad;
};
// executioners
for (const k of ['boss:executioners']) delete G.SAVE.flags[k]; G.SAVE.flags['cut:executioners'] = 1;
G.tp('NV5', 20, 10); let b = G.boss; b.activate(); G.step(10);
const moves = ['chop', 'sweep', 'chain', 'leap', 'charge'];
let bad = [];
for (const px of [2.2 * 16, 33.8 * 16]) for (const q of b.parts) for (const m of moves) {
  G.P.x = px; G.P.y = b.floor; for (const o of b.parts) { o.x = clamp(px + (px < 200 ? 90 : -90), b.L, b.R); o.state = 'idle'; }
  q.x = px < 200 ? b.L + 10 : b.R - 10; q.start(m);
  for (let i = 0; i < 90; i++) { G.step(1); G.P.hp = 9999; G.P.x = px; bad.push(...check('ex', b, b.parts)); }
}
out.push(`executioners edge violations: ${bad.length} ${[...new Set(bad)].slice(0, 6)}`);
// vael
for (const k of ['boss:vael']) delete G.SAVE.flags[k]; G.SAVE.flags['cut:vael'] = 1; G.SAVE.flags['cutp2:vael'] = 1; G.SAVE.flags['cutp3:vael'] = 1;
G.tp('NV7', 30, 12); b = G.boss; b.activate(); G.step(10);
bad = [];
const vm = ['combo', 'overhead', 'thrust', 'chain', 'ghostfire', 'sweep', 'leap'];
for (const ph of [1, 2, 3]) {
  if (ph === 2) { b.hp = b.maxHp * 0.6; for (let i = 0; i < 400 && b.phase < 2; i++) { G.step(2); G.P.hp = 9999; } for (let i = 0; i < 200; i++) { G.step(2); G.P.hp = 9999; } }
  if (ph === 3) { b.hp = b.maxHp * 0.25; for (let i = 0; i < 400 && b.phase < 3; i++) { G.step(2); G.P.hp = 9999; } for (let i = 0; i < 200; i++) { G.step(2); G.P.hp = 9999; } }
  for (const px of [1.6 * 16, 43.6 * 16]) for (const m of vm) {
    G.P.x = px; G.P.y = b.floor; b.x = px < 300 ? b.L + 30 : b.R - 30; b.state = 'idle'; b.startMove(m);
    for (let i = 0; i < 130; i++) { G.step(1); G.P.hp = 9999; G.P.x = px; bad.push(...check('v', b, [b, ...(b.court || [])])); }
  }
  out.push(`vael phase ${b.phase} court ${(b.court || []).filter(q => q.alive).length}`);
}
out.push(`vael edge violations: ${bad.length} ${[...new Set(bad)].slice(0, 6)}`);
return out;
