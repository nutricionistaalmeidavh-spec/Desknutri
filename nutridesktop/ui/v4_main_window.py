from __future__ import annotations
from datetime import date
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QMessageBox,QInputDialog,QApplication
from .p3_main_window import P3MainWindow
from .account_dialog import AccountActivationDialog
from .common import button,show_error
from nutridesktop.services.account_licensing import AccountLicenseService
from nutridesktop.services import licensing

class V4MainWindow(P3MainWindow):
    NAV=['Dashboard','Pacientes','Agenda','Alimentos','Crescimento WHO','Materno-infantil','Receitas','Templates','Protocolos','Conta','Atualizações','Exportações','Suporte','Configurações']
    def __init__(self):self.account_license=AccountLicenseService();super().__init__()
    def show_page(self,name):
        if name=='Conta':
            self.lock.touch()
            if name in self.pages:self.stack.removeWidget(self.pages[name]);self.pages[name].deleteLater();del self.pages[name]
            w=self.account_page();self.pages[name]=w;self.stack.addWidget(w);self.stack.setCurrentWidget(w);return
        return super().show_page(name)
    def account_page(self):
        w,v=self.page('Conta','Sua licença e este computador. Configurações técnicas do servidor são gerenciadas pelo NutriDesk.');st=self.account_license.state();lic=licensing.current()
        v.addWidget(QLabel(f"E-mail: {st.email or 'não ativado'}"));v.addWidget(QLabel(f"Plano: {(lic or {}).get('plan','—')}"));v.addWidget(QLabel(f"Licença válida até: {(lic or {}).get('expires','—')}"));v.addWidget(QLabel(f"Computador: {licensing.machine_id()}"));v.addWidget(QLabel(f"Última renovação: {st.last_refresh or '—'}"))
        if st.last_error:v.addWidget(QLabel('Houve uma falha na última tentativa de conexão. A autorização offline continua válida enquanto estiver dentro do prazo.'))
        row=QHBoxLayout();row.addWidget(button('Ativar / trocar conta',self.open_account_activation,True));row.addWidget(button('Renovar agora',self.refresh_account));row.addStretch();v.addLayout(row)
        row2=QHBoxLayout();row2.addWidget(button('Trocar senha',self.change_account_password));row2.addWidget(button('Desvincular este computador',self.unlink_account));row2.addStretch();v.addLayout(row2)
        self.account_feedback=QLabel('Pronto.');self.account_feedback.setObjectName('muted');v.addWidget(self.account_feedback);note=QLabel('A senha não fica salva no NutriDesk. Após a ativação, este computador recebe um token próprio para renovar a licença.');note.setWordWrap(True);v.addWidget(note);v.addStretch();return w
    def settings(self):
        w=super().settings();st=self.account_license.state();lic=licensing.current();general=self.settings_tabs.widget(0).layout();card=QWidget();lay=QVBoxLayout(card);lay.addWidget(QLabel('Status da conta'));lay.addWidget(QLabel(f"{st.email or 'Não ativado'} • {(lic or {}).get('plan','—')} • validade {(lic or {}).get('expires','—')}"));lay.addWidget(button('Abrir conta e licença',lambda:self.show_page('Conta')));general.insertWidget(max(1,general.count()-1),card);return w
    def save_account_server(self):
        try:self.account_license.set_server_url(self.account_server.text());QMessageBox.information(self,'Conta','Servidor salvo.')
        except Exception as e:show_error(self,'Conta',e)
    def open_account_activation(self):
        try:
            dlg=AccountActivationDialog(self.account_license,self);dlg.email.setText(self.account_license.state().email);dlg.exec()
        except Exception as e:show_error(self,'Conta',e)
    def refresh_account(self):
        if hasattr(self,'account_feedback'):self.account_feedback.setText('Verificando licença…');QApplication.processEvents()
        try:
            self.account_license.refresh()
            if hasattr(self,'account_feedback'):self.account_feedback.setText('Licença renovada com sucesso.')
            QMessageBox.information(self,'Conta','Licença renovada neste computador.')
        except Exception as e:
            if hasattr(self,'account_feedback'):self.account_feedback.setText('Não foi possível renovar agora.')
            show_error(self,'Conta',e)
    def change_account_password(self):
        current,ok=QInputDialog.getText(self,'Senha atual','Senha atual:',QLineEdit.Password)
        if not ok:return
        new,ok=QInputDialog.getText(self,'Nova senha','Nova senha (mínimo 8 caracteres):',QLineEdit.Password)
        if not ok:return
        try:self.account_license.change_password(current,new);QMessageBox.information(self,'Conta','Senha alterada.')
        except Exception as e:show_error(self,'Conta',e)
    def unlink_account(self):
        if QMessageBox.question(self,'Desvincular','Desvincular este computador libera uma vaga da licença e exigirá login novamente. Continuar?')!=QMessageBox.Yes:return
        try:self.account_license.unlink_current();QMessageBox.information(self,'Conta','Computador desvinculado. O NutriDesk exigirá ativação no próximo início.')
        except Exception as e:show_error(self,'Conta',e)
