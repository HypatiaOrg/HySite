// Inspect the Next.js pages of a running HySite the way the browser's DevTools would, without a screen:
// console errors, failed requests, sideways overflow, accessibility basics, text contrast (WCAG AA),
// and a full-page screenshot of each page at desktop and phone widths.
//
//   cd frontend && npm install --no-save playwright-core && npx playwright-core install --with-deps chromium
//   node ../scripts/inspect_pages.mjs http://localhost [screenshot-folder]
//
// Requests to other sites (analytics, fonts) are blocked, so the checks are about this site alone.
// A Next.js prefetch answered with a 307 (a new _rsc key) is normal and not reported.
import { chromium } from 'playwright-core';
const base = process.argv[2] ?? 'http://localhost';
const shotDir = process.argv[3];
import { mkdirSync } from 'node:fs';
if (shotDir) mkdirSync(shotDir, { recursive: true });
const pages = ['/', '/help', '/about', '/acknowledgements', '/api', '/style', '/scatter', '/targets', '/hist'];
const widths = [1280, 390];
const browser = await chromium.launch({ args: ['--no-proxy-server'] });

function luminance([r, g, b]) {
  const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
for (const path of pages) {
  for (const width of widths) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    const console_ = [], failed = [];
    page.on('console', (m) => { if (['error', 'warning'].includes(m.type()) && !/ERR_FAILED/.test(m.text())) console_.push(`${m.type()}: ${m.text().slice(0, 160)}`); });
    page.on('pageerror', (e) => console_.push(`pageerror: ${e.message.slice(0, 160)}`));
    page.on('response', (r) => { if (r.status() >= 400) failed.push(`${r.status()} ${r.url()}`); });
    // a prefetch cut short when the page closes is not a failure
    page.on('requestfailed', (r) => { if (/_rsc=/.test(r.url())) return; });
    page.on('requestfailed', (r) => { if (!/googletagmanager|google-analytics|fonts\.|_rsc=/.test(r.url())) failed.push(`failed ${r.url()}`); });
    await page.route(/^https?:\/\/(?!localhost)/, (route) => route.abort());
    const response = await page.goto(base + path, { waitUntil: 'load' });
    await page.waitForTimeout(400);
    const report = await page.evaluate((w) => {
      const out = { overflow: document.documentElement.scrollWidth > w, a11y: [], contrast: [] };
      for (const img of document.images) if (!img.alt) out.a11y.push(`img without alt: ${img.src.slice(-40)}`);
      for (const a of document.links) if (!a.textContent.trim() && !a.getAttribute('aria-label')) out.a11y.push(`link without text: ${a.href}`);
      const levels = [...document.querySelectorAll('h1,h2,h3,h4')].map((h) => Number(h.tagName[1]));
      for (let i = 1; i < levels.length; i++) if (levels[i] > levels[i - 1] + 1) { out.a11y.push(`heading jumps h${levels[i - 1]} -> h${levels[i]}`); break; }
      if (!document.querySelector('main')) out.a11y.push('no <main>');
      if (!document.title) out.a11y.push('no title');
      // the text colors in use against their backgrounds (sampled)
      const canvas = document.createElement('canvas'); canvas.width = canvas.height = 1;
      const ctx = canvas.getContext('2d', { willReadFrequently: true });
      const rgb = (css, over) => { ctx.fillStyle = over; ctx.fillRect(0, 0, 1, 1); ctx.fillStyle = css; ctx.fillRect(0, 0, 1, 1);
        const d = ctx.getImageData(0, 0, 1, 1).data; return `rgb(${d[0]}, ${d[1]}, ${d[2]})`; };
      const seen = new Map();
      for (const el of document.querySelectorAll('p, li, dt, dd, h1, h2, h3, a, code, span, div')) {
        if (!el.childNodes.length || ![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) continue;
        const cs = getComputedStyle(el);
        let bg = 'rgba(0, 0, 0, 0)', p = el;
        while (p && (bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent')) { bg = getComputedStyle(p).backgroundColor; p = p.parentElement; }
        if (!p) bg = 'rgb(255, 255, 255)';
        bg = rgb(bg, 'rgb(255, 255, 255)');
        const key = cs.color + '|' + bg + '|' + (parseFloat(cs.fontSize) >= 24 || (parseFloat(cs.fontSize) >= 18.66 && Number(cs.fontWeight) >= 700) ? 'large' : 'normal');
        if (!seen.has(key)) seen.set(key, { color: cs.color, bg, size: key.split('|')[2], sample: el.textContent.trim().slice(0, 30) });
      }
      out.contrast = [...seen.values()];
      return out;
    }, width);
    for (const c of report.contrast) {
      const L1 = luminance(c.color.match(/[\d.]+/g).slice(0, 3).map(Number)), L2 = luminance(c.bg.match(/[\d.]+/g).slice(0, 3).map(Number));
      c.ratio = ((Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05)).toFixed(2);
      c.pass = c.ratio >= (c.size === 'large' ? 3 : 4.5);
    }
    const low = report.contrast.filter((c) => !c.pass).map((c) => `${c.color} on ${c.bg} (${c.size}) ${c.ratio}:1 "${c.sample}"`);
    console.log(`\n## ${path} @ ${width}  status ${response.status()}`);
    console.log(`overflow: ${report.overflow}  console: ${console_.length}  failed requests: ${failed.length}  a11y: ${report.a11y.length}  low contrast: ${low.length}`);
    for (const line of [...console_, ...failed, ...report.a11y, ...low]) console.log('  - ' + line);
    if (shotDir) await page.screenshot({ path: `${shotDir}/${path === '/' ? 'home' : path.slice(1)}-${width}.png`, fullPage: true });
    await page.close();
  }
}
await browser.close();
