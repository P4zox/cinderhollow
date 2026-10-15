// every input of every table (WEAPON_REVAMP.md A2-A10, rank I + the Mastery moves) produces its move, and the move's
// damage (x AR, per hit), poise (whole move, split over its hits), stamina and timing (wind-up / total) are within
// +-10% of the table (timing: +-10% or one frame).
E(`(() => {
  const W = window.__wm; W.starts = [];
  const ms = mvStart; mvStart = function (id, o = {}) { const st0 = P.st; const r = ms.call(this, id, o); if (r) W.starts.push({ id, t: W.ms, cost: st0 - P.st }); return r; };
  const sp = startPlunge; startPlunge = function () { const st0 = P.st; sp(); W.starts.push({ id: 'plunge', t: W.ms, cost: st0 - P.st }); };
  const sd = startSpDive; startSpDive = function () { const st0 = P.st; sd(); W.starts.push({ id: 'spdive', t: W.ms, cost: st0 - P.st }); };
  const s0 = setP; setP = function (st) { if (st !== P.state) W.chg.push({ from: P.state, t: W.ms }); return s0.apply(this, arguments); };
  W.chg = [];
  const md = mvDodge; mvDodge = function (o, ax) { const st0 = P.st; const r = md(o, ax); if (r) W.starts.push({ id: 'dodge', t: W.ms, cost: st0 - P.st, total: o.total, inv: o.inv }); return r; };
})()`);
const ops = { J: [['tap', 'attack']], K: [['tap', 'heavy']], I: [['tap', 'parry']], L: [['tap', 'roll']] };
// script: a list of ops: 'J' 'K' 'I' 'L' (taps), 'w<n>' (wait n frames), 'hK<ms>' (hold K for ms), 'jump', 'up+J', 'down+J', 'gc' (a guard counter window), 'fwd' / 'back' (hold a direction for the next op)
function play(script) {
  const w = W();
  for (const s of script) {
    if (s === 'J' || s === 'K' || s === 'I' || s === 'L') w.tap({ J: 'attack', K: 'heavy', I: 'parry', L: 'roll' }[s]);
    else if (s[0] === 'w') w.frame(+s.slice(1));
    else if (s.startsWith('hK')) { w.down('heavy'); w.frame(Math.round(+s.slice(2) / (1000 / 60))); w.up('heavy'); }
    else if (s.startsWith('hJ')) { w.down('attack'); w.frame(Math.round(+s.slice(2) / (1000 / 60))); w.up('attack'); }
    else if (s === 'jump') { w.down('jump'); w.frame(6); w.up('jump'); }
    else if (s === 'fall') { for (let i = 0; i < 80 && G.P.vy <= 20; i++) w.frame(1); }
    else if (s === 'up+J') { w.down('up'); w.tap('attack'); w.up('up'); }
    else if (s === 'down+J') { w.down('down'); w.tap('attack'); w.up('down'); }
    else if (s === 'down+K') { w.down('down'); w.tap('heavy'); w.up('down'); }
    else if (s === 'fwd+L') { w.down('right'); w.tap('roll'); w.up('right'); }
    else if (s === 'move+hK') { w.down('right'); w.down('heavy'); }
    else if (s === 'relK') { w.up('heavy'); w.up('right'); }
    else if (s === 'gc') E('P.gcT = 0.6; P.parried = true');
    else if (s === 'demon') E("P.demon = true");
    else if (s === 'arch') E("P.demon = true; P.arch = true; P.gauge = 1");
    else if (s === 'sheathed') E("P.sheathed = true");
    else if (s === 'crack') E("P.crack = 100");
    else if (s.startsWith('E:')) E(s.slice(2));
  }
  w.frame(100);
}
// [type, rank, script, moveId, dmg (per hit) | [hits], poise (move), stam, wind, total, opts]
const S = 1.015;   // heavies: +1.5% poise per Strength over 10 (str 11)
const C = [
  // ---- Longsword (A2)
  ['longsword', 1, ['J'], 'attack1', 1.0, 12, 12, 160, 380],
  ['longsword', 1, ['J', 'w6', 'J'], 'attack2', 1.05, 12, 12, 160, 380],
  ['longsword', 1, ['J', 'w6', 'J', 'w20', 'J'], 'attack3', 1.1, 14, 13, 200, 420],
  ['longsword', 1, ['J', 'w6', 'J', 'w20', 'J', 'w20', 'J'], 'attack4', 2.0, 40, 18, 300, 650],
  ['longsword', 1, ['K'], 'heavy', 1.6, 45 * S, 24, 380, 700],
  ['longsword', 1, ['hK700'], 'ls_kc', 2.4, 70 * S, 6, 380, 650, { stamNote: '24 + 6 = 30' }],
  ['longsword', 1, ['J', 'w6', 'J', 'w6', 'K'], 'ls_jjk', 1.7, 35 * S, 22, 330, 640],
  ['longsword', 1, ['J', 'w6', 'J', 'w20', 'J', 'w6', 'K'], 'ls_jjjk', 1.9, 38 * S, 24, 350, 680],
  ['longsword', 1, ['gc', 'J'], 'ls_riposte', 2.2, 50, 10, 250, 600],
  ['longsword', 1, ['L', 'w16', 'J'], 'ls_quick', 1.2, 14, 12, 140, 400],
  ['longsword', 1, ['jump', 'J'], 'air_attack', 1.0, 12, 12, 150, 330, { air: true }],
  ['longsword', 1, ['jump', 'up+J'], 'attack_up', 1.0, 12, 12, 160, 360, { air: true }],
  ['longsword', 1, ['jump', 'fall', 'down+J'], 'attack_down', 0.9, 12, 10, 100, 300, { below: true }],
  ['longsword', 1, ['jump', 'K'], 'plunge', 1.5, 70, 18, null, null, { plunge: true }],
  ['longsword', 2, ['fwd+L', 'w2', 'J'], 'ls_step', 1.2, 14, 10, 140, 400, { stamNet: true }],
  ['longsword', 4, ['J', 'w6', 'J', 'w20', 'J', 'w4', 'E:press("heavy")', 'w60', 'E:release("heavy")'], 'ls_pommel', 1.0, 90 * S, 16, 260, 600],
  // ---- Katana (A3)
  ['katana', 1, ['J'], 'kt_1', 0.9, 10, 10, 120, 330],
  ['katana', 1, ['J', 'w6', 'J'], 'kt_2', 0.9, 10, 10, 120, 330],
  ['katana', 1, ['J', 'w6', 'J', 'w6', 'J'], 'kt_3', [0.45, 0.45, 0.45], 18, 16, 180, 600],
  ['katana', 1, ['J', 'w6', 'J', 'w6', 'J', 'w20', 'I'], 'kt_fsheathe', null, null, 4, null, 250, { after: 'P.sheathed === true' }],
  ['katana', 1, ['K'], 'kt_rush', 1.4, 30 * S, 20, 260, 620, { after: 'P.sheathed === true' }],
  ['katana', 1, ['sheathed', 'K'], 'kt_iai', 2.2, 45 * S, 18, 90, 520, { after: 'P.sheathed === false' }],
  ['katana', 1, ['sheathed', 'hK550'], 'kt_focus', 2.6, 55 * S, 28, 120, 500],
  ['katana', 1, ['I'], 'kt_sheathe', null, null, 4, null, 300, { after: 'P.sheathed === true' }],
  ['katana', 1, ['L', 'w8', 'J'], 'kt_stepcut', 1.1, 12, 10, 120, 360],
  ['katana', 1, ['jump', 'J'], 'kt_air', 1.0, 12, 12, 140, 330, { air: true }],
  ['katana', 1, ['jump', 'up+J'], 'kt_up', 1.0, 14, 12, 160, 360, { air: true }],
  ['katana', 1, ['jump', 'fall', 'down+J'], 'kt_down', 0.9, 10, 10, 100, 280, { below: true }],
  ['katana', 1, ['jump', 'K'], 'plunge', 1.5, 60, 18, null, null, { plunge: true }],
  ['katana', 3, ['sheathed', 'L'], 'kt_flash', 1.6, 30, 12, 80, 360],
  // ---- Greatsword (A4)
  ['greatsword', 1, ['J'], 'gs_1', 1.3, 32, 20, 300, 700],
  ['greatsword', 1, ['J', 'w10', 'J'], 'gs_2', 1.35, 32, 20, 300, 700],
  ['greatsword', 1, ['J', 'w10', 'J', 'w30', 'J'], 'gs_3', 1.6, 45, 22, 320, 760],
  ['greatsword', 1, ['K'], 'gs_charged', 1.8, 50 * S, 28, 200, 500, { lv: 1 }],
  ['greatsword', 1, ['hK600'], 'gs_charged', 2.6, 70 * S, 32, 200, 500, { lv: 2 }],
  ['greatsword', 1, ['hK1000'], 'gs_charged', 3.6, 95 * S, 36, 200, 500, { lv: 3 }],
  ['greatsword', 1, ['hK1500'], 'gs_charged', 2.6, 70 * S, 32, 200, 500, { lv: 2, note: 'overcharge' }],
  ['greatsword', 1, ['hK1000', 'w14', 'hK1300'], 'gs_strong', 4.5, 95 * S, 40, 220, 560, { lv: 3 }],
  ['greatsword', 1, ['L', 'w18', 'K'], 'gs_rollheavy', 1.8, 50 * S, 28, 220, 600, { lv: 1, note: 'rolling heavy' }],
  ['greatsword', 1, ['jump', 'J'], 'gs_air', 1.3, 40, 16, 220, 560, { air: true }],
  ['greatsword', 1, ['jump', 'up+J'], 'gs_up', 1.2, 35, 16, 240, 560, { air: true }],
  ['greatsword', 1, ['jump', 'fall', 'down+J'], 'gs_down', 1.1, 45, 12, 140, 390, { below: true }],
  ['greatsword', 1, ['jump', 'K'], 'plunge', 1.8, 90, 20, null, null, { plunge: true }],
  ['greatsword', 2, ['E:press("heavy")', 'w20', 'L', 'w40', 'E:release("heavy")'], 'gs_tackle', 0.6, 40, 10, 120, 300],
  ['greatsword', 3, ['hK1000', 'w14', 'hK1300', 'w20', 'hK1300'], 'gs_true1', 1.5, 40 * S, null, 220, 420],
  ['greatsword', 3, ['hK1000', 'w14', 'hK1300', 'w20', 'hK1300'], 'gs_true2', 4.5, 95 * 1.2 * S, 0, 250, 700],
  ['greatsword', 5, ['hK1500'], 'gs_wrath', 4.2, 110 * S, 40, 220, 640, { lv: 4, note: 'wrath' }],
  // ---- Maul (A5): poise x1.6 stun (x1.2 more when the blow lands high)
  ['maul', 1, ['J'], 'ml_1', 1.2, 40 * 1.6, 18, 260, 620, { stun: true }],
  ['maul', 1, ['J', 'w10', 'J'], 'ml_2', 1.25, 40 * 1.6, 18, 260, 620, { stun: true }],
  ['maul', 1, ['J', 'w10', 'J', 'w20', 'J'], 'ml_3', 1.6, 70 * 1.6, 22, 300, 720, { stun: true }],
  ['maul', 1, ['K'], 'ml_upswing', 1.6, 60 * 1.6 * S, 24, 200, 520, { stun: true }],
  ['maul', 1, ['hK650'], 'ml_double', [1.2, 1.2], 110 * 1.6 * S, 28, 180, 900, { stun: true }],
  ['maul', 1, ['hK1050'], 'ml_bigsmash', 3.0, 90 * 1.6 * S, 32, 300, 750, { stun: true }],
  ['maul', 1, ['move+hK', 'w100', 'relK'], 'ml_spin_end', 2.0, 90 * 1.6 * S, 0, 200, 500, { stun: true }],
  ['maul', 1, ['L', 'w18', 'J'], 'ml_rollswing', 1.3, 35 * 1.6, 16, 200, 560, { stun: true }],
  ['maul', 1, ['jump', 'J'], 'ml_air', 1.2, 30 * 1.6, 16, 200, 520, { air: true, stun: true }],
  ['maul', 1, ['jump', 'up+J'], 'ml_up', 1.1, 30 * 1.6, 14, 220, 520, { air: true, stun: true }],
  ['maul', 1, ['jump', 'fall', 'down+J'], 'ml_down', 1.0, 50 * 1.6, 12, 140, 380, { below: true, stun: true }],
  ['maul', 1, ['jump', 'K'], 'plunge', 1.8, 100 * 1.6, 20, null, null, { plunge: true, stun: true }],
  ['maul', 3, ['J', 'w10', 'J', 'w20', 'J', 'w30', 'K', 'w30', 'K', 'w30', 'K', 'w30', 'K', 'w80'], 'ml_bb4', 3.0, 90 * 2 * S, 24, 360, 900, { stun: true, stunMul: 2 }],
  // ---- Sword & Shield (A6)
  ['sns', 1, ['J'], 'sh_1', 0.85, 10, 9, 120, 320],
  ['sns', 1, ['J', 'w6', 'J'], 'sh_2', 0.85, 10, 9, 120, 320],
  ['sns', 1, ['J', 'w6', 'J', 'w6', 'J'], 'sh_3', 0.9, 12, 10, 140, 340],
  ['sns', 1, ['J', 'w6', 'J', 'w6', 'J', 'w6', 'J'], 'sh_4', 1.4, 55, 14, 220, 560],
  ['sns', 1, ['K'], 'sh_heavy', 1.2, 60 * S, 16, 200, 520],
  ['sns', 1, ['hK500'], 'sh_rush', 1.8, 90 * S, 8, 220, 450, { stamNote: '16 + 8 = 24' }],
  ['sns', 1, ['gc', 'J'], 'sh_counter', 1.9, 45, 10, 200, 520],
  ['sns', 1, ['L', 'w8', 'J'], 'sh_leap', 1.8, 40, 16, 320, 700],
  ['sns', 1, ['jump', 'J'], 'sh_air', 0.85, 10, 9, 120, 300, { air: true }],
  ['sns', 1, ['jump', 'up+J'], 'sh_up', 0.9, 20, 10, 150, 340, { air: true, far: 10 }],
  ['sns', 1, ['jump', 'fall', 'down+J'], 'sh_down', 0.9, 20, 10, 100, 300, { below: true }],
  ['sns', 1, ['jump', 'K'], 'plunge', 1.4, 70, 16, null, null, { plunge: true }],
  ['sns', 2, ['J', 'w12', 'J', 'w16', 'K'], 'sh_prush', 2.0, 70 * S, 16, 200, 520],
  ['sns', 3, ['E:press("parry")', 'w20', 'K', 'w40', 'E:release("parry")'], 'sh_slam', 1.6, 110 * S, 18, 260, 620],
  ['sns', 4, ['jump', 'K'], 'plunge', 1.6, 80, 16, null, null, { plunge: true }],
  // ---- Dual Blades (A7): Demon Mode swings 20% faster
  ['dual', 1, ['J'], 'tw_1', [0.45, 0.45], 6, 8, 100, 300],
  ['dual', 1, ['J', 'w4', 'J'], 'tw_2', [0.45, 0.45], 6, 8, 100, 300],
  ['dual', 1, ['J', 'w4', 'J', 'w4', 'J'], 'tw_3', [0.5, 0.5], 8, 9, 110, 300],
  ['dual', 1, ['J', 'w4', 'J', 'w4', 'J', 'w4', 'J'], 'tw_4', 1.2, 20, 12, 220, 520],
  ['dual', 1, ['demon', 'J', 'w4', 'J', 'w4', 'J', 'w4', 'J', 'w12', 'J'], 'tw_d5', [0.5, 0.5], 8, 8, 100, 280, { speed: 1.2 }],
  ['dual', 1, ['demon', 'J', 'w4', 'J', 'w12', 'J', 'w12', 'J', 'w20', 'J', 'w14', 'J'], 'tw_d6', [0.45, 0.45, 0.45], 8, 10, 100, 280, { speed: 1.2 }],
  ['dual', 1, ['K'], 'tw_heavy', 1.1, 15 * S, 12, 200, 480],
  ['dual', 1, ['demon', 'K'], 'tw_dflurry', [0.3, 0.3, 0.3, 0.3, 0.3, 0.3], 30 * S, 16, 150, 800, { speed: 1.2 }],
  ['dual', 1, ['arch', 'hK400'], 'tw_dance', [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 1.0], 60 * S, 0, 150, 1400, { speed: 1.2 }],
  ['dual', 1, ['I'], 'tw_demon', null, null, 0, null, 200, { after: 'P.demon === true', speed: 1.2 }],
  ['dual', 1, ['L', 'w16', 'J'], 'tw_dashslash', 1.0, 10, 8, 100, 320],
  ['dual', 1, ['jump', 'J'], 'tw_air', [0.45, 0.45], 8, 9, 120, 330, { air: true }],
  ['dual', 1, ['jump', 'up+J'], 'tw_up', [0.45, 0.45], 8, 9, 140, 340, { air: true }],
  ['dual', 1, ['jump', 'fall', 'down+J'], 'tw_down', [0.3, 0.3, 0.3], 10, 10, 100, 320, { below: true, hitsMin: 1 }],
  ['dual', 1, ['jump', 'K'], 'plunge', 1.3, 50, 16, null, null, { plunge: true }],
  ['dual', 2, ['demon', 'L', 'w3', 'J'], 'tw_dthrough', 1.0, 15, 8, 100, 320, { speed: 1.2 }],
  ['dual', 3, ['arch', 'hK400'], 'tw_dance2', [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.3, 0.3, 0.3, 1.6], 80 * S, 0, 150, 1680, { speed: 1.2 }],
  // ---- Spear (A8)
  ['spear', 1, ['J'], 'sp_1', 1.0, 14, 11, 140, 380, { far: 50 }],
  ['spear', 1, ['J', 'w6', 'J'], 'sp_2', 1.0, 14, 11, 140, 380],
  ['spear', 1, ['J', 'w6', 'J', 'w6', 'J'], 'sp_3', 1.15, 18, 12, 160, 420],
  ['spear', 1, ['K'], 'sp_heavy', 1.4, 35 * S, 18, 260, 600],
  ['spear', 1, ['E:press("parry")', 'w10', 'J', 'w30', 'E:release("parry")'], 'sp_gpoke', 0.9, 12, 10, 140, 380],
  ['spear', 1, ['E:press("parry")', 'w10', 'E:P.gcT = 0.5', 'K', 'w40', 'E:release("parry")'], 'sp_counter', 2.0, 60, 14, 160, 520],
  ['spear', 1, ['move+hK', 'w50', 'relK'], 'sp_finish', 2.2, 70 * S, 0, 120, 480, { far: 34 }],
  ['spear', 1, ['move+hK', 'w60', 'relK'], 'sp_run', 0.4, 15, null, null, null, { far: 34, perHit: true, hitsMin: 1 }],
  ['spear', 1, ['L', 'w10', 'J'], 'sp_hpoke', 1.0, 14, 10, 120, 360],
  ['spear', 1, ['jump', 'w1', 'J'], 'spdive', 1.5, 40, 16, null, null, { plunge: true, dive: true }],
  ['spear', 1, ['jump', 'up+J'], 'sp_up', 1.1, 20, 12, 180, 420, { air: true, far: 8 }],
  ['spear', 1, ['jump', 'fall', 'down+J'], 'sp_down', 0.9, 14, 10, 100, 300, { below: true }],
  ['spear', 1, ['jump', 'K'], 'plunge', 1.5, 70, 18, null, null, { plunge: true }],
  ['spear', 3, ['E:press("parry")', 'w10', 'E:P.gcT = 0.5', 'E:press("heavy")', 'w30', 'E:release("heavy")', 'w40', 'E:release("parry")'], 'sp_ccounter', 3.0, 90 * S, 0, 360, 800, { stamNote: '14 (the counter-thrust) + 0' }],
  // ---- Staff (A9)
  ['staff', 1, ['J'], 'st_1', 0.85, 12, 10, 140, 360],
  ['staff', 1, ['J', 'w6', 'J'], 'st_2', 0.85, 12, 10, 140, 360],
  ['staff', 1, ['J', 'w6', 'J', 'w6', 'J'], 'st_3', 0.9, 16, 11, 160, 380],
  ['staff', 1, ['J', 'w6', 'J', 'w6', 'J', 'w6', 'J'], 'st_4', 1.4, 35, 14, 240, 560],
  ['staff', 1, ['K'], 'st_heavy', [0.8, 0.8], 60 * S, 'spin', 220, 640],
  ['staff', 1, ['L', 'w16', 'J'], 'st_lowsweep', 1.1, 20, 10, 140, 380],
  ['staff', 1, ['jump', 'J'], 'st_air', 0.9, 14, 10, 120, 320, { air: true }],
  ['staff', 1, ['jump', 'K'], 'st_aspin', 1.4, 40 * S, 16, 180, 460, { air: true, mom: 1 }],
  ['staff', 1, ['jump', 'up+J'], 'st_up', 0.9, 14, 10, 140, 340, { air: true }],
  ['staff', 1, ['jump', 'fall', 'down+J'], 'st_down', 1.0, 30, 10, 100, 300, { below: true }],
  ['staff', 3, ['jump', 'K', 'w8', 'K'], 'st_aspin2', 1.8, 45 * S, 16, 120, 540, { air: true, mom: 2 }],
  // ---- Whip (A10): untipped up close, tipped at range
  ['whip', 1, ['J'], 'wh_1', 0.8, 8, 9, 160, 400],
  ['whip', 1, ['J'], 'wh_1', 1.04, 8, 9, 160, 400, { far: 70, note: 'tip' }],
  ['whip', 1, ['J', 'w8', 'J'], 'wh_2', 0.8, 8, 9, 160, 400],
  ['whip', 1, ['J', 'w8', 'J', 'w8', 'J'], 'wh_3', 1.1, 20, 14, 260, 620],
  ['whip', 1, ['K'], 'wh_heavy', 1.4, 30 * S, 18, 300, 680],
  ['whip', 1, ['K'], 'wh_heavy', 1.82, 30 * S, 18, 300, 680, { far: 70, note: 'tip' }],
  ['whip', 1, ['hK650'], 'wh_overhead', 2.0, 45 * S, 6, 300, 600, { stamNote: '18 + 6 = 24', far: 50 }],
  ['whip', 1, ['crack', 'K'], 'wh_thunder', 3.2, 90 * S, 20, 300, 700],
  ['whip', 1, ['L', 'w16', 'J'], 'wh_retreat', 1.0, 10, 10, 160, 420, { far: 20 }],
  ['whip', 1, ['jump', 'J'], 'wh_air', 0.9, 12, 10, 160, 380, { air: true }],
  ['whip', 1, ['jump', 'up+J'], 'wh_up', 0.9, 14, 10, 160, 380, { air: true }],
  ['whip', 1, ['jump', 'fall', 'down+J'], 'wh_down', 0.9, 12, 10, 120, 320, { below: true }],
  ['whip', 1, ['jump', 'K'], 'plunge', 1.3, 50, 16, null, null, { plunge: true }],
  ['whip', 4, ['K', 'w10', 'K'], 'wh_double', 1.8, 35 * S, 18, 220, 550],
  ['whip', 5, ['hJ600'], 'wh_thousand', [0.585, 0.585, 0.585, 0.585, 0.585, 0.585, 0.585, 0.585], 32, 20, 80, 1000, { far: 70, hitsMin: 6 }],
];
const ok = (got, want, tol = 0.1) => want === null || want === undefined || (got !== null && Math.abs(got - want) <= Math.max(Math.abs(want) * tol, 0.011));
const okT = (got, want) => want === null || want === undefined || (got !== null && Math.abs(got - want) <= Math.max(want * 0.1, 17.5));
const rows = [], fails = [];
for (const c of C) {
  const [type, rank, script, id, dmg, poise, stam, wind, total, o = {}] = c;
  W().reset(type, rank); arena(); E('P.face = 1; P.st = D.maxSt = 999; D.maxSt = 999;');
  W().reset(type, rank); E('D.maxSt = 999; P.st = 999');
  const far = o.far || 26;
  if (o.below) W().dummy(0, { tall: 70 });
  else if (o.air) W().dummy(far, { tall: 90 });
  else W().dummy(far, { tall: 40 });
  if (!o.below && !o.air && !o.plunge && !o.noFollow) E('window.__wm.follow = ' + far);
  W().starts = []; E('window.__wm.chg = []');
  play(script);
  const starts = W().starts, si = starts.findIndex(s => s.id === id);
  const st = si >= 0 ? starts[si] : null;
  const hits = W().log.filter(h => h.melee && h.st === id || (o.plunge && (h.st === 'plunge' || h.st === 'air' || h.st === 'spdive' || h.st === 'jump_up')));
  const L = G.D.light;
  const r = { case: `${type}${rank > 1 ? ' R' + rank : ''} ${script.filter(s => !s.startsWith('E:')).join(' ')} -> ${id}${o.note ? ' (' + o.note + ')' : ''}`, started: !!st, hits: hits.length };
  const errs = [];
  if (!st) errs.push('move did not start (saw ' + starts.map(s => s.id).join(',') + ')');
  else {
    const want = Array.isArray(dmg) ? dmg : dmg === null ? [] : [dmg];
    const gotD = hits.map(h => +(h.dmg / L).toFixed(3));
    r.dmg = gotD.join('/'); r.dmgWant = want.join('/');
    if (want.length && !hits.length) errs.push('no hits');
    if (!o.perHit && want.length > 1 && hits.length < (o.hitsMin || want.length)) errs.push(`hits ${hits.length} < ${want.length}`);
    for (let i = 0; i < Math.min(hits.length, want.length); i++) if (!ok(gotD[i], want[i])) errs.push(`dmg[${i}] ${gotD[i]} vs ${want[i]}`);
    if (o.perHit) { for (const g of gotD) if (!ok(g, want[0])) errs.push(`dmg ${g} vs ${want[0]}`); }
    if (poise !== null && hits.length) {
      const n = o.perHit ? 1 : want.length || 1, per = poise / n;
      const gp = hits[0].poise; r.poise = +(gp * n).toFixed(1); r.poiseWant = +poise.toFixed(1);
      if (!(ok(gp, per) || (o.stun && ok(gp, per * 1.2)))) errs.push(`poise ${gp.toFixed(1)}/hit vs ${per.toFixed(1)}`);
    }
    if (stam !== null && stam !== 'spin') { r.stam = +st.cost.toFixed(1); if (!ok(st.cost, stam)) errs.push(`stam ${st.cost.toFixed(1)} vs ${stam}`); }
    if (stam === 'spin') { const want2 = 0.3 * 999; r.stam = Math.round(st.cost); if (!ok(st.cost, want2)) errs.push(`stam ${st.cost} vs 30% max`); }
    const spd = o.speed || 1;
    if (wind !== null && hits.length) { r.wind = Math.round(hits[0].t - st.t); if (!okT(r.wind, wind / spd)) errs.push(`wind ${r.wind} vs ${Math.round(wind / spd)}`); }
    if (total !== null) {
      const nx = starts[si + 1], end = nx ? nx.t : null;
      // total = when the state ends: the next start, else the frame the state left
      const endc = E('window.__wm.chg').find(c => c.from === id && c.t > st.t);
      r.total = endc ? Math.round(endc.t - st.t) : nx ? Math.round(nx.t - st.t) : null;
      if (!o.noTotal && !o.air && !(o.below && r.total >= total && r.total <= total + 100) && !okT(r.total, total / spd)) errs.push(`total ${r.total} vs ${Math.round(total / spd)}`);
      if (o.after && !E(o.after)) errs.push('after: ' + o.after);
    }
  }
  r.ok = !errs.length; if (errs.length) { r.err = errs.join('; '); fails.push(r.case + ': ' + r.err); }
  rows.push(r);
}
return { n: rows.length, pass: rows.filter(r => r.ok).length, fails, rows: rows.map(r => `${r.ok ? 'OK ' : 'BAD'} ${r.case} | dmg ${r.dmg ?? '-'} (${r.dmgWant ?? '-'}) poise ${r.poise ?? '-'} (${r.poiseWant ?? '-'}) stam ${r.stam ?? '-'} wind ${r.wind ?? '-'} total ${r.total ?? '-'}`) };
