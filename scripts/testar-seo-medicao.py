#!/usr/bin/env python3
"""Verifica SEO e GA4 sem acessar o site real nem enviar estatísticas."""
import argparse
import json
import shutil
from contextlib import contextmanager
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORTAL = ROOT / 'municipios-na-reforma'
PRODUCAO = 'municipiosnareforma.com.br'
ID_TESTE = 'G-SEO000001'
CHAVE = 'mnr-medicao-v1'
ASSETS = {
    'chart.umd.min.js': 'https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js',
    'd3.min.js': 'https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js',
}


class HTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = []
        self.em_h1 = False
        self.em_json = False
        self.json_text = ''
        self.schemas = []
        self.metas = {}
        self.canonica = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1':
            self.em_h1 = True
            self.h1.append('')
        if tag == 'meta':
            self.metas[attrs.get('name', attrs.get('property'))] = attrs.get('content')
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonica = attrs['href']
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.em_json = True
            self.json_text = ''

    def handle_data(self, text):
        if self.em_h1:
            self.h1[-1] += text
        if self.em_json:
            self.json_text += text

    def handle_endtag(self, tag):
        if tag == 'h1':
            self.em_h1 = False
        if tag == 'script' and self.em_json:
            self.schemas.append(json.loads(self.json_text))
            self.em_json = False


def verificar_seo():
    html = HTML()
    html.feed((PORTAL / 'index.html').read_text())
    assert html.h1 == ['Municípios na Reforma'], html.h1
    assert html.canonica == f'https://{PRODUCAO}/'
    assert html.metas['robots'] == 'index, follow'
    assert html.metas['og:site_name'] == 'Municípios na Reforma'
    site = next(schema for schema in html.schemas if schema['@type'] == 'WebSite')
    assert site['name'] == html.h1[0] and site['url'] == html.canonica
    assert (PORTAL / 'images/logo-vertex-advisory.png').is_file()
    robots = RobotFileParser()
    robots.parse((PORTAL / 'robots.txt').read_text().splitlines())
    for caminho in ['/', '/app.js', '/medicao.js', '/data/painel-municipios/index.json', '/data/malha-municipios.json']:
        assert robots.can_fetch('Googlebot', f'https://{PRODUCAO}{caminho}'), caminho
    sitemap = ElementTree.parse(PORTAL / 'sitemap.xml')
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    assert [loc.text for loc in sitemap.findall('.//s:loc', ns)] == [html.canonica]
    headers = json.loads((PORTAL / 'vercel.json').read_text())['headers']
    dados = next(regra for regra in headers if regra['source'] == '/data/(.*)')
    assert {'key': 'X-Robots-Tag', 'value': 'noindex'} in dados['headers']
    assert not any(h['key'].lower() == 'x-robots-tag' for regra in headers if regra is not dados for h in regra['headers'])
    print('PASS: HTML indexável, identidade, schema, sitemap e recursos de renderização')


def fila(page):
    return page.evaluate('JSON.parse(JSON.stringify(Array.from(window.dataLayer || [], item => Array.from(item))))')


def eventos(page, nome):
    return [item[2] for item in fila(page) if item[:2] == ['event', nome]]


