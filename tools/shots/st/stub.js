// prototype stub: the old 15 nodes + invented fillers laid out in the new data format (used only until 57_skills.js exists)
const STUB = (() => {
  const S = [], brs = ['blade', 'ash', 'veil', 'blood', 'flame'];
  const keep = { blade: ['keen_edge', 'fourth_strike', 'charged_arts', 'riposte_mastery'], ash: ['azure_thrift', 'soul_siphon'], veil: ['quickstep', 'steadfast', 'second_wind', 'iron_flask'], blood: ['bloodthirst', 'last_stand'], flame: [] };
  const keys = { blade: 'Relentless', ash: 'Spellblade', veil: 'Shadowstep', blood: 'Crimson Pact', flame: 'Kindled' };
  brs.forEach((br, bi) => {
    const A = -Math.PI / 2 + bi * 2 * Math.PI / 5, K = keep[br].slice(); let n = 0;
    const id = () => K.length ? K.shift() : `${br}_${++n}`;
    const at = (r, da) => ({ x: Math.cos(A + da) * r, y: Math.sin(A + da) * r });
    const add = (o, r, da) => { const q = { id: o.id || id(), br, name: '', desc: 'A stub node used while prototyping the new tree screen. Its real text comes from 57_skills.js.', cost: o.cost || 1, req: o.req || [], excl: o.excl || [], ...at(r, da), ...o }; q.name = q.name || q.id.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()); q.icon = 'sk_' + q.id; S.push(q); return q.id; };
    const t1 = add({}, 1.2, 0), t2 = add({ req: [t1] }, 2.2, 0), s1 = add({ req: [t1] }, 2.0, -0.42), s2 = add({ req: [t1], cost: 2 }, 2.0, 0.42);
    const fa = id(), fb = id();
    add({ id: fa, req: [t2], excl: [fb], cost: 2 }, 3.1, -0.24); add({ id: fb, req: [t2], excl: [fa], cost: 2 }, 3.1, 0.24);
    const t3 = add({ req: [t2], cost: 2 }, 3.5, 0), t4 = add({ req: [t3], cost: 3 }, 4.5, 0);
    const ga = id(), gb = id();
    add({ id: ga, req: [t3], excl: [gb], cost: 3 }, 4.3, -0.3); add({ id: gb, req: [t3], excl: [ga], cost: 3 }, 4.3, 0.3);
    add({ id: br + '_key', key: true, req: [t4], cost: 4, name: keys[br] }, 5.6, 0);
  });
  const cls = ['sword', 'dagger', 'great', 'spear', 'katana', 'staff', 'shield', 'twin', 'scythe', 'whip'];
  cls.forEach((c, i) => S.push({ id: 'mastery_' + c, br: 'arsenal', cls: c, name: c[0].toUpperCase() + c.slice(1) + ' Mastery', desc: 'Active only while this class is equipped.', cost: 2, req: [], excl: [], x: i, y: 20, icon: 'sk_mastery_' + c }));
  ['long_hook', 'swift_glide', 'twin_dash', 'slam_wave', 'wall_glint', 'cinder_greed', 'deep_breath', 'ashen_step'].forEach((id, i) => {
    const a = -Math.PI / 2 + Math.PI / 5 + i * 2 * Math.PI / 8;
    S.push({ id, br: 'way', name: id.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), desc: 'A wayfarer utility.', cost: 1 + (i % 2), req: [], excl: [], x: Math.cos(a) * 6.7, y: Math.sin(a) * 6.7, icon: 'sk_' + id });
  });
  return S;
})();
const stubOn = () => { const K = G.st.SKILLS; if (!K.some(s => s.x !== undefined)) { K.length = 0; K.push(...STUB); G.st.reset(); } };
