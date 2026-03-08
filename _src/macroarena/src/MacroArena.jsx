import { useState, useEffect, useCallback, useRef } from "react";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  "https://ecjeuwadpmtvbkcvrxoc.supabase.co",
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjamV1d2FkcG10dmJrY3ZyeG9jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjAwMzI1MiwiZXhwIjoyMDg3NTc5MjUyfQ.aj3mC2Cgcen4TViejwU_St0sLD0SdrqlSenB66SuA1s"
);
import {
  AreaChart, Area, LineChart, Line,
  XAxis, YAxis, ResponsiveContainer, Tooltip
} from "recharts";

// ─────────────────────────────────────────────
// CONSTANTS
// ─────────────────────────────────────────────
const PROFESSOR_PASSWORD = "123123";
const INITIAL_CASH = 10000;
const INITIAL_PRICE = 100;
const AMM_FACTOR = 0.0001;

// Timer por faixa: 0 = sem timer (professor controla)
// Rodadas 1-2: treino livre | 3-6: 120s | 7-10: 90s
const ROUND_TIMER = (round) => {
  if (round <= 2) return 0;
  if (round <= 6) return 120;
  return 90;
};

// Aleatoriedade na magnitude: direção preservada, tamanho varia ±35%
// Ensina que saber a DIREÇÃO é o trabalho analítico;
// a MAGNITUDE é incerteza irredutível — como no mercado real.
const randomizeImpact = (base) => {
  const factor = 0.65 + Math.random() * 0.70; // [0.65, 1.35]
  return base * factor;
};

const C = {
  bg: "#000000", card: "#111111", card2: "#181818",
  border: "#222222", text: "#FFFFFF", muted: "#666666",
  gold: "#F5A623", green: "#00D68F", red: "#FF4757",
};

const ASSETS = [
  { id: "pib",      name: "Ação PIB",      icon: "📈", desc: "Sobe com crescimento real, cai com recessão" },
  { id: "emprego",  name: "Ação Emprego",  icon: "👷", desc: "Sobe quando desemprego cai, cai quando sobe" },
  { id: "inflacao", name: "Ação Inflação", icon: "🔥", desc: "Sobe quando inflação sobe, cai quando deflação" },
];

// ─────────────────────────────────────────────
// CENÁRIOS — explicações com cadeia de mecanismo
// ─────────────────────────────────────────────
const SCENARIOS = [
  {
    round: 1, mode: "treino",
    title: "Copom inicia ciclo de cortes da Selic",
    theme: "Política Monetária",
    text: "Após manter a Selic em 15% ao ano por quase um semestre — o maior nível em 20 anos —, o Copom anuncia o início do ciclo de cortes com redução de 0,5 p.p. O desemprego segue em mínima histórica de 5,4% e o crédito começa a dar sinais de descompressão.",
    impacts: { pib: 0.08, emprego: 0.05, inflacao: 0.06 },
    explanationSteps: [
      { asset: "pib", direction: 1, chain: ["Selic ↓ 0,5 p.p.", "crédito mais barato", "empresas investem mais", "famílias consomem mais", "PIB ↑ → Ação PIB sobe"] },
      { asset: "emprego", direction: 1, chain: ["PIB ↑", "empresas precisam produzir mais", "contratações aumentam", "desemprego ↓ → Ação Emprego sobe"] },
      { asset: "inflacao", direction: 1, chain: ["corte com mercado de trabalho aquecido", "expectativas de inflação não ancoram", "demanda > oferta nos serviços", "Inflação ↑ → Ação Inflação sobe"] },
    ],
  },
  {
    round: 2, mode: "treino",
    title: "Isenção de IR para renda até R$ 5 mil",
    theme: "Política Fiscal e Multiplicador",
    text: "O governo aprova a isenção do Imposto de Renda para quem ganha até R$ 5 mil mensais. Cerca de R$ 28 bilhões retornam à economia. O Banco Central, preocupado com o estímulo à demanda, sinaliza cautela no ritmo de cortes da Selic.",
    impacts: { pib: 0.07, emprego: 0.06, inflacao: 0.10 },
    explanationSteps: [
      { asset: "pib", direction: 1, chain: ["renda disponível ↑ R$ 28 bi", "famílias de baixa renda consomem quase tudo", "multiplicador fiscal amplifica o efeito", "PIB ↑ → Ação PIB sobe"] },
      { asset: "emprego", direction: 1, chain: ["consumo ↑", "setor de serviços e varejo aquecem", "empresas contratam para atender demanda", "desemprego ↓ → Ação Emprego sobe"] },
      { asset: "inflacao", direction: 1, chain: ["demanda ↑ com oferta estável", "economia já sem capacidade ociosa", "sem folga para absorver o choque", "Inflação ↑ forte → Ação Inflação sobe"] },
    ],
  },
  {
    round: 3, mode: "treino",
    title: "Escândalo fiscal em ano eleitoral",
    theme: "Expectativas e Risco Fiscal",
    text: "Uma investigação da PGR expõe irregularidades em emendas parlamentares e desvios em contratos federais às vésperas das eleições de 2026. O risco-país sobe 90 pontos, o câmbio deprecia 7% e investidores exigem prêmio maior nos títulos públicos.",
    impacts: { pib: -0.08, emprego: -0.06, inflacao: 0.09 },
    explanationSteps: [
      { asset: "pib", direction: -1, chain: ["incerteza política ↑", "investidores adiam decisões", "crédito fica mais caro (risco ↑)", "investimento e consumo ↓", "PIB ↓ → Ação PIB cai"] },
      { asset: "emprego", direction: -1, chain: ["empresas congelam contratações", "setor público paralisa obras", "demissões em projetos suspensos", "desemprego ↑ → Ação Emprego cai"] },
      { asset: "inflacao", direction: 1, chain: ["câmbio deprecia 7%", "importados ficam mais caros", "pass-through para combustíveis e insumos", "Inflação ↑ → Ação Inflação sobe"] },
    ],
  },
  {
    round: 4, mode: "treino",
    title: "IBGE divulga PIB consolidado de 2025",
    theme: "PIB Nominal vs. Real — Blanchard Cap. 2",
    text: "O IBGE divulga o PIB consolidado de 2025. O crescimento nominal foi de 8,7%. O deflator implícito ficou em 6,2%, acima do IPCA de 4,44%. O mercado de trabalho fechou o ano com desemprego histórico de 5,4% e renda média recorde.",
    impacts: { pib: 0.04, emprego: 0.05, inflacao: 0.07 },
    explanationSteps: [
      { asset: "pib", direction: 1, chain: ["PIB nominal = 8,7%", "deflator = 6,2%", "PIB real = (1,087 ÷ 1,062) − 1 ≈ 2,3%", "modesto mas acima do esperado → Ação PIB sobe levemente"] },
      { asset: "emprego", direction: 1, chain: ["desemprego em mínima histórica (5,4%)", "renda média em recorde", "mercado mais aquecido do que o esperado", "Emprego ↑ → Ação Emprego sobe"] },
      { asset: "inflacao", direction: 1, chain: ["deflator (6,2%) > IPCA (4,44%)", "preços ao produtor subiram mais que ao consumidor", "sinaliza pressão inflacionária na cadeia produtiva", "Inflação ↑ → Ação Inflação sobe"] },
    ],
  },
  {
    round: 5, mode: "treino",
    title: "Governo anuncia corte de gastos para conter dívida",
    theme: "Multiplicador Fiscal — sentido contrário",
    text: "Com a dívida pública projetada para 83,8% do PIB, o Ministério da Fazenda anuncia contingenciamento de R$ 35 bilhões e revisão do arcabouço fiscal. Juros futuros recuam, mas analistas alertam para impacto no crescimento de curto prazo.",
    impacts: { pib: -0.06, emprego: -0.07, inflacao: -0.08 },
    explanationSteps: [
      { asset: "pib", direction: -1, chain: ["G é componente direto do PIB", "G ↓ R$ 35 bi", "multiplicador amplifica a contração", "PIB ↓ no curto prazo → Ação PIB cai"] },
      { asset: "emprego", direction: -1, chain: ["contratos e obras públicas suspensos", "setor privado dependente de repasses sofre", "demissões em serviços e construção", "desemprego ↑ → Ação Emprego cai"] },
      { asset: "inflacao", direction: -1, chain: ["juros futuros recuam (fiscal mais crível)", "câmbio aprecia com melhora do risco-país", "importados mais baratos reduzem pressão", "Inflação ↓ → Ação Inflação cai"] },
    ],
  },
  {
    round: 6, mode: "competicao",
    title: "Suprema Corte dos EUA derruba tarifas Trump",
    theme: "Choque Externo e Exportações",
    text: "Após as tarifas de Trump chegarem a 40% em 2025 e as exportações brasileiras para os EUA recuarem 6,7%, a Suprema Corte americana derruba as tarifas recíprocas. O Brasil emerge como o maior beneficiado, com redução de 13,6 p.p. nas sobretaxas sobre US$ 21,6 bilhões em produtos.",
    impacts: { pib: 0.09, emprego: 0.08, inflacao: -0.05 },
    explanationSteps: [
      { asset: "pib", direction: 1, chain: ["tarifas caem 13,6 p.p.", "exportações retomam acesso ao mercado americano", "X ↑ → saldo comercial melhora", "PIB ↑ pela ótica da demanda → Ação PIB sobe"] },
      { asset: "emprego", direction: 1, chain: ["setores exportadores reativam produção", "agro, manufatura e celulose contratam", "cadeias antes paralisadas voltam a funcionar", "desemprego ↓ → Ação Emprego sobe"] },
      { asset: "inflacao", direction: -1, chain: ["entrada de dólares aprecia o câmbio", "importados ficam mais baratos", "pressão de custos na cadeia produtiva recua", "Inflação ↓ → Ação Inflação cai"] },
    ],
  },
  {
    round: 7, mode: "competicao",
    title: "Guerra no Oriente Médio: petróleo dispara",
    theme: "Choque de Oferta — Stagflação",
    text: "Conflito entre Irã e Israel fecha parcialmente o Estreito de Ormuz. O barril de petróleo salta de US$ 75 para US$ 115. O frete marítimo internacional triplica em duas semanas. A Petrobras anuncia que não repassará integralmente o aumento à bomba.",
    impacts: { pib: -0.07, emprego: -0.05, inflacao: 0.12 },
    explanationSteps: [
      { asset: "pib", direction: -1, chain: ["petróleo ↑ 53%", "custos de energia e transporte sobem para toda a indústria", "margens caem → produção recua", "PIB ↓ (choque de oferta) → Ação PIB cai"] },
      { asset: "emprego", direction: -1, chain: ["custos de produção ↑", "empresas cortam custos variáveis", "primeiro corte: horas extras e temporários", "desemprego ↑ → Ação Emprego cai"] },
      { asset: "inflacao", direction: 1, chain: ["petróleo e frete mais caros", "combustíveis encarecem o transporte de tudo", "inflação de custos se espalha pela cadeia", "Inflação ↑ forte (stagflação) → Ação Inflação sobe"] },
    ],
  },
  {
    round: 8, mode: "competicao",
    title: "Autonomia plena do Banco Central aprovada",
    theme: "Credibilidade Institucional e Expectativas",
    text: "O Congresso aprova emenda constitucional garantindo autonomia plena e irrevogável ao Banco Central, blindando a política monetária de pressões eleitorais. Risco-país cai 120 pontos, câmbio aprecia 5% e curva de juros futuros recua com força.",
    impacts: { pib: 0.06, emprego: 0.05, inflacao: -0.09 },
    explanationSteps: [
      { asset: "pib", direction: 1, chain: ["credibilidade do BC ↑", "expectativas de inflação futura ancoram", "juro neutro da economia cai", "horizonte de planejamento empresarial melhora", "PIB ↑ → Ação PIB sobe"] },
      { asset: "emprego", direction: 1, chain: ["juro neutro ↓", "projetos de longo prazo se tornam viáveis", "investimento produtivo ↑", "demanda por trabalho ↑ → Ação Emprego sobe"] },
      { asset: "inflacao", direction: -1, chain: ["BC autônomo = compromisso crível com a meta", "agentes ajustam expectativas para baixo", "espiral salário-preço se desarma", "Inflação ↓ → Ação Inflação cai"] },
    ],
  },
  {
    round: 9, mode: "competicao",
    title: "Automação industrial elimina 400 mil postos",
    theme: "Mercado de Trabalho: estrutural vs. cíclico",
    text: "O IBGE divulga que a taxa de desemprego saltou de 5,4% para 9,1% em dois trimestres. Empresas do setor industrial substituíram 400 mil trabalhadores por sistemas automatizados. A renda média dos ocupados sobe 8%, mas o total da massa salarial cai.",
    impacts: { pib: 0.03, emprego: -0.12, inflacao: -0.07 },
    explanationSteps: [
      { asset: "pib", direction: 1, chain: ["automação ↑ produtividade por trabalhador", "output total mantido com menos gente", "PIB não cai — apenas redistribui fatores", "PIB ↑ leve → Ação PIB sobe levemente"] },
      { asset: "emprego", direction: -1, chain: ["máquinas substituem 400 mil trabalhadores", "desemprego estrutural: habilidades obsoletas", "diferente do cíclico: juro baixo não resolve", "desemprego ↑ forte → Ação Emprego cai forte"] },
      { asset: "inflacao", direction: -1, chain: ["massa salarial total cai", "famílias desempregadas consomem menos", "demanda agregada ↓", "Inflação ↓ → Ação Inflação cai"] },
    ],
  },
  {
    round: 10, mode: "competicao",
    title: "Síntese: leitura integrada do trimestre",
    theme: "Todas as variáveis — Blanchard Cap. 2",
    text: "Resumo do trimestre: PIB nominal cresceu 6,2%, deflator ficou em 5,5%, desemprego recuou de 9,1% para 8,3%, Selic chegou a 11,5% e o Tesouro registrou déficit primário de 0,6% do PIB. O câmbio estabilizou em R$ 5,40.",
    impacts: { pib: 0.05, emprego: 0.06, inflacao: 0.04 },
    explanationSteps: [
      { asset: "pib", direction: 1, chain: ["PIB nominal 6,2% ÷ deflator 5,5%", "PIB real ≈ 0,7%", "crescimento modesto mas consistente", "PIB ↑ leve → Ação PIB sobe levemente"] },
      { asset: "emprego", direction: 1, chain: ["desemprego caiu de 9,1% → 8,3%", "recuperação após choque de automação", "Selic em queda facilita novas contratações", "Emprego ↑ → Ação Emprego sobe"] },
      { asset: "inflacao", direction: 1, chain: ["deflator ainda em 5,5% (acima da meta)", "déficit primário mantém pressão fiscal", "câmbio estável não alivia", "Inflação ↑ leve → Ação Inflação sobe"] },
    ],
  },
];

