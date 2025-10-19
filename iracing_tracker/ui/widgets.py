from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QSizePolicy,
    QAbstractItemView,
)

from .constants import (
    SEPARATOR_THICKNESS,
    FONT_FAMILY,
    TIRE_SQUARE_WIDTH,
    TIRE_SQUARE_HEIGHT,
    TIRE_SQUARE_RADIUS,
    TIRE_SQUARE_FONT_PT,
    FONT_SIZE_LAST_LAPTIMES,
    TIME_COL_PX,
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


class LastLapsList(QListWidget):
    """
    Liste spécialisée pour afficher les derniers tours avec le temps à gauche
    et le pilote aligné à droite.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setUniformItemSizes(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setSpacing(2)
        self._font = QFont(FONT_FAMILY, FONT_SIZE_LAST_LAPTIMES)
        self._time_width = TIME_COL_PX
        self._text_color = "#000000"
        self._row_labels = []

        self.setStyleSheet(
            "QListWidget{border:none; background:transparent;}"
            "QListWidget::item{margin:0px; padding:0px;}"
        )

    def set_items(self, entries):
        """
        entries peut être :
          - une chaîne (séparée par '\\n')
          - une liste de chaînes (avec tabulation '\\t' entre temps et joueur)
          - une liste de tuples/listes [time, player]
          - une liste de dicts {"time": ..., "player": ...}
        """
        if isinstance(entries, str):
            entries = entries.splitlines()

        self.clear()
        self._row_labels.clear()

        normalized = []
        for entry in entries or []:
            time_str = ""
            player = ""
            if isinstance(entry, str):
                parts = entry.split("\t", 1)
                time_str = parts[0].strip()
                player = parts[1].strip() if len(parts) > 1 else ""
            elif isinstance(entry, dict):
                time_str = str(entry.get("time", "")).strip()
                player = str(entry.get("player", "")).strip()
            elif isinstance(entry, (list, tuple)) and entry:
                time_str = str(entry[0]).strip()
                if len(entry) > 1:
                    player = str(entry[1]).strip()
            if not time_str and not player:
                continue
            normalized.append((time_str, player))

        for time_str, player in normalized:
            item = QListWidgetItem("")
            row_widget = QWidget()
            row_widget.setStyleSheet("QWidget{background:transparent;}")
            layout = QHBoxLayout(row_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(6)

            time_label = QLabel(time_str)
            time_label.setFont(self._font)
            time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            time_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            if self._time_width:
                time_label.setMinimumWidth(self._time_width)
            layout.addWidget(time_label)

            player_label = QLabel(player)
            player_label.setFont(self._font)
            player_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            player_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            layout.addWidget(player_label)

            item.setSizeHint(row_widget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, row_widget)
            self._row_labels.append((time_label, player_label))

        self._apply_text_color(self._text_color)

    def _apply_text_color(self, color):
        for time_label, player_label in self._row_labels:
            sheet = f"QLabel{{color:{color}; background:transparent;}}"
            time_label.setStyleSheet(sheet)
            player_label.setStyleSheet(sheet)

    def apply_palette(self, text_color, background, extra_css=""):
        if text_color:
            self._text_color = text_color
        base = "QListWidget{border:none;"
        if background:
            base += f" background:{background};"
        else:
            base += " background:transparent;"
        base += "}"
        base += "QListWidget::item{margin:0px; padding:0px;}"
        if extra_css:
            base += extra_css
        self.setStyleSheet(base)
        self._apply_text_color(self._text_color)
