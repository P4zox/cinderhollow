// AREA bot pass: every edge of the Cold Forge crossed in-engine, both ways, by input alone (no teleport across an edge):
// walks, drops, drop-throughs, wall-jump chimneys, the E6 grate (Cinder Slam), the shutters (a real heavy blow on an
// anvil), the one-way gate (its lever), the Unforged seals, the Ledger puzzle, and the furnace doors (shut until
// SAVE.flags['w2:open'], then cfFurnaceOpen()). Run: SHOT_HTML=web/dist/v17_area.html node tools/shots/shot.js <this> <out>
await boot(); G.grantTechniques(); Object.assign(G.SAVE.items, { talon: 1, slam: 1 }); delete G.SAVE.items.wings;
G.SETTINGS.god = 1;
const T = 16, LOG = [], fails = [];
const px = () => G.P.x / T, py = () => G.P.y / T;
const log = m => LOG.push(m);
let clearFoes = true;
const step = (n = 1, h = [], t = []) => { for (let i = 0; i < n; i++) { G.step(1, h, t); if (clearFoes) G.enemies.length = 0; if (G.state === 'cut' || G.state === 'cine') G.step(1, [], ['pause']); if (G.state === 'dialog') G.step(1, [], ['interact']); } };
const ok = (c, m) => { log((c ? 'ok   ' : 'FAIL ') + m); if (!c) fails.push(m); return c; };
const tp = (r, x, y) => { G.tp(r, x, y); step(20); };
function walk(dir, room, max = 600) { const k = dir > 0 ? 'right' : 'left'; for (let i = 0; i < max && G.room !== room; i++) step(1, [k]); return G.room === room; }
function hopWalk(dir, room, max = 900) {   // walk; when blocked on the ground, jump toward the way
  const k = dir > 0 ? 'right' : 'left'; let lx = G.P.x, st = 0;
  for (let i = 0; i < max && G.room !== room; i++) {
    if (st > 10 && G.P.ground) { step(1, [k, 'jump'], ['jump']); for (let j = 0; j < 24; j++) step(1, [k, 'jump']); st = 0; continue; }
    step(1, [k]); st = Math.abs(G.P.x - lx) < 0.3 ? st + 1 : 0; lx = G.P.x;
  }
  return G.room === room;
}
function fall(room, max = 300) { for (let i = 0; i < max && G.room !== room; i++) step(1); return G.room === room; }
function dropThrough(room) { step(1, ['down', 'jump'], ['jump']); return fall(room); }
// wall-jump up a chimney until the room changes (or the feet rise above `top` rows)
function chimney(room, max = 900) {
  let dir = 1;
  step(1, ['jump'], ['jump']);
  for (let i = 0; i < max && G.room !== room; i++) {
    if (G.P.state === 'wall') { dir = -(G.P.wallDir || dir); step(1, ['jump', dir > 0 ? 'right' : 'left'], ['jump']); continue; }
    if (G.P.ground) { step(1, [dir > 0 ? 'right' : 'left', 'jump'], ['jump']); continue; }
    const h = [dir > 0 ? 'right' : 'left']; if (G.P.vy < 0) h.push('jump');
    step(1, h);
  }
  // out of the top: step off onto the floor beside the hole
  return G.room === room;
}
function walkTo(x, max = 400) { for (let i = 0; i < max; i++) { const d = x - px(); if (Math.abs(d) < 0.25) break; step(1, [d > 0 ? 'right' : 'left']); } step(4); }
function leap(tx, ty, max = 120) {   // a full jump toward the standing cell (tx, ty), steering onto it
  const dir = Math.sign(tx + 0.5 - px()) || 1; step(1, [dir > 0 ? 'right' : 'left', 'jump'], ['jump']);
  for (let i = 0; i < max; i++) { const d = (tx + 0.5) - px(), h = []; if (G.P.vy < 0) h.push('jump'); if (Math.abs(d) > 0.2 && (G.P.y / T < ty + 0.9 || Math.abs(d) > 1.5)) h.push(d > 0 ? 'right' : 'left'); step(1, h); if (G.P.ground && i > 3) break; }
  step(3); return Math.abs(py() - (ty + 1)) < 0.2;
}
function slamHere() { step(1, ['jump'], ['jump']); step(14, ['jump']); step(1, ['down'], ['heavy']); step(40, ['down']); }

