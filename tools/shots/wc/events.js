// WC: functional checks — hitstop cap over every attack, charged release, pogo kick, shake setting, player-swing detection
await boot(); G.giveArmory(); G.grantTechniques(); G.SETTINGS.god = 1;
const F = G.feel, ev = F.ev, o = [];
const until = (fn, n = 90) => { for (let i = 0; i < n && !fn(); i++) G.step(1); };
// 1. hitstop table: every ATK entry x every weapon, charged / boss variants; the max must be <= 0.12
let mx = 0, mn = 1, where = '';
for (const w of Object.keys(ev('WEAPONS'))) { G.SAVE.weapon = w;
  for (const k of Object.keys(ev('ATK'))) for (const ch of [false, true]) for (const bs of [false, true]) {
    const h = ev(`P.charged = ${ch}; FEEL.strikeBoss = ${bs}; feelHitstop(ATK['${k}'])`); if (h > mx) { mx = h; where = w + ' ' + k + (ch ? ' charged' : '') + (bs ? ' boss' : ''); } mn = Math.min(mn, h); } }
ev('P.charged = false; FEEL.strikeBoss = false'); o.push(`hitstop range ${mn.toFixed(3)}..${mx.toFixed(3)} (max at ${where}) cap ok: ${mx <= 0.1201}`);
// 2. wrapped swing counter: every class's combo swing is recognised as the player's
ev('window.__sw = 0; if (!window.__swHook) { window.__swHook = 1; const f = WSFX.swing; WSFX.swing = function (A) { window.__sw++; window.__swA = A; return f.apply(this, arguments); }; }');
const WPN = { sword: 'longsword', dagger: 'dagger', great: 'greatsword', spear: 'spear', katana: 'katana', staff: 'quarterstaff', shield: 'knight_shield', twin: 'twinfangs', scythe: 'antler_scythe', whip: 'headsman_chain', mirror: 'first_ember' };
const rec = [];
for (const [c, w] of Object.entries(WPN)) { G.SAVE.weapon = w; ev('refreshDerived()'); G.tp('R1', 20, 10); G.step(20); const n0 = ev('window.__sw'); G.step(1, [], ['attack']); G.step(40); rec.push(c + ':' + (ev('window.__sw') - n0)); }
o.push('player swings recognised (1 each): ' + rec.join(' '));
// 3. charged heavy on a hammer: release flare, kick, hitstop
G.SAVE.weapon = 'greatsword'; ev('refreshDerived()'); G.tp('R1', 20, 10); G.step(30); G.P.face = 1;
ev(`(() => { for (const e of enemies) e.gone = true; enemies = enemies.filter(e => !e.gone); const e = new Enemy('grave_knight', P.x + 30, P.y, 'wce'); e.hp = e.maxHp = 1e6; e.cool = 99; enemies.push(e); })()`);
G.step(1, ['heavy'], ['heavy']); for (let i = 0; i < 150 && !G.P.charged; i++) G.step(1, ['heavy']);
const charged = G.P.charged; until(() => ev('ATK[P.state] && P.anim.i >= ATK[P.state].active[0]'), 60); G.step(1);
o.push(`charged heavy: charged=${charged} swingA=${ev('window.__swA && window.__swA.kind')} kick=${F.FEEL.kx.toFixed(2)},${F.FEEL.ky.toFixed(2)} (slam: vertical) flashes=${F.FEEL.flashes.length} hitstop=${ev('hitstop').toFixed(3)}`);
await snap('ev_charged');
// 4. pogo: down attack onto a foe from above
G.step(60); G.tp('R1', 20, 10); G.step(30);
ev(`(() => { for (const e of enemies) e.gone = true; enemies = enemies.filter(e => !e.gone); const e = new Enemy('hollow_soldier', P.x, P.y, 'wcp'); e.hp = e.maxHp = 1e6; e.cool = 99; e.cfg = { ...e.cfg, poise: 1e9, stance: 1e9 }; enemies.push(e); })()`);
G.P.y -= 60; G.P.vy = 0; G.P.ground = false; G.step(1);
G.step(1, ['down'], ['attack']); let pog = false, ky = 0, sq = 0; for (let i = 0; i < 40 && !pog; i++) { G.step(1, ['down']); if (G.P.pogoed) { pog = true; ky = F.FEEL.ky; sq = F.FEEL.sq; } }
o.push(`pogo: ${pog} kickY=${ky.toFixed(2)} stretch=${sq.toFixed(2)} vy=${Math.round(G.P.vy)}`);
// 5. Screen shake Off: kicks never reach the camera; Low halves them
G.step(60); const camTest = lvl => { G.SETTINGS.shake = lvl; ev('hitstop = 0'); ev('FEEL.kx = 4; FEEL.ky = 0'); G.step(1); return ev('FEEL.ax').toFixed(2); };
o.push(`camera offset for a 4px kick: Off=${camTest(0)} Low=${camTest(0.5)} Full=${camTest(1)}`);
G.SETTINGS.shake = 1;
// 6. shakeLvl mirror isn't saved; wtrail default
o.push(`shakeLvl=${G.SETTINGS.shakeLvl} in JSON: ${JSON.stringify(G.SETTINGS).includes('shakeLvl')} wtrail=${G.SETTINGS.wtrail}`);
return o;
