# Parte 1: tabelas do artigo, direto do repositório
import sys,json,re,copy
sys.path.insert(0,'/tmp/claude-0/-home-user-site-eduardo/81c38a17-983b-5e8a-a2ce-12db2b4f5b48/scratchpad')
from art_data import *
from docx.enum.text import WD_COLOR_INDEX
S='/tmp/claude-0/-home-user-site-eduardo/81c38a17-983b-5e8a-a2ce-12db2b4f5b48/scratchpad/'
doc=docx.Document(S+'artigo_pre_v3.docx');T=doc.tables;LOG=[]
def num(s):
    s=s.replace('\xa0','').replace('R$','').replace(' bi','').replace(' mi','').replace('bi','').strip().replace('−','-').replace('%','').replace('+','')
    if re.fullmatch(r'-?\d{1,3}(\.\d{3})+',s): s=s.replace('.','')
    return float(s.replace(',','.'))
def fmt(x,d=1,sign=False,pct=False):
    s=f"{abs(x):,.{d}f}".replace(',','X').replace('.',',').replace('X','.')
    if round(x,d)<0: s='−'+s
    elif sign: s='+'+s
    return s+('%' if pct else '')
def setcell(cell,txt,tag=''):
    p=cell.paragraphs[0];rs=p.runs;old=cell.text.strip()
    if old==txt or not rs:return
    rs[0].text=txt
    for r in rs[1:]:r.text=''
    rs[0].font.highlight_color=WD_COLOR_INDEX.YELLOW;LOG.append((tag,old.replace('\n',' '),txt))
bi=lambda x:x/1e9
# T1
for row in T[1].rows[2:]:
    uf=row.cells[0].text.strip()
    if uf not in RES:continue
    r=RES[uf];setcell(row.cells[1],fmt(bi(r['pre_2025'])),f'T1 {uf} base')
    for j,y in enumerate(Y):
        pos,cf=r['pos_por_ano'][y],r['contrafactual_por_ano'][y]
        setcell(row.cells[2+j],fmt(bi(pos)),f'T1 {uf} rec {y}');setcell(row.cells[7+j],fmt(100*(pos/cf-1),2,sign=True),f'T1 {uf} var {y}')
# T2
r=RES['PR']
for row in T[2].rows[1:6]:
    y=row.cells[0].text.strip();pos,cf=r['pos_por_ano'][y],r['contrafactual_por_ano'][y]
    setcell(row.cells[1],fmt(bi(cf),2),f'T2 cf {y}');setcell(row.cells[2],fmt(bi(pos),2),f'T2 rec {y}')
    setcell(row.cells[3],fmt(100*(pos/cf-1),2,sign=True,pct=True),f'T2 var {y}');setcell(row.cells[4],fmt((pos-cf)/1e6,0,sign=True),f'T2 dif {y}')
# T3 (A.1) validação Ipea
for row in T[3].rows[2:]:
    uf=row.cells[0].text.strip()
    if uf not in RES:continue
    own25=bi(RES[uf]['pre_2025']);own33=bi(RES[uf]['pos_por_ano']['2033']);i=IPEA[uf]
    setcell(row.cells[2],fmt(own25),f'T3 {uf} own25');setcell(row.cells[3],fmt(i[0]),f'T3 {uf} ipea25')
    setcell(row.cells[4],fmt(100*(i[0]/own25-1),1,sign=True,pct=True),f'T3 {uf} d25')
    setcell(row.cells[5],fmt(own33),f'T3 {uf} own33');setcell(row.cells[6],fmt(i[5]),f'T3 {uf} ipea33')
    setcell(row.cells[7],fmt(100*(i[5]/own33-1),1,sign=True,pct=True),f'T3 {uf} d33')
# T4 (A.2) com linha de 2026 estimado
import copy as _cp
Yh=[str(y) for y in range(2019,2026)]
hist=PE['PR']['historico_por_ano']
base={y:sum(e['historico_por_ano'][y]['icms_reais_2025']-e['historico_por_ano'][y]['outras_deducoes_reais_2025']+e['historico_por_ano'][y]['iss_reais_2025']+e['historico_por_ano'][y]['fecop_reais_2025'] for e in PE.values()) for y in Yh}
refaj=[bi(hist[y]['estado_reais_2025']) for y in Yh]
est=PE['PR']['estimativa_2026']
for k,row in enumerate(T[4].rows[1:8]):
    setcell(row.cells[7],fmt(refaj[k],2),f'T4 ref ajustada {Yh[k]}')
