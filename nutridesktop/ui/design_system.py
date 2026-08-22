from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame,QVBoxLayout,QHBoxLayout,QLabel,QWidget

COLORS={
    'brand':'#0F5B55','brand_hover':'#0B4E49','brand_soft':'#E7F3F0','ink':'#17211F','muted':'#697571',
    'line':'#DCE5E2','canvas':'#F6F9F8','surface':'#FFFFFF','warning':'#B7791F','danger':'#B5473C','info':'#2463B5'
}
APP_STYLE=f'''
*{{font-family:"Segoe UI";font-size:13px;color:{COLORS['ink']};}}
QMainWindow,QDialog,QWidget#appRoot{{background:{COLORS['canvas']};}}
QWidget#sidebar{{background:#0B4E49;border-right:1px solid #123F3B;}}
QLabel#brand{{font-size:24px;font-weight:800;color:white;padding:4px 0 14px 4px;}}
QLabel#navSection{{font-size:10px;font-weight:700;color:#9AC0BB;letter-spacing:1px;padding:12px 6px 3px 6px;}}
QPushButton{{border:0;border-radius:9px;padding:9px 11px;text-align:left;background:transparent;}}
QWidget#sidebar QPushButton{{color:#EAF6F4;}}
QWidget#sidebar QPushButton:hover{{background:#17655F;}}
QWidget#sidebar QPushButton[active="true"]{{background:#1E736C;color:white;font-weight:700;}}
QPushButton[primary="true"]{{background:{COLORS['brand']};color:white;font-weight:700;text-align:center;}}
QPushButton[primary="true"]:hover{{background:{COLORS['brand_hover']};}}
QLineEdit,QTextEdit,QComboBox,QDateEdit,QSpinBox,QDoubleSpinBox{{background:white;border:1px solid {COLORS['line']};border-radius:8px;padding:7px 9px;}}
QTableWidget{{background:white;border:1px solid {COLORS['line']};border-radius:12px;gridline-color:#EEF2F1;selection-background-color:{COLORS['brand_soft']};}}
QHeaderView::section{{background:#F8FAF9;border:0;border-bottom:1px solid {COLORS['line']};padding:8px;font-weight:700;}}
QFrame#card{{background:white;border:1px solid {COLORS['line']};border-radius:14px;}}
QFrame#softCard{{background:{COLORS['brand_soft']};border:1px solid #D3EAE5;border-radius:14px;}}
QLabel#pageTitle{{font-size:28px;font-weight:800;}}
QLabel#pageSubtitle{{color:{COLORS['muted']};}}
QLabel#metricValue{{font-size:24px;font-weight:800;color:{COLORS['ink']};}}
QLabel#metricLabel{{color:{COLORS['muted']};font-weight:600;}}
QLabel#sectionTitle{{font-size:15px;font-weight:750;}}
QLabel#muted{{color:{COLORS['muted']};}}
QTabWidget::pane{{border:0;background:transparent;}}
QTabBar::tab{{padding:10px 14px;margin-right:4px;border-bottom:2px solid transparent;color:#66726F;}}
QTabBar::tab:selected{{color:{COLORS['brand']};border-bottom:2px solid {COLORS['brand']};font-weight:700;}}
'''

class Card(QFrame):
    def __init__(self,parent=None,soft=False):
        super().__init__(parent);self.setObjectName('softCard' if soft else 'card');self.body=QVBoxLayout(self);self.body.setContentsMargins(16,14,16,14);self.body.setSpacing(8)

class StatCard(Card):
    def __init__(self,label,value,detail='',parent=None):
        super().__init__(parent);a=QLabel(str(label));a.setObjectName('metricLabel');v=QLabel(str(value));v.setObjectName('metricValue');self.body.addWidget(a);self.body.addWidget(v)
        if detail:
            d=QLabel(str(detail));d.setObjectName('muted');self.body.addWidget(d)

class EmptyState(Card):
    def __init__(self,title,message='',parent=None):
        super().__init__(parent);t=QLabel(title);t.setAlignment(Qt.AlignCenter);t.setStyleSheet('font-size:16px;font-weight:700');self.body.addWidget(t)
        if message:
            m=QLabel(message);m.setObjectName('muted');m.setWordWrap(True);m.setAlignment(Qt.AlignCenter);self.body.addWidget(m)


class LoadingState(Card):
    def __init__(self,message='Carregando…',parent=None):
        super().__init__(parent,soft=True);m=QLabel(message);m.setObjectName('muted');m.setAlignment(Qt.AlignCenter);self.body.addWidget(m)

def section_title(text):
    q=QLabel(text);q.setObjectName('sectionTitle');return q


def muted(text):
    q=QLabel(text);q.setObjectName('muted');q.setWordWrap(True);return q
