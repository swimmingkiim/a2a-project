const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');
const MarkdownIt = require('markdown-it');
const hljs = require('highlight.js');
const mk = require('@iktakahiro/markdown-it-katex');

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value;
      } catch (__) { }
    }
    return ''; // use external default escaping
  }
});

// mk handles KaTeX correctly!
md.use(mk);

const files = [
  "docs/RESEARCH_SYNTHESIS.md",
  "docs/RESEARCH_SYNTHESIS_EN.md",
  "docs/SIMULATION_PAPER_EN.md",
  "docs/SIMULATION_PAPER.md",
  "docs/philosophy/SIMULATION_PAPER_APPENDIX_EN.md",
  "docs/philosophy/SIMULATION_PAPER_APPENDIX.md",
  "docs/FINDINGS_SUMMARY.md",
  "docs/FINDINGS_SUMMARY_EN.md"
];

const css = `
  @import url('https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css');
  @import url('https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css');
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600&family=Noto+Serif+KR:wght@400;700&display=swap');

  body { 
    font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', 'Noto Sans KR', sans-serif; 
    font-size: 11pt; 
    line-height: 1.6; 
    color: #333; 
    word-break: keep-all; 
    overflow-wrap: break-word; 
    margin: 0;
    padding: 0;
  }
  h1, h2, h3, h4, h5 { 
    font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', 'Noto Serif KR', serif; 
    color: #111; 
    margin-top: 1.5em; 
  }
  table { width: 100%; border-collapse: collapse; margin-bottom: 2em; page-break-inside: auto; font-size: 0.95em; }
  th { background-color: #f8f9fa; text-align: left; padding: 12px; border-bottom: 2px solid #dee2e6; font-weight: 600; }
  td { padding: 12px; border-bottom: 1px solid #dee2e6; }
  tr:nth-child(even) { background-color: #fcfcfc; }
  tr { page-break-inside: avoid; page-break-after: auto; }
  code { font-family: 'Menlo', 'Monaco', monospace; background-color: #f1f3f5; padding: 0.2em 0.4em; border-radius: 3px; font-size: 0.9em; }
  pre code { display: block; padding: 1em; overflow-x: auto; background-color: #f8f9fa; border: 1px solid #dee2e6; }
  blockquote { border-left: 4px solid #007bff; margin-left: 0; padding-left: 1em; color: #555; background: #f8f9fa; margin-bottom: 1.5em; }
  img { max-width: 100%; max-height: 45vh; object-fit: contain; height: auto; display: block; margin: 1.5em auto; page-break-inside: avoid; }
  
  /* Math container styles */
  .katex-display { margin: 1.5em 0; overflow-x: auto; overflow-y: hidden; text-align: center; }
  .katex { font-size: 1.15em; }
`;

async function generate() {
  console.log("Launching Puppeteer...");
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();

  // Route local file requests so they can bypass strict CORS/path issues if any,
  // but usually absolute file:// paths are fine in evaluate.
  // We'll rewrite the paths directly.

  for (const file of files) {
    if (!fs.existsSync(file)) {
      console.log(`File not found: ${file}`);
      continue;
    }

    console.log(`Processing ${file}...`);
    let content = fs.readFileSync(file, 'utf8');

    // Convert math tags if necessary
    let htmlBody = md.render(content);

    // Resolve relative image paths and inline them as base64 to avoid Puppeteer local file restrictions
    const baseDir = path.resolve(path.dirname(file));
    htmlBody = htmlBody.replace(/src="([^"]+)"/g, (match, src) => {
      if (!src.startsWith('http') && !src.startsWith('data:')) {
        const absPath = path.resolve(baseDir, src);
        if (fs.existsSync(absPath)) {
          const ext = path.extname(absPath).substring(1);
          const base64Text = fs.readFileSync(absPath, { encoding: 'base64' });
          return 'src="data:image/' + ext + ';base64,' + base64Text + '"';
        }
        return 'src="file://' + absPath + '"';
      }
      return match;
    });

    const fullHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>${css}</style>
</head>
<body>
  ${htmlBody}
</body>
</html>`;

    // Wait until network is idle to make sure external fonts and katex css and local images are loaded
    await page.setContent(fullHtml, { waitUntil: 'load' });

    // Explicitly wait for all fonts to be ready
    await page.evaluateHandle('document.fonts.ready');

    // Explicitly wait for images to load to prevent missing graphics
    await page.evaluate(async () => {
      await Promise.all(
        Array.from(document.images).map(img => {
          if (img.complete) return Promise.resolve();
          return new Promise((resolve) => {
            img.onload = resolve;
            img.onerror = resolve; /* resolve on error to prevent hang */
          });
        })
      );
    });

    const outPdf = file.replace(/\.md$/, '.pdf');
    await page.pdf({
      path: outPdf,
      format: 'A4',
      printBackground: true,
      displayHeaderFooter: true,
      headerTemplate: '<div></div>',
      footerTemplate: '<div style="font-size: 9px; text-align: center; width: 100%; border-top: 1px solid #eee; padding-top: 5px; color: #888; font-family: sans-serif;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
      margin: {
        top: '25mm',
        bottom: '25mm',
        left: '20mm',
        right: '20mm'
      }
    });
    console.log(`=> Created ${outPdf}`);
  }

  await browser.close();
  console.log("All PDFs generated successfully!");
}

generate().catch(console.error);
