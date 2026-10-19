"""P2: realistic, isolated clinical UI regression smoke; no production records."""
import json
import os
import sys
import traceback
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["NUTRIDESKTOP_DATA_DIR"] = str(Path("qa-output/isolated-data").resolve())
from PySide6.QtWidgets import QApplication
from nutridesktop.data.database import db
from nutridesktop.data.repositories import (
    PatientRepository, AssessmentRepository, AnamnesisRepository,
    PlanRepository, AgendaRepository, FoodRepository,
)
from nutridesktop.services.app_settings import AppSettings
from nutridesktop.services.reports import _identity
from nutridesktop.ui.main_window import MainWindow
from nutridesktop.ui.refined_patient_dialog import RefinedPatientDialog

OUT = Path("qa-output")
OUT.mkdir(exist_ok=True)
checks = []
def check(name, action):
    try:
        action()
        checks.append({"name": name, "status": "PASS"})
    except Exception as exc:
        checks.append({"name": name, "status": "FAIL", "error": repr(exc), "traceback": traceback.format_exc()})

def require(condition, message):
    if not condition:
        raise AssertionError(message)

db.initialize()
patients = PatientRepository()
assessments = AssessmentRepository()
anamneses = AnamnesisRepository()
plans = PlanRepository()
agenda = AgendaRepository()
food = FoodRepository()
settings = AppSettings(db)
settings.set("clinica_nome", "Consultório Nutri QA")
settings.set("profissional_nome", "Dra. Exemplo QA")
settings.set("profissional_crn", "CRN-TESTE-000")
check("Identidade dos relatórios", lambda: require("Consultório Nutri QA" in _identity(db), "Identidade ausente"))
personas = [
    ("Adulto acompanhamento QA", "F", "1991-06-15", "Reeducação alimentar e acompanhamento longitudinal"),
    ("Infantil crescimento QA", "M", "2022-02-01", "Crescimento infantil e acompanhamento familiar"),
    ("Gestante acompanhamento QA", "F", "1997-03-10", "Acompanhamento materno-infantil"),
    ("Bariátrico acompanhamento QA", "M", "1986-09-20", "Acompanhamento pós-bariátrico"),
    ("SIBO acompanhamento QA", "F", "1993-11-12", "Acompanhamento gastrointestinal"),
]
ids = []
for i, (name, sex, birth, note) in enumerate(personas):
    pid = patients.create(name, sex, birth, f"11999990{i:03d}", f"qa-persona-{i}@example.invalid", note)
    ids.append(pid)
    check(f"Anamnese {name}", lambda pid=pid,note=note: anamneses.save_version(pid, {
        "queixa_principal": note, "rotina": "Trabalho e refeições em horários regulares",
        "recordatorio": "Café: fruta e aveia; almoço: arroz, feijão, legumes e proteína; jantar: sopa",
        "atividade_fisica": "Caminhada 3 vezes por semana",
        "sono": "7-8 horas", "hidratacao": "Aproximadamente 2 litros por dia",
        "alergias": "Nenhuma alergia declarada (dado fictício)",
    }))
    for j in range(3):
        weight = (70 + i*5) + j * (0.8 if i == 2 else -0.6)
        payload = {"data": (date.today()-timedelta(days=(2-j)*30)).isoformat(),
                   "peso": weight, "altura_cm": 165 + i*3,
                   "imc": round(weight/((165+i*3)/100)**2, 2)}
        check(f"Avaliação {name} #{j+1}", lambda pid=pid,payload=payload: assessments.create(pid,payload))
    check(f"Plano {name}", lambda pid=pid,name=name: plans.create(pid,"Plano QA - "+name, 2000, "Cinco refeições; metas individualizadas em consulta"))
    check(f"Consulta {name}", lambda pid=pid,note=note: agenda.create(pid,(date.today()+timedelta(days=3)).isoformat(),"09:30","Retorno",note))
    require(len(assessments.list(pid)) == 3, "Avaliações não persistidas")
    require(len(plans.list(pid)) >= 1, "Plano não persistido")
require(len(patients.list()) == len(personas), "Pacientes não persistidos")

app = QApplication.instance() or QApplication([])
window = MainWindow()
window.resize(1440, 900)
window.show()
app.processEvents()
def screenshot(name, widget):
    app.processEvents()
    target = OUT / "screenshots"
    target.mkdir(exist_ok=True)
    require(widget.grab().save(str(target / (name+".png"))), "Screenshot não foi salva")

for page in ("Dashboard","Pacientes","Agenda","Biblioteca","Configurações","Curvas","Materno-infantil"):
    def open_page(page=page):
        window.show_page(page)
        screenshot("page-"+page.replace("/","-"), window)
    check("Tela "+page, open_page)
for pid, persona in zip(ids, personas):
    def patient_flow(pid=pid, persona=persona):
        dlg = RefinedPatientDialog(pid, window)
        dlg.resize(1280, 850)
        dlg.show()
        app.processEvents()
        names = [dlg.tabs.tabText(i) for i in range(dlg.tabs.count())]
        for expected in ("Resumo","Consulta","Avaliações","Plano alimentar","Evolução","Arquivos"):
            require(expected in names, "Aba clínica ausente: "+expected)
        for i, name in enumerate(names):
            dlg.tabs.setCurrentIndex(i)
            screenshot("patient-"+str(pid)+"-"+str(i)+"-"+name.replace("/","-"), dlg)
        dlg.close()
    check("Prontuário completo "+persona[0], patient_flow)
check("Persistência após reabrir banco", lambda: require(len(PatientRepository().list()) == 5, "Perda de pacientes"))
window.close()
report = {"patients": len(ids), "evaluations": 15, "screenshots": len(list((OUT/"screenshots").glob("*.png"))), "checks": checks}
(OUT/"report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),encoding="utf-8")
print(json.dumps({"total":len(checks),"failed":[x["name"] for x in checks if x["status"]=="FAIL"],"screenshots":report["screenshots"]},ensure_ascii=False))
if any(x["status"]=="FAIL" for x in checks):
    sys.exit(1)
