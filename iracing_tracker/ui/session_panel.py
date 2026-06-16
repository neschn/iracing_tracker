################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui/session_panel.py                                                                #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Panneau "SESSION" (infos session, top 3).                                                      #
################################################################################################################

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QSizePolicy,
)

from .constants import (
    FONT_FAMILY,
    FONT_SIZE_SECTION_TITLE,
    FONT_SIZE_LABELS,
    FONT_SIZE_LAPTIME,
    FONT_SIZE_RANKING_PLAYER,
    FONT_WEIGHT_RANKING_PLAYER,
    BASE_MARGIN,
    SECTION_TITLE_GAP,
    SECTION_SEPARATOR_SPACING,
    MEDAL_GOLD_ICON_PATH,
    MEDAL_SILVER_ICON_PATH,
    MEDAL_BRONZE_ICON_PATH,
    MEDAL_ICON_SIZE,
    LIST_ICON_PATH,
)
from .widgets import hsep as _hsep
from .qt_helpers import align_top, load_svg_pixmap, resolve_font_weight, load_svg_icon, icon_button_css
from iracing_tracker.record_manager import format_lap_time


class SessionPanel(QWidget):
    """Colonne gauche: SESSION + Top3."""

    def __init__(self, action_icon_px: int = 18, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.separators = []
        self.absolute_rank_rows = []
        self._medal_icon_px = MEDAL_ICON_SIZE
        self._action_icon_px = int(action_icon_px or 18)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(BASE_MARGIN, BASE_MARGIN, BASE_MARGIN, BASE_MARGIN)
        lay.setSpacing(BASE_MARGIN)

        # Titre
        title = QLabel("SESSION")
        title.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        lay.addWidget(title)
        align_top(lay, title)
        lay.addSpacing(SECTION_TITLE_GAP)

        # Infos session (time / track / car)
        info_rows = QWidget()
        ir_lay = QGridLayout(info_rows)
        ir_lay.setContentsMargins(0, 0, 0, 0)
        ir_lay.setHorizontalSpacing(12)
        ir_lay.setVerticalSpacing(4)

        self.session_time_label = QLabel("Temps de session :")
        self.session_time_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        ir_lay.addWidget(self.session_time_label, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)

        self.session_time_value = QLabel("-:--:--")
        self.session_time_value.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        ir_lay.addWidget(self.session_time_value, 0, 1, Qt.AlignLeft | Qt.AlignVCenter)

        self.track_label = QLabel("Circuit :")
        self.track_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        ir_lay.addWidget(self.track_label, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)

        self.track_value = QLabel("---")
        self.track_value.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        self.track_value.setWordWrap(False)
        self.track_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        ir_lay.addWidget(self.track_value, 1, 1, Qt.AlignLeft | Qt.AlignVCenter)

        self.car_label = QLabel("Voiture :")
        self.car_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        ir_lay.addWidget(self.car_label, 2, 0, Qt.AlignLeft | Qt.AlignVCenter)

        self.car_value = QLabel("---")
        self.car_value.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        self.car_value.setWordWrap(False)
        self.car_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        ir_lay.addWidget(self.car_value, 2, 1, Qt.AlignLeft | Qt.AlignVCenter)

        ir_lay.setColumnStretch(0, 0)
        ir_lay.setColumnStretch(1, 1)
        lay.addWidget(info_rows)

        # Contraintes de largeur similaires à l'implémentation d'origine
        try:
            from PySide6.QtGui import QFontMetrics
            fm = QFontMetrics(self.track_value.font())
            self.track_value.setMinimumWidth(fm.horizontalAdvance("W" * 28))
            fm_car = QFontMetrics(self.car_value.font())
            self.car_value.setMinimumWidth(fm_car.horizontalAdvance("W" * 28))
        except Exception:
            pass

        s = _hsep(self); self.separators.append(s)
        lay.addSpacing(SECTION_SEPARATOR_SPACING); lay.addWidget(s); lay.addSpacing(SECTION_SEPARATOR_SPACING)

        # Classement
        ranking_header = QWidget()
        rh_lay = QHBoxLayout(ranking_header)
        rh_lay.setContentsMargins(0, 0, 0, 0)
        self.absolute_ranking_label = QLabel("Classement :")
        self.absolute_ranking_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        rh_lay.addWidget(self.absolute_ranking_label)
        align_top(rh_lay, self.absolute_ranking_label)
        rh_lay.addStretch(1)
        self.rankings_btn = QPushButton("")
        self.rankings_btn.setCursor(Qt.PointingHandCursor)
        self.rankings_btn.setProperty("variant", "icon")
        self.rankings_btn.setFixedSize(32, 32)
        # Icon is applied by app via theme
        rh_lay.addWidget(self.rankings_btn)
        align_top(rh_lay, self.rankings_btn)
        lay.addWidget(ranking_header)

        ranking_rows = QWidget()
        rr_lay = QVBoxLayout(ranking_rows)
        rr_lay.setContentsMargins(0, 0, 0, 0)
        rr_lay.setSpacing(4)

        medal_defs = [
            (MEDAL_GOLD_ICON_PATH, "Nico"),
            (MEDAL_SILVER_ICON_PATH, "Booki"),
            (MEDAL_BRONZE_ICON_PATH, "Gillou"),
        ]

        for medal_path, placeholder_name in medal_defs:
            row = QWidget()
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(8)

            medal_label = QLabel()
            medal_label.setFixedSize(self._medal_icon_px, self._medal_icon_px)
            medal_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            medal_pix = load_svg_pixmap(medal_path, self._medal_icon_px)
            if not medal_pix.isNull():
                scaled = medal_pix.scaled(
                    self._medal_icon_px,
                    self._medal_icon_px,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                medal_label.setPixmap(scaled)
            row_lay.addWidget(medal_label)

            time_label = QLabel("-:--.---")
            time_font = QFont(FONT_FAMILY, FONT_SIZE_LAPTIME, QFont.Bold)
            time_label.setFont(time_font)
            time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            row_lay.addWidget(time_label)

            player_label = QLabel(placeholder_name)
            player_font = QFont(FONT_FAMILY, FONT_SIZE_RANKING_PLAYER)
            try:
                player_font.setWeight(resolve_font_weight(FONT_WEIGHT_RANKING_PLAYER))
            except Exception:
                pass
            player_label.setFont(player_font)
            player_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            player_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            row_lay.addWidget(player_label, 1)

            rr_lay.addWidget(row)
            self.absolute_rank_rows.append(
                {"medal": medal_label, "time": time_label, "player": player_label, "path": medal_path}
            )

        lay.addWidget(ranking_rows)
        lay.addStretch(1)

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour le temps de session affiché (format H:MM:SS).                                                    #
    #--------------------------------------------------------------------------------------------------------------#
    def set_session_time(self, seconds):
        if seconds is None:
            self.session_time_value.setText("-:--:--")
            return
        try:
            s = int(max(0, float(seconds)))
        except Exception:
            self.session_time_value.setText("-:--:--")
            return
        h = s // 3600
        m = (s % 3600) // 60
        sec = s % 60
        self.session_time_value.setText(f"{h}:{m:02d}:{sec:02d}")

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour le contexte affiché (circuit / voiture), avec le numéro d'ID si disponible.                      #
    #--------------------------------------------------------------------------------------------------------------#
    def set_context(self, track: str, car: str, track_id=None, car_id=None):
        track_text = track or "---"
        car_text = car or "---"
        display_track = track_text
        try:
            if track_text != "---" and track_id is not None:
                display_track = f"{track_text} - N° {int(track_id)}"
        except Exception:
            display_track = track_text
        display_car = car_text
        try:
            if car_text != "---" and car_id is not None:
                display_car = f"{car_text} - N° {int(car_id)}"
        except Exception:
            display_car = car_text
        self.track_value.setText(display_track)
        self.track_value.setToolTip(display_track)
        self.car_value.setText(display_car)
        self.car_value.setToolTip(display_car)

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour les 3 lignes du classement (complète à 3 entrées, formate les temps).                            #
    #--------------------------------------------------------------------------------------------------------------#
    def set_ranking(self, ranking: list):
        ranking = list(ranking)
        while len(ranking) < 3:
            ranking.append({"player": "", "time": 0.0})
        for i, row_data in enumerate(self.absolute_rank_rows[:3]):
            entry = ranking[i]
            player_name = entry.get("player", "")
            lap_time = entry.get("time", 0.0)
            if lap_time > 0:
                time_text = format_lap_time(lap_time)
            else:
                time_text = "-:--.---"
            row_data["time"].setText(time_text)
            row_data["player"].setText(player_name)

    #--------------------------------------------------------------------------------------------------------------#
    # Applique le thème courant (bouton-icône classements, séparateurs).                                          #
    #--------------------------------------------------------------------------------------------------------------#
    def apply_palette(self, c: dict):
        # Bouton-icône "classements"
        self.rankings_btn.setStyleSheet(icon_button_css(c))
        color = c.get("action_icon_color", c.get("control_fg", "#000000"))
        size = max(12, int(self._action_icon_px))
        list_icon = load_svg_icon(LIST_ICON_PATH, color, size)
        if list_icon.isNull():
            try:
                self.rankings_btn.setIcon(QIcon())
            except Exception:
                pass
        else:
            try:
                self.rankings_btn.setIcon(list_icon)
                self.rankings_btn.setIconSize(QSize(size, size))
            except Exception:
                pass

        # Séparateurs internes
        for sep in self.separators:
            try:
                sep.setStyleSheet(f"QFrame{{background:{c['separator']};}}")
            except Exception:
                pass
