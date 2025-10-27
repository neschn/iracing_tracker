################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui/players_dialog.py                                                               #
# Description : Boîtes de dialogue pour gérer les joueurs (liste, ajout, suppression).                         #
################################################################################################################

from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
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

from .constants import FONT_FAMILY, FONT_SIZE_LABELS, FONT_SIZE_BUTTON, PLAYER_NAME_MAX_LENGTH
from iracing_tracker.data_store import DataStore


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
        ok_btn = self.findChild(QDialogButtonBox)
        # Safer: disable via button box lookup
        for b in self.findChildren(QDialogButtonBox):
            b.button(QDialogButtonBox.Ok).setEnabled(error is None)

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
        lay.addWidget(self.list_widget)

        btn_row = QWidget(self)
        h = QHBoxLayout(btn_row)
        h.setContentsMargins(0, 0, 0, 0)
        h.addStretch(1)
        self.add_btn = QPushButton("Ajouter", self)
        self.add_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_BUTTON))
        self.del_btn = QPushButton("Supprimer", self)
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

    # --- Helpers ---
    def _reload_players(self):
        self.list_widget.clear()
        players = DataStore.load_players()
        for name in players:
            self.list_widget.addItem(str(name))
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
        ret = msg.exec()
        if ret == QMessageBox.Yes:
            DataStore.delete_player(name)
            self.modified = True
            self._reload_players()

