from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication

from .constants import (
    LIGHT_WINDOW_BORDER_COLOR, LIGHT_BG_MAIN, LIGHT_TEXT, LIGHT_BG_SECONDARY, LIGHT_MENU_ITEM_BG,
    LIGHT_BUTTON_BG, LIGHT_BUTTON_BORDER_COLOR,
    LIGHT_SCROLLBAR_TRACK, LIGHT_SCROLLBAR_BORDER,
    LIGHT_SCROLLBAR_HANDLE_START, LIGHT_SCROLLBAR_HANDLE_END,
    LIGHT_SCROLLBAR_HANDLE_HOVER_START, LIGHT_SCROLLBAR_HANDLE_HOVER_END,
    LIGHT_BANNER_BG, LIGHT_BANNER_TEXT, LIGHT_DEBUG_BG, LIGHT_LOG_BG,
    LIGHT_SEPARATOR, LIGHT_CONTROL_FG, LIGHT_TIRE_BG, LIGHT_TIRE_BORDER, LIGHT_TIRE_TEXT,
    LIGHT_TITLE_BG, LIGHT_TITLE_FG, LIGHT_TITLE_BTN_HOVER, LIGHT_TITLE_BTN_PRESSED,
    LIGHT_TITLE_BTN_CLOSE_HOVER, LIGHT_TITLE_BTN_CLOSE_PRESSED, LIGHT_INTERACTIVE_HOVER_BG,
    LIGHT_LAST_LAPS_HOVER_BG,
    LIGHT_ACTION_ICON_COLOR,

    DARK_WINDOW_BORDER_COLOR, DARK_BG_MAIN, DARK_TEXT, DARK_BG_SECONDARY, DARK_MENU_ITEM_BG,
    DARK_BUTTON_BG, DARK_BUTTON_BORDER_COLOR,
    DARK_SCROLLBAR_TRACK, DARK_SCROLLBAR_BORDER,
    DARK_SCROLLBAR_HANDLE_START, DARK_SCROLLBAR_HANDLE_END,
    DARK_SCROLLBAR_HANDLE_HOVER_START, DARK_SCROLLBAR_HANDLE_HOVER_END,
    DARK_BANNER_BG, DARK_BANNER_TEXT, DARK_DEBUG_BG, DARK_LOG_BG,
    DARK_SEPARATOR, DARK_CONTROL_FG, DARK_TIRE_BG, DARK_TIRE_BORDER, DARK_TIRE_TEXT,
    DARK_TITLE_BG, DARK_TITLE_FG, DARK_TITLE_BTN_HOVER, DARK_TITLE_BTN_PRESSED,
    DARK_TITLE_BTN_CLOSE_HOVER, DARK_TITLE_BTN_CLOSE_PRESSED, DARK_INTERACTIVE_HOVER_BG,
    DARK_LAST_LAPS_HOVER_BG,
    DARK_ACTION_ICON_COLOR,
)


class ThemeManager:
    """
    Gestion du thème clair/sombre/système.
    Stocke le choix via QSettings.
    """
    SETTINGS_ORG = "iRacingTracker"
    SETTINGS_APP = "iRacingTracker"
    SETTINGS_KEY = "theme.mode"   # "system" | "light" | "dark"

    def __init__(self, app):
        self.app = app
        self.settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        self.mode = self.settings.value(self.SETTINGS_KEY, "system")
        # Écoute (si dispo) du changement système
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
        """Dictionnaire de couleurs pour le schéma effectif."""
        scheme = self.effective_scheme()
        if scheme == "dark":
            return dict(
                window_border=DARK_WINDOW_BORDER_COLOR,
                bg_main=DARK_BG_MAIN,
                text=DARK_TEXT,
                bg_secondary=DARK_BG_SECONDARY,
                menu_item_bg=DARK_MENU_ITEM_BG,
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
                interactive_hover=DARK_INTERACTIVE_HOVER_BG,
                last_laps_hover=DARK_LAST_LAPS_HOVER_BG,
                button_bg=DARK_BUTTON_BG,
                button_border_color=DARK_BUTTON_BORDER_COLOR,
                action_icon_color=DARK_ACTION_ICON_COLOR,
                scrollbar_track=DARK_SCROLLBAR_TRACK,
                scrollbar_border=DARK_SCROLLBAR_BORDER,
                scrollbar_handle_start=DARK_SCROLLBAR_HANDLE_START,
                scrollbar_handle_end=DARK_SCROLLBAR_HANDLE_END,
                scrollbar_handle_hover_start=DARK_SCROLLBAR_HANDLE_HOVER_START,
                scrollbar_handle_hover_end=DARK_SCROLLBAR_HANDLE_HOVER_END,
            )
        else:
            return dict(
                window_border=LIGHT_WINDOW_BORDER_COLOR,
                bg_main=LIGHT_BG_MAIN,
                text=LIGHT_TEXT,
                bg_secondary=LIGHT_BG_SECONDARY,
                menu_item_bg=LIGHT_MENU_ITEM_BG,
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
                interactive_hover=LIGHT_INTERACTIVE_HOVER_BG,
                last_laps_hover=LIGHT_LAST_LAPS_HOVER_BG,
                button_bg=LIGHT_BUTTON_BG,
                button_border_color=LIGHT_BUTTON_BORDER_COLOR,
                action_icon_color=LIGHT_ACTION_ICON_COLOR,
                scrollbar_track=LIGHT_SCROLLBAR_TRACK,
                scrollbar_border=LIGHT_SCROLLBAR_BORDER,
                scrollbar_handle_start=LIGHT_SCROLLBAR_HANDLE_START,
                scrollbar_handle_end=LIGHT_SCROLLBAR_HANDLE_END,
                scrollbar_handle_hover_start=LIGHT_SCROLLBAR_HANDLE_HOVER_START,
                scrollbar_handle_hover_end=LIGHT_SCROLLBAR_HANDLE_HOVER_END,
            )

    # ---------- Interne ----------
    def _system_scheme(self) -> str:
        try:
            scheme = QGuiApplication.styleHints().colorScheme()
            s = str(scheme)
            return "dark" if "Dark" in s else "light"
        except Exception:
            return "light"

    def _on_system_scheme_changed(self, *_):
        # Le TrackerUI réapplique le thème si mode == "system"
        pass
