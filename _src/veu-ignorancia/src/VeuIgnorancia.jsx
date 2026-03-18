import { useState, useEffect, useRef, useCallback } from "react";
import { createClient } from "@supabase/supabase-js";

// ─── SUPABASE ─────────────────────────────────────────────────────────────────
const supabase = createClient(
  "https://ecjeuwadpmtvbkcvrxoc.supabase.co",
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjamV1d2FkcG10dmJrY3ZyeG9jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjAwMzI1MiwiZXhwIjoyMDg3NTc5MjUyfQ.aj3mC2Cgcen4TViejwU_St0sLD0SdrqlSenB66SuA1s"
);
async function sGet(key) {
  try { const { data } = await supabase.from("game_kv").select("value").eq("key", key).single(); return data?.value ?? null; } catch { return null; }
}
async function sSet(key, value) {
  try {
    await supabase.from("game_kv").upsert({ key, value, updated_at: new Date().toISOString() });
    await supabase.channel("vi_bus").send({ type: "broadcast", event: "kv_change", payload: { key } });
  } catch {}
}
async function sList(prefix) {
  try { const { data } = await supabase.from("game_kv").select("key").like("key", `${prefix}%`); return data?.map(r => r.key) ?? []; } catch { return []; }
}

// ─── CONSTANTS ────────────────────────────────────────────────────────────────
const PROFESSOR_PASSWORD = "123123";
const TOTAL_ROUNDS = 5;
const SEQUENCE = ['classe_media', 'pobre', 'rico', 'pobre', 'pobre'];
const SPIN_MS = 4000;

