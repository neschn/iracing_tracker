################################################################################################################
# Projet : iRacing Tracker
# Fichier : iracing_tracker/ui/last_laps_panel.py
# Description : Panneau "DERNIERS TOURS"
################################################################################################################

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy

from .constants import (
    FONT_FAMILY,
    FONT_SIZE_SECTION_TITLE,
    SECTION_MARGIN,
    SECTION_TITLE_GAP,
)
from .widgets import LastLapsList as _LastLapsList


class SessionTimesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        lay.setSpacing(6)

        cap = QLabel("TEMPS DE LA SESSION")
        cap.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        lay.addWidget(cap)
        self._align_top(lay, cap)
        lay.addSpacing(SECTION_TITLE_GAP)

        self.laps_list = _LastLapsList()
        lay.addWidget(self.laps_list, 1)

    @staticmethod
    def _align_top(layout, widget):
        if layout is None or widget is None:
            return
        try:
            layout.setAlignment(widget, Qt.AlignTop)
        except Exception:
            pass
