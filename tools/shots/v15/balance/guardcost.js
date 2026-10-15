// block cost vs stamina along the journey: a typical boss blow (~18% of max HP, the bot's median big hit) blocked by each guard
return E(`(() => { const out = []; for (const s of [1, 3, 5, 7, 9, 11, 13]) { const X = window.__bb.expected(s); SAVE.stats = { ...X.st }; refreshDerived(false);
  const blow = D.maxHp * 0.18; const row = ['stage ' + s, 'HP ' + D.maxHp, 'St ' + Math.round(D.maxSt), 'blow ' + Math.round(blow)];
  for (const ty of ['sns', 'greatsword', 'spear']) { wmEquip(ty, { quiet: true }); refreshDerived(false); const c = mvGuardCost(blow, {}).cost; row.push(ty + ' ' + Math.round(c) + ' (' + (D.maxSt / c).toFixed(1) + ' blocks)'); }
  out.push(row.join('  ')); } return out; })()`);
