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
import ctypes
import queue as _q
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QSize, QSettings, Signal, QPoint, QEvent
from PySide6.QtGui import QIcon, QFont, QAction, QTextOption, QActionGroup, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QPlainTextEdit, QTextEdit, QMenuBar, QMenu, QComboBox,
    QSizePolicy, QSpacerItem, QToolButton, QStyle
)

# --------------------------------------------------------------------
# Paramètres visuels (reprennent l'esprit de la version Tkinter)
# --------------------------------------------------------------------
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
ICON_PATH = os.path.join(ASSETS_DIR, "icon.png")
WINDOWS_ICON_PATH = os.path.join(ASSETS_DIR, "icon.ico")

WINDOW_TITLE = "iRacing Tracker"
WINDOW_GEOMETRY = (1600, 1000)
MIN_WIDTH = 1200
MIN_HEIGHT = 800

# --- Chrome fenêtre (bordure externe) ---
WINDOW_BORDER_WIDTH   = 1      # épaisseur visuelle de la bordure
WINDOW_BORDER_RADIUS  = 8      # rayon des coins (0 = coins droits)

# --- Thème clair ---
LIGHT_WINDOW_BORDER_COLOR = "#000000"
LIGHT_BG_MAIN         = "#f0f0f0"
LIGHT_TEXT            = "#000000"
LIGHT_BG_SECONDARY    = "#e5e5e5"
LIGHT_BANNER_BG       = "#f0f0f0"
LIGHT_BANNER_TEXT     = "#0d47a1"
LIGHT_DEBUG_BG        = "#f0f0f0"
LIGHT_LOG_BG          = "#f0f0f0"
LIGHT_SEPARATOR       = "#cccccc"
LIGHT_CONTROL_FG      = "#000000"
LIGHT_TIRE_BG         = "#eaeaea"
LIGHT_TIRE_BORDER     = "#bdbdbd"
LIGHT_TIRE_TEXT       = "#000000"

# --- Thème sombre ---
DARK_WINDOW_BORDER_COLOR  = "#ffffff"
DARK_BG_MAIN          = "#1f1f1f"
DARK_TEXT             = "#e6e6e6"
DARK_BG_SECONDARY     = "#2a2a2a"
DARK_BANNER_BG        = "#1f1f1f"
DARK_BANNER_TEXT      = "#e6e6e6"
DARK_DEBUG_BG         = "#262626"
DARK_LOG_BG           = "#262626"
DARK_SEPARATOR        = "#3a3a3a"
DARK_CONTROL_FG       = "#e6e6e6"
DARK_TIRE_BG          = "#2b2b2b"
DARK_TIRE_BORDER      = "#4b4b4b"
DARK_TIRE_TEXT        = "#e6e6e6"

LIGHT_TITLE_BG                = "#e7e7e7"
LIGHT_TITLE_FG                = "#111111"
LIGHT_TITLE_BTN_HOVER         = "#d9d9d9"
LIGHT_TITLE_BTN_PRESSED       = "#c4c4c4"
LIGHT_TITLE_BTN_CLOSE_HOVER   = "#e81123"
LIGHT_TITLE_BTN_CLOSE_PRESSED = "#b50d1c"

DARK_TITLE_BG                 = "#2a2a2a"
DARK_TITLE_FG                 = "#f1f1f1"
DARK_TITLE_BTN_HOVER          = "#3a3a3a"
DARK_TITLE_BTN_PRESSED        = "#4b4b4b"
DARK_TITLE_BTN_CLOSE_HOVER    = "#c42b1c"
DARK_TITLE_BTN_CLOSE_PRESSED  = "#9a1d13"

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

TIRE_SQUARE_WIDTH = 48          
TIRE_SQUARE_HEIGHT = 72         
TIRE_SQUARE_RADIUS = 8          
TIRE_SQUARE_FONT_PT = 12        

TIRE_TEMP_PLACEHOLDER = "--°"
TIRE_WEAR_PLACEHOLDER = "--%"

SECTION_MARGIN = 15 
SECTION_TITLE_GAP = 10
SECTION_SEPARATOR_SPACING = 15
SEPARATOR_THICKNESS = 1

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
    f.setFrameShape(QFrame.NoFrame)
    f.setFixedWidth(SEPARATOR_THICKNESS)
    # Couleur appliquée par _apply_theme()
    return f

