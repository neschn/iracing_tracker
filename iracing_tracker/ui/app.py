import os
import sys,ctypes
from datetime import datetime
import queue as _q

from PySide6.QtCore import Qt, QTimer, QSize, QRectF
from PySide6.QtGui import QIcon, QFont, QTextOption, QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QPlainTextEdit, QTextEdit, QComboBox,
    QSizePolicy, QSpacerItem, QMenu
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QAction, QActionGroup

from .constants import (
    ICON_PATH, WINDOWS_ICON_PATH, EDIT_ICON_PATH, HIDE_ICON_PATH,
    WINDOW_TITLE, WINDOW_GEOMETRY, MIN_WIDTH, MIN_HEIGHT,
    WINDOW_BORDER_RADIUS, WINDOW_BORDER_WIDTH,
    FONT_FAMILY, FONT_SIZE_SECTION_TITLE, FONT_SIZE_BANNER, FONT_SIZE_LABELS,
    FONT_SIZE_PLAYER, FONT_SIZE_LAPTIME, FONT_SIZE_LAST_LAPTIMES, FONT_SIZE_DEBUG,
    FONT_SIZE_LOG, FONT_SIZE_BUTTON,
    BANNER_HEIGHT,
    SECTION_MARGIN, SECTION_TITLE_GAP, SECTION_SEPARATOR_SPACING,
    TIME_COL_PX,
    DEBUG_INITIAL_VISIBLE,
    TIRE_TEMP_PLACEHOLDER,
    BUTTON_BORDER_WIDTH, BUTTON_BORDER_RADIUS, BUTTON_PADDING, ICON_BUTTON_PADDING,
)
from .window import TrackerMainWindow
from .titlebar import CustomTitleBar
from .theme import ThemeManager
from .widgets import BoolVarCompat as _BoolVarCompat, hsep as _hsep, vsep as _vsep, make_tire_square as _make_tire_square

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
        self._tire_squares = []
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
        sc_lay = QVBoxLayout(self.session_col)
        sc_lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        sc_lay.setSpacing(6)

        sec_label = QLabel("SESSION")
        sec_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        sc_lay.addWidget(sec_label)
        sc_lay.addSpacing(SECTION_TITLE_GAP)

        self.session_time_label = QLabel("Temps de session : 1:23:45")
        self.session_time_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        self.track_label = QLabel("Circuit : ---")
        self.track_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        self.car_label = QLabel("Voiture : ---")
        self.car_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        sc_lay.addWidget(self.session_time_label)
        sc_lay.addWidget(self.track_label)
        sc_lay.addWidget(self.car_label)

        s = _hsep(self.session_col); self._seps.append(s)
        sc_lay.addSpacing(SECTION_SEPARATOR_SPACING); sc_lay.addWidget(s); sc_lay.addSpacing(SECTION_SEPARATOR_SPACING)

        abs_info = QLabel("Record absolu (détenu par ---) :")
        abs_info.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        self.absolute_record_value = QLabel("---")
        self.absolute_record_value.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAPTIME, QFont.Bold))
        self.absolute_record_value.setAlignment(Qt.AlignCenter)
        sc_lay.addWidget(abs_info)
        sc_lay.addWidget(self.absolute_record_value)

        s = _hsep(self.session_col); self._seps.append(s)
        sc_lay.addSpacing(SECTION_SEPARATOR_SPACING); sc_lay.addWidget(s); sc_lay.addSpacing(SECTION_SEPARATOR_SPACING)

        # Températures/usure pneus
        tires_grid = QWidget()
        tg_lay = QGridLayout(tires_grid)
        tg_lay.setContentsMargins(0, 0, 0, 0)
        tg_lay.setHorizontalSpacing(12)
        tg_lay.setVerticalSpacing(8)

        tires_title = QLabel("Température et usure des pneus :")
        tires_title.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        tg_lay.addWidget(tires_title, 0, 0, 1, 5)

        # Rangée 1
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq); tg_lay.addWidget(sq, 1, 0)
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq); tg_lay.addWidget(sq, 1, 1)
        tg_lay.addItem(QSpacerItem(24, 1, QSizePolicy.Fixed, QSizePolicy.Minimum), 1, 2)
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq); tg_lay.addWidget(sq, 1, 3)
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq); tg_lay.addWidget(sq, 1, 4)
        # Rangée 2
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq); tg_lay.addWidget(sq, 2, 0)
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq); tg_lay.addWidget(sq, 2, 1)
        tg_lay.addItem(QSpacerItem(24, 1, QSizePolicy.Fixed, QSizePolicy.Minimum), 2, 2)
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq); tg_lay.addWidget(sq, 2, 3)
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq); tg_lay.addWidget(sq, 2, 4)

        sc_lay.addWidget(tires_grid)
        sc_lay.addStretch(1)

        # Colonne joueur
        self.player_col = QWidget()
        pc_lay = QVBoxLayout(self.player_col)
        pc_lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        pc_lay.setSpacing(6)

        header_player = QWidget()
        hp_lay = QHBoxLayout(header_player)
        hp_lay.setContentsMargins(0, 0, 0, 0)
        title_player = QLabel("JOUEUR")
        title_player.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        hp_lay.addWidget(title_player)
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
        self.best_time_label = QLabel("---")
        self.best_time_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAPTIME, QFont.Bold))
        self.best_time_label.setAlignment(Qt.AlignCenter)
        pc_lay.addWidget(self.best_time_label)

        s = _hsep(self.player_col); self._seps.append(s)
        pc_lay.addSpacing(SECTION_SEPARATOR_SPACING); pc_lay.addWidget(s); pc_lay.addSpacing(SECTION_SEPARATOR_SPACING)

        lbl_last = QLabel("Dernier tour :")
        lbl_last.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        pc_lay.addWidget(lbl_last)
        self.current_lap_label = QLabel("---")
        self.current_lap_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAPTIME, QFont.Bold))
        self.current_lap_label.setAlignment(Qt.AlignCenter)
        pc_lay.addWidget(self.current_lap_label)
        pc_lay.addStretch(1)

        # Colonne derniers tours
        self.laps_col = QWidget()
        lc_lay = QVBoxLayout(self.laps_col)
        lc_lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        lc_lay.setSpacing(6)
        cap = QLabel("DERNIERS TOURS")
        cap.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        lc_lay.addWidget(cap)
        lc_lay.addSpacing(SECTION_TITLE_GAP)

        self.laps_text = QPlainTextEdit()
        self.laps_text.setReadOnly(True)
        self.laps_text.setFrameShape(QFrame.NoFrame)
        self.laps_text.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAST_LAPTIMES))
        self._populate_laps_placeholder()
        lc_lay.addWidget(self.laps_text, 1)

        # Colonne debug (masquable)
        self.debug_col = QWidget()
        dc_lay = QVBoxLayout(self.debug_col)
        dc_lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        dc_lay.setSpacing(6)
        header_dbg = QWidget()
        hd_lay = QHBoxLayout(header_dbg)
        hd_lay.setContentsMargins(0, 0, 0, 0)
        lbl_dbg = QLabel("DEBUG")
        lbl_dbg.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        hd_lay.addWidget(lbl_dbg)
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
        self._apply_debug_visibility(initial=True)

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
        self.track_label.setText(f"Circuit : {track}")
        self.car_label.setText(f"Voiture : {car}")

    def update_player_personal_record(self, best_time_str: str):
        self.best_time_label.setText(best_time_str or "---")

    def update_current_lap_time(self, text: str):
        self.current_lap_label.setText(text or "---")

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

    def update_players(self, players: list, current: str):
        self._players_list = list(players) if players else ["---"]
        self.player_combo.blockSignals(True)
        self.player_combo.clear()
        self.player_combo.addItems(self._players_list)
        if current and players and current in players:
            self.player_combo.setCurrentText(current)
        elif players:
            self.player_combo.setCurrentIndex(0)
        else:
            self.player_combo.setCurrentText("---")
        self.player_combo.blockSignals(False)

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

    def get_selected_player(self) -> str:
        return self.player_combo.currentText() or "---"

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
        text_scroll_css = self._scrollbar_css(
            "QTextEdit",
            scroll_track,
            scroll_border,
            handle_start,
            handle_end,
            handle_hover_start,
            handle_hover_end,
        )

        self.laps_text.setStyleSheet(f"QPlainTextEdit{{background:{c['bg_main']}; color:{c['text']};}}{plain_scroll_css}")
        self.debug_text.setStyleSheet(f"QPlainTextEdit{{background:{c['debug_bg']}; color:{c['text']};}}{plain_scroll_css}")
        self.log_text.setStyleSheet(f"QTextEdit{{background:{c['log_bg']}; color:{c['text']};}}{text_scroll_css}")

        for sep in self._seps:
            sep.setStyleSheet(f"QFrame{{background:{c['separator']};}}")

        self.set_player_menu_state(self.player_combo.isEnabled())

        for sq in self._tire_squares:
            sq.setStyleSheet(
                "QWidget{"
                f"background:{c['tire_bg']};"
                f"border:1px solid {c['tire_border']};"
                "border-radius:8px;"
                "}"
            )
            lab = sq.findChild(QLabel)
            if lab:
                lab.setStyleSheet(f"QLabel{{background:transparent; color:{c['tire_text']};}}")

    def _on_window_state_for_chrome(self, *args):
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

    def _apply_debug_visibility(self, initial: bool=False):
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
        self.laps_text.setPlainText("\n".join(lines))

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

