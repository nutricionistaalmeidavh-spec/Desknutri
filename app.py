from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication,QMessageBox
from nutridesktop.data.database import db
from nutridesktop.data.repositories import TemplateRepository,ProtocolRepository
from nutridesktop.data.seed import seed_taco,seed_legacy_content,seed_demo_patient
from nutridesktop.services.templates import seed as seed_templates
from nutridesktop.clinical.protocols import seed as seed_protocols
from nutridesktop.core.logging_setup import configure_logging
from nutridesktop.core.exceptions import install_exception_hook
from nutridesktop.services.security_settings import SecuritySettings
from nutridesktop.services.documents import DocumentService
from nutridesktop.ui.main_window import PinDialog
from nutridesktop.ui.application_window import MainWindow
from nutridesktop.ui_kit import ThemeManager
from nutridesktop.services.update_service import UpdateService


def main():
    if '--healthcheck' in sys.argv:
        try:
            db.initialize()
            with db.connect() as c:ok=c.execute('PRAGMA integrity_check').fetchone()[0]
            return 0 if ok=='ok' else 2
        except Exception:return 3
    log=configure_logging()
    try:
        db.initialize()
        # Check target version and SQLite integrity before changing clinical records.
        UpdateService().complete_pending_update()
    except Exception as exc:
        log.exception("Falha de integridade após atualização")
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None, "NutriDesk — recuperação",
            "A atualização não passou na verificação do banco. "
            "Nenhuma restauração automática foi executada.\n\n"
            f"{exc}\n\nPreserve os arquivos clínicos e o backup pré-atualização para recuperação."
        )
        return 2
    seed_taco();seed_legacy_content();seed_demo_patient();DocumentService().migrate_legacy_documents();seed_templates(TemplateRepository());seed_protocols(ProtocolRepository())
    app=QApplication(sys.argv)
    theme_manager=ThemeManager(app);app.setProperty('theme_manager',theme_manager);theme_manager.apply()
    install_exception_hook(lambda t,m:QMessageBox.critical(None,t,m))
    sec=SecuritySettings();row=sec.get()
    if row and row['pin_hash']:
        if PinDialog(sec).exec()!=PinDialog.Accepted:return 1
    win=MainWindow();win.show();return app.exec()
if __name__=='__main__':raise SystemExit(main())
