// Shading phase 3: how many big boss frames are drawn flat (no normals yet) in the first ~20 s of the Hearthkeeper fight, with
// the pre-warm on (default) or off (window.__noWarm). Real clock (the normal budget is per frame).  node ../../shot.js warm.js <out>
await boot(); G.grantTechniques(); G.SETTINGS.god = 1;
const E = G.sk.ev;
E('window.requestAnimationFrame = () => 0');
E(`(() => { let seed = 5; Math.random = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; })()`);
if (window.__noWarm) E('LXN_WARM.per = 0');
E(`delete SAVE.flags['boss:hearthkeeper']; SAVE.flags['cut:hearthkeeper'] = 1; boss = null; enterRoom('CF8', 30 * TILE + 8, 18 * TILE, { quiet: true })`);
const o = [], snap0 = () => E('[LXN.miss || 0, LXN.gen, LXN.q.length, LXN.warmed || 0].join(" ")');
for (let i = 0; i < 5; i++) G.step(1);
o.push('enter ' + snap0());
for (let i = 0; i < 900; i++) {   // walk up to it, wake it, fight (its intro plays inside this)
  const b = G.boss; if (!b) break;
  E(`(() => { const b = boss; if (!b.active) P.x += b.x < P.x ? -2 : 2; else { P.x = clamp(b.x + b.face * 50, TILE + 10, room.pw - TILE - 10); P.hp = D.maxHp; } if (state === 'menu' || state === 'dialog') { menu = null; dialog = null; state = 'play'; } })()`);
  G.step(1, [], i % 9 === 0 ? ['attack'] : []);
  if (i === 120 || i === 400 || i === 899) o.push(`f${i} ` + snap0() + ' boss ' + E('[boss.state, boss.phase, boss.tag || ""].join(" ")'));
}
E('boss.phase = 3; hkDark(true); boss.applySpeed && boss.applySpeed()');
for (let i = 0; i < 300; i++) { E('P.hp = D.maxHp; if (state === "menu" || state === "dialog") { menu = null; dialog = null; state = "play"; }'); G.step(1); }
o.push('p3 +300 ' + snap0());
return o;
