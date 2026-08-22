# NutriDesk v6 Clinical Expansion Design

## Goal
Transform NutriDesk 5.0 into a stronger longitudinal clinical workspace by adding structured laboratory exams, smart pending actions, WhatsApp output, migration/import tools, specialized clinical packs, richer longitudinal comparison, and selectable visual templates for plans/PDFs.

## Product rules
- Keep the desktop/local-first architecture. Clinical data remains in local SQLite.
- Do not create a separate main-menu page for every specialty. Specialized packs live inside the patient workspace.
- A patient may activate multiple clinical packs simultaneously.
- SIBO is a documentation/follow-up pack; NutriDesk must not diagnose it automatically.
- WhatsApp is an outbound convenience layer using prefilled messages/links; no CRM/chat history sync is required in v6.
- The provisional license password remains optional to change.
- Reuse existing patient, consultation, assessment, plan, recipe, document and timeline data rather than duplicating them.

## A. Structured laboratory exams
Add a longitudinal laboratory subsystem with exam panels and individual markers. Each result stores collection date, marker name, numeric/text value, unit, optional reference range, flag and notes. NutriDesk can group results by panel (e.g. metabolic, renal, micronutrients) and compare the same marker over time.

The system must show trends but not infer diagnoses. Reference-range flags are simple comparisons when numeric limits are supplied.

## B. Longitudinal clinical comparator
Create one patient-level comparison service that aligns assessment metrics, laboratory markers, consultation context, plan versions and specialty follow-up data by date. The UI exposes a compact comparator inside the patient workspace with selectable dates and categories.

## C. Smart pending actions
Generalize the existing "plan not sent" logic into a pending-actions service. Initial rules:
- latest completed consultation with plan not sent;
- return expected/consultation completed but no future appointment;
- stale assessment (default >90 days, configurable later);
- active specialty follow-up with missing required checkpoint when applicable;
- laboratory result marked for review.

Pending actions are derived from data where possible; manual actions are stored in a small task table. The dashboard shows counts and lets the user open the patient.

## D. WhatsApp output
Provide safe message builders for:
- send plan notification;
- remind return/appointment;
- request missing exam/result;
- generic follow-up.

Messages open WhatsApp Web/Desktop through a generated URL using the patient's phone number. NutriDesk does not claim message delivery and does not store external chat content.

## E. Migration/import center
Add import support for:
- patients CSV;
- assessments CSV;
- laboratory results CSV;
- generic patient export spreadsheet (XLSX/CSV) with mapping by common aliases.

Every import runs in preview mode first, reports valid/invalid/skipped rows, and writes an import-history record. Duplicate patient detection uses normalized name + birth date and email/phone when available.

## F. Clinical packs
Packs are activated per patient and store structured data in generic JSON records plus pack-specific helpers. v6 packs:

### Materno-infantil
- gestational age/DPP and pre-gestational weight/height;
- gestational weight-gain tracking;
- lactation status;
- child growth/WHO linkage;
- introduction-feeding stage and feeding notes;
- mother/child relationship metadata when both are patients.

### Sports
- sport/modality;
- training frequency, volume and schedule;
- pre/intra/post strategy notes;
- hydration target;
- performance/body-composition goals.

### Obesity/Metabolic
- metabolic diagnoses/conditions recorded by professional;
- glycemic/lipid/blood-pressure follow-up markers;
- weight/composition targets;
- lifestyle barriers and goals.

### Renal
- kidney condition/stage recorded by professional;
- protein, sodium, potassium, phosphorus and fluid targets;
- renal-lab panel linkage.

### Bariatric
- pre/post-op state and surgery date/type;
- food consistency phase;
- supplement checklist;
- intolerance/symptom log;
- micronutrient follow-up.

### Gastrointestinal
- symptom log;
- Bristol scale;
- bowel frequency;
- reflux/constipation/diarrhea/intolerance fields;
- FODMAP phase and food-symptom notes.

### SIBO
- status recorded as suspected/referred/confirmed-by-external-record/resolved;
- subtype recorded if documented by the professional;
- external test/treatment notes;
- diet phase, trigger/reintroduction notes and symptom score;
- longitudinal follow-up only, no automated diagnosis.

## G. Template library and prettier plans/PDFs
Extend document templates with:
- category/type;
- visual style key;
- active/default flag per document type;
- specialty tags;
- preview metadata.

Seed several local built-in styles such as Clean Clinical, Minimal, Modern Teal and Materno-infantil. The nutritionist can choose a default for Plan, Report, Orientation and Recipe while still overriding it at generation time.

Plan PDFs should render meal sections, item quantities, optional substitutions/recipes, footer identity and selected accent style. Existing free-text templates remain compatible.

## UI placement
- Main menu remains Dashboard, Patients, Agenda, Library, Account, Settings.
- Patient workspace gains sections/tabs: Summary, Consultation, Assessments, Plan, Evolution, Files, plus contextual "Clinical packs" and "Exams" panels.
- Library gains Recipes, Templates, Protocols and Import Center.
- Settings > Reports gains default-template selection.
- Dashboard Alerts uses the smart pending-actions service.

## Data model
Schema version 13 adds:
- lab_panels
- lab_results
- patient_clinical_packs
- clinical_pack_records
- manual_pending_actions
- import_history
- template metadata columns/default constraints

No cloud schema changes are required for clinical data.

## Error handling
- Imports are transactional and provide row-level validation summaries.
- WhatsApp requires a valid patient phone and otherwise shows a friendly error.
- Lab range comparison tolerates text/non-numeric results.
- Clinical-pack JSON must remain readable after future extensions; unknown keys are preserved.

## Testing
- Repository/service tests first for schema, labs, packs, pending actions, import, WhatsApp URL generation and templates.
- Static UI contract tests for PySide6 source because the current runtime lacks PySide6.
- Full existing suite must remain green.
- compileall must pass.
