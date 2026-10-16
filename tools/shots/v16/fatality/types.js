// every one of the 14 types: K on a staggered regular foe (real input) and on a staggered boss in a real arena.
G.SAVE.flags['sc:seal'] = 1;
const TYPES = ['longsword', 'katana', 'greatsword', 'maul', 'sns', 'dual', 'spear', 'staff', 'whip', 'saxe', 'bow', 'fist', 'scythe', 'bell'];
const ARENAS = [['C5','hound',6,10],['K4','omen',6,10],['M5','kalden',6,10],['HF7','twins',4,13],['NV5','executioners',30,10],['X3','sentinels',3,8],['NV7','vael',40,12],['TV8','warden',5,10],['A3','librarian',20,10],['HF4','ice_warden',31,10],['SP5','bellringer',3,10]];
const out = {};
const runOut = () => { let f = 0; while (E('!!FAT.on') && f++ < 500) W().frame(1); return f; };
for (let i = 0; i < TYPES.length; i++) {
  const ty = TYPES[i], res = {};
  try {
    const [r, k, x, y] = ARENAS[i % ARENAS.length];
    // boss in a real arena
    delete G.SAVE.flags['boss:' + k]; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + k] = 1;
    G.tp(r, x, y); W().frame(2); W().reset(ty, 1);
    const b = G.boss;
    for (let j = 0; j < 300 && b && !b.active; j++) { E(`P.x += ${b.x < G.P.x ? -2 : 2}`); W().frame(1); }
    W().frame(220); E('P.hp = D.maxHp');
    E(`window.__q = (boss.parts || [boss]).filter(p => p.alive !== false && typeof p.stagger === 'function')[0] || boss; __q.stagger();`);
    let okc = false;
    for (let j = 0; j < 40 && !okc; j++) { W().frame(1); okc = E(`(() => { const q = __q; if (!q.critable()) return false; const side = P.x < q.x ? -1 : 1; P.y = q.floor ?? q.y; P.vy = 0; P.ground = true; P.x = q.x + side * Math.min((q.critRange || 34) - 8, 40); P.face = -side; P.state = 'idle'; P.anim.set('idle', true); return critTarget() === q; })()`); }
    E('clearBuffer(); held.clear()'); W().tap('heavy', 1);
    res.bossStart = E('P.state') === 'fatality'; res.arena = k;
    const h0 = E('P.hp'); runOut(); W().frame(3);
    const LB = E('FAT.last');
    res.boss = { ratio: +(LB.beats.reduce((a, q) => a + q.dmg, 0) / LB.unit).toFixed(2), gotRatio: +(LB.dealt / LB.unit).toFixed(2), end: E('P.state'), held: !!E('boss._fatHold'), hpKept: E('P.hp') >= h0 };
    let rec = -1; for (let j = 0; j < 240; j++) { W().frame(1); E('P.hp = D.maxHp'); if (rec < 0 && E('__q.state') !== 'stagger') rec = j; }
    res.boss.recoverFrames = rec;
    G.SAVE.flags['boss:' + k] = 1;
    // regular foe
    G.tp(r, x, y); W().frame(30); W().reset(ty, 1); for (let j = 0; j < 60 && !G.P.ground; j++) W().frame(1);
    E(`enemies = enemies.filter(e => !e.fxT); const e = makeEnemy('hollow_soldier', P.x + 26, P.y, 'fx_ty${i}'); e.fxT = true; e.hp = e.maxHp = 30000; enemies.push(e); e.breakStance(); window.__t = e;`);
    W().frame(2); W().tap('heavy', 1);
    res.foeStart = E('P.state') === 'fatality'; res.def = E('FAT.on ? (FAT.on.def.fallback ? "fallback" : FAT.on.name) : null'); res.tag = E('P.anim.tag');
    const f1 = runOut(); W().frame(3);
    const L = E('FAT.last');
    res.foe = { ratio: +(L.dealt / L.unit).toFixed(2), frames: f1, end: E('P.state'), held: !!E('__t._fatHold') };
    res.pass = res.foeStart && res.bossStart && Math.abs(res.foe.ratio - 8) < 0.05 && Math.abs(res.boss.ratio - 5) < 0.05 && res.foe.end === 'idle' && ['idle', 'air'].includes(res.boss.end) && !res.boss.held && res.boss.hpKept && rec >= 0;
  } catch (e) { res.err = e.message; }
  out[ty] = res;
}
out.allPass = Object.values(out).every(r => r.pass);
return out;
