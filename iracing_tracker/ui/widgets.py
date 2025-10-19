from PySide6.QtCore import QSize, Qt, QRect
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QAbstractItemView,
    QListView,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QStyle,
    QApplication,
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
        self.setSpacing(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(False)
        self._font = QFont(FONT_FAMILY, FONT_SIZE_LAST_LAPTIMES)
        self._time_width = TIME_COL_PX
        self._text_color = "#000000"

        self._delegate = _LastLapsDelegate(self._time_width, parent=self)
        self._delegate.set_text_color(self._text_color)
        self.setItemDelegate(self._delegate)

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
            item.setFlags(Qt.NoItemFlags)
            item.setData(Qt.UserRole, (time_str, player))
            self.addItem(item)

    def apply_palette(self, text_color, background, extra_css=""):
        if text_color:
            self._text_color = text_color
            self._delegate.set_text_color(text_color)
        self._delegate.set_time_width(self._time_width)
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


class _LastLapsDelegate(QStyledItemDelegate):
    """
    Délégué pour dessiner proprement un temps (colonne fixe) et un pilote
    aligné à droite avec ellipsis automatique.
    """

    def __init__(self, time_width: int, spacing: int = 12, parent=None):
        super().__init__(parent)
        self._time_width = int(time_width or 0)
        self._spacing = int(spacing or 0)
        self._text_color = QColor("#000000")

    def set_time_width(self, width: int):
        self._time_width = int(width or 0)

    def set_text_color(self, color: str):
        if color:
            col = QColor(color)
            if col.isValid():
                self._text_color = col

    def paint(self, painter, option, index):
        data = index.data(Qt.UserRole)
        if not data or not isinstance(data, (tuple, list)) or len(data) < 2:
            super().paint(painter, option, index)
            return

        time_str, player = data

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, opt, painter, opt.widget)

        painter.save()
        painter.setFont(opt.font)
        color = self._text_color if self._text_color.isValid() else opt.palette.color(QPalette.Text)
        painter.setPen(color)

        rect = QRect(opt.rect)

        time_rect = QRect(rect)
        time_rect.setWidth(max(0, self._time_width))

        fm = painter.fontMetrics()
        time_text = fm.elidedText(str(time_str), Qt.ElideRight, time_rect.width())
        painter.drawText(time_rect, Qt.AlignLeft | Qt.AlignVCenter, time_text)

        player_rect = QRect(rect)
        player_rect.setLeft(time_rect.right() + self._spacing)
        player_rect.adjust(0, 0, -2, 0)
        player_width = max(0, player_rect.width())
        player_text = fm.elidedText(str(player), Qt.ElideRight, player_width)
        painter.drawText(player_rect, Qt.AlignRight | Qt.AlignVCenter, player_text)

        painter.restore()

    def sizeHint(self, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        data = index.data(Qt.UserRole)
        player = ""
        if data and isinstance(data, (tuple, list)) and len(data) >= 2:
            player = str(data[1])
        fm = opt.fontMetrics
        height = fm.height() + 4
        width = self._time_width + self._spacing + fm.horizontalAdvance(player)
        return QSize(width, height)
