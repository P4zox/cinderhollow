// WA: every class's own up / air / down attack: tag used, hit lands, down pogos off a foe and off spikes, air limit holds.
await boot(); G.giveArmory(); G.grantTechniques(); G.SETTINGS.god = 1;
const X = G.sk.ev('({ ATK, MOVESETS, Enemy, setP, refreshDerived, get enemies() { return enemies; }, get room() { return room; }, T_SPIKE, BRAMBLE: typeof TV_T_BRAMBLE !== "undefined" ? TV_T_BRAMBLE : null })');
const { ATK, MOVESETS, Enemy, setP, refreshDerived, T_SPIKE } = X;
const WPN = { sword: 'longsword', dagger: 'dagger', great: 'greatsword', spear: 'spear', katana: 'katana', staff: 'quarterstaff', shield: 'knight_shield',
  twin: 'twinfangs', scythe: 'briar_scythe', whip: 'gravechain', mirror: 'first_ember' };
const out = [], bad = [];
const A = () => ATK[G.P.state];
const until = (fn, n = 90) => { for (let i = 0; i < n && !fn(); i++) G.step(1); };
const clear = () => { for (const e of X.enemies) e.state = 'dead'; X.enemies.length = 0; };
const foe = (dx, dy) => { const e = new Enemy('hollow_soldier', G.P.x + dx, G.P.y + dy, 'wa' + Math.random()); e.hp = e.maxHp = 99999;
  e.update = function (dt) { this.flash = Math.max(0, this.flash - dt * 6); }; X.enemies.push(e); return e; };
