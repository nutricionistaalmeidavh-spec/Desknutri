# Matriz P3 — Itens 29 a 35

| Item | Implementação | Evidência principal |
|---|---|---|
| 29 Atualizador | Manifesto Ed25519, SHA-256, auto-check, download, runner PowerShell, health-check e rollback por instalador anterior | `services/update_service.py`, tela Atualizações, `--healthcheck`, testes P3 |
| 30 Versionamento | App/schema/conteúdo clínico/WHO/canal separados | `nutridesktop/version.py`, diagnóstico e release manifest |
| 31 `.nutri` | Exportação/importação individual com documentos/fotos, checksums e senha opcional | `services/patient_package.py`, tela Exportações, roundtrip test |
| 32 Estruturado | JSON, CSV ZIP e XLSX de dados do consultório; PDF permanece no prontuário | `services/structured_export.py`, tela Exportações |
| 33 Diagnóstico | Integridade SQLite, versões, espaço, dependências, último backup/update e suporte ZIP redigido sem prontuário | `services/diagnostics.py`, tela Suporte |
| 34 Backup automático | Diário/semanal, startup/close, histórico e retenção diária/semanal/mensal | `services/auto_backup.py`, migration 10, Configurações |
| 35 Release | pytest → compileall → PyInstaller → Inno Setup → SHA256SUMS → version.json assinado; workflow Windows opcionalmente publica release | `tools/build_release.py`, `GERAR_RELEASE.ps1`, `.github/workflows/release.yml` |
