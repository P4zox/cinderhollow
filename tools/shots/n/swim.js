// The drowned gate: without Tidebreath the sump won't take you under; with it you swim the U-bend to the east chamber.
await boot(); G.give({ stats: { vig: 60 } });
const out = [];
const run = async (tb) => {
  G.SAVE.items.tidebreath = tb ? 1 : undefined; delete G.SAVE.flags['lever:NV1'];
  G.tp('NV1', 9, 21); G.step(10);
  for (let i = 0; i < 40; i++) G.step(2, ['left']);          // walk into the west pool
  const a = [Math.round(G.P.x / 16), Math.round(G.P.y / 16), G.P.state];
  for (let i = 0; i < 60; i++) G.step(2, ['down']);           // dive
  const b = [Math.round(G.P.x / 16), Math.round(G.P.y / 16), G.P.state];
  for (let i = 0; i < 200; i++) G.step(2, G.P.y < 26.5 * 16 ? ['down', 'right'] : ['right']);   // along the tunnel
  const c = [Math.round(G.P.x / 16), Math.round(G.P.y / 16), G.P.state];
  await snap('swim_' + (tb ? 'tb' : 'no'));
  for (let i = 0; i < 80; i++) G.step(2, ['up'], i % 10 === 0 ? ['jump'] : []);   // up the east pool, out through the grate
  for (let i = 0; i < 30; i++) G.step(2, ['right'], i % 6 === 0 ? ['jump'] : []);
  const d = [Math.round(G.P.x / 16), Math.round(G.P.y / 16), G.P.state, Math.round(G.P.hp)];
  out.push(`${tb ? 'WITH' : 'WITHOUT'} tidebreath: in pool ${a} dive ${b} tunnel ${c} out ${d}`);
};
await run(false); G.P.hp = 999;
await run(true);
return out;
