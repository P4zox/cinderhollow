await boot(); window.__godS = true;
G.give({ items: { wings: 1, talon: 1, hook: 1, emberdash: 1, gale: 1, slam: 1, moonstep: 1 } });
G.SAVE.seenAreas = { starfall: 1, crown: 1 };
// X4 cairn before / after
G.tp('X4', 8, 10); S(30); await snap('l00_x4_before');
G.tp('X4', 5, 10); S(10); S(1, [], ['jump']); S(14, ['jump']); S(1, ['down'], ['heavy']); S(40); await snap('l01_x4_wake'); S(90); await snap('l02_x4_after');
// moonstep fx
G.tp('SF7', 20, 16); G.SAVE.flags['boss:astrel'] = 1; G.tp('SF7', 20, 16); S(20);
S(1, [], ['jump']); S(20, ['jump']); S(1, [], ['jump']); S(22, ['jump']); S(1, [], ['jump']); S(4, ['jump']); await snap('l03_moonstep'); S(8, ['jump']); await snap('l04_moonstep2');
// enemies in SF2
G.tp('SF2', 12, 12); S(60); await snap('l05_sf2_pilgrim');
for (let i = 0; i < 40; i++) S(2, ['right']); await snap('l06_sf2_pilgrim_fight');
G.tp('SF2', 34, 12); S(80); await snap('l07_sf2_golem');
for (let i = 0; i < 40; i++) S(2, ['right'], i % 6 ? [] : ['attack']); await snap('l08_sf2_golem_fight');
const gl = G.enemies.find(e => e.type === 'sf_golem'); if (gl) { gl.hit({ dmg: 9999, poise: 0, dir: 1, kind: 'light', x: gl.x, y: gl.y - 20, melee: true }); S(12); await snap('l09_golem_shatter'); }
G.tp('SF1', 10, 18); S(60); await snap('l10_sf1_wisp');
G.tp('SF4', 12, 21); S(60); await snap('l11_sf4_obs');
G.tp('SF2', 22, 10); S(1, [], ['jump']); S(30, ['jump']); await snap('l12_lowgrav');
return 'ok';
