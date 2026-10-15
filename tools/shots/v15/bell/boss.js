// Warbell against a real boss (wm/bench.js boss rules: Gravetusk held in place, swinging every 2 s, real stamina and hitstop).
// Two plans: plain J J J, and the bell's play -- notes into a Perform (Fury / Iron hymn) every ~6 s. Then snapshots in the arena.
const BSECS = 30, res = { boss: [] };
const setup = () => {
  W().reset('bell', 1); E('enemies = enemies.filter(e => !e.wmDummy)');
  delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
  G.tp('C5', 6, 10); const b = G.boss;
  for (let i = 0; i < 200 && !b.active; i++) { W().down('right'); W().frame(4); W().up('right'); G.P.hp = 99999; }
  W().reset('bell', 1); E('enemies = enemies.filter(e => !e.wmDummy); P.belNotes = []; P.belBuff = {}');
  return b;
};
for (const plan of ['JJJ', 'JJJ+perform']) {
  const b = setup(), bx = b.x, by0 = b.y;
  b.update = function (dt) { this.x = bx; this.y = by0; this.commonUpdate(dt); if (this.state === 'stagger') { this.anim.update(dt); this.t -= dt; if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); } } };
  b.state = 'idle'; b.maxHp = 3500; b.hp = 1e7;
  let sum = 0, staggers = 0, wasSt = false; const oh = b.hit; b.hit = function (info) { if (info.melee) sum += info.dmg; return oh.call(this, info); };
  const px = bx - 34; G.P.x = px; G.P.face = 1;
  let presses = 0, performs = 0, k = 0; const seq = plan === 'JJJ' ? 'JJJ' : 'JJJ';
  for (let f = 0; f < 60 * BSECS; f++) {
    const c = f % 120;
    const free = E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40)");
    if (plan !== 'JJJ' && c < 70 && free && E("['idle','run','land'].includes(P.state)") && E('belNotes().length') >= 2 && !(E('P.belBuff.fury') > 8)) { W().tap('parry'); performs++; continue; }
    if (c < 78 && free && G.P.st > 13 && G.P.state !== 'roll') { W().tap(plan !== 'JJJ' && k % 6 >= 3 ? 'heavy' : 'attack'); k++; presses++; continue; }
    if (c === 102) E("hitstop = 0; if (P.state !== 'roll' && P.state !== 'dead') { if (!['idle','run','land'].includes(P.state)) setP('idle', 'idle', true); if (P.st > 0) mvDodgeStart(0); }");
    W().frame(1); G.P.hp = G.D.maxHp;
    if (b.state === 'stagger' && !wasSt) staggers++; wasSt = b.state === 'stagger';
    if (G.P.ground && ['idle', 'run'].includes(G.P.state) && Math.abs(G.P.x - px) > 4) { G.P.x = px; G.P.face = 1; }
    else if (G.P.state !== 'roll' && G.P.x > bx - 12) G.P.x = bx - 12;
  }
  b.hit = oh;
  res.boss.push({ plan, dps: +(sum / G.D.light / BSECS).toFixed(2), presses, performs, staggers, buffs: E('JSON.stringify(P.belBuff)') });
}
const shot = async n => { E('hitstop = 0; areaCard = null; toasts.length = 0; render()'); await snap(n); };
// snapshots: the staff on the HUD, a Perform's shock ring, the tolls sounding
const b = setup(); b.update = function () {}; b.hit = () => {}; b.x += 400;
W().reset('bell', 4); E('P.belNotes = []; P.belBuff = {}'); G.P.x = b.x - 520; G.P.face = 1; W().frame(30); W().dummy(26);
W().tap('attack'); W().frame(12); W().tap('attack'); W().frame(24); W().tap('heavy'); W().frame(30); await shot('bell_staff');
E("P.belNotes = ['A','A','E']"); W().tap('parry'); for (let i = 0; i < 21; i++) W().frame(1); await shot('bell_perform');
W().frame(6); await shot('bell_perform2');
E("P.belBuff = { fury: 22, iron: 14, echo: 30 }; P.belEchoN = 2; P.belNotes = ['G','G']"); W().frame(30); await shot('bell_buffs');
W().down('heavy'); W().frame(46); await shot('bell_wind'); W().up('heavy'); W().frame(16); await shot('bell_toll');
return res;
