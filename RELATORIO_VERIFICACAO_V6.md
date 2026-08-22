# Verificação NutriDesk 6.0

## Escopo verificado
- migração SQLite 12 → 13;
- criação das novas tabelas e colunas de template;
- exames estruturados;
- packs clínicos;
- comparação longitudinal;
- pendências inteligentes;
- WhatsApp;
- importação CSV/XLSX;
- templates visuais;
- planos PDF e substituições;
- receitas enriquecidas;
- contratos estáticos da UI.

## Evidências da execução
- `pytest -q`: 82 passed, 1 skipped.
- `python -m compileall -q nutridesktop app.py`: sucesso.
- migration smoke: schema 12 antes, schema 13 depois.
- novas tabelas verificadas: lab_panels, lab_results, patient_clinical_packs, clinical_pack_records, plano_substituicoes, manual_pending_actions e import_history.
- novas colunas de document_templates verificadas: style_key, specialty_tags, is_default e preview_json.

## Skip
O único skip é o teste WHO condicionado à dependência/ambiente já existente nas versões anteriores.

## Limitação
PySide6 não está instalado no runtime desta sessão; por isso as janelas Qt não foram abertas. A camada UI foi validada por testes de contrato estático e `compileall`. Recomenda-se smoke test visual no Windows antes do instalador final.
