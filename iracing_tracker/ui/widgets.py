from PySide6.QtCore import QSize, Qt, QRect, QRectF
from PySide6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter
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
from PySide6.QtSvg import QSvgRenderer

from .constants import (
    SEPARATOR_THICKNESS,
    FONT_FAMILY,
    TIRE_SQUARE_WIDTH,
    TIRE_SQUARE_HEIGHT,
    TIRE_SQUARE_RADIUS,
    TIRE_SQUARE_FONT_PT,
    TIRE_ICON_BASE_PX,
    TIRE_ICON_MAX_SCALE,
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


class TireInfoWidget(QWidget):
    """
    Petit widget pour représenter un pneu avec son libellé et sa valeur.
    """

    def __init__(self, position_text: str, value_text: str, icon_path: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("TireInfoWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._icon_path = icon_path
        self._renderer = QSvgRenderer(self._icon_path, self)
        view_box = self._renderer.viewBoxF()
        if view_box.width() > 0 and view_box.height() > 0:
            self._aspect_ratio = view_box.width() / view_box.height()
        else:
            self._aspect_ratio = 1.0

        base_width = float(TIRE_ICON_BASE_PX or 96)
        if base_width <= 0:
            base_width = 96.0
        base_height = base_width / self._aspect_ratio if self._aspect_ratio else base_width
        if base_height <= 0:
            base_height = base_width
        self._base_width = base_width
        self._base_height = base_height
        self._icon_color = QColor("#000000")
        self._current_icon_size = QSize()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignCenter)

        self.position_label = QLabel(position_text.upper())
        self.position_label.setAlignment(Qt.AlignCenter)
        pos_font = QFont(FONT_FAMILY, TIRE_SQUARE_FONT_PT, QFont.Bold)
        self.position_label.setFont(pos_font)
        lay.addWidget(self.position_label)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.icon_label.setStyleSheet("QLabel{background:transparent; border:none;}")
        lay.addWidget(self.icon_label, 1)

        self.value_label = QLabel(value_text)
        self.value_label.setAlignment(Qt.AlignCenter)
        val_font = QFont(FONT_FAMILY, TIRE_SQUARE_FONT_PT)
        self.value_label.setFont(val_font)
        lay.addWidget(self.value_label)

        self.setStyleSheet("QWidget#TireInfoWidget{background:transparent; border:none;}")

        # Valeurs par défaut avant application du thème.
        self.apply_palette("", "", "#000000")

    def set_value_text(self, text: str):
        self.value_label.setText(text)

    def set_position_text(self, text: str):
        self.position_label.setText(text.upper())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_icon_pixmap()

    def set_icon_color(self, color: str | QColor):
        qcolor = QColor(color)
        if not qcolor.isValid():
            qcolor = QColor("#000000")
        self._icon_color = qcolor
        self._update_icon_pixmap(force=True)

    def apply_palette(self, _background: str, _border: str, text_color: str):
        color = text_color if QColor(text_color).isValid() else "#000000"
        text_css = f"QLabel{{color:{color}; background:transparent; border:none;}}"
        self.position_label.setStyleSheet(text_css)
        self.value_label.setStyleSheet(text_css)
        self.set_icon_color(color)

    def _update_icon_pixmap(self, force: bool = False):
        if not self._renderer.isValid():
            self.icon_label.clear()
            return

        layout = self.layout()
        margins = layout.contentsMargins() if layout else None
        available_width = (
            max(16, self.width() - (margins.left() + margins.right()))
            if margins
            else max(16, self.width() - 16)
        )
        spacing = layout.spacing() if layout else 0
        text_height = (
            self.position_label.sizeHint().height()
            + self.value_label.sizeHint().height()
        )
        total_margins = (margins.top() + margins.bottom()) if margins else 16
        available_height = max(
            16,
            self.height() - total_margins - text_height - (spacing * 2),
        )

        base_width = self._base_width
        base_height = self._base_height
        width_ratio = available_width / base_width
        height_ratio = available_height / base_height
        max_scale = max(1.0, float(TIRE_ICON_MAX_SCALE or 1.0))
        scale = min(width_ratio, height_ratio, max_scale)

        target_width = max(16, int(round(base_width * scale)))
        target_height = max(16, int(round(base_height * scale)))

        if self._aspect_ratio > 0:
            target_height = max(16, int(round(target_width / self._aspect_ratio)))
            if target_height > available_height:
                target_height = int(available_height)
                target_width = max(16, int(round(target_height * self._aspect_ratio)))

        size = QSize(target_width, target_height)
        if not force and size == self._current_icon_size:
            return

        self._current_icon_size = size
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        target = QRectF(0, 0, size.width(), size.height())
        self._renderer.render(painter, target)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), self._icon_color)
        painter.end()

        self.icon_label.setFixedSize(size)
        self.icon_label.setPixmap(pixmap)



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
        self._hover_row = -1
        self.setFont(self._font)
        self.setMouseTracking(True)
        try:
            self.viewport().setMouseTracking(True)
        except Exception:
            pass

        self._delegate = _LastLapsDelegate(self._time_width, parent=self)
        self._delegate.set_text_color(self._text_color)
        self._delegate.set_hovered_row(self._hover_row)
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
        self._hover_row = -1
        self._delegate.set_hovered_row(-1)

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
            item.setFlags(Qt.ItemIsEnabled)
            item.setData(Qt.UserRole, (time_str, player))
            self.addItem(item)

    def apply_palette(self, text_color, background, hover_color, extra_css=""):
        if text_color:
            self._text_color = text_color
            self._delegate.set_text_color(text_color)
        self._delegate.set_time_width(self._time_width)
        self._delegate.set_hover_color(hover_color)
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
        self.viewport().update()

    def mouseMoveEvent(self, event):
        idx = self.indexAt(event.pos())
        row = idx.row() if idx.isValid() else -1
        if row != self._hover_row:
            self._hover_row = row
            self._delegate.set_hovered_row(row)
            self.viewport().update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self._hover_row != -1:
            self._hover_row = -1
            self._delegate.set_hovered_row(-1)
            self.viewport().update()
        super().leaveEvent(event)


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
        self._hover_bg = QColor(0, 0, 0, 0)
        self._hover_row = -1

    def set_time_width(self, width: int):
        self._time_width = int(width or 0)

    def set_text_color(self, color: str):
        if color:
            col = QColor(color)
            if col.isValid():
                self._text_color = col
                return
        self._text_color = QColor("#000000")

    def set_hover_color(self, color):
        if color:
            col = QColor(color)
            if col.isValid():
                self._hover_bg = col
                return
        self._hover_bg = QColor(0, 0, 0, 0)

    def set_hovered_row(self, row: int):
        self._hover_row = int(row)

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
        if index.row() == self._hover_row and self._hover_bg.alpha() > 0:
            painter.fillRect(opt.rect, self._hover_bg)
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
