from __future__ import annotations
from datetime import date,datetime
from pathlib import Path
from PySide6.QtCore import Qt,QDate,QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QTabWidget,QWidget,QLineEdit,QComboBox,QTextEdit,QPushButton,QTableWidget,QHeaderView,QMessageBox,QFileDialog,QInputDialog,QLabel,QGridLayout,QCheckBox,QDateEdit,QGroupBox)
from .common import button,item,show_error
from .design_system import Card,StatCard,EmptyState,section_title,muted
from .view_models import age_on,age_label
from nutridesktop.core.validation import required_text,email,iso_date,number,ValidationError
from nutridesktop.data.repositories import PatientRepository,AssessmentRepository,PlanRepository,FoodRepository,TimelineRepository,AnamnesisRepository,PhotoRepository,RecipeRepository,AgendaRepository
from nutridesktop.services.documents import DocumentService
from nutridesktop.services.plans import plan_nutrients,substitute,target_status,meal_distribution_status
from nutridesktop.services.reports import generate_complete_report
from nutridesktop.services.charts import patient_evolution_figure
from nutridesktop.services.growth import GrowthService
from nutridesktop.services.longitudinal import build_patient_comparison
from nutridesktop.services.whatsapp import build_whatsapp_url,message_for
from nutridesktop.services.plan_documents import generate_plan_pdf
from nutridesktop.clinical.formulas import calcular_avaliacao_completa


class FoodSearchDialog(QDialog):
    def __init__(self,repo,parent=None,title='Selecionar alimento'):
        super().__init__(parent);self.repo=repo;self.selected=None;self.setWindowTitle(title);self.resize(760,520);lay=QVBoxLayout(self);self.query=QLineEdit();self.query.setPlaceholderText('Digite parte do nome do alimento');self.query.textChanged.connect(self.refresh);lay.addWidget(self.query);self.table=QTableWidget(0,6);self.table.setHorizontalHeaderLabels(['ID','Alimento','kcal','Proteína','Carboidrato','Lipídios']);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);self.table.cellDoubleClicked.connect(lambda *_:self.choose());lay.addWidget(self.table);row=QHBoxLayout();row.addStretch();row.addWidget(button('Cancelar',self.reject));row.addWidget(button('Selecionar',self.choose,True));lay.addLayout(row);self.refresh()
    def refresh(self):
        rows=self.repo.search(self.query.text().strip(),80);self.rows=rows;self.table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,v in enumerate([x['id'],x['descricao'],x['kcal'],x['proteina'],x['carboidrato'],x['lipideos']]):self.table.setItem(r,c,item(v))
    def choose(self):
        r=self.table.currentRow()
        if r<0:QMessageBox.information(self,'Alimento','Selecione um alimento da lista.');return
        self.selected=self.rows[r];self.accept()

