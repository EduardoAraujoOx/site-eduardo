#!/usr/bin/env python3
"""
Baixa a tabela mais recente de "Grandes Números do IRPF" da Receita Federal (ano-calendário 2024, exercício 2025; xlsx de ~19 MB)
e extrai a Tabela 8 (declarantes e rendimentos totais por UF e faixa de rendimentos totais em salários mínimos anuais),
agregando os tipos de formulário. Rendimentos totais = tributáveis + exclusiva/definitiva + isentos e não tributáveis.
O painel público do IRPF 2026 (ano-base 2025, lançado em jul/2026) é Power BI sem download nem microdados; por isso a fonte
mais recente que se consegue ler por script é a do ano-calendário 2024.
Saída: data/irpf-uf-faixas-ac2024.json
"""
import json
import subprocess
from collections import defaultdict
from pathlib import Path

import openpyxl

HERE = Path(__file__).parent
URL = ("https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/estudos/imposto-de-renda/estudos-por-ano/"
       "grandes-numeros-do-IRPF-2008-a-2025/grandes-numeros-do-irpf-2025-ano-calendario-2024-tabelas/@@download/file")
NOME = {'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA', 'Ceará': 'CE', 'Distrito Federal': 'DF', 'Espírito Santo': 'ES',
        'Goiás': 'GO', 'Maranhão': 'MA', 'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG', 'Paraná': 'PR', 'Paraíba': 'PB',
        'Pará': 'PA', 'Pernambuco': 'PE', 'Piauí': 'PI', 'Rio Grande do Norte': 'RN', 'Rio Grande do Sul': 'RS', 'Rio de Janeiro': 'RJ',
        'Rondônia': 'RO', 'Roraima': 'RR', 'Santa Catarina': 'SC', 'Sergipe': 'SE', 'São Paulo': 'SP', 'Tocantins': 'TO'}


def num(v):
    return float(v) if isinstance(v, (int, float)) else 0.0      # 'x' = célula protegida por sigilo (3 de 3.672)


def main():
    arq = Path("/tmp/gn_irpf_ac2024.xlsx")
    if not arq.exists():
        subprocess.run(["curl", "-sSL", "--retry", "4", "-m", "600", "-o", str(arq), URL], check=True)   # arquivo grande: curl com retentativas
    ws = openpyxl.load_workbook(arq, read_only=True, data_only=True)["Tab8"]
    rows = list(ws.iter_rows(values_only=True))
    h = {n: i for i, n in enumerate(rows[1]) if n}
    ag = defaultdict(lambda: {"declarantes": 0.0, "renda_total": 0.0})
    for r in rows[2:]:
        if r[h["uf"]] not in NOME:
            continue
        faixa = r[h["faixa_de_rendim_tributavel_mais_trib_exclusiva_mais_isentos_em_sal_minimos"]]
        k = (NOME[r[h["uf"]]], faixa)
        ag[k]["declarantes"] += num(r[h["qtde_contribuintes"]])
        ag[k]["renda_total"] += num(r[h["rendimento_tributavel_total"]]) + num(r[h["rend_sujeitos_a_tribut_exclusiva"]]) + num(r[h["rend_isentos_e_nao_tributaveis"]])
    out = defaultdict(dict)
    for (u, f), v in ag.items():
        out[u][f] = {"declarantes": v["declarantes"], "renda_total": round(v["renda_total"], 2)}
    (HERE / "irpf-uf-faixas-ac2024.json").write_text(json.dumps({"_meta": "Grandes Números do IRPF, ano-calendário 2024 (exercício 2025), Tabela 8; faixas em salários mínimos anuais; R$ correntes",
                                                              "fonte": URL, "por_uf": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("salvo", len(out), "UFs")


if __name__ == "__main__":
    main()