const air = (h = 70) => { G.P.y -= h; G.P.vy = 0; G.P.vx = 0; G.P.ground = false; G.P.airN = 0; G.P.airLock = false; setP('air', 'jump_fall'); };
const hold = n => { for (let i = 0; i < n; i++) { G.step(1); if (!G.P.ground) G.P.vy = Math.min(G.P.vy, 30); } };
const shots = [];
for (const [cls, id] of Object.entries(WPN)) {
  G.SAVE.weapon = id; G.SAVE.weapons[id] = G.SAVE.weapons[id] || 0; refreshDerived();
  if (cls === 'mirror') G.SAVE.lastCls = 'scythe';
  G.tp('R1', 20, 10); G.step(20); G.P.face = 1; clear();
  const want = cls === 'mirror' ? MOVESETS.scythe : MOVESETS[cls];
  const r = { cls };
  // ---- up (on the ground): a foe hanging over the head
  let e = foe(4, -34); G.step(2);
  G.step(1, ['up'], ['attack']); r.up = G.P.state;
  until(() => !A() || G.P.anim.i > A().active[1], 60, ['up']);
  r.upHit = e.hp < e.maxHp;
  until(() => !A(), 90); G.step(10); clear();
  // ---- air (mid-air, foe ahead at head height); spins also behind
  air(); e = foe(22, -4); const eb = foe(-16, -4); G.step(1, [], ['attack']); r.air = G.P.state;
  if (G.P.state === want.air) { until(() => G.P.anim.i >= A().active[0], 40); hold(1); shots.push(`${cls}_air`); await snap(`${cls}_air`); }
  until(() => !A() || G.P.anim.i > A().active[1], 60); r.airHit = e.hp < e.maxHp; r.airBack = eb.hp < eb.maxHp; r.spin = !!(ATK[want.air] && ATK[want.air].spin);
  until(() => G.P.ground, 200); G.step(20); clear();
  // ---- the greatsword's air cleave stops the rise (the hang); nobody else's does
  { air(90); G.P.vy = -220; G.step(1, [], ['attack']); G.step(4); r.hangVy = Math.round(G.P.vy);
    r.hangOk = cls === 'great' ? G.P.vy >= 0 : G.P.vy < 0; until(() => G.P.ground, 200); G.step(25); }
  // ---- down onto a foe: must hit and bounce
  air(60); e = foe(3, 0); const y0 = G.P.y;
  G.step(1, ['down'], ['attack']); r.down = G.P.state;
  if (A() && A().down) { until(() => G.P.anim.i >= A().active[0], 30); G.step(1); shots.push(`${cls}_down`); await snap(`${cls}_down`); }
  let bounced = false; for (let i = 0; i < 60 && !G.P.ground; i++) { G.step(1); if (G.P.pogoed && G.P.vy < -100) { bounced = true; break; } }
  r.downHit = e.hp < e.maxHp; r.pogoFoe = bounced;
  until(() => G.P.ground, 200); G.step(20); clear();
  // ---- down onto spikes: pogo + one air attack refunded
  { const tx = Math.floor(G.P.x / 16), ty = Math.floor(G.P.y / 16), k = ty * X.room.w + tx, k2 = k - 1, k3 = k + 1, old = [X.room.grid[k], X.room.grid[k2], X.room.grid[k3]];
    X.room.grid[k] = X.room.grid[k2] = X.room.grid[k3] = T_SPIKE;
    air(28); G.P.airN = 1; G.step(1, ['down'], ['attack']);
    let sp = false; for (let i = 0; i < 60 && !G.P.ground; i++) { G.step(1); if (G.P.pogoed && G.P.vy < -100) { sp = true; break; } }
    r.pogoSpike = sp; r.refund = G.P.airN === 1;   // airAtkStart made it 2, the spike pogo refunded one
    X.room.grid[k] = old[0]; X.room.grid[k2] = old[1]; X.room.grid[k3] = old[2];
    until(() => G.P.ground, 200); G.step(30); }
  // ---- down onto brambles (Thornveil's tile): pogo too
  { const B = X.BRAMBLE;
    if (B !== null) { const tx = Math.floor(G.P.x / 16), ty = Math.floor(G.P.y / 16), ks = [-1, 0, 1].map(d => ty * X.room.w + tx + d), old = ks.map(k => X.room.grid[k]);
      ks.forEach(k => X.room.grid[k] = B); air(28); G.P.airN = 1; G.step(1, ['down'], ['attack']);
      let bp = false; for (let i = 0; i < 60 && !G.P.ground; i++) { G.step(1); if (G.P.pogoed && G.P.vy < -100) { bp = true; break; } }
      r.pogoBramble = bp; ks.forEach((k, i) => X.room.grid[k] = old[i]); until(() => G.P.ground, 200); G.step(30); } else r.pogoBramble = 'n/a'; }
  // ---- air limit: two airborne attacks, the third is refused until you land and wait AIR_CD
  air(140); let n = 0, prev = G.P.state; const seq = [];
  for (let k = 0; k < 3; k++) {
    G.step(1, [], ['attack']);
    for (let j = 0; j < 40; j++) { G.step(1); G.P.vy = Math.min(G.P.vy, 20); if (G.P.state !== prev) { seq.push(G.P.state); if (ATK[G.P.state] && ATK[G.P.state].air) n++; } prev = G.P.state; }
  }
  r.airCount = n; r.lock = !!G.P.airLock; r.seq = seq.join(',') + ' airN=' + G.P.airN + ' g=' + G.P.ground;
  until(() => G.P.ground, 300); G.step(25); r.unlocked = !G.P.airLock;
  const okTags = r.up === want.up && r.air === want.air && r.down === want.down;
  const ok = okTags && r.upHit && r.airHit && (!r.spin || r.airBack) && r.downHit && r.pogoFoe && r.pogoSpike && r.pogoBramble === true && r.refund && r.airCount === 2 && r.lock && r.unlocked && r.hangOk;
  if (!ok) bad.push(cls);
  out.push(`${ok ? 'OK ' : 'BAD'} ${cls.padEnd(7)} up=${r.up}${r.upHit ? '+' : '-'} air=${r.air}${r.airHit ? '+' : '-'}${r.spin ? (r.airBack ? ' back+' : ' back-') : ''} down=${r.down}${r.downHit ? '+' : '-'} pogoFoe=${r.pogoFoe} pogoSpike=${r.pogoSpike} pogoBramble=${r.pogoBramble} refund=${r.refund} airAttacks=${r.airCount} vyAfterAirStart=${r.hangVy} lock=${r.lock} unlockedAfterLanding=${r.unlocked}` + (ok ? '' : ' | ' + r.seq));
}
out.push(bad.length ? 'FAILED: ' + bad.join(' ') : 'ALL CLASSES OK');
return out;
