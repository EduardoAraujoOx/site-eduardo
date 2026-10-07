import sys,json,re,copy,io,csv,statistics as st
S='/tmp/claude-0/-home-user-site-eduardo/81c38a17-983b-5e8a-a2ce-12db2b4f5b48/scratchpad/'
sys.path.insert(0,S)
src=open(S+'refresh_v3_p1.py').read()
head=src[:src.index('# T1')].replace('artigo_pre_v3.docx','artigo_pre_v5.docx')
def sl(a,b):return src[src.index(a):src.index(b)]
exec(head)                       # doc, T, LOG, fmt, num, setcell(realce), bi, RES, PE, ...
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from PIL import Image
import subprocess
# ---- tabelas dependentes do Seguro e dos municípios
exec(sl('# T1','# T2'))
exec(sl('# T3 (A.1)','# T4 (A.2)'))
CAP={'AC':'1200401','AL':'2704302','AM':'1302603','AP':'1600303','BA':'2927408','CE':'2304400','ES':'3205309','GO':'5208707','MA':'2111300','MG':'3106200','MS':'5002704','MT':'5103403','PA':'1501402','PB':'2507507','PE':'2611606','PI':'2211001','PR':'4106902','RJ':'3304557','RN':'2408102','RO':'1100205','RR':'1400100','RS':'4314902','SC':'4205407','SE':'2800308','SP':'3550308','TO':'1721000'}
exec(sl('# T6 capitais','# T8 (B.1) e T9 (B.2)'))
exec(src[src.index('for row in T[9].rows[1:]:'):src.index('# T10')])
acc=sum(SUM['seguro_receita'][y]['repasse_pr'] for y in Y)/1e6
exec(sl('# T11','# T12'))
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
# limpa o realce das células tocadas (versão limpa)
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
# ------------------------------------------------------------------ dados
RT=json.load(open(N+'data/auditoria-pr-validacao/resumo-todos-municipios-pr.json'));Tt=RT['todos'];A=RT['amostra_principal_10mil_iss']
RD=json.load(open(N+'data/auditoria-pr-validacao/tabelas-artigo/resumo-tabela-unica.json'))
SENS=json.load(open(S+'sens_v5.json'))
CSVr=list(csv.DictReader(open(N+'data/auditoria-pr-validacao/municipios-pr-final-auditado-latest.csv',encoding='utf-8-sig')))
mi=lambda x:x/1e6
def norm(s):return s.replace('\xa0',' ')
def haspar(key):
    c=[p for p in doc.paragraphs if norm(p.text).startswith(norm(key))]
    assert len(c)==1,(key,len(c));return c[0]
def setpar(key,new):
    p=haspar(key);assert not p._p.findall('.//'+M+'oMath'),('math',key)
    p.runs[0].text=new
    for r in p.runs[1:]:r.text=''
def subre(key,pat,repl):
    p=haspar(key)
    for r in p.runs:
        if re.search(pat,r.text):
            r.text=re.sub(pat,repl,r.text);return True
    print('NÃO ENCONTRADO',key[:30],pat[:50]);return False
def clone_after(ref,text,prototype=None):
    proto=prototype or ref
    new=copy.deepcopy(proto._p);ref._p.addnext(new);p=Paragraph(new,ref._parent)
    p.runs[0].text=text
    for r in p.runs[1:]:r.text=''
    return p
def nota_set(p,texto):
    p.runs[2].text=texto
    for r in p.runs[3:]:r.text=''
def pct(x,d=1,sign=False):return fmt(x,d,sign=sign,pct=True)
# ---- números centrais
R_=RES['PR'];pos33=bi(R_['pos_por_ano']['2033']);cf33=bi(R_['contrafactual_por_ano']['2033']);var33=100*(pos33/cf33-1)
agm=SUM['agregado_municipios_pr'];m_pos,m_cf=bi(agm['2033']['receita_final']),bi(agm['2033']['contrafactual']);m_var=agm['2033']['variacao_pct']
m_acum=sum(agm[y]['contrafactual']-agm[y]['receita_final'] for y in Y)/1e9
tot_var=100*((R_['pos_por_ano']['2033']+agm['2033']['receita_final'])/(R_['contrafactual_por_ano']['2033']+agm['2033']['contrafactual'])-1)
seg=SUM['seguro_receita'];ben=[seg[y]['beneficiarios_nacional'] for y in Y];npr=[seg[y]['beneficiarios_pr'] for y in Y]
rep=sum(seg[y]['repasse_pr'] for y in Y)/1e6
perda_acum_perdedores=Tt['perda_acum_2029_2033_dos_que_perdem_2033']
aseg=json.load(open(N+'data/seguro-receita-repasses.json'))['anos']
am_pool={a:v['pool'] for a,v in aseg.items()}
am_rep={a:sum(e['repasse'] for e in v['entidades'] if e['nome']=='AM' and e['esfera']=='estado') for a,v in aseg.items()}
# ------------------------------------------------------------------ resumo, abstract, introdução
setpar('Este artigo estima os efeitos da reforma tributária do consumo sobre as receitas do Estado do Paraná e de seus municípios. A metodologia',
 f"Este artigo estima os efeitos da reforma tributária do consumo sobre as receitas do Estado do Paraná e de seus municípios. A metodologia aplica as regras de transição do ICMS e do ISS para o IBS e compara as receitas projetadas com um cenário contrafactual sem reforma. Os resultados indicam relativa neutralidade para o governo estadual: em 2033, a receita líquida da cota-parte municipal é projetada em R$ {fmt(pos33,1)} bilhões, {fmt(var33,1)}% acima do contrafactual. Entre os municípios, {Tt['perdem_2033']} apresentam perdas, que somam R$ {fmt(bi(perda_acum_perdedores),2)} bilhões entre 2029 e 2033. Os resultados ressaltam o papel do coeficiente de participação histórica na suavização dos efeitos iniciais da reforma e a relevância da qualidade das informações fiscais para a projeção das receitas subnacionais.")
