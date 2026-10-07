# Artigo sobre o Paraná e o IBS

Versão de trabalho do artigo (prêmio do Tesouro do Pará). O arquivo `artigo-parana-ibs.docx` é a versão limpa e deve ser editado diretamente no Word. Cada nova versão entra por commit, e o histórico do Git guarda as anteriores.

Os números do texto vêm do modelo do repositório (`data/*.py` → JSON). Quando o modelo mudar, a pasta `pipeline/` mostra como as tabelas, o Gráfico 2 (leque de sensibilidade) e o mapa foram regenerados na última rodada: `fig_v5.py` gera o gráfico e `sens_v5.json`; `refresh_v5.py` (que importa trechos de `refresh_v3_p1.py`) reescreve tabelas e números no docx. Os scripts foram escritos como patches sobre a versão anterior do documento e têm caminhos fixos do ambiente em que rodaram, então servem como referência de método, não como comando de um passo.

`figuras/` guarda as duas imagens inseridas no documento (Gráfico 2 e mapa de 2033).
