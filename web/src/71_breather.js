// ------------------------------------------------------------------ A breath between a great foe's attacks
// Bosses used to pick their next attack 0.1-0.6 s after the last one ended, leaving no time to strike back. When a boss
// (or one body of a duo/trio) comes out of an attack into a calm state, its next attack now waits at least
// BREATH[phase] seconds: 0.9 s in phase 1, 0.75 s in phase 2, 0.65 s in phase 3. Combos inside one attack are unchanged;
// bosses that already rest longer are unchanged.
const BREATH = [0.9, 0.9, 0.75, 0.65];
const BREATH_CALM = new Set(['idle', 'walk', 'run', 'glide', 'approach', 'backstep', 'blinking', 'ready', 'recover', 'goto', 'pace', 'stalk', 'hover', 'circle', 'drift']);
const BREATH_SKIP = new Set(['dormant', 'intro', 'stagger', 'dead', 'transform', 'xform', 'toppled', 'rising', 'sunk', 'cyberWait']);
function breathBodies() { return boss ? (boss.parts ? [boss, ...boss.parts.filter(q => q && q.state !== undefined)] : [boss]) : []; }
HOOKS.update.push(() => {
  if (!boss || !boss.active) return;
  for (const b of breathBodies()) {
    const st = b.state; if (st === undefined) continue;
    const calm = BREATH_CALM.has(st), skip = BREATH_SKIP.has(st);
    if (calm && b._breathAtk) {
      const g = BREATH[clamp(b.phase || boss.phase || 1, 1, 3)];
      if (typeof b.cool === 'number' && b.cool < g) b.cool = g;
      if (typeof b.breathe === 'function') b.breathe(g);   // bosses with their own pacing hook in here
    }
    b._breathAtk = !calm && !skip;
  }
});