def _hsep(parent: QWidget) -> QFrame:
    f = QFrame(parent)
    f.setFrameShape(QFrame.NoFrame)
    f.setFixedHeight(SEPARATOR_THICKNESS)
    # Couleur appliquée par _apply_theme()
    return f

def _make_tire_square(text: str) -> QWidget:
    """Carré avec taille/rayon ; couleurs posées par _apply_theme()."""
    w = QWidget()
    w.setFixedSize(QSize(TIRE_SQUARE_WIDTH, TIRE_SQUARE_HEIGHT))
    w.setStyleSheet(
        "QWidget{"
        "border:1px solid transparent;"
        f"border-radius:{TIRE_SQUARE_RADIUS}px;"
        "}"
    )
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)

    lab = QLabel(text)
    lab.setAlignment(Qt.AlignCenter)
    lab.setFont(QFont(FONT_FAMILY, TIRE_SQUARE_FONT_PT, QFont.Bold))
    # couleur du texte appliquée par _apply_theme()
    lay.addWidget(lab)
    return w


IS_WINDOWS = os.name == "nt"

if IS_WINDOWS:
    from ctypes import wintypes

    WM_NCHITTEST = 0x0084
    WM_GETMINMAXINFO = 0x0024
    WM_NCLBUTTONDOWN  = 0x00A1
    WM_NCLBUTTONDBLCLK = 0x00A3
    WM_MOUSEMOVE       = 0x0200
    WM_LBUTTONUP       = 0x0202
    MK_LBUTTON         = 0x0001
    WM_NCMOUSEMOVE = 0x00A0
    HTCLIENT = 1
    HTCAPTION = 2
    HTLEFT = 10
    HTRIGHT = 11
    HTTOP = 12
    HTTOPLEFT = 13
    HTTOPRIGHT = 14
    HTBOTTOM = 15
    HTBOTTOMLEFT = 16
    HTBOTTOMRIGHT = 17
    SM_CXDRAG = 68
    SM_CYDRAG = 69

    MONITOR_DEFAULTTONEAREST = 0x00000002

    class MINMAXINFO(ctypes.Structure):
        _fields_ = [
            ("ptReserved", wintypes.POINT),
            ("ptMaxSize", wintypes.POINT),
            ("ptMaxPosition", wintypes.POINT),
            ("ptMinTrackSize", wintypes.POINT),
            ("ptMaxTrackSize", wintypes.POINT),
        ]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", wintypes.RECT),
            ("rcWork", wintypes.RECT),
            ("dwFlags", wintypes.DWORD),
        ]


