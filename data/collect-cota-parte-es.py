#!/usr/bin/env python3
"""
Cota-parte municipal do ICMS no ES: declarado (SICONFI/SIOPE/SIOPS) x oficial (SEFAZ-ES).

Cruza dois lados de uma mesma transferência constitucional:

- Oficial: boletins de "Distribuição de ICMS/IPVA aos Municípios" publicados pela
  SEFAZ-ES (12 PDFs mensais para 2023 e 2024; demonstrativo acumulado anual já
  consolidado para 2025). https://sefaz.es.gov.br/transferencias-constitucionais-aos-municipios
- Declarado: planilha de compilação SICONFI (DCA/STN) x SIOPE (MEC) x SIOPS (MS)
  por município do ES, 2019-2025 (fornecida pelo autor; ver
  estudos/Compilação Dados - SICONFI, SIOPS e SIOPE - ES.zip).

Achado central de metodologia: a coluna "COTA" da planilha declarada corresponde à
Cota-Parte do ICMS em valor BRUTO (antes da retenção de 20% ao FUNDEB) -- confirmado
pela reconciliação quase perfeita com o valor bruto oficial da SEFAZ (desvio < 0,1%
somando todos os municípios do ES, 2023-2025). A comparação correta portanto usa
icms_bruto (SEFAZ) vs DCA (SICONFI), não ICMS+IPVA líquido.

Duas exceções de formato precisaram de parsers dedicados:
- abril/2023: fonte com codificação cid corrompida (glifos deslocados em +29 no
  código do caractere); tabela sem coluna de estornos, ordem ICMS/IPI/IPVA/CIDE/
  Compensação Financeira.
- junho/2023: texto plano, mas só publica "Valor LÍQUIDO" (sem bruto); o valor
  bruto é reconstituído por líquido / 0.8 (retenção FUNDEB de 20% é sempre exata).

Uso:
  python3 collect-cota-parte-es.py
"""

import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

import fitz  # PyMuPDF
import openpyxl
import pdfplumber

HERE = Path(__file__).parent
PDF_CACHE = HERE / ".cache-sefaz-pdfs"
PDF_CACHE.mkdir(exist_ok=True)

SEFAZ_BASE = "https://sefaz.es.gov.br"
XLSX_ZIP = HERE / "raw" / "siconfi-siope-siops-es.zip"
OUTPUT = HERE / "cota-parte-municipal-es.json"

