import json,sys
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
D='/home/user/site-eduardo/data/'
S='/tmp/claude-0/-home-user-site-eduardo/81c38a17-983b-5e8a-a2ce-12db2b4f5b48/scratchpad/'
L={s['ano']:s for s in json.load(open(D+'ibs-projecao-longo-prazo.json'))['projecao']}
PE=json.load(open(D+'painel-estados.json'))['estados'];P=PE['PR']
CF=json.load(open(D+'coeficientes-uf.json'))
cpt=P['coef_cpt_estado_pct']/100;D0=json.load(open(D+'phi-dest-pof-censo.json'))['por_uf']['PR']['coef_estado_compras_pct']/100
ref25=P['coef_neutro_estado_pct']/100
Y=[str(y) for y in range(2019,2026)]
base={y:sum(e['historico_por_ano'][y]['icms_reais_2025']-e['historico_por_ano'][y]['outras_deducoes_reais_2025']+e['historico_por_ano'][y]['iss_reais_2025']+e['historico_por_ano'][y]['fecop_reais_2025'] for e in PE.values()) for y in Y}
sh={y:P['historico_por_ano'][y]['estado_reais_2025']/base[y] for y in Y}
ref26=P['estimativa_2026']['estado_reais_2025']/CF['total_br_2025']
BASES={'2025 (central)':ref25,'2026 (estimado)':ref26,'Média 2019–2026':cpt,'2019':sh['2019']}
INC=0.08
anos=[2029,2030,2031,2032,2033]
def var(ref,Dc,ano):
    s=L[ano];h=s['ibs_historico']*cpt;d=s['ibs_destino_liquido']*Dc
    pos=s['icms_iss_residual']*ref+h+d-s['ca']*h
    return 100*(pos/(ref*s['bolo_projetado'])-1)
M={(b,m):[var(r,D0*(1+m),a) for a in anos] for b,r in BASES.items() for m in (-INC,0,INC)}
central=M[('2025 (central)',0)]
env_all=[(min(v[i] for v in M.values()),max(v[i] for v in M.values())) for i in range(5)]
env_base=[(min(M[(b,0)][i] for b in BASES),max(M[(b,0)][i] for b in BASES)) for i in range(5)]
env_dest=[(min(M[('2025 (central)',m)][i] for m in (-INC,0,INC)),max(M[('2025 (central)',m)][i] for m in (-INC,0,INC))) for i in range(5)]
if __name__=='__main__':
    json.dump({'central':central,'env_all':env_all,'env_base':env_base,'env_dest':env_dest,'M':{f'{b}|{m}':v for (b,m),v in M.items()},'bases':BASES,'D0':D0},open(S+'sens_v5.json','w'),ensure_ascii=False)
    plt.rcParams['font.family']='Liberation Serif'
    vir=lambda x,d=1,sg=False:(('+' if (sg and round(x,d)>0) else '')+f"{(0.0 if round(x,d)==0 else x):.{d}f}").replace('.',',').replace('-','−')
    fig,(a1,a2)=plt.subplots(1,2,figsize=(8.57,4.78),dpi=200,gridspec_kw={'width_ratios':[1.05,1.0]})
    a1.fill_between(anos,[e[0] for e in env_all],[e[1] for e in env_all],color='#9db4d6',alpha=.30,lw=0,label='Ano-base e destino ±8% (envoltória)')
    a1.fill_between(anos,[e[0] for e in env_base],[e[1] for e in env_base],color='#1f3864',alpha=.22,lw=0,label='Ano-base alternativo')
    st={'2026 (estimado)':('#2e7d32','--'),'Média 2019–2026':('#8a6d1f','-.'),'2019':('#9c3d3d',':')}
    for b,(c,ls) in st.items():
        a1.plot(anos,M[(b,0)],ls=ls,color=c,lw=1.3,label=b)
    a1.plot(anos,central,'-o',color='#1f3864',lw=2.4,label='Central (2025)')
    a1.axhline(0,color='#555',lw=.8)
    a1.set_xticks(anos);a1.set_ylabel('Variação ante o cenário sem reforma (%)');a1.set_title('(a) Sensibilidade, 2029 a 2033',fontsize=11,loc='left')
    a1.grid(axis='y',alpha=.3);[a1.spines[k].set_visible(False) for k in('top','right')]
    a1.text(2033.06,central[-1],vir(central[-1],2,True)+'%',fontsize=8.5,color='#1f3864',va='center')
    a1.text(2033.06,env_all[-1][1],vir(env_all[-1][1],1,True)+'%',fontsize=8,color='#555',va='center')
    a1.text(2033.06,env_all[-1][0],vir(env_all[-1][0],1,True)+'%',fontsize=8,color='#555',va='center')
    a1.set_xlim(2028.7,2033.9);a1.legend(frameon=False,fontsize=7,loc='upper left')
    # painel (b): extensão do cronograma (mantido)
    D_=D0;ref=ref25
    lv={}
    for a in (2033,2040,2050,2060,2070,2077):
        s=L[a];hh=s['ibs_historico']*cpt;dd=s['ibs_destino_liquido']*D_;cg=s['ca']*hh
        lv[a]=((hh+dd-cg)/1e9,ref*s['bolo_projetado']/1e9)
    xs=[2033,2040,2050,2060,2070,2077]
    a2.plot(xs,[lv[x][1] for x in xs],':o',color='#666',lw=2.4,mfc='white',label='Cenário sem reforma')
    a2.plot(xs,[lv[x][0] for x in xs],'--o',color='#1f3864',lw=2.4,label='Com reforma')
    a2.fill_between(xs,[lv[x][0] for x in xs],[lv[x][1] for x in xs],color='#c0504d',alpha=.18,lw=0)
    for x in xs:
        a2.annotate(vir(100*(lv[x][0]/lv[x][1]-1)+0.0,1,x==2033)+'%',(x,lv[x][0]),textcoords='offset points',xytext=(8,-17) if x!=2033 else (-4,-20),fontsize=9)
    a2.set_ylim(38,max(lv[x][1] for x in xs)*1.04)
    a2.set_title('(b) Extensão do cronograma legal, 2033 a 2077',fontsize=11,loc='left');a2.set_xticks(xs);a2.set_ylabel('Receita estadual (R$ bilhões de 2025)');a2.grid(axis='y',alpha=.3);a2.legend(frameon=False,loc='upper left',fontsize=9)
    [a2.spines[k].set_visible(False) for k in('top','right')]
    fig.tight_layout();fig.savefig(S+'img/g2_v5.png');print('ok',[round(x,2) for x in central],env_all[-1])