class PatientDialog(QDialog):
    def __init__(self,pid,parent=None):
        super().__init__(parent);self.pid=pid;self.pr=PatientRepository();self.ar=AssessmentRepository();self.pl=PlanRepository();self.fr=FoodRepository();self.docs=DocumentService();self.tr=TimelineRepository();self.anr=AnamnesisRepository();self.phr=PhotoRepository();self.rr=RecipeRepository();self.ag=AgendaRepository();self.gs=GrowthService();self.setWindowTitle('Prontuário • NutriDesk');self.resize(1180,800)
        root=QVBoxLayout(self);head=QHBoxLayout();self.title=QLabel();self.title.setStyleSheet('font-size:26px;font-weight:800');head.addWidget(self.title);self.header_meta=QLabel();self.header_meta.setStyleSheet('color:#697571');head.addWidget(self.header_meta);head.addStretch();head.addWidget(button('Nova consulta',self.open_guided_consultation,True));head.addWidget(button('Editar paciente',self.open_profile_editor));root.addLayout(head)
        self.tabs=QTabWidget();root.addWidget(self.tabs);self.tabs.addTab(self.summary_tab(),'Resumo');self.tabs.addTab(self.consultation_tab(),'Consulta');self.tabs.addTab(self.assessment_tab(),'Avaliações');self.tabs.addTab(self.plan_tab(),'Plano alimentar');self.tabs.addTab(self.evolution_workspace_tab(),'Evolução');self.tabs.addTab(self.files_workspace_tab(),'Arquivos');self.refresh_header()
    def refresh_header(self):
        p=self.pr.get(self.pid);self.title.setText(p['nome'] if p else 'Paciente')
        if p:self.header_meta.setText(f"{age_label(p['data_nascimento'])}  •  {'Feminino' if p['sexo']=='F' else 'Masculino'}  •  {p['telefone'] or 'sem telefone'}")
    def summary_tab(self):
        w=QWidget();lay=QVBoxLayout(w);p=self.pr.get(self.pid);ass=self.ar.list(self.pid);latest=ass[-1] if ass else None;plans=self.pl.list(self.pid);timeline=self.tr.list(self.pid)
        grid=QGridLayout();grid.addWidget(StatCard('Peso',f"{latest['peso']:.1f} kg" if latest and latest['peso'] is not None else '—','Última avaliação'),0,0);grid.addWidget(StatCard('IMC',f"{latest['imc']:.1f}" if latest and latest['imc'] is not None else '—','Última avaliação'),0,1);grid.addWidget(StatCard('Gordura corporal',f"{latest['pg_final']:.1f}%" if latest and latest['pg_final'] is not None else '—','Composição corporal'),0,2);grid.addWidget(StatCard('Plano atual',plans[0]['nome'] if plans else 'Nenhum','Plano alimentar'),0,3);lay.addLayout(grid)
        cols=QHBoxLayout();left=Card();left.body.addWidget(section_title('Linha do tempo'))
        for e in timeline[:7]:left.body.addWidget(QLabel(f"{e.get('event_date','')}  •  {e.get('title','')}"))
        if not timeline:left.body.addWidget(muted('O histórico clínico aparecerá aqui conforme os atendimentos forem registrados.'))
        cols.addWidget(left,2);right=Card();right.body.addWidget(section_title('Ações clínicas'))
        if p and age_on(p['data_nascimento']) is not None and age_on(p['data_nascimento'])<=19:right.body.addWidget(button('Crescimento WHO',self.open_growth_context))
        if p and p['sexo']=='F':right.body.addWidget(button('Gestação / lactação',self.open_maternal_context))
        right.body.addWidget(button('Exames laboratoriais',self.open_labs))
        right.body.addWidget(button('Packs clínicos',self.open_clinical_packs))
        right.body.addWidget(button('Comparação longitudinal',self.show_longitudinal_comparison))
        right.body.addWidget(button('Enviar via WhatsApp',self.open_whatsapp))
        right.body.addWidget(button('Gerar relatório',lambda:self.tabs.setCurrentIndex(5)));right.body.addStretch();cols.addWidget(right,1);lay.addLayout(cols);lay.addStretch();return w
    def consultation_tab(self):
        w=QWidget();lay=QVBoxLayout(w);top=Card(soft=True);top.body.addWidget(section_title('Consulta guiada'));top.body.addWidget(muted('Use o fluxo guiado para conduzir dados da consulta, anamnese, avaliação, plano, orientações e retorno.'));top.body.addWidget(button('Iniciar nova consulta',self.open_guided_consultation,True));lay.addWidget(top);lay.addWidget(self.anamnesis_tab(),1);return w
    def evolution_workspace_tab(self):
        w=QWidget();lay=QVBoxLayout(w);row=QHBoxLayout();row.addWidget(button('Gráfico de evolução',self.show_chart,True));row.addStretch();lay.addLayout(row);tabs=QTabWidget();tabs.addTab(self.timeline_tab(),'Linha do tempo');lay.addWidget(tabs);return w
    def files_workspace_tab(self):
        w=QWidget();lay=QVBoxLayout(w);tabs=QTabWidget();tabs.addTab(self.documents_tab(),'Documentos');tabs.addTab(self.photos_tab(),'Fotos');tabs.addTab(self.report_tab(),'Relatórios');lay.addWidget(tabs);return w
    def open_profile_editor(self):
        d=QDialog(self);d.setWindowTitle('Editar paciente');lay=QVBoxLayout(d);lay.addWidget(self.profile_tab());d.resize(560,520);d.exec();self.refresh_header()
    def open_guided_consultation(self):
        try:
            from .consultation_dialog import ConsultationDialog
            dlg=ConsultationDialog(self.pr.list(),self.ag,self,self.pid)
            if dlg.exec()==QDialog.Accepted:self.refresh_header();self.refresh_timeline();self.refresh_assessments();self.refresh_plans()
        except Exception as e:show_error(self,'Consulta',e)
    def open_labs(self):
        from .labs_dialog import LabsDialog
        LabsDialog(self.pid,self.pr.db,self).exec();self.refresh_timeline()
    def open_clinical_packs(self):
        from .clinical_packs_dialog import ClinicalPacksDialog
        ClinicalPacksDialog(self.pid,self.pr.db,self).exec();self.refresh_timeline()
    def show_longitudinal_comparison(self):
        try:
            data=build_patient_comparison(self.pid,self.pr.db);d=QDialog(self);d.setWindowTitle('Comparação longitudinal');d.resize(900,620);lay=QVBoxLayout(d);table=QTableWidget(0,4);table.setHorizontalHeaderLabels(['Data','Categoria','Indicador','Valor']);table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);rows=[]
            for a in data['assessments']:
                for key,label,unit in [('peso','Peso','kg'),('imc','IMC',''),('pg_final','Gordura corporal','%'),('cintura','Cintura','cm')]:
                    if a.get(key) is not None:rows.append((a.get('data',''),'Avaliação',label,f"{a[key]} {unit}".strip()))
            for marker,series in data['labs'].items():
                for x in series:rows.append((x['date'],'Exame',marker,f"{x['value']} {x['unit']}".strip()))
            for c in data['consultations']:
                if c.get('objetivo'):rows.append((c.get('data',''),'Consulta','Objetivo',c.get('objetivo','')))
            rows.sort(key=lambda x:x[0],reverse=True);table.setRowCount(len(rows))
            for r,row in enumerate(rows):
                for c,v in enumerate(row):table.setItem(r,c,item(v))
            lay.addWidget(QLabel('Comparação longitudinal'));lay.addWidget(table);d.exec()
        except Exception as e:show_error(self,'Comparação longitudinal',e)
    def open_whatsapp(self):
        p=self.pr.get(self.pid)
        if not p:return
        kinds=['Plano alimentar','Lembrar retorno','Solicitar exames','Acompanhamento'];kind,ok=QInputDialog.getItem(self,'WhatsApp','Mensagem',kinds,0,False)
        if not ok:return
        mapping={'Plano alimentar':'plan','Lembrar retorno':'return','Solicitar exames':'exam','Acompanhamento':'followup'}
        try:QDesktopServices.openUrl(QUrl(build_whatsapp_url(p['telefone'],message_for(mapping[kind],p['nome']))))
        except Exception as e:show_error(self,'WhatsApp',e)
    def open_growth_context(self):
        p=self.pr.get(self.pid)
        if not p or not p['data_nascimento']:QMessageBox.information(self,'Crescimento','Informe a data de nascimento no cadastro.');return
        d=QDialog(self);d.setWindowTitle('Crescimento WHO');f=QFormLayout(d);when=QDateEdit();when.setCalendarPopup(True);when.setDate(QDate.currentDate());weight=QLineEdit();height=QLineEdit();result=QLabel();result.setWordWrap(True);f.addRow('Data',when);f.addRow('Peso kg',weight);f.addRow('Altura cm',height);f.addRow('',button('Calcular e registrar',lambda:self._save_growth(d,when,weight,height,result),True));f.addRow('Resultado',result);d.exec()
    def _save_growth(self,dialog,when,weight,height,result):
        try:
            p=self.pr.get(self.pid);res=self.gs.assess_and_save(self.pid,p['sexo'],p['data_nascimento'],when.date().toString('yyyy-MM-dd'),number(weight.text(),'Peso',0.1,500),number(height.text(),'Altura',20,250));lines=[]
            for key,obj in res.items():lines.append(f"{key}: z {obj.zscore:.2f}")
            result.setText('\n'.join(lines) or 'Sem referência aplicável.');self.refresh_timeline()
        except Exception as e:show_error(self,'Crescimento',e)
    def open_maternal_context(self):
        from nutridesktop.clinical.maternal import gestational_weight_range,maternal_reference
        d=QDialog(self);d.setWindowTitle('Gestação e lactação');f=QFormLayout(d);pre=QLineEdit();height=QLineEdit();phase=QComboBox();phase.addItems(['1º trimestre','2º trimestre','3º trimestre','Lactação 0-6 meses']);out=QLabel();out.setWordWrap(True)
        def calc():
            try:
                bmi=number(pre.text(),'Peso pré-gestacional',20,300)/(number(height.text(),'Altura',100,230)/100)**2;rg=gestational_weight_range(bmi);ref=maternal_reference(phase.currentText());out.setText(f"IMC pré-gestacional: {bmi:.1f}\nClassificação: {rg['classification']}\nGanho recomendado: {rg['gain_min']}–{rg['gain_max']} kg\nEnergia adicional: {ref['energy_extra_kcal']} kcal/dia")
            except Exception as e:show_error(self,'Materno-infantil',e)
        f.addRow('Peso pré-gestacional kg',pre);f.addRow('Altura cm',height);f.addRow('Fase',phase);f.addRow('',button('Calcular referência',calc,True));f.addRow('Referência',out);d.exec()
    def profile_tab(self):
        w=QWidget();f=QFormLayout(w);p=self.pr.get(self.pid);self.p_name=QLineEdit(p['nome']);self.p_sex=QComboBox();self.p_sex.addItems(['Feminino','Masculino']);self.p_sex.setCurrentIndex(0 if p['sexo']=='F' else 1);self.p_birth=QDateEdit();self.p_birth.setCalendarPopup(True);self.p_birth.setDisplayFormat('dd/MM/yyyy');self.p_birth.setDate(QDate.fromString(p['data_nascimento'],'yyyy-MM-dd') if p['data_nascimento'] else QDate.currentDate().addYears(-30));self.p_phone=QLineEdit(p['telefone'] or '');self.p_email=QLineEdit(p['email'] or '');self.p_obs=QTextEdit(p['observacoes'] or '')
        for l,x in [('Nome',self.p_name),('Sexo',self.p_sex),('Nascimento',self.p_birth),('Telefone',self.p_phone),('E-mail',self.p_email),('Observações',self.p_obs)]:f.addRow(l,x)
        f.addRow('',button('Salvar alterações',self.save_profile,True));return w
    def save_profile(self):
        try:
            sex='F' if self.p_sex.currentText()=='Feminino' else 'M';birth=self.p_birth.date().toString('yyyy-MM-dd');self.pr.update(self.pid,nome=required_text(self.p_name.text(),'Nome'),sexo=sex,data_nascimento=birth,telefone=self.p_phone.text().strip(),email=email(self.p_email.text()),observacoes=self.p_obs.toPlainText().strip());self.refresh_header();QMessageBox.information(self,'Paciente','Cadastro atualizado.')
        except Exception as e:show_error(self,'Validação',e)
    def assessment_tab(self):
        w=QWidget();lay=QVBoxLayout(w);p=self.pr.get(self.pid);previous=self.ar.list(self.pid);last=previous[-1] if previous else None
        form=QGridLayout();self.a_date=QDateEdit();self.a_date.setCalendarPopup(True);self.a_date.setDate(QDate.currentDate());self.a_weight=QLineEdit(str(last['peso']) if last and last['peso'] is not None else '');self.a_height=QLineEdit(str(last['altura_cm']) if last and last['altura_cm'] is not None else '');age=age_on(p['data_nascimento']) if p else None;self.a_age=QLabel(str(age) if age is not None else 'Cadastre a data de nascimento');self.a_activity=QComboBox();self.a_activity.addItems(['Sedentário','Levemente ativo','Moderadamente ativo','Muito ativo','Extremamente ativo']);self.a_adjust=QLineEdit('0');self.a_ptn=QLineEdit('1.2');self.a_lip=QLineEdit('30');self.a_method=QComboBox();self.a_method.addItems(['Estimativa antropométrica','Bioimpedância','Dobras cutâneas']);self.a_bia=QLineEdit();self.a_bia.setPlaceholderText('% gordura informado')
        fields=[('Data',self.a_date),('Peso kg',self.a_weight),('Altura cm',self.a_height),('Idade',self.a_age),('Atividade',self.a_activity),('Método corporal',self.a_method),('Bioimpedância %',self.a_bia),('Ajuste %',self.a_adjust),('Proteína g/kg',self.a_ptn),('Lipídios %',self.a_lip)]
        for i,(label,x) in enumerate(fields):form.addWidget(QLabel(label),i//4*2,i%4);form.addWidget(x,i//4*2+1,i%4)
        lay.addLayout(form);self.fold_box=QGroupBox('Dobras cutâneas (mm)');fold=QGridLayout(self.fold_box);self.fold_fields={}
        for i,k in enumerate(['peitoral','axilar','triceps','subescapular','abdominal','suprailiaca','coxa','biceps','panturrilha']):
            x=QLineEdit();x.setPlaceholderText(k.title());self.fold_fields[k]=x;fold.addWidget(QLabel(k.replace('_',' ').title()),i//3*2,i%3);fold.addWidget(x,i//3*2+1,i%3)
        self.fold_box.setVisible(False);self.a_method.currentTextChanged.connect(lambda t:self.fold_box.setVisible(t=='Dobras cutâneas'));self.a_bia.setVisible(False);self.a_method.currentTextChanged.connect(lambda t:self.a_bia.setVisible(t=='Bioimpedância'));lay.addWidget(self.fold_box);lay.addWidget(button('Calcular e salvar avaliação',self.save_assessment,True));self.ass_table=QTableWidget(0,7);self.ass_table.setHorizontalHeaderLabels(['ID','Data','Peso','IMC','% Gordura','VET','Versões']);self.ass_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);lay.addWidget(self.ass_table)
        row=QHBoxLayout();row.addWidget(button('Corrigir peso',self.revise_assessment));row.addWidget(button('Ver gráfico',self.show_chart));row.addStretch();lay.addLayout(row);self.refresh_assessments();return w
    def save_assessment(self):
        try:
            p=self.pr.get(self.pid);age=age_on(p['data_nascimento'],date.fromisoformat(self.a_date.date().toString('yyyy-MM-dd'))) if p else None
            if age is None:raise ValidationError('Informe a data de nascimento do paciente antes da avaliação.')
            weight=number(self.a_weight.text(),'Peso',1,500);height=number(self.a_height.text(),'Altura',30,250);dobras={}
            if self.a_method.currentText()=='Dobras cutâneas':
                for k,x in self.fold_fields.items():
                    if x.text().strip():dobras[k]=number(x.text(),k,0.1,100)
            bia=None
            if self.a_method.currentText()=='Bioimpedância':bia=number(self.a_bia.text(),'Bioimpedância',1,80)
            res=calcular_avaliacao_completa(p['sexo'],age,weight,height,dobras,'Mifflin-St Jeor',self.a_activity.currentText(),number(self.a_adjust.text(),'Ajuste',-90,300),number(self.a_ptn.text(),'Proteína',0,5),number(self.a_lip.text(),'Lipídios',0,80),bia_pg=bia)
            d={'data':self.a_date.date().toString('yyyy-MM-dd'),'peso':weight,'altura_cm':height,'idade':age,'imc':res['imc'],'pg_final':res['pg_final'],'origem_pg':res['origem_pg'],'massa_gorda':res['massa_gorda'],'massa_magra':res['massa_magra'],'formula_tmb':'Mifflin-St Jeor','tmb':res['tmb'],'atividade':self.a_activity.currentText(),'fator_atividade':res['fator_atividade'],'get_total':res['get_total'],'ajuste_pct':float(self.a_adjust.text().replace(',','.')),'vet':res['vet'],'ptn_gkg':float(self.a_ptn.text().replace(',','.')),'ptn_g':res['ptn_g'],'lip_pct':float(self.a_lip.text().replace(',','.')),'lip_g':res['lip_g'],'cho_g':res['cho_g'],'bia_pg':bia}
            d.update({f'dobra_{k}':v for k,v in dobras.items() if k in {'triceps','biceps','subescapular','suprailiaca','abdominal','coxa','peitoral','axilar','panturrilha'}});self.ar.create(self.pid,d);self.a_age.setText(str(age));self.refresh_assessments()
        except Exception as e:show_error(self,'Avaliação',e)
    def refresh_assessments(self):
        if not hasattr(self,'ass_table'):return
        rows=self.ar.list(self.pid);self.ass_table.setRowCount(len(rows))
        for r,a in enumerate(rows):
            rev=len(self.ar.revisions(a['id']))
            for c,v in enumerate([a['id'],a['data'],a['peso'],round(a['imc'] or 0,1),round(a['pg_final'] or 0,1),round(a['vet'] or 0),rev]):self.ass_table.setItem(r,c,item(v))
    def revise_assessment(self):
        r=self.ass_table.currentRow()
        if r<0:return
        aid=int(self.ass_table.item(r,0).text());new,ok=QInputDialog.getDouble(self,'Correção','Novo peso (kg)',float(self.ass_table.item(r,2).text()),1,500,1)
        if ok:self.ar.update_versioned(aid,{'peso':new},'Correção manual de peso');self.refresh_assessments()
    def show_chart(self):
        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
            metric,ok=QInputDialog.getItem(self,'Gráfico','Métrica',['peso','imc','pg_final','massa_magra','cintura'],0,False)
            if not ok:return
            from nutridesktop.services.charts import patient_metric_figure
            d=QDialog(self);d.setWindowTitle('Evolução');lay=QVBoxLayout(d);lay.addWidget(FigureCanvasQTAgg(patient_metric_figure(self.ar.list(self.pid),metric)));d.resize(800,500);d.exec()
        except Exception as e:show_error(self,'Gráfico',e)
    def anamnesis_tab(self):
        w=QWidget();lay=QHBoxLayout(w);left=QFormLayout();self.anam_fields={}
        for label in ['Queixa principal','Objetivo','Histórico clínico','Medicamentos e suplementos','Alergias/intolerâncias','Rotina alimentar','Sono e estresse','Atividade física','Hábito intestinal','Observações e conduta']:
            x=QTextEdit();x.setFixedHeight(55);left.addRow(label,x);self.anam_fields[label]=x
        left.addRow('',button('Salvar nova versão',self.save_anam,True));lay.addLayout(left,3);self.anam_table=QTableWidget(0,3);self.anam_table.setHorizontalHeaderLabels(['ID','Versão','Data']);self.anam_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);self.anam_table.cellDoubleClicked.connect(lambda *_:self.load_anam());lay.addWidget(self.anam_table,1);self.refresh_anam();return w
    def refresh_anam(self):
        if not hasattr(self,'anam_table'):return
        rows=self.anr.list(self.pid);self.anam_rows=rows;self.anam_table.setRowCount(len(rows))
        for r,a in enumerate(rows):
            for c,v in enumerate([a['id'],a['versao'],a['data']]):self.anam_table.setItem(r,c,item(v))
    def save_anam(self):
        data={k:v.toPlainText().strip() for k,v in self.anam_fields.items()}
        if not any(data.values()):QMessageBox.information(self,'Anamnese','Preencha ao menos um campo.');return
        self.anr.save_version(self.pid,data);self.refresh_anam();self.refresh_timeline()
    def load_anam(self):
        r=self.anam_table.currentRow()
        if r<0:return
        data=self.anr.data(self.anam_rows[r])
        for k,v in self.anam_fields.items():v.setPlainText(data.get(k,''))
    def photos_tab(self):
        w=QWidget();lay=QVBoxLayout(w);lay.addWidget(button('Adicionar foto de evolução',self.add_photo,True));self.photo_table=QTableWidget(0,3);self.photo_table.setHorizontalHeaderLabels(['Data','Arquivo','Observação']);self.photo_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);lay.addWidget(self.photo_table);self.refresh_photos();return w
    def add_photo(self):
        path,_=QFileDialog.getOpenFileName(self,'Foto','','Imagens (*.png *.jpg *.jpeg *.bmp)')
        if path:self.phr.add(self.pid,path);self.refresh_photos();self.refresh_timeline()
    def refresh_photos(self):
        if not hasattr(self,'photo_table'):return
        rows=self.phr.list(self.pid);self.photo_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,v in enumerate([x['data'],Path(x['caminho']).name,x['observacao']]):self.photo_table.setItem(r,c,item(v))
    def timeline_tab(self):
        w=QWidget();lay=QVBoxLayout(w);self.time_table=QTableWidget(0,3);self.time_table.setHorizontalHeaderLabels(['Data','Tipo','Evento']);self.time_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);lay.addWidget(self.time_table);self.refresh_timeline();return w
    def refresh_timeline(self):
        if not hasattr(self,'time_table'):return
        rows=self.tr.list(self.pid);self.time_table.setRowCount(len(rows))
        for r,e in enumerate(rows):
            for c,v in enumerate([e.get('event_date'),e.get('event_type'),e.get('title')]):self.time_table.setItem(r,c,item(v))
    def plan_tab(self):
        w=QWidget();lay=QVBoxLayout(w);top=QHBoxLayout();self.plan_name=QLineEdit();self.plan_name.setPlaceholderText('Nome do plano');self.plan_vet=QLineEdit('2000');top.addWidget(self.plan_name,1);top.addWidget(self.plan_vet);top.addWidget(button('Novo plano',self.new_plan,True));lay.addLayout(top)
        self.plan_table=QTableWidget(0,5);self.plan_table.setMaximumHeight(180);self.plan_table.setHorizontalHeaderLabels(['ID','Nome','Data','Versão','VET']);self.plan_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);lay.addWidget(self.plan_table)
        foodrow=QHBoxLayout();self.food_query=QLineEdit();self.food_query.setPlaceholderText('Buscar alimento para adicionar');self.food_grams=QLineEdit('100');self.food_grams.setMaximumWidth(90);self.food_meal=QComboBox();self.food_meal.setEditable(True);self.food_meal.addItems(['Café da manhã','Lanche da manhã','Almoço','Lanche da tarde','Jantar','Ceia']);foodrow.addWidget(self.food_query,1);foodrow.addWidget(self.food_grams);foodrow.addWidget(self.food_meal);foodrow.addWidget(button('Selecionar alimento',self.add_food,True));lay.addLayout(foodrow)
        act=QHBoxLayout();act.addWidget(button('Nova versão',self.revise_plan));act.addWidget(button('Adicionar receita',self.add_recipe_to_plan));act.addWidget(button('Salvar substituição',self.save_plan_substitution));act.addWidget(button('Gerar plano em PDF',self.export_plan_pdf,True));act.addWidget(button('Metas macro',self.set_macro_targets));act.addWidget(button('Aplicar DRI',self.apply_dri));act.addWidget(button('Distribuir VET',self.set_meal_pct));act.addWidget(button('Marcar plano como enviado',self.mark_plan_sent));act.addStretch();lay.addLayout(act)
        self.plan_total=Card(soft=True);self.plan_total_label=QLabel('Selecione um plano para ver o resumo.');self.plan_total.body.addWidget(self.plan_total_label);lay.addWidget(self.plan_total)
        self.plan_items=QTableWidget(0,5);self.plan_items.setHorizontalHeaderLabels(['Refeição','Item','Quantidade','kcal','Origem']);self.plan_items.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);lay.addWidget(self.plan_items);self.plan_table.itemSelectionChanged.connect(self.refresh_plan_summary);self.refresh_plans();return w
    def selected_plan_id(self):
        r=self.plan_table.currentRow();return int(self.plan_table.item(r,0).text()) if r>=0 else None
    def new_plan(self):
        try:self.pl.create(self.pid,required_text(self.plan_name.text(),'Nome do plano'),number(self.plan_vet.text(),'VET',0,10000));self.refresh_plans()
        except Exception as e:show_error(self,'Plano',e)
    def refresh_plans(self):
        if not hasattr(self,'plan_table'):return
        rows=self.pl.list(self.pid);self.plan_table.setRowCount(len(rows))
        for r,p in enumerate(rows):
            for c,v in enumerate([p['id'],p['nome'],p['data'],p['version_no'],p['vet_meta']]):self.plan_table.setItem(r,c,item(v))
        if rows:self.plan_table.selectRow(0)
    def add_food(self):
        pid=self.selected_plan_id()
        if not pid:QMessageBox.information(self,'Plano','Selecione ou crie um plano primeiro.');return
        dlg=FoodSearchDialog(self.fr,self);dlg.query.setText(self.food_query.text().strip())
        if dlg.exec()!=QDialog.Accepted or not dlg.selected:return
        grams=number(self.food_grams.text(),'Gramas',0.1,5000);meal=self.food_meal.currentText().strip() or 'Refeição';self.pl.add_food(pid,meal,dlg.selected['id'],grams);self.food_query.setText(dlg.selected['descricao']);self.refresh_plan_summary()
    def refresh_plan_summary(self):
        pid=self.selected_plan_id()
        if not pid:return
        total,meals=plan_nutrients(pid,self.pl);self.plan_total_label.setText(f"{total.get('kcal',0):.0f} kcal  •  Proteína {total.get('proteina',0):.1f} g  •  Carboidratos {total.get('carboidrato',0):.1f} g  •  Lipídios {total.get('lipideos',0):.1f} g")
        rows=self.pl.items(pid);self.plan_items.setRowCount(len(rows))
        for r,x in enumerate(rows):
            name=x['descricao'] or x['recipe_name'] or 'Item';qty=f"{x['quantidade_g'] or 0:g} g" if x['alimento_id'] else f"{x['quantidade_porcoes'] or 0:g} porção(ões)";kcal=(float(x['kcal'] or 0)*float(x['quantidade_g'] or 0)/100) if x['alimento_id'] else ''
            for c,v in enumerate([x['refeicao'],name,qty,f'{kcal:.0f}' if kcal!='' else 'receita','Alimento' if x['alimento_id'] else 'Receita']):self.plan_items.setItem(r,c,item(v))
    def suggest_substitutions(self):
        dlg=FoodSearchDialog(self.fr,self,'Alimento de referência');dlg.query.setText(self.food_query.text().strip())
        if dlg.exec()!=QDialog.Accepted or not dlg.selected:return
        grams=number(self.food_grams.text(),'Gramas',1,5000);opts=substitute(dlg.selected['id'],grams,'',self.fr);QMessageBox.information(self,'Substituições','\n'.join(f"{o['descricao']} — {o['grams']} g (ΔP {o['protein_delta']} g)" for o in opts) or 'Sem opções próximas.')
    def mark_plan_sent(self):
        pending=self.ag.latest_pending_plan(self.pid)
        if not pending:QMessageBox.information(self,'Plano alimentar','Não há consulta recente aguardando envio do plano.');return
        if QMessageBox.question(self,'Plano alimentar',f"Confirmar que o plano da consulta de {pending['data']} foi enviado ao paciente?")!=QMessageBox.Yes:return
        self.ag.mark_latest_plan_sent(self.pid);QMessageBox.information(self,'Plano alimentar','Plano marcado como enviado. A pendência foi removida do Dashboard.')
    def save_plan_substitution(self):
        plan_id=self.selected_plan_id();row=self.plan_items.currentRow()
        if not plan_id or row<0:QMessageBox.information(self,'Substituições','Selecione um alimento do plano.');return
        items=self.pl.items(plan_id);base=items[row] if row<len(items) else None
        if not base or not base['alimento_id']:QMessageBox.information(self,'Substituições','Selecione um alimento simples, não uma receita.');return
        dlg=FoodSearchDialog(self.fr,self,'Selecionar substituição')
        if dlg.exec()!=QDialog.Accepted or not dlg.selected:return
        base_food=self.fr.get(base['alimento_id']);alt=dlg.selected;base_kcal=float(base_food['kcal'] or 0)*float(base['quantidade_g'] or 0)/100;alt100=float(alt['kcal'] or 0)
        grams=round(base_kcal/alt100*100,1) if alt100>0 else float(base['quantidade_g'] or 0)
        self.pl.add_substitution(plan_id,base['id'],alt['id'],grams,'Equivalência energética aproximada; ajustar clinicamente quando necessário.')
        QMessageBox.information(self,'Substituições',f"Substituição salva: {alt['descricao']} — {grams:g} g.")
    def export_plan_pdf(self):
        plan_id=self.selected_plan_id()
        if not plan_id:QMessageBox.information(self,'Plano alimentar','Selecione um plano.');return
        from nutridesktop.data.repositories import TemplateRepository
        tr=TemplateRepository(self.pl.db);templates=tr.list('Plano');labels=['Padrão configurado']+[f"{t['id']} - {t['nome']}" for t in templates];choice,ok=QInputDialog.getItem(self,'Template do plano','Template',labels,0,False)
        if not ok:return
        template_id=None if choice=='Padrão configurado' else int(choice.split(' - ',1)[0]);path,_=QFileDialog.getSaveFileName(self,'Gerar plano em PDF',f"plano_{self.pid}_{date.today().isoformat()}.pdf",'PDF (*.pdf)')
        if not path:return
        try:generate_plan_pdf(self.pid,plan_id,path,template_id,self.pl.db);self.docs.import_file(self.pid,path,'Plano alimentar');QMessageBox.information(self,'Plano alimentar','PDF gerado com o template selecionado e anexado ao prontuário.');self.refresh_docs()
        except Exception as e:show_error(self,'Plano alimentar',e)
    def revise_plan(self):
        pid=self.selected_plan_id()
        if pid:self.pl.create_revision(pid);self.refresh_plans();self.refresh_timeline()
    def add_recipe_to_plan(self):
        pid=self.selected_plan_id()
        if not pid:return
        recipes=self.rr.list()
        if not recipes:QMessageBox.information(self,'Receitas','Cadastre uma receita primeiro.');return
        labels=[f"{r['id']} - {r['nome']}" for r in recipes];choice,ok=QInputDialog.getItem(self,'Receita','Receita',labels,0,False)
        if ok:
            rid=int(choice.split(' - ',1)[0]);portions,ok2=QInputDialog.getDouble(self,'Porções','Quantidade de porções',1,0.1,20,1)
            if ok2:self.pl.add_recipe(pid,self.food_meal.text().strip() or 'Refeição',rid,portions);self.refresh_plan_summary()
    def set_macro_targets(self):
        pid=self.selected_plan_id()
        if not pid:return
        with self.pl.db.connect() as c:plan=c.execute('SELECT vet_meta FROM planos WHERE id=?',(pid,)).fetchone()
        kcal=float(plan['vet_meta'] or 0) if plan else 0
        protein,ok=QInputDialog.getDouble(self,'Meta de proteína','Proteína (g/dia)',100,0,1000,1)
        if not ok:return
        carbs,ok=QInputDialog.getDouble(self,'Meta de carboidrato','Carboidrato (g/dia)',250,0,2000,1)
        if not ok:return
        lipids,ok=QInputDialog.getDouble(self,'Meta de lipídios','Lipídios (g/dia)',70,0,1000,1)
        if not ok:return
        if kcal:self.pl.set_target(pid,'kcal',kcal,'kcal',0.9*kcal,1.1*kcal)
        for n,v in [('proteina',protein),('carboidrato',carbs),('lipideos',lipids)]:self.pl.set_target(pid,n,v,'g',0.9*v,1.1*v)
        self.refresh_plan_summary()
    def apply_dri(self):
        pid=self.selected_plan_id()
        if not pid:return
        from nutridesktop.services.plans import apply_lifecycle_dri
        p=self.pr.get(self.pid);av=self.ar.list(self.pid);age=float(av[-1]['idade']) if av else 30
        state,ok=QInputDialog.getItem(self,'Ciclo de vida','Condição',['Padrão por idade','Gestante','Lactante'],0,False)
        if not ok:return
        pregnant=state=='Gestante';lactating=state=='Lactante'
        if (pregnant or lactating) and p['sexo']!='F':
            QMessageBox.warning(self,'DRI','Gestação/lactação requer paciente com sexo feminino no cadastro.');return
        refs=apply_lifecycle_dri(pid,age,p['sexo'],pregnant,lactating,self.pl)
        if not refs:QMessageBox.warning(self,'DRI','Não há referência configurada para este ciclo de vida.');return
        QMessageBox.information(self,'DRI','Metas-chave aplicadas: '+', '.join(x.nutrient for x in refs.values()));self.refresh_plan_summary()
    def set_meal_pct(self):
        pid=self.selected_plan_id()
        if not pid:return
        meal,ok=QInputDialog.getText(self,'Refeição','Nome da refeição')
        if not ok:return
        pct,ok=QInputDialog.getDouble(self,'Distribuição','% do VET para esta refeição',25,0,100,1)
        if ok:self.pl.set_meal_distribution(pid,meal,pct);QMessageBox.information(self,'Plano','Distribuição salva.')
    def documents_tab(self):
        w=QWidget();lay=QVBoxLayout(w);lay.addWidget(button('Importar documento para pasta gerenciada',self.import_doc,True));self.doc_table=QTableWidget(0,4);self.doc_table.setHorizontalHeaderLabels(['ID','Tipo','Arquivo','Integridade']);self.doc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);lay.addWidget(self.doc_table);self.refresh_docs();return w
    def import_doc(self):
        p,_=QFileDialog.getOpenFileName(self,'Documento');
        if p:self.docs.import_file(self.pid,p);self.refresh_docs();self.refresh_timeline()
    def refresh_docs(self):
        if not hasattr(self,'doc_table'):return
        rows=self.docs.list(self.pid);self.doc_table.setRowCount(len(rows))
        for r,d in enumerate(rows):
            ok,msg=self.docs.verify(d['id'])
            for c,v in enumerate([d['id'],d['tipo'],d['nome_arquivo'],'OK' if ok else msg]):self.doc_table.setItem(r,c,item(v))
    def report_tab(self):
        w=QWidget();lay=QVBoxLayout(w);lay.addWidget(QLabel('Escolha as seções do relatório: cadastro, anamnese, avaliação, evolução, plano/metas e linha do tempo.'));lay.addWidget(button('Gerar relatório clínico completo',self.report,True));lay.addStretch();return w
    def report(self):
        d=QDialog(self);d.setWindowTitle('Seções do relatório');v=QVBoxLayout(d);checks={}
        for key,label in [('patient','Cadastro'),('anamnesis','Anamnese mais recente'),('assessment','Última avaliação'),('evolution','Evolução antropométrica'),('plan','Plano e metas'),('labs','Exames laboratoriais'),('packs','Packs clínicos'),('timeline','Linha do tempo')]:
            cb=QCheckBox(label);cb.setChecked(True);v.addWidget(cb);checks[key]=cb
        v.addWidget(button('Continuar',d.accept,True))
        if d.exec()!=QDialog.Accepted:return
        sections={k for k,cb in checks.items() if cb.isChecked()}
        if not sections:QMessageBox.information(self,'Relatório','Selecione ao menos uma seção.');return
        path,_=QFileDialog.getSaveFileName(self,'Salvar relatório',f"relatorio_{self.pid}_{date.today().isoformat()}.pdf",'PDF (*.pdf)')
        if not path:return
        try:generate_complete_report(self.pid,path,sections);self.docs.import_file(self.pid,path,'Relatório completo');QMessageBox.information(self,'Relatório','Relatório gerado e anexado ao prontuário.');self.refresh_docs();self.refresh_timeline()
        except Exception as e:show_error(self,'Relatório',e)