# (ano, mes, caminho relativo ao SEFAZ_BASE) -- preferindo sempre a versão republicada
MONTHLY_FILES = [
    (2023, 1, "/media/Tesouro Estadual/GECOG/Distribuicao Mensal Janeiro_2023.pdf"),
    (2023, 2, "/media/Tesouro Estadual/GECOG/Distribuicao Mensal Fevereiro_2023.pdf"),
    (2023, 3, "/media/Tesouro Estadual/GECOG/Distribuicao Mensal Março_2023.pdf"),
    (2023, 4, "/media/Tesouro Estadual/GECOG/Distribuição Mensal Abril_2023.pdf"),
    (2023, 5, "/media/Tesouro Estadual/GECOG/Distribuicao Mensal Maio_2023.pdf"),
    (2023, 6, "/media/Tesouro Estadual/GECOG/Distribuicao Mensal Junho_2023.pdf"),
    (2023, 7, "/media/Tesouro Estadual/GECOG/Distribuição Mensal Julho_2023.pdf"),
    (2023, 8, "/media/Tesouro Estadual/GECOG/Distribuicao Mensal Agosto_2023.pdf"),
    (2023, 9, "/media/Tesouro Estadual/GECOG/Distribuicao Mensal Setembro_2023.pdf"),
    (2023, 10, "/media/Tesouro Estadual/GECOG/Distribuição Mensal Outubro_2023.pdf"),
    (2023, 11, "/media/Tesouro Estadual/GECOG/Distribuição Mensal Novembro_2023.pdf"),
    (2023, 12, "/media/Tesouro Estadual/GECOG/Distribuição Mensal_12 2023.pdf"),
    (2024, 1, "/media/Tesouro Estadual/Distribuição Mensal republicação 01 2024.pdf"),
    (2024, 2, "/media/Tesouro Estadual/Distribuição Mensal Republicação 02 2024.pdf"),
    (2024, 3, "/media/Tesouro Estadual/Distribuição Mensal Republicação 03 2024.pdf"),
    (2024, 4, "/media/Tesouro Estadual/GECOG/Distribuição Mensal 04 2024.pdf"),
    (2024, 5, "/media/Tesouro Estadual/OS-SUBSET Nº 45 a- Transferência aos Municipios_Vlr. Bruto e Líquido_05-2024.pdf"),
    (2024, 6, "/media/Tesouro Estadual/Distribuição Mensal NOVO 06 2024-1.pdf"),
    (2024, 7, "/media/Tesouro Estadual/Distribuição Mensal NOVO 07 2024-1.pdf"),
    (2024, 8, "/media/Tesouro Estadual/Distribuição Mensal NOVO 08 2024.pdf"),
    (2024, 9, "/media/Tesouro Estadual/Distribuição Mensal 09 2024.pdf"),
    (2024, 10, "/media/Tesouro Estadual/Distribuição Mensal 10 2024.pdf"),
    (2024, 11, "/media/Tesouro Estadual/Distribuição Mensal 11 2024-1.pdf"),
    (2024, 12, "/media/Tesouro Estadual/Distribuição Mensal NOVO 12 2024_Republicacao.pdf"),
]
ACUMULADO_2025 = "/media/Tesouro Estadual/Transferências de impostos aos Municípios_Acumulado 2025.pdf"

FIELDS = ["icms_bruto", "icms_liquido", "ipva_bruto", "ipva_liquido"]

PDF_NAME_OVERRIDES = {
    "CACH. ITAPEMIRIM": "CACHOEIRO DE ITAPEMIRIM",
    "CONC. DA BARRA": "CONCEICAO DA BARRA",
    "CONC. CASTELO": "CONCEICAO DO CASTELO",
    "DIVINO SAO LOURENCO": "DIVINO DE SAO LOURENCO",
}


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(s):
    return re.sub(r"\s+", " ", strip_accents(s).upper()).strip()


def canonical(pdf_name):
    n = norm(pdf_name)
    return PDF_NAME_OVERRIDES.get(n, n)


def download(year, month, relpath):
    fname = f"{year}_{month:02d}.pdf"
    dest = PDF_CACHE / fname
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    url = SEFAZ_BASE + urllib.parse.quote(relpath)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                dest.write_bytes(r.read())
            return dest
        except Exception as e:
            print(f"  retry {year}-{month:02d}: {e}", file=sys.stderr)
            time.sleep(2)
    raise RuntimeError(f"failed to download {year}-{month:02d}")