// ─────────────────────────────────────────────
// STORAGE HELPERS — Supabase Realtime
// ─────────────────────────────────────────────
async function sGet(key) {
  try {
    const { data } = await supabase.from("game_kv").select("value").eq("key", key).single();
    return data?.value ?? null;
  } catch { return null; }
}

async function sSet(key, value) {
  try {
    await supabase.from("game_kv").upsert({ key, value, updated_at: new Date().toISOString() });
    // Notifica todos os clientes via Broadcast (não requer configuração DDL)
    await supabase.channel("game_bus").send({ type: "broadcast", event: "kv_change", payload: { key } });
  } catch {}
}

async function sList(prefix) {
  try {
    const { data } = await supabase.from("game_kv").select("key").like("key", `${prefix}%`);
    return data?.map(r => r.key) ?? [];
  } catch { return []; }
}

const fmtBRL = v => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
const fmtPct = v => `${v >= 0 ? "+" : ""}${(v * 100).toFixed(2)}%`;
const col = v => (v >= 0 ? C.green : C.red);
const newPrice = (cur, qty, buy) => cur * (1 + (buy ? 1 : -1) * Math.abs(qty) * AMM_FACTOR);

// ─────────────────────────────────────────────
// GLOBAL STYLES
// ─────────────────────────────────────────────
const GlobalStyles = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;600;700;800;900&display=swap');
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #000; color: #fff; font-family: 'DM Sans', sans-serif; -webkit-font-smoothing: antialiased; font-size: 15px; }
    input { outline: none; font-family: inherit; }
    button { font-family: inherit; transition: opacity .15s, transform .1s; }
    button:active { transform: scale(0.97); }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #111; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.2} }
    @keyframes fall { to { transform: translateY(110vh) rotate(720deg); opacity: 0; } }
    @keyframes shake { 0%,100%{transform:translateX(0)} 20%{transform:translateX(-10px)} 40%{transform:translateX(10px)} 60%{transform:translateX(-8px)} 80%{transform:translateX(8px)} }
    @keyframes fadeUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
    @keyframes slideIn { from{transform:translateY(100%)} to{transform:translateY(0)} }
    @keyframes glow { 0%,100%{box-shadow:0 0 8px #F5A62344} 50%{box-shadow:0 0 20px #F5A62388} }
  `}</style>
);

// ─────────────────────────────────────────────
// CONFETTI
// ─────────────────────────────────────────────
function Confetti({ active }) {
  if (!active) return null;
  const pieces = Array.from({ length: 50 }, (_, i) => ({
    id: i, x: Math.random() * 100,
    color: [C.gold, C.green, "#FF6B6B", "#4ECDC4", "#45B7D1", "#fff"][Math.floor(Math.random() * 6)],
    delay: Math.random() * 0.8, dur: 1.2 + Math.random() * 1.5,
    size: 5 + Math.random() * 9, circle: Math.random() > 0.5,
  }));
  return (
    <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 999, overflow: "hidden" }}>
      {pieces.map(p => (
        <div key={p.id} style={{
          position: "absolute", left: `${p.x}%`, top: -20,
          width: p.size, height: p.size, backgroundColor: p.color,
          borderRadius: p.circle ? "50%" : 2,
          animation: `fall ${p.dur}s ${p.delay}s linear forwards`,
        }} />
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────
// SPARKLINE
// ─────────────────────────────────────────────
function Sparkline({ data, color }) {
  if (!data || data.length < 2) return <div style={{ height: 44 }} />;
  const chartData = data.map((price, i) => ({ i, price }));
  const gradId = `sg-${color.replace("#", "")}`;
  return (
    <ResponsiveContainer width="100%" height={44}>
      <AreaChart data={chartData} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.25} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area type="monotone" dataKey="price" stroke={color} strokeWidth={1.5}
          fill={`url(#${gradId})`} dot={false} isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ─────────────────────────────────────────────
// TIMER BAR
// ─────────────────────────────────────────────
function TimerBar({ timerStart, duration }) {
  const [remaining, setRemaining] = useState(duration);
  useEffect(() => {
    const iv = setInterval(() => {
      const elapsed = (Date.now() - timerStart) / 1000;
      setRemaining(Math.max(0, duration - elapsed));
    }, 200);
    return () => clearInterval(iv);
  }, [timerStart, duration]);
  const pct = (remaining / duration) * 100;
  const c = pct > 50 ? C.green : pct > 25 ? C.gold : C.red;
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ color: C.muted, fontSize: 12 }}>Mercado aberto</span>
        <span style={{ color: c, fontFamily: "'Space Mono', monospace", fontWeight: 700, fontSize: 13 }}>{Math.ceil(remaining)}s</span>
      </div>
      <div style={{ height: 3, backgroundColor: "#1a1a1a", borderRadius: 2 }}>
        <div style={{ height: "100%", width: `${pct}%`, backgroundColor: c, borderRadius: 2, transition: "width .2s, background-color .5s" }} />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// EXPLANATION STEPS — cadeia de mecanismo com setas
// ─────────────────────────────────────────────
function ExplanationSteps({ steps }) {
  const assetMap = { pib: ASSETS[0], emprego: ASSETS[1], inflacao: ASSETS[2] };
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {steps.map((step, si) => {
        const asset = assetMap[step.asset];
        const bg = step.direction > 0 ? "#06110A" : "#130608";
        const accent = step.direction > 0 ? C.green : C.red;
        return (
          <div key={si} style={{ backgroundColor: bg, borderRadius: 12, padding: "12px 14px", border: `1px solid ${accent}22` }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
              <span style={{ fontSize: 15 }}>{asset.icon}</span>
              <span style={{ fontSize: 12, fontWeight: 800, color: accent }}>{asset.name}</span>
              <span style={{ marginLeft: "auto", fontSize: 12, fontWeight: 800, color: accent, fontFamily: "'Space Mono', monospace" }}>
                {step.direction > 0 ? "▲ SOBE" : "▼ CAI"}
              </span>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 4 }}>
              {step.chain.map((item, ci) => {
                const isLast = ci === step.chain.length - 1;
                return (
                  <div key={ci} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <span style={{
                      fontSize: 11, lineHeight: 1.4,
                      color: isLast ? accent : "#ccc",
                      fontWeight: isLast ? 800 : 400,
                      backgroundColor: isLast ? `${accent}18` : "transparent",
                      padding: isLast ? "2px 8px" : "0",
                      borderRadius: isLast ? 6 : 0,
                    }}>{item}</span>
                    {!isLast && <span style={{ color: C.muted, fontSize: 11, flexShrink: 0 }}>→</span>}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────
// TRADE MODAL — monta ordem (não executa ainda)
// ─────────────────────────────────────────────
function TradeModal({ asset, price, cash, position, onClose, onStage, existingOrder }) {
  const [side, setSide] = useState(existingOrder?.side ?? null);
  const [qty, setQty] = useState(existingOrder?.qty ?? 10);

  const maxBuy = Math.max(1, Math.floor(cash / price));
  const maxSell = position;

  const handleSetSide = (newSide) => {
    setSide(newSide);
    if (newSide === "buy") setQty(q => Math.min(q, maxBuy));
    else if (newSide === "sell") setQty(q => Math.min(Math.max(q, 1), maxSell || 1));
  };

  const total = qty * price;
  const canAdd = side === "buy" ? total <= cash : side === "sell" ? qty <= position && position > 0 : false;
  const noPosition = side === "sell" && position === 0;
  const saldoApos = side === "buy" ? cash - total : side === "sell" ? cash + total : cash;

  return (
    <div style={{ position: "fixed", inset: 0, backgroundColor: "rgba(0,0,0,.88)", display: "flex", alignItems: "flex-end", zIndex: 300 }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{
        width: "100%", maxWidth: 500, margin: "0 auto",
        backgroundColor: "#0C0C0C", borderRadius: "20px 20px 0 0",
        padding: "20px 20px 44px", border: `1px solid ${C.border}`,
        animation: "slideIn .25s ease-out",
      }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
          <div>
            <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 2, color: C.gold, textTransform: "uppercase", marginBottom: 4 }}>MONTAR ORDEM</div>
            <div style={{ fontSize: 18, fontWeight: 800 }}>{asset.icon} {asset.name}</div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2 }}>
            <button onClick={onClose} style={{ background: "none", border: "none", color: C.muted, fontSize: 22, cursor: "pointer", lineHeight: 1 }}>×</button>
            <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 15, fontWeight: 700, color: C.muted }}>{fmtBRL(price)}/unid.</div>
          </div>
        </div>

        {/* Contexto: Financeiro + Estoque */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 14 }}>
          <div style={{ backgroundColor: "#071410", border: `1px solid ${C.green}33`, borderRadius: 10, padding: "9px 12px" }}>
            <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 1.5, color: C.green, textTransform: "uppercase", marginBottom: 3 }}>Financeiro</div>
            <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 13, fontWeight: 700 }}>{fmtBRL(cash)}</div>
            <div style={{ fontSize: 10, color: C.muted, marginTop: 1 }}>disponível · máx. {maxBuy} unid.</div>
          </div>
          <div style={{ backgroundColor: "#0D0D07", border: `1px solid ${C.gold}33`, borderRadius: 10, padding: "9px 12px" }}>
            <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 1.5, color: C.gold, textTransform: "uppercase", marginBottom: 3 }}>Estoque</div>
            <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 13, fontWeight: 700 }}>{position} unid.</div>
            <div style={{ fontSize: 10, color: C.muted, marginTop: 1 }}>em carteira · {fmtBRL(position * price)}</div>
          </div>
        </div>

        {/* Side picker */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 14 }}>
          <button onClick={() => handleSetSide("sell")} disabled={position === 0} style={{
            padding: "12px 10px", borderRadius: 12, fontWeight: 800, fontSize: 14,
            cursor: position === 0 ? "not-allowed" : "pointer",
            backgroundColor: side === "sell" ? "#1C1400" : C.card,
            border: `2px solid ${side === "sell" ? C.gold : C.border}`,
            color: side === "sell" ? C.gold : position === 0 ? "#333" : C.muted,
            opacity: position === 0 ? 0.45 : 1,
          }}>
            <div>VENDER</div>
            <div style={{ fontSize: 10, fontWeight: 400, marginTop: 2, color: side === "sell" ? C.gold + "99" : C.muted }}>
              máx. {position} unid.
            </div>
          </button>
          <button onClick={() => handleSetSide("buy")} style={{
            padding: "12px 10px", borderRadius: 12, fontWeight: 800, fontSize: 14, cursor: "pointer",
            backgroundColor: side === "buy" ? C.gold : C.card,
            border: side === "buy" ? "none" : `2px solid ${C.border}`,
            color: side === "buy" ? "#000" : C.muted,
          }}>
            <div>COMPRAR</div>
            <div style={{ fontSize: 10, fontWeight: 400, marginTop: 2, color: side === "buy" ? "#555" : C.muted }}>
              máx. {maxBuy} unid.
            </div>
          </button>
        </div>

        {/* Quantidade */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, border: `1px solid ${C.border}`, borderRadius: 12, padding: "10px 16px", backgroundColor: C.card, marginBottom: 10 }}>
          <button onClick={() => setQty(q => Math.max(1, q - 10))} style={{ width: 36, height: 36, borderRadius: 8, border: `1px solid ${C.border}`, backgroundColor: "#1e1e1e", color: C.gold, fontSize: 22, cursor: "pointer" }}>−</button>
          <div style={{ flex: 1, textAlign: "center" }}>
            <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 24, fontWeight: 700 }}>{qty}</div>
            <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>unidades</div>
          </div>
          <button
            onClick={() => {
              const max = side === "buy" ? maxBuy : side === "sell" ? maxSell : 999;
              setQty(q => Math.min(q + 10, max));
            }}
            style={{ width: 36, height: 36, borderRadius: 8, border: `1px solid ${C.border}`, backgroundColor: "#1e1e1e", color: C.gold, fontSize: 22, cursor: "pointer" }}
          >+</button>
        </div>

        {/* Valor da ordem + financeiro após */}
        <div style={{ backgroundColor: C.card2, borderRadius: 10, padding: "10px 14px", marginBottom: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: C.muted, fontSize: 12 }}>Valor da ordem</span>
            <span style={{ fontFamily: "'Space Mono', monospace", fontWeight: 700, fontSize: 13 }}>{fmtBRL(total)}</span>
          </div>
          {side && (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: `1px solid ${C.border}`, paddingTop: 7, marginTop: 7 }}>
              <span style={{ color: C.muted, fontSize: 12 }}>Financeiro após ordem</span>
              <span style={{ fontFamily: "'Space Mono', monospace", fontWeight: 700, fontSize: 13, color: saldoApos < 0 ? C.red : C.green }}>
                {fmtBRL(Math.max(0, saldoApos))}
              </span>
            </div>
          )}
        </div>

        {/* Validação */}
        {noPosition && (
          <div style={{ color: C.red, fontSize: 12, marginBottom: 10, textAlign: "center" }}>Você não tem este ativo em carteira para vender</div>
        )}
        {side === "sell" && !noPosition && !canAdd && (
          <div style={{ color: C.red, fontSize: 12, marginBottom: 10, textAlign: "center" }}>Quantidade maior que o estoque ({position} unid.)</div>
        )}

        {/* Botão principal */}
        <button
          disabled={!side || !canAdd}
          onClick={() => { if (side && canAdd) onStage(side, qty); }}
          style={{
            width: "100%", padding: "15px", borderRadius: 14, fontWeight: 800, fontSize: 15,
            backgroundColor: !side || !canAdd ? "#1a1a1a" : side === "buy" ? C.gold : "#1C1400",
            border: !side || !canAdd ? "none" : side === "buy" ? "none" : `1.5px solid ${C.gold}`,
            color: !side || !canAdd ? C.muted : side === "buy" ? "#000" : C.gold,
            cursor: !side || !canAdd ? "not-allowed" : "pointer",
          }}
        >
          {!side
            ? "Selecione compra ou venda"
            : !canAdd
              ? (side === "buy" ? `Limite: máx. ${maxBuy} unid. (${fmtBRL(cash)})` : "Sem estoque para vender")
              : side === "buy"
                ? `Comprar ${qty} unid. · ${fmtBRL(total)}`
                : `Vender ${qty} unid. · receber ${fmtBRL(total)}`}
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// ASSET CARD
// ─────────────────────────────────────────────
function AssetCard({ asset, price, history, position, cash, pendingOrder, onStage, open }) {
  const [modal, setModal] = useState(false);
  const start = history?.[0] || INITIAL_PRICE;
  const change = (price - start) / start;
  const chartCol = change >= 0 ? C.green : C.red;
  return (
    <>
      <div style={{ backgroundColor: C.card, borderRadius: 16, padding: 16, border: `1px solid ${pendingOrder ? C.gold + "55" : C.border}`, marginBottom: 10, animation: "fadeUp .3s ease-out" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 800 }}>{asset.icon} {asset.name}</div>
            <div style={{ color: C.muted, fontSize: 12, marginTop: 2 }}>{asset.desc}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 17, fontWeight: 700 }}>{fmtBRL(price)}</div>
            <div style={{ color: chartCol, fontSize: 12, fontWeight: 700, marginTop: 2 }}>
              {change >= 0 ? "▲" : "▼"} {Math.abs(change * 100).toFixed(2)}%
            </div>
          </div>
        </div>
        <Sparkline data={history} color={chartCol} />
        {position > 0 && (
          <div style={{ marginTop: 8, padding: "7px 12px", backgroundColor: "#0D0D0D", borderRadius: 8, fontSize: 12, color: C.muted, display: "flex", justifyContent: "space-between" }}>
            <span>Posição: <b style={{ color: C.text }}>{position} unid.</b></span>
            <span>Valor: <b style={{ color: C.text }}>{fmtBRL(position * price)}</b></span>
          </div>
        )}
        {open && (
          pendingOrder ? (
            <button onClick={() => setModal(true)} style={{
              width: "100%", marginTop: 10, padding: "11px 14px",
              backgroundColor: "transparent",
              border: `1.5px solid ${pendingOrder.side === "buy" ? C.gold : C.gold + "99"}`,
              borderRadius: 10, fontWeight: 700, fontSize: 13,
              color: C.gold, cursor: "pointer",
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <span style={{ fontSize: 10, backgroundColor: pendingOrder.side === "buy" ? C.gold : "#1C1400", color: pendingOrder.side === "buy" ? "#000" : C.gold, borderRadius: 5, padding: "2px 7px", fontWeight: 800 }}>
                {pendingOrder.side === "buy" ? "COMPRA" : "VENDA"}
              </span>
              <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 12 }}>{pendingOrder.qty} unid.</span>
              <span style={{ fontSize: 11, color: C.muted }}>✏ editar</span>
            </button>
          ) : (
            <button onClick={() => setModal(true)} style={{
              width: "100%", marginTop: 10, padding: "12px 0",
              backgroundColor: C.gold, border: "none",
              borderRadius: 10, fontWeight: 800, fontSize: 13,
              color: "#000", cursor: "pointer",
            }}>
              Montar Ordem
            </button>
          )
        )}
      </div>
      {modal && (
        <TradeModal asset={asset} price={price} cash={cash} position={position}
          existingOrder={pendingOrder}
          onClose={() => setModal(false)}
          onStage={(side, qty) => { onStage(asset.id, side, qty); setModal(false); }} />
      )}
    </>
  );
}

