// fheavy: the three heavy fatalities on REGULAR foes with real inputs (K on a staggered foe): the real tag plays, execute
// (HP <= 12 x AR) vs 8 x AR, invulnerable mid-way, the leap lands, the small foe is lifted / knocked and lands, the
// player ends idle and can act again, and nothing is left held.
G.SAVE.flags['sc:seal'] = 1;
const TYPES = window.__types || ['greatsword', 'maul', 'bell'];
const TAG = { greatsword: 'gs_fatal', maul: 'ml_fatal', bell: 'wb_fatal' };
const out = {};
const place = (hp, foe = 'hollow_soldier') => {
  arena(); W().reset(window.__ty, 1); arena(); W().frame(2);
  E(`enemies = enemies.filter(e => !e.fhT); const e = makeEnemy('${foe}', P.x + 26, P.y, 'fh_' + Math.random()); e.fhT = true; ${hp ? `e.hp = e.maxHp = ${hp};` : ''} enemies.push(e); e.breakStance(); window.__t = e;`);
  W().frame(2);
};
for (const ty of TYPES) {
  const r = {}; window.__ty = ty;
  try {
    // 1. a tough foe: 8 x AR, the whole choreography
    W().reset(ty, 1); place(30000);
    const y0 = E('P.y'), ty0 = E('__t.y'), tx0 = E('__t.x');
    E('clearBuffer(); held.clear()'); W().tap('heavy', 1);
    r.started = E('P.state') === 'fatality';
    r.name = E('FAT.on && FAT.on.name'); r.fallback = E('!!(FAT.on && FAT.on.def.fallback)');
    let f = 0, minY = y0, tags = new Set(), hurt = null, maxLift = 0, frames = [];
    while (E('!!FAT.on') && f < 500) {
      W().frame(1); f++;
      tags.add(E('P.anim.tag')); minY = Math.min(minY, E('P.y')); maxLift = Math.max(maxLift, ty0 - E('__t.y'));
      if (f === 25 || f === 60) { const h = E(`(() => { const h0 = P.hp; hurtPlayer(9999, 1, 'fh', {}); spikeHurt(); killPlayer && killPlayer(); return { same: P.hp === h0, st: P.state }; })()`); hurt = hurt && !hurt.same ? hurt : h; }
    }
    const L = E('FAT.last');
    r.frames = f; r.realTag = [...tags].includes(TAG[ty]); r.tags = [...tags];
    r.ratio = +(L.dealt / L.unit).toFixed(2); r.beats = L.beats.map(b => [b.at, +(b.got / L.unit).toFixed(2)]); r.exec = L.exec;
    r.leapPx = Math.round(y0 - minY); r.targetLiftPx = Math.round(maxLift); r.invuln = hurt;
    W().frame(40);
    r.after = E(`({ st: P.state, ground: P.ground, dy: Math.round(P.y - ${y0}), held: !!__t._fatHold, tDy: Math.round(__t.y - ${ty0}), tGround: !!__t.ground, tAlive: __t.alive, cine: +(FAT.cine.dark + FAT.cine.bars).toFixed(2) })`);
    // acts again: a light attack starts a move
    E('clearBuffer(); held.clear()'); W().tap('attack', 1); W().frame(2); r.actsAfter = E('P.state');
    // 2. a weak foe: executed on the last beat
    W().reset(ty, 1); place(0);
    const unit = E('outgoing(D.light, 1, "melee")'); E(`__t.hp = Math.floor(${unit} * 6)`);
    E('clearBuffer(); held.clear()'); W().tap('heavy', 1);
    r.execStarted = E('P.state') === 'fatality';
    let g2 = 0, aliveMid = null; while (E('!!FAT.on') && g2++ < 500) { W().frame(1); if (g2 === 50) aliveMid = E('__t.alive !== false && __t.hp > 0'); }
    const L2 = E('FAT.last'); W().frame(20);
    r.execute = { exec: L2.exec, aliveMid, deadAfter: E('__t.alive === false || __t.hp <= 0'), end: E('P.state') };
    r.pass = r.started && r.realTag && !r.fallback && Math.abs(r.ratio - 8) < 0.05 && r.invuln && r.invuln.same && r.after.st === 'idle' && r.after.ground
      && Math.abs(r.after.dy) <= 1 && !r.after.held && r.actsAfter !== 'idle' && r.execute.exec && r.execute.aliveMid && r.execute.deadAfter && r.execute.end === 'idle';
  } catch (e) { r.err = e.message + ' ' + (e.stack || '').split('\n')[1]; }
  out[ty] = r;
}
out.allPass = TYPES.every(t => out[t].pass);
return out;
