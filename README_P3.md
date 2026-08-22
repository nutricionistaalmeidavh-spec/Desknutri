# NutriDesktop 3.0.0 — P3 comercial

Esta camada é cumulativa sobre a v2 (itens 1–28). Não exige servidor para o uso clínico normal.

## Ativação do atualizador
1. Em um diretório seguro, fora do repositório: `python tools/update_key_admin.py C:\Segredos\NutriDesktop`.
2. Guarde `update_private.pem` offline. **Nunca** distribua nem faça commit.
3. Copie apenas `update_public.pem` para `config\update_public.pem` antes do build comercial.
4. Gere cada release com `GERAR_RELEASE.ps1 -PrivateKey C:\Segredos\NutriDesktop\update_private.pem -BaseUrl https://seu-endereco/releases`.
5. A partir da segunda release, passe também `-RollbackInstaller <instalador-anterior>` para embutir o fallback no manifesto assinado.
6. Publique juntos `version.json` e o(s) instalador(es). O usuário configura a URL de `version.json` na tela Atualizações.

O app verifica assinatura Ed25519 + SHA-256. A instalação só começa após confirmação. Depois o runner executa `NutriDesktop.exe --healthcheck`; se falhar e houver instalador anterior informado no manifesto, tenta rollback.

## Backup automático
Configurações permite diário/semanal, execução no startup/fechamento e retenções diária/semanal/mensal. Backups manuais continuam aceitando senha.

## Portabilidade
- `.nutri`: prontuário individual com dados, planos, avaliações, consultas, fotos/documentos e checksums; senha opcional.
- JSON / CSV ZIP / XLSX: exportação estruturada do consultório.
- PDFs: continuam sendo gerados no prontuário.

## Suporte
A tela Suporte mostra versão, schema, integridade SQLite, espaço, dependências e último backup/update. O ZIP de diagnóstico não inclui `.db`, fotos, documentos ou prontuários; logs passam por redação de e-mail/telefone e caminho de dados.

## Aplicação no repositório
`./APLICAR_V3_P3.ps1 -RepoPath "C:\caminho\Desknutri"`

Depois execute `./VERIFICAR_V3_P3.ps1`.
