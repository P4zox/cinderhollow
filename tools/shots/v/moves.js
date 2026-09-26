// every move in every phase: does it land on a standing player at a sensible range, and can it be rolled through?
await boot();
G.give({ flags: { ...G.SAVE.flags, 'boss:omen': 1, 'boss:sovereign': 1, 'cut:sovereign': 1, venn_betrayed: 1, 'cut:venn': 1, 'cutp2:venn': 1, 'cutp3:venn': 1 } });
G.give({ stats: { ...G.SAVE.stats, vig: 60 } });
G.tp('X5', 20, 10);
G.step(10);
const b = G.boss;
const out = { spawn: { kind: b.kind, x: b.x, s: b.state } };
// wake her
G.P.x = 300; G.step(20);
out.woke = { active: b.active, s: b.state, fog: G.props.filter(p => p.type === 'fog').map(p => p.on()) };
const MOVES = { 1: ['sweep', 'reap', 'rising', 'pillars', 'ring', 'heal'], 2: ['sweep', 'reap', 'rising', 'lance', 'dive', 'pillars', 'ring', 'absorb'], 3: ['flurry', 'blinkcut', 'slam'] };
const RANGE = { sweep: 40, reap: 38, rising: 120, pillars: 100, ring: 60, heal: 120, lance: 70, dive: 110, absorb: 60, flurry: 60, blinkcut: 90, slam: 100 };
const res = [];
let shot = 0;
for (const ph of [1, 2, 3]) {
  b.phase = ph; b.speed = ph === 1 ? 1 : ph === 2 ? 1.12 : 1.3; b.pendingPhase = 0;
  b.hp = Math.round(b.maxHp * (ph === 1 ? 0.8 : ph === 2 ? 0.44 : 0.15));
  for (const m of MOVES[ph]) {
    for (const mode of ['stand', 'roll']) {
      if (m === 'heal' && mode === 'roll') continue;
      b.x = 420; b.y = b.floor; b.airH = 0; b.hidden = false; b.stanceImmune = 99; b.face = 1; b.chain = 5;
      G.P.x = 420 + RANGE[m]; G.P.y = b.floor; G.P.vx = 0; G.P.hp = G.D.maxHp; G.P.inv = 0;
      G.step(1);
      b.cool = 99; b.start(m);
      let minHp = G.P.hp, hits = 0, rolls = 0;
      for (let f = 0; f < 480; f++) {
        const before = G.P.hp;
        const roll = mode === 'roll' && G.vn.danger() && G.P.state !== 'roll';
        if (roll) rolls++;
        G.step(1, [], roll ? ['roll'] : []);
        G.vn.hold();
        if (G.P.hp < before - 1) hits++;
        minHp = Math.min(minHp, G.P.hp);
        if ((f === 30 || f === 55 || f === 80) && mode === 'stand') await snap(`m_p${ph}_${m}_${f}`);
        if (b.state !== 'attack' && f > 200) break;
      }
      res.push(`p${ph} ${m} ${mode}: hits=${hits} dmg=${Math.round(G.D.maxHp - minHp)} rolls=${rolls} bossX=${Math.round(b.x)} y=${Math.round(b.y)} s=${b.state}`);
    }
  }
}
out.res = res;
out.hp = b.hp;
return out;
