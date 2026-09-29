#!/usr/bin/env python3
"""
Validação conservadora das anomalias de ISS do Paraná usando o PIT/TCE-PR.

Para cada observação de ISS previamente sinalizada no DCA/SICONFI:
1. abre remotamente, via HTTP Range, o ZIP anual consolidado do PIT;
2. extrai apenas o ZIP de Receita do município;
3. lê ReceitasConsolidado.xml;
4. recupera o maior acumulado anual do item "Impostos" (idSumarioItem 5040);
5. compara o ISS declarado no DCA com o total de impostos do PIT.

Teste conservador:
ISS_DCA não pode exceder a receita TOTAL de impostos do mesmo município/ano
se as duas fontes cobrem o mesmo orçamento fiscal consolidado. Portanto,
ISS_DCA > Impostos_TCE por margem material é evidência forte de
inconsistência do registro DCA. O inverso NÃO valida o ISS: um ISS pequeno
pode continuar errado e requer uma rubrica específica ou outra fonte.

A rotina é diagnóstica e NÃO altera a base canônica.
"""
from __future__ import annotations

import csv
import io
import json
import math
import time
import zipfile
import xml.etree.ElementTree as ET
import urllib.parse
import urllib.request
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from remotezip import RemoteZip
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
AUDIT = HERE / "auditoria-pr-validacao"
ANOM = AUDIT / "anomalias-iss-pr-latest.csv"
UA = "Mozilla/5.0 auditoria-reforma-tributaria-sefaz-es/1.0"
TCE_URL = "https://pit.tce.pr.gov.br/Arquivos/{ano}_PIT_TodosArquivos.zip"
ID_IMPOSTOS = "5040"


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    if not rows:
        Path(path).write_text("", encoding="utf-8")
        return
    with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def dump_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def pit_code(codigo_ibge: str) -> str:
    # O PIT usa os seis primeiros dígitos do código IBGE; o sétimo é dígito
    # verificador e não aparece no nome do arquivo.
    return str(codigo_ibge).strip()[:6]


def extract_total_impostos(rz, ano, codigo_ibge):
    target = f"{ano}_{pit_code(codigo_ibge)}_Receita.zip"
    infos = {i.filename: i for i in rz.infolist()}
    info = infos.get(target)
    if info is None:
        return None, None, target, "receita_zip_ausente"

    rawzip = rz.read(info)
    entity_id = None
    with zipfile.ZipFile(io.BytesIO(rawzip)) as nz:
        name = next((n for n in nz.namelist() if "ReceitasConsolidado" in n), None)
        ent_name = next((n for n in nz.namelist() if "ReceitasEntidade" in n), None)
        if not name:
            return None, None, target, "xml_consolidado_ausente"
        root = ET.fromstring(nz.read(name))
        if ent_name:
            eroot = ET.fromstring(nz.read(ent_name))
            entities = {}
            for el in eroot.iter():
                a = el.attrib
                pid = a.get("idpessoa")
                nm = (a.get("nmEntidade") or "").strip()
                if pid and nm:
                    entities[pid] = nm
            for pid, nm in entities.items():
                up = nm.upper()
                if up.startswith("MUNICÍPIO DE ") or up.startswith("MUNICIPIO DE "):
                    entity_id = pid
                    break

    candidates = []
    for el in root.iter():
        a = el.attrib
        if a.get("idSumarioItem") != ID_IMPOSTOS and (a.get("dsItem") or "").strip().lower() != "impostos":
            continue
        v = a.get("vlRealizadoAteOMes")
        mes = a.get("nrMes")
        try:
            vf = float(v) if v not in (None, "") else None
        except ValueError:
            vf = None
        try:
            mf = int(mes) if mes not in (None, "") else None
        except ValueError:
            mf = None
        if vf is not None:
            candidates.append((mf, vf, (a.get("dsItem") or "").strip(), a.get("idSumarioItem")))

    if not candidates:
        return None, entity_id, target, "item_impostos_ausente"

    # Preferimos dezembro; se não houver, o maior acumulado disponível.
    dec = [x for x in candidates if x[0] == 12]
    chosen = max(dec or candidates, key=lambda x: x[1])
    return {
        "mes": chosen[0],
        "valor": chosen[1],
        "dsItem": chosen[2],
        "idSumarioItem": chosen[3],
    }, entity_id, target, "ok"




ISS_LABEL = re.compile(
    r"imposto\s+sobre\s+servi[cç]os\s+de\s+qualquer\s+natureza",
    re.IGNORECASE,
)


def br_money(text):
    if text is None:
        return None
    s = str(text).strip()
    m = re.fullmatch(r"-?\d{1,3}(?:\.\d{3})*,\d{2}", s)
    if not m:
        m = re.fullmatch(r"-?\d+,\d{2}", s)
    if not m:
        return None
    return float(s.replace(".", "").replace(",", "."))


