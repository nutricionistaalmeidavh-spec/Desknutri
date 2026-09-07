# Atualizações assinadas do NutriDesk

O NutriDesk usa Ed25519 para validar o manifesto de atualização antes de baixar ou executar instaladores.

- A chave pública é distribuída no aplicativo em `config/update_public.pem`.
- A chave privada **nunca** deve ser versionada.
- A pipeline lê a chave privada apenas do secret `UPDATE_SIGNING_PRIVATE_KEY_B64`.
- Releases automáticas devem falhar se o secret de assinatura estiver ausente.
- O manifesto oficial é publicado como asset `version.json` da GitHub Release.

Endpoint estável do manifesto:

`https://github.com/nutricionistaalmeidavh-spec/Desknutri/releases/latest/download/version.json`

O cliente valida assinatura Ed25519, canal, versão e SHA-256 do instalador antes de aplicar a atualização. O healthcheck pós-instalação e o rollback permanecem obrigatórios.
