// Funeral Peal balance: v15 boss.js rules (Gravetusk held in place, swinging every 2 s, real stamina and hitstop, 30 s).
// Plans: the bell's best boss play (J J J with notes into a Perform), the art alone whenever it is ready (FP refilled: the worst
// case), and the best play with the art used whenever ready (FP refilled). dps in light-attack units; staggers counted.
const BSECS = 30, res = { boss: [] };
const setup = () => {
  W().reset('bell', 1); E('enemies = enemies.filter(e => !e.wmDummy)');
  delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
  G.tp('C5', 6, 10); const b = G.boss;
  for (let i = 0; i < 200 && !b.active; i++) { W().down('right'); W().frame(4); W().up('right'); G.P.hp = 99999; }
  W().reset('bell', 1); E('enemies = enemies.filter(e => !e.wmDummy); P.belNotes = []; P.belBuff = {}; P.cds = {}');
  return b;
};
for (const plan of ['JJJ+perform', 'art only', 'JJJ+perform+art']) {
  const b = setup(), bx = b.x, by0 = b.y;
  b.update = function (dt) { this.x = bx; this.y = by0; this.commonUpdate(dt); if (this.state === 'stagger') { this.anim.update(dt); this.t -= dt; if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); } } };
  b.state = 'idle'; b.maxHp = 3500; b.hp = 1e7;
  let sum = 0, artSum = 0, staggers = 0, wasSt = false; const oh = b.hit; b.hit = function (info) { if (info.melee) { sum += info.dmg; if (G.P.state === 'art' || E('FPL.waves.length') > 0) artSum += info.dmg; } return oh.call(this, info); };
  const px = bx - 34; G.P.x = px; G.P.face = 1;
  let presses = 0, performs = 0, arts = 0, k = 0;
  const useArt = plan !== 'JJJ+perform', useJ = plan !== 'art only';
  for (let f = 0; f < 60 * BSECS; f++) {
    if (useArt) E('P.fp = D.maxFp');
    const c = f % 120;
    const idle = E("['idle','run','land'].includes(P.state)");
    const free = idle || E("(!!ATK[P.state] && !P.mvQ && P.mvT > 40)");
    if (useArt && c < 60 && idle && E("cdLeft('art','funeral_peal') <= 0")) { W().tap('art'); arts++; continue; }
    if (useJ && c < 70 && free && idle && E('belNotes().length') >= 2 && !(E('P.belBuff.fury') > 8)) { W().tap('parry'); performs++; continue; }
    if (useJ && c < 78 && free && G.P.st > 13 && G.P.state !== 'roll') { W().tap(k % 6 >= 3 ? 'heavy' : 'attack'); k++; presses++; continue; }
    if (c === 102) E("hitstop = 0; if (P.state !== 'roll' && P.state !== 'dead') { if (!['idle','run','land'].includes(P.state)) setP('idle', 'idle', true); if (P.st > 0) mvDodgeStart(0); }");
    W().frame(1); G.P.hp = G.D.maxHp;
    if (b.state === 'stagger' && !wasSt) staggers++; wasSt = b.state === 'stagger';
    if (G.P.ground && ['idle', 'run'].includes(G.P.state) && Math.abs(G.P.x - px) > 4) { G.P.x = px; G.P.face = 1; }
    else if (G.P.state !== 'roll' && G.P.x > bx - 12) G.P.x = bx - 12;
  }
  b.hit = oh;
  res.boss.push({ plan, dps: +(sum / G.D.light / BSECS).toFixed(2), artDps: +(artSum / G.D.light / BSECS).toFixed(2), arts, presses, performs, staggers, buffs: E('JSON.stringify(P.belBuff)') });
}
// one use on a still dummy, tapped and held: damage per use and per FP in light hits (weapon_balance.md's art table units)
for (const hold of [1, 75]) {
  W().reset('bell', 1); arena(); W().reset('bell', 1); E('P.cds = {}'); W().dummy(30); W().log = [];
  W().down('art'); W().frame(hold); W().up('art'); for (let i = 0; i < 200 && !E("['idle','run','land'].includes(P.state)"); i++) W().frame(1);
  const h = W().log.reduce((a, l) => a + l.dmg, 0) / G.D.light;
  res[hold > 1 ? 'held' : 'tap'] = { hitsPerUse: +h.toFixed(2), perFp: +(h / 14).toFixed(3), perCdSec: +(h / 6.5).toFixed(3) };
}
return res;