setpar('This paper estimates the effects of Brazil',
 f"This paper estimates the effects of Brazil’s consumption tax reform on the revenues of the State of Paraná and its municipalities. The methodology applies the transition rules from ICMS and ISS to the IBS and compares projected revenues with a no-reform counterfactual. Results indicate relative neutrality for the state government: in 2033, revenue net of the municipal share is projected at BRL {fmt(pos33,1).replace(',','.')} billion, {fmt(var33,1).replace(',','.')}% above the counterfactual. Among municipalities, {Tt['perdem_2033']} record losses, which total BRL {fmt(bi(perda_acum_perdedores),2).replace(',','.')} billion over 2029–2033. The results highlight the role of the historical participation coefficient in smoothing the initial effects of the reform and the relevance of fiscal data quality for projecting subnational revenues.")
p=haspar('Este estudo estima os efeitos da transição para o IBS');setpar('Este estudo estima os efeitos da transição para o IBS',
 re.sub(r'perdas acumuladas de R\$ [\d,]+ bilhões',f"perdas acumuladas de R$ {fmt(bi(perda_acum_perdedores),2)} bilhões",re.sub(r'R\$ [\d,]+ bilhões em 2033, [\d,]+% acima',f"R$ {fmt(pos33,1)} bilhões em 2033, {fmt(var33,1)}% acima",p.text)))
# ------------------------------------------------------------------ metodologia 3.2
setpar('Para os estados, a receita de referência corresponde',
 "Para os estados, a receita de referência corresponde ao ICMS bruto, líquido das demais deduções registradas na DCA e da cota-parte municipal, acrescido do Fundo de Combate à Pobreza (FECOP) e das contribuições a fundos estaduais de que trata o art. 115, inciso I, alínea “b”, da Lei Complementar n.o 227/2026. Esta última categoria só é incorporada quando o valor pode ser verificado na DCA, o que hoje ocorre apenas com o Amazonas; Goiás, Mato Grosso e Rio de Janeiro permanecem pendentes de informação oficial. Para os municípios, somam-se o ISS e a cota-parte do ICMS, e o Distrito Federal, ente de esfera única, incorpora também o ISS. "
 "Como a lei inclui 2026 na média, mas o exercício só será fechado na DCA em 2027, esse ano entra estimado. Nos estados, o ICMS líquido e a cota-parte de 2025 são corrigidos pelo desempenho relativo de cada UF no RREO de janeiro a agosto de 2026, com renormalização que preserva o total. Nos municípios, a cota-parte segue o fator da UF e o ISS repete o valor de 2025, tratamento que apresentou o menor erro de previsão em todas as faixas de população entre 2022 e 2025. Nos testes com os estados, a estimativa errou em média 0,24% da participação, contra 0,45% ao repetir 2025 e 0,90% ao omitir 2026.")
setpar('No caso municipal, a série é submetida',
 "No caso municipal, a série é submetida a uma etapa de consistência antes do cálculo do coeficiente. A cota-parte do ICMS declarada pelos municípios é confrontada com os repasses brutos registrados pelo Estado do Paraná e reconciliada ao total estadual da DCA; o ISS permanece ancorado na DCA e somente é substituído quando uma divergência material é confirmada em segunda fonte oficial. Ausência de informação não é tratada como valor igual a zero: as 74 observações de ISS ausentes na DCA, de um total de 2.793, são imputadas a partir dos demais anos do próprio município (53 casos) ou recuperadas de versão anterior da base (21). O objetivo é preservar a lógica do coeficiente legal sem permitir que falhas de preenchimento ou de cobertura determinem artificialmente a participação histórica. O Anexo B documenta a comparação entre as fontes e seus efeitos sobre os resultados.")
# ------------------------------------------------------------------ Seguro-Receita 3.4
setpar('O Seguro-Receita atua sobre a parcela',
 "O Seguro-Receita atua sobre a parcela do IBS não distribuída pelo componente histórico, antes de sua repartição pelo destino. Nos termos do art. 132 do ADCT e dos arts. 110 e 117 da Lei Complementar n.o 227/2026, 5% dessa parcela é retida para compensar os entes com as menores razões entre dois valores: a média, nos doze meses anteriores, do IBS que cada ente apuraria pelo critério do destino, com as alíquotas de referência, e a respectiva receita média de referência ajustada. O numerador da razão é, portanto, o IBS total do ente pelo destino, e não apenas a fração já distribuída por esse critério. No horizonte analisado, a retenção corresponde a 0,10% da arrecadação nacional de referência em 2029 e alcança 0,50% em 2033.")
