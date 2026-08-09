"""NutriDesktop - interface desktop moderna em PySide6."""
import csv
import os
import sys
from datetime import date

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFileDialog, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QScrollArea, QSplitter, QStackedWidget, QTableWidget, QTableWidgetItem, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget
)

import database as db
import licensing
import pdf_export
import formulas
import guidelines
import materno_infantil as mi
import crescimento_infantil as ci

COLORS = {
    "ink": "#202124", "muted": "#73777F", "line": "#E7E8EA", "canvas": "#FAFAFB",
    "sidebar": "#F5F1F0", "selected": "#E9E3E1", "accent": "#145C57", "accent_soft": "#E1EFEB",
    "card": "#FFFFFF", "danger": "#B42318", "warning": "#A35A00",
}

APP_STYLE = f"""
* {{ font-family: 'Segoe UI'; color: {COLORS['ink']}; font-size: 13px; }}
QMainWindow, QWidget#root {{ background: {COLORS['canvas']}; }}
QFrame#sidebar {{ background: {COLORS['sidebar']}; border-right: 1px solid {COLORS['line']}; }}
QFrame#topbar {{ background: #FFFFFF; border-bottom: 1px solid {COLORS['line']}; }}
QLabel#brand {{ font-size: 22px; font-weight: 700; }}
QLabel#pageTitle {{ font-size: 22px; font-weight: 650; }}
QLabel#pageSub {{ color: {COLORS['muted']}; font-size: 12px; }}
QPushButton {{ border: 0; border-radius: 9px; padding: 9px 12px; background: transparent; text-align: left; }}
QPushButton:hover {{ background: #F0EDEC; }}
QPushButton#navActive {{ background: {COLORS['selected']}; font-weight: 600; }}
QPushButton#primary {{ background: {COLORS['accent']}; color: white; font-weight: 600; padding: 10px 15px; }}
QPushButton#primary:hover {{ background: #0C4D48; }}
QPushButton#secondary {{ background: #FFFFFF; border: 1px solid {COLORS['line']}; font-weight: 600; }}
QLineEdit, QTextEdit, QComboBox {{ background: #FFFFFF; border: 1px solid {COLORS['line']}; border-radius: 8px; padding: 8px 10px; selection-background-color: {COLORS['accent']}; }}
QLineEdit:focus, QTextEdit:focus {{ border: 1px solid {COLORS['accent']}; }}
QFrame#card {{ background: {COLORS['card']}; border: 1px solid {COLORS['line']}; border-radius: 13px; }}
QTableWidget {{ background: #FFFFFF; border: 1px solid {COLORS['line']}; border-radius: 10px; gridline-color: transparent; }}
QHeaderView::section {{ background: #FFFFFF; color: {COLORS['muted']}; border: 0; border-bottom: 1px solid {COLORS['line']}; padding: 10px; font-weight: 600; }}
QTableWidget::item {{ border-bottom: 1px solid #F0F0F1; padding: 8px; }}
QTableWidget::item:selected {{ background: {COLORS['accent_soft']}; color: {COLORS['ink']}; }}
QTabBar::tab {{ background: transparent; padding: 10px 14px; color: {COLORS['muted']}; }}
QTabBar::tab:selected {{ color: {COLORS['accent']}; border-bottom: 2px solid {COLORS['accent']}; font-weight: 600; }}
"""


def button(text, primary=False, callback=None, object_name=None):
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setObjectName(object_name or ("primary" if primary else "secondary"))
    if callback: b.clicked.connect(callback)
    return b


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget(): item.widget().deleteLater()
        elif item.layout(): clear_layout(item.layout())


def table_item(value):
    item = QTableWidgetItem("" if value is None else str(value))
    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    return item


class MetricCard(QFrame):
    def __init__(self, label, value, note=""):
        super().__init__(); self.setObjectName("card"); self.setMinimumHeight(112)
        layout = QVBoxLayout(self); layout.setContentsMargins(16, 14, 16, 14); layout.setSpacing(5)
        label_w = QLabel(label); label_w.setStyleSheet(f"color: {COLORS['muted']}; font-size: 12px;")
        value_w = QLabel(value); value_w.setStyleSheet(f"font-size: 27px; font-weight: 700; color: {COLORS['accent']};")
        layout.addWidget(label_w); layout.addWidget(value_w)
        if note:
            n = QLabel(note); n.setStyleSheet(f"color: {COLORS['muted']}; font-size: 11px;"); layout.addWidget(n)
        layout.addStretch()


class LicenseDialog(QDialog):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Ativacao - NutriDesktop"); self.setMinimumWidth(420)
        layout = QVBoxLayout(self); layout.setContentsMargins(28, 28, 28, 28); layout.setSpacing(12)
        title = QLabel("Ative o NutriDesktop"); title.setStyleSheet("font-size: 22px; font-weight: 700;")
        layout.addWidget(title); layout.addWidget(QLabel("Digite a chave recebida. A licenca permanece salva neste computador."))
        self.key = QLineEdit(); self.key.setPlaceholderText("NUTRI-0000-0000-0000-0000-0000"); layout.addWidget(self.key)
        self.status = QLabel(""); self.status.setStyleSheet(f"color: {COLORS['danger']};"); layout.addWidget(self.status)
        activate = button("Ativar licenca", True, self.activate); layout.addWidget(activate); layout.addStretch()
    def activate(self):
        ok, message = licensing.ativar(db, self.key.text())
        if ok: self.accept()
        else: self.status.setText(message)


