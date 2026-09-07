from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .account_dialog import AccountActivationDialog
from .common import button, show_error
from nutridesktop.core.paths import DATA_DIR, EXPORT_DIR
from nutridesktop.services import licensing
from nutridesktop.services.account_licensing import AccountLicenseService
from nutridesktop.services.auto_backup import AutoBackupService, BackupPolicy
from nutridesktop.services.diagnostics import DiagnosticsService
from nutridesktop.services.patient_package import export_patient, import_patient
from nutridesktop.services.structured_export import export_csv_zip, export_json, export_xlsx
from nutridesktop.services.update_service import UpdateService
from nutridesktop.version import (
    APP_VERSION,
    CLINICAL_CONTENT_VERSION,
    SCHEMA_VERSION,
    WHO_ENGINE_VERSION,
)


class OperationalFeaturesMixin:
    """Recursos operacionais antes versionados como P3.

    Este mixin preserva backup automático, atualização, portabilidade e suporte
    sem acoplar a janela principal a uma versão histórica do produto.
    """

    def __init__(self):
        self.auto_backup_service = AutoBackupService()
        self.update_service = UpdateService()
        self.diagnostics_service = DiagnosticsService()
        self.pending_update = None
        super().__init__()
        try:
            self.update_service.record_result()
        except Exception:
            pass
        QTimer.singleShot(1200, self._startup_backup)
        QTimer.singleShot(2600, self._auto_update_check)

    def show_page(self, name):
        if name in {"Atualizações", "Exportações", "Suporte"}:
            self.lock.touch()
            if name in self.pages:
                self.stack.setCurrentWidget(self.pages[name])
                return
            factory = {
                "Atualizações": self.updates_page,
                "Exportações": self.exports_page,
                "Suporte": self.support_page,
            }[name]
            w = factory()
            self.pages[name] = w
            self.stack.addWidget(w)
            self.stack.setCurrentWidget(w)
            return
        return super().show_page(name)

    def settings(self):
        w = super().settings()
        policy = self.auto_backup_service.policy()
        bk = self.settings_backup_layout
        box = QWidget()
        f = QFormLayout(box)
        self.ab_enabled = QCheckBox("Ativar backup automático")
        self.ab_enabled.setChecked(policy.enabled)
        self.ab_frequency = QComboBox()
        self.ab_frequency.addItems(["daily", "weekly"])
        self.ab_frequency.setCurrentText(policy.frequency)
        self.ab_run = QComboBox()
        self.ab_run.addItems(["startup", "close", "startup_or_close"])
        self.ab_run.setCurrentText(policy.run_at)
        self.ab_daily = QLineEdit(str(policy.retain_daily))
        self.ab_weekly = QLineEdit(str(policy.retain_weekly))
        self.ab_monthly = QLineEdit(str(policy.retain_monthly))
        f.addRow("Backup automático", self.ab_enabled)
        f.addRow("Frequência", self.ab_frequency)
        f.addRow("Executar em", self.ab_run)
        f.addRow("Retenção diária", self.ab_daily)
        f.addRow("Retenção semanal", self.ab_weekly)
        f.addRow("Retenção mensal", self.ab_monthly)
        f.addRow("", button("Salvar política de backup", self.save_backup_policy, True))
        bk.insertWidget(max(1, bk.count() - 1), box)

        data = self.settings_data_layout
        row = QHBoxLayout()
        row.addWidget(button("Exportações e portabilidade", lambda: self.show_page("Exportações")))
        row.addStretch()
        data.insertLayout(max(1, data.count() - 1), row)

        adv = self.settings_advanced_layout
        row2 = QHBoxLayout()
        row2.addWidget(button("Atualizações", lambda: self.show_page("Atualizações")))
        row2.addWidget(button("Suporte e diagnóstico", lambda: self.show_page("Suporte")))
        row2.addStretch()
        adv.insertLayout(max(1, adv.count() - 1), row2)
        return w

    def save_backup_policy(self):
        try:
            p = BackupPolicy(
                self.ab_enabled.isChecked(),
                self.ab_frequency.currentText(),
                self.ab_run.currentText(),
                int(self.ab_daily.text()),
                int(self.ab_weekly.text()),
                int(self.ab_monthly.text()),
            ).normalized()
            self.auto_backup_service.save_policy(p)
            QMessageBox.information(self, "Backup automático", "Política salva.")
        except Exception as e:
            show_error(self, "Backup automático", e)

    def _startup_backup(self):
        try:
            self.auto_backup_service.maybe_run("startup")
        except Exception:
            pass

    def closeEvent(self, event):
        try:
            self.auto_backup_service.maybe_run("close")
        except Exception:
            pass
        return super().closeEvent(event)

    def updates_page(self):
        w, v = self.page(
            "Atualizações",
            "Release assinada, verificação SHA-256, health-check e rollback assistido.",
        )
        v.addWidget(
            QLabel(
                f"Instalado: App {APP_VERSION} | Schema {SCHEMA_VERSION} | "
                f"Clínico {CLINICAL_CONTENT_VERSION} | WHO {WHO_ENGINE_VERSION}"
            )
        )
        form = QFormLayout()
        self.upd_url = QLineEdit(self.update_service.manifest_url())
        self.upd_url.setPlaceholderText("https://.../version.json ou caminho local")
        self.upd_channel = QComboBox()
        self.upd_channel.addItems(["stable", "beta"])
        self.upd_channel.setCurrentText(self.update_service.channel())
        self.upd_auto = QCheckBox("Verificar automaticamente ao abrir")
        self.upd_auto.setChecked(self.update_service.auto_check())
        form.addRow("Manifesto assinado", self.upd_url)
        form.addRow("Canal", self.upd_channel)
        form.addRow("", self.upd_auto)
        v.addLayout(form)
        row = QHBoxLayout()
        row.addWidget(button("Salvar configuração", self.save_update_settings))
        row.addWidget(button("Verificar agora", self.check_updates, True))
        row.addWidget(button("Baixar e instalar", self.install_update))
        row.addStretch()
        v.addLayout(row)
        self.upd_status = QTextEdit()
        self.upd_status.setReadOnly(True)
        self.upd_status.setPlainText("Nenhuma verificação nesta sessão.")
        v.addWidget(self.upd_status)
        return w

    def save_update_settings(self):
        self.update_service.set_manifest_url(self.upd_url.text())
        self.update_service.set_channel(self.upd_channel.currentText())
        self.update_service.set_auto_check(self.upd_auto.isChecked())
        QMessageBox.information(self, "Atualizações", "Configuração salva.")

    def check_updates(self, silent=False):
        try:
            if hasattr(self, "upd_url") and not silent:
                self.save_update_settings()
            info = self.update_service.check()
            self.pending_update = info
            if info:
                msg = f"Versão {info.version} disponível ({info.channel}).\n\n{info.notes[:2500]}"
                if hasattr(self, "upd_status"):
                    self.upd_status.setPlainText(msg)
                if not silent:
                    QMessageBox.information(self, "Atualização disponível", msg)
            else:
                if hasattr(self, "upd_status"):
                    self.upd_status.setPlainText("Nenhuma atualização aplicável encontrada.")
                if not silent:
                    QMessageBox.information(
                        self,
                        "Atualizações",
                        "Você já está na versão mais recente do canal configurado.",
                    )
            return info
        except Exception as e:
            if hasattr(self, "upd_status"):
                self.upd_status.setPlainText(str(e))
            if not silent:
                show_error(self, "Atualizações", e)
            return None

    def _auto_update_check(self):
        if not self.update_service.auto_check() or not self.update_service.manifest_url():
            return
        info = self.check_updates(silent=True)
        if info:
            QMessageBox.information(
                self,
                "Nova versão disponível",
                f"NutriDesk {info.version} está disponível. Abra Atualizações para revisar e instalar.",
            )

    def install_update(self):
        info = self.pending_update or self.check_updates(silent=True)
        if not info:
            QMessageBox.information(self, "Atualizações", "Nenhuma atualização nova encontrada.")
            return
        if (
            QMessageBox.question(
                self,
                "Instalar atualização",
                f"Baixar e instalar NutriDesk {info.version}? O aplicativo será fechado e fará health-check após instalar.",
            )
            != QMessageBox.Yes
        ):
            return
        try:
            installer, rollback = self.update_service.stage(info)
            self.update_service.launch_staged(info, installer, rollback)
            QApplication.quit()
        except Exception as e:
            show_error(self, "Atualização", e)

    def exports_page(self):
        w, v = self.page(
            "Exportações e portabilidade",
            "Pacote nativo .nutri e exportações estruturadas JSON, CSV e XLSX.",
        )
        self.export_patient_combo = QComboBox()
        self._refresh_export_patients()
        v.addWidget(QLabel("Paciente para pacote .nutri:"))
        v.addWidget(self.export_patient_combo)
        row = QHBoxLayout()
        row.addWidget(button("Exportar .nutri", self.export_nutri, True))
        row.addWidget(button("Importar .nutri", self.import_nutri))
        row.addStretch()
        v.addLayout(row)
        v.addWidget(QLabel("Exportação estruturada de todo o consultório:"))
        row2 = QHBoxLayout()
        row2.addWidget(button("JSON", self.export_structured_json))
        row2.addWidget(button("CSV ZIP", self.export_structured_csv))
        row2.addWidget(button("Excel XLSX", self.export_structured_xlsx))
        row2.addStretch()
        v.addLayout(row2)
        v.addWidget(QLabel("PDFs clínicos continuam disponíveis no prontuário individual."))
        v.addStretch()
        return w

    def _refresh_export_patients(self):
        if not hasattr(self, "export_patient_combo"):
            return
        self.export_patient_combo.clear()
        for p in self.pr.list():
            self.export_patient_combo.addItem(f"{p['id']} - {p['nome']}", p["id"])

    def export_nutri(self):
        pid = self.export_patient_combo.currentData()
        if pid is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar paciente",
            f"paciente_{pid}.nutri",
            "NutriDesk Patient (*.nutri)",
        )
        if not path:
            return
        password, ok = QInputDialog.getText(
            self,
            "Proteção opcional",
            "Senha do pacote (deixe vazio para sem senha)",
            QLineEdit.Password,
        )
        if not ok:
            return
        try:
            export_patient(int(pid), path, password or None)
            QMessageBox.information(self, ".nutri", "Paciente exportado com checksums.")
        except Exception as e:
            show_error(self, ".nutri", e)

    def import_nutri(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar paciente", "", "NutriDesk Patient (*.nutri)"
        )
        if not path:
            return
        password, _ = QInputDialog.getText(
            self, "Senha", "Senha do pacote se houver", QLineEdit.Password
        )
        try:
            pid = import_patient(path, password or None)
            self.refresh_patients()
            self._refresh_export_patients()
            QMessageBox.information(self, ".nutri", f"Paciente importado com novo ID {pid}.")
        except Exception as e:
            show_error(self, ".nutri", e)

    def _export_path(self, title, default, filter_text):
        return QFileDialog.getSaveFileName(
            self, title, str(EXPORT_DIR / default), filter_text
        )[0]

    def export_structured_json(self):
        path = self._export_path("Exportar JSON", "NutriDesk-dados.json", "JSON (*.json)")
        if path:
            try:
                export_json(path)
                QMessageBox.information(self, "Exportação", "JSON exportado.")
            except Exception as e:
                show_error(self, "Exportação", e)

    def export_structured_csv(self):
        path = self._export_path("Exportar CSV", "NutriDesk-CSV.zip", "ZIP (*.zip)")
        if path:
            try:
                export_csv_zip(path)
                QMessageBox.information(self, "Exportação", "CSV ZIP exportado.")
            except Exception as e:
                show_error(self, "Exportação", e)

    def export_structured_xlsx(self):
        path = self._export_path(
            "Exportar Excel", "NutriDesk-dados.xlsx", "Excel (*.xlsx)"
        )
        if path:
            try:
                export_xlsx(path)
                QMessageBox.information(self, "Exportação", "XLSX exportado.")
            except Exception as e:
                show_error(self, "Exportação", e)

    def support_page(self):
        w, v = self.page(
            "Suporte e diagnóstico",
            "Informações técnicas sem expor banco de dados ou prontuários.",
        )
        self.diag_text = QTextEdit()
        self.diag_text.setReadOnly(True)
        v.addWidget(self.diag_text)
        row = QHBoxLayout()
        row.addWidget(button("Atualizar diagnóstico", self.refresh_diagnostics, True))
        row.addWidget(button("Criar pacote de suporte", self.create_support_bundle))
        row.addWidget(button("Abrir pasta de dados", self.open_data_dir))
        row.addStretch()
        v.addLayout(row)
        v.addWidget(
            QLabel(
                "O pacote de suporte contém diagnóstico e logs redigidos; não inclui banco, fotos ou documentos clínicos."
            )
        )
        self.refresh_diagnostics()
        return w

    def refresh_diagnostics(self):
        try:
            self.diag_text.setPlainText(self.diagnostics_service.text())
        except Exception as e:
            self.diag_text.setPlainText(str(e))

    def create_support_bundle(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Pacote de suporte",
            f"NutriDesk-Diagnostico-{date.today().isoformat()}.zip",
            "ZIP (*.zip)",
        )
        if not path:
            return
        try:
            self.diagnostics_service.create_support_bundle(path)
            QMessageBox.information(
                self, "Suporte", "Pacote técnico criado sem prontuários."
            )
        except Exception as e:
            show_error(self, "Suporte", e)

    def open_data_dir(self):
        try:
            if os.name == "nt":
                os.startfile(str(DATA_DIR))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(DATA_DIR)])
            else:
                subprocess.Popen(["xdg-open", str(DATA_DIR)])
        except Exception as e:
            show_error(self, "Pasta de dados", e)


