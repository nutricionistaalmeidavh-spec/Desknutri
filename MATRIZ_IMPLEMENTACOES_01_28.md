# Matriz de implementação — NutriDesktop v2.0

| Item | Resultado implementado | Evidência principal |
|---:|---|---|
| 1 | Backup inclui banco, documentos e fotos | `nutridesktop/services/backup.py` |
| 2 | Documentos copiados para armazenamento gerenciado + migração legada | `nutridesktop/services/documents.py` |
| 3 | Snapshot SQLite, manifest, SHA-256, staging, validação e rollback | `nutridesktop/services/backup.py` |
| 4 | Licença Ed25519 com chave privada fora do app | `nutridesktop/services/licensing.py`, `tools/license_admin.py` |
| 5 | Configuração comercial externa | `nutridesktop/core/config.py`, `config/commercial.example.json` |
| 6 | PIN scrypt, auto-lock, backup criptografado e EFS opcional | `core/security.py`, `services/security_settings.py`, `services/local_protection.py` |
| 7 | WHO 2006/2007 via referência LMS do `pygrowthstandards` | `clinical/growth.py`, `services/growth.py` |
| 8 | Testes clínicos automatizados | `tests/test_clinical.py` |
| 9 | UI separada em módulos | `nutridesktop/ui/` |
| 10 | Camada de repositories | `nutridesktop/data/repositories.py` |
| 11 | Migrations versionadas/aditivas 1→8 | `nutridesktop/data/migrations.py` |
| 12 | Edição de paciente | `PatientRepository.update`, `ui/patient_dialog.py` |
| 13 | Revisões/snapshots de avaliações + audit log | `AssessmentRepository.update_versioned` |
| 14 | Validação centralizada | `nutridesktop/core/validation.py` |
| 15 | Log técnico rotativo/redigido | `nutridesktop/core/logging_setup.py` |
| 16 | Captura global de exceções | `nutridesktop/core/exceptions.py` |
| 17 | Testes de banco, migrations e fluxos | `tests/test_database.py`, `tests/test_backup.py` |
| 18 | Timeline longitudinal | `TimelineRepository`, `ui/patient_dialog.py` |
| 19 | Gráficos de peso, IMC, gordura, massa magra e cintura | `services/charts.py`, `ui/patient_dialog.py` |
| 20 | Metas macro/micro, alertas e distribuição do VET | `services/plans.py`, `ui/patient_dialog.py` |
| 21 | Substituições por equivalência energética/proteica | `services/plans.py::substitute` |
| 22 | Versões de plano preservando histórico | `PlanRepository.create_revision` |
| 23 | Receita composta adicionável ao plano por porção | `RecipeRepository`, `services/plans.py` |
| 24 | DRI por infância, adolescência, adulto, idoso, gestante e lactante | `clinical/dri_lifecycle.py` |
| 25 | Protocolos clínicos imutáveis por versão | `ProtocolRepository`, `ui/main_window.py` |
| 26 | Relatório completo selecionável com identidade/anamnese/evolução/plano/timeline | `services/reports.py`, `ui/patient_dialog.py` |
| 27 | Templates editáveis para avaliação/plano/orientação/receita/encaminhamento/evolução/relatório | `services/templates.py`, `ui/main_window.py` |
| 28 | Agenda com tipo, retorno, observações, duração, status, filtro e recorrência materializada | `AgendaRepository`, `ui/main_window.py` |