am29,am33=am_rep['2029'],am_rep['2033']
setpar('Na simulação, o fundo nacional',
 f"Na simulação, o fundo nacional cresce de R$ {fmt(seg['2029']['pool']/1e9,2)} bilhão em 2029 para R$ {fmt(seg['2033']['pool']/1e9,2)} bilhões em 2033, e o número de entes contemplados cai de {ben[0]} para {ben[-1]} à medida que o nível de equalização se eleva. Entre os estados, apenas o Amazonas é contemplado, resultado coerente com a simulação do Comsefaz, em que esse é o primeiro estado beneficiário. No Paraná, o governo estadual não recebe repasses no período, e {('entre %d e %d municípios são contemplados' % (min(npr),max(npr))) if min(npr)!=max(npr) else ('%d municípios são contemplados' % npr[0])} a cada ano. Após a auditoria dos dados municipais, os repasses aos municípios paranaenses somam aproximadamente R$ {fmt(rep,1)} milhões entre 2029 e 2033; o detalhamento anual é apresentado no Anexo C.")
setpar('Como a legislação opera mensalmente',
 "A simulação reproduz o procedimento previsto em lei: a distribuição é feita mês a mês, com média móvel de doze meses e, de 2029 a 2033, com a correção dos meses do ano anterior pela razão entre as alíquotas de referência (art. 117, § 2o), admitindo-se receita constante dentro de cada ano. A população usa a média de 2019 a 2026, com o Censo Demográfico de 2022 no ano de 2022 e a interpolação entre o Censo e a estimativa de 2024 em 2023, anos em que o IBGE não publica estimativa.")
# ------------------------------------------------------------------ 3.5: ano-base do contrafactual
pc=haspar('O cenário contrafactual mantém a participação de 2025')
clone_after(pc,"A escolha do último exercício fechado, 2025, como referência do cenário contrafactual tem justificativa institucional. As despesas dos entes são fixadas a partir de projeções de receita que, na prática, tomam o resultado realizado mais recente como ponto de partida, de modo que a participação observada em 2025 aproxima a expectativa com que as dotações seriam definidas na ausência de mudança de regras. O contrafactual, de participação constante, não pretende, portanto, prever a trajetória própria do ICMS de cada ente, mas isolar o efeito das novas regras de repartição sobre uma posição relativa conhecida no momento da decisão. Como o último ano pode refletir flutuações transitórias, a Seção 4.2.2 e o Anexo A examinam a sensibilidade dos resultados a bases alternativas, entre as quais a média histórica e a estimativa para 2026.",prototype=haspar('Para os estados, a receita de referência corresponde'))
# ------------------------------------------------------------------ 3.6 limitações
setpar('As projeções estão condicionadas',
 "As projeções estão condicionadas à disponibilidade e à qualidade das informações que formarão os parâmetros definitivos da transição. O coeficiente de participação deverá considerar 2019 a 2026, mas os dados fechados da DCA de 2026 ainda não estão disponíveis; por isso, 2026 entra como estimativa baseada no RREO, e o coeficiente deverá ser recalculado com o dado fechado. Além disso, o cálculo incorpora o FECOP e, entre as contribuições a fundos estaduais referidas no art. 115, inciso I, alínea “b”, da Lei Complementar n.o 227/2026, apenas as do Amazonas, as únicas verificáveis em base pública; as dos demais estados dependem de informação que a lei exige que eles prestem ao CGIBS. No Paraná, cada R$ 1 bilhão de contribuições elegíveis elevaria o coeficiente histórico estadual em cerca de 0,1 ponto percentual e a variação da receita de 2033 em cerca de 2 pontos percentuais. A incorporação do dado fechado de 2026 e dessas receitas pode, portanto, alterar os coeficientes históricos e os valores projetados.")
p62=haspar('Há ainda incertezas sobre a trajetória da base tributária')
setpar('Há ainda incertezas sobre a trajetória da base tributária',p62.text.replace('A trajetória do PIB é necessariamente incerta e o Seguro-Receita é simulado em frequência anual, embora a legislação opere com médias móveis mensais.','A trajetória do PIB é necessariamente incerta.'))
# ------------------------------------------------------------------ 4.1 UFs
def r2(xs,ys):
    mx,my=st.mean(xs),st.mean(ys);cov=sum((a-mx)*(b-my) for a,b in zip(xs,ys));return cov*cov/(sum((a-mx)**2 for a in xs)*sum((b-my)**2 for b in ys))
