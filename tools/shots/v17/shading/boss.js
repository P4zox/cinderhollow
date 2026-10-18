// Shading phase 1: the Hearthkeeper mid-flurry in its arena (CF8), with hit flashes; plus a 0.55 white flash stress test.
//   tools/shots/v17/boss/run.sh tools/shots/v17/shading/boss.js <outdir> '{"arena":1}'   (SHOT_HTML=... test build)
Object.assign(G.SETTINGS, window.__shSet || {});
const PRE = window.__shPrefix || '';
const world = async (n, hud) => { E(hud ? 'render()' : `vctx.fillStyle = '#050407'; vctx.fillRect(0, 0, view.width, view.height); renderWorld(); presentWorld();`); await snap(PRE + n); };
const out = { summon: E('window.__hk.summon()') };
out.wake = E('window.__hk.wake()');
E('boss.stanceMax = boss.stanceBase = 9999');
let shots = 0, f = 0, flashes = 0;
for (; f < 900 && shots < 3; f++) {
  if (f % 40 === 0) E('window.__hk.front(34)');
  if (f % 9 === 0) E('press("attack")'); else if (f % 9 === 2) E('release("attack")');
  E('window.__hk.play(1); P.hp = D.maxHp');
  const fl = E('boss.flash');
  if (fl > 0.25 && f > 120 && f - flashes > 70) { flashes = f; await world('hk_p1_flash' + shots, false); shots++; }
}
out.p1 = { f, shots };
// phase 3 (the dark arena), a hit flash under the coal light
E('boss.phase = 3; hkDark(true); boss.applySpeed && boss.applySpeed()');
for (let i = 0; i < 120; i++) E('window.__hk.play(1); P.hp = D.maxHp');
E('window.__hk.front(34)'); E('boss.flash = 1'); E('window.__hk.frame(1)'); await world('hk_p3_flash');
E('hkDark(false)');
for (let i = 0; i < 60; i++) E('window.__hk.play(1); P.hp = D.maxHp');
// stress: a plain foe flashing white at 0.55 right under the arena light, + a 0.3 screen flash
E(`(() => { boss.x = boss.L + 20; boss.cool = 99; const e = makeEnemy('hollow_soldier', P.x + 26, P.y, 'shade_t'); enemies.push(e); window.__shE = e; })()`);
for (let i = 0; i < 4; i++) E('window.__hk.frame(1); window.__shE.flash = 0.8; window.__shE.x = P.x + 26');
await world('hk_flash55');
E('flashScreen = 0.3; window.__shE.flash = 0.8'); E('renderWorld()'); await world('hk_flash55_screen');
out.errs = E('window.__hk.errs.slice(0, 5)');
return out;
