################################################################################################################
# Projet : iRacing Tracker
# Fichier : iracing_tracker/ui/player_panel.py
# Description : Panneau "JOUEUR" (sélection joueur, record perso, dernier tour)
################################################################################################################

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QSizePolicy,
)

from .constants import (
    FONT_FAMILY,
    FONT_SIZE_SECTION_TITLE,
    FONT_SIZE_LABELS,
    FONT_SIZE_PLAYER,
    FONT_SIZE_LAPTIME,
    FONT_SIZE_BUTTON,
    SECTION_MARGIN,
    SECTION_TITLE_GAP,
    SECTION_SEPARATOR_SPACING,
)
from .widgets import hsep as _hsep


class PlayerPanel(QWidget):
    """Colonne JOUEUR avec combo et métriques."""

    def __init__(self, players: list[str] | None, on_player_changed, action_icon_px: int = 18, parent=None):
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
        title = QLabel("JOUEUR")
        title.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        h_lay.addWidget(title)
        self._align_top(h_lay, title)
        h_lay.addStretch(1)
        self.edit_players_btn = QPushButton("")
        self.edit_players_btn.setCursor(Qt.PointingHandCursor)
        self.edit_players_btn.setProperty("variant", "icon")
        self.edit_players_btn.setFixedSize(32, 32)
        self.edit_players_btn.setIconSize(QSize(self._action_icon_px, self._action_icon_px))
        self.edit_players_btn.setToolTip("Éditer la liste des joueurs")
        self.edit_players_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        self.edit_players_btn.setEnabled(False)  # inchangé
        h_lay.addWidget(self.edit_players_btn)
        self._align_top(h_lay, self.edit_players_btn)
        lay.addWidget(header)
        lay.addSpacing(SECTION_TITLE_GAP)

        players = list(players) if players else ["---"]
        self.player_combo = QComboBox()
        self.player_combo.setEditable(False)
        self.player_combo.addItems(players)
        self.player_combo.setCurrentIndex(0)
        self.player_combo.setStyleSheet(
            f"QComboBox{{font-family:{FONT_FAMILY}; font-size:{FONT_SIZE_PLAYER}pt;}}"
        )
        if callable(on_player_changed):
            self.player_combo.currentTextChanged.connect(on_player_changed)
        lay.addWidget(self.player_combo)

        s = _hsep(self); self.separators.append(s)
        lay.addSpacing(SECTION_SEPARATOR_SPACING); lay.addWidget(s); lay.addSpacing(SECTION_SEPARATOR_SPACING)

        lbl_personal = QLabel("Record personnel :")
        lbl_personal.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        lay.addWidget(lbl_personal)

        self.best_time_label = QLabel("-:--.---")
        self.best_time_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAPTIME, QFont.Bold))
        self.best_time_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.best_time_label)

        s = _hsep(self); self.separators.append(s)
        lay.addSpacing(SECTION_SEPARATOR_SPACING); lay.addWidget(s); lay.addSpacing(SECTION_SEPARATOR_SPACING)

        lbl_last = QLabel("Dernier tour :")
        lbl_last.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        lay.addWidget(lbl_last)

        self.current_lap_label = QLabel("-:--.---")
        self.current_lap_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAPTIME, QFont.Bold))
        self.current_lap_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.current_lap_label)
        lay.addStretch(1)

    @staticmethod
    def _align_top(layout, widget):
        if layout is None or widget is None:
            return
        try:
            layout.setAlignment(widget, Qt.AlignTop)
        except Exception:
            pass

