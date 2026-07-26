NOTA TÉCNICA Nº 02/2026 — VERSÃO 22

Arquivo principal:
  Nota_Tecnica_02_2026_Coeficientes_IBS_Retido_v22.tex

Compilação recomendada:
  xelatex Nota_Tecnica_02_2026_Coeficientes_IBS_Retido_v22.tex
  xelatex Nota_Tecnica_02_2026_Coeficientes_IBS_Retido_v22.tex

Reprodução das figuras:
  python3 gerar_figura1_trajetoria_es.py
  python3 gerar_mapa_ufs.py

Principais arquivos de dados:
  table1_v22.csv                     memória anual do cálculo estadual
  cpt_ufs_v22.csv                    resultados completos por unidade da Federação
  cpt_municipios_es_v22.csv          resultados completos dos municípios capixabas
  cpt_ufs.csv                        base formatada do Anexo A e do mapa
  cpt_municipios_es_mainpage.csv     base formatada do Anexo B
  comparacao_sefaz_es_ba_ufs.csv     comparação apresentada no Anexo C

Critério metodológico:
  - receita estadual anual = ICMS comum - cota-parte municipal + FECOP;
  - utiliza-se preferencialmente a cota-parte registrada pelo Estado no DCA;
  - na ausência desse registro, aplica-se subsidiariamente 25% ao ICMS comum;
  - o FECOP, registrado em conta própria, integra integralmente o componente estadual;
  - o agregado nacional reúne ICMS comum, FECOP e ISS;
  - para o Distrito Federal, ICMS, FECOP e ISS compõem um coeficiente único.

Comparação técnica:
  A estimativa comparativa foi fornecida por Daniel Lanza, auditor fiscal da
  Sefaz-BA, como material técnico não publicado. Os exercícios foram produzidos
  em momentos distintos; esta Nota incorpora informações extraídas e atualizadas
  até julho de 2026. Nenhum dos dois exercícios incorpora as contribuições para
  fundos estaduais previstas no art. 115, I, "b", da LC nº 227/2026.

Fontes:
  DCA/Siconfi, exercícios de 2019 a 2025; SIOPE e SIOPS, conforme indicado no
  exercício comparativo.

Os valores exibidos no documento são arredondados. Os cálculos utilizam os valores
sem arredondamento constantes das bases CSV.
