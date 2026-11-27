# Acesso aos estudos por cadastro (suspenso)

A seção de estudos foi retirada do ar por decisão do autor. Este diretório guarda, fora da publicação, o código do acesso por cadastro (`api/`, que a Vercel só publica quando está na raiz do repositório) e o esquema do banco (`api/acesso/schema.sql`). Os textos completos dos estudos estão no repositório privado (`estudos-restritos/`), e os materiais de apoio em `materiais-retirados/`.

Para recolocar a seção no ar, com a decisão do autor:

1. `git mv scripts/acesso-estudos/api api` e recriar `package.json` com a dependência `nodemailer` (versão 10.6.1).
2. Gerar as páginas e os arquivos cifrados: `ESTUDOS_SENHA='...' python3 scripts/cifrar-estudos.py <pasta com os originais do repositório privado>`.
3. Em `vercel.json`, remover os dois redirecionamentos de `/estudos` e acrescentar `"functions": {"api/estudo.js": {"includeFiles": "_cifrado/**"}}`.
4. Recolocar o link "Estudos" no menu de `index.html` e conferir as variáveis de ambiente na Vercel (`ESTUDOS_SENHA`, `SESSION_SECRET`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`).
