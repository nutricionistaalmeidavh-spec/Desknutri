from __future__ import annotations
from datetime import date
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QPushButton,QLineEdit,QTableWidget,QHeaderView,QMessageBox,QScrollArea,QWidget
from .common import button,item,show_error
from nutridesktop.clinical.packs import PACK_DEFINITIONS,pack_defaults,SIBO_STATUSES
from nutridesktop.data.repositories import ClinicalPackRepository
from nutridesktop.services.clinical_packs import save_pack_snapshot,latest_pack_snapshot

FIELD_LABELS={
 'dpp':'DPP','idade_gestacional_semanas':'Idade gestacional (semanas)','peso_pre_gestacional':'Peso pré-gestacional (kg)','fase_introducao_alimentar':'Introdução alimentar',
 'modalidade':'Modalidade','frequencia_semanal':'Treinos/semana','volume_treino':'Volume de treino','meta_hidratacao_ml':'Meta de hidratação (mL)',
 'condicoes':'Condições registradas','estagio_registrado':'Estágio renal registrado','fase_consistencia':'Fase/consistência alimentar','suplementos':'Suplementos',
 'bristol':'Escala de Bristol (1–7)','fase_fodmap':'Fase FODMAP','alimento_sintoma':'Correlação alimento × sintoma','score_sintomas':'Score de sintomas (0–10)',
 'subtipo_documentado':'Subtipo documentado','teste_externo':'Teste/registro externo','tratamento_informado':'Tratamento informado','fase_dietetica':'Fase dietética','reintroducoes':'Reintroduções'
}

class ClinicalPacksDialog(QDialog):
    def __init__(self,patient_id,database=None,parent=None):
        super().__init__(parent);self.patient_id=patient_id;self.repo=ClinicalPackRepository(database) if database else ClinicalPackRepository();self.setWindowTitle('Packs clínicos');self.resize(940,700)
        root=QVBoxLayout(self);top=QHBoxLayout();self.pack=QComboBox();[(self.pack.addItem(v['label'],k)) for k,v in PACK_DEFINITIONS.items()];top.addWidget(self.pack);top.addWidget(button('Ativar pack',self.activate,True));top.addStretch();root.addLayout(top)
        self.active_table=QTableWidget(0,3);self.active_table.setHorizontalHeaderLabels(['Pack','Status','Último acompanhamento']);self.active_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);root.addWidget(self.active_table)
        self.form_widget=QWidget();self.form=QFormLayout(self.form_widget);root.addWidget(self.form_widget);self.fields={};self.pack.currentIndexChanged.connect(self.build_form);root.addWidget(button('Salvar acompanhamento',self.save_snapshot,True));self.build_form();self.refresh_active()
    def current_slug(self):return self.pack.currentData()
    def build_form(self):
        while self.form.rowCount():self.form.removeRow(0)
        self.fields={};slug=self.current_slug();defaults=pack_defaults(slug);latest=latest_pack_snapshot(self.patient_id,slug,self.repo) or {}
        for key in PACK_DEFINITIONS[slug]['fields']:
            if key=='status' and slug=='sibo':
                field=QComboBox();field.addItems(SIBO_STATUSES);field.setCurrentText(str(latest.get(key,defaults.get(key,''))))
            else:
                field=QLineEdit();value=latest.get(key,defaults.get(key,''));
                if isinstance(value,list):value=', '.join(map(str,value))
                field.setText(str(value) if value is not None else '')
            self.fields[key]=field;self.form.addRow(FIELD_LABELS.get(key,key.replace('_',' ').title()),field)
        if slug=='sibo':self.form.addRow('',QPushButton('SIBO: registro e acompanhamento; o NutriDesk não realiza diagnóstico automático.'))
    def activate(self):
        self.repo.activate(self.patient_id,self.current_slug());self.refresh_active();QMessageBox.information(self,'Packs clínicos','Pack ativado no prontuário.')
    def _value(self,key,field):
        if isinstance(field,QComboBox):return field.currentText()
        text=field.text().strip();default=pack_defaults(self.current_slug()).get(key)
        if isinstance(default,bool):return text.lower() in {'1','true','sim','s'}
        if isinstance(default,list):return [x.strip() for x in text.split(',') if x.strip()]
        if isinstance(default,(int,float)) and text:
            try:return float(text) if '.' in text else int(text)
            except ValueError:return text
        return text
    def save_snapshot(self):
        try:
            slug=self.current_slug();data={k:self._value(k,f) for k,f in self.fields.items()};self.repo.activate(self.patient_id,slug);save_pack_snapshot(self.patient_id,slug,data,date.today().isoformat(),self.repo);self.refresh_active();QMessageBox.information(self,'Packs clínicos','Acompanhamento salvo no histórico do paciente.')
        except Exception as e:show_error(self,'Packs clínicos',e)
    def refresh_active(self):
        rows=self.repo.active(self.patient_id);self.active_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            latest=self.repo.latest_record(self.patient_id,x['pack_slug']);label=PACK_DEFINITIONS.get(x['pack_slug'],{}).get('label',x['pack_slug']);day=latest['record_date'] if latest else 'Sem registro'
            for c,v in enumerate([label,'Ativo',day]):self.active_table.setItem(r,c,item(v))
