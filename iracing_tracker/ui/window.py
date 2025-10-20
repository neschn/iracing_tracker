# ui/window.py — Windows only
# QMainWindow frameless avec redimensionnement aux bords/cornes, coins arrondis,
# double-clic titre pour max/restore, et "drag depuis maximisé".
# Comportement identique à la version multi‑OS précédente, mais sans branches non‑Windows.

import ctypes
from ctypes import wintypes

from PySide6.QtCore import Qt, QTimer, QPoint, Signal, QEvent
from PySide6.QtGui import QGuiApplication, QCursor
from PySide6.QtWidgets import QMainWindow

from .constants import WINDOW_BORDER_RADIUS, RESIZE_BORDER_THICKNESS
from .platform import (
    # Hit-test codes
    HTCLIENT, HTCAPTION, HTLEFT, HTRIGHT, HTTOP, HTTOPLEFT, HTTOPRIGHT, HTBOTTOM, HTBOTTOMLEFT, HTBOTTOMRIGHT,
    # Messages Windows
    WM_NCHITTEST, WM_GETMINMAXINFO, WM_NCLBUTTONDOWN, WM_NCLBUTTONDBLCLK, WM_MOUSEMOVE, WM_LBUTTONUP, WM_LBUTTONDOWN,
    WM_NCMOUSEMOVE, WM_SYSCOMMAND, WM_SETCURSOR, SC_SIZE,
    # Directions de redimensionnement
    WMSZ_LEFT, WMSZ_RIGHT, WMSZ_TOP, WMSZ_TOPLEFT, WMSZ_TOPRIGHT, WMSZ_BOTTOM, WMSZ_BOTTOMLEFT, WMSZ_BOTTOMRIGHT,
    # Metrics / monitor
    SM_CXDRAG, SM_CYDRAG, MONITOR_DEFAULTTONEAREST,
    # Cursors
    IDC_ARROW, IDC_SIZENWSE, IDC_SIZENESW, IDC_SIZEWE, IDC_SIZENS,
    # Structures Win32
    MINMAXINFO, MONITORINFO,
    
)


