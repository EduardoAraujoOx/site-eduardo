import { useState, useEffect, useRef } from "react";

// ─── SEQUÊNCIA PREDETERMINADA ─────────────────────────────────────────────────
// G1:pobre G2:rico G3:pobre G4:pobre G5:classe_media
// Rawls(5+8+5+5+7=30) · Igualit(25) · Utilit(20) — antes dos modificadores
const SEQUENCE = ['pobre','rico','pobre','pobre','classe_media'];
const TOTAL_ROUNDS = 5;
const PROFESSOR_PASSWORD = "123123";
const RESULTS_KEY = "vi_resultados";
// Modificador de circunstância por rodada: -5, 0 ou +5
const MODIFIER_OPTIONS = [-5, 0, 5];
const MODIFIER_LABELS = {
  '-5': { emoji: '🌧️', titulo: 'Circunstância adversa', descricao: 'Um imprevisto pesou nesta geração: doença, greve de ônibus ou problema no transporte consumiu energia e recursos antes que você pudesse aproveitá-los.' },
  '0':  { emoji: '☁️', titulo: 'Semana comum', descricao: 'Os acasos da vida se equilibraram. Nada extraordinário aconteceu — nem problema grave, nem sorte inesperada.' },
  '5':  { emoji: '🌤️', titulo: 'Circunstância favorável', descricao: 'Uma oportunidade chegou na hora certa: apoio de rede de contatos, bolsa de estudos aprovada ou renda extra inesperada abriu margem que o esforço sozinho não criaria.' }
};

// ─── REGRAS DO JOGO ───────────────────────────────────────────────────────────
const RULES = {
  utilitarista:{
    name:"Utilitarista", emoji:"⚖️", philosopher:"Jeremy Bentham",
    tagline:"Maximize o total da sociedade",
    plain:"Some os pontos de prosperidade de todos. Se a soma crescer, a sociedade melhorou — não importa como está distribuída entre as pessoas.",
    analogy:"Como um time que mede sucesso pelo placar total, não por quem marcou os gols. O bolo maior importa mais do que as fatias.",
    tradeoff:"O risco é real: se você nascer na faixa baixa (60% de chance), receberá apenas 1 ponto — o mínimo para sobreviver.",
    color:"#F59E0B", glow:"rgba(245,158,11,0.4)", bg:"rgba(245,158,11,0.09)", border:"rgba(245,158,11,0.25)",
    utils:{ rico:12, classe_media:5, pobre:1 }, expected:3.6,
    why:{ rico:"A sociedade investe onde a prosperidade é maior. Quem nasceu com mais recursos recebe mais oportunidades de multiplicar.", classe_media:"Acesso a serviços razoáveis. A lógica é que o crescimento no topo eventualmente chegue ao meio.", pobre:"Acesso mínimo ao padrão de vida. A prosperidade se concentra em quem já tem mais — o total cresce, mas você fica para trás." }
  },
  rawlsiana:{
    name:"Rawlsiana", emoji:"🛡️", philosopher:"John Rawls",
    tagline:"Proteja quem está em pior situação",
    plain:"A prosperidade social é medida pela prosperidade de quem está pior. Só vale melhorar a vida dos mais ricos se isso também melhorar os mais vulneráveis.",
    analogy:"Como uma expedição de montanha: ninguém chega ao topo se o elo mais fraco não consegue subir. Fortalecer os mais frágeis é a prioridade.",
    tradeoff:"O 'custo' é que quem nasceu na faixa alta recebe menos do que numa sociedade utilitarista. Mas ninguém fica abaixo de 5.",
    color:"#10B981", glow:"rgba(16,185,129,0.4)", bg:"rgba(16,185,129,0.09)", border:"rgba(16,185,129,0.25)",
    utils:{ rico:8, classe_media:7, pobre:5 }, expected:5.9,
    why:{ rico:"Ainda acima da média — parte da prosperidade é redistribuída para garantir piso digno a todos.", classe_media:"Levemente melhor que em outras sociedades. A redistribuição toca positivamente a classe intermediária.", pobre:"Muito acima do que receberia na sociedade utilitarista. A redistribuição garantiu acesso real a saúde, educação e oportunidades." }
  },
  igualitaria:{
    name:"Igualitária", emoji:"🟰", philosopher:"Igualitarismo estrito",
    tagline:"Todos devem ter exatamente o mesmo",
    plain:"Todos recebem o mesmo padrão de vida. Qualquer desigualdade é injusta — mesmo que o total da sociedade seja menor.",
    analogy:"Cada fatia de pizza deve ser idêntica para todos à mesa. Não importa se o bolo poderia ter sido maior.",
    tradeoff:"A igualdade absoluta pode travar o crescimento. Se ninguém pode ganhar mais por esforço ou talento, os incentivos para produzir mais diminuem.",
    color:"#818CF8", glow:"rgba(129,140,248,0.4)", bg:"rgba(129,140,248,0.09)", border:"rgba(129,140,248,0.25)",
    utils:{ rico:5, classe_media:5, pobre:5 }, expected:5.0,
    why:{ rico:"Recebe o mesmo que todos — bem menos do que em outras sociedades. A igualdade redistribui do topo para os demais.", classe_media:"Exatamente igual a todos. Sem vantagem nem desvantagem de posição.", pobre:"Igual a todos. Garante acesso real, mas o piso é mais baixo do que na sociedade rawlsiana." }
  }
};

const POS = {
  rico:{ label:"Faixa Alta", color:"#FBBF24", bg:"rgba(251,191,36,0.12)", border:"rgba(251,191,36,0.32)", prob:"10%" },
  classe_media:{ label:"Faixa Média", color:"#60A5FA", bg:"rgba(96,165,250,0.12)", border:"rgba(96,165,250,0.32)", prob:"30%" },
  pobre:{ label:"Faixa Baixa", color:"#F87171", bg:"rgba(248,113,113,0.12)", border:"rgba(248,113,113,0.32)", prob:"60%" }
};

const STORIES = {
  1:{ pos:'pobre', titulo:"Você nasceu na faixa baixa de renda", local:"UPA de Carapina, Serra — 3h47 da madrugada",
    drama:"Dona Aparecida chegou à UPA às 2h com contrações a cada oito minutos. Não havia macas livres. Ela esperou duas horas sentada numa cadeira plástica laranja ao lado de um senhor com febre e uma criança chorando no colo da mãe. O parto foi feito numa sala improvisada, sem anestesia — havia fila para o bloco cirúrgico. Você chegou ao mundo às 3h47 sob uma lâmpada fluorescente oscilante, no município com o maior índice de homicídios do Espírito Santo.",
    vida:"Cresceu no Alto Carapina. A escola estadual teve três diretores diferentes nos quatro anos do ensino médio. Aos 17, começou a lavar carros no posto da rodovia. Nunca fez cursinho.",
    fim:"Aos 42 anos: trabalho informal. Três tentativas de aposentadoria negadas pelo INSS por vínculos insuficientes." },
  2:{ pos:'rico', titulo:"Você nasceu na faixa alta de renda", local:"Santa Casa de Misericórdia, ala particular — Vitória",
    drama:"Sua mãe, Dra. Patrícia, havia agendado o parto com três meses de antecedência. Suíte com TV a cabo, frigobar e sofá-cama para o marido. Obstetrícia particular, anestesia peridural sem fila. Você nasceu às 10h numa sala climatizada, com fotógrafo contratado registrando cada momento. Seu pai, dono de uma construtora com contratos pela Prefeitura de Vitória, abriu uma caderneta de poupança no mesmo dia.",
    vida:"Saint Peter Bilingual School em Jardim Camburi. Intercâmbio em Dublin aos 16. UFES Direito, turno integral. Nunca precisou trabalhar enquanto estudava.",
    fim:"Aos 30 anos: sócio-fundador de escritório próprio. Apartamento em Praia do Canto. Herança projetada em R$ 4 milhões." },
  3:{ pos:'pobre', titulo:"Você nasceu na faixa baixa de renda", local:"Flexal II, Cariacica — bairro sem UBS há 8 meses",
    drama:"Sua mãe deu à luz em casa com a ajuda da vizinha Dona Neuza, porque o ônibus para a UPA passava de hora em hora e as contrações não esperavam. O Flexal II é o bairro mais violento de Cariacica segundo o IPES-ES. A escola municipal ficou seis meses sem professor de português em 2019. Quando você completou 15 anos, seu melhor amigo foi baleado numa esquina a quatrocentos metros de casa.",
    vida:"Abandonou o ensino médio para trabalhar. Mecânico informal em oficina sem registro. Nunca contribuiu para o INSS.",
    fim:"Aos 38 anos: entregador de aplicativo. Sem carteira assinada. Sem proteção social. Sem previsão de aposentadoria." },
  4:{ pos:'pobre', titulo:"Você nasceu na faixa baixa de renda", local:"Bairro República, Vitória — embaixo da Terceira Ponte",
    drama:"Seu pai construiu parte dos pilares do Porto de Vitória nos anos 1990 — sem carteira assinada, sem EPI. Desenvolveu silicose aos 54 anos. O INSS negou o benefício: vínculo empregatício não comprovado. Você vende água mineral num isopor embaixo da Terceira Ponte desde os 40 anos. No verão capixaba, o asfalto chega a 55°C. Você ganha R$ 80 nos dias bons.",
    vida:"Construiu prédios que nunca vai morar. Ajudou a erguer a cidade que o expulsou para a periferia.",
    fim:"63 anos. R$ 412 de auxílio-doença. Divide um quarto com o filho de 26 anos, desempregado." },
  5:{ pos:'classe_media', titulo:"Você nasceu na faixa média de renda", local:"Itaparica, Vila Velha — família de servidores estaduais",
    drama:"Seu pai é analista do DETRAN-ES desde 1998, concursado. Sua mãe é professora da rede estadual. Você nasceu num hospital conveniado, quarto compartilhado, mas com atendimento adequado. A casa própria foi financiada pela Caixa em 360 parcelas — ainda faltam 18 anos. O carro tem doze anos e troca de óleo em dia. Há uma reserva de emergência de exatamente dois salários e meio.",
    vida:"Escola pública em Itaparica — razoável. UFES Engenharia Civil depois de dois anos de cursinho pago com o 13º do pai. Primeiro emprego na Vale Fertilizantes em Anchieta.",
    fim:"Estável. Mas qualquer crise de saúde, demissão ou reforma da previdência pode desfazer em meses o que levou décadas para construir." }
};

