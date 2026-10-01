#!/usr/bin/env python3
"""
Gráfico do artigo: variação da receita municipal bruta em 2033 (IBS municipal
versus o contrafactual sem reforma) nos municípios da amostra do artigo
(qualificado_artigo = True na base final auditada do Paraná), ordenados do maior
ganho à maior perda. Sem título (o título entra na legenda do Word).

Uso: python3 build-grafico-variacao-pr.py   -> graficos-artigo/grafico-variacao-2033-pr.{png,svg}
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

HERE = Path(__file__).parent
CSV = HERE / "auditoria-pr-validacao" / "municipios-pr-final-auditado-latest.csv"
OUT = HERE / "auditoria-pr-validacao" / "graficos-artigo"
OUT.mkdir(exist_ok=True)

AZUL, VERMELHO = "#2f6db5", "#cf4a3a"     # par divergente validado (ΔE CVD 18,8; contraste >= 3:1)
INK, INK2, GRADE = "#0b0b0b", "#52514e", "#e4e3df"
YMIN, YMAX = -33, 36                        # eixo truncado; barras além de YMAX são marcadas
N_ROT = 5


def pt(x, casas=1, sinal=False):
    s = f"{x:+.{casas}f}" if sinal else f"{x:.{casas}f}"
    return s.replace(".", ",").replace("-", "−")


d = pd.read_csv(CSV, encoding="utf-8-sig", dtype={"codigo_ibge": str})
d = d[d["qualificado_artigo"] == True].copy()
d["v"] = d["variacao_2033_final_pct"].astype(float)
d = d.sort_values("v", ascending=False).reset_index(drop=True)
n = len(d)
ganham, perdem = int((d.v > 0).sum()), int((d.v < 0).sum())

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "text.color": INK,
                     "axes.edgecolor": INK2, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
fig, ax = plt.subplots(figsize=(6.5, 3.6), dpi=300)   # 16,5 cm x 9,1 cm: largura útil do Word
x = range(n)
cores = [AZUL if v > 0 else VERMELHO for v in d.v]
ax.bar(x, d.v.clip(upper=YMAX), width=0.82, color=cores, linewidth=0, zorder=3)
ax.axhline(0, color=INK2, linewidth=0.8, zorder=4)
ax.set_ylim(YMIN, YMAX); ax.set_xlim(-2, n + 1)
ax.grid(axis="y", color=GRADE, linewidth=0.6, zorder=0)
ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.spines["left"].set_color(GRADE); ax.spines["bottom"].set_visible(False)
ax.set_xticks([])
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pt(v, 0, sinal=v != 0)))
ax.set_ylabel("Variação da receita municipal em 2033 (%)")
ax.set_xlabel(f"{n} municípios paranaenses, ordenados do maior ganho à maior perda", labelpad=4)

# rótulos diretos nos extremos (nomes com a variação), sem rótulo em todas as barras
kw = dict(fontsize=7, color=INK, va="center", zorder=5)
seta = dict(arrowstyle="-", color=INK2, linewidth=0.5, shrinkA=0, shrinkB=1)
topo = d.head(N_ROT)
for i, r in topo.iterrows():
    y_txt = 31 - i * 4.6
    cortada = r.v > YMAX
    alvo = min(r.v, YMAX)
    ax.annotate(f"{r.municipio} ({pt(r.v, 1, True)}%)" + (" ↑" if cortada else ""),
                xy=(i, alvo - (1 if cortada else 0)), xytext=(i + 9, y_txt), arrowprops=seta, ha="left", **kw)
fim = d.tail(N_ROT)   # da 5ª pior à pior; o pior fica no rótulo mais baixo, sem cruzar linhas
for k, (i, r) in enumerate(fim.iterrows()):
    ax.annotate(f"{r.municipio} ({pt(r.v, 1, True)}%)", xy=(i - 0.4, r.v), xytext=(i - 10, -14.0 - k * 3.6),
                arrowprops=seta, ha="right", **kw)

leg = ax.legend(handles=[Patch(color=AZUL, label=f"Ganham ({ganham} municípios)"),
                         Patch(color=VERMELHO, label=f"Perdem ({perdem} municípios)")],
                loc="upper right", frameon=False, fontsize=7.5, handlelength=1.0, handleheight=1.0, bbox_to_anchor=(1.0, 0.72))
mediana = d.v.median()
im = n // 2
ax.annotate(f"Mediana: {pt(mediana, 1, True)}%", xy=(im, mediana - 0.3), xytext=(im - 14, -9.5), fontsize=7, color=INK2,
            ha="center", va="center", arrowprops=dict(arrowstyle="-", color=INK2, linewidth=0.5, shrinkA=0, shrinkB=0))
fig.tight_layout(pad=0.6)
fig.savefig(OUT / "grafico-variacao-2033-pr.png", dpi=300, facecolor="white")
fig.savefig(OUT / "grafico-variacao-2033-pr.svg", facecolor="white")
print(n, ganham, perdem, round(mediana, 2))
