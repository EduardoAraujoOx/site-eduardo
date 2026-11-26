#!/usr/bin/env python3
"""Insere a ressalva editorial padronizada nas páginas dos estudos e na página principal.

Idempotente (marcador <!-- ressalva-editorial -->). A frase de metodologia própria só entra nos
estudos listados em INDEPENDENTES: aqueles em que a auditoria confirmou uso exclusivo de fontes públicas.
Uso: python3 scripts/aplicar-ressalva-editorial.py
"""
import pathlib, re

RAIZ = pathlib.Path(__file__).resolve().parents[1]
GERAL = ("Os estudos publicados neste site têm caráter técnico e analítico e não representam posicionamentos "
         "oficiais das instituições às quais o autor está vinculado. As estimativas apresentadas não constituem "
         "projeções oficiais. As fontes de informação, premissas e limitações metodológicas são identificadas em cada estudo.")
PROPRIA = ("As estimativas foram produzidas mediante metodologia própria, fundamentada na legislação aplicável "
           "e em bases públicas de informação.")
INDEPENDENTES = {"fndr-es-2029-2033.html", "icms-iss-participacao-vs-populacao.html", "icms-iss-ibs-atual-potencial.html"}
ESTILO = "max-width:860px;margin:2rem auto 1rem;padding:0 1rem;font-size:.8rem;line-height:1.55;opacity:.75;text-align:center;color:inherit"
MARCA = "<!-- ressalva-editorial -->"

def bloco(propria):
    t = GERAL + ((" " + PROPRIA) if propria else "")
    return f'{MARCA}\n<aside class="ressalva-editorial" style="{ESTILO}">{t}</aside>\n'

def aplicar(p, propria=False):
    s = p.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in s else "\n"
    if MARCA in s:
        return "já tinha"
    for pat in (r'(\s*)<footer class="footer"', r'(\s*)<script src="/js/search.js"', r'(\s*)</body>'):
        m = re.search(pat, s)
        if m:
            b = bloco(propria).rstrip("\n").replace("\n", nl)
            s = s[:m.start()] + nl + b + s[m.start():]
            p.write_bytes(s.encode("utf-8"))
            return "ok"
    return "SEM ÂNCORA"

if __name__ == "__main__":
    for p in sorted((RAIZ / "estudos").glob("*.html")):
        print(p.relative_to(RAIZ), aplicar(p, p.name in INDEPENDENTES))
    print("index.html", aplicar(RAIZ / "index.html"))
