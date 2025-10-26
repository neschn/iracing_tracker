################################################################################################################
# Projet : iRacing Tracker
# Fichier : iracing_tracker/ui/logs_panel.py
# Description : Panneau "MESSAGES / LOGS" (bas de fenêtre)
################################################################################################################

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QTextEdit, QFrame

from .constants import (
    FONT_FAMILY,
    FONT_SIZE_SECTION_TITLE,
    FONT_SIZE_LOG,
    SECTION_MARGIN,
    SECTION_TITLE_GAP,
)


class LogsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.separators = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        lay.setSpacing(6)

        title = QLabel("MESSAGES / LOGS")
        title.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        lay.addWidget(title)
        self._align_top(lay, title)
        lay.addSpacing(SECTION_TITLE_GAP)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFrameShape(QFrame.NoFrame)
        self.log_text.setFont(QFont(FONT_FAMILY, FONT_SIZE_LOG))
        lay.addWidget(self.log_text)

    @staticmethod
    def _align_top(layout, widget):
        if layout is None or widget is None:
            return
        try:
            layout.setAlignment(widget, Qt.AlignTop)
        except Exception:
            pass
