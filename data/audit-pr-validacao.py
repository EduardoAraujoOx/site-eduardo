#!/usr/bin/env python3
"""
Validação externa dos dados municipais do Paraná usados no cálculo do CPT.

Etapas:
1. Baixa, para 2019-2025, a visão anual de repasses aos 399 municípios no
   Portal da Transparência do Governo do Paraná.
2. Compara a cota-parte do ICMS declarada por cada município no DCA/SICONFI
   com o ICMS bruto efetivamente repassado pelo Estado.
3. Sinaliza divergências cadastrais/contábeis sem substituir silenciosamente
   valores observados.
4. Produz uma lista separada de anomalias de ISS observadas na série DCA,
   para verificação posterior em outra fonte oficial (TCE-PR/SIM-AM).
5. Recoleta o ente estadual Paraná no DCA (ICMS, FECOP, cota-parte e outras
   deduções), compara com a fotografia vigente e confere a cota-parte agregada
   contra a soma do Portal estadual.

A rotina é exclusivamente de auditoria. NÃO altera reforma-tributaria.json
nem os coeficientes/projeções usados pelo site.
"""
from __future__ import annotations

import csv
import json
import math
import re
import statistics
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError as exc:
    raise SystemExit("Instale beautifulsoup4 antes de executar este script.") from exc

HERE = Path(__file__).resolve().parent
OUTDIR = HERE / "auditoria-pr-validacao"
ANOS = list(range(2019, 2026))
PORTAL_URL = (
    "https://www4.pr.gov.br/Gestao/portaldatransparencia/repasses/relatorio/"
    "rrepassesmun.jsp?Param_Data=01%2F01%2F{ano}&Param_Tiporelatorio=ANUAL"
)
SICONFI_BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
USER_AGENT = "Mozilla/5.0 auditoria-reforma-tributaria-sefaz-es/1.0"

ICMS_NEW = "RO1.1.1.4.50.1.0"
FECOP_NEW = "RO1.1.1.4.50.2.0"
ICMS_OLD = "RO1.1.1.8.02.1.0"
FECOP_OLD = "RO1.1.1.8.02.2.0"

COL_BRUTA = "Receitas Brutas Realizadas"
COL_TRANSF = "Deduções - Transferências Constitucionais"
COL_OUTRAS = "Outras Deduções da Receita"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def fetch_text(url: str, retries: int = 5, timeout: int = 60) -> str:
    errors = []
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                charset = r.headers.get_content_charset() or "iso-8859-1"
                try:
                    return raw.decode(charset)
                except UnicodeDecodeError:
                    return raw.decode("utf-8", errors="replace")
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            if attempt < retries:
                time.sleep(min(2 ** (attempt - 1), 16))
    raise RuntimeError(f"Falha ao baixar {url}: {' | '.join(errors[-3:])}")


def fetch_json(url: str, retries: int = 5, timeout: int = 60):
    return json.loads(fetch_text(url, retries=retries, timeout=timeout))


