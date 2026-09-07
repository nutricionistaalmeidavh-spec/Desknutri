from __future__ import annotations

import os

from PySide6.QtWidgets import QApplication, QCheckBox, QMessageBox


class SignedAutoUpdateMixin:
    """Aplica automaticamente apenas releases que passem pela cadeia assinada."""

    def updates_page(self):
        w = super().updates_page()
        self.upd_auto_install = QCheckBox(
            "Instalar automaticamente atualizações assinadas"
        )
        self.upd_auto_install.setChecked(self.update_service.auto_install())
        layout = w.layout()
        if layout is not None:
            layout.insertWidget(max(0, layout.count() - 2), self.upd_auto_install)
        return w

    def save_update_settings(self):
        super().save_update_settings()
        if hasattr(self, "upd_auto_install"):
            self.update_service.set_auto_install(self.upd_auto_install.isChecked())

    def _auto_update_check(self):
        if not self.update_service.auto_check():
            return
        if not self.update_service.auto_install():
            return super()._auto_update_check()
        if os.name != "nt":
            return super()._auto_update_check()

        info = self.check_updates(silent=True)
        if not info:
            return

        try:
            installer, rollback = self.update_service.stage(info)
            self.update_service.launch_staged(info, installer, rollback)
            QApplication.quit()
        except Exception:
            QMessageBox.warning(
                self,
                "Atualização automática",
                "Não foi possível aplicar a atualização automaticamente. "
                "Abra Atualizações para tentar novamente.",
            )
