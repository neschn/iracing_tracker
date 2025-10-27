################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui/players_dialog.py                                                               #
# Description : Boîtes de dialogue pour gérer les joueurs (liste, ajout, suppression).                         #
################################################################################################################

from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QPainter, QPixmap, QColor
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
    QWidget,
)

from .constants import (
    FONT_FAMILY,
    FONT_SIZE_LABELS,
    FONT_SIZE_BUTTON,
    PLAYER_NAME_MAX_LENGTH,
    BUTTON_BORDER_WIDTH,
    BUTTON_BORDER_RADIUS,
    BUTTON_PADDING,
    ICON_BUTTON_PADDING,
    ADD_ICON_PATH,
    DELETE_ICON_PATH,
)
from iracing_tracker.data_store import DataStore
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QSize, QRectF


class AddPlayerDialog(QDialog):
    """Boîte simple pour saisir un nouveau nom de joueur avec validation."""

    def __init__(self, existing: Iterable[str] | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau joueur")
        self.setModal(True)

        self._existing_lower = {str(x).strip().lower() for x in (existing or [])}
        self.result_name: str | None = None

        lay = QVBoxLayout(self)
        lbl = QLabel(f"Nom du joueur (max {PLAYER_NAME_MAX_LENGTH} caractères) :")
        lbl.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        lay.addWidget(lbl)

        self.name_edit = QLineEdit(self)
        self.name_edit.setMaxLength(int(PLAYER_NAME_MAX_LENGTH))
        self.name_edit.textChanged.connect(self._validate)
        lay.addWidget(self.name_edit)

        self.error_lbl = QLabel("")
        self.error_lbl.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        self.error_lbl.setStyleSheet("color:#c0392b;")
        self.error_lbl.setVisible(False)
        lay.addWidget(self.error_lbl)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        for b in btns.buttons():
            b.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

        self._validate()

    def _validate(self):
        text = (self.name_edit.text() or "").strip()
        error = None
        if not text:
            error = "Le nom ne peut pas être vide."
        elif len(text) > int(PLAYER_NAME_MAX_LENGTH):
            error = f"Maximum {PLAYER_NAME_MAX_LENGTH} caractères."
        elif text.lower() in self._existing_lower:
            error = "Ce joueur existe déjà."

        self.error_lbl.setVisible(bool(error))
        if error:
            self.error_lbl.setText(error)
        # Safer: disable via button box lookup
        for b in self.findChildren(QDialogButtonBox):
            try:
                b.button(QDialogButtonBox.Ok).setEnabled(error is None)
            except Exception:
                pass

    def _on_accept(self):
        text = (self.name_edit.text() or "").strip()
        if not text:
            return
        if text.lower() in self._existing_lower:
            return
        self.result_name = text
        self.accept()


class PlayersDialog(QDialog):
    """Fenêtre modale simple pour lister, ajouter et supprimer des joueurs."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Joueurs")
        self.setModal(True)
        self.modified = False  # Passe à True si ajout/suppression

        lay = QVBoxLayout(self)

        title = QLabel("Liste des joueurs")
        title.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS, QFont.Bold))
        lay.addWidget(title)

        self.list_widget = QListWidget(self)
        # Pas de sélection par défaut à l'ouverture
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        lay.addWidget(self.list_widget)

        btn_row = QWidget(self)
        h = QHBoxLayout(btn_row)
        h.setContentsMargins(0, 0, 0, 0)
        h.addStretch(1)
        self.add_btn = QPushButton("", self)
        self.add_btn.setProperty("variant", "icon")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setFixedSize(32, 32)
        self.add_btn.setIconSize(QSize(18, 18))
        self.add_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        self.del_btn = QPushButton("", self)
        self.del_btn.setProperty("variant", "icon")
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.setFixedSize(32, 32)
        self.del_btn.setIconSize(QSize(18, 18))
        self.del_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        self.del_btn.setEnabled(False)
        h.addWidget(self.add_btn)
        h.addWidget(self.del_btn)
        lay.addWidget(btn_row)

        # Chargement initial
        self._reload_players()

        # Connexions
        self.add_btn.clicked.connect(self._on_add)
        self.del_btn.clicked.connect(self._on_delete)
        self.list_widget.currentRowChanged.connect(self._update_buttons_state)
        self.list_widget.itemSelectionChanged.connect(self._update_buttons_state)

    # --- Helpers ---
    def _reload_players(self):
        self.list_widget.clear()
        players = DataStore.load_players()
        for name in players:
            self.list_widget.addItem(str(name))
        try:
            self.list_widget.setCurrentRow(-1)
        except Exception:
            pass
        try:
            self.list_widget.clearSelection()
        except Exception:
            pass
        self._update_buttons_state()

    def _current_player(self) -> str | None:
        item = self.list_widget.currentItem()
        return item.text() if item else None

    def _update_buttons_state(self, *_):
        self.del_btn.setEnabled(self.list_widget.currentRow() >= 0)

    # --- Actions ---
    def _on_add(self):
        existing = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        dlg = AddPlayerDialog(existing, self)
        # Appliquer le même thème à la boîte d'ajout si fourni via apply_palette()
        try:
            colors = getattr(self, "_colors", {})
            if hasattr(dlg, "apply_palette"):
                dlg.apply_palette(colors)
            try:
                dlg.name_edit.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
            except Exception:
                pass
        except Exception:
            pass
        if dlg.exec() == QDialog.Accepted and dlg.result_name:
            # Persiste et met à jour la liste
            players = DataStore.load_players()
            new_name = dlg.result_name
            if new_name.strip().lower() not in {p.strip().lower() for p in players}:
                players.append(new_name)
                DataStore.save_players(players)
                self.modified = True
                self._reload_players()

    def _on_delete(self):
        name = self._current_player()
        if not name:
            return
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmer la suppression")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(f"Supprimer le joueur « {name} » ?")
        msg.setInformativeText("Cette action supprimera aussi tous ses meilleurs tours.")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
        # Thème pour la boîte de confirmation
        try:
            c = getattr(self, "_colors", {}) or {}
            bg = c.get("bg_main"); fg = c.get("text")
            msg.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
            btn_css = (
                "QPushButton{"
                f"background:{c.get('button_bg', '#e5e5e5')};"
                f"color:{c.get('control_fg', fg or '#000')};"
                f"border:{BUTTON_BORDER_WIDTH}px solid {c.get('button_border_color', '#d0d0d0')};"
                f"border-radius:{BUTTON_BORDER_RADIUS}px;"
                f"padding:{BUTTON_PADDING};"
                "}"
                "QPushButton:hover{"
                f"background:{c.get('interactive_hover', '#dcdcdc')};"
                "}"
                "QPushButton:pressed{"
                f"background:{c.get('interactive_hover', '#dcdcdc')};"
                "}"
                "QPushButton:disabled{"
                f"background:{c.get('button_bg', '#e5e5e5')}; color:#888888;"
                "}"
            )
            msg.setStyleSheet(
                ("QDialog{" + (f"background:{bg};" if bg else "") + (f"color:{fg};" if fg else "") + "}")
                + (f"QLabel{{color:{fg}; font-family:{FONT_FAMILY}; font-size:{FONT_SIZE_LABELS}pt;}}" if fg else "")
                + btn_css
            )
        except Exception:
            pass
        ret = msg.exec()
        if ret == QMessageBox.Yes:
            DataStore.delete_player(name)
            self.modified = True
            self._reload_players()

    # --- Thème ---
    def apply_palette(self, colors: dict | None):
        self._colors = colors or {}
        c = self._colors
        # Base dialog colors
        bg = c.get("bg_main"); fg = c.get("text")
        base_style = (
            "QDialog{" + (f"background:{bg};" if bg else "") + (f"color:{fg};" if fg else "") + "}"
            + (f"QLabel{{color:{fg};}}" if fg else "")
        )
        # List widget style (selection visible, sans bordure de focus)
        list_text = c.get("text", fg or "#000000")
        hover_bg = c.get("interactive_hover", "#dcdcdc")
        list_bg = c.get("bg_secondary", bg) or "#f0f0f0"
        list_style = (
            f"QListWidget{{background:{list_bg}; color:{list_text}; border:1px solid transparent; outline:0;}}"
            f"QListWidget::item{{border:none; outline:0;}}"
            f"QListWidget::item:selected{{background:{hover_bg}; color:{list_text}; border:none; outline:0;}}"
            f"QListWidget::item:hover{{background:{hover_bg}; border:none; outline:0;}}"
            f"QListView::item:selected{{border:none; outline:0;}}"
            f"QListView::item:focus{{border:none; outline:0;}}"
        )
        # Scrollbar CSS (aligné avec la fenêtre principale)
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
        scroll_track = c.get("scrollbar_track", c.get("bg_secondary", list_bg))
        scroll_border = c.get("scrollbar_border", c.get("separator", "#b0b0b0"))
        handle_start = c.get("scrollbar_handle_start", c.get("separator", "#b0b0b0"))
        handle_end = c.get("scrollbar_handle_end", c.get("control_fg", "#7d7d7d"))
        handle_hover_start = c.get("scrollbar_handle_hover_start", c.get("control_fg", "#7d7d7d"))
        handle_hover_end = c.get("scrollbar_handle_hover_end", c.get("text", "#3a3a3a"))
        list_scroll_css = _scrollbar_css("QListWidget", scroll_track, scroll_border, handle_start, handle_end,
                                         handle_hover_start, handle_hover_end)
        # Button style
        btn_style = (
            "QPushButton{"
            f"background:{c.get('button_bg', '#e5e5e5')};"
            f"color:{c.get('control_fg', list_text)};"
            f"border:{BUTTON_BORDER_WIDTH}px solid {c.get('button_border_color', '#d0d0d0')};"
            f"border-radius:{BUTTON_BORDER_RADIUS}px;"
            f"padding:{BUTTON_PADDING};"
            "}"
            "QPushButton:hover{"
            f"background:{c.get('interactive_hover', '#dcdcdc')};"
            "}"
            "QPushButton:pressed{"
            f"background:{c.get('interactive_hover', '#dcdcdc')};"
            "}"
            "QPushButton:disabled{"
            f"background:{c.get('button_bg', '#e5e5e5')}; color:#888888;"
            "}"
        )
        icon_override = ("QPushButton[variant=\"icon\"]{" f"padding:{ICON_BUTTON_PADDING};" "min-width:28px;" "min-height:28px;" "}")
        self.setStyleSheet(base_style + list_style + btn_style + icon_override + list_scroll_css)
        # Fonts
        self.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        self.list_widget.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
        self.add_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        self.del_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        # Icônes add/delete avec couleur du thème
        try:
            size = 18
            color = c.get('action_icon_color', c.get('control_fg', '#000000'))
            add_icon = self._load_svg_icon(ADD_ICON_PATH, color, size)
            del_icon = self._load_svg_icon(DELETE_ICON_PATH, color, size)
            if not add_icon.isNull():
                self.add_btn.setIcon(add_icon)
                self.add_btn.setIconSize(QSize(size, size))
            if not del_icon.isNull():
                self.del_btn.setIcon(del_icon)
                self.del_btn.setIconSize(QSize(size, size))
        except Exception:
            pass

    @staticmethod
    def _load_svg_icon(path: str, color: str, size: int) -> QIcon:
        try:
            if not path:
                return QIcon()
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

# Extend AddPlayerDialog with theming support without changing constructor
def _addplayer_apply_palette(self, colors: dict | None):
    c = colors or {}
    bg = c.get("bg_main"); fg = c.get("text")
    if bg or fg:
        self.setStyleSheet(
            "QDialog{" + (f"background:{bg};" if bg else "") + (f"color:{fg};" if fg else "") + "}"
            + (f"QLabel{{color:{fg};}}" if fg else "")
        )
    # Line edit style
    base_bg = c.get("bg_secondary", bg)
    ctrl_fg = c.get("control_fg", fg)
    try:
        self.name_edit.setStyleSheet(
            f"QLineEdit{{background:{base_bg or '#ffffff'}; color:{ctrl_fg or '#000000'};}}"
        )
        self.name_edit.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))
    except Exception:
        pass
    # Fonts
    self.setFont(QFont(FONT_FAMILY, FONT_SIZE_LABELS))

# Bind method dynamically to class
setattr(AddPlayerDialog, 'apply_palette', _addplayer_apply_palette)