U=list(RES);yv=[100*(RES[u]['pos_por_ano']['2033']/RES[u]['contrafactual_por_ano']['2033']-1) for u in U]
R2a=r2([100*(PE[u]['coef_cpt_estado_pct']/PE[u]['coef_neutro_estado_pct']-1) for u in U],yv)
R2b=r2([100*(PHI['por_uf'][u]['coef_estado_compras_pct']/PE[u]['coef_neutro_estado_pct']-1) for u in U],yv)
NM={'AM':'Amazonas','TO':'Tocantins','MA':'Maranhão','MT':'Mato Grosso','AL':'Alagoas','RS':'Rio Grande do Sul','RJ':'Rio de Janeiro','SP':'São Paulo','AC':'Acre','DF':'Distrito Federal','ES':'Espírito Santo','MG':'Minas Gerais','MS':'Mato Grosso do Sul','PA':'Pará','GO':'Goiás','PE':'Pernambuco','BA':'Bahia','CE':'Ceará','RN':'Rio Grande do Norte','RO':'Rondônia','SC':'Santa Catarina','SE':'Sergipe','PB':'Paraíba','PI':'Piauí','PR':'Paraná','AP':'Amapá','RR':'Roraima'}
v33=sorted((v,u) for v,u in zip(yv,U));low=v33[:3];top=v33[::-1][:3]
T2v=[(100*(R_['pos_por_ano'][y]/R_['contrafactual_por_ano'][y]-1),(R_['pos_por_ano'][y]-R_['contrafactual_por_ano'][y])/1e6) for y in Y]
setpar('A Tabela 2 revela variações expressivas',
 f"A Tabela 2 revela variações expressivas entre as unidades da federação nos anos iniciais da transição. Em 2033, as maiores perdas relativas são observadas em {NM[low[0][1]]}, com redução de {fmt(-low[0][0],1,pct=True)}, {NM[low[1][1]]}, com {fmt(-low[1][0],1,pct=True)}, e {NM[low[2][1]]}, com {fmt(-low[2][0],1,pct=True)}. No outro extremo, os maiores ganhos ocorrem no {NM[top[0][1]]}, com {fmt(top[0][0],1,pct=True)}, {NM[top[1][1]]}, com {fmt(top[1][0],1,pct=True)}, e {NM[top[2][1]]}, com {fmt(top[2][0],1,pct=True)}. O Paraná ocupa posição intermediária: depois de variações próximas de zero entre 2029 e 2032 (de {fmt(T2v[0][0],2,pct=True)} a {fmt(T2v[3][0],2,True,True)}), a projeção para 2033 fica aproximadamente {fmt(var33,1)}% acima do cenário contrafactual sem reforma.".replace('no Rio de Janeiro','no Rio de Janeiro'))
subre('O painel (a) mostra associação elevada',r'de aproximadamente 0,\d{3}(?=\.? ?O painel|\. )',f'de aproximadamente {fmt(R2a,3)}') if False else None
for p in doc.paragraphs:
    if norm(p.text).startswith('O painel (a) mostra associação elevada'):
        vals=iter([fmt(R2a,3),fmt(R2b,3)])
        for r in p.runs:
            if re.search(r'aproximadamente 0,\d{3}',r.text):
                r.text=re.sub(r'aproximadamente 0,\d{3}',lambda m:'aproximadamente '+next(vals),r.text)
# ------------------------------------------------------------------ 4.2.2 sensibilidade
sa=SENS;ea=sa['env_all'][-1];eb=sa['env_base'][-1]
p89=haspar('A mudança de sinal decorre da composição da receita')
setpar('A mudança de sinal decorre da composição da receita',p89.text)
sens_par=clone_after(p89,f"O Gráfico 2(a) examina a robustez dessa trajetória a duas escolhas de modelagem. A primeira é o ano-base do contrafactual, para o qual, além de 2025, consideram-se a estimativa de 2026, a média de 2019 a 2026, equivalente ao coeficiente histórico, e o ano de 2019. A segunda é o coeficiente de destino, que varia 8% para mais e para menos em torno do valor central. Em 2033, a variação projetada fica entre {fmt(ea[0],1,pct=True)} e {fmt(ea[1],1,sign=True,pct=True)} no conjunto das combinações, e entre {fmt(eb[0],1,pct=True)} e {fmt(eb[1],1,sign=True,pct=True)} quando apenas o ano-base muda. A trajetória central, de {fmt(var33,1,sign=True,pct=True)}, situa-se no interior dessa faixa, cujo limite superior corresponde à base de 2026, em que a participação do Estado é menor, e cujo limite inferior corresponde à base de 2019, em que é maior. A relativa neutralidade é, portanto, robusta em ordem de grandeza, mas o sinal do resultado depende da referência adotada, o que justifica apresentá-lo como uma faixa, e não como um valor pontual.",prototype=haspar('Para os estados, a receita de referência corresponde'))
subre('A proximidade da neutralidade se mantém',r'\(Gráfico 2\)','(Gráfico 2, painel b)')
setpar('Gráfico 2:','Gráfico 2:') if False else None
cap=haspar('Gráfico 2:');cap.runs[1].text='\xa0Variação da receita estadual do Paraná em relação ao cenário sem reforma, 2029 a 2033 (sensibilidade), e receita estadual com e sem reforma até 2077'
for r in cap.runs[2:]:r.text=''
nt=[p for p in doc.paragraphs if norm(p.text).startswith('Nota: Valores a preços constantes de 2025. O painel (b)')][0]
nota_set(nt,"No painel (a), a linha central usa 2025 como ano-base do contrafactual e o coeficiente de destino estimado; a faixa escura reúne os anos-base alternativos (estimativa de 2026, média de 2019 a 2026 e 2019) e a faixa clara, a combinação desses anos com variação de 8% no coeficiente de destino. O painel (b) estende mecanicamente o cronograma legal até 2077, com coeficientes e demais hipóteses constantes, e representa um exercício condicionado a essas hipóteses, não uma previsão macroeconômica de longo prazo. Os percentuais indicam a diferença em relação ao cenário sem reforma. Valores a preços constantes de 2025.")
# ------------------------------------------------------------------ 4.3 municípios
p99=haspar('O principal resultado para o Paraná é a assimetria')
for r in p99.runs:
    r.text=re.sub(r'R\$ [\d,]+ bilhões em 2033, frente a R\$ [\d,]+ bilhões',f'R$ {fmt(m_pos,2)} bilhões em 2033, frente a R$ {fmt(m_cf,2)} bilhões',r.text)
    r.text=re.sub(r'aproximadamente R\$ [\d,]+ bilhão, ou',f'aproximadamente R$ {fmt(m_cf-m_pos,2)} bilhão, ou',r.text)
    r.text=re.sub(r'cerca de R\$ [\d,]+ bilhão(?!,)',f'cerca de R$ {fmt(m_acum,2)} bilhão',r.text)
    r.text=re.sub(r'aproximadamente [\d,]+% abaixo',f'aproximadamente {fmt(-tot_var,2)}% abaixo',r.text)