// ─── CENAS SVG ────────────────────────────────────────────────────────────────
function CenaUPA() {
  return (
    <svg viewBox="0 0 400 220" style={{width:"100%",display:"block"}} fill="none">
      <defs>
        <radialGradient id="lamp-pool-l" cx="22%" cy="0%" r="50%">
          <stop offset="0%" stopColor="#CCFF90" stopOpacity="0.10"/>
          <stop offset="100%" stopColor="#CCFF90" stopOpacity="0"/>
        </radialGradient>
        <radialGradient id="lamp-pool-r" cx="72%" cy="0%" r="45%">
          <stop offset="0%" stopColor="#CCFF90" stopOpacity="0.06"/>
          <stop offset="100%" stopColor="#CCFF90" stopOpacity="0"/>
        </radialGradient>
        <radialGradient id="birth-glow" cx="88%" cy="50%" r="35%">
          <stop offset="0%" stopColor="#FF8F00" stopOpacity="0.08"/>
          <stop offset="100%" stopColor="#FF8F00" stopOpacity="0"/>
        </radialGradient>
        <radialGradient id="clock-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#66BB6A" stopOpacity="0.2"/>
          <stop offset="100%" stopColor="#66BB6A" stopOpacity="0"/>
        </radialGradient>
      </defs>
      {/* Fundo institucional verde-escuro */}
      <rect width="400" height="220" fill="#04100A"/>
      <rect width="400" height="24" fill="#071A0E"/>
      {/* Lâmpadas fluorescentes */}
      <rect x="18" y="5" width="110" height="13" rx="3" fill="#CCFF90" opacity="0.65"/>
      <rect x="20" y="5" width="106" height="6" rx="2" fill="#E8FFB0" opacity="0.4"/>
      <rect x="260" y="5" width="85" height="13" rx="3" fill="#CCFF90" opacity="0.42"/>
      <rect x="262" y="5" width="81" height="6" rx="2" fill="#E8FFB0" opacity="0.25"/>
      {/* Pools de luz */}
      <rect width="400" height="220" fill="url(#lamp-pool-l)"/>
      <rect width="400" height="220" fill="url(#lamp-pool-r)"/>
      <rect width="400" height="220" fill="url(#birth-glow)"/>
      {/* Parede de fundo / balcão triagem */}
      <rect x="0" y="24" width="275" height="75" fill="#061009"/>
      <rect x="0" y="72" width="220" height="20" rx="0" fill="#0A1C10" stroke="#1A5220" strokeWidth="0.8"/>
      {/* Sinalizações */}
      <rect x="8" y="30" width="72" height="14" rx="2" fill="#1B5E20"/>
      <text x="44" y="40" textAnchor="middle" fill="#C8E6C9" fontSize="7.5" fontWeight="bold" fontFamily="monospace">TRIAGEM</text>
      <rect x="8" y="49" width="108" height="14" rx="2" fill="#7F1D1D"/>
      <text x="62" y="59" textAnchor="middle" fill="#FFCDD2" fontSize="7.5" fontWeight="bold" fontFamily="monospace">ESPERA: +4 HORAS</text>
      {/* Enfermeira silhueta */}
      <rect x="158" y="54" width="13" height="22" rx="4" fill="#ECEFF1" opacity="0.6"/>
      <circle cx="164" cy="49" r="8" fill="#D7CCC8" opacity="0.6"/>
      <rect x="162" y="59" width="2" height="8" fill="#EF5350" opacity="0.8"/>
      <rect x="159" y="63" width="8" height="2" fill="#EF5350" opacity="0.8"/>
      {/* RELÓGIO — elemento focal, destaque */}
      <circle cx="354" cy="52" r="30" fill="url(#clock-glow)"/>
      <circle cx="354" cy="52" r="24" fill="#030A05" stroke="#2E7D32" strokeWidth="2.5"/>
      <circle cx="354" cy="52" r="20" fill="#061009"/>
      {[0,1,2,3,4,5,6,7,8,9,10,11].map(i => {
        const a = (i*30-90)*Math.PI/180;
        const r1 = i%3===0 ? 14 : 17, r2 = 19;
        return <line key={i} x1={354+r1*Math.cos(a)} y1={52+r1*Math.sin(a)} x2={354+r2*Math.cos(a)} y2={52+r2*Math.sin(a)} stroke="#2E7D32" strokeWidth={i%3===0?1.5:0.8}/>;
      })}
      {/* Ponteiros: 3h47 */}
      <line x1="354" y1="52" x2="354" y2="38" stroke="#66BB6A" strokeWidth="2.5" strokeLinecap="round"/>
      <line x1="354" y1="52" x2="341" y2="53" stroke="#66BB6A" strokeWidth="1.8" strokeLinecap="round"/>
      <circle cx="354" cy="52" r="2.5" fill="#66BB6A"/>
      <text x="354" y="81" textAnchor="middle" fill="#66BB6A" fontSize="8.5" fontFamily="monospace" fontWeight="bold">3:47</text>
      {/* Placa UPA */}
      <rect x="310" y="28" width="42" height="18" rx="3" fill="#1B5E20" stroke="#2E7D32" strokeWidth="0.8"/>
      <text x="331" y="40" textAnchor="middle" fill="#A5D6A7" fontSize="11" fontWeight="bold" fontFamily="monospace">UPA</text>
      {/* Cortinas da sala de parto — direita */}
      <rect x="307" y="24" width="93" height="152" fill="#040C07"/>
      <path d="M307 24 C313 65 306 100 310 140 C312 158 307 165 309 176" stroke="#1B5E20" strokeWidth="9" fill="none" strokeLinecap="round"/>
      <path d="M307 24 C310 68 305 103 308 143 C310 161 306 168 308 176" stroke="#0D3A10" strokeWidth="5" fill="none" strokeLinecap="round"/>
      <path d="M400 24 C394 65 397 100 391 140 C389 158 394 165 392 176" stroke="#1B5E20" strokeWidth="9" fill="none" strokeLinecap="round"/>
      {/* Cadeiras e pessoas na sala de espera */}
      {[14,52,90,148,186,234].map((x,i) => (
        <g key={i}>
          <rect x={x} y={154} width={32} height={24} rx="3" fill={i%2===0?"#B71C1C":"#7F1D1D"} opacity="0.82"/>
          <rect x={x-2} y={164} width={36} height={6} rx="1" fill={i%2===0?"#8B0000":"#6B1717"} opacity="0.8"/>
        </g>
      ))}
      {/* Pessoa 1: cabeça nas mãos */}
      <rect x="17" y="138" width="13" height="20" rx="4" fill="#3E2723" opacity="0.9"/>
      <circle cx="23" cy="133" r="7" fill="#4E342E" opacity="0.9"/>
      <path d="M17 138 C14 146 15 154 17 154" stroke="#3E2723" strokeWidth="3" strokeLinecap="round"/>
      <path d="M31 138 C34 146 33 154 31 154" stroke="#3E2723" strokeWidth="3" strokeLinecap="round"/>
      <path d="M19 133 Q23 130 27 133" stroke="#5D4037" strokeWidth="3" strokeLinecap="round" opacity="0.8"/>
      {/* Pessoa 2: ereta, ansiosa */}
      <rect x="55" y="136" width="12" height="22" rx="4" fill="#263238" opacity="0.9"/>
      <circle cx="61" cy="131" r="7" fill="#37474F" opacity="0.9"/>
      {/* Pessoa 3: criança no colo */}
      <rect x="93" y="138" width="13" height="20" rx="4" fill="#1A237E" opacity="0.85"/>
      <circle cx="99" cy="133" r="7" fill="#283593" opacity="0.85"/>
      <circle cx="103" cy="148" r="5" fill="#4527A0" opacity="0.85"/>
      <rect x="99" y="152" width="9" height="10" rx="3" fill="#4527A0" opacity="0.7"/>
      {/* Pessoa 4: deita no chão */}
      <ellipse cx="208" cy="183" rx="34" ry="7" fill="#37474F" opacity="0.65"/>
      <circle cx="239" cy="178" r="7" fill="#455A64" opacity="0.65"/>
      {/* Pessoa 5: idosa, soro */}
      <rect x="152" y="136" width="12" height="22" rx="4" fill="#3E2723" opacity="0.9"/>
      <circle cx="158" cy="131" r="7" fill="#4E342E" opacity="0.9"/>
      <line x1="163" y1="128" x2="172" y2="112" stroke="#78909C" strokeWidth="1.2" opacity="0.8"/>
      <rect x="169" y="104" width="6" height="14" rx="2" fill="#B0BEC5" opacity="0.55"/>
      {/* Chão — linóleo */}
      {Array.from({length:8},(_,c) => (
        <rect key={c} x={c*50} y={186} width={49} height={34} fill={c%2===0?"#040D07":"#060E09"} stroke="#030807" strokeWidth="0.5"/>
      ))}
      <rect width="400" height="220" fill="url(#birth-glow)"/>
      <text x="200" y="214" textAnchor="middle" fill="#66BB6A" fontSize="9" opacity="0.72" fontStyle="italic">Serra, ES — UPA de Carapina — 3h47</text>
    </svg>
  );
}

