// bosses rise to meet an over-strong build: First Ember and Gravetusk vs typical / maxed / weak builds; setting off = no change
await new Promise(r => setTimeout(r, 300));
const T = G.trn, E = G.sk.ev, out = [];
T.start(); G.step(10);
const build = (lvlStats, up, skills) => { E(`SAVE.weapon = 'longsword'; SAVE.weapons.longsword = ${up}`); G.give({ stats: lvlStats, skills }); E('refreshDerived(false)'); };
const typical = st => { const b = E('({...BASE_STATS})'), order = ['vig','str','dex','end','vig','str','dex','mnd']; const L = Math.round(5 + 6 * st); for (let i = 0, n = L - E('levelOf(BASE_STATS)'); i < n; i++) b[order[i % 8]]++; return b; };
const all = E('SKILLS.map(s => s.id)');
const cases = [
  ['first_ember typical (L83 +5, 65% tree)', 'first_ember', typical(13), 5, all.slice(0, Math.round(all.length * 0.55))],
  ['first_ember maxed (all 99, +5, full tree)', 'first_ember', { vig: 99, mnd: 99, end: 99, str: 99, dex: 99, fth: 99 }, 5, all],
  ['first_ember weak (L30 +2)', 'first_ember', typical(4), 2, []],
  ['hound typical (L11 +1)', 'hound', typical(1), 1, []],
  ['hound overlevelled (L60 +5)', 'hound', typical(9), 5, all.slice(0, 20)],
];
for (const [label, kind, st, up, sk] of cases) {
  build(st, up, sk);
  const a = E(`adaptFor('${kind}')`);
  T.summon(kind); G.step(4);
  out.push(`${label}: light ${Math.round(G.D.light)} hp ${G.D.maxHp} -> boss HP x${a.hp.toFixed(2)} dmg x${a.dmg.toFixed(2)}  maxHp ${G.boss && G.boss.maxHp}`);
  T.clear(); G.step(3);
}
G.SETTINGS.adapt = 0; build({ vig: 99, mnd: 99, end: 99, str: 99, dex: 99, fth: 99 }, 5, all);
T.summon('first_ember'); G.step(4); out.push(`setting off, maxed: ${JSON.stringify(E("adaptFor('first_ember')"))} maxHp ${G.boss.maxHp}`); T.clear(); G.SETTINGS.adapt = 1;
// damage actually scales: a boss hit on the maxed build
build({ vig: 99, mnd: 99, end: 99, str: 99, dex: 99, fth: 99 }, 5, all); T.summon('first_ember'); G.step(4); G.boss.active = true;
const hp0 = G.P.hp; E(`P.inv = 0; P.lastHit = null; hurtPlayer(100, 1, 'adapt' + time, { src: boss })`);
out.push(`100 raw boss dmg on maxed build -> lost ${Math.round(hp0 - G.P.hp)} (adapt dmg x${E('adaptCur.dmg').toFixed(2)})`);
return out;