class PatientDialog(QDialog):
    FIELDS = ["Queixa principal", "Objetivo", "Historico clinico", "Medicamentos e suplementos", "Alergias/intolerancias", "Rotina alimentar", "Sono e estresse", "Atividade fisica", "Habito intestinal", "Observacoes e conduta"]
    def __init__(self, patient_id, parent=None):
        super().__init__(parent); self.patient_id = patient_id; self.patient = db.get_paciente(patient_id)
        self.setWindowTitle(self.patient["nome"]); self.resize(990, 700)
        root = QVBoxLayout(self); root.setContentsMargins(28, 24, 28, 24); root.setSpacing(16)
        top = QHBoxLayout(); avatar = QLabel(self.patient["nome"][:1].upper()); avatar.setAlignment(Qt.AlignCenter); avatar.setFixedSize(48,48); avatar.setStyleSheet(f"background:{COLORS['accent_soft']}; color:{COLORS['accent']}; border-radius:24px; font-size:20px; font-weight:700;")
        top.addWidget(avatar); info = QVBoxLayout(); name = QLabel(self.patient["nome"]); name.setStyleSheet("font-size:22px; font-weight:700;"); info.addWidget(name); info.addWidget(QLabel(f"{self.patient['telefone'] or 'Sem telefone'}  ?  {self.patient['email'] or 'Sem e-mail'}")); top.addLayout(info); top.addStretch()
        top.addWidget(button("Exportar PDF", True, self.export_pdf)); root.addLayout(top)
        tabs = QTabWidget(); tabs.addTab(self.assessment_tab(), "Avaliacao"); tabs.addTab(self.overview_tab(), "Visao geral"); tabs.addTab(self.history_tab(), "Evolucao"); tabs.addTab(self.anamnesis_tab(), "Anamnese"); tabs.addTab(self.photos_tab(), "Fotos"); tabs.addTab(self.documents_tab(), "Documentos"); root.addWidget(tabs)
    def overview_tab(self):
        page=QWidget(); layout=QVBoxLayout(page); cards=QGridLayout(); avals=db.list_avaliacoes(self.patient_id); latest=avals[-1] if avals else None
        data=[("Peso atual", f"{latest['peso']:.1f} kg" if latest else "-"), ("IMC", f"{latest['imc']:.1f}" if latest and latest['imc'] else "-"), ("Gordura", f"{latest['pg_final']:.1f}%" if latest and latest['pg_final'] else "-"), ("Consultas", str(len(db.list_consultas(self.patient_id))))]
        for i,(label,val) in enumerate(data): cards.addWidget(MetricCard(label,val),0,i)
        layout.addLayout(cards); layout.addSpacing(10); title=QLabel("Resumo clinico"); title.setStyleSheet("font-size:16px;font-weight:700;"); layout.addWidget(title); notes=QTextEdit(); notes.setPlaceholderText("Registre observacoes importantes da consulta..."); notes.setText(self.patient['observacoes'] or ''); layout.addWidget(notes); layout.addStretch(); return page
    def history_tab(self):
        page=QWidget(); layout=QVBoxLayout(page); layout.addWidget(QLabel("Evolucao antropometrica"))
        table=QTableWidget(); table.setColumnCount(6); table.setHorizontalHeaderLabels(["Data","Peso (kg)","IMC","% Gordura","Cintura","VET"]); rows=db.list_avaliacoes(self.patient_id); table.setRowCount(len(rows))
        for r,a in enumerate(rows):
            for c,key in enumerate(("data","peso","imc","pg_final","cintura","vet")): table.setItem(r,c,table_item(a[key]))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); layout.addWidget(table); return page
    def anamnesis_tab(self):
        page=QWidget(); layout=QHBoxLayout(page); form=QScrollArea(); form.setWidgetResizable(True); holder=QWidget(); form_layout=QFormLayout(holder); self.anam_inputs={}
        for field in self.FIELDS:
            input=QTextEdit(); input.setFixedHeight(58); form_layout.addRow(field+":",input); self.anam_inputs[field]=input
        form.setWidget(holder); layout.addWidget(form,3); side=QVBoxLayout(); side.addWidget(QLabel("Versoes salvas")); self.anam_table=QTableWidget(); self.anam_table.setColumnCount(2); self.anam_table.setHorizontalHeaderLabels(["Versao","Data"]); self.anam_table.horizontalHeader().setStretchLastSection(True); side.addWidget(self.anam_table); side.addWidget(button("Carregar selecionada",False,self.load_anam)); side.addWidget(button("Salvar nova versao",True,self.save_anam)); layout.addLayout(side,1); self.refresh_anam(); return page
    def refresh_anam(self):
        self.anams=db.list_anamneses_paciente(self.patient_id); self.anam_table.setRowCount(len(self.anams))
        for r,a in enumerate(self.anams): self.anam_table.setItem(r,0,table_item(a['versao'] or '-')); self.anam_table.setItem(r,1,table_item(a['data']))
    def load_anam(self):
        r=self.anam_table.currentRow()
        if r<0:return
        data=db.dados_anamnese(self.anams[r])
        for field,input in self.anam_inputs.items(): input.setPlainText(data.get(field,""))
    def save_anam(self):
        data={k:v.toPlainText().strip() for k,v in self.anam_inputs.items()}
        if not any(data.values()): QMessageBox.information(self,"Anamnese","Preencha ao menos um campo."); return
        db.salvar_anamnese_estruturada(self.patient_id,data); self.refresh_anam(); QMessageBox.information(self,"Anamnese","Nova versao salva com sucesso.")
    def photos_tab(self):
        page=QWidget(); layout=QVBoxLayout(page); header=QHBoxLayout(); header.addWidget(QLabel("Comparacao de fotos locais")); header.addStretch(); header.addWidget(button("Adicionar foto",True,self.add_photo)); layout.addLayout(header)
        self.photos_grid=QHBoxLayout(); layout.addLayout(self.photos_grid); layout.addStretch(); self.refresh_photos(); return page
    def refresh_photos(self):
        clear_layout(self.photos_grid); photos=db.list_fotos_paciente(self.patient_id)
        if not photos: self.photos_grid.addWidget(QLabel("Ainda nao ha fotos cadastradas.")); return
        for photo in photos[-2:]:
            card=QFrame(); card.setObjectName("card"); cl=QVBoxLayout(card); image=QLabel(); image.setFixedSize(250,240); image.setAlignment(Qt.AlignCenter)
            pix=QPixmap(photo['caminho'])
            if pix.isNull(): image.setText("Foto indisponivel")
            else: image.setPixmap(pix.scaled(image.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))
            cl.addWidget(image); cl.addWidget(QLabel(f"{photo['data']}\n{photo['observacao'] or ''}")); self.photos_grid.addWidget(card)
    def add_photo(self):
        path,_=QFileDialog.getOpenFileName(self,"Selecionar foto","","Imagens (*.png *.jpg *.jpeg *.bmp)")
        if not path:return
        db.add_foto_paciente(self.patient_id,path,date.today().strftime("%d/%m/%Y"),""); self.refresh_photos()
    def documents_tab(self):
        page=QWidget(); layout=QVBoxLayout(page); table=QTableWidget(); table.setColumnCount(3); table.setHorizontalHeaderLabels(["Tipo","Arquivo","Data"]); docs=db.list_documentos_paciente(self.patient_id); table.setRowCount(len(docs))
        for r,d in enumerate(docs):
            for c,key in enumerate(("tipo","nome_arquivo","data")): table.setItem(r,c,table_item(d[key]))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); layout.addWidget(table); return page
    def export_pdf(self):
        avals=db.list_avaliacoes(self.patient_id)
        if not avals:
            QMessageBox.information(self,"PDF","Cadastre uma avaliacao antes de gerar o relatorio.")
            return
        a=avals[-1]; dobras={key.replace("dobra_",""):a[key] for key in a.keys() if key.startswith("dobra_")}
        results=formulas.calcular_avaliacao_completa(self.patient["sexo"],a["idade"],a["peso"],a["altura_cm"],dobras,a["formula_tmb"],a["atividade"],a["ajuste_pct"],a["ptn_gkg"],a["lip_pct"],bia_pg=a["bia_pg"])
        path,_=QFileDialog.getSaveFileName(self,"Exportar avaliacao",f"avaliacao_{self.patient['nome'].replace(' ','_')}.pdf","PDF (*.pdf)")
        if not path:return
        identity={"clinica_nome":db.get_config("clinica_nome",""),"profissional_nome":db.get_config("profissional_nome",""),"crn":db.get_config("profissional_crn",""),"telefone":db.get_config("profissional_telefone",""),"email":db.get_config("profissional_email",""),"logo_path":db.get_config("logo_path",""),"cor_primaria":db.get_config("pdf_cor_primaria","#145C57"),"cor_secundaria":db.get_config("pdf_cor_secundaria","#E1EFEB")}
        pdf_export.exportar_avaliacao(path,self.patient,a,results,identidade=identity)
        db.add_documento_paciente(self.patient_id,"Avaliacao",os.path.basename(path),path)
        QMessageBox.information(self,"PDF","Relatorio exportado e anexado ao paciente.")


class NewPatientDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent); self.setWindowTitle("Novo paciente"); self.setMinimumWidth(430); layout=QVBoxLayout(self); form=QFormLayout(); self.name=QLineEdit(); self.birth=QLineEdit(); self.phone=QLineEdit(); self.email=QLineEdit(); self.sex=QComboBox(); self.sex.addItems(["F","M"])
        for label,field in (("Nome",self.name),("Sexo",self.sex),("Nascimento",self.birth),("Telefone",self.phone),("E-mail",self.email)): form.addRow(label+":",field)
        layout.addLayout(form); layout.addWidget(button("Salvar paciente",True,self.save))
    def save(self):
        if not self.name.text().strip(): QMessageBox.warning(self,"Paciente","Informe o nome."); return
        self.patient_id=db.add_paciente(self.name.text().strip(),self.sex.currentText(),self.birth.text().strip(),self.phone.text().strip(),self.email.text().strip()); self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); db.init_db(); self.setWindowTitle("NutriDesktop"); self.resize(1440,900); self.setMinimumSize(1120,700)
        self.setStyleSheet(APP_STYLE); self.pages={}; self.nav={}; self.build_shell(); self.show_page("Dashboard")
    def build_shell(self):
        root=QWidget(); root.setObjectName("root"); self.setCentralWidget(root); layout=QHBoxLayout(root); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        sidebar=QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(258); side=QVBoxLayout(sidebar); side.setContentsMargins(12,20,12,18); side.setSpacing(4)
        brand=QHBoxLayout(); brand.addWidget(FruitMark()); brand.addWidget(QLabel("NutriDesktop",objectName="brand")); brand.addStretch(); side.addLayout(brand)
        new=button("+ Novo paciente",False,self.new_patient); new.setStyleSheet(f"background: {COLORS['accent_soft']}; color:{COLORS['accent']}; font-weight:600; margin: 12px 0 8px 0;"); side.addWidget(new)
        for group,items in (("TRABALHO",[("Dashboard","?"),("Pacientes","?"),("Agenda","?"),("Alimentos","?")]),("CONTEUDO",[("Planos alimentares","?"),("Receitas","?"),("Diretrizes","?"),("Materno-infantil","?")]),("SISTEMA",[("Identidade visual","?"),("Configuracoes","?")])):
            label=QLabel(group); label.setStyleSheet(f"color:{COLORS['muted']}; font-size:10px; font-weight:700; margin: 14px 10px 3px;"); side.addWidget(label)
            for name,icon in items:
                b=button(name,False,lambda checked=False,n=name:self.show_page(n)); self.nav[name]=b; side.addWidget(b)
        side.addStretch(); profile=QLabel("ND  Nutricionista"); profile.setStyleSheet("padding: 12px; font-weight:600;"); side.addWidget(profile)
        layout.addWidget(sidebar)
        right=QWidget(); right_layout=QVBoxLayout(right); right_layout.setContentsMargins(0,0,0,0); right_layout.setSpacing(0)
        top=QFrame(); top.setObjectName("topbar"); tl=QHBoxLayout(top); tl.setContentsMargins(28,12,28,12); search=QLineEdit(); search.setPlaceholderText("Buscar paciente, alimento ou documento"); search.setMaximumWidth(380); tl.addWidget(search); tl.addStretch(); right_layout.addWidget(top)
        self.stack=QStackedWidget(); right_layout.addWidget(self.stack); layout.addWidget(right)
    def set_nav(self,name):
        for n,b in self.nav.items(): b.setObjectName("navActive" if n==name else ""); b.style().unpolish(b); b.style().polish(b)
    def show_page(self,name):
        self.set_nav(name)
        if name not in self.pages:
            factory={"Dashboard":self.dashboard_page,"Pacientes":self.patients_page,"Agenda":self.agenda_page,"Alimentos":self.foods_page,"Planos alimentares":self.plans_page,"Receitas":self.recipes_page,"Diretrizes":self.guidelines_page,"Materno-infantil":self.maternal_page,"Configuracoes":self.settings_page,"Identidade visual":self.identity_page}.get(name)
            page=factory() if factory else self.dashboard_page(); self.pages[name]=page; self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.pages[name])
    def page_frame(self,title,subtitle=""):
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(34,28,34,28); layout.setSpacing(18); title_w=QLabel(title); title_w.setObjectName("pageTitle"); layout.addWidget(title_w)
        if subtitle: sub=QLabel(subtitle); sub.setObjectName("pageSub"); layout.addWidget(sub)
        return page,layout
    def dashboard_page(self):
        page,layout=self.page_frame("Bom dia, Nutricionista","Uma visao clara do consultorio e dos proximos atendimentos.")
        patients=db.list_pacientes(); av=sum(len(db.list_avaliacoes(p['id'])) for p in patients); consult=db.list_consultas(); cards=QGridLayout(); cards.setHorizontalSpacing(14)
        for i,x in enumerate((("Pacientes ativos",str(len(patients)),"Base local protegida"),("Avaliacoes",str(av),"Historico clinico"),("Consultas",str(len(consult)),"Agenda cadastrada"),("Planos",str(sum(len(db.list_planos(p['id'])) for p in patients)),"Orientacoes ativas"))): cards.addWidget(MetricCard(*x),0,i)
        layout.addLayout(cards); row=QHBoxLayout(); recent=QFrame(); recent.setObjectName("card"); rl=QVBoxLayout(recent); header=QHBoxLayout(); h=QLabel("Pacientes recentes"); h.setStyleSheet("font-size:16px;font-weight:700;"); header.addWidget(h); header.addStretch(); header.addWidget(button("Ver todos",False,lambda:self.show_page("Pacientes"))); rl.addLayout(header)
        table=QTableWidget(); table.setColumnCount(4); table.setHorizontalHeaderLabels(["Paciente","Sexo","Telefone","Ultima avaliacao"]); table.setRowCount(min(7,len(patients))); table.verticalHeader().hide()
        for r,p in enumerate(patients[:7]):
            last=db.list_avaliacoes(p['id']); vals=(p['nome'],p['sexo'],p['telefone'] or '-',last[-1]['data'] if last else 'Sem avaliacao')
            for c,v in enumerate(vals):table.setItem(r,c,table_item(v))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); table.setMinimumHeight(280); rl.addWidget(table); row.addWidget(recent,2)
        agenda=QFrame(); agenda.setObjectName("card"); al=QVBoxLayout(agenda); t=QLabel("Proximas consultas"); t.setStyleSheet("font-size:16px;font-weight:700;"); al.addWidget(t)
        if consult:
            for c in consult[:5]:
                line=QLabel(f"{c['data']}  {c['hora'] or ''}\n{c['paciente_nome']}"); line.setStyleSheet("padding:9px 0; border-bottom:1px solid #EEE;"); al.addWidget(line)
        else: al.addWidget(QLabel("Nenhuma consulta agendada."))
        al.addStretch(); row.addWidget(agenda,1); layout.addLayout(row); layout.addStretch(); return page
    def patients_page(self):
        page,layout=self.page_frame("Pacientes","Cadastros, historico e documentos em um unico lugar."); bar=QHBoxLayout(); self.patient_search=QLineEdit(); self.patient_search.setPlaceholderText("Buscar por nome, telefone ou e-mail"); self.patient_search.textChanged.connect(self.refresh_patients); bar.addWidget(self.patient_search); bar.addStretch(); bar.addWidget(button("+ Novo paciente",True,self.new_patient)); layout.addLayout(bar)
        self.patient_table=QTableWidget(); self.patient_table.setColumnCount(5); self.patient_table.setHorizontalHeaderLabels(["Paciente","Sexo","Telefone","E-mail","Acoes"]); self.patient_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch); self.patient_table.horizontalHeader().setSectionResizeMode(3,QHeaderView.Stretch); self.patient_table.setSelectionBehavior(QTableWidget.SelectRows); self.patient_table.setEditTriggers(QTableWidget.NoEditTriggers); self.patient_table.cellDoubleClicked.connect(lambda r,c:self.open_patient(int(self.patient_table.item(r,0).data(Qt.UserRole)))); layout.addWidget(self.patient_table); self.refresh_patients(); return page
    def refresh_patients(self):
        if not hasattr(self,"patient_table"):return
        rows=db.list_pacientes(self.patient_search.text() if hasattr(self,"patient_search") else ""); self.patient_table.setRowCount(len(rows))
        for r,p in enumerate(rows):
            values=(p['nome'],p['sexo'],p['telefone'] or '-',p['email'] or '-')
            for c,v in enumerate(values):
                it=table_item(v); self.patient_table.setItem(r,c,it)
                if c==0:it.setData(Qt.UserRole,p['id'])
            open_b=button("Abrir",False,lambda checked=False,pid=p['id']:self.open_patient(pid)); self.patient_table.setCellWidget(r,4,open_b)
        self.patient_table.horizontalHeader().setSectionResizeMode(4,QHeaderView.ResizeToContents)
    def new_patient(self):
        dialog=NewPatientDialog(self)
        if dialog.exec(): self.refresh_patients(); self.open_patient(dialog.patient_id)
    def open_patient(self,pid): PatientDialog(pid,self).exec(); self.refresh_patients()
    def agenda_page(self):
        page,layout=self.page_frame("Agenda","Acompanhe os atendimentos registrados no consultorio."); table=QTableWidget(); table.setColumnCount(5); table.setHorizontalHeaderLabels(["Data","Hora","Paciente","Status","Observacoes"]); rows=db.list_consultas(); table.setRowCount(len(rows))
        for r,c in enumerate(rows):
            for col,key in enumerate(("data","hora","paciente_nome","status","observacoes")):table.setItem(r,col,table_item(c[key]))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); layout.addWidget(table); return page
    def foods_page(self):
        page,layout=self.page_frame("Alimentos","Base TACO preservada, acrescida de itens personalizados e importacao CSV."); bar=QHBoxLayout(); self.food_search=QLineEdit(); self.food_search.setPlaceholderText("Buscar alimento ou categoria"); self.food_search.textChanged.connect(self.refresh_foods); bar.addWidget(self.food_search); bar.addStretch(); bar.addWidget(button("Importar CSV",False,self.import_foods)); bar.addWidget(button("+ Novo alimento",True,self.new_food)); layout.addLayout(bar)
        self.food_table=QTableWidget(); self.food_table.setColumnCount(6); self.food_table.setHorizontalHeaderLabels(["Descricao","Categoria","Kcal","Proteina","Carboidrato","Origem"]); self.food_table.setSelectionBehavior(QTableWidget.SelectRows); self.food_table.setEditTriggers(QTableWidget.NoEditTriggers); self.food_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch); layout.addWidget(self.food_table); self.refresh_foods(); return page
    def refresh_foods(self):
        if not hasattr(self,"food_table"):return
        rows=db.list_alimentos(self.food_search.text() if hasattr(self,"food_search") else "",500); self.food_table.setRowCount(len(rows))
        for r,a in enumerate(rows):
            for c,k in enumerate(("descricao","categoria","kcal","proteina","carboidrato","origem")):self.food_table.setItem(r,c,table_item(a[k] if a[k] is not None else '-'))
    def new_food(self):
        d=QDialog(self); d.setWindowTitle("Novo alimento"); d.setMinimumWidth(390); layout=QVBoxLayout(d); form=QFormLayout(); inputs={}
        for key,label in (("descricao","Descricao"),("categoria","Categoria"),("kcal","Kcal /100g"),("proteina","Proteina"),("lipideos","Lipideos"),("carboidrato","Carboidrato"),("fibra","Fibra")):
            i=QLineEdit(); form.addRow(label+":",i); inputs[key]=i
        layout.addLayout(form)
        def save():
            try:
                data={k:i.text().strip() for k,i in inputs.items()}
                for k in ("kcal","proteina","lipideos","carboidrato","fibra"): data[k]=float(data[k].replace(',','.')) if data[k] else None
                db.salvar_alimento(data); d.accept()
            except ValueError as e: QMessageBox.warning(d,"Dados invalidos",str(e))
        layout.addWidget(button("Salvar alimento",True,save))
        if d.exec():self.refresh_foods()
    def import_foods(self):
        path,_=QFileDialog.getOpenFileName(self,"Importar CSV","","CSV (*.csv)")
        if not path:return
        try:
            result=db.importar_alimentos_csv(path); errors='\n'.join(result['erros'][:10]); QMessageBox.information(self,"Importacao",f"{result['inseridos']} alimentos importados."+(f"\n\nErros:\n{errors}" if errors else '')); self.refresh_foods()
        except Exception as e: QMessageBox.warning(self,"Importacao",str(e))
    def identity_page(self):
        page,layout=self.page_frame("Identidade visual","Personalize os proximos PDFs com os dados da clinica."); card=QFrame(); card.setObjectName("card"); form=QFormLayout(card); form.setContentsMargins(22,22,22,22); inputs={}
        for key,label,default in (("clinica_nome","Nome da clinica",""),("profissional_nome","Profissional",""),("profissional_crn","CRN",""),("profissional_telefone","Telefone",""),("profissional_email","E-mail",""),("pdf_cor_primaria","Cor principal","#145C57"),("pdf_cor_secundaria","Cor clara","#E1EFEB")):
            i=QLineEdit(db.get_config(key,default)); form.addRow(label+":",i); inputs[key]=i
        def save():
            for k,i in inputs.items():db.set_config(k,i.text().strip())
            pdf_export.DEFAULT_IDENTITY.update({k:i.text().strip() for k,i in inputs.items()}); QMessageBox.information(self,"Identidade","Dados salvos para os proximos PDFs.")
        form.addRow("",button("Salvar identidade",True,save)); layout.addWidget(card); layout.addStretch(); return page
    def settings_page(self):
        page,layout=self.page_frame("Configuracoes","Dados locais, backup e restauracao."); card=QFrame(); card.setObjectName("card"); box=QVBoxLayout(card); box.setContentsMargins(22,22,22,22); box.addWidget(QLabel("Dados locais",styleSheet="font-size:16px;font-weight:700;")); box.addWidget(QLabel(f"Banco: {db.DB_PATH}\nOs arquivos de pacientes, fotos, documentos e licenca ficam nesta pasta."))
        actions=QHBoxLayout(); actions.addWidget(button("Exportar backup",True,self.backup)); actions.addWidget(button("Restaurar backup",False,self.restore)); actions.addStretch(); box.addLayout(actions); layout.addWidget(card); layout.addStretch(); return page
    def backup(self):
        path,_=QFileDialog.getSaveFileName(self,"Exportar backup",f"backup_nutridesktop_{date.today().isoformat()}.zip","ZIP (*.zip)")
        if path: db.exportar_backup(path); QMessageBox.information(self,"Backup","Backup criado com sucesso.")
    def restore(self):
        path,_=QFileDialog.getOpenFileName(self,"Restaurar backup","","ZIP (*.zip)")
        if path and QMessageBox.question(self,"Restaurar","Substituir os dados atuais pelo backup?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes: db.restaurar_backup(path); QMessageBox.information(self,"Restaurado","Backup restaurado. Reinicie o aplicativo.")


class FruitMark(QWidget):
    """Marca vetorial original: fruta minimalista com folha, sem reproduzir logotipos de terceiros."""
    def __init__(self):
        super().__init__(); self.setFixedSize(27, 30)
    def paintEvent(self, event):
        painter=QPainter(self); painter.setRenderHint(QPainter.Antialiasing); painter.setPen(Qt.NoPen); painter.setBrush(QColor(COLORS["accent"]))
        path=QPainterPath(); path.moveTo(13,9); path.cubicTo(4,5,2,12,4,19); path.cubicTo(6,27,11,29,14,25); path.cubicTo(17,29,23,27,24,19); path.cubicTo(26,12,22,5,15,9); path.cubicTo(14,10,14,10,13,9); painter.drawPath(path)
        leaf=QPainterPath(); leaf.moveTo(15,7); leaf.cubicTo(16,1,22,1,23,2); leaf.cubicTo(22,7,19,9,15,9); painter.drawPath(leaf)


def _simple_label(text, style=""):
    label=QLabel(text); label.setWordWrap(True)
    if style: label.setStyleSheet(style)
    return label


class AssessmentDialog(QDialog):
    def __init__(self, patient, parent=None):
        super().__init__(parent); self.patient=patient; self.setWindowTitle("Nova avaliacao"); self.resize(620,620)
        layout=QVBoxLayout(self); layout.addWidget(_simple_label("Nova avaliacao antropometrica", "font-size:20px;font-weight:700;")); layout.addWidget(_simple_label("Os campos essenciais calculam IMC, percentual de gordura estimado, gasto energetico e meta diaria.", f"color:{COLORS['muted']};"))
        scroll=QScrollArea(); scroll.setWidgetResizable(True); holder=QWidget(); form=QFormLayout(holder); self.inputs={}
        values=(
            ("idade","Idade", "30"), ("peso","Peso (kg)", ""), ("altura_cm","Altura (cm)", ""), ("cintura","Cintura (cm)", ""),
            ("bia_pg","% gordura bioimpedancia (opcional)", ""), ("ajuste_pct","Ajuste VET (%)", "0"), ("ptn_gkg","Proteina (g/kg)", "1.2"), ("lip_pct","Lipideos (%)", "30"),
        )
        for key,label,default in values:
            entry=QLineEdit(default); entry.setPlaceholderText(label); form.addRow(label+":",entry); self.inputs[key]=entry
        self.formula=QComboBox(); self.formula.addItems(["Mifflin-St Jeor","Harris-Benedict","Katch-McArdle","Cunningham"]); form.addRow("Formula TMB:",self.formula)
        self.activity=QComboBox(); self.activity.addItems(list(formulas.FATORES_ATIVIDADE.keys())); form.addRow("Nivel de atividade:",self.activity)
        scroll.setWidget(holder); layout.addWidget(scroll)
        layout.addWidget(button("Calcular e salvar avaliacao",True,self.save))
    def number(self,key,required=False):
        text=self.inputs[key].text().strip().replace(",", ".")
        if not text and not required:return None
        return float(text)
    def save(self):
        try:
            idade=self.number("idade",True); peso=self.number("peso",True); altura=self.number("altura_cm",True)
            result=formulas.calcular_avaliacao_completa(self.patient["sexo"],idade,peso,altura,{},self.formula.currentText(),self.activity.currentText(),self.number("ajuste_pct",True),self.number("ptn_gkg",True),self.number("lip_pct",True),bia_pg=self.number("bia_pg"))
            data={"paciente_id":self.patient["id"],"data":date.today().strftime("%d/%m/%Y"),"peso":peso,"altura_cm":altura,"idade":idade,"imc":result["imc"],"cintura":self.number("cintura"),"bia_pg":self.number("bia_pg"),"pg_final":result["pg_final"],"origem_pg":result["origem_pg"],"massa_gorda":result["massa_gorda"],"massa_magra":result["massa_magra"],"formula_tmb":self.formula.currentText(),"tmb":result["tmb"],"atividade":self.activity.currentText(),"fator_atividade":result["fator_atividade"],"get_total":result["get_total"],"ajuste_pct":self.number("ajuste_pct",True),"vet":result["vet"],"ptn_gkg":self.number("ptn_gkg",True),"ptn_g":result["ptn_g"],"lip_pct":self.number("lip_pct",True),"lip_g":result["lip_g"],"cho_g":result["cho_g"]}
            db.add_avaliacao(data); QMessageBox.information(self,"Avaliacao salva",f"IMC: {result['imc']:.1f}\nMeta energetica: {result['vet']:.0f} kcal"); self.accept()
        except (ValueError, KeyError) as error: QMessageBox.warning(self,"Dados invalidos",f"Confira os campos obrigatorios.\n{error}")


def _assessment_tab(self):
    page=QWidget(); layout=QVBoxLayout(page); top=QHBoxLayout(); top.addWidget(_simple_label("Avaliacoes antropometricas", "font-size:16px;font-weight:700;")); top.addStretch(); top.addWidget(button("+ Nova avaliacao",True,lambda:self._new_assessment())); layout.addLayout(top)
    self.qt_assessment_table=QTableWidget(); self.qt_assessment_table.setColumnCount(6); self.qt_assessment_table.setHorizontalHeaderLabels(["Data","Peso","IMC","% Gordura","Cintura","VET"]); self.qt_assessment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); layout.addWidget(self.qt_assessment_table); self._refresh_assessments(); return page