// ─── GAME DATA ────────────────────────────────────────────────────────────────
const BASE = {
  utilitarista: { pobre: 20,  classe_media: 100, rico: 550 },
  igualitarista: { pobre: 90,  classe_media: 90,  rico: 90  },
  rawlsiano:     { pobre: 95,  classe_media: 92,  rico: 110 },
};
const REGIMES = {
  utilitarista: {
    name: "Utilitarista", emoji: "📈", color: "#F59E0B",
    tagline: "Maximiza a soma total.",
    payoff: "Pobre: 20 · Classe Média: 100 · Rico: 550",
    desc_curta: "Faz o bolo crescer. Aceita desigualdade se o total for maior.",
    desc_longa: [
      "A lógica é direta: se a soma total de bem-estar da sociedade é maior, ela é mais justa — mesmo que poucos tenham muito e muitos tenham pouco.",
      "Tributos baixos, liberdade econômica máxima, mercado decide a alocação. Uma empresa pode crescer sem limites. Quem nasce rico tem liberdade para multiplicar riqueza sem tetos redistributivos.",
      "Quem nasce pobre... depende da maré. O sistema não garante o piso — garante o crescimento do bolo. Se o bolo crescer o suficiente, talvez todos se beneficiem. Talvez.",
    ],
  },
  igualitarista: {
    name: "Igualitarista", emoji: "⚖️", color: "#818CF8",
    tagline: "Divide o bolo igualmente.",
    payoff: "Pobre: 90 · Classe Média: 90 · Rico: 90",
    desc_curta: "Todos recebem o mesmo. Nenhuma vantagem de berço.",
    desc_longa: [
      "Todos recebem exatamente o mesmo, independentemente de onde nasceram. Nenhuma vantagem de herança, de rede de contatos, de escola particular.",
      "Para financiar isso: tributação pesada sobre patrimônio e renda alta. Uma empresa rentável não pode acumular muito mais do que as demais — o Estado redistribui até equiparar. Isso cria um teto. Você aceita um teto mais baixo em troca de um piso garantido.",
      "O problema que economistas levantam: limita os incentivos para crescer. Por que arriscar e inovar se o ganho vai ser redistribuído? O bolo pode encolher — mas estará dividido em pedaços iguais.",
    ],
  },
  rawlsiano: {
    name: "Rawlsiano", emoji: "🛡️", color: "#10B981",
    tagline: "Protege quem nasceu mais vulnerável.",
    payoff: "Pobre: 95 · Classe Média: 92 · Rico: 110",
    desc_curta: "Protege o piso. Ricos ganham menos que no utilitarismo, pobres ganham mais.",
    desc_longa: [
      "John Rawls propôs um experimento mental: se você pudesse escolher as regras da sociedade sem saber onde nasceria — sem saber sua classe, seu talento, sua família — qual escolheria?",
      "Por trás desse 'véu da ignorância', pessoas racionais tendem a proteger o piso. Não porque são altruístas, mas porque não sabem se vão nascer pobres. Então escolhem a sociedade onde, mesmo no pior cenário, a vida ainda vale a pena.",
      "Resultado: os pobres têm uma base digna acima do utilitarismo. Os ricos ainda se saem bem — mas contribuem um pouco mais para sustentar o piso. Equilíbrio entre crescimento e proteção.",
    ],
  },
};
const CLASSES = {
  pobre:        { label: "Pobre",        emoji: "🏚️", color: "#EF4444" },
  classe_media: { label: "Classe Média", emoji: "🏠", color: "#F59E0B" },
  rico:         { label: "Rico",         emoji: "🏛️", color: "#10B981" },
};
// Narrativa de vida por rodada (0-4) — contexto ES, tom ácido
// SEQUENCE = ['classe_media', 'pobre', 'rico', 'pobre', 'pobre']
const LIFE_STORIES_BY_ROUND = [
  // Rodada 1 — Classe Média
  {
    headline: "Você nasceu na classe média capixaba",
    scene: "Sobrado próprio em Campo Grande, Serra — financiado em 360 meses. Seu pai é servidor estadual: trabalha no DETRAN-ES há dezoito anos, concursado. Salário de R$ 5.200 que parece confortável até você distribuir entre o financiamento, o plano de saúde básico, o condomínio e a faculdade particular que se tornou o único plano B quando a UFES não deu certo.",
    constraints: "Você não passa fome — isso é real, e não é pouco. A margem de erro, porém, é pequena: uma demissão, um problema de saúde sério, um filho que precisa de cursinho particular... qualquer crise desequilibra tudo em três meses. Você vive exatamente no ponto onde a ascensão exige uma vida inteira de disciplina e a queda exige apenas um azar.",
    punchline: "Nem protegido como os ricos, nem esquecido como os pobres. Apenas... no meio.",
  },
  // Rodada 2 — Pobre (Cariacica)
  {
    headline: "Você nasceu pobre em Cariacica",
    scene: "Cresceu no Itacibá, periferia de Cariacica. Sua mãe é diarista: sai às 6h30, chega às 20h, cuida dos apartamentos na Praia do Canto — onde o piso que ela lava custa mais do que ela ganha no mês. Seu pai trabalha na construção civil por empreitada. Quando não tem serviço, o orçamento não fecha.",
    constraints: "Você está trabalhando aos 16 como motoboy ou no mercadinho do bairro. A UFES existe e é gratuita — mas o cursinho que aumenta as chances custa dinheiro e tempo que você não tem. Cada mês é uma equação difícil: conta de luz, alimentação, condução. A margem de erro é zero. Literalmente.",
    punchline: "Seu talento importa. Mas importa menos do que o CEP onde você nasceu.",
  },
  // Rodada 3 — Rico (Ilha do Boi)
  {
    headline: "Você nasceu rico na Ilha do Boi, Vitória",
    scene: "Cresceu na Ilha do Boi, em Vitória — o bairro mais caro do Espírito Santo, onde o metro quadrado rivaliza com Ipanema. Seu avô fundou uma empresa de mármore e granito em Cachoeiro de Itapemirim. Você estudou no Colégio São Vicente de Paulo, fez intercâmbio nos Estados Unidos e nunca precisou escolher entre comer e estudar.",
    constraints: "Seu primeiro emprego foi numa empresa onde o CEO almoçava com seu pai toda semana. Você entrou como trainee executivo — que, na prática, significa herdeiro em formação. Sua rede de contatos foi construída em jantares em cobertura e passeios de lancha na Baía de Vitória. O capital social vale tanto quanto o financeiro: só que não aparece na declaração de Imposto de Renda.",
    punchline: "Você pode até fracassar. Mas vai ser muito difícil cair para onde os outros nasceram.",
  },
  // Rodada 4 — Pobre (Serra, monoparental)
  {
    headline: "Você nasceu pobre na Serra",
    scene: "Cresceu no Novo Horizonte, Serra. Sua mãe cria você e dois irmãos sozinha: faz bolo para vender durante a semana e cuida de idoso nos fins de semana. Seu pai parou de aparecer quando você tinha 9 anos. Na prática, significa que sua mãe fez o trabalho de dois com o salário de nenhum.",
    constraints: "A armadilha da pobreza não é preguiça — é a impossibilidade de acumular. Todo dinheiro poupado some antes de virar capital: conserto do celular, medicamento, material escolar. Você foi ao cinema pela primeira vez aos 15 anos. Não porque não quisesse antes: o shopping fica do outro lado da cidade e a condução custa R$ 10 de ida e volta.",
    punchline: "A pobreza é cara. Ela cobra juros em tudo: no crédito, no tempo, no sonho.",
  },
  // Rodada 5 — Pobre (interior do ES)
  {
    headline: "Você nasceu pobre no interior do Espírito Santo",
    scene: "Cresceu em Colatina, no noroeste do estado. Sua mãe é caixa de supermercado. Seu avô plantava café no sul do Espírito Santo, mas a propriedade foi vendida para pagar dívida quando você era criança. A escola fica a 12 quilômetros. O ônibus escolar quebrou em março e voltou em agosto.",
    constraints: "A saída de quem nasce aqui tem nome: migrar para Vitória, trabalhar muito e torcer para ser notado. Os empregos bons pedem experiência que você não tem, endereço que você não tem e indicação que você definitivamente não tem. As oportunidades existem — só foram distribuídas com o mesmo critério do sobrenome.",
    punchline: "Mobilidade social não é uma escada. É uma parede com alguns ganchos, e você começa embaixo.",
  },
];
const CIRCS = {
  pobre: [
    { mod: 6,  text: "Um talento raro notado pela professora de matemática: bolsa integral no IFES abriu uma brecha que, nessa condição, pouquíssimos conseguem. Você foi um dos três por geração." },
    { mod: 3,  text: "O bairro puxava para o tráfico. Você chegou perto — mas saiu a tempo. O emprego formal que veio depois virou uma segunda chance que poucos conseguem." },
    { mod: 0,  text: "A vida seguiu o trilho esperado: trabalho informal, conta no limite. Sem avanço, sem retrocesso — a rotina de quem sobrevive sem folga." },
    { mod: -3, text: "Dois anos no tráfico: saiu vivo e sem passagem, mas carregando o estigma. O tempo perdido e as portas fechadas não voltam." },
    { mod: -6, text: "Uma abordagem policial virou processo por engano. Absolvido — mas o antecedente processual fechou portas de emprego formal por anos." },
  ],
  classe_media: [
    { mod: 6,  text: "Um negócio próprio aberto na crise virou empresa de verdade. Saiu na frente de toda uma geração com disciplina, timing e uma dívida que valeu a pena." },
    { mod: 3,  text: "Aprovado em concurso estadual: estabilidade de cargo público mudou o horizonte de planejamento de toda a família." },
    { mod: 0,  text: "CLT estável, conta equilibrada. A vida funcional que a maioria conhece e poucos admitem que é boa." },
    { mod: -3, text: "Reestruturação da empresa: oito meses desempregado consumiram a reserva de emergência. Foi recontratado, mas recomeçou financeiramente do zero." },
    { mod: -6, text: "Separação depois de dez anos: patrimônio dividido ao meio, casa, FGTS e investimentos juntos. Voltou para o aluguel aos 42." },
  ],
  rico: [
    { mod: 6,  text: "Herdou participação societária no momento certo: a valorização do setor portuário triplicou o patrimônio em dois anos sem esforço relevante." },
    { mod: 3,  text: "Acesso via rede fechada a um IPO fora do radar do varejo: o retorno foi o que a maioria dos investidores jamais veria." },
    { mod: 0,  text: "Gestão conservadora do patrimônio: cresceu na média do CDI, sem riscos e sem ganhos extraordinários. O patrimônio existe amanhã — isso já é muito." },
    { mod: -3, text: "Conflito societário com o sócio histórico: dois anos de litígio drenaram dinheiro, atenção e a reputação construída em décadas." },
    { mod: -6, text: "Sucessão mal preparada: o herdeiro assumiu sem experiência real e destruiu metade do que foi construído em trinta anos." },
  ],
};

// ─── UTILITIES ────────────────────────────────────────────────────────────────
function rndCirc(cls) { const a = CIRCS[cls]; return a[Math.floor(Math.random() * a.length)]; }
function genCircs() { return SEQUENCE.map(cls => rndCirc(cls)); }
function calcRoundScore(regime, cls, mod) { return BASE[regime][cls] + mod; }
function calcStats(scores) {
  if (!scores || scores.length === 0) return { total: 0, safety: 0, volatility: 0 };
  const total = scores.reduce((s, x) => s + x, 0);
  const safety = Math.min(...scores);
  const volatility = Math.max(...scores) - Math.min(...scores);
  return { total, safety, volatility };
}
function calcAlt(circs) {
  const out = {};
  Object.keys(BASE).forEach(r => {
    const scores = SEQUENCE.map((cls, i) => BASE[r][cls] + circs[i].mod);
    out[r] = calcStats(scores);
  });
  return out;
}
function rank(players) {
  return [...players].sort((a, b) => {
    const sa = calcStats(a.scores ?? []), sb = calcStats(b.scores ?? []);
    if (sb.safety !== sa.safety) return sb.safety - sa.safety;
    if (sb.total !== sa.total) return sb.total - sa.total;
    return sa.volatility - sb.volatility;
  });
}

