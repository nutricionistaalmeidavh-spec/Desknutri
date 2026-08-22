from __future__ import annotations
from datetime import date,timedelta
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QDate
from PySide6.QtGui import QKeySequence,QShortcut
from PySide6.QtWidgets import (QMainWindow,QWidget,QHBoxLayout,QVBoxLayout,QLabel,QPushButton,QStackedWidget,QLineEdit,QComboBox,QTableWidget,QHeaderView,QDialog,QFormLayout,QMessageBox,QFileDialog,QTextEdit,QInputDialog,QCheckBox,QDateEdit,QCalendarWidget,QTabWidget,QGridLayout,QFrame)
from .common import button,item,show_error
from .patient_dialog import PatientDialog,FoodSearchDialog
from .import_dialog import ImportDialog
from .design_system import APP_STYLE,Card,StatCard,EmptyState,section_title,muted
from .view_models import NAV_GROUPS,age_label
from nutridesktop.data.repositories import PatientRepository,AgendaRepository,RecipeRepository,FoodRepository,TemplateRepository,ProtocolRepository
from nutridesktop.core.validation import required_text,email,iso_date,number
from nutridesktop.services.growth import GrowthService
from nutridesktop.services.plans import recipe_nutrients
from nutridesktop.services.templates import render_template,STYLE_PRESETS
from nutridesktop.services.pending_actions import collect_pending_actions
from nutridesktop.services.backup import create_backup,restore_backup,validate_backup
from nutridesktop.services.security_settings import SecuritySettings
from nutridesktop.core.security import SessionLock
from nutridesktop.core.paths import DB_PATH,DATA_DIR
from nutridesktop.services.local_protection import LocalProtectionService
from nutridesktop.version import APP_VERSION,SCHEMA_VERSION,CLINICAL_CONTENT_VERSION

STYLE=APP_STYLE

class NewPatient(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent);self.setWindowTitle('Novo paciente');self.resize(460,300);f=QFormLayout(self)
        self.name=QLineEdit();self.sex=QComboBox();self.sex.addItems(['Feminino','Masculino'])
        self.has_birth=QCheckBox('Informar data de nascimento');self.has_birth.setChecked(True)
        self.birth=QDateEdit();self.birth.setCalendarPopup(True);self.birth.setDisplayFormat('dd/MM/yyyy');self.birth.setDate(QDate.currentDate().addYears(-30));self.birth.setEnabled(True);self.has_birth.toggled.connect(self.birth.setEnabled)
        self.phone=QLineEdit();self.phone.setPlaceholderText('(00) 00000-0000');self.mail=QLineEdit();self.mail.setPlaceholderText('paciente@email.com')
        f.addRow('Nome',self.name);f.addRow('Sexo',self.sex);f.addRow('',self.has_birth);f.addRow('Nascimento',self.birth);f.addRow('Telefone',self.phone);f.addRow('E-mail',self.mail);f.addRow('',button('Cadastrar paciente',self.accept,True))
    def values(self):
        birth=self.birth.date().toString('yyyy-MM-dd') if self.has_birth.isChecked() else None
        sex='F' if self.sex.currentText()=='Feminino' else 'M'
        return required_text(self.name.text(),'Nome'),sex,birth,self.phone.text().strip(),email(self.mail.text())

class PinDialog(QDialog):
    def __init__(self,settings,parent=None):
        super().__init__(parent);self.settings=settings;self.setWindowTitle('Desbloquear NutriDesk');f=QFormLayout(self);self.pin=QLineEdit();self.pin.setEchoMode(QLineEdit.Password);f.addRow('PIN',self.pin);f.addRow('',button('Desbloquear',self.check,True))
    def check(self):
        if self.settings.verify(self.pin.text()):self.accept()
        else:QMessageBox.warning(self,'PIN','PIN inválido.')