def _refresh_assessments(self):
    if not hasattr(self,"qt_assessment_table"): return
    rows=db.list_avaliacoes(self.patient_id); self.qt_assessment_table.setRowCount(len(rows))
    for r,a in enumerate(rows):
        for c,k in enumerate(("data","peso","imc","pg_final","cintura","vet")): self.qt_assessment_table.setItem(r,c,table_item(a[k]))

def _new_assessment(self):
    dialog=AssessmentDialog(self.patient,self)
    if dialog.exec():
        self._refresh_assessments()
        if hasattr(self,"history_tab"): pass

PatientDialog.assessment_tab=_assessment_tab
PatientDialog._refresh_assessments=_refresh_assessments
PatientDialog._new_assessment=_new_assessment


class PlanDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Novo plano alimentar"); self.setMinimumWidth(500); layout=QVBoxLayout(self); form=QFormLayout(); self.patient=QComboBox(); self.people=db.list_pacientes()
        self.patient.addItems([p["nome"] for p in self.people]); self.name=QLineEdit("Plano alimentar"); self.vet=QLineEdit("1800")
        form.addRow("Paciente:",self.patient); form.addRow("Nome do plano:",self.name); form.addRow("Meta VET (kcal):",self.vet); layout.addLayout(form)
        layout.addWidget(_simple_label("Primeiro item do plano (opcional)","font-weight:700; margin-top:8px;")); item_form=QFormLayout(); self.meal=QComboBox(); self.meal.addItems(["Cafe da manha","Lanche da manha","Almoco","Lanche da tarde","Jantar","Ceia"]); self.food=QComboBox(); self.foods=db.list_alimentos("",500); self.food.addItems([x["descricao"] for x in self.foods]); self.qty=QLineEdit("100"); item_form.addRow("Refeicao:",self.meal); item_form.addRow("Alimento:",self.food); item_form.addRow("Quantidade (g):",self.qty); layout.addLayout(item_form); layout.addWidget(button("Criar plano",True,self.save))
    def save(self):
        if not self.people: QMessageBox.warning(self,"Plano","Cadastre um paciente antes de criar o plano."); return
        try:
            pid=self.people[self.patient.currentIndex()]["id"]; plan=db.add_plano(pid,self.name.text().strip() or "Plano alimentar",date.today().strftime("%d/%m/%Y"),float(self.vet.text().replace(",",".")))
            if self.foods: db.add_item_plano(plan,self.meal.currentText(),self.foods[self.food.currentIndex()]["id"],float(self.qty.text().replace(",",".")))
            self.accept()
        except ValueError: QMessageBox.warning(self,"Plano","Informe valores numericos validos.")


