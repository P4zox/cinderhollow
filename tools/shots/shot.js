// headless harness: node shot.js <script.js> [outdir]
// script body runs in the page as an async function; call await snap('name') to save the game canvas as PNG.
const puppeteer = require('puppeteer-core'); const fs = require('fs'); const path = require('path');
(async () => {
  const [,, scriptFile, outDir = path.join(__dirname, 'out')] = process.argv;
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', args: ['--autoplay-policy=no-user-gesture-required', '--mute-audio'] });
  const page = await browser.newPage(); await page.setViewport({ width: 1152, height: 648 });
  const errors = []; page.on('pageerror', e => errors.push(String(e))); page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.exposeFunction('__save', (name, url) => fs.writeFileSync(path.join(outDir, name + '.png'), Buffer.from(url.split(',')[1], 'base64')));
  const H = process.env.SHOT_HTML || path.join(__dirname, '../../web/dist/index.html'); const url = /^https?:/.test(H) ? H : 'file://' + path.resolve(H);
  await page.goto(url); await page.waitForFunction('window.__game', { timeout: 90000 }); await new Promise(r => setTimeout(r, 1500));
  const body = fs.readFileSync(scriptFile, 'utf8');
  const res = await page.evaluate(`(async () => { const G = window.__game;
    const snap = async (n) => { const c = [...document.querySelectorAll('canvas')].sort((a,b)=>b.width*b.height-a.width*a.height)[0]; await window.__save(n, c.toDataURL('image/png')); };
    const boot = async () => { G.newGame(); await new Promise(r=>setTimeout(r,800)); for (let i=0;i<300 && G.state!=='play';i++){ if (G.state==='cine'||G.state==='cut') G.step(1,[],['pause']); else G.step(10);} };
    ${body}
  })()`);
  console.log(JSON.stringify(res, null, 1)); if (errors.length) console.log('ERRORS:', errors.slice(0, 10).join('\n'));
  await browser.close();
})();