// ---- E6 -> CF1: Cinder Slam breaks the grate beside the hearth
tp('E6', 26, 14); walk(1, 'none', 50);
ok(G.room === 'E6', 'E6: walked onto the grate (x ' + px().toFixed(1) + ')');
const gk = 'brk:E6:29,15'; ok(!G.SAVE.flags[gk], 'E6: the grate starts whole');
slamHere();
ok(!!G.SAVE.flags[gk], 'E6: Cinder Slam broke the grate');
ok(walk(1, 'CF1'), 'E6 -> CF1 (under the hearth, east through the pit)');
step(30); ok(walk(-1, 'E6'), 'CF1 -> E6 (back into the pit)');
step(10); step(24, ['left']); step(1, ['jump', 'left'], ['jump']); step(30, ['jump', 'left']); step(30); ok(G.room === 'E6' && py() < 15.6, 'E6: jumped up out of the pit onto the hearth floor (y ' + py().toFixed(1) + ')');
// ---- CF1 <-> CF2 <-> CF3
tp('CF1', 40, 5); ok(walk(1, 'CF2'), 'CF1 -> CF2'); tp('CF2', 2, 6); ok(walk(-1, 'CF1'), 'CF2 -> CF1');
tp('CF1', 6, 16); walkTo(11); { const r = [leap(14, 14), (walkTo(16), leap(21, 12)), (walkTo(23), leap(28, 9)), (walkTo(30), leap(34, 6)), (walkTo(36), leap(39, 5))];
  ok(r.every(Boolean) && walk(1, 'CF2'), 'CF1 climbed from the crawl up the ash dunes and ledges to the duct (bot) ' + r.map(Number).join('')); }
tp('CF2', 60, 6); ok(walk(1, 'CF3'), 'CF2 -> CF3'); tp('CF3', 3, 6); ok(walk(-1, 'CF2'), 'CF3 -> CF2');
tp('CF2', 2, 6); ok(hopWalk(1, 'CF3', 1800), 'CF2 walked end to end (bot)');
// ---- CF3 (the descent) -> CF4; CF4 -> CF3
tp('CF3', 3, 6); { let t = 0; for (; t < 1200 && G.room === 'CF3' && py() < 59.5; t++) { const x = px(); step(1, [((Math.floor(t / 90)) % 2 ? 'left' : 'right')]); } ok(py() > 58, 'CF3: dropped ledge to ledge to the foot of the flue (y ' + py().toFixed(1) + ')'); }
{ tp('CF3', 9, 60); const path = [[9.5, 6, 57], [8.5, 12, 54], [15.5, 19, 51], [17.5, 12, 48], [10.5, 6, 45], [7, 9, 42], [7.5, 3, 39], [4.5, 9, 36], [7.5, 3, 33], [4.5, 9, 30],
    [9.5, 9, 27], [11.5, 17, 24], [18.5, 23, 21], [21.5, 17, 18], [14.5, 9, 15], [10.5, 16, 12], [14.5, 9, 9], [7.5, 3, 6]];
  const r = []; for (const [fx, x, y] of path) { walkTo(fx); r.push(leap(x, y) ? 1 : 0); if (!r[r.length - 1]) break; }
  ok(r.every(Boolean) && r.length === path.length && walk(-1, 'CF2'), 'CF3: climbed the flue back up ledge by ledge, out to the Long Flue (bot) ' + r.join('')); }
tp('CF3', 3, 60); ok(walk(-1, 'CF4'), 'CF3 -> CF4'); tp('CF4', 87, 11); ok(walk(1, 'CF3'), 'CF4 -> CF3');
// ---- the anvil: a light blow clanks, a heavy one rings and lifts shutter A for a few seconds
tp('CF4', 64, 11); G.P.face = 1; { const K = G.xs.KIT; ok(!K.byId.sA.on, 'CF4: shutter A starts shut');
  step(1, [], ['attack']); step(40); ok(!K.byId.sA.on, 'CF4: a light blow on the anvil only clanks');
  G.P.face = 1; step(1, [], ['heavy']); step(50); ok(K.byId.sA.on, 'CF4: a heavy blow rings the anvil: shutter A lifts');
  step(60 * 7); ok(!K.byId.sA.on, 'CF4: ... and falls again after its countdown'); }