def _plans_page(self):
    page,layout=self.page_frame("Planos alimentares","Monte planos por paciente e acompanhe suas metas energeticas."); bar=QHBoxLayout(); bar.addStretch(); bar.addWidget(button("+ Novo plano",True,lambda:self._new_plan())); layout.addLayout(bar)
    split=QSplitter(); left=QWidget(); ll=QVBoxLayout(left); self.qt_plan_patients=QComboBox(); self.qt_plan_people=db.list_pacientes(); self.qt_plan_patients.addItems([p["nome"] for p in self.qt_plan_people]); self.qt_plan_patients.currentIndexChanged.connect(self._refresh_plans); ll.addWidget(_simple_label("Paciente","font-weight:700;")); ll.addWidget(self.qt_plan_patients); self.qt_plans=QTableWidget(); self.qt_plans.setColumnCount(3); self.qt_plans.setHorizontalHeaderLabels(["Plano","Data","VET"]); self.qt_plans.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); ll.addWidget(self.qt_plans); split.addWidget(left)
    right=QWidget(); rl=QVBoxLayout(right); rl.addWidget(_simple_label("Itens do plano","font-size:16px;font-weight:700;")); self.qt_plan_items=QTableWidget(); self.qt_plan_items.setColumnCount(4); self.qt_plan_items.setHorizontalHeaderLabels(["Refeicao","Alimento","Qtd. (g)","Kcal"]); self.qt_plan_items.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); rl.addWidget(self.qt_plan_items); split.addWidget(right); split.setSizes([420,650]); layout.addWidget(split, 1); self.qt_plans.itemSelectionChanged.connect(self._show_plan_items); self._refresh_plans(); return page

