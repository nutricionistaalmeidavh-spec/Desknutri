from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication,QMessageBox,QInputDialog
from nutridesktop.data.database import db
from nutridesktop.data.repositories import TemplateRepository,ProtocolRepository
from nutridesktop.data.seed import seed_taco,seed_legacy_content
from nutridesktop.services.templates import seed as seed_templates
from nutridesktop.clinical.protocols import seed as seed_protocols
from nutridesktop.core.logging_setup import configure_logging
from nutridesktop.core.exceptions import install_exception_hook
from nutridesktop.services.security_settings import SecuritySettings
from nutridesktop.services.documents import DocumentService
from nutridesktop.ui.main_window import PinDialog
from nutridesktop.ui.account_dialog import AccountActivationDialog
from nutridesktop.ui.v4_main_window import V4MainWindow as MainWindow
from nutridesktop.services.account_licensing import AccountLicenseService,AccountLicenseError
from nutridesktop.services import licensing
from nutridesktop.ui_kit import ThemeManager


def _ensure_license(log) -> bool:
    account=AccountLicenseService()
    current=licensing.current(db)
    # Licenças antigas assinadas continuam válidas durante a migração.
    if current and not current.get('server_managed'):
        return True
    if account.configured():
        if current:
            try:account.refresh_if_due()
            except AccountLicenseError as e:
                # Falha de internet não derruba uma autorização offline ainda válida.
                if e.code!='offline':log.warning('Falha ao renovar licença de conta: %s',e)
            return licensing.current(db) is not None
        # Se já existe token do dispositivo, tenta renovar sem pedir senha.
        if account.state().has_device_token:
            try:
                account.refresh();return True
            except AccountLicenseError as e:
                if e.code=='offline':
                    QMessageBox.warning(None,'Licença','A autorização offline expirou e não foi possível acessar o servidor de licenças. Conecte-se à internet e tente novamente.')
                    return False
        dlg=AccountActivationDialog(account)
        return dlg.exec()==AccountActivationDialog.Accepted and licensing.current(db) is not None
    # Compatibilidade com o licenciamento assinado manual anterior.
    if any(p.exists() for p in licensing.PUBLIC_KEY_LOCATIONS):
        if current:return True
        key,ok=QInputDialog.getMultiLineText(None,'Ativação','Cole a licença assinada:')
        if not ok:return False
        try:licensing.activate(key);return True
        except Exception as e:QMessageBox.critical(None,'Licença',str(e));return False
    log.warning('Public license key/server not configured; source/development mode.')
    return True


def main():
    if '--healthcheck' in sys.argv:
        try:
            db.initialize()
            with db.connect() as c:ok=c.execute('PRAGMA integrity_check').fetchone()[0]
            return 0 if ok=='ok' else 2
        except Exception:return 3
    log=configure_logging();db.initialize();seed_taco();seed_legacy_content();DocumentService().migrate_legacy_documents();seed_templates(TemplateRepository());seed_protocols(ProtocolRepository())
    app=QApplication(sys.argv)
    theme_manager=ThemeManager(app);app.setProperty('theme_manager',theme_manager);theme_manager.apply()
    install_exception_hook(lambda t,m:QMessageBox.critical(None,t,m))
    sec=SecuritySettings();row=sec.get()
    if row and row['pin_hash']:
        if PinDialog(sec).exec()!=PinDialog.Accepted:return 1
    try:
        if not _ensure_license(log):return 1
    except Exception:
        log.exception('License initialization failed');QMessageBox.critical(None,'Licença','Não foi possível inicializar a licença.');return 1
    win=MainWindow();win.show();return app.exec()
if __name__=='__main__':raise SystemExit(main())
