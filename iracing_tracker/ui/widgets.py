from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout

from .constants import (
    SEPARATOR_THICKNESS, FONT_FAMILY, TIRE_SQUARE_WIDTH, TIRE_SQUARE_HEIGHT,
    TIRE_SQUARE_RADIUS, TIRE_SQUARE_FONT_PT,
)


class BoolVarCompat:
    """
    Remplace tk.BooleanVar pour conserver l'API (.get() / .set()) attendue
    par la logique existante (main.py).
    """
    def __init__(self, value=False):
        self._v = bool(value)

    def get(self) -> bool:
        return bool(self._v)

    def set(self, v: bool):
        self._v = bool(v)


def vsep(parent: QWidget) -> QFrame:
    """Séparateur vertical (la couleur est appliquée par _apply_theme())."""
    f = QFrame(parent)
    f.setFrameShape(QFrame.NoFrame)
    f.setFixedWidth(SEPARATOR_THICKNESS)
    return f


def hsep(parent: QWidget) -> QFrame:
    """Séparateur horizontal (la couleur est appliquée par _apply_theme())."""
    f = QFrame(parent)
    f.setFrameShape(QFrame.NoFrame)
    f.setFixedHeight(SEPARATOR_THICKNESS)
    return f


def make_tire_square(text: str) -> QWidget:
    """
    Petit "carré" (rectangle) pour température/usure pneus.
    Les couleurs sont posées par _apply_theme().
    """
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
    lay.addWidget(lab)
    return w
