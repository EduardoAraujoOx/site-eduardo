#!/usr/bin/env python3
"""
Mapa do artigo: variação da receita municipal bruta em 2033 (IBS municipal
versus o contrafactual sem reforma) nos 399 municípios do Paraná, em classes de
cor divergentes (azul = ganha, vermelho = perde). Municípios fora da amostra do
artigo (qualificado_artigo = False) recebem hachura branca. Sem título.

Malha: IBGE, Malha Municipal 2024 (baixada na execução).
Uso: python3 build-mapa-variacao-pr.py -> graficos-artigo/mapa-variacao-2033-pr.{png,svg}
"""
import io, tempfile, urllib.request, zipfile
from pathlib import Path
import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = Path(__file__).parent
CSV = HERE / "auditoria-pr-validacao" / "municipios-pr-final-auditado-latest.csv"
OUT = HERE / "auditoria-pr-validacao" / "graficos-artigo"
OUT.mkdir(exist_ok=True)
URL = ("https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/"
       "municipio_2024/UFs/PR/PR_Municipios_2024.zip")
INK, INK2 = "#0b0b0b", "#52514e"

# classes (limite inferior, limite superior, cor, rótulo) — par divergente azul/vermelho, neutro cinza no meio
CLASSES = [
    (-1e9, -15, "#a8281b", "Perde mais de 15%"),
    (-15, -7.5, "#cf4a3a", "Perde de 7,5% a 15%"),
    (-7.5, -2.5, "#eb9a8c", "Perde de 2,5% a 7,5%"),
    (-2.5, 2.5, "#dedcd6", "Variação de −2,5% a +2,5%"),
    (2.5, 7.5, "#9dc3e6", "Ganha de 2,5% a 7,5%"),
    (7.5, 15, "#4a86c8", "Ganha de 7,5% a 15%"),
    (15, 1e9, "#1b4a85", "Ganha mais de 15%"),
]
# nome: (deslocamento x, y em pontos, alinhamento, com linha-guia?)
ROTULOS = {"Curitiba": (-4, -15, "center", False), "Londrina": (8, 8, "left", False), "Maringá": (-8, 8, "right", False),
           "Cascavel": (-9, 9, "right", False), "Ponta Grossa": (-9, 10, "right", False),
           "Foz do Iguaçu": (9, 5, "left", False), "Paranaguá": (26, -12, "left", True)}


def classe(v):
    for lo, hi, cor, _ in CLASSES:
        if lo <= v < hi:
            return cor
    return "#ffffff"


def fmt(v):
    return f"{v:+.1f}".replace(".", ",").replace("-", "−") + "%"


with tempfile.TemporaryDirectory() as tmp:
    zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(URL, timeout=120).read())).extractall(tmp)
    gdf = gpd.read_file(next(Path(tmp).glob("*.shp")))
d = pd.read_csv(CSV, encoding="utf-8-sig", dtype={"codigo_ibge": str})
d["v"] = d["variacao_2033_final_pct"].astype(float)
gdf["codigo_ibge"] = gdf["CD_MUN"].astype(str)
m = gdf.merge(d[["codigo_ibge", "municipio", "v", "qualificado_artigo"]], on="codigo_ibge", how="left")
assert m["v"].notna().all() and len(m) == 399, (m["v"].isna().sum(), len(m))
m["cor"] = m["v"].apply(classe)
m = m.to_crs(31982)   # SIRGAS 2000 / UTM 22S: proporções corretas

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "text.color": INK})
fig = plt.figure(figsize=(6.5, 4.3), dpi=300)
ax = fig.add_axes([0.0, 0.2, 1.0, 0.8])
dentro = m[m["qualificado_artigo"] == True]
fora = m[m["qualificado_artigo"] != True]
dentro.plot(ax=ax, color=dentro["cor"], edgecolor="white", linewidth=0.25)
plt.rcParams["hatch.linewidth"] = 0.45
fora.plot(ax=ax, color=fora["cor"], edgecolor="white", linewidth=0.25, hatch="//////")
m.dissolve().boundary.plot(ax=ax, color=INK2, linewidth=0.5)
ax.set_axis_off()

# rótulos das principais cidades (deslocamentos em pontos, com halo branco)
x0, y0, x1, y1 = m.total_bounds
ax.set_xlim(x0 - 0.01 * (x1 - x0), x1 + 0.18 * (x1 - x0))
for nome, (dx, dy, ha, guia) in ROTULOS.items():
    r = m[m["municipio"] == nome].iloc[0]
    pt = r.geometry.representative_point()
    ax.plot(pt.x, pt.y, marker="o", markersize=2.4, color=INK, markeredgecolor="white", markeredgewidth=0.4, zorder=6)
    ax.annotate(f"{nome} ({fmt(r.v)})", xy=(pt.x, pt.y), xytext=(dx, dy), textcoords="offset points",
                fontsize=6.4, ha=ha, va="center", color=INK, zorder=7,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85),
                arrowprops=dict(arrowstyle="-", color=INK2, linewidth=0.4, shrinkA=0, shrinkB=1) if guia else None)

cont = lambda lo, hi: int(((m.v >= lo) & (m.v < hi)).sum())
handles = [Patch(facecolor=c, edgecolor="white", label=f"{lab} ({cont(lo, hi)})") for lo, hi, c, lab in CLASSES[::-1]]
handles.append(Patch(facecolor="#cfcfcf", edgecolor="white", hatch="//////", label=f"Fora da amostra do artigo ({len(fora)})"))
fig.legend(handles=handles, loc="lower left", frameon=False, fontsize=6.8, ncol=3, handlelength=1.3, handleheight=1.0,
           title="Variação da receita municipal em 2033 (n.º de municípios)", title_fontsize=7, alignment="left",
           bbox_to_anchor=(0.03, 0.0), columnspacing=1.4)
fig.savefig(OUT / "mapa-variacao-2033-pr.png", dpi=300, facecolor="white")
fig.savefig(OUT / "mapa-variacao-2033-pr.svg", facecolor="white")
print({lab: cont(lo, hi) for lo, hi, _, lab in CLASSES}, len(dentro), len(fora))
