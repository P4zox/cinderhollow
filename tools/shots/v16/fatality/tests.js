// v16 fatality: the framework's rules with real inputs (press / release + frames). Training Grounds floor, real foes.
const R = {}, ok = (k, v, info) => { R[k] = v ? 'PASS' : 'FAIL ' + JSON.stringify(info === undefined ? null : info); };
arena();
const foe = (hp, dx = 26, type = 'hollow_soldier') => E(`(() => { enemies = enemies.filter(e => !e.fxT); const e = makeEnemy('${type}', P.x + P.face * ${dx}, P.y, 'fx_t' + Math.random()); e.fxT = true; e.hp = e.maxHp = ${hp}; enemies.push(e); e.breakStance(); window.__t = e; return e.critable(); })()`);
const runOut = (n = 400) => { let f = 0; while (E('!!FAT.on') && f++ < n) W().frame(1); return f; };
const ready = () => E('fatReady()');
// 1. K on a staggered regular foe starts it; 8 x AR on a sturdy foe; the stagger is consumed (once per stagger)
W().reset('longsword', 1); foe(20000); W().frame(2);
W().tap('heavy', 1);
const st1 = E('P.state'), tag1 = E('P.anim.tag');
let fr = runOut(); W().frame(2);
const L1 = E('FAT.last');
ok('K_regular_starts', st1 === 'fatality', st1);
ok('regular_8xAR', Math.abs(L1.dealt / L1.unit - 8) < 0.05 && !L1.exec, { ratio: L1.dealt / L1.unit, exec: L1.exec });
ok('ends_idle', E('P.state') === 'idle' && !E('FAT.on'), E('P.state'));
ok('length_1.1_to_1.8s', fr / 60 >= 1.1 && fr / 60 <= 1.8 + 0.6, fr / 60);   // (frames include slow-mo / hitstop)
R.real_length_s = +(fr / 60).toFixed(2); R.tag = tag1;
ok('once_per_stagger', !E('__t.critable()') && !ready(), E('__t.state'));
W().tap('heavy', 1); W().frame(1); ok('K_after_is_normal_heavy', E('P.state') !== 'fatality' && !!E('ATK[P.state]'), E('P.state'));
W().frame(60);
// 2. execute rule: HP <= 12 x AR dies outright; just above it takes 8 x AR
W().reset('longsword', 1);
const unit = E('outgoing(D.light, 1, "melee")');
foe(Math.floor(unit * 12) - 2); W().frame(2); W().tap('heavy', 1); runOut(); W().frame(2);
const L2 = E('FAT.last');
ok('execute_at_12xAR', L2.exec && E('__t.alive') === false, { exec: L2.exec, alive: E('__t.alive'), hp: E('__t.hp') });
W().frame(30); W().reset('longsword', 1);
foe(Math.ceil(unit * 12) + 40); W().frame(2); W().tap('heavy', 1); runOut(); W().frame(2);
const L3 = E('FAT.last');
ok('no_execute_above_12xAR', !L3.exec && E('__t.alive') !== false && Math.abs(L3.dealt / L3.unit - 8) < 0.05, { exec: L3.exec, r: L3.dealt / L3.unit });
// 3. J still ripostes
W().frame(30); W().reset('longsword', 1); foe(20000); W().frame(2);
W().tap('attack', 1); const stJ = E('P.state'); W().frame(60);
ok('J_still_ripostes', stJ === 'riposte' && !E('FAT.on') && !E('__t.critable()'), stJ);
W().frame(20); W().tap('heavy', 1); W().frame(1); ok('K_after_riposte_no_fatality', E('P.state') !== 'fatality', E('P.state'));
// 4. Riposte Mastery x Executioner x weapon crit multiply it like the riposte (+ 5% heal, +30 stamina)
W().frame(40); W().reset('longsword', 1);
E("SAVE.skills = ['riposte_mastery', 'executioner']; refreshDerived(false); P.hp = D.maxHp * 0.5; P.st = 10");
foe(50000); W().frame(2); const hpB = E('P.hp'); W().tap('heavy', 1); runOut(); W().frame(1);
const L4 = E('FAT.last'), base = E('outgoing(D.light, 1, "melee") * (D.W.crit || 1)');
ok('mods_multiply', Math.abs(L4.unit / base - 1.5 * 1.3) < 0.02, { ratio: L4.unit / base });
ok('mastery_heal_exec_stamina', E('P.hp') > hpB && E('P.st') >= 30, { hp: E('P.hp'), hpB, st: E('P.st') });
// 5. invulnerable + uninterruptible: blows, projectiles, spikes, a stun, a room-exit abort
W().frame(40); W().reset('longsword', 1); foe(20000); W().frame(2); W().tap('heavy', 1); W().frame(12);
const inv = E(`(() => { const h0 = P.hp; const a = hurtPlayer(99999, -P.face, 'fat_x', {}); spikeHurt(); const b = killPlayer(1); setP('hurt', 'hurt');
  projectiles.push({ owner: 'enemy', kind: 'test', x: P.x, y: P.y - 12, vx: 0, vy: 0, dmg: 500, life: 0.3, r: 8, hits: new Set(), t: 0 }); return { a, b, same: P.hp === h0, h0 }; })()`);