def _new_plan(self):
    dialog=PlanDialog(self)
    if dialog.exec():
        self.qt_plan_people=db.list_pacientes(); self.qt_plan_patients.clear(); self.qt_plan_patients.addItems([p["nome"] for p in self.qt_plan_people]); self._refresh_plans()

def _refresh_plans(self):
    if not hasattr(self,"qt_plans"):return
    index=self.qt_plan_patients.currentIndex() if hasattr(self,"qt_plan_patients") else -1
    rows=db.list_planos(self.qt_plan_people[index]["id"]) if index>=0 and index<len(self.qt_plan_people) else []; self.qt_plans.setRowCount(len(rows)); self.qt_current_plans=rows
    for r,plan in enumerate(rows):
        for c,k in enumerate(("nome","data","vet_meta")):
            item=table_item(plan[k]); self.qt_plans.setItem(r,c,item)
            if c==0:item.setData(Qt.UserRole,plan["id"])
    self.qt_plan_items.setRowCount(0)

def _show_plan_items(self):
    rows=self.qt_plans.selectedItems()
    if not rows:return
    plan_id=rows[0].data(Qt.UserRole); items=db.list_itens_plano(plan_id); self.qt_plan_items.setRowCount(len(items))
    for r,item in enumerate(items):
        values=(item["refeicao"],item["descricao"],f"{item['quantidade_g']:.0f}",f"{(item['kcal'] or 0)*item['quantidade_g']/100:.0f}")
        for c,value in enumerate(values):self.qt_plan_items.setItem(r,c,table_item(value))

