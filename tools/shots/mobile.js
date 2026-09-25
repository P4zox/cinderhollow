const puppeteer = require('puppeteer-core'); const path = require('path'); const fs = require('fs');
(async () => {
  const H = process.argv[2]; const url = /^https?:/.test(H) ? H : 'file://' + path.resolve(H);
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', args: ['--mute-audio'] });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1');
  await page.setViewport({ width: 844, height: 390, isMobile: true, hasTouch: true, deviceScaleFactor: 3, isLandscape: true });
  const errs = []; page.on('pageerror', e => errs.push(String(e)));
  const t0 = Date.now(); await page.goto(url);
  await new Promise(r => setTimeout(r, 300)); await page.screenshot({ path: 'out/m_loading.png' });
  await page.waitForFunction('window.__game && window.__game.state === "title"', { timeout: 60000 });
  await new Promise(r => setTimeout(r, 800)); await page.screenshot({ path: 'out/m_title.png' });
  // tap Jump (confirm) to start a new game
  await page.tap('button[data-act="confirm"]'); await new Promise(r => setTimeout(r, 2500));
  const st = await page.evaluate(() => window.__game.state); await page.screenshot({ path: 'out/m_game.png' });
  console.log(JSON.stringify({ ms: Date.now() - t0, state: st, errs }));
  await browser.close();
})();
