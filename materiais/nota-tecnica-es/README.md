# Nota técnica: impactos da transição do ICMS para o IBS sobre a receita do Espírito Santo, 2029 a 2033

Esta pasta guarda a versão de trabalho da nota técnica, assinada por Eduardo Araújo, em LaTeX e com formatação ABNT. O arquivo principal é `nota-tecnica-impacto-es.tex`, e `nota-tecnica-impacto-es.pdf` é a última versão compilada. A metodologia, as equações, as tabelas e os gráficos seguem o artigo sobre o Paraná (branch `artigo-parana-fonte`, pasta `artigos/parana-ibs/`), com o Espírito Santo no lugar do Paraná e sem a parte municipal.

Nenhum número do texto é digitado à mão. O script `gerar-tabelas.py` lê os dados do site (pasta `data/` na raiz do repositório, incluindo `data/referencias-externas/NT_COMSEFAZ_RefTributaria_v3.md`, usada na validação externa) e escreve em `tabelas/` as tabelas, os gráficos (pgfplots) e o arquivo `numeros.tex`, que define as macros `\Num...` usadas no texto. Quando o modelo ou os dados mudarem, basta rodar o script de novo e recompilar, e os valores da nota se atualizam.

Para regenerar e compilar, a partir desta pasta: `python3 gerar-tabelas.py` e depois `pdflatex nota-tecnica-impacto-es.tex`, duas vezes, para resolver as referências cruzadas. Os arquivos auxiliares (`.aux`, `.log`, `.out`) podem ser apagados depois.