// ─── DESIGN TOKENS ────────────────────────────────────────────────────────────
const C = { bg: '#010B18', card: 'rgba(255,255,255,0.04)', border: 'rgba(255,255,255,0.08)', text: '#F1F5F9', muted: '#64748B', subtle: '#334155' };
const BG_STYLE = { minHeight: '100vh', background: C.bg, color: C.text, fontFamily: 'Inter, sans-serif' };
const CARD = { background: C.card, border: `1px solid ${C.border}`, borderRadius: 16 };
function inp(extra = {}) { return { width: '100%', background: 'rgba(255,255,255,0.06)', border: `1px solid ${C.border}`, borderRadius: 8, padding: '12px 14px', color: C.text, fontSize: 14, outline: 'none', boxSizing: 'border-box', fontFamily: 'Inter,sans-serif', ...extra }; }
function btn(color, extra = {}) { return { padding: '13px 24px', background: color, border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 15, color: color === 'transparent' || color?.includes('rgba') ? C.muted : '#000', cursor: 'pointer', fontFamily: 'Inter,sans-serif', ...extra }; }

// ─── ROULETTE ─────────────────────────────────────────────────────────────────
function Roulette({ target, go, onDone, size }) {
  const ORDER = ['pobre', 'classe_media', 'rico'];
  const [idx, setIdx] = useState(0);
  const [done, setDone] = useState(false);
  const timerRef = useRef(null);
  const large = size !== 'small';

  useEffect(() => {
    if (!go) { setDone(false); return; }
    setDone(false);
    let elapsed = 0;
    let interval = 80;

    function tick() {
      setIdx(i => (i + 1) % ORDER.length);
      elapsed += interval;
      if (elapsed < SPIN_MS * 0.5) { interval = 80; }
      else if (elapsed < SPIN_MS * 0.75) { interval = 180; }
      else if (elapsed < SPIN_MS) { interval = 350; }
      else {
        setIdx(ORDER.indexOf(target));
        setDone(true);
        onDone?.();
        return;
      }
      timerRef.current = setTimeout(tick, interval);
    }
    timerRef.current = setTimeout(tick, interval);
    return () => clearTimeout(timerRef.current);
  }, [go, target]);

  const current = done ? target : ORDER[idx];
  const cls = CLASSES[current];

  return (
    <div style={{ textAlign: 'center', padding: large ? '32px 0' : '16px 0' }}>
      <div style={{
        display: 'inline-block',
        background: done ? `${cls.color}18` : C.card,
        border: `2px solid ${done ? cls.color : C.border}`,
        borderRadius: 20,
        padding: large ? '32px 56px' : '20px 36px',
        transition: 'border-color 0.4s, background 0.4s',
        minWidth: large ? 260 : 160,
      }}>
        <div style={{ fontSize: large ? 80 : 48, lineHeight: 1, marginBottom: 12 }}>{cls.emoji}</div>
        <div style={{ fontSize: large ? 30 : 20, fontWeight: 900, color: done ? cls.color : C.muted, letterSpacing: -1, transition: 'color 0.3s' }}>
          {cls.label}
        </div>
        {!done && <div style={{ marginTop: 8, color: C.muted, fontSize: 12 }}>sorteando…</div>}
        {done && <div style={{ marginTop: 8, color: cls.color, fontSize: 12, fontWeight: 600 }}>classe revelada!</div>}
      </div>
    </div>
  );
}

// ─── ENTRY SCREEN ─────────────────────────────────────────────────────────────
function EntryScreen({ onStudent, onProfessor }) {
  const [name, setName] = useState('');
  const [pass, setPass] = useState('');
  const [err, setErr] = useState(false);

  return (
    <div style={{ ...BG_STYLE, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <div style={{ fontSize: 56, marginBottom: 10 }}>⚖️</div>
        <h1 style={{ fontFamily: 'Playfair Display, serif', fontSize: 38, fontWeight: 900, margin: '0 0 8px', lineHeight: 1.1 }}>O Véu da Ignorância</h1>
        <p style={{ color: C.muted, fontSize: 13, margin: 0 }}>Economia do Setor Público · Fucape Business School</p>
      </div>
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center', width: '100%', maxWidth: 460 }}>
        <div style={{ ...CARD, padding: 24, flex: '1 1 180px', minWidth: 180 }}>
          <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: 2, color: C.muted, textTransform: 'uppercase', marginBottom: 12 }}>Aluno</div>
          <input placeholder="Seu nome" value={name} onChange={e => setName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && name.trim() && onStudent(name.trim())}
            style={{ ...inp(), marginBottom: 10 }} />
          <button onClick={() => name.trim() && onStudent(name.trim())}
            style={btn('#10B981', { width: '100%', color: '#000' })}>Entrar →</button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: C.subtle, fontSize: 12, padding: '0 4px' }}>
          <div style={{ width: 1, flex: 1, background: C.border }} />
          <span style={{ padding: '8px 0' }}>ou</span>
          <div style={{ width: 1, flex: 1, background: C.border }} />
        </div>
        <div style={{ ...CARD, padding: 24, flex: '1 1 180px', minWidth: 180 }}>
          <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: 2, color: C.muted, textTransform: 'uppercase', marginBottom: 12 }}>Professor</div>
          <input type="password" placeholder="Senha" value={pass}
            onChange={e => { setPass(e.target.value); setErr(false); }}
            onKeyDown={e => { if (e.key === 'Enter') { if (pass === PROFESSOR_PASSWORD) onProfessor(); else setErr(true); } }}
            style={{ ...inp({ border: `1px solid ${err ? '#EF4444' : C.border}` }), marginBottom: err ? 4 : 10 }} />
          {err && <div style={{ color: '#EF4444', fontSize: 11, marginBottom: 8 }}>Senha incorreta</div>}
          <button onClick={() => { if (pass === PROFESSOR_PASSWORD) onProfessor(); else setErr(true); }}
            style={btn('transparent', { width: '100%', border: '1.5px solid #10B981', color: '#10B981' })}>Painel →</button>
        </div>
      </div>
    </div>
  );
}

