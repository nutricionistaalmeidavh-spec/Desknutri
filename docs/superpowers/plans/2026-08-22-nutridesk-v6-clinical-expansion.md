# NutriDesk v6 Clinical Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver NutriDesk 6.0 with structured exams, smart pending actions, WhatsApp output, longitudinal comparison, import center, seven clinical packs including SIBO, and selectable visual templates for plans/PDFs.

**Architecture:** Keep clinical data local in SQLite and extend existing repositories/services with focused modules. Clinical packs use a generic activation/record model so multiple specialties can coexist per patient; UI changes remain contextual inside the patient workspace and Library/Settings rather than expanding the main navigation.

**Tech Stack:** Python 3, SQLite, PySide6, fpdf2, pandas/openpyxl-compatible XLSX reading, pytest.

**Spec:** `docs/superpowers/specs/2026-08-22-nutridesk-v6-clinical-expansion-design.md`

## Global Constraints
- Desktop/local-first; no new cloud storage for clinical data.
- APP_VERSION becomes 6.0.0 and SCHEMA_VERSION becomes 13.
- Clinical packs: Materno-infantil, Esportiva, Obesidade/Metabólica, Renal, Bariátrica, Gastrointestinal and SIBO.
- SIBO is documentation/follow-up only; no automated diagnosis.
- WhatsApp is outbound prefilled messaging only.
- Provisional license password remains optional to change.
- Existing database data and existing text templates must remain compatible.

---

### Task 1: Schema 13 and core repositories

**Files:**
- Modify: `nutridesktop/version.py`
- Modify: `nutridesktop/data/migrations.py`
- Modify: `nutridesktop/data/repositories.py`
- Test: `tests/test_v6_clinical_expansion.py`

**Interfaces:**
- Produces `LabRepository`, `ClinicalPackRepository`, `PendingActionRepository`, `ImportHistoryRepository`.
- Existing repositories remain source-compatible.

- [ ] Write failing tests that initialize schema 13 and exercise creating/listing lab results, activating multiple packs, storing pack records, and manual pending actions.
- [ ] Run `pytest tests/test_v6_clinical_expansion.py -q` and confirm failures are caused by missing schema/classes.
- [ ] Add schema 13 tables/indexes and version bump.
- [ ] Add the four repositories with transactional writes and timeline/audit events where patient-facing.
- [ ] Re-run targeted tests and full suite.

### Task 2: Laboratory trends and longitudinal comparator

**Files:**
- Create: `nutridesktop/services/labs.py`
- Create: `nutridesktop/services/longitudinal.py`
- Test: `tests/test_v6_clinical_expansion.py`

**Interfaces:**
- `flag_result(value, ref_min, ref_max) -> str`
- `marker_series(patient_id, marker, repo=None) -> list[dict]`
- `build_patient_comparison(patient_id, database=None) -> dict`

- [ ] Write failing tests for low/normal/high lab flags, ordered marker series and comparison payload containing assessment/lab/consultation/plan dates.
- [ ] Verify RED.
- [ ] Implement minimal services without diagnostic interpretation.
- [ ] Verify GREEN and regression suite.

### Task 3: Smart pending actions

**Files:**
- Create: `nutridesktop/services/pending_actions.py`
- Modify: `nutridesktop/data/repositories.py`
- Test: `tests/test_v6_clinical_expansion.py`

**Interfaces:**
- `collect_pending_actions(database=None, today=None) -> list[dict]`
- Each action contains `kind`, `patient_id`, `patient_name`, `title`, `detail`, `severity`, `entity_id`.

- [ ] Write failing tests for plan-not-sent, no-future-return, stale-assessment, lab-review and manual action.
- [ ] Verify RED.
- [ ] Implement derived rules with duplicate suppression.
- [ ] Verify GREEN and full suite.

### Task 4: WhatsApp output service

**Files:**
- Create: `nutridesktop/services/whatsapp.py`
- Test: `tests/test_v6_clinical_expansion.py`

**Interfaces:**
- `normalize_br_phone(phone) -> str`
- `build_whatsapp_url(phone, message) -> str`
- `message_for(kind, patient_name, context=None) -> str`

- [ ] Write failing tests for BR phone normalization, URL encoding, and four message presets.
- [ ] Verify RED.
- [ ] Implement pure functions only; opening browser remains UI responsibility.
- [ ] Verify GREEN.

### Task 5: Import center

**Files:**
- Create: `nutridesktop/services/import_center.py`
- Modify: `nutridesktop/data/repositories.py`
- Test: `tests/test_v6_import_center.py`

