'use strict';
const L = require('../_lib');

// Indica apenas se o acesso por cadastro está configurado (sem revelar quais variáveis faltam).
module.exports = (req, res) => {
  const e = L.env;
  const pronto = !!(e('ESTUDOS_SENHA') && e('SESSION_SECRET') && e('SUPABASE_URL') && e('SUPABASE_SERVICE_ROLE_KEY') &&
    ((e('GMAIL_USER') && e('GMAIL_APP_PASSWORD')) || e('RESEND_API_KEY')));
  L.resposta(res, 200, { pronto });
};
