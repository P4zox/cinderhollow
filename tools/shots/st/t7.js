await boot(); const o = [];
const settle = (n = 30) => { for (let i = 0; i < n; i++) G.step(1); };
const view = document.getElementById('game');
const cl = (x, y) => { const r = view.getBoundingClientRect(), p = G.st.pt(x, y), k = view.width / r.width; return { clientX: r.left + p.sx / k, clientY: r.top + p.sy / k }; };
const tap = (x, y) => { const c = cl(x, y); view.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerId: 7, pointerType: 'touch', button: 0, ...c })); window.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 7, pointerType: 'touch', button: 0, ...c })); view.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, button: 0, ...c })); window.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, button: 0, ...c })); };
const S = G.SAVE; S.skills = ['keen_edge']; S.shards = 6; G.st.open(0); settle();
let p = G.st.nodeScreen('fourth_strike'); tap(p.x, p.y); settle(3); o.push('tap1 sel ' + G.st.ST.sel + ' arm ' + G.st.ST.arm);
tap(p.x, p.y); settle(3); o.push('tap2 arm ' + G.st.ST.arm);
tap(p.x, p.y); settle(3); o.push('tap3 learned ' + S.skills.includes('fourth_strike'));
// tap the panel's Learn button: select a node, then hit the action bar twice
p = G.st.nodeScreen('heavy_hand'); tap(p.x, p.y); settle(3);
tap(300, 197); settle(3); o.push('button arm ' + G.st.ST.arm); tap(300, 197); settle(3); o.push('button learned ' + S.skills.includes('heavy_hand'));
// footer Esc -> back to the shrine
tap(300, 211); settle(3);
o.push('menu now ' + (G.menu && G.menu.screen));
return o;
