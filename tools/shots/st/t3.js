await boot(); const o = [];
const settle = (n = 30) => { for (let i = 0; i < n; i++) G.step(1); };
const view = document.getElementById('game');
const cl = (x, y) => { const r = view.getBoundingClientRect(), p = G.st.pt(x, y), k = view.width / r.width; return { clientX: r.left + p.sx / k, clientY: r.top + p.sy / k }; };
const ev = (type, x, y, extra = {}) => { const c = cl(x, y); const e = new PointerEvent(type, { bubbles: true, pointerId: 1, pointerType: 'mouse', button: 0, buttons: type === 'pointerup' ? 0 : 1, ...c, ...extra }); (type === 'pointerdown' ? view : window).dispatchEvent(e); };
const mouse = (type, x, y) => { const c = cl(x, y); view.dispatchEvent(new MouseEvent(type, { bubbles: true, button: 0, ...c })); };
const S = G.SAVE; S.skills = ['keen_edge']; S.shards = 6;
G.st.open(0); settle();
// ---- mouse: hover a node -> it becomes the cursor
let p = G.st.nodeScreen('heavy_hand'); ev('pointermove', p.x, p.y, { buttons: 0 }); settle(3);
o.push('hover sel: ' + G.st.ST.sel);
// click once -> armed, click again -> learned (the mousedown's 'attack' must be swallowed)
ev('pointerdown', p.x, p.y); mouse('mousedown', p.x, p.y); ev('pointerup', p.x, p.y); settle(3);
o.push('armed: ' + G.st.ST.arm + ' learned? ' + S.skills.includes('heavy_hand'));
await snap('m1_armed_mouse');
ev('pointerdown', p.x, p.y); mouse('mousedown', p.x, p.y); ev('pointerup', p.x, p.y); settle(10);
o.push('after 2nd click learned? ' + S.skills.includes('heavy_hand') + ' pts ' + G.st.pts);
// drag pans the camera
const c0 = { ...G.st.ST.cam }; ev('pointerdown', 120, 120); ev('pointermove', 60, 90); ev('pointermove', 30, 80); ev('pointerup', 30, 80); settle(10);
o.push(`drag cam ${Math.round(c0.x)},${Math.round(c0.y)} -> ${Math.round(G.st.ST.cam.x)},${Math.round(G.st.ST.cam.y)}`);
await snap('m2_dragged');
// wheel zoom
const zi0 = G.st.ST.zi; { const c = cl(120, 110); view.dispatchEvent(new WheelEvent('wheel', { bubbles: true, cancelable: true, deltaY: 120, ...c })); } settle(20);
o.push('wheel out: zi ' + zi0 + ' -> ' + G.st.ST.zi);
// click the Arsenal tab
ev('pointerdown', 212, 13); ev('pointerup', 212, 13); settle(10); o.push('tab click page ' + G.st.ST.page);
// click the Build tab in the panel
ev('pointerdown', 342, 36); ev('pointerup', 342, 36); settle(5); o.push('summary ' + G.st.ST.summary);
await snap('m3_tab_build');
ev('pointerdown', 298, 36); ev('pointerup', 298, 36); settle(5); o.push('summary after node tab ' + G.st.ST.summary);
// ---- controller: fake a standard pad
let pad = { id: 'Fake Pad (STANDARD GAMEPAD)', connected: true, buttons: Array.from({ length: 17 }, () => ({ pressed: false, value: 0 })), axes: [0, 0, 0, 0] };
navigator.getGamepads = () => [pad];
const btn = async (i) => { pad.buttons[i] = { pressed: true, value: 1 }; G.pad(1 / 60); settle(2); pad.buttons[i] = { pressed: false, value: 0 }; G.pad(1 / 60); settle(2); };
G.pad(1 / 60); settle(2);
await btn(4); o.push('LB page ' + G.st.ST.page);
const s0 = G.st.ST.sel; await btn(15); o.push('D-pad right: ' + s0 + ' -> ' + G.st.ST.sel);
await btn(7); o.push('RT zoom ' + G.st.ST.zi);
await btn(6); o.push('LT zoom ' + G.st.ST.zi);
await btn(3); o.push('Y summary ' + G.st.ST.summary); await btn(3);
// right stick pans
const cx0 = G.st.ST.tgt.x; pad.axes[2] = 1; settle(1); for (let i = 0; i < 20; i++) G.step(1); pad.axes[2] = 0; o.push('R-stick pan ' + Math.round(cx0) + ' -> ' + Math.round(G.st.ST.tgt.x));
await snap('m4_pad');
// A twice learns the cursor node if learnable
const sel = G.st.ST.sel; o.push('can ' + sel + ' ' + JSON.stringify(G.st.can(sel)));
await btn(0); await btn(0); o.push('A,A learned ' + S.skills.includes(sel));
await btn(1); o.push('B -> ' + (G.menu && G.menu.screen));
return o;