// ─────────────────────────────────────────────
// ORDER BASKET — cesta de ordens antes de enviar
// ─────────────────────────────────────────────
function OrderBasket({ orders, prices, cash, positions, onSubmit }) {
  const [confirming, setConfirming] = useState(false);
  const entries = ASSETS.map(a => ({ asset: a, order: orders[a.id], price: prices[a.id] || INITIAL_PRICE }))
    .filter(e => e.order);
  if (entries.length === 0) return null;

  const totalBuy = entries.filter(e => e.order.side === "buy").reduce((s, e) => s + e.order.qty * e.price, 0);
  const totalSell = entries.filter(e => e.order.side === "sell").reduce((s, e) => s + e.order.qty * e.price, 0);
  const cashAfter = cash - totalBuy + totalSell;

  const handleConfirm = () => { onSubmit(); setConfirming(false); };

  return (
    <div style={{ position: "fixed", bottom: 0, left: 0, right: 0, zIndex: 200 }}>
      {confirming ? (
        <div onClick={() => setConfirming(false)} style={{ position: "fixed", inset: 0, backgroundColor: "rgba(0,0,0,.75)", display: "flex", alignItems: "flex-end" }}>
          <div onClick={e => e.stopPropagation()} style={{
            width: "100%", maxWidth: 500, margin: "0 auto",
            backgroundColor: "#0C0C0C", borderRadius: "20px 20px 0 0",
            padding: "22px 20px 44px", border: `1px solid ${C.border}`,
            animation: "slideIn .25s ease-out",
          }}>
            <div style={{ fontSize: 9, fontWeight: 800, letterSpacing: 2, color: C.gold, textTransform: "uppercase", marginBottom: 16 }}>Confirmar e enviar ordens</div>

            {/* Resumo financeiro + estoque */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 16 }}>
              <div style={{ backgroundColor: "#071410", border: `1px solid ${C.green}33`, borderRadius: 10, padding: "9px 12px" }}>
                <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 1.5, color: C.green, textTransform: "uppercase", marginBottom: 3 }}>Financeiro atual</div>
                <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 13, fontWeight: 700 }}>{fmtBRL(cash)}</div>
                <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 5, paddingTop: 5, borderTop: `1px solid ${C.green}22` }}>
                  <span style={{ fontSize: 10, color: C.muted }}>após ordens</span>
                  <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 11, fontWeight: 700, color: cashAfter >= 0 ? C.green : C.red, marginLeft: "auto" }}>{fmtBRL(cashAfter)}</span>
                </div>
              </div>
              <div style={{ backgroundColor: "#0D0D07", border: `1px solid ${C.gold}33`, borderRadius: 10, padding: "9px 12px" }}>
                <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 1.5, color: C.gold, textTransform: "uppercase", marginBottom: 4 }}>Estoque em carteira</div>
                {ASSETS.map(a => {
                  const pos = positions?.[a.id] || 0;
                  const order = orders[a.id];
                  const posAfter = pos + (order ? (order.side === "buy" ? order.qty : -order.qty) : 0);
                  return (
                    <div key={a.id} style={{ display: "flex", justifyContent: "space-between", fontSize: 10, marginBottom: 2, color: pos > 0 || posAfter > 0 ? C.text : C.muted }}>
                      <span>{a.icon} {a.name.replace("Ação ", "")}</span>
                      <span style={{ fontFamily: "'Space Mono', monospace" }}>
                        {pos}{order ? <span style={{ color: order.side === "buy" ? C.green : C.red }}>→{posAfter}</span> : ""}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Lista de ordens */}
            {entries.map(({ asset, order, price }) => {
              const isBuy = order.side === "buy";
              return (
                <div key={asset.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "11px 0", borderBottom: `1px solid ${C.border}` }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{
                      fontSize: 10, fontWeight: 800, padding: "3px 8px", borderRadius: 6,
                      backgroundColor: isBuy ? C.gold : "#1C1400",
                      color: isBuy ? "#000" : C.gold,
                      border: isBuy ? "none" : `1px solid ${C.gold}`,
                    }}>{isBuy ? "COMPRA" : "VENDA"}</span>
                    <span style={{ fontWeight: 700, fontSize: 14 }}>{asset.icon} {asset.name.replace("Ação ", "")}</span>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 13, fontWeight: 700 }}>{order.qty} unid.</div>
                    <div style={{ color: isBuy ? C.red : C.green, fontSize: 11, fontWeight: 700 }}>
                      {isBuy ? "−" : "+"}{fmtBRL(order.qty * price)}
                    </div>
                  </div>
                </div>
              );
            })}

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 18 }}>
              <button onClick={() => setConfirming(false)} style={{
                padding: "14px", borderRadius: 12, fontWeight: 700, fontSize: 14,
                backgroundColor: "transparent", border: `1px solid ${C.border}`,
                color: C.muted, cursor: "pointer",
              }}>← Editar</button>
              <button onClick={handleConfirm} style={{
                padding: "14px", borderRadius: 12, fontWeight: 800, fontSize: 14,
                backgroundColor: C.gold, border: "none", color: "#000", cursor: "pointer",
              }}>Confirmar →</button>
            </div>
          </div>
        </div>
      ) : (
        <div style={{
          backgroundColor: "rgba(0,0,0,.96)", borderTop: `1px solid ${C.gold}55`,
          padding: "12px 16px", backdropFilter: "blur(12px)",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", maxWidth: 500, margin: "0 auto" }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 800 }}>
                {entries.length} {entries.length === 1 ? "ordem montada" : "ordens montadas"}
              </div>
              <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>
                Financeiro após: <span style={{ color: cashAfter >= 0 ? C.green : C.red, fontWeight: 700 }}>{fmtBRL(cashAfter)}</span>
              </div>
            </div>
            <button onClick={() => setConfirming(true)} style={{
              padding: "12px 20px", backgroundColor: C.gold, border: "none",
              borderRadius: 12, fontWeight: 800, fontSize: 14, color: "#000", cursor: "pointer",
            }}>Revisar e Enviar →</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
// STUDENT VIEW
// ─────────────────────────────────────────────
function StudentView({ name, gameState, prices, priceHistory, player, onTrade }) {
  const [confetti, setConfetti] = useState(false);
  const [shake, setShake] = useState(false);
  const [pendingOrders, setPendingOrders] = useState({ pib: null, emprego: null, inflacao: null });
  const prevPhase = useRef(null);
  const prevWealth = useRef(INITIAL_CASH);

  const totalWealth = player
    ? player.cash + ASSETS.reduce((s, a) => s + (player.positions[a.id] || 0) * (prices[a.id] || INITIAL_PRICE), 0)
    : INITIAL_CASH;
  const ret = (totalWealth - INITIAL_CASH) / INITIAL_CASH;

  useEffect(() => {
    if (prevPhase.current === "scenario" && gameState?.phase === "closed") {
      if (totalWealth > prevWealth.current + 1) { setConfetti(true); setTimeout(() => setConfetti(false), 3500); }
      else if (totalWealth < prevWealth.current - 1) { setShake(true); setTimeout(() => setShake(false), 700); }
      prevWealth.current = totalWealth;
    }
    if (gameState?.phase === "reading") prevWealth.current = totalWealth;
    if (gameState?.phase !== "scenario") setPendingOrders({ pib: null, emprego: null, inflacao: null });
    prevPhase.current = gameState?.phase;
  }, [gameState?.phase]);

  const sc = gameState?.round ? SCENARIOS[gameState.round - 1] : null;
  const phase = gameState?.phase;
  const open = phase === "scenario";
  const reading = phase === "reading";
  const timerDuration = sc ? ROUND_TIMER(sc.round) : 0;

  const handleStageOrder = (assetId, side, qty) => {
    setPendingOrders(prev => ({ ...prev, [assetId]: { side, qty } }));
  };

  const handleSubmitOrders = async () => {
    for (const a of ASSETS) {
      const order = pendingOrders[a.id];
      if (order) await onTrade(a.id, order.side, order.qty, prices[a.id] || INITIAL_PRICE);
    }
    setPendingOrders({ pib: null, emprego: null, inflacao: null });
  };

  if (!gameState?.gameStarted) {
    return (
      <div style={{ minHeight: "100vh", backgroundColor: C.bg, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 24 }}>
        <GlobalStyles />
        <div style={{ fontSize: 60, marginBottom: 12 }}>🏟️</div>
        <div style={{ fontSize: 32, fontWeight: 900, letterSpacing: -1, marginBottom: 6 }}>Macro<span style={{ color: C.gold }}>Arena</span></div>
        <div style={{ color: C.muted, fontSize: 14, marginBottom: 32, textAlign: "center" }}>Aguarde o professor iniciar o jogo</div>
        <div style={{ backgroundColor: C.card, borderRadius: 40, padding: "10px 20px", fontSize: 14, fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 7, height: 7, borderRadius: "50%", backgroundColor: C.green, animation: "pulse 2s infinite" }} />
          {name}
        </div>
      </div>
    );
  }

  // ── FASE DE LEITURA: cenário + carteira, sem negociação ──
  if (reading && sc) {
    return (
      <div style={{ minHeight: "100vh", backgroundColor: C.bg, fontFamily: "'DM Sans', sans-serif" }}>
        <GlobalStyles />
        <div style={{
          position: "sticky", top: 0, zIndex: 100,
          backgroundColor: "rgba(0,0,0,.95)", backdropFilter: "blur(12px)",
          borderBottom: `1px solid ${C.border}`, padding: "8px 16px",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", maxWidth: 500, margin: "0 auto" }}>
            <div style={{ fontSize: 10, color: C.muted, letterSpacing: 1, textTransform: "uppercase" }}>
              🏟️ R{gameState.round}/10
              {sc.mode === "treino" && <span style={{ color: C.gold, marginLeft: 5 }}>treino</span>}
            </div>
            <div style={{ backgroundColor: "#0A0A14", border: `1px solid ${C.gold}44`, borderRadius: 20, padding: "4px 11px", fontSize: 10, fontWeight: 700, color: C.gold }}>
              📖 Leia o cenário
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6, maxWidth: 500, margin: "6px auto 0" }}>
            <div style={{ backgroundColor: C.card2, borderRadius: 8, padding: "6px 10px" }}>
              <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 2 }}>Caixa</div>
              <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 12, fontWeight: 700 }}>{fmtBRL(player?.cash ?? INITIAL_CASH)}</div>
            </div>
            <div style={{ backgroundColor: C.card2, borderRadius: 8, padding: "6px 10px" }}>
              <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 2 }}>Patrimônio</div>
              <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 12, fontWeight: 700 }}>{fmtBRL(totalWealth)}</div>
            </div>
            <div style={{ backgroundColor: C.card2, borderRadius: 8, padding: "6px 10px", textAlign: "right" }}>
              <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 2 }}>Retorno</div>
              <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 12, fontWeight: 700, color: col(ret) }}>{ret >= 0 ? "+" : ""}{(ret * 100).toFixed(2)}%</div>
            </div>
          </div>
        </div>

        <div style={{ padding: "16px 16px 32px", maxWidth: 500, margin: "0 auto" }}>
          <div style={{ backgroundColor: C.card2, borderRadius: 20, padding: "4px 12px", fontSize: 11, color: C.muted, display: "inline-block", marginBottom: 12 }}>{sc.theme}</div>

          {/* Cenário */}
          <div style={{ backgroundColor: C.card, borderRadius: 16, padding: 20, border: `1px solid ${C.gold}33`, marginBottom: 14 }}>
            <div style={{ color: C.gold, fontSize: 9, fontWeight: 800, textTransform: "uppercase", letterSpacing: 2, marginBottom: 10 }}>
              Cenário · Rodada {gameState.round}
              {sc.mode === "treino" && <span style={{ marginLeft: 8, backgroundColor: C.gold + "22", padding: "1px 7px", borderRadius: 10, fontSize: 10 }}>treino</span>}
            </div>
            <div style={{ fontSize: 17, fontWeight: 800, marginBottom: 12, lineHeight: 1.3 }}>{sc.title}</div>
            <div style={{ color: "#bbb", fontSize: 14, lineHeight: 1.7 }}>{sc.text}</div>
          </div>

          {/* Carteira atual */}
          <div style={{ backgroundColor: C.card, borderRadius: 16, padding: 16, border: `1px solid ${C.border}` }}>
            <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: 2, color: C.muted, marginBottom: 12, textTransform: "uppercase" }}>Sua Carteira Atual</div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <span style={{ color: C.muted, fontSize: 13 }}>Caixa disponível</span>
              <span style={{ fontFamily: "'Space Mono', monospace", fontWeight: 700 }}>{fmtBRL(player?.cash ?? INITIAL_CASH)}</span>
            </div>
            {ASSETS.map(a => {
              const pos = player?.positions[a.id] || 0;
              const val = pos * (prices[a.id] || INITIAL_PRICE);
              return (
                <div key={a.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderTop: `1px solid ${C.border}` }}>
                  <span style={{ fontSize: 13, color: pos > 0 ? C.text : C.muted }}>{a.icon} {a.name.replace("Ação ", "")}: {pos > 0 ? `${pos} unid.` : "—"}</span>
                  {pos > 0 && <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 12 }}>{fmtBRL(val)}</span>}
                </div>
              );
            })}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: `1px solid ${C.gold}33`, paddingTop: 10, marginTop: 4 }}>
              <span style={{ fontSize: 13, fontWeight: 800, color: C.gold }}>Total</span>
              <span style={{ fontFamily: "'Space Mono', monospace", fontWeight: 800, color: C.gold }}>{fmtBRL(totalWealth)}</span>
            </div>
          </div>

          <div style={{ marginTop: 18, textAlign: "center", color: C.muted, fontSize: 13, display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: C.muted, animation: "pulse 2s infinite" }} />
            Aguardando abertura do mercado
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", backgroundColor: C.bg, fontFamily: "'DM Sans', sans-serif", animation: shake ? "shake .6s" : "none" }}>
      <GlobalStyles />
      <Confetti active={confetti} />
      <div style={{
        position: "sticky", top: 0, zIndex: 100,
        backgroundColor: "rgba(0,0,0,.95)", backdropFilter: "blur(12px)",
        borderBottom: `1px solid ${C.border}`, padding: "8px 16px",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", maxWidth: 500, margin: "0 auto" }}>
          <div style={{ fontSize: 10, color: C.muted, letterSpacing: 1, textTransform: "uppercase" }}>
            🏟️ R{gameState.round}/10
            {sc?.mode === "treino" && <span style={{ color: C.gold, marginLeft: 5 }}>treino</span>}
          </div>
          <div style={{ fontSize: 11, color: C.muted, fontWeight: 600 }}>{name}</div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6, maxWidth: 500, margin: "6px auto 0" }}>
          <div style={{ backgroundColor: C.card2, borderRadius: 8, padding: "6px 10px" }}>
            <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 2 }}>Caixa</div>
            <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 12, fontWeight: 700 }}>{fmtBRL(player?.cash ?? INITIAL_CASH)}</div>
          </div>
          <div style={{ backgroundColor: C.card2, borderRadius: 8, padding: "6px 10px" }}>
            <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 2 }}>Patrimônio</div>
            <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 12, fontWeight: 700 }}>{fmtBRL(totalWealth)}</div>
          </div>
          <div style={{ backgroundColor: C.card2, borderRadius: 8, padding: "6px 10px", textAlign: "right" }}>
            <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 2 }}>Retorno</div>
            <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 12, fontWeight: 700, color: col(ret) }}>{ret >= 0 ? "+" : ""}{(ret * 100).toFixed(2)}%</div>
          </div>
        </div>
      </div>

      <div style={{ padding: "14px 16px", maxWidth: 500, margin: "0 auto", paddingBottom: open ? 100 : 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
          <div style={{ backgroundColor: C.card2, borderRadius: 20, padding: "4px 12px", fontSize: 11, color: C.muted }}>{sc?.theme}</div>
          <div style={{
            borderRadius: 20, padding: "4px 12px", fontSize: 11, fontWeight: 700,
            backgroundColor: open ? "#001A08" : "#1a1a0a",
            color: open ? C.green : C.muted,
            border: `1px solid ${open ? C.green + "44" : C.border}`,
          }}>
            {open ? (timerDuration === 0 ? "● Treino — sem timer" : "● Mercado Aberto") : gameState.phase === "closed" ? "🔒 Encerrado" : "⏸ Aguardando"}
          </div>
        </div>

        {sc && (
          <>
            <div style={{ backgroundColor: C.card, borderRadius: 16, padding: 16, border: `1px solid ${C.border}`, marginBottom: 12 }}>
              <div style={{ color: C.gold, fontSize: 10, fontWeight: 800, textTransform: "uppercase", letterSpacing: 2, marginBottom: 8 }}>
                Cenário · Rodada {gameState.round}
                {sc.mode === "treino" && <span style={{ marginLeft: 8, backgroundColor: C.gold + "22", padding: "1px 7px", borderRadius: 10, fontSize: 10 }}>treino</span>}
              </div>
              <div style={{ fontSize: 15, fontWeight: 800, marginBottom: 8, lineHeight: 1.3 }}>{sc.title}</div>
              <div style={{ color: "#bbb", fontSize: 13, lineHeight: 1.6 }}>{sc.text}</div>
            </div>

            {open && timerDuration > 0 && gameState.timerStart && (
              <TimerBar timerStart={gameState.timerStart} duration={timerDuration} />
            )}

            {gameState.phase === "closed" && (
              <div style={{ marginBottom: 12, animation: "fadeUp .4s ease-out" }}>
                <div style={{ color: C.green, fontWeight: 800, fontSize: 13, marginBottom: 10 }}>📋 Mecanismo de transmissão</div>
                <ExplanationSteps steps={sc.explanationSteps} />
                <div style={{ marginTop: 10, backgroundColor: "#0D0D18", borderRadius: 10, padding: "10px 14px", border: `1px solid ${C.gold}22` }}>
                  <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, marginBottom: 3 }}>💡 Sobre a magnitude</div>
                  <div style={{ fontSize: 11, color: "#888", lineHeight: 1.6 }}>
                    A <b style={{ color: "#aaa" }}>direção</b> você previu com a análise. A <b style={{ color: "#aaa" }}>magnitude</b> foi sorteada — como no mercado real, onde economistas acertam o sinal mas raramente o tamanho exato do impacto.
                  </div>
                </div>
              </div>
            )}

            {gameState.phase === "closed" && player && (() => {
              const pnl = totalWealth - prevWealth.current;
              return (
                <div style={{ backgroundColor: C.card, borderRadius: 16, padding: 14, border: `1px solid ${col(pnl)}44`, marginBottom: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontSize: 13, color: C.muted }}>Resultado da rodada</div>
                  <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 16, fontWeight: 700, color: col(pnl) }}>{pnl >= 0 ? "+" : ""}{fmtBRL(pnl)}</div>
                </div>
              );
            })()}

            {ASSETS.map(a => (
              <AssetCard key={a.id} asset={a}
                price={prices[a.id] || INITIAL_PRICE}
                history={priceHistory[a.id] || [INITIAL_PRICE]}
                position={player?.positions[a.id] || 0}
                cash={player?.cash || INITIAL_CASH}
                pendingOrder={pendingOrders[a.id]}
                onStage={handleStageOrder}
                open={open} />
            ))}
            {open && <OrderBasket orders={pendingOrders} prices={prices} cash={player?.cash ?? INITIAL_CASH} positions={player?.positions ?? {}} onSubmit={handleSubmitOrders} />}
          </>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// PROFESSOR VIEW
