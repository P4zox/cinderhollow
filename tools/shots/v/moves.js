// every move and pattern in every phase: does it land on a standing player at a sensible range, and can it be avoided?
await boot();
G.give({ flags: { ...G.SAVE.flags, 'boss:omen': 1, 'boss:sovereign': 1, 'cut:sovereign': 1, venn_betrayed: 1, 'cut:venn': 1, 'cutp2:venn': 1, 'cutp3:venn': 1 } });
G.give({ stats: { ...G.SAVE.stats, vig: 60 } });
G.tp('X5', 20, 10); G.step(10);
const b = G.boss;
G.P.x = 300; G.step(20);
const ONLY = null;
const MOVES = {
  1: ['sweep', 'reap', 'string3', 'string', 'spin', 'vault', 'hook', 'lowsweep', 'thrust', 'rising', 'pillars', 'ring', 'heal'],
  2: ['string', 'spin', 'whip', 'nova', 'gust', 'lines', 'rows', 'cage', 'lance', 'divecombo', 'vault', 'hook', 'absorb'],
  3: ['flurry', 'grab', 'spin', 'string', 'cut3', 'blinkcut', 'blink3', 'blinkfall', 'blinkx', 'dance', 'beam', 'ashstorm', 'slam', 'allout'] };
const RANGE = { sweep: 40, reap: 38, string3: 40, string: 40, spin: 36, vault: 120, hook: 60, lowsweep: 44, thrust: 46, rising: 120, pillars: 100, ring: 60, heal: 120,
  whip: 60, nova: 50, gust: 80, lines: 90, rows: 90, cage: 60, lance: 70, divecombo: 110, absorb: 60,
  flurry: 60, grab: 40, cut3: 40, blinkcut: 90, blink3: 90, blinkfall: 90, blinkx: 50, dance: 90, beam: 120, ashstorm: 80, slam: 100, allout: 50 };
const res = [];
for (const ph of [1, 2, 3]) {
  b.phase = ph; b.speed = ph === 1 ? 1 : ph === 2 ? 1.12 : 1.3; b.pendingPhase = 0;
  for (const m of MOVES[ph]) {
    for (const mode of ['stand', 'dodge']) {
      if (m === 'heal' && mode === 'dodge') continue;
      b.hp = Math.round(b.maxHp * (ph === 1 ? 0.8 : ph === 2 ? 0.5 : 0.15));
      b.x = 420; b.airH = 0; b.hidden = false; b.stanceImmune = 99; b.face = 1; b.chain = 5; b.queue = [];
      G.vn.VN.shots.length = 0; G.vn.VN.ash.length = 0; G.vn.VN.echoes.length = 0;
      G.P.x = 420 + RANGE[m]; G.P.vx = 0; G.P.hp = G.D.maxHp; G.P.inv = 0; G.P.face = -1;
      for (let k = 0; k < 40; k++) { G.vn.hold(); G.step(1); }
      G.P.x = 420 + RANGE[m]; G.P.hp = G.D.maxHp; G.P.inv = 0; G.P.face = -1; b.x = 420; b.face = 1;
      b.cool = 99; b.begin(m);
      let minHp = G.P.hp, hits = 0, rolls = 0, minX = 1e9, maxX = -1e9, maxY = -1e9, frames = 0, seen = new Set([b.atk]);
      for (let f = 0; f < 900; f++) {
        const before = G.P.hp;
        let hold = [], tap = [];
        if (mode === 'dodge') {
          const bs = G.vn.beam();
          if (bs === 'lock' || bs === 'fire') hold = [G.P.x < b.x ? 'left' : 'right'];   // step out of the locked line (away: it ends at your feet)
          else if (m === 'spin' && b.atk === 'spin' && b.anim.i <= 3) hold = [G.P.x < b.x ? 'left' : 'right'];   // back out of the circle
          else if (G.vn.danger() && G.P.state !== 'roll') { tap = ['roll']; rolls++; }
          if (m === 'ashstorm' && !tap.length && !hold.length) { const a = G.vn.VN.ash.find(a => !a.fall && Math.abs(a.x - G.P.x) < 12 && a.delay < 0.6); if (a) hold = [G.P.x < 380 ? 'right' : 'left']; }
        }
        G.step(1, hold, tap);
        G.vn.hold();
        if (b.state === 'attack') seen.add(b.atk);
        if (G.P.hp < before - 1) hits++;
        minHp = Math.min(minHp, G.P.hp);
        minX = Math.min(minX, b.x); maxX = Math.max(maxX, b.x); maxY = Math.max(maxY, b.y);
        if ((f === 40 || f === 90) && mode === 'stand') await snap(`m_p${ph}_${m}_${f}`);
        frames = f;
        if (b.state !== 'attack' && !b.queue.length && f > 20 && !G.vn.busy()) break;
      }
      const out = minX < b.L - 0.5 || maxX > b.R + 0.5 || maxY > b.floor + 0.01;
      res.push(`p${ph} ${m} ${mode}: hits=${hits} dmg=${Math.round(G.D.maxHp - minHp)} rolls=${rolls} frames=${frames} steps=${[...seen].join('>')} ${out ? 'OUT-OF-ARENA' : ''} end=${b.state}`);
      G.P.hp = G.D.maxHp; if (G.P.state === 'dead') return res;
    }
  }
}
return res;