ts=list(p99._p.iter(M+'t'))
for k,t in enumerate(ts):
    if t.text.isdigit() and k+2<len(ts) and ts[k+1].text==',' and ts[k+2].text.isdigit() and k>0:
        a,b=f"{abs(m_var):.2f}".split('.');t.text=a;ts[k+2].text=b;break
setpar('O Seguro-Receita reduz parte das perdas',
 f"O Seguro-Receita reduz parte das perdas, mas não altera essa conclusão agregada. Em 2033, {npr[-1]} municípios paranaenses recebem aproximadamente R$ {fmt(seg['2033']['repasse_pr']/1e6,1)} milhões do mecanismo, frente a uma diferença agregada municipal de cerca de R$ {fmt(m_cf-m_pos,2)} bilhão naquele ano. No acumulado de 2029 a 2033, os repasses municipais do Seguro-Receita somam aproximadamente R$ {fmt(rep,1)} milhões.")
setpar('Para examinar a heterogeneidade entre municípios',
 f"Para examinar a heterogeneidade entre municípios, a análise considera os {Tt['n']} municípios do Estado. Em 2033, {Tt['perdem_2033']} apresentam receita inferior ao cenário sem reforma e {Tt['ganham_2033']} registram resultado positivo; a mediana da variação é de {fmt(Tt['mediana_var_2033_pct'],1,pct=True)}. Os {Tt['perdem_2033']} municípios que perdem em 2033 acumulam perda de R$ {fmt(bi(perda_acum_perdedores),2)} bilhões entre 2029 e 2033, contra ganho acumulado de R$ {fmt(bi(Tt['ganho_acum_2029_2033_dos_que_ganham_2033']),2)} bilhão dos demais, o que resulta na perda líquida de R$ {fmt(bi(-Tt['saldo_acum_2029_2033']),2)} bilhão. O Mapa 1 mostra que perdas e ganhos não se concentram em uma única região do Estado. Como teste de robustez, restringir o conjunto aos {A['n']} municípios com população média de pelo menos 10 mil habitantes, ISS observado diretamente em 2025 e em ao menos cinco exercícios e sem pendência de validação não altera o quadro: {A['perdem_2033']} perdem, {A['ganham_2033']} ganham e a mediana é de {fmt(A['mediana_var_2033_pct'],1,pct=True)}.")
def lst(L,sinal,k=5):
    out=[f"{x['municipio']} ({'−' if sinal<0 else '+'}R$ {fmt(abs(mi(x['dif_2033_reais'])),1)} milhões; {fmt(x['var_2033_pct'],1,sign=True,pct=True)})" for x in L[:k]];return ', '.join(out[:-1])+' e '+out[-1]
def lstp(L,k=5):
    out=[f"{x['municipio']} ({fmt(x['var_2033_pct'],1,sign=True,pct=True)})" for x in L[:k]];return ', '.join(out[:-1])+' e '+out[-1]
def juntar(L):return L[0] if len(L)==1 else ', '.join(L[:-1])+' e '+L[-1]
cu=[r for r in CSVr if r['municipio']=='Curitiba'][0];gc=[r for r in CSVr if r['municipio']=='General Carneiro'][0];pg=[r for r in CSVr if r['municipio']=='Pontal do Paraná'][0]
flg=lambda L:[x['municipio'] for x in L[:5] if x['dado_iss_incompleto']]
fp,fg=flg(RT['maiores_perdas_pct']),flg(RT['maiores_ganhos_pct'])
flagtxt=(f"Entre os cinco maiores percentuais de perda, {juntar(fp)} {'tem' if len(fp)==1 else 'têm'} ISS incompleto na DCA (†, Tabela B.3), e a base pequena {'desse município' if len(fp)==1 else 'desses municípios'} amplia o percentual." if fp else "Nenhum dos cinco maiores percentuais de perda tem ISS incompleto.")
if fg: flagtxt+=f" O mesmo vale para {juntar(fg)} entre os maiores percentuais de ganho."
setpar('Em valores absolutos, as maiores perdas',
 f"Em valores absolutos, as maiores perdas em 2033 concentram-se nos municípios grandes: {lst(RT['maiores_perdas_reais'],-1)}. Curitiba, por exemplo, tem receita projetada de aproximadamente R$ {fmt(float(cu['receita_2033_final'])/1e9,2)} bilhões em 2033, frente a R$ {fmt(float(cu['contrafactual_2033_final'])/1e9,2)} bilhões no cenário sem reforma. Em termos percentuais, as maiores perdas ocorrem em municípios menores: {lstp(RT['maiores_perdas_pct'])}. General Carneiro, por exemplo, combina receita de referência de 2025 de aproximadamente R$ {fmt(float(gc['base_2025_final'])/1e6,1)} milhões com média histórica de R$ {fmt(float(gc['receita_media_historica_final'])/1e6,1)} milhões, e Paranaguá apresenta coeficiente de destino substancialmente inferior à sua participação histórica, o que reforça a perda à medida que o destino ganha peso. {flagtxt}")