// ─────────────────────────────────────────────
function ProfessorView({ gameState, prices, priceHistory, players, onControl }) {
  const pCount = Object.keys(players).length;
  const sc = gameState?.round ? SCENARIOS[gameState.round - 1] : null;
  const timerDuration = sc ? ROUND_TIMER(sc.round) : 0;

  const leaderboard = Object.entries(players)
    .map(([name, p]) => {
      const w = p.cash + ASSETS.reduce((s, a) => s + (p.positions[a.id] || 0) * (prices[a.id] || INITIAL_PRICE), 0);
      return { name, w, ret: (w - INITIAL_CASH) / INITIAL_CASH };
    })
    .sort((a, b) => b.w - a.w);

  const maxRounds = Math.max(...ASSETS.map(a => (priceHistory[a.id] || []).length));
  const chartData = Array.from({ length: maxRounds }, (_, i) => ({
    r: i + 1,
    pib: priceHistory.pib?.[i] || INITIAL_PRICE,
    emprego: priceHistory.emprego?.[i] || INITIAL_PRICE,
    inflacao: priceHistory.inflacao?.[i] || INITIAL_PRICE,
  }));

  const phase = gameState?.phase;

  return (
    <div style={{ minHeight: "100vh", backgroundColor: C.bg, padding: "20px 24px", fontFamily: "'DM Sans', sans-serif", color: C.text }}>
      <GlobalStyles />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 22 }}>
        <div>
          <div style={{ fontSize: 24, fontWeight: 900, letterSpacing: -1 }}>🏟️ Macro<span style={{ color: C.gold }}>Arena</span></div>
          <div style={{ color: C.muted, fontSize: 12, marginTop: 2 }}>Painel do Professor · Fucape Business School</div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <div style={{ backgroundColor: C.card, borderRadius: 20, padding: "5px 14px", fontSize: 12 }}>
            <span style={{ color: C.green }}>●</span> {pCount} {pCount === 1 ? "aluno" : "alunos"}
          </div>
          {gameState?.gameStarted && (
            <>
              <div style={{ backgroundColor: C.card2, borderRadius: 20, padding: "5px 14px", color: C.gold, fontSize: 12, fontWeight: 800 }}>
                Rodada {gameState.round}/10
                {sc?.mode === "treino" && <span style={{ color: "#777", marginLeft: 5 }}>· treino</span>}
              </div>
              <div style={{
                backgroundColor: phase === "scenario" ? "#001A08" : phase === "reading" ? "#0A0A14" : "#1a1a0a",
                border: `1px solid ${phase === "scenario" ? C.green + "55" : phase === "reading" ? C.gold + "55" : C.border}`,
                borderRadius: 20, padding: "5px 14px", fontSize: 12, fontWeight: 700,
                color: phase === "scenario" ? C.green : phase === "reading" ? C.gold : C.muted,
              }}>
                {phase === "scenario"
                  ? (timerDuration === 0 ? "● Treino — sem timer" : "● Mercado Aberto")
                  : phase === "reading" ? "📖 Lendo o Cenário"
                  : phase === "closed" ? "🔒 Encerrado" : "⏸ Aguardando"}
              </div>
            </>
          )}
        </div>
      </div>

      {!gameState?.gameStarted ? (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, maxWidth: 740, margin: "0 auto" }}>
          <div style={{ backgroundColor: C.card, borderRadius: 18, padding: 24, border: `1px solid ${C.border}` }}>
            <div style={{ fontWeight: 800, marginBottom: 16 }}>📱 QR Code para alunos</div>
            <img src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(window.location.href)}&bgcolor=111111&color=F5A623&qzone=1`} alt="QR Code" style={{ width: 180, height: 180, borderRadius: 12, display: "block", margin: "0 auto 14px" }} />
            <div style={{ color: C.muted, fontSize: 11, textAlign: "center", wordBreak: "break-all" }}>{window.location.href}</div>
          </div>
          <div style={{ backgroundColor: C.card, borderRadius: 18, padding: 24, border: `1px solid ${C.border}` }}>
            <div style={{ fontWeight: 800, marginBottom: 14 }}>👥 Alunos conectados ({pCount})</div>
            <div style={{ maxHeight: 180, overflowY: "auto", marginBottom: 16 }}>
              {Object.keys(players).length === 0 ? (
                <div style={{ color: C.muted, fontSize: 13 }}>Aguardando alunos...</div>
              ) : Object.keys(players).map(n => (
                <div key={n} style={{ padding: "6px 0", borderBottom: `1px solid ${C.border}`, fontSize: 13, display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ color: C.green, fontSize: 9 }}>●</span>{n}
                </div>
              ))}
            </div>
            <button onClick={() => onControl("startGame")} style={{ width: "100%", padding: 14, backgroundColor: C.gold, border: "none", borderRadius: 12, fontWeight: 800, fontSize: 16, color: "#000", cursor: "pointer", animation: "glow 2s infinite" }}>▶ Iniciar Jogo</button>
            <button onClick={() => onControl("reset")} style={{ width: "100%", marginTop: 8, padding: 10, backgroundColor: "transparent", border: `1px solid ${C.border}`, borderRadius: 12, fontWeight: 600, fontSize: 13, color: C.muted, cursor: "pointer" }}>🔄 Resetar</button>
          </div>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "320px 1fr 280px", gap: 18 }}>
          {/* LEFT */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {sc && (
              <div style={{ backgroundColor: C.card, borderRadius: 16, padding: 16, border: `1px solid ${C.border}` }}>
                <div style={{ color: C.gold, fontSize: 10, fontWeight: 800, letterSpacing: 2, textTransform: "uppercase", marginBottom: 6 }}>
                  Rodada {gameState.round} · {sc.theme}
                </div>
                <div style={{ fontSize: 14, fontWeight: 800, marginBottom: 8, lineHeight: 1.3 }}>{sc.title}</div>
                <div style={{ fontSize: 12, color: "#bbb", lineHeight: 1.6 }}>{sc.text}</div>
                {phase === "closed" && (
                  <div style={{ marginTop: 14 }}>
                    <div style={{ fontSize: 11, color: C.green, fontWeight: 700, marginBottom: 8 }}>📋 Mecanismo de transmissão</div>
                    <ExplanationSteps steps={sc.explanationSteps} />
                    <div style={{ marginTop: 10, backgroundColor: "#0D0D18", borderRadius: 10, padding: "8px 12px", border: `1px solid ${C.gold}22` }}>
                      <div style={{ fontSize: 10, color: C.gold, fontWeight: 700, marginBottom: 3 }}>💡 Discuta com a turma</div>
                      <div style={{ fontSize: 11, color: "#777", lineHeight: 1.5 }}>Direção = análise econômica. Magnitude = incerteza irredutível do mercado real.</div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {phase === "scenario" && timerDuration > 0 && gameState.timerStart && (
              <div style={{ backgroundColor: C.card, borderRadius: 14, padding: 14, border: `1px solid ${C.border}` }}>
                <TimerBar timerStart={gameState.timerStart} duration={timerDuration} />
              </div>
            )}
            {phase === "scenario" && timerDuration === 0 && (
              <div style={{ backgroundColor: "#0D1200", borderRadius: 14, padding: 14, border: `1px solid ${C.gold}33`, fontSize: 12, color: C.gold, textAlign: "center" }}>
                🎓 Rodada de treino — você controla o ritmo
              </div>
            )}

            <div style={{ backgroundColor: C.card, borderRadius: 16, padding: 16, border: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: 2, color: C.muted, marginBottom: 12, textTransform: "uppercase" }}>Controles</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {(phase === "lobby" || !phase) && <button onClick={() => onControl("showScenario")} style={{ padding: "12px", backgroundColor: C.gold, border: "none", borderRadius: 10, fontWeight: 800, color: "#000", cursor: "pointer", fontSize: 14 }}>📖 Mostrar Cenário</button>}
                {phase === "reading" && <button onClick={() => onControl("openMarket")} style={{ padding: "12px", backgroundColor: C.green, border: "none", borderRadius: 10, fontWeight: 800, color: "#000", cursor: "pointer", fontSize: 14 }}>▶ Abrir Mercado</button>}
                {phase === "scenario" && <button onClick={() => onControl("closeMarket")} style={{ padding: "12px", backgroundColor: C.red, border: "none", borderRadius: 10, fontWeight: 800, color: "#fff", cursor: "pointer", fontSize: 14 }}>🔒 Fechar Mercado</button>}
                {phase === "closed" && gameState.round < 10 && <button onClick={() => onControl("nextRound")} style={{ padding: "12px", backgroundColor: C.green, border: "none", borderRadius: 10, fontWeight: 800, color: "#000", cursor: "pointer", fontSize: 14 }}>⏭ Próxima Rodada</button>}
                {phase === "closed" && gameState.round >= 10 && <div style={{ backgroundColor: "#0D1A0D", border: `1px solid ${C.green}44`, borderRadius: 10, padding: 12, textAlign: "center", fontSize: 13, color: C.green, fontWeight: 800 }}>🏆 Jogo Encerrado!</div>}
                <button onClick={() => onControl("reset")} style={{ padding: "9px", backgroundColor: "transparent", border: `1px solid ${C.border}`, borderRadius: 10, fontWeight: 600, color: C.muted, cursor: "pointer", fontSize: 12 }}>🔄 Resetar Jogo</button>
              </div>
            </div>
          </div>

          {/* CENTER */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ backgroundColor: C.card, borderRadius: 16, padding: 16, border: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: 2, color: C.muted, marginBottom: 14, textTransform: "uppercase" }}>Preços em tempo real</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
                {ASSETS.map(a => {
                  const p = prices[a.id] || INITIAL_PRICE;
                  const chg = (p - INITIAL_PRICE) / INITIAL_PRICE;
                  return (
                    <div key={a.id} style={{ backgroundColor: C.card2, borderRadius: 12, padding: "12px 14px", border: `1px solid ${col(chg)}33` }}>
                      <div style={{ fontSize: 13, marginBottom: 6 }}>{a.icon} <b style={{ fontSize: 12 }}>{a.name.replace("Ação ", "")}</b></div>
                      <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 16, fontWeight: 700 }}>{fmtBRL(p)}</div>
                      <div style={{ color: col(chg), fontSize: 12, fontWeight: 700, marginTop: 3 }}>{chg >= 0 ? "▲" : "▼"} {Math.abs(chg * 100).toFixed(2)}%</div>
                      <Sparkline data={priceHistory[a.id] || [INITIAL_PRICE]} color={col(chg)} />
                    </div>
                  );
                })}
              </div>
            </div>
            <div style={{ backgroundColor: C.card, borderRadius: 16, padding: 16, border: `1px solid ${C.border}`, flex: 1 }}>
              <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: 2, color: C.muted, marginBottom: 14, textTransform: "uppercase" }}>Evolução por rodada</div>
              {chartData.length > 1 ? (
                <>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={chartData}>
                      <XAxis dataKey="r" stroke={C.muted} tick={{ fontSize: 11 }} />
                      <YAxis stroke={C.muted} tick={{ fontSize: 11 }} domain={["auto", "auto"]} />
                      <Tooltip contentStyle={{ backgroundColor: C.card2, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 12 }} labelFormatter={v => `Rodada ${v}`} formatter={(v, n) => [fmtBRL(v), n.charAt(0).toUpperCase() + n.slice(1)]} />
                      <Line type="monotone" dataKey="pib" stroke={C.gold} strokeWidth={2} dot={false} name="PIB" />
                      <Line type="monotone" dataKey="emprego" stroke={C.green} strokeWidth={2} dot={false} name="Emprego" />
                      <Line type="monotone" dataKey="inflacao" stroke={C.red} strokeWidth={2} dot={false} name="Inflação" />
                    </LineChart>
                  </ResponsiveContainer>
                  <div style={{ display: "flex", gap: 16, marginTop: 10, justifyContent: "center" }}>
                    {[["📈 PIB", C.gold], ["👷 Emprego", C.green], ["🔥 Inflação", C.red]].map(([n, c]) => (
                      <div key={n} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11 }}>
                        <div style={{ width: 14, height: 2, backgroundColor: c, borderRadius: 1 }} />
                        <span style={{ color: C.muted }}>{n}</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div style={{ height: 200, display: "flex", alignItems: "center", justifyContent: "center", color: C.muted, fontSize: 13 }}>Gráfico disponível após 2 rodadas</div>
              )}
            </div>
          </div>

          {/* RIGHT */}
          <div style={{ backgroundColor: C.card, borderRadius: 16, padding: 16, border: `1px solid ${C.border}` }}>
            <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: 2, color: C.muted, marginBottom: 14, textTransform: "uppercase" }}>🏆 Ranking</div>
            {leaderboard.length === 0 ? (
              <div style={{ color: C.muted, fontSize: 13 }}>Nenhum jogador ainda</div>
            ) : leaderboard.slice(0, 15).map((p, i) => (
              <div key={p.name} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: `1px solid ${C.border}` }}>
                <div style={{ width: 22, height: 22, borderRadius: "50%", flexShrink: 0, backgroundColor: i === 0 ? C.gold : i === 1 ? "#C0C0C0" : i === 2 ? "#CD7F32" : "#1e1e1e", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 800, color: i < 3 ? "#000" : C.muted }}>{i + 1}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{p.name}</div>
                  <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 10, color: C.muted }}>{fmtBRL(p.w)}</div>
                </div>
                <div style={{ color: col(p.ret), fontSize: 11, fontFamily: "'Space Mono', monospace", fontWeight: 700, flexShrink: 0 }}>{fmtPct(p.ret)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
// ENTRY SCREEN
// ─────────────────────────────────────────────
function EntryScreen({ onStudent, onProfessor }) {
  const [nameInput, setNameInput] = useState("");
  const [passInput, setPassInput] = useState("");
  const [passErr, setPassErr] = useState(false);
  return (
    <div style={{ minHeight: "100vh", backgroundColor: C.bg, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 24, position: "relative", overflow: "hidden" }}>
      <GlobalStyles />
      <div style={{ position: "fixed", inset: 0, opacity: 0.04, pointerEvents: "none", backgroundImage: "linear-gradient(#fff 1px,transparent 1px),linear-gradient(90deg,#fff 1px,transparent 1px)", backgroundSize: "36px 36px" }} />
      <div style={{ position: "fixed", width: 400, height: 400, borderRadius: "50%", background: `radial-gradient(circle, ${C.gold}18 0%, transparent 70%)`, top: "10%", left: "50%", transform: "translateX(-50%)", pointerEvents: "none" }} />
      <div style={{ textAlign: "center", marginBottom: 44, position: "relative" }}>
        <div style={{ fontSize: 72, marginBottom: 10, filter: "drop-shadow(0 0 24px #F5A62344)" }}>🏟️</div>
        <div style={{ fontSize: 44, fontWeight: 900, letterSpacing: -2, lineHeight: 1 }}>Macro<span style={{ color: C.gold }}>Arena</span></div>
        <div style={{ color: C.muted, fontSize: 14, marginTop: 10 }}>Bolsa de Valores Macroeconômica · Fucape Business School</div>
        <div style={{ color: "#444", fontSize: 12, marginTop: 4 }}>Baseado em Blanchard, <em>Macroeconomia</em>, Capítulo 2</div>
      </div>
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", justifyContent: "center", width: "100%", maxWidth: 440 }}>
        <div style={{ backgroundColor: C.card, borderRadius: 18, padding: 20, border: `1px solid ${C.border}`, flex: "1 1 180px", minWidth: 180 }}>
          <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: 2, color: C.muted, textTransform: "uppercase", marginBottom: 12 }}>Aluno</div>
          <input placeholder="Seu nome completo" value={nameInput} onChange={e => setNameInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && nameInput.trim() && onStudent(nameInput.trim())}
            style={{ width: "100%", padding: "12px 14px", backgroundColor: "#0D0D0D", border: `1px solid ${C.border}`, borderRadius: 10, color: C.text, fontSize: 14, marginBottom: 10 }} />
          <button onClick={() => nameInput.trim() && onStudent(nameInput.trim())} style={{ width: "100%", padding: "13px 0", backgroundColor: C.gold, border: "none", borderRadius: 10, fontWeight: 800, fontSize: 15, color: "#000", cursor: "pointer" }}>Entrar →</button>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", color: C.muted, fontSize: 12, padding: "0 4px" }}>
          <div style={{ width: 1, flex: 1, backgroundColor: C.border }} />
          <span style={{ padding: "8px 0" }}>ou</span>
          <div style={{ width: 1, flex: 1, backgroundColor: C.border }} />
        </div>
        <div style={{ backgroundColor: C.card, borderRadius: 18, padding: 20, border: `1px solid ${C.border}`, flex: "1 1 180px", minWidth: 180 }}>
          <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: 2, color: C.muted, textTransform: "uppercase", marginBottom: 12 }}>Professor</div>
          <input type="password" placeholder="Senha" value={passInput}
            onChange={e => { setPassInput(e.target.value); setPassErr(false); }}
            onKeyDown={e => { if (e.key === "Enter") { if (passInput === PROFESSOR_PASSWORD) onProfessor(); else setPassErr(true); } }}
            style={{ width: "100%", padding: "12px 14px", backgroundColor: "#0D0D0D", border: `1px solid ${passErr ? C.red : C.border}`, borderRadius: 10, color: C.text, fontSize: 14, marginBottom: passErr ? 4 : 10 }} />
          {passErr && <div style={{ color: C.red, fontSize: 11, marginBottom: 8 }}>Senha incorreta</div>}
          <button onClick={() => { if (passInput === PROFESSOR_PASSWORD) onProfessor(); else setPassErr(true); }} style={{ width: "100%", padding: "13px 0", backgroundColor: "transparent", border: `1.5px solid ${C.gold}`, borderRadius: 10, fontWeight: 800, fontSize: 15, color: C.gold, cursor: "pointer" }}>Painel →</button>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// ROOT APP
// ─────────────────────────────────────────────
export default function MacroArena() {
  const [mode, setMode] = useState(null);
  const [playerName, setPlayerName] = useState("");
  const [gameState, setGameState] = useState(null);
  const [prices, setPrices] = useState({ pib: INITIAL_PRICE, emprego: INITIAL_PRICE, inflacao: INITIAL_PRICE });
  const [priceHistory, setPriceHistory] = useState({ pib: [INITIAL_PRICE], emprego: [INITIAL_PRICE], inflacao: [INITIAL_PRICE] });
  const [player, setPlayer] = useState(null);
  const [players, setPlayers] = useState({});

  useEffect(() => {
    if (mode !== "student" || !playerName) return;
    (async () => {
      const existing = await sGet(`game:player:${playerName}`);
      if (!existing) {
        const p = { cash: INITIAL_CASH, positions: { pib: 0, emprego: 0, inflacao: 0 } };
        await sSet(`game:player:${playerName}`, p); setPlayer(p);
      } else setPlayer(existing);
    })();
  }, [mode, playerName]);

  useEffect(() => {
    if (!mode) return;

    // Busca inicial
    const fetchAll = async () => {
      const state = await sGet("game:state");
      if (state) { setGameState(state); if (state.prices) setPrices(state.prices); if (state.priceHistory) setPriceHistory(state.priceHistory); }
      if (mode === "professor") {
        const keys = await sList("game:player:");
        const all = {};
        for (const k of keys) { const n = k.replace("game:player:", ""); const p = await sGet(k); if (p) all[n] = p; }
        setPlayers(all);
      } else if (playerName) {
        const p = await sGet(`game:player:${playerName}`); if (p) setPlayer(p);
      }
    };
    fetchAll();

    // Realtime via Broadcast — funciona sem configuração DDL (REPLICA IDENTITY etc.)
    const channel = supabase
      .channel("game_bus")
      .on("broadcast", { event: "kv_change" }, async ({ payload }) => {
        const key = payload?.key;
        if (key === "game:state") {
          const state = await sGet("game:state");
          if (state) { setGameState(state); if (state.prices) setPrices(state.prices); if (state.priceHistory) setPriceHistory(state.priceHistory); }
        } else if (key?.startsWith("game:player:")) {
          const name = key.replace("game:player:", "");
          if (mode === "professor") {
            const p = await sGet(key);
            if (p) setPlayers(prev => ({ ...prev, [name]: p }));
          } else if (name === playerName) {
            const p = await sGet(key);
            if (p) setPlayer(p);
          }
        }
      })
      .subscribe();

    return () => supabase.removeChannel(channel);
  }, [mode, playerName]);

  const handleTrade = useCallback(async (assetId, side, qty, price) => {
    if (!player || !playerName) return;
    const buy = side === "buy";
    const cost = qty * price;
    if (buy && cost > player.cash) return;
    if (!buy && qty > (player.positions[assetId] || 0)) return;
    const np = newPrice(price, qty, buy);
    const updated = {
      ...player,
      cash: buy ? player.cash - cost : player.cash + qty * price,
      positions: { ...player.positions, [assetId]: (player.positions[assetId] || 0) + (buy ? qty : -qty) },
    };
    setPlayer(updated);
    await sSet(`game:player:${playerName}`, updated);
    const state = await sGet("game:state");
    if (state) {
      const newPrices = { ...state.prices, [assetId]: np };
      const newHist = { ...state.priceHistory, [assetId]: [...(state.priceHistory[assetId] || [INITIAL_PRICE]), np] };
      await sSet("game:state", { ...state, prices: newPrices, priceHistory: newHist });
    }
  }, [player, playerName]);

  const handleControl = useCallback(async (action) => {
    const state = await sGet("game:state") || {};
    switch (action) {
      case "startGame": {
        const ns = { gameStarted: true, round: 1, phase: "lobby", prices: { pib: INITIAL_PRICE, emprego: INITIAL_PRICE, inflacao: INITIAL_PRICE }, priceHistory: { pib: [INITIAL_PRICE], emprego: [INITIAL_PRICE], inflacao: [INITIAL_PRICE] }, timerStart: null };
        await sSet("game:state", ns); setGameState(ns); break;
      }
      case "showScenario": {
        const ns = { ...state, phase: "reading" };
        await sSet("game:state", ns); setGameState(ns); break;
      }
      case "openMarket": {
        const ns = { ...state, phase: "scenario", timerStart: Date.now() };
        await sSet("game:state", ns); setGameState(ns); break;
      }
      case "closeMarket": {
        const sc = SCENARIOS[(state.round || 1) - 1];
        const np = { ...state.prices };
        const nh = { ...state.priceHistory };
        ASSETS.forEach(a => {
          const impact = randomizeImpact(sc.impacts[a.id]);
          np[a.id] = (state.prices?.[a.id] || INITIAL_PRICE) * (1 + impact);
          nh[a.id] = [...(state.priceHistory?.[a.id] || [INITIAL_PRICE]), np[a.id]];
        });
        const ns = { ...state, phase: "closed", prices: np, priceHistory: nh };
        await sSet("game:state", ns); setGameState(ns); setPrices(np); setPriceHistory(nh); break;
      }
      case "nextRound": {
        const ns = { ...state, round: (state.round || 1) + 1, phase: "lobby" };
        await sSet("game:state", ns); setGameState(ns); break;
      }
      case "reset": {
        const ns = { gameStarted: false, round: 1, phase: null, prices: { pib: INITIAL_PRICE, emprego: INITIAL_PRICE, inflacao: INITIAL_PRICE }, priceHistory: { pib: [INITIAL_PRICE], emprego: [INITIAL_PRICE], inflacao: [INITIAL_PRICE] } };
        await sSet("game:state", ns); setGameState(ns); setPlayers({});
        setPrices({ pib: INITIAL_PRICE, emprego: INITIAL_PRICE, inflacao: INITIAL_PRICE });
        setPriceHistory({ pib: [INITIAL_PRICE], emprego: [INITIAL_PRICE], inflacao: [INITIAL_PRICE] });
        break;
      }
    }
  }, []);

  if (!mode) return <EntryScreen onStudent={n => { setPlayerName(n); setMode("student"); }} onProfessor={() => setMode("professor")} />;
  if (mode === "professor") return <ProfessorView gameState={gameState} prices={prices} priceHistory={priceHistory} players={players} onControl={handleControl} />;
  return <StudentView name={playerName} gameState={gameState} prices={prices} priceHistory={priceHistory} player={player} onTrade={handleTrade} />;
}
