# Relatório de verificação — NutriDesktop 4.0 Conta + Licenças

## Resultado

- App: **4.0.0**
- Schema local: **11**
- Suíte: **44 passed, 1 skipped**
- Skip: teste opcional WHO quando `pygrowthstandards` não está instalado no ambiente de verificação.
- `compileall`: aprovado para `app.py`, `nutridesktop/`, `license_server/` e `tools/`.

## Smoke de rede real

Foi iniciado um Uvicorn em localhost com banco e chaves temporários. O desktop, usando `AccountLicenseService`, executou:

1. ativação de e-mail pré-liberado;
2. criação da senha no primeiro acesso;
3. recebimento e validação do entitlement Ed25519;
4. armazenamento do token de dispositivo;
5. renovação via `/api/v1/refresh` sem reutilizar a senha.

Resultado: `network_smoke_ok`.

## Segurança verificada

- senha armazenada apenas como hash scrypt no servidor;
- token do dispositivo armazenado como SHA-256 no servidor;
- senha não é persistida no desktop;
- token local protegido via DPAPI no Windows ou AES-GCM fallback;
- API remota do desktop exige HTTPS, exceto localhost;
- painel admin usa sessão HMAC, cookie HttpOnly/SameSite e CSRF nos POSTs administrativos;
- chave privada Ed25519 e segredo de sessão não fazem parte do pacote;
- SQLite do servidor e chave privada recebem permissão restritiva quando suportado pelo SO.

## Limitações de ambiente

- PySide6 não está instalado neste ambiente Linux, então a janela gráfica não foi aberta aqui. Os módulos de UI compilam sintaticamente.
- Inno Setup não está disponível; o instalador Windows precisa ser gerado no PC Windows pelo script existente.
- Em produção o servidor deve ser publicado atrás de HTTPS e usar volume persistente para `license_server_data`.

## Comportamento deliberado

Uma conta bloqueada/desvinculada pode continuar funcionando enquanto estiver totalmente offline até a autorização local assinada expirar. O período é configurável por licença (`offline_days`, padrão 30). Na próxima renovação online, bloqueio/expiração/revogação é aplicado.
