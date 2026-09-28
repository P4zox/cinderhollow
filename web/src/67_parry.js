// ------------------------------------------------------------------ Parrying great foes: break their rhythm, not just their stance
// On top of the existing parry (hurtPlayer's parry branch + each boss's onParried stance hit):
//   * every parry deals ~30% of the boss's stance bar (the flat +90 of onParried is topped up to that), so three clean
//     parries break a stance at any stage of the journey;
//   * two parries in a row (within PARRY_CHAIN s) interrupt the combo: the boss recoils for PARRY_RECOIL s and its
//     attack ends -- a real opening;
//   * the stance immunity after a stagger is 3 s instead of 7, so parries count again soon after a critical;
//   * weapon / limb strikes that were never flagged parryable are (PARRY_MELEE); slams, stomps, grabs, breath,
//     magic and projectiles stay unparryable.
const PARRY_STANCE = 0.3, PARRY_CHAIN = 1.6, PARRY_RECOIL = 0.55, PARRY_IMMUNE = 3;
const PARRY_MELEE = {   // boss kind -> attack names (boss.atk) whose hits become parryable
  hound: ['sweep'], omen: ['rising', 'flurry', 'sweep'], vessel: ['sweep'], ice_warden: ['sweep'], bellringer: ['swing'],
  overseer: ['bash'], ferryman: ['hook'], choir: ['sweep'], enforcer: ['bash'], vael: ['overhead', 'string', 'combo'],
  astrel: ['thrust', 'upslash', 'combo'], sanguine: ['cut'], venn: ['string', 'sweep', 'rising'], sovereign: ['sweep'],
};
const NO_RECOIL = new Set(['stagger', 'dead', 'dormant', 'intro', 'transform', 'xform', 'break', 'summon', 'cyberWait', 'phase', 'p2', 'rise', 'sunk', 'crit']);
function parryBody(src) {   // the thing that was parried: the boss itself, or one body of a duo / trio
  if (!src || !boss) return null;
  if (src === boss) return boss;
  if (boss.parts && boss.parts.includes(src)) return src;
  return null;
}
{ const _hurt = hurtPlayer; hurtPlayer = function (dmg, dir, id, opt = {}) {
    const t = parryBody(opt && opt.src);
    if (t && !opt.parryable && boss && boss.active) {
      const list = PARRY_MELEE[boss.kind], atk = t.atk || boss.atk;
      if (list && atk && list.includes(atk)) opt = { ...opt, parryable: true };
    }
    if (t && opt.parryable && typeof t.stance === 'number') t._stance0 = t.stance;   // stance before onParried
    return _hurt.call(this, dmg, dir, id, opt);
  }; }
HOOKS.parry.push(src => {
  const t = parryBody(src); if (!t || !t.alive || !boss.active) return;
  const now = time;
  // stance: top the boss's own parry hit up to PARRY_STANCE of its bar
  if (typeof t.stance === 'number' && t.stanceMax > 0 && !(t.stanceImmune > 0) && t.state !== 'stagger') {
    const gained = t.stance - (t._stance0 ?? t.stance), want = t.stanceMax * PARRY_STANCE;
    if (gained < want) t.stance += want - gained;
    if (t.stance >= t.stanceMax && typeof t.stagger === 'function' && (!t.canStagger || t.canStagger())) { t.stagger(); return; }
  }
  t._stance0 = undefined;
  // rhythm: the second parry in a row breaks the combo
  t._pChain = now - (t._pT ?? -9) < PARRY_CHAIN ? (t._pChain || 1) + 1 : 1;
  t._pT = now;
  parryFeedback(t, t._pChain >= 2);
  if (t._pChain >= 2 && !NO_RECOIL.has(t.state)) { t._pChain = 0; parryRecoil(t); }
});
function parryFeedback(t, broke) {
  t.flash = Math.max(t.flash || 0, broke ? 1 : 0.6);
  const hb = t.hurtbox && t.hurtbox(), x = hb ? (hb.x0 + hb.x1) / 2 : t.x, y = hb ? hb.y0 - 6 : t.y - 40;
  popups.push({ x, y, v: broke ? 'BROKEN' : 'PARRIED', color: broke ? '#ffd070' : '#e6dcc4', life: 0.8 });
  if (broke) { tone(988, 0.25, 0.08, 'triangle', 0.6); tone(494, 0.35, 0.06, 'square', 0.9); shake = Math.max(shake, 5); hitstop = Math.max(hitstop, 0.12); }
}
// recoil: the boss is knocked back and frozen for a moment, then its attack is dropped
function parryRecoil(t) {
  if (t._recoilT > 0) return;
  t._recoilT = PARRY_RECOIL; t._recoilDir = Math.sign(t.x - P.x) || 1;
  P.gcT = Math.max(P.gcT, 0.9);   // the guard counter window stays open through the recoil
  if (!t._recoilWrapped) {
    t._recoilWrapped = true;
    const _up = t.update;
    t.update = function (dt, ...rest) {
      if (this._recoilT > 0 && this.alive && !NO_RECOIL.has(this.state)) {
        this._recoilT -= dt;
        const nx = this.x + this._recoilDir * 40 * dt * (this._recoilT / PARRY_RECOIL);   // a short shove, easing out
        if (!solidAtPx(nx + this._recoilDir * 10, this.y - 8)) this.x = nx;
        if (this.flash !== undefined) this.flash = Math.max(this.flash, 0.25);
        if (this.stanceImmune > 0) this.stanceImmune -= dt;
        if (this._recoilT <= 0) parryEndAttack(this);
        return;
      }
      this._recoilT = 0;
      return _up.call(this, dt, ...rest);
    };
  }
}
function parryEndAttack(t) {   // back to a neutral beat: whatever swing or chain was running is over
  if (t.hitIds && t.hitIds.clear) t.hitIds.clear();
  if ('chain' in t) t.chain = 0;
  if (t.state !== 'idle' && !NO_RECOIL.has(t.state) && t.anim && t.anim.sh && t.anim.sh.has && t.anim.sh.has('idle')) {
    t.state = 'idle'; t.anim.set('idle', true);
  }
  if ('t' in t) t.t = Math.max(0, Math.min(t.t || 0, 0.3));
  if ('cool' in t) t.cool = Math.max(t.cool || 0, 0.45);
}
// a critical opens a 3 s window of stance immunity (was 7)
HOOKS.update.push(() => {
  if (!boss) return;
  for (const t of boss.parts ? [boss, ...boss.parts] : [boss]) {
    if (!t) continue;
    if (t.stanceImmune > PARRY_IMMUNE && !t._immCap) { t.stanceImmune = PARRY_IMMUNE; t._immCap = true; }
    if (!(t.stanceImmune > 0)) t._immCap = false;
  }
});
