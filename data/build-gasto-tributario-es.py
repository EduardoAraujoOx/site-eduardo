#!/usr/bin/env python3
"""
Gasto tributário de ICMS do Espírito Santo, segundo o Demonstrativo VII
(Estimativa e Compensação da Renúncia de Receita) do Anexo de Metas Fiscais da LDO.

Fontes (Secretaria de Economia e Planejamento do ES, planejamento.es.gov.br,
"Leis de Diretrizes Orçamentárias"):
  PLDO 2027  - Mensagem do projeto, Demonstrativo VII nas páginas 53 a 69 (tabela na p. 60)
  LDO 2026   - Lei n. 12.485/2025, DIO de 21/07/2025 (tabela na p. 45)
  LDO 2025   - DIO de 25/07/2024 (tabela na p. 42)
  LDO 2024   - DIO de 20/07/2023 (tabela em texto, p. 38)

As tabelas do PLDO 2027 e da LDO 2026 foram publicadas como imagem; os valores abaixo
foram transcritos linha a linha e conferidos contra os subtotais e totais publicados
(ver ``confere``). Qualquer erro de transcrição aparece como diferença de soma; a tolerância
é de R$ 5 porque as células publicadas são arredondadas.

Os valores estão em R$ correntes. O gasto tributário de ICMS é, na definição da própria
SEFAZ, a diferença entre o ICMS potencial e o ICMS real; a base é a escrituração
fiscal (EFD) do ano anterior ao da LDO, corrigida por IPCA e PIB (Focus).

Uso:
  python3 build-gasto-tributario-es.py
Gera data/gasto-tributario-es/gasto-tributario-es.json e os CSV ao lado.
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "gasto-tributario-es"

# ---------------------------------------------------------------------------
# LDO 2027 (PLDO 2027): anos 2027, 2028, 2029. Fonte: BI/SEFAZ-GEARC, emitido em 11/03/2026.
# (tributo, instrumento legal, modalidade, setor, v2027, v2028, v2029)
# ---------------------------------------------------------------------------
L27 = [
    ("ICMS", "Lei 10.568/2016", "Crédito presumido", "Atacadista", 6860431823, 7242557875, 7645968349),
    ("ICMS", "Lei 10.568/2016", "Crédito presumido", "Varejo Não Presencial", 1864727811, 1968593150, 2078243788),
    ("ICMS", "Lei 10.568/2016", "Modificação da base de cálculo e crédito presumido", "Rochas Ornamentais", 99084894, 104603923, 110430361),
    ("ICMS", "Lei 10.568/2016", "Modificação da base de cálculo e crédito presumido", "Metalmecânica", 87927560, 92825125, 97995484),
    ("ICMS", "Lei 10.568/2016", "Modificação da base de cálculo e crédito presumido", "Outros (a)", 39566455, 41770306, 44096912),
    ("ICMS", "Lei 10.568/2016", "Modificação da base de cálculo e crédito presumido", "Vestuário", 68770267, 72600771, 76644634),
    ("ICMS", "Lei 10.568/2016", "Modificação da base de cálculo", "Bares e Restaurantes", 47411150, 50051951, 52839845),
    ("ICMS", "Lei 10.550/2016", "Crédito presumido", "Indústrias/Importadoras (INVEST)", 7040462810, 7432616589, 7846613333),
    ("ICMS", "Lei 11.620/2022", "Isenção", "Construção", 8941758, 9439814, 9965612),
    ("ICMS", "Lei 11.660/2022", "Isenção", "Construção", 2962181, 3127175, 3301358),
    ("ICMS", "Lei 11.765/2022", "Isenção", "Alojamento e Alimentação", 4542927, 4795968, 5063104),
    ("ICMS", "Lei 11.769/2022", "Isenção", "Eletricidade e Gás", 1273630, 1344571, 1419464),
    ("ICMS", "Lei 11.764/2022", "Alteração de alíquota", "Comércio; Reparação de Veículos Automotores e Motocicletas", 2962181, 3127175, 3301358),
    ("ICMS", "Lei 11.246/2021", "Crédito presumido", "Artes, Cultura, Esporte e Recreação", 70000000, 70000000, 70000000),
    ("ICMS", "Lei 12.022/2023", "Modificação da base de cálculo", "Eletricidade e Gás", 120247670, 126945465, 134016328),
    ("ICMS", "Lei 11.813/2023", "Alteração de alíquota", "Alojamento e Alimentação", 1728637, 1824922, 1926570),
    ("ICMS", "Lei 11.994/2023", "Crédito presumido", "Indústrias Extrativas", 4924528, 5198824, 5488398),
    ("ICMS", "Lei 12.185/2024", "Crédito presumido", "Transporte, Armazenagem e Correio", 3844997, 4059163, 4285259),
    ("ICMS", "Lei 12.203/2024", "Crédito presumido", "Indústrias Extrativas", 923126, 974544, 1028826),
    ("ICMS", "Lei 12.320/2024", "Alteração de alíquota", "Saúde Humana e Serviços Sociais", 1372, 1449, 1530),
    ("ICMS", "Lei 12.186/2024", "Alteração de alíquota", "Comércio; Reparação de Veículos Automotores e Motocicletas", 16067419, 16962374, 17907178),
    ("ICMS", "Lei 12.308/2024", "Modificação da base de cálculo", "Regimes Especiais", 4280719, 4519156, 4770873),
    ("ICMS", "Lei 12.317/2024", "Alteração de alíquota", "Eletricidade e Gás", 68843, 72677, 76725),
    ("ICMS", "Lei 12.257/2024", "Modificação da base de cálculo", "Indústrias Extrativas", 71129121, 75091013, 79273583),
    ("ICMS", "Lei 12.316/2024", "Alteração de alíquota", "Eletricidade e Gás", 7379134, 7790151, 8224063),
    ("ICMS", "Lei 12.202/2024", "Isenção", "Indústria de Transformação", 5597323, 5909094, 6238230),
    ("ICMS", "Lei 12.322/2024", "Isenção", "Eletricidade e Gás", 0, 0, 0),
    ("ICMS", "Lei 12.187/2024", "Isenção", "Organismos Internacionais e Outras Instituições Extraterritoriais", 0, 0, 0),
    ("ICMS", "Lei 12.487/2025", "Modificação da base de cálculo", "Eletricidade e Gás", 97833, 103283, 109036),
    ("ICMS", "Lei 12.690/2025", "Crédito outorgado", "Eletricidade e Gás", 8494954, 8968123, 9467647),
    ("ICMS", "Lei 12.698/2025", "Crédito presumido", "Indústria de Transformação", 1273502, 1344436, 1419321),
    ("IPVA", "Lei 6.999/2001", "Modificação da base de cálculo", "Veículos 1º emplacamento", 24454772, 25816903, 27254905),
    ("IPVA", "Lei 6.999/2001", "Alteração de alíquota", "Locadoras", 18429050, 19455548, 20539222),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Veículos (mais de 15 anos)", 225667744, 238237438, 251507263),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Deficiente físico", 14930223, 15761836, 16639770),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Veículo oficial", 11161902, 11783620, 12439968),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Perda, roubo ou sinistro", 7517115, 7935819, 8377844),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Táxis", 5607316, 5919644, 6249368),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Ônibus urbanos", 3616, 3818, 4030),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Outros veículos (b)", 2082373, 2198361, 2320810),
    ("ITCMD", "Lei 4.215/1989", "Isenção", "Art. 4º, I", 358652, 378629, 399719),
    ("ITCMD", "Lei 4.215/1989", "Isenção", "Art. 4º, II", 43307, 45719, 48266),
    ("ITCMD", "Lei 10.011/2013", "Isenção", "Art. 7º, I, a", 3496359, 3691106, 3896701),
    ("ITCMD", "Lei 10.011/2013", "Isenção", "Art. 7º, I, b", 158637, 167473, 176802),
    ("ITCMD", "Lei 10.011/2013", "Isenção", "Art. 7º, I, c", 523700, 552871, 583665),
    ("ITCMD", "Lei 10.011/2013", "Isenção", "Art. 7º, I, d", 908520, 959125, 1012548),
    ("ITCMD", "Lei 10.011/2013", "Isenção", "Art. 7º, I, e", 542934, 573176, 605102),
    ("ITCMD", "Lei 10.011/2013", "Isenção", "Art. 7º, I, f", 72194, 76215, 80460),
    ("ITCMD", "Lei 10.011/2013", "Isenção", "Art. 7º, II, b", 58744, 62016, 65470),
    ("ITCMD", "Lei 10.011/2013", "Isenção", "Art. 7º, II, c", 163453, 172557, 182168),
    ("ITCMD", "Lei 10.011/2013", "Isenção", "Art. 7º, §2º, I", 7939, 8382, 8848),
    ("TAXAS", "Lei 11.863/2023", "Alteração de alíquota", "Transporte, Armazenagem e Correio", 1589495, 1678030, 1771497),
    ("OUTROS", "", "Outros incentivos (c)", "Novos incentivos que podem ser aprovados no exercício", 200000000, 200000000, 200000000),
]
SUB27 = {  # subtotais e total publicados
    "ICMS": (16445124624, 17357219065, 18320117167),
    "IPVA": (309854112, 327112986, 345333180),
    "ITCMD": (6334440, 6687268, 7059749),
    "TAXAS": (1589495, 1678030, 1771497),
    "OUTROS": (200000000, 200000000, 200000000),
    "TOTAL": (16962902671, 17892697350, 18874281593),
}

# ---------------------------------------------------------------------------
# LDO 2026: anos 2026, 2027, 2028. Fonte: BI/SEFAZ-GEARC, emitido em 21/03/2025.
# Não há linha de ITCMD nesta edição.
# ---------------------------------------------------------------------------
L26 = [
    ("ICMS", "Lei 10.568/2016", "Crédito presumido", "Atacadista", 6483018449, 6877185971, 7279886473),
    ("ICMS", "Lei 10.568/2016", "Crédito presumido", "Varejo Não Presencial", 1353983038, 1436305206, 1520409494),
    ("ICMS", "Lei 10.568/2016", "Modificação da base de cálculo e crédito presumido", "Rochas Ornamentais", 144710233, 153508615, 162497466),
    ("ICMS", "Lei 10.568/2016", "Modificação da base de cálculo e crédito presumido", "Metalmecânica", 6176293, 6551812, 6935460),
    ("ICMS", "Lei 10.568/2016", "Modificação da base de cálculo e crédito presumido", "Outros (a)", 59633615, 63259338, 66963552),
    ("ICMS", "Lei 10.568/2016", "Modificação da base de cálculo e crédito presumido", "Vestuário", 142455669, 151116973, 159965779),
    ("ICMS", "Lei 10.568/2016", "Modificação da base de cálculo", "Bares e Restaurantes", 48776337, 51741938, 54771739),
    ("ICMS", "Lei 10.550/2016", "Crédito presumido", "Indústrias/Importadoras (INVEST)", 5770783933, 6121647596, 6480106792),
    ("ICMS", "Lei 11.620/2022", "Isenção", "Construção", 9499328, 10076887, 10666950),
    ("ICMS", "Lei 11.660/2022", "Isenção", "Construção", 3146890, 3338221, 3533694),
    ("ICMS", "Lei 11.765/2022", "Isenção", "Alojamento e Alimentação", 4826205, 5119638, 5419424),
    ("ICMS", "Lei 11.769/2022", "Isenção", "Eletricidade e Gás", 1353048, 1435313, 1519359),
    ("ICMS", "Lei 11.758/2022", "Modificação da base de cálculo", "Comércio; Reparação de Veículos Automotores e Motocicletas", 1410, 1496, 1584),
    ("ICMS", "Lei 11.764/2022", "Alteração de alíquota", "Comércio; Reparação de Veículos Automotores e Motocicletas", 41844951, 44389124, 46988374),
    ("ICMS", "Lei 11.246/2021", "Crédito presumido", "Artes, Cultura, Esporte e Recreação", 70000000, 70000000, 70000000),
    ("ICMS", "Lei 12.022/2023", "Modificação da base de cálculo", "Eletricidade e Gás", 125158665, 132768312, 140542693),
    ("ICMS", "Lei 11.813/2023", "Alteração de alíquota", "Alojamento e Alimentação", 1799235, 1908629, 2020390),
    ("ICMS", "Lei 11.994/2023", "Crédito presumido", "Indústrias Extrativas", 5125649, 5437288, 5755674),
    ("ICMS", "Lei 12.185/2024", "Crédito presumido", "Transporte, Armazenagem e Correio", 3650794, 3872762, 4099535),
    ("ICMS", "Lei 12.203/2024", "Crédito presumido", "Indústrias Extrativas", 876500, 929792, 984236),
    ("ICMS", "Lei 12.320/2024", "Alteração de alíquota", "Saúde Humana e Serviços Sociais", 1303, 1382, 1463),
    ("ICMS", "Lei 12.186/2024", "Alteração de alíquota", "Comércio; Reparação de Veículos Automotores e Motocicletas", 15255885, 16183443, 17131081),
    ("ICMS", "Lei 12.308/2024", "Modificação da base de cálculo", "Regimes Especiais", 4064509, 4311631, 4564103),
    ("ICMS", "Lei 12.317/2024", "Alteração de alíquota", "Eletricidade e Gás", 0, 0, 0),
    ("ICMS", "Lei 12.257/2024", "Modificação da base de cálculo", "Indústrias Extrativas", 67536530, 71642751, 75837864),
    ("ICMS", "Lei 12.316/2024", "Alteração de alíquota", "Eletricidade e Gás", 7006428, 7432419, 7867632),
    ("ICMS", "Lei 12.202/2024", "Isenção", "Indústria de Transformação", 5314613, 5637742, 5967865),
    ("ICMS", "Lei 12.322/2024", "Isenção", "Eletricidade e Gás", 0, 0, 0),
    ("ICMS", "Lei 12.187/2024", "Isenção", "Organismos Internacionais e Outras Instituições Extraterritoriais", 0, 0, 0),
    ("IPVA", "Lei 6.999/2001", "Modificação da base de cálculo", "Veículos 1º emplacamento", 24207296, 25679100, 27182765),
    ("IPVA", "Lei 6.999/2001", "Alteração de alíquota", "Locadoras", 17476989, 18539589, 19625194),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Veículos (mais de 15 anos)", 214305590, 227335369, 240647219),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Deficiente físico", 14129966, 14989068, 15866768),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Veículo oficial", 10666811, 11315353, 11977935),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Perda, roubo ou sinistro", 7621802, 8085208, 8558645),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Táxis", 4857355, 5152683, 5454403),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Ônibus urbanos", 712, 755, 799),
    ("IPVA", "Lei 6.999/2001", "Isenção", "Outros veículos (b)", 2023191, 2146202, 2271874),
    ("TAXAS", "Lei 11.863/2023", "Alteração de alíquota", "Transporte, Armazenagem e Correio", 1688610, 1791277, 1896167),
    ("OUTROS", "", "Outros incentivos (c)", "Novos incentivos que podem ser aprovados no exercício", 200000000, 200000000, 200000000),
]
SUB26 = {
    "ICMS": (14375999510, 15245804280, 16134438676),
    "IPVA": (295289712, 313243326, 331585602),
    "TAXAS": (1688610, 1791277, 1896167),
    "OUTROS": (200000000, 200000000, 200000000),
    "TOTAL": (14872977831, 15760838883, 16667920445),
}

# ---------------------------------------------------------------------------
# Safras anteriores: só os subtotais, que é o que importa para mostrar a quebra de série.
# Em R$ milhares nas LDO 2024 e 2025; convertidos para R$.
# ---------------------------------------------------------------------------
SAFRAS_ANTIGAS = {
    "LDO 2024 (base EFD 2022, Focus mar/2023)": {
        "anos": [2023, 2024, 2025, 2026],
        "icms": [2871570e3, 3077246e3, 3294308e3, 3729110e3],
        "total": [3097596e3, 3320660e3, 3555471e3, 4009666e3],
        "atacadista": [2082131e3, 2198320e3, 2322930e3, 2647244e3],
        "varejo_nao_presencial": [485044e3, 512111e3, 541139e3, 616690e3],
        "invest": None,
    },
    "LDO 2025 (base EFD 2023, Focus fev/2024)": {
        "anos": [2025, 2026, 2027],
        "icms": [3162214e3, 3335007e3, 3517425e3],
        "total": [3600339e3, 3786396e3, 3982816e3],
        "atacadista": [2262185e3, 2388188e3, 2521211e3],
        "varejo_nao_presencial": [554423e3, 585304e3, 617905e3],
        "invest": None,
    },
}

# ---------------------------------------------------------------------------
# Regionalização da LDO 2027 (R$ 1,00), por microrregião de planejamento (Lei 9.768/2011).
# Ordem: Caparaó, Central Serrana, Central Sul, Centro-Oeste, Litoral Sul, Metropolitana,
#        Nordeste, Noroeste, Rio Doce, Sudoeste Serrana
# ---------------------------------------------------------------------------
MICRORREGIOES = ["Caparaó", "Central Serrana", "Central Sul", "Centro-Oeste", "Litoral Sul",
                 "Metropolitana", "Nordeste", "Noroeste", "Rio Doce", "Sudoeste Serrana"]
REG27 = {
    "Atacadista": ([67323078, 16759221, 81195259, 91387881, 13946067, 6472238639, 30432783, 4892193, 78243572, 4013130], 6860431823),
    "Varejo Não Presencial": ([4719960, 115162, 5958178, 4809499, 1022270, 1830619429, 12164803, 0, 5318509, 0], 1864727811),
    "Rochas Ornamentais": ([0, 0, 52391202, 8569571, 2551292, 24467154, 0, 9623417, 533853, 948405], 99084894),
    "Metalmecânica": ([139016, 14736, 3906948, 2378121, 10640, 70112522, 328760, 0, 11036816, 0], 87927560),
    "Outros (a)": ([985105, 92577, 653613, 5390, 0, 19601031, 308076, 51333, 17869329, 0], 39566455),
    "Bares e Restaurantes": ([31366, 74222, 2328559, 440872, 292669, 38797050, 391684, 0, 3826675, 1228054], 47411150),
    "Vestuário": ([1214370, 0, 0, 58273216, 0, 6821426, 0, 0, 1409711, 1051544], 68770267),
    "Indústrias/Importadoras (INVEST)": ([1338204, 1813315, 12672725, 61919116, 474002, 6541739018, 41852013, 2852161, 365852990, 9949268], 7040462810),
}

# ---------------------------------------------------------------------------
# ICMS previsto e realizado, R$ mil (PLDO 2027, p. 68-69; Leis orçamentárias e BI SEFAZ)
# ---------------------------------------------------------------------------
ICMS_PREV_REAL = {
    2008: (6053564, 6916205), 2009: (6892977, 6398030), 2010: (6691019, 7122150),
    2011: (7458076, 8409372), 2012: (8765024, 9060725), 2013: (7697904, 8605921),
    2014: (9100100, 8706067), 2015: (9114141, 9009854), 2016: (9739866, 8605404),
    2017: (8912680, 9045423), 2018: (8826458, 10057576), 2019: (9873918, 11193317),
    2020: (10820555, 11686647), 2021: (11513882, 15133760), 2022: (15028983, 16466910),
    2023: (16720729, 17820869), 2024: (18851694, 20987371), 2025: (22356469, 22780947),
}


def soma_por_tributo(linhas, idx):
    s = {}
    for linha in linhas:
        s[linha[0]] = s.get(linha[0], 0) + linha[4 + idx]
    return s


TOL = 5  # R$; as células publicadas são arredondadas, e a soma de dezenas de linhas difere em R$ 1 a 3
MAX_DESVIO = [0]


def confere(nome, linhas, sub):
    erros = []
    for i in range(3):
        s = soma_por_tributo(linhas, i)
        for trib, pub in sub.items():
            if trib == "TOTAL":
                calc = sum(s.values())
            else:
                calc = s.get(trib, 0)
            MAX_DESVIO[0] = max(MAX_DESVIO[0], abs(calc - pub[i]))
            if abs(calc - pub[i]) > TOL:
                erros.append(f"{nome} {trib} col{i}: soma das linhas {calc:,} != publicado {pub[i]:,} (dif {calc - pub[i]:,})")
    return erros


def main():
    erros = confere("LDO 2027", L27, SUB27) + confere("LDO 2026", L26, SUB26)
    for seg, (vals, tot) in REG27.items():
        MAX_DESVIO[0] = max(MAX_DESVIO[0], abs(sum(vals) - tot))
        if abs(sum(vals) - tot) > TOL:
            erros.append(f"Regionalização {seg}: soma {sum(vals):,} != total {tot:,}")
        # o total regional deve bater com a linha do Demonstrativo VII de 2027
    linhas27 = {l[3]: l[4] for l in L27 if l[0] == "ICMS"}
    for seg, (_, tot) in REG27.items():
        if linhas27.get(seg) != tot:
            erros.append(f"Regionalização {seg}: total regional {tot:,} != linha do demonstrativo {linhas27.get(seg)}")
    if erros:
        raise SystemExit("Falhas de conferência:\n" + "\n".join(erros))

    OUT.mkdir(exist_ok=True)

    def pack(linhas, anos):
        return [dict(tributo=l[0], instrumento_legal=l[1], modalidade=l[2], setor=l[3],
                     valores={str(a): l[4 + i] for i, a in enumerate(anos)}) for l in linhas]

    icms27 = [l for l in L27 if l[0] == "ICMS"]
    total_icms_27 = SUB27["ICMS"][0]
    big3 = sum(l[4] for l in icms27 if l[3] in ("Atacadista", "Varejo Não Presencial", "Indústrias/Importadoras (INVEST)"))
    metro = {seg: vals[5] for seg, (vals, _) in REG27.items()}
    metro_total = sum(metro.values())
    reg_total = sum(tot for _, tot in REG27.values())
    regional_soma = [sum(vals[i] for vals, _ in REG27.values()) for i in range(len(MICRORREGIOES))]

    real25 = ICMS_PREV_REAL[2025][1] * 1000
    # A LDO 2027 corrige a base de 2025 (EFD) por IPCA e PIB até 2027. Para recuar o gasto de 2027
    # até 2025 e compará-lo com o ICMS realizado de 2025, desfaz-se essa correção com o IPCA e o PIB
    # real de 2026 e 2027 da trajetória macro do modelo do site (data/ibs-projecao-nacional.json).
    macro = {m["ano"]: m for m in json.loads((HERE / "ibs-projecao-nacional.json").read_text(encoding="utf-8"))["macro_path"]}
    fator = 1.0
    for a in (2026, 2027):
        fator *= (1 + macro[a]["ipca_pct"]) * (1 + macro[a]["pib_real_pct"])
    gt25_aprox = SUB27["ICMS"][0] / fator

    dados = {
        "_meta": {
            "descricao": "Gasto tributário (renúncia de receita) do Espírito Santo no Demonstrativo VII do Anexo de Metas Fiscais das LDO 2024 a 2027, e dados auxiliares para o estudo do gasto tributário de ICMS frente à transição para o IBS.",
            "unidade": "R$ correntes (valores inteiros)",
            "fontes": {
                "PLDO 2027": "https://planejamento.es.gov.br/media/Or%C3%A7amento/Lei%20de%20Diretrizes%20Or%C3%A7ament%C3%A1rias/PLDO_2027.pdf",
                "LDO 2026": "https://planejamento.es.gov.br/media/Or%C3%A7amento/Lei%20de%20Diretrizes%20Or%C3%A7ament%C3%A1rias/LDO%202026.pdf",
                "LDO 2025": "https://planejamento.es.gov.br/media/Or%C3%A7amento/Lei%20de%20Diretrizes%20Or%C3%A7ament%C3%A1rias/LDO%202025.pdf",
                "LDO 2024": "https://planejamento.es.gov.br/media/Or%C3%A7amento/Lei%20de%20Diretrizes%20Or%C3%A7ament%C3%A1rias/LDO%202024.pdf",
            },
            "metodo_sefaz": "Gasto tributário de ICMS = ICMS potencial - ICMS real. ICMS potencial = faturamento do beneficiário x índice de recolhimento (ICMS recolhido / faturamento) das empresas do mesmo CNAE principal no regime normal, sem benefício. Para Compete Atacadista, Vendas Não Presenciais e INVEST, soma dos ajustes nos registros E110, E111 e C197 da EFD (malha fiscal). Base: EFD do ano anterior à LDO, corrigida por IPCA e PIB (Focus).",
            "transcricao": "As tabelas do PLDO 2027 (p. 60) e da LDO 2026 (p. 45) são imagens; os valores foram transcritos à mão e conferidos contra subtotais e totais publicados (build-gasto-tributario-es.py falha se a soma diferir mais de R$ 5; o desvio observado é de até R$ 3, por arredondamento das células).",
            "gerado_por": "data/build-gasto-tributario-es.py",
        },
        "ldo_2027": {"anos": [2027, 2028, 2029], "emitido": "11/03/2026 (BI/SEFAZ-GEARC)", "linhas": pack(L27, [2027, 2028, 2029]),
                     "subtotais": {k: dict(zip(["2027", "2028", "2029"], v)) for k, v in SUB27.items()},
                     "empresas_compete_2025": 3600},
        "ldo_2026": {"anos": [2026, 2027, 2028], "emitido": "21/03/2025 (BI/SEFAZ-GEARC)", "linhas": pack(L26, [2026, 2027, 2028]),
                     "subtotais": {k: dict(zip(["2026", "2027", "2028"], v)) for k, v in SUB26.items()},
                     "empresas_compete_2024": 3384},
        "safras_anteriores_subtotais": SAFRAS_ANTIGAS,
        "regionalizacao_ldo_2027": {
            "microrregioes": MICRORREGIOES,
            "por_segmento": {seg: dict(zip(MICRORREGIOES, vals)) for seg, (vals, _) in REG27.items()},
            "total_por_segmento": {seg: tot for seg, (_, tot) in REG27.items()},
            "total_por_microrregiao": dict(zip(MICRORREGIOES, regional_soma)),
            "nota": "Regionaliza a renúncia 2027 apenas dos segmentos Compete e INVEST (R$ 16,1 bi dos R$ 16,4 bi de ICMS em 2027); as demais linhas de ICMS não são regionalizadas.",
        },
        "icms_previsto_realizado_mil": {str(a): {"previsto": p, "realizado": r} for a, (p, r) in ICMS_PREV_REAL.items()},
        "derivados": {
            "gt_icms_2027": total_icms_27,
            "tres_maiores_programas_2027": {"valor": big3, "participacao_no_gt_icms": big3 / total_icms_27,
                                           "programas": ["Compete Atacadista", "Compete Varejo Não Presencial", "INVEST"]},
            "metropolitana_participacao_nos_segmentos_regionalizados": metro_total / reg_total,
            "gt_icms_2027_sobre_icms_realizado_2025": total_icms_27 / real25,
            "gt_icms_2025_aproximado": {"valor": gt25_aprox, "metodo": "GT de 2027 dividido pelo IPCA e pelo PIB real de 2026 e 2027 da trajetória macro do modelo (Focus ago/2026), que desfaz a correção que a LDO aplica sobre a base de 2025",
                                         "sobre_icms_realizado_2025": gt25_aprox / real25,
                                         "sobre_icms_potencial_2025": gt25_aprox / (gt25_aprox + real25)},
            "quebra_de_serie": {
                "icms_ldo_2025_primeiro_ano": 3162214e3, "icms_ldo_2026_primeiro_ano": SUB26["ICMS"][0],
                "razao": SUB26["ICMS"][0] / 3162214e3,
                "icms_realizado_crescimento_2023_2025": ICMS_PREV_REAL[2025][1] / ICMS_PREV_REAL[2023][1] - 1,
                "leitura": "A LDO 2026 passou a medir Atacadista, Vendas Não Presenciais e INVEST pelos ajustes da EFD (E110/E111/C197) e incluiu o INVEST (R$ 5,8 bi), ausente das safras anteriores. O salto de 4,5 vezes não corresponde a variação econômica: o ICMS realizado cresceu 28% entre 2023 e 2025."
            },
            "revisao_entre_safras_2027": {"ldo_2026": SUB26["ICMS"][1], "ldo_2027": SUB27["ICMS"][0], "variacao": SUB27["ICMS"][0] / SUB26["ICMS"][1] - 1},
        },
    }
    (OUT / "gasto-tributario-es.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")

    with open(OUT / "demonstrativo-vii.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["safra", "ano", "tributo", "instrumento_legal", "modalidade", "setor", "valor_rs"])
        for safra, linhas, anos in (("LDO 2026", L26, [2026, 2027, 2028]), ("LDO 2027", L27, [2027, 2028, 2029])):
            for l in linhas:
                for i, a in enumerate(anos):
                    w.writerow([safra, a, l[0], l[1], l[2], l[3], l[4 + i]])
    with open(OUT / "regionalizacao-ldo-2027.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["segmento", "microrregiao", "renuncia_2027_rs"])
        for seg, (vals, _) in REG27.items():
            for m, v in zip(MICRORREGIOES, vals):
                w.writerow([seg, m, v])
    with open(OUT / "icms-previsto-realizado-es.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ano", "previsto_rs_mil", "realizado_rs_mil"])
        for a, (p, r) in ICMS_PREV_REAL.items():
            w.writerow([a, p, r])

    d = dados["derivados"]
    print(f"Conferência: somas das linhas fecham com os subtotais e totais publicados (desvio máximo R$ {MAX_DESVIO[0]}, arredondamento).")
    print(f"GT de ICMS 2027: R$ {total_icms_27/1e9:.2f} bi; três maiores programas: {d['tres_maiores_programas_2027']['participacao_no_gt_icms']:.1%}")
    print(f"Metropolitana nos segmentos regionalizados: {d['metropolitana_participacao_nos_segmentos_regionalizados']:.1%}")
    print(f"GT 2027 / ICMS realizado 2025: {d['gt_icms_2027_sobre_icms_realizado_2025']:.1%}")
    a = d["gt_icms_2025_aproximado"]
    print(f"GT 2025 aproximado: R$ {a['valor']/1e9:.2f} bi = {a['sobre_icms_realizado_2025']:.1%} do realizado; {a['sobre_icms_potencial_2025']:.1%} do potencial")
    q = d["quebra_de_serie"]
    print(f"Quebra de série: {q['razao']:.1f}x entre a primeira linha da LDO 2025 e a da LDO 2026")


if __name__ == "__main__":
    main()
