// ------------------------------------------------------------------ mouse & touch in menus (shrine, Esc menu and every screen they open)
// Menu renderers register clickable boxes each frame: uiHit(x, y, w, h, hover, click), in low-res UI coords (W×H).
//   hover(): the pointer moved onto the box (usually: select that row)
//   click(): left click / tap; when omitted: hover() and then the confirm action, exactly like Enter
// Right-click = back, the wheel = ↑/↓. Everything goes through the same actions as the keyboard (uiAct), so menus
// behave identically whichever device drives them. The skill tree has its own pointer code (58_skilltree_ui.js).
const UIM = { hits: [], shown: [], x: -1, y: -1, moved: false, overKey: null, wheel: 0, eatT: 0, cursor: false };
function uiHit(x, y, w, h, hover, click) { UIM.hits.push({ x, y, w, h, hover, click }); }
function uiAct(a) { press(a); release(a); }
function uiMouseOn() { return state === 'menu' && !!menu && !(typeof stActive === 'function' && stActive()); }
function uiEatsClick() { return uiMouseOn() || performance.now() < UIM.eatT; }   // 00_core: menu clicks never become attacks
function uiPt(e) { const r = view.getBoundingClientRect(), k = view.width / (r.width || 1); return { x: ((e.clientX - r.left) * k - ox) / scale, y: ((e.clientY - r.top) * k - oy) / scale }; }
function uiHitAt(p) {
  for (let i = UIM.shown.length - 1; i >= 0; i--) { const h = UIM.shown[i]; if (p.x >= h.x && p.x <= h.x + h.w && p.y >= h.y && p.y <= h.y + h.h) return h; }
  return null;
}
function uiSetCursor(on) { if (on === UIM.cursor) return; UIM.cursor = on; try { view.style.cursor = on ? 'pointer' : ''; } catch (e) {} }

const _uimRenderMenu = renderMenu;
renderMenu = function () {
  UIM.hits = [];
  _uimRenderMenu();
  UIM.shown = UIM.hits;
  if (!uiMouseOn()) return;
  const h = UIM.x >= 0 ? uiHitAt(UIM) : null;
  if (UIM.moved) {
    UIM.moved = false;
    const key = h ? `${Math.round(h.x)},${Math.round(h.y)},${Math.round(h.w)}` : null;
    if (key !== UIM.overKey) { UIM.overKey = key; if (h && h.hover) h.hover(); }
  }
  uiSetCursor(!!h);
};
HOOKS.update.push(() => { if (!uiMouseOn()) { if (UIM.cursor && !(typeof stActive === 'function' && stActive())) uiSetCursor(false); UIM.overKey = null; } });

addEventListener('pointermove', e => {
  if (e.pointerType !== 'mouse') return;
  const p = uiPt(e);
  if (Math.abs(p.x - UIM.x) + Math.abs(p.y - UIM.y) > 0.3) { UIM.x = p.x; UIM.y = p.y; UIM.moved = true; }
});
view.addEventListener('pointerdown', e => {
  if (!uiMouseOn()) return;
  const p = uiPt(e); UIM.x = p.x; UIM.y = p.y; UIM.eatT = performance.now() + 300;
  if (e.button === 2) { e.preventDefault(); uiAct('back'); return; }
  if (e.button !== 0) return;
  const h = uiHitAt(p); if (!h) return;
  UIM.overKey = `${Math.round(h.x)},${Math.round(h.y)},${Math.round(h.w)}`;
  if (h.click) h.click(); else { if (h.hover) h.hover(); uiAct('confirm'); }
});
view.addEventListener('wheel', e => {
  if (!uiMouseOn()) return;
  e.preventDefault();
  UIM.wheel += e.deltaY * (e.deltaMode === 1 ? 16 : 1);
  let n = 0;
  while (Math.abs(UIM.wheel) >= 40 && n++ < 4) { const d = Math.sign(UIM.wheel); UIM.wheel -= d * 40; uiAct(d < 0 ? 'up' : 'down'); }
}, { passive: false });

// footer key chips: clicking one does what the key does
const UI_KEY_ACT = { Esc: 'back', Enter: 'confirm', Tab: 'map', Q: 'spell' };
