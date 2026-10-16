// AREA checks: a stress pass (random inputs, live foes) through every forge room, phantom damage (stand still with foes
// removed: only the visible vents may hurt), NPC lines, lore pages, the vista bench, the world map. Errors are printed by
// shot.js (page errors) and collected here (exceptions).
await boot(); G.grantTechniques(); Object.assign(G.SAVE.items, { talon: 1, slam: 1 }); G.giveArmory && G.giveArmory();
const out = { exc: [], phantom: [], npc: {}, pages: [], errs: [] };
window.addEventListener('error', e => out.errs.push(String(e.message)));
const ROOMS = [['CF1', 8, 16], ['CF2', 30, 6], ['CF3', 16, 12], ['CF4', 40, 11], ['CF9', 25, 9], ['CF5', 22, 5], ['CF10', 34, 7], ['CF6', 40, 15], ['CF13', 20, 11],
  ['CF7', 12, 15], ['CF12', 10, 20], ['CF11', 14, 15], ['CF8', 20, 17], ['CT1', 10, 13], ['CT2', 30, 31]];
const acts = ['left', 'right', 'jump', 'attack', 'heavy', 'roll', 'parry', 'down', 'up'];
let rnd = 1; const R = () => (rnd = (rnd * 16807) % 2147483647) / 2147483647;
for (const [r, x, y] of ROOMS) {
  try {
    G.tp(r, x, y);
    for (let i = 0; i < 150; i++) {
      const h = [acts[Math.floor(R() * 4)]], t = R() < 0.4 ? [acts[Math.floor(R() * acts.length)]] : [];
      G.step(4, h, t);
      if (G.state === 'cut' || G.state === 'dialog' || G.state === 'menu' || G.state === 'cine') G.step(1, [], ['pause']);
      if (G.state === 'dead') G.step(200);
      G.P.hp = Math.max(G.P.hp, 60);
    }
  } catch (e) { out.exc.push(r + ': ' + e.message + ' ' + (e.stack || '').split('\n')[1]); }
}
// phantom damage: every reachable standing spot sampled (a few per room), foes removed, 3 s still
const SPOTS = [['CF1', 4, 16], ['CF1', 14, 14], ['CF1', 28, 9], ['CF1', 40, 5], ['CF2', 5, 6], ['CF2', 24, 5], ['CF2', 50, 6], ['CF3', 3, 6], ['CF3', 16, 12], ['CF3', 24, 36], ['CF3', 13, 59],
  ['CF4', 84, 11], ['CF4', 30, 7], ['CF4', 47, 4], ['CF4', 5, 9], ['CF9', 20, 9], ['CF5', 22, 5], ['CF5', 3, 14], ['CF5', 35, 14], ['CF5', 70, 14], ['CF5', 60, 5], ['CF10', 13, 4], ['CF10', 34, 7],
  ['CF6', 3, 9], ['CF6', 45, 15], ['CF6', 50, 4], ['CF6', 67, 12], ['CF13', 20, 11], ['CF13', 6, 5], ['CF7', 12, 15], ['CF7', 21, 13], ['CF7', 6, 5], ['CF12', 10, 20], ['CF12', 27, 9], ['CF12', 40, 25],
  ['CF11', 14, 15], ['CF11', 15, 8], ['CF8', 20, 17], ['CF8', 45, 17], ['CT1', 10, 13], ['CT1', 30, 13], ['CT2', 30, 31], ['CT2', 80, 31]];
G.SAVE.flags['boss:hearthkeeper'] = 1;
for (const [r, x, y] of SPOTS) {
  G.tp(r, x, y); G.SETTINGS.god = 1; for (let i = 0; i < 30; i++) { G.step(1); G.enemies.length = 0; }
  G.SETTINGS.god = 0; G.P.hp = G.D.maxHp; const h0 = G.P.hp;
  for (let i = 0; i < 180; i++) { G.step(1); G.enemies.length = 0; if (G.state !== 'play') G.step(1, [], ['pause']); }
  if (G.P.hp < h0 || G.room !== r) out.phantom.push(`${r} ${x},${y}: hp ${Math.round(h0)} -> ${Math.round(G.P.hp)} room ${G.room}`);
}
G.SETTINGS.god = 1;
// NPC lines before / after the forge and the keeper
const F = G.SAVE.flags; delete F['cf:seen']; delete F['boss:hearthkeeper'];
out.npc.ashwright_before = window.__game.cf.npc('ashwright').filter(t => /Cold Forge|soot/.test(t));
F['cf:seen'] = 1; F.v_met = 1; out.npc.ashwright_seen = window.__game.cf.npc('ashwright').filter(t => /Forge|soot|keeper|Hearth/i.test(t));
out.npc.venn_seen = window.__game.cf.npc('venn');
F['boss:hearthkeeper'] = 1; F.v_coldforge = 1; F['w2:open'] = 1; for (const k of ['v_ink', 'v_twins', 'v_drake', 'v_forge', 'v_oswin', 'v_first', 'v_truth', 'v_tear']) F[k] = 1; F['boss:omen'] = 1; F['boss:hound'] = 1;
out.npc.venn_keeper = window.__game.cf.npc('venn');
out.npc.ashwright_keeper = window.__game.cf.npc('ashwright').filter(t => /keeper|furnace|Forge/i.test(t));
out.pages = window.__game.cf.pages();
// the vista: sit at the Last Gate's bench
G.tp('CT2', 22, 31); G.step(30); G.step(1, [], ['interact']); G.step(150); if (G.xs) G.xs.clean(); await snap('c_CT2_bench');
G.step(1, [], ['left']); G.step(30);
// the world map, centred here
for (const id of ['E6', 'CF1', 'CF2', 'CF3', 'CF4', 'CF5', 'CF6', 'CF7', 'CF8', 'CF9', 'CF10', 'CF11', 'CF12', 'CF13', 'CT1', 'CT2']) G.SAVE.visited[id] = 1;
G.tp('CF7', 12, 15); G.step(20); G.step(1, [], ['map']); G.step(20); await snap('c_map'); G.step(1, [], ['confirm']); G.step(10); await snap('c_map2'); G.step(1, [], ['map']); G.step(5);
return out;
