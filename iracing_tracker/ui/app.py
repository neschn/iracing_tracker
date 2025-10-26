################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui/app.py                                                                          #
# Description : Construit l'interface PySide6 complète du tracker, refactorisée en panneaux.                   #
################################################################################################################

import os
import sys, ctypes
from datetime import datetime
import queue as _q

from PySide6.QtCore import Qt, QTimer, QSize, QRectF
from PySide6.QtGui import QIcon, QFont, QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QGridLayout, QMenu
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QAction, QActionGroup

from .constants import (
    WINDOWS_ICON_PATH, EDIT_ICON_PATH, HIDE_ICON_PATH, LIST_ICON_PATH,
    WINDOW_TITLE, WINDOW_GEOMETRY, MIN_WIDTH, MIN_HEIGHT,
    WINDOW_BORDER_RADIUS, WINDOW_BORDER_WIDTH,
    FONT_FAMILY, FONT_SIZE_BANNER, FONT_SIZE_PLAYER,
    BANNER_HEIGHT,
    SECTION_MARGIN,
    BUTTON_BORDER_WIDTH, BUTTON_BORDER_RADIUS, BUTTON_PADDING, ICON_BUTTON_PADDING,
)
from .window import TrackerMainWindow
from .titlebar import CustomTitleBar
from .theme import ThemeManager
from .banner_manager import BannerManager, BannerMessageType
from .widgets import (
    BoolVarCompat as _BoolVarCompat,
    hsep as _hsep,
    vsep as _vsep,
)

from .session_panel import SessionPanel
from .player_panel import PlayerPanel
from .last_laps_panel import LastLapsPanel
from .debug_panel import DebugPanel
from .logs_panel import LogsPanel


if os.name == "nt":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Nico.iRacingTracker")
    except Exception:
        pass


