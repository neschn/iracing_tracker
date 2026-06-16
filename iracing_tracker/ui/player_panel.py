################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui/player_panel.py                                                                 #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Panneau "JOUEUR" (sélection joueur, record perso, dernier tour).                               #
################################################################################################################

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
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
    BASE_MARGIN,
    SECTION_TITLE_GAP,
    SECTION_SEPARATOR_SPACING,
    EDIT_ICON_PATH,
)
from .widgets import hsep as _hsep
from .qt_helpers import align_top, scrollbar_css, icon_button_css, load_svg_icon


#--------------------------------------------------------------------------------------------------------------#
# Panneau « JOUEUR » : sélecteur de joueur, record personnel et dernier tour.                                  #
#--------------------------------------------------------------------------------------------------------------#
class PlayerPanel(QWidget):

    #--------------------------------------------------------------------------------------------------------------#
    # Construit l'en-tête (titre + bouton éditer), le combo joueur et les métriques.                               #
    #--------------------------------------------------------------------------------------------------------------#
    def __init__(self, players: list[str] | None, on_player_changed, on_edit_players=None,
                 action_icon_px: int = 18, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.separators = []
        self._action_icon_px = int(action_icon_px or 18)
        self._on_player_changed = on_player_changed
        # Couleurs du thème courant et état actif/inactif du sélecteur (pour le restylage du combo)
        self._colors = None
        self._menu_enabled = True

        lay = QVBoxLayout(self)
        lay.setContentsMargins(BASE_MARGIN, BASE_MARGIN, BASE_MARGIN, BASE_MARGIN)
        lay.setSpacing(BASE_MARGIN)

        header = QWidget()
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(0, 0, 0, 0)
        title = QLabel("JOUEUR")
        title.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        h_lay.addWidget(title)
        align_top(h_lay, title)
        h_lay.addStretch(1)
        self.edit_players_btn = QPushButton("")
        self.edit_players_btn.setCursor(Qt.PointingHandCursor)
        self.edit_players_btn.setProperty("variant", "icon")
        self.edit_players_btn.setFixedSize(32, 32)
        self.edit_players_btn.setIconSize(QSize(self._action_icon_px, self._action_icon_px))
        self.edit_players_btn.setToolTip("Éditer la liste des joueurs")
        self.edit_players_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        # Le bouton n'est actif que si un callback d'édition est fourni
        if callable(on_edit_players):
            self.edit_players_btn.setEnabled(True)
            self.edit_players_btn.clicked.connect(on_edit_players)
        else:
            self.edit_players_btn.setEnabled(False)
        h_lay.addWidget(self.edit_players_btn)
        align_top(h_lay, self.edit_players_btn)
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
        if callable(self._on_player_changed):
            self.player_combo.currentTextChanged.connect(self._on_player_changed)
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

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour le record personnel affiché.                                                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def set_personal_record(self, text: str):
        self.best_time_label.setText(text or "---")

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour le temps du dernier tour affiché.                                                                 #
    #--------------------------------------------------------------------------------------------------------------#
    def set_current_lap(self, text: str):
        self.current_lap_label.setText(text or "---")

    #--------------------------------------------------------------------------------------------------------------#
    # Active/désactive le sélecteur de joueur (et le restyle selon l'état).                                        #
    #--------------------------------------------------------------------------------------------------------------#
    def set_menu_state(self, enabled: bool):
        self._menu_enabled = bool(enabled)
        self.player_combo.setEnabled(self._menu_enabled)
        self._restyle_combo()

    #--------------------------------------------------------------------------------------------------------------#
    # Recharge la liste des joueurs dans le combo en conservant la sélection si possible.                          #
    #--------------------------------------------------------------------------------------------------------------#
    def set_players(self, players: list[str] | None):
        current = self.player_combo.currentText()
        self.player_combo.blockSignals(True)
        self.player_combo.clear()
        if players:
            self.player_combo.addItems(players)
        else:
            self.player_combo.addItem("---")
        # Restaurer la sélection précédente si elle existe encore
        idx = -1
        if players:
            try:
                idx = next((i for i, p in enumerate(players) if str(p) == current), -1)
            except Exception:
                idx = -1
        self.player_combo.setCurrentIndex(0 if idx < 0 else idx)
        self.player_combo.blockSignals(False)
        # Si la sélection a changé, propager au reste de l'application
        new_cur = self.player_combo.currentText()
        if new_cur != current and callable(self._on_player_changed):
            self._on_player_changed(new_cur)

    #--------------------------------------------------------------------------------------------------------------#
    # Applique le thème courant (bouton-icône éditer + restylage du combo + séparateurs).                          #
    #--------------------------------------------------------------------------------------------------------------#
    def apply_palette(self, c: dict):
        self._colors = c

        # Bouton-icône "éditer les joueurs"
        self.edit_players_btn.setStyleSheet(icon_button_css(c))
        color = c.get("action_icon_color", c.get("control_fg", "#000000"))
        size = max(12, int(self._action_icon_px))
        edit_icon = load_svg_icon(EDIT_ICON_PATH, color, size)
        if edit_icon.isNull():
            self.edit_players_btn.setIcon(QIcon())
        else:
            self.edit_players_btn.setIcon(edit_icon)
        self.edit_players_btn.setIconSize(QSize(size, size))

        self._restyle_combo()

        for sep in self.separators:
            try:
                sep.setStyleSheet(f"QFrame{{background:{c['separator']};}}")
            except Exception:
                pass

    #--------------------------------------------------------------------------------------------------------------#
    # (Re)applique la feuille de style du combo selon le thème et l'état actif/inactif.                            #
    #--------------------------------------------------------------------------------------------------------------#
    def _restyle_combo(self):
        en = self._menu_enabled
        colors = self._colors
        if colors:
            fg_enabled = colors.get("control_fg", colors.get("text", "#000000"))
            fg_disabled = "#888888"
            text_color = fg_enabled if en else fg_disabled
            base_bg = colors.get("bg_secondary", "#f0f0f0")
            hover_bg = colors.get("interactive_hover", "#dcdcdc")
            menu_bg = colors.get("menu_item_bg", base_bg)
            list_text = colors.get("text", "#000000")
            track_border = colors.get("scrollbar_border", colors.get("separator", "#b0b0b0"))
            track_bg = colors.get("scrollbar_track", menu_bg)
            handle_start = colors.get("scrollbar_handle_start", colors.get("separator", "#b0b0b0"))
            handle_end = colors.get("scrollbar_handle_end", colors.get("text", "#555555"))
            handle_hover_start = colors.get("scrollbar_handle_hover_start", colors.get("text", "#666666"))
            handle_hover_end = colors.get("scrollbar_handle_hover_end", colors.get("text", "#222222"))
            scroll_css = scrollbar_css(
                "QComboBox QAbstractItemView",
                track_bg,
                track_border,
                handle_start,
                handle_end,
                handle_hover_start,
                handle_hover_end,
            )
            combo_ss = (
                f"QComboBox{{font-family:{FONT_FAMILY}; font-size:{FONT_SIZE_PLAYER}pt; "
                f"color:{text_color}; background:{base_bg}; border:1px solid transparent; padding:2px 6px;}}"
                f"QComboBox:!enabled{{color:{fg_disabled};}}"
                f"QComboBox:hover{{background:{hover_bg};}}"
                f"QComboBox:pressed{{background:{hover_bg};}}"
                f"QComboBox::drop-down{{border:0; width:16px;}}"
                f"QComboBox QAbstractItemView{{background:{menu_bg}; color:{list_text}; "
                f"selection-background-color:{hover_bg}; selection-color:{list_text}; border:0; outline:0;}}"
                f"QComboBox QAbstractItemView::item:hover{{background:{hover_bg}; color:{list_text}; border:none; outline:0;}}"
                f"QComboBox QAbstractItemView::item:selected{{background:{hover_bg}; color:{list_text}; border:none; outline:0;}}"
                f"{scroll_css}"
            )
            self.player_combo.setStyleSheet(combo_ss)
        else:
            fg = "#000000" if en else "#888888"
            scroll_css = scrollbar_css(
                "QComboBox QAbstractItemView",
                "#f5f5f5",
                "#bcbcbc",
                "#cfcfcf",
                "#8f8f8f",
                "#9f9f9f",
                "#6f6f6f",
            )
            self.player_combo.setStyleSheet(
                f"QComboBox{{font-family:{FONT_FAMILY}; font-size:{FONT_SIZE_PLAYER}pt; color:{fg}; padding:2px 6px;}}"
                f"QComboBox::drop-down{{border:0; width:16px;}}"
                "QComboBox QAbstractItemView{border:0; outline:0;}"
                "QComboBox QAbstractItemView::item:hover{border:none; outline:0;}"
                "QComboBox QAbstractItemView::item:selected{border:none; outline:0;}"
                f"{scroll_css}"
            )
