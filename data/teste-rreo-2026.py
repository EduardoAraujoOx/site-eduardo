#!/usr/bin/env python3
"""
Backtest do tratamento de 2026 com o RREO municipal (Anexo 03, SICONFI): em 2024 e em 2025, qual regra prevê melhor o ano fechado
a partir do que se observa até agosto?

  A  repetir o ano anterior (o que se fazia com o ISS)
  B  jan-ago do ano + set-dez do ano anterior (o "total dos últimos 12 meses" do 4º bimestre)
  C  ano anterior x crescimento observado de jan-ago

O erro é medido na participação do município no total do conjunto (previsto x real), o que compensa o crescimento agregado.
Resultado (mediana do erro na participação): ISS, B (6,4-6,9%) melhor que C (7,4-7,8%) e que A (13,9%); cota-parte, C (0,9-1,8%) melhor que
B (2,4-2,8%) e que A (6,2-8,5%); mesmo onde o crescimento é extremo (jan-ago acima de 1,8x) C erra 1,4-1,6% no nível do ano.
Adotado em data/cpt2026.py: ISS por B, cota-parte por C.
Entradas: data/rreo-municipios/{2023,2024,2025}-p6.json (data/collect-rreo-municipios.py). Executar a partir da raiz.
"""
import json
import statistics as st

def carrega(a): return json.load(open(f'data/rreo-municipios/{a}-p6.json'))
def ok(v): return bool(v and v.get('iss') and v.get('cota') and None not in v['iss']['meses'] and None not in v['cota']['meses'])
def teste(ant,atual,rot):
    A=carrega(ant); B=carrega(atual)
    lista={'iss':[],'cota':[],'total':[]}
    for c in B:
        a,b=A.get(c),B.get(c)
        if not(ok(a) and ok(b)): continue
        row={}; bom=True
        for k in ['iss','cota']:
            ma,mb=a[k]['meses'],b[k]['meses']
            tot_a=sum(ma); ja_a=sum(ma[:8]); ja_b=sum(mb[:8]); sd_a=sum(ma[8:])
            if min(tot_a,ja_a,ja_b)<=0 or sum(mb)<=0: bom=False;break
            row[k]={'real':sum(mb),'A':tot_a,'B':ja_b+sd_a,'C':tot_a*ja_b/ja_a}
        if not bom: continue
        row['total']={m:row['iss'][m]+row['cota'][m] for m in row['iss']}
        for k in lista: lista[k].append((c,row[k]))
    print(f'\n##### Teste {rot}: {len(lista["total"])} municípios')
    def er(l,f):
        vals=[(f(x),x['real']) for _,x in l]
        sp=sum(v for v,_ in vals); sr=sum(r for _,r in vals)
        e=sorted(abs((v/sp)/(r/sr)-1) for v,r in vals); w=sum(abs((v/sp)/(r/sr)-1)*r for v,r in vals)/sr
        return st.median(e),e[int(len(e)*.9)],w
    for k,tit in [('iss','ISS'),('cota','COTA-PARTE'),('total','ISS+COTA')]:
        print(tit)
        for m,n in [('A','repetir ano anterior'),('B','observado até ago + resto do ano anterior'),('C','ano anterior × crescimento jan–ago')]:
            a,b,c=er(lista[k],lambda x:x[m]); print(f'   {m} {n:44s} {a*100:5.1f}% | p90 {b*100:5.1f}% | pond. {c*100:4.1f}%')
    iss=dict(lista['iss']); cota=dict(lista['cota'])
    print('Híbrido ISS=B + cota=C:')
    L=[(c,{'real':iss[c]['real']+cota[c]['real'],'H':iss[c]['B']+cota[c]['C']}) for c in iss]
    a,b,c=er(L,lambda x:x['H']); print(f'   mediana {a*100:.1f}% | p90 {b*100:.1f}% | ponderado {c*100:.1f}%')
    # extremos em B do ISS: fallback para a média da UF fora de [lo,hi]
    for lo,hi in [(0.4,2.5),(0.5,2.0),(0.33,3)]:
        def fiss(x):
            g=x['B']/x['A']; return x['B'] if lo<=g<=hi else x['A']*1.0
        L=[(c,{'real':iss[c]['real']+cota[c]['real'],'H':fiss(iss[c])+cota[c]['C']}) for c in iss]
        a,b,c=er(L,lambda x:x['H']); print(f'   ISS=B com recuo p/ ano anterior fora de [{lo},{hi}] + cota=C: mediana {a*100:.1f}% | p90 {b*100:.1f}% | pond. {c*100:.1f}%')
teste('2023','2024','2024 (previsto com 2023 e jan–ago/2024)')
teste('2024','2025','2025 (previsto com 2024 e jan–ago/2025)')