class MainWindow(QMainWindow):
    NAV=['Dashboard','Pacientes','Agenda','Biblioteca','Conta','Configurações']
    def __init__(self):
        super().__init__();self.setObjectName('nutridesk-main');self.setWindowTitle(f'NutriDesk {APP_VERSION}');self.resize(1440,900);self.setStyleSheet(STYLE)
        self.pr=PatientRepository();self.ag=AgendaRepository();self.rr=RecipeRepository();self.fr=FoodRepository();self.tr=TemplateRepository();self.pro=ProtocolRepository();self.gs=GrowthService();self.sec=SecuritySettings();self.local_protection=LocalProtectionService();row=self.sec.get();self.lock=SessionLock(row['auto_lock_minutes'] if row else 15);self.pages={};self._build();self._shortcuts();self.show_page('Dashboard');self.timer=QTimer(self);self.timer.timeout.connect(self.check_lock);self.timer.start(15000)
    def _build(self):
        root=QWidget();root.setObjectName('appRoot');self.setCentralWidget(root);l=QHBoxLayout(root);l.setContentsMargins(0,0,0,0);l.setSpacing(0)
        side=QWidget();side.setObjectName('sidebar');side.setFixedWidth(226);sv=QVBoxLayout(side);sv.setContentsMargins(14,18,14,14);sv.setSpacing(4)
        brand=QLabel('NutriDesk');brand.setObjectName('brand');sv.addWidget(brand);sv.addWidget(button('+ Nova consulta',self.new_consultation,True));self.nav={};self.nav_sections={}
        for section,names in NAV_GROUPS.items():
            lab=QLabel(section);lab.setObjectName('navSection');sv.addWidget(lab);self.nav_sections[section]=lab
            for n in names:
                b=button(n,lambda checked=False,name=n:self.show_page(name));sv.addWidget(b);self.nav[n]=b
        sv.addStretch();profile=Card(soft=True);profile.body.addWidget(QLabel('NutriDesk'));profile.body.addWidget(muted(f'v{APP_VERSION}'));sv.addWidget(profile);l.addWidget(side)
        self.stack=QStackedWidget();l.addWidget(self.stack,1)
    def _shortcuts(self):
        self.shortcuts=[]
        for seq,callback in [('Ctrl+N',self.new_consultation),('Ctrl+P',lambda:self.show_page('Pacientes')),('Ctrl+K',self.focus_patient_search)]:
            s=QShortcut(QKeySequence(seq),self);s.activated.connect(callback);self.shortcuts.append(s)
    def focus_patient_search(self):
        self.show_page('Pacientes')
        if hasattr(self,'patient_search'):self.patient_search.setFocus();self.patient_search.selectAll()
    def mousePressEvent(self,e):self.lock.touch();super().mousePressEvent(e)
    def keyPressEvent(self,e):self.lock.touch();super().keyPressEvent(e)
    def check_lock(self):
        row=self.sec.get()
        if row and row['pin_hash'] and self.lock.expired():
            dlg=PinDialog(self.sec,self);dlg.exec();self.lock.touch()
    def show_page(self,name):
        self.lock.touch()
        if name in self.pages:self.stack.setCurrentWidget(self.pages[name]);self._mark_nav(name);return
        factory={'Dashboard':self.dashboard,'Pacientes':self.patients,'Agenda':self.agenda,'Biblioteca':self.library,'Alimentos':self.foods,'Crescimento WHO':self.growth,'Materno-infantil':self.maternal,'Receitas':self.recipes,'Templates':self.templates,'Protocolos':self.protocols,'Configurações':self.settings}.get(name)
        if not factory:return
        w=factory();self.pages[name]=w;self.stack.addWidget(w);self.stack.setCurrentWidget(w);self._mark_nav(name)
    def _mark_nav(self,name):
        for n,b in self.nav.items():b.setProperty('active',n==name);b.style().unpolish(b);b.style().polish(b)
    def page(self,title,subtitle=''):
        w=QWidget();v=QVBoxLayout(w);v.setContentsMargins(26,22,26,22);v.setSpacing(14);h=QLabel(title);h.setObjectName('pageTitle');v.addWidget(h)
        if subtitle:
            s=QLabel(subtitle);s.setObjectName('pageSubtitle');s.setWordWrap(True);v.addWidget(s)
        return w,v
    def dashboard(self):
        w,v=self.page('Dashboard','Visão geral da sua clínica e das ações que precisam de atenção hoje.')
        patients=len(self.pr.list());today=date.today();today_s=today.isoformat();consults=self.ag.list(today_s,today_s);upcoming=self.ag.list(today_s,(today+timedelta(days=7)).isoformat());pending_actions=collect_pending_actions(self.pr.db,today);plan_pending=[a for a in pending_actions if a['kind']=='plan_not_sent'];objectives=self.ag.objective_distribution()
        grid=QGridLayout();stats=[('Consultas de hoje',len(consults),'Agenda do dia'),('Pacientes ativos',patients,'Prontuários cadastrados'),('Retornos próximos',len(upcoming),'Próximos 7 dias'),('Pendências',len(pending_actions),'Ações clínicas e operacionais')]
        for i,(a,b,c) in enumerate(stats):grid.addWidget(StatCard(a,b,c),0,i)
        v.addLayout(grid)
        body=QGridLayout();body.setColumnStretch(0,2);body.setColumnStretch(1,2);body.setColumnStretch(2,2)
        consult_card=Card();consult_card.body.addWidget(section_title('Consultas de hoje'))
        if consults:
            for a in consults[:7]:consult_card.body.addWidget(QLabel(f"{a['hora']}   {a['paciente_nome']}   •   {a['tipo']}   •   {a['status']}"))
        else:consult_card.body.addWidget(muted('Nenhuma consulta agendada para hoje.'))
        consult_card.body.addWidget(button('Ver agenda completa',lambda:self.show_page('Agenda')));body.addWidget(consult_card,0,0)
        patient_card=Card();patient_card.body.addWidget(section_title('Pacientes'))
        recent=self.pr.list()[:6]
        for p in recent:patient_card.body.addWidget(QLabel(f"{p['nome']}   •   {age_label(p['data_nascimento'])}"))
        if not recent:patient_card.body.addWidget(muted('Cadastre o primeiro paciente para começar.'))
        patient_card.body.addWidget(button('Ver todos os pacientes',lambda:self.show_page('Pacientes')));body.addWidget(patient_card,0,1)
        alert_card=Card();alert_card.body.addWidget(section_title('Pendências inteligentes'))
        if pending_actions:
            for a in pending_actions[:7]:alert_card.body.addWidget(QLabel(f"{a['patient_name']} • {a['title']}"));alert_card.body.addWidget(muted(a['detail']))
        else:alert_card.body.addWidget(muted('Nenhuma pendência clínica ou operacional identificada.'))
        body.addWidget(alert_card,0,2)
        v.addLayout(body)
        insights=QHBoxLayout();dist_card=Card();dist_card.body.addWidget(section_title('Distribuição de objetivos'));total_obj=sum(objectives.values())
        if objectives:
            for name,count in objectives.items():dist_card.body.addWidget(QLabel(f"{name}: {(count/total_obj*100):.0f}% ({count})"))
        else:dist_card.body.addWidget(muted('Os objetivos aparecerão após as consultas guiadas.'))
        adherence=Card();adherence.body.addWidget(section_title('Adesão aos planos'));adherence.body.addWidget(QLabel('—'));adherence.body.addWidget(muted('Sem dados suficientes de acompanhamento para calcular adesão.'));insights.addWidget(dist_card,1);insights.addWidget(adherence,1);v.addLayout(insights)
        lower=Card();lower.body.addWidget(section_title('Retornos próximos'))
        returns=[a for a in upcoming if a['data']>today_s]
        if returns:
            row=QHBoxLayout()
            for a in returns[:6]:
                c=Card(soft=True);c.body.addWidget(QLabel(a['paciente_nome']));c.body.addWidget(muted(f"{a['data']} • {a['hora']}"));row.addWidget(c)
            lower.body.addLayout(row)
        else:lower.body.addWidget(muted('Nenhum retorno nos próximos 7 dias.'))
        v.addWidget(lower);v.addStretch();return w
    def new_patient(self):
        d=NewPatient(self)
        if d.exec()==QDialog.Accepted:
            try:self.pr.create(*d.values());self.refresh_patients()
            except Exception as e:show_error(self,'Paciente',e)
    def patients(self):
        w,v=self.page('Pacientes','Prontuário longitudinal, avaliações, planos e evolução em um único workspace.');row=QHBoxLayout();self.patient_search=QLineEdit();self.patient_search.setPlaceholderText('Buscar paciente por nome');self.patient_search.textChanged.connect(self.refresh_patients);row.addWidget(self.patient_search,1);row.addWidget(button('Novo paciente',self.new_patient));row.addWidget(button('Nova consulta',self.new_consultation,True));v.addLayout(row);self.patient_table=QTableWidget(0,5);self.patient_table.setHorizontalHeaderLabels(['ID','Nome','Sexo','Nascimento','Telefone']);self.patient_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);self.patient_table.cellDoubleClicked.connect(lambda *_:self.open_patient());v.addWidget(self.patient_table);self.patient_empty=EmptyState('Nenhum paciente encontrado','Cadastre um novo paciente ou ajuste a busca.');v.addWidget(self.patient_empty);v.addWidget(button('Abrir prontuário selecionado',self.open_patient));self.refresh_patients();return w
    def refresh_patients(self):
        if not hasattr(self,'patient_table'):return
        rows=self.pr.list(self.patient_search.text() if hasattr(self,'patient_search') else '');self.patient_table.setRowCount(len(rows));self.patient_table.setVisible(bool(rows));self.patient_empty.setVisible(not bool(rows)) if hasattr(self,'patient_empty') else None
        for r,p in enumerate(rows):
            sex={'F':'Feminino','M':'Masculino'}.get(p['sexo'],p['sexo'])
            for c,x in enumerate([p['id'],p['nome'],sex,p['data_nascimento'],p['telefone']]):self.patient_table.setItem(r,c,item(x))
    def open_patient(self):
        r=self.patient_table.currentRow()
        if r>=0:PatientDialog(int(self.patient_table.item(r,0).text()),self).exec();self.refresh_patients()
    def new_consultation(self):
        pats=self.pr.list()
        if not pats:QMessageBox.information(self,'Nova consulta','Cadastre um paciente antes de iniciar uma consulta.');return
        try:
            from .consultation_dialog import ConsultationDialog
            dlg=ConsultationDialog(pats,self.ag,parent=self)
            if dlg.exec()==QDialog.Accepted:
                self.pages.pop('Dashboard',None);self.pages.pop('Agenda',None);self.show_page('Dashboard')
        except Exception as e:show_error(self,'Nova consulta',e)
    def agenda(self):
        w,v=self.page('Agenda','Selecione uma data no calendário e acompanhe consultas, retornos e status.');split=QHBoxLayout();self.ag_calendar=QCalendarWidget();self.ag_calendar.setObjectName('agendaCalendar');self.ag_calendar.setGridVisible(True);self.ag_calendar.selectionChanged.connect(self._agenda_calendar_changed);split.addWidget(self.ag_calendar,1)
        right=QVBoxLayout();filters=QHBoxLayout();self.ag_start=QLineEdit(date.today().isoformat());self.ag_end=QLineEdit((date.today()+timedelta(days=30)).isoformat());self.ag_status=QComboBox();self.ag_status.addItems(['Todos','Agendada','Realizada','Faltou','Cancelada','Remarcada']);filters.addWidget(self.ag_start);filters.addWidget(self.ag_end);filters.addWidget(self.ag_status);filters.addWidget(button('Filtrar',self.refresh_agenda));filters.addWidget(button('Agendar',self.new_appointment,True));right.addLayout(filters);self.ag_table=QTableWidget(0,7);self.ag_table.setHorizontalHeaderLabels(['ID','Data','Hora','Paciente','Tipo','Status','Duração']);self.ag_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);right.addWidget(self.ag_table);self.agenda_empty=EmptyState('Nenhuma consulta no período','Selecione outra data ou agende uma nova consulta.');right.addWidget(self.agenda_empty);actions=QHBoxLayout()
        for status in ['Realizada','Faltou','Cancelada','Remarcada']:actions.addWidget(button(status,lambda checked=False,s=status:self.set_appointment_status(s)))
        actions.addStretch();right.addLayout(actions);split.addLayout(right,3);v.addLayout(split);self.refresh_agenda();return w
    def _agenda_calendar_changed(self):
        d=self.ag_calendar.selectedDate().toString('yyyy-MM-dd');self.ag_start.setText(d);self.ag_end.setText(d);self.refresh_agenda()
    def refresh_agenda(self):
        if not hasattr(self,'ag_table'):return
        try:rows=self.ag.list(self.ag_start.text(),self.ag_end.text(),None if self.ag_status.currentText()=='Todos' else self.ag_status.currentText())
        except Exception:return
        self.ag_table.setRowCount(len(rows));self.ag_table.setVisible(bool(rows));self.agenda_empty.setVisible(not bool(rows)) if hasattr(self,'agenda_empty') else None
        for r,a in enumerate(rows):
            for c,x in enumerate([a['id'],a['data'],a['hora'],a['paciente_nome'],a['tipo'],a['status'],a['duracao_min']]):self.ag_table.setItem(r,c,item(x))
    def new_appointment(self):
        pats=self.pr.list()
        if not pats:QMessageBox.information(self,'Agenda','Cadastre um paciente primeiro.');return
        choices=[f"{p['id']} - {p['nome']}" for p in pats];chosen,ok=QInputDialog.getItem(self,'Paciente','Paciente',choices,0,False)
        if not ok:return
        pid=int(chosen.split(' - ',1)[0]);d=QDialog(self);d.setWindowTitle('Nova consulta');f=QFormLayout(d);dt=QDateEdit();dt.setCalendarPopup(True);dt.setDate(QDate.currentDate());dt.setDisplayFormat('dd/MM/yyyy');hr=QLineEdit('09:00');typ=QComboBox();typ.addItems(['Consulta','Retorno','Teleconsulta']);dur=QLineEdit('60');obs=QTextEdit();obs.setFixedHeight(70);return_of=QLineEdit();return_of.setPlaceholderText('ID da consulta anterior (opcional)');freq=QComboBox();freq.addItems(['Não repetir','Semanal','Quinzenal','Mensal']);until=QDateEdit();until.setCalendarPopup(True);until.setDate(QDate.currentDate().addMonths(1));f.addRow('Data',dt);f.addRow('Hora',hr);f.addRow('Tipo',typ);f.addRow('Duração min',dur);f.addRow('Retorno de',return_of);f.addRow('Observações',obs);f.addRow('Recorrência',freq);f.addRow('Até',until);f.addRow('',button('Salvar',d.accept,True))
        if d.exec()==QDialog.Accepted:
            rec=None
            if freq.currentText()!='Não repetir':rec={'frequencia':freq.currentText(),'intervalo':1,'ate_data':until.date().toString('yyyy-MM-dd')}
            rid=int(return_of.text()) if return_of.text().strip().isdigit() else None
            self.ag.create(pid,dt.date().toString('yyyy-MM-dd'),hr.text().strip(),typ.currentText(),observacoes=obs.toPlainText().strip(),duration=int(number(dur.text(),'Duração',5,1440)),return_of=rid,recurrence=rec);self.refresh_agenda()
    def set_appointment_status(self,status):
        r=self.ag_table.currentRow()
        if r>=0:self.ag.set_status(int(self.ag_table.item(r,0).text()),status);self.refresh_agenda()
    def library(self):
        w,v=self.page('Biblioteca','Alimentos, receitas, templates, protocolos e migração de dados em um único lugar.');tabs=QTabWidget();tabs.addTab(self.foods(),'Alimentos');tabs.addTab(self.recipes(),'Receitas');tabs.addTab(self.templates(),'Templates');tabs.addTab(self.protocols(),'Protocolos');tabs.addTab(self.import_center_page(),'Central de importação');v.addWidget(tabs);return w
    def import_center_page(self):
        w=QWidget();v=QVBoxLayout(w);v.addWidget(section_title('Central de importação'));v.addWidget(muted('Importe pacientes, avaliações e exames por CSV/XLSX. O NutriDesk sempre mostra uma prévia antes de gravar.'));v.addWidget(button('Abrir Central de importação',lambda:ImportDialog(self.pr.db,self).exec(),True));v.addStretch();return w
    def foods(self):
        w,v=self.page('Alimentos','Base TACO + importações CSV sem apagar a base original.');row=QHBoxLayout();self.food_search=QLineEdit();self.food_search.setPlaceholderText('Buscar alimento');self.food_search.textChanged.connect(self.refresh_foods);row.addWidget(self.food_search);row.addWidget(button('Importar CSV',self.import_food_csv));v.addLayout(row);self.food_table=QTableWidget(0,7);self.food_table.setHorizontalHeaderLabels(['ID','Descrição','kcal','Proteína','Carboidrato','Lipídios','Origem']);self.food_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);v.addWidget(self.food_table);self.refresh_foods();return w
    def refresh_foods(self):
        if not hasattr(self,'food_table'):return
        rows=self.fr.search(self.food_search.text() if hasattr(self,'food_search') else '',100);self.food_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,y in enumerate([x['id'],x['descricao'],x['kcal'],x['proteina'],x['carboidrato'],x['lipideos'],x['origem']]):self.food_table.setItem(r,c,item(y))
    def import_food_csv(self):
        path,_=QFileDialog.getOpenFileName(self,'CSV de alimentos','','CSV (*.csv)')
        if path:
            try:res=self.fr.import_csv(path);QMessageBox.information(self,'Importação',f"{res['valid']} linhas importadas; {res['invalid']} inválidas.");self.refresh_foods()
            except Exception as e:show_error(self,'Importação',e)
    def growth(self):
        w,v=self.page('Crescimento WHO','WHO Child Growth Standards 2006 + Growth Reference 2007; z-score e percentil.');pats=self.pr.list();self.g_patient=QComboBox();self.g_patient.addItems([f"{p['id']} - {p['nome']}" for p in pats]);self.g_date=QLineEdit(date.today().isoformat());self.g_weight=QLineEdit();self.g_height=QLineEdit();f=QFormLayout();f.addRow('Paciente',self.g_patient);f.addRow('Data da medida',self.g_date);f.addRow('Peso kg',self.g_weight);f.addRow('Altura cm',self.g_height);f.addRow('',button('Calcular WHO e salvar',self.calculate_growth,True));v.addLayout(f);self.g_result=QTextEdit();self.g_result.setReadOnly(True);v.addWidget(self.g_result);return w
    def calculate_growth(self):
        try:
            pid=int(self.g_patient.currentText().split(' - ',1)[0]);p=self.pr.get(pid);res=self.gs.assess_and_save(pid,p['sexo'],p['data_nascimento'],iso_date(self.g_date.text()),number(self.g_weight.text(),'Peso',1,300,True),number(self.g_height.text(),'Altura',30,230,True));self.g_result.setPlainText('\n'.join(f"{k}: z={v.zscore:.2f}, P{v.percentile:.1f} — {v.classification}" for k,v in res.items() if v))
        except Exception as e:show_error(self,'Crescimento WHO',e)
    def maternal(self):
        from nutridesktop.clinical.maternal import gestational_weight_range,maternal_reference
        w,v=self.page('Materno-infantil','Ganho de peso gestacional e referências estruturadas para gestação/lactação.');f=QFormLayout();self.m_weight=QLineEdit();self.m_height=QLineEdit();self.m_phase=QComboBox();self.m_phase.addItems(['1º trimestre','2º trimestre','3º trimestre','Lactação 0-6 meses']);f.addRow('Peso pré-gestacional kg',self.m_weight);f.addRow('Altura cm',self.m_height);f.addRow('Fase',self.m_phase);f.addRow('',button('Calcular referência',self.calculate_maternal,True));v.addLayout(f);self.m_result=QTextEdit();self.m_result.setReadOnly(True);v.addWidget(self.m_result);return w
    def calculate_maternal(self):
        try:
            from nutridesktop.clinical.maternal import gestational_weight_range,maternal_reference
            wt=number(self.m_weight.text(),'Peso',20,300)
            ht=number(self.m_height.text(),'Altura',100,230)
            bmi=wt/(ht/100)**2
            gain=gestational_weight_range(bmi)
            ref=maternal_reference(self.m_phase.currentText())
            dri=', '.join(f"{v.nutrient}: {v.value} {v.unit}" for v in ref['dri'].values())
            text=(f"IMC pré-gestacional: {bmi:.1f} ({gain['classification']})\n"
                  f"Ganho total de referência: {gain['gain_min']}–{gain['gain_max']} kg\n"
                  f"Acréscimo energético de referência: {ref['energy_extra_kcal']} kcal/dia\n{dri}")
            self.m_result.setPlainText(text)
        except Exception as e:show_error(self,'Materno-infantil',e)
    def recipes(self):
        w,v=self.page('Receitas','Receitas compostas com categoria, tags, modo de preparo e nutrientes por porção.');form=QFormLayout();self.rec_name=QLineEdit();self.rec_name.setPlaceholderText('Nome da receita');self.rec_category=QLineEdit();self.rec_category.setPlaceholderText('Categoria da receita');self.rec_tags=QLineEdit();self.rec_tags.setPlaceholderText('Tags: proteica, rápida, vegetariana…');self.rec_serv=QLineEdit('1');self.rec_method=QTextEdit();self.rec_method.setPlaceholderText('Modo de preparo');self.rec_method.setFixedHeight(80);form.addRow('Nome',self.rec_name);form.addRow('Categoria da receita',self.rec_category);form.addRow('Tags',self.rec_tags);form.addRow('Porções',self.rec_serv);form.addRow('Modo de preparo',self.rec_method);form.addRow('',button('Criar receita',self.create_recipe,True));v.addLayout(form);self.rec_table=QTableWidget(0,7);self.rec_table.setHorizontalHeaderLabels(['ID','Nome','Categoria','Tags','Porções','kcal/porção','Proteína/porção']);self.rec_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);v.addWidget(self.rec_table);ing=QHBoxLayout();self.rec_food=QLineEdit();self.rec_food.setPlaceholderText('Buscar ingrediente');self.rec_grams=QLineEdit('100');ing.addWidget(self.rec_food);ing.addWidget(self.rec_grams);ing.addWidget(button('Adicionar ingrediente',self.add_recipe_ingredient));v.addLayout(ing);self.refresh_recipes();return w
    def refresh_recipes(self):
        if not hasattr(self,'rec_table'):return
        rows=self.rr.list();self.rec_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            n=recipe_nutrients(x['id'],self.rr)
            for c,y in enumerate([x['id'],x['nome'],x['categoria'] or '',x['tags'] or '',x['porcoes'],round(n.get('kcal',0),1),round(n.get('proteina',0),1)]):self.rec_table.setItem(r,c,item(y))
    def create_recipe(self):
        try:self.rr.create(required_text(self.rec_name.text(),'Receita'),self.rec_category.text().strip(),number(self.rec_serv.text(),'Porções',1,100),self.rec_method.toPlainText().strip(),self.rec_tags.text().strip());self.refresh_recipes();self.rec_name.clear();self.rec_method.clear()
        except Exception as e:show_error(self,'Receita',e)
    def add_recipe_ingredient(self):
        r=self.rec_table.currentRow()
        if r<0:QMessageBox.information(self,'Receita','Selecione uma receita primeiro.');return
        dlg=FoodSearchDialog(self.fr,self,'Selecionar ingrediente');dlg.query.setText(self.rec_food.text().strip())
        if dlg.exec()!=QDialog.Accepted or not dlg.selected:return
        self.rr.add_ingredient(int(self.rec_table.item(r,0).text()),dlg.selected['id'],number(self.rec_grams.text(),'Gramas',0.1,10000));self.rec_food.setText(dlg.selected['descricao']);self.refresh_recipes()
    def templates(self):
        w,v=self.page('Templates de documentos','Biblioteca visual para planos, relatórios, orientações, receitas e outros documentos. Escolha um Template padrão por tipo.');self.t_table=QTableWidget(0,6);self.t_table.setHorizontalHeaderLabels(['ID','Tipo','Nome','Estilo','Especialidades','Padrão']);self.t_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);self.t_table.cellDoubleClicked.connect(lambda *_:self.load_template());v.addWidget(self.t_table);self.t_name=QLineEdit();self.t_type=QComboBox();self.t_type.addItems(['Avaliação','Plano','Orientação','Receita','Encaminhamento','Evolução','Relatório']);self.t_style=QComboBox();[(self.t_style.addItem(cfg['label'],key)) for key,cfg in STYLE_PRESETS.items()];self.t_tags=QLineEdit();self.t_tags.setPlaceholderText('Ex.: materno_infantil, esportiva');self.t_default=QCheckBox('Usar como Template padrão deste tipo');self.t_content=QTextEdit();self.t_content.setPlaceholderText('Conteúdo do template');self._editing_template_id=None;f=QFormLayout();f.addRow('Nome',self.t_name);f.addRow('Tipo',self.t_type);f.addRow('Estilo visual',self.t_style);f.addRow('Especialidades',self.t_tags);f.addRow('',self.t_default);f.addRow('Conteúdo',self.t_content);actions=QHBoxLayout();actions.addWidget(button('Salvar template',self.save_template,True));actions.addWidget(button('Carregar selecionado para editar',self.load_template));actions.addWidget(button('Novo',self.clear_template));f.addRow('',actions);v.addLayout(f);v.addWidget(button('Gerar documento do template selecionado para um paciente',self.generate_template_document));self.refresh_templates();return w
    def refresh_templates(self):
        if not hasattr(self,'t_table'):return
        rows=self.tr.list();self.t_table.setRowCount(len(rows))
        for r,t in enumerate(rows):
            style=STYLE_PRESETS.get(t['style_key'] or 'clean_clinical',{}).get('label',t['style_key'])
            for c,x in enumerate([t['id'],t['tipo'],t['nome'],style,t['specialty_tags'] or '','Sim' if t['is_default'] else '']):self.t_table.setItem(r,c,item(x))
    def save_template(self):
        try:
            self._editing_template_id=self.tr.save(required_text(self.t_name.text(),'Nome'),self.t_type.currentText(),required_text(self.t_content.toPlainText(),'Conteúdo',10000),self._editing_template_id,style_key=self.t_style.currentData(),specialty_tags=self.t_tags.text().strip(),is_default=self.t_default.isChecked());self.refresh_templates();QMessageBox.information(self,'Template','Template salvo.')
        except Exception as e:show_error(self,'Template',e)
    def load_template(self):
        r=self.t_table.currentRow()
        if r<0:return
        tid=int(self.t_table.item(r,0).text());template=next((x for x in self.tr.list() if x['id']==tid),None)
        if not template:return
        self._editing_template_id=tid;self.t_name.setText(template['nome']);self.t_type.setCurrentText(template['tipo']);idx=self.t_style.findData(template['style_key'] or 'clean_clinical');self.t_style.setCurrentIndex(max(idx,0));self.t_tags.setText(template['specialty_tags'] or '');self.t_default.setChecked(bool(template['is_default']));self.t_content.setPlainText(template['conteudo'])
    def clear_template(self):
        self._editing_template_id=None;self.t_name.clear();self.t_content.clear();self.t_type.setCurrentIndex(0);self.t_style.setCurrentIndex(0);self.t_tags.clear();self.t_default.setChecked(False)
    def generate_template_document(self):
        from nutridesktop.services.reports import generate_from_template
        from nutridesktop.services.documents import DocumentService
        r=self.t_table.currentRow()
        if r<0:return
        tid=int(self.t_table.item(r,0).text());template=next((x for x in self.tr.list() if x['id']==tid),None)
        pats=self.pr.list()
        if not template or not pats:return
        labels=[f"{p['id']} - {p['nome']}" for p in pats];choice,ok=QInputDialog.getItem(self,'Paciente','Paciente',labels,0,False)
        if not ok:return
        pid=int(choice.split(' - ',1)[0]);patient=self.pr.get(pid);content,ok2=QInputDialog.getMultiLineText(self,'Conteúdo','Conteúdo/observação para {{conteudo}}')
        if not ok2:return
        rendered=render_template(template['conteudo'],{'paciente':dict(patient),'data':date.today().isoformat(),'conteudo':content,'destino':''});path,_=QFileDialog.getSaveFileName(self,'Salvar documento',f"{template['tipo']}_{pid}.pdf",'PDF (*.pdf)')
        if path:generate_from_template(pid,path,rendered,template['nome']);DocumentService().import_file(pid,path,template['tipo']);QMessageBox.information(self,'Template','Documento gerado e anexado.')
    def protocols(self):
        w,v=self.page('Protocolos clínicos versionados','Cada alteração exige nova versão; fonte, população-alvo e conteúdo anterior permanecem rastreáveis.');self.p_table=QTableWidget(0,5);self.p_table.setHorizontalHeaderLabels(['Slug','Versão','Título','Público','Fonte']);self.p_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);self.p_table.cellDoubleClicked.connect(lambda *_:self.load_protocol());v.addWidget(self.p_table);self.p_slug=QLineEdit();self.p_version=QLineEdit();self.p_title=QLineEdit();self.p_source=QLineEdit();self.p_target=QLineEdit();self.p_content=QTextEdit();f=QFormLayout();f.addRow('Identificador',self.p_slug);f.addRow('Nova versão',self.p_version);f.addRow('Título',self.p_title);f.addRow('Fonte',self.p_source);f.addRow('População-alvo',self.p_target);f.addRow('Conteúdo',self.p_content);actions=QHBoxLayout();actions.addWidget(button('Salvar como nova versão',self.save_protocol,True));actions.addWidget(button('Carregar selecionado',self.load_protocol));actions.addWidget(button('Limpar',self.clear_protocol));f.addRow('',actions);v.addLayout(f);self.refresh_protocols();return w
    def refresh_protocols(self):
        if not hasattr(self,'p_table'):return
        rows=self.pro.list();self.p_table.setRowCount(len(rows))
        for r,p in enumerate(rows):
            for c,x in enumerate([p['slug'],p['versao'],p['titulo'],p['publico_alvo'],p['fonte']]):self.p_table.setItem(r,c,item(x))
    def load_protocol(self):
        r=self.p_table.currentRow()
        if r<0:return
        slug=self.p_table.item(r,0).text();version=self.p_table.item(r,1).text();row=next((x for x in self.pro.list(slug) if x['versao']==version),None)
        if not row:return
        self.p_slug.setText(row['slug']);self.p_version.setText(row['versao']);self.p_title.setText(row['titulo']);self.p_source.setText(row['fonte'] or '');self.p_target.setText(row['publico_alvo'] or '');self.p_content.setPlainText(row['conteudo'])
    def clear_protocol(self):
        for field in (self.p_slug,self.p_version,self.p_title,self.p_source,self.p_target):field.clear()
        self.p_content.clear()
    def save_protocol(self):
        try:
            self.pro.save(required_text(self.p_slug.text(),'Identificador'),required_text(self.p_version.text(),'Versão'),required_text(self.p_title.text(),'Título'),self.p_source.text().strip(),self.p_target.text().strip(),required_text(self.p_content.toPlainText(),'Conteúdo',20000));self.refresh_protocols();QMessageBox.information(self,'Protocolo','Nova versão salva. Versões anteriores foram preservadas.')
        except Exception as e:show_error(self,'Protocolo',e)
    def settings(self):
        w,v=self.page('Configurações','Preferências do consultório, segurança, backup, dados e recursos avançados.')
        tabs=QTabWidget();tabs.setObjectName('settingsTabs');self.settings_tabs=tabs
        def tab(title):
            page=QWidget();lay=QVBoxLayout(page);lay.setContentsMargins(8,14,8,8);lay.setSpacing(12);tabs.addTab(page,title);return page,lay
        general,g=tab('Geral');g.addWidget(section_title('NutriDesk'));g.addWidget(muted(f'Versão {APP_VERSION} • dados armazenados localmente'));g.addWidget(muted('Atalhos: Ctrl+N nova consulta • Ctrl+K buscar paciente • Ctrl+P pacientes'));g.addStretch()
        clinic,c=tab('Consultório');c.addWidget(section_title('Preferências do consultório'));c.addWidget(muted('Identidade, dados profissionais e padrões clínicos serão usados nos relatórios e documentos.'));c.addStretch()
        reports,r=tab('Relatórios');r.addWidget(section_title('Relatórios e documentos'));r.addWidget(muted('Escolha o Template padrão para cada tipo. O padrão ainda pode ser substituído ao gerar um documento.'));self.report_default_selectors={}
        for typ in ['Plano','Relatório','Orientação','Receita']:
            rowt=QHBoxLayout();rowt.addWidget(QLabel(f'Template padrão — {typ}'));combo=QComboBox();templates=self.tr.list(typ);[(combo.addItem(t['nome'],t['id'])) for t in templates];default=self.tr.default(typ);idx=combo.findData(default['id']) if default else -1;combo.setCurrentIndex(max(idx,0));rowt.addWidget(combo,1);rowt.addWidget(button('Salvar',lambda checked=False,t=typ,c=combo:self.save_default_template(t,c)));r.addLayout(rowt);self.report_default_selectors[typ]=combo
        r.addStretch()
        security,sec=tab('Segurança');sec.addWidget(section_title('Acesso local'));row2=QHBoxLayout();row2.addWidget(button('Definir/alterar PIN',self.set_pin));row2.addWidget(button('Alterar auto-lock',self.set_autolock));row2.addStretch();sec.addLayout(row2);sec.addWidget(muted('Proteção avançada do Windows (EFS) fica na aba Avançado.'));sec.addStretch()
        backup_tab,bk=tab('Backup');self.settings_backup_layout=bk;bk.addWidget(section_title('Backup local'));row=QHBoxLayout();row.addWidget(button('Criar backup',self.backup,True));row.addWidget(button('Validar backup',self.validate_bak));row.addWidget(button('Restaurar backup',self.restore_bak));row.addStretch();bk.addLayout(row);bk.addWidget(muted('Backups podem ser protegidos por senha e são verificados por checksum.'));bk.addStretch()
        data_tab,dl=tab('Dados e portabilidade');self.settings_data_layout=dl;dl.addWidget(section_title('Dados locais'));dl.addWidget(muted(f'Banco: {DB_PATH}\nPasta de dados: {DATA_DIR}'));dl.addStretch()
        advanced,adv=tab('Avançado');self.settings_advanced_layout=adv;adv.addWidget(section_title('Recursos técnicos'));row3=QHBoxLayout();row3.addWidget(button('Ativar EFS',self.enable_local_encryption));row3.addWidget(button('Verificar EFS',self.local_encryption_status));row3.addWidget(button('Desativar EFS',self.disable_local_encryption));row3.addStretch();adv.addLayout(row3);adv.addWidget(muted('EFS é opcional e depende da edição do Windows/NTFS.'));adv.addStretch()
        v.addWidget(tabs);return w
    def save_default_template(self,typ,combo):
        template_id=combo.currentData()
        if template_id:self.tr.set_default(int(template_id),typ);QMessageBox.information(self,'Template padrão',f'Template padrão de {typ} atualizado.')
    def backup(self):
        path,_=QFileDialog.getSaveFileName(self,'Backup',f"nutridesktop_{date.today().isoformat()}.nbak",'NutriDesk Backup (*.nbak);;ZIP (*.zip)')
        if not path:return
        password,ok=QInputDialog.getText(self,'Criptografia','Senha opcional do backup',QLineEdit.Password)
        if ok:create_backup(path,password or None);QMessageBox.information(self,'Backup','Backup criado e validável por checksum.')
    def validate_bak(self):
        path,_=QFileDialog.getOpenFileName(self,'Backup','','Backups (*.nbak *.zip)');
        if not path:return
        password,_=QInputDialog.getText(self,'Senha','Senha se o backup estiver criptografado',QLineEdit.Password)
        try:info=validate_backup(path,password or None);QMessageBox.information(self,'Backup',f"Backup íntegro. Schema {info['schema_version']}.")
        except Exception as e:show_error(self,'Backup inválido',e)
    def restore_bak(self):
        path,_=QFileDialog.getOpenFileName(self,'Restaurar','','Backups (*.nbak *.zip)');
        if not path:return
        if QMessageBox.question(self,'Restaurar','Validar e substituir dados atuais? Há rollback automático se falhar.')!=QMessageBox.Yes:return
        password,_=QInputDialog.getText(self,'Senha','Senha se necessário',QLineEdit.Password)
        try:restore_backup(path,password or None);QMessageBox.information(self,'Restaurado','Restauração concluída. Reinicie o aplicativo.')
        except Exception as e:show_error(self,'Restauração',e)
    def set_pin(self):
        pin,ok=QInputDialog.getText(self,'PIN','Novo PIN (mín. 4 caracteres)',QLineEdit.Password)
        if ok:
            try:self.sec.set_pin(pin);QMessageBox.information(self,'PIN','PIN salvo com hash scrypt.')
            except Exception as e:show_error(self,'PIN',e)
    def set_autolock(self):
        n,ok=QInputDialog.getInt(self,'Auto-lock','Minutos sem atividade',15,1,240)
        if ok:self.sec.set_auto_lock(n);self.lock.timeout=n*60
    def enable_local_encryption(self):
        try:
            self.local_protection.enable();QMessageBox.information(self,'Criptografia local','EFS solicitado para a pasta de dados. Use Verificar EFS para confirmar a política do Windows.')
        except Exception as e:show_error(self,'Criptografia local',e)
    def local_encryption_status(self):
        try:QMessageBox.information(self,'Status EFS',self.local_protection.status()[-4000:])
        except Exception as e:show_error(self,'Status EFS',e)
    def disable_local_encryption(self):
        if QMessageBox.question(self,'Desativar EFS','Descriptografar a pasta local de dados?')!=QMessageBox.Yes:return
        try:self.local_protection.disable();QMessageBox.information(self,'Criptografia local','Solicitação de descriptografia concluída.')
        except Exception as e:show_error(self,'Criptografia local',e)
