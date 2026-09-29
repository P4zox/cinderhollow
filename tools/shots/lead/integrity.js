// signed saves: clean save verifies; hand edit -> ✦ Tampered (still loads); cheats in a real journey -> ✦ Cheated;
// old unsigned saves load clean; training never marks the real save
await boot();
const E = G.sk.ev, out = [], K = 'cinderhollow_save_v1';
E('saveGame()');
out.push('clean save check: ' + E(`saveCheck(localStorage.getItem('${K}'))`));
// hand edit keeping the old signature
E(`(() => { const s = JSON.parse(localStorage.getItem('${K}')); s.cinders = 999999; localStorage.setItem('${K}', JSON.stringify(s)); })()`);
out.push('edited check: ' + E(`saveCheck(localStorage.getItem('${K}'))`));
E("state = 'title'"); E('continueGame()'); G.step(5);
out.push(`after continue: cinders ${G.SAVE.cinders} tampered ${G.SAVE.tampered} stored ${JSON.parse(localStorage.getItem(K)).tampered} marks ${JSON.stringify(E('saveMarks(SAVE)'))}`);
E('openPauseMenu(); menu.tab = 2'); G.step(2); await snap('status_tampered'); E('menu = null; state = "play"');
// unsigned (pre-update) save loads clean
E(`(() => { const s = JSON.parse(localStorage.getItem('${K}')); delete s.sig; delete s.tampered; delete s.cheated; localStorage.setItem('${K}', JSON.stringify(s)); })()`);
out.push('unsigned check: ' + E(`saveCheck(localStorage.getItem('${K}'))`) + ' -> loads tampered=' + E('loadGame().tampered'));
E("state = 'title'"); E('continueGame()'); G.step(5);
// cheat toggle in a real journey
out.push('before cheat: cheated=' + G.SAVE.cheated);
G.SETTINGS.god = 1; G.step(3); G.SETTINGS.god = 0;
out.push('after god mode: cheated=' + G.SAVE.cheated + ' stored=' + JSON.parse(localStorage.getItem(K)).cheated + ' check=' + E(`saveCheck(localStorage.getItem('${K}'))`));
out.push('journey list line: ' + E(`saveMeta(localStorage.getItem('${K}')).line1`));
// training never marks the real save
E(`(() => { const s = JSON.parse(localStorage.getItem('${K}')); delete s.cheated; delete s.sig; localStorage.setItem('${K}', JSON.stringify(s)); })()`);
const before = localStorage.getItem(K);
E("state = 'title'"); E('trainingStart()'); G.step(10); G.SETTINGS.god = 1; G.step(5); E('saveGame()'); G.SETTINGS.god = 0; E('trainingExit()'); G.step(10);
out.push('training left real save untouched: ' + (localStorage.getItem(K) === before));
return out;
