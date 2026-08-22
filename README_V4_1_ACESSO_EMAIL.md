# NutriDesktop 4.1 — acesso por e-mail e senha provisória

Fluxo comercial:

1. Administrador abre o painel `/admin/` do site NutriDesk.
2. Clica em **Liberar e-mail** e informa cliente, plano, limite de PCs e validade.
3. O sistema gera uma senha provisória numérica de 8 dígitos com `crypto.getRandomValues`.
4. A conta é criada no Supabase Auth já confirmada; não existe link de confirmação para localhost.
5. A senha provisória é enviada automaticamente por e-mail usando o Gmail configurado no backend do AppDeploy.
6. O cliente instala o NutriDesktop, informa e-mail + senha recebida e registra o dispositivo.
7. Depois de entrar, pode usar **Conta → Trocar senha** para escolher uma nova senha com pelo menos 8 caracteres.
8. O administrador pode usar **Gerar nova senha e reenviar** se necessário.

## Infraestrutura online

- Site e painel: `https://nutridesk-sfdln8.v2.appdeploy.ai/`
- Painel: `https://nutridesk-sfdln8.v2.appdeploy.ai/admin/`
- Licenciamento: Supabase Edge Function `nutridesk-licensing`
- Conta/senha: Supabase Edge Function `nutridesk-account`
- E-mail: backend AppDeploy, segredo `GMAIL_APP_PASSWORD`

O valor do segredo SMTP não faz parte deste pacote.
