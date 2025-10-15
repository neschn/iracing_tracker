from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QWidget, QMenuBar, QSizePolicy, QLabel, QHBoxLayout, QToolButton, QStyle, QMenu
)
from PySide6.QtGui import QAction, QActionGroup

from .platform import IS_WINDOWS, HTCLIENT, HTCAPTION
from .constants import (
    FONT_FAMILY,
)

class CustomTitleBar(QWidget):
    """Barre de titre personnalisée avec menu intégré (style VS Code)."""

    HEIGHT = 36

    def __init__(self, window):
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

    # ---- API ----
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
        menu_item_bg = colors["menu_item_bg"]
        separator = colors["separator"]

        style = (
            f"#CustomTitleBar{{background:{bg};}}"
            f"#CustomTitleBar QLabel{{color:{fg}; font-family:{FONT_FAMILY};}}"
            f"#CustomTitleBar QMenuBar{{background:{menu_item_bg}; color:{fg}; border:0; padding:0;}}"
            f"#CustomTitleBar QMenuBar::item{{background:{menu_item_bg}; color:{fg}; padding:3px 12px; margin:0 2px; border-radius:4px;}}"
            f"#CustomTitleBar QMenuBar::item:selected{{background:{hover};}}"
            f"#CustomTitleBar QMenu{{background:{menu_item_bg}; color:{fg}; border:1px solid {separator};}}"
            f"#CustomTitleBar QMenu::item{{background:{menu_item_bg}; color:{fg}; padding:4px 16px;}}"
            f"#CustomTitleBar QMenu::item:selected{{background:{hover}; color:{fg};}}"
            f"#CustomTitleBar QToolButton{{background:transparent; border:none; color:{fg};}}"
            f"#CustomTitleBar QToolButton:hover{{background:{hover};}}"
            f"#CustomTitleBar QToolButton:pressed{{background:{pressed};}}"
            f"#CustomTitleBar QToolButton#CloseButton:hover{{background:{close_hover}; color:#ffffff;}}"
            f"#CustomTitleBar QToolButton#CloseButton:pressed{{background:{close_pressed}; color:#ffffff;}}"
        )
        self.setStyleSheet(style)

    def on_window_state_changed(self, state):
        self._update_max_button_icon()
        if state & Qt.WindowMaximized:
            self._btn_max.setToolTip("Restaurer")
        else:
            self._btn_max.setToolTip("Agrandir")

    def hit_test(self, pos: QPoint):
        """Renvoie un code HT* si la souris est dans la zone draggable."""
        if not self.rect().contains(pos):
            return None
        if self._buttons_container.geometry().contains(pos):
            return HTCLIENT
        if self._menu_bar.geometry().contains(pos):
            return HTCLIENT
        return HTCAPTION

    # ---- Interne ----
    def _make_button(self, standard_icon, tooltip: str) -> QToolButton:
        btn = QToolButton(self)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.ArrowCursor)
        btn.setIcon(self.style().standardIcon(standard_icon))
        btn.setIconSize(QSize(self.style().pixelMetric(QStyle.PM_SmallIconSize),
                      self.style().pixelMetric(QStyle.PM_SmallIconSize)))
        btn.setAutoRaise(False)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setFixedSize(46, self.HEIGHT)
        return btn

    def _toggle_max_restore(self):
        if self._win.isMaximized():
            self._win.restore_normal_geometry()
        else:
            self._win.showMaximized()

    def _update_max_button_icon(self):
        icon_role = QStyle.SP_TitleBarNormalButton if self._win.isMaximized() else QStyle.SP_TitleBarMaxButton
        self._btn_max.setIcon(self.style().standardIcon(icon_role))
