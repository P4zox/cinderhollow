// fguard: other real K paths for the three types: K out of the held guard (sns, spear), K held (the bow's draw) and K
// pressed mid-combo (J then K), each on a stance-broken foe; plus the Move List row naming the fatality.
G.SAVE.flags['sc:seal'] = 1; G.SAVE.flags['boss:omen'] = 1;
const out = {};
const runOut = () => { let f = 0; while (E('!!FAT.on') && f++ < 500) W().frame(1); W().frame(30); return f; };
const foe = () => { E(`enemies = []; const e = makeEnemy('hollow_soldier', P.x + 28, P.y, 'fg_p' + Math.random()); e.hp = e.maxHp = 30000; enemies.push(e); e.breakStance(); window.__t = e;`); W().frame(2); };
const setup = ty => { G.tp('K4', 6, 10); W().frame(20); W().reset(ty, 1); for (let j = 0; j < 60 && !G.P.ground; j++) W().frame(1); };
for (const ty of ['sns', 'spear']) {
  setup(ty); foe(); W().down('parry'); W().frame(8); const gst = E('P.state'); W().tap('heavy', 1); const s = E('P.state'); W().up('parry'); runOut();
  out[ty + '_guardK'] = { guardState: gst, started: s === 'fatality', end: E('P.state') };
}
for (const ty of ['sns', 'spear', 'bow']) {
  setup(ty); foe(); W().down('heavy'); W().frame(1); const s = E('P.state'); W().frame(20); W().up('heavy'); runOut();
  out[ty + '_holdK'] = { started: s === 'fatality', end: E('P.state') };
  setup(ty); E(`enemies = []; const e = makeEnemy('hollow_soldier', P.x + 28, P.y, 'fg_j'); e.hp = e.maxHp = 30000; enemies.push(e); window.__t = e;`); W().frame(2);
  W().tap('attack', 1); W().frame(12); const jSt = E('P.state'); E('__t.x = P.x + P.face * 26; __t.breakStance()'); W().tap('heavy', 1); let st = false; for (let i = 0; i < 60 && !st; i++) { W().frame(1); st = E('P.state') === 'fatality'; } runOut();
  out[ty + '_midJ_K'] = { during: jSt, started: st, name: E('FAT.last && FAT.last.name'), end: E('P.state') };
  out[ty + '_moveList'] = E(`(MV.types['${ty}'].combos.find(c => c.fatality) || {}).desc`).split(':')[0];
}
// spear_midJ_K: sp_1's push slides the foe past the 34 px crit range before the move ends; a latched K reaches 36 px
// further and steps in (fatLatchTarget / fatStepIn), so it must start the fatality too
out.pass = Object.entries(out).filter(([k]) => /guardK|holdK|midJ_K/.test(k) && true).every(([, v]) => v.started && v.end === 'idle');
return out;