r25=T[4].rows[7]._tr;nr=_cp.deepcopy(r25);r25.addnext(nr)
rows=T[4].rows
r26=rows[8]
vals26=['2026 (est.)',fmt(bi(est['icms_reais_2025']),2),fmt(bi(est['outras_deducoes_reais_2025']),2),fmt(bi(est['cota_parte_reais_2025']),2),fmt(bi(est['fecop_reais_2025']),2),fmt(bi(est['estado_reais_2025']),2),'—',fmt(bi(est['estado_reais_2025']),2)]
for j,v in enumerate(vals26):setcell(r26.cells[j],v,f'T4 2026 c{j}')
refaj8=refaj+[bi(est['estado_reais_2025'])]
CF=J('data/coeficientes-uf.json');TB=bi(CF['total_br_2025'])
setcell(rows[9].cells[7],fmt(st.mean(refaj8),2),'T4 média ajustada')
setcell(rows[10].cells[7],fmt(TB,2),'T4 base nacional 2025')
shares=[100*hist[y]['estado_reais_2025']/base[y] for y in Yh]
HIST=PE['PR']['coef_cpt_estado_pct'];REF=shares[-1]
chk=100*st.mean(refaj8)/TB
print('check coef T4',chk,HIST)
setcell(rows[11].cells[7],fmt(HIST,4,pct=True),'T4 coeficiente')
# T5 (A.3) memória 2033
CA=0.002
pr33=[s for s in LP if s['ano']==2033][0]
cpt=PE['PR']['coef_cpt_estado_pct']/100;D=PHI['por_uf']['PR']['coef_estado_compras_pct']/100;REFf=PE['PR']['coef_neutro_estado_pct']/100
A=bi(pr33['bolo_projetado']);assert abs(pr33['ca']-CA)<1e-12
h=A*0.9*cpt;dg=A*0.1*0.95*D;sub_=h+dg;ded=CA*sub_;rec_=sub_-ded;cf_=A*REFf
pos33=bi(r['pos_por_ano']['2033']);cf33=bi(r['contrafactual_por_ano']['2033'])
print('T5 checks',rec_,pos33,cf_,cf33)
assert abs(rec_-pos33)<0.01 and abs(cf_-cf33)<0.01
def toks(s):
    out=[]
    for m in re.finditer(r'(\d[\d.]*)(?:,(\d+))?|([×+\-−/])',s):
        if m.group(3):out.append(m.group(3))
        else:
            out.append(m.group(1))
            if m.group(2) is not None:out+= [',',m.group(2)]
    return out
MM='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
def setmath(cell,s,tag):
    ts=list(cell._tc.iter(MM+'t'));new=toks(s)
    assert len(ts)==len(new),(tag,[t.text for t in ts],new)
    old=''.join(t.text for t in ts)
    for t,n in zip(ts,new):t.text=n
    LOG.append((tag,old,s))
f4=lambda x:fmt(x,2);f3=lambda x:fmt(x,3)
d7=lambda x:fmt(x,7)
for row in T[5].rows:
    k=row.cells[0].text.strip();v=row.cells[3];c2=row.cells[2]
    if k=='Base nacional de referência':setcell(v,'R$\xa0'+fmt(A,2)+' bi','T5 base')
    elif k=='Participação de referência do Paraná':setcell(v,fmt(100*REFf,5,pct=True),'T5 ref')
    elif k=='Coeficiente histórico do Paraná':setcell(v,fmt(100*cpt,5,pct=True),'T5 hist')
    elif k=='Coeficiente estadual de destino':setcell(v,fmt(100*D,5,pct=True),'T5 destino')
    elif k=='Cenário sem reforma':
        setcell(v,'R$\xa0'+fmt(cf33,2)+' bi','T5 cf');setmath(c2,f'{fmt(A,2)} × {d7(REFf)}','T5 cf expr')
    elif k=='ICMS residual':setmath(c2,f'{fmt(A,2)} × 0 × {d7(REFf)}','T5 icms expr')
    elif k.startswith('IBS pelo histórico'):
        setcell(v,'R$\xa0'+fmt(h,2)+' bi','T5 hist bruto');setmath(c2,f'{fmt(A,2)} × 1 × 0,90 × {d7(cpt)}','T5 hist expr')
    elif k.startswith('IBS pelo destino'):
        setcell(v,'R$\xa0'+fmt(dg,2)+' bi','T5 destino bi');setmath(c2,f'{fmt(A,2)} × 1 × 0,10 × 0,95 × {d7(D)}','T5 dest expr')
    elif k.startswith('Subtotal'):
        setcell(v,'R$\xa0'+fmt(sub_,2)+' bi','T5 subtotal');setmath(c2,f'{f4(h)} + {f4(dg)}','T5 sub expr')
    elif k.startswith('Dedução'):
        setcell(v,'R$\xa0'+fmt(-ded,2)+' bi','T5 cgibs');setmath(c2,f'− 0,002 × {f3(sub_)}','T5 ded expr')
    elif k=='Receita com reforma':
        setcell(v,'R$\xa0'+fmt(pos33,2)+' bi','T5 receita');setmath(c2,f'{f3(sub_)} − {f3(ded)}','T5 rec expr')
    elif k.startswith('Variação ante'):
        setcell(v,fmt(100*(pos33/cf33-1),2,sign=True,pct=True),'T5 var');setmath(c2,f'{f3(pos33)} / {f3(cf33)} − 1','T5 var expr')
