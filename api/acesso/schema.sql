-- Esquema do acesso por cadastro aos estudos (Supabase / Postgres).
-- Já aplicado no projeto Supabase do site; este arquivo documenta e permite recriar o ambiente.
-- Uso: executar no SQL Editor do Supabase. Os dados só são lidos e gravados pelas funções de api/ com a chave de serviço.

create table if not exists public.acesso_leitores (
  email text primary key,                                   -- sempre em minúsculas
  status text not null default 'ativo' check (status in ('ativo','revogado')),
  criado_em timestamptz not null default now(),
  ultimo_acesso timestamptz
);

create table if not exists public.acesso_tokens (
  hash text primary key,                                    -- SHA-256 do token enviado por e-mail (o token em claro não é guardado)
  email text not null,
  destino text,                                             -- página do estudo para onde o leitor volta depois do login
  ip_hash text,                                             -- SHA-256 de IP + segredo, usado só para limitar pedidos
  criado_em timestamptz not null default now(),
  expira_em timestamptz not null,                           -- 30 minutos após a criação
  usado_em timestamptz                                      -- uso único
);
create index if not exists acesso_tokens_email_idx on public.acesso_tokens (email, criado_em);
create index if not exists acesso_tokens_ip_idx on public.acesso_tokens (ip_hash, criado_em);

create table if not exists public.acesso_log (
  id bigserial primary key,
  email text not null,
  slug text not null,                                       -- estudo lido
  em timestamptz not null default now()
);
create index if not exists acesso_log_email_idx on public.acesso_log (email, em);

-- RLS ligada e sem políticas: anon e authenticated não leem nem escrevem; a chave de serviço ignora a RLS.
alter table public.acesso_leitores enable row level security;
alter table public.acesso_tokens enable row level security;
alter table public.acesso_log enable row level security;
revoke all on public.acesso_leitores, public.acesso_tokens, public.acesso_log from anon, authenticated;
revoke all on sequence public.acesso_log_id_seq from anon, authenticated;

-- Revogar um leitor:   update public.acesso_leitores set status = 'revogado' where email = 'pessoa@exemplo.com';
-- Excluir um leitor (LGPD): delete from public.acesso_log where email = '...'; delete from public.acesso_tokens where email = '...'; delete from public.acesso_leitores where email = '...';
