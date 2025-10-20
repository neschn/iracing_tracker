import os
import sys,ctypes
from datetime import datetime
import queue as _q

from PySide6.QtCore import Qt, QTimer, QSize, QRectF
from PySide6.QtGui import QIcon, QFont, QTextOption, QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QPlainTextEdit, QTextEdit, QComboBox,
    QSizePolicy, QMenu
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QAction, QActionGroup

from .constants import (
    WINDOWS_ICON_PATH, EDIT_ICON_PATH, HIDE_ICON_PATH, LIST_ICON_PATH,
    MEDAL_GOLD_ICON_PATH, MEDAL_SILVER_ICON_PATH, MEDAL_BRONZE_ICON_PATH,
    WINDOW_TITLE, WINDOW_GEOMETRY, MIN_WIDTH, MIN_HEIGHT,
    WINDOW_BORDER_RADIUS, WINDOW_BORDER_WIDTH,
    FONT_FAMILY, FONT_SIZE_SECTION_TITLE, FONT_SIZE_BANNER, FONT_SIZE_LABELS,
    FONT_SIZE_PLAYER, FONT_SIZE_LAPTIME, FONT_SIZE_DEBUG,
    FONT_SIZE_LOG, FONT_SIZE_BUTTON, FONT_SIZE_RANKING_PLAYER, FONT_WEIGHT_RANKING_PLAYER,
    BANNER_HEIGHT,
    SECTION_MARGIN, SECTION_TITLE_GAP, SECTION_SEPARATOR_SPACING,
    MEDAL_ICON_SIZE,
    DEBUG_INITIAL_VISIBLE,
    TIRE_TEMP_PLACEHOLDER,
    TIRE_WEAR_PLACEHOLDER,
    TIRE_ICON_PATH,
    TIRE_SECTION_HEADER_SPACING,
    BUTTON_BORDER_WIDTH, BUTTON_BORDER_RADIUS, BUTTON_PADDING, ICON_BUTTON_PADDING,
)
from .window import TrackerMainWindow
from .titlebar import CustomTitleBar
from .theme import ThemeManager
from .widgets import (
    BoolVarCompat as _BoolVarCompat,
    hsep as _hsep,
    vsep as _vsep,
    TireInfoWidget as _TireInfoWidget,
    LastLapsList as _LastLapsList,
)

# -------------------------------------------------------
# Pour que l'affichage de l'icone dans la barre des tâches fonctionne correctement
# -------------------------------------------------------
if os.name == "nt":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Nico.iRacingTracker")
    except Exception:
        pass


