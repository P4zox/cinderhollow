// WC: feel must not change damage, reach or timing. Same seeded fight with feel off / on (sound muted, feel has its own RNG).
// Logs every *unfrozen* game frame (player state, anim frame, x, foe HP) and every hit's damage; the logs must match.
// With hitstop tuning on, only the number of frozen frames may differ (hitstop freezes both sides equally).
await boot(); G.giveArmory(); G.grantTechniques(); G.SETTINGS.god = 1;
const F = G.feel, ev = F.ev; ev('muted = true');
const seed = s => () => 0.5;   // a constant: every damage roll is exactly 1.0x and nothing depends on how many draws came before
const R0 = Math.random, PN = performance.now.bind(performance); window.__rs = seed; let fakeT = 1e6;
// the input buffer runs on wall-clock time: give it a fake clock that ticks 1/60 s per stepped frame (frozen frames included)
performance.now = () => fakeT;
const WPN = ['longsword', 'dagger', 'greatsword', 'spear', 'katana', 'quarterstaff', 'knight_shield', 'twinfangs', 'briar_scythe', 'headsman_chain', 'kalden', 'colossus_hammer'];
const script = f => { const k = f % 30; return k === 0 || k === 10 || k === 20 ? ['attack'] : f % 150 === 75 ? ['heavy'] : f % 150 === 110 ? ['jump'] : f % 150 === 118 ? ['attack'] : f % 150 === 130 ? ['attack'] : []; };
const fight = (w, off, hs) => {
  ev(`FEEL.off = ${off}; FEEL.hs = ${hs}`); G.SAVE.weapon = w; ev('refreshDerived()');
  Math.random = seed(1234); G.tp('R1', 20, 10); G.step(40); G.P.face = 1;
  ev('clearBuffer(); held.clear(); hitstop = 0; shake = 0; slowmo = 0; time = 1000; particles = []; fx = []; projectiles = []; hazards = []; Object.assign(P, { x: 328, vx: 0, vy: 0, combo: 0, comboStep: -1, charge: 0, charged: false, airN: 0, airLock: false, smashN: 0, smashLock: false, cds: {}, inv: 0, st: D.maxSt, fp: D.maxFp, empower: 0, twinBuff: false, gcT: 0, bsT: 0, backRoll: 0, pogoed: false, lastHit: undefined, sigCharge: 0 }); setP("idle", "idle", true); Math.random = window.__rs(1234); enemyId = 1; if (typeof hazardId !== "undefined") hazardId = 0; for (const k of Object.keys(brkHits)) delete brkHits[k];');
  ev('enemyId = 1'); ev(`(() => { for (const e of enemies) e.gone = true; enemies = enemies.filter(e => !e.gone);
    for (const [t, dx] of [['grave_knight', 26], ['hollow_soldier', 44], ['rot_hulk', 60]]) { const e = new Enemy(t, P.x + dx, P.y, 'wci' + dx); e.hp = e.maxHp = 1e6; enemies.push(e); } })()`);
  const log = [], dmg = []; let frozen = 0;
  ev('window.__dmgLog = []; if (!window.__hooked) { window.__hooked = 1; HOOKS.strike.push((t, info) => window.__dmgLog.push((t.type || t.kind || t.prop || "?") + "@" + window.__f + ":" + Math.round(info.dmg * 100) / 100)); }');
  // inputs and the input-buffer clock follow *unfrozen* frames, so a longer or shorter hitstop can't shift when a key lands
  for (let f = 0, u = 0; u < 600 && f < 2000; f++) {
    window.__f = u; const fr = ev('hitstop > 0'); G.step(1, [], fr ? [] : script(u));
    if (fr) { frozen++; continue; }
    fakeT += 1000 / 60; u++;
    log.push(`${G.P.state}:${G.P.anim.i}:${Math.round(G.P.x * 10)}:${Math.round(G.P.y * 10)}:` + ev('enemies.map(e => Math.round(e.hp) + "/" + e.state).join(",")'));
  }
  Math.random = R0;
  return { log, dmg: ev('window.__dmgLog.slice()'), frozen };
};
const out = [];
for (const w of WPN) {
  const a = fight(w, true, false), a2 = fight(w, true, false), b = fight(w, false, false), c = fight(w, false, true);
  const diff = (x, y) => { const n = Math.min(x.log.length, y.log.length); for (let i = 0; i < n; i++) if (x.log[i] !== y.log[i]) return `frame ${i}: ${x.log[i]} vs ${y.log[i]}`; return x.log.length === y.log.length ? 'same' : 'len ' + x.log.length + ' vs ' + y.log.length; };
  const sum = d => Math.round(d.reduce((s, v) => s + +String(v).split(':').pop(), 0));
  if (window.__dump === w) out.push(JSON.stringify([a.dmg, b.dmg]));
  out.push(`${w.padEnd(16)} determinism: ${diff(a, a2).slice(0, 50)} hits ${a.dmg.length}/${a2.dmg.length} dmg ${sum(a.dmg)}/${sum(a2.dmg)} | off→on(no hitstop change): ${diff(a, b)} hits ${a.dmg.length}/${b.dmg.length} dmg ${sum(a.dmg)}/${sum(b.dmg)} | on+hitstop: unfrozen ${diff(a, c).slice(0, 60)} hits ${c.dmg.length} dmg ${sum(c.dmg)} frozen ${a.frozen}→${c.frozen}`);
}
ev('FEEL.off = false; FEEL.hs = true; muted = false'); performance.now = PN;
return out;
