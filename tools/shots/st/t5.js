await boot(); const o = [];
const settle = (n = 30) => { for (let i = 0; i < n; i++) G.step(1); };
o.push('room ' + G.room + ' props ' + G.props.map(p => p.type).filter(t => /shrine/.test(t)).join(','));
let sh = G.props.find(p => p.type === 'shrine');
if (!sh) { G.tp('R1', 5, 10); settle(5); sh = G.props.find(p => p.type === 'shrine'); o.push('R1 props ' + G.props.map(p => p.type).join(',')); }
if (sh) {
  G.P.x = sh.x; G.P.y = sh.y; settle(5);
  G.step(1, [], ["interact"]); settle(10); await new Promise(r => setTimeout(r, 700)); settle(10);
  o.push('state ' + G.state + ' menu ' + (G.menu && G.menu.screen));
  if (G.state === 'menu') {
    G.step(1, [], ['down']); settle(3); G.step(1, [], ['confirm']); settle(30);
    o.push('after Skill Tree: ' + G.menu.screen); await snap('p_from_shrine');
    G.step(1, [], ['right']); settle(10); G.step(1, [], ['confirm']); settle(5); await snap('p_armed_kb');
    G.step(1, [], ['pause']); settle(5); o.push('Esc from armed -> ' + G.menu.screen + ' arm ' + G.st.ST.arm);
    G.step(1, [], ['pause']); settle(5); o.push('Esc again -> ' + (G.menu && G.menu.screen)); await snap('p_back_shrine');
  }
}
return o;
