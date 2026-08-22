# NutriDesk UX P0-P2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernizar UI e fluxos clínicos do NutriDesk até P2, preservando o motor existente e a troca opcional da senha provisória.

**Architecture:** Introduzir uma camada visual reutilizável e view-models puros, manter repositórios/serviços clínicos, adicionar apenas estado mínimo de consulta para plano enviado e montar novos fluxos Qt sobre os serviços existentes.

**Tech Stack:** Python 3, PySide6, SQLite, pytest, matplotlib.

**Spec:** `docs/superpowers/specs/2026-08-22-nutridesk-ux-p0-p2-design.md`

## Global Constraints
- Senha provisória continua opcional de trocar.
- Marca visual é “NutriDesk”.
- Persistência local e licenciamento online atual não podem regredir.
- Novo schema: 12.

---

### Task 1: Modelo de dados e view-models de UX
**Files:** `nutridesktop/version.py`, `nutridesktop/data/migrations.py`, `nutridesktop/data/repositories.py`, criar `nutridesktop/ui/view_models.py`, testar em `tests/test_ux_v5.py`.
- [ ] RED: testes de idade, nav agrupada e pendência de plano.
- [ ] Verificar falha esperada.
- [ ] GREEN: migration 12, consultas enriquecidas e view-models.
- [ ] Rodar testes focados e suite.

### Task 2: Design system e navegação/dashboard
**Files:** criar `nutridesktop/ui/design_system.py`, modificar `main_window.py`, `p3_main_window.py`, `v4_main_window.py`.
- [ ] RED: testes Qt de branding, nav e cards/atalhos.
- [ ] Verificar falha.
- [ ] GREEN: aplicar shell moderno, grupos e dashboard clínico.
- [ ] Rodar testes.

### Task 3: Cadastro/paciente e fluxo Nova consulta
**Files:** criar `nutridesktop/ui/consultation_dialog.py`, modificar `main_window.py`, `patient_dialog.py`.
- [ ] RED: QDateEdit/sexo, tabs do workspace, criação de consulta.
- [ ] Verificar falha.
- [ ] GREEN: wizard e workspace do paciente.
- [ ] Rodar testes.

### Task 4: Plano alimentar e contextos clínicos
**Files:** `patient_dialog.py`, `main_window.py`.
- [ ] RED: seleção explícita de alimento e acesso contextual WHO/Materno.
- [ ] Verificar falha.
- [ ] GREEN: editor por refeição, busca com resultados e painéis contextuais.
- [ ] Rodar testes.

### Task 5: Agenda, configurações e UX P2
**Files:** `main_window.py`, `p3_main_window.py`, `v4_main_window.py`, `common.py`.
- [ ] RED: calendário, configuração agrupada, erro amigável.
- [ ] Verificar falha.
- [ ] GREEN: calendário + abas de configurações + mensagens/empty states.
- [ ] Rodar testes.

### Task 6: Verificação e empacotamento
**Files:** `CHANGELOG.md`, `README_V5_UX.md`, `MANIFEST_SHA256.txt`.
- [ ] Rodar suite completa.
- [ ] Smoke test Qt offscreen.
- [ ] Validar migração 11→12.
- [ ] Gerar ZIP cumulativo e SHA-256.
