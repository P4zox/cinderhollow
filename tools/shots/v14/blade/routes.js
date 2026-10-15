// v14 blade routes: every new combo (and the fixed inputs) starts from real inputs, at a human rhythm.
// Run: SHOT_HTML=web/dist/v14_blade.html sh tools/shots/wm/run.sh tools/shots/v14/blade/routes.js <out>
const R = [];
const T = (name, pass, detail = '') => R.push(`${pass ? 'OK ' : 'BAD'} ${name}${detail ? '  [' + detail + ']' : ''}`);
const st = () => G.P.state;
const keyOf = { J: 'attack', K: 'heavy', I: 'parry', L: 'roll' };
const setup = (type, rank = 1, far = 26) => { W().reset(type, rank); arena(); W().reset(type, rank); E('D.maxSt = 1e6; P.st = 1e6; P.lastHit = null'); if (far !== null) W().dummy(far); };
// ops: J K I L taps (1 frame), w<n> wait n frames, hK<ms> hold K, end2<n> wait until the current move ends + n frames,
// R+/R- L+/L- hold/release a direction, jump, up+J, sheathed, E:<js>
let seen = [];
const fr = n => { for (let i = 0; i < n; i++) { W().frame(1); if (seen[seen.length - 1] !== st()) seen.push(st()); } };
function play(script, tail = 90) {
  seen = [st()];
  for (const s of script) {
    if (keyOf[s]) { W().down(keyOf[s]); fr(1); W().up(keyOf[s]); }
    else if (s[0] === 'w') fr(+s.slice(1));
    else if (s.startsWith('hK')) { W().down('heavy'); fr(Math.round(+s.slice(2) / (1000 / 60))); W().up('heavy'); }
    else if (s.startsWith('end')) { const cur = st(); for (let i = 0; i < 90 && st() === cur; i++) fr(1); fr(+s.slice(3) || 0); }
    else if (s === 'R+') W().down('right'); else if (s === 'R-') W().up('right');
    else if (s === 'L+') W().down('left'); else if (s === 'L-') W().up('left');
    else if (s === 'jump') { W().down('jump'); fr(6); W().up('jump'); }
    else if (s === 'up+J') { W().down('up'); W().down('attack'); fr(1); W().up('attack'); W().up('up'); }
    else if (s === 'sheathed') E('P.sheathed = true');
    else if (s.startsWith('E:')) E(s.slice(2));
  }
  fr(tail); W().up('right'); W().up('left'); W().up('heavy');
  return seen.filter((s, i) => s !== seen[i - 1]).join('>');
}
const has = (seq, ...ids) => { const a = seq.split('>'); let i = 0; for (const s of a) if (s === ids[i]) i++; return i === ids.length; };
const hits = id => W().log.filter(h => h.st === id && h.melee);
// ================================================================ Longsword
setup('longsword', 1); let s = play(['J', 'w12', 'K']);
T('LS J K -> lifting cleave (rank I)', has(s, 'attack1', 'ls_jk') && hits('ls_jk').length === 1, s);
setup('longsword', 1); s = play(['J', 'w12', 'K', 'w20', 'J']);
T('LS J K J -> lifting cleave flows into the poke', has(s, 'attack1', 'ls_jk', 'attack3'), s);
setup('longsword', 1, 22); s = play(['L', 'w14', 'K']);
const fRoll = E('P.face');
T('LS L -> K -> wheeling cut, turned back on the foe it rolled through', has(s, 'roll', 'ls_rollk') && fRoll === -1 && hits('ls_rollk').length === 1, s + ' face ' + fRoll);
setup('longsword', 1, null); s = play(['L', 'w30', 'K']);
T('LS L, roll ends, K within 0.25 s -> still the wheeling cut', has(s, 'roll', 'ls_rollk'), s);
setup('longsword', 1); s = play(['jump', 'J', 'w14', 'J'], 60);
T('LS air J J -> falling crescent', has(s, 'air_attack', 'ls_air2'), s);
setup('longsword', 1); s = play(['jump', 'J', 'w14', 'up+J'], 60);
T('LS air J, up+J -> still the up slash', has(s, 'air_attack', 'attack_up'), s);
setup('longsword', 2); s = play(['J', 'w12', 'J', 'end0', 'end8', 'J']);
T('LS II J J (beat) J -> wheel slash, 2 hits', has(s, 'attack2', 'ls_wheel') && hits('ls_wheel').length === 2, s + ' hits ' + hits('ls_wheel').length);
setup('longsword', 2); s = play(['J', 'w12', 'J', 'w14', 'J']);
T('LS II J J J in rhythm -> still the poke', has(s, 'attack2', 'attack3') && !s.includes('ls_wheel'), s);
setup('longsword', 1); s = play(['J', 'w12', 'J', 'end0', 'end8', 'J']);
T('LS rank I: the beat gives the poke (wheel is II)', has(s, 'attack2', 'attack3') && !s.includes('ls_wheel'), s);
setup('longsword', 2); s = play(['J', 'w12', 'J', 'end0', 'end8', 'J', 'w20', 'J'], 120);
T('LS II J J (beat) J J -> wheel then critical slash', has(s, 'ls_wheel', 'attack4'), s);
// pommel: K pressed early in the poke and held 0.2 s, released before the poke ends
setup('longsword', 4); s = play(['J', 'w12', 'J', 'w14', 'J', 'end0', 'w3', 'hK200']);
T('LS IV J J J -> hold K early in the poke -> pommel', has(s, 'attack3', 'ls_pommel'), s);
setup('longsword', 4); s = play(['J', 'w12', 'J', 'w14', 'J', 'end2', 'hK200']);
T('LS IV J J J, (just after) hold K -> pommel', has(s, 'attack3', 'ls_pommel'), s);
setup('longsword', 4); s = play(['J', 'w12', 'J', 'w14', 'J', 'end0', 'w3', 'K']);
T('LS IV J J J K (tap) -> heavy poke', has(s, 'attack3', 'ls_jjjk') && !s.includes('ls_pommel'), s);
// ember edge: the 4th J on the cue
setup('longsword', 5); E('window.__wm.follow = 26'); play(['J', 'w12', 'J', 'w14', 'J', 'E:0'], 0);
for (let i = 0; i < 60 && !(st() === 'attack3' && E('P.mvT') >= 300); i++) fr(1);
s = play(['J'], 70);
T('LS V ember edge: J on the cue -> burning follow-up', hits('attack4').length === 2, hits('attack4').map(h => (h.dmg / h.light).toFixed(2)).join('/'));
setup('longsword', 5); play(['J', 'w12', 'J', 'w14', 'J'], 0); for (let i = 0; i < 60 && st() !== 'attack3'; i++) fr(1); for (let i = 0; i < 60 && st() === 'attack3'; i++) fr(1); fr(4); play(['J'], 70);
T('LS V ember edge: J ~70 ms after the poke ends still counts', hits('attack4').length === 2, String(hits('attack4').length));
setup('longsword', 3); s = play(['I', 'w6', 'K', 'w3', 'E:hurtPlayer(30, -1, "fz", {})']);
T('LS III foresight I -> K negates and cuts', has(s, 'ls_fore', 'ls_fore_cut'), s);
setup('longsword', 1, null); W().down('heavy'); fr(20); W().down('left'); fr(6); const lsHoldFace = E('P.face'); W().up('left'); W().up('heavy'); fr(60);
T('LS hold K: the charge stance turns with the stick', lsHoldFace === -1);
// ================================================================ Katana
setup('katana', 1); s = play(['sheathed', 'J']);
T('KT sheathed J -> draw cut (rank I)', has(s, 'kt_draw') && hits('kt_draw').length === 1 && !E('P.sheathed'), s);
setup('katana', 1); s = play(['sheathed', 'J', 'w14', 'J']);
T('KT sheathed J J -> draw cut flows into the return cut', has(s, 'kt_draw', 'kt_2'), s);
setup('katana', 1); s = play(['J', 'w14', 'J', 'w14', 'K']);
const shJ = E('P.sheathed');
T('KT J J K -> crescent sheathe, ends sheathed', has(s, 'kt_1', 'kt_2', 'kt_jjk') && shJ === true, s + ' sheathed ' + shJ);
setup('katana', 1); s = play(['J', 'w14', 'J', 'w14', 'K', 'w24', 'K']);
T('KT J J K K -> crescent sheathe then Iai', has(s, 'kt_jjk', 'kt_iai'), s);
setup('katana', 1); s = play(['sheathed', 'K', 'w14', 'J']);
T('KT Iai -> J -> swallow return', has(s, 'kt_iai', 'kt_tsubame') && hits('kt_tsubame').length === 1, s);
setup('katana', 1); s = play(['sheathed', 'K', 'w14', 'J', 'w14', 'I']);
T('KT Iai J I -> swallow return then sheathe', has(s, 'kt_iai', 'kt_tsubame', 'kt_fsheathe') && E('P.sheathed') === true, s);
setup('katana', 2, 30); s = play(['sheathed', 'hK560', 'w6', 'K']);
const fTurn = E('P.face');
T('KT II focus draw -> K -> turning draw, back on the foe', has(s, 'kt_focus', 'kt_turn') && fTurn === -1 && hits('kt_turn').length === 1 && E('P.sheathed') === true, s + ' face ' + fTurn);
setup('katana', 1, 30); s = play(['sheathed', 'hK560', 'w6', 'K']);
T('KT rank I: focus -> K is not the turning draw', has(s, 'kt_focus') && !s.includes('kt_turn'), s);
// Iai tap latency: press -> hit, for a 100 ms tap
setup('katana', 1, 30); E('P.sheathed = true; window.__wm.log = []'); const t0 = W().ms; W().down('heavy'); fr(6); W().up('heavy'); for (let i = 0; i < 40 && !W().log.length; i++) fr(1);
const lat = W().log.length ? W().log[0].t - t0 : 999;
T('KT a 100 ms K tap draws within ~170 ms', lat <= 175 && W().log[0].st === 'kt_iai', Math.round(lat) + ' ms');
// Iai parry mash: I every 100 ms sheathed, a 1-dmg blow every 167 ms
setup('katana', 1); E('P.sheathed = true; D.maxSt = 100; P.st = 100'); let neg = 0, n = 0;
for (let i = 0; i < 120; i++) { if (i % 6 === 0) W().tap('parry'); else fr(1); if (i % 10 === 5) { n++; const hp = G.P.hp; E('P.lastHit = null; P.inv = 0'); E(`(() => { const d = enemies.find(e => e.wmDummy); hurtPlayer(1, -1, 'm${i}', { src: d }); })()`); if (G.P.hp === hp) neg++; E('P.hp = D.maxHp'); } }
T('KT mashing the Iai parry is no longer a wall (<= 60% negated)', neg / n <= 0.6, neg + '/' + n);
setup('katana', 1, null); E('P.sheathed = true'); W().down('heavy'); fr(10); W().down('left'); fr(6); const ktHoldFace = E('P.face'); W().up('left'); W().up('heavy'); fr(60);
T('KT hold K: the focus stance turns with the stick', ktHoldFace === -1);
setup('katana', 4); E('window.__wm.follow = 26'); play(['sheathed', 'K', 'w14', 'J', 'w14', 'I'], 60);
T('KT IV: swallow return -> I does not echo an old flurry', W().log.filter(h => Math.abs(h.dmg / h.light - 0.3) < 0.02).length === 0);
setup('katana', 4); E('window.__wm.follow = 26'); play(['J', 'w14', 'J', 'w14', 'J', 'w20', 'I'], 60);
T('KT IV: J J J I thousand cuts echo x3', W().log.filter(h => Math.abs(h.dmg / h.light - 0.3) < 0.02).length === 3);
// ================================================================ v14c J/K mixes
setup('longsword', 1); s = play(['K', 'w20', 'J']);
T('LS K J -> return slash', has(s, 'heavy', 'ls_kj') && hits('ls_kj').length === 1, s);
setup('longsword', 1); s = play(['K', 'w20', 'J', 'w14', 'J', 'w20', 'J'], 120);
T('LS K J J J -> return slash, poke, critical', has(s, 'heavy', 'ls_kj', 'attack3', 'attack4'), s);
setup('longsword', 1); s = play(['K', 'w20', 'K']);
T('LS K K -> crosswise strike (no accidental charge)', has(s, 'heavy', 'ls_kk') && !s.includes('ls_kc_hold') && hits('ls_kk').length === 1, s);
setup('longsword', 1); s = play(['K', 'w10', 'K']);
T('LS K K fast (2nd press inside the hold window) -> still the crosswise strike', has(s, 'heavy', 'ls_kk') && !s.includes('ls_kc_hold'), s);
setup('longsword', 1); s = play(['hK700', 'w10', 'J'], 90);
T('LS hold K (charged) J -> return slash', has(s, 'ls_kc', 'ls_kj'), s);
setup('longsword', 1); s = play(['hK400'], 60);
T('LS hold K still charges', has(s, 'ls_kc_hold'), s);
setup('longsword', 1); s = play(['J', 'w12', 'K', 'w20', 'K']);
T('LS J K K -> splitting cleave', has(s, 'attack1', 'ls_jk', 'ls_jkk') && hits('ls_jkk').length === 1, s);
setup('longsword', 1); s = play(['J', 'w12', 'J', 'w14', 'K'], 100);
T('LS J J K still the horizontal slash', has(s, 'attack2', 'ls_jjk'), s);
setup('katana', 1); s = play(['J', 'w14', 'K']);
T('KT J K -> kesa cut', has(s, 'kt_1', 'kt_kesa') && hits('kt_kesa').length === 1, s);
setup('katana', 1); s = play(['J', 'w14', 'K', 'w24', 'J', 'w14', 'J'], 100);
T('KT J K J J -> kesa cut back into the chain', has(s, 'kt_kesa', 'kt_2', 'kt_3'), s);
setup('katana', 1); s = play(['J', 'w14', 'J', 'w14', 'J', 'w24', 'K'], 100);
T('KT J J J K -> helm splitter', has(s, 'kt_3', 'kt_kabuto') && hits('kt_kabuto').length === 1, s);
setup('katana', 1); s = play(['J', 'w14', 'J', 'w14', 'J', 'w24', 'I'], 100);
T('KT J J J I still the flurry sheathe', has(s, 'kt_3', 'kt_fsheathe') && E('P.sheathed') === true, s);
setup('katana', 1); s = play(['sheathed', 'K', 'w14', 'J', 'w14', 'K']);
const shT = E('P.sheathed');
T('KT Iai J K -> thrust home, ends sheathed', has(s, 'kt_iai', 'kt_tsubame', 'kt_tsuki') && hits('kt_tsuki').length === 1 && shT === true, s + ' sheathed ' + shT);
setup('katana', 1); s = play(['sheathed', 'K', 'w14', 'J', 'w14', 'K', 'w30', 'K'], 100);
T('KT Iai J K K -> thrust home then the Iai again', has(s, 'kt_tsuki', 'kt_iai'), s);
setup('katana', 1); s = play(['K'], 60);
T('KT K (drawn) still the rushing draw', has(s, 'kt_rush'), s);
return { pass: R.filter(r => r.startsWith('OK')).length, n: R.length, R };
