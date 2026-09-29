#!/usr/bin/env python3
"""
Validação paralela das 22 anomalias de ISS do Paraná contra a rubrica exata
de ISSQN no PIT/TCE-PR.

É uma versão operacionalmente mais rápida de validate-pr-iss-tce.py:
- agrupa observações por exercício;
- abre um RemoteZip por exercício;
- extrai os idpessoa dos municípios sinalizados;
- consulta em paralelo, entre exercícios, a página detalhada de dezembro;
- compara diretamente o ISS da DCA/SICONFI com a rubrica
  1.1.1.4.51.1.0... "Imposto sobre Serviços de Qualquer Natureza - ISSQN".

Não altera a base canônica.
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup
from remotezip import RemoteZip

HERE = Path(__file__).resolve().parent
OUT = HERE / "auditoria-pr-validacao"
ANOM = OUT / "anomalias-iss-pr-latest.csv"
UA = "Mozilla/5.0 auditoria-reforma-tributaria-sefaz-es/1.0"
TCE_ZIP = "https://pit.tce.pr.gov.br/Arquivos/{ano}_PIT_TodosArquivos.zip"
DETAIL = "https://pit.tce.pr.gov.br/Receitas/ReceitaDetalhes/PlanoOrcamentarioPadrao"
ISS_LABEL = re.compile(r"imposto\s+sobre\s+servi[cç]os\s+de\s+qualquer\s+natureza\s*-\s*issqn", re.I)


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
        if not rows:
            return
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def pit_code(codigo_ibge):
    return str(codigo_ibge).strip()[:6]


def br_money(token):
    s = str(token or "").strip()
    if not re.fullmatch(r"-?\d{1,3}(?:\.\d{3})*,\d{2}|-?\d+,\d{2}", s):
        return None
    return float(s.replace(".", "").replace(",", "."))


def entity_id_from_receita_zip(rz, ano, codigo_ibge):
    target = f"{ano}_{pit_code(codigo_ibge)}_Receita.zip"
    try:
        raw = rz.read(target)
    except Exception as exc:
        return None, target, f"zip_receita:{type(exc).__name__}:{exc}"
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as nz:
            ent_name = next((n for n in nz.namelist() if "ReceitasEntidade" in n), None)
            if not ent_name:
                return None, target, "ReceitasEntidade.xml ausente"
            root = ET.fromstring(nz.read(ent_name))
        entities = {}
        for el in root.iter():
            pid = el.attrib.get("idpessoa")
            nm = (el.attrib.get("nmEntidade") or "").strip()
            if pid and nm:
                entities[pid] = nm
        for pid, nm in entities.items():
            up = nm.upper()
            if up.startswith("MUNICÍPIO DE ") or up.startswith("MUNICIPIO DE "):
                return pid, target, "ok"
        return None, target, "entidade municipal não localizada"
    except Exception as exc:
        return None, target, f"parse_entidade:{type(exc).__name__}:{exc}"


def fetch_exact_iss(entity_id, ano, timeout=90):
    params = {
        "IdEntidade": entity_id,
        "NrAno": ano,
        "NrMes": 12,
        "tipo": "padrao",
        "tipoExibicao": "Imprimir",
    }
    url = DETAIL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return None, url, f"http:{type(exc).__name__}:{exc}", None

    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for tr in soup.find_all("tr"):
        cells = [" ".join(td.stripped_strings) for td in tr.find_all(["td", "th"])]
        joined = " ".join(cells)
        if not ISS_LABEL.search(joined):
            continue
        low = joined.lower()
        # rubrica agregada: exclui principal, multas, dívida etc.
        if any(x in low for x in (
            " - principal", " - multas", " - juros", " - dívida ativa",
            " - divida ativa", "adicional iss"
        )):
            continue
        vals = []
        for tok in re.findall(r"-?\d{1,3}(?:\.\d{3})*,\d{2}|-?\d+,\d{2}", joined):
            v = br_money(tok)
            if v is not None:
                vals.append(v)
        if vals:
            candidates.append((len(joined), vals[-1], joined))

    if not candidates:
        return None, url, "rubrica agregada ISSQN não localizada", None
    candidates.sort()
    _, value, row = candidates[0]
    return value, url, "ok", row


def classify(dca, tce):
    if dca is None or tce is None:
        return "sem_comparacao", None
    if tce == 0:
        if dca == 0:
            return "coerente_ate_5pct", 0.0
        return "divergencia_extrema_acima_100pct", math.inf
    delta = (dca / tce - 1) * 100
    ad = abs(delta)
    if ad <= 5:
        return "coerente_ate_5pct", delta
    if ad <= 20:
        return "revisar_5a20pct", delta
    if ad <= 100:
        return "divergencia_forte_20a100pct", delta
    return "divergencia_extrema_acima_100pct", delta


def process_year(ano, rows):
    url = TCE_ZIP.format(ano=ano)
    result = []
    try:
        with RemoteZip(url, headers={"User-Agent": UA}) as rz:
            enriched = []
            for r in rows:
                entity_id, archive, entity_status = entity_id_from_receita_zip(
                    rz, ano, r["codigo_ibge"]
                )
                enriched.append((r, entity_id, archive, entity_status))
    except Exception as exc:
        for r in rows:
            result.append({
                "codigo_ibge": r["codigo_ibge"],
                "municipio": r["municipio"],
                "ano": ano,
                "iss_dca": float(r["iss_dca"]),
                "mediana_outros_anos_dca": float(r["mediana_outros_anos"]),
                "razao_iss_mediana_dca": float(r["razao_valor_mediana"]),
                "iss_tce": None,
                "diferenca_dca_vs_tce_pct": None,
                "classificacao": "sem_comparacao",
                "id_entidade_tce": None,
                "arquivo_pit": None,
                "status": f"remotezip:{type(exc).__name__}:{exc}",
                "url_detalhe": None,
                "linha_tce": None,
            })
        return result

    for r, entity_id, archive, entity_status in enriched:
        dca = float(r["iss_dca"])
        if entity_id is None:
            tce, detail_url, status, line = None, None, entity_status, None
        else:
            tce, detail_url, status, line = fetch_exact_iss(entity_id, ano)
        cls, delta = classify(dca, tce)
        result.append({
            "codigo_ibge": r["codigo_ibge"],
            "municipio": r["municipio"],
            "ano": ano,
            "iss_dca": dca,
            "mediana_outros_anos_dca": float(r["mediana_outros_anos"]),
            "razao_iss_mediana_dca": float(r["razao_valor_mediana"]),
            "iss_tce": tce,
            "diferenca_dca_vs_tce_pct": delta,
            "classificacao": cls,
            "id_entidade_tce": entity_id,
            "arquivo_pit": archive,
            "status": status if entity_status == "ok" else f"{entity_status};{status}",
            "url_detalhe": detail_url,
            "linha_tce": line,
        })
    return result


def main():
    anom = read_csv(ANOM)
    by_year = defaultdict(list)
    for r in anom:
        by_year[int(r["ano"])].append(r)

    rows = []
    with ThreadPoolExecutor(max_workers=min(6, len(by_year))) as ex:
        futs = {ex.submit(process_year, ano, rs): ano for ano, rs in by_year.items()}
        for fut in as_completed(futs):
            ano = futs[fut]
            yr = fut.result()
            rows.extend(yr)
            print(f"{ano}: {len(yr)} casos concluídos")

    rows.sort(key=lambda r: (r["ano"], r["municipio"]))
    counts = defaultdict(int)
    for r in rows:
        counts[r["classificacao"]] += 1

    strong = [
        r for r in rows
        if r["classificacao"] in {
            "divergencia_forte_20a100pct",
            "divergencia_extrema_acima_100pct",
        }
    ]
    coherent = [r for r in rows if r["classificacao"] == "coerente_ate_5pct"]
    review = [r for r in rows if r["classificacao"] == "revisar_5a20pct"]

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "fonte": "PIT/TCE-PR, PlanoOrcamentarioPadrao, rubrica agregada ISSQN, dezembro",
        "criterio": {
            "coerente": "|DCA/TCE - 1| <= 5%",
            "revisar": ">5% e <=20%",
            "forte": ">20% e <=100%",
            "extrema": ">100%",
        },
        "n_sinalizados": len(rows),
        "classificacoes": dict(counts),
        "n_divergencia_forte_ou_extrema": len(strong),
        "n_coerentes_ate_5pct": len(coherent),
        "n_revisar_5a20pct": len(review),
        "divergencias_fortes_ou_extremas": strong,
        "coerentes_ate_5pct": coherent,
        "revisar_5a20pct": review,
        "nota": (
            "O teste temporal apenas seleciona observações para revisão. "
            "A classificação final desta rotina usa a comparação direta entre "
            "o ISS declarado na DCA/SICONFI e a rubrica agregada de ISSQN "
            "realizada no PIT/TCE-PR."
        ),
    }

    date = datetime.now(timezone.utc).date().isoformat()
    write_csv(OUT / f"validacao-iss-tce-pr-fast-{date}.csv", rows)
    write_csv(OUT / "validacao-iss-tce-pr-fast-latest.csv", rows)
    (OUT / f"resumo-validacao-iss-tce-pr-fast-{date}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "resumo-validacao-iss-tce-pr-fast-latest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
