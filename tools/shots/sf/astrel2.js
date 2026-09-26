await boot(); window.__godS = true;
G.give({ items: { wings: 1, talon: 1, hook: 1, emberdash: 1, gale: 1, slam: 1 }, stats: { vig: 30, mnd: 15, end: 25, str: 22, dex: 18, fth: 10 } });
G.SAVE.flags['cut:astrel'] = 1;
const out = {};
G.tp('SF7', 5, 16); S(10);
for (let i = 0; i < 200 && !(G.boss && G.boss.active); i++) S(2, ['right']);
const b = G.boss; S(200);
out.start = { state: b.state, cons: b.cons, x: Math.round(b.x) };
// edges: pin the player at each fog wall / wall and force every movement move
const moves = ['dash', 'leap', 'thrust', 'combo', 'upslash', 'counter', 'rain', 'well'];
out.edges = [];
for (const side of ['L', 'R']) {
  G.P.x = side === 'L' ? 2 * 16 + 14 : 46 * 16 + 4; G.P.y = b.floor; S(2);
  for (const m of moves) {
    b.state = 'idle'; b.cool = 99; S(1);
    if (m === 'dash') b.startDash(); else if (m === 'counter') b.startCounter(); else if (m === 'rain' || m === 'well') b.startCast(m); else b.start(m);
    let minX = 1e9, maxX = -1e9, maxY = -1e9;
    for (let i = 0; i < 150; i++) { S(1); minX = Math.min(minX, b.x); maxX = Math.max(maxX, b.x); maxY = Math.max(maxY, b.y); if (b.state === 'idle') break; }
    out.edges.push(`${side}:${m}: x ${Math.round(minX)}..${Math.round(maxX)} (arena ${b.L}..${b.R}) y<=${Math.round(maxY)} floor ${b.floor}`);
  }
}
// nova: force phase 3
b.state = 'idle'; b.phase = 2; b.hp = Math.round(b.maxHp * 0.19); b.cool = 0; S(5);
for (let i = 0; i < 60 && G.state === 'cut'; i++) S(1, [], ['pause']);
for (let i = 0; i < 400 && b.state !== 'nova'; i++) { S(1); if (G.state === 'cut') S(1, [], ['pause']); }
out.nova0 = { state: b.state, phase: b.phase, monos: window.__sf.SFA.monos.length };
// hide behind the left monolith
G.P.x = b.L + 30; G.P.y = b.floor; const hp0 = G.P.hp; window.__godS = false;
for (let i = 0; i < 900 && b.state === 'nova'; i++) { S(1); G.P.x = b.L + 30; if (i === 300) await snap('nova_hide'); }
out.novaHid = { took: Math.round(hp0 - G.P.hp), max: G.D.maxHp, state: b.state, desperate: b.desperate };
window.__godS = true; S(200);
// second nova: stand in the open, then strike her down instead
b.novaCool = 0; b.state = 'idle'; for (let i = 0; i < 300 && b.state !== 'nova'; i++) S(1);
window.__godS = false; G.P.hp = G.D.maxHp; G.P.x = b.mid + 100; const h1 = G.P.hp;
for (let i = 0; i < 900 && b.state === 'nova'; i++) { S(1); G.P.x = b.mid + 100; }
out.novaOpen = { took: Math.round(h1 - G.P.hp), state: b.state };
window.__godS = true; S(100);
b.novaCool = 0; b.state = 'idle'; for (let i = 0; i < 300 && b.state !== 'nova'; i++) S(1);
for (let i = 0; i < 200 && b.nova && b.nova.st !== 'charge'; i++) S(1);
for (let k = 0; k < 12 && b.state === 'nova'; k++) { b.hit({ dmg: 60, poise: 10, dir: 1, kind: 'light', x: b.x, y: b.y - 40, melee: true }); S(10); }
S(40); out.novaBroken = { state: b.state, t: b.t, critable: b.critable && b.critable() };

// kill her: check reward flags and fog
b.hp = 1; b.state = 'idle'; b.hit({ dmg: 50, poise: 0, dir: 1, kind: 'light', x: b.x, y: b.y - 40, melee: true });
S(120); await snap('dead1');
await new Promise(r => setTimeout(r, 9500)); S(30);
out.after = { moonstep: G.SAVE.items.moonstep, flag: G.SAVE.flags['boss:astrel'], fog: G.props.filter(p => p.type === 'fog' && p.on()).length, grav: window.__sf.SFA.grav, dyn: G.room };
await snap('dead2');
return out;