def norm_name(s: str) -> str:
    s = unescape(s or "")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = s.replace("d'", "d ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def br_number(s: str):
    if s is None:
        return None
    s = unescape(str(s)).strip()
    if not s or s in {"-", "–", "—"}:
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


def parse_portal_annual(ano: int):
    html = fetch_text(PORTAL_URL.format(ano=ano))
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if len(cells) < 4:
            continue
        municipio = cells[0].strip()
        n = norm_name(municipio)
        if (
            not n
            or n.startswith("municipio")
            or n.startswith("totais")
            or n.startswith("total em")
            or n.startswith("acumulado")
        ):
            continue
        if "repasse bruto" in n or "referencia" in n:
            continue

        # Na visão anual, as primeiras colunas são:
        # Município | Índice FPM/IPM | ICMS bruto | ICMS líquido | ...
        icms_bruto = br_number(cells[2])
        icms_liquido = br_number(cells[3])
        if icms_bruto is None:
            continue
        rows.append({
            "ano": ano,
            "municipio_portal": municipio,
            "nome_norm": n,
            "icms_bruto_portal": icms_bruto,
            "icms_liquido_portal": icms_liquido,
        })

    # Deduplicação defensiva: algumas páginas repetem cabeçalhos/rodapés.
    uniq = {}
    for r in rows:
        uniq[r["nome_norm"]] = r
    rows = list(uniq.values())

    # A visão anual deve trazer 399 municípios. Não abortamos por diferença pequena,
    # mas registramos para auditoria e abortamos se a estrutura tiver mudado muito.
    if len(rows) < 390:
        raise RuntimeError(
            f"Parser do Portal encontrou apenas {len(rows)} municípios em {ano}; "
            "possível mudança de estrutura HTML."
        )
    return rows


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def dump_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def fnum(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def discrepancy_class(dca, portal):
    if dca is None and portal is None:
        return "ambos_ausentes"
    if dca is None:
        return "dca_ausente"
    if portal is None:
        return "portal_ausente"
    if portal == 0:
        return "portal_zero" if dca != 0 else "ambos_zero"
    rel = abs(dca - portal) / abs(portal)
    if rel <= 0.05:
        return "coerente_ate_5pct"
    if rel <= 0.20:
        return "revisar_5a20pct"
    if rel <= 1.00:
        return "divergencia_forte_20a100pct"
    return "divergencia_extrema_acima_100pct"


def build_portal_crosscheck(portal_by_year, obs_rows):
    obs_index = {}
    names_by_code = {}
    for o in obs_rows:
        cod = o["codigo_ibge"]
        ano = int(o["ano"])
        obs_index[(cod, ano)] = o
        names_by_code[cod] = o["municipio"]

    portal_index = {
        (ano, r["nome_norm"]): r
        for ano, rows in portal_by_year.items()
        for r in rows
    }

    out = []
    unmatched = []
    for (cod, ano), o in sorted(obs_index.items()):
        nome = o["municipio"]
        p = portal_index.get((ano, norm_name(nome)))
        if p is None:
            unmatched.append({"codigo_ibge": cod, "municipio": nome, "ano": ano})
            portal = None
        else:
            portal = p["icms_bruto_portal"]

        dca = fnum(o.get("new_cota_raw"))
        cls = discrepancy_class(dca, portal)
        diff = (dca - portal) if (dca is not None and portal is not None) else None
        rel = (diff / portal) if (diff is not None and portal not in (None, 0)) else None

        out.append({
            "codigo_ibge": cod,
            "municipio": nome,
            "ano": ano,
            "status_dca": o.get("data_status"),
            "cota_dca": dca,
            "icms_bruto_portal_pr": portal,
            "diferenca_reais": diff,
            "diferenca_pct_portal": rel * 100 if rel is not None else None,
            "classificacao": cls,
            "fonte_portal": PORTAL_URL.format(ano=ano),
        })
    return out, unmatched


def build_iss_anomalies(obs_rows):
    by_muni = defaultdict(list)
    for o in obs_rows:
        v = fnum(o.get("new_iss"))
        if v is not None:
            by_muni[(o["codigo_ibge"], o["municipio"])].append((int(o["ano"]), v))

    anomalies = []
    for (cod, nome), vals in by_muni.items():
        vals.sort()
        for ano, v in vals:
            peers = [x for y, x in vals if y != ano and x is not None and x > 0]
            if len(peers) < 3:
                continue
            med = statistics.median(peers)
            ratio = v / med if med > 0 else None
            if ratio is None:
                continue
            # Sinalizador conservador. Não substitui o dado: apenas prioriza verificação.
            if ratio >= 5 or ratio <= 0.20:
                anomalies.append({
                    "codigo_ibge": cod,
                    "municipio": nome,
                    "ano": ano,
                    "iss_dca": v,
                    "mediana_outros_anos": med,
                    "razao_valor_mediana": ratio,
                    "sinal": "muito_acima" if ratio >= 5 else "muito_abaixo",
                    "tratamento": "verificar_em_fonte_externa;nao_substituir_automaticamente",
                })
    anomalies.sort(key=lambda r: abs(math.log(max(r["razao_valor_mediana"], 1e-12))), reverse=True)
    return anomalies


def state_dca_url(ano):
    params = {
        "an_exercicio": ano,
        "co_tipo_demonstrativo": "DCA",
        "no_anexo": "DCA-Anexo I-C",
        "co_esfera": "E",
        "id_ente": 41,
    }
    return f"{SICONFI_BASE}/dca?{urllib.parse.urlencode(params)}"


def parse_state_dca(ano):
    data = fetch_json(state_dca_url(ano))
    items = data.get("items", [])
    icms_code = ICMS_NEW if ano >= 2022 else ICMS_OLD
    fecop_code = FECOP_NEW if ano >= 2022 else FECOP_OLD

    icms_rows = {i.get("coluna"): fnum(i.get("valor")) for i in items if i.get("cod_conta") == icms_code}
    fecop_rows = {i.get("coluna"): fnum(i.get("valor")) for i in items if i.get("cod_conta") == fecop_code}

    def pick(rows, *needles):
        for col, val in rows.items():
            ncol = norm_name(col)
            if all(norm_name(n) in ncol for n in needles):
                return val
        return None

    if not icms_rows:
        return {
            "ano": ano,
            "status": "conta_icms_ausente",
            "icms_bruto": None,
            "cota_parte": None,
            "outras_deducoes": None,
            "fecop": pick(fecop_rows, "receitas brutas") if fecop_rows else None,
            "colunas_icms": [],
        }
    return {
        "ano": ano,
        "status": "ok",
        "icms_bruto": pick(icms_rows, "receitas brutas"),
        "cota_parte": pick(icms_rows, "transferencias constitucionais"),
        # Se a coluna não estiver na resposta atual, mantemos None. Não a
        # transformamos em zero porque isso confundiria ausência de dimensão
        # na resposta com valor contábil efetivamente nulo.
        "outras_deducoes": pick(icms_rows, "outras deducoes"),
        "fecop": pick(fecop_rows, "receitas brutas") if fecop_rows else None,
        "colunas_icms": sorted(str(k) for k in icms_rows.keys() if k),
    }


def get_nested(d, key, ano, uf="PR"):
    return ((d.get(key, {}) or {}).get(str(ano), {}) or {}).get(uf)


def build_state_audit(portal_by_year):
    ref = json.loads((HERE / "reforma-tributaria.json").read_text(encoding="utf-8"))
    rows = []
    for ano in ANOS:
        new = parse_state_dca(ano)
        portal_total = sum(r["icms_bruto_portal"] for r in portal_by_year[ano])

        old_icms = get_nested(ref, "dca_icms_por_uf", ano)
        old_cota = get_nested(ref, "dca_transf_munis_por_uf", ano)
        old_fecop = get_nested(ref, "dca_fecop_por_uf", ano)
        old_outras = get_nested(ref, "dca_icms_outras_deducoes_por_uf", ano)

        def pct(new_v, old_v):
            if new_v is None or old_v in (None, 0):
                return None
            return (new_v / old_v - 1) * 100

        rows.append({
            "ano": ano,
            "status_nova_coleta": new["status"],
            "icms_bruto_novo": new["icms_bruto"],
            "icms_bruto_base_atual": old_icms,
            "delta_icms_pct": pct(new["icms_bruto"], old_icms),
            "fecop_novo": new["fecop"],
            "fecop_base_atual": old_fecop,
            "delta_fecop_pct": pct(new["fecop"], old_fecop),
            "cota_parte_nova_dca_estado": new["cota_parte"],
            "cota_parte_base_atual": old_cota,
            "delta_cota_base_pct": pct(new["cota_parte"], old_cota),
            "soma_icms_bruto_portal_municipios": portal_total,
            "delta_nova_cota_dca_vs_portal_pct": (
                (new["cota_parte"] / portal_total - 1) * 100
                if new["cota_parte"] is not None and portal_total
                else None
            ),
            "delta_base_atual_cota_vs_portal_pct": (
                (old_cota / portal_total - 1) * 100
                if old_cota is not None and portal_total
                else None
            ),
            "colunas_icms_resposta_atual": " | ".join(new.get("colunas_icms") or []),
            "outras_deducoes_novas": new["outras_deducoes"],
            "outras_deducoes_base_atual": old_outras,
            "delta_outras_pct": pct(new["outras_deducoes"], old_outras),
        })
        time.sleep(0.2)
    return rows


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    audit_dir = HERE / "auditoria-dca-pr"
    obs_path = audit_dir / "observacoes-pr-latest.csv"
    if not obs_path.exists():
        raise SystemExit("Execute antes data/audit-dca-pr.py; observacoes-pr-latest.csv não encontrado.")
    obs_rows = read_csv(obs_path)

    portal_by_year = {}
    portal_raw = {"_meta": {"generated_at_utc": now_iso(), "fonte": "Portal da Transparência do Estado do Paraná"}, "anos": {}}
    for ano in ANOS:
        print(f"Portal PR {ano}...")
        rows = parse_portal_annual(ano)
        portal_by_year[ano] = rows
        portal_raw["anos"][str(ano)] = rows
        print(f"  {len(rows)} municípios; soma ICMS bruto = R$ {sum(r['icms_bruto_portal'] for r in rows):,.2f}")
        time.sleep(0.4)

    cross, unmatched = build_portal_crosscheck(portal_by_year, obs_rows)
    anomalies_icms = [
        r for r in cross
        if r["classificacao"] in {
            "dca_ausente",
            "portal_ausente",
            "revisar_5a20pct",
            "divergencia_forte_20a100pct",
            "divergencia_extrema_acima_100pct",
        }
    ]
    anomalies_icms.sort(
        key=lambda r: abs(r["diferenca_pct_portal"]) if r["diferenca_pct_portal"] is not None else 1e99,
        reverse=True,
    )
    iss_anom = build_iss_anomalies(obs_rows)
    state_rows = build_state_audit(portal_by_year)

    classes = defaultdict(int)
    for r in cross:
        classes[r["classificacao"]] += 1

    # Municípios com alguma divergência forte/extrema em pelo menos um ano.
    # O Portal informa bruto e líquido (líquido após FUNDEB). A comparação
    # principal usa o bruto, coerente com a coluna "Receitas Brutas Realizadas"
    # do DCA. Diferenças próximas de -20% são, portanto, um sinal adicional de
    # que alguns entes podem ter escriturado o valor líquido na coluna bruta.
    strong_munis = sorted({
        r["municipio"] for r in cross
        if r["classificacao"] in {"divergencia_forte_20a100pct", "divergencia_extrema_acima_100pct"}
    })

    summary = {
        "generated_at_utc": now_iso(),
        "periodo": ANOS,
        "n_observacoes_municipio_ano": len(cross),
        "classificacoes_cota_parte": dict(classes),
        "n_municipios_divergencia_forte_ou_extrema": len(strong_munis),
        "municipios_divergencia_forte_ou_extrema": strong_munis,
        "n_sinais_iss_para_verificacao_externa": len(iss_anom),
        "n_matches_portal_nao_encontrados": len(unmatched),
        "matches_portal_nao_encontrados": unmatched,
        "auditoria_estado": state_rows,
        "criterios": {
            "coerente": "diferença absoluta <=5% frente ao ICMS bruto do Portal PR",
            "revisar": ">5% e <=20%",
            "forte": ">20% e <=100%",
            "extrema": ">100%",
            "iss": "valor anual >=5x ou <=20% da mediana dos demais anos observados; apenas sinalizador",
        },
        "nota": (
            "Divergência frente ao Portal PR identifica inconsistência entre duas fontes oficiais, "
            "mas não autoriza atribuir erro ao SICONFI como sistema. O DCA é declaração do ente. "
            "Casos fortes devem ser descritos como inconsistências nos registros declarados ao DCA/SICONFI "
            "até confirmação da origem contábil."
        ),
    }

    date = datetime.now(timezone.utc).date().isoformat()
    dump_json(OUTDIR / f"repasses-portal-pr-{date}.json", portal_raw)
    dump_json(OUTDIR / "repasses-portal-pr-latest.json", portal_raw)
    dump_json(OUTDIR / f"resumo-validacao-pr-{date}.json", summary)
    dump_json(OUTDIR / "resumo-validacao-pr-latest.json", summary)
    write_csv(OUTDIR / f"comparacao-cota-parte-pr-{date}.csv", cross)
    write_csv(OUTDIR / "comparacao-cota-parte-pr-latest.csv", cross)
    write_csv(OUTDIR / f"anomalias-cota-parte-pr-{date}.csv", anomalies_icms)
    write_csv(OUTDIR / "anomalias-cota-parte-pr-latest.csv", anomalies_icms)
    write_csv(OUTDIR / f"anomalias-iss-pr-{date}.csv", iss_anom)
    write_csv(OUTDIR / "anomalias-iss-pr-latest.csv", iss_anom)
    write_csv(OUTDIR / f"auditoria-estado-pr-{date}.csv", state_rows)
    write_csv(OUTDIR / "auditoria-estado-pr-latest.csv", state_rows)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nResultados em {OUTDIR}. Base canônica NÃO alterada.")


if __name__ == "__main__":
    main()