setpar('No extremo oposto, os maiores ganhos',
 f"No extremo oposto, os maiores ganhos em valores absolutos são {lst(RT['maiores_ganhos_reais'],+1)}. Em termos percentuais, destacam-se {lstp(RT['maiores_ganhos_pct'])}. Pontal do Paraná é um caso particularmente marcado pela diferença entre a base de 2025, cerca de R$ {fmt(float(pg['base_2025_final'])/1e6,1)} milhões, e a média histórica, aproximadamente R$ {fmt(float(pg['receita_media_historica_final'])/1e6,1)} milhões. Os valores elevados de cota-parte observados em 2020 e 2021 aparecem tanto na DCA quanto na fonte estadual, razão pela qual o resultado é preservado na base auditada.")
tot0=sum(float(x['base_2025_final']) for x in CSVr);yy=[float(x['variacao_2033_final_pct']) for x in CSVr];sh=[float(x['base_2025_final'])/tot0*100 for x in CSVr]
R2mh=r2([float(x['cpt_final_pct'])/s-1 for x,s in zip(CSVr,sh)],yy);R2md=r2([float(x['destino_pct'])/s-1 for x,s in zip(CSVr,sh)],yy)
p108=haspar('A posição histórica continua sendo o principal fator')
for r in p108.runs:
    r.text=re.sub(r'de 0,\d{3}(?= com a variação projetada)','de '+fmt(R2mh,3),r.text)
    r.text=re.sub(r'frente a 0,\d{3}','frente a '+fmt(R2md,3),r.text)
dz=RD['dispersao'];dr=RD['dispersao_robustez_iss_completo']
rz=lambda y:fmt(dz[str(y)]['Razão máx./mín.'],1);gn=lambda y:fmt(dz[str(y)]['Índice de Gini'],3)
rzr=lambda y:fmt(dr[str(y)]['Razão máx./mín.'],1);gnr=lambda y:fmt(dr[str(y)]['Índice de Gini'],3)
setpar('A transição também altera a distribuição',
 f"A transição também altera a distribuição da receita por habitante entre os municípios. A Tabela D.1, apresentada no Anexo D, acompanha a receita per capita dos {RD['n']} municípios do Estado. A razão entre a maior e a menor receita per capita recua de {rz(2025)} em 2025 para {rz(2033)} em 2033 e cai para {rz(2050)} em 2050 e {rz(2077)} em 2077, enquanto o índice de Gini passa de {gn(2025)} em 2025 para {gn(2050)} em 2050 e {gn(2077)} em 2077. Excluídos os {RD['n']-RD['n_robustez_iss_completo']} municípios com ISS incompleto, a razão cai de {rzr(2025)} para {rzr(2077)} e o Gini, de {gnr(2025)} para {gnr(2077)}, de modo que o resultado não depende deles. A convergência ocorre porque, à medida que o destino ganha peso, a receita passa a acompanhar a população e a renda do município, e não sua participação histórica, o que eleva sobretudo os municípios de menor receita por habitante.")
# ------------------------------------------------------------------ discussão e conclusões
p116=haspar('Esse novo desenho atribui maior importância');setpar('Esse novo desenho atribui maior importância',re.sub(r'em \d+ dos \d+ municípios',f"em {Tt['mudancas_de_sinal']} dos {Tt['n']} municípios",p116.text))
p117=haspar('A LC n.o 227/2026 determina que a receita média')
setpar('A LC n.o 227/2026 determina que a receita média',p117.text.replace('A estimativa deste estudo ainda não incorpora essas receitas, diante da ausência de uma base nacional comparável, e por isso pode subestimar a participação histórica de estados nos quais essas contribuições tenham maior relevância.','A estimativa deste estudo incorpora apenas as contribuições do Amazonas, as únicas verificáveis em base pública, e por isso pode subestimar a participação histórica dos estados cujos fundos ainda dependem de informação oficial.'))
p123=haspar('Este artigo estimou os efeitos da transição')
for r in p123.runs:
    r.text=re.sub(r'variação de [\d,]+%, enquanto o conjunto dos municípios registra redução de [\d,]+%',f"variação de {fmt(var33,2,pct=True)}, enquanto o conjunto dos municípios registra redução de {fmt(-m_var,2,pct=True)}",r.text)
    r.text=re.sub(r'fica [\d,]+% abaixo do contrafactual',f"fica {fmt(-tot_var,2)}% abaixo do contrafactual",r.text)