class TrackerMainWindow(QMainWindow):
    """QMainWindow frameless avec gestion du redimensionnement/windows spécifique."""

    window_state_changed = Signal(Qt.WindowStates)

    def __init__(self):
        super().__init__()
        self._border_width = 8
        self._title_bar_widget = None

        # Flags pour un bon comportement taskbar (minimize/maximize toggle)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Window
            | Qt.WindowSystemMenuHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
        )

        # État pour le drag depuis maximisé
        self._drag_from_max = False
        self._drag_start_global = QPoint()
        self._drag_anchor_ratio = 0.5
        if IS_WINDOWS:
            self._drag_threshold_x = max(1, ctypes.windll.user32.GetSystemMetrics(SM_CXDRAG))
            self._drag_threshold_y = max(1, ctypes.windll.user32.GetSystemMetrics(SM_CYDRAG))

        # Suivi d’état (pas d’appel à windowState() ici)
        self._last_window_state = Qt.WindowNoState
        self._was_maximized_before_minimize = False
        self._saved_normal_geom = None


    def set_title_bar_widget(self, widget: QWidget):
        self._title_bar_widget = widget

    def resizeEvent(self, event):
        try:
            self._update_corner_region()
        except Exception:
            pass
        super().resizeEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            prev = getattr(self, "_last_window_state", Qt.WindowNoState)
            new_state = self.windowState()

            # On entre en maximisé -> mémoriser la géométrie "normale" pour un vrai restore
            if (new_state & Qt.WindowMaximized) and not (prev & Qt.WindowMaximized):
                try:
                    self._saved_normal_geom = self.normalGeometry()
                except Exception:
                    self._saved_normal_geom = self.geometry()
                    
            # Si on entre en minimisé, mémoriser si on était maximisé avant
            if new_state & Qt.WindowMinimized:
                self._was_maximized_before_minimize = bool(prev & Qt.WindowMaximized)

            # Si on sort du minimisé : si on était maximisé avant, re-maximiser proprement
            if (prev & Qt.WindowMinimized) and not (new_state & Qt.WindowMinimized):
                if self._was_maximized_before_minimize and not (new_state & Qt.WindowMaximized):
                    QTimer.singleShot(0, self.showMaximized)
                self._was_maximized_before_minimize = False

            self.window_state_changed.emit(new_state)
            try:
                self._update_corner_region()
            except Exception:
                pass

            self._last_window_state = new_state

        super().changeEvent(event)

    def restore_normal_geometry(self):
        self.showNormal()
        try:
            if self._saved_normal_geom and self._saved_normal_geom.isValid():
                self.setGeometry(self._saved_normal_geom)
        except Exception:
            pass

    def _update_corner_region(self):
        # Découpe la forme de la fenêtre en arrondi (ou remet à 0 en maximisé)
        if not IS_WINDOWS:
            return
        r = 0 if self.isMaximized() else max(0, int(WINDOW_BORDER_RADIUS))
        hwnd = int(self.winId())
        if r == 0:
            ctypes.windll.user32.SetWindowRgn(hwnd, 0, True)
            return
        w, h = self.width(), self.height()
        rgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1, 2 * r, 2 * r)
        ctypes.windll.user32.SetWindowRgn(hwnd, rgn, True)
        ctypes.windll.gdi32.DeleteObject(rgn)

    @staticmethod
    def _make_lparam_from_point(pt: QPoint) -> int:
        # fabrique un LPARAM (x,y) pour SendMessage
        return ctypes.c_uint32(((pt.y() & 0xFFFF) << 16) | (pt.x() & 0xFFFF)).value


    def nativeEvent(self, eventType, message):
        if not IS_WINDOWS:
            return super().nativeEvent(eventType, message)

        if eventType not in ("windows_generic_MSG", b"windows_generic_MSG"):
            return super().nativeEvent(eventType, message)

        msg = ctypes.wintypes.MSG.from_address(int(message))

        if msg.message == WM_NCHITTEST:
            result = self._handle_nc_hit_test(msg.lParam)
            if result is not None:
                return True, result

        if msg.message == WM_GETMINMAXINFO:
            self._handle_get_min_max_info(msg.lParam)
            return True, 0
        

        # Double-clic dans la zone titre -> Max/Restore (comportement standard)
        if msg.message == WM_NCLBUTTONDBLCLK and msg.wParam == HTCAPTION:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
            return True, 0

        # Prépare un drag depuis l'état maximisé (NE RESTAURE PAS ENCORE)
        if msg.message == WM_NCLBUTTONDOWN and msg.wParam == HTCAPTION and self.isMaximized():
            self._drag_from_max = True
            self._drag_start_global = self._unpack_lparam(msg.lParam)
            # mémorise l'ancrage horizontal sous la souris
            try:
                if self._title_bar_widget:
                    local = self._title_bar_widget.mapFromGlobal(self._drag_start_global)
                    bar_w = max(1, self._title_bar_widget.width())
                    self._drag_anchor_ratio = max(0.0, min(1.0, local.x() / bar_w))
                else:
                    self._drag_anchor_ratio = 0.5
            except Exception:
                self._drag_anchor_ratio = 0.5
            return False, 0  # on laisse Windows gérer le clic (rien à déplacer en max)

        # Si on bouge vraiment -> restaurer et relayer le drag natif
        if self._drag_from_max and self.isMaximized() and (
            msg.message == WM_MOUSEMOVE or msg.message == WM_NCMOUSEMOVE
        ):
            if msg.message == WM_MOUSEMOVE:
                client_pos = self._unpack_lparam(msg.lParam)     # coords client
                global_pos = self.mapToGlobal(client_pos)
            else:  # WM_NCMOUSEMOVE -> coords écran directement
                global_pos = self._unpack_lparam(msg.lParam)

            dx = abs(global_pos.x() - self._drag_start_global.x())
            dy = abs(global_pos.y() - self._drag_start_global.y())
            if dx >= self._drag_threshold_x or dy >= self._drag_threshold_y:
                self.showNormal()
                new_x = int(global_pos.x() - self.width() * self._drag_anchor_ratio)
                new_y = max(0, global_pos.y() - (self._title_bar_widget.HEIGHT // 2 if self._title_bar_widget else 10))
                self.move(new_x, new_y)

                ctypes.windll.user32.ReleaseCapture()
                ctypes.windll.user32.SendMessageW(
                    int(self.winId()), WM_NCLBUTTONDOWN, HTCAPTION, self._make_lparam_from_point(global_pos)
                )
                self._drag_from_max = False
                return True, 0

                # Bouton relâché -> on sort du mode "peut-être drag"
        if msg.message == WM_LBUTTONUP and self._drag_from_max:
            self._drag_from_max = False
            return False, 0

        return super().nativeEvent(eventType, message)

    def _handle_nc_hit_test(self, lparam):
        if self.isMaximized():
            if self._title_bar_widget:
                global_pos = self._unpack_lparam(lparam)
                local = self._title_bar_widget.mapFromGlobal(global_pos)
                hit = self._title_bar_widget.hit_test(local)
                if hit is not None:
                    return hit
            return None

        global_pos = self._unpack_lparam(lparam)
        local = self.mapFromGlobal(global_pos)

        # Bords pour le redimensionnement
        bw = self._border_width
        w = self.width()
        h = self.height()
        x = local.x()
        y = local.y()

        if x < 0 or y < 0 or x > w or y > h:
            return None

        on_left = x <= bw
        on_right = x >= w - bw
        on_top = y <= bw
        on_bottom = y >= h - bw

        if on_top and on_left:
            return HTTOPLEFT
        if on_top and on_right:
            return HTTOPRIGHT
        if on_bottom and on_left:
            return HTBOTTOMLEFT
        if on_bottom and on_right:
            return HTBOTTOMRIGHT
        if on_top:
            return HTTOP
        if on_bottom:
            return HTBOTTOM
        if on_left:
            return HTLEFT
        if on_right:
            return HTRIGHT

        if self._title_bar_widget:
            local_title = self._title_bar_widget.mapFromGlobal(global_pos)
            hit = self._title_bar_widget.hit_test(local_title)
            if hit is not None:
                return hit

        return None

    def _handle_get_min_max_info(self, lparam):
        if not IS_WINDOWS:
            return

        info = ctypes.cast(lparam, ctypes.POINTER(MINMAXINFO)).contents
        info.ptMinTrackSize.x = self.minimumWidth()
        info.ptMinTrackSize.y = self.minimumHeight()

        monitor = ctypes.windll.user32.MonitorFromWindow(int(self.winId()), MONITOR_DEFAULTTONEAREST)
        if monitor:
            monitor_info = MONITORINFO()
            monitor_info.cbSize = ctypes.sizeof(MONITORINFO)
            if ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(monitor_info)):
                work = monitor_info.rcWork
                info.ptMaxPosition.x = work.left
                info.ptMaxPosition.y = work.top
                info.ptMaxSize.x = work.right - work.left
                info.ptMaxSize.y = work.bottom - work.top
                info.ptMaxTrackSize.x = info.ptMaxSize.x
                info.ptMaxTrackSize.y = info.ptMaxSize.y

    @staticmethod
    def _unpack_lparam(lparam) -> QPoint:
        value = int(lparam) & 0xFFFFFFFF
        x = ctypes.c_short(value & 0xFFFF).value
        y = ctypes.c_short((value >> 16) & 0xFFFF).value
        return QPoint(x, y)


class CustomTitleBar(QWidget):
    """Barre de titre personnalisée avec menu intégré (style VS Code)."""

    HEIGHT = 36

    def __init__(self, window: QMainWindow):
        super().__init__(window)
        self._win = window
        self.setObjectName("CustomTitleBar")
        self.setFixedHeight(self.HEIGHT)

        self._menu_bar = QMenuBar(self)
        self._menu_bar.setNativeMenuBar(False)
        self._menu_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(6)

        self._icon_label = QLabel()
        self._icon_label.setObjectName("TitleIcon")
        self._icon_label.setFixedSize(18, 18)
        self._icon_label.setScaledContents(True)
        layout.addWidget(self._icon_label)
        layout.addWidget(self._menu_bar)
        layout.addStretch(1)

        self._buttons_container = QWidget()
        btn_layout = QHBoxLayout(self._buttons_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(0)

        self._btn_min = self._make_button(QStyle.SP_TitleBarMinButton, "Réduire")
        self._btn_min.clicked.connect(self._win.showMinimized)

        self._btn_max = self._make_button(QStyle.SP_TitleBarMaxButton, "Agrandir")
        self._btn_max.clicked.connect(self._toggle_max_restore)

        self._btn_close = self._make_button(QStyle.SP_TitleBarCloseButton, "Fermer")
        self._btn_close.setObjectName("CloseButton")
        self._btn_close.clicked.connect(self._win.close)

        btn_layout.addWidget(self._btn_min)
        btn_layout.addWidget(self._btn_max)
        btn_layout.addWidget(self._btn_close)

        layout.addWidget(self._buttons_container)

    def menu_bar(self) -> QMenuBar:
        return self._menu_bar

    def set_icon(self, icon: QIcon):
        if icon and not icon.isNull():
            self._icon_label.setPixmap(icon.pixmap(18, 18))
        else:
            self._icon_label.clear()

    def apply_colors(self, colors: dict):
        bg = colors["title_bg"]
        fg = colors["title_fg"]
        hover = colors["title_btn_hover"]
        pressed = colors["title_btn_pressed"]
        close_hover = colors["title_btn_close_hover"]
        close_pressed = colors["title_btn_close_pressed"]
        menu_bg = colors["bg_secondary"]
        separator = colors["separator"]

        style = (
            f"#CustomTitleBar{{background:{bg};}}"
            f"#CustomTitleBar QLabel{{color:{fg};}}"
            f"#CustomTitleBar QMenuBar{{background:{bg}; color:{fg}; border:0; padding:0;}}"
            f"#CustomTitleBar QMenuBar::item{{background:transparent; color:{fg}; padding:3px 12px; margin:0 2px; border-radius:4px;}}"
            f"#CustomTitleBar QMenuBar::item:selected{{background:{hover};}}"
            f"#CustomTitleBar QMenu{{background:{menu_bg}; color:{fg}; border:1px solid {separator};}}"
            f"#CustomTitleBar QMenu::item:selected{{background:{hover}; color:{fg};}}"
            f"#CustomTitleBar QToolButton{{background:transparent; border:none; color:{fg};}}"
            f"#CustomTitleBar QToolButton:hover{{background:{hover};}}"
            f"#CustomTitleBar QToolButton:pressed{{background:{pressed};}}"
            f"#CustomTitleBar QToolButton#CloseButton:hover{{background:{close_hover}; color:#ffffff;}}"
            f"#CustomTitleBar QToolButton#CloseButton:pressed{{background:{close_pressed}; color:#ffffff;}}"
        )
        self.setStyleSheet(style)

    def on_window_state_changed(self, state: Qt.WindowStates):
        self._update_max_button_icon()
        if state & Qt.WindowMaximized:
            self._btn_max.setToolTip("Restaurer")
        else:
            self._btn_max.setToolTip("Agrandir")

    def hit_test(self, pos: QPoint):
        if not self.rect().contains(pos):
            return None
        if self._buttons_container.geometry().contains(pos):
            return HTCLIENT if IS_WINDOWS else None
        if self._menu_bar.geometry().contains(pos):
            return HTCLIENT if IS_WINDOWS else None
        return HTCAPTION if IS_WINDOWS else None

    def _make_button(self, standard_icon, tooltip: str) -> QToolButton:
        btn = QToolButton(self)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.ArrowCursor)
        btn.setIcon(self.style().standardIcon(standard_icon))
        btn.setIconSize(QSize(12, 12))
        btn.setAutoRaise(False)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setFixedSize(46, self.HEIGHT)
        return btn

    def _toggle_max_restore(self):
        if self._win.isMaximized():
            self._win.restore_normal_geometry()  # <- appeler la méthode du QMainWindow
        else:
            self._win.showMaximized()
        # (facultatif) pas besoin d'appeler _update_max_button_icon ici


    def _update_max_button_icon(self):
        icon_role = QStyle.SP_TitleBarNormalButton if self._win.isMaximized() else QStyle.SP_TitleBarMaxButton
        self._btn_max.setIcon(self.style().standardIcon(icon_role))

# --------------------------------------------------------------------
# Gestion de thème (Clair / Sombre / Système)
# --------------------------------------------------------------------
class ThemeManager:
    """
    Fournit un jeu de couleurs cohérent pour light/dark et un mode "system".
    Stocke le choix dans QSettings et suit le thème système si demandé.
    """
    SETTINGS_ORG = "iRacingTracker"
    SETTINGS_APP = "iRacingTracker"
    SETTINGS_KEY = "theme.mode"   # "system" | "light" | "dark"

    def __init__(self, app: QApplication):
        self.app = app
        self.settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        self.mode = self.settings.value(self.SETTINGS_KEY, "system")
        # connexion au changement de schéma de couleur du système (Windows 10/11)
        hints = self.app.styleHints()
        try:
            hints.colorSchemeChanged.connect(self._on_system_scheme_changed)
        except Exception:
            pass

    # ---------- API publique ----------
    def get_mode(self) -> str:
        return self.mode

    def set_mode(self, mode: str):
        if mode not in ("system", "light", "dark"):
            return
        self.mode = mode
        self.settings.setValue(self.SETTINGS_KEY, mode)

    def effective_scheme(self) -> str:
        """Retourne 'light' ou 'dark' selon le mode courant."""
        if self.mode == "system":
            return self._system_scheme()
        return self.mode

    def colors(self) -> dict:
        """Renvoie le dictionnaire de couleurs pour le schéma effectif."""
        scheme = self.effective_scheme()
        if scheme == "dark":
            return dict(
                window_border=DARK_WINDOW_BORDER_COLOR,
                bg_main=DARK_BG_MAIN,
                text=DARK_TEXT,
                bg_secondary=DARK_BG_SECONDARY,
                banner_bg=DARK_BANNER_BG,
                banner_text=DARK_BANNER_TEXT,
                debug_bg=DARK_DEBUG_BG,
                log_bg=DARK_LOG_BG,
                separator=DARK_SEPARATOR,
                control_fg=DARK_CONTROL_FG,
                tire_bg=DARK_TIRE_BG,
                tire_border=DARK_TIRE_BORDER,
                tire_text=DARK_TIRE_TEXT,
                title_bg=DARK_TITLE_BG,
                title_fg=DARK_TITLE_FG,
                title_btn_hover=DARK_TITLE_BTN_HOVER,
                title_btn_pressed=DARK_TITLE_BTN_PRESSED,
                title_btn_close_hover=DARK_TITLE_BTN_CLOSE_HOVER,
                title_btn_close_pressed=DARK_TITLE_BTN_CLOSE_PRESSED,
            )
        else:
            return dict(
                window_border=LIGHT_WINDOW_BORDER_COLOR,
                bg_main=LIGHT_BG_MAIN,
                text=LIGHT_TEXT,
                bg_secondary=LIGHT_BG_SECONDARY,
                banner_bg=LIGHT_BANNER_BG,
                banner_text=LIGHT_BANNER_TEXT,
                debug_bg=LIGHT_DEBUG_BG,
                log_bg=LIGHT_LOG_BG,
                separator=LIGHT_SEPARATOR,
                control_fg=LIGHT_CONTROL_FG,
                tire_bg=LIGHT_TIRE_BG,
                tire_border=LIGHT_TIRE_BORDER,
                tire_text=LIGHT_TIRE_TEXT,
                title_bg=LIGHT_TITLE_BG,
                title_fg=LIGHT_TITLE_FG,
                title_btn_hover=LIGHT_TITLE_BTN_HOVER,
                title_btn_pressed=LIGHT_TITLE_BTN_PRESSED,
                title_btn_close_hover=LIGHT_TITLE_BTN_CLOSE_HOVER,
                title_btn_close_pressed=LIGHT_TITLE_BTN_CLOSE_PRESSED,
            )


    # ---------- Interne ----------
    def _system_scheme(self) -> str:
        try:
            scheme = QGuiApplication.styleHints().colorScheme()
            # Robustesse: on regarde la string de l'enum
            s = str(scheme)
            return "dark" if "Dark" in s else "light"
        except Exception:
            return "light"

    def _on_system_scheme_changed(self, *args):
        # Le TrackerUI re‑applique le thème si mode == "system"
        pass




# --------------------------------------------------------------------
# Classe principale (composition autour d'un QMainWindow)
# --------------------------------------------------------------------
class TrackerUI:
    def __init__(self, players: list, on_player_change, on_debug_toggle=None):
        # QApplication (unique) dans le thread UI
        self._app = QApplication.instance() or QApplication(sys.argv)

        # Fenêtre principale
        self._win = TrackerMainWindow()

        self._theme = ThemeManager(self._app)  # gestionnaire de thèmes
        self._colors = None                    # couleurs effective du thème courant
        self._seps = []                        # tous les séparateurs (H+V) à re‑styler
        self._tire_squares = []                # les 8 carrés "pneus" à re‑styler
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
            # Rend les coins visuellement arrondis si tu mets un rayon > 0
            self._win.setAttribute(Qt.WA_TranslucentBackground, True)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- BARRE DE TITRE PERSONNALIS�E --------------------------------
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

        # --- BANNIÈRE ---------------------------------------------------
        banner = QWidget()
        self._banner = banner
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


        # --- ZONE CENTRALE (4 colonnes dont Debug masquable) ------------
        center = QWidget()
        self.center_lay = QGridLayout(center)
        self.center_lay.setContentsMargins(0, 0, 0, 0)
        self.center_lay.setHorizontalSpacing(0)
        self.center_lay.setVerticalSpacing(8)

        # Colonne Session
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
        s = _hsep(self.session_col)
        self._seps.append(s)
        sc_lay.addSpacing(SECTION_SEPARATOR_SPACING)
        sc_lay.addWidget(s)
        sc_lay.addSpacing(SECTION_SEPARATOR_SPACING)


        abs_info = QLabel("Record absolu (détenu par ---) :")
        abs_info.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        self.absolute_record_value = QLabel("---")
        self.absolute_record_value.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAPTIME, QFont.Bold))
        self.absolute_record_value.setAlignment(Qt.AlignCenter)
        sc_lay.addWidget(abs_info)
        sc_lay.addWidget(self.absolute_record_value)
        s = _hsep(self.session_col)
        self._seps.append(s)
        sc_lay.addSpacing(SECTION_SEPARATOR_SPACING)
        sc_lay.addWidget(s)
        sc_lay.addSpacing(SECTION_SEPARATOR_SPACING)

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
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq)
        tg_lay.addWidget(sq, 1, 0)

        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq)
        tg_lay.addWidget(sq, 1, 1)
        tg_lay.addItem(QSpacerItem(24, 1, QSizePolicy.Fixed, QSizePolicy.Minimum), 1, 2)
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq)
        tg_lay.addWidget(sq, 1, 3)
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq)
        tg_lay.addWidget(sq, 1, 4)

        # Rangée 2
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq)
        tg_lay.addWidget(sq, 2, 0)
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq)
        tg_lay.addWidget(sq, 2, 1)
        tg_lay.addItem(QSpacerItem(24, 1, QSizePolicy.Fixed, QSizePolicy.Minimum), 2, 2)
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq)
        tg_lay.addWidget(sq, 2, 3)
        sq = _make_tire_square(TIRE_TEMP_PLACEHOLDER); self._tire_squares.append(sq)
        tg_lay.addWidget(sq, 2, 4)

        sc_lay.addWidget(tires_grid)
        sc_lay.addStretch(1)

        # Colonne Joueur
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
        self.edit_players_btn = QPushButton("Éditer la liste")
        self.edit_players_btn.setCursor(Qt.PointingHandCursor)
        self.edit_players_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        self.edit_players_btn.setEnabled(False)  # même comportement que l'original (placeholder)
        hp_lay.addWidget(self.edit_players_btn)
        pc_lay.addWidget(header_player)
        pc_lay.addSpacing(SECTION_TITLE_GAP)

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

        s = _hsep(self.player_col)
        self._seps.append(s)
        pc_lay.addSpacing(SECTION_SEPARATOR_SPACING)
        pc_lay.addWidget(s)
        pc_lay.addSpacing(SECTION_SEPARATOR_SPACING)

        lbl_personal = QLabel("Record personnel :")
        lbl_personal.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        pc_lay.addWidget(lbl_personal)
        self.best_time_label = QLabel("---")
        self.best_time_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_LAPTIME, QFont.Bold))
        self.best_time_label.setAlignment(Qt.AlignCenter)
        pc_lay.addWidget(self.best_time_label)

        s = _hsep(self.player_col)
        self._seps.append(s)
        pc_lay.addSpacing(SECTION_SEPARATOR_SPACING)
        pc_lay.addWidget(s)
        pc_lay.addSpacing(SECTION_SEPARATOR_SPACING)

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

        # Colonne Debug (masquable)
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
        self.debug_toggle_btn = QPushButton("Masquer")
        self.debug_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.debug_toggle_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        self.debug_toggle_btn.clicked.connect(lambda: self._set_debug_visible(False))
        hd_lay.addWidget(self.debug_toggle_btn)
        dc_lay.addWidget(header_dbg)
        dc_lay.addSpacing(SECTION_TITLE_GAP)

        self.debug_text = QPlainTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setFrameShape(QFrame.NoFrame)
        self.debug_text.setFont(QFont(FONT_FAMILY, FONT_SIZE_DEBUG))
        self.debug_text.setWordWrapMode(QTextOption.NoWrap)
        dc_lay.addWidget(self.debug_text, 1)

        # Placement (session | sep | joueur | sep | tours | sep | debug)
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

        # Pas de stretch sur les colonnes séparateurs
        for col in (1, 3, 5):
            self.center_lay.setColumnStretch(col, 0)

        root.addWidget(center, 1)

        # --- LOGS -------------------------------------------------------
        self._sep_logs = _hsep(central)
        self._seps.append(self._sep_logs)
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

        # --- MENU -------------------------------------------------------
        self._build_menubar()

        # Appliquer visibilité initiale de la colonne Debug
        self._apply_debug_visibility(initial=True)

        # Timer pour pomper la queue (équivalent de .after(16, ...))
        self._event_queue = None
        self._queue_timer = QTimer(self._win)
        self._queue_timer.setInterval(16)
        self._queue_timer.timeout.connect(self._pump_event_queue)

        # Applique le thème au démarrage
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
        fg = (self._colors["control_fg"] if getattr(self, "_colors", None) else LIGHT_CONTROL_FG) if en else "#888888"
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

        # ---- Thème ----
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
        """Choix utilisateur via le menu."""
        self._theme.set_mode(mode)
        self._apply_theme(self._theme.colors())

    def _apply_theme(self, c: dict):
        """Applique les couleurs du thème à tous les widgets concernés."""
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

        # Bannière
        self._banner.setStyleSheet(f"QWidget{{background:{c['banner_bg']};}}")
        self.banner_label.setStyleSheet(f"QLabel{{color:{c['banner_text']};}}")

        # Boutons secondaires (même style pour les 2)
        btn_ss = (
            "QPushButton{"
            f"background:{c['bg_main']};"
            "border:none;"
            f"color:{c['text']};"
            "}"
            "QPushButton:hover{"
            f"background:{c['bg_secondary']};"
            "}"
        )
        self.edit_players_btn.setStyleSheet(btn_ss)
        self.debug_toggle_btn.setStyleSheet(btn_ss)

        # Zones de texte
        self.laps_text.setStyleSheet(f"QPlainTextEdit{{background:{c['bg_main']}; color:{c['text']};}}")
        self.debug_text.setStyleSheet(f"QPlainTextEdit{{background:{c['debug_bg']}; color:{c['text']};}}")
        self.log_text.setStyleSheet(f"QTextEdit{{background:{c['log_bg']}; color:{c['text']};}}")

        # Séparateurs (H+V)
        for sep in self._seps:
            sep.setStyleSheet(f"QFrame{{background:{c['separator']};}}")

        # Combobox joueur: garder l'état enabled/disabled
        self.set_player_menu_state(self.player_combo.isEnabled())

        # Carrés pneus
        for sq in self._tire_squares:
            sq.setStyleSheet(
                "QWidget{"
                f"background:{c['tire_bg']};"
                f"border:1px solid {c['tire_border']};"
                f"border-radius:{TIRE_SQUARE_RADIUS}px;"
                "}"
            )
            lab = sq.findChild(QLabel)
            if lab:
                lab.setStyleSheet(f"QLabel{{background:transparent; color:{c['tire_text']};}}")

    def _on_window_state_for_chrome(self, *args):
        self._apply_theme(self._colors or self._theme.colors())

    def _on_system_color_scheme_changed(self):
        """Appelé si Windows bascule clair/sombre et que le mode est 'Système'."""
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
            icon = None
            if os.path.isfile(ICON_PATH):
                icon = QIcon(ICON_PATH)
            elif os.name == "nt" and os.path.isfile(WINDOWS_ICON_PATH):
                icon = QIcon(WINDOWS_ICON_PATH)

            if icon is not None and not icon.isNull():
                self._win.setWindowIcon(icon)
                if hasattr(self, "_title_bar"):
                    self._title_bar.set_icon(icon)
        except Exception:
            pass
