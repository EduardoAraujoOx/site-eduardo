// Converte HTMLs da nota em PDF A4 pelo Chromium e avisa se algum conteúdo passa do rodapé de alguma página.
// Uso: node render_pdf.js nota-3201308.html [nota-outro.html ...]  (o PDF sai ao lado, com o mesmo nome)
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  for (const entrada of process.argv.slice(2)) {
    const p = await b.newPage({ viewport: { width: 794, height: 1123 } });
    await p.goto('file://' + path.resolve(entrada));
    await p.evaluate(() => document.fonts.ready);
    const avisos = await p.evaluate(() => {
      const mm = 96 / 25.4, out = [];
      document.querySelectorAll('.page').forEach((pg, i) => {
        const topo = pg.getBoundingClientRect().top, limite = topo + (297 - 17.5) * mm;
        let max = 0, quem = '';
        pg.querySelectorAll('*').forEach(el => {
          if (el.closest('.cab, .rod, .qrbox') && !el.closest('.citar')) return;
          if (el.closest('.cab, .rod')) return;
          const r = el.getBoundingClientRect();
          if (r.height > 0 && r.bottom > max) { max = r.bottom; quem = el.tagName + '.' + (el.className && el.className.baseVal === undefined ? el.className : ''); }
        });
        if (max > limite + 1) out.push(`página ${i + 1}: conteúdo passa ${((max - limite) / mm).toFixed(1)} mm do limite (${quem})`);
      });
      return out;
    });
    const saida = entrada.replace(/\.html$/, '.pdf');
    await p.pdf({ path: saida, format: 'A4', printBackground: true, preferCSSPageSize: true });
    console.log(saida, avisos.length ? 'ATENÇÃO: ' + avisos.join('; ') : 'ok');
    await p.close();
  }
  await b.close();
})();