function CenaPraiaCanto() {
  return (
    <svg viewBox="0 0 400 220" style={{width:"100%",display:"block"}} fill="none">
      <defs>
        <linearGradient id="bay-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#0A1E38"/>
          <stop offset="55%" stopColor="#162840"/>
          <stop offset="85%" stopColor="#7C2D12" stopOpacity="0.7"/>
          <stop offset="100%" stopColor="#92400E" stopOpacity="0.5"/>
        </linearGradient>
        <linearGradient id="bay-water" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#0C2A45"/>
          <stop offset="100%" stopColor="#091828"/>
        </linearGradient>
        <radialGradient id="sun-glow-bay" cx="82%" cy="35%" r="30%">
          <stop offset="0%" stopColor="#FCD34D" stopOpacity="0.45"/>
          <stop offset="100%" stopColor="#FCD34D" stopOpacity="0"/>
        </radialGradient>
        <radialGradient id="interior-light" cx="50%" cy="100%" r="60%">
          <stop offset="0%" stopColor="#FEF3C7" stopOpacity="0.07"/>
          <stop offset="100%" stopColor="#FEF3C7" stopOpacity="0"/>
        </radialGradient>
      </defs>
      {/* Interior escuro do quarto */}
      <rect width="400" height="220" fill="#071422"/>
      {/* JANELÃO — elemento principal */}
      <rect x="28" y="12" width="344" height="162" rx="4" fill="url(#bay-sky)"/>
      {/* Glow do sol */}
      <rect x="28" y="12" width="344" height="162" fill="url(#sun-glow-bay)"/>
      {/* Sol ao entardecer */}
      <circle cx="326" cy="60" r="18" fill="#FCD34D" opacity="0.7"/>
      <circle cx="326" cy="60" r="26" fill="#FCD34D" opacity="0.18"/>
      <circle cx="326" cy="60" r="38" fill="#F59E0B" opacity="0.07"/>
      {/* Linha do horizonte */}
      <rect x="30" y="108" width="340" height="64" fill="url(#bay-water)"/>
      {/* Ondas suaves */}
      <path d="M30 114 Q130 109 200 116 Q270 122 370 113" fill="none" stroke="#1E4976" strokeWidth="1.2" opacity="0.8"/>
      <path d="M30 126 Q120 121 200 128 Q278 134 370 125" fill="none" stroke="#1E4976" strokeWidth="0.8" opacity="0.6"/>
      <path d="M30 140 Q140 136 200 142 Q260 148 370 138" fill="none" stroke="#1E4976" strokeWidth="0.6" opacity="0.4"/>
      {/* Reflexo do sol na água */}
      <ellipse cx="326" cy="145" rx="35" ry="7" fill="#F59E0B" opacity="0.08"/>
      {/* TERCEIRA PONTE — silhueta reconhecível */}
      {[80,110,140,170,200,230,260,290,320].map((x,i) => (
        <rect key={i} x={x} y={128} width={5} height={18} fill="#0A1828" stroke="#1A3050" strokeWidth="0.4"/>
      ))}
      <rect x="72" y="125" width="265" height="6" fill="#0A1828" stroke="#1A3050" strokeWidth="0.8"/>
      {/* Cabos da ponte */}
      {[114,185,255].map((x,i) => (
        <g key={i}>
          <line x1={x} y1={102} x2={x-28} y2={128} stroke="#162A44" strokeWidth="0.8" opacity="0.7"/>
          <line x1={x} y1={102} x2={x+28} y2={128} stroke="#162A44" strokeWidth="0.8" opacity="0.7"/>
          <circle cx={x} cy={100} r={3} fill="#162A44" opacity="0.7"/>
        </g>
      ))}
      {/* Skyline de Vitória */}
      {[[38,65,22,55],[64,55,18,65],[86,48,28,72],[118,58,24,62],[146,44,32,76],[182,54,26,66],[212,47,34,73],[250,56,22,64],[276,50,26,70],[306,62,20,58]].map(([x,y,w,h],i) => (
        <g key={i}>
          <rect x={x} y={y} width={w} height={h} fill="#081526" stroke="#0F1E34" strokeWidth="0.4"/>
          {Array.from({length:2},(_,r) => Array.from({length:2},(_,c) => (
            <rect key={`${r}-${c}`} x={x+3+c*9} y={y+4+r*14} width={5} height={7} rx="0.5"
              fill={(r+c+i)%3===0 ? "#DBEAFE" : "#0C1A2E"} opacity={0.2+((r*c+i)%3)*0.15}/>
          )))}
        </g>
      ))}
      {/* Moldura da janela */}
      <rect x="24" y="8" width="8" height="168" fill="#0A1628" stroke="#1A3050" strokeWidth="1"/>
      <rect x="368" y="8" width="8" height="168" fill="#0A1628" stroke="#1A3050" strokeWidth="1"/>
      <rect x="24" y="8" width="352" height="8" fill="#0A1628" stroke="#1A3050" strokeWidth="1"/>
      <rect x="24" y="172" width="352" height="8" fill="#0A1628" stroke="#1A3050" strokeWidth="1"/>
      {/* Interior — piso reflexivo */}
      <rect x="0" y="180" width="400" height="40" fill="#070E1A"/>
      <rect x="28" y="180" width="344" height="40" fill="#0A1428" opacity="0.6"/>
      <rect width="400" height="220" fill="url(#interior-light)"/>
      {/* Orquídea no parapeito */}
      <rect x="238" y="172" width="4" height="14" fill="#065F46"/>
      <ellipse cx="234" cy="170" rx="7" ry="5" fill="#9D174D" opacity="0.82" transform="rotate(-15,234,170)"/>
      <ellipse cx="246" cy="167" rx="6" ry="4.5" fill="#BE185D" opacity="0.75" transform="rotate(10,246,167)"/>
      <ellipse cx="241" cy="173" rx="5" ry="3.5" fill="#F9A8D4" opacity="0.65"/>
      {/* Taça de champanhe */}
      <path d="M186 178 Q186 165 190 160 Q194 155 198 160 Q202 165 202 178" fill="#1E3A5F" stroke="#60A5FA" strokeWidth="0.8"/>
      <ellipse cx="194" cy="178" rx="10" ry="3.5" fill="#1E3A5F" stroke="#60A5FA" strokeWidth="0.8"/>
      <path d="M186 171 Q194 175 202 171" fill="#7C3AED" opacity="0.35"/>
      <text x="200" y="213" textAnchor="middle" fill="#93C5FD" fontSize="9" opacity="0.78" fontStyle="italic">Praia do Canto, Vitória — vista da suíte particular</text>
    </svg>
  );
}