// ─── RANKING TABLE ─────────────────────────────────────────────────────────────
function RankingTable({ players, round, isFinal }) {
  const eligible = players.filter(p => (p.scores?.length ?? 0) > 0);
  const sorted = rank(eligible);
  return (
    <div style={{ ...CARD, padding: 24 }}>
      <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5, marginBottom: 16 }}>
        {isFinal ? 'RANKING FINAL' : `RANKING — APÓS RODADA ${round}`}
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ borderBottom: `1px solid ${C.border}` }}>
            <th style={{ textAlign: 'left', padding: '8px 10px', color: C.muted, fontWeight: 600, width: 36 }}>#</th>
            <th style={{ textAlign: 'left', padding: '8px 10px', color: C.muted, fontWeight: 600 }}>Aluno</th>
            <th style={{ textAlign: 'left', padding: '8px 10px', color: C.muted, fontWeight: 600 }}>Regime</th>
            <th style={{ textAlign: 'right', padding: '8px 10px', color: C.muted, fontWeight: 600 }}>Total</th>
            <th style={{ textAlign: 'right', padding: '8px 10px', color: C.muted, fontWeight: 600 }}>Safety ↑</th>
            {isFinal && <th style={{ textAlign: 'right', padding: '8px 10px', color: C.muted, fontWeight: 600 }}>Volat. ↓</th>}
          </tr>
        </thead>
        <tbody>
          {sorted.map((p, i) => {
            const stats = calcStats(p.scores ?? []);
            const rv = REGIMES[p.regime];
            return (
              <tr key={p.name} style={{ borderBottom: `1px solid ${C.border}`, background: i === 0 ? `${rv?.color}10` : 'transparent' }}>
                <td style={{ padding: '10px 10px', fontWeight: 700, color: i === 0 ? '#F59E0B' : C.muted }}>{i === 0 ? '🥇' : i + 1}</td>
                <td style={{ padding: '10px 10px', color: C.text, fontWeight: i === 0 ? 700 : 400 }}>{p.name}</td>
                <td style={{ padding: '10px 10px', color: rv?.color }}>{rv?.emoji} {rv?.name}</td>
                <td style={{ padding: '10px 10px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600 }}>{stats.total}</td>
                <td style={{ padding: '10px 10px', textAlign: 'right', fontFamily: 'monospace', color: '#10B981' }}>{stats.safety}</td>
                {isFinal && <td style={{ padding: '10px 10px', textAlign: 'right', fontFamily: 'monospace', color: C.muted }}>{stats.volatility}</td>}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─── PROFESSOR VIEW ───────────────────────────────────────────────────────────
function ProfessorView({ onExit }) {
  const [gs, setGs] = useState(null);
  const [players, setPlayers] = useState({});
  const [spinDone, setSpinDone] = useState(false);

  const fetchAll = useCallback(async () => {
    const state = await sGet('vi:state');
    setGs(state);
    const keys = await sList('vi:player:');
    const all = {};
    await Promise.all(keys.map(async k => { const p = await sGet(k); if (p) all[p.name] = p; }));
    setPlayers(all);
  }, []);

  useEffect(() => {
    fetchAll();
    // Polling de fallback — garante atualização mesmo se broadcast falhar
    const poll = setInterval(fetchAll, 4000);
    const ch = supabase.channel('vi_bus')
      .on('broadcast', { event: 'kv_change' }, async ({ payload }) => {
        const k = payload?.key;
        if (k === 'vi:state') { const s = await sGet('vi:state'); setGs(s); }
        else if (k?.startsWith('vi:player:')) { const p = await sGet(k); if (p) setPlayers(prev => ({ ...prev, [p.name]: p })); }
      }).subscribe();
    return () => { clearInterval(poll); supabase.removeChannel(ch); };
  }, [fetchAll]);

  useEffect(() => { setSpinDone(false); }, [gs?.round, gs?.phase]);

  const phase = gs?.phase ?? 'lobby';
  const round = gs?.round ?? 1;
  const currentClass = gs?.currentClass;
  const pList = Object.values(players);
  const W = { maxWidth: 800, margin: '0 auto', padding: '28px 20px 80px' };
  const gameUrl = typeof window !== 'undefined' ? window.location.href : '';
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(gameUrl)}&bgcolor=010B18&color=10B981&qzone=1`;

  async function startGame() {
    // Não apaga players — eles já escolheram regime. Apenas inicia a rodada 1.
    await sSet('vi:state', {
      phase: 'spinning',
      round: 1,
      currentClass: SEQUENCE[0],
      spinStart: Date.now(),
      started: true,
      gameId: gs?.gameId ?? Date.now(),
    });
  }
  async function spinRound() {
    const cls = SEQUENCE[round - 1];
    await sSet('vi:state', { ...gs, phase: 'spinning', currentClass: cls, spinStart: Date.now() });
  }
  async function showRanking() { await sSet('vi:state', { ...gs, phase: 'ranking' }); }
  async function nextRound() {
    if (round >= TOTAL_ROUNDS) { await sSet('vi:state', { ...gs, phase: 'final' }); }
    else {
      const nr = round + 1;
      await sSet('vi:state', { ...gs, phase: 'spinning', round: nr, currentClass: SEQUENCE[nr - 1], spinStart: Date.now() });
      setSpinDone(false);
    }
  }
  async function resetGame() {
    const keys = await sList('vi:player:');
    await Promise.all(keys.map(k => supabase.from('game_kv').delete().eq('key', k)));
    await sSet('vi:state', { phase: 'lobby', round: 1, currentClass: null, gameId: Date.now(), started: false });
    setPlayers({});
  }

  return (
    <div style={BG_STYLE}>
      <div style={W}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
          <div>
            <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5 }}>PAINEL DO PROFESSOR</div>
            <h2 style={{ fontFamily: 'Playfair Display, serif', fontSize: 22, fontWeight: 700, margin: '4px 0 0' }}>O Véu da Ignorância</h2>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={resetGame} style={btn('rgba(239,68,68,0.1)', { color: '#EF4444', border: '1px solid rgba(239,68,68,0.3)', fontSize: 13 })}>↺ Resetar</button>
            <button onClick={onExit} style={btn(`rgba(255,255,255,0.05)`, { color: C.muted, border: `1px solid ${C.border}`, fontSize: 13 })}>← Sair</button>
          </div>
        </div>

        {/* Lobby */}
        {(phase === 'lobby') && (
          <>
            <div style={{ display: 'flex', gap: 16, marginBottom: 20, flexWrap: 'wrap' }}>
              <div style={{ ...CARD, padding: 20, display: 'flex', gap: 20, alignItems: 'center', flex: 1 }}>
                <img src={qrUrl} alt="QR" style={{ width: 120, height: 120, borderRadius: 8, flexShrink: 0 }} />
                <div>
                  <div style={{ fontWeight: 700, marginBottom: 6 }}>📱 QR Code para alunos</div>
                  <div style={{ color: C.muted, fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}>Alunos entram com o nome — sem código de acesso.</div>
                  <div style={{ fontSize: 12, color: '#10B981', fontFamily: 'monospace', wordBreak: 'break-all' }}>{gameUrl}</div>
                </div>
              </div>
              <div style={{ ...CARD, padding: 20, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minWidth: 160 }}>
                <div style={{ fontSize: 40, fontWeight: 900, marginBottom: 4 }}>{pList.length}</div>
                <div style={{ color: C.muted, fontSize: 13, marginBottom: 16 }}>aluno{pList.length !== 1 ? 's' : ''}</div>
                <button onClick={startGame}
                  style={btn('#10B981', { fontSize: 14, color: '#000' })}>
                  Iniciar Jogo →
                </button>
              </div>
            </div>
            {pList.length > 0 && (
              <div style={{ ...CARD, padding: 20, marginBottom: 20 }}>
                <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5, marginBottom: 12 }}>ALUNOS CONECTADOS</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {pList.map(p => {
                    const rv = REGIMES[p.regime];
                    return (
                      <div key={p.name} style={{ background: `${rv?.color ?? '#555'}18`, border: `1px solid ${rv?.color ?? '#555'}44`, borderRadius: 8, padding: '6px 12px', fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ color: rv?.color ?? C.muted }}>{rv?.emoji ?? '⏳'}</span>
                        <span>{p.name}</span>
                        <span style={{ color: C.muted, fontSize: 11 }}>{rv?.name ?? 'escolhendo…'}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
            <div style={{ ...CARD, padding: 16, fontSize: 13, color: C.muted, lineHeight: 1.7 }}>
              <strong style={{ color: C.text }}>Critério de desempate:</strong> safety_score (mínimo) → total → menor volatilidade
            </div>
          </>
        )}

        {/* Round controls */}
        {gs?.started && phase !== 'lobby' && phase !== 'final' && (
          <>
            {/* Spin button when in ranking phase (ready for next) */}
            {phase === 'ranking' && (
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
                <button onClick={nextRound} style={btn('#10B981', { color: '#000', fontSize: 15 })}>
                  {round >= TOTAL_ROUNDS ? 'Ver Resultado Final →' : `Rodada ${round + 1} →`}
                </button>
              </div>
            )}

            {/* Roulette card */}
            <div style={{ ...CARD, padding: 24, marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <div>
                  <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5 }}>RODADA {round} DE {TOTAL_ROUNDS}</div>
                  <div style={{ fontSize: 18, fontWeight: 700, marginTop: 2 }}>Sorteio de Classe Social</div>
                </div>
                {phase === 'spinning' && spinDone && (
                  <button onClick={showRanking} style={btn('#10B981', { color: '#000' })}>Ver Ranking →</button>
                )}
              </div>
              <Roulette target={currentClass} go={phase === 'spinning'} onDone={() => setSpinDone(true)} size="large" />
            </div>

            {/* Live ranking during ranking phase */}
            {phase === 'ranking' && pList.filter(p => (p.scores?.length ?? 0) > 0).length > 0 && (
              <RankingTable players={pList} round={round} isFinal={false} />
            )}
          </>
        )}

        {/* Final */}
        {phase === 'final' && (
          <>
            {pList.filter(p => (p.scores?.length ?? 0) > 0).length > 0 && (
              <RankingTable players={pList} round={TOTAL_ROUNDS} isFinal={true} />
            )}
            <div style={{ ...CARD, padding: 16, marginTop: 16, fontSize: 13, color: C.muted, lineHeight: 1.8 }}>
              Os alunos podem ver a tela final no celular com a comparação entre os três regimes.
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ─── STUDENT REGIME CHOICE ────────────────────────────────────────────────────
function StudentRegimeChoice({ onChoose }) {
  const [selected, setSelected] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const keys = Object.keys(REGIMES);

  return (
    <div style={{ ...BG_STYLE, padding: 20 }}>
      <div style={{ maxWidth: 560, margin: '0 auto', paddingTop: 36, paddingBottom: 100 }}>

        {/* Abertura filosófica */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ fontSize: 52, marginBottom: 14 }}>⚖️</div>
          <h1 style={{ fontFamily: 'Playfair Display, serif', fontSize: 26, fontWeight: 900, lineHeight: 1.3, marginBottom: 0 }}>
            Que tipo de sociedade você escolheria se não soubesse em qual classe social nasceria?
          </h1>
        </div>

        {/* Setup */}
        <div style={{ ...CARD, padding: 20, marginBottom: 16, borderLeft: '3px solid #818CF8' }}>
          <p style={{ color: C.text, fontSize: 14, lineHeight: 1.8, margin: 0 }}>
            Esta é a pergunta de John Rawls. Imagine que você vai nascer numa sociedade — mas
            não sabe se vai ser <strong style={{ color: '#EF4444' }}>pobre</strong>,{' '}
            <strong style={{ color: '#F59E0B' }}>classe média</strong> ou{' '}
            <strong style={{ color: '#10B981' }}>rico</strong>. Atrás desse <em>véu da ignorância</em>,
            você precisa escolher as regras dessa sociedade <em>antes de descobrir onde vai nascer.</em>{' '}
            Uma vez escolhido, o regime vale para as 5 rodadas. Não pode trocar depois.
          </p>
        </div>

        {/* Regimes */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20 }}>
          {keys.map(k => {
            const rv = REGIMES[k];
            const sel = selected === k;
            const exp = expanded === k;
            return (
              <div key={k} style={{
                ...CARD, padding: 0, cursor: 'pointer', overflow: 'hidden',
                border: `1px solid ${sel ? rv.color : C.border}`,
                background: sel ? `${rv.color}10` : C.card,
                transition: 'all 0.15s',
              }}>
                {/* Header row */}
                <div onClick={() => setSelected(k)} style={{ padding: '14px 16px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                  <div style={{ fontSize: 26, flexShrink: 0, marginTop: 2 }}>{rv.emoji}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                      <span style={{ fontWeight: 700, fontSize: 16, color: sel ? rv.color : C.text }}>{rv.name}</span>
                      <span style={{ fontSize: 11, color: C.muted, fontStyle: 'italic' }}>{rv.desc_curta}</span>
                    </div>
                    <div style={{ fontSize: 12, color: sel ? rv.color : C.subtle, fontFamily: 'monospace' }}>{rv.payoff}</div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                    <div style={{ width: 18, height: 18, borderRadius: '50%', border: `2px solid ${sel ? rv.color : C.border}`, background: sel ? rv.color : 'transparent', flexShrink: 0 }} />
                    <button onClick={e => { e.stopPropagation(); setExpanded(exp ? null : k); }}
                      style={{ background: 'none', border: 'none', color: C.muted, fontSize: 11, cursor: 'pointer', padding: 0, fontFamily: 'Inter,sans-serif' }}>
                      {exp ? 'menos ▲' : 'entender ▼'}
                    </button>
                  </div>
                </div>
                {/* Expanded explanation */}
                {exp && (
                  <div style={{ padding: '0 16px 16px 54px', borderTop: `1px solid ${C.border}` }}>
                    {rv.desc_longa.map((para, i) => (
                      <p key={i} style={{ color: C.muted, fontSize: 13, lineHeight: 1.7, margin: i === 0 ? '12px 0 8px' : '0 0 8px' }}>{para}</p>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Critério de vitória */}
        <div style={{ ...CARD, padding: 16, marginBottom: 24, borderLeft: '3px solid #F59E0B' }}>
          <div style={{ fontSize: 11, color: '#F59E0B', fontWeight: 800, letterSpacing: 1.5, marginBottom: 8 }}>COMO SE VENCE</div>
          <p style={{ color: C.text, fontSize: 13, lineHeight: 1.7, margin: 0 }}>
            Vence quem tiver o <strong style={{ color: '#10B981' }}>maior piso</strong> — ou seja, a melhor pontuação na rodada em que fez menos pontos.
            Não importa o total acumulado: importa quanto você garantiu sofrer menos na pior geração.
            Em caso de empate no piso, desempata pelo total; depois, por quem teve menos volatilidade.
          </p>
        </div>

        <button disabled={!selected} onClick={() => selected && onChoose(selected)}
          style={btn('#10B981', { width: '100%', opacity: selected ? 1 : 0.4, cursor: selected ? 'pointer' : 'default', color: '#000', fontSize: 16, padding: '15px 0' })}>
          Confirmar Escolha →
        </button>
      </div>
    </div>
  );
}

// ─── STUDENT FINAL ────────────────────────────────────────────────────────────
function StudentFinal({ player, onExit }) {
  const rv = REGIMES[player.regime];
  const stats = calcStats(player.scores ?? []);
  const alts = calcAlt(player.circumstances ?? []);
  const [allPlayers, setAllPlayers] = useState([]);

  useEffect(() => {
    sList('vi:player:').then(rows => {
      setAllPlayers(rows.map(r => r.value).filter(p => p?.regime));
    });
  }, []);

  return (
    <div style={{ ...BG_STYLE, padding: 20 }}>
      <div style={{ maxWidth: 480, margin: '0 auto', paddingTop: 32, paddingBottom: 80 }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5 }}>RESULTADO FINAL</div>
          <h2 style={{ fontFamily: 'Playfair Display, serif', fontSize: 28, fontWeight: 700, margin: '8px 0 4px' }}>{player.name}</h2>
          <div style={{ color: rv.color, fontWeight: 600 }}>{rv.emoji} Regime {rv.name}</div>
        </div>

        {/* Trajectory */}
        <div style={{ ...CARD, padding: 20, marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5, marginBottom: 12 }}>SUA TRAJETÓRIA</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {SEQUENCE.map((cls, i) => {
              const circ = player.circumstances?.[i];
              const sc = player.scores?.[i];
              const cl = CLASSES[cls];
              return (
                <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'center', padding: '10px 12px', background: `${cl.color}10`, borderRadius: 8 }}>
                  <div style={{ fontSize: 24, flexShrink: 0 }}>{cl.emoji}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: cl.color }}>{cl.label}</div>
                    <div style={{ fontSize: 12, color: C.muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{circ?.text}</div>
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: 18 }}>{sc ?? '—'}</div>
                    {circ && <div style={{ fontSize: 11, color: circ.mod > 0 ? '#10B981' : circ.mod < 0 ? '#EF4444' : C.muted }}>
                      {circ.mod > 0 ? `+${circ.mod}` : circ.mod !== 0 ? circ.mod : '±0'}
                    </div>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Stats */}
        <div style={{ ...CARD, padding: 20, marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5, marginBottom: 12 }}>SUA PONTUAÇÃO</div>
          <div style={{ display: 'flex', gap: 8 }}>
            {[
              { label: 'Total', value: stats.total, color: rv.color },
              { label: 'Mínimo', value: stats.safety, color: '#10B981', sub: 'critério principal' },
              { label: 'Volatilidade', value: stats.volatility, color: C.muted, sub: 'menor = melhor' },
            ].map(s => (
              <div key={s.label} style={{ flex: 1, textAlign: 'center', ...CARD, padding: '12px 8px' }}>
                <div style={{ fontSize: 10, color: C.muted, marginBottom: 4, fontWeight: 600 }}>{s.label}</div>
                <div style={{ fontFamily: 'monospace', fontWeight: 800, fontSize: 22, color: s.color }}>{s.value}</div>
                {s.sub && <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>{s.sub}</div>}
              </div>
            ))}
          </div>
        </div>

        {/* Comparison */}
        <div style={{ ...CARD, padding: 20, marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5, marginBottom: 4 }}>E SE VOCÊ TIVESSE ESCOLHIDO OUTRO REGIME?</div>
          <p style={{ color: C.subtle, fontSize: 12, lineHeight: 1.5, margin: '0 0 14px' }}>Com a mesma trajetória e as mesmas circunstâncias:</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {Object.keys(REGIMES).map(rk => {
              const rrv = REGIMES[rk];
              const altSt = alts[rk];
              const isChosen = rk === player.regime;
              return (
                <div key={rk} style={{ padding: '12px 14px', borderRadius: 10, background: isChosen ? `${rrv.color}18` : C.card, border: `1px solid ${isChosen ? rrv.color : C.border}`, display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ fontSize: 22, flexShrink: 0 }}>{rrv.emoji}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: isChosen ? 700 : 400, color: isChosen ? rrv.color : C.text, fontSize: 14 }}>
                      {rrv.name}{isChosen && <span style={{ fontSize: 11, color: C.muted, marginLeft: 6 }}>← sua escolha</span>}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: 16, color: isChosen ? rrv.color : C.text }}>{altSt.total}</div>
                    <div style={{ fontSize: 11, color: '#10B981' }}>min: {altSt.safety}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Class distribution bar chart */}
        {allPlayers.length > 0 && (() => {
          const counts = { utilitarista: 0, igualitarista: 0, rawlsiano: 0 };
          allPlayers.forEach(p => { if (counts[p.regime] !== undefined) counts[p.regime]++; });
          const total = allPlayers.length;
          return (
            <div style={{ ...CARD, padding: 20, marginBottom: 16 }}>
              <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5, marginBottom: 14 }}>
                ESCOLHA DA TURMA ({total} aluno{total !== 1 ? 's' : ''})
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {Object.keys(REGIMES).map(rk => {
                  const rrv = REGIMES[rk];
                  const count = counts[rk];
                  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                  const isChosen = rk === player.regime;
                  return (
                    <div key={rk}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                        <span style={{ fontSize: 13, fontWeight: isChosen ? 700 : 400, color: isChosen ? rrv.color : C.text }}>
                          {rrv.emoji} {rrv.name}{isChosen && <span style={{ fontSize: 11, color: C.muted, marginLeft: 6 }}>← você</span>}
                        </span>
                        <span style={{ fontSize: 13, fontFamily: 'monospace', color: rrv.color, fontWeight: 700 }}>
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div style={{ height: 10, borderRadius: 5, background: `${rrv.color}25`, overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${pct}%`, background: rrv.color, borderRadius: 5, transition: 'width 0.8s ease' }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })()}

        {/* Reflective question */}
        <div style={{ ...CARD, padding: 18, marginBottom: 16, borderLeft: '3px solid #F59E0B' }}>
          <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5, marginBottom: 8 }}>REFLEXÃO FINAL</div>
          <p style={{ color: C.text, fontSize: 14, lineHeight: 1.75, margin: 0, fontStyle: 'italic' }}>
            Agora que você conhece sua trajetória completa — se voltasse atrás do véu da ignorância,
            sem saber onde nasceria, escolheria o mesmo regime?
          </p>
        </div>

        <div style={{ ...CARD, padding: 16, marginBottom: 24, borderLeft: '3px solid #818CF8' }}>
          <p style={{ color: C.text, fontSize: 13, lineHeight: 1.75, margin: 0 }}>
            <strong>Rawls argumenta:</strong> se você não soubesse onde nasceria, qual regime você escolheria?
            O véu da ignorância é esse exercício mental — escolher as regras sem conhecer seu lugar na sociedade.
          </p>
        </div>
        <button onClick={onExit} style={btn(`rgba(255,255,255,0.05)`, { width: '100%', color: C.muted, border: `1px solid ${C.border}` })}>← Voltar ao início</button>
      </div>
    </div>
  );
}

