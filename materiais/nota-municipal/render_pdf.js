// Converte o HTML da nota em PDF A4 pelo Chromium: node render_pdf.js nota-3201308.html saida.pdf
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const path = require('path');
(async () => {
  const [entrada, saida] = process.argv.slice(2);
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage();
  await p.goto('file://' + path.resolve(entrada));
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: saida, format: 'A4', printBackground: true, preferCSSPageSize: true });
  await b.close();
})();
