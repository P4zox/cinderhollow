await boot();
const D = window.__db;
G.give({ items: { hook: 1, talon: 1, tidebreath: 1 } });
G.SAVE.seenAreas = { barrows: 1 }; G.SAVE.flags['cut:choir'] = 1;
const out = [];
const tally = () => { const t = {}; for (const h of window.__dbLog) { const k = h[1].replace(/\d$/, ''); t[k] = (t[k] || 0) + 1; } return t; };
// 1) every move, forced 3 times each, against a still player mid-pool
G.tp('DB6', 18, 13); G.step(20);
const per = {};
for (const m of ['bite', 'sweep', 'tail', 'coil', 'wail', 'bile', 'whirl', 'sonar', 'seal']) {
  per[m] = 0;
  for (let r = 0; r < 3; r++) {
    window.__dbLog = []; const b = D.choir(); if (D.DBW.seal) { D.DBW.seal.t = 99; G.step(2); }
    G.P.x = 300 + (r - 1) * 90; G.P.y = 230; G.P.vx = G.P.vy = 0;
    if (m === 'tail') { const T = b.spine[34]; G.P.x = T.x; G.P.y = T.y + 13; }
    b.begin(m);
    for (let i = 0; i < 70; i++) { G.step(4); G.P.hp = G.D.maxHp; D.DBS.breath = 12; if (b.bs === 'cruise') break; }
    per[m] += window.__dbLog.length;
    b.cool = 99; G.step(30);
  }
}
out.push(['hits on a still player (3 tries each)', per]);
// 2) a free fight: passive vs dodging bot, 60 s each
for (const mode of ['passive', 'dodge']) {
  G.tp('DB6', 18, 13); G.step(10); window.__dbLog = []; let bells = 0, maxSeal = 0;
  const b = D.choir(); b.cool = 1;
  for (let i = 0; i < 900; i++) {
    const c = b.headC(); const near = Math.hypot(c.x - G.P.x, c.y - G.P.y + 13) < 90;
    const bell = G.props.find(p => p.type === 'db_bell');
    let hold = [], tap = [];
    if (D.DBW.seal && D.DBW.seal.on && mode === 'dodge') { const dx = bell.x - G.P.x, dy = bell.y + 36 - G.P.y; if (Math.abs(dx) > 22) hold.push(dx > 0 ? 'right' : 'left'); if (Math.abs(dy) > 6) hold.push(dy > 0 ? 'down' : 'up'); if (Math.abs(dx) < 30 && Math.abs(dy) < 16) tap.push('attack'); }
    else if (mode === 'dodge' && near) tap.push('roll');
    G.step(4, hold, tap); G.P.hp = G.D.maxHp;
    if (D.DBW.seal) maxSeal = Math.max(maxSeal, D.DBW.seal.t);
  }
  out.push([mode, 'hits', window.__dbLog.length, tally(), 'longest seal', +maxSeal.toFixed(1), 'boss hp', b.hp]);
}
return out;
