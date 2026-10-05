#!/usr/bin/env python3
"""
Backtest (rolling origin) de modelos alternativos para o ICMS real de cada UF (20 UFs sem quebras da DCA, 2013-2025):
A estrutura adotada (participação de 2025 x bolo nacional, com deriva da participação), B série própria (passeio com
deriva), C série própria com encolhimento para a média das UFs, D regressão no crescimento do PIB com encolhimento,
E modelo comum. Mede cobertura de 80% e 90%, CRPS e desvio de z. Não altera nenhum resultado publicado.
Saída: data/sensibilidade-modelos-icms.json
"""
import json,sys,math
import numpy as np
sys.path.insert(0,'data')
from fundos_art115b import fold
r=fold(json.load(open('data/reforma-tributaria.json')))
icms=dict(r['dca_icms_por_uf']); icms.update(json.load(open('data/icms-dca-2013-2018.json'))); out=r['dca_icms_outras_deducoes_por_uf']
dfl=json.load(open('data/macro-parametros.json'))['deflator_ipca_para_2025']
g=json.load(open('data/sidra-pib-crescimento-brasil.json'))['crescimento_real_pct']
hist=json.load(open('data/ibs-projecao-nacional.json'))['historico']
EX={'DF','GO','MS','MT','TO','RO','CE'}
ufs=[u for u in sorted(icms['2025']) if u not in EX]
Y=list(range(2013,2026))
L={u:np.log([icms[str(y)][u]*dfl[str(y)] for y in Y]) for u in ufs}
D={u:np.diff(L[u]) for u in ufs}          # crescimentos 2014..2025 (12)
nat=np.diff(np.log([x['bolo_real_2025'] for x in hist]))   # idem
G=np.array([g.get(str(y),np.nan) for y in range(2014,2026)])/100   # PIB até 2023
def cr(y,sig):
    z=y/sig; Phi=0.5*(1+math.erf(z/math.sqrt(2))); return sig*(z*(2*Phi-1)+2*math.exp(-0.5*z*z)/math.sqrt(2*math.pi)-1/math.sqrt(math.pi))
res={}
def reg(m,y,sg): res.setdefault(m,[]).append((y/sg,cr(y,sg)))
for T in range(6,11):   # nº de crescimentos observados
    mun=nat[:T].mean(); sgn=nat[:T].std(ddof=1)
    # deriva de participação: sd de h anos das participações (treino)
    Ls=np.array([L[u][:T+1] for u in ufs]); shr=Ls-np.log(np.exp(Ls).sum(0))[None,:]
    def sdshare(h):
        d=np.array([ (shr[:,t+h]-shr[:,t])-(shr[:,t+h]-shr[:,t]).mean() for t in range(T+1-h)]); return d.std(ddof=1)
    pm=np.mean([D[u][:T].mean() for u in ufs]); ps=np.mean([D[u][:T].std(ddof=1) for u in ufs])
    ok=~np.isnan(G[:T]); gm=np.nanmean(G[:T]); gs=np.nanstd(G[:T],ddof=1)
    # regressão pooled de PIB
    bs={}
    for u in ufs:
        x=G[:T][ok]; yv=D[u][:T][ok]
        if len(x)>=4:
            b,a=np.polyfit(x,yv,1); e=yv-(a+b*x); bs[u]=(a,b,e.std(ddof=2) if len(x)>2 else ps)
    bp=np.mean([v[1] for v in bs.values()]); sep=np.mean([v[2] for v in bs.values()])
    for u in ufs:
        for h in range(1,min(4,12-T)+1):
            real=D[u][T:T+h].sum()
            # A: estrutura atual (participação x bolo nacional)
            sdA=math.sqrt(sgn**2*h+ (sdshare(h) if T+1-h>=3 else ps*math.sqrt(h))**2)
            reg('A_participacao_x_bolo',real-h*mun,sdA)
            # B: própria série (passeio com deriva)
            mu=D[u][:T].mean(); sd=D[u][:T].std(ddof=1)
            reg('B_serie_propria',real-h*mu,sd*math.sqrt(h))
            # C: própria com encolhimento 50% (média e desvio)
            mu_c=0.5*mu+0.5*pm; sd_c=math.sqrt(0.5*sd**2+0.5*ps**2)
            reg('C_serie_propria_encolhida',real-h*mu_c,sd_c*math.sqrt(h))
            # D: regressão no PIB (beta encolhido), PIB incerto
            if u in bs:
                a,b,se=bs[u]; bsh=0.5*b+0.5*bp; ash=0.5*a+0.5*np.mean([v[0] for v in bs.values()]); seh=math.sqrt(0.5*se**2+0.5*sep**2)
                mean=h*(ash+bsh*gm); sdD=math.sqrt(bsh**2*gs**2*h+seh**2*h)
                reg('D_regressao_no_PIB',real-mean,sdD)
            # E: comum
            reg('E_comum',real-h*pm,ps*math.sqrt(h))
saida={}
print('modelo                         cob80  cob90   CRPS(%)  sd(z)  n')
for m,v in res.items():
    z=np.array([a for a,_ in v]); c=np.mean([b for _,b in v])*100
    saida[m]={'cobertura80':round(float(np.mean(abs(z)<1.2816)),2),'cobertura90':round(float(np.mean(abs(z)<1.645)),2),'CRPS_pct':round(float(c),3),'sd_z':round(float(z.std()),2),'n':len(z)}
    print(f'{m:30s} {np.mean(abs(z)<1.2816):.2f}   {np.mean(abs(z)<1.645):.2f}   {c:6.3f}   {z.std():.2f}  {len(z)}')

import pathlib
pathlib.Path('data/sensibilidade-modelos-icms.json').write_text(json.dumps({'_meta':'Backtest de modelos para o ICMS real por UF; origens com 6 a 10 crescimentos anuais observados, horizontes de 1 a 4 anos','resultados':saida},ensure_ascii=False,indent=1),encoding='utf-8')