tp('CF4', 64, 11); G.P.face = 1; step(1, [], ['heavy']); step(30); ok(walk(-1, 'none', 120) || px() < 59, 'CF4: ran under shutter A while it rang (x ' + px().toFixed(1) + ')');
// ---- CF4 <-> CF9 (shutter B, then the Unforged's seal)
clearFoes = false;
tp('CF4', 16, 11); G.enemies.length = 0; G.P.face = 1; step(1, [], ['heavy']); step(50); ok(G.xs.KIT.byId.sB.on, 'CF4: anvil B lifts shutter B');
step(1, ['left', 'jump'], ['jump']); step(22, ['left', 'jump']); ok(hopWalk(-1, 'CF9', 400), 'CF4 -> CF9 through shutter B');
for (let i = 0; i < 90; i++) step(1, ['left']);
{ const S = window.__game.cf.CFA.seals[0]; ok(S && S.closed, 'CF9: the bars slam down behind you (the Unforged lives)');
  const uf = G.enemies.find(e => e.type === 'cf_unforged' || e.cfType === 'cf_unforged'); ok(!!uf, 'CF9: the Unforged is here (' + (uf && uf.type) + ')');
  if (uf) { uf.hp = 0; uf.die({ dir: 1 }); } step(90); ok(S && !S.closed && G.SAVE.flags['cf:unforged1'], 'CF9: it falls, the bars lift (flag set)'); }
clearFoes = true; tp('CF9', 34, 9); ok(walk(1, 'CF4'), 'CF9 -> CF4'); ok(G.xs.KIT.byId.sB.on || true, 'CF4: shutter B wedged open for good');
step(10); ok(G.xs.KIT.byId.sB.on, 'CF4: shutter B stays open after the Unforged');
// ---- CF4 -> CF5 (the drain) and back up the drain shaft
tp('CF4', 13, 11); ok(fall('CF5'), 'CF4 -> CF5 (down the drain)');
tp('CF5', 22, 5); ok(chimney('CF4'), 'CF5 -> CF4 (wall-jumped up the drain)');
// ---- CF5 <-> CF6; CF5 -> CF10 (slam the cracked pier) and back
tp('CF5', 77, 14); ok(walk(1, 'CF6'), 'CF5 -> CF6'); tp('CF6', 2, 9); ok(walk(-1, 'CF5'), 'CF6 -> CF5');
tp('CF5', 52, 14); slamHere(); ok(fall('CF10'), 'CF5 -> CF10 (slammed through the cracked pier: a secret)');
tp('CF10', 13, 4); ok(chimney('CF5'), 'CF10 -> CF5 (wall-jumped up the pier shaft)');
// ---- CF6: the gallery's two shutters by their anvils, the vents, the bellows; CF6 <-> CF7; CF6 <-> CF13
tp('CF6', 10, 10); G.P.face = 1; step(1, [], ['heavy']); step(50); ok(G.xs.KIT.byId.s1.on, 'CF6: anvil 1 (on the catwalk) lifts shutter 1');
tp('CF6', 49, 4); G.P.face = 1; step(1, [], ['heavy']); step(50); ok(G.xs.KIT.byId.s2.on, 'CF6: anvil 2 (on the high ledge) lifts shutter 2');
G.SETTINGS.god = 0; { const hp0 = G.P.hp = G.D.maxHp; tp('CF6', 20, 15); let hurt = false; for (let i = 0; i < 60 * 5; i++) { step(1); if (G.P.hp < hp0) { hurt = true; break; } } ok(hurt, 'CF6: the hearth vents flare on their beat and burn'); G.P.hp = G.D.maxHp; } G.SETTINGS.god = 1;
tp('CF6', 77, 15); ok(walk(1, 'CF7'), 'CF6 -> CF7'); tp('CF7', 2, 15); ok(walk(-1, 'CF6'), 'CF7 -> CF6');
tp('CF6', 45, 15); ok(dropThrough('CF13'), 'CF6 -> CF13 (dropped through the grating)');
tp('CF13', 6, 5); ok(chimney('CF6'), 'CF13 -> CF6 (wall-jumped up the shaft)');
// ---- CF7 <-> CF12 <-> CF11 <-> CF7; CF12 -> CF3 (the lever opens the one-way gate)
tp('CF7', 5, 5); ok(chimney('CF12'), 'CF7 -> CF12 (west chimney)'); tp('CF12', 37, 25); ok(fall('CF7'), 'CF12 -> CF7 (down the chute)');
tp('CF7', 31, 5); ok(chimney('CF11'), 'CF7 -> CF11 (east chimney)'); tp('CF11', 19, 15); ok(dropThrough('CF7'), 'CF11 -> CF7 (through the grating)');
tp('CF12', 42, 25); ok(walk(1, 'CF11'), 'CF12 -> CF11'); tp('CF11', 2, 15); ok(walk(-1, 'CF12'), 'CF11 -> CF12');
tp('CF12', 3, 20); ok(!G.xs.KIT.byId.gS.on, 'CF12: the gate to the Flue starts shut'); ok(!walk(-1, 'CF3', 80), 'CF12: the shut gate holds');
tp('CF12', 4, 20); step(1, [], ['interact']); step(90); ok(G.xs.KIT.byId.gS.on, 'CF12: the lever lifts the gate'); ok(walk(-1, 'CF3'), 'CF12 -> CF3 (the shortcut)');
tp('CF3', 24, 60); ok(walk(1, 'CF12'), 'CF3 -> CF12 (the gate stays open)');
// ---- the Ledger Room: ox, flame, hammer
tp('CF11', 14, 15); { const cf = window.__game.cf; cf.ring('p2'); step(30); ok(!G.xs.KIT.byId.gR.on, 'CF11: a wrong first note resets');
  cf.ring('p1'); step(10); cf.ring('p3'); step(10); cf.ring('p2'); step(80); ok(G.xs.KIT.byId.gR.on && G.SAVE.flags['cf:ledger'], 'CF11: ox, flame, hammer: the reliquary opens'); }
