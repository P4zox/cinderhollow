// fblade: katana / saxe (both forms) / scythe fatalities with real K presses: 4 real boss arenas (2 multi-body) + regular
// foes (8x AR on a tough one, executed at <= 12x AR, not executed above), invulnerability mid-way, the hold (no other body
// moves), clean recovery, and the weapon-state rules (saxe: form + gauge frozen and kept; scythe: souls filled to 3).
G.SAVE.flags['sc:seal'] = 1; G.SAVE.items.tidebreath = 1; G.SAVE.items.moonstep = 1;
const CASES = [['saxe', 0], ['saxe', 1], ['katana', 0], ['scythe', 0]];   // [type, start in axe form]
const ARENAS = window.__arenas || [['K4','omen',6,10],['HF7','twins',4,13],['X3','sentinels',3,8],['TV8','warden',5,10]];
const out = {};
const runOut = () => { let f = 0; while (E('!!FAT.on') && f++ < 600) W().frame(1); return f; };
const prep = (ty, axe) => { W().reset(ty, 1); if (ty === 'saxe') E(axe ? 'sxSetAxe(true); P.sxG = 63' : 'P.sxG = 41'); if (ty === 'scythe') E('P.scySouls = 0'); };
for (const [ty, axe] of CASES) {
  const key = ty + (axe ? '_axe' : '');
  const res = out[key] = { arenas: {}, foes: {} };
  for (const [r, k, x, y] of ARENAS) {
    const a = res.arenas[k] = {};
    try {
      delete G.SAVE.flags['boss:' + k]; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + k] = 1;
      G.tp(r, x, y); W().frame(2); prep(ty, axe);
      const b = G.boss; if (!b) { a.err = 'no boss'; continue; }
      for (let j = 0; j < 300 && !b.active; j++) { E(`P.x += ${b.x < G.P.x ? -2 : 2}`); W().frame(1); E('P.hp = D.maxHp'); }
      W().frame(200); E('P.hp = D.maxHp'); prep(ty, axe);
      E(`window.__q = (boss.parts || [boss]).filter(p => p.alive !== false && typeof p.critable === 'function' && typeof p.stagger === 'function')[0] || boss; (__q.stagger || boss.stagger).call(__q.stagger ? __q : boss);`);
      let ok = false;
      for (let j = 0; j < 40 && !ok; j++) { W().frame(1); ok = E(`(() => { const q = __q; if (!q.critable()) return false; const side = P.x < q.x ? -1 : 1; P.y = q.floor ?? q.y; P.vy = 0; P.ground = true; P.x = q.x + side * Math.min((q.critRange || 34) - 8, 40); P.face = -side; P.state = 'idle'; P.anim.set('idle', true); return critTarget() === q; })()`); }
      if (!ok) { a.err = 'not critable'; continue; }
      const others0 = E(`JSON.stringify((boss.parts || []).filter(p => p !== __q).map(p => Math.round(p.x) + ':' + p.state))`);
      const s0 = { g: 0, axe: false };
      E('clearBuffer(); held.clear()'); W().tap('heavy', 1);
      a.start = E('P.state') === 'fatality'; const sxF = E('FAT.on && FAT.on.sx ? FAT.on.sx : null'); if (sxF) { s0.g = sxF.g; s0.axe = sxF.axe; } a.tag = E('P.anim.tag'); a.def = E('FAT.on && FAT.on.name');
      let fr = 0, moved = false, hurt = null, minHp = 1e9, sxBad = 0;
      while (E('!!FAT.on') && fr < 600) {
        W().frame(1); fr++;
        if (fr === 25) hurt = E(`(() => { const h0 = P.hp; hurtPlayer(9999, P.face, 'fb_t', {}); spikeHurt(); killPlayer && killPlayer(); return P.hp === h0 && P.state === 'fatality'; })()`);
        if (E('!!FAT.on') && E(`JSON.stringify((boss.parts || []).filter(p => p !== __q).map(p => Math.round(p.x) + ':' + p.state))`) !== others0) moved = true;
        if (ty === 'saxe' && E(`!FAT.on || (Math.abs(P.sxG - FAT.on.sx.g) > 1e-9 || !!P.sxAxe !== FAT.on.sx.axe)`) && E('!!FAT.on')) sxBad++;
        minHp = Math.min(minHp, E('P.hp'));
        if (ty === 'katana' && E('!!__q._fbSplit && FAT.on && FAT.on.split && FAT.on.split.k > 0.9')) a.splitSeen = (a.splitSeen || 0) + 1;
      }
      const L = E('FAT.last');
      a.frames = fr; a.ratio = +(L.dealt / L.unit).toFixed(2); a.beats = L.beats.map(q => q.got); a.hurtBlocked = hurt; a.othersMoved = moved;
      a.post = E(`({ st: P.state, held: !!boss._fatHold, qHeld: !!__q._fatHold, split: !!__q._fbSplit, ownDraw: Object.prototype.hasOwnProperty.call(__q, 'draw'), g: P.sxG, axe: !!P.sxAxe, souls: P.scySouls || 0 })`);
      if (ty === "saxe") a.s0 = s0; a.sxBad = sxBad; a.sxKept = sxBad === 0 && Math.abs(a.post.g - s0.g) < 0.25 && a.post.axe === s0.axe;
      let rec = -1; const seen = new Set();
      for (let j = 0; j < 300; j++) { W().frame(1); E('P.hp = D.maxHp'); const s = E('__q.alive === false ? "dead" : __q.state'); seen.add(s); if (rec < 0 && s !== 'stagger') rec = j; }
      a.recover = rec; a.statesAfter = [...seen].slice(0, 6); a.pAfter = E('P.state');
      a.pass = a.start && Math.abs(a.ratio - 5) < 0.06 && hurt && !moved && !a.post.held && !a.post.qHeld && !a.post.split && rec >= 0 && ['idle', 'air'].includes(a.post.st) && (ty !== 'saxe' || a.sxKept) && (ty !== 'scythe' || a.post.souls === 3) && (ty !== 'katana' || a.splitSeen > 10);
      G.SAVE.flags['boss:' + k] = 1;
    } catch (e) { a.err = e.message; }
  }
  // regular foes: tough (8x), weak (executed), just above the execute line (8x, survives)
  for (const [nm, hpExpr] of [['tough', '30000'], ['weak', 'Math.floor(__u * 11)'], ['above', 'Math.ceil(__u * 12.5)']]) {
    const f = res.foes[nm] = {};
    try {
      G.SAVE.flags['boss:omen'] = 1; G.tp('K4', 6, 10); W().frame(30); prep(ty, axe); for (let j = 0; j < 60 && !G.P.ground; j++) W().frame(1);
      E(`window.__u = outgoing(D.light, 1, 'melee') * (D.W.crit || 1); enemies = []; const e = makeEnemy('hollow_soldier', P.x + 26, P.y, 'fb_${nm}'); e.hp = e.maxHp = ${hpExpr}; enemies.push(e); e.breakStance(); window.__t = e;`);
      W().frame(2); E('clearBuffer(); held.clear()'); W().tap('heavy', 1);
      f.start = E('P.state') === 'fatality'; f.tag = E('P.anim.tag'); f.frames = runOut(); W().frame(3);
      const L = E('FAT.last'); f.ratio = +(L.dealt / L.unit).toFixed(2); f.exec = L.exec; f.dead = E('__t.alive === false || __t.hp <= 0'); f.end = E('P.state'); f.held = !!E('__t._fatHold'); f.split = !!E('__t._fbSplit');
      f.pass = f.start && f.end === 'idle' && !f.held && !f.split && (nm === 'weak' ? f.exec && f.dead : !f.exec && Math.abs(f.ratio - 8) < 0.06 && !f.dead);
    } catch (e) { f.err = e.message; }
  }
}
out.allPass = Object.values(out).every(r => Object.values(r.arenas).every(a => a.pass) && Object.values(r.foes).every(f => f.pass));
return out;
