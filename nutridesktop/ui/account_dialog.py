from __future__ import annotations
from PySide6.QtWidgets import QDialog,QVBoxLayout,QFormLayout,QLabel,QLineEdit,QMessageBox,QPushButton
from nutridesktop.services.account_licensing import AccountLicenseService

class AccountActivationDialog(QDialog):
    def __init__(self,service:AccountLicenseService,parent=None):
        super().__init__(parent);self.service=service;self.setWindowTitle('Ativar NutriDesk');self.setMinimumWidth(450)
        v=QVBoxLayout(self);title=QLabel('Entre com seu acesso');title.setStyleSheet('font-size:22px;font-weight:700');v.addWidget(title)
        info=QLabel('Use o e-mail liberado na compra e a senha provisória de 8 dígitos recebida por e-mail. Depois de entrar, você pode trocar a senha em Conta → Trocar senha.');info.setWordWrap(True);v.addWidget(info)
        f=QFormLayout();self.email=QLineEdit();self.email.setPlaceholderText('voce@email.com');self.password=QLineEdit();self.password.setEchoMode(QLineEdit.Password);self.password.setPlaceholderText('senha recebida por e-mail');f.addRow('E-mail',self.email);f.addRow('Senha',self.password);v.addLayout(f)
        self.status=QLabel('');self.status.setWordWrap(True);v.addWidget(self.status);b=QPushButton('Entrar e ativar');b.clicked.connect(self.activate);v.addWidget(b)
    def activate(self):
        self.status.setText('Validando acesso...')
        try:self.service.activate(self.email.text(),self.password.text());self.accept()
        except Exception as e:self.status.setText(str(e));QMessageBox.warning(self,'Ativação',str(e))