MainWindow.plans_page=_plans_page; MainWindow._new_plan=_new_plan; MainWindow._refresh_plans=_refresh_plans; MainWindow._show_plan_items=_show_plan_items


class RecipeDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent); self.setWindowTitle("Nova receita"); self.setMinimumWidth(500); layout=QVBoxLayout(self); form=QFormLayout(); self.name=QLineEdit(); self.category=QLineEdit(); self.tags=QLineEdit(); self.portions=QLineEdit("1"); self.prepare=QTextEdit(); self.prepare.setFixedHeight(80)
        for label,field in (("Nome",self.name),("Categoria",self.category),("Tags",self.tags),("Porcoes",self.portions),("Modo de preparo",self.prepare)):form.addRow(label+":",field)
        layout.addLayout(form); self.ingredients=[]; self.foods=db.list_alimentos("",500); add=QHBoxLayout(); self.food=QComboBox(); self.food.addItems([x["descricao"] for x in self.foods]); self.qty=QLineEdit("100"); add.addWidget(self.food); add.addWidget(self.qty); add.addWidget(button("Adicionar",False,self.add_item)); layout.addLayout(add); self.list=QTableWidget(); self.list.setColumnCount(2); self.list.setHorizontalHeaderLabels(["Ingrediente","Qtd. (g)"]); self.list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); layout.addWidget(self.list); layout.addWidget(button("Salvar receita",True,self.save))
    def add_item(self):
        try:self.ingredients.append((self.foods[self.food.currentIndex()]["id"],float(self.qty.text().replace(",",".")))); r=len(self.ingredients)-1; self.list.setRowCount(len(self.ingredients)); self.list.setItem(r,0,table_item(self.food.currentText())); self.list.setItem(r,1,table_item(self.qty.text()))
        except ValueError: QMessageBox.warning(self,"Receita","Quantidade invalida.")
    def save(self):
        if not self.name.text().strip(): QMessageBox.warning(self,"Receita","Informe o nome."); return
        db.add_receita(self.name.text().strip(),self.category.text().strip(),self.tags.text().strip(),float(self.portions.text().replace(",",".")),self.prepare.toPlainText(),self.ingredients); self.accept()

def _recipes_page(self):
    page,layout=self.page_frame("Modelos de receitas","Cadastre receitas reutilizaveis a partir da base de alimentos."); bar=QHBoxLayout(); self.qt_recipe_search=QLineEdit(); self.qt_recipe_search.setPlaceholderText("Buscar receita"); self.qt_recipe_search.textChanged.connect(self._refresh_recipes); bar.addWidget(self.qt_recipe_search); bar.addStretch(); bar.addWidget(button("+ Nova receita",True,self._new_recipe)); layout.addLayout(bar); self.qt_recipes=QTableWidget(); self.qt_recipes.setColumnCount(4); self.qt_recipes.setHorizontalHeaderLabels(["Receita","Categoria","Tags","Porcoes"]); self.qt_recipes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); layout.addWidget(self.qt_recipes); self._refresh_recipes(); return page
def _new_recipe(self):
    if RecipeDialog(self).exec():self._refresh_recipes()
def _refresh_recipes(self):
    rows=db.list_receitas(busca=self.qt_recipe_search.text() if hasattr(self,"qt_recipe_search") else ""); self.qt_recipes.setRowCount(len(rows))
    for r,row in enumerate(rows):
        for c,k in enumerate(("nome","categoria","tags","porcoes")):self.qt_recipes.setItem(r,c,table_item(row[k]))
MainWindow.recipes_page=_recipes_page; MainWindow._new_recipe=_new_recipe; MainWindow._refresh_recipes=_refresh_recipes