class AccountFeaturesMixin:
    """Recursos de conta/licenciamento antes versionados como V4."""

    def __init__(self):
        self.account_license = AccountLicenseService()
        super().__init__()

    def show_page(self, name):
        if name == "Conta":
            self.lock.touch()
            if name in self.pages:
                self.stack.removeWidget(self.pages[name])
                self.pages[name].deleteLater()
                del self.pages[name]
            w = self.account_page()
            self.pages[name] = w
            self.stack.addWidget(w)
            self.stack.setCurrentWidget(w)
            return
        return super().show_page(name)

    def account_page(self):
        w, v = self.page(
            "Conta",
            "Sua licença e este computador. Configurações técnicas do servidor são gerenciadas pelo NutriDesk.",
        )
        st = self.account_license.state()
        lic = licensing.current()
        v.addWidget(QLabel(f"E-mail: {st.email or 'não ativado'}"))
        v.addWidget(QLabel(f"Plano: {(lic or {}).get('plan', '—')}"))
        v.addWidget(QLabel(f"Licença válida até: {(lic or {}).get('expires', '—')}"))
        v.addWidget(QLabel(f"Computador: {licensing.machine_id()}"))
        v.addWidget(QLabel(f"Última renovação: {st.last_refresh or '—'}"))
        if st.last_error:
            v.addWidget(
                QLabel(
                    "Houve uma falha na última tentativa de conexão. A autorização offline continua válida enquanto estiver dentro do prazo."
                )
            )
        row = QHBoxLayout()
        row.addWidget(button("Ativar / trocar conta", self.open_account_activation, True))
        row.addWidget(button("Renovar agora", self.refresh_account))
        row.addStretch()
        v.addLayout(row)
        row2 = QHBoxLayout()
        row2.addWidget(button("Trocar senha", self.change_account_password))
        row2.addWidget(button("Desvincular este computador", self.unlink_account))
        row2.addStretch()
        v.addLayout(row2)
        self.account_feedback = QLabel("Pronto.")
        self.account_feedback.setObjectName("muted")
        v.addWidget(self.account_feedback)
        note = QLabel(
            "A senha não fica salva no NutriDesk. Após a ativação, este computador recebe um token próprio para renovar a licença."
        )
        note.setWordWrap(True)
        v.addWidget(note)
        v.addStretch()
        return w

    def settings(self):
        w = super().settings()
        st = self.account_license.state()
        lic = licensing.current()
        general = self.settings_tabs.widget(0).layout()
        card = QWidget()
        lay = QVBoxLayout(card)
        lay.addWidget(QLabel("Status da conta"))
        lay.addWidget(
            QLabel(
                f"{st.email or 'Não ativado'} • {(lic or {}).get('plan', '—')} • validade {(lic or {}).get('expires', '—')}"
            )
        )
        lay.addWidget(button("Abrir conta e licença", lambda: self.show_page("Conta")))
        general.insertWidget(max(1, general.count() - 1), card)
        return w

    def save_account_server(self):
        try:
            self.account_license.set_server_url(self.account_server.text())
            QMessageBox.information(self, "Conta", "Servidor salvo.")
        except Exception as e:
            show_error(self, "Conta", e)

    def open_account_activation(self):
        try:
            dlg = AccountActivationDialog(self.account_license, self)
            dlg.email.setText(self.account_license.state().email)
            dlg.exec()
        except Exception as e:
            show_error(self, "Conta", e)

    def refresh_account(self):
        if hasattr(self, "account_feedback"):
            self.account_feedback.setText("Verificando licença…")
            QApplication.processEvents()
        try:
            self.account_license.refresh()
            if hasattr(self, "account_feedback"):
                self.account_feedback.setText("Licença renovada com sucesso.")
            QMessageBox.information(self, "Conta", "Licença renovada neste computador.")
        except Exception as e:
            if hasattr(self, "account_feedback"):
                self.account_feedback.setText("Não foi possível renovar agora.")
            show_error(self, "Conta", e)

    def change_account_password(self):
        current, ok = QInputDialog.getText(
            self, "Senha atual", "Senha atual:", QLineEdit.Password
        )
        if not ok:
            return
        new, ok = QInputDialog.getText(
            self,
            "Nova senha",
            "Nova senha (mínimo 8 caracteres):",
            QLineEdit.Password,
        )
        if not ok:
            return
        try:
            self.account_license.change_password(current, new)
            QMessageBox.information(self, "Conta", "Senha alterada.")
        except Exception as e:
            show_error(self, "Conta", e)

    def unlink_account(self):
        if (
            QMessageBox.question(
                self,
                "Desvincular",
                "Desvincular este computador libera uma vaga da licença e exigirá login novamente. Continuar?",
            )
            != QMessageBox.Yes
        ):
            return
        try:
            self.account_license.unlink_current()
            QMessageBox.information(
                self,
                "Conta",
                "Computador desvinculado. O NutriDesk exigirá ativação no próximo início.",
            )
        except Exception as e:
            show_error(self, "Conta", e)
