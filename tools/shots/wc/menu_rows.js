window.__rows = "GFX_ROWS.push({ k: 'shakeLvl', label: 'Screen shake', opts: ['Off', 'Low', 'Full'], desc: 'x' }, { k: 'wtrail', label: 'Weapon trail', opts: ['Off', 'On'], desc: 'A faint streak of light follows the blade tip.' })";
// WC: the Graphics menu (with the two WC rows if present) and the Settings › Screen shake row
await boot(); const o = [];
const key = (code, type='keydown') => window.dispatchEvent(new KeyboardEvent(type, { code, bubbles: true }));
const tap = async code => { key(code); G.step(1); key(code, 'keyup'); G.step(1); };
if (window.__rows) G.feel.ev(window.__rows);
await tap('Escape'); await tap('KeyQ'); G.step(2); await snap('settings');
for (let i = 0; i < 3; i++) await tap('ArrowDown'); await tap('Enter'); G.step(2); await snap('gfx');
const n = G.feel.ev('GFX_ROWS.length'); for (let i = 0; i < n - 1; i++) await tap('ArrowDown'); G.step(2); await snap('gfx_last');
await tap('ArrowRight'); G.step(2); o.push('after right on last row: wtrail=' + G.SETTINGS.wtrail + ' shake=' + G.SETTINGS.shake); await snap('gfx_last2');
await tap('ArrowUp'); await tap('ArrowRight'); G.step(2); o.push('after right on row n-2: wtrail=' + G.SETTINGS.wtrail + ' shake=' + G.SETTINGS.shake);
o.push('saved json has shakeLvl? ' + /shakeLvl/.test(localStorage.getItem(Object.keys(localStorage).find(k => /settings/i.test(k)) || '') || ''));
return o;