def busca(page):
    expect(page.locator('#busca')).to_be_enabled(timeout=20000)
    page.locator('#busca').fill('São Francisco do Conde')
    page.locator('#sugestoes [data-cod="2929206"]').click()
    expect(page.locator('#fichaTitulo')).to_contain_text('São Francisco do Conde', timeout=20000)
    page.wait_for_function("typeof Chart !== 'undefined' && !!Chart.getChart(document.getElementById('gSerie'))")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-dir', type=Path, default=ROOT / '.cache/seo-medicao')
    parser.add_argument('--screenshots-dir', type=Path, default=ROOT / 'artifacts/seo-medicao')
    args = parser.parse_args()
    verificar_seo()
    args.assets_dir.mkdir(parents=True, exist_ok=True)
    args.screenshots_dir.mkdir(parents=True, exist_ok=True)
    for arquivo, url in ASSETS.items():
        destino = args.assets_dir / arquivo
        if not destino.is_file():
            with urlopen(url, timeout=30) as response:
                destino.write_bytes(response.read())

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which('chromium'), headless=True, args=['--no-sandbox']
        )

        @contextmanager
        def cenario(identificador=None, host=PRODUCAO, width=1512, height=1100, inicial=None):
            context = browser.new_context(viewport={'width': width, 'height': height})
            requests_ga = []
            erros = []
            inesperadas = []

            def responder(route):
                url = urlsplit(route.request.url)
                if url.hostname == host:
                    if route.request.method != 'GET':
                        inesperadas.append(route.request.method + ' ' + url.path)
                        route.abort()
                    elif url.path.startswith('/api/'):
                        route.fulfill(json={'ativo': False} if url.path != '/api/geo' else {'uf': None})
                    else:
                        clean = unquote(url.path).lstrip('/') or 'index.html'
                        raiz = ROOT if clean.startswith('data/') else PORTAL
                        caminho = (raiz / clean).resolve()
                        assert caminho.is_relative_to(raiz), caminho
                        assert caminho.is_file(), caminho
                        if url.path == '/app.js' and identificador is not None:
                            codigo = caminho.read_text().replace("gaId: '',", f"gaId: '{identificador}',", 1)
                            route.fulfill(body=codigo, content_type='application/javascript')
                        else:
                            route.fulfill(path=str(caminho))
                elif url.hostname == 'cdn.jsdelivr.net':
                    arquivo = next((nome for nome, origem in ASSETS.items() if route.request.url == origem), None)
                    if arquivo:
                        route.fulfill(path=str(args.assets_dir / arquivo), content_type='application/javascript')
                    else:
                        inesperadas.append(route.request.url)
                        route.abort()
                elif url.hostname == 'www.googletagmanager.com':
                    requests_ga.append(route.request.url)
                    route.fulfill(body='', content_type='application/javascript')
                elif url.hostname in ['fonts.googleapis.com', 'fonts.gstatic.com']:
                    route.fulfill(body='', content_type='text/css')
                elif url.hostname == 'wa.me':
                    route.fulfill(body='WhatsApp simulado; nenhuma mensagem enviada.', content_type='text/plain')
                else:
                    inesperadas.append(route.request.url)
                    route.abort()

            context.route('**/*', responder)
            if inicial:
                context.add_init_script(inicial)
            page = context.new_page()
            page.on('pageerror', lambda erro: erros.append(str(erro)))
            try:
                yield page, requests_ga
                assert not erros, erros
                assert not inesperadas, inesperadas
            finally:
                context.set_offline(True)
                context.unroute_all(behavior='wait')
                context.close()

        # O código publicado continua sem ID: sem Google, sem banner e painel operante.
        for nome, width, height in [('desktop', 1512, 1100), ('celular', 390, 844)]:
            with cenario(width=width, height=height) as (page, ga):
                page.goto(f'https://{PRODUCAO}/', wait_until='domcontentloaded')
                expect(page.locator('#busca')).to_be_enabled(timeout=20000)
                expect(page.locator('#mapaSvg path').first).to_be_attached(timeout=20000)
                expect(page.locator('h1')).to_be_visible()
                expect(page.locator('.medicao-aviso')).to_have_count(0)
                expect(page.locator('#medicaoPreferencias')).to_be_hidden()
                assert not ga and not fila(page)
                assert page.evaluate('document.documentElement.scrollWidth') <= width
                page.screenshot(path=str(args.screenshots_dir / f'home-{nome}.png'), full_page=True)
                busca(page)
                assert page.evaluate('document.documentElement.scrollWidth') <= width
                page.screenshot(path=str(args.screenshots_dir / f'ficha-{nome}.png'), full_page=True)
                assert not ga
            print(f'PASS: busca, mapa e gráfico em {nome}, sem ID e sem coleta')

        with cenario(ID_TESTE, width=390, height=844) as (page, ga):
            page.goto(f'https://{PRODUCAO}/', wait_until='domcontentloaded')
            expect(page.locator('.medicao-aviso')).to_be_visible()
            page.evaluate("MnrMedicao.registrar('clique_contato', {canal:'whatsapp'})")
            assert not ga and not fila(page)
            page.screenshot(path=str(args.screenshots_dir / 'consentimento-celular.png'), full_page=True)
            page.get_by_role('button', name='Continuar sem medição').click()
            busca(page)
            assert not ga and not fila(page)
            page.reload(wait_until='domcontentloaded')
            expect(page.locator('.medicao-aviso')).to_have_count(0)
            assert not ga and not fila(page)
            assert json.loads(page.evaluate(f'localStorage.getItem("{CHAVE}")'))['escolha'] == 'denied'
        print('PASS: nenhum pedido/evento antes da autorização; recusa persistida sem impedir a consulta')

        with cenario(ID_TESTE) as (page, ga):
            page.goto(f'https://{PRODUCAO}/?email=pessoa%40exemplo.com&texto=privado#segredo', wait_until='domcontentloaded')
            page.get_by_role('button', name='Aceitar medição').click()
            expect(page.locator('script[src*="googletagmanager.com/gtag/js"]')).to_have_count(1)
            assert len(eventos(page, 'page_view')) == 1
            assert eventos(page, 'page_view')[0]['page_location'] == f'https://{PRODUCAO}/'
            busca(page)
            assert eventos(page, 'busca_municipio')[-1]['municipio_codigo'] == '2929206'
            assert eventos(page, 'busca_municipio')[-1]['uf'] == 'BA'
            page.evaluate("""() => {
                MnrMedicao.registrar('clique_contato', {
                    canal:'whatsapp', municipio_codigo:'2929206', local:'flutuante',
                    nome:'Pessoa privada', email:'pessoa@exemplo.com', telefone:'27999999999',
                    mensagem:'texto privado', interesse:'dado privado', municipio:'texto livre',
                    page_location:'https://exemplo.com/?segredo=1'
                });
                MnrMedicao.registrar('evento_desconhecido', {email:'pessoa@exemplo.com'});
            }""")
            evento = eventos(page, 'clique_contato')[-1]
            assert set(evento) == {'canal', 'municipio_codigo', 'local', 'page_location'}, evento
            assert evento['page_location'] == f'https://{PRODUCAO}/?m=2929206'
            assert not eventos(page, 'evento_desconhecido')
            # Exercitar o formulário de verdade, com WhatsApp simulado e nenhum envio externo.
            page.locator('.site-foot a[data-ir="privacidade"]').click()
            page.locator('#medicaoPreferencias').click()
            page.get_by_role('button', name='Aceitar medição').click()
            assert len(eventos(page, 'page_view')) == 1
            expect(page.locator('script[src*="googletagmanager.com/gtag/js"]')).to_have_count(1)
            page.locator('[data-view="vertex"]').click()
            page.locator('#btnServico').click()
            page.locator('#ctNome').fill('Pessoa Teste')
            page.locator('#ctEmail').fill('teste@example.com')
            page.locator('#ctMunicipio').fill('Município escrito livremente')
            page.locator('#ctMsg').fill('Mensagem privada de teste')
            page.locator('#formContato [name="aceite_privacidade"]').check()
            with page.expect_popup() as popup:
                page.locator('#formContato button[type="submit"]').click()
            popup.value.close()
            assert eventos(page, 'contato_enviado')[-1]['canal'] == 'whatsapp'
            comandos = json.dumps(fila(page))
            for privado in ['Pessoa Teste', 'teste@example.com', 'escrito livremente', 'Mensagem privada', 'texto privado', 'pessoa@exemplo.com']:
                assert privado not in comandos, privado
            page.evaluate("document.cookie = '_ga=teste; Path=/'; document.cookie = '_ga_SEO000001=teste; Path=/; Domain=municipiosnareforma.com.br'")
            page.locator('.site-foot a[data-ir="privacidade"]').click()
            page.locator('#medicaoPreferencias').click()
            with page.expect_navigation(wait_until='domcontentloaded'):
                page.get_by_role('button', name='Continuar sem medição').click()
            expect(page.locator('.medicao-aviso')).to_have_count(0)
            assert not fila(page)
            assert not any(cookie['name'].startswith('_ga') for cookie in page.context.cookies())
            assert json.loads(page.evaluate(f'localStorage.getItem("{CHAVE}")'))['escolha'] == 'denied'
            assert len(ga) == 1, ga
        print('PASS: aceite, eventos reais da busca/formulário, filtros de privacidade e revogação')

        with cenario(ID_TESTE, inicial=f"localStorage.setItem('{CHAVE}', JSON.stringify({{escolha:'granted', em:Date.now()}}))") as (page, ga):
            page.goto(f'https://{PRODUCAO}/?m=2929206&segredo=privado', wait_until='domcontentloaded')
            expect(page.locator('.medicao-aviso')).to_have_count(0)
            assert eventos(page, 'page_view')[0]['page_location'] == f'https://{PRODUCAO}/?m=2929206'
            assert len(ga) == 1
        print('PASS: autorização persistida e URL municipal sem parâmetros livres')

        vencida = f"localStorage.setItem('{CHAVE}', JSON.stringify({{escolha:'granted', em:Date.now()-181*86400000}}))"
        indisponivel = "Object.defineProperty(window, 'localStorage', {get() {throw new Error('storage bloqueado')}})"
        for inicial in [vencida, indisponivel]:
            with cenario(ID_TESTE, inicial=inicial) as (page, ga):
                page.goto(f'https://{PRODUCAO}/', wait_until='domcontentloaded')
                expect(page.locator('.medicao-aviso')).to_be_visible()
                assert not ga
                page.get_by_role('button', name='Continuar sem medição').click()
                busca(page)
                assert not ga
        print('PASS: consentimento vencido e armazenamento indisponível')

        for host, identificador in [('municipiosnareforma-preview.vercel.app', ID_TESTE), (PRODUCAO, 'id-invalido')]:
            with cenario(identificador, host=host) as (page, ga):
                page.goto(f'https://{host}/', wait_until='domcontentloaded')
                expect(page.locator('#busca')).to_be_enabled(timeout=20000)
                expect(page.locator('.medicao-aviso')).to_have_count(0)
                assert not ga and not fila(page)
        print('PASS: ID inválido e prévias da Vercel não medem')
        browser.close()



if __name__ == '__main__':
    main()
