// Sister Venn boss fight smoke test (agent VN): activates, deals damage, takes damage, changes phase 1->2->3, no errors.
// SHOT_HTML=web/dist/vn.html node tools/shots/shot.js tools/shots/vn/fight.js <out>
await boot(); G.grantTechniques(); G.giveArmory && G.giveArmory();
const F = G.SAVE.flags;
F['boss:sovereign'] = 1; F.venn_betrayed = 1; delete F['boss:venn'];
for (const f of ['cut:', 'cutp2:', 'cutp3:']) F[f + 'venn'] = 1;
const out = [];
G.tp('X5', 20, 10); G.step(10);
let b = G.boss;
if (!b || b.kind !== 'venn') return ['NO VENN BOSS in X5: ' + (b && b.kind)];
out.push(`spawned venn at ${Math.round(b.x)},${Math.round(b.y)} state=${b.state} active=${b.active} player ${Math.round(G.P.x)}`);
for (let i = 0; i < 300 && !b.active; i++) { G.step(4, [b.x < G.P.x ? 'left' : 'right']); G.P.hp = 99999; if (G.state !== 'play') G.step(1, [], ['pause']); }
out.push(`active=${b.active} state=${b.state} phase=${b.phase} hp=${b.hp}/${b.maxHp}`);
const shots = { 1: 0, 2: 0, 3: 0 };
let lastShot = 0; let dealt = 0, taken = 0, phases = new Set(), states = new Set(), atks = new Set();
for (let i = 0; i < 2400 && b.alive; i++) {
  const hp0 = b.hp, php = G.P.hp;
  const d = b.x - G.P.x;
  const watch = (shots[b.phase] || 0) < 2;
  const hold = watch ? (Math.abs(d) < 110 ? [d > 0 ? 'left' : 'right'] : []) : Math.abs(d) > 40 ? [d > 0 ? 'right' : 'left'] : [];
  const tap = (!watch && i % 3 === 0 && Math.abs(d) < 70) ? ['attack'] : [];
  if (G.state !== 'play') { G.step(1, [], ['pause']); continue; }
  G.step(2, hold, tap);
  if (b.hp < hp0) dealt += hp0 - b.hp;
  if (G.P.hp < php) taken++;
  G.P.hp = G.D ? 99999 : 99999; G.P.st = 999;
  phases.add(b.phase); states.add(b.state); if (b.atk) atks.add(b.phase + ':' + b.atk);
  // speed the test up: once she has shown a few attacks in a phase, bring her to the next threshold
  if (i === 500 && b.phase === 1) b.hp = Math.round(b.maxHp * 0.605);
  if (i === 1100 && b.phase === 2) b.hp = Math.round(b.maxHp * 0.205);
  if (i === 1800 && b.phase === 3) b.hp = Math.min(b.hp, 200);
  // photo pass: in each phase, catch her twice mid-attack, visible and not hit-flashing
  if (b.state === 'attack' && b.phase && shots[b.phase] < 2 && b.anim && b.anim.i >= 2 && !b.hidden && !(b.flash > 0)
      && (i - (lastShot || 0)) > 60) {
    shots[b.phase]++; lastShot = i; await snap(`vn_fight_p${b.phase}_${shots[b.phase]}`);
  }
}
await snap('vn_fight_end');
out.push(`dealt=${dealt} hitsTaken=${taken} phases=${[...phases].join(',')} final: alive=${b.alive} state=${b.state} hp=${b.hp}`);
out.push('states=' + [...states].join(','));
out.push('attacks=' + [...atks].join(','));
out.push(`ending=${G.SAVE.ending} flag boss:venn=${F['boss:venn']}`);
out.push((dealt > 0 && taken > 0 && phases.has(2) && phases.has(3)) ? 'PASS' : 'FAIL');
return out;
