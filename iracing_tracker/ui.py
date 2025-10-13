# ui.py — Port PySide6 (Qt) de l'interface Tkinter d'origine
# ----------------------------------------------------------
# Dépendance: PySide6
# pip install PySide6
#
# Cette classe conserve la même API publique que l'ancienne :
#  - debug_visible.get()
#  - set_on_player_change(cb), set_on_debug_toggle(cb)
#  - bind_event_queue(queue), mainloop()
#  - add_log(), update_context(), update_debug(), update_player_personal_record(),
#    update_current_lap_time(), set_player_menu_state(), update_players(),
#    get_selected_player(), set_banner()
#
# Le worker thread et la logique métier ne changent pas (voir main.py).  ⮕  API compatible.

import os
import sys
import queue as _q
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon, QFont, QAction, QTextOption
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QPlainTextEdit, QTextEdit, QMenuBar, QMenu, QComboBox,
    QSizePolicy, QSpacerItem
)

# --------------------------------------------------------------------
# Paramètres visuels (reprennent l'esprit de la version Tkinter)
# --------------------------------------------------------------------
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
ICON_PATH = os.path.join(ASSETS_DIR, "icon.png")
WINDOWS_ICON_PATH = os.path.join(ASSETS_DIR, "icon.ico")

WINDOW_TITLE = "iRacing Tracker"
WINDOW_GEOMETRY = (1600, 1000)
MIN_WIDTH = 900
MIN_HEIGHT = 550

COLOR_BG_MAIN = "#f0f0f0"
COLOR_BG_SECONDARY = "#e5e5e5"
COLOR_TEXT = "black"
COLOR_CONTROL_FG = "black"
COLOR_BANNER_BG = "#f0f0f0"
COLOR_BANNER_TEXT = "#0d47a1"
COLOR_DEBUG_TEXT_BG = "#f0f0f0"
COLOR_LOG_TEXT_BG = "#f0f0f0"
COLOR_SEPARATOR = "#cccccc"
COLOR_CARD_RED = "#e57373"
COLOR_CARD_GREEN = "#9ccc65"

FONT_FAMILY = "Arial"
FONT_SIZE_LABELS = 12
FONT_SIZE_SECTION_TITLE = 12
FONT_SIZE_BANNER = 22
FONT_SIZE_PLAYER = 20
FONT_SIZE_LAPTIME = 24
FONT_SIZE_LAST_LAPTIMES = 12
FONT_SIZE_DEBUG = 12
FONT_SIZE_LOG = 12
FONT_SIZE_BUTTON = 9

TIRE_SQUARE_WIDTH = 48          # px
TIRE_SQUARE_HEIGHT = 72         # px
TIRE_SQUARE_RADIUS = 8          # px
TIRE_SQUARE_BG = "#eaeaea"      # fond neutre par défaut
TIRE_SQUARE_BORDER = "#bdbdbd"  # bordure neutre
TIRE_SQUARE_FONT_PT = 12        # taille de police
TIRE_SQUARE_TEXT_COLOR = "black"

TIRE_TEMP_PLACEHOLDER = "--°"
TIRE_WEAR_PLACEHOLDER = "--%"

UI_SECTION_MARGIN = 6 

DEBUG_INITIAL_VISIBLE = True
LOG_TEXT_HEIGHT_ROWS = 8   # approximation (Qt: on gère la hauteur via policy)
TIME_COL_PX = 120          # réserve visuelle pour la colonne "temps"

# --------------------------------------------------------------------
# Petits utilitaires pour compatibilité Tk
# --------------------------------------------------------------------
class _BoolVarCompat:
    """Expose .get() / .set() à la manière de tk.BooleanVar pour garder main.py inchangé."""
    def __init__(self, value=False):
        self._v = bool(value)
    def get(self):
        return bool(self._v)
    def set(self, v: bool):
        self._v = bool(v)

