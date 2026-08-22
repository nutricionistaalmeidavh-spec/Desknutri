# Painel de Licenças NutriDesktop 4.0

Servidor separado para cadastro de clientes, ativação por conta, dispositivos e licenças.

## Regra de ativação

1. O administrador libera o e-mail no painel.
2. No primeiro uso, o cliente informa o e-mail e escolhe uma senha de no mínimo 8 caracteres.
3. O servidor grava somente o hash `scrypt` da senha.
4. A partir daí o mesmo e-mail já está reivindicado: nova ativação exige a senha existente.
5. A licença limita a quantidade de computadores ativos.
6. O desktop recebe um `device_token` exclusivo e uma autorização Ed25519 de curta duração para funcionamento offline. A senha nunca é salva no desktop.

## Inicialização local

Na raiz do projeto:

```powershell
python -m pip install -r license_server\requirements.txt
python -m license_server.admin_cli init-keys
python -m license_server.admin_cli init-admin --email SEU_EMAIL
python -m license_server.admin_cli copy-public-key --to config\license_public_key.pem
$env:NUTRIDESK_COOKIE_SECURE="0"
python -m uvicorn license_server.main:app --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000/admin`.

Para testar o NutriDesktop localmente, copie `config/commercial.example.json` para `config/commercial.json` e use:

```json
"license_server_url": "http://127.0.0.1:8000"
```

HTTP só é aceito pelo cliente para localhost. Em produção, use HTTPS.

## Produção

- Monte um volume persistente em `/data`.
- Faça proxy HTTPS para o Uvicorn (Cloudflare, Caddy, Nginx ou plataforma gerenciada).
- Mantenha `NUTRIDESK_COOKIE_SECURE=1`.
- Nunca coloque `license_private.pem`, `server_secret.txt` ou `licenses.db` no Git.
- Faça backup periódico do volume de dados.
- Use um único processo Uvicorn enquanto estiver usando SQLite.

O `Dockerfile` e o `docker-compose.yml` desta pasta servem como base de publicação.

## Administração

O painel permite:
- liberar e-mail;
- visualizar conta pendente/ativa/bloqueada;
- definir plano, validade, dias offline e quantidade de dispositivos;
- bloquear/desbloquear conta;
- desvincular computadores;
- liberar redefinição de senha;
- acompanhar histórico de eventos.

`Permitir nova senha` limpa o hash atual. Até o cliente definir a nova senha, o e-mail volta ao estado de primeiro acesso; use essa ação somente a pedido do cliente.
