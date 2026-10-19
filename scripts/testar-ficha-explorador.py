#!/usr/bin/env python3
"""Smoke test real do portal; não grava dados nem chama APIs de produção.

Requer Python com Playwright e Chromium. --bibliotecas pode apontar para cópias
locais de chart.umd.min.js e d3.min.js para uma execução sem acesso aos CDNs.
"""
import argparse
import csv
import io
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import unquote, urlsplit
from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bibliotecas', type=Path)
    parser.add_argument('--fontes', type=Path)
    parser.add_argument('--chromium', default='/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None)
    parser.add_argument('--saida', type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    portal = repo / 'municipios-na-reforma'
    output = args.saida or repo / 'artifacts/ficha-explorador'
    output.mkdir(parents=True, exist_ok=True)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(portal), **kw)

        def translate_path(self, path):
            clean = unquote(urlsplit(path).path)
            if clean.startswith('/data/'):
                requested = (repo / clean.lstrip('/')).resolve()
                if requested.is_relative_to(repo / 'data'):
                    return str(requested)
            return super().translate_path(path)

        def do_GET(self):
            endpoint = urlsplit(self.path).path
            if endpoint in ('/api/lead', '/api/geo'):
                body = b'{"ativo":false}' if endpoint == '/api/lead' else b'{"uf":null}'
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(body)
            else:
                super().do_GET()

        def log_message(self, *a):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    checks = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=args.chromium, headless=True, args=['--no-sandbox'])
        for device, width, height in [('desktop', 1512, 1100), ('mobile', 390, 844)]:
            context = browser.new_context(viewport={'width': width, 'height': height}, has_touch=device == 'mobile', accept_downloads=True)

            def route(route):
                url = route.request.url
                if args.bibliotecas and 'cdn.jsdelivr.net/npm/chart.js@' in url:
                    route.fulfill(path=str(args.bibliotecas / 'chart.umd.min.js'), content_type='application/javascript')
                elif args.bibliotecas and 'cdn.jsdelivr.net/npm/d3@' in url:
                    route.fulfill(path=str(args.bibliotecas / 'd3.min.js'), content_type='application/javascript')
                elif args.fontes and 'fonts.googleapis.com' in url:
                    route.fulfill(body='@font-face{font-family:Inter;src:url(/__inter.woff2);font-weight:100 900}@font-face{font-family:Montserrat;src:url(/__montserrat.woff2);font-weight:100 900}', content_type='text/css')
                elif args.fontes and url.endswith('/__inter.woff2'):
                    route.fulfill(path=str(args.fontes / 'inter.woff2'), content_type='font/woff2')
                elif args.fontes and url.endswith('/__montserrat.woff2'):
                    route.fulfill(path=str(args.fontes / 'montserrat.woff2'), content_type='font/woff2')
                elif urlsplit(url).hostname == '127.0.0.1' or urlsplit(url).hostname == 'cdn.jsdelivr.net':
                    route.continue_()
                else:
                    # No external API calls, geolocation, forms, tracking, or messaging.
                    route.abort()

            context.route('**/*', route)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(base + '/?m=2929206&visual=novo', wait_until='domcontentloaded')
            root = page.locator('#fichaExplorador')
            expect(root.locator('#difference')).to_have_text('+ R$ 421,4 mi', timeout=20000)
            page.evaluate('document.fonts.ready')
            assert page.evaluate('document.documentElement.scrollWidth') == width
            expect(page.locator('#fichaTitulo')).to_contain_text('São Francisco do Conde')
            assert page.locator('html.ficha-preview-nova').count() == 1
            assert not page.locator('#gSerie').is_visible()
            assert page.evaluate("Chart.getChart(document.querySelector('#gSerie')) == null")
            expect(page.locator('#miniSvg')).to_be_visible()
            page.screenshot(path=str(output / f'site-{device}.png'), full_page=True, animations='disabled')
            page.screenshot(path=str(output / f'site-{device}-tela.png'), animations='disabled')
            root.locator('#stage').screenshot(path=str(output / f'grafico-{device}.png'), animations='disabled')

            root.locator('#time').focus()
            page.keyboard.press('ArrowLeft')
            expect(root.locator('#readout-year')).to_have_text('2032')
            expect(root.locator('#comp-year')).to_have_text('2032')
            expect(root.locator('#difference')).to_have_text('+ R$ 140,4 mi')
            root.get_by_role('button', name='Impacto da reforma', exact=True).click()
            expect(root.locator('#legend')).to_contain_text('Diferença:')
            root.get_by_role('button', name='Receita', exact=True).click()
            root.get_by_role('button', name='+ Histórico', exact=True).click()
            expect(root.locator('#chart')).to_contain_text('Sem projeção')
            root.get_by_role('button', name='Transição', exact=True).click()
            box = root.locator('#chart').bounding_box()
            if device == 'desktop':
                page.mouse.move(box['x'] + 45, box['y'] + 150)
                expect(root.locator('#readout-year')).to_have_text('2032')
                page.mouse.click(box['x'] + 45, box['y'] + 150)
            else:
                page.touchscreen.tap(box['x'] + 34, box['y'] + 150)
            expect(root.locator('#readout-year')).to_have_text('2029')
            root.locator('.band-label[data-key="cpt"]').click()
            expect(root.locator('#component-title')).to_have_text('O histórico participa da repartição.')
            root.get_by_role('button', name='Ver composição completa', exact=True).click()
            root.get_by_role('button', name='Mostrar tabela', exact=True).click()
            assert root.locator('#rows tr').count() == 5
            root.locator('[data-row-year="2031"]').click()
            expect(root.locator('#difference')).to_have_text('+ R$ 102,6 mi')
            root.get_by_role('button', name='Mostrar gráfico', exact=True).click()
            with page.expect_download() as download:
                root.get_by_role('button', name='Baixar dados da ficha', exact=True).click()
            download.value.save_as(output / f'exportacao-{device}.csv')
            rows = list(csv.DictReader(io.StringIO((output / f'exportacao-{device}.csv').read_text(encoding='utf-8-sig')), delimiter=';'))
            assert len(rows) == 5
            original = json.loads((repo / 'data/painel-municipios/BA.json').read_text())['municipios']['2929206']
            assert abs(float(rows[-1]['impacto_reais_2025'].replace(',', '.')) - (original['pos_por_ano']['2033'] - original['contrafactual_por_ano']['2033'])) < .01

            # Existing chart controls remain usable after removing positional coupling.
            page.locator('#compModo [data-modo="rs"]').click()
            assert page.evaluate("Chart.getChart(document.querySelector('#gComp')).options.scales.y.max !== 100")
            page.locator('#compModo [data-modo="pct"]').click()
            assert page.evaluate("Chart.getChart(document.querySelector('#gComp')).options.scales.y.max === 100")

            root.get_by_role('button', name='Assistir à transição', exact=True).click()
            expect(root.locator('#readout-year')).to_have_text('2029')
            expect(root.locator('#readout-year')).to_have_text('2033', timeout=10000)
            root.get_by_role('button', name='Assistir à transição', exact=True).click()
            if device == 'mobile':
                page.locator('#navToggle').click()
            page.locator('.tab-btn[data-view="agenda"]').click()
            expect(root.locator('#play')).to_have_attribute('aria-pressed', 'false')
            assert page.locator('html.ficha-preview-nova').count() == 0
            if device == 'mobile':
                page.locator('#navToggle').click()
            page.locator('.tab-btn[data-view="municipio"]').click()
            assert page.locator('html.ficha-preview-nova').count() == 1

            # Search changes the actual municipality, retaining the preview parameter.
            field = page.locator('#buscaMuni')
            field.fill('Catu')
            option = page.locator('#sugestoesMuni [data-cod="2907509"]')
            expect(option).to_be_visible()
            option.click()
            expect(page.locator('#fichaTitulo')).to_contain_text('Catu')
            root = page.locator('#fichaExplorador')
            expect(root.locator('#difference')).to_contain_text('− R$')
            expect(root.locator('#percent')).to_contain_text('−22,6%')
            assert 'visual=novo' in page.url and 'm=2907509' in page.url
            assert root.locator('#difference.neg').count() == 1
            root.get_by_role('button', name='Impacto da reforma', exact=True).click()
            assert 'NaN' not in root.locator('#chart').inner_html()
            assert 'NaN' not in root.inner_text()

            # Zero/neutral rows must render without division by zero; mounting never
            # modifies its input. Incomplete rows deliberately decline the new UI.
            edge = page.evaluate('''async () => {
                const model = (await fetch('/data/painel-municipios/BA.json').then(r => r.json())).municipios['2929206'];
                const zero = structuredClone(model);
                for (const yr of ['2029','2030','2031','2032','2033']) {
                    zero.pos_por_ano[yr] = 0;
                    zero.contrafactual_por_ano[yr] = 0;
                    zero.variacao_por_ano[yr] = 0;
                    zero.componentes_por_ano[yr] = {origem:0,cpt:0,destino:0,seguro:0};
                }
                const before = JSON.stringify(zero);
                const mount = document.createElement('div');
                document.body.append(mount);
                const instance = FichaExplorador.montar(mount,{municipio:zero});
                const valid = !!instance && !/NaN|Infinity/.test(mount.innerHTML);
                const immutable = JSON.stringify(zero) === before;
                instance?.destruir();
                mount.remove();
                const incomplete = structuredClone(model);
                delete incomplete.pos_por_ano['2031'];
                const declined = FichaExplorador.montar(document.createElement('div'),{municipio:incomplete}) === null;
                return {valid,immutable,declined};
            }''')
            assert edge == {'valid': True, 'immutable': True, 'declined': True}, edge

            # With the optional module unavailable, the standard chart remains the fallback.
            page.reload(wait_until='domcontentloaded')
            expect(page.locator('#fichaExplorador #difference')).to_contain_text('− R$')
            page.locator('[data-visual-ficha]').click()
            expect(page.locator('#gSerie')).to_be_visible()
            assert page.locator('html.ficha-preview-nova').count() == 0
            assert page.evaluate("Chart.getChart(document.querySelector('#gSerie')) != null")
            page.locator('#compModo [data-modo="rs"]').click()
            page.locator('#compModo [data-modo="pct"]').click()
            page.locator('[data-visual-ficha]').click()
            expect(page.locator('#fichaExplorador #difference')).to_contain_text('− R$')
            # Optional enhancement failure must leave a working standard page.
            context.route('**/ficha-explorador.js*', lambda r: r.abort())
            page.reload(wait_until='domcontentloaded')
            expect(page.locator('#gSerie')).to_be_visible()
            assert page.evaluate("Chart.getChart(document.querySelector('#gSerie')) != null")
            context.unroute('**/ficha-explorador.js*')
            # Existing caveats and unavailable rankings remain visible in the preview.
            page.goto(base + '/?m=1600105&visual=novo', wait_until='domcontentloaded')
            expect(page.locator('#fichaCorpo .aviso')).to_contain_text('Estimativa aproximada', timeout=20000)
            expect(page.locator('#cap-compara + .ficha-grid')).to_contain_text('indisponível para municípios com ressalva')
            # Large cities use compact billions without overflowing direct labels.
            page.goto(base + '/?m=3550308&visual=novo', wait_until='domcontentloaded')
            expect(page.locator('#fichaTitulo')).to_contain_text('São Paulo')
            expect(page.locator('#fichaExplorador #with-value')).to_contain_text('bi')
            assert page.evaluate('document.documentElement.scrollWidth') == width
            assert not errors, errors
            checks.append({'device': device, 'result': 'PASS', 'checks': ['timeline_keyboard_pointer', 'chart_lenses', 'source_csv', 'legacy_composition_controls', 'playback_lifecycle', 'municipality_search', 'loss_sign_and_scale', 'legacy_toggle', 'zero_and_missing_rows', 'immutable_source', 'module_failure_fallback', 'data_caveats', 'large_city_scale', 'no_overflow', 'no_uncaught_errors']})
            context.close()
        browser.close()
    server.shutdown()
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
