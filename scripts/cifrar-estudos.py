#!/usr/bin/env python3
"""Prepara o acesso por cadastro aos estudos.

Para cada estudo (todos os HTML da pasta de originais, exceto index.html):
  - cifra o texto completo (AES-256-GCM, chave derivada da frase por PBKDF2-SHA256) em _cifrado/<estudo>.json;
  - grava em estudos/<estudo>.html a página pública (vitrine): título, descrição curta, aviso e formulário de cadastro.
O texto só é decifrado no servidor (api/estudo.js), que usa a frase da variável de ambiente ESTUDOS_SENHA da Vercel e entrega o estudo
a quem tem sessão válida (api/acesso/*). A frase nunca é enviada ao navegador.

Os originais em texto aberto NÃO ficam no repositório público: ficam no repositório privado.
Uso:   ESTUDOS_SENHA='frase longa e aleatória' python3 scripts/cifrar-estudos.py <pasta com os HTML originais>
       python3 scripts/cifrar-estudos.py --so-vitrines <pasta>   (refaz só as páginas públicas, sem recifrar nem precisar da frase)
A vitrine mostra o título, a descrição e um trecho curto de abertura (primeiro parágrafo do estudo, revisado) sob um véu escuro com o
formulário de cadastro. Só esse trecho é público; o restante do texto nunca vai ao navegador sem sessão válida.
Para trocar a frase: gere outra, atualize ESTUDOS_SENHA na Vercel e rode este script de novo antes do deploy.
Limites: protege apenas o que é publicado a partir daqui; histórico do Git, caches e cópias anteriores não são afetados;
os arquivos de data/ e materiais/ carregados ou linkados pelos estudos continuam públicos.
"""
import base64, html, json, os, re, sys
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

RAIZ = Path(__file__).resolve().parents[1]
ITER = 600_000
RESSALVA = ("Os estudos publicados neste site têm caráter técnico e analítico e não representam posicionamentos oficiais das "
            "instituições às quais o autor está vinculado. As estimativas apresentadas não constituem projeções oficiais. "
            "As fontes de informação, premissas e limitações metodológicas são identificadas em cada estudo.")
DESC = {  # estudos sem meta description: descrição curta e neutra
    "reforma-tributaria-coeficiente": "Cálculo do Coeficiente de Participação de Transição do Espírito Santo conforme a LC 227/2026.",
    "ibs-projecao-arrecadacao-es": "Projeção da receita de ICMS e IBS do Espírito Santo no primeiro quinquênio do IBS estadual (2029–2033).",
    "ibs-projecao-arrecadacao-br": "Projeção da receita de ICMS e IBS dos estados e do agregado municipal de cada UF no quinquênio 2029–2033.",
    "ibs-projecao-longo-prazo": "Extensão do Estudo 06 até o fim do cronograma constitucional de transição (2029–2077).",
    "reforma-tributaria-coeficiente-municipios": "Coeficiente de Participação de Transição de cada município, nas 27 UFs, a partir do DCA/Siconfi.",
    "seguro-receita-repasses": "Repasses do Seguro-Receita por ente, 2029–2033, conforme o art. 132 do ADCT e o art. 117 da LC 227/2026.",
}

