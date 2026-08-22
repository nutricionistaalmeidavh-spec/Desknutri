from __future__ import annotations
from PySide6.QtCore import QDate,QTime
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QDateEdit,QTimeEdit,QLineEdit,QTextEdit,QCheckBox,QStackedWidget,QWidget,QFormLayout,QMessageBox)
from .common import button,show_error
from .design_system import Card,muted
from nutridesktop.data.repositories import AnamnesisRepository

CONSULTATION_STEPS=['Dados da consulta','Anamnese','Avaliação','Plano alimentar','Orientações','Retorno']

class ConsultationDialog(QDialog):
    def __init__(self,patients,agenda_repo,parent=None,patient_id=None):
        super().__init__(parent);self.patients=list(patients);self.ag=agenda_repo;self.anr=AnamnesisRepository(self.ag.db);self.created_consultation_id=None;self.setWindowTitle('Nova consulta • NutriDesk');self.resize(980,700)
        root=QVBoxLayout(self);head=QHBoxLayout();title=QLabel('Nova consulta');title.setStyleSheet('font-size:26px;font-weight:800');head.addWidget(title);head.addStretch();self.step_label=QLabel();head.addWidget(self.step_label);root.addLayout(head)
        self.progress=QLabel();self.progress.setStyleSheet('color:#0F5B55;font-weight:700;padding:8px 0');root.addWidget(self.progress)
        self.stack=QStackedWidget();root.addWidget(self.stack,1);self._build_steps(patient_id)
        nav=QHBoxLayout();self.back=button('Voltar',self.previous);self.next=button('Avançar',self.advance,True);nav.addWidget(self.back);nav.addStretch();nav.addWidget(button('Cancelar',self.reject));nav.addWidget(self.next);root.addLayout(nav);self._sync()
    def _build_steps(self,patient_id):
        p=QWidget();f=QFormLayout(p);self.patient=QComboBox()
        for row in self.patients:self.patient.addItem(row['nome'],row['id'])
        if patient_id is not None:
            idx=self.patient.findData(patient_id)
            if idx>=0:self.patient.setCurrentIndex(idx)
        self.when=QDateEdit();self.when.setCalendarPopup(True);self.when.setDate(QDate.currentDate());self.time=QTimeEdit();self.time.setTime(QTime.currentTime());self.kind=QComboBox();self.kind.addItems(['Consulta inicial','Retorno','Teleconsulta']);self.objective=QComboBox();self.objective.setEditable(True);self.objective.addItems(['Emagrecimento','Ganho de massa','Reeducação alimentar','Saúde geral']);self.approach=QComboBox();self.approach.setEditable(True);self.approach.addItems(['Alimentação equilibrada','Plano individualizado','Educação nutricional'])
        for label,w in [('Paciente',self.patient),('Data',self.when),('Hora',self.time),('Tipo',self.kind),('Objetivo principal',self.objective),('Abordagem nutricional',self.approach)]:f.addRow(label,w)
        self.stack.addWidget(p)
        p=QWidget();v=QVBoxLayout(p);v.addWidget(muted('Registre os principais pontos da consulta. O texto entra como nova versão da anamnese.'));self.anamnesis=QTextEdit();self.anamnesis.setPlaceholderText('Queixa, evolução, rotina, observações e conduta...');v.addWidget(self.anamnesis);self.stack.addWidget(p)
        p=QWidget();v=QVBoxLayout(p);self.reassess=QCheckBox('Reavaliar medidas e composição corporal nesta consulta');self.reassess.setChecked(True);v.addWidget(self.reassess);v.addWidget(Card());v.addWidget(muted('Após finalizar, o prontuário abre a área Avaliações com idade calculada e dados anteriores pré-preenchidos.'));v.addStretch();self.stack.addWidget(p)
        p=QWidget();f=QFormLayout(p);self.plan_delivery=QComboBox();self.plan_delivery.addItems(['Entregar o plano durante esta consulta','Entregar o plano depois da consulta']);self.update_plan=QCheckBox('Atualizar/criar plano alimentar');self.update_plan.setChecked(True);f.addRow('Entrega',self.plan_delivery);f.addRow('',self.update_plan);f.addRow('',muted('Se escolher entregar depois, o paciente aparecerá em “Planos alimentares não enviados” no Dashboard.'));self.stack.addWidget(p)
        p=QWidget();v=QVBoxLayout(p);self.guidance=QTextEdit();self.guidance.setPlaceholderText('Orientações combinadas com o paciente...');v.addWidget(self.guidance);self.stack.addWidget(p)
        p=QWidget();f=QFormLayout(p);self.schedule_return=QCheckBox('Agendar retorno');self.return_date=QDateEdit();self.return_date.setCalendarPopup(True);self.return_date.setDate(QDate.currentDate().addDays(30));self.return_time=QTimeEdit();self.return_time.setTime(QTime(9,0));f.addRow('',self.schedule_return);f.addRow('Data do retorno',self.return_date);f.addRow('Hora',self.return_time);self.stack.addWidget(p)
    def _sync(self):
        i=self.stack.currentIndex();self.step_label.setText(f'Etapa {i+1} de {len(CONSULTATION_STEPS)}');self.progress.setText('  →  '.join(f'{n}' if x==i else n for x,n in enumerate(CONSULTATION_STEPS)));self.back.setEnabled(i>0);self.next.setText('Finalizar consulta' if i==len(CONSULTATION_STEPS)-1 else 'Avançar')
    def previous(self):
        if self.stack.currentIndex()>0:self.stack.setCurrentIndex(self.stack.currentIndex()-1);self._sync()
    def advance(self):
        if self.stack.currentIndex()<len(CONSULTATION_STEPS)-1:self.stack.setCurrentIndex(self.stack.currentIndex()+1);self._sync();return
        self.finish_consultation()
    def finish_consultation(self):
        try:
            pid=self.patient.currentData()
            if pid is None:raise ValueError('Selecione um paciente.')
            data=self.when.date().toString('yyyy-MM-dd');hora=self.time.time().toString('HH:mm');obs=self.guidance.toPlainText().strip()
            cid=self.ag.create(int(pid),data,hora,self.kind.currentText(),observacoes=obs,duration=60)
            self.ag.update_clinical_context(cid,self.objective.currentText().strip(),self.approach.currentText().strip(),obs)
            self.ag.set_status(cid,'Realizada')
            if self.plan_delivery.currentIndex()==0:self.ag.mark_plan_sent(cid)
            anam=self.anamnesis.toPlainText().strip()
            if anam:self.anr.save_version(int(pid),{'Consulta':anam,'Objetivo':self.objective.currentText().strip(),'Orientações':obs},'Consulta guiada')
            if self.schedule_return.isChecked():self.ag.create(int(pid),self.return_date.date().toString('yyyy-MM-dd'),self.return_time.time().toString('HH:mm'),'Retorno',return_of=cid,duration=60)
            self.created_consultation_id=cid;self.accept()
        except Exception as e:show_error(self,'Nova consulta',e)
