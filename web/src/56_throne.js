// ------------------------------------------------------------------ The Pale Throne: after the story, the only way to begin again
// Finishing the game drops you back into the world (the ending screen no longer starts New Game+). The empty throne in the
// Heart of the Root (X5) offers the next journey: sit, confirm, and the Hallow resets as Journey N+1 (startNGPlus).
const throneReady = () => !!SAVE.ending && !(boss && boss.alive) && !props.some(p => p.vnEnd) && state === 'play';
function throneOffer() {
  const next = (SAVE.ngp || 0) + 2;
  P.face = 1; setP('idle', 'idle', true);
  startDialogue([
    { t: 'The Pale Throne is cold, and the Root is quiet beneath it.', lore: true },
    { t: 'If you sit, the Hallow begins again. The shrines go dark, the fallen rise, and every foe returns crueler. Your strength, your gear and your Chronicle remain.', lore: true },
    { choice: [
      [`Sit, and begin Journey ${next}`, [{ do() { dialog.after = throneSit; } }]],
      ['Rise, and walk on', []],
    ] },
  ], null);
}
function throneSit() {
  setP('rest', pHas('rest') ? 'rest' : 'heal', false); P.vx = 0;
  sfx.kindle(); flashScreen = Math.max(flashScreen, 0.5); shake = Math.max(shake, 3);
  throneT = 1.2;   // a breath on the throne before the world turns over (game time, so pausing waits too)
}
let throneT = 0;
HOOKS.update.push(dt => { if (throneT > 0 && (throneT -= dt) <= 0) fadeTo(() => startNGPlus()); });
HOOKS.enter.push(def => {
  if (def.id !== 'X5') return;
  const t = props.find(p => p.type === 'throne'); if (!t) return;
  t.prompt = () => throneReady() ? 'Sit upon the throne' : null;
  t.interact = () => { if (throneReady()) throneOffer(); };
});