# T6 capitais
CAP={'AC':'1200401','AL':'2704302','AM':'1302603','AP':'1600303','BA':'2927408','CE':'2304400','ES':'3205309','GO':'5208707','MA':'2111300','MG':'3106200','MS':'5002704','MT':'5103403','PA':'1501402','PB':'2507507','PE':'2611606','PI':'2211001','PR':'4106902','RJ':'3304557','RN':'2408102','RO':'1100205','RR':'1400100','RS':'4314902','SC':'4205407','SE':'2800308','SP':'3550308','TO':'1721000'}
for row in T[6].rows[1:]:
    uf=row.cells[0].text.strip()
    if uf=='DF':
        e=PE['DF'];rr=RES['DF']
        setcell(row.cells[2],fmt(e['coef_cpt_estado_pct'],3,pct=True),'T6 DF hist');setcell(row.cells[3],fmt(e['coef_pleno_estado_pct'],3,pct=True),'T6 DF dest')
        cf,pos=rr['contrafactual_por_ano']['2033'],rr['pos_por_ano']['2033']
    elif uf in CAP:
        m=json.load(open(N+f'data/painel-municipios/{uf}.json'))['municipios'][CAP[uf]]
        setcell(row.cells[2],fmt(m['coef_cpt_pct'],3,pct=True),f'T6 {uf} hist');setcell(row.cells[3],fmt(m['coef_pleno_pct'],3,pct=True),f'T6 {uf} dest')
        if uf=='PR':
            a=CSV['Curitiba'];cf,pos=float(a['contrafactual_2033_final']),float(a['receita_2033_final'])
        else:cf,pos=m['contrafactual_por_ano']['2033'],m['pos_por_ano']['2033']
    else:continue
    setcell(row.cells[4],fmt(bi(cf),2),f'T6 {uf} cf');setcell(row.cells[5],fmt(bi(pos),2),f'T6 {uf} rec');setcell(row.cells[6],fmt(100*(pos/cf-1),1,sign=True,pct=True),f'T6 {uf} var')
# T8 (B.1) e T9 (B.2)
am,ag=SUM['amostra_artigo'],SUM['agregado_municipios_pr']['2033']
acc=sum(SUM['seguro_receita'][y]['repasse_pr'] for y in Y)/1e6
ART_AUD_SEG=471.6;ART_DCA_SEG=502.2;ART_DCA_AGG=-2.13
for row in T[8].rows[1:]:
    k=row.cells[0].text.strip()
    if k.startswith('Municípios na amostra'):
        setcell(row.cells[1],fmt(am['n'],0),'T8 n');setcell(row.cells[2],fmt(am['n'],0),'T8 n')
    elif k.startswith('Resultado negativo'):
        setcell(row.cells[1],fmt(am['metodo_original']['negativos'],0),'T8 neg DCA');setcell(row.cells[2],fmt(am['metodo_auditado']['negativos'],0),'T8 neg aud')
    elif k.startswith('Resultado positivo'):
        setcell(row.cells[1],fmt(am['metodo_original']['positivos'],0),'T8 pos DCA');setcell(row.cells[2],fmt(am['metodo_auditado']['positivos'],0),'T8 pos aud')
    elif k.startswith('Mediana'):
        setcell(row.cells[1],fmt(am['metodo_original']['mediana_pct'],2,pct=True),'T8 med DCA');setcell(row.cells[2],fmt(am['metodo_auditado']['mediana_pct'],2,pct=True),'T8 med aud')
    elif k.startswith('Repasse municipal'):
        setcell(row.cells[1],'R$\xa0'+fmt(ART_DCA_SEG*acc/ART_AUD_SEG,1)+' mi','T8 seguro DCA (estimado)');setcell(row.cells[2],'R$\xa0'+fmt(acc,1)+' mi','T8 seguro aud')
    elif k.startswith('Variação agregada'):
        # DCA: valor do artigo + efeito da nova metodologia (ponderado pelo contrafactual)
        setcell(row.cells[2],fmt(ag['variacao_pct'],2,pct=True),'T8 agg aud')
        setcell(row.cells[1],fmt(ART_DCA_AGG+(ag['variacao_pct']-(-4.29)),2,pct=True),'T8 agg DCA (estimado)')