def parse_brl(s):
    if s is None:
        return 0.0
    s = s.strip()
    if s in ("", "-"):
        return 0.0
    s = s.replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def find_value_cols(table):
    """Localiza a linha de fórmulas (com 'Valor BRUTO'/'Valor LÍQUIDO') e devolve,
    para cada coluna não-estorno, a que imposto (ICMS/IPVA) e tipo (bruto/líquido)
    ela pertence -- descobertos varrendo a linha de grupos (ICMS-25%/IPVA-50%)
    acima dela."""
    frow_idx = None
    for i, row in enumerate(table):
        for cell in row:
            if cell and norm(cell).startswith("VALOR") and "LIQUIDO" in norm(cell):
                frow_idx = i
                break
        if frow_idx is not None:
            break
    if frow_idx is None:
        raise RuntimeError("formula row not found")

    grow_idx = None
    for i in range(frow_idx - 1, -1, -1):
        row = table[i]
        if any(
            cell and ("ICMS" in norm(cell) or "IPVA" in norm(cell)) and "ESTORNO" not in norm(cell)
            for cell in row
        ):
            grow_idx = i
            break
    if grow_idx is None:
        raise RuntimeError("group row not found")

    grow, frow = table[grow_idx], table[frow_idx]
    cols = []
    for idx, cell in enumerate(frow):
        if not cell or "ESTORNO" in norm(cell):
            continue
        c = norm(cell)
        if c.startswith("VALOR") and "LIQUIDO" in c:
            kind = "liquido"
        elif c.startswith("VALOR") and "BRUTO" in c:
            kind = "bruto"
        else:
            continue
        j, group_text = idx, None
        while j >= 0:
            if grow[j]:
                group_text = norm(grow[j])
                break
            j -= 1
        if group_text and "ICMS" in group_text:
            cols.append((idx, "icms", kind))
        elif group_text and "IPVA" in group_text:
            cols.append((idx, "ipva", kind))
    return frow_idx, cols


def parse_pdf(path):
    """Formato padrão (a maioria dos meses): tabela pdfplumber com uma célula por
    coluna contendo todos os 78 municípios separados por quebra de linha."""
    with pdfplumber.open(path) as pdf:
        table = pdf.pages[0].extract_tables()[0]
        frow_idx, cols = find_value_cols(table)
        data_row = table[frow_idx + 1]
        names = [n.strip() for n in data_row[0].split("\n")]
        result = {}
        for idx, tax, kind in cols:
            values = [parse_brl(v) for v in data_row[idx].split("\n")]
            if len(values) != len(names):
                raise RuntimeError(f"{path.name}: mismatch names={len(names)} {tax}_{kind}={len(values)}")
            for name, val in zip(names, values):
                result.setdefault(name, {})[f"{tax}_{kind}"] = val
        return result


def get_canonical_names():
    """Lista oficial dos 78 municípios do ES, na ordem fixa usada em todo boletim,
    extraída de um mês com fonte limpa (usado para municípios de meses com fonte
    corrompida, ver parse_pdf_2023_04)."""
    path = download(2023, 1, "/media/Tesouro Estadual/GECOG/Distribuicao Mensal Janeiro_2023.pdf")
    with pdfplumber.open(path) as pdf:
        table = pdf.pages[0].extract_tables()[0]
        frow_idx, _ = find_value_cols(table)
        return [n.strip() for n in table[frow_idx + 1][0].split("\n")]


