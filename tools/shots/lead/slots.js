// save slots: New Game archives the current journey (max 3 old), a full list asks which to forget, Load swaps journeys
await boot();
const E = G.sk.ev, out = [];
localStorage.removeItem('cinderhollow_old_saves_v1');
const mark = v => { G.SAVE.stats.vig = v; E('saveGame()'); };   // tag each journey by its Vigor
const vigOf = raw => JSON.parse(raw).stats.vig;
const olds = () => E('oldSaves()').map(o => vigOf(o.data));
const cur = () => vigOf(E('curSaveRaw()'));
const title = () => { E("state = 'title'; menu = null; titleSel = 0; TITLE_DIFF.open = false; TITLE_SLOTS.screen = null"); G.step(2); };
const choose = name => { const i = E('titleOptions()').indexOf(name); E(`titleSel = ${i}`); G.step(1, [], ['confirm']); G.step(2); };
const startNew = () => { choose('New Game'); if (E('TITLE_DIFF.open')) { G.step(1, [], ['confirm']); G.step(2); E("newGame(true)"); G.step(3); } };
mark(11);
for (const v of [12, 13, 14]) { title(); startNew(); mark(v); }
out.push(`after 3 new games: current ${cur()} old ${JSON.stringify(olds())}  options ${JSON.stringify((title(), E('titleOptions()')))}`);
// 4th: the old list is full -> replace screen
title(); choose('New Game'); out.push('4th New Game opens ' + E('TITLE_SLOTS.screen'));
await snap('replace');
G.step(1, [], ['down']); G.step(1, [], ['confirm']); out.push('popup ' + E('TITLE_SLOTS.pop && TITLE_SLOTS.pop.opts.join("/")'));
G.step(1, [], ['left']); G.step(1, [], ['confirm']); out.push('forget chosen -> difficulty open ' + E('TITLE_DIFF.open'));
G.step(1, [], ['confirm']); G.step(2); E('newGame(true)'); G.step(3); mark(15);
out.push(`after replace: current ${cur()} old ${JSON.stringify(olds())} (12 forgotten)`);
// Load Journey: open the oldest (vig 11) -> it becomes current, 15 goes to the old list
title(); choose('Load Journey'); out.push('load screen ' + E('TITLE_SLOTS.screen') + ' rows ' + E('slotRows().length'));
await snap('load');
for (let i = 0; i < 3; i++) G.step(1, [], ['down']);
G.step(1, [], ['confirm']); out.push('row popup ' + E('TITLE_SLOTS.pop && TITLE_SLOTS.pop.opts.join("/")'));
G.step(1, [], ['confirm']); G.step(5);
out.push(`loaded: state ${G.state} current ${cur()} SAVE vig ${G.SAVE.stats.vig} old ${JSON.stringify(olds())}`);
// forget one from the load screen
title(); choose('Load Journey'); G.step(1, [], ['down']); G.step(1, [], ['confirm']); G.step(1, [], ['right']); G.step(1, [], ['confirm']);
out.push('ask ' + E('TITLE_SLOTS.pop && TITLE_SLOTS.pop.ask'));
G.step(1, [], ['left']); G.step(1, [], ['confirm']); out.push(`after forget: old ${JSON.stringify(olds())}`);
// backing out of the difficulty chooser keeps the current journey where it is
title(); const c0 = cur(), o0 = JSON.stringify(olds()); choose('New Game'); G.step(1, [], ['back']);
out.push(`New Game then Esc: current ${cur()} (was ${c0}) old ${JSON.stringify(olds())} (was ${o0})`);
return out;