// ─── STUDENT VIEW ─────────────────────────────────────────────────────────────
function StudentView({ name, onExit }) {
  const [gs, setGs] = useState(null);
  const [player, setPlayer] = useState(null);
  const [spinDone, setSpinDone] = useState(false);
  const playerRef = useRef(null);
  useEffect(() => { playerRef.current = player; }, [player]);

  useEffect(() => {
    (async () => {
      const [state, p] = await Promise.all([sGet('vi:state'), sGet(`vi:player:${name}`)]);
      setGs(state);
      if (p) {
        setPlayer(p);
      } else {
        // Registra presença imediatamente (sem regime ainda) para professor ver aluno conectado
        const presence = { name, regime: null, circumstances: null, scores: [] };
        setPlayer(presence);
        await sSet(`vi:player:${name}`, presence);
      }
    })();
    // Polling de fallback para estado do jogo
    const poll = setInterval(async () => {
      const s = await sGet('vi:state');
      setGs(s);
    }, 4000);
    const ch = supabase.channel('vi_bus')
      .on('broadcast', { event: 'kv_change' }, async ({ payload }) => {
        const k = payload?.key;
        if (k === 'vi:state') { const s = await sGet('vi:state'); setGs(s); }
        else if (k === `vi:player:${name}`) { const p = await sGet(`vi:player:${name}`); if (p) setPlayer(p); }
      }).subscribe();
    return () => { clearInterval(poll); supabase.removeChannel(ch); };
  }, [name]);

  useEffect(() => { setSpinDone(false); }, [gs?.round, gs?.phase]);

  async function chooseRegime(regime) {
    const circs = genCircs();
    const p = { name, regime, circumstances: circs, scores: [] };
    setPlayer(p);
    await sSet(`vi:player:${name}`, p);
  }

  async function scoreRound() {
    const p = playerRef.current;
    if (!p?.regime || !gs) return;
    const roundIdx = (gs.round ?? 1) - 1;
    if ((p.scores?.length ?? 0) >= gs.round) return; // already scored
    const circ = p.circumstances?.[roundIdx];
    if (!circ) return;
    const score = calcRoundScore(p.regime, gs.currentClass, circ.mod);
    const updated = { ...p, scores: [...(p.scores ?? []), score] };
    setPlayer(updated);
    await sSet(`vi:player:${name}`, updated);
  }

  // Auto-score when spin animation finishes
  useEffect(() => {
    if (gs?.phase === 'spinning' && spinDone) scoreRound();
  }, [spinDone, gs?.phase]);

  const phase = gs?.phase ?? 'lobby';
  const round = gs?.round ?? 1;
  const p = player;
  const rv = p?.regime ? REGIMES[p.regime] : null;
  const currentClass = gs?.currentClass;
  const roundIdx = round - 1;
  const myCirc = p?.circumstances?.[roundIdx];
  const myScores = p?.scores ?? [];
  const myStats = myScores.length > 0 ? calcStats(myScores) : null;

  // Regime not chosen yet
  if (!p?.regime) return <StudentRegimeChoice onChoose={chooseRegime} />;

  // Final
  if (phase === 'final') return <StudentFinal player={p} onExit={onExit} />;

  // Lobby / waiting
  if (phase === 'lobby' || !gs?.started) {
    return (
      <div style={{ ...BG_STYLE, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24, textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>⚖️</div>
        <h2 style={{ fontFamily: 'Playfair Display, serif', fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Olá, {name}</h2>
        <div style={{ ...CARD, padding: 20, marginBottom: 20, maxWidth: 300, width: '100%' }}>
          <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5, marginBottom: 8 }}>SEU REGIME</div>
          <div style={{ fontSize: 36 }}>{rv?.emoji}</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: rv?.color, marginTop: 8 }}>{rv?.name}</div>
          <p style={{ color: C.muted, fontSize: 13, marginTop: 6, lineHeight: 1.5 }}>{rv?.tagline}</p>
        </div>
        <p style={{ color: C.muted, fontSize: 14 }}>Aguardando o professor iniciar o jogo…</p>
      </div>
    );
  }

  // Spinning
  if (phase === 'spinning') {
    return (
      <div style={{ ...BG_STYLE, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 20, textAlign: 'center' }}>
        <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5, marginBottom: 8 }}>RODADA {round} DE {TOTAL_ROUNDS}</div>
        <h2 style={{ fontFamily: 'Playfair Display, serif', fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Onde você vai nascer?</h2>
        <p style={{ color: C.muted, fontSize: 14, marginBottom: 16 }}>Sorteando classe social…</p>
        <Roulette target={currentClass} go={true} onDone={() => setSpinDone(true)} size="large" />

        {spinDone && currentClass && (() => {
          const story = LIFE_STORIES_BY_ROUND[roundIdx];
          const cl = CLASSES[currentClass];
          return (
            <div style={{ maxWidth: 440, width: '100%', marginTop: 4, textAlign: 'left', display: 'flex', flexDirection: 'column', gap: 10 }}>
              {/* Narrativa de vida */}
              <div style={{ background: `${cl.color}10`, border: `1px solid ${cl.color}40`, borderRadius: 14, padding: 18 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: cl.color, letterSpacing: 1, marginBottom: 8 }}>{story.headline.toUpperCase()}</div>
                <p style={{ color: C.text, fontSize: 13, lineHeight: 1.7, margin: '0 0 8px' }}>{story.scene}</p>
                <p style={{ color: C.muted, fontSize: 13, lineHeight: 1.7, margin: '0 0 8px' }}>{story.constraints}</p>
                <p style={{ color: cl.color, fontSize: 13, fontWeight: 600, fontStyle: 'italic', margin: 0 }}>{story.punchline}</p>
              </div>

              {/* Circunstância individual */}
              {myCirc && (
                <div style={{ ...CARD, padding: 16 }}>
                  <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5, marginBottom: 8 }}>
                    SEU RESULTADO NESTA GERAÇÃO
                  </div>
                  <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                    <div style={{ fontSize: 28, flexShrink: 0, marginTop: 2 }}>
                      {myCirc.mod >= 6 ? '🌟' : myCirc.mod === 3 ? '🌤️' : myCirc.mod === 0 ? '☁️' : myCirc.mod === -3 ? '🌧️' : '⛈️'}
                    </div>
                    <p style={{ color: C.text, fontSize: 13, lineHeight: 1.65, margin: 0, flex: 1 }}>{myCirc.text}</p>
                    <div style={{
                      fontWeight: 800, fontSize: 20, flexShrink: 0, fontFamily: 'monospace',
                      color: myCirc.mod > 0 ? '#10B981' : myCirc.mod < 0 ? '#EF4444' : C.muted,
                    }}>
                      {myCirc.mod > 0 ? `+${myCirc.mod}` : myCirc.mod}
                    </div>
                  </div>
                  {myScores.length === round && (
                    <div style={{ marginTop: 12, paddingTop: 12, borderTop: `1px solid ${C.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: C.muted, fontSize: 13 }}>
                        Pontuação ({BASE[p?.regime]?.[currentClass] ?? '?'} base {myCirc.mod >= 0 ? '+' : ''}{myCirc.mod}):
                      </span>
                      <span style={{ fontFamily: 'monospace', fontWeight: 800, fontSize: 24, color: rv?.color }}>{myScores[round - 1]}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })()}

        <div style={{ marginTop: 10, color: C.muted, fontSize: 12 }}>
          {rv?.emoji} <span style={{ color: rv?.color }}>{rv?.name}</span>
        </div>
      </div>
    );
  }

  // Ranking
  if (phase === 'ranking') {
    return (
      <div style={{ ...BG_STYLE, padding: 20 }}>
        <div style={{ maxWidth: 420, margin: '0 auto', paddingTop: 36 }}>
          <div style={{ textAlign: 'center', marginBottom: 20 }}>
            <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5 }}>RODADA {round} DE {TOTAL_ROUNDS}</div>
            <h2 style={{ fontFamily: 'Playfair Display, serif', fontSize: 24, fontWeight: 700, margin: '8px 0 0' }}>Resultado</h2>
          </div>
          {/* Classe + punchline */}
          {currentClass && (() => {
            const cl = CLASSES[currentClass];
            const story = LIFE_STORIES_BY_ROUND[roundIdx];
            return (
              <div style={{ background: `${cl.color}10`, border: `1px solid ${cl.color}40`, borderRadius: 12, padding: 16, marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                  <div style={{ fontSize: 36 }}>{cl.emoji}</div>
                  <div>
                    <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5 }}>VOCÊ NASCEU COMO</div>
                    <div style={{ fontSize: 20, fontWeight: 800, color: cl.color }}>{cl.label}</div>
                  </div>
                </div>
                <p style={{ color: cl.color, fontSize: 12, fontStyle: 'italic', margin: 0 }}>{story.punchline}</p>
              </div>
            );
          })()}
          {/* Circumstance */}
          {myCirc && (
            <div style={{ ...CARD, padding: 16, marginBottom: 12 }}>
              <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, letterSpacing: 1.5, marginBottom: 8 }}>SEU RESULTADO NESTA GERAÇÃO</div>
              <p style={{ color: C.text, fontSize: 13, lineHeight: 1.6, margin: '0 0 8px' }}>{myCirc.text}</p>
              <span style={{ color: myCirc.mod > 0 ? '#10B981' : myCirc.mod < 0 ? '#EF4444' : C.muted, fontWeight: 700, fontFamily: 'monospace' }}>
                {myCirc.mod > 0 ? `+${myCirc.mod}` : myCirc.mod !== 0 ? myCirc.mod : '±0'} pts
              </span>
            </div>
          )}
          {/* Scores */}
          {myScores.length > 0 && (
            <div style={{ ...CARD, padding: 16 }}>
              <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
                {myScores.map((s, i) => (
                  <div key={i} style={{ flex: 1, textAlign: 'center', background: i === round - 1 ? `${rv?.color}20` : 'rgba(255,255,255,0.03)', border: `1px solid ${i === round - 1 ? rv?.color : C.border}`, borderRadius: 6, padding: '6px 2px' }}>
                    <div style={{ fontSize: 9, color: C.muted }}>R{i + 1}</div>
                    <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: 14 }}>{s}</div>
                  </div>
                ))}
                {Array(TOTAL_ROUNDS - myScores.length).fill(null).map((_, i) => (
                  <div key={`e${i}`} style={{ flex: 1, textAlign: 'center', background: 'rgba(255,255,255,0.02)', border: `1px solid ${C.border}`, borderRadius: 6, padding: '6px 2px' }}>
                    <div style={{ fontSize: 9, color: C.muted }}>R{myScores.length + i + 1}</div>
                    <div style={{ color: C.subtle, fontSize: 14 }}>—</div>
                  </div>
                ))}
              </div>
              {myStats && (
                <div style={{ display: 'flex', gap: 8, paddingTop: 10, borderTop: `1px solid ${C.border}` }}>
                  <div style={{ flex: 1, textAlign: 'center' }}>
                    <div style={{ fontSize: 10, color: C.muted }}>TOTAL</div>
                    <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: 20, color: rv?.color }}>{myStats.total}</div>
                  </div>
                  <div style={{ flex: 1, textAlign: 'center' }}>
                    <div style={{ fontSize: 10, color: C.muted }}>MÍNIMO</div>
                    <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: 20, color: '#10B981' }}>{myStats.safety}</div>
                  </div>
                </div>
              )}
            </div>
          )}
          <p style={{ textAlign: 'center', color: C.subtle, fontSize: 13, marginTop: 16 }}>Aguardando próxima rodada…</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ ...BG_STYLE, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <p style={{ color: C.muted }}>Aguardando…</p>
    </div>
  );
}

// ─── ROOT ─────────────────────────────────────────────────────────────────────
export default function VeuIgnorancia() {
  const [mode, setMode] = useState(null);
  const [playerName, setPlayerName] = useState('');

  if (!mode) return (
    <EntryScreen
      onStudent={n => { setPlayerName(n); setMode('student'); }}
      onProfessor={() => setMode('professor')}
    />
  );
  if (mode === 'professor') return <ProfessorView onExit={() => setMode(null)} />;
  return <StudentView key={playerName} name={playerName} onExit={() => setMode(null)} />;
}
