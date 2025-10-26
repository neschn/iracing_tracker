################################################################################################################
# Projet : iRacing Tracker
# Fichier : iracing_tracker/ui/debug_panel.py
# Description : Panneau "DEBUG" (masquable)
################################################################################################################

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QTextOption
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QFrame,
    QSizePolicy,
)

from .constants import (
    FONT_FAMILY,
    FONT_SIZE_SECTION_TITLE,
    FONT_SIZE_DEBUG,
    FONT_SIZE_BUTTON,
    SECTION_MARGIN,
    SECTION_TITLE_GAP,
)


class DebugPanel(QWidget):
    def __init__(self, on_toggle_click, action_icon_px: int = 18, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.separators = []
        self._action_icon_px = int(action_icon_px or 18)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        lay.setSpacing(6)

        header = QWidget()
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel("DEBUG")
        lbl.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        h_lay.addWidget(lbl)
        self._align_top(h_lay, lbl)
        h_lay.addStretch(1)

        self.debug_toggle_btn = QPushButton("")
        self.debug_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.debug_toggle_btn.setProperty("variant", "icon")
        self.debug_toggle_btn.setFixedSize(32, 32)
        self.debug_toggle_btn.setIconSize(QSize(self._action_icon_px, self._action_icon_px))
        self.debug_toggle_btn.setToolTip("Masquer la zone debug")
        self.debug_toggle_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        if callable(on_toggle_click):
            self.debug_toggle_btn.clicked.connect(lambda: on_toggle_click(False))
        h_lay.addWidget(self.debug_toggle_btn)
        self._align_top(h_lay, self.debug_toggle_btn)
        lay.addWidget(header)
        lay.addSpacing(SECTION_TITLE_GAP)

        self.debug_text = QPlainTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setFrameShape(QFrame.NoFrame)
        self.debug_text.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEBUG))
        self.debug_text.setWordWrapMode(QTextOption.WrapAnywhere)
        lay.addWidget(self.debug_text, 1)

    @staticmethod
    def _align_top(layout, widget):
        if layout is None or widget is None:
            return
        try:
            layout.setAlignment(widget, Qt.AlignTop)
        except Exception:
            pass

