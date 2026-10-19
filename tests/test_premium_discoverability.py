"""Regression checks for restored Premium discoverability."""
from nutridesktop.ui.view_models import NAV_GROUPS
from nutridesktop.ui.main_window import MainWindow

def test_premium_navigation_entries():
    entries=[name for group in NAV_GROUPS.values() for name in group]
    for name in ('Consultas','Avaliações','Planos','Orientações','Curvas','Materno-infantil'):
        assert name in entries
    assert len(entries)==len(set(entries))

def test_clinic_settings_persist_across_reopening(qtbot,monkeypatch,tmp_path):
    from PySide6.QtCore import QSettings
    QSettings.setDefaultFormat(QSettings.IniFormat)
    QSettings.setPath(QSettings.IniFormat,QSettings.UserScope,str(tmp_path))
    w=MainWindow()
    qtbot.addWidget(w)
    w.show_page('Configurações')
    fields=w.clinic_fields
    fields['nome'].setText('Clínica QA')
    fields['profissional'].setText('Profissional QA')
    monkeypatch.setattr('nutridesktop.ui.main_window.QMessageBox.information',lambda *args:None)
    w.save_clinic_profile()
    w.pages.pop('Configurações')
    w.show_page('Configurações')
    assert w.clinic_fields['nome'].text()=='Clínica QA'
    assert w.clinic_fields['profissional'].text()=='Profissional QA'
    w.close()