function CenaFlexal() {
  return (
    <svg viewBox="0 0 400 220" style={{width:"100%",display:"block"}} fill="none">
      <defs>
        <radialGradient id="lamp-flexal" cx="65%" cy="30%" r="40%">
          <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.12"/>
          <stop offset="100%" stopColor="#F59E0B" stopOpacity="0"/>
        </radialGradient>
        <radialGradient id="phone-blue" cx="20%" cy="72%" r="12%">
          <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.3"/>
          <stop offset="100%" stopColor="#3B82F6" stopOpacity="0"/>
        </radialGradient>
      </defs>
      {/* Noite — fundo quase negro */}
      <rect width="400" height="220" fill="#030508"/>
      <rect width="400" height="68" fill="#050710"/>
      <rect width="400" height="220" fill="url(#lamp-flexal)"/>
      <rect width="400" height="220" fill="url(#phone-blue)"/>
      {/* Lua minguante */}
      <circle cx="52" cy="30" r="13" fill="#FEF3C7" opacity="0.65"/>
      <circle cx="58" cy="25" r="11" fill="#050710"/>
      {/* PAREDES DO BECO — tijolos aparentes */}
      {Array.from({length:13},(_,r) => [0,1].map(c => (
        <rect key={`L${r}-${c}`} x={c*28+(r%2)*14} y={r*17} width={26} height={15} rx="0.4"
          fill={r%3===0?"#1A1006":"#120C04"} stroke="#080503" strokeWidth="0.3"/>
      )))}
      {Array.from({length:13},(_,r) => [0,1].map(c => (
        <rect key={`R${r}-${c}`} x={345+c*28+(r%2)*14} y={r*17} width={26} height={15} rx="0.4"
          fill={r%3===0?"#181006":"#100B04"} stroke="#070503" strokeWidth="0.3"/>
      )))}
      {/* Fios elétricos e varal */}
      <path d="M56 35 Q140 29 200 38 Q265 45 344 34" stroke="#1E293B" strokeWidth="1.2" opacity="0.9"/>
      <path d="M56 45 Q135 52 200 44 Q262 37 344 48" stroke="#1E293B" strokeWidth="0.8" opacity="0.6"/>
      {/* Roupas no varal */}
      {[[92,38,20,14],[122,34,16,15],[150,40,22,13],[182,36,14,11]].map(([x,y,w,h],i) => (
        <g key={i}>
          <rect x={x} y={y+5} width={w} height={h} rx="2" fill="#1E293B" opacity={0.55+i*0.07}/>
          <line x1={x} y1={y} x2={x} y2={y+6} stroke="#334155" strokeWidth="0.8"/>
          <line x1={x+w} y1={y} x2={x+w} y2={y+6} stroke="#334155" strokeWidth="0.8"/>
        </g>
      ))}
      {/* ESCOLA — prédio ao fundo */}
      <rect x="98" y="68" width="204" height="120" fill="#050709" stroke="#0D1016" strokeWidth="0.8"/>
      <rect x="106" y="74" width="188" height="14" rx="1" fill="#090C16"/>
      <text x="200" y="84" textAnchor="middle" fill="#1E293B" fontSize="8.5" fontFamily="monospace">E.E. PROF. SEVERINO LIMA</text>
      {/* Janelas escuras da escola */}
      {[[110,92,38,30],[156,92,38,30],[206,92,38,30],[252,92,38,30]].map(([x,y,w,h]) => (
        <rect key={x} x={x} y={y} width={w} height={h} fill="#030507" stroke="#0D1016" strokeWidth="0.5"/>
      ))}
      {/* PORTÃO COM CORRENTE */}
      <rect x="138" y="147" width="124" height="42" fill="#040609"/>
      {Array.from({length:14},(_,i) => (
        <rect key={i} x={138+i*8.9} y={147} width={2.5} height={42} fill="#0D1016" opacity="0.95"/>
      ))}
      {/* Corrente — elemento focal */}
      <path d="M178 153 Q188 161 183 170 Q178 177 184 183 Q192 189 202 184" stroke="#92400E" strokeWidth="3" fill="none" strokeLinecap="round"/>
      <path d="M202 184 Q210 180 215 186 Q220 192 214 197" stroke="#78350F" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
      <circle cx="214" cy="198" r="6" fill="#92400E" stroke="#78350F" strokeWidth="1.2"/>
      {/* Placa obras */}
      <rect x="106" y="143" width="78" height="12" rx="2" fill="#7F1D1D"/>
      <text x="145" y="152" textAnchor="middle" fill="#FCA5A5" fontSize="7" fontWeight="bold">OBRAS — PRAZO IND.</text>
      {/* TRÊS JOVENS — silhuetas */}
      {[62,78,96].map((x,i) => (
        <g key={i}>
          <rect x={x} y={152+i} width={12} height={36-i*2} rx="4" fill="#0E0C0A" opacity="0.95"/>
          <circle cx={x+6} cy={148+i} r={7+i*0.5} fill="#0E0C0A" opacity="0.95"/>
        </g>
      ))}
      {/* Glow de celular */}
      <rect x="65" y="156" width="12" height="8" rx="1" fill="#1E3A5F" opacity="0.9"/>
      <rect x="66" y="157" width="10" height="6" rx="0.5" fill="#3B82F6" opacity="0.55"/>
      {/* Grafite CV */}
      <text x="298" y="138" fill="#7C3AED" fontSize="22" opacity="0.52" fontWeight="bold" fontFamily="monospace">CV</text>
      <text x="298" y="153" fill="#374151" fontSize="8" opacity="0.45" fontFamily="monospace">zona quente</text>
      {/* Rachadura no chão */}
      <path d="M56 195 Q140 192 200 196 Q265 200 344 194" fill="none" stroke="#0A0C14" strokeWidth="0.8"/>
      <text x="200" y="214" textAnchor="middle" fill="#F87171" fontSize="9" opacity="0.72" fontStyle="italic">Flexal II, Cariacica — madrugada</text>
    </svg>
  );
}

function CenaTerceiraPonte() {
  return (
    <svg viewBox="0 0 400 220" style={{width:"100%",display:"block"}} fill="none">
      <defs>
        <radialGradient id="sun-extreme" cx="50%" cy="0%" r="55%">
          <stop offset="0%" stopColor="#FFFDE7" stopOpacity="0.3"/>
          <stop offset="50%" stopColor="#FFF9C4" stopOpacity="0.1"/>
          <stop offset="100%" stopColor="#FFF9C4" stopOpacity="0"/>
        </radialGradient>
        <linearGradient id="heat-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#0A1525"/>
          <stop offset="100%" stopColor="#152035"/>
        </linearGradient>
        <linearGradient id="bay-ponte" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#091828"/>
          <stop offset="100%" stopColor="#060E1A"/>
        </linearGradient>
      </defs>
      {/* Fundo */}
      <rect width="400" height="220" fill="url(#heat-sky)"/>
      <rect width="400" height="220" fill="url(#sun-extreme)"/>
      {/* SOL IMPLACÁVEL */}
      <circle cx="200" cy="14" r="20" fill="#FFFDE7" opacity="0.88"/>
      <circle cx="200" cy="14" r="30" fill="#FEF9E7" opacity="0.2"/>
      <circle cx="200" cy="14" r="44" fill="#FEF3C7" opacity="0.08"/>
      <circle cx="200" cy="14" r="60" fill="#FEF3C7" opacity="0.03"/>
      {/* Raios do sol */}
      {Array.from({length:12},(_,i) => {
        const a = i*30*Math.PI/180;
        return <line key={i} x1={200+26*Math.cos(a)} y1={14+26*Math.sin(a)} x2={200+60*Math.cos(a)} y2={14+60*Math.sin(a)} stroke="#FEF3C7" strokeWidth="1" opacity="0.18"/>;
      })}
      {/* TEMPERATURA — destaque */}
      <text x="20" y="44" fill="#F59E0B" fontSize="24" fontWeight="bold" fontFamily="monospace" opacity="0.95">39°C</text>
      {/* PILARES DE CONCRETO */}
      <rect x="0" y="16" width="58" height="204" fill="#0E1826" stroke="#1A2E44" strokeWidth="1.5"/>
      <rect x="342" y="16" width="58" height="204" fill="#0E1826" stroke="#1A2E44" strokeWidth="1.5"/>
      {/* Textura concreto */}
      {Array.from({length:10},(_,i) => <>
        <line key={`cl${i}`} x1="0" y1={24+i*20} x2="58" y2={26+i*20} stroke="#162030" strokeWidth="0.6"/>
        <line key={`cr${i}`} x1="342" y1={24+i*20} x2="400" y2={26+i*20} stroke="#162030" strokeWidth="0.6"/>
      </>)}
      {/* TABULEIRO DA PONTE — overhead */}
      <rect x="0" y="62" width="400" height="26" fill="#0E1826" stroke="#1A2E44" strokeWidth="1.5"/>
      <rect x="0" y="62" width="400" height="7" fill="#162030"/>
      {/* Cabos da ponte */}
      {[95,145,200,255,305].map((x,i) => (
        <g key={i}>
          <line x1={x} y1={28} x2={x-30} y2={62} stroke="#1E2E44" strokeWidth="1.2" opacity="0.8"/>
          <line x1={x} y1={28} x2={x+30} y2={62} stroke="#1E2E44" strokeWidth="1.2" opacity="0.8"/>
          <circle cx={x} cy={26} r={3.5} fill="#1A2838"/>
        </g>
      ))}
      {/* ÁGUA DA BAÍA — abaixo da ponte */}
      <rect x="58" y="88" width="284" height="132" fill="url(#bay-ponte)"/>
      <path d="M58 100 Q150 95 200 103 Q252 110 342 100" fill="none" stroke="#1E4070" strokeWidth="1.2" opacity="0.7"/>
      <path d="M58 115 Q145 111 200 118 Q255 124 342 114" fill="none" stroke="#1E4070" strokeWidth="0.8" opacity="0.5"/>
      <path d="M58 133 Q148 129 200 136 Q252 142 342 132" fill="none" stroke="#1E4070" strokeWidth="0.6" opacity="0.4"/>
      {/* Embarcações ao fundo */}
      <rect x="88" y="145" width="26" height="8" rx="2" fill="#0E2038"/>
      <path d="M101 145 L101 135 L113 145Z" fill="#0E2038"/>
      <rect x="258" y="152" width="22" height="7" rx="2" fill="#0E2038"/>
      {/* Reflexo do sol na água */}
      <ellipse cx="200" cy="162" rx="50" ry="7" fill="#FEF3C7" opacity="0.05"/>
      {/* Sombra da ponte no nível do olho */}
      <rect x="58" y="88" width="284" height="18" fill="#060E14" opacity="0.55"/>
      {/* VENDEDOR — figura humana */}
      <rect x="177" y="162" width="16" height="38" rx="5" fill="#374151"/>
      <circle cx="185" cy="157" r="10" fill="#5D4037"/>
      {/* Boné */}
      <ellipse cx="185" cy="151" rx="12" ry="5" fill="#1F2937"/>
      <rect x="174" y="151" width="22" height="4" rx="1" fill="#111827"/>
      {/* Braços estendidos */}
      <rect x="158" y="164" width="21" height="8" rx="3" fill="#374151"/>
      <rect x="193" y="164" width="21" height="8" rx="3" fill="#374151"/>
      {/* ISOPOR — elemento visual */}
      <rect x="146" y="172" width="46" height="24" rx="3" fill="#E8EDF2" stroke="#CBD5E1" strokeWidth="1"/>
      <rect x="148" y="174" width="42" height="5" rx="1" fill="#F1F5F9"/>
      {/* Garrafinhas */}
      {[152,162,172,182].map(x => (
        <g key={x}>
          <rect x={x} y={178} width={8} height={14} rx="2" fill="#BFDBFE" opacity="0.85"/>
          <rect x={x+1} y={175} width={6} height={4} rx="1" fill="#93C5FD" opacity="0.7"/>
        </g>
      ))}
      {/* Placa "ÁGUA R$ 2,00" */}
      <rect x="194" y="185" width="52" height="12" rx="2" fill="#1E293B"/>
      <text x="220" y="194" textAnchor="middle" fill="#93C5FD" fontSize="8" fontWeight="bold" fontFamily="monospace">ÁGUA R$ 2,00</text>
      {/* Linhas de calor no asfalto */}
      {[196,199,202,205,208].map((y,i) => (
        <path key={i} d={`M58 ${y} Q200 ${y-1+i%2} 342 ${y}`} fill="none" stroke="#FFFDE7" strokeWidth="0.4" opacity="0.04+i*0.01"/>
      ))}
      <text x="200" y="214" textAnchor="middle" fill="#F87171" fontSize="9" opacity="0.72" fontStyle="italic">Terceira Ponte, Vitória — 39°C, 14h</text>
    </svg>
  );
}