**Interfaces:**
- `preview_import(kind, path, database=None) -> ImportPreview`
- `apply_import(preview, database=None) -> dict`
- `ImportPreview` exposes normalized rows, errors, skipped duplicates and source metadata.

- [ ] Write failing CSV tests for patient import, duplicate skip, assessment import and lab-result import.
- [ ] Add an XLSX test guarded by pandas/openpyxl availability.
- [ ] Verify RED.
- [ ] Implement alias mapping, preview validation and transactional apply with import history.
- [ ] Verify GREEN and full suite.

### Task 6: Clinical pack definitions and helpers

**Files:**
- Create: `nutridesktop/clinical/packs.py`
- Create: `nutridesktop/services/clinical_packs.py`
- Modify: `nutridesktop/clinical/maternal.py`
- Test: `tests/test_v6_clinical_packs.py`

**Interfaces:**
- `PACK_DEFINITIONS` keyed by stable slug.
- `pack_defaults(slug) -> dict`
- `save_pack_snapshot(patient_id, slug, data, date=None, repo=None) -> int`
- `latest_pack_snapshot(patient_id, slug, repo=None) -> dict | None`

- [ ] Write failing tests asserting all seven pack slugs and required fields, including SIBO non-diagnostic status values.
- [ ] Write tests for maternal gestational-weight tracking helper and GI Bristol/SIBO symptom score normalization.
- [ ] Verify RED.
- [ ] Implement definitions/helpers and preserve unknown JSON keys.
- [ ] Verify GREEN.

### Task 7: Template library and richer PDF rendering

**Files:**
- Modify: `nutridesktop/data/migrations.py`
- Modify: `nutridesktop/data/repositories.py`
- Modify: `nutridesktop/services/templates.py`
- Modify: `nutridesktop/services/reports.py`
- Create: `nutridesktop/services/plan_documents.py`
- Test: `tests/test_v6_templates_reports.py`

**Interfaces:**
- Template repository accepts `style_key`, `specialty_tags`, `is_default`.
- `set_default(template_id, typ)` guarantees at most one active default per type.
- `generate_plan_pdf(patient_id, plan_id, destination, template_id=None, database=None)`.

- [ ] Write failing tests for seeded visual templates, default selection and legacy-template compatibility.
- [ ] Write a PDF smoke test verifying generated file and selected template title/style metadata path.
- [ ] Verify RED.
- [ ] Add migration metadata columns safely within schema 13 and implement repository/service behavior.
- [ ] Implement styled plan PDF with meal sections, recipes/substitutions and professional identity.
- [ ] Verify GREEN and full suite.

### Task 8: Desktop UI integration

**Files:**
- Modify: `nutridesktop/ui/main_window.py`
- Modify: `nutridesktop/ui/patient_dialog.py`
- Modify: `nutridesktop/ui/view_models.py`
- Create: `nutridesktop/ui/labs_dialog.py`
- Create: `nutridesktop/ui/clinical_packs_dialog.py`
- Create: `nutridesktop/ui/import_dialog.py`
- Test: `tests/test_v6_ui_contract.py`

**Interfaces:**
- Dashboard consumes `collect_pending_actions`.
- Patient dialog exposes Exams, Clinical Packs, Longitudinal Comparison and WhatsApp actions.
- Library exposes Import Center and richer Templates.
- Settings > Reports exposes default-template selectors.

- [ ] Write failing static UI contract tests for new labels/classes/actions.
- [ ] Verify RED.
- [ ] Add dialogs and contextual patient controls without adding specialty pages to main navigation.
- [ ] Add WhatsApp open action using `QDesktopServices.openUrl`.
- [ ] Replace dashboard plan-only alert with smart pending actions.
- [ ] Verify static contract tests, `compileall`, and full non-Qt suite.

### Task 9: Documentation, manifest and clean-package verification

**Files:**
- Modify: `CHANGELOG.md`
- Create: `README_V6_CLINICAL.md`
- Create: `MATRIZ_V6_EXPANSAO_CLINICA.md`
- Create: `RELATORIO_VERIFICACAO_V6.md`
- Regenerate: `MANIFEST_SHA256.txt`

**Interfaces:** none.

- [ ] Document schema 13, new modules, clinical limitations and upgrade behavior.
- [ ] Run `pytest -q`.
- [ ] Run `python -m compileall -q nutridesktop app.py`.
- [ ] Build a ZIP, extract it into a clean directory, run tests from the extracted package and verify manifest hashes.
- [ ] Record exact pass/skip counts and ZIP SHA-256.