def parse_pdf_2023_04(path, canonical_names):
    doc = fitz.open(path)
    lines = ["".join(chr(ord(c) + 29) for c in l).strip() for l in doc[0].get_text().split("\n")]
    lines = [l for l in lines if l]
    body = lines[lines.index("AFONSO CLAUDIO"): lines.index("TOTAL")]
    assert len(body) // 11 == len(canonical_names) == len(body) / 11
    result = {}
    for i in range(0, len(body), 11):
        row = body[i : i + 11]
        result[canonical_names[i // 11]] = {
            "icms_bruto": parse_brl(row[2]), "icms_liquido": parse_brl(row[3]),
            "ipva_bruto": parse_brl(row[6]), "ipva_liquido": parse_brl(row[7]),
        }
    return result


def parse_pdf_2023_06(path, canonical_names):
    doc = fitz.open(path)
    lines = [l.strip() for l in doc[0].get_text().split("\n") if l.strip()]
    body = lines[lines.index("AFONSO CLAUDIO"): lines.index("TOTAL")]
    assert len(body) // 7 == len(canonical_names) == len(body) / 7
    result = {}
    for i in range(0, len(body), 7):
        row = body[i : i + 7]
        icms_liq, ipva_liq = parse_brl(row[2]), parse_brl(row[4])
        # este boletim só publica "valor líquido"; bruto = líquido / 0.8 (FUNDEB = 20% do bruto)
        result[canonical_names[i // 7]] = {
            "icms_bruto": icms_liq / 0.8, "icms_liquido": icms_liq,
            "ipva_bruto": ipva_liq / 0.8, "ipva_liquido": ipva_liq,
        }
    return result


SPECIAL_PARSERS = {(2023, 4): parse_pdf_2023_04, (2023, 6): parse_pdf_2023_06}


def collect_sefaz():
    yearly = {}
    canonical_names = get_canonical_names()

    for year, month, relpath in MONTHLY_FILES:
        path = download(year, month, relpath)
        try:
            parsed = (
                SPECIAL_PARSERS[(year, month)](path, canonical_names)
                if (year, month) in SPECIAL_PARSERS
                else parse_pdf(path)
            )
        except Exception as e:
            print(f"ERRO ao parsear {year}-{month:02d} ({path.name}): {e}", file=sys.stderr)
            continue
        yd = yearly.setdefault(year, {})
        for name, vals in parsed.items():
            entry = yd.setdefault(name, {f: 0.0 for f in FIELDS})
            for f in FIELDS:
                entry[f] += vals.get(f, 0.0)
        print(f"  OK {year}-{month:02d}: {len(parsed)} municípios", file=sys.stderr)

    # 2025: demonstrativo acumulado anual, já consolidado pela SEFAZ
    path = download(2025, 0, ACUMULADO_2025)
    with pdfplumber.open(path) as pdf:
        table = pdf.pages[0].extract_tables()[0]
        row = table[3]  # layout fixo, validado manualmente: 2=icms bruto,4=icms líq,5=ipva bruto,7=ipva líq
        names = [n.strip() for n in row[0].split("\n")]
        icms_b = [parse_brl(v) for v in row[2].split("\n")]
        icms_l = [parse_brl(v) for v in row[4].split("\n")]
        ipva_b = [parse_brl(v) for v in row[5].split("\n")]
        ipva_l = [parse_brl(v) for v in row[7].split("\n")]
        yearly[2025] = {
            name: {"icms_bruto": ib, "icms_liquido": il, "ipva_bruto": pb, "ipva_liquido": pl}
            for name, ib, il, pb, pl in zip(names, icms_b, icms_l, ipva_b, ipva_l)
        }
    return yearly


def load_siconfi():
    with zipfile.ZipFile(XLSX_ZIP) as zf:
        xlsx_name = next(n for n in zf.namelist() if n.lower().endswith(".xlsx"))
        data = zf.read(xlsx_name)
    wb = openpyxl.load_workbook(BytesIO(data), read_only=True, data_only=True)
    ws = wb["ES"]
    it = ws.iter_rows(values_only=True)
    next(it)  # header
    rows, cod_to_name = [], {}
    for ano, cod, uf, ente, tipo, dca, siope, siops, validacao, qtd_div, base_div, media_desvio in it:
        if ano is None:
            continue
        cod_to_name[cod] = ente
        rows.append(dict(
            ano=ano, cod=cod, ente=ente, tipo=tipo, dca=dca, siope=siope, siops=siops,
            validacao=validacao, base_div=base_div, media_desvio=media_desvio,
        ))
    return rows, cod_to_name


def main():
    print("=== Extraindo boletins oficiais da SEFAZ-ES (2023-2025) ===", file=sys.stderr)
    sefaz = collect_sefaz()

    print("=== Lendo planilha SICONFI/SIOPE/SIOPS ===", file=sys.stderr)
    rows, cod_to_name = load_siconfi()
    name_to_cod = {canonical(name): cod for cod, name in cod_to_name.items() if cod != 32}
    cota = {(r["ano"], r["cod"]): r for r in rows if r["tipo"] == "COTA" and r["cod"] != 32}

    # 1) Comparação por município: oficial (SEFAZ, ICMS bruto) x declarado (DCA/SICONFI)
    municipio_comp = []
    for year, muns in sefaz.items():
        if year not in (2023, 2024, 2025):
            continue
        for pdf_name, vals in muns.items():
            cod = name_to_cod.get(canonical(pdf_name))
            declared_row = cota.get((year, cod)) if cod else None
            if not declared_row or not declared_row["dca"]:
                continue
            oficial, declarado = vals["icms_bruto"], declared_row["dca"]
            municipio_comp.append(dict(
                ano=year, cod_ibge=cod, municipio=cod_to_name[cod],
                oficial_icms_bruto=round(oficial, 2),
                oficial_icms_liquido=round(vals["icms_liquido"], 2),
                oficial_ipva_liquido=round(vals["ipva_liquido"], 2),
                declarado_siconfi=round(declarado, 2),
                diff_rs=round(oficial - declarado, 2),
                diff_pct=round((oficial - declarado) / declarado * 100, 3),
                validacao_interna=declared_row["validacao"],
            ))
    municipio_comp.sort(key=lambda c: -abs(c["diff_pct"]))

    agregado = {}
    for year in (2023, 2024, 2025):
        yc = [c for c in municipio_comp if c["ano"] == year]
        tot_of = sum(c["oficial_icms_bruto"] for c in yc)
        tot_de = sum(c["declarado_siconfi"] for c in yc)
        agregado[str(year)] = dict(
            oficial_icms_bruto=round(tot_of, 2), declarado_siconfi=round(tot_de, 2),
            diff_rs=round(tot_of - tot_de, 2), diff_pct=round((tot_of - tot_de) / tot_de * 100, 3),
            n_municipios=len(yc),
        )

    # 2) Validação cruzada histórica entre as três bases declaradas (2019-2025)
    cota_all = [r for r in rows if r["tipo"] == "COTA" and r["cod"] != 32]
    internal = [
        dict(
            ano=r["ano"], cod_ibge=r["cod"], municipio=cod_to_name[r["cod"]],
            dca=r["dca"], siope=r["siope"], siops=r["siops"],
            validacao=r["validacao"], base_divergencia=r["base_div"],
            desvio_medio_pct=round((r["media_desvio"] or 0) * 100, 3),
        )
        for r in cota_all
    ]
    internal.sort(key=lambda r: -abs(r["desvio_medio_pct"]))

    resumo_por_ano = {}
    for ano in sorted(set(r["ano"] for r in cota_all)):
        yr = [r for r in cota_all if r["ano"] == ano]
        ok = sum(1 for r in yr if r["validacao"] == "OK")
        falso = sum(1 for r in yr if r["validacao"] == "FALSO")
        resumo_por_ano[str(ano)] = dict(ok=ok, falso=falso, pct_divergente=round(falso / (ok + falso) * 100, 1))

    output = dict(
        fonte_oficial=(
            "SEFAZ-ES, Subsecretaria do Tesouro Estadual — Distribuição de ICMS/IPVA aos "
            "municípios (boletins mensais e demonstrativo acumulado anual, 2023-2025)"
        ),
        fonte_declarado="Compilação SICONFI (DCA/STN), SIOPE (MEC) e SIOPS (MS) por município do ES, 2019-2025",
        unidade="R$ nominais",
        nota_metodologica=(
            "'COTA' na base declarada corresponde à Cota-Parte do ICMS em valor BRUTO "
            "(antes da retenção de 20% ao FUNDEB), confirmado pela reconciliação quase "
            "perfeita com o valor bruto oficial da SEFAZ-ES somando todos os municípios "
            "do ES (desvio < 0,1% em 2023-2025)."
        ),
        agregado_es_por_ano=agregado,
        comparacao_municipio_sefaz_siconfi=municipio_comp,
        validacao_interna_dca_siope_siops=internal,
        resumo_validacao_interna_por_ano=resumo_por_ano,
    )
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Salvo em {OUTPUT} ({OUTPUT.stat().st_size / 1024:.1f} KB)", file=sys.stderr)


if __name__ == "__main__":
    main()
