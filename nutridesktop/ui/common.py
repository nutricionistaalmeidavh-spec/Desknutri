from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem,QMessageBox
from .view_models import friendly_error
from nutridesktop.ui_kit.components import UiButton


def button(text,callback=None,primary=False,variant=None,compact=False,tone=None):
    """Compatibilidade para telas legadas usando a hierarquia canônica de botões."""
    chosen=variant or ('primary' if primary else 'secondary')
    return UiButton(text,callback,variant=chosen,compact=compact,tone=tone)


def item(value):
    it=QTableWidgetItem('' if value is None else str(value));it.setFlags(it.flags() & ~Qt.ItemIsEditable);return it


def show_error(parent,title,exc):
    QMessageBox.critical(parent,title,friendly_error(exc))
