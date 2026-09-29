// Release build smoke test (no debug hooks): node tools/shots/release_test.js <html> <outdir>
// Plays through real key presses, checks no debug handle is reachable, saves are signed, and a hand-edited save is
// marked tampered while still loading.
const puppeteer = require('puppeteer-core'); const fs = require('fs'); const path = require('path');
(async () => {
  const [,, H = 'web/dist/index.html', outDir = path.join(__dirname, 'out_release')] = process.argv;
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', args: ['--autoplay-policy=no-user-gesture-required', '--mute-audio', '--allow-file-access-from-files'] });
  const page = await browser.newPage(); await page.setViewport({ width: 1152, height: 648 });
  const errors = []; page.on('pageerror', e => errors.push(String(e))); page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  const out = [], wait = ms => new Promise(r => setTimeout(r, ms));
  const shot = async n => { await page.screenshot({ path: path.join(outDir, n + '.png') }); };
  const key = async (k, hold = 60) => { await page.keyboard.down(k); await wait(hold); await page.keyboard.up(k); await wait(120); };
  await page.goto('file://' + path.resolve(H)); await wait(7000);
  await page.mouse.click(576, 324); await wait(300);
  const leaks = await page.evaluate(() => Object.getOwnPropertyNames(window).filter(k => k.startsWith('__')));
  out.push('window.__* left: ' + JSON.stringify(leaks));
  out.push('reachable: ' + JSON.stringify(await page.evaluate(() => ({ game: typeof window.__game, P: typeof P, SAVE: typeof SAVE, boss: typeof boss, hurtPlayer: typeof hurtPlayer }))));
  await shot('01_title');
  // New Game -> difficulty (Normal) -> skip the intro
  await key('Enter'); await wait(400); await shot('02_diff'); await key('Enter'); await wait(1500);
  for (let i = 0; i < 6; i++) { await key('Escape'); await wait(500); }
  await wait(1500); await shot('03_play');
  for (let i = 0; i < 8; i++) { await key('KeyD', 200); await key('KeyJ'); }
  await key('Space', 200); await wait(600); await shot('04_moved');
  await key('Escape'); await wait(500); await shot('05_menu'); await key('Escape'); await wait(500);
  const raw = await page.evaluate(() => localStorage.getItem('cinderhollow_save_v1'));
  const sv = raw && JSON.parse(raw);
  out.push('save written: ' + !!raw + ' signed: ' + !!(sv && /^[0-9a-f]{16}$/.test(sv.sig || '')));
  // hand-edit the save (cinders) keeping the old signature, reload, continue: it must still load and be marked
  await page.evaluate(() => { const s = JSON.parse(localStorage.getItem('cinderhollow_save_v1')); s.cinders = 999999; localStorage.setItem('cinderhollow_save_v1', JSON.stringify(s)); });
  await page.reload(); await wait(7000); await page.mouse.click(576, 324); await wait(300);
  await key('Enter'); await wait(3000);   // Continue
  await key('Escape'); await wait(400); for (let i = 0; i < 2; i++) { await key('KeyE'); await wait(300); }
  await shot('06_status_tampered');
  await key('Escape'); await wait(400);
  const after = JSON.parse(await page.evaluate(() => localStorage.getItem('cinderhollow_save_v1')));
  out.push('after edit: cinders=' + after.cinders + ' tampered=' + after.tampered);
  out.push('page errors: ' + JSON.stringify(errors.slice(0, 5)));
  console.log(JSON.stringify(out, null, 1));
  await browser.close();
})();
