#!/usr/bin/env python3
"""
Validação dirigida de anomalias de ISS no PIT/TCE-PR.

Consulta a página "Plano Orçamentário Padrão" do PIT para o mês 12 do ano
alvo e extrai linhas relacionadas ao ISS. A rotina é diagnóstica: não altera
a base canônica.

Os IDs abaixo foram confirmados em páginas públicas do próprio PIT:
- Guaraqueçaba: 12311
- Itaipulândia: 12331
- Terra Boa: 12550
- Santo Antônio do Paraíso: 12512

Uso:
  python3 data/validate-iss-pit.py
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
OUT = HERE / "auditoria-pr-validacao"
USER_AGENT = "Mozilla/5.0 auditoria-reforma-tributaria-sefaz-es/1.0"

CASOS = [
    {"municipio": "Guaraqueçaba", "id_entidade": 12311, "ano": 2025, "iss_dca": 23811721.32},
    {"municipio": "Itaipulândia", "id_entidade": 12331, "ano": 2022, "iss_dca": 17026553.60},
    {"municipio": "Terra Boa", "id_entidade": 12550, "ano": 2021, "iss_dca": 42021.54},
    {"municipio": "Santo Antônio do Paraíso", "id_entidade": 12512, "ano": 2021, "iss_dca": 20107.40},
    {"municipio": "Santo Antônio do Paraíso", "id_entidade": 12512, "ano": 2024, "iss_dca": 455033.52},
    {"municipio": "Santo Antônio do Paraíso", "id_entidade": 12512, "ano": 2025, "iss_dca": 330808.78},
]


def fetch_text(url, retries=4, timeout=90):
    errors = []
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                try:
                    return raw.decode("utf-8")
                except UnicodeDecodeError:
                    return raw.decode("cp1252", errors="replace")
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            if attempt < retries:
                time.sleep(2 ** (attempt - 1))
    raise RuntimeError(" | ".join(errors))


def brnum(s):
    if s is None:
        return None
    s = str(s).strip()
    if not s or s in {"-", "—"}:
        return None
    s = re.sub(r"[^0-9,.\-]", "", s)
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def norm(s):
    s = (s or "").lower()
    repl = {
        "ç":"c","ã":"a","á":"a","â":"a","à":"a","é":"e","ê":"e",
        "í":"i","ó":"o","ô":"o","õ":"o","ú":"u",
    }
    for a,b in repl.items():
        s=s.replace(a,b)
    return re.sub(r"\s+"," ",s).strip()


def is_iss_label(text):
    n = norm(text)
    return (
        "imposto sobre servicos de qualquer natureza" in n
        or "imposto sobre servico de qualquer natureza" in n
        or "issqn" in n
    )


def extract_rows(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td","th"])]
        if not cells:
            continue
        joined = " | ".join(cells)
        if not is_iss_label(joined):
            continue
        rows.append(cells)
    return rows


def infer_amount(cells):
    # Nas tabelas do PIT os dois últimos campos numéricos são, em geral,
    # previsão atualizada e arrecadação acumulada. Escolhemos o último valor
    # monetário parseável, que corresponde à arrecadação.
    vals = []
    for c in cells:
        v = brnum(c)
        if v is not None:
            vals.append(v)
    return vals[-1] if vals else None


def specificity_score(cells):
    text = norm(" | ".join(cells))
    score = 0
    if "principal" in text:
        score += 4
    if "divida ativa" in text:
        score -= 3
    if "multas" in text or "juros" in text:
        score -= 2
    # Preferência por linha cujo código começa com a natureza principal do ISS
    # na classificação vigente (quando exposto no HTML).
    code = cells[0] if cells else ""
    if re.search(r"1[.\s]*1[.\s]*1[.\s]*4[.\s]*51", code):
        score += 3
    return score


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    resultados = []
    for caso in CASOS:
        params = urllib.parse.urlencode({
            "IdEntidade": caso["id_entidade"],
            "NrAno": caso["ano"],
            "NrMes": 12,
            "tipo": "padrao",
            "tipoExibicao": "Imprimir",
        })
        url = "https://pit.tce.pr.gov.br/Receitas/ReceitaDetalhes/PlanoOrcamentarioPadrao?" + params
        print(f"{caso['municipio']} {caso['ano']}...")
        try:
            html = fetch_text(url)
            rows = extract_rows(html)
            candidates = []
            for cells in rows:
                candidates.append({
                    "cells": cells,
                    "amount": infer_amount(cells),
                    "score": specificity_score(cells),
                })
            candidates.sort(key=lambda x: (x["score"], len(x["cells"])), reverse=True)
            best = candidates[0] if candidates else None
            pit = best["amount"] if best else None
            dca = caso["iss_dca"]
            resultados.append({
                **caso,
                "url": url,
                "status": "ok" if best else "iss_nao_localizado",
                "iss_pit_estimado": pit,
                "diferenca_reais": (dca - pit) if pit is not None else None,
                "diferenca_pct_pit": ((dca / pit - 1) * 100) if pit not in (None,0) else None,
                "linha_escolhida": best,
                "todas_linhas_iss": candidates,
            })
        except Exception as exc:
            resultados.append({
                **caso,
                "url": url,
                "status": "erro",
                "erro": str(exc),
            })
        time.sleep(0.5)

    out = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "fonte": "PIT/TCE-PR - Plano Orçamentário Padrão, mês 12",
        "nota": (
            "Validação independente da DCA/SICONFI. O valor PIT é extraído da "
            "linha de ISS mais específica encontrada; conferir manualmente a "
            "linha escolhida antes de qualquer substituição canônica."
        ),
        "casos": resultados,
    }
    p = OUT / "validacao-iss-pit-dirigida.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