class TrackerMainWindow(QMainWindow):
    """
    QMainWindow frameless (Windows) avec :
      - Redimensionnement via bords/cornes (WM_NCHITTEST + WM_SYSCOMMAND/SC_SIZE),
      - Coins arrondis (Rgn),
      - Double-clic dans la barre de titre -> Max/Restore,
      - Drag depuis l'état maximisé (détache en Normal puis relaye un drag natif),
      - Gestion correcte Minimize/Restore (taskbar) et rappel de la géométrie "normale".
    """

    window_state_changed = Signal(Qt.WindowStates)

    def __init__(self):
        super().__init__()

        self._border_width = RESIZE_BORDER_THICKNESS
        self._title_bar_widget = None

        # Flags pour un bon comportement taskbar (minimize/maximize)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Window
            | Qt.WindowSystemMenuHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
        )

        # Drag depuis maximisé : seuils système Windows
        self._drag_from_max = False
        self._drag_start_global = QPoint()
        self._drag_anchor_ratio = 0.5
        self._drag_threshold_x = max(1, ctypes.windll.user32.GetSystemMetrics(SM_CXDRAG))
        self._drag_threshold_y = max(1, ctypes.windll.user32.GetSystemMetrics(SM_CYDRAG))

        # Suivi d'état fenêtre
        self._last_window_state = Qt.WindowNoState
        self._was_maximized_before_minimize = False
        self._saved_normal_geom = None
        self._suppress_next_save_normal = False
        self._last_hit_code = None

    # ---------------- API ----------------
    def set_title_bar_widget(self, widget):
        """Widget 'title bar' custom qui fournit hit_test(localPos)->HT*."""
        self._title_bar_widget = widget

    def restore_normal_geometry(self):
        """Restaure la fenêtre à la dernière géométrie 'normale' connue."""
        self.showNormal()
        try:
            if self._saved_normal_geom and self._saved_normal_geom.isValid():
                self.setGeometry(self._saved_normal_geom)
        except Exception:
            pass

    # -------------- Événements Qt --------------
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

            # Entrée en maximisé -> mémoriser la géométrie "normale"
            if (new_state & Qt.WindowMaximized) and not (prev & Qt.WindowMaximized):
                if self._suppress_next_save_normal:
                    self._suppress_next_save_normal = False
                elif not (prev & Qt.WindowMinimized):
                    try:
                        candidate = self.normalGeometry()
                    except Exception:
                        candidate = self.geometry()
                    try:
                        if candidate and candidate.isValid() and not self._is_geometry_maximized_like(candidate):
                            self._saved_normal_geom = candidate
                    except Exception:
                        pass

            # On passe en minimisé -> mémoriser si on était maximisé
            if new_state & Qt.WindowMinimized:
                self._was_maximized_before_minimize = bool(prev & Qt.WindowMaximized)

            # Restore depuis minimisé -> re-maximiser si nécessaire, sans écraser la geom "normale"
            if (prev & Qt.WindowMinimized) and not (new_state & Qt.WindowMinimized):
                if self._was_maximized_before_minimize and not (new_state & Qt.WindowMaximized):
                    self._suppress_next_save_normal = True
                    QTimer.singleShot(0, self.showMaximized)
                self._was_maximized_before_minimize = False

            self.window_state_changed.emit(new_state)
            try:
                self._update_corner_region()
            except Exception:
                pass
            self._last_window_state = new_state

        super().changeEvent(event)

        # -------------- Helpers --------------
    def _is_geometry_maximized_like(self, g) -> bool:
        """Retourne True si 'g' a (quasi) la taille de la zone de travail (maximisé)."""
        handle = self.windowHandle() if hasattr(self, "windowHandle") else None
        screen = None
        if handle:
            try:
                screen = handle.screen()
            except Exception:
                screen = None
        if not screen:
            try:
                screen = QGuiApplication.primaryScreen()
            except Exception:
                screen = None
        if not screen:
            return False
        try:
            ag = screen.availableGeometry()
            return (abs(g.width() - ag.width()) <= 2 and abs(g.height() - ag.height()) <= 2)
        except Exception:
            return False

    def _update_corner_region(self):
        """Applique un RGN arrondi selon WINDOW_BORDER_RADIUS (0 si maximisé)."""
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
        """Fabrique un LPARAM(x,y) (low: x, high: y) pour SendMessage."""
        return ctypes.c_uint32(((pt.y() & 0xFFFF) << 16) | (pt.x() & 0xFFFF)).value

    # -------------- Natif Windows --------------
    def nativeEvent(self, eventType, message):
        # Nous ne gérons que les messages Windows génériques
        if eventType not in ("windows_generic_MSG", b"windows_generic_MSG"):
            return super().nativeEvent(eventType, message)

        msg = wintypes.MSG.from_address(int(message))

        if msg.message == WM_NCHITTEST:
            result = self._handle_nc_hit_test(msg.lParam)
            if result is not None:
                self._last_hit_code = int(result)  # utile si on démarre le resize en zone client
                return True, result
            else:
                self._last_hit_code = None

        if msg.message == WM_GETMINMAXINFO:
            self._handle_get_min_max_info(msg.lParam)
            return True, 0

        if msg.message == WM_SETCURSOR:
            try:
                self._handle_set_cursor()
                return True, 1
            except Exception:
                pass

        # Double-clic dans la zone titre -> Max/Restore
        if msg.message == WM_NCLBUTTONDBLCLK and msg.wParam == HTCAPTION:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
            return True, 0

        # Prépare un drag depuis maximisé (ne restaure pas encore)
        if msg.message == WM_NCLBUTTONDOWN and msg.wParam == HTCAPTION and self.isMaximized():
            self._drag_from_max = True
            self._drag_start_global = self._unpack_lparam(msg.lParam)
            try:
                if self._title_bar_widget:
                    local = self._title_bar_widget.mapFromGlobal(self._drag_start_global)
                    bar_w = max(1, self._title_bar_widget.width())
                    self._drag_anchor_ratio = max(0.0, min(1.0, local.x() / bar_w))
                else:
                    self._drag_anchor_ratio = 0.5
            except Exception:
                self._drag_anchor_ratio = 0.5
            return False, 0

        # Démarre un redimensionnement manuel depuis la zone client si clic proche d'un bord
        if msg.message == WM_LBUTTONDOWN and not self.isMaximized():
            try:
                gp = QCursor.pos()
            except Exception:
                gp = None
            hit = self._hit_from_global_point(gp) if gp is not None else (self._last_hit_code or 0)
            wmsz = self._wmsz_from_hit(hit) if hit else 0
            if wmsz:
                try:
                    ctypes.windll.user32.ReleaseCapture()
                    ctypes.windll.user32.SendMessageW(int(self.winId()), WM_SYSCOMMAND, SC_SIZE + wmsz, 0)
                    return True, 0
                except Exception:
                    pass

        # Si on a bougé de plus que le seuil -> restaurer et relayer le drag natif
        if self._drag_from_max and self.isMaximized() and (msg.message in (WM_MOUSEMOVE, WM_NCMOUSEMOVE)):
            if msg.message == WM_MOUSEMOVE:
                client_pos = self._unpack_lparam(msg.lParam)
                global_pos = self.mapToGlobal(client_pos)
            else:  # WM_NCMOUSEMOVE
                global_pos = self._unpack_lparam(msg.lParam)

            dx = abs(global_pos.x() - self._drag_start_global.x())
            dy = abs(global_pos.y() - self._drag_start_global.y())
            if dx >= self._drag_threshold_x or dy >= self._drag_threshold_y:
                self.showNormal()
                new_x = int(global_pos.x() - self.width() * self._drag_anchor_ratio)
                new_y = max(0, global_pos.y() - (getattr(self._title_bar_widget, "HEIGHT", 20) // 2))
                self.move(new_x, new_y)

                ctypes.windll.user32.ReleaseCapture()
                ctypes.windll.user32.SendMessageW(
                    int(self.winId()), WM_NCLBUTTONDOWN, HTCAPTION, self._make_lparam_from_point(global_pos)
                )
                self._drag_from_max = False
                return True, 0

        # Bouton relâché -> on abandonne le "peut‑être drag"
        if msg.message == WM_LBUTTONUP and self._drag_from_max:
            self._drag_from_max = False
            return False, 0

        # Redimensionnement via non‑client down (au cas où Windows ne l'initie pas seul)
        if msg.message == WM_NCLBUTTONDOWN and not self.isMaximized():
            try:
                hit = int(msg.wParam)
            except Exception:
                hit = 0
            wmsz = self._wmsz_from_hit(hit) if hit else 0
            if wmsz:
                try:
                    ctypes.windll.user32.ReleaseCapture()
                    ctypes.windll.user32.SendMessageW(int(self.winId()), WM_SYSCOMMAND, SC_SIZE + wmsz, 0)
                    return True, 0
                except Exception:
                    pass

        return super().nativeEvent(eventType, message)

    # -------------- Handlers --------------
    def _handle_nc_hit_test(self, lparam):
        """Calcule le HT* pour le redimensionnement aux bords/cornes et la zone titre."""
        # En maximisé, seules les zones 'titre' (drag) s'appliquent
        if self.isMaximized():
            if self._title_bar_widget:
                global_pos = self._unpack_lparam(lparam)
                local = self._title_bar_widget.mapFromGlobal(global_pos)
                hit = self._title_bar_widget.hit_test(local)
                if hit is not None:
                    return hit
            return None

        # Sinon, on expose toutes les zones de resize
        global_pos = self._unpack_lparam(lparam)
        local = self.mapFromGlobal(global_pos)

        bw = self._border_width
        w = self.width()
        h = self.height()
        x = local.x()
        y = local.y()

        if x < 0 or y < 0 or x > w or y > h:
            return None

        on_left   = x <= bw
        on_right  = x >= w - bw
        on_top    = y <= bw
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
        """Contraint la taille min et renseigne la zone de travail (maximized)."""
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
        """Décode (x,y) d'un LPARAM vers un QPoint."""
        value = int(lparam) & 0xFFFFFFFF
        x = ctypes.c_short(value & 0xFFFF).value
        y = ctypes.c_short((value >> 16) & 0xFFFF).value
        return QPoint(x, y)

    def _wmsz_from_hit(self, hit: int) -> int:
        """Mappe un code HT* en direction WMSZ_* pour WM_SYSCOMMAND/SC_SIZE."""
        mapping = {
            HTLEFT: WMSZ_LEFT, HTRIGHT: WMSZ_RIGHT, HTTOP: WMSZ_TOP, HTTOPLEFT: WMSZ_TOPLEFT,
            HTTOPRIGHT: WMSZ_TOPRIGHT, HTBOTTOM: WMSZ_BOTTOM, HTBOTTOMLEFT: WMSZ_BOTTOMLEFT, HTBOTTOMRIGHT: WMSZ_BOTTOMRIGHT,
        }
        return mapping.get(hit, 0)

    def _hit_from_global_point(self, gp: QPoint) -> int:
        """Hit-test depuis une position *globale* (utile sur WM_LBUTTONDOWN en zone client)."""
        if self.isMaximized():
            return HTCLIENT
        local = self.mapFromGlobal(gp)
        x, y = local.x(), local.y()
        w, h = self.width(), self.height()
        if x < 0 or y < 0 or x > w or y > h:
            return HTCLIENT
        bw = self._border_width
        on_left   = x <= bw
        on_right  = x >= w - bw
        on_top    = y <= bw
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
        return HTCLIENT

    def _handle_set_cursor(self):
        """Affiche le curseur de redimensionnement approprié selon la position."""
        if self.isMaximized():
            ctypes.windll.user32.SetCursor(ctypes.windll.user32.LoadCursorW(None, IDC_ARROW))
            return

        gp = QCursor.pos()
        local = self.mapFromGlobal(gp)
        x, y = local.x(), local.y()
        w, h = self.width(), self.height()
        if x < 0 or y < 0 or x > w or y > h:
            ctypes.windll.user32.SetCursor(ctypes.windll.user32.LoadCursorW(None, IDC_ARROW))
            return

        bw = self._border_width
        on_left   = x <= bw
        on_right  = x >= w - bw
        on_top    = y <= bw
        on_bottom = y >= h - bw

        if (on_top and on_left) or (on_bottom and on_right):
            cursor_id = IDC_SIZENWSE
        elif (on_top and on_right) or (on_bottom and on_left):
            cursor_id = IDC_SIZENESW
        elif on_left or on_right:
            cursor_id = IDC_SIZEWE
        elif on_top or on_bottom:
            cursor_id = IDC_SIZENS
        else:
            cursor_id = IDC_ARROW

        ctypes.windll.user32.SetCursor(ctypes.windll.user32.LoadCursorW(None, cursor_id))
