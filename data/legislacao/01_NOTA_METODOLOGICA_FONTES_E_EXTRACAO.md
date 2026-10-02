# Nota metodológica sobre fontes e extração

Este pacote adota uma arquitetura conservadora para uso em projeto do ChatGPT: texto legal literal em primeiro plano, recortes literais para os blocos de maior interesse e índice mínimo sem interpretação.

## Preferência metodológica

A preferência técnica seria extrair o texto diretamente do HTML oficial do Planalto, porque o HTML tende a preservar melhor a estrutura textual da norma do que PDFs convertidos automaticamente. No entanto, durante a preparação deste pacote, a abertura direta dos links do Planalto apresentou erro de decodificação Unicode no ambiente de navegação utilizado.

Por esse motivo, este pacote usa fontes oficiais alternativas e documenta a origem de cada arquivo.

## Fontes utilizadas neste pacote

- Lei Complementar nº 227/2026: texto literal baseado na Legislação Informatizada da Câmara dos Deputados, fonte oficial que disponibiliza publicação original, texto atualizado em HTML, PDF e DOCX.
- Constituição Federal e ADCT atualizados pela EC 132/2023: recortes literais baseados na Constituição compilada pelo Senado Federal até a EC 132/2023.
- Links do Planalto: mantidos como referência oficial primária, mas não usados como extração direta nesta versão por falha técnica de decodificação.

## Como usar no projeto

Use os arquivos de texto literal como fonte primária. O arquivo de índice serve apenas para ajudar a busca interna e não deve ser citado como fundamento jurídico.

Para máxima robustez futura, recomenda-se substituir os arquivos integrais por versões extraídas diretamente do HTML do Planalto, caso a extração seja feita em ambiente que consiga ler corretamente a codificação das páginas.
