################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui/logs_panel.py                                                                   #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Panneau "MESSAGES / LOGS" (bas de fenêtre).                                                    #
################################################################################################################

from datetime import datetime

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QTextEdit, QFrame

from .constants import (
    FONT_FAMILY,
    FONT_SIZE_SECTION_TITLE,
    FONT_SIZE_LOG,
    BASE_MARGIN,
    SECTION_TITLE_GAP,
)
from .qt_helpers import align_top, scrollbar_css


#--------------------------------------------------------------------------------------------------------------#
# Panneau « MESSAGES / LOGS » affiché en bas de fenêtre.                                                       #
#--------------------------------------------------------------------------------------------------------------#
class LogsPanel(QWidget):

    #--------------------------------------------------------------------------------------------------------------#
    # Construit le titre et la zone de logs en lecture seule.                                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def __init__(self, parent=None):
        super().__init__(parent)
        self.separators = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(BASE_MARGIN, BASE_MARGIN, BASE_MARGIN, BASE_MARGIN)
        lay.setSpacing(BASE_MARGIN)

        title = QLabel("MESSAGES / LOGS")
        title.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        lay.addWidget(title)
        align_top(lay, title)
        lay.addSpacing(SECTION_TITLE_GAP)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFrameShape(QFrame.NoFrame)
        self.log_text.setFont(QFont(FONT_FAMILY, FONT_SIZE_LOG))
        lay.addWidget(self.log_text)

    #--------------------------------------------------------------------------------------------------------------#
    # Ajoute un message horodaté dans la zone de logs.                                                             #
    #--------------------------------------------------------------------------------------------------------------#
    def append_log(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {message}")

    #--------------------------------------------------------------------------------------------------------------#
    # Applique le thème courant à la zone de logs (couleurs + scrollbar).                                          #
    #--------------------------------------------------------------------------------------------------------------#
    def apply_palette(self, c: dict):
        scroll_track = c.get("scrollbar_track", c.get("bg_secondary", "#f0f0f0"))
        scroll_border = c.get("scrollbar_border", c.get("separator", "#b0b0b0"))
        handle_start = c.get("scrollbar_handle_start", c.get("separator", "#b0b0b0"))
        handle_end = c.get("scrollbar_handle_end", c.get("control_fg", "#7d7d7d"))
        handle_hover_start = c.get("scrollbar_handle_hover_start", c.get("control_fg", "#7d7d7d"))
        handle_hover_end = c.get("scrollbar_handle_hover_end", c.get("text", "#3a3a3a"))
        text_scroll_css = scrollbar_css(
            "QTextEdit", scroll_track, scroll_border,
            handle_start, handle_end, handle_hover_start, handle_hover_end,
        )
        self.log_text.setStyleSheet(f"QTextEdit{{background:{c['log_bg']}; color:{c['text']};}}{text_scroll_css}")
