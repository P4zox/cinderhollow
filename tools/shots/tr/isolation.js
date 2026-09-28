// save isolation: a real save + old-journey slot + settings exist; enter training via the title, do a lot, exit; every stored byte must match
const E = G.sk.ev, out = [], T = G.trn;
await boot();                                     // a real journey (New Game)
G.give({ cinders: 1234 }); G.SAVE.flags['boss:hound'] = 0; E("SAVE.flags.realMarker = 1; saveGame()");
E("localStorage.setItem(OLD_KEY, JSON.stringify([{ t: 1, data: localStorage.getItem(SAVE_KEY) }]))");   // an old journey too
E("SETTINGS.god = 0; SETTINGS.numbers = 1; saveSettings()");
E("menu = null; state = 'title'; titleBackdrop()"); G.step(5);
const dump = () => { const o = {}; for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); o[k] = localStorage.getItem(k); } return o; };
const before = dump();
out.push('stored keys: ' + Object.keys(before).join(', '));
// enter from the title menu, as a player would
const opts = E('titleOptions()'); out.push('title options: ' + opts.join(' | '));
E(`titleSel = ${opts.indexOf('Training Grounds')}`); G.step(1, [], ['confirm']); G.step(20);
out.push('entered: state=' + G.state + ' room=' + G.room + ' TRAINING.on=' + T.TRAINING.on);
// --- do lots of things
E("SAVE.stats.vig = 99; SAVE.stats.str = 80; trnApplyBuild()");
E("trnLearnAll()"); out.push('skills learned in sandbox: ' + G.SAVE.skills.length);
E("SAVE.weapon = 'starblade'; SAVE.weapons.starblade = 5; SAVE.charmsEq = Object.keys(CHARMS).slice(0, 4); trnApplyBuild()");
E("setDiff(2)"); E("SETTINGS.god = 1; SETTINGS.inffp = 1; SETTINGS.nocd = 1; saveSettings()");
T.open(0); G.step(2); G.step(1, [], ['down']); G.step(1, [], ['right']); G.step(1, [], ['pause']);   // panel in and out
E("menu = { screen: 'pause', tab: 0, sel: 0, trnRet: 2 }; state = 'menu'"); G.step(1, [], ['pause']); out.push('equipment screen closed -> ' + G.state + (G.menu ? ' ' + G.menu.screen : ''));
T.spawn('hollow_soldier', 3); T.spawn('gloom_wisp', 1); G.step(60);
E("SETTINGS.god = 0");
for (const k of ['hound', 'sovereign', 'venn', 'colossus', 'champion']) {    // summon and kill: rewards, endings, timers
  T.summon(k); G.step(30); E("TRN.ohk = true");
  const B = G.boss; for (let i = 0; i < 40 && B.alive; i++) { for (const t of T.targets) try { t.hit({ dmg: 999999, poise: 0, dir: 1, kind: 'light', x: t.x, y: t.y - 20 }); } catch (e) {} G.step(10); if (G.state !== 'play') G.step(1, [], ['pause']); }
  G.step(200); if (G.state !== 'play') { G.step(1, [], ['pause']); G.step(1, [], ['pause']); }
  out.push(`killed ${k}: alive=${B.alive} state=${G.state} flag=${G.SAVE.flags['boss:' + k] ? 1 : 0}`);
}
E("TRN.ohk = false");
// die once: respawn in the chamber, nothing lost
const c0 = G.SAVE.cinders; E("P.hp = 1; hurtPlayer(9999, 1, 'trn-test')"); for (let i = 0; i < 60 && G.state !== 'play'; i++) G.step(10);
G.step(60); out.push(`after death: state=${G.state} room=${G.room} deaths=${G.SAVE.deaths} remnant=${JSON.stringify(G.SAVE.remnant)} cinders ${c0}->${G.SAVE.cinders}`);
E("saveGame(); rest && 0"); E("SAVE.flags.leak = 1; saveGame()");
out.push('blocked writes during training: ' + [...new Set(E('TRN.blocked'))].join(', '));
// --- leave via the panel's Exit to title
T.open(5); G.step(1); const rows = T.rows(5); E(`menu.sel = ${rows.findIndex(r => r.label === 'Exit to title')}`); G.step(1, [], ['confirm']); G.step(10);
out.push('exited: state=' + G.state + ' TRAINING.on=' + T.TRAINING.on + ' god=' + G.SETTINGS.god + ' inffp=' + G.SETTINGS.inffp);
await new Promise(r => setTimeout(r, 12000)); G.step(120);     // let any stray timers (boss item grants at 2.6 s + 2.4 s/item) fire
const after = dump();
const keys = [...new Set([...Object.keys(before), ...Object.keys(after)])];
let same = true; for (const k of keys) { const eq = before[k] === after[k]; if (!eq) same = false; out.push(`${eq ? 'SAME' : 'DIFF'} ${k} (${(before[k] || '').length} -> ${(after[k] || '').length} bytes)`); }
out.push('ALL STORED BYTES IDENTICAL: ' + same);
// and the journey still loads clean
G.continueGame(); G.step(30);
out.push(`continue: room=${G.room} cinders=${G.SAVE.cinders} realMarker=${G.SAVE.flags.realMarker} leak=${G.SAVE.flags.leak} trn=${G.SAVE.trn} skills=${G.SAVE.skills.length} vig=${G.SAVE.stats.vig} diff=${G.SAVE.diff} flags.boss:sovereign=${G.SAVE.flags['boss:sovereign']}`);
return out;
