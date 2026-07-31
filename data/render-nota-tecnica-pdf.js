// Renderiza data/_nota-tecnica-estudo11.html em materiais/Nota-Tecnica-Estudo-11-IBS-Nacional.pdf
// Uso: node data/render-nota-tecnica-pdf.js
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await browser.newPage();
  const inputPath = path.join(__dirname, '_nota-tecnica-estudo11.html');
  const outputPath = path.join(__dirname, '..', 'materiais', 'Nota-Tecnica-Estudo-11-IBS-Nacional.pdf');
  await page.goto('file://' + inputPath, { waitUntil: 'networkidle' });
  await page.pdf({
    path: outputPath,
    format: 'A4',
    printBackground: true,
    margin: { top: '0', bottom: '0', left: '0', right: '0' },
  });
  await browser.close();
  console.log('Gravado em ' + outputPath);
})();
