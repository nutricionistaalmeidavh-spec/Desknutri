from __future__ import annotations
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QLineEdit,QTableWidget,QHeaderView,QMessageBox,QInputDialog
from .common import button,item,show_error
from nutridesktop.data.repositories import LabRepository
from nutridesktop.core.validation import required_text,number


class LabsDialog(QDialog):
    def __init__(self,patient_id,database=None,parent=None):
        super().__init__(parent);self.patient_id=patient_id;self.repo=LabRepository(database) if database else LabRepository();self.setWindowTitle('Exames laboratoriais');self.resize(900,640)
        lay=QVBoxLayout(self);top=QHBoxLayout();top.addWidget(button('Novo painel de exames',self.new_panel,True));top.addWidget(button('Adicionar resultado',self.add_result));top.addWidget(button('Marcar revisado',self.mark_reviewed));top.addStretch();lay.addLayout(top)
        self.table=QTableWidget(0,9);self.table.setHorizontalHeaderLabels(['ID','Coleta','Painel','Marcador','Valor','Unidade','Referência','Sinalização','Revisão']);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);lay.addWidget(self.table);self.current_panel_id=None;self.refresh()
    def refresh(self):
        rows=self.repo.list_results(self.patient_id);self.rows=rows;self.table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            value=x['value_numeric'] if x['value_numeric'] is not None else x['value_text'];ref=''
            if x['ref_min'] is not None or x['ref_max'] is not None:ref=f"{x['ref_min'] if x['ref_min'] is not None else '—'}–{x['ref_max'] if x['ref_max'] is not None else '—'}"
            review='Pendente' if x['needs_review'] and not x['reviewed_at'] else ('Revisado' if x['reviewed_at'] else '—')
            for c,v in enumerate([x['id'],x['data_coleta'],x['panel_name'],x['marker_name'],value,x['unit'],ref,x['flag'],review]):self.table.setItem(r,c,item(v))
    def new_panel(self):
        d=QDialog(self);d.setWindowTitle('Novo painel de exames');f=QFormLayout(d);name=QLineEdit('Painel laboratorial');date=QLineEdit();date.setPlaceholderText('AAAA-MM-DD');lab=QLineEdit();notes=QLineEdit();f.addRow('Nome',name);f.addRow('Data da coleta',date);f.addRow('Laboratório',lab);f.addRow('Observações',notes);f.addRow('',button('Criar painel',d.accept,True))
        if d.exec()!=QDialog.Accepted:return
        try:self.current_panel_id=self.repo.create_panel(self.patient_id,required_text(name.text(),'Nome'),required_text(date.text(),'Data'),lab.text().strip(),notes.text().strip());QMessageBox.information(self,'Exames','Painel criado. Agora adicione os resultados.');self.refresh()
        except Exception as e:show_error(self,'Exames',e)
    def add_result(self):
        panels=self.repo.list_panels(self.patient_id)
        if not panels:self.new_panel();panels=self.repo.list_panels(self.patient_id)
        if not panels:return
        labels=[f"{p['id']} - {p['data_coleta']} - {p['nome']}" for p in panels];choice,ok=QInputDialog.getItem(self,'Painel','Painel de exames',labels,0,False)
        if not ok:return
        panel_id=int(choice.split(' - ',1)[0]);d=QDialog(self);d.setWindowTitle('Adicionar resultado');f=QFormLayout(d);marker=QLineEdit();value=QLineEdit();unit=QLineEdit();rmin=QLineEdit();rmax=QLineEdit();review=QLineEdit('não');f.addRow('Marcador',marker);f.addRow('Valor',value);f.addRow('Unidade',unit);f.addRow('Referência mínima',rmin);f.addRow('Referência máxima',rmax);f.addRow('Marcar para revisão? (sim/não)',review);f.addRow('',button('Salvar resultado',d.accept,True))
        if d.exec()!=QDialog.Accepted:return
        try:
            rv=lambda x: number(x,'Referência',-1e9,1e9,True) if x.strip() else None
            self.repo.add_result(panel_id,required_text(marker.text(),'Marcador'),value.text().strip(),unit.text().strip(),rv(rmin.text()),rv(rmax.text()),needs_review=review.text().strip().lower() in {'sim','s','1','true'});self.refresh()
        except Exception as e:show_error(self,'Exames',e)
    def mark_reviewed(self):
        r=self.table.currentRow()
        if r<0:return
        self.repo.mark_reviewed(int(self.table.item(r,0).text()));self.refresh()