def _guidelines_page(self):
    page,layout=self.page_frame("Diretrizes clinicas","Consulta rapida e editavel para orientacoes nutricionais."); split=QSplitter(); left=QWidget(); ll=QVBoxLayout(left); self.qt_guidelines=QTableWidget(); self.qt_guidelines.setColumnCount(1); self.qt_guidelines.setHorizontalHeaderLabels(["Diretriz"]); self.qt_guidelines.horizontalHeader().setStretchLastSection(True); self.qt_guidelines.itemSelectionChanged.connect(self._show_guideline); ll.addWidget(self.qt_guidelines); buttons=QHBoxLayout(); buttons.addWidget(button("+ Nova",True,self._new_guideline)); buttons.addWidget(button("Excluir",False,self._delete_guideline)); ll.addLayout(buttons); split.addWidget(left); right=QWidget(); rl=QVBoxLayout(right); self.qt_guideline_title=_simple_label("Selecione uma diretriz","font-size:18px;font-weight:700;"); self.qt_guideline_source=_simple_label("",f"color:{COLORS['muted']};"); self.qt_guideline_body=QTextEdit(); self.qt_guideline_body.setReadOnly(True); rl.addWidget(self.qt_guideline_title); rl.addWidget(self.qt_guideline_source); rl.addWidget(self.qt_guideline_body); split.addWidget(right); split.setSizes([360,700]); layout.addWidget(split); self._refresh_guidelines(); return page
def _refresh_guidelines(self):
    self.qt_guideline_rows=db.list_diretrizes(); self.qt_guidelines.setRowCount(len(self.qt_guideline_rows))
    for r,row in enumerate(self.qt_guideline_rows):
        item=table_item(row["nome"]); item.setData(Qt.UserRole,row["id"]); self.qt_guidelines.setItem(r,0,item)
def _show_guideline(self):
    rows=self.qt_guidelines.selectedItems()
    if not rows:return
    item=rows[0]; row=db.get_diretriz(item.data(Qt.UserRole)); self.qt_guideline_title.setText(row["nome"]); self.qt_guideline_source.setText(row["fonte"] or ""); self.qt_guideline_body.setPlainText("\n\n".join(row["pontos"].split("|||")))
def _new_guideline(self):
    d=QDialog(self); d.setWindowTitle("Nova diretriz"); layout=QVBoxLayout(d); name=QLineEdit(); source=QLineEdit(); body=QTextEdit(); body.setPlaceholderText("Um ponto por linha"); form=QFormLayout(); form.addRow("Nome:",name); form.addRow("Fonte:",source); layout.addLayout(form); layout.addWidget(body)
    def save():
        if name.text().strip():db.add_diretriz(name.text().strip(),source.text().strip(),[x for x in body.toPlainText().splitlines() if x.strip()]);d.accept()
    layout.addWidget(button("Salvar",True,save));
    if d.exec():self._refresh_guidelines()
def _delete_guideline(self):
    rows=self.qt_guidelines.selectedItems()
    if rows and QMessageBox.question(self,"Excluir","Excluir a diretriz selecionada?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:db.delete_diretriz(rows[0].data(Qt.UserRole));self._refresh_guidelines()
MainWindow.guidelines_page=_guidelines_page; MainWindow._refresh_guidelines=_refresh_guidelines; MainWindow._show_guideline=_show_guideline; MainWindow._new_guideline=_new_guideline; MainWindow._delete_guideline=_delete_guideline


def _maternal_page(self):
    page,layout=self.page_frame("Materno-infantil","Ferramentas de apoio para gestacao, lactacao e crescimento infantil."); tabs=QTabWidget(); gest=QWidget(); gl=QVBoxLayout(gest); card=QFrame(); card.setObjectName("card"); form=QFormLayout(card); pre=QLineEdit(); h=QLineEdit(); phase=QComboBox(); phase.addItems(list(mi.INCREMENTOS.keys())); result=_simple_label("Informe peso e altura pre-gestacionais.","font-size:15px;"); form.addRow("Peso pre-gestacional (kg):",pre); form.addRow("Altura (cm):",h); form.addRow("Fase:",phase)
    def calculate():
        try:
            imc=float(pre.text().replace(",","."))/(float(h.text().replace(",","."))/100)**2; faixa=mi.faixa_ganho_peso(imc); inc=mi.calcular_incremento(phase.currentText()); result.setText(f"IMC pre-gestacional: {imc:.1f}\nFaixa recomendada: {faixa[0]}\nGanho total: {faixa[1]:.1f} a {faixa[2]:.1f} kg\n\nIncremento: {inc['kcal']} kcal/dia | Proteina extra: {inc['proteina_g_dia_extra']} g/dia | Ferro: {inc['ferro_mg']} mg/dia")
        except ValueError: result.setText("Informe peso e altura validos.")
    gl.addWidget(card); gl.addWidget(button("Calcular recomendacao",True,calculate)); gl.addWidget(result); gl.addStretch(); tabs.addTab(gest,"Gestacao e lactacao")
    infant=QWidget(); il=QVBoxLayout(infant); card2=QFrame();card2.setObjectName("card"); f2=QFormLayout(card2); sex=QComboBox();sex.addItems(["F","M"]); age=QLineEdit(); wt=QLineEdit(); ht=QLineEdit(); out=_simple_label("Preencha os dados para triagem de crescimento.");
    for label,w in (("Sexo",sex),("Idade (meses)",age),("Peso (kg)",wt),("Altura (cm)",ht)):f2.addRow(label+":",w)
    def growth():
        try: out.setText(f"Peso por idade: {ci.avaliar_peso(sex.currentText(),float(age.text()),float(wt.text()))}\nAltura por idade: {ci.avaliar_altura(sex.currentText(),float(age.text()),float(ht.text()))}")
        except ValueError:out.setText("Informe idade, peso e altura validos.")
    il.addWidget(card2);il.addWidget(button("Avaliar crescimento",True,growth));il.addWidget(out);il.addStretch();tabs.addTab(infant,"Crescimento infantil");layout.addWidget(tabs);return page
MainWindow.maternal_page=_maternal_page

def main():
    db.init_db(); app=QApplication(sys.argv); app.setApplicationName("NutriDesktop")
    # Garante uma fonte legivel mesmo quando o Qt nao descobre as fontes do Windows automaticamente.
    font_path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "segoeui.ttf")
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id >= 0:
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families: app.setFont(QFont(families[0], 10))
    if not licensing.esta_ativado(db):
        dialog=LicenseDialog()
        if dialog.exec()!=QDialog.Accepted:return 0
    window=MainWindow(); window.show(); return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