def _vsep(parent: QWidget) -> QFrame:
    f = QFrame(parent)
    f.setFrameShape(QFrame.VLine)
    f.setFrameShadow(QFrame.Plain)
    f.setStyleSheet(f"QFrame{{background:{COLOR_SEPARATOR}; max-width:1px;}}")
    return f

def _hsep(parent: QWidget) -> QFrame:
    f = QFrame(parent)
    f.setFrameShape(QFrame.HLine)
    f.setFrameShadow(QFrame.Plain)
    f.setStyleSheet(f"QFrame{{background:{COLOR_SEPARATOR}; max-height:1px;}}")
    return f

def _make_tire_square(text: str, bg: str = None, border: str = None) -> QWidget:
    """Carré stylé (taille, rayon, couleurs) avec valeurs par défaut neutres."""
    bg = bg or TIRE_SQUARE_BG
    border = border or TIRE_SQUARE_BORDER

    w = QWidget()
    w.setFixedSize(QSize(TIRE_SQUARE_WIDTH, TIRE_SQUARE_HEIGHT))
    w.setStyleSheet(
        "QWidget{"
        f"background:{bg};"
        f"border:1px solid {border};"
        f"border-radius:{TIRE_SQUARE_RADIUS}px;"
        "}"
    )
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)

    lab = QLabel(text)
    lab.setAlignment(Qt.AlignCenter)
    lab.setFont(QFont(FONT_FAMILY, TIRE_SQUARE_FONT_PT, QFont.Bold))
    lab.setStyleSheet(f"QLabel{{background:transparent; color:{TIRE_SQUARE_TEXT_COLOR};}}")

    lay.addWidget(lab)
    return w


