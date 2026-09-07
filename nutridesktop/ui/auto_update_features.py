from __future__ import annotations

import os

from PySide6.QtWidgets import QApplication, QCheckBox, QHBoxLayout, QLabel, QMessageBox, QTextEdit

from .common import button, show_error
from nutridesktop.version import APP_VERSION, CLINICAL_CONTENT_VERSION, SCHEMA_VERSION, WHO_ENGINE_VERSION


class GitHubReleaseUpdateMixin:
    """Atualizações simples via GitHub Releases, sempre iniciadas pelo usuário."""

    def updates_page(self):
        w, v = self.page(
            "Atualizações",
            "O NutriDesk consulta a Release estável mais recente no GitHub. Você escolhe quando instalar.",
        )
        v.addWidget(
            QLabel(
                f"Instalado: App {APP_VERSION} | Schema {SCHEMA_VERSION} | "
                f"Clínico {CLINICAL_CONTENT_VERSION} | WHO {WHO_ENGINE_VERSION}"
            )
        )
        self.upd_auto = QCheckBox("Avisar automaticamente quando houver nova versão")
        self.upd_auto.setChecked(self.update_service.auto_check())
        v.addWidget(self.upd_auto)

        row = QHBoxLayout()
        row.addWidget(button("Salvar preferência", self.save_update_settings))
        row.addWidget(button("Verificar agora", self.check_updates, True))
        row.addWidget(button("Atualizar agora", self.install_update))
        row.addStretch()
        v.addLayout(row)

        self.upd_status = QTextEdit()
        self.upd_status.setReadOnly(True)
        self.upd_status.setPlainText("Nenhuma verificação nesta sessão.")
        v.addWidget(self.upd_status)
        return w

    def save_update_settings(self):
        self.update_service.set_auto_check(self.upd_auto.isChecked())
        QMessageBox.information(self, "Atualizações", "Preferência salva.")

    def _auto_update_check(self):
        if not self.update_service.auto_check():
            return
        info = self.check_updates(silent=True)
        if not info:
            return

        answer = QMessageBox.question(
            self,
            "Nova versão disponível",
            f"NutriDesk {info.version} está disponível.\n\nDeseja baixar e abrir o instalador agora?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        if os.name != "nt":
            QMessageBox.information(
                self,
                "Atualizações",
                "A instalação integrada está disponível no Windows.",
            )
            return

        try:
            installer, _ = self.update_service.stage(info)
            self.update_service.launch_staged(info, installer)
            QApplication.quit()
        except Exception as e:
            show_error(self, "Atualização", e)