class TrackerUI:
    """
    Point d'entrée principal de l'UI.
    Conserve l'API publique d'origine.
    """

    def __init__(self, players: list, on_player_change, on_debug_toggle=None):
        # QApplication (unique) dans le thread UI
        self._app = QApplication.instance() or QApplication(sys.argv)

        # Fenêtre principale
        self._win = TrackerMainWindow()

        self._theme = ThemeManager(self._app)
        self._colors = None
        self._seps = []
        self._tire_widgets = []
        self._tires_map = {"temperature": {}, "wear": {}}
        self._action_icon_px = 18
        self._last_action_icon_color = None
        self._win.setWindowTitle(WINDOW_TITLE)
        self._win.resize(*WINDOW_GEOMETRY)
        self._win.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)

        # Compat .debug_visible.get()
        self.debug_visible = _BoolVarCompat(DEBUG_INITIAL_VISIBLE)

        # Callbacks externes
        self.on_player_change = on_player_change
        self.on_debug_toggle = on_debug_toggle

        # Widget central
        central = QWidget()
        self._central = central
        self._win.setCentralWidget(central)

        central.setObjectName("Root")
        if WINDOW_BORDER_RADIUS > 0:
            self._win.setAttribute(Qt.WA_TranslucentBackground, True)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._root_layout = root

        # ---- Barre de titre
        self._title_bar = CustomTitleBar(self._win)
        self._win.set_title_bar_widget(self._title_bar)
        self._win.window_state_changed.connect(self._title_bar.on_window_state_changed)
        self._win.window_state_changed.connect(self._on_window_state_for_chrome)
        root.addWidget(self._title_bar)
        self._title_bar.on_window_state_changed(self._win.windowState())

        self._sep_title = _hsep(central)
        self._seps.append(self._sep_title)
        root.addWidget(self._sep_title)

        self._apply_window_icon()

        # ---- Bannière
        banner = QWidget()
        self._banner = banner
        if BANNER_HEIGHT is not None:
            banner.setFixedHeight(BANNER_HEIGHT)
        banner_lay = QVBoxLayout(banner)
        banner_lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        self.banner_label = QLabel("")
        self.banner_label.setAlignment(Qt.AlignCenter)
        self.banner_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_BANNER, QFont.Bold))
        banner_lay.addWidget(self.banner_label)
        root.addWidget(banner)

        self._sep_banner = _hsep(central)
        self._seps.append(self._sep_banner)
        root.addWidget(self._sep_banner)

        # ---- Zone centrale (grid)
        center = QWidget()
        self.center_lay = QGridLayout(center)
        self.center_lay.setContentsMargins(0, 0, 0, 0)
        self.center_lay.setHorizontalSpacing(0)
        self.center_lay.setVerticalSpacing(8)

        # Colonne session
        self.session_col = QWidget()
        self.session_col.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sc_lay = QVBoxLayout(self.session_col)
        sc_lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        sc_lay.setSpacing(6)

        sec_label = QLabel("SESSION")
        sec_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        sc_lay.addWidget(sec_label)
        self._align_top(sc_lay, sec_label)
        sc_lay.addSpacing(SECTION_TITLE_GAP)


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
        self.track_value.setWordWrap(True)
        ir_lay.addWidget(self.track_value, 1, 1, Qt.AlignLeft | Qt.AlignVCenter)

        self.car_label = QLabel("Voiture :")
        self.car_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        ir_lay.addWidget(self.car_label, 2, 0, Qt.AlignLeft | Qt.AlignVCenter)

        self.car_value = QLabel("---")
        self.car_value.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        self.car_value.setWordWrap(True)
        ir_lay.addWidget(self.car_value, 2, 1, Qt.AlignLeft | Qt.AlignVCenter)

        ir_lay.setColumnStretch(0, 0)
        ir_lay.setColumnStretch(1, 1)
        sc_lay.addWidget(info_rows)

        s = _hsep(self.session_col); self._seps.append(s)
        sc_lay.addSpacing(SECTION_SEPARATOR_SPACING); sc_lay.addWidget(s); sc_lay.addSpacing(SECTION_SEPARATOR_SPACING)

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
        self.rankings_btn.setIconSize(QSize(self._action_icon_px, self._action_icon_px))
        self.rankings_btn.setToolTip("Afficher le classement complet")
        self.rankings_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        rh_lay.addWidget(self.rankings_btn)
        self._align_top(rh_lay, self.rankings_btn)
        sc_lay.addWidget(ranking_header)

        ranking_rows = QWidget()
        rr_lay = QVBoxLayout(ranking_rows)
        rr_lay.setContentsMargins(0, 0, 0, 0)
        rr_lay.setSpacing(4)
        self._medal_icon_px = MEDAL_ICON_SIZE
        medal_defs = [
            (MEDAL_GOLD_ICON_PATH, "Nico"),
            (MEDAL_SILVER_ICON_PATH, "Booki"),
            (MEDAL_BRONZE_ICON_PATH, "Gillou"),
        ]
        self.absolute_rank_rows = []
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
            player_font.setWeight(self._resolve_font_weight(FONT_WEIGHT_RANKING_PLAYER))
            player_label.setFont(player_font)
            player_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            player_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            row_lay.addWidget(player_label, 1)

            rr_lay.addWidget(row)
            self.absolute_rank_rows.append(
                {"medal": medal_label, "time": time_label, "player": player_label, "path": medal_path}
            )

        sc_lay.addWidget(ranking_rows)

        s = _hsep(self.session_col); self._seps.append(s)
        sc_lay.addSpacing(SECTION_SEPARATOR_SPACING); sc_lay.addWidget(s); sc_lay.addSpacing(SECTION_SEPARATOR_SPACING)

        # Températures/usure pneus
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

        temp_positions = [("AVG", 0, 0), ("AVD", 0, 1), ("ARG", 1, 0), ("ARD", 1, 1)]
        for code, row, col in temp_positions:
            widget = _TireInfoWidget(code, TIRE_TEMP_PLACEHOLDER, TIRE_ICON_PATH)
            temp_grid.addWidget(widget, row, col)
            self._tire_widgets.append(widget)
            self._tires_map["temperature"][code] = widget

        tc_lay.addWidget(temp_column, 1, Qt.AlignTop)

        sep_tires = _vsep(tires_content); self._seps.append(sep_tires)
        sep_tires.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        tc_lay.addWidget(sep_tires)

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

        wear_positions = [("AVG", 0, 0), ("AVD", 0, 1), ("ARG", 1, 0), ("ARD", 1, 1)]
        for code, row, col in wear_positions:
            widget = _TireInfoWidget(code, TIRE_WEAR_PLACEHOLDER, TIRE_ICON_PATH)
            wear_grid.addWidget(widget, row, col)
            self._tire_widgets.append(widget)
            self._tires_map["wear"][code] = widget

        tc_lay.addWidget(wear_column, 1, Qt.AlignTop)

        sc_lay.addWidget(tires_section, 1)

        # Colonne joueur
        self.player_col = QWidget()
        self.player_col.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        pc_lay = QVBoxLayout(self.player_col)
        pc_lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        pc_lay.setSpacing(6)

        header_player = QWidget()
        hp_lay = QHBoxLayout(header_player)
        hp_lay.setContentsMargins(0, 0, 0, 0)
        title_player = QLabel("JOUEUR")
        title_player.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        hp_lay.addWidget(title_player)
        self._align_top(hp_lay, title_player)
        hp_lay.addStretch(1)
        self.edit_players_btn = QPushButton("")
        self.edit_players_btn.setCursor(Qt.PointingHandCursor)
        self.edit_players_btn.setProperty("variant", "icon")
        self.edit_players_btn.setFixedSize(32, 32)
        self.edit_players_btn.setIconSize(QSize(self._action_icon_px, self._action_icon_px))
        self.edit_players_btn.setToolTip("Éditer la liste des joueurs")
        self.edit_players_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        self.edit_players_btn.setEnabled(False)  # placeholder inchangé
        hp_lay.addWidget(self.edit_players_btn)
        self._align_top(hp_lay, self.edit_players_btn)
        pc_lay.addWidget(header_player)
        pc_lay.addSpacing(SECTION_TITLE_GAP)

        self._players_list = list(players) if players else ["---"]
        self.player_combo = QComboBox()
        self.player_combo.setEditable(False)
        self.player_combo.addItems(self._players_list)
        self.player_combo.setCurrentIndex(0)
        self.player_combo.setStyleSheet(
            f"QComboBox{{font-family:{FONT_FAMILY}; font-size:{FONT_SIZE_PLAYER}pt;}}"
        )
        self.player_combo.currentTextChanged.connect(self._on_player_changed)
        pc_lay.addWidget(self.player_combo)

        s = _hsep(self.player_col); self._seps.append(s)
        pc_lay.addSpacing(SECTION_SEPARATOR_SPACING); pc_lay.addWidget(s); pc_lay.addSpacing(SECTION_SEPARATOR_SPACING)

        lbl_personal = QLabel("Record personnel :")
        lbl_personal.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        pc_lay.addWidget(lbl_personal)
        self.best_time_label = QLabel("-:--.---")
        self.best_time_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAPTIME, QFont.Bold))
        self.best_time_label.setAlignment(Qt.AlignCenter)
        pc_lay.addWidget(self.best_time_label)

        s = _hsep(self.player_col); self._seps.append(s)
        pc_lay.addSpacing(SECTION_SEPARATOR_SPACING); pc_lay.addWidget(s); pc_lay.addSpacing(SECTION_SEPARATOR_SPACING)

        lbl_last = QLabel("Dernier tour :")
        lbl_last.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        pc_lay.addWidget(lbl_last)
        self.current_lap_label = QLabel("-:--.---")
        self.current_lap_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAPTIME, QFont.Bold))
        self.current_lap_label.setAlignment(Qt.AlignCenter)
        pc_lay.addWidget(self.current_lap_label)
        pc_lay.addStretch(1)

        # Colonne derniers tours
        self.laps_col = QWidget()
        self.laps_col.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lc_lay = QVBoxLayout(self.laps_col)
        lc_lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        lc_lay.setSpacing(6)
        cap = QLabel("DERNIERS TOURS")
        cap.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        lc_lay.addWidget(cap)
        self._align_top(lc_lay, cap)
        lc_lay.addSpacing(SECTION_TITLE_GAP)

        self.laps_list = _LastLapsList()
        self._populate_laps_placeholder()
        lc_lay.addWidget(self.laps_list, 1)

        # Colonne debug (masquable)
        self.debug_col = QWidget()
        self.debug_col.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        dc_lay = QVBoxLayout(self.debug_col)
        dc_lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        dc_lay.setSpacing(6)
        header_dbg = QWidget()
        hd_lay = QHBoxLayout(header_dbg)
        hd_lay.setContentsMargins(0, 0, 0, 0)
        lbl_dbg = QLabel("DEBUG")
        lbl_dbg.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        hd_lay.addWidget(lbl_dbg)
        self._align_top(hd_lay, lbl_dbg)
        hd_lay.addStretch(1)
        self.debug_toggle_btn = QPushButton("")
        self.debug_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.debug_toggle_btn.setProperty("variant", "icon")
        self.debug_toggle_btn.setFixedSize(32, 32)
        self.debug_toggle_btn.setIconSize(QSize(self._action_icon_px, self._action_icon_px))
        self.debug_toggle_btn.setToolTip("Masquer la zone debug")
        self.debug_toggle_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        self.debug_toggle_btn.clicked.connect(lambda: self._set_debug_visible(False))
        hd_lay.addWidget(self.debug_toggle_btn)
        self._align_top(hd_lay, self.debug_toggle_btn)
        dc_lay.addWidget(header_dbg)
        dc_lay.addSpacing(SECTION_TITLE_GAP)

        self.debug_text = QPlainTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setFrameShape(QFrame.NoFrame)
        self.debug_text.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEBUG))
        self.debug_text.setWordWrapMode(QTextOption.WrapAnywhere)
        dc_lay.addWidget(self.debug_text, 1)

        # Placement grid (session | sep | joueur | sep | tours | sep | debug)
        self.center_lay.addWidget(self.session_col, 0, 0)
        self._sep_1 = _vsep(center); self._seps.append(self._sep_1)
        self.center_lay.addWidget(self._sep_1, 0, 1)
        self.center_lay.addWidget(self.player_col, 0, 2)
        self._sep_2 = _vsep(center); self._seps.append(self._sep_2)
        self.center_lay.addWidget(self._sep_2, 0, 3)
        self.center_lay.addWidget(self.laps_col, 0, 4)
        self._sep_debug = _vsep(center); self._seps.append(self._sep_debug)
        self.center_lay.addWidget(self._sep_debug, 0, 5)
        self.center_lay.addWidget(self.debug_col, 0, 6)

        for col in (0, 2, 4, 6):
            self.center_lay.setColumnStretch(col, 1)
        for col in (1, 3, 5):
            self.center_lay.setColumnStretch(col, 0)

        root.addWidget(center, 1)

        # ---- Logs
        self._sep_logs = _hsep(central); self._seps.append(self._sep_logs)
        root.addWidget(self._sep_logs)

        logs = QWidget()
        logs_lay = QVBoxLayout(logs)
        logs_lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        logs_lay.setSpacing(6)
        ltitle = QLabel("MESSAGES / LOGS")
        ltitle.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        logs_lay.addWidget(ltitle)
        self._align_top(logs_lay, ltitle)
        logs_lay.addSpacing(SECTION_TITLE_GAP)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFrameShape(QFrame.NoFrame)
        self.log_text.setFont(QFont(FONT_FAMILY, FONT_SIZE_LOG))
        logs_lay.addWidget(self.log_text)
        root.addWidget(logs, 0)

        # ---- Menu
        self._build_menubar()

        # Visibilité initiale Debug
        self._apply_debug_visibility()

        # Timer pour pomper la queue (≈ .after(16, ...))
        self._event_queue = None
        self._queue_timer = QTimer(self._win)
        self._queue_timer.setInterval(16)
        self._queue_timer.timeout.connect(self._pump_event_queue)

        # Appliquer le thème au démarrage
        self._apply_theme(self._theme.colors())

        # Suivi des changements de thème système (si supporté)
        try:
            self._app.styleHints().colorSchemeChanged.connect(self._on_system_color_scheme_changed)
        except Exception:
            pass

    # -------------------------
    # API publique (compat main.py)
    # -------------------------
    def mainloop(self):
        self._win.show()
        return self._app.exec()

    def set_on_player_change(self, cb):
        self.on_player_change = cb

    def set_on_debug_toggle(self, cb):
        self.on_debug_toggle = cb

    def bind_event_queue(self, q):
        self._event_queue = q
        self._queue_timer.start()

    def update_context(self, track: str, car: str):
        self.track_value.setText(track or "---")
        self.car_value.setText(car or "---")

    def update_player_personal_record(self, best_time_str: str):
        self.best_time_label.setText(best_time_str or "---")

    def update_current_lap_time(self, text: str):
        self.current_lap_label.setText(text or "---")

    def update_last_laps(self, entries):
        self.laps_list.set_items(entries)

    def update_debug(self, data: dict):
        sb = self.debug_text.verticalScrollBar()
        at_bottom = sb.value() >= (sb.maximum() - 4)
        lines = [f"{k}: {v}" for k, v in (data or {}).items()]
        self.debug_text.setPlainText("\n".join(lines))
        if at_bottom:
            sb.setValue(sb.maximum())

    def add_log(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {message}")

    @staticmethod
    def _align_top(layout, widget):
        if layout is None or widget is None:
            return
        try:
            layout.setAlignment(widget, Qt.AlignTop)
        except Exception:
            pass

    @staticmethod
    def _scrollbar_css(selector: str, track: str, border: str, handle_start: str, handle_end: str,
                       hover_start: str, hover_end: str) -> str:
        return (
            f"{selector} QScrollBar:vertical{{background:{track}; width:12px; margin:4px 2px; "
            f"border:1px solid {border}; border-radius:6px;}}"
            f"{selector} QScrollBar::groove:vertical{{border:none; margin:2px;}}"
            f"{selector} QScrollBar::handle:vertical{{background:qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            f"stop:0 {handle_start}, stop:1 {handle_end}); border:1px solid {border}; "
            f"border-radius:4px; min-height:18px; margin:1px;}}"
            f"{selector} QScrollBar::handle:vertical:hover{{background:qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            f"stop:0 {hover_start}, stop:1 {hover_end});}}"
            f"{selector} QScrollBar::add-line:vertical,{selector} QScrollBar::sub-line:vertical"
            f"{{height:0; width:0; background:none; border:none;}}"
            f"{selector} QScrollBar::add-page:vertical,{selector} QScrollBar::sub-page:vertical"
            f"{{background:transparent;}}"
        )

    def _apply_action_icons(self, color: str):
        target_color = color or "#000000"
        if target_color == self._last_action_icon_color:
            return
        size = max(12, int(self._action_icon_px))
        icon_size = QSize(size, size)

        edit_icon = self._load_svg_icon(EDIT_ICON_PATH, target_color, size)
        if edit_icon.isNull():
            self.edit_players_btn.setIcon(QIcon())
        else:
            self.edit_players_btn.setIcon(edit_icon)
        self.edit_players_btn.setIconSize(icon_size)

        list_icon = self._load_svg_icon(LIST_ICON_PATH, target_color, size)
        if hasattr(self, "rankings_btn"):
            if list_icon.isNull():
                self.rankings_btn.setIcon(QIcon())
            else:
                self.rankings_btn.setIcon(list_icon)
            self.rankings_btn.setIconSize(icon_size)

        hide_icon = self._load_svg_icon(HIDE_ICON_PATH, target_color, size)
        if hide_icon.isNull():
            self.debug_toggle_btn.setIcon(QIcon())
        else:
            self.debug_toggle_btn.setIcon(hide_icon)
        self.debug_toggle_btn.setIconSize(icon_size)

        self._last_action_icon_color = target_color

    @staticmethod
    def _load_svg_icon(path: str, color: str, size: int) -> QIcon:
        if not path or not os.path.isfile(path):
            return QIcon()
        try:
            renderer = QSvgRenderer(path)
            if not renderer.isValid():
                return QIcon()
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            renderer.render(painter, QRectF(0, 0, size, size))
            painter.end()

            fg = QColor(color)
            if not fg.isValid():
                fg = QColor("#000000")
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), fg)
            painter.end()
            return QIcon(pixmap)
        except Exception:
            return QIcon()

    @staticmethod
    def _load_svg_pixmap(path: str, size: int) -> QPixmap:
        if not path or not os.path.isfile(path):
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

    def set_player_menu_state(self, enabled: bool):
        en = bool(enabled)
        self.player_combo.setEnabled(en)
        colors = getattr(self, "_colors", None)
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
            scroll_css = self._scrollbar_css(
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
            scroll_css = self._scrollbar_css(
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

    def set_banner(self, text: str = ""):
        self.banner_label.setText(text or "")

    # -------------------------
    # Interne (UI)
    # -------------------------
    def _on_player_changed(self, name: str):
        if callable(self.on_player_change):
            try:
                self.on_player_change(name)
            except Exception:
                pass

    def _build_menubar(self):
        menubar = self._title_bar.menu_bar()
        menubar.clear()

        file_menu = QMenu("Fichier", menubar)
        file_menu.addAction(QAction("(à venir)", file_menu, enabled=False))
        menubar.addMenu(file_menu)

        edit_menu = QMenu("Édition", menubar)
        edit_menu.addAction(QAction("(à venir)", edit_menu, enabled=False))
        menubar.addMenu(edit_menu)

        view_menu = QMenu("Affichage", menubar)
        # Debug toggle
        self._act_debug = QAction("Debug", view_menu, checkable=True)
        self._act_debug.setChecked(self.debug_visible.get())
        self._act_debug.triggered.connect(self._toggle_debug_action)
        view_menu.addAction(self._act_debug)

        # Thème
        theme_menu = QMenu("Thème", menubar)
        group = QActionGroup(self._win)
        group.setExclusive(True)

        self._act_theme_system = QAction("Système", group, checkable=True)
        self._act_theme_light  = QAction("Clair",   group, checkable=True)
        self._act_theme_dark   = QAction("Sombre",  group, checkable=True)

        mode = self._theme.get_mode()
        self._act_theme_system.setChecked(mode == "system")
        self._act_theme_light.setChecked(mode == "light")
        self._act_theme_dark.setChecked(mode == "dark")

        self._act_theme_system.triggered.connect(lambda: self._on_theme_changed("system"))
        self._act_theme_light.triggered.connect(lambda: self._on_theme_changed("light"))
        self._act_theme_dark.triggered.connect(lambda: self._on_theme_changed("dark"))

        theme_menu.addAction(self._act_theme_system)
        theme_menu.addAction(self._act_theme_light)
        theme_menu.addAction(self._act_theme_dark)
        view_menu.addMenu(theme_menu)

        menubar.addMenu(view_menu)

    def _on_theme_changed(self, mode: str):
        self._theme.set_mode(mode)
        self._apply_theme(self._theme.colors())

    def _apply_theme(self, c: dict):
        self._colors = c
        self._title_bar.apply_colors(c)

        r  = 0 if self._win.isMaximized() else WINDOW_BORDER_RADIUS
        bw = WINDOW_BORDER_WIDTH if r > 0 else 0

        self._central.setStyleSheet(
            "QWidget{"
            f"background:{c['bg_main']};"
            f"color:{c['text']};"
            "}"
            "QWidget#Root{"
            f"border:{bw}px solid {c['window_border']};"
            f"border-radius:{r}px;"
            "}"
        )
        try:
            if hasattr(self, "_root_layout") and self._root_layout is not None:
                self._root_layout.setContentsMargins(bw, bw, bw, bw)
        except Exception:
            pass

        self._banner.setStyleSheet(f"QWidget{{background:{c['banner_bg']};}}")
        self.banner_label.setStyleSheet(f"QLabel{{color:{c['banner_text']};}}")

        btn_ss = (
            "QPushButton{"
            f"background:{c['button_bg']};"
            f"color:{c['control_fg']};"
            f"border:{BUTTON_BORDER_WIDTH}px solid {c['button_border_color']};"
            f"border-radius:{BUTTON_BORDER_RADIUS}px;"
            f"padding:{BUTTON_PADDING};"
            "}"
            "QPushButton:hover{"
            f"background:{c['interactive_hover']};"
            "}"
            "QPushButton:pressed{"
            f"background:{c['interactive_hover']};"
            "}"
            "QPushButton:disabled{"
            f"background:{c['button_bg']};"
            "color:#888888;"
            "}"
        )
        icon_override = (
            "QPushButton[variant=\"icon\"]{"
            f"padding:{ICON_BUTTON_PADDING};"
            "min-width:28px;"
            "min-height:28px;"
            "}"
        )
        icon_btn_ss = btn_ss + icon_override
        self.edit_players_btn.setStyleSheet(icon_btn_ss)
        if hasattr(self, "rankings_btn"):
            self.rankings_btn.setStyleSheet(icon_btn_ss)
        self.debug_toggle_btn.setStyleSheet(icon_btn_ss)
        self._apply_action_icons(c.get("action_icon_color", c.get("control_fg", "#000000")))

        scroll_track = c.get("scrollbar_track", c.get("bg_secondary", "#f0f0f0"))
        scroll_border = c.get("scrollbar_border", c.get("separator", "#b0b0b0"))
        handle_start = c.get("scrollbar_handle_start", c.get("separator", "#b0b0b0"))
        handle_end = c.get("scrollbar_handle_end", c.get("control_fg", "#7d7d7d"))
        handle_hover_start = c.get("scrollbar_handle_hover_start", c.get("control_fg", "#7d7d7d"))
        handle_hover_end = c.get("scrollbar_handle_hover_end", c.get("text", "#3a3a3a"))
        plain_scroll_css = self._scrollbar_css(
            "QPlainTextEdit",
            scroll_track,
            scroll_border,
            handle_start,
            handle_end,
            handle_hover_start,
            handle_hover_end,
        )
        list_scroll_css = self._scrollbar_css(
            "QListWidget",
            scroll_track,
            scroll_border,
            handle_start,
            handle_end,
            handle_hover_start,
            handle_hover_end,
        )
        text_scroll_css = self._scrollbar_css(
            "QTextEdit",
            scroll_track,
            scroll_border,
            handle_start,
            handle_end,
            handle_hover_start,
            handle_hover_end,
        )

        hover_color = c.get('last_laps_hover', c.get('interactive_hover'))
        self.laps_list.apply_palette(c['text'], c['bg_main'], hover_color, list_scroll_css)
        self.debug_text.setStyleSheet(f"QPlainTextEdit{{background:{c['debug_bg']}; color:{c['text']};}}{plain_scroll_css}")
        self.log_text.setStyleSheet(f"QTextEdit{{background:{c['log_bg']}; color:{c['text']};}}{text_scroll_css}")

        for sep in self._seps:
            sep.setStyleSheet(f"QFrame{{background:{c['separator']};}}")

        self.set_player_menu_state(self.player_combo.isEnabled())

        for tire_widget in self._tire_widgets:
            tire_widget.apply_palette(c['tire_bg'], c['tire_border'], c['tire_text'])

    def _on_window_state_for_chrome(self, *_):
        self._apply_theme(self._colors or self._theme.colors())

    def _on_system_color_scheme_changed(self):
        if self._theme.get_mode() == "system":
            self._apply_theme(self._theme.colors())

    def _toggle_debug_action(self, checked: bool):
        self.debug_visible.set(bool(checked))
        self._apply_debug_visibility()
        if callable(self.on_debug_toggle):
            try:
                self.on_debug_toggle(bool(checked))
            except Exception:
                pass

    def _set_debug_visible(self, flag: bool):
        self.debug_visible.set(bool(flag))
        self._act_debug.blockSignals(True)
        self._act_debug.setChecked(self.debug_visible.get())
        self._act_debug.blockSignals(False)
        self._apply_debug_visibility()
        if callable(self.on_debug_toggle):
            try:
                self.on_debug_toggle(self.debug_visible.get())
            except Exception:
                pass

    def _apply_debug_visibility(self):
        vis = self.debug_visible.get()
        self.debug_col.setVisible(vis)
        self._sep_debug.setVisible(vis)
        self.debug_toggle_btn.setToolTip("Masquer la zone debug" if vis else "Afficher la zone debug")

        if vis:
            for col in (0, 2, 4, 6):
                self.center_lay.setColumnStretch(col, 1)
        else:
            for col in (0, 2, 4):
                self.center_lay.setColumnStretch(col, 1)
            self.center_lay.setColumnStretch(6, 0)

    def _pump_event_queue(self):
        if self._event_queue is None:
            return
        try:
            while True:
                name, payload = self._event_queue.get_nowait()
                payload = payload or {}
                if name == "debug":
                    self.update_debug(payload)
                elif name == "context":
                    self.update_context(payload.get("track", "---"), payload.get("car", "---"))
                elif name == "player_menu_state":
                    self.set_player_menu_state(payload.get("enabled", False))
                elif name == "log":
                    self.add_log(payload.get("message", ""))
                elif name == "player_best":
                    self.update_player_personal_record(payload.get("text", "---"))
                elif name == "current_lap":
                    self.update_current_lap_time(payload.get("text", "---"))
                elif name == "last_laps":
                    entries = payload.get("entries")
                    if entries is None:
                        entries = payload.get("lines")
                    if entries is None:
                        entries = payload.get("text")
                    self.update_last_laps(entries or [])
                elif name == "banner":
                    self.set_banner(payload.get("text", ""))
        except _q.Empty:
            pass
        except Exception as e:
            try:
                self.add_log(f"UI error: {e}")
            except Exception:
                pass

    def _populate_laps_placeholder(self):
        lines = [
            "0:34.678\tNico",
            "0:36.878\tNico",
            "0:35.679\tNico",
            "0:34.678\tBooki",
            "0:36.878\tNico",
            "0:35.679\tJacques",
            "0:34.678\tNico",
            "0:34.132\tNico",
            "0:34.678\tNico",
        ]
        self.laps_list.set_items(lines)

    def _apply_window_icon(self):
        try:
            if os.path.isfile(WINDOWS_ICON_PATH):
                icon = QIcon(WINDOWS_ICON_PATH)
                self._app.setWindowIcon(icon)      # icône au niveau process
                self._win.setWindowIcon(icon)      # icône de la fenêtre
                if hasattr(self, "_title_bar"):
                    self._title_bar.set_icon(icon) # icône barre de titre custom
        except Exception:
            pass

