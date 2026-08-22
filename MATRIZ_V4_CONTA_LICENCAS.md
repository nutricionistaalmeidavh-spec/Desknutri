# Matriz — NutriDesktop 4.0 Conta + Licenças

| Requisito | Implementação | Evidência |
|---|---|---|
| Administrador libera e-mail | `license_server/core.py::AdminService.authorize_email` + dashboard `/admin` | `test_admin_dashboard_flow`, `test_email_not_pre_authorized_cannot_register` |
| Primeiro acesso cria senha | `LicenseService.activate` reivindica apenas conta sem `password_hash` | `test_first_claim_then_password_required` |
| E-mail já usado não cria outra conta | `accounts.email UNIQUE` + senha obrigatória após claim | `test_first_claim_then_password_required` |
| Senha não fica no desktop | desktop guarda apenas `device_token`; servidor usa scrypt | `test_server_never_stores_plain_password_or_device_token` |
| Segundo PC exige senha | `/api/v1/activate` sempre valida credencial em conta já reivindicada | `test_first_claim_then_password_required` |
| Limite de PCs | `licenses.max_devices` e contagem de dispositivos ativos | `test_device_limit_and_revoke` |
| Desvincular PC | painel admin e `/api/v1/unlink` | `test_device_limit_and_revoke` |
| Bloquear conta | `accounts.status=blocked`; refresh é recusado | `test_blocked_account_refresh_fails` |
| Reset de senha | admin remove hash e volta a permitir novo primeiro acesso | `test_admin_password_reset_allows_new_password_but_old_stops` |
| Trocar senha pelo cliente | `/api/v1/change-password` + tela Conta | `test_change_password` |
| Uso offline | entitlement Ed25519 com `expires` e `offline_days` | `test_refresh_uses_device_token_not_password` |
| Renovação sem guardar senha | token aleatório por dispositivo, hash no servidor | `test_refresh_uses_device_token_not_password` |
| Proteção do token local | DPAPI no Windows; AES-GCM fallback | `test_local_secret_roundtrip` |
| Servidor remoto exige HTTPS | cliente recusa HTTP exceto localhost | `test_server_requires_https_for_remote` |
| Painel visual separado | FastAPI server-rendered responsivo | `test_admin_dashboard_flow` |
| Migração de clientes antigos | licença Ed25519 manual anterior continua válida | `_ensure_license` em `app.py` |
| Chave privada fora do cliente | `license_server_data/license_private.pem`; cliente recebe só pública | varredura final sem `*private*.pem` no ZIP |
