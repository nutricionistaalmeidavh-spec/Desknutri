from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QButtonGroup,QFrame,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QWidget
from nutridesktop.ui_kit.theme import DEFAULT_THEME,THEMES,build_stylesheet,get_theme

COLORS={
    'brand':'#0F5B55','brand_hover':'#0B4E49','brand_soft':'#E7F3F0','ink':'#17211F','muted':'#697571',
    'line':'#DCE5E2','canvas':'#F6F9F8','surface':'#FFFFFF','warning':'#B7791F','danger':'#B5473C','info':'#2463B5'
}
# Compatibilidade: telas existentes continuam usando os objectNames originais,
# mas sua aparência agora vem dos tokens semânticos do UI Kit.
APP_STYLE=build_stylesheet(get_theme(DEFAULT_THEME))

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


class ThemeSelector(Card):
    """Seletor de tema reutilizável, sem acoplar Configurações ao QSettings."""
    def __init__(self,current,on_change,parent=None):
        super().__init__(parent,soft=True);self.group=QButtonGroup(self);self.group.setExclusive(True)
        self.body.addWidget(section_title('Aparência'))
        self.body.addWidget(muted('Escolha o tema da interface. O tema escuro profissional é o padrão do NutriDesk.'))
        for key,theme in THEMES.items():
            b=QPushButton(theme.label);b.setCheckable(True);b.setChecked(key==current);b.setProperty('primary',key==current)
            b.clicked.connect(lambda checked=False,k=key:on_change(k) if checked else None);self.group.addButton(b);self.body.addWidget(b)
