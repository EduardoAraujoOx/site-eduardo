#!/usr/bin/env python3
"""
Coletor das publicações oficiais do Comitê Gestor do IBS (CGIBS).

O site https://www.cgibs.gov.br organiza os atos em seções (Resoluções,
Portarias, Atos Conjuntos...), e cada ato é um painel com o título, o link do
PDF e a data de publicação no site. Esta rotina lê as seções, extrai esses
campos e grava data/cgibs-publicacoes.json, preservando o que já foi coletado:
um ato que sumiu do site continua no arquivo, marcado como "fora do ar".

O texto explicativo ("o que é" e "por que importa ao município") não é gerado
aqui. Ele fica em data/cgibs-editorial.json, escrito e revisado pelo autor, e
só é exibido no portal quando "revisado" for verdadeiro. Esta rotina apenas
informa quais atos novos ainda não têm ficha editorial.

Uso:
  python3 collect-cgibs.py            # coleta e grava
  python3 collect-cgibs.py --dry-run  # coleta e só mostra o resumo
"""

import hashlib
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
SAIDA = HERE / "cgibs-publicacoes.json"
EDITORIAL = HERE / "cgibs-editorial.json"
BASE = "https://www.cgibs.gov.br"

SECOES = {
    "resolucoes": "Resolução",
    "regulamentos": "Regulamento",
    "portarias": "Portaria",
    "atos-conjuntos": "Ato Conjunto",
    "atos-tecnicos-conjuntos": "Ato Técnico Conjunto",
    "relatorios": "Relatório",
    "editais-de-chamamento-publico": "Edital de Chamamento Público",
}


def baixa(caminho):
    req = urllib.request.Request(
        BASE + "/" + caminho, headers={"User-Agent": "municipiosnareforma.com.br coletor (contato: fale@municipiosnareforma.com.br)"}
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", errors="ignore")


def texto(trecho):
    t = re.sub(r"<[^>]+>", " ", trecho)
    return " ".join(html.unescape(t).split())


def data_do_caminho(pdf):
    """Os uploads seguem /upload/arquivos/AAAAMM/DDHHMMSS-nome.pdf."""
    m = re.search(r"/(\d{4})(\d{2})/(\d{2})\d{6}-", pdf)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def paineis(pagina):
    """Cada ato é um bloco 'panel-group accordion'."""
    partes = re.split(r'<div id="accordion-\d+" class="panel-group accordion">', pagina)
    return partes[1:]


def limpa_rotulo(r):
    """Tira o sufixo '(.pdf 455,57 KBytes)' e a codificação de URL do nome do arquivo."""
    r = re.sub(r"\s*\(\.pdf[^)]*\)\s*$", "", r, flags=re.I)
    return " ".join(urllib.parse.unquote(r).replace("_", " ").split())


TIPOS_PELO_TITULO = [
    (r"portaria conjunta", "Portaria Conjunta"),
    (r"ato t[ée]cnico conjunto", "Ato Técnico Conjunto"),
    (r"ato conjunto", "Ato Conjunto"),
    (r"edital", "Edital de Chamamento Público"),
    (r"resolu", "Resolução"),
    (r"portaria", "Portaria"),
]


def tipo_do_titulo(titulo, padrao):
    for rx, nome in TIPOS_PELO_TITULO:
        if re.search(rx, titulo, flags=re.I):
            return nome
    return padrao


def le_secao(slug, tipo):
    achados = []
    for bloco in paineis(baixa(slug)):
        pdfs = re.findall(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', bloco, flags=re.S | re.I)
        if not pdfs:
            continue
        mt = re.search(r'<(?:h\d|p)[^>]*class="panel-title"[^>]*>(.*?)</(?:h\d|p)>', bloco, flags=re.S)
        titulo_painel = texto(mt.group(1)) if mt else ""
        md = re.search(r"em\s+(\d{2})/(\d{2})/(\d{4})", texto(bloco))
        publicado = f"{md.group(3)}-{md.group(2)}-{md.group(1)}" if md else None
        for href, rotulo in pdfs:
            rotulo = limpa_rotulo(texto(rotulo))
            url = href if href.startswith("http") else BASE + href
            titulo = titulo_painel or rotulo
            achados.append(
                {
                    "id": hashlib.sha1(href.encode()).hexdigest()[:10],
                    "tipo": tipo_do_titulo(titulo + " " + rotulo, tipo),
                    "secao": slug,
                    "titulo": titulo,
                    "rotulo_arquivo": rotulo,
                    "revogado": bool(re.search(r"revogad", titulo, flags=re.I)),
                    "publicado_em": publicado or data_do_caminho(href),
                    "pdf_url": url,
                }
            )
    return achados


def main():
    dry = "--dry-run" in sys.argv
    anterior = {}
    if SAIDA.exists():
        for it in json.loads(SAIDA.read_text(encoding="utf-8"))["itens"]:
            anterior[it["id"]] = it

    hoje = date.today().isoformat()
    atuais, falhas = {}, []
    for slug, tipo in SECOES.items():
        try:
            for it in le_secao(slug, tipo):
                # o mesmo PDF pode aparecer em duas seções (ex.: Resolução nº 6 e Regulamentos)
                if it["id"] not in atuais or len(it["titulo"]) > len(atuais[it["id"]]["titulo"]):
                    atuais[it["id"]] = it
        except Exception as e:  # uma seção fora do ar não pode apagar as demais
            falhas.append(f"{slug}: {e}")

    itens = []
    for id_, it in atuais.items():
        velho = anterior.get(id_, {})
        it["visto_primeira_vez"] = velho.get("visto_primeira_vez", hoje)
        it["fora_do_ar"] = False
        itens.append(it)
    for id_, velho in anterior.items():
        if id_ not in atuais and not any(f.startswith(velho["secao"]) for f in falhas):
            velho["fora_do_ar"] = True
            itens.append(velho)
        elif id_ not in atuais:
            itens.append(velho)  # seção falhou: mantém como estava

    itens.sort(key=lambda x: (x["publicado_em"] or "", x["titulo"]), reverse=True)
    novos = [i for i in itens if i["id"] not in anterior]

    editorial = json.loads(EDITORIAL.read_text(encoding="utf-8")).get("fichas", {}) if EDITORIAL.exists() else {}
    sem_ficha = [i for i in itens if i["id"] not in editorial and not i["fora_do_ar"]]

    saida = {
        "fonte": BASE,
        "coletado_em": hoje,
        "secoes_consultadas": list(SECOES),
        "falhas": falhas,
        "total": len(itens),
        "itens": itens,
    }
    print(f"{len(itens)} atos ({len(novos)} novos desde a última coleta); {len(sem_ficha)} sem ficha editorial")
    for f in falhas:
        print("FALHA", f)
    for i in novos[:30]:
        print("  novo:", i["publicado_em"], i["tipo"], "-", i["titulo"][:90])
    if not dry:
        # só regrava quando a lista mudou: a data da coleta sozinha não justifica novo commit
        antigo = json.loads(SAIDA.read_text(encoding="utf-8")) if SAIDA.exists() else {}
        if antigo.get("itens") == itens and antigo.get("falhas") == falhas:
            print("sem mudanças na lista; arquivo mantido")
        else:
            SAIDA.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
            print("gravado", SAIDA)


if __name__ == "__main__":
    main()
