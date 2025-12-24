# Eduardo Araujo - Site Pessoal

Site pessoal profissional de Eduardo Araujo - Economista, Consultor do Tesouro Estadual do Espirito Santo, Professor na Fucape Business School e Mestre em Politicas Publicas pela Universidade de Oxford.

## Estrutura do Projeto

```
site-eduardo/
├── index.html              # Pagina principal
├── css/
│   └── styles.css          # Estilos do site
├── js/
│   └── main.js             # JavaScript principal
├── assets/
│   └── images/             # Imagens do site
├── materiais/              # PDFs para download
│   ├── teoria-monopolios.pdf
│   ├── transferencia-renda.pdf
│   ├── economia-institucional.pdf
│   └── avaliacao-politicas.pdf
├── .github/
│   └── workflows/
│       └── deploy.yml      # CI/CD para GitHub Pages
├── .gitignore
└── README.md
```

## Funcionalidades

- Design responsivo (mobile-first)
- Tema escuro elegante com detalhes dourados
- Animacoes suaves com Intersection Observer
- Menu mobile com acessibilidade
- SEO otimizado com Schema.org
- Suporte a Google Analytics
- Deploy automatico via GitHub Pages

## Configuracao

### 1. Google Analytics

Substitua `G-XXXXXXXXXX` pelo seu ID do Google Analytics em `index.html`:

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=SEU-ID-AQUI"></script>
<script>
    gtag('config', 'SEU-ID-AQUI');
</script>
```

### 2. Materiais para Download

Adicione os arquivos PDF na pasta `materiais/`:
- `teoria-monopolios.pdf`
- `transferencia-renda.pdf`
- `economia-institucional.pdf`
- `avaliacao-politicas.pdf`

### 3. Imagem de Perfil

A imagem atual e carregada da Oxford. Para usar uma imagem local:

1. Salve sua foto em `assets/images/profile.jpg`
2. Atualize o src no `index.html`:
```html
<img src="assets/images/profile.jpg" alt="Eduardo Araujo">
```

## Deploy

### GitHub Pages (Automatico)

O site e publicado automaticamente via GitHub Actions quando voce faz push para a branch `main`.

1. Va em **Settings > Pages**
2. Em **Source**, selecione **GitHub Actions**
3. O site estara disponivel em: `https://seuusuario.github.io/site-eduardo/`

### Dominio Personalizado

1. Adicione um arquivo `CNAME` com seu dominio:
```
eduardoaraujo.com.br
```

2. Configure o DNS do seu dominio:
   - Tipo A: `185.199.108.153`
   - Tipo A: `185.199.109.153`
   - Tipo A: `185.199.110.153`
   - Tipo A: `185.199.111.153`
   - Ou CNAME: `seuusuario.github.io`

## Desenvolvimento Local

Para visualizar o site localmente:

```bash
# Usando Python
python -m http.server 8000

# Usando Node.js (npx)
npx serve

# Usando PHP
php -S localhost:8000
```

Acesse: `http://localhost:8000`

## Secoes do Site

1. **Hero** - Apresentacao com foto e credenciais
2. **Sobre** - Biografia e conquistas
3. **Areas** - Areas de pesquisa e atuacao
4. **Publicacoes** - Artigos recentes com links
5. **Materiais** - PDFs para download
6. **Midia** - Participacoes em eventos
7. **Visao** - Filosofia e valores
8. **Contato** - Links para contato

## Tecnologias

- HTML5 semantico
- CSS3 com variaveis customizadas
- JavaScript ES6+ (vanilla)
- Intersection Observer API
- Schema.org para SEO
- GitHub Actions para CI/CD

## Acessibilidade

- Skip link para navegacao por teclado
- ARIA labels em elementos interativos
- Suporte a preferencia de movimento reduzido
- Alto contraste entre texto e fundo
- Foco visivel em elementos interativos

## Licenca

Todos os direitos reservados - Eduardo Araujo
