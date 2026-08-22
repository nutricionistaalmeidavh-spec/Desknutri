# NutriDesktop 4.0 — Conta + Painel de Licenças

Esta entrega substitui o uso diário de chaves manuais por conta vinculada a uma licença.

## Fluxo do cliente

`e-mail liberado pelo administrador → primeiro acesso → cliente cria senha → PC é registrado → autorização assinada é salva localmente`

Depois do primeiro acesso, conhecer apenas o e-mail não permite criar uma segunda conta nem ativar outro computador. O servidor exige a senha cadastrada e também respeita o limite de dispositivos.

A senha nunca é armazenada no NutriDesktop. O desktop guarda somente um token aleatório daquele dispositivo, protegido localmente, para renovar a autorização sem pedir a senha em toda abertura.

## Modo offline

Cada renovação gera uma autorização Ed25519 válida por `offline_days` (30 dias por padrão). O aplicativo funciona offline até essa data. Quando consegue acessar o servidor, renova a autorização. Bloqueio, expiração ou desvinculação são aplicados na próxima renovação online.

## Painel separado

A pasta `license_server/` contém um minidashboard web responsivo para:
- liberar e-mails;
- bloquear/desbloquear contas;
- definir plano e validade;
- configurar 1 ou mais computadores;
- desvincular dispositivos;
- permitir redefinição de senha;
- visualizar histórico.

## Primeiro teste local

```powershell
.\CONFIGURAR_LICENCAS.ps1 -AdminEmail seu@email.com -ServerUrl http://127.0.0.1:8000
.\INICIAR_PAINEL_LICENCAS.bat
```

Depois abra `http://127.0.0.1:8000/admin`.

Para produção, publique o servidor com HTTPS e use o endereço HTTPS em `config/commercial.json`.

## Compatibilidade

Licenças Ed25519 manuais já existentes continuam aceitas para não bloquear clientes atuais. Novos clientes podem usar exclusivamente conta + e-mail + senha.

## Arquitetura

```text
PAINEL ADMIN (web)
   ↓ libera e-mail / plano / PCs
SERVIDOR DE LICENÇAS
   ↓ conta + senha / token do dispositivo
NUTRIDESKTOP
   ↓ valida assinatura Ed25519
AUTORIZAÇÃO OFFLINE
```

O banco clínico do NutriDesktop continua local e não é enviado ao servidor de licenças. O servidor conhece apenas dados de conta/licença/dispositivo necessários para controle de acesso.
