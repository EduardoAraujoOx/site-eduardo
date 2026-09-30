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


# Minimal SVG for direct use in the article. Geometry is simplified only for display.
mg=m.to_crs(4674).copy()
mg["geometry"]=mg.geometry.simplify(0.035,preserve_topology=True)
minx,miny,maxx,maxy=mg.total_bounds
W,H=760,540
pad=20
sx=(W-2*pad)/(maxx-minx)
sy=(H-2*pad)/(maxy-miny)
scale=min(sx,sy)
ox=(W-(maxx-minx)*scale)/2
oy=(H-(maxy-miny)*scale)/2
def col(v):
    if pd.isna(v): return "#d9d9d9"
    if v <= -15: return "#b2182b"
    if v <= -5: return "#ef8a62"
    if v < 0: return "#fddbc7"
    if v < 5: return "#d9f0d3"
    if v < 15: return "#7fbf7b"
    return "#1b7837"
def ring_path(coords):
    pts=[]
    for x,y in coords:
        X=ox+(x-minx)*scale
        Y=H-(oy+(y-miny)*scale)
        pts.append((X,Y))
    if not pts: return ""
    return "M"+"L".join(f"{x:.1f},{y:.1f}" for x,y in pts)+"Z"
def geom_paths(g):
    if g is None or g.is_empty: return []
    if g.geom_type=="Polygon": return [ring_path(g.exterior.coords)]
    if g.geom_type=="MultiPolygon": return [ring_path(p.exterior.coords) for p in g.geoms]
    return []
legend=[
    ("#b2182b","≤ -15%"),
    ("#ef8a62","-15% a -5%"),
    ("#fddbc7","-5% a 0"),
    ("#d9f0d3","0 a +5%"),
    ("#7fbf7b","+5% a +15%"),
    ("#1b7837","> +15%"),
]
parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H+55}" viewBox="0 0 {W} {H+55}">']
parts.append('<rect width="100%" height="100%" fill="white"/>')
parts.append('<text x="20" y="20" font-family="Arial" font-size="16" font-weight="bold">Municípios do Paraná: variação da receita em 2033</text>')
for _,r in mg.iterrows():
    fill=col(r["var"])
    for p in geom_paths(r.geometry):
        parts.append(f'<path d="{p}" fill="{fill}" stroke="#ffffff" stroke-width="0.35"/>')
lx=28; ly=H+18
for color,label in legend:
    parts.append(f'<rect x="{lx}" y="{ly-10}" width="16" height="10" fill="{color}" stroke="#777" stroke-width="0.3"/>')
    parts.append(f'<text x="{lx+21}" y="{ly-1}" font-family="Arial" font-size="10">{label}</text>')
    lx += 112
parts.append('</svg>')
(OUT/"mapa_variacao_municipal_pr_2033.svg").write_text("".join(parts),encoding="utf-8")