function CenaItaparica() {
  return (
    <svg viewBox="0 0 400 220" style={{width:"100%",display:"block"}} fill="none">
      <defs>
        <radialGradient id="lamp-sala" cx="50%" cy="12%" r="55%">
          <stop offset="0%" stopColor="#FEF3C7" stopOpacity="0.09"/>
          <stop offset="100%" stopColor="#FEF3C7" stopOpacity="0"/>
        </radialGradient>
        <radialGradient id="tv-glow" cx="82%" cy="42%" r="18%">
          <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.14"/>
          <stop offset="100%" stopColor="#3B82F6" stopOpacity="0"/>
        </radialGradient>
      </defs>
      {/* Sala de jantar modesta */}
      <rect width="400" height="220" fill="#050C14"/>
      <rect width="400" height="175" fill="#08131F"/>
      <rect width="400" height="3" y="172" fill="#0C1A2C"/>
      <rect width="400" height="48" y="172" fill="#060D15"/>
      <rect width="400" height="220" fill="url(#lamp-sala)"/>
      <rect width="400" height="220" fill="url(#tv-glow)"/>
      {/* Lustre de teto */}
      <line x1="200" y1="0" x2="200" y2="14" stroke="#334155" strokeWidth="1.2"/>
      <rect x="188" y="14" width="24" height="10" rx="3" fill="#1E293B"/>
      <ellipse cx="200" cy="26" rx="14" ry="5" fill="#FEF3C7" opacity="0.5"/>
      {/* MESA DE JANTAR */}
      <ellipse cx="200" cy="150" rx="108" ry="22" fill="#1A2030" stroke="#253040" strokeWidth="1.5"/>
      <ellipse cx="200" cy="146" rx="108" ry="20" fill="#1E2A3A" stroke="#2A3848" strokeWidth="1"/>
      <rect x="106" y="164" width="9" height="28" rx="2" fill="#1A2030"/>
      <rect x="285" y="164" width="9" height="28" rx="2" fill="#1A2030"/>
      {/* Pratos na mesa */}
      {[148,200,256].map(x => (
        <g key={x}>
          <ellipse cx={x} cy={148} rx={20} ry={8} fill="#243040"/>
          <ellipse cx={x} cy={147} rx={15} ry={6} fill="#1A2A38"/>
          <ellipse cx={x} cy={147} rx={9} ry={4} fill="#2D4A30" opacity="0.8"/>
        </g>
      ))}
      {/* FAMÍLIA — três silhuetas */}
      <rect x="118" y="118" width="16" height="35" rx="5" fill="#1E3A5F"/>
      <circle cx="126" cy="112" r="10" fill="#8B6452"/>
      <rect x="182" y="116" width="18" height="36" rx="5" fill="#374151"/>
      <circle cx="191" cy="110" r="11" fill="#7C5544"/>
      <rect x="245" y="122" width="14" height="30" rx="5" fill="#1E3A5F"/>
      <circle cx="252" cy="117" r="9" fill="#A1887F"/>
      {/* TV NA PAREDE */}
      <rect x="296" y="54" width="84" height="54" rx="4" fill="#090F18" stroke="#1E3A5F" strokeWidth="1.5"/>
      <rect x="299" y="57" width="78" height="46" fill="#0B1622"/>
      {/* Tela da TV */}
      <rect x="300" y="58" width="76" height="11" fill="#1E3A5F"/>
      <text x="338" y="66.5" textAnchor="middle" fill="#93C5FD" fontSize="5.5" fontWeight="bold" fontFamily="monospace">JORNAL DA GAZETA</text>
      <text x="338" y="79" textAnchor="middle" fill="#94A3B8" fontSize="5" fontFamily="monospace">PIB ES: +1,2% tri.</text>
      <text x="338" y="88" textAnchor="middle" fill="#F87171" fontSize="5" fontFamily="monospace">Desemprego: 14,3%</text>
      <text x="338" y="97" textAnchor="middle" fill="#94A3B8" fontSize="5" fontFamily="monospace">Reajuste serv.: 3%</text>
      {/* FATURA — elemento focal */}
      <rect x="64" y="126" width="52" height="36" rx="3" fill="#0F1E30" stroke="#1E293B" strokeWidth="0.8"/>
      <rect x="66" y="128" width="48" height="8" rx="1" fill="#DC2626" opacity="0.75"/>
      <text x="90" y="134.5" textAnchor="middle" fill="#FCA5A5" fontSize="6" fontWeight="bold" fontFamily="monospace">FATURA CEF</text>
      <text x="90" y="145" textAnchor="middle" fill="#94A3B8" fontSize="5.5" fontFamily="monospace">360x — 18 anos</text>
      <text x="90" y="155" textAnchor="middle" fill="#F59E0B" fontSize="7" fontWeight="bold" fontFamily="monospace">R$ 890/mês</text>
      {/* CALENDÁRIO */}
      <rect x="12" y="56" width="54" height="60" rx="3" fill="#0F1E30" stroke="#1E293B" strokeWidth="0.8"/>
      <rect x="12" y="56" width="54" height="12" rx="2" fill="#1E3A5F"/>
      <text x="39" y="65" textAnchor="middle" fill="#93C5FD" fontSize="6.5" fontWeight="bold" fontFamily="monospace">NOVEMBRO</text>
      <circle cx="31" cy="94" r="7" fill="#7F1D1D"/>
      <text x="31" y="97" textAnchor="middle" fill="#FCA5A5" fontSize="7" fontWeight="bold">5</text>
      <text x="39" y="108" textAnchor="middle" fill="#475569" fontSize="5" fontFamily="monospace">PAGAR CAIXA</text>
      {/* Janela pequena */}
      <rect x="318" y="114" width="64" height="52" rx="2" fill="#060D16" stroke="#1E293B" strokeWidth="1"/>
      <rect x="320" y="116" width="60" height="48" fill="#08101A"/>
      <rect x="322" y="140" width="56" height="24" fill="#060D14"/>
      <rect x="323" y="128" width="18" height="36" fill="#0E1826"/>
      <polygon points="323,128 332,119 341,128" fill="#162030"/>
      <rect x="347" y="132" width="20" height="32" fill="#0E1826"/>
      <polygon points="347,132 357,123 367,132" fill="#162030"/>
      <text x="200" y="213" textAnchor="middle" fill="#93C5FD" fontSize="9" opacity="0.78" fontStyle="italic">Itaparica, Vila Velha — noite de semana</text>
    </svg>
  );
}

const SCENE_FOR_ROUND = { 1:CenaUPA, 2:CenaPraiaCanto, 3:CenaFlexal, 4:CenaTerceiraPonte, 5:CenaItaparica };

