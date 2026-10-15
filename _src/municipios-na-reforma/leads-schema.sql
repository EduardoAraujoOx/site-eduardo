-- Cadastros do portal Municípios na Reforma (quem pede a memória de cálculo).
-- Rodar uma vez no SQL Editor do projeto Supabase. A função api/lead.js grava com a chave
-- anon; a política abaixo só permite INSERT, então ninguém lê a tabela por essa chave.
-- Quem consulta a lista é o dono do projeto, pelo painel do Supabase (ou pelo MCP autorizado).

create table if not exists public.leads (
    id uuid primary key default gen_random_uuid(),
    criado_em timestamptz not null default now(),
    nome text not null,
    email text not null,
    cargo text not null,
    vinculo text,
    municipio text,
    municipio_cod text,
    uf text,
    origem text,
    utm text,
    aceite_privacidade boolean not null,
    aceite_contato boolean not null default false,
    versao_termos text
);

create index if not exists leads_email_idx on public.leads (lower(email));
create index if not exists leads_municipio_idx on public.leads (municipio_cod);

alter table public.leads enable row level security;

drop policy if exists "inserir cadastro" on public.leads;
create policy "inserir cadastro" on public.leads
    for insert to anon
    with check (aceite_privacidade = true and length(nome) >= 3 and length(email) >= 5);

-- sem política de select, update ou delete para anon: a leitura fica restrita ao dono do projeto