def fetch_detail_iss(entity_id, ano):
    if not entity_id:
        return None, None, "entidade_municipal_ausente"
    params = {
        "IdEntidade": entity_id,
        "NrAno": ano,
        "NrMes": 12,
        "tipo": "padrao",
        "tipoExibicao": "Imprimir",
    }
    url = (
        "https://pit.tce.pr.gov.br/Receitas/ReceitaDetalhes/PlanoOrcamentarioPadrao?"
        + urllib.parse.urlencode(params)
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return None, url, f"erro_http:{type(exc).__name__}:{exc}"

    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        cells = [" ".join(td.stripped_strings) for td in tr.find_all(["td", "th"])]
        joined = " ".join(cells)
        if not ISS_LABEL.search(joined):
            continue
        low = joined.lower()
        # Seleciona a rubrica agregada do ISS, não seus desdobramentos.
        if any(k in low for k in (
            " - principal",
            " - multas",
            " - juros",
            " - dívida ativa",
            " - divida ativa",
            "adicional iss",
        )):
            continue
        monies = []
        for cell in cells:
            v = br_money(cell)
            if v is not None:
                monies.append(v)
        # Em alguns layouts código+descrição ficam juntos; capturamos valores
        # monetários também no texto integral da linha.
        if len(monies) < 2:
            for tok in re.findall(r"-?\d{1,3}(?:\.\d{3})*,\d{2}|-?\d+,\d{2}", joined):
                v = br_money(tok)
                if v is not None:
                    monies.append(v)
        if monies:
            rows.append({"text": joined, "values": monies, "realizado": monies[-1]})

    if not rows:
        return None, url, "rubrica_iss_nao_localizada"

    # Normalmente há uma única rubrica agregada. Se houver duplicidade,
    # preferimos a linha mais curta, que tende a ser o nível-pai.
    rows.sort(key=lambda x: len(x["text"]))
    return rows[0], url, "ok"


def classify_exact(dca, tce):
    if dca is None or tce is None:
        return "sem_comparacao", None
    if tce == 0:
        return ("coerente_ate_5pct", 0.0) if dca == 0 else ("divergencia_extrema", math.inf)
    delta = (dca / tce - 1) * 100
    ad = abs(delta)
    if ad <= 5:
        return "coerente_ate_5pct", delta
    if ad <= 20:
        return "revisar_5a20pct", delta
    if ad <= 100:
        return "divergencia_forte_20a100pct", delta
    return "divergencia_extrema_acima_100pct", delta


def classify(iss_dca, impostos_tce):
    if iss_dca is None:
        return "iss_dca_ausente", None
    if impostos_tce is None:
        return "tce_indisponivel", None
    if impostos_tce <= 0:
        if iss_dca > 0:
            return "inconsistencia_forte_iss_maior_que_total_impostos", math.inf
        return "ambos_zero", None
    ratio = iss_dca / impostos_tce
    # Tolerância de 2% para diferenças de atualização/escopo e arredondamento.
    if ratio > 1.02:
        return "inconsistencia_forte_iss_maior_que_total_impostos", ratio
    if ratio > 0.90:
        return "iss_proximo_do_total_impostos_requer_detalhe", ratio
    return "teste_nao_conclusivo_iss_abaixo_do_total_impostos", ratio


def main():
    rows = read_csv(ANOM)
    by_year = defaultdict(list)
    for r in rows:
        by_year[int(r["ano"])].append(r)

    output = []
    year_meta = {}

    for ano in sorted(by_year):
        url = TCE_URL.format(ano=ano)
        print(f"{ano}: abrindo diretório remoto do PIT...")
        try:
            with RemoteZip(url, headers={"User-Agent": UA}) as rz:
                year_meta[str(ano)] = {"url": url, "status": "ok", "n_anomalias": len(by_year[ano])}
                for r in by_year[ano]:
                    iss = float(r["iss_dca"]) if r.get("iss_dca") not in (None, "") else None
                    try:
                        tce, entity_id, target, status = extract_total_impostos(rz, ano, r["codigo_ibge"])
                    except Exception as exc:
                        tce, entity_id, target, status = None, None, f"{ano}_{pit_code(r['codigo_ibge'])}_Receita.zip", f"erro:{type(exc).__name__}:{exc}"

                    impostos = tce["valor"] if isinstance(tce, dict) else None
                    cls, ratio = classify(iss, impostos)
                    detail, detail_url, detail_status = fetch_detail_iss(entity_id, ano)
                    iss_tce = detail["realizado"] if isinstance(detail, dict) else None
                    exact_cls, exact_delta = classify_exact(iss, iss_tce)
                    output.append({
                        "codigo_ibge": r["codigo_ibge"],
                        "municipio": r["municipio"],
                        "ano": ano,
                        "iss_dca": iss,
                        "mediana_outros_anos_dca": r.get("mediana_outros_anos"),
                        "razao_iss_mediana_dca": r.get("razao_valor_mediana"),
                        "tce_total_impostos": impostos,
                        "razao_iss_dca_sobre_total_impostos_tce": ratio,
                        "classificacao_teste_total_impostos": cls,
                        "tce_iss_detalhado": iss_tce,
                        "diferenca_dca_vs_tce_iss_pct": exact_delta,
                        "classificacao_iss_detalhado": exact_cls,
                        "status_iss_detalhado": detail_status,
                        "url_iss_detalhado": detail_url,
                        "linha_iss_tce": (detail or {}).get("text") if isinstance(detail, dict) else None,
                        "id_entidade_tce": entity_id,
                        "status_leitura_tce": status,
                        "arquivo_pit": target,
                        "item_tce": (tce or {}).get("dsItem") if isinstance(tce, dict) else None,
                        "id_sumario_tce": (tce or {}).get("idSumarioItem") if isinstance(tce, dict) else None,
                        "mes_tce": (tce or {}).get("mes") if isinstance(tce, dict) else None,
                        "fonte_tce": url,
                    })
        except Exception as exc:
            year_meta[str(ano)] = {"url": url, "status": f"erro:{type(exc).__name__}:{exc}", "n_anomalias": len(by_year[ano])}
            for r in by_year[ano]:
                output.append({
                    "codigo_ibge": r["codigo_ibge"],
                    "municipio": r["municipio"],
                    "ano": ano,
                    "iss_dca": r.get("iss_dca"),
                    "mediana_outros_anos_dca": r.get("mediana_outros_anos"),
                    "razao_iss_mediana_dca": r.get("razao_valor_mediana"),
                    "tce_total_impostos": None,
                    "razao_iss_dca_sobre_total_impostos_tce": None,
                    "classificacao_teste_total_impostos": "tce_indisponivel",
                    "tce_iss_detalhado": None,
                    "diferenca_dca_vs_tce_iss_pct": None,
                    "classificacao_iss_detalhado": "sem_comparacao",
                    "status_iss_detalhado": "tce_indisponivel",
                    "url_iss_detalhado": None,
                    "linha_iss_tce": None,
                    "id_entidade_tce": None,
                    "status_leitura_tce": year_meta[str(ano)]["status"],
                    "arquivo_pit": None,
                    "item_tce": None,
                    "id_sumario_tce": None,
                    "mes_tce": None,
                    "fonte_tce": url,
                })
        time.sleep(0.2)

    strong = [r for r in output if r["classificacao_teste_total_impostos"] == "inconsistencia_forte_iss_maior_que_total_impostos"]
    near = [r for r in output if r["classificacao_teste_total_impostos"] == "iss_proximo_do_total_impostos_requer_detalhe"]
    unresolved = [r for r in output if r["classificacao_teste_total_impostos"].startswith("teste_nao_conclusivo")]
    exact_ok = [r for r in output if r["classificacao_iss_detalhado"] == "coerente_ate_5pct"]
    exact_review = [r for r in output if r["classificacao_iss_detalhado"] == "revisar_5a20pct"]
    exact_strong = [r for r in output if r["classificacao_iss_detalhado"] in {"divergencia_forte_20a100pct", "divergencia_extrema_acima_100pct"}]
    exact_missing = [r for r in output if r["classificacao_iss_detalhado"] == "sem_comparacao"]

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "fonte": "PIT/TCE-PR, arquivo anual consolidado, tema Receita, ReceitasConsolidado.xml",
        "teste": (
            "Compara o ISS do DCA/SICONFI com o item agregado 'Impostos' do PIT. "
            "ISS_DCA superior ao total de impostos do TCE, com tolerância de 2%, "
            "é classificado como inconsistência forte. ISS abaixo do total de impostos "
            "não é validado por este teste e permanece inconclusivo."
        ),
        "n_observacoes_sinalizadas": len(output),
        "n_inconsistencia_forte": len(strong),
        "n_iss_proximo_total_impostos": len(near),
        "n_teste_inconclusivo": len(unresolved),
        "validacao_iss_detalhada": {
            "n_coerente_ate_5pct": len(exact_ok),
            "n_revisar_5a20pct": len(exact_review),
            "n_divergencia_forte_ou_extrema": len(exact_strong),
            "n_sem_comparacao": len(exact_missing),
            "divergencias_fortes_ou_extremas": exact_strong,
            "coerentes_ate_5pct": exact_ok,
        },
        "anos": year_meta,
        "inconsistencias_fortes_teste_total_impostos": strong,
        "proximos_do_total": near,
        "nota": (
            "O teste agregado usa 'Impostos' apenas como limite superior conservador. "
            "A validação principal adicional consulta a rubrica detalhada de ISSQN no próprio PIT, "
            "por entidade, ano e dezembro, e compara diretamente o realizado com a DCA."
        ),
    }

    date = datetime.now(timezone.utc).date().isoformat()
    write_csv(AUDIT / f"validacao-iss-tce-pr-{date}.csv", output)
    write_csv(AUDIT / "validacao-iss-tce-pr-latest.csv", output)
    dump_json(AUDIT / f"resumo-validacao-iss-tce-pr-{date}.json", summary)
    dump_json(AUDIT / "resumo-validacao-iss-tce-pr-latest.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