PAGINA = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>{titulo} | Eduardo Reis Araújo</title>
<meta name="description" content="{desc_attr}">
<style>
:root{{--bg:#f7f6f2;--fg:#1c1c1c;--mut:#5b5b5b;--card:#fff;--bd:#d9d6cc;--ac:#8a6d1d}}
@media (prefers-color-scheme:dark){{:root{{--bg:#14161a;--fg:#ece9e1;--mut:#a7a39a;--card:#1c1f25;--bd:#33373f;--ac:#d4b25c}}}}
*{{box-sizing:border-box}}html,body{{height:100%}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
main{{max-width:680px;margin:0 auto;padding:1.6rem 1.1rem}}
.voltar{{font-size:.9rem;color:var(--mut);text-decoration:none}}
h1{{font-size:1.45rem;line-height:1.28;margin:1rem 0 .5rem}}
.desc{{color:var(--mut);margin:0 0 1rem;font-size:.95rem}}
.trecho{{font-family:Georgia,'Times New Roman',serif;font-size:1.08rem;line-height:1.75;margin:0;
  -webkit-mask-image:linear-gradient(#000 35%,transparent 95%);mask-image:linear-gradient(#000 35%,transparent 95%)}}
.veu{{position:fixed;inset:0;z-index:10;background:rgba(8,10,14,.58);
  display:flex;align-items:flex-end;justify-content:center;padding:1rem;overflow:auto}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:1rem 1.1rem .9rem;width:100%;max-width:520px;
  box-shadow:0 12px 40px rgba(0,0,0,.35);margin-top:auto}}
.tag{{display:inline-block;font:500 .68rem ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--ac);border:1px solid var(--ac);padding:.15rem .5rem;border-radius:4px}}
.card h2{{font-size:1.1rem;margin:.45rem 0 .2rem;line-height:1.3}}
.card p{{margin:.1rem 0 .7rem;font-size:.93rem;line-height:1.5}}
form{{display:flex;gap:.5rem;flex-wrap:wrap}}
input[type=email]{{flex:1 1 200px;padding:.7rem .75rem;font-size:1rem;border:1px solid var(--bd);border-radius:6px;background:var(--bg);color:var(--fg)}}
button{{padding:.7rem 1.1rem;font-size:1rem;border:0;border-radius:6px;background:var(--ac);color:#fff;cursor:pointer}}
button[disabled]{{opacity:.6;cursor:default}}
.oculto{{position:absolute;left:-9999px;height:0;width:0;overflow:hidden}}
#msg{{min-height:1.3em;margin:.7rem 0 0;font-size:.92rem}}#msg.erro{{color:#b3261e}}
.peq{{font-size:.78rem;color:var(--mut);margin:.5rem 0 0;line-height:1.45}}.peq a,.card a{{color:var(--ac)}}
.sair{{display:inline-block;margin-top:.4rem;font-size:.9rem}}
details{{margin-top:.5rem}}summary{{font-size:.82rem;color:var(--mut);cursor:pointer}}
</style>
</head>
<body>
<main id="vitrine">
<a class="voltar" href="/estudos/">&larr; Todos os estudos</a>
<h1 id="t">{titulo}</h1>
<p class="desc">{desc}</p>
{trecho_html}
</main>
<div class="veu" id="veu">
<div class="card" role="dialog" aria-modal="true" aria-labelledby="ct">
<span class="tag">Acesso por cadastro</span>
<h2 id="ct">Continue lendo</h2>
<p>Informe seu e-mail e receba um link de acesso pessoal. É gratuito, sem senha, e vale por 30 dias neste navegador.</p>
<form id="f" autocomplete="on">
<input id="e" type="email" name="email" placeholder="seu@email.com" aria-label="Seu e-mail" required>
<input class="oculto" type="text" name="site" tabindex="-1" autocomplete="off" aria-hidden="true">
<button id="b" type="submit">Receber link</button>
</form>
<p id="msg" role="status"></p>
<a class="sair" href="/estudos/">&larr; Voltar à lista de estudos</a>
<details><summary>Sobre o cadastro e este site</summary>
<p class="peq">Seu e-mail é usado apenas para liberar o acesso e registrar quais estudos foram lidos. Para pedir a exclusão ou esclarecimentos, entre em contato pela <a href="/#contato">seção de contato</a>.</p>
<p class="peq">{ressalva}</p>
</details>
<noscript><p>É necessário habilitar JavaScript para acessar o estudo.</p></noscript>
</div>
</div>
<script>
(function(){{
var SLUG={slug};
var m=document.getElementById('msg'),f=document.getElementById('f'),b=document.getElementById('b');
fetch('/api/estudo?slug='+encodeURIComponent(SLUG),{{credentials:'same-origin',cache:'no-store'}}).then(function(r){{
  if(r.status===200)return r.text().then(function(h){{document.open();document.write(h);document.close();}});
}}).catch(function(){{}});
f.addEventListener('submit',function(ev){{
  ev.preventDefault();m.className='';m.textContent='Enviando…';b.disabled=true;
  fetch('/api/acesso/solicitar',{{method:'POST',headers:{{'Content-Type':'application/json'}},credentials:'same-origin',
    body:JSON.stringify({{email:f.email.value,site:f.site.value,slug:SLUG}})}})
  .then(function(r){{return r.json().catch(function(){{return{{}}}}).then(function(j){{return{{s:r.status,j:j}}}});}})
  .then(function(x){{
    if(x.s===200){{f.style.display='none';m.textContent='Enviamos um link para '+f.email.value+'. Abra o e-mail e clique em "Abrir estudo". O link vale por 30 minutos. Confira também a caixa de spam.';}}
    else{{b.disabled=false;m.className='erro';m.textContent=x.s===400?'E-mail inválido. Confira e tente de novo.':x.s===429?'Muitas tentativas. Tente de novo em alguns minutos.':'O cadastro está temporariamente indisponível. Tente mais tarde ou entre em contato pela seção de contato do site.';}}
  }}).catch(function(){{b.disabled=false;m.className='erro';m.textContent='Sem conexão. Tente novamente.';}});
}});
}})();
</script>
</body>
</html>
"""

SEM_TRECHO = {"icms-diesel-importado"}   # primeira página sem parágrafo de abertura utilizável: fica só com a descrição

def _limpa(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()

def trecho(orig, slug):
    """Primeiro parágrafo de abertura do estudo, em texto simples, com no máximo ~420 caracteres, cortado em fim de frase."""
    if slug in SEM_TRECHO:
        return ""
    body = re.sub(r"<script.*?</script>|<style.*?</style>|<nav.*?</nav>|<header.*?</header>|<footer.*?</footer>", "", orig, flags=re.S | re.I)
    i = body.lower().find("<h1")
    body = body[i:] if i >= 0 else body
    cands = [_limpa(m.group(2)) for m in re.finditer(r'<(p|div)[^>]*class="[^"]*(?:intro|lead|lede|subtitle|resumo|abstract)[^"]*"[^>]*>(.*?)</\1>', body, re.S)]
    cands += [_limpa(x) for x in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S)]
    for c in cands:
        if len(c) < 110 or re.match(r"(?i)(atualiza|fonte|nota|dados:|\d+\.|figura|tabela|metodologia|aviso)", c) or "Os estudos publicados neste site" in c:
            continue
        c = re.sub(r"^Resumo\s+", "", c)
        if len(c) > 420:
            fins = [m.end() for m in re.finditer(r"(?<!\bart)(?<!\barts)(?<!\bn)(?<!§)\.\s", c[:430]) if m.end() > 150]
            c = c[:fins[-1]].strip() if fins else c[:420].rsplit(" ", 1)[0] + "…"
        return c
    return ""

def cifra(texto, senha):
    salt, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(senha.encode())).encrypt(iv, texto.encode(), None)
    b = lambda x: base64.b64encode(x).decode()
    return {"iter": ITER, "salt": b(salt), "iv": b(iv), "ct": b(ct)}

def main():
    so_vitrines = "--so-vitrines" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    senha = os.environ.get("ESTUDOS_SENHA", "")
    if not so_vitrines and len(senha) < 24:
        sys.exit("Defina ESTUDOS_SENHA com pelo menos 24 caracteres.")
    pasta = Path(args[0])
    (RAIZ / "_cifrado").mkdir(exist_ok=True)
    for arq in sorted(pasta.glob("*.html")):
        if arq.name == "index.html":
            continue
        slug = arq.stem
        orig = arq.read_text(encoding="utf-8")
        if "<!-- pagina-restrita -->" in orig or 'id="vitrine"' in orig:
            sys.exit(f"{arq.name} já é página cifrada; aponte para os originais.")
        titulo = html.unescape(re.search(r"<title>(.*?)</title>", orig, re.S).group(1).strip())
        titulo = re.sub(r"\s*\|\s*Eduardo Reis Ara[úu]jo\s*$", "", titulo)
        m = re.search(r'<meta name="description" content="([^"]*)"', orig)
        desc = DESC.get(slug) or (html.unescape(m.group(1)) if m else "")
        if not so_vitrines:
            (RAIZ / "_cifrado" / f"{slug}.json").write_text(json.dumps(cifra(orig, senha), separators=(",", ":")), encoding="utf-8")
        (RAIZ / "estudos" / f"{slug}.html").write_text(PAGINA.format(
            titulo=html.escape(titulo), desc=html.escape(desc), desc_attr=html.escape(desc, quote=True), ressalva=RESSALVA, slug=json.dumps(slug),
            trecho_html=("<p class=\"trecho\">" + html.escape(trecho(orig, slug)) + "</p>") if trecho(orig, slug) else ""), encoding="utf-8")
        print("preparado:", slug)

if __name__ == "__main__":
    main()
