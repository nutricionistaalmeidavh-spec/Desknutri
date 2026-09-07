from __future__ import annotations

import os

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from nutridesktop.services.auto_backup import BackupPolicy
from nutridesktop.ui_kit.components import SaveStateLabel

PAGE_TRANSITION_MS = 180
SAVE_FEEDBACK_MS = 220
SAVE_FEEDBACK_VISIBLE_MS = 1800


class FinalPolishMixin:
    """Microinterações visuais sem alterar contratos, eventos ou persistência."""

    def __init__(self):
        self._ui_motion_animations = {}
        self._save_feedback_generation = 0
        super().__init__()

    def _build(self):
        super()._build()
        topbar = self.findChild(QWidget, "topbar")
        layout = topbar.layout() if topbar is not None else None
        if layout is not None:
            self.save_state_label = SaveStateLabel("", "saved")
            self.save_state_label.setVisible(False)
            search_index = layout.indexOf(self.global_search) if hasattr(self, "global_search") else -1
            layout.insertWidget(search_index if search_index >= 0 else layout.count(), self.save_state_label)

    def show_page(self, name):
        previous = self.stack.currentWidget() if hasattr(self, "stack") else None
        result = super().show_page(name)
        current = self.stack.currentWidget() if hasattr(self, "stack") else None
        if current is not None and current is not previous:
            self._fade_in(current, PAGE_TRANSITION_MS, 0.82)
        return result

    def _motion_reduced(self) -> bool:
        return os.environ.get("NUTRIDESK_REDUCE_MOTION", "").strip() in {"1", "true", "yes"}

    def _fade_in(self, widget, duration: int, start_opacity: float = 0.65):
        if self._motion_reduced() or widget is None:
            return
        key = id(widget)
        previous = self._ui_motion_animations.pop(key, None)
        if previous is not None:
            previous.stop()

        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(start_opacity)
        widget.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(max(1, int(duration)))
        animation.setStartValue(start_opacity)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        self._ui_motion_animations[key] = animation

        def cleanup():
            if widget.graphicsEffect() is effect:
                widget.setGraphicsEffect(None)
            if self._ui_motion_animations.get(key) is animation:
                self._ui_motion_animations.pop(key, None)

        animation.finished.connect(cleanup)
        animation.start()

    def show_save_feedback(self, text: str = "Alterações salvas"):
        label = getattr(self, "save_state_label", None)
        if label is None:
            return
        self._save_feedback_generation += 1
        generation = self._save_feedback_generation
        label.set_state(text, "saved")
        label.setVisible(True)
        self._fade_in(label, SAVE_FEEDBACK_MS, 0.35)

        def hide_if_current():
            if generation == self._save_feedback_generation:
                label.setVisible(False)

        QTimer.singleShot(SAVE_FEEDBACK_VISIBLE_MS, hide_if_current)

    def save_update_settings(self):
        result = super().save_update_settings()
        self.show_save_feedback("Preferência de atualização salva")
        return result

    def save_default_template(self, typ, combo):
        template_id = combo.currentData()
        result = super().save_default_template(typ, combo)
        if template_id:
            self.show_save_feedback(f"Template padrão de {typ} salvo")
        return result

    def save_backup_policy(self):
        result = super().save_backup_policy()
        try:
            expected = BackupPolicy(
                self.ab_enabled.isChecked(),
                self.ab_frequency.currentText(),
                self.ab_run.currentText(),
                int(self.ab_daily.text()),
                int(self.ab_weekly.text()),
                int(self.ab_monthly.text()),
            ).normalized()
            if self.auto_backup_service.policy() == expected:
                self.show_save_feedback("Política de backup salva")
        except Exception:
            pass
        return result

    def save_template(self):
        result = super().save_template()
        try:
            template_id = self._editing_template_id
            row = next((item for item in self.tr.list() if item["id"] == template_id), None)
            if (
                row
                and row["nome"] == self.t_name.text().strip()
                and row["tipo"] == self.t_type.currentText()
                and row["conteudo"] == self.t_content.toPlainText().strip()
            ):
                self.show_save_feedback("Template salvo")
        except Exception:
            pass
        return result

    def save_protocol(self):
        result = super().save_protocol()
        try:
            slug = self.p_slug.text().strip()
            version = self.p_version.text().strip()
            row = next((item for item in self.pro.list(slug) if item["versao"] == version), None)
            if (
                row
                and row["titulo"] == self.p_title.text().strip()
                and row["conteudo"] == self.p_content.toPlainText().strip()
            ):
                self.show_save_feedback("Protocolo salvo")
        except Exception:
            pass
        return result
