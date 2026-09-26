// every move: does it land on a player who stands there, and can a simple policy dodge it?
await boot(); window.__godS = false;
G.give({ items: { wings: 1, talon: 1 }, stats: { vig: 40, mnd: 15, end: 40, str: 22, dex: 18, fth: 10 } });
G.SAVE.flags['cut:astrel'] = 1; G.SAVE.flags['cutp2:astrel'] = 1; G.SAVE.flags['cutp3:astrel'] = 1;
G.tp('SF7', 12, 16); S(10);
for (let i = 0; i < 200 && !(G.boss && G.boss.active); i++) S(2, ['right']);
const b = G.boss; for (let i = 0; i < 400 && (b.introT > 0 || b.state === 'intro'); i++) S(1); S(10);
b.cons = null; b.hazT = 999;
const kd = window.__kd;
const out = {};
async function trial(name, setup, dodge, frames = 150, dist = 40) {
  const res = {};
  for (const mode of ['stand', 'dodge']) {
    hazards_clear(); b.state = 'idle'; b.cool = 99; b.hp = b.maxHp * (setup.p2 ? 0.45 : 0.9); b.phase = setup.p2 ? 2 : 1;
    b.x = b.mid; b.y = b.floor; b.face = -1; G.P.x = b.x - dist; G.P.y = b.floor; G.P.vx = 0; G.P.vy = 0; G.P.hp = G.D.maxHp; G.P.inv = 0; G.P.st = G.D.maxSt;
    S(2); await flush();
    const seen = new WeakSet(); for (const f of kd.fx) seen.add(f);
    setup.go(); let hits = 0, taken = 0, rollAt = -1;
    for (let i = 0; i < frames; i++) {
      let hold = [], tap = [];
      if (mode === 'dodge') [hold, tap] = dodge(i, seen);
      const h0 = G.P.hp; S(1, hold, tap); if (G.P.hp < h0) { hits++; taken += h0 - G.P.hp; }
      G.P.hp = Math.max(G.P.hp, 1); b.cool = 99; if (b.state === 'idle' && i > 20 && !setup.hazard) break;
    }
    res[mode] = hits + 'x/' + Math.round(taken);
  }
  out[name] = res.stand + ' | dodge ' + res.dodge;
}
function hazards_clear() { for (const h of window.__kd.hazards) h.life = 0; S(1); }
const awayDir = () => (G.P.x < b.x ? 'left' : 'right');
// melee dodge: roll away the moment her telegraph glints, then keep running away
const rollOnTele = (i, seen) => { for (const f of kd.fx) if (!seen.has(f)) { seen.add(f); if (f.name === 'telegraph') return [[awayDir()], ['roll']]; } return [[awayDir()], []]; };
const melee = m => ({ go: () => b.start(m) });
await trial('combo', melee('combo'), rollOnTele);
await trial('flurry', melee('flurry'), rollOnTele);
await trial('thrust', melee('thrust'), rollOnTele);
await trial('upslash_air', { go: () => { G.P.vy = -250; G.P.y -= 4; b.start('upslash'); } }, rollOnTele, 150, 24);
await trial('riposte', melee('riposte'), rollOnTele);
await trial('leap', melee('leap'), (i, seen) => [[awayDir()], i === 30 ? ['roll'] : []], 150, 90);
await trial('dash', { go: () => b.startDash() }, (i, seen) => [[], b.dsh && b.dsh.phase === 'go' && Math.abs(b.x - G.P.x) < 60 && !window.__rolled ? (window.__rolled = 1, ['roll']) : []], 120, 90); window.__rolled = 0;
await trial('wave+crescent', melee('wave'), (i, seen) => { const c = kd.hazards.find(h => h.dir && h.h === 34); return [c && Math.abs(c.x - G.P.x) < 120 ? ['jump'] : [], c && Math.abs(c.x - G.P.x) < 75 && G.P.ground ? ['jump'] : []]; }, 150, 120);
await trial('rain', { go: () => b.startCast('rain'), hazard: true }, (i) => [[i < 60 ? 'left' : 'left'], []], 170, 60);
await trial('well', { go: () => b.startCast('well'), hazard: true }, (i) => { const w = kd.hazards.find(h => h.w === 60); return [[w ? (G.P.x < w.x ? 'left' : 'right') : awayDir()], []]; }, 240, 80);
const hz = (fn, p2 = true) => ({ go: fn, hazard: true, p2 });
const fleeMarks = (i) => { const ms = window.__sf.SFA.marks.filter(m => Math.abs(m.x - G.P.x) < m.w / 2 + 16); if (!ms.length) return [[], []]; const m = ms[0]; return [[m.x > G.P.x ? 'left' : 'right'], []]; };
for (const pat of ['barrage', 'march', 'pincer', 'ring', 'great']) {
  await trial('meteor_' + pat, hz(() => { b.metDir = 1; const saved = Object.getPrototypeOf(b).meteorPattern; const rr = Math.random; const order = ['barrage', 'march', 'pincer', 'ring', 'great']; let n = 0; b.lastMet = null; Math.random = () => { n++; return n === 1 ? (order.indexOf(pat) + 0.5) / 5 * 0.999 : rr(); }; try { saved.call(b); } finally { Math.random = rr; } }),
    pat === 'ring' ? (() => [[], []]) : pat === 'pincer' ? ((i) => [[i < 90 ? 'left' : []].flat(), []]) : pat === 'great' ? ((i) => { const w = kd.hazards.find(h => h.dir && h.h === 14 && Math.abs(h.x - G.P.x) < 40); return [[i < 70 ? 'left' : [], w ? 'jump' : []].flat(), w && G.P.ground ? ['jump'] : []]; }) : fleeMarks, 220, 60);
}
await trial('hunter', hz(() => b.hunterVolley(), false), (i) => [[i % 60 < 30 ? 'left' : 'right'], []], 150, 60);
await trial('serpent', hz(() => b.serpent(), false), (i) => { const h = kd.hazards.find(q => q.yAt); if (!h) return [[], []]; if (h.goal === undefined) { let best = null; for (let x = G.P.x - 140; x <= G.P.x + 140; x += 2) { if (b.floor - h.yAt(x) > 44 && (best === null || Math.abs(x - G.P.x) < Math.abs(best - G.P.x))) best = x; } h.goal = best ?? G.P.x; } const d = h.goal - G.P.x; return [[Math.abs(d) > 3 ? (d > 0 ? 'right' : 'left') : []].flat(), []]; }, 420, 60);
await trial('crown', hz(() => b.crownPillars(), false), fleeMarks, 150, 60);
return out;