setpar('A redistribuição municipal apresenta',
 f"A redistribuição municipal apresenta uma dinâmica distinta. Entre os {RD['n']} municípios do Estado, a razão entre a maior e a menor receita per capita cai de {rz(2025)} em 2025 para {rz(2077)} em 2077, enquanto o índice de Gini recua de {gn(2025)} para {gn(2077)}. A transição reduz, portanto, de forma expressiva a desigualdade de receita por habitante entre os municípios paranaenses. Esse resultado mostra que perdas agregadas da esfera municipal podem coexistir com maior equalização na distribuição dos recursos dentro do Estado.")
# ------------------------------------------------------------------ anexos
setpar('Este anexo reúne seis conjuntos',"Este anexo reúne sete conjuntos de resultados complementares. O primeiro confronta diretamente as projeções estaduais deste estudo com as apresentadas pelo Ipea ao Confaz, tanto na base de 2025 quanto em 2033. O segundo apresenta a memória de cálculo do coeficiente de participação do governo estadual do Paraná na transição federativa. O terceiro apresenta a associação entre os coeficientes de repartição e a variação da receita estadual em 2033. O quarto destrincha, como exemplo, o cálculo da receita estadual do Paraná em 2033. O quinto compara Curitiba com as demais capitais brasileiras no mesmo ano. O sexto reúne os símbolos e as definições utilizados no modelo de projeção, e o sétimo apresenta a sensibilidade do resultado de 2033 ao ano-base do contrafactual e ao coeficiente de destino.")
pn=haspar('Nota: Na amostra comparável') if False else None
setpar('Nota: Nos 399 municípios',f"Nota: Nos {Tt['n']} municípios, {Tt['mudancas_de_sinal']} mudam de sinal entre as metodologias e a revisão absoluta média da variação de 2033 é de {fmt(Tt['media_abs_revisao_pp'],2)} pontos percentuais.")
setpar('Este anexo detalha a redução da desigualdade',f"Este anexo detalha a redução da desigualdade de receita por habitante entre os municípios do Paraná ao longo da transição. A tabela apresenta os dez municípios com maior e os dez com menor receita per capita em 2025, a trajetória dessa receita até 2077 e, na parte inferior, duas medidas de dispersão calculadas para os {RD['n']} municípios do Estado.")
setpar('Nota: Receita per capita em R$ de 2025',f"Nota: Receita per capita em R$ de 2025, reunindo o ICMS ou ISS remanescente, o IBS pelo componente histórico e pelo destino, o Seguro-Receita e a dedução do CGIBS, com população média fixa em todo o período. A razão máx./mín. e o índice de Gini referem-se aos {RD['n']} municípios; excluídos os {RD['n']-RD['n_robustez_iss_completo']} com ISS incompleto, os resultados mudam pouco (razão de {rzr(2025)} para {rzr(2077)}; Gini de {gnr(2025)} para {gnr(2077)}). Mato Rico, com pendência de validação do ISS, aparece entre os maiores valores de 2025.")
# tabelas B.1, B.3, D.1
t8=doc.tables[8]
for row in t8.rows[1:]:
    k=row.cells[0].text.strip();o=Tt['metodo_dca_direto']
    if k.startswith('Resultado negativo'):setcell(row.cells[1],str(o['negativos']));setcell(row.cells[2],str(Tt['perdem_2033']))
    elif k.startswith('Resultado positivo'):setcell(row.cells[1],str(o['positivos']));setcell(row.cells[2],str(Tt['ganham_2033']))
    elif k.startswith('Mediana'):setcell(row.cells[1],fmt(o['mediana_pct'],2,pct=True));setcell(row.cells[2],fmt(Tt['mediana_var_2033_pct'],2,pct=True))
    elif k.startswith('Repasse municipal'):
        setcell(row.cells[1],'R$\xa0'+fmt(502.2*acc/471.6,1)+' mi');setcell(row.cells[2],'R$\xa0'+fmt(acc,1)+' mi')
    elif k.startswith('Variação agregada'):
        setcell(row.cells[2],fmt(m_var,2,pct=True));setcell(row.cells[1],fmt(-2.13+(m_var-(-4.29)),2,pct=True))
t10=doc.tables[10]
def cel(x):
    return x['municipio']+('†' if x['dado_iss_incompleto'] else ''), f"{fmt(-mi(x['dif_2033_reais']),1,sign=True)} ({fmt(x['var_2033_pct'],1,sign=True,pct=True)})"
for i,row in enumerate(t10.rows[2:]):
    a,b=cel(RT['maiores_perdas_reais'][i]);c,d=cel(RT['maiores_ganhos_reais'][i])
    setcell(row.cells[0],a);setcell(row.cells[1],b);setcell(row.cells[2],c);setcell(row.cells[3],d)
new=docx.Document(N+'data/auditoria-pr-validacao/tabelas-artigo/tabela-unica-dispersao-percapita-pr.docx').tables[0]
nr=[[c.text.strip().replace('\n',' ') for c in r.cells] for r in new.rows[2:]]
t12=doc.tables[12]
def pfx(x):return re.sub(r'^\d+\.\s*','',x)
popmil=lambda x:fmt(float(x.replace('.','').replace(',','.'))/1000,1)
varp=lambda x:fmt(float(x.replace('%','').replace('+','').replace('−','-').replace('.','').replace(',','.')),0,sign=True,pct=True)
for row,vals in zip(t12.rows[1:],nr):
    cells=[]
    for c in row.cells:
        if not cells or c._tc is not cells[-1]._tc:cells.append(c)
    if vals[0].startswith('...'):continue
    if vals[0].startswith('Razão') or vals[0].startswith('Índice'):
        for c,v in zip(cells,vals[:len(cells)]):setcell(c,v)
        continue
    for c,v in zip(cells,[pfx(vals[0]),popmil(vals[1])]+vals[2:7]+[varp(vals[7])]):setcell(c,v)
