"""GitHub Releases updater UI: network and file operations never block Qt."""
from __future__ import annotations

import os

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QCheckBox, QHBoxLayout, QLabel, QMessageBox, QProgressBar, QTextEdit

from .common import button, show_error
from nutridesktop.version import APP_VERSION, CLINICAL_CONTENT_VERSION, SCHEMA_VERSION, WHO_ENGINE_VERSION


class UpdateWorker(QThread):
    """One-shot worker delivering values through Qt's queued signals."""
    succeeded = Signal(object)
    failed = Signal(str)
    progress = Signal(int)

    def __init__(self, operation):
        super().__init__()
        self.operation = operation

    def run(self):
        try:
            self.succeeded.emit(self.operation(self.progress.emit))
        except Exception as exc:
            self.failed.emit(str(exc))


class GitHubReleaseUpdateMixin:
    """Automatic check, opt-in install and background transfer."""

    def updates_page(self):
        w, v = self.page(
            "Atualizações",
            "O NutriDesk consulta as versões estáveis no GitHub e instala após sua confirmação.",
        )
        v.addWidget(QLabel(
            f"Instalado: App {APP_VERSION} | Schema {SCHEMA_VERSION} | "
            f"Clínico {CLINICAL_CONTENT_VERSION} | WHO {WHO_ENGINE_VERSION}"
        ))
        self.upd_auto = QCheckBox("Avisar automaticamente quando houver nova versão")
        self.upd_auto.setChecked(self.update_service.auto_check())
        v.addWidget(self.upd_auto)

        row = QHBoxLayout()
        self.upd_save_button = button("Salvar preferência", self.save_update_settings)
        self.upd_check_button = button("Verificar agora", self.check_updates, True)
        self.upd_install_button = button("Atualizar agora", self.install_update)
        for control in (self.upd_save_button, self.upd_check_button, self.upd_install_button):
            row.addWidget(control)
        row.addStretch()
        v.addLayout(row)

        self.upd_progress = QProgressBar()
        self.upd_progress.setRange(0, 100)
        self.upd_progress.setValue(0)
        self.upd_progress.setVisible(False)
        v.addWidget(self.upd_progress)
        self.upd_status = QTextEdit()
        self.upd_status.setReadOnly(True)
        self.upd_status.setPlainText("Nenhuma verificação nesta sessão.")
        v.addWidget(self.upd_status)
        return w

    def save_update_settings(self):
        self.update_service.set_auto_check(self.upd_auto.isChecked())
        QMessageBox.information(self, "Atualizações", "Preferência salva.")

    def _update_status(self, text):
        if hasattr(self, "upd_status"):
            self.upd_status.setPlainText(text)

    def _update_progress(self, percentage):
        if hasattr(self, "upd_progress"):
            self.upd_progress.setVisible(True)
            self.upd_progress.setValue(percentage)

    def _start_update_worker(self, operation, on_success, silent=False):
        if getattr(self, "_update_worker", None) is not None:
            return False
        worker = UpdateWorker(operation)
        self._update_worker = worker
        for name in ("upd_check_button", "upd_install_button"):
            if hasattr(self, name):
                getattr(self, name).setEnabled(False)

        def finish():
            self._update_worker = None
            for name in ("upd_check_button", "upd_install_button"):
                if hasattr(self, name):
                    getattr(self, name).setEnabled(True)
            worker.deleteLater()

        def failed(message):
            self._update_status("Falha na atualização: " + message)
            if not silent:
                QMessageBox.warning(self, "Atualização", message)

        worker.progress.connect(self._update_progress)
        worker.succeeded.connect(on_success)
        worker.failed.connect(failed)
        worker.finished.connect(finish)
        worker.start()
        return True

    def check_updates(self, silent=False):
        """Called by UI and startup. Neither network nor checksum blocks the Qt loop."""
        self._update_status("Procurando uma versão estável no GitHub…")

        def checked(info):
            self.pending_update = info
            if info is None:
                self._update_status("O NutriDesk já está atualizado.")
                if not silent:
                    QMessageBox.information(self, "Atualizações", "Você já está na versão mais recente.")
                return
            self._update_status(
                f"NutriDesk {info.version} disponível.\n\n"
                f"{info.notes[:1800]}\n\nPara instalar, use 'Atualizar agora'."
            )
            if silent:
                answer = QMessageBox.question(
                    self, "Atualização disponível",
                    f"NutriDesk {info.version} está disponível.\n\nDeseja instalar agora?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
                )
                if answer == QMessageBox.Yes:
                    # Worker cleanup runs when finished, so queue the next step.
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(0, self.install_update)

        self._start_update_worker(
            lambda progress: self.update_service.check(), checked, silent=bool(silent)
        )

    def _auto_update_check(self):
        if self.update_service.auto_check():
            self.check_updates(silent=True)

    def install_update(self):
        if getattr(self, "_update_worker", None) is not None:
            return
        info = self.pending_update
        if info is None:
            self.check_updates(silent=False)
            return
        if os.name != "nt":
            QMessageBox.information(self, "Atualizações", "A instalação integrada exige Windows.")
            return
        answer = QMessageBox.question(
            self, "Instalar atualização",
            f"Atualizar para NutriDesk {info.version}?\n\n"
            "O sistema fará backup do banco clínico antes de fechar, "
            "instalar e reabrir automaticamente. "
            "O Windows poderá solicitar permissão de administrador.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self._update_status("Baixando e validando a atualização. Os dados clínicos não serão alterados.")
        self._update_progress(0)

        def staged(items):
            installer, backup = items
            self._update_status("Instalador verificado. Backup concluído. Reiniciando para atualizar…")
            try:
                self.update_service.launch_staged(info, installer, backup)
            except Exception as exc:
                show_error(self, "Atualização", exc)
                return
            QApplication.quit()

        self._start_update_worker(
            lambda progress: self.update_service.stage(info, progress=progress), staged
        )
