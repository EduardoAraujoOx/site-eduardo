#!/usr/bin/env python3
from __future__ import annotations
import io, zipfile, requests
from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

ROOT=Path(__file__).resolve().parent.parent
CSV=ROOT/"data/auditoria-pr-validacao/municipios-pr-final-auditado-latest.csv"
OUT=ROOT/"artifacts"
OUT.mkdir(exist_ok=True)
URL="https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/UFs/PR/PR_Municipios_2024.zip"

r=requests.get(URL,timeout=120); r.raise_for_status()
z=zipfile.ZipFile(io.BytesIO(r.content))
tmp=OUT/"_pr_shape"
tmp.mkdir(exist_ok=True)
z.extractall(tmp)
shp=next(tmp.glob("*.shp"))
gdf=gpd.read_file(shp)
df=pd.read_csv(CSV,encoding="utf-8-sig",dtype={"codigo_ibge":str})
df["var"]=pd.to_numeric(df["variacao_2033_final_pct"],errors="coerce")
code_col="CD_MUN" if "CD_MUN" in gdf.columns else "CD_GEOCMU"
gdf[code_col]=gdf[code_col].astype(str)
m=gdf.merge(df[["codigo_ibge","var"]],left_on=code_col,right_on="codigo_ibge",how="left")

fig,ax=plt.subplots(figsize=(6.3,7.1))
norm=TwoSlopeNorm(vmin=-30,vcenter=0,vmax=30)
m.plot(column="var",cmap="RdYlGn",norm=norm,linewidth=0.15,edgecolor="white",ax=ax,missing_kwds={"color":"lightgrey"})
ax.set_axis_off()
sm=plt.cm.ScalarMappable(cmap="RdYlGn",norm=norm); sm.set_array([])
cb=fig.colorbar(sm,ax=ax,fraction=0.036,pad=0.01)
cb.set_label("Variação da receita em 2033 (%)",fontsize=9)
cb.ax.tick_params(labelsize=8)
ax.set_title("Municípios do Paraná: variação da receita em 2033",fontsize=12,pad=8)
fig.text(0.5,0.02,"Nota: valores inferiores a -30% ou superiores a +30% são representados nos extremos da escala.",ha="center",fontsize=7.5)
fig.tight_layout(rect=[0,0.04,1,1])
fig.savefig(OUT/"mapa_variacao_municipal_pr_2033.pdf",bbox_inches="tight")
fig.savefig(OUT/"mapa_variacao_municipal_pr_2033.png",dpi=250,bbox_inches="tight")