// ─── ENTRY SCREEN ────────────────────────────────────────────────────────────
function EntryScreen({ onStudent, onProfessor }) {
  const [nameInput, setNameInput] = useState('');
  const [passInput, setPassInput] = useState('');
  const [passErr, setPassErr] = useState(false);
  const BG = { minHeight: '100vh', background: '#010B18', color: '#F1F5F9', fontFamily: 'Inter, sans-serif', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24 };
  const card = { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, padding: 24, flex: '1 1 180px', minWidth: 180 };
  const inp = (extra = {}) => ({ width: '100%', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 8, padding: '12px 14px', color: '#F1F5F9', fontSize: 14, outline: 'none', boxSizing: 'border-box', fontFamily: 'Inter,sans-serif', marginBottom: 10, ...extra });
  return (
    <div style={BG}>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <div style={{ fontSize: 56, marginBottom: 10 }}>⚖️</div>
        <h1 style={{ fontFamily: 'Playfair Display, serif', fontSize: 36, fontWeight: 900, marginBottom: 8, lineHeight: 1.2 }}>O Véu da Ignorância</h1>
        <p style={{ color: '#64748B', fontSize: 13, margin: 0 }}>Economia do Setor Público · Fucape Business School</p>
        <p style={{ color: '#475569', fontSize: 12, marginTop: 4 }}>Os Dois Teoremas do Bem-Estar · Rawls, Bentham, Igualitarismo</p>
      </div>
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center', width: '100%', maxWidth: 460 }}>
        <div style={card}>
          <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: 2, color: '#64748B', textTransform: 'uppercase', marginBottom: 12 }}>Aluno</div>
          <input
            placeholder="Seu nome"
            value={nameInput}
            onChange={e => setNameInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && nameInput.trim() && onStudent(nameInput.trim())}
            style={inp()}
          />
          <button
            onClick={() => nameInput.trim() && onStudent(nameInput.trim())}
            style={{ width: '100%', padding: '13px 0', background: '#10B981', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 15, color: '#000', cursor: 'pointer', fontFamily: 'Inter,sans-serif' }}
          >
            Entrar →
          </button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#334155', fontSize: 12, padding: '0 4px' }}>
          <div style={{ width: 1, flex: 1, background: 'rgba(255,255,255,0.06)' }} />
          <span style={{ padding: '8px 0' }}>ou</span>
          <div style={{ width: 1, flex: 1, background: 'rgba(255,255,255,0.06)' }} />
        </div>
        <div style={card}>
          <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: 2, color: '#64748B', textTransform: 'uppercase', marginBottom: 12 }}>Professor</div>
          <input
            type="password"
            placeholder="Senha"
            value={passInput}
            onChange={e => { setPassInput(e.target.value); setPassErr(false); }}
            onKeyDown={e => { if (e.key === 'Enter') { if (passInput === PROFESSOR_PASSWORD) onProfessor(); else setPassErr(true); } }}
            style={inp({ border: `1px solid ${passErr ? '#EF4444' : 'rgba(255,255,255,0.12)'}`, marginBottom: passErr ? 4 : 10 })}
          />
          {passErr && <div style={{ color: '#EF4444', fontSize: 11, marginBottom: 8 }}>Senha incorreta</div>}
          <button
            onClick={() => { if (passInput === PROFESSOR_PASSWORD) onProfessor(); else setPassErr(true); }}
            style={{ width: '100%', padding: '13px 0', background: 'transparent', border: '1.5px solid #10B981', borderRadius: 8, fontWeight: 700, fontSize: 15, color: '#10B981', cursor: 'pointer', fontFamily: 'Inter,sans-serif' }}
          >
            Painel →
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── PROFESSOR VIEW ───────────────────────────────────────────────────────────
function ProfessorView({ onExit }) {
  const [resultados, setResultados] = useState(() => {
    try { return JSON.parse(localStorage.getItem(RESULTS_KEY) || '[]'); } catch { return []; }
  });
  const BG = { minHeight: '100vh', background: '#010B18', color: '#F1F5F9', fontFamily: 'Inter, sans-serif' };
  const W = { maxWidth: 680, margin: '0 auto', padding: '32px 20px 80px' };
  const gameUrl = typeof window !== 'undefined' ? window.location.href : '';
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(gameUrl)}&bgcolor=010B18&color=10B981&qzone=1`;
  const limpar = () => { localStorage.removeItem(RESULTS_KEY); setResultados([]); };
  const contratos = { utilitarista: RULES.utilitarista, rawlsiana: RULES.rawlsiana, igualitaria: RULES.igualitaria };

  return (
    <div style={BG}>
      <div style={W}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32 }}>
          <div>
            <div style={{ fontSize: 12, color: '#64748B', fontWeight: 700, letterSpacing: 1 }}>PAINEL DO PROFESSOR</div>
            <h2 style={{ fontFamily: 'Playfair Display, serif', fontSize: 24, fontWeight: 700, margin: '4px 0 0' }}>O Véu da Ignorância</h2>
          </div>
          <button onClick={onExit} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '8px 16px', color: '#94A3B8', fontSize: 13, cursor: 'pointer', fontFamily: 'Inter,sans-serif' }}>← Sair</button>
        </div>

        {/* QR Code */}
        <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, padding: 28, marginBottom: 24, display: 'flex', gap: 28, alignItems: 'center', flexWrap: 'wrap' }}>
          <img src={qrUrl} alt="QR Code" style={{ width: 180, height: 180, borderRadius: 12, display: 'block', flexShrink: 0 }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 800, fontSize: 16, marginBottom: 8 }}>📱 QR Code para alunos</div>
            <p style={{ color: '#94A3B8', fontSize: 14, lineHeight: 1.6, margin: '0 0 12px' }}>
              Projete ou compartilhe este QR Code. Os alunos entram com o nome — sem código de acesso.
            </p>
            <div style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#10B981', fontFamily: 'JetBrains Mono, monospace', wordBreak: 'break-all' }}>
              {gameUrl}
            </div>
          </div>
        </div>

        {/* Resultados */}
        <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, padding: 24, marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <div>
              <div style={{ fontSize: 12, color: '#64748B', fontWeight: 700, letterSpacing: 1, marginBottom: 4 }}>RESULTADOS DA SESSÃO</div>
              <div style={{ fontSize: 14, color: '#94A3B8' }}>{resultados.length} aluno{resultados.length !== 1 ? 's' : ''} completou o jogo</div>
            </div>
            {resultados.length > 0 && (
              <button onClick={limpar} style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '6px 14px', color: '#EF4444', fontSize: 12, cursor: 'pointer', fontFamily: 'Inter,sans-serif' }}>Limpar</button>
            )}
          </div>
          {resultados.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#475569', fontSize: 14, padding: '24px 0' }}>Nenhum resultado ainda. Os alunos aparecem aqui ao concluir o jogo.</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                    <th style={{ textAlign: 'left', padding: '8px 12px', color: '#64748B', fontWeight: 600 }}>Aluno</th>
                    <th style={{ textAlign: 'left', padding: '8px 12px', color: '#64748B', fontWeight: 600 }}>Contrato</th>
                    <th style={{ textAlign: 'right', padding: '8px 12px', color: '#64748B', fontWeight: 600 }}>Pts</th>
                    <th style={{ textAlign: 'right', padding: '8px 12px', color: '#64748B', fontWeight: 600 }}>Rawls</th>
                    <th style={{ textAlign: 'right', padding: '8px 12px', color: '#64748B', fontWeight: 600 }}>Utilit.</th>
                    <th style={{ textAlign: 'right', padding: '8px 12px', color: '#64748B', fontWeight: 600 }}>Igual.</th>
                  </tr>
                </thead>
                <tbody>
                  {[...resultados].reverse().map((r, i) => {
                    const rule = RULES[r.contrato];
                    return (
                      <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        <td style={{ padding: '10px 12px', color: '#F1F5F9', fontWeight: 500 }}>{r.nome}</td>
                        <td style={{ padding: '10px 12px', color: rule?.color || '#94A3B8' }}>{rule?.emoji} {rule?.name}</td>
                        <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: rule?.color || '#F1F5F9' }}>{r.total}</td>
                        <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'JetBrains Mono, monospace', color: '#10B981' }}>{r.altScores?.rawlsiana ?? '—'}</td>
                        <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'JetBrains Mono, monospace', color: '#F59E0B' }}>{r.altScores?.utilitarista ?? '—'}</td>
                        <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'JetBrains Mono, monospace', color: '#818CF8' }}>{r.altScores?.igualitaria ?? '—'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Info da sessão */}
        <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 12, padding: '16px 20px', fontSize: 13, color: '#475569', lineHeight: 1.7 }}>
          <strong style={{ color: '#64748B' }}>Sequência de nascimento:</strong> Pobre → Rico → Pobre → Pobre → Classe Média<br />
          <strong style={{ color: '#64748B' }}>Pontuação base:</strong> Rawls (30) · Igualitária (25) · Utilitarista (20) — antes dos modificadores de circunstância (±0 ou ±5 aleatórios)
        </div>
      </div>
    </div>
  );
}

// ─── GAME COMPONENT ──────────────────────────────────────────────────────────
function Game({ name, onRestart }) {
  const [phase, setPhase] = useState('contract');
  const [contract, setContract] = useState(null);
  const [round, setRound] = useState(1);
  const [subPhase, setSubPhase] = useState('reveal');
  const [modifiers] = useState(() =>
    Array.from({ length: TOTAL_ROUNDS }, () =>
      MODIFIER_OPTIONS[Math.floor(Math.random() * MODIFIER_OPTIONS.length)]
    )
  );
  const [scores, setScores] = useState([]);

  const W = { maxWidth: 640, margin: '0 auto', padding: '0 20px' };
  const BG = { minHeight: '100vh', background: '#010B18', color: '#F1F5F9', fontFamily: 'Inter, sans-serif' };

  // ── CONTRACT ─────────────────────────────────────────────────────────────
  if (phase === 'contract') {
    return (
      <div style={BG}>
        <div style={{ ...W, paddingTop: 40, paddingBottom: 64 }}>
          <div style={{ marginBottom: 28 }}>
            <div style={{ fontSize: 12, color: '#64748B', fontWeight: 700, letterSpacing: 1.5, marginBottom: 10 }}>
              VÉLO DA IGNORÂNCIA
            </div>
            <h2 style={{ fontFamily: 'Playfair Display, serif', fontSize: 26, fontWeight: 700, marginBottom: 10, lineHeight: 1.3 }}>
              Você ainda não sabe como vai nascer.
            </h2>
            <p style={{ color: '#94A3B8', fontSize: 14, lineHeight: 1.7 }}>
              Escolha as regras da sociedade antes de descobrir sua posição. Você pode nascer
              rico (10%), classe média (30%) ou pobre (60%).
            </p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 28 }}>
            {Object.entries(RULES).map(([key, rule]) => {
              const selected = contract === key;
              return (
                <div
                  key={key}
                  onClick={() => setContract(key)}
                  style={{
                    background: selected ? rule.bg : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${selected ? rule.border : 'rgba(255,255,255,0.07)'}`,
                    borderRadius: 12, padding: '18px 20px', cursor: 'pointer',
                    transition: 'border-color 0.15s, background 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                    <div style={{ fontSize: 26, lineHeight: 1, paddingTop: 2 }}>{rule.emoji}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                        <span style={{ fontSize: 17, fontWeight: 700, color: selected ? rule.color : '#F1F5F9' }}>{rule.name}</span>
                        <span style={{ fontSize: 12, color: '#64748B' }}>{rule.philosopher}</span>
                      </div>
                      <div style={{ fontSize: 13, color: selected ? rule.color : '#94A3B8', marginBottom: 8, fontWeight: 500 }}>{rule.tagline}</div>
                      <p style={{ fontSize: 13, color: '#94A3B8', lineHeight: 1.6, margin: '0 0 12px' }}>{rule.plain}</p>
                      <div style={{ display: 'flex', gap: 20 }}>
                        {Object.entries(POS).map(([pk, pv]) => (
                          <div key={pk} style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: 11, color: '#475569', marginBottom: 2 }}>{pv.label}</div>
                            <div style={{ fontSize: 18, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: selected ? rule.color : pv.color }}>{rule.utils[pk]}</div>
                          </div>
                        ))}
                        <div style={{ textAlign: 'center', marginLeft: 'auto' }}>
                          <div style={{ fontSize: 11, color: '#475569', marginBottom: 2 }}>Esperado</div>
                          <div style={{ fontSize: 18, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: '#64748B' }}>{rule.expected.toFixed(1)}</div>
                        </div>
                      </div>
                    </div>
                    {selected && (
                      <div style={{ width: 22, height: 22, background: rule.color, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2 }}>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={key === 'igualitaria' ? '#1e1b4b' : '#000'} strokeWidth="3.5" strokeLinecap="round"><path d="M20 6L9 17l-5-5" /></svg>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          <button
            disabled={!contract}
            onClick={() => setPhase('round')}
            style={{
              width: '100%',
              background: contract ? RULES[contract].color : '#1E293B',
              color: contract ? (contract === 'igualitaria' ? '#1e1b4b' : '#000') : '#475569',
              border: 'none', borderRadius: 8, padding: '15px',
              fontSize: 16, fontWeight: 700,
              cursor: contract ? 'pointer' : 'not-allowed',
              fontFamily: 'Inter,sans-serif', transition: 'all 0.2s',
            }}
          >
            {contract ? `Confirmar: Sociedade ${RULES[contract].name} →` : 'Escolha uma sociedade'}
          </button>
          <p style={{ color: '#475569', fontSize: 13, marginTop: 14, textAlign: 'center', lineHeight: 1.6 }}>
            ⚠️ Esta escolha é definitiva. Você viverá com ela por 5 gerações.
          </p>
        </div>
      </div>
    );
  }

  // ── ROUND ────────────────────────────────────────────────────────────────
  if (phase === 'round') {
    const story = STORIES[round];
    const mod = modifiers[round - 1];
    const modInfo = MODIFIER_LABELS[String(mod)];
    const Scene = SCENE_FOR_ROUND[round];
    const pos = story.pos;
    const posInfo = POS[pos];
    const rule = RULES[contract];
    const base = rule.utils[pos];
    const roundTotal = base + mod;
    const accum = scores.reduce((s, x) => s + x, 0);

    if (subPhase === 'reveal') {
      return (
        <div style={BG}>
          <div style={{ ...W, paddingTop: 24, paddingBottom: 64 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
              <div style={{ fontSize: 12, color: '#64748B', fontWeight: 700, letterSpacing: 1 }}>GERAÇÃO {round}/{TOTAL_ROUNDS}</div>
              <div style={{ background: rule.bg, border: `1px solid ${rule.border}`, borderRadius: 20, padding: '4px 14px', fontSize: 13, color: rule.color, fontWeight: 600 }}>
                {rule.emoji} {rule.name}
              </div>
            </div>
            <div style={{ borderRadius: 10, overflow: 'hidden', marginBottom: 20, border: '1px solid rgba(255,255,255,0.06)' }}>
              <Scene />
            </div>
            <div style={{ background: posInfo.bg, border: `1px solid ${posInfo.border}`, borderRadius: 10, padding: '14px 18px', marginBottom: 16 }}>
              <div style={{ fontSize: 11, color: posInfo.color, fontWeight: 700, letterSpacing: 1, marginBottom: 4 }}>
                VOCÊ NASCEU NA {posInfo.label.toUpperCase()} · {posInfo.prob} de probabilidade
              </div>
              <h3 style={{ fontSize: 19, fontWeight: 700, marginBottom: 4, lineHeight: 1.3 }}>{story.titulo}</h3>
              <div style={{ fontSize: 12, color: '#64748B' }}>{story.local}</div>
            </div>
            <details style={{ marginBottom: 20 }}>
              <summary style={{ cursor: 'pointer', fontSize: 14, color: '#64748B', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 8, padding: '10px 16px', fontWeight: 500 }}>
                📖 Ler a história completa desta geração
              </summary>
              <div style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '0 0 8px 8px', padding: '16px 18px' }}>
                <p style={{ fontSize: 14, color: '#CBD5E1', lineHeight: 1.75, marginBottom: 10 }}>{story.drama}</p>
                <p style={{ fontSize: 13, color: '#94A3B8', lineHeight: 1.7, marginBottom: 10 }}>{story.vida}</p>
                <p style={{ fontSize: 13, color: '#64748B', lineHeight: 1.7, fontStyle: 'italic' }}>{story.fim}</p>
              </div>
            </details>
            <button
              onClick={() => setSubPhase('score')}
              style={{ width: '100%', background: posInfo.bg, border: `1px solid ${posInfo.border}`, borderRadius: 8, padding: '14px', fontSize: 16, fontWeight: 600, color: posInfo.color, cursor: 'pointer', fontFamily: 'Inter,sans-serif' }}
            >
              Ver pontuação desta geração →
            </button>
          </div>
        </div>
      );
    }

    // subPhase === 'score'
    return (
      <div style={BG}>
        <div style={{ ...W, paddingTop: 24, paddingBottom: 64 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <div style={{ fontSize: 12, color: '#64748B', fontWeight: 700, letterSpacing: 1 }}>GERAÇÃO {round}/{TOTAL_ROUNDS}</div>
            <div style={{ background: rule.bg, border: `1px solid ${rule.border}`, borderRadius: 20, padding: '4px 14px', fontSize: 13, color: rule.color, fontWeight: 600 }}>
              {rule.emoji} {rule.name}
            </div>
          </div>
          <div style={{ background: posInfo.bg, border: `1px solid ${posInfo.border}`, borderRadius: 10, padding: '12px 18px', marginBottom: 20 }}>
            <span style={{ fontSize: 13, color: posInfo.color, fontWeight: 600 }}>{posInfo.label} · {story.titulo}</span>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, overflow: 'hidden', marginBottom: 20 }}>
            <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 12, color: '#64748B', marginBottom: 4 }}>Pontuação base · {rule.name}</div>
                <div style={{ fontSize: 13, color: '#94A3B8', lineHeight: 1.5, maxWidth: 280 }}>{rule.why[pos]}</div>
              </div>
              <div style={{ fontSize: 32, fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: rule.color, marginLeft: 16 }}>+{base}</div>
            </div>
            <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 12, color: '#64748B', marginBottom: 4 }}>{modInfo.emoji} {modInfo.titulo}</div>
                <div style={{ fontSize: 13, color: '#94A3B8', lineHeight: 1.5, maxWidth: 280 }}>{modInfo.descricao}</div>
              </div>
              <div style={{ fontSize: 32, fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: mod > 0 ? '#10B981' : mod < 0 ? '#EF4444' : '#94A3B8', marginLeft: 16 }}>
                {mod > 0 ? `+${mod}` : mod === 0 ? '±0' : mod}
              </div>
            </div>
            <div style={{ padding: '20px 24px', background: rule.bg, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 13, color: rule.color, fontWeight: 700 }}>Total desta geração</div>
                {scores.length > 0 && (
                  <div style={{ fontSize: 12, color: '#64748B', marginTop: 4 }}>
                    Acumulado: {accum} + {roundTotal} = <strong style={{ color: rule.color }}>{accum + roundTotal}</strong>
                  </div>
                )}
              </div>
              <div style={{ fontSize: 48, fontFamily: 'JetBrains Mono, monospace', fontWeight: 900, color: rule.color }}>{roundTotal}</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 24 }}>
            {Array.from({ length: TOTAL_ROUNDS }).map((_, i) => (
              <div key={i} style={{ width: i < round ? 24 : 8, height: 8, borderRadius: 4, transition: 'width 0.3s', background: i < round ? rule.color : 'rgba(255,255,255,0.1)' }} />
            ))}
          </div>
          <button
            onClick={() => {
              const newScores = [...scores, roundTotal];
              setScores(newScores);
              if (round >= TOTAL_ROUNDS) {
                // salvar resultado no localStorage para o painel do professor
                const altScores = {};
                Object.keys(RULES).forEach(c => {
                  altScores[c] = SEQUENCE.reduce((sum, pos, i) => sum + RULES[c].utils[pos] + modifiers[i], 0);
                });
                try {
                  const prev = JSON.parse(localStorage.getItem(RESULTS_KEY) || '[]');
                  prev.push({ nome: name, contrato: contract, total: newScores.reduce((s, x) => s + x, 0), altScores, ts: Date.now() });
                  localStorage.setItem(RESULTS_KEY, JSON.stringify(prev));
                } catch {}
                setPhase('final');
              } else {
                setRound(r => r + 1);
                setSubPhase('reveal');
              }
            }}
            style={{ width: '100%', background: rule.color, color: contract === 'igualitaria' ? '#1e1b4b' : '#000', border: 'none', borderRadius: 8, padding: '15px', fontSize: 16, fontWeight: 700, cursor: 'pointer', fontFamily: 'Inter,sans-serif' }}
          >
            {round >= TOTAL_ROUNDS ? '🏁 Ver Resultado Final →' : `Próxima Geração (${round + 1}/${TOTAL_ROUNDS}) →`}
          </button>
        </div>
      </div>
    );
  }

  // ── FINAL ────────────────────────────────────────────────────────────────
  if (phase === 'final') {
    const total = scores.reduce((s, x) => s + x, 0);
    const rule = RULES[contract];
    const altScores = {};
    Object.keys(RULES).forEach(c => {
      altScores[c] = SEQUENCE.reduce((sum, pos, i) => sum + RULES[c].utils[pos] + modifiers[i], 0);
    });
    const maxAlt = Math.max(...Object.values(altScores));

    return (
      <div style={BG}>
        <div style={{ ...W, paddingTop: 32, paddingBottom: 80 }}>
          <div style={{ textAlign: 'center', marginBottom: 36 }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>🏁</div>
            <h2 style={{ fontFamily: 'Playfair Display, serif', fontSize: 30, fontWeight: 900, marginBottom: 8 }}>5 Gerações Concluídas</h2>
            <p style={{ color: '#94A3B8', fontSize: 15 }}>{name}, este foi o seu percurso:</p>
          </div>
          <div style={{ background: rule.bg, border: `2px solid ${rule.border}`, borderRadius: 16, padding: '28px 32px', textAlign: 'center', marginBottom: 24 }}>
            <div style={{ fontSize: 13, color: rule.color, fontWeight: 700, letterSpacing: 1, marginBottom: 8 }}>{rule.emoji} SOCIEDADE {rule.name.toUpperCase()}</div>
            <div style={{ fontSize: 88, fontFamily: 'JetBrains Mono, monospace', fontWeight: 900, color: rule.color, lineHeight: 1 }}>{total}</div>
            <div style={{ fontSize: 15, color: '#94A3B8', marginTop: 8 }}>pontos em 5 gerações</div>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 12, padding: '20px 24px', marginBottom: 20 }}>
            <div style={{ fontSize: 12, color: '#64748B', fontWeight: 700, letterSpacing: 1, marginBottom: 16 }}>GERAÇÃO A GERAÇÃO</div>
            {SEQUENCE.map((pos, i) => {
              const m = modifiers[i];
              const b = rule.utils[pos];
              const t = b + m;
              const posInfo = POS[pos];
              const mInfo = MODIFIER_LABELS[String(m)];
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, paddingBottom: 12, borderBottom: i < 4 ? '1px solid rgba(255,255,255,0.04)' : 'none', marginBottom: i < 4 ? 12 : 0 }}>
                  <div style={{ fontSize: 12, color: '#475569', fontFamily: 'JetBrains Mono,monospace', width: 22, flexShrink: 0 }}>G{i + 1}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, color: posInfo.color, fontWeight: 600 }}>{posInfo.label}</div>
                    <div style={{ fontSize: 12, color: '#475569' }}>{mInfo.emoji} {mInfo.titulo}</div>
                  </div>
                  <div style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: rule.color, fontSize: 20 }}>{t > 0 ? `+${t}` : t}</div>
                </div>
              );
            })}
          </div>
          <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 12, padding: '20px 24px', marginBottom: 24 }}>
            <div style={{ fontSize: 12, color: '#64748B', fontWeight: 700, letterSpacing: 1, marginBottom: 16 }}>E SE VOCÊ TIVESSE ESCOLHIDO OUTRA SOCIEDADE?</div>
            {Object.entries(altScores).sort((a, b) => b[1] - a[1]).map(([c, s]) => {
              const r = RULES[c];
              const isChosen = c === contract;
              const isBest = s === maxAlt;
              return (
                <div key={c} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '12px 16px', borderRadius: 10, marginBottom: 8, background: isChosen ? r.bg : 'transparent', border: `1px solid ${isChosen ? r.border : 'rgba(255,255,255,0.04)'}` }}>
                  <div style={{ fontSize: 22 }}>{r.emoji}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, color: isChosen ? r.color : '#CBD5E1', fontWeight: isChosen ? 700 : 400 }}>
                      {r.name}
                      {isChosen && <span style={{ fontSize: 12, color: '#64748B', marginLeft: 8 }}>← sua escolha</span>}
                      {isBest && !isChosen && <span style={{ fontSize: 12, color: '#F59E0B', marginLeft: 8 }}>← melhor resultado</span>}
                    </div>
                  </div>
                  <div style={{ width: 80, height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ width: `${(s / maxAlt) * 100}%`, height: '100%', background: r.color, borderRadius: 3 }} />
                  </div>
                  <div style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, fontSize: 20, color: isChosen ? r.color : '#64748B', width: 32, textAlign: 'right' }}>{s}</div>
                </div>
              );
            })}
          </div>
          <div style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 12, padding: '20px 24px', marginBottom: 32 }}>
            <div style={{ fontSize: 15, color: '#10B981', fontWeight: 700, marginBottom: 12 }}>🛡️ O que Rawls diria?</div>
            <p style={{ fontSize: 14, color: '#94A3B8', lineHeight: 1.7, margin: 0 }}>
              Rawls argumenta que, por trás do véu da ignorância — sem saber em qual posição você nasceria —
              a escolha racional seria a sociedade <strong style={{ color: '#10B981' }}>Rawlsiana</strong>. Por quê?
              Porque você precisa se proteger do pior cenário: nascer na faixa baixa (60% de chance).
              A garantia de pelo menos <strong style={{ color: '#10B981' }}>5 pontos por geração</strong> é preferível ao risco de receber apenas 1 (utilitarista).
            </p>
            <p style={{ fontSize: 14, color: '#64748B', lineHeight: 1.7, marginTop: 12 }}>
              Este é o princípio <em>maximin</em>: maximize o mínimo garantido.
              Ele justifica transferências redistributivas e sistemas de proteção social mesmo
              para quem já tem muito — porque, antes de nascer, você não sabia que teria.
            </p>
          </div>
          <button
            onClick={onRestart}
            style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '14px', fontSize: 15, fontWeight: 600, color: '#CBD5E1', cursor: 'pointer', fontFamily: 'Inter,sans-serif' }}
          >
            Jogar novamente
          </button>
        </div>
      </div>
    );
  }

  return null;
}

// ─── ROOT EXPORT ─────────────────────────────────────────────────────────────
export default function VeuIgnorancia() {
  const [mode, setMode] = useState(null); // null | 'student' | 'professor'
  const [playerName, setPlayerName] = useState('');
  const [gameKey, setGameKey] = useState(0);

  if (!mode) return <EntryScreen onStudent={n => { setPlayerName(n); setMode('student'); }} onProfessor={() => setMode('professor')} />;
  if (mode === 'professor') return <ProfessorView onExit={() => setMode(null)} />;
  return <Game key={gameKey} name={playerName} onRestart={() => { setGameKey(k => k + 1); setMode(null); }} />;
}
