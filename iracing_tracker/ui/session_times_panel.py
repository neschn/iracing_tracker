################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui/session_times_panel.py                                                          #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Panneau "TEMPS DE LA SESSION" (liste des derniers tours).                                      #
################################################################################################################

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy

from .constants import (
    FONT_FAMILY,
    FONT_SIZE_SECTION_TITLE,
    BASE_MARGIN,
    SECTION_TITLE_GAP,
)
from .widgets import LastLapsList as _LastLapsList
from .qt_helpers import align_top, scrollbar_css


#--------------------------------------------------------------------------------------------------------------#
# Panneau « TEMPS DE LA SESSION » : liste des derniers tours.                                                  #
#--------------------------------------------------------------------------------------------------------------#
class SessionTimesPanel(QWidget):

    #--------------------------------------------------------------------------------------------------------------#
    # Construit le titre et la liste des derniers tours.                                                           #
    #--------------------------------------------------------------------------------------------------------------#
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(BASE_MARGIN, BASE_MARGIN, BASE_MARGIN, BASE_MARGIN)
        lay.setSpacing(BASE_MARGIN)

        cap = QLabel("TEMPS DE LA SESSION")
        cap.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        lay.addWidget(cap)
        align_top(lay, cap)
        lay.addSpacing(SECTION_TITLE_GAP)

        self.laps_list = _LastLapsList()
        lay.addWidget(self.laps_list, 1)

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour la liste des derniers tours affichés.                                                             #
    #--------------------------------------------------------------------------------------------------------------#
    def set_items(self, entries):
        self.laps_list.set_items(entries)

    #--------------------------------------------------------------------------------------------------------------#
    # Applique le thème courant à la liste (couleurs + scrollbar).                                                 #
    #--------------------------------------------------------------------------------------------------------------#
    def apply_palette(self, c: dict):
        scroll_track = c.get("scrollbar_track", c.get("bg_secondary", "#f0f0f0"))
        scroll_border = c.get("scrollbar_border", c.get("separator", "#b0b0b0"))
        handle_start = c.get("scrollbar_handle_start", c.get("separator", "#b0b0b0"))
        handle_end = c.get("scrollbar_handle_end", c.get("control_fg", "#7d7d7d"))
        handle_hover_start = c.get("scrollbar_handle_hover_start", c.get("control_fg", "#7d7d7d"))
        handle_hover_end = c.get("scrollbar_handle_hover_end", c.get("text", "#3a3a3a"))
        list_scroll_css = scrollbar_css(
            "QListWidget", scroll_track, scroll_border,
            handle_start, handle_end, handle_hover_start, handle_hover_end,
        )
        try:
            self.laps_list.apply_palette(
                c['text'], c['bg_main'],
                c.get('last_laps_hover', c.get('interactive_hover')),
                list_scroll_css,
            )
        except Exception:
            pass
