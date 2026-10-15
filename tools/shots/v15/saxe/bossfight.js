// v15 Switch Axe vs real bosses (Training Grounds summon), with the v15 balance bot (tools/shots/v15/balance/bot_lib.js):
//   SHOT_HTML=web/dist/v15_saxe.html sh tools/shots/v15/balance/run.sh tools/shots/v15/saxe/bossfight.js tools/shots/v15/saxe/out
// The bot plays the blade J J J J in the boss's openings, rolls a share of the blows (the roll's window), presses I the
// moment the gauge locks (Morph slash) and then plays the axe J J J; from Mastery III it cashes a 40-52 gauge in as a Full
// Release. Compared with the Longsword and Greatsword bots on the same bosses / seeds / builds.
const kinds = ARGS.kinds || ['hound', 'warden', 'kalden', 'librarian'], seeds = ARGS.seeds || [1, 2];
E(`window.__bb.PROF.saxe = { de: 12, route: ['J','J','J','J'], def: 'roll', win: 280 }`);
E(`(() => { if (window.__sxBot) return; window.__sxBot = 1;
  HOOKS.update.push(() => {
    if (!window.__bb.on || !mvOn('saxe') || !P.ground) return;
    const free = ['idle', 'run', 'land'].includes(P.state) || (ATK[P.state] && P.mvT > 40 && !P.mvQ && !ATK[P.state].mv.loop);
    if (!free || !boss || !boss.active) return;
    const near = Math.abs(boss.x - P.x) < 70;
    if (!P.sxAxe && P.sxLock && near) { buffered.set('parry', performance.now()); MV.sxBotMorph = (MV.sxBotMorph || 0) + 1; }
    else if (P.sxAxe && mvHas(3) && P.sxG >= 40 && P.sxG < 52 && near) buffered.set('parry', performance.now());
  });
  for (const k of ['sxMorphs', 'sxVents', 'sxReleases', 'sxWhiffs', 'sxLost', 'sxFull']) MV[k] = 0;
})()`);
const rows = [];
for (const k of kinds) for (const s of seeds) for (const ty of ['saxe', 'longsword', 'greatsword']) {
  E("for (const k of ['sxMorphs', 'sxVents', 'sxReleases', 'sxWhiffs', 'sxLost', 'sxFull']) MV[k] = 0");
  const r = E(`window.__bb.fight('${k}', '${ty}', { seed: ${s}, secs: 150 })`);
  if (ty === 'saxe') r.sx = E("({ morphs: MV.sxMorphs, full: MV.sxFull, vents: MV.sxVents, releases: MV.sxReleases, whiffs: MV.sxWhiffs, lostToHits: Math.round(MV.sxLost) })");
  rows.push([r.kind, r.type, 'seed' + s, 'killed ' + r.killed, r.secs + 's', 'dps ' + r.dps, 'taken ' + r.taken, 'hits ' + r.hits, 'stag ' + r.staggers, r.sx ? JSON.stringify(r.sx) : '', r.dmgBy].join(' | '));
}
return rows;
