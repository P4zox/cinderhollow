// the old endings still work (kindle / ash), backing out of the choice re-offers it, and dying to Venn lets you retry
const log = [];
const adv = n => { for (let i = 0; i < n; i++) { G.step(2, [], ['interact']); G.step(2, [], ['interact']); } };
const setup = async () => {
  await boot();
  G.give({ flags: { ...G.SAVE.flags, 'boss:omen': 1, 'boss:sovereign': 1, 'cut:sovereign': 1 }, shrine: 'X4', shrines: ['R1', 'X4'] });
  G.tp('X5', 36, 10); G.step(20);
  const npc = G.props.find(p => p.vnEnd); G.P.x = npc.x - 20; return npc;
};
for (const [which, downs] of [['kindle', 0], ['ash', 1]]) {
  const npc = await setup();
  G.vn.vnOfferEnding(npc); adv(3);
  for (let i = 0; i < downs; i++) G.step(2, [], ['down']);
  G.step(2, [], ['interact']);
  for (let i = 0; i < 10 && G.state === 'dialog'; i++) adv(1);
  G.step(60); await snap('e_' + which + '_cine');
  for (let i = 0; i < 20 && G.state === 'cine'; i++) G.step(80, [], ['interact']);
  log.push({ which, state: G.state, ending: G.SAVE.ending, endings: { ...G.SAVE.endings }, boss: G.boss && G.boss.kind });
}
// back out of the choice with Esc, then talk to her again; then "…No. Let me choose again." then walk away
{
  const npc = await setup();
  G.vn.vnOfferEnding(npc); adv(3); G.step(2, [], ['pause']);
  log.push({ backedOut: G.state, ending: G.SAVE.ending || null, npcStill: G.props.includes(npc) });
  G.step(10, [], ['interact']);   // talk again (custom interact)
  log.push({ retalk: G.state });
  adv(1); G.step(2, [], ['down']); G.step(2, [], ['down']); G.step(2, [], ['interact']); adv(2);
  G.step(2, [], ['down']); G.step(2, [], ['interact']);   // "...No. Let me choose again."
  await snap('e_choose_again');
  log.push({ again: G.state, betrayed: !!G.SAVE.flags.venn_betrayed });
  G.step(2, [], ['pause']);
  // leave the room and come back: she still waits with the choice
  G.tp('X4', 12, 10); G.step(10); G.tp('X5', 3, 10); G.step(10);
  log.push({ reenter: !!G.props.find(p => p.vnEnd), vennInX4: false });
}
// refuse, die, respawn at the Crown Shrine, walk back in: the fight is waiting, fog closes, no cutscene
{
  const npc = await setup();
  G.vn.vnOfferEnding(npc); adv(3); G.step(2, [], ['down']); G.step(2, [], ['down']); G.step(2, [], ['interact']);
  adv(2); G.step(2, [], ['interact']); adv(4);
  for (let i = 0; i < 80 && G.state !== 'play'; i++) G.step(10, [], ['pause']);
  log.push({ fight: G.boss.kind, active: G.boss.active });
  G.P.hp = 1; G.boss.cool = 0; G.P.x = G.boss.x - 30;
  for (let i = 0; i < 400 && G.state === 'play'; i++) G.step(1);
  log.push({ afterHit: G.state, php: G.P.hp });
  for (let i = 0; i < 100 && G.room !== 'X4' && G.room !== 'R1'; i++) G.step(10);
  for (let i = 0; i < 60 && G.state !== 'play'; i++) G.step(10);
  log.push({ respawnRoom: G.room, state: G.state, vennNpcX4: G.props.some(p => p.type === 'npc' && p.id === 'venn') });
  G.tp('X5', 1, 10); G.step(30);
  log.push({ inX5: G.room, boss: G.boss && G.boss.kind, active: G.boss && G.boss.active, fog: G.props.filter(p => p.type === 'fog').map(p => p.on()), endNpc: !!G.props.find(p => p.vnEnd) });
  for (let i = 0; i < 60; i++) G.step(4, ['right']);
  await snap('e_retry');
  log.push({ px: Math.round(G.P.x), active: G.boss.active, state: G.state, cut: !!G.cut, fog: G.props.filter(p => p.type === 'fog').map(p => p.on()), hp: G.boss.hp });
  // can't walk out through the fog
  for (let i = 0; i < 120; i++) G.step(4, ['left']);
  log.push({ blockedAt: Math.round(G.P.x), room: G.room });
}
return log;
