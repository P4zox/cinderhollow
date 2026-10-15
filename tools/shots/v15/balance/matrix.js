// every boss x every type at the expected build for the boss's stage; ARGS: { kinds?, types?, seeds?, o? }
const kinds = ARGS.kinds || E('Object.keys(BOSS_STAGE)'), types = ARGS.types || E('MV.order.slice()'), seeds = ARGS.seeds || [1, 2, 3];
const rows = [];
for (const k of kinds) for (const ty of types) for (const s of seeds) {
  try { rows.push(E(`window.__bb.fight('${k}', '${ty}', ${JSON.stringify({ ...(ARGS.o || {}), seed: s })})`)); }
  catch (e) { rows.push({ kind: k, type: ty, err: String(e.message).slice(0, 120) }); }
}
return rows;
