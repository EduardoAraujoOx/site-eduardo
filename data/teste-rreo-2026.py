#!/usr/bin/env python3
"""
Backtest do tratamento de 2026 com o RREO (Anexo 03, por município): para o ano de 2025, qual regra prevê melhor o ano fechado?

  A  repetir o ano anterior (hoje, no ISS)
  B  jan-ago do ano + set-dez do ano anterior (o total de 12 meses do 4º bimestre)
  C  ano anterior x crescimento observado de jan-ago

O erro é medido na participação do município no total do conjunto (previsto x real), o que compensa o crescimento agregado.
Entradas: data/rreo-municipios/2024-p6.json, 2025-p4.json e 2025-p6.json (data/collect-rreo-municipios.py). Executar a partir da raiz.
"""
d24=json.load(open('data/rreo-municipios/2024-p6.json'))   # jan-dez/2024 (meses: <MR-11>=jan ... <MR>=dez)
d25a=json.load(open('data/rreo-municipios/2025-p4.json'))  # set/24..ago/25
d25=json.load(open('data/rreo-municipios/2025-p6.json'))   # jan-dez/2025
def ok(v): return bool(v and v.get('iss') and v.get('cota') and None not in v['iss']['meses'] and None not in v['cota']['meses'])
def serie(v,k): return v[k]['meses']
res={}
for k in ['iss','cota','total']:
    res[k]=[]
n=0
for c in d25:
    a,b,f=d24.get(c),d25a.get(c),d25.get(c)
    if not(ok(a) and ok(b) and ok(f)): continue
    n+=1
    row={}
    for k in ['iss','cota']:
        m24=serie(a,k); m25=serie(f,k)
        jan_ago24=sum(m24[:8]); set_dez24=sum(m24[8:]); tot24=sum(m24)
        jan_ago25=sum(m25[:8]); set_dez25=sum(m25[8:]); tot25=sum(m25)
        if min(tot24,tot25,jan_ago24)<=0: row=None; break
        row[k]={'real':tot25,
                'A_repete':tot24,
                'B_carrega':jan_ago25+set_dez24,
                'C_cresce':tot24*(jan_ago25/jan_ago24)}
    if row is None: continue
    row['total']={m:row['iss'][m]+row['cota'][m] for m in row['iss']}
    for k in res: res[k].append((c,row[k]))
print('municípios com 2024, 2025 e a janela completos:',len(res['total']))
def erro_share(lista,metodo,pesos=None):
    # participação de cada município no total do conjunto: previsto x real (compensa o crescimento agregado)
    sp=sum(x[1][metodo] for x in lista); sr=sum(x[1]['real'] for x in lista)
    erros=[]; pond=0; wsum=0
    for c,x in lista:
        p=x[metodo]/sp; r=x['real']/sr
        e=abs(p/r-1); erros.append(e); pond+=e*x['real']; wsum+=x['real']
    erros.sort()
    return st.median(erros),erros[int(len(erros)*0.9)],pond/wsum
nomes={'A_repete':'A  repetir o ano anterior (hoje, no ISS)','B_carrega':'B  jan–ago observado + set–dez do ano anterior','C_cresce':'C  ano anterior × crescimento jan–ago'}
for k,tit in [('iss','ISS'),('cota','COTA-PARTE DO ICMS'),('total','ISS + COTA-PARTE')]:
    print('\n',tit,'— erro na participação do município (mediana | percentil 90 | ponderado pela receita)')
    for m in nomes:
        a,b,c=erro_share(res[k],m); print(f'  {nomes[m]:48s} {a*100:5.1f}% | {b*100:5.1f}% | {c*100:5.1f}%')
# calibragem do crescimento aplicado (quanto do crescimento jan-ago se mantém em set-dez?)
import math
xs=[];ys=[]
for c,x in res['total']:
    pass

print('\n=== híbridos ===')
iss=dict(res['iss']); cota=dict(res['cota'])
def lista_hibrida(fiss,fcota):
    out=[]
    for c in iss:
        x={'real':iss[c]['real']+cota[c]['real'],'H':fiss(iss[c])+fcota(cota[c])}
        out.append((c,x))
    return out
def er(lista):
    sp=sum(x['H'] for _,x in lista); sr=sum(x['real'] for _,x in lista)
    e=sorted(abs((x['H']/sp)/(x['real']/sr)-1) for _,x in lista)
    pond=sum(abs((x['H']/sp)/(x['real']/sr)-1)*x['real'] for _,x in lista)/sr
    return st.median(e),e[int(len(e)*.9)],pond
meio=lambda x:(x['B_carrega']+x['C_cresce'])/2
for nome,fi,fc in [('ISS B + cota-parte C',lambda x:x['B_carrega'],lambda x:x['C_cresce']),
                   ('ISS média(B,C) + cota-parte C',meio,lambda x:x['C_cresce']),
                   ('ISS C + cota-parte C',lambda x:x['C_cresce'],lambda x:x['C_cresce']),
                   ('ISS B + cota-parte B',lambda x:x['B_carrega'],lambda x:x['B_carrega'])]:
    a,b,c=er(lista_hibrida(fi,fc)); print(f'  {nome:34s} mediana {a*100:4.1f}% | p90 {b*100:4.1f}% | ponderado {c*100:4.1f}%')
# ISS: efeito de limitar crescimentos extremos
for lim in [None,2.0,1.5]:
    def fiss(x,lim=lim):
        g=x['C_cresce']/x['A_repete']
        if lim: g=max(1/lim,min(lim,g))
        return x['A_repete']*g
    a,b,c=er(lista_hibrida(fiss,lambda x:x['C_cresce'])); print(f'  ISS C com limite {lim}: mediana {a*100:4.1f}% | p90 {b*100:4.1f}% | ponderado {c*100:4.1f}%')
