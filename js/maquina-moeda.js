const $ = (id) => document.getElementById(id);
    const fmt = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 2 });
    const pct = (x) => `${Math.round(x * 100)}%`;

    const controls = {
      omo: $('omo'), reserve: $('reserve'), lend: $('lend'), cash: $('cash'), rounds: $('rounds'), consumers: $('consumers')
    };

    let model = null;
    let stepIndex = 0;

    const presets = {
      textbook: { omo: 1000, reserve: 10, lend: 100, cash: 0, rounds: 7 },
      cautious: { omo: 1000, reserve: 10, lend: 50, cash: 0, rounds: 7 },
      cash: { omo: 1000, reserve: 10, lend: 100, cash: 20, rounds: 7 },
      crisis: { omo: 1000, reserve: 10, lend: 30, cash: 20, rounds: 7 }
    };

    function money(v) { return fmt.format(Math.abs(v) < 0.005 ? 0 : v); }
    function multiplier(moneyValue, base) { return base > 0 ? moneyValue / base : 0; }

    function currentParams() {
      return {
        omo: Number(controls.omo.value),
        r: Number(controls.reserve.value) / 100,
        lend: Number(controls.lend.value) / 100,
        cash: Number(controls.cash.value) / 100,
        rounds: Number(controls.rounds.value),
        consumers: Math.max(4, Math.min(40, Number(controls.consumers.value) || 10))
      };
    }

    function makeState(base=0, deposits=0, cash=0, loans=0) {
      return { base, deposits, cash, money: deposits + cash, loans, reserves: Math.max(0, base - cash) };
    }

    function buildModel() {
      const p = currentParams();
      const steps = [];
      const initialState = makeState();
      steps.push({
        kind: 'setup', round: 0, bank: null, from: 'Professor', to: 'Dealer', amount: 0,
        kicker: 'Antes de começar', title: 'Distribua os papéis pela sala', label: 'Preparação',
        text: 'O dealer recebe um cartão que representa um título público. Os bancos e consumidores começam sem novos saldos decorrentes desta experiência.',
        explain: 'Peça aos alunos que acompanhem dois números durante todo o jogo: a base monetária e os meios de pagamento. Eles não se comportam da mesma forma.',
        prompt: 'de onde virá o primeiro real novo de base monetária?',
        state: initialState, deltaB: 0, deltaM: 0, deltaDeposits: 0, deltaCash: 0
      });

      let state = makeState();
      state = makeState(p.omo, p.omo, 0, 0);
      steps.push({
        kind: 'omo', round: 0, bank: 'Banco A', from: 'Banco Central', to: 'Dealer via Banco A', amount: p.omo,
        kicker: 'Operação de mercado aberto', title: 'O Banco Central compra o título do dealer', label: 'Jogada do professor',
        text: `O Banco Central compra o título por ${money(p.omo)}. O pagamento é creditado ao dealer no Banco A e as reservas do Banco A aumentam no mesmo valor.`,
        explain: 'Aqui nasce nova base monetária. Como o vendedor é um agente não bancário, também surge um novo depósito no Banco A.',
        prompt: 'a base monetária e os meios de pagamento aumentaram pelo mesmo valor nesta primeira jogada?',
        state: { ...state }, deltaB: p.omo, deltaM: p.omo, deltaDeposits: p.omo, deltaCash: 0
      });

      let incoming = p.omo;
      for (let i = 1; i <= p.rounds; i++) {
        const bank = i % 2 === 1 ? 'Banco A' : 'Banco B';
        const nextBank = i % 2 === 1 ? 'Banco B' : 'Banco A';
        const borrowerIndex = ((i - 1) * 2) % p.consumers + 1;
        const recipientIndex = ((i - 1) * 2 + 1) % p.consumers + 1;
        const required = incoming * p.r;
        const available = incoming - required;
        const loan = available * p.lend;
        const excess = available - loan;

        const beforeLoan = { ...state };
        state = makeState(state.base, state.deposits + loan, state.cash, state.loans + loan);
        steps.push({
          kind: 'loan', round: i, bank, from: bank, to: `Consumidor ${borrowerIndex}`, amount: loan,
          kicker: `Rodada bancária ${i}`, title: `${bank} concede um novo empréstimo`, label: 'Criação de crédito',
          text: `${bank} recebe ${money(incoming)} como base da rodada. Separa ${money(required)} para a exigência de reservas, mantém ${money(excess)} como reserva excedente e concede ${money(loan)} de crédito ao Consumidor ${borrowerIndex}.`,
          explain: 'O empréstimo cria um novo depósito. Os meios de pagamento aumentam, mas a base monetária não muda nesta jogada.',
          prompt: 'se o banco acabou de criar um depósito, por que a base monetária permaneceu igual?',
          state: { ...state }, deltaB: 0, deltaM: state.money - beforeLoan.money, deltaDeposits: loan, deltaCash: 0,
          required, excess, incoming
        });

        const cashHeld = loan * p.cash;
        const redeposit = loan - cashHeld;
        const beforeSpend = { ...state };
        state = makeState(state.base, state.deposits - cashHeld, state.cash + cashHeld, state.loans);
        steps.push({
          kind: 'spend', round: i, bank: nextBank, from: `Consumidor ${borrowerIndex}`, to: `Consumidor ${recipientIndex} via ${nextBank}`, amount: loan,
          kicker: `Rodada bancária ${i}`, title: 'O empréstimo vira gasto e chega ao próximo banco', label: 'Pagamento e redepósito',
          text: `Consumidor ${borrowerIndex} gasta ${money(loan)} com o Consumidor ${recipientIndex}. Deste valor, ${money(redeposit)} volta ao sistema como depósito no ${nextBank} e ${money(cashHeld)} fica em espécie.`,
          explain: 'O pagamento desloca reservas entre bancos. A parte mantida em espécie muda a composição da base, de reservas para papel-moeda, mas não altera o total da base nem os meios de pagamento.',
          prompt: cashHeld > 0 ? 'por que retirar dinheiro em espécie reduz a capacidade de multiplicação sem reduzir os meios de pagamento naquele instante?' : 'o que precisa acontecer com esse novo depósito para a próxima rodada continuar?',
          state: { ...state }, deltaB: 0, deltaM: state.money - beforeSpend.money, deltaDeposits: -cashHeld, deltaCash: cashHeld,
          redeposit, cashHeld
        });

        incoming = redeposit;
      }

      const final = steps[steps.length - 1].state;
      steps.push({
        kind: 'finish', round: p.rounds, bank: null, from: 'Sistema bancário', to: 'Turma', amount: final.money,
        kicker: 'Fim da simulação', title: 'Compare a base com os meios de pagamento', label: 'Síntese',
        text: `A operação inicial criou ${money(final.base)} de base monetária. Depois de ${p.rounds} rodadas, o jogo chegou a ${money(final.money)} de meios de pagamento e ${money(final.loans)} de crédito acumulado.`,
        explain: `O multiplicador realizado nesta simulação foi ${multiplier(final.money, final.base).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})} vezes. Mude os parâmetros e compare como o comportamento de bancos e público altera o resultado.`,
        prompt: 'qual parâmetro desta simulação o Banco Central controla diretamente e quais dependem do comportamento dos bancos e do público?',
        state: { ...final }, deltaB: 0, deltaM: 0, deltaDeposits: 0, deltaCash: 0
      });

      return { p, steps };
    }

    function actorMarkup(step) {
      const active = new Set();
      if (step.kind === 'omo') { active.add('bc'); active.add('dealer'); active.add('a'); }
      if (step.kind === 'loan') { active.add(step.bank === 'Banco A' ? 'a' : 'b'); active.add('cons'); }
      if (step.kind === 'spend') { active.add('cons'); active.add(step.bank === 'Banco A' ? 'a' : 'b'); }
      if (step.kind === 'setup') { active.add('bc'); active.add('dealer'); active.add('a'); active.add('b'); }
      if (step.kind === 'finish') { active.add('bc'); active.add('a'); active.add('b'); active.add('cons'); }
      return `
        <div class="actor ${active.has('bc')?'active':''}"><div class="icon">🏛️</div><div class="role">Professor</div><div class="name">Banco Central</div><div class="detail">Opera a compra inicial do título</div></div>
        <div class="actor ${active.has('dealer')?'active':''}"><div class="icon">📄</div><div class="role">1 aluno</div><div class="name">Dealer</div><div class="detail">Começa com o título público</div></div>
        <div class="actor ${active.has('a')||active.has('b')?'active':''}"><div class="icon">🏦</div><div class="role">2 alunos</div><div class="name">Banco A + Banco B</div><div class="detail">Reservas, depósitos e empréstimos</div></div>
        <div class="actor ${active.has('cons')?'active':''}"><div class="icon">👥</div><div class="role">Turma</div><div class="name">Consumidores</div><div class="detail">Tomam crédito, gastam e recebem pagamentos</div></div>`;
    }

    function flowMarkup(step) {
      if (step.kind === 'setup') return `<div class="flow-node"><div class="small">Ativo inicial</div><div class="big">Dealer: título público</div></div><div class="flow-arrow">→</div><div class="flow-node"><div class="small">Próxima ação</div><div class="big">BC compra o título</div></div>`;
      if (step.kind === 'finish') return `<div class="flow-node"><div class="small">Base criada pelo BC</div><div class="big">${money(step.state.base)}</div></div><div class="flow-arrow">≠</div><div class="flow-node"><div class="small">Meios de pagamento após o circuito</div><div class="big">${money(step.state.money)}</div></div>`;
      return `<div class="flow-node"><div class="small">Sai de</div><div class="big">${step.from}</div></div><div class="flow-arrow">→</div><div class="flow-node"><div class="small">Chega a</div><div class="big">${step.to}<br><span style="color:var(--blue)">${money(step.amount)}</span></div></div>`;
    }

    function deltaMarkup(step) {
      const parts = [];
      if (step.deltaB > 0) parts.push(`<span class="delta up">Base +${money(step.deltaB)}</span>`);
      else parts.push(`<span class="delta flat">Base: sem mudança</span>`);
      if (step.deltaM > 0.005) parts.push(`<span class="delta up">Meios de pagamento +${money(step.deltaM)}</span>`);
      else if (step.deltaM < -0.005) parts.push(`<span class="delta flat">Meios de pagamento ${money(step.deltaM)}</span>`);
      else parts.push(`<span class="delta flat">Meios de pagamento: sem mudança</span>`);
      if (step.deltaCash > 0.005) parts.push(`<span class="delta shift">Reservas → espécie: ${money(step.deltaCash)}</span>`);
      return parts.join('');
    }

    function render() {
      const step = model.steps[stepIndex];
      const s = step.state;
      $('scoreBase').textContent = money(s.base);
      $('scoreDeposits').textContent = money(s.deposits);
      $('scoreCash').textContent = money(s.cash);
      $('scoreMoney').textContent = money(s.money);
      $('scoreMultiplier').textContent = `${multiplier(s.money, s.base).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})}×`;

      $('stepKicker').textContent = step.kicker;
      $('stepTitle').textContent = step.title;
      $('stepStatus').textContent = `Jogada ${stepIndex} de ${model.steps.length - 1}`;
      $('actors').innerHTML = actorMarkup(step);
      $('actionLabel').textContent = step.label;
      $('actionText').innerHTML = step.text.replace(/(R\$\s?[\d\.]+(?:,\d+)?)/g, '<span class="action-amount">$1</span>');
      $('actionExplain').textContent = step.explain;
      $('flow').innerHTML = flowMarkup(step);
      $('deltas').innerHTML = deltaMarkup(step);
      $('teacherPrompt').innerHTML = `<strong>Pergunta para a turma:</strong> ${step.prompt}`;

      $('prevBtn').disabled = stepIndex === 0;
      $('nextBtn').disabled = stepIndex === model.steps.length - 1;
      if (stepIndex === 0) $('nextBtn').textContent = 'Iniciar operação de mercado aberto';
      else if (stepIndex === model.steps.length - 2) $('nextBtn').textContent = 'Ver síntese final';
      else $('nextBtn').textContent = 'Próxima jogada';

      renderLedger();
      renderTheory();
    }

    function renderLedger() {
      const tbody = $('ledgerBody');
      tbody.innerHTML = model.steps.slice(1, stepIndex + 1).map((step, idx) => {
        const s = step.state;
        return `<tr class="${idx + 1 === stepIndex ? 'current' : ''}">
          <td>${idx + 1}</td><td>${step.label}</td><td>${money(s.base)}</td><td>${money(s.deposits)}</td><td>${money(s.cash)}</td><td>${money(s.money)}</td><td>${money(s.loans)}</td><td>${multiplier(s.money,s.base).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})}×</td>
        </tr>`;
      }).join('');
      if (stepIndex === 0) tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:#94a3b8;padding:22px">O livro razão será preenchido à medida que o jogo avançar.</td></tr>`;
    }

    function renderTheory() {
      const p = model.p;
      const theoretical = p.r > 0 ? p.omo / p.r : Infinity;
      $('theoreticalDeposits').textContent = Number.isFinite(theoretical) ? money(theoretical) : 'Sem limite no modelo';
      const final = model.steps[model.steps.length - 2].state;
      $('finalMoney').textContent = money(final.money);
    }

    function updateLabels() {
      $('omoValue').textContent = money(Number(controls.omo.value));
      $('reserveValue').textContent = `${controls.reserve.value}%`;
      $('lendValue').textContent = `${controls.lend.value}%`;
      $('cashValue').textContent = `${controls.cash.value}%`;
      $('roundsValue').textContent = controls.rounds.value;
      const n = Math.max(4, Math.min(40, Number(controls.consumers.value) || 10));
      $('consumerRoles').textContent = `${n} alunos: Consumidores 1 a ${n}`;
    }

    function resetGame() {
      controls.consumers.value = Math.max(4, Math.min(40, Number(controls.consumers.value) || 10));
      updateLabels();
      model = buildModel();
      stepIndex = 0;
      render();
      window.scrollTo({ top: document.querySelector('.score-grid').offsetTop - 78, behavior: 'smooth' });
    }

    Object.values(controls).forEach(control => {
      control.addEventListener('input', updateLabels);
      control.addEventListener('change', () => document.querySelectorAll('.preset').forEach(b => b.classList.remove('active')));
    });

    document.querySelectorAll('.preset').forEach(btn => {
      btn.addEventListener('click', () => {
        const p = presets[btn.dataset.preset];
        controls.omo.value = p.omo; controls.reserve.value = p.reserve; controls.lend.value = p.lend; controls.cash.value = p.cash; controls.rounds.value = p.rounds;
        document.querySelectorAll('.preset').forEach(b => b.classList.toggle('active', b === btn));
        resetGame();
      });
    });

    $('restartBtn').addEventListener('click', resetGame);
    $('nextBtn').addEventListener('click', () => { if (stepIndex < model.steps.length - 1) { stepIndex++; render(); } });
    $('prevBtn').addEventListener('click', () => { if (stepIndex > 0) { stepIndex--; render(); } });
    $('printBtn').addEventListener('click', () => window.print());
    $('projectorBtn').addEventListener('click', () => {
      document.body.classList.toggle('projector');
      $('projectorBtn').textContent = document.body.classList.contains('projector') ? 'Sair do projetor' : 'Modo projetor';
      if (document.body.classList.contains('projector') && document.documentElement.requestFullscreen) document.documentElement.requestFullscreen().catch(()=>{});
      if (!document.body.classList.contains('projector') && document.fullscreenElement) document.exitFullscreen().catch(()=>{});
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ') { if (stepIndex < model.steps.length - 1) { e.preventDefault(); stepIndex++; render(); } }
      if (e.key === 'ArrowLeft') { if (stepIndex > 0) { e.preventDefault(); stepIndex--; render(); } }
    });

    updateLabels();
    model = buildModel();
    render();
