// WA1 in-game check: every WA1 v13 tag drawn by the engine (player sheet + its weapon overlay) on its hit frame.
// SHOT_HTML=web/dist/wa1.html node tools/shots/shot.js tools/shots/wa1/ingame.js <outdir>
await boot();
const P = () => G.P;
const T = {
  longsword: [['ls_kc_hold', 0], ['ls_kc', 3], ['ls_jjk', 3], ['ls_jjjk', 3], ['ls_quick', 2], ['ls_step', 2], ['ls_fore_stance', 1], ['ls_fore_cut', 2], ['ls_pommel', 2]],
  katana: [['kt_sheathe', 3], ['kt_sheathed_idle', 0], ['kt_sheathed_walk', 2], ['kt_iai', 2], ['kt_focus_hold', 1], ['kt_focus', 2], ['kt_iai_parry', 3], ['kt_sidestep', 1], ['kt_stepcut', 2], ['kt_flurry', 4], ['kt_flash', 2], ['kt_rush', 3]],
  greatsword: [['gs_charge_hold', 0], ['gs_charged', 2], ['gs_strong', 3], ['gs_true1', 2], ['gs_true2', 4], ['gs_guard', 0], ['gs_tackle', 1], ['gs_rollheavy', 3], ['gs_wrath', 3]],
  maul: [['ml_1', 5], ['ml_2', 4], ['ml_3', 3], ['ml_charge_walk', 2], ['ml_charge_idle', 0], ['ml_upswing', 3], ['ml_double', 7], ['ml_bigsmash', 5], ['ml_spin', 1], ['ml_spin_end', 3], ['ml_brace', 1], ['ml_rollswing', 2], ['ml_bb1', 2], ['ml_bb2', 2], ['ml_bb3', 3], ['ml_bb4', 5], ['ml_quake', 4]],
  knight_shield: [['sh_4', 2], ['sh_rush_hold', 1], ['sh_rush', 3], ['sh_backhop', 2], ['sh_leap', 3], ['sh_slam', 3], ['sh_fallbash', 2]],
};
const out = {}, sh = () => G.sheet ? G.sheet('player') : null;
for (const [w, list] of Object.entries(T)) {
  G.SAVE.weapon = w;
  for (let i = 0; i < 20; i++) { G.step(1); await new Promise(r => setTimeout(r, 100)); }   // let the overlay sheet load
  for (const [tag, k] of list) {
    const p = P(); p.state = 'wa1test'; p.vx = 0;
    p.anim.set(tag, true, 0); p.anim.i = k;
    G.step(1);
    out[tag] = { has: p.anim.n > 1 || tag.endsWith('hold'), n: p.anim.n, frame: p.anim.frame, i: p.anim.i, tag: p.anim.tag, x: Math.round(p.x), y: Math.round(p.y) };
    await snap(`${w}_${tag}`);
  }
}
return out;
