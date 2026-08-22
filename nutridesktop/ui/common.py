from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton,QTableWidgetItem,QMessageBox
from .view_models import friendly_error

def button(text,callback=None,primary=False):
    b=QPushButton(text);b.setCursor(Qt.PointingHandCursor);b.setProperty('primary',primary)
    if callback:b.clicked.connect(callback)
    return b

def item(value):
    it=QTableWidgetItem('' if value is None else str(value));it.setFlags(it.flags() & ~Qt.ItemIsEditable);return it

def show_error(parent,title,exc):
    QMessageBox.critical(parent,title,friendly_error(exc))
