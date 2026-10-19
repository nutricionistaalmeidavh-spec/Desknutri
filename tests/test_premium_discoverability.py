"""Regression checks for restored Premium discoverability."""
from nutridesktop.ui.view_models import NAV_GROUPS
from nutridesktop.ui.main_window import MainWindow

def test_premium_navigation_entries():
    entries=[name for group in NAV_GROUPS.values() for name in group]
    for name in ('Consultas','Avaliações','Planos','Orientações','Curvas','Materno-infantil','Bariátrica','SIBO'):
        assert name in entries
    assert len(entries)==len(set(entries))

def test_clinic_settings_persist_across_reopening(monkeypatch,tmp_path):
    from PySide6.QtWidgets import QApplication
    app=QApplication.instance() or QApplication([])
    from nutridesktop.data.database import db
    db.initialize()
    w=MainWindow()
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
    from nutridesktop.services.reports import _identity
    assert 'Clínica QA' in _identity(w.pr.db)
    assert any('Profissional QA' in x for x in _identity(w.pr.db))
    w.close()
