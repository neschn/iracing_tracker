################################################################################################################
# Projet : iRacing Tracker
# Fichier : iracing_tracker/ui/session_panel.py
# Description : Panneau "SESSION" (infos session, top 3, pneus)
################################################################################################################

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QFont, QPixmap, QPainter
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QSizePolicy,
)
from PySide6.QtSvg import QSvgRenderer

from .constants import (
    FONT_FAMILY,
    FONT_SIZE_SECTION_TITLE,
    FONT_SIZE_LABELS,
    FONT_SIZE_LAPTIME,
    FONT_SIZE_RANKING_PLAYER,
    FONT_WEIGHT_RANKING_PLAYER,
    SECTION_MARGIN,
    SECTION_TITLE_GAP,
    SECTION_SEPARATOR_SPACING,
    MEDAL_GOLD_ICON_PATH,
    MEDAL_SILVER_ICON_PATH,
    MEDAL_BRONZE_ICON_PATH,
    MEDAL_ICON_SIZE,
    TIRE_SECTION_HEADER_SPACING,
    TIRE_TEMP_PLACEHOLDER,
    TIRE_WEAR_PLACEHOLDER,
    TIRE_ICON_PATH,
)
from .widgets import hsep as _hsep, vsep as _vsep, TireInfoWidget as _TireInfoWidget


