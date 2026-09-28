await boot(); const o = [];
const names = new Set(JSON.parse(JSON.stringify(G.st.SKILLS.map(s => s.icon || 'sk_' + s.id))));
const J = window.__stIcons || null;
o.push('nodes ' + G.st.SKILLS.length);
const miss = G.st.SKILLS.filter(s => !G.st.hasIcon(s.icon || 'sk_' + s.id)).map(s => s.id);
o.push('missing icons: ' + (miss.join(',') || 'none'));
const dmiss = G.st.SKILLS.filter(s => !G.st.hasIcon((s.icon || 'sk_' + s.id).replace(/^sk_/, 'skd_'), 'sk_icons_dim')).map(s => s.id);
o.push('missing dim: ' + (dmiss.join(',') || 'none'));
return o;
