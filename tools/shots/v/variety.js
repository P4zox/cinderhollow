// what she chooses when left to herself: 45 s per phase with a player who keeps changing range (god mode)
await boot();
G.give({ flags: { ...G.SAVE.flags, 'boss:omen': 1, 'boss:sovereign': 1, 'cut:sovereign': 1, venn_betrayed: 1, 'cut:venn': 1, 'cutp2:venn': 1, 'cutp3:venn': 1 } });
G.tp('X5', 20, 10); G.step(10);
const b = G.boss; G.P.x = 300; G.step(20);
const out = {};
let shot = 0;
for (const ph of [1, 2, 3]) {
  b.phase = ph; b.speed = [1, 1, 1.12, 1.3][ph]; b.setS('idle', 'idle'); b.picks = {}; b.recent = []; b.queue = []; b.absorbs = ph === 2 ? 0 : 1;
  b.hp = b.maxHp * [0, 0.9, 0.5, 0.15][ph];
  const start = G.vn.VN.log.length;
  let want = 60;
  for (let s = 0; s < 450; s++) {
    if (G.state === 'cut') { G.step(20); continue; }
    G.P.hp = G.D.maxHp; b.hp = Math.max(b.hp, b.maxHp * [0, 0.62, 0.22, 0.05][ph]); b.pendingPhase = 0;
    if (s % 90 === 0) want = [40, 130, 230][Math.floor(s / 90) % 3];
    const d = G.P.x - b.x, hold = [];
    if (Math.abs(d) < want - 20) hold.push(d > 0 ? 'right' : 'left'); else if (Math.abs(d) > want + 20) hold.push(d > 0 ? 'left' : 'right');
    G.step(6, hold, G.vn.danger() ? ['roll'] : []);
    if (s % 75 === 30 && shot < 18) { await snap(`v${ph}_${String(shot).padStart(2, '0')}`); shot++; }
  }
  const log = G.vn.VN.log.slice(start);
  let rep = 0; for (let i = 1; i < log.length; i++) if (log[i] === log[i - 1]) rep++;
  const cnt = {}; for (const m of log) cnt[m] = (cnt[m] || 0) + 1;
  out['p' + ph] = { n: log.length, distinct: Object.keys(cnt).length, backToBack: rep, counts: cnt, seq: log.join(' ') };
}
return out;
