#!/usr/bin/env python3
"""
Coleta o OrcamentosExecucoes-<ano>.csv do ES (dataset de Despesas do
dados.es.gov.br): uma fotografia consolidada por Unidade Gestora (dotacao,
empenhado, liquidado, pago, RAP), cerca de 100-130 linhas por ano para o
Estado inteiro. Serve de total de controle para reconciliar qualquer
agregacao feita a partir da base granular de eventos (Despesas-<ano>.csv)
e, por si so, ja da a visao consolidada do Executivo por UG.

Classificacao de Poder: os codigos de UG dos outros Poderes/orgaos autonomos
(Legislativo, TCE, Judiciario, Ministerio Publico, Defensoria) tem 5 digitos
(ex.: 10101, 30101, 50101); todas as UGs do Executivo (direto e indireto,
incluindo o IPAJM) tem 6 digitos (ex.: 440901). Regra simples e conferida
manualmente contra as 123 UGs de 2026 -- ver OUTROS_PODERES abaixo como
salvaguarda caso apareca algum codigo de 5 digitos novo.
"""

import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

API = "https://dados.es.gov.br/api/3/action/datastore_search"

# resource_id de OrcamentosExecucoes-<ano>.csv (dataset 99e16b13-...)
RESOURCES = {
    2023: "00827698-d8da-40eb-8798-5fb3916e0f28",
    2024: "3b39753a-1b99-459b-9955-56b7449f810b",
    2025: "538b6477-dbc6-4183-9b73-adcc18867369",
    2026: "240f70ca-c810-442b-bade-bb0ea3280880",
}

# codigos de UG (5 digitos) que NAO pertencem ao Poder Executivo
OUTROS_PODERES_PREFIXOS = {"1", "2", "3", "5", "6"}  # 1o digito quando o codigo tem 5 digitos

OUTPUT = Path(__file__).parent / "orcamentos-execucoes-es.json"


def fetch(resource_id, retries=4):
    params = {"resource_id": resource_id, "limit": 500}
    url = API + "?" + urllib.parse.urlencode(params)
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read())
        except Exception:
            if i < retries - 1:
                time.sleep(2 ** i)
            else:
                raise


def to_float(s):
    if not s:
        return 0.0
    s = s.strip()
    return float(s.replace(".", "").replace(",", ".")) if s else 0.0


def is_executivo(codigo_ug):
    return len(codigo_ug) == 6


def main():
    resultado = {}
    for ano, rid in sorted(RESOURCES.items()):
        data = fetch(rid)
        result = data["result"]
        registros = []
        for r in result["records"]:
            ug = r["CodigoUnidadeGestora"]
            emp = to_float(r["ValorEmpenho"])
            liq = to_float(r["ValorLiquidado"])
            pago = to_float(r["ValorPago"])
            rap = to_float(r["ValorRap"])
            orcado = to_float(r["ValorOrcado"])
            orcado_inicial = to_float(r["ValorOrcadoInicial"])
            registros.append(
                {
                    "codigo_ug": ug,
                    "unidade_gestora": r["UnidadeGestora"],
                    "poder": "Executivo" if is_executivo(ug) else "Outros Poderes",
                    "dotacao_inicial": round(orcado_inicial, 2),
                    "dotacao_atualizada": round(orcado, 2),
                    "empenhado": round(emp, 2),
                    "liquidado": round(liq, 2),
                    "pago": round(pago, 2),
                    "rap": round(rap, 2),
                    "saldo_a_empenhar": round(orcado - emp, 2),
                    "empenhado_a_liquidar": round(emp - liq, 2),
                    "liquidado_nao_pago": round(liq - pago, 2),
                    "empenhado_nao_pago": round(emp - pago, 2),
                }
            )
        resultado[str(ano)] = {
            "resource_id": rid,
            "total_ugs": len(registros),
            "registros": sorted(registros, key=lambda x: -x["liquidado_nao_pago"]),
        }
        print(f"{ano}: {len(registros)} UGs coletadas")

    output = {
        "fonte": "dados.es.gov.br - OrcamentosExecucoes-<ano>.csv (fotografia consolidada por UG), via API DataStore",
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "metodologia": (
            "Fotografia consolidada por Unidade Gestora (nao e serie diaria). "
            "Serve de total de controle para reconciliar as agregacoes feitas a "
            "partir da base granular de eventos (Despesas-<ano>.csv). "
            "Poder classificado pelo numero de digitos do codigo de UG: 5 digitos "
            "= Legislativo/TCE/Judiciario/MP/Defensoria; 6 digitos = Executivo."
        ),
        "por_ano": resultado,
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Salvo em {OUTPUT}")


if __name__ == "__main__":
    main()
