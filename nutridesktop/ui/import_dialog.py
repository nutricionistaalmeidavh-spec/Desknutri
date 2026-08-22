from __future__ import annotations
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QComboBox,QLineEdit,QFileDialog,QTextEdit,QMessageBox
from .common import button,show_error
from nutridesktop.services.import_center import preview_import,apply_import

class ImportDialog(QDialog):
    def __init__(self,database=None,parent=None):
        super().__init__(parent);self.database=database;self.preview=None;self.setWindowTitle('Central de importação');self.resize(760,560);lay=QVBoxLayout(self);row=QHBoxLayout();self.kind=QComboBox();self.kind.addItem('Pacientes','patients');self.kind.addItem('Avaliações','assessments');self.kind.addItem('Exames laboratoriais','labs');self.path=QLineEdit();row.addWidget(self.kind);row.addWidget(self.path,1);row.addWidget(button('Escolher arquivo',self.choose));lay.addLayout(row);actions=QHBoxLayout();actions.addWidget(button('Pré-visualizar',self.do_preview,True));actions.addWidget(button('Aplicar importação',self.do_apply));actions.addStretch();lay.addLayout(actions);self.output=QTextEdit();self.output.setReadOnly(True);lay.addWidget(self.output)
    def choose(self):
        path,_=QFileDialog.getOpenFileName(self,'Importar dados','','Planilhas (*.csv *.xlsx *.xls)')
        if path:self.path.setText(path)
    def do_preview(self):
        try:
            self.preview=preview_import(self.kind.currentData(),self.path.text().strip(),self.database);p=self.preview;self.output.setPlainText(f"Linhas: {p.total_rows}\nProntas para importar: {len(p.rows)}\nDuplicadas/ignoradas: {len(p.skipped)}\nInválidas: {len(p.errors)}\n\n"+'\n'.join(f"Linha {e['row']}: {e['reason']}" for e in p.errors[:30]))
        except Exception as e:show_error(self,'Importação',e)
    def do_apply(self):
        if not self.preview:QMessageBox.information(self,'Importação','Faça a pré-visualização antes de aplicar.');return
        try:
            result=apply_import(self.preview,self.database);QMessageBox.information(self,'Importação',f"Importados: {result['imported']}\nIgnorados: {result['skipped']}\nInválidos: {result['invalid']}");self.accept()
        except Exception as e:show_error(self,'Importação',e)
