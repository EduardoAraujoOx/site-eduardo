#!/usr/bin/env node

/**
 * Article Generator Script
 * Generates individual HTML pages for each article from artigos.json
 */

const fs = require('fs');
const path = require('path');

// Read the template
const templatePath = path.join(__dirname, 'publicacoes', 'template.html');
const template = fs.readFileSync(templatePath, 'utf8');

// Read the articles data
const artigosPath = path.join(__dirname, 'data', 'artigos.json');
const artigosData = JSON.parse(fs.readFileSync(artigosPath, 'utf8'));

// Function to generate HTML for tags
function generateTagsHTML(tags) {
    return tags.map(tag => `<span class="article-tag">${tag}</span>`).join('\n                    ');
}

// Function to replace placeholders in template
function generateArticlePage(article) {
    let html = template;

    // Replace all placeholders
    const replacements = {
        '{{TITULO}}': article.titulo,
        '{{SUBTITULO}}': article.subtitulo || article.resumo,
        '{{RESUMO}}': article.resumo,
        '{{SLUG}}': article.slug,
        '{{AUTOR}}': article.autor,
        '{{AUTOR_CARGO}}': article.autorCargo,
        '{{DATA_ISO}}': article.data,
        '{{DATA_FORMATADA}}': article.dataFormatada,
        '{{CATEGORIA}}': article.categoria,
        '{{TEMPO_LEITURA}}': article.tempoLeitura,
        '{{IMAGEM}}': article.imagem,
        '{{IMAGEM_ALT}}': article.imagemAlt,
        '{{TAGS}}': article.tags.join(', '),
        '{{TAGS_HTML}}': generateTagsHTML(article.tags),
        '{{LINK_EXTERNO}}': article.linkExterno,
        '{{CONTEUDO}}': article.conteudo || ''
    };

    for (const [placeholder, value] of Object.entries(replacements)) {
        html = html.split(placeholder).join(value);
    }

    return html;
}

// Generate a page for each article
const publicacoesDir = path.join(__dirname, 'publicacoes');
if (!fs.existsSync(publicacoesDir)) {
    fs.mkdirSync(publicacoesDir, { recursive: true });
}

let generated = 0;
let errors = 0;

artigosData.artigos.forEach(article => {
    try {
        const html = generateArticlePage(article);
        const filePath = path.join(publicacoesDir, `${article.slug}.html`);
        fs.writeFileSync(filePath, html, 'utf8');
        console.log(`✓ Generated: ${article.slug}.html`);
        generated++;
    } catch (error) {
        console.error(`✗ Error generating ${article.slug}.html:`, error.message);
        errors++;
    }
});

console.log(`\n📄 Summary:`);
console.log(`   Generated: ${generated} pages`);
console.log(`   Errors: ${errors}`);
console.log(`   Total articles: ${artigosData.artigos.length}\n`);