class TrackerUI:
    """Entrée principale de l'UI (API inchangée)."""

    def __init__(self, players: list, on_player_change, on_debug_toggle=None):
        # Instances et état de base
        self._app = QApplication.instance() or QApplication(sys.argv)
        self._win = TrackerMainWindow()
        self._win.setWindowTitle(WINDOW_TITLE)
        self._win.resize(*WINDOW_GEOMETRY)
        self._win.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)

        self._theme = ThemeManager(self._app)
        self._colors = None
        self._seps = []
        self._tire_widgets = []
        self._tires_map = {"temperature": {}, "wear": {}}
        self._action_icon_px = 18
        self._last_action_icon_color = None
        self.debug_visible = _BoolVarCompat(True)

        self.on_player_change = on_player_change
        self.on_debug_toggle = on_debug_toggle

        # Root
        central = QWidget(); self._central = central
        self._win.setCentralWidget(central)
        central.setObjectName("Root")
        if WINDOW_BORDER_RADIUS > 0:
            self._win.setAttribute(Qt.WA_TranslucentBackground, True)
        root = QVBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self._root_layout = root

        # Barre de titre + séparateur
        self._title_bar = CustomTitleBar(self._win)
        self._win.set_title_bar_widget(self._title_bar)
        self._win.window_state_changed.connect(self._title_bar.on_window_state_changed)
        self._win.window_state_changed.connect(self._on_window_state_for_chrome)
        root.addWidget(self._title_bar)
        self._title_bar.on_window_state_changed(self._win.windowState())
        self._sep_title = _hsep(central); self._seps.append(self._sep_title); root.addWidget(self._sep_title)
        self._apply_window_icon()

        # Bannière + séparateur
        banner = QWidget(); self._banner = banner
        if BANNER_HEIGHT is not None: banner.setFixedHeight(BANNER_HEIGHT)
        b_lay = QVBoxLayout(banner); b_lay.setContentsMargins(SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN, SECTION_MARGIN)
        self.banner_label = QLabel(""); self.banner_label.setAlignment(Qt.AlignCenter)
        self.banner_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_BANNER, QFont.Bold))
        b_lay.addWidget(self.banner_label); root.addWidget(banner)
        self._banner_manager = None
        self._sep_banner = _hsep(central); self._seps.append(self._sep_banner); root.addWidget(self._sep_banner)

        # Zone centrale (panneaux)
        center = QWidget(); self.center_lay = QGridLayout(center)
        self.center_lay.setContentsMargins(0,0,0,0); self.center_lay.setHorizontalSpacing(0); self.center_lay.setVerticalSpacing(8)

        self.session_panel = SessionPanel(center)
        self.player_panel = PlayerPanel(players, self._on_player_changed, action_icon_px=self._action_icon_px, parent=center)
        self.last_laps_panel = LastLapsPanel(center)
        self.debug_panel = DebugPanel(self._set_debug_visible, action_icon_px=self._action_icon_px, parent=center)

        self.center_lay.addWidget(self.session_panel, 0, 0)
        self._sep_1 = _vsep(center); self._seps.append(self._sep_1); self.center_lay.addWidget(self._sep_1, 0, 1)
        self.center_lay.addWidget(self.player_panel, 0, 2)
        self._sep_2 = _vsep(center); self._seps.append(self._sep_2); self.center_lay.addWidget(self._sep_2, 0, 3)
        self.center_lay.addWidget(self.last_laps_panel, 0, 4)
        self._sep_debug = _vsep(center); self._seps.append(self._sep_debug); self.center_lay.addWidget(self._sep_debug, 0, 5)
        self.center_lay.addWidget(self.debug_panel, 0, 6)
        for col in (0,2,4,6): self.center_lay.setColumnStretch(col, 1)
        for col in (1,3,5): self.center_lay.setColumnStretch(col, 0)

        # Back-compat: références directes
        self.session_time_value = self.session_panel.session_time_value
        self.track_value = self.session_panel.track_value
        self.car_value = self.session_panel.car_value
        self.absolute_rank_rows = self.session_panel.absolute_rank_rows
        self.rankings_btn = self.session_panel.rankings_btn
        self._tire_widgets = list(self.session_panel.tire_widgets)
        self._tires_map = self.session_panel.tires_map
        self.edit_players_btn = self.player_panel.edit_players_btn
        self.player_combo = self.player_panel.player_combo
        self.best_time_label = self.player_panel.best_time_label
        self.current_lap_label = self.player_panel.current_lap_label
        self.laps_list = self.last_laps_panel.laps_list
        self.debug_toggle_btn = self.debug_panel.debug_toggle_btn
        self.debug_text = self.debug_panel.debug_text
        self.debug_col = self.debug_panel
        for s in getattr(self.session_panel,'separators',[]): self._seps.append(s)
        for s in getattr(self.player_panel,'separators',[]): self._seps.append(s)
        for s in getattr(self.debug_panel,'separators',[]): self._seps.append(s)
        root.addWidget(center, 1)

        # Logs
        self._sep_logs = _hsep(central); self._seps.append(self._sep_logs); root.addWidget(self._sep_logs)
        self.logs_panel = LogsPanel(central); self.log_text = self.logs_panel.log_text; root.addWidget(self.logs_panel, 0)

        # Menu + thème + timers
        self._build_menubar()
        self._apply_debug_visibility()
        self._event_queue = None
        self._queue_timer = QTimer(self._win); self._queue_timer.setInterval(16); self._queue_timer.timeout.connect(self._pump_event_queue)
        self._apply_theme(self._theme.colors())
        try: self._app.styleHints().colorSchemeChanged.connect(self._on_system_color_scheme_changed)
        except Exception: pass
        self._populate_laps_placeholder()

    # API publique (compat)
    def mainloop(self):
        self._win.show(); return self._app.exec()

    def set_on_player_change(self, cb): self.on_player_change = cb
    def set_on_debug_toggle(self, cb): self.on_debug_toggle = cb
    def bind_event_queue(self, q): self._event_queue = q; self._queue_timer.start()

    # --- Méthodes d'update ---
    def update_context(self, track: str, car: str, track_id=None):
        track_text = track or "---"; car_text = car or "---"
        display_track = track_text
        try:
            if track_text != "---" and track_id is not None:
                display_track = f"{track_text} - N° {int(track_id)}"
        except Exception:
            display_track = track_text
        self.track_value.setText(display_track); self.track_value.setToolTip(display_track)
        self.car_value.setText(car_text); self.car_value.setToolTip(car_text)

    def update_player_personal_record(self, best_time_str: str):
        self.best_time_label.setText(best_time_str or "---")

    def _update_ranking_display(self, ranking: list):
        while len(ranking) < 3:
            ranking.append({"player": "", "time": 0.0})
        for i, row_data in enumerate(self.absolute_rank_rows[:3]):
            entry = ranking[i]
            player_name = entry.get("player", "")
            lap_time = entry.get("time", 0.0)
            if lap_time > 0:
                from iracing_tracker.record_manager import format_lap_time
                time_text = format_lap_time(lap_time)
            else:
                time_text = "-:--.---"
            row_data["time"].setText(time_text)
            row_data["player"].setText(player_name)

    def _handle_banner_message(self, message_type: str):
        if not hasattr(self, "_banner_manager") or not self._banner_manager:
            return
        type_map = {
            "waiting": BannerMessageType.WAITING_SESSION,
            "personal_record": BannerMessageType.PERSONAL_RECORD,
            "absolute_record": BannerMessageType.ABSOLUTE_RECORD,
            "clear": BannerMessageType.NONE,
        }
        banner_type = type_map.get(message_type, BannerMessageType.NONE)
        self._banner_manager.show_message(banner_type)

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
        if list_icon.isNull():
            try:
                self.rankings_btn.setIcon(QIcon())
            except Exception:
                pass
        else:
            try:
                self.rankings_btn.setIcon(list_icon)
                self.rankings_btn.setIconSize(icon_size)
            except Exception:
                pass

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

    def _on_player_changed(self, name: str):
        if callable(self.on_player_change):
            try:
                self.on_player_change(name)
            except Exception:
                pass

    def _build_menubar(self):
        menubar = self._title_bar.menu_bar(); menubar.clear()
        file_menu = QMenu("Fichier", menubar); file_menu.addAction(QAction("(à venir)", file_menu, enabled=False)); menubar.addMenu(file_menu)
        edit_menu = QMenu("Édition", menubar); edit_menu.addAction(QAction("(à venir)", edit_menu, enabled=False)); menubar.addMenu(edit_menu)
        view_menu = QMenu("Affichage", menubar)
        self._act_debug = QAction("Debug", view_menu, checkable=True); self._act_debug.setChecked(self.debug_visible.get()); self._act_debug.triggered.connect(self._toggle_debug_action); view_menu.addAction(self._act_debug)
        theme_menu = QMenu("Thème", menubar); group = QActionGroup(self._win); group.setExclusive(True)
        self._act_theme_system = QAction("Système", group, checkable=True); self._act_theme_light = QAction("Clair", group, checkable=True); self._act_theme_dark = QAction("Sombre", group, checkable=True)
        mode = self._theme.get_mode(); self._act_theme_system.setChecked(mode=="system"); self._act_theme_light.setChecked(mode=="light"); self._act_theme_dark.setChecked(mode=="dark")
        self._act_theme_system.triggered.connect(lambda: self._on_theme_changed("system")); self._act_theme_light.triggered.connect(lambda: self._on_theme_changed("light")); self._act_theme_dark.triggered.connect(lambda: self._on_theme_changed("dark"))
        theme_menu.addAction(self._act_theme_system); theme_menu.addAction(self._act_theme_light); theme_menu.addAction(self._act_theme_dark); view_menu.addMenu(theme_menu)
        menubar.addMenu(view_menu)

    def _on_theme_changed(self, mode: str):
        self._theme.set_mode(mode); self._apply_theme(self._theme.colors())

    def _apply_theme(self, c: dict):
        self._colors = c; self._title_bar.apply_colors(c)
        r = 0 if self._win.isMaximized() else WINDOW_BORDER_RADIUS; bw = WINDOW_BORDER_WIDTH if r>0 else 0
        self._central.setStyleSheet("QWidget{" f"background:{c['bg_main']};" f"color:{c['text']};" "}" "QWidget#Root{" f"border:{bw}px solid {c['window_border']};" f"border-radius:{r}px;" "}")
        try:
            if hasattr(self, "_root_layout") and self._root_layout is not None: self._root_layout.setContentsMargins(bw,bw,bw,bw)
        except Exception: pass
        self._banner.setStyleSheet(f"QWidget{{background:{c['banner_bg']};}}"); self.banner_label.setStyleSheet(f"QLabel{{color:{c['banner_text']};}}")
        if not hasattr(self, "_banner_manager") or self._banner_manager is None: self._banner_manager = BannerManager(self._banner, self.banner_label, c)
        else: self._banner_manager.update_theme(c)
        btn_ss = ("QPushButton{" f"background:{c['button_bg']};" f"color:{c['control_fg']};" f"border:{BUTTON_BORDER_WIDTH}px solid {c['button_border_color']};" f"border-radius:{BUTTON_BORDER_RADIUS}px;" f"padding:{BUTTON_PADDING};" "}" "QPushButton:hover{" f"background:{c['interactive_hover']};" "}" "QPushButton:pressed{" f"background:{c['interactive_hover']};" "}" "QPushButton:disabled{" f"background:{c['button_bg']};" "color:#888888;" "}")
        icon_override = ("QPushButton[variant=\"icon\"]{" f"padding:{ICON_BUTTON_PADDING};" "min-width:28px;" "min-height:28px;" "}")
        icon_btn_ss = btn_ss + icon_override
        self.edit_players_btn.setStyleSheet(icon_btn_ss)
        try: self.rankings_btn.setStyleSheet(icon_btn_ss)
        except Exception: pass
        self.debug_toggle_btn.setStyleSheet(icon_btn_ss)
        self._apply_action_icons(c.get("action_icon_color", c.get("control_fg", "#000000")))
        scroll_track = c.get("scrollbar_track", c.get("bg_secondary", "#f0f0f0")); scroll_border = c.get("scrollbar_border", c.get("separator", "#b0b0b0"))
        handle_start = c.get("scrollbar_handle_start", c.get("separator", "#b0b0b0")); handle_end = c.get("scrollbar_handle_end", c.get("control_fg", "#7d7d7d"))
        handle_hover_start = c.get("scrollbar_handle_hover_start", c.get("control_fg", "#7d7d7d")); handle_hover_end = c.get("scrollbar_handle_hover_end", c.get("text", "#3a3a3a"))
        plain_scroll_css = self._scrollbar_css("QPlainTextEdit", scroll_track, scroll_border, handle_start, handle_end, handle_hover_start, handle_hover_end)
        list_scroll_css = self._scrollbar_css("QListWidget", scroll_track, scroll_border, handle_start, handle_end, handle_hover_start, handle_hover_end)
        text_scroll_css = self._scrollbar_css("QTextEdit", scroll_track, scroll_border, handle_start, handle_end, handle_hover_start, handle_hover_end)
        try: self.laps_list.apply_palette(c['text'], c['bg_main'], c.get('last_laps_hover', c.get('interactive_hover')), list_scroll_css)
        except Exception: pass
        self.debug_text.setStyleSheet(f"QPlainTextEdit{{background:{c['debug_bg']}; color:{c['text']};}}{plain_scroll_css}")
        self.log_text.setStyleSheet(f"QTextEdit{{background:{c['log_bg']}; color:{c['text']};}}{text_scroll_css}")
        for sep in self._seps:
            try: sep.setStyleSheet(f"QFrame{{background:{c['separator']};}}")
            except Exception: pass
        self.set_player_menu_state(self.player_combo.isEnabled())
        for tire_widget in self._tire_widgets:
            try: tire_widget.apply_palette(c['tire_bg'], c['tire_border'], c['tire_text'])
            except Exception: pass

    def _on_window_state_for_chrome(self, *_): self._apply_theme(self._colors or self._theme.colors())
    def _on_system_color_scheme_changed(self):
        if self._theme.get_mode()=="system": self._apply_theme(self._theme.colors())

    def _toggle_debug_action(self, checked: bool):
        self.debug_visible.set(bool(checked)); self._apply_debug_visibility()
        if callable(self.on_debug_toggle):
            try: self.on_debug_toggle(bool(checked))
            except Exception: pass

    def _set_debug_visible(self, flag: bool):
        self.debug_visible.set(bool(flag))
        self._act_debug.blockSignals(True); self._act_debug.setChecked(self.debug_visible.get()); self._act_debug.blockSignals(False)
        self._apply_debug_visibility()
        if callable(self.on_debug_toggle):
            try: self.on_debug_toggle(self.debug_visible.get())
            except Exception: pass

    def _apply_debug_visibility(self):
        vis = self.debug_visible.get(); self.debug_col.setVisible(vis); self._sep_debug.setVisible(vis)
        self.debug_toggle_btn.setToolTip("Masquer la zone debug" if vis else "Afficher la zone debug")
        if vis:
            for col in (0,2,4,6): self.center_lay.setColumnStretch(col, 1)
        else:
            for col in (0,2,4): self.center_lay.setColumnStretch(col, 1)
            self.center_lay.setColumnStretch(6, 0)

    def _pump_event_queue(self):
        if self._event_queue is None: return
        try:
            while True:
                name, payload = self._event_queue.get_nowait(); payload = payload or {}
                if name == "debug": self.update_debug(payload)
                elif name == "context": self.update_context(payload.get("track","---"), payload.get("car","---"), payload.get("track_id"))
                elif name == "player_menu_state": self.set_player_menu_state(payload.get("enabled", False))
                elif name == "log": self.add_log(payload.get("message",""))
                elif name == "player_best": self.update_player_personal_record(payload.get("text","---"))
                elif name == "ranking": self._update_ranking_display(payload.get("ranking", []))
                elif name == "banner":
                    if "type" in payload:
                        self._handle_banner_message(payload.get("type", ""))
                    else:
                        self.set_banner(payload.get("text", ""))
                elif name == "current_lap": self.update_current_lap_time(payload.get("text","---"))
                elif name == "last_laps":
                    entries = payload.get("entries") or payload.get("lines") or payload.get("text")
                    self.update_last_laps(entries or [])
        except _q.Empty: pass
        except Exception as e:
            try: self.add_log(f"UI error: {e}")
            except Exception: pass

    def _populate_laps_placeholder(self):
        lines = [
            "0:34.678\tNico", "0:36.878\tNico", "0:35.679\tNico", "0:34.678\tBooki",
            "0:36.878\tNico", "0:35.679\tJacques", "0:34.678\tNico", "0:34.132\tNico", "0:34.678\tNico",
        ]
        try: self.laps_list.set_items(lines)
        except Exception: pass

    def _apply_window_icon(self):
        try:
            if os.path.isfile(WINDOWS_ICON_PATH):
                icon = QIcon(WINDOWS_ICON_PATH); self._app.setWindowIcon(icon); self._win.setWindowIcon(icon)
                if hasattr(self, "_title_bar"): self._title_bar.set_icon(icon)
        except Exception: pass