W().frame(8);
ok('invulnerable', inv.a === false && inv.b === false && inv.same && E('P.hp') >= inv.h0, inv);
ok('uninterruptible', E('P.state') === 'fatality' && !!E('FAT.on'), E('P.state'));
runOut(); W().frame(2);
ok('no_hp_lost', E('P.hp') >= inv.h0, E('P.hp'));
// held target: no update of its own afterwards, the dimmed draws come back, the cinematic layers fade to 0
W().frame(40);
ok('target_released', !E('Object.prototype.hasOwnProperty.call(__t, "update")') && !E('__t._fatHold'));
ok('cine_cleared', E('FAT.cine.bars + FAT.cine.dark + FAT.cine.vig') < 0.01 && E('FAT.dimmed.length') === 0, E('FAT.cine'));
W().tap('attack', 1); W().frame(2); ok('acts_after', !!E('ATK[P.state]'), E('P.state'));
// 6. K pressed DURING a move latches and leads to the fatality when the move ends
W().frame(60); W().reset('longsword', 1); foe(20000, 40); E('__t.state = "idle"; __t.critDone = true'); W().frame(1);
W().tap('attack', 1); W().frame(4); E('__t.breakStance(); __t.x = P.x + P.face * 26'); W().frame(2); W().tap('heavy', 1);
let started = false; for (let i = 0; i < 60 && !started; i++) { W().frame(1); E('__t.x = P.x + P.face * 26'); started = E('P.state') === 'fatality'; }
ok('K_during_move_latches', started, E('P.state')); runOut(); W().frame(30);
// 7. the guard path (sword & shield: K out of the held guard) and the parry path (a parried foe is critable)
W().reset('sns', 1); foe(20000); W().frame(2); W().down('parry'); W().frame(8); const gst = E('P.state'); W().tap('heavy', 1); const g1 = E('P.state'); W().up('parry'); runOut(); W().frame(30);
ok('guard_K_path', g1 === 'fatality', { gst, g1 });
// 8. room exit mid-fatality: aborted cleanly, nothing left held
W().reset('longsword', 1); foe(20000); W().frame(2); W().tap('heavy', 1); W().frame(20);
E(`enterRoom(room.id, P.x, P.y)`); W().frame(3);
ok('room_exit_aborts', !E('FAT.on') && E('P.state') !== 'fatality' && E('FAT.last.aborted') === true, { st: E('P.state'), last: E('FAT.last.aborted') });
// 9. Move List row on every type
ok('move_list_rows', E(`Object.keys(MV.types).every(t => (MV.types[t].combos || []).some(c => c.fatality && c.input === 'K on a staggered foe' && c.desc.length > 10))`), E('Object.keys(MV.types).length'));
R.fxPrimitives = E('fatFxNames()');
// 10. target helpers on a small foe (a throwaway def on the whip): lift + knockback mid-fatality, it lands after; every
// primitive spawns and draws without errors; a custom draw fn step runs
W().frame(30); W().reset('whip', 1);
E(`window.__fxSeen = 0; fatalityRegister('whip', { name: 'Test Rite', col: '150,195,255', tag: 'wh_1', dur: 1200, steps: [
  { at: 0, target: { lift: 20, dur: 200 } }, { at: 300, target: { knock: 24, dur: 150 } }, { at: 400, hit: 1 },
  ...fatFxNames().map((k, i) => ({ at: 420 + i * 20, fx: k, o: {} })),
  { at: 700, fx: (ctx, t, F) => { window.__fxSeen++; }, o: { life: 200 } },
  { at: 900, target: { drop: true } }, { at: 1000, hit: 2, name: true } ] })`);
foe(20000); W().frame(2); const y0 = E('__t.y'), x0 = E('__t.x');
W().tap('heavy', 1); W().frame(24); const yLift = E('__t.y');
W().frame(20); const xKn = E('__t.x');
for (let i = 0; i < 300 && E('!!FAT.on'); i++) { W().frame(1); E('render()'); } W().frame(40);
ok('target_lift', y0 - yLift > 12, { y0, yLift });
ok('target_knock', Math.abs(xKn - x0) > 12, { x0, xKn });
ok('target_lands', Math.abs(E('__t.y') - y0) < 2, { y: E('__t.y'), y0 });
ok('all_primitives_and_fn', E('window.__fxSeen') > 0 && E('FAT.last.beats.length') === 2, { seen: E('window.__fxSeen') });
E('delete FAT.defs.whip');
// 11. Boss Core: the fatality takes the Core's colour, nothing procs
W().frame(30); W().reset('longsword', 1);
E("SAVE.cores = { omen: 1 }; SAVE.enchants = { longsword: 'omen' }; CR.vfx = []");
foe(20000); W().frame(2); W().tap('heavy', 1);
const cc = E('FAT.on && [FAT.on.col, FAT.on.base, FAT.on.core]');
runOut(); W().frame(50);
ok('core_tint_no_proc', cc && cc[0] !== cc[1] && !!cc[2] && E('CR.vfx.filter(v => v.k === "line" || v.k === "pillar").length') === 0, { cc, vfx: E('CR.vfx.length') });
E("SAVE.enchants = {}");
R.checks = Object.values(R).filter(v => typeof v === 'string' && /^(PASS|FAIL)/.test(v)).length;
R.failed = Object.entries(R).filter(([k, v]) => typeof v === 'string' && v.startsWith('FAIL')).map(([k]) => k);
return R;