# --------------------------------------------------------------------
# Classe principale (composition autour d'un QMainWindow)
# --------------------------------------------------------------------
class TrackerUI:
    def __init__(self, players: list, on_player_change, on_debug_toggle=None):
        # QApplication (unique) dans le thread UI
        self._app = QApplication.instance() or QApplication(sys.argv)

        # Fenêtre principale
        self._win = QMainWindow()
        self._win.setWindowTitle(WINDOW_TITLE)
        self._win.resize(*WINDOW_GEOMETRY)
        self._win.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self._apply_window_icon()

        # Compat .debug_visible.get()
        self.debug_visible = _BoolVarCompat(DEBUG_INITIAL_VISIBLE)

        # Callbacks externes
        self.on_player_change = on_player_change
        self.on_debug_toggle = on_debug_toggle

        # Widget central
        central = QWidget()
        central.setStyleSheet(f"QWidget{{background:{COLOR_BG_MAIN}; color:{COLOR_TEXT};}}")
        self._win.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- BANNIÈRE ---------------------------------------------------
        banner = QWidget()
        banner.setStyleSheet(f"QWidget{{background:{COLOR_BANNER_BG};}}")
        banner_lay = QVBoxLayout(banner)
        banner_lay.setContentsMargins(UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN)
        self.banner_label = QLabel("")
        self.banner_label.setAlignment(Qt.AlignCenter)
        self.banner_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_BANNER, QFont.Bold))
        self.banner_label.setStyleSheet(f"QLabel{{color:{COLOR_BANNER_TEXT};}}")
        banner_lay.addWidget(self.banner_label)
        root.addWidget(banner)
        # fine bordure inférieure
        root.addWidget(_hsep(central))

        # --- ZONE CENTRALE (4 colonnes dont Debug masquable) ------------
        center = QWidget()
        self.center_lay = QGridLayout(center)
        self.center_lay.setContentsMargins(UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN)
        self.center_lay.setHorizontalSpacing(12)
        self.center_lay.setVerticalSpacing(8)

        # Colonne Session
        self.session_col = QWidget()
        sc_lay = QVBoxLayout(self.session_col)
        sc_lay.setContentsMargins(UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN)
        sc_lay.setSpacing(6)

        sec_label = QLabel("SESSION")
        sec_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        sc_lay.addWidget(sec_label)

        self.session_time_label = QLabel("Temps de session : 1:23:45")
        self.session_time_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        self.track_label = QLabel("Circuit : ---")
        self.track_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        self.car_label = QLabel("Voiture : ---")
        self.car_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        sc_lay.addWidget(self.session_time_label)
        sc_lay.addWidget(self.track_label)
        sc_lay.addWidget(self.car_label)
        sc_lay.addWidget(_hsep(self.session_col))

        abs_info = QLabel("Record absolu (détenu par ---) :")
        abs_info.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        self.absolute_record_value = QLabel("---")
        self.absolute_record_value.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAPTIME, QFont.Bold))
        self.absolute_record_value.setAlignment(Qt.AlignCenter)
        sc_lay.addWidget(abs_info)
        sc_lay.addWidget(self.absolute_record_value)
        sc_lay.addWidget(_hsep(self.session_col))

        tires_grid = QWidget()
        tg_lay = QGridLayout(tires_grid)
        tg_lay.setContentsMargins(0, 0, 0, 0)
        tg_lay.setHorizontalSpacing(12)
        tg_lay.setVerticalSpacing(8)

        # Titre de la section (prend toute la ligne)
        tires_title = QLabel("Température et usure des pneus :")
        tires_title.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        tg_lay.addWidget(tires_title, 0, 0, 1, 5)

        # Rangée 1
        tg_lay.addWidget(_make_tire_square(TIRE_TEMP_PLACEHOLDER), 1, 0)
        tg_lay.addWidget(_make_tire_square(TIRE_TEMP_PLACEHOLDER), 1, 1)
        tg_lay.addItem(QSpacerItem(24, 1, QSizePolicy.Fixed, QSizePolicy.Minimum), 1, 2)
        tg_lay.addWidget(_make_tire_square(TIRE_WEAR_PLACEHOLDER), 1, 3)
        tg_lay.addWidget(_make_tire_square(TIRE_WEAR_PLACEHOLDER), 1, 4)

        # Rangée 2
        tg_lay.addWidget(_make_tire_square(TIRE_TEMP_PLACEHOLDER), 2, 0)
        tg_lay.addWidget(_make_tire_square(TIRE_TEMP_PLACEHOLDER), 2, 1)
        tg_lay.addItem(QSpacerItem(24, 1, QSizePolicy.Fixed, QSizePolicy.Minimum), 2, 2)
        tg_lay.addWidget(_make_tire_square(TIRE_WEAR_PLACEHOLDER), 2, 3)
        tg_lay.addWidget(_make_tire_square(TIRE_WEAR_PLACEHOLDER), 2, 4)

        sc_lay.addWidget(tires_grid)
        sc_lay.addStretch(1)

        # Colonne Joueur
        self.player_col = QWidget()
        pc_lay = QVBoxLayout(self.player_col)
        pc_lay.setContentsMargins(UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN)
        pc_lay.setSpacing(6)

        header_player = QWidget()
        hp_lay = QHBoxLayout(header_player)
        hp_lay.setContentsMargins(0, 0, 0, 0)
        title_player = QLabel("JOUEUR")
        title_player.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        hp_lay.addWidget(title_player)
        hp_lay.addStretch(1)
        self.edit_players_btn = QPushButton("Éditer la liste")
        self.edit_players_btn.setCursor(Qt.PointingHandCursor)
        self.edit_players_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        self.edit_players_btn.setStyleSheet(
            f"QPushButton{{background:{COLOR_BG_MAIN}; border:none;}}"
            f"QPushButton:hover{{background:{COLOR_BG_SECONDARY};}}"
        )
        self.edit_players_btn.setEnabled(False)  # même comportement que l'original (placeholder)
        hp_lay.addWidget(self.edit_players_btn)
        pc_lay.addWidget(header_player)

        # Sélecteur de joueur
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

        pc_lay.addWidget(_hsep(self.player_col))
        lbl_personal = QLabel("Record personnel :")
        lbl_personal.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        pc_lay.addWidget(lbl_personal)
        self.best_time_label = QLabel("---")
        self.best_time_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAPTIME, QFont.Bold))
        self.best_time_label.setAlignment(Qt.AlignCenter)
        pc_lay.addWidget(self.best_time_label)

        pc_lay.addWidget(_hsep(self.player_col))
        lbl_last = QLabel("Dernier tour :")
        lbl_last.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        pc_lay.addWidget(lbl_last)
        self.current_lap_label = QLabel("---")
        self.current_lap_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAPTIME, QFont.Bold))
        self.current_lap_label.setAlignment(Qt.AlignCenter)
        pc_lay.addWidget(self.current_lap_label)
        pc_lay.addStretch(1)

        # Colonne Derniers tours
        self.laps_col = QWidget()
        lc_lay = QVBoxLayout(self.laps_col)
        lc_lay.setContentsMargins(UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN)
        lc_lay.setSpacing(6)
        cap = QLabel("DERNIERS TOURS")
        cap.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        lc_lay.addWidget(cap)
        self.laps_text = QPlainTextEdit()
        self.laps_text.setReadOnly(True)
        self.laps_text.setFrameShape(QFrame.NoFrame)
        self.laps_text.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAST_LAPTIMES))
        self.laps_text.setStyleSheet(f"QPlainTextEdit{{background:{COLOR_BG_MAIN};}}")
        self._populate_laps_placeholder()
        lc_lay.addWidget(self.laps_text, 1)

        # Colonne Debug (masquable)
        self.debug_col = QWidget()
        dc_lay = QVBoxLayout(self.debug_col)
        dc_lay.setContentsMargins(UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN)
        dc_lay.setSpacing(6)
        header_dbg = QWidget()
        hd_lay = QHBoxLayout(header_dbg)
        hd_lay.setContentsMargins(0, 0, 0, 0)
        lbl_dbg = QLabel("DEBUG")
        lbl_dbg.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        hd_lay.addWidget(lbl_dbg)
        hd_lay.addStretch(1)
        self.debug_toggle_btn = QPushButton("Masquer")
        self.debug_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.debug_toggle_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        self.debug_toggle_btn.setStyleSheet(
            f"QPushButton{{background:{COLOR_BG_MAIN}; border:none;}}"
            f"QPushButton:hover{{background:{COLOR_BG_SECONDARY};}}"
        )
        self.debug_toggle_btn.clicked.connect(lambda: self._set_debug_visible(False))
        hd_lay.addWidget(self.debug_toggle_btn)
        dc_lay.addWidget(header_dbg)

        self.debug_text = QPlainTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setFrameShape(QFrame.NoFrame)
        self.debug_text.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEBUG))
        self.debug_text.setStyleSheet(f"QPlainTextEdit{{background:{COLOR_DEBUG_TEXT_BG};}}")
        self.debug_text.setWordWrapMode(QTextOption.NoWrap)
        dc_lay.addWidget(self.debug_text, 1)

        # Placement (session | sep | joueur | sep | tours | sep | debug)
        self.center_lay.addWidget(self.session_col, 0, 0)
        self.center_lay.addWidget(_vsep(center), 0, 1)
        self.center_lay.addWidget(self.player_col, 0, 2)
        self.center_lay.addWidget(_vsep(center), 0, 3)
        self.center_lay.addWidget(self.laps_col, 0, 4)
        self._sep_debug = _vsep(center)
        self.center_lay.addWidget(self._sep_debug, 0, 5)
        self.center_lay.addWidget(self.debug_col, 0, 6)

        # Pas de stretch sur les colonnes séparateurs
        for col in (1, 3, 5):
            self.center_lay.setColumnStretch(col, 0)

        root.addWidget(center, 1)

        # --- LOGS -------------------------------------------------------
        root.addWidget(_hsep(central))
        logs = QWidget()
        logs_lay = QVBoxLayout(logs)
        logs_lay.setContentsMargins(UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN, UI_SECTION_MARGIN)
        logs_lay.setSpacing(6)
        ltitle = QLabel("MESSAGES / LOGS")
        ltitle.setFont(QFont(FONT_FAMILY, FONT_SIZE_SECTION_TITLE, QFont.Bold))
        logs_lay.addWidget(ltitle)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFrameShape(QFrame.NoFrame)
        self.log_text.setFont(QFont(FONT_FAMILY, FONT_SIZE_LOG))
        self.log_text.setStyleSheet(f"QTextEdit{{background:{COLOR_LOG_TEXT_BG};}}")
        logs_lay.addWidget(self.log_text)
        root.addWidget(logs, 0)

        # --- MENU -------------------------------------------------------
        self._build_menubar()

        # Appliquer visibilité initiale de la colonne Debug
        self._apply_debug_visibility(initial=True)

        # Timer pour pomper la queue (équivalent de .after(16, ...))
        self._event_queue = None
        self._queue_timer = QTimer(self._win)
        self._queue_timer.setInterval(16)
        self._queue_timer.timeout.connect(self._pump_event_queue)

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
        # reste en bas si l'utilisateur est déjà en bas
        sb = self.debug_text.verticalScrollBar()
        at_bottom = sb.value() >= (sb.maximum() - 4)
        # remplir
        lines = []
        for k, v in (data or {}).items():
            lines.append(f"{k}: {v}")
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
        # sélection
        if current and players and current in players:
            self.player_combo.setCurrentText(current)
        elif players:
            self.player_combo.setCurrentIndex(0)
        else:
            self.player_combo.setCurrentText("---")
        self.player_combo.blockSignals(False)

    def set_player_menu_state(self, enabled: bool):
        en = bool(enabled)
        self.player_combo.setEnabled(en)
        # nuance visuelle simple
        fg = COLOR_CONTROL_FG if en else "#888888"
        self.player_combo.setStyleSheet(
            f"QComboBox{{font-family:{FONT_FAMILY}; font-size:{FONT_SIZE_PLAYER}pt; color:{fg};}}"
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
        menubar = QMenuBar(self._win)
        self._win.setMenuBar(menubar)

        file_menu = QMenu("Fichier", menubar)
        file_menu.addAction(QAction("(à venir)", file_menu, enabled=False))
        menubar.addMenu(file_menu)

        edit_menu = QMenu("Édition", menubar)
        edit_menu.addAction(QAction("(à venir)", edit_menu, enabled=False))
        menubar.addMenu(edit_menu)

        view_menu = QMenu("Affichage", menubar)
        self._act_debug = QAction("Debug", view_menu, checkable=True)
        self._act_debug.setChecked(self.debug_visible.get())
        self._act_debug.triggered.connect(self._toggle_debug_action)
        view_menu.addAction(self._act_debug)
        menubar.addMenu(view_menu)

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
        # synchroniser l'action du menu
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
        self.debug_toggle_btn.setText("Masquer" if vis else "Afficher")

        # Répartition équitable des colonnes visibles
        if vis:
            # 4 colonnes visibles → mêmes facteurs de stretch
            for col in (0, 2, 4, 6):
                self.center_lay.setColumnStretch(col, 1)
        else:
            # 3 colonnes visibles → mêmes facteurs de stretch, debug désactivé
            for col in (0, 2, 4):
                self.center_lay.setColumnStretch(col, 1)
            self.center_lay.setColumnStretch(6, 0)  # colonne Debug sans stretch


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
            # Comme avant: on reste robuste, on consigne l'erreur dans les logs UI
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
            if os.path.isfile(ICON_PATH):
                self._win.setWindowIcon(QIcon(ICON_PATH))
            elif os.name == "nt" and os.path.isfile(WINDOWS_ICON_PATH):
                self._win.setWindowIcon(QIcon(WINDOWS_ICON_PATH))
        except Exception:
            pass