class SessionPanel(QWidget):
    """Colonne gauche: SESSION + Top3 + Pneus."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.separators = []
        self.tire_widgets = []
        self.tires_map = {"temperature": {}, "wear": {}}
        self.absolute_rank_rows = []
        self._medal_icon_px = MEDAL_ICON_SIZE

        lay = QVBoxLayout(self)
        lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        lay.setSpacing(6)

        # Titre
        title = QLabel("SESSION")
        title.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        lay.addWidget(title)
        self._align_top(lay, title)
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
        self._align_top(rh_lay, self.absolute_ranking_label)
        rh_lay.addStretch(1)
        self.rankings_btn = QPushButton("")
        self.rankings_btn.setCursor(Qt.PointingHandCursor)
        self.rankings_btn.setProperty("variant", "icon")
        self.rankings_btn.setFixedSize(32, 32)
        # Icon is applied by app via theme
        rh_lay.addWidget(self.rankings_btn)
        self._align_top(rh_lay, self.rankings_btn)
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
            medal_pix = self._load_svg_pixmap(medal_path, self._medal_icon_px)
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
                player_font.setWeight(self._resolve_font_weight(FONT_WEIGHT_RANKING_PLAYER))
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

        s = _hsep(self); self.separators.append(s)
        lay.addSpacing(SECTION_SEPARATOR_SPACING); lay.addWidget(s); lay.addSpacing(SECTION_SEPARATOR_SPACING)

        # Pneus
        tires_section = QWidget()
        tires_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tires_layout = QVBoxLayout(tires_section)
        tires_layout.setContentsMargins(0, 0, 0, 0)
        tires_layout.setSpacing(12)

        tires_title = QLabel("Pneus")
        tires_title.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        tires_title.setAlignment(Qt.AlignCenter)
        tires_layout.addWidget(tires_title)
        self._align_top(tires_layout, tires_title)

        tires_content = QWidget()
        tc_lay = QHBoxLayout(tires_content)
        tc_lay.setContentsMargins(0, 0, 0, 0)
        tc_lay.setSpacing(24)
        tires_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tires_layout.addWidget(tires_content, 1)

        # Températures
        temp_column = QWidget()
        temp_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        temp_col_lay = QVBoxLayout(temp_column)
        temp_col_lay.setContentsMargins(0, 0, 0, 0)
        temp_col_lay.setSpacing(12)

        temp_label = QLabel("Températures :")
        temp_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        temp_label.setAlignment(Qt.AlignCenter)
        temp_col_lay.addWidget(temp_label)
        self._align_top(temp_col_lay, temp_label)
        temp_col_lay.addSpacing(TIRE_SECTION_HEADER_SPACING)

        temp_grid = QGridLayout()
        temp_grid.setContentsMargins(0, 0, 0, 0)
        temp_grid.setHorizontalSpacing(24)
        temp_grid.setVerticalSpacing(12)
        temp_col_lay.addLayout(temp_grid, 1)

        temp_grid.setColumnStretch(0, 1)
        temp_grid.setColumnStretch(1, 1)
        temp_grid.setRowStretch(0, 1)
        temp_grid.setRowStretch(1, 1)

        for code, row, col in [("AVG", 0, 0), ("AVD", 0, 1), ("ARG", 1, 0), ("ARD", 1, 1)]:
            widget = _TireInfoWidget(code, TIRE_TEMP_PLACEHOLDER, TIRE_ICON_PATH)
            temp_grid.addWidget(widget, row, col)
            self.tire_widgets.append(widget)
            self.tires_map["temperature"][code] = widget

        tc_lay.addWidget(temp_column, 1, Qt.AlignTop)

        sep_tires = _vsep(tires_content)
        self.separators.append(sep_tires)
        sep_tires.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        tc_lay.addWidget(sep_tires)

        # Usure/Profil
        wear_column = QWidget()
        wear_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        wear_col_lay = QVBoxLayout(wear_column)
        wear_col_lay.setContentsMargins(0, 0, 0, 0)
        wear_col_lay.setSpacing(12)

        wear_label = QLabel("Profil :")
        wear_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        wear_label.setAlignment(Qt.AlignCenter)
        wear_col_lay.addWidget(wear_label)
        self._align_top(wear_col_lay, wear_label)
        wear_col_lay.addSpacing(TIRE_SECTION_HEADER_SPACING)

        wear_grid = QGridLayout()
        wear_grid.setContentsMargins(0, 0, 0, 0)
        wear_grid.setHorizontalSpacing(24)
        wear_grid.setVerticalSpacing(12)
        wear_col_lay.addLayout(wear_grid, 1)

        wear_grid.setColumnStretch(0, 1)
        wear_grid.setColumnStretch(1, 1)
        wear_grid.setRowStretch(0, 1)
        wear_grid.setRowStretch(1, 1)

        for code, row, col in [("AVG", 0, 0), ("AVD", 0, 1), ("ARG", 1, 0), ("ARD", 1, 1)]:
            widget = _TireInfoWidget(code, TIRE_WEAR_PLACEHOLDER, TIRE_ICON_PATH)
            wear_grid.addWidget(widget, row, col)
            self.tire_widgets.append(widget)
            self.tires_map["wear"][code] = widget

        tc_lay.addWidget(wear_column, 1, Qt.AlignTop)

        lay.addWidget(tires_section, 1)

    @staticmethod
    def _align_top(layout, widget):
        if layout is None or widget is None:
            return
        try:
            layout.setAlignment(widget, Qt.AlignTop)
        except Exception:
            pass

    @staticmethod
    def _load_svg_pixmap(path: str, size: int) -> QPixmap:
        if not path:
            return QPixmap()
        try:
            renderer = QSvgRenderer(path)
            if not renderer.isValid():
                return QPixmap()
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            view_box = renderer.viewBoxF()
            if not view_box.isValid() or view_box.isEmpty():
                view_box = QRectF(0, 0, size, size)
            max_dim = max(view_box.width(), view_box.height(), 1.0)
            scale = size / max_dim
            target_w = view_box.width() * scale
            target_h = view_box.height() * scale
            target_x = (size - target_w) / 2.0
            target_y = (size - target_h) / 2.0
            target_rect = QRectF(target_x, target_y, target_w, target_h)
            renderer.render(painter, target_rect)
            painter.end()
            return pixmap
        except Exception:
            return QPixmap()

    @staticmethod
    def _resolve_font_weight(weight) -> QFont.Weight:
        mapping = {
            "thin": QFont.Weight.Thin,
            "extralight": QFont.Weight.ExtraLight,
            "ultralight": QFont.Weight.ExtraLight,
            "light": QFont.Weight.Light,
            "normal": QFont.Weight.Normal,
            "regular": QFont.Weight.Normal,
            "medium": QFont.Weight.Medium,
            "semibold": QFont.Weight.DemiBold,
            "demibold": QFont.Weight.DemiBold,
            "bold": QFont.Weight.Bold,
            "extrabold": QFont.Weight.ExtraBold,
            "black": QFont.Weight.Black,
        }
        if isinstance(weight, str):
            key = weight.strip().lower()
            if key in mapping:
                return mapping[key]
        try:
            value = int(weight)
            candidates = [
                QFont.Weight.Thin,
                QFont.Weight.ExtraLight,
                QFont.Weight.Light,
                QFont.Weight.Normal,
                QFont.Weight.Medium,
                QFont.Weight.DemiBold,
                QFont.Weight.Bold,
                QFont.Weight.ExtraBold,
                QFont.Weight.Black,
            ]
            return min(candidates, key=lambda enum: abs(enum.value - value))
        except Exception:
            return QFont.Weight.Normal
