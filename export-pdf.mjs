import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile, rm } from 'node:fs/promises';
import { dirname, extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const deckDir = dirname(fileURLToPath(import.meta.url));
const htmlDir = resolve(deckDir, '_slides');
const output = resolve(deckDir, 'out', 'lean-trust-freiburg.pdf');
const width = 1920;
const height = 1080;
const mimeTypes = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.gif': 'image/gif', '.webp': 'image/webp', '.woff': 'font/woff',
  '.woff2': 'font/woff2', '.ttf': 'font/ttf',
};

// Serve locally so Verso's code highlighting and proof information can load.
const server = createServer(async (request, response) => {
  try {
    const path = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    if (path === '/favicon.ico') {
      response.writeHead(204).end();
      return;
    }
    const file = resolve(htmlDir, `.${path === '/' ? '/index.html' : path}`);
    if (!file.startsWith(htmlDir + sep)) {
      response.writeHead(403).end();
      return;
    }
    const body = await readFile(file);
    response.writeHead(200, { 'Content-Type': mimeTypes[extname(file)] ?? 'application/octet-stream' });
    response.end(body);
  } catch {
    response.writeHead(404).end();
  }
});

let browser;
try {
  await readFile(resolve(htmlDir, 'index.html'));
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const origin = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({
    headless: true,
    ...(process.env.CHROME ? { executablePath: process.env.CHROME } : { channel: 'chrome' }),
  });
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => {
    if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
  });
  page.on('requestfailed', request => errors.push(`Failed to load ${request.url()}`));
  // The exported artifact must not depend on web fonts or other remote assets.
  await page.route('**/*', route => {
    if (new URL(route.request().url()).origin === origin) return route.continue();
    errors.push(`External asset: ${route.request().url()}`);
    return route.abort();
  });
  // Render the actual HTML presentation. Do not enter Reveal's print layout.
  await page.emulateMedia({ media: 'screen' });
  await page.goto(origin, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.Reveal?.isReady());
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(Array.from(document.images, image => image.decode()));
  });
  await page.addStyleTag({ content: `
    @page { size: ${width}px ${height}px; margin: 0; }
    html, body { width: ${width}px; height: ${height}px; }
    * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .reveal .controls, .reveal .progress { display: none !important; }
    .reveal .slides section .fragment { transition: none !important; }
  ` });
  const indices = await page.evaluate(() => {
    Reveal.configure({ transition: 'none', backgroundTransition: 'none', autoSlide: 0 });
    // Reused slides may override the global transition with their own metadata.
    Reveal.getSlides().forEach(slide => slide.setAttribute('data-transition', 'none'));
    return Reveal.getSlides().map(slide => Reveal.getIndices(slide));
  });
  if (!indices.length) throw new Error('No slides found.');
  const pagesDir = resolve(dirname(output), 'pages');
  await rm(pagesDir, { recursive: true, force: true });
  await rm(resolve(dirname(output), 'browser'), { recursive: true, force: true });
  const previewsDir = resolve(dirname(output), 'browser');
  await mkdir(pagesDir, { recursive: true });
  await mkdir(previewsDir, { recursive: true });
  const pages = [];
  const problems = [];
  for (const [index, position] of indices.entries()) {
    await page.evaluate(async ({ h, v }) => {
      Reveal.slide(h, v, Number.MAX_SAFE_INTEGER);
      await Promise.all(Array.from(Reveal.getCurrentSlide().querySelectorAll('img'), image => image.decode()));
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    }, position);

    const problem = await page.evaluate(() => {
      const slide = Reveal.getCurrentSlide();
      // Scroll extents include empty margins and padding. Check the painted
      // text and images instead, so empty space cannot reject a fitting slide.
      const visible = element => {
        if (element.closest('aside.notes, .hover-container, .hover-info, script, style, title, desc')) return false;
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.display !== 'none' && style.visibility !== 'hidden' &&
          Number(style.opacity) !== 0 && rect.width > 0 && rect.height > 0;
      };
      const outside = rect => rect.left < -2 || rect.top < -2 ||
        rect.right > innerWidth + 2 || rect.bottom > innerHeight + 2;
      for (const image of slide.querySelectorAll('img, svg[role="img"]')) {
        if (visible(image) && outside(image.getBoundingClientRect())) {
          return `Image exceeds the viewport: ${image.getAttribute('alt') ?? image.querySelector('title')?.textContent ?? 'SVG'}`;
        }
      }
      const walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const node = walker.currentNode;
        if (!node.textContent.trim() || !visible(node.parentElement)) continue;
        const range = document.createRange();
        range.selectNodeContents(node);
        if (outside(range.getBoundingClientRect())) {
          return `Text exceeds the viewport: ${node.textContent.trim().slice(0, 100)}`;
        }
      }
      for (const code of slide.querySelectorAll('code.hl.lean.block')) {
        if (getComputedStyle(code).boxShadow !== 'none') return 'Unexpected code-block shadow';
        if (code.scrollWidth > code.clientWidth + 2 || code.scrollHeight > code.clientHeight + 2) {
          return 'Code block has clipped content';
        }
      }
      return null;
    });
    if (problem) problems.push(`Slide ${index + 1}: ${problem}`);
    if (errors.length) { problems.push(...errors.map(e => `Slide ${index + 1}: ${e}`)); errors.length = 0; }

    const number = String(index + 1).padStart(3, '0');
    // These screenshots are for direct visual comparison, not PDF input.
    await page.screenshot({ path: resolve(previewsDir, `slide-${number}.png`) });
    const path = resolve(pagesDir, `slide-${number}.pdf`);
    await page.pdf({
      path,
      preferCSSPageSize: true,
      printBackground: true,
      displayHeaderFooter: false,
    });
    pages.push(path);
  }
  execFileSync('pdfunite', [...pages, output], { stdio: 'inherit' });
  console.log(`Wrote ${output} (${pages.length} slides, original HTML screen layout, vector text).`);
  await writeFile(resolve(dirname(output), 'problems.txt'), problems.join('\n') + '\n');
  console.log(problems.length ? `PROBLEMS (${problems.length}):\n` + problems.join('\n') : 'No layout problems.');
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
} finally {
  await browser?.close();
  if (server.listening) await new Promise(resolve => server.close(resolve));
}