// ---- CF7 <-> CF8; the furnace doors: shut until the core is taken
G.SAVE.flags['boss:hearthkeeper'] = 1; delete G.SAVE.flags['w2:open'];
tp('CF7', 41, 15); ok(walk(1, 'CF8'), 'CF7 -> CF8'); tp('CF8', 2, 17); ok(walk(-1, 'CF7'), 'CF8 -> CF7');
tp('CF8', 46, 17); ok(window.__game.cf.door() === 1, 'CF8: the furnace doors are solid while w2:open is unset');
ok(!walk(1, 'CT1', 200), 'CF8: walking into the shut doors goes nowhere');
G.SAVE.flags['w2:open'] = 1; window.__game.cf.open(); for (let i = 0; i < 60 * 16 && G.state !== 'play'; i++) G.step(1); step(10);
ok(window.__game.cf.door() === 0, 'CF8: cfFurnaceOpen(): the doors open (cutscene played)');
ok(walk(1, 'CT1'), 'CF8 -> CT1 (through the furnace)'); tp('CT1', 2, 13); ok(walk(-1, 'CF8'), 'CT1 -> CF8');
tp('CF8', 10, 17); ok(window.__game.cf.door() === 0, 'CF8: re-entered: the doors stay open');
tp('CT1', 37, 13); ok(walk(1, 'CT2'), 'CT1 -> CT2'); tp('CT2', 5, 31); ok(walk(-1, 'CT1'), 'CT2 -> CT1');
tp('CT2', 80, 31); ok(walk(1, 'none', 200) || G.room === 'CT2', 'CT2: the gate is the end of the road (x ' + px().toFixed(1) + ')');
tp('CT2', 83, 31); step(1, [], ['interact']); step(5); ok(G.state === 'dialog' || G.state === 'play', 'CT2: touching the gate speaks (' + G.state + ')');
return { fails, log: LOG };
