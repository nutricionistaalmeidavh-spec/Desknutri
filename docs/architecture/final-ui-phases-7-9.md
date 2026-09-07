# NutriDesk — fechamento das fases 7–9

## Fase 7 — Motion P2

- Transição de entrada entre páginas: 180 ms, `OutCubic`.
- Feedback de salvamento: 220 ms, não bloqueante, reaproveitando `SaveStateLabel`.
- Nenhum handler clínico, rota, persistência ou ordem de eventos foi alterado.
- `NUTRIDESK_REDUCE_MOTION=1` desativa as animações sem remover feedback funcional.

## Fase 8 — Limpeza com equivalência

Os scripts P3/V4 removidos eram instaladores/verificadores/rollbacks one-shot de entregas antigas. A aplicação atual inicializa e migra o banco por `Database.initialize()` -> `migrate()`, e as funcionalidades promovidas dessas fases vivem nos módulos canônicos atuais.

| Legado removido | Substituição canônica atual |
| --- | --- |
| Aplicar/verificar/rollback P3 | `nutridesktop/data/migrations.py`, CI e testes |
| Updater P3 e manifesto estático | `services/update_service.py` + `ui/auto_update_features.py` + GitHub Releases |
| Backup/exportação/suporte P3 | `services/auto_backup.py`, `patient_package.py`, `structured_export.py`, `diagnostics.py` |
| Aplicar/verificar/rollback V4 | migrations + testes atuais |
| Documentação/matrizes V4 de conta | `services/account_licensing.py`, `ui/account_dialog.py`, `license_server/` |
| README de chave de update | fluxo 6.2+ sem chave própria |

Foram preservados `CONFIGURAR_LICENCAS.ps1` e `INICIAR_PAINEL_LICENCAS.bat`, pois continuam sendo utilitários operacionais do licenciamento atual.

## Fase 9 — Release única

`nutridesktop/version.py` é a fonte única da versão corrente.

- Janela e sidebar importam `APP_VERSION`.
- `tools/build_release.py` injeta `APP_VERSION` no Inno Setup.
- `NutriDesktop.iss` não possui fallback numérico e falha se `MyAppVersion` não for fornecida.
- O build valida que `CHANGELOG.md` começa pela mesma `APP_VERSION`.
- O workflow lê `APP_VERSION` para título/tag da Release.
- O instalador e o asset seguem `NutriDesktop-Setup-{APP_VERSION}.exe`.

A versão de fechamento dessas três fases é 6.3.0. O schema permanece 13.
