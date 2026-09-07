from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Isolated demo profile: never touches the user's production/local database.
os.environ.setdefault("NUTRIDESKTOP_DATA_DIR", str(Path.cwd() / ".video-demo-data"))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from nutridesktop.data.database import db
from nutridesktop.data.repositories import TemplateRepository, ProtocolRepository
from nutridesktop.data.seed import seed_taco, seed_legacy_content
from nutridesktop.services.templates import seed as seed_templates
from nutridesktop.clinical.protocols import seed as seed_protocols
from nutridesktop.ui.v4_main_window import V4MainWindow
from nutridesktop.ui_kit import ThemeManager


def seed_demo_data() -> None:
    db.initialize()
    seed_taco()
    seed_legacy_content()
    seed_templates(TemplateRepository())
    seed_protocols(ProtocolRepository())

    today = date.today()
    with db.connect() as c:
        c.executescript(
            """
            DELETE FROM manual_pending_actions;
            DELETE FROM consultas;
            DELETE FROM avaliacoes;
            DELETE FROM planos;
            DELETE FROM pacientes;
            """
        )
        patients = [
            ("Ana Carolina Silva", "F", "1998-04-12", "(16) 99120-1840", "ana@example.com", "Objetivo: redução de gordura e melhora de composição corporal."),
            ("Mariana Costa", "F", "1991-11-03", "(16) 99820-7701", "mariana@example.com", "Acompanhamento esportivo e performance."),
            ("Carlos Henrique Lima", "M", "1985-07-21", "(16) 99244-6220", "carlos@example.com", "Reeducação alimentar e controle metabólico."),
            ("Beatriz Alves", "F", "2002-02-16", "(16) 99710-3118", "beatriz@example.com", "Plano alimentar para rotina universitária."),
        ]
        c.executemany(
            "INSERT INTO pacientes(nome,sexo,data_nascimento,telefone,email,observacoes) VALUES(?,?,?,?,?,?)",
            patients,
        )
        ids = [r[0] for r in c.execute("SELECT id FROM pacientes ORDER BY id")]
        evals = [
            (ids[0], (today-timedelta(days=60)).isoformat(), 71.6, 167, 25.7, 24.6, 86, 17.6, 54.0),
            (ids[0], (today-timedelta(days=30)).isoformat(), 69.9, 167, 25.1, 22.9, 82, 16.0, 53.9),
            (ids[0], today.isoformat(), 68.8, 167, 24.7, 21.5, 79, 14.7, 54.1),
            (ids[1], today.isoformat(), 62.4, 165, 22.9, 20.8, 72, 13.0, 49.4),
        ]
        c.executemany(
            "INSERT INTO avaliacoes(paciente_id,data,peso,altura_cm,imc,pg_final,cintura,massa_gorda,massa_magra) VALUES(?,?,?,?,?,?,?,?,?)",
            evals,
        )
        plans = [
            (ids[0], "Plano alimentar - Agosto", today.isoformat(), 1850, "Distribuição em 5 refeições", "Ativo"),
            (ids[1], "Performance - Treinos", today.isoformat(), 2300, "Ajuste para dias de treino", "Ativo"),
            (ids[2], "Controle metabólico", today.isoformat(), 2000, "Foco em fibras e regularidade", "Ativo"),
        ]
        c.executemany(
            "INSERT INTO planos(paciente_id,nome,data,vet_meta,observacoes,status) VALUES(?,?,?,?,?,?)",
            plans,
        )
        consultations = [
            (ids[0], today.isoformat(), "08:30", "Agendada", "Consulta", 60, "Redução de gordura", "Reavaliação"),
            (ids[1], today.isoformat(), "10:00", "Agendada", "Retorno", 45, "Performance", "Ajuste do plano"),
            (ids[2], today.isoformat(), "14:30", "Agendada", "Consulta", 60, "Controle metabólico", "Avaliação inicial"),
            (ids[3], (today+timedelta(days=2)).isoformat(), "09:00", "Agendada", "Retorno", 45, "Organização alimentar", "Acompanhamento"),
            (ids[0], (today+timedelta(days=5)).isoformat(), "16:00", "Agendada", "Retorno", 45, "Redução de gordura", "Revisão de metas"),
        ]
        c.executemany(
            "INSERT INTO consultas(paciente_id,data,hora,status,tipo,duracao_min,objetivo,abordagem) VALUES(?,?,?,?,?,?,?,?)",
            consultations,
        )
        c.execute(
            "INSERT INTO manual_pending_actions(paciente_id,kind,title,detail,severity,due_date) VALUES(?,?,?,?,?,?)",
            (ids[0], "follow_up", "Revisar evolução corporal", "Comparar medidas e ajustar meta para o próximo retorno.", "media", today.isoformat()),
        )
        c.execute(
            "INSERT INTO manual_pending_actions(paciente_id,kind,title,detail,severity,due_date) VALUES(?,?,?,?,?,?)",
            (ids[2], "lab_review", "Revisar exames laboratoriais", "Painel recente aguardando revisão clínica.", "alta", today.isoformat()),
        )
        c.commit()


def main() -> int:
    seed_demo_data()
    app = QApplication(sys.argv)
    theme_manager = ThemeManager(app)
    app.setProperty("theme_manager", theme_manager)
    theme_manager.apply()

    win = V4MainWindow()
    win.showMaximized()

    # Real application pages, navigated by the application's own show_page flow.
    # The first seconds remain on Dashboard so Chromium/noVNC can connect cleanly.
    sequence = [
        (0, "Dashboard"),
        (7000, "Pacientes"),
        (11300, "Agenda"),
        (15600, "Alimentos"),
        (19900, "Crescimento WHO"),
        (24200, "Materno-infantil"),
        (28500, "Receitas"),
        (32800, "Templates"),
        (37100, "Protocolos"),
        (41400, "Exportações"),
        (45700, "Configurações"),
        (50000, "Dashboard"),
    ]
    for delay, page in sequence:
        QTimer.singleShot(delay, lambda p=page: win.show_page(p))

    QTimer.singleShot(65000, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
