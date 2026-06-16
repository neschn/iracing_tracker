################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui/app.py                                                                          #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Façade de l'interface PySide6 : assemble les panneaux et orchestre thème et événements.        #
################################################################################################################

import os
import sys
import ctypes
import queue as _q

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QGridLayout, QMenu
)
from PySide6.QtGui import QAction, QActionGroup

from .constants import (
    WINDOWS_ICON_PATH,
    WINDOW_TITLE, WINDOW_GEOMETRY, MIN_WIDTH, MIN_HEIGHT,
    WINDOW_BORDER_RADIUS, WINDOW_BORDER_WIDTH,
    FONT_FAMILY, FONT_SIZE_BANNER,
    BANNER_HEIGHT,
    BASE_MARGIN,
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
from .session_times_panel import SessionTimesPanel
from .debug_panel import DebugPanel
from .logs_panel import LogsPanel
from .players_dialog import PlayersDialog


if os.name == "nt":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Nico.iRacingTracker")
    except Exception:
        pass


#--------------------------------------------------------------------------------------------------------------#
# Façade de l'UI : assemble la fenêtre et les panneaux, orchestre le thème et les événements worker → UI.      #
#--------------------------------------------------------------------------------------------------------------#
class TrackerUI:

    #--------------------------------------------------------------------------------------------------------------#
    # Assemble la fenêtre (barre de titre, bannière, panneaux, logs), le menu, le thème et le timer.               #
    #--------------------------------------------------------------------------------------------------------------#
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
        self._action_icon_px = 18
        self.debug_visible = _BoolVarCompat(True)

        self.on_player_change = on_player_change
        self.on_debug_toggle = on_debug_toggle

        # Root
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

        # Barre de titre + séparateur
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

        # Bannière + séparateur
        banner = QWidget()
        self._banner = banner
        if BANNER_HEIGHT is not None:
            banner.setFixedHeight(BANNER_HEIGHT)
        b_lay = QVBoxLayout(banner)
        b_lay.setContentsMargins(BASE_MARGIN, BASE_MARGIN, BASE_MARGIN, BASE_MARGIN)
        self.banner_label = QLabel("")
        self.banner_label.setAlignment(Qt.AlignCenter)
        self.banner_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_BANNER, QFont.Bold))
        b_lay.addWidget(self.banner_label)
        root.addWidget(banner)
        self._banner_manager = None
        self._sep_banner = _hsep(central)
        self._seps.append(self._sep_banner)
        root.addWidget(self._sep_banner)

        # Zone centrale (panneaux)
        center = QWidget()
        self.center_lay = QGridLayout(center)
        self.center_lay.setContentsMargins(0, 0, 0, 0)
        self.center_lay.setHorizontalSpacing(0)
        self.center_lay.setVerticalSpacing(8)

        self.session_panel = SessionPanel(action_icon_px=self._action_icon_px, parent=center)
        self.player_panel = PlayerPanel(
            players, self._on_player_changed,
            on_edit_players=self._on_edit_players_clicked,
            action_icon_px=self._action_icon_px, parent=center,
        )
        self.session_times_panel = SessionTimesPanel(center)
        self.debug_panel = DebugPanel(self._set_debug_visible, action_icon_px=self._action_icon_px, parent=center)

        self.center_lay.addWidget(self.session_panel, 0, 0)
        self._sep_1 = _vsep(center)
        self._seps.append(self._sep_1)
        self.center_lay.addWidget(self._sep_1, 0, 1)
        self.center_lay.addWidget(self.player_panel, 0, 2)
        self._sep_2 = _vsep(center)
        self._seps.append(self._sep_2)
        self.center_lay.addWidget(self._sep_2, 0, 3)
        self.center_lay.addWidget(self.session_times_panel, 0, 4)
        self._sep_debug = _vsep(center)
        self._seps.append(self._sep_debug)
        self.center_lay.addWidget(self._sep_debug, 0, 5)
        self.center_lay.addWidget(self.debug_panel, 0, 6)
        for col in (0, 2, 4, 6):
            self.center_lay.setColumnStretch(col, 1)
        for col in (1, 3, 5):
            self.center_lay.setColumnStretch(col, 0)
        root.addWidget(center, 1)

        # Logs
        self._sep_logs = _hsep(central)
        self._seps.append(self._sep_logs)
        root.addWidget(self._sep_logs)
        self.logs_panel = LogsPanel(central)
        root.addWidget(self.logs_panel, 0)

        # Menu + thème + timers
        self._build_menubar()
        self._apply_debug_visibility()
        self._event_queue = None
        self._queue_timer = QTimer(self._win)
        self._queue_timer.setInterval(16)
        self._queue_timer.timeout.connect(self._pump_event_queue)
        self._apply_theme(self._theme.colors())
        try:
            self._app.styleHints().colorSchemeChanged.connect(self._on_system_color_scheme_changed)
        except Exception:
            pass
        # Liste des derniers tours vierge au démarrage

    # ---- API publique (consommée par main.py) ----

    #--------------------------------------------------------------------------------------------------------------#
    # Affiche la fenêtre et lance la boucle d'événements Qt (bloquant).                                            #
    #--------------------------------------------------------------------------------------------------------------#
    def mainloop(self):
        self._win.show()
        return self._app.exec()

    #--------------------------------------------------------------------------------------------------------------#
    # Définit le callback appelé lors d'un changement de joueur.                                                   #
    #--------------------------------------------------------------------------------------------------------------#
    def set_on_player_change(self, cb):
        self.on_player_change = cb

    #--------------------------------------------------------------------------------------------------------------#
    # Définit le callback appelé lors de l'activation/désactivation du debug.                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def set_on_debug_toggle(self, cb):
        self.on_debug_toggle = cb

    #--------------------------------------------------------------------------------------------------------------#
    # Associe la queue d'événements worker → UI et démarre le timer de vidage.                                     #
    #--------------------------------------------------------------------------------------------------------------#
    def bind_event_queue(self, q):
        self._event_queue = q
        self._queue_timer.start()

    # ---- Méthodes d'update (délèguent aux panneaux) ----

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour le circuit et la voiture affichés.                                                                #
    #--------------------------------------------------------------------------------------------------------------#
    def update_context(self, track: str, car: str, track_id=None, car_id=None):
        self.session_panel.set_context(track, car, track_id, car_id)

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour le record personnel affiché.                                                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def update_player_personal_record(self, best_time_str: str):
        self.player_panel.set_personal_record(best_time_str)

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour le classement Top 3 affiché.                                                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def _update_ranking_display(self, ranking: list):
        self.session_panel.set_ranking(ranking)

    #--------------------------------------------------------------------------------------------------------------#
    # Affiche un message de bannière selon son type (attente / record perso / record absolu / clear).              #
    #--------------------------------------------------------------------------------------------------------------#
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

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour le temps du dernier tour affiché.                                                                 #
    #--------------------------------------------------------------------------------------------------------------#
    def update_current_lap_time(self, text: str):
        self.player_panel.set_current_lap(text)

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour le temps de session affiché.                                                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def update_session_time(self, seconds: int | float | None):
        self.session_panel.set_session_time(seconds)

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour la liste des temps de la session.                                                                 #
    #--------------------------------------------------------------------------------------------------------------#
    def update_session_times(self, entries):
        self.session_times_panel.set_items(entries)

    #--------------------------------------------------------------------------------------------------------------#
    # Alias de update_session_times (compat).                                                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def update_last_laps(self, entries):
        self.update_session_times(entries)

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour la zone de debug.                                                                                 #
    #--------------------------------------------------------------------------------------------------------------#
    def update_debug(self, data: dict):
        self.debug_panel.set_debug_data(data)

    #--------------------------------------------------------------------------------------------------------------#
    # Ajoute un message horodaté dans les logs.                                                                    #
    #--------------------------------------------------------------------------------------------------------------#
    def add_log(self, message: str):
        self.logs_panel.append_log(message)

    #--------------------------------------------------------------------------------------------------------------#
    # Active/désactive le sélecteur de joueur.                                                                     #
    #--------------------------------------------------------------------------------------------------------------#
    def set_player_menu_state(self, enabled: bool):
        self.player_panel.set_menu_state(enabled)

    #--------------------------------------------------------------------------------------------------------------#
    # Affiche un texte brut dans la bannière.                                                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def set_banner(self, text: str = ""):
        self.banner_label.setText(text or "")

    # ---- Interne ----

    #--------------------------------------------------------------------------------------------------------------#
    # Propage le changement de joueur au callback fourni par main.py.                                              #
    #--------------------------------------------------------------------------------------------------------------#
    def _on_player_changed(self, name: str):
        if callable(self.on_player_change):
            try:
                self.on_player_change(name)
            except Exception:
                pass

    #--------------------------------------------------------------------------------------------------------------#
    # Ouvre la fenêtre d'édition des joueurs puis recharge la liste du sélecteur.                                  #
    #--------------------------------------------------------------------------------------------------------------#
    def _on_edit_players_clicked(self):
        try:
            dlg = PlayersDialog(self._win)
            # Appliquer le même thème + police que la fenêtre principale
            try:
                colors = self._colors or self._theme.colors()
                dlg.apply_palette(colors)
            except Exception:
                pass
            res = dlg.exec()
            # Recharger la liste des joueurs à la fermeture (le panneau gère la sélection)
            if res is not None:
                from iracing_tracker.data_store import DataStore
                players = DataStore.load_players()
                self.player_panel.set_players(players)
        except Exception as e:
            try:
                self.add_log(f"Erreur édition joueurs: {e}")
            except Exception:
                pass

    #--------------------------------------------------------------------------------------------------------------#
    # Construit la barre de menus (Fichier, Édition, Affichage avec Debug et Thème).                               #
    #--------------------------------------------------------------------------------------------------------------#
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
        self._act_debug = QAction("Debug", view_menu, checkable=True)
        self._act_debug.setChecked(self.debug_visible.get())
        self._act_debug.triggered.connect(self._toggle_debug_action)
        view_menu.addAction(self._act_debug)

        theme_menu = QMenu("Thème", menubar)
        group = QActionGroup(self._win)
        group.setExclusive(True)
        self._act_theme_system = QAction("Système", group, checkable=True)
        self._act_theme_light = QAction("Clair", group, checkable=True)
        self._act_theme_dark = QAction("Sombre", group, checkable=True)
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

    #--------------------------------------------------------------------------------------------------------------#
    # Change le mode de thème puis le réapplique.                                                                  #
    #--------------------------------------------------------------------------------------------------------------#
    def _on_theme_changed(self, mode: str):
        self._theme.set_mode(mode)
        self._apply_theme(self._theme.colors())

    #--------------------------------------------------------------------------------------------------------------#
    # Applique le thème : chrome de la fenêtre (bordures, bannière), puis délégation à chaque panneau.             #
    #--------------------------------------------------------------------------------------------------------------#
    def _apply_theme(self, c: dict):
        self._colors = c
        self._title_bar.apply_colors(c)
        r = 0 if self._win.isMaximized() else WINDOW_BORDER_RADIUS
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
        if not hasattr(self, "_banner_manager") or self._banner_manager is None:
            self._banner_manager = BannerManager(self._banner, self.banner_label, c)
        else:
            self._banner_manager.update_theme(c)

        # Chaque panneau applique lui-même le thème à ses widgets internes
        self.session_panel.apply_palette(c)
        self.player_panel.apply_palette(c)
        self.session_times_panel.apply_palette(c)
        self.debug_panel.apply_palette(c)
        self.logs_panel.apply_palette(c)

        # Séparateurs appartenant à la fenêtre (titre, bannière, colonnes, logs)
        for sep in self._seps:
            try:
                sep.setStyleSheet(f"QFrame{{background:{c['separator']};}}")
            except Exception:
                pass

    #--------------------------------------------------------------------------------------------------------------#
    # Réapplique le thème au changement d'état de la fenêtre (bordures/coins selon maximisé).                      #
    #--------------------------------------------------------------------------------------------------------------#
    def _on_window_state_for_chrome(self, *_):
        self._apply_theme(self._colors or self._theme.colors())

    #--------------------------------------------------------------------------------------------------------------#
    # Réapplique le thème si le mode système est actif et que le schéma OS change.                                 #
    #--------------------------------------------------------------------------------------------------------------#
    def _on_system_color_scheme_changed(self):
        if self._theme.get_mode() == "system":
            self._apply_theme(self._theme.colors())

    #--------------------------------------------------------------------------------------------------------------#
    # Bascule l'affichage de la zone debug depuis l'action du menu.                                                #
    #--------------------------------------------------------------------------------------------------------------#
    def _toggle_debug_action(self, checked: bool):
        self.debug_visible.set(bool(checked))
        self._apply_debug_visibility()
        if callable(self.on_debug_toggle):
            try:
                self.on_debug_toggle(bool(checked))
            except Exception:
                pass

    #--------------------------------------------------------------------------------------------------------------#
    # Définit la visibilité de la zone debug (depuis le bouton du panneau) et synchronise le menu.                 #
    #--------------------------------------------------------------------------------------------------------------#
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

    #--------------------------------------------------------------------------------------------------------------#
    # Affiche/masque la zone debug et ajuste l'étirement des colonnes de la grille.                                #
    #--------------------------------------------------------------------------------------------------------------#
    def _apply_debug_visibility(self):
        vis = self.debug_visible.get()
        self.debug_panel.setVisible(vis)
        self._sep_debug.setVisible(vis)
        self.debug_panel.update_toggle_tooltip(vis)
        if vis:
            for col in (0, 2, 4, 6):
                self.center_lay.setColumnStretch(col, 1)
        else:
            for col in (0, 2, 4):
                self.center_lay.setColumnStretch(col, 1)
            self.center_lay.setColumnStretch(6, 0)

    #--------------------------------------------------------------------------------------------------------------#
    # Vide la queue d'événements worker → UI et dispatche chaque message vers la bonne méthode.                    #
    #--------------------------------------------------------------------------------------------------------------#
    def _pump_event_queue(self):
        if self._event_queue is None:
            return
        try:
            while True:
                name, payload = self._event_queue.get_nowait()
                payload = payload or {}
                if name == "debug":
                    self.update_debug(payload)
                elif name == "session_time":
                    self.update_session_time(payload.get("seconds"))
                elif name == "context":
                    self.update_context(
                        payload.get("track", "---"),
                        payload.get("car", "---"),
                        payload.get("track_id"),
                        payload.get("car_id"),
                    )
                elif name == "player_menu_state":
                    self.set_player_menu_state(payload.get("enabled", False))
                elif name == "log":
                    self.add_log(payload.get("message", ""))
                elif name == "player_best":
                    self.update_player_personal_record(payload.get("text", "---"))
                elif name == "ranking":
                    self._update_ranking_display(payload.get("ranking", []))
                elif name == "banner":
                    if "type" in payload:
                        self._handle_banner_message(payload.get("type", ""))
                    else:
                        self.set_banner(payload.get("text", ""))
                elif name == "current_lap":
                    self.update_current_lap_time(payload.get("text", "---"))
                elif name == "session_times":
                    entries = payload.get("entries") or payload.get("lines") or payload.get("text")
                    self.update_session_times(entries or [])
                elif name == "last_laps":
                    entries = payload.get("entries") or payload.get("lines") or payload.get("text")
                    self.update_session_times(entries or [])
        except _q.Empty:
            pass
        except Exception as e:
            try:
                self.add_log(f"UI error: {e}")
            except Exception:
                pass

    #--------------------------------------------------------------------------------------------------------------#
    # Charge et applique l'icône de la fenêtre (et de la barre de titre).                                          #
    #--------------------------------------------------------------------------------------------------------------#
    def _apply_window_icon(self):
        try:
            if os.path.isfile(WINDOWS_ICON_PATH):
                icon = QIcon(WINDOWS_ICON_PATH)
                self._app.setWindowIcon(icon)
                self._win.setWindowIcon(icon)
                if hasattr(self, "_title_bar"):
                    self._title_bar.set_icon(icon)
        except Exception:
            pass
