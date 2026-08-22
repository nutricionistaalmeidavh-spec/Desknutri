# Relatório de verificação — NutriDesk 5.0 P0–P2

Data: 22/08/2026

## Desktop
- Versão: 5.0.0
- Schema: 12
- Suite: 61 passed / 1 skipped
- `python -m compileall -q nutridesktop app.py`: OK
- Migration schema 11 → 12: OK
- Pendência de plano: OK
- Marcar último plano pendente como enviado: OK
- Distribuição de objetivos baseada na última consulta concluída por paciente: OK
- Contratos estáticos de navegação, dashboard, prontuário, wizard, calendário, configurações e conta: OK

## Licenciamento/admin online
- Colunas `email_status`, `email_last_sent_at`, `email_last_error`: presentes no Supabase.
- Edge Function `nutridesk-account`: v3 ACTIVE.
- Painel AppDeploy: deploy READY; QA sem erros de frontend/rede.
- Gmail App Password permanece em secret do AppDeploy, não no código/frontend.
- Não foi enviado e-mail real de teste para evitar criar/alterar conta de cliente sem necessidade.

## Verificação Qt
Não executada neste ambiente: `PySide6` não está instalado e a rede do runtime não permite instalar a dependência. A UI foi validada por análise de fonte/AST e compilação; é necessário abrir a aplicação em Windows com PySide6 antes do build final do `.exe`.
