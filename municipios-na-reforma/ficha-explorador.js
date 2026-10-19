/* Ficha municipal explorável. Interface opt-in: ?visual=novo&m=CODIGO.
 * Recebe a mesma linha do modelo usada pelo portal. Não consulta APIs nem altera premissas.
 * Toda instância tem ciclo de vida próprio; o app deve destruí-la ao trocar de município.
 */
(function () {
  'use strict';

  let sequence = 0;
  const YEARS = ['2029', '2030', '2031', '2032', '2033'];
  function formatMoney(v) {
    const a = Math.abs(v), divisor = a >= 1e9 ? 1e9 : a >= 1e6 ? 1e6 : a >= 1e3 ? 1e3 : 1;
    const suffix = divisor === 1e9 ? ' bi' : divisor === 1e6 ? ' mi' : divisor === 1e3 ? ' mil' : '';
    const precision = divisor === 1e9 ? 2 : divisor === 1e6 ? 1 : 0;
    return (v < 0 ? '− ' : '') + 'R$ ' + (a / divisor).toLocaleString('pt-BR', {
      minimumFractionDigits: precision,
      maximumFractionDigits: precision
    }) + suffix;
  }
  function signedMoney(v) {
    const sign = v < 0 ? '− ' : v > 0 ? '+ ' : '';
    return sign + formatMoney(Math.abs(v));
  }
  function signedPercent(v) {
    const rounded = Math.round(v * 1000) / 10;
    const sign = rounded < 0 ? '−' : rounded > 0 ? '+' : '';
    return sign + (Math.abs(v) * 100).toLocaleString('pt-BR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1
    }) + '%';
  }
  function scaleDomain(values, trim) {
    let low = Math.min(0, ...values);
    const high = Math.max(0, ...values);
    const floor = Math.min(...values);
    // Em linhas, quando todos os valores são positivos e próximos entre si, o zero esconde a diferença
    // entre os cenários. Nesse caso o eixo parte de um piso próximo do menor valor (avisado no gráfico).
    if (trim && floor > 0 && (high - floor) / high < 0.45) low = floor - (high - floor) * 0.6;
    const range = high - low || 1e6;
    const raw = range / 4,
      power = 10 ** Math.floor(Math.log10(raw)),
      fraction = raw / power;
    const step = (fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 2.5 ? 2.5 : fraction <= 5 ? 5 : 10) * power;
    const min = trim && low > 0 ? Math.max(0, Math.floor(low / step) * step) : Math.floor(low / step) * step;
    const max = Math.max(min + step, Math.ceil(high / step) * step);
    const ticks = [];
    for (let i = 0; i <= Math.round((max - min) / step); i++) ticks.push(min + i * step);
    return {
      min,
      max,
      ticks
    };
  }
  function montar(root, options) {
    const m = options.municipio,
      years = YEARS;
    if (!m || !years.every(yr => [m.pos_por_ano?.[yr], m.contrafactual_por_ano?.[yr], m.variacao_por_ano?.[yr]].every(Number.isFinite)) || !years.every(yr => ['origem', 'cpt', 'destino', 'seguro'].every(k => Number.isFinite(m.componentes_por_ano?.[yr]?.[k])))) return null;
    const uid = 'fe-' + ++sequence,
      events = new AbortController();
    const barMaximum = scaleDomain(years.flatMap(yr => [m.pos_por_ano[yr], m.contrafactual_por_ano[yr]])).max;
    const on = (target, type, handler, extra = {}) => target.addEventListener(type, handler, {
      ...extra,
      signal: events.signal
    });
    root.classList.add('ficha-explorador');
    root.innerHTML = TEMPLATE;
    const $ = s => root.querySelector(s),
      $$ = s => [...root.querySelectorAll(s)];
    const dec = (v, n = 1) => v.toLocaleString('pt-BR', {
        minimumFractionDigits: n,
        maximumFractionDigits: n
      }),
      money = formatMoney;
    let disposed = false, rendered = false;
    let year = '2033',
      lens = 'receita',
      period = 'transicao',
      focus = null,
      timer = null,
      dragging = false,
      chartGeometry = null;
    const components = {
      origem: {
        name: 'ISS + cota-parte ICMS',
        color: '#858384',
        title: 'As receitas na origem diminuem.',
        copy: 'Parcela residual do ISS e da cota-parte do ICMS que permanece durante a transição. Na projeção de 2033, essa parcela chega a zero.'
      },
      cpt: {
        name: 'IBS · critério histórico',
        color: '#0f508e',
        title: 'O histórico participa da repartição.',
        copy: 'Parcela de IBS distribuída pelo critério histórico do modelo. Seu peso varia com o cronograma da transição e os coeficientes municipais.'
      },
      destino: {
        name: 'IBS · destino',
        color: '#6aa8dd',
        title: 'A receita acompanha o destino.',
        copy: 'Parcela de IBS atribuída ao critério de destino, incluindo os repasses estaduais considerados pelo modelo.'
      },
      seguro: {
        name: 'Seguro-Receita efetivo',
        color: '#249266',
        title: 'A compensação entra na composição.',
        copy: 'Parcela efetiva do Seguro-Receita incorporada ao total do modelo. O repasse bruto é informado separadamente no resumo do gráfico.'
      }
    };
    function stop() {
      if (timer) clearInterval(timer);
      timer = null;
      $('#play').setAttribute('aria-pressed', 'false');
      $('#play').setAttribute('aria-label', 'Assistir à transição');
      $('#play-label').textContent = 'Assistir à transição';
      $('#play-icon').innerHTML = '<path d="M4 2v12l10-6Z"/>';
    }
    function selectYear(value, {
      manual = true
    } = {}) {
      if (!years.includes(String(value))) return;
      if (manual) stop();
      if (rendered && year === String(value)) return;
      rendered = true;
      year = String(value);
      $('#readout-year').textContent = year;
      $('#time-label').textContent = year;
      $('#time').value = year;
      $('#time').setAttribute('aria-valuetext', year);
      $('#with-rule').style.width = Math.max(0, m.pos_por_ano[year]) / barMaximum * 100 + '%';
      $('#without-rule').style.width = Math.max(0, m.contrafactual_por_ano[year]) / barMaximum * 100 + '%';
      $('#with-value').innerHTML = money(m.pos_por_ano[year]).replace(' mi', ' <small>mi</small>');
      $('#without-value').innerHTML = money(m.contrafactual_por_ano[year]).replace(' mi', ' <small>mi</small>');
      $('#difference').textContent = signedMoney(m.pos_por_ano[year] - m.contrafactual_por_ano[year]);
      $('#difference').classList.toggle('neg', m.pos_por_ano[year] < m.contrafactual_por_ano[year]);
      $('#percent').textContent = signedPercent(m.variacao_por_ano[year]) + ' frente ao cenário sem reforma';
      $('#percent').classList.toggle('neg', m.variacao_por_ano[year] < 0);
      const seguro = m.repasse_seguro_receita_por_ano?.[year] || 0,
        dif = m.pos_por_ano[year] - m.contrafactual_por_ano[year];
      $('#readout-insurance').hidden = !(seguro > 0);
      $('#insurance').textContent = money(seguro);
      $('#insurance-dep').innerHTML = dif > 0 && seguro > dif ? `<b>O ganho depende dele:</b> sem o repasse, a diferença seria de ${signedMoney(dif - seguro)}.` : '';
      $('#comp-year').textContent = year;
      $('#comp-total').textContent = money(m.pos_por_ano[year]);
      $$('[data-tick]').forEach(el => {
        el.classList.toggle('active', el.dataset.tick === year);
        el.setAttribute('aria-pressed', el.dataset.tick === year);
      });
      $$('#rows tr').forEach(el => el.classList.toggle('selected', el.dataset.year === year));
      const difference = m.pos_por_ano[year] - m.contrafactual_por_ano[year];
      $('#narrative').innerHTML = year === '2029' ? `A transição começa com um efeito estimado de <b>${signedMoney(difference)} no ano.</b>` : year === '2033' ? `No fim do horizonte exibido, a diferença anual estimada é de <b>${signedMoney(difference)}.</b>` : `Em ${year}, o efeito estimado equivale a <b>${signedPercent(m.variacao_por_ano[year])}</b> frente ao cenário sem reforma.`;
      draw();
      renderComposition();
    }
    function draw() {
      if (disposed || !root.isConnected) return;
      const svg = $('#chart'),
        small = matchMedia('(max-width:620px)').matches;
      const rect = svg.getBoundingClientRect();
      if (!rect.width) return;
      const w = Math.max(300, Math.round(rect.width)),
        h = Math.round(rect.height) || 370;
      svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
      const L = small ? 32 : 44,
        R = w - (small ? 20 : 27),
        T = 43,
        B = h - 37;
      const all = period === 'completo' && lens === 'receita';
      const start = all ? 2019 : 2029;
      const x = yr => L + (yr - start) / (2033 - start) * (R - L);
      const values = lens === 'impacto' ? years.map(yr => m.pos_por_ano[yr] - m.contrafactual_por_ano[yr]) : years.flatMap(yr => [m.pos_por_ano[yr], m.contrafactual_por_ano[yr]]).concat(all ? Object.values(m.historico_por_ano || {}).map(row => row.total_reais_2025).filter(Number.isFinite) : []);
      const domain = scaleDomain(values, lens === 'receita');
      const truncated = lens === 'receita' && domain.min > 0;
      const y = v => B - (v - domain.min) / (domain.max - domain.min) * (B - T);
      const diff = yr => m.pos_por_ano[yr] - m.contrafactual_por_ano[yr];
      const line = field => years.map((yr, i) => `${i ? 'L' : 'M'}${x(+yr).toFixed(1)},${y(m[field][yr]).toFixed(1)}`).join(' ');
      let html = `<defs><linearGradient id="${uid}-area" x1="0" x2="0" y1="0" y2="1"><stop stop-color="#0f508e" stop-opacity=".14"/><stop offset="1" stop-color="#0f508e" stop-opacity=".025"/></linearGradient><linearGradient id="${uid}-impact-area" x1="0" x2="0" y1="0" y2="1"><stop stop-color="#0f508e" stop-opacity=".22"/><stop offset="1" stop-color="#0f508e" stop-opacity=".02"/></linearGradient></defs>`;
      if (all) html += `<rect x="${x(2026)}" y="${T - 12}" width="${x(2028) - x(2026)}" height="${B - T + 12}" fill="#dce4ef" fill-opacity=".7"/><text x="${x(2027)}" y="${T + 14}" text-anchor="middle" fill="#5d7090" font-size="${small ? 9 : 11}">Sem projeção</text>`;
      const ticks = domain.ticks;
      ticks.forEach(v => html += `<line x1="${L}" x2="${R}" y1="${y(v)}" y2="${y(v)}" stroke="#d6e0ed" stroke-width=".8"/><text x="${L - 9}" y="${y(v) + 3}" text-anchor="end" fill="#526a8a" font-size="${small ? 11 : 12}">${dec(v / 1e6, Math.abs(v) < 1e6 && v !== 0 ? 2 : 0)}</text>`);
      if (lens === 'receita') {
        const area = line('pos_por_ano') + ' ' + years.slice().reverse().map(yr => `L${x(+yr)},${y(m.contrafactual_por_ano[yr])}`).join(' ') + ' Z';
        html += `<path d="${area}" fill="url(#${uid}-area)"/><path d="${line('contrafactual_por_ano')}" fill="none" stroke="#7c8fa9" stroke-width="2" stroke-dasharray="4 5"/><path d="${line('pos_por_ano')}" fill="none" stroke="#0f508e" stroke-width="3.3" stroke-linecap="round" stroke-linejoin="round"/>`;
        if (all) {
          const hist = Object.entries(m.historico_por_ano || {}).filter(([, row]) => Number.isFinite(row.total_reais_2025));
          html += `<path d="${hist.map(([yr, row], i) => `${i ? 'L' : 'M'}${x(+yr)},${y(row.total_reais_2025)}`).join(' ')}" fill="none" stroke="#7287a4" stroke-width="2"/>`;
          hist.forEach(([yr, row]) => html += `<circle cx="${x(+yr)}" cy="${y(row.total_reais_2025)}" r="2.5" fill="#7287a4"/>`);
        }
      } else {
        const a = years.map((yr, i) => `${i ? 'L' : 'M'}${x(+yr)},${y(diff(yr))}`).join(' ');
        html += `<path d="${a} L${x(2033)},${y(0)} L${x(2029)},${y(0)} Z" fill="url(#${uid}-impact-area)"/><path d="${a}" fill="none" stroke="#0f508e" stroke-width="3.3" stroke-linejoin="round"/>`;
      }
      const labels = all ? small ? [2019, 2022, 2025, 2029, 2033] : [2019, 2021, 2023, 2025, 2029, 2031, 2033] : years.map(Number);
      labels.forEach(yr => html += `<text x="${x(yr)}" y="${B + 25}" text-anchor="middle" fill="${String(yr) === year ? '#062254' : '#526a8a'}" font-size="${small ? 11 : 12}" font-weight="${String(yr) === year ? 750 : 400}">${yr}</text>`);
      const sx = x(+year),
        val = lens === 'impacto' ? diff(year) : m.pos_por_ano[year],
        sy = y(val);
      html += `<line x1="${sx}" x2="${sx}" y1="${T - 14}" y2="${B}" stroke="#b8c7dc" stroke-width="1" stroke-dasharray="3 4"/>`;
      if (lens === 'receita') {
        const ny = y(m.contrafactual_por_ano[year]);
        html += `<line x1="${sx}" x2="${sx}" y1="${sy}" y2="${ny}" stroke="#fcbb1b" stroke-width="3"/><path d="M${sx - 5} ${sy}h10M${sx - 5} ${ny}h10" stroke="#bf8d11" stroke-width="1.2"/><circle cx="${sx}" cy="${ny}" r="4" fill="#7c8fa9" stroke="#edf2f8" stroke-width="2"/>`;
        if ((!small || !all) && Math.abs(ny - sy) > 52 && B - Math.max(ny, sy) > (small ? 66 : 72)) {
          const aw = small ? 140 : 156,
            ah = small ? 43 : 49;
          const ax = Math.max(L + 6, Math.min(R - aw - 12, sx - aw - 16)),
            ay = Math.min(B - ah - 9, Math.max(ny, sy) + 16);
          html += `<g class="gap-label"><rect x="${ax}" y="${ay}" width="${aw}" height="${ah}" rx="5" fill="#f9fbfe" stroke="#d2ddec"/><rect x="${ax}" y="${ay + 9}" width="3" height="${ah - 18}" rx="1" fill="#fcbb1b"/><text x="${ax + 12}" y="${ay + 15}" fill="#7389a6" font-size="${small ? 10 : 11}">Efeito da reforma · ${year}</text><text x="${ax + 12}" y="${ay + ah - 11}" fill="${diff(year) < 0 ? '#a02525' : '#062254'}" font-size="${small ? 11 : 14}" font-weight="700">${signedMoney(diff(year))}</text><path d="M${ax + aw} ${ay + ah / 2}H${sx}V${Math.max(ny, sy) + 5}" fill="none" stroke="#d1a339" stroke-width="1"/></g>`;
        }
      }
      years.forEach(yr => {
        const py = lens === 'impacto' ? y(diff(yr)) : y(m.pos_por_ano[yr]);
        html += `<circle cx="${x(+yr)}" cy="${py}" r="${yr === year ? 7 : 4}" fill="${yr === year ? '#fcbb1b' : '#0f508e'}" stroke="#edf2f8" stroke-width="${yr === year ? 3 : 2}"/>`;
      });
      const label = lens === 'impacto' ? signedMoney(val) : money(val),
        lw = small ? 102 : 124,
        lh = 27,
        labelX = Math.max(L, Math.min(R - lw, sx - lw / 2)),
        labelY = Math.max(1, sy - 42);
      html += `<g><rect x="${labelX}" y="${labelY}" width="${lw}" height="${lh}" rx="5" fill="#f9fbfe" stroke="#c3d3e7"/><circle cx="${labelX + 12}" cy="${labelY + 13.5}" r="2.7" fill="#0f508e"/><text x="${labelX + lw / 2 + 5}" y="${labelY + 17}" text-anchor="middle" fill="#0f508e" font-size="${small ? 11 : 12}" font-weight="700">${label}</text></g><circle class="handle" cx="${sx}" cy="${B}" r="6" fill="#fcbb1b" stroke="#b88916" stroke-width="1"/>`;
      svg.innerHTML = html;
      chartGeometry = {
        L,
        R,
        start
      };
      $('#axis-note').textContent = truncated ? 'Eixo vertical a partir de R$ ' + dec(domain.min / 1e6, 0) + ' mi' : '';
      $('#legend').innerHTML = lens === 'impacto' ? '<span><i class="legend-line"></i>Diferença: com reforma − sem reforma</span>' : '<span><i class="legend-line"></i>Com reforma</span><span><i class="legend-line without"></i>Sem reforma</span>' + (all ? '<span><i class="legend-line history"></i>Histórico</span>' : '');
    }
    function scrub(event) {
      if (!chartGeometry || !$('#table-view').hidden) return;
      const r = $('#chart').getBoundingClientRect(),
        cx = event.clientX - r.left,
        {
          L,
          R,
          start
        } = chartGeometry;
      const proposed = Math.round(start + (cx - L) / (R - L) * (2033 - start));
      selectYear(Math.max(2029, Math.min(2033, proposed)));
      $('#hint').hidden = true;
    }
    on($('#chart'), 'pointerdown', e => {
      if (e.pointerType === 'touch') {
        dragging = true;
        $('#chart').setPointerCapture(e.pointerId);
      } else {
        dragging = true;
        $('#chart').setPointerCapture(e.pointerId);
      }
      scrub(e);
    });
    on($('#chart'), 'pointermove', e => {
      if (dragging) scrub(e);
    });
    on($('#chart'), 'pointerup', () => dragging = false);
    on($('#chart'), 'pointercancel', () => dragging = false);
    function renderComposition() {
      const row = m.componentes_por_ano[year];
      const total = Object.keys(components).reduce((a, key) => a + row[key], 0);
      $('#bands').classList.toggle('focused', !!focus);
      $('#bands').innerHTML = Object.entries(components).map(([k, c]) => {
        const pct = total ? row[k] / total * 100 : 0;
        return pct > 0 ? `<button class="band ${focus === k ? 'active' : ''}" data-key="${k}" style="width:${pct}%" aria-label="${c.name}: ${money(row[k])}, ${dec(pct)}%" aria-pressed="${focus === k}">${pct > 18 ? dec(pct, 0) + '%' : ''}</button>` : '';
      }).join('');
      $('#band-labels').innerHTML = Object.entries(components).map(([k, c]) => `<button class="band-label ${focus === k ? 'active' : ''}" data-key="${k}" aria-pressed="${focus === k}"><div class="band-label-top"><i style="background:${c.color}"></i>${c.name}</div><b>${money(row[k])}</b><span>${dec(total ? row[k] / total * 100 : 0)}% do total</span></button>`).join('');
      $('#clear-band').hidden = !focus;
      if (focus) {
        $('#component-tag').textContent = components[focus].name;
        $('#component-title').textContent = components[focus].title;
        $('#component-copy').textContent = components[focus].copy + ' Em ' + year + ': ' + money(row[focus]) + ' (' + dec(total ? row[focus] / total * 100 : 0) + '% do total).';
      } else {
        $('#component-tag').textContent = 'ENTENDA A COMPOSIÇÃO';
        $('#component-title').textContent = 'Uma receita. Quatro origens.';
        $('#component-copy').textContent = 'O peso de cada parcela muda ao longo da transição. Explore os anos no gráfico e selecione uma das parcelas para acompanhar essa mudança.';
      }
    }
    on($('#composicao'), 'click', e => {
      const target = e.target.closest('[data-key]');
      if (!target || !components[target.dataset.key]) return;
      focus = focus === target.dataset.key ? null : target.dataset.key;
      renderComposition();
    });
    on($('#clear-band'), 'click', () => {
      focus = null;
      renderComposition();
    });
    on($('#time'), 'input', e => {
      selectYear(e.target.value);
      $('#hint').hidden = true;
    });
    $('#ticks').innerHTML = years.map(yr => `<button data-tick="${yr}" aria-label="Selecionar ${yr}" aria-pressed="${yr === year}">${yr}</button>`).join('');
    $$('[data-tick]').forEach(el => on(el, 'click', () => selectYear(el.dataset.tick)));
    $$('[data-lens]').forEach(el => on(el, 'click', () => {
      stop();
      lens = el.dataset.lens;
      if (lens === 'impacto') period = 'transicao';
      $$('[data-lens]').forEach(b => {
        b.classList.toggle('active', b === el);
        b.setAttribute('aria-pressed', b === el);
      });
      $$('[data-period]').forEach(b => {
        b.disabled = lens === 'impacto' && b.dataset.period === 'completo';
        b.classList.toggle('active', b.dataset.period === period);
        b.setAttribute('aria-pressed', b.dataset.period === period);
      });
      draw();
    }));
    $$('[data-period]').forEach(el => on(el, 'click', () => {
      stop();
      period = el.dataset.period;
      $$('[data-period]').forEach(b => {
        b.classList.toggle('active', b === el);
        b.setAttribute('aria-pressed', b === el);
      });
      draw();
    }));
    on($('#play'), 'click', () => {
      if (timer) {
        stop();
        return;
      }
      selectYear(2029, {
        manual: false
      });
      $('#play').setAttribute('aria-pressed', 'true');
      $('#play').setAttribute('aria-label', 'Pausar transição');
      $('#play-label').textContent = 'Pausar transição';
      $('#play-icon').innerHTML = '<path d="M3 2h4v12H3zM10 2h4v12h-4z"/>';
      $('#hint').hidden = true;
      timer = setInterval(() => {
        if (+year >= 2033) {
          stop();
          return;
        }
        selectYear(+year + 1, {
          manual: false
        });
        if (+year === 2033) stop();
      }, 1600);
    });
    on($('#reset'), 'click', () => selectYear(2029));
    on($('#table-toggle'), 'click', () => {
      const table = $('#table-view').hidden;
      $('#table-view').hidden = !table;
      $('#svg-view').hidden = table;
      $('#table-toggle').setAttribute('aria-pressed', table);
      $('#table-toggle').setAttribute('aria-label', table ? 'Mostrar gráfico' : 'Mostrar tabela');
      $('#table-toggle span').textContent = table ? 'Gráfico' : 'Tabela';
      if (!table) draw();
    });
    $('#rows').innerHTML = years.map(yr => `<tr data-year="${yr}"><td><button class="year-button" data-row-year="${yr}">${yr}</button></td><td>${money(m.pos_por_ano[yr])}</td><td>${money(m.contrafactual_por_ano[yr])}</td><td>${signedMoney(m.pos_por_ano[yr] - m.contrafactual_por_ano[yr])}</td><td>${signedPercent(m.variacao_por_ano[yr])}</td></tr>`).join('');
    $$('[data-row-year]').forEach(el => on(el, 'click', () => selectYear(el.dataset.rowYear)));
    on($('#fullscreen'), 'click', async () => {
      try {
        if (document.fullscreenElement) await document.exitFullscreen();else await $('#stage').requestFullscreen();
      } catch (e) {
        toast('Use a ampliação do navegador para apresentar o gráfico.');
      }
    });
    on(document, 'fullscreenchange', () => setTimeout(draw, 70));
    let resize;
    on(window, 'resize', () => {
      clearTimeout(resize);
      resize = setTimeout(draw, 80);
    });
    function toast(text) {
      root.querySelector('[data-explorador-status]').textContent = text;
      options.avisar?.(text);
    }
    on($('#download'), 'click', () => {
      const header = ['ano', 'receita_com_reforma_reais_2025', 'receita_sem_reforma_reais_2025', 'impacto_reais_2025', 'variacao_pct', 'seguro_bruto_reais_2025'];
      const csv = [header.join(';'), ...years.map(yr => [yr, m.pos_por_ano[yr], m.contrafactual_por_ano[yr], m.pos_por_ano[yr] - m.contrafactual_por_ano[yr], m.variacao_por_ano[yr] * 100, m.repasse_seguro_receita_por_ano?.[yr] || 0].map(v => String(v).replace('.', ',')).join(';'))].join('\r\n');
      const url = URL.createObjectURL(new Blob(['\ufeff' + csv], {
        type: 'text/csv;charset=utf-8'
      }));
      const a = document.createElement('a');
      a.href = url;
      a.download = (m.nome || options.nome || 'municipio').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-') + '-projecoes.csv';
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      toast('Projeções de 2029 a 2033 exportadas em CSV.');
    });
    let tableBeforePrint = false;
    on(window, 'beforeprint', () => {
      stop();
      tableBeforePrint = !$('#table-view').hidden;
      $('#svg-view').hidden = false;
      $('#table-view').hidden = true;
      draw();
    });
    on(window, 'afterprint', () => {
      $('#table-view').hidden = !tableBeforePrint;
      $('#svg-view').hidden = tableBeforePrint;
      draw();
    });
    on(window, 'pagehide', stop);
    selectYear('2033');
    document.fonts?.ready.then(() => {
      if (!disposed) draw();
    });
    on(document, 'visibilitychange', () => {
      if (document.hidden) stop();
    });
    $('#chart').setAttribute('aria-label', 'Receitas projetadas de ' + (m.nome || options.nome || 'município') + ' de 2029 a 2033, com e sem reforma. Os valores também estão na tabela.');
    return {
      pausar: stop,
      atualizar: draw,
      destruir() {
        stop();
        clearTimeout(resize);
        events.abort();
        disposed = true;
        root.replaceChildren();
      }
    };
  }
  const TEMPLATE = `<section class="stage" id="stage" aria-labelledby="chart-title">
<div class="stage-head">
<div>
<div class="eyebrow"><span class="dot"></span>Explore a transição · 2029—2033</div>
<h2 id="chart-title">A receita, <em>em perspectiva.</em></h2>
<p class="stage-sub">Explore os anos. Veja os cenários. Entenda a diferença.</p></div>
<div class="stage-head-right"><span class="live"><i></i>Dados do modelo do portal</span>
<button type="button" class="chart-tool" id="fullscreen" aria-label="Ampliar gráfico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
<path d="M8 3H3v5m13-5h5v5M3 16v5h5m8 0h5v-5"/></svg><span class="normal-label">Ampliar</span><span class="fullscreen-label">Sair da tela cheia</span></button>
<button class="chart-tool" id="download" type="button" aria-label="Baixar dados da ficha"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
<path d="M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4"/></svg><span>CSV</span></button>
<button type="button" class="chart-tool" id="table-toggle" aria-label="Mostrar tabela" aria-pressed="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
<path d="M3 4h18v16H3zM3 10h18M9 4v16M15 4v16"/></svg><span>Tabela</span></button></div></div>
<div class="chart-controls">
<div class="lens" role="group" aria-label="Lente do gráfico">
<button type="button" class="active" data-lens="receita" aria-pressed="true"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor">
<path d="M2 13V3m0 10h12M4 10l3-3 3 1 4-5"/></svg>Receita</button>
<button type="button" data-lens="impacto" aria-pressed="false">Impacto da reforma</button></div>
<div class="periods" role="group" aria-label="Período do gráfico">
<button type="button" class="active" data-period="transicao" aria-pressed="true">Transição</button>
<button type="button" data-period="completo" aria-pressed="false">+ Histórico</button></div></div>
<div class="stage-core">
<div class="graph">
<div class="graph-meta">
<div class="graph-legend" id="legend"><span><i class="legend-line"></i>Com reforma</span><span><i class="legend-line without"></i>Sem reforma</span></div><span class="graph-unit">R$ milhões · preços de 2025<span id="axis-note"></span></span></div>
<div id="svg-view"><svg id="chart" class="chart" viewBox="0 0 900 360" role="img" aria-label="Gráfico interativo das receitas projetadas com e sem reforma de 2029 a 2033. Selecione o ano no controle de tempo ou abra a tabela."></svg>
<div class="graph-hint" id="hint"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor">
<path d="m5 4-4 4 4 4m6-8 4 4-4 4M1 8h14"/></svg>Arraste o ponto para explorar</div></div>
<div class="chart-table" id="table-view" hidden><table><caption class="skip">Projeções em milhões de reais de 2025</caption><thead><tr><th>Ano</th><th>Com reforma</th><th>Sem reforma</th><th>Impacto</th><th>Variação</th></tr></thead><tbody id="rows"></tbody></table></div>
<div class="chart-narrative" aria-live="polite"><svg class="spark" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
<path d="m10 2 2 6 6 2-6 2-2 6-2-6-6-2 6-2Z"/></svg><span id="narrative"></span></div></div>
<aside class="readout" aria-label="Resultado do ano selecionado">
<div class="readout-head">
<div class="readout-year" id="readout-year">2033</div><span class="estimate-badge">Estimativa</span></div>
<div class="scenario">
<div class="scenario-label"><i></i>Com a reforma</div>
<div class="scenario-value" id="with-value">R$ 791,8 <small>mi</small></div>
<div class="scenario-rule" aria-hidden="true"><span id="with-rule" style="width:88%"></span></div></div>
<div class="scenario without">
<div class="scenario-label"><i></i>Sem a reforma</div>
<div class="scenario-value" id="without-value">R$ 370,4 <small>mi</small></div>
<div class="scenario-rule" aria-hidden="true"><span id="without-rule" style="width:41%"></span></div></div>
<div class="difference">
<div class="difference-label">Diferença anual estimada</div>
<div class="difference-value" id="difference">+ R$ 421,4 mi</div>
<div class="difference-percent" id="percent">+113,8% frente ao cenário sem reforma</div></div>
<div class="readout-insurance" id="readout-insurance">Inclui <b id="insurance">R$ 48,7 mi</b> de Seguro-Receita, o repasse compensatório do Comitê Gestor. <span id="insurance-dep"></span></div>
</aside></div>
<div class="transport">
<button type="button" class="play" id="play" aria-label="Assistir à transição" aria-pressed="false"><svg id="play-icon" viewBox="0 0 16 16">
<path d="M4 2v12l10-6Z"/></svg><span id="play-label">Assistir à transição</span></button>
<div class="time-slider"><label for="time">LINHA DO TEMPO <b id="time-label">2033</b></label><input type="range" min="2029" max="2033" step="1" value="2033" id="time" aria-label="Ano da análise" aria-valuetext="2033">
<div class="time-ticks" id="ticks"></div></div>
<button type="button" class="reset" id="reset"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
<path d="M4 11a8 8 0 1 1 1 7M4 4v7h7"/></svg>Recomeçar</button></div>
</section>
<div class="stage-note"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor"><circle cx="8" cy="8" r="6"/>
<path d="M8 7v4M8 4v1"/></svg><span>Estimativas independentes, em R$ de 2025. O resultado se refere às receitas do consumo, incluindo a cota-parte estadual. <a href="#" data-tab="metodologia" data-depois="met-5">Fontes e premissas</a></span></div>
<section id="composicao" aria-labelledby="comp-title">
<div class="section-title">
<div>
<div class="section-index">O MESMO ANO. OUTRA PERSPECTIVA.</div>
<h2 id="comp-title">De onde vem cada real.</h2>
<p>Selecione uma parcela para entender sua participação na receita.</p></div>
<div class="year-pill"><i></i>Conectado a <b id="comp-year">2033</b></div></div>
<div class="composition">
<div class="composition-left">
<div class="composition-total"><span>Composição da receita com reforma</span><b id="comp-total">R$ 791,8 mi</b></div>
<div class="bands" id="bands" role="group" aria-label="Parcelas da receita"></div>
<div class="band-labels" id="band-labels"></div>
<p class="composition-note">A parcela do Seguro-Receita aqui é o valor efetivo do modelo, que pode diferir levemente do repasse bruto citado no resumo e no texto.</p></div>
<aside class="explain-component">
<div class="component-tag" id="component-tag">ENTENDA A COMPOSIÇÃO</div>
<h3 id="component-title">Uma receita. Quatro origens.</h3>
<p id="component-copy">O peso de cada parcela muda ao longo da transição. Explore os anos no gráfico e selecione uma das parcelas para acompanhar essa mudança.</p>
<button type="button" class="clear-band" id="clear-band" hidden>Ver composição completa</button>
</aside></div>
</section>
<p class="sr-only" data-explorador-status role="status"></p>`;
  window.FichaExplorador = Object.freeze({
    ativo: () => new URLSearchParams(location.search).get("visual") === "novo",
    montar
  });
})();
