################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui/debug_panel.py                                                                  #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Panneau "DEBUG" (masquable, affiche les variables iRSDK).                                      #
################################################################################################################

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QTextOption, QIcon
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
    BASE_MARGIN,
    SECTION_TITLE_GAP,
    HIDE_ICON_PATH,
)
from .qt_helpers import align_top, scrollbar_css, icon_button_css, load_svg_icon


class DebugPanel(QWidget):
    def __init__(self, on_toggle_click, action_icon_px: int = 18, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.separators = []
        self._action_icon_px = int(action_icon_px or 18)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(BASE_MARGIN, BASE_MARGIN, BASE_MARGIN, BASE_MARGIN)
        lay.setSpacing(BASE_MARGIN)

        header = QWidget()
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel("DEBUG")
        lbl.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        h_lay.addWidget(lbl)
        align_top(h_lay, lbl)
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
        align_top(h_lay, self.debug_toggle_btn)
        lay.addWidget(header)
        lay.addSpacing(SECTION_TITLE_GAP)

        self.debug_text = QPlainTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setFrameShape(QFrame.NoFrame)
        self.debug_text.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEBUG))
        self.debug_text.setWordWrapMode(QTextOption.WrapAnywhere)
        lay.addWidget(self.debug_text, 1)

    #--------------------------------------------------------------------------------------------------------------#
    # Affiche les données de debug (préserve le scroll si l'utilisateur n'est pas en bas).                        #
    #--------------------------------------------------------------------------------------------------------------#
    def set_debug_data(self, data: dict):
        sb = self.debug_text.verticalScrollBar()
        at_bottom = sb.value() >= (sb.maximum() - 4)
        lines = [f"{k}: {v}" for k, v in (data or {}).items()]
        self.debug_text.setPlainText("\n".join(lines))
        if at_bottom:
            sb.setValue(sb.maximum())

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour l'infobulle du bouton selon l'état visible/masqué de la zone debug.                              #
    #--------------------------------------------------------------------------------------------------------------#
    def update_toggle_tooltip(self, visible: bool):
        self.debug_toggle_btn.setToolTip("Masquer la zone debug" if visible else "Afficher la zone debug")

    #--------------------------------------------------------------------------------------------------------------#
    # Applique le thème courant (zone de texte, bouton-icône, séparateurs).                                       #
    #--------------------------------------------------------------------------------------------------------------#
    def apply_palette(self, c: dict):
        scroll_track = c.get("scrollbar_track", c.get("bg_secondary", "#f0f0f0"))
        scroll_border = c.get("scrollbar_border", c.get("separator", "#b0b0b0"))
        handle_start = c.get("scrollbar_handle_start", c.get("separator", "#b0b0b0"))
        handle_end = c.get("scrollbar_handle_end", c.get("control_fg", "#7d7d7d"))
        handle_hover_start = c.get("scrollbar_handle_hover_start", c.get("control_fg", "#7d7d7d"))
        handle_hover_end = c.get("scrollbar_handle_hover_end", c.get("text", "#3a3a3a"))
        plain_scroll_css = scrollbar_css(
            "QPlainTextEdit", scroll_track, scroll_border,
            handle_start, handle_end, handle_hover_start, handle_hover_end,
        )
        self.debug_text.setStyleSheet(f"QPlainTextEdit{{background:{c['debug_bg']}; color:{c['text']};}}{plain_scroll_css}")

        # Bouton-icône (masquer la zone debug)
        self.debug_toggle_btn.setStyleSheet(icon_button_css(c))
        color = c.get("action_icon_color", c.get("control_fg", "#000000"))
        size = max(12, int(self._action_icon_px))
        hide_icon = load_svg_icon(HIDE_ICON_PATH, color, size)
        if hide_icon.isNull():
            self.debug_toggle_btn.setIcon(QIcon())
        else:
            self.debug_toggle_btn.setIcon(hide_icon)
        self.debug_toggle_btn.setIconSize(QSize(size, size))

        for sep in self.separators:
            try:
                sep.setStyleSheet(f"QFrame{{background:{c['separator']};}}")
            except Exception:
                pass