# ------------------------------------------------------------------ Tabela A.6
base_keys=list(sa['bases'].keys());lab={'2025 (central)':'2025 (ano-base adotado)','2026 (estimado)':'2026 (estimado)','Média 2019–2026':'Média de 2019 a 2026','2019':'2019'}
cap5=haspar('Tabela A.5:');idx=[i for i,p in enumerate(doc.paragraphs) if p._p is cap5._p][0]
fonte5=[p for p in doc.paragraphs[idx:] if norm(p.text).startswith('Fonte:')][0]
# valores de sensibilidade ao peso das compras (estado)
ff=PHI['frac_estado_pct']/100;phif=PHI['por_uf']['PR']['phi_fam_pct']/100
sE=(PHI['por_uf']['PR']['coef_estado_compras_pct']/100/ff-(1-0.0601)*phif)/0.0601
D_te=lambda te:ff*((1-te)*phif+te*sE)
Ls={s['ano']:s for s in LP}
def v33(ref,Dc):
    s=Ls[2033];h=s['ibs_historico']*(PE['PR']['coef_cpt_estado_pct']/100);d=s['ibs_destino_liquido']*Dc
    return 100*((s['icms_iss_residual']*ref+h+d-s['ca']*h)/(ref*s['bolo_projetado'])-1)
ref25_=PE['PR']['coef_neutro_estado_pct']/100
vc0,vc12=v33(ref25_,D_te(0.0)),v33(ref25_,D_te(0.12))
new_cap=copy.deepcopy(cap5._p);fonte5._p.addnext(new_cap);pc6=Paragraph(new_cap,cap5._parent)
pc6.runs[0].text='Tabela A.6:';pc6.runs[1].text='\xa0Sensibilidade da variação da receita estadual do Paraná em 2033 ao ano-base do contrafactual e ao coeficiente de destino'
tbl=copy.deepcopy(doc.tables[2]._tbl);new_cap.addnext(tbl)
from docx.table import Table
t6=Table(tbl,cap5._parent)
for r_ in list(t6.rows)[5:]:tbl.remove(r_._tr)
hdr=['Ano-base do contrafactual','Participação do Estado (%)','Destino −8%','Destino central','Destino +8%']
for c,v in zip(t6.rows[0].cells,hdr):setcell(c,v)
for row,b in zip(t6.rows[1:5],base_keys):
    vals=[lab[b],fmt(100*sa['bases'][b],4)]+[fmt(sa['M'][f'{b}|{m}'][-1],2,sign=True,pct=True) for m in (-0.08,0,0.08)]
    for c,v in zip(row.cells,vals):setcell(c,v)
nota_proto=[p for p in doc.paragraphs if norm(p.text).startswith('Nota: Valores a preços constantes de 2025. O valor do IBS pelo destino')][0]
pn6=copy.deepcopy(nota_proto._p);tbl.addnext(pn6);pn6p=Paragraph(pn6,cap5._parent)
nota_set(pn6p,f"Variação da receita estadual projetada para 2033 em relação ao cenário sem reforma definido pelo ano-base indicado. A variação do coeficiente de destino é de 8% para mais e para menos, correspondente à incerteza relativa estimada para o coeficiente. Variar o peso das compras públicas no IBS estadual entre 0% e 12% altera o coeficiente de destino estadual entre {fmt(100*D_te(0.0),2)}% e {fmt(100*D_te(0.12),2)}% e a variação de 2033 entre {fmt(vc0,2,sign=True,pct=True)} e {fmt(vc12,2,sign=True,pct=True)}, no ano-base de 2025.")
src6=copy.deepcopy(fonte5._p);pn6.addnext(src6);Paragraph(src6,cap5._parent).runs[2].text='Elaboração própria, com base nos coeficientes estimados e nas projeções nacionais do modelo.'
# ------------------------------------------------------------------ imagens
def troca(rid_old,path):
    rels={r.target_ref:r for r in doc.part.rels.values() if 'image' in r.reltype}
    part=rels[f'media/{rid_old}.png'].target_part
    old=Image.open(io.BytesIO(part.blob));new_=Image.open(path).convert('RGB').resize(old.size,Image.LANCZOS)
    b=io.BytesIO();new_.save(b,'PNG');part._blob=b.getvalue()
troca('rId27',S+'img/g2_v5.png')
troca('rId33',N+'data/auditoria-pr-validacao/graficos-artigo/mapa-variacao-2033-pr.png')
for el in list(doc.element.body.iter(W+'highlight')):el.getparent().remove(el)
doc.save(S+'art_v5.docx');print('ok',len(LOG),'| compras',vc0,vc12,'| aseg',am_rep['2029']/1e6,am_rep['2033']/1e6)
