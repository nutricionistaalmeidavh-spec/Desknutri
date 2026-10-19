"""Read-only screenshot capture for comparing released NutriDesk desktop UI."""
import os,sys,traceback
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
root=Path.cwd()
sys.path.insert(0,str(root))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from nutridesktop.data.database import db
from nutridesktop.ui.application_window import MainWindow
out=Path(os.environ["SCREENSHOT_DIR"]).resolve();out.mkdir(parents=True,exist_ok=True)
db.initialize()
from nutridesktop.data.repositories import PatientRepository
qa_patients=PatientRepository()
if not qa_patients.list():
    qa_patients.create('Paciente QA Adulto','F','1991-06-15')
    qa_patients.create('Paciente QA Infantil','M','2022-02-01')
app=QApplication([])
window=MainWindow()
window.resize(1440,900)
window.show()
app.processEvents()
def shot(name,widget):
    app.processEvents()
    widget.grab().save(str(out/(name+".png")))
    print("CAPTURED",name,flush=True)
for page in ("Dashboard","Pacientes","Agenda","Biblioteca","Configurações"):
    try:
        window.show_page(page);app.processEvents();shot(page,window)
        if page=="Configurações":
            tabs=getattr(window,"settings_tabs",None)
            if tabs:
                for i in range(tabs.count()):
                    tabs.setCurrentIndex(i);shot("Config-"+tabs.tabText(i).replace("/","-"),window)
    except Exception as e:print("ERROR",page,repr(e),flush=True);traceback.print_exc()
try:
    from nutridesktop.ui.refined_patient_dialog import RefinedPatientDialog
    for patient in qa_patients.list():
        dialog=RefinedPatientDialog(int(patient['id']),window)
        dialog.show();app.processEvents()
        for i in range(dialog.tabs.count()):
            dialog.tabs.setCurrentIndex(i);app.processEvents()
            shot('Prontuario-'+str(patient['id'])+'-'+dialog.tabs.tabText(i),dialog)
        dialog.close()
except Exception as e:print("ERROR patient",repr(e),flush=True);traceback.print_exc()
window.close()
print("TOTAL_PNG",len(list(out.glob("*.png"))),flush=True)
