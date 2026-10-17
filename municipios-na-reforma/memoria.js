/* Memória de cálculo do município.
   Funções portadas SEM alteração de texto, fórmula ou ordem de passos de
   painel-reforma-tributaria.html (fmtExato, fmtNum2, passoHtml, op, confere,
   memoHistoricoHtml, memoDestinoMuniHtml, memoSeguroHtml). A conta é a mesma
   do painel, o que dá ao portal a mesma auditabilidade.
   ATENÇÃO: é uma cópia. Se o painel mudar o texto jurídico ou a fórmula de
   alguma dessas funções, atualizar aqui também (ou extrair um módulo comum). */
(function () {
'use strict';
const ANOS = [2029, 2030, 2031, 2032, 2033];
let MEMO_NAC = null;
function fmtPctPlain(v, dec){ return v==null ? '—' : v.toLocaleString('pt-BR',{maximumFractionDigits:dec==null?4:dec})+'%'; }

function fmtExato(v){
    return (v==null || !isFinite(v)) ? '—'
        : 'R$ ' + v.toLocaleString('pt-BR',{minimumFractionDigits:2, maximumFractionDigits:2});
}

function fmtNum2(v, dec){
    return (v==null || !isFinite(v)) ? '—'
        : v.toLocaleString('pt-BR',{minimumFractionDigits:dec, maximumFractionDigits:dec});
}

function passoHtml(n, titulo, corpo){
    return `<div class="passo"><div class="passo-n">${n}</div><div><h4>${titulo}</h4>${corpo}</div></div>`;
}

function op(sinal){ return `<span class="op">${sinal}</span>`; }

function confere(calculado, publicado, dec){
    if (publicado == null || !isFinite(publicado)) return '';
    const bate = Math.abs(calculado - publicado) < 1e-9;
    return `<span class="formula-nota">${bate
        ? 'Confere com o coeficiente publicado nas demais abas do painel.'
        : 'O painel publica ' + fmtPctPlain(publicado, dec || 6) + '.'}</span>`;
}

function memoHistoricoHtml(ctx){
    // a média da lei é de 2019 a 2026: o ano estimado (2026) entra na tabela quando o painel o traz
    const anos = MEMO_NAC.anos_historicos.concat(MEMO_NAC.ano_estimado_na_media && ctx.historico[String(MEMO_NAC.ano_estimado_na_media)] ? [MEMO_NAC.ano_estimado_na_media] : []);
    const nAnosTxt = anos.length === 8 ? 'oito' : 'sete';
    // anos preenchidos fora da DCA (RREO anual ou estimativa a partir do ano anterior) levam o selo da fonte
    const seloOrigem = a => {
        const o = ctx.historico[String(a)] && ctx.historico[String(a)].origem; if (!o) return '';
        const f = [o.iss, o.cota].filter(x => x && x !== 'dca');
        return f.length ? (f.every(x => x === 'rreo') ? ' (RREO)' : f.some(x => x === 'estimativa_serie') ? ' (est.)' : '') : '';
    };
    const rotuloAno = a => a === MEMO_NAC.ano_estimado_na_media ? a + (ctx.origem2026 === 'rreo' ? ' (RREO)' : ' (est.)') : a + seloOrigem(a);
    const totalBr = MEMO_NAC.total_br_2025;
    const serie = anos.map(a => ctx.historico[String(a)] || null);
    const valores = serie.map(h => h ? h[ctx.campoTotal] : null);
    const validos = valores.filter(v => v != null);
    const media = validos.length ? validos.reduce((x,y)=>x+y, 0) / anos.length : null;
    const coef = media != null ? media / totalBr * 100 : null;
    const ref2025 = ctx.historico['2025'] ? ctx.historico['2025'][ctx.campoTotal] : null;
    // Quando 2025 falta no SICONFI (município novo, ausente da DCA daquele ano),
    // a rotina usa o próprio φCPT no lugar da participação neutra, em vez de
    // deixar o contrafactual desse ente sem base nenhuma. É a mesma regra por
    // trás do selo "estimativa aproximada" que aparece nas demais abas.
    const neutroAproximado = ref2025 == null && coef != null;
    const neutro = ref2025 != null ? ref2025 / totalBr * 100 : (neutroAproximado ? coef : null);

    const colunas = ctx.colunas;
    // Com os fatores de ajuste (ctx.fatores), a tabela mostra a conta inteira: valor declarado, fator do ano e referência em R$ de 2025.
    const fatores = ctx.fatores || null;
    const cab = fatores
        ? colunas.map(c => c.total ? '' : `<th class="num">${c.rotulo}</th>`).join('') + '<th class="num">= Referência (valores correntes)</th><th class="num">× Fator de ajuste</th><th class="num">= Referência em R$ de 2025</th>'
        : colunas.map(c => `<th class="num">${c.rotulo}</th>`).join('');
    const linhas = anos.map((a,i) => {
        const h = serie[i];
        const fa = fatores ? fatores[String(a)] : null;
        const valor = (c) => { const v = h ? h[c.campo] : null; return v == null ? v : (fatores && fa ? v / fa : v); };
        const cels = fatores
            ? colunas.filter(c => !c.total).map(c => `<td class="num">${fmtExato(valor(c))}</td>`).join('')
              + `<td class="num">${fmtExato(h ? (fa ? h[ctx.campoTotal] / fa : h[ctx.campoTotal]) : null)}</td>`
              + `<td class="num">${fa ? fmtNum2(fa, 4) : 'n.a.'}</td><td class="num" style="font-weight:700">${fmtExato(h ? h[ctx.campoTotal] : null)}</td>`
            : colunas.map(c => {
                const v = h ? h[c.campo] : null;
                return `<td class="num"${c.total ? ' style="font-weight:700"' : ''}>${fmtExato(v)}</td>`;
            }).join('');
        return `<tr><td>${rotuloAno(a)}</td>${cels}</tr>`;
    }).join('');

    const soma = validos.reduce((x,y)=>x+y, 0);

    return `
    <div class="panel">
        <h3>Coeficiente histórico, φ<sup>CPT</sup></h3>
        <p class="panel-sub">É a fatia do ente no critério de origem, que rege 90% do IBS em 2033 e vai cedendo lugar ao destino até 2078 (ADCT art. 131, §1º). A base é a receita de referência média de ${nAnosTxt} anos, definida no art. 115 da LC 227/2026.</p>

        ${passoHtml(1, 'Receita de referência, ano a ano', `
            <p>${ctx.descricaoReferencia}</p>
            <div class="table-wrap" style="margin-top:0.6rem">
                <table class="data" style="font-size:0.78rem"><thead><tr><th>Ano</th>${cab}</tr></thead><tbody>${linhas}</tbody></table>
            </div>
            <p style="margin-top:0.5rem">Os valores de cada ano são levados a reais de 2025, para que anos distantes possam ser somados${fatores ? ': a referência corrente multiplicada pelo fator de ajuste do ano (a variação nominal da arrecadação total de ICMS e ISS do país, LC 227, art. 115, §2º) dá a última coluna.' : '.'}${anos.length === 8 ? (ctx.origem2026 === 'rreo' ? ' Em 2026, ainda sem a DCA, o ISS é o observado no RREO de setembro de 2025 a agosto de 2026 e a cota-parte é a de 2025 ajustada pelo crescimento de janeiro a agosto, também do RREO.' : ' Em 2026, ainda sem a DCA, este município não publica o Anexo 3 do RREO e mantém a posição relativa de 2025 no estado.') : ''}</p>`)}

        ${passoHtml(2, 'Média dos ' + nAnosTxt + ' anos', `
            <div class="formula">${fmtExato(soma)} ${op('÷')} ${anos.length} ${op('=')} <span class="res">${fmtExato(media)}</span>
                <span class="formula-nota">O dividendo é a soma da última coluna da tabela acima.</span></div>`)}

        ${passoHtml(3, 'Divisão pelo total nacional', `
            <p>O denominador é a receita de referência de todos os entes do país somada, no mesmo conceito e na mesma moeda.</p>
            <div class="formula">${fmtExato(media)} ${op('÷')} ${fmtExato(totalBr)} ${op('=')} <span class="res">${fmtPctPlain(coef, 6)}</span>
                ${confere(coef, ctx.coefPublicado)}</div>`)}

        ${passoHtml(4, 'Participação neutra, para comparação', neutroAproximado ? `
            <p>A participação neutra usa só o ano de 2025, em vez da média de ${nAnosTxt} anos, e é a fatia com que o painel monta o contrafactual de cada ano. Este ente não tem registro individualizado de 2025 no SICONFI, então a rotina usa em seu lugar o próprio φ<sup>CPT</sup> do passo 3, calculado com os anos disponíveis.</p>
            <div class="formula">${fmtPctPlain(neutro, 6)} <span class="formula-nota">Igual ao φ<sup>CPT</sup> acima, por construção: é a aproximação que o painel adota quando falta 2025, não um segundo cálculo.</span></div>` : `
            <p>A participação neutra não é o φ<sup>CPT</sup>: usa só o ano de 2025, em vez da média de ${nAnosTxt} anos, e é a fatia com que o painel monta o contrafactual de cada ano.</p>
            <div class="formula">${fmtExato(ref2025)} ${op('÷')} ${fmtExato(totalBr)} ${op('=')} <span class="res">${fmtPctPlain(neutro, 6)}</span></div>`)}
    </div>`;
}

function memoDestinoMuniHtml(refs, m, cod){
    const pesoCota = 0.95 * (m.pop_media / refs.pop_uf) + 0.05 * (1 / refs.n_municipios);
    const renda = m.renda_domiciliar_per_capita_2022 || 0;
    const produto = renda * m.pop_media;
    const cg = refs.compras_governamentais;
    const med = m.renda_mediana_domiciliar_per_capita_2022 || 0;
    // Com função de consumo e compras (Estudo 17) o peso do destino próprio combina dois critérios.
    let eps = 0, sigma2 = 0, brutoCons = 0, pesoCons = 0, pesoCompras = 0, theta = 0;
    let pesoPropria;
    if (cg) {
        eps = cg.elasticidade_consumo;
        sigma2 = (med > 0 && renda >= med) ? 2 * Math.log(renda / med) : 0;
        brutoCons = (med > 0 && renda >= med) ? m.pop_media * Math.pow(med, eps) * Math.exp(eps * eps * sigma2 / 2) : m.peso_consumo_bruto;
        pesoCons = m.peso_consumo_bruto / cg.soma_peso_consumo_uf;
        pesoCompras = m.compras_base_reais / cg.soma_compras_uf_reais;
        theta = cg.theta_compras_uf || 0;
        pesoPropria = (1 - theta) * pesoCons + theta * pesoCompras;
    } else {
        pesoPropria = refs.soma_renda_pop_uf ? produto / refs.soma_renda_pop_uf : 0;
    }
    const cotaPct = pesoCota * refs.cota_parte_municipios_pct;
    const propriaPct = pesoPropria * refs.propria_municipios_pct;
    return `
    <div class="panel">
        <h3>Coeficiente de destino, φ<sup>dest</sup></h3>
        <p class="panel-sub">O destino municipal chega por dois caminhos separados, com critérios legais distintos, e o coeficiente do município é a soma dos dois.</p>

        ${passoHtml(1, 'Caminho A: cota-parte do destino estadual', `
            <p>A cota-parte corresponde a 25% da receita de destino do estado (CF art. 158, IV, "b") e é repartida entre os municípios pelo art. 128 da LC 227/2026: 80% por população, 10% por educação e equidade, 5% por critério ambiental e 5% em partes iguais. Como os indicadores de educação e ambientais dependem de lei estadual ainda não editada na maior parte das UFs, o painel aplica os dois critérios já definidos e redistribui os 15% pendentes proporcionalmente, o que equivale a 95% por população e 5% em partes iguais.</p>
            <div class="formula">0,95 ${op('×')} (${fmtNum2(m.pop_media, 1)} ${op('÷')} ${fmtNum2(refs.pop_uf, 1)}) ${op('+')} 0,05 ${op('×')} (1 ${op('÷')} ${refs.n_municipios}) ${op('=')} <span class="res">${fmtNum2(pesoCota*100, 6)}%</span>
                <span class="formula-nota">Peso deste município dentro da cota-parte da UF.</span></div>
            <div class="formula">${fmtNum2(pesoCota*100, 6)}% ${op('×')} ${fmtPctPlain(refs.cota_parte_municipios_pct, 6)} ${op('=')} <span class="res">${fmtPctPlain(cotaPct, 6)}</span>
                <span class="formula-nota">Fatia do IBS nacional que chega por este caminho.</span>${confere(cotaPct, m.cota_parte_pct)}</div>`)}

        ${cg ? passoHtml(2, 'Caminho B: destino próprio, no lugar do ISS', `
            <p>A parcela que substitui o ISS é rateada por dois critérios. O primeiro é o consumo estimado do município. O painel parte da renda domiciliar per capita do Censo 2022, média e mediana, e aproxima a distribuição de renda por uma lognormal. O consumo cresce menos que a renda: a elasticidade-renda estimada nos microdados da POF 2017–2018 é de ${fmtNum2(eps, 2)}, e o consumo esperado do município é a população multiplicada por mediana<sup>${fmtNum2(eps, 2)}</sup> × exp(${fmtNum2(eps, 2)}² × σ² ÷ 2), com σ² = 2 × ln(média ÷ mediana).</p>
            <div class="formula">σ² = 2 ${op('×')} ln(${fmtExato(renda)} ${op('÷')} ${fmtExato(med)}) ${op('=')} <span class="res">${fmtNum2(sigma2, 4)}</span></div>
            <div class="formula">${fmtNum2(m.pop_media, 1)} ${op('×')} ${fmtExato(med)}<sup>${fmtNum2(eps, 2)}</sup> ${op('×')} exp(${fmtNum2(eps, 2)}² ${op('×')} ${fmtNum2(sigma2, 4)} ÷ 2) ${op('=')} <span class="res">${fmtExato(brutoCons)}</span>${confere(brutoCons, m.peso_consumo_bruto)}</div>
            <div class="formula">${fmtExato(m.peso_consumo_bruto)} ${op('÷')} ${fmtExato(cg.soma_peso_consumo_uf)} ${op('=')} <span class="res">${fmtNum2(pesoCons*100, 6)}%</span>
                <span class="formula-nota">Peso deste município no consumo estimado da UF.</span></div>
            <p>O segundo critério são as compras da prefeitura: o IBS das compras vai ao ente comprador (CF art. 149-C; LC 214/2025, arts. 472 e 473). O painel mede as compras pela despesa liquidada (média de 2024 e 2025, a preços de 2025) nos elementos de bens e serviços (SICONFI, DCA Anexo I-D), com teto por habitante no percentil 99 nacional e imputação pela mediana da UF quando o município não informou.</p>
            <div class="formula">${fmtExato(m.compras_base_reais)} ${op('÷')} ${fmtExato(cg.soma_compras_uf_reais)} ${op('=')} <span class="res">${fmtNum2(pesoCompras*100, 6)}%</span>
                <span class="formula-nota">Peso deste município nas compras dos municípios da UF.</span></div>
            <p>As compras pesam ${fmtNum2(theta*100, 1)}% do destino próprio desta UF (${fmtNum2(cg.theta_municipal*100, 0)}% do IBS municipal na estimativa nacional, ajustado pela participação da UF nas compras).</p>
            <div class="formula">(1 ${op('−')} ${fmtNum2(theta, 4)}) ${op('×')} ${fmtNum2(pesoCons*100, 6)}% ${op('+')} ${fmtNum2(theta, 4)} ${op('×')} ${fmtNum2(pesoCompras*100, 6)}% ${op('=')} <span class="res">${fmtNum2(pesoPropria*100, 6)}%</span></div>
            <div class="formula">${fmtNum2(pesoPropria*100, 6)}% ${op('×')} ${fmtPctPlain(refs.propria_municipios_pct, 6)} ${op('=')} <span class="res">${fmtPctPlain(propriaPct, 6)}</span>
                ${confere(propriaPct, m.propria_pct)}</div>`) : passoHtml(2, 'Caminho B: destino próprio, no lugar do ISS', `
            <p>A parcela que substitui o ISS é rateada pelo consumo estimado do município. Sem medida direta, o painel usa a renda domiciliar per capita do Censo 2022 multiplicada pela população média, como proxy da massa de consumo local.</p>
            <div class="formula">${fmtExato(renda)} ${op('×')} ${fmtNum2(m.pop_media, 1)} habitantes ${op('=')} <span class="res">${fmtExato(produto)}</span></div>
            <div class="formula">${fmtExato(produto)} ${op('÷')} ${fmtExato(refs.soma_renda_pop_uf)} ${op('=')} <span class="res">${fmtNum2(pesoPropria*100, 6)}%</span>
                <span class="formula-nota">Peso deste município no consumo estimado da UF.</span></div>
            <div class="formula">${fmtNum2(pesoPropria*100, 6)}% ${op('×')} ${fmtPctPlain(refs.propria_municipios_pct, 6)} ${op('=')} <span class="res">${fmtPctPlain(propriaPct, 6)}</span>
                ${confere(propriaPct, m.propria_pct)}</div>`)}

        ${passoHtml(3, 'Soma dos dois caminhos', `
            <div class="formula">${fmtPctPlain(cotaPct, 6)} ${op('+')} ${fmtPctPlain(propriaPct, 6)} ${op('=')} <span class="res">${fmtPctPlain(cotaPct + propriaPct, 6)}</span>
                <span class="formula-nota">Coeficiente de destino pleno do município.</span>${confere(cotaPct + propriaPct, m.coef_pleno_pct)}</div>`)}

        <div class="memo-ressalva">
            ${cg ? `<p><b>Duas ressalvas que afetam este número.</b> A primeira é que a elasticidade-renda do consumo é um valor único (${fmtNum2(eps, 2)}), estimado em microdados da POF 2017–2018, mas a curva real não é de elasticidade constante, e a distribuição de renda de cada município é aproximada por uma lognormal. As compras são uma proxy bruta, a soma de elementos de despesa, que não desconta fornecedores do Simples Nacional nem dispensas de licitação presenciais.</p>` : `<p><b>Duas ressalvas que afetam este número.</b> A primeira é que o consumo é função côncava da renda: famílias mais pobres consomem quase tudo o que ganham e as mais ricas poupam uma fração maior. Usar renda per capita de forma linear como proxy tende, portanto, a superestimar a fatia dos municípios mais ricos dentro da UF.</p>`}
            <p>A segunda é que os 10% de educação e equidade e os 5% ambientais do art. 128 ainda não têm indicadores fixados por lei estadual na maior parte das unidades da federação. Enquanto não tiverem, o rateio da cota-parte exibido aqui é uma aproximação, e municípios com desempenho educacional ou ambiental acima da média tendem a receber mais do que este cálculo indica.</p>
        </div>
    </div>`;
}

function memoSeguroHtml(serie, mediaReferencia, nomeEsfera){
    if (!serie || !Object.keys(serie).length) {
        return '<div class="panel"><h3>Seguro-Receita</h3><p class="panel-sub">Não há registro deste ente no rateio do fundo.</p></div>';
    }
    const anos = ANOS.map(String).filter(a => serie[a]);
    const linhas = anos.map(a => {
        const r = serie[a], nac = MEMO_NAC.seguro_por_ano[a] || {};
        const capado = mediaReferencia != null && r.den < mediaReferencia - 1;
        return `<tr>
            <td>${a}</td>
            <td class="num">${fmtExato(r.num)}</td>
            <td class="num">${fmtExato(r.den)}${capado ? ' <span class="badge warn" title="Limitado pelo teto de 3x a média nacional per capita da esfera">teto</span>' : ''}</td>
            <td class="num">${fmtNum2(r.raz*100, 4)}%</td>
            <td class="num" style="color:var(--ink-muted)">${nac.nivel != null ? fmtNum2(nac.nivel*100, 4)+'%' : '—'}</td>
            <td class="num" style="font-weight:700">${r.rep > 1 ? fmtExato(r.rep) : '—'}</td>
        </tr>`;
    }).join('');
    const ultimo = serie['2033'] || serie[anos[anos.length-1]];
    const nac33 = MEMO_NAC.seguro_por_ano['2033'] || {};
    const recebe = ultimo && ultimo.rep > 1;
    return `
    <div class="panel">
        <h3>Seguro-Receita</h3>
        <p class="panel-sub">O ADCT (art. 132) e o art. 117 da LC 227/2026 retêm 5% do IBS pelo critério de destino para um fundo que nivela os entes mais prejudicados pela mudança de critério. A distribuição é sequencial, não proporcional.</p>

        ${passoHtml(1, 'A razão que ordena a fila', `
            <p>Para cada ente calcula-se a razão entre o IBS que ele recebe pelo critério de destino naquele ano e sua receita de referência ajustada. Quanto menor a razão, mais cedo o ente é atendido. A receita de referência ajustada é a menor entre a média histórica de 2019 a 2026, a mesma do φ<sup>CPT</sup>, e três vezes a média nacional per capita da esfera ${nomeEsfera} (art. 117, §6º).</p>
            <div class="table-wrap" style="margin-top:0.6rem">
                <table class="data" style="font-size:0.78rem"><thead><tr>
                    <th>Ano</th><th class="num">IBS por destino recebido</th><th class="num">Receita de referência ajustada</th>
                    <th class="num">Razão do ente</th><th class="num">Nível do ano</th><th class="num">Repasse</th>
                </tr></thead><tbody>${linhas}</tbody></table>
            </div>`)}

        ${passoHtml(2, 'Até onde o fundo alcança', `
            <p>O fundo eleva, um a um, os entes de menor razão, até se esgotar. O patamar em que ele para é o nível do ano, igual para todos os contemplados. Em 2033 o fundo dispõe de ${fmtExato(nac33.pool)} e alcança ${fmtNum2(nac33.n_beneficiarios, 0)} dos ${fmtNum2(nac33.n_entes, 0)} entes do país, parando na razão de ${nac33.nivel != null ? fmtNum2(nac33.nivel*100, 4)+'%' : '—'}.</p>
            ${ultimo ? `<div class="formula">(${fmtExato(ultimo.num)} ${op('+')} ${fmtExato(ultimo.rep)}) ${op('÷')} ${fmtExato(ultimo.den)} ${op('=')} <span class="res">${fmtNum2((ultimo.num+ultimo.rep)/ultimo.den*100, 4)}%</span>
                <span class="formula-nota">${recebe ? 'Com o repasse, a razão do ente chega exatamente ao nível do ano.' : 'A razão do ente já está no nível do ano ou acima dele, e por isso não há repasse em 2033.'}</span></div>` : ''}`)}

        <div class="memo-ressalva">
            <p><b>O repasse não encolhe sozinho.</b> O fundo é uma fração fixa de 5% do IBS pelo critério de destino, que cresce enquanto o ICMS e o ISS são extintos, de modo que tanto o montante total quanto o nível de nivelamento sobem a cada ano. Na projeção, o fundo passa de ${fmtExato((MEMO_NAC.seguro_por_ano['2029']||{}).pool)} em 2029 para ${fmtExato(nac33.pool)} em 2033, e o repasse de quase todos os contemplados cresce junto. Um ente deixa de receber quando a própria receita de destino alcança o nível do ano, não pela passagem do tempo.</p>
        </div>
    </div>`;
}

window.MemoriaCalculo = {
    definirNacional: n => { MEMO_NAC = n; },
    historico: memoHistoricoHtml,
    destinoMuni: memoDestinoMuniHtml,
    seguro: memoSeguroHtml
};
})();