for row in T[9].rows[1:]:
    m=row.cells[0].text.strip()
    if m not in CSV:print('T9 sem',m);continue
    dca=float(CSV[m]['variacao_2033_metodo_original_pct']);aud=float(CSV[m]['variacao_2033_final_pct'])
    setcell(row.cells[1],fmt(dca,1,sign=True,pct=True),f'T9 {m} dca');setcell(row.cells[2],fmt(aud,1,sign=True,pct=True),f'T9 {m} aud');setcell(row.cells[3],fmt(aud-dca,1,sign=True),f'T9 {m} pp')
# T10
Q={m:float(x['variacao_2033_portal_sem_pit_pct']) for m,x in CSV.items() if x['qualificado_artigo']=='True' and x['variacao_2033_portal_sem_pit_pct'] not in('','None')}
perd=sorted(Q,key=lambda m:Q[m])[:20];gan=sorted(Q,key=lambda m:-Q[m])[:20]
for i,row in enumerate(T[10].rows[2:]):
    setcell(row.cells[0],perd[i],f'T10 p{i}');setcell(row.cells[1],fmt(Q[perd[i]],1,sign=True,pct=True),f'T10 pv{i}')
    setcell(row.cells[2],gan[i],f'T10 g{i}');setcell(row.cells[3],fmt(Q[gan[i]],1,sign=True,pct=True),f'T10 gv{i}')
# T11
for row in T[11].rows[1:6]:
    y=row.cells[0].text.strip();s=SUM['seguro_receita'][y]
    setcell(row.cells[1],fmt(bi(s['pool']),2),f'T11 pool {y}');setcell(row.cells[2],fmt(100*s['nivel'],3,pct=True),f'T11 nivel {y}')
    setcell(row.cells[3],fmt(s['beneficiarios_nacional'],0),f'T11 benef {y}');setcell(row.cells[4],fmt(s['beneficiarios_pr'],0),f'T11 pr {y}');setcell(row.cells[5],fmt(s['repasse_pr']/1e6,1),f'T11 rep {y}')
tot=T[11].rows[6];setcell(tot.cells[1],fmt(sum(bi(SUM['seguro_receita'][y]['pool']) for y in Y),2),'T11 pool tot');setcell(tot.cells[5],fmt(acc,1),'T11 total')
# T12
def tab(root):
    t=docx.Document(root+'data/auditoria-pr-validacao/tabelas-artigo/tabela-unica-dispersao-percapita-pr.docx').tables[0];o={}
    for r_ in t.rows[2:]:
        c=[x.text.strip().replace('\n',' ') for x in r_.cells];o[re.sub(r'^\d+\.\s*','',c[0])]=c
    return o
tn=tab(N)
for row in T[12].rows[1:]:
    nm=row.cells[0].text.strip()
    if nm.startswith('Razão') or nm.startswith('Índice'):
        key=next(k for k in tn if k.startswith(nm.split(' –')[0].split('.')[0][:6]));d=3 if nm.startswith('Índice') else 1
        for j in(2,3,4,5,6):setcell(row.cells[j],fmt(num(tn[key][j]),d),f'T12 {nm} c{j}')
        continue
    key=next((k for k in tn if k==nm or k.startswith(nm)),None)
    if not key:print('sem',nm);continue
    for j in(2,3,4,5,6):setcell(row.cells[j],fmt(num(tn[key][j]),0),f'T12 {nm} c{j}')
    setcell(row.cells[7],fmt(100*(num(tn[key][6])/num(tn[key][2])-1),0,sign=True,pct=True),f'T12 {nm} var')
json.dump(LOG,open(S+'log_t_v3.json','w'),ensure_ascii=False)
doc.save(S+'art_v3_p1.docx')
print(len(LOG),'| REF',REF,'HIST',HIST,'D',100*D)
