#!/usr/bin/env python3
"""Restringe de fato o acesso a estudos selecionados: substitui a página pública por uma página de acesso que
guarda o conteúdo cifrado (AES-256-GCM, chave derivada da frase de acesso por PBKDF2-SHA256, 600 mil iterações)
e o decifra no navegador. Sem a frase, o HTML publicado não contém o texto do estudo.

Os originais em texto aberto NÃO ficam no repositório público: ficam no repositório privado.
Uso:
  ESTUDOS_SENHA='frase longa e aleatória' python3 scripts/cifrar-estudos.py <pasta com os HTML originais>
Limites: protege apenas o que é publicado a partir daqui; o histórico do Git, caches e cópias anteriores não são afetados.
Os dados em data/*.json carregados pelas páginas continuam públicos (não cifrados).
"""
import base64, json, os, re, sys, html
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

RAIZ = Path(__file__).resolve().parents[1]
RESTRITOS = ["reforma-tributaria-coeficiente.html", "ibs-projecao-arrecadacao-es.html", "ibs-projecao-arrecadacao-br.html",
             "ibs-projecao-longo-prazo.html", "reforma-tributaria-coeficiente-municipios.html", "seguro-receita-repasses.html"]
ITER = 600_000
RESSALVA = ("Os estudos publicados neste site têm caráter técnico e analítico e não representam posicionamentos oficiais das "
            "instituições às quais o autor está vinculado. As estimativas apresentadas não constituem projeções oficiais. "
            "As fontes de informação, premissas e limitações metodológicas são identificadas em cada estudo.")

PAGINA = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- pagina-restrita -->
<meta name="robots" content="noindex, nofollow">
<title>{titulo}</title>
<style>
:root{{--bg:#f7f6f2;--fg:#1c1c1c;--mut:#5b5b5b;--card:#fff;--bd:#d9d6cc;--ac:#8a6d1d}}
@media (prefers-color-scheme:dark){{:root{{--bg:#14161a;--fg:#ece9e1;--mut:#a7a39a;--card:#1c1f25;--bd:#33373f;--ac:#d4b25c}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
main{{max-width:640px;margin:0 auto;padding:3rem 1rem}}
.voltar{{font-size:.9rem;color:var(--mut);text-decoration:none}}
h1{{font-size:1.35rem;line-height:1.3;margin:1.2rem 0 .4rem}}
.tag{{display:inline-block;font:500 .7rem ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--ac);border:1px solid var(--ac);padding:.2rem .55rem;border-radius:4px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:1.25rem;margin-top:1.5rem}}
.card p{{margin:.2rem 0 1rem}}
form{{display:flex;gap:.5rem;flex-wrap:wrap}}
input{{flex:1 1 220px;padding:.65rem .75rem;font-size:1rem;border:1px solid var(--bd);border-radius:6px;background:var(--bg);color:var(--fg)}}
button{{padding:.65rem 1.1rem;font-size:1rem;border:0;border-radius:6px;background:var(--ac);color:#fff;cursor:pointer}}
#erro{{color:#b3261e;min-height:1.4em;margin:.6rem 0 0;font-size:.9rem}}
.nota{{font-size:.8rem;color:var(--mut);margin-top:2rem;opacity:.9}}
a{{color:var(--ac)}}
</style>
</head>
<body>
<main>
<a class="voltar" href="/estudos/">&larr; Todos os estudos</a>
<h1>{titulo}</h1>
<span class="tag">Acesso restrito</span>
<div class="card">
<p>Este estudo integra uma linha de pesquisa em andamento do autor sobre a reforma tributária e está, por ora, com acesso restrito. Para solicitar acesso ou informações sobre a metodologia, entre em contato com o autor pela <a href="/#contato">seção de contato</a> da página inicial.</p>
<form id="f" autocomplete="off"><input id="s" type="password" placeholder="Frase de acesso" aria-label="Frase de acesso" required><button type="submit">Abrir</button></form>
<p id="erro" role="alert"></p>
</div>
<p class="nota">{ressalva}</p>
</main>
<script>
(function(){{
var P={payload};
function b64(x){{var s=atob(x),a=new Uint8Array(s.length);for(var i=0;i<s.length;i++)a[i]=s.charCodeAt(i);return a;}}
async function abrir(pw){{
  var enc=new TextEncoder();
  var km=await crypto.subtle.importKey('raw',enc.encode(pw),'PBKDF2',false,['deriveKey']);
  var key=await crypto.subtle.deriveKey({{name:'PBKDF2',salt:b64(P.salt),iterations:P.iter,hash:'SHA-256'}},km,{{name:'AES-GCM',length:256}},false,['decrypt']);
  var pt=await crypto.subtle.decrypt({{name:'AES-GCM',iv:b64(P.iv)}},key,b64(P.ct));
  var h=new TextDecoder().decode(pt);
  try{{sessionStorage.setItem('estudos_acesso',pw);}}catch(e){{}}
  document.open();document.write(h);document.close();
}}
function tentar(pw,silencioso){{
  var e=document.getElementById('erro');if(!silencioso)e.textContent='Verificando…';
  abrir(pw).catch(function(){{
    if(!silencioso)e.textContent='Frase incorreta.';
    else try{{sessionStorage.removeItem('estudos_acesso');}}catch(x){{}}
  }});
}}
document.getElementById('f').addEventListener('submit',function(ev){{ev.preventDefault();tentar(document.getElementById('s').value,false);}});
try{{var g=sessionStorage.getItem('estudos_acesso');if(g)tentar(g,true);}}catch(e){{}}
}})();
</script>
</body>
</html>
"""

def cifra(texto, senha):
    salt, iv = os.urandom(16), os.urandom(12)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER)
    ct = AESGCM(kdf.derive(senha.encode("utf-8"))).encrypt(iv, texto.encode("utf-8"), None)
    b = lambda x: base64.b64encode(x).decode()
    return {"iter": ITER, "salt": b(salt), "iv": b(iv), "ct": b(ct)}

def main():
    senha = os.environ.get("ESTUDOS_SENHA", "")
    if len(senha) < 16:
        sys.exit("Defina ESTUDOS_SENHA com pelo menos 16 caracteres.")
    pasta = Path(sys.argv[1])
    for nome in RESTRITOS:
        orig = (pasta / nome).read_text(encoding="utf-8")
        if "<!-- pagina-restrita -->" in orig:
            sys.exit(f"{nome} já é página cifrada; aponte para os originais.")
        titulo = html.unescape(re.search(r"<title>(.*?)</title>", orig, re.S).group(1).strip())
        pag = PAGINA.format(titulo=html.escape(titulo), ressalva=RESSALVA, payload=json.dumps(cifra(orig, senha)))
        (RAIZ / "estudos" / nome).write_text(pag, encoding="utf-8")
        print("cifrado:", nome)

if __name__ == "__main__":
    main()
