await boot(); G.SAVE.seenAreas = { hoarfrost: 1 }; G.give({ items: { talon: 1, hook: 1, emberdash: 1 } }); G.SETTINGS.god = true;
const RB = window.__rb, sim = RB.sim, out = [];
G.tp('HF12', 27, 14); G.step(5);
const ic = () => G.props.filter(p => p.type === 'hf_icicle').map(p => `${(p.x/16).toFixed(0)}:${p.st}:${Math.round(p.y)}`).join(' ');
out.push('P ' + (G.P.x/16).toFixed(1) + ',' + (G.P.y/16).toFixed(1) + ' ' + ic());
for (let i = 0; i < 8; i++) { sim(10); out.push(`${i} ${ic()} feet ${RB.XRB.feet.length}`); }
return out;
