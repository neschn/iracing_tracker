################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui/widgets.py                                                                      #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Widgets PySide sur mesure : séparateurs, liste des derniers tours et son délégué.              #
################################################################################################################

from PySide6.QtCore import QSize, Qt, QRect
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
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
    FONT_SIZE_LAST_LAPTIMES,
    TIME_COL_PX,
    LAP_NUM_COL_PX,
)


#--------------------------------------------------------------------------------------------------------------#
# Remplace tk.BooleanVar : conserve l'API .get() / .set() attendue par main.py.                                #
#--------------------------------------------------------------------------------------------------------------#
class BoolVarCompat:

    def __init__(self, value=False):
        self._v = bool(value)

    def get(self) -> bool:
        return bool(self._v)

    def set(self, v: bool):
        self._v = bool(v)


#--------------------------------------------------------------------------------------------------------------#
# Crée un séparateur vertical (couleur appliquée ensuite par le thème).                                        #
#--------------------------------------------------------------------------------------------------------------#
def vsep(parent: QWidget) -> QFrame:
    f = QFrame(parent)
    f.setFrameShape(QFrame.NoFrame)
    f.setFixedWidth(SEPARATOR_THICKNESS)
    return f


#--------------------------------------------------------------------------------------------------------------#
# Crée un séparateur horizontal (couleur appliquée ensuite par le thème).                                      #
#--------------------------------------------------------------------------------------------------------------#
def hsep(parent: QWidget) -> QFrame:
    f = QFrame(parent)
    f.setFrameShape(QFrame.NoFrame)
    f.setFixedHeight(SEPARATOR_THICKNESS)
    return f


#--------------------------------------------------------------------------------------------------------------#
# Liste des derniers tours : n° + temps à gauche, pilote aligné à droite (via un délégué).                     #
#--------------------------------------------------------------------------------------------------------------#
class SessionTimesList(QListWidget):

    #--------------------------------------------------------------------------------------------------------------#
    # Configure la liste (sans cadre ni sélection) et son délégué de rendu.                                        #
    #--------------------------------------------------------------------------------------------------------------#
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
        self._lap_width = LAP_NUM_COL_PX
        self._time_width = TIME_COL_PX
        self._text_color = "#000000"
        self._hover_row = -1
        self.setFont(self._font)
        self.setMouseTracking(True)
        try:
            self.viewport().setMouseTracking(True)
        except Exception:
            pass

        self._delegate = _SessionTimesDelegate(self._lap_width, self._time_width, parent=self)
        self._delegate.set_text_color(self._text_color)
        self._delegate.set_hovered_row(self._hover_row)
        self.setItemDelegate(self._delegate)

        self.setStyleSheet(
            "QListWidget{border:none; background:transparent;}"
            "QListWidget::item{margin:0px; padding:0px;}"
        )

    #--------------------------------------------------------------------------------------------------------------#
    # Remplit la liste à partir d'entrées variées (str, liste de str « lap\ttemps\tjoueur », tuples ou dicts).     #
    #--------------------------------------------------------------------------------------------------------------#
    def set_items(self, entries):
        if isinstance(entries, str):
            entries = entries.splitlines()

        self.clear()
        self._hover_row = -1
        self._delegate.set_hovered_row(-1)

        normalized = []
        for entry in entries or []:
            lap = ""
            time_str = ""
            player = ""
            if isinstance(entry, str):
                parts = entry.split("\t")
                if len(parts) >= 3:
                    lap = parts[0].strip()
                    time_str = parts[1].strip()
                    player = parts[2].strip()
                elif len(parts) == 2:
                    time_str = parts[0].strip()
                    player = parts[1].strip()
            elif isinstance(entry, dict):
                lap = str(entry.get("lap", "")).strip()
                time_str = str(entry.get("time", "")).strip()
                player = str(entry.get("player", "")).strip()
            elif isinstance(entry, (list, tuple)) and entry:
                if len(entry) >= 3:
                    lap = str(entry[0]).strip()
                    time_str = str(entry[1]).strip()
                    player = str(entry[2]).strip()
                else:
                    time_str = str(entry[0]).strip()
                    if len(entry) > 1:
                        player = str(entry[1]).strip()
            if not time_str and not player:
                continue
            normalized.append((lap, time_str, player))

        for lap, time_str, player in normalized:
            item = QListWidgetItem("")
            item.setFlags(Qt.ItemIsEnabled)
            item.setData(Qt.UserRole, (lap, time_str, player))
            self.addItem(item)

    #--------------------------------------------------------------------------------------------------------------#
    # Applique les couleurs du thème (texte, fond, survol) et un éventuel CSS de scrollbar.                        #
    #--------------------------------------------------------------------------------------------------------------#
    def apply_palette(self, text_color, background, hover_color, extra_css=""):
        if text_color:
            self._text_color = text_color
            self._delegate.set_text_color(text_color)
        self._delegate.set_lap_width(self._lap_width)
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

    #--------------------------------------------------------------------------------------------------------------#
    # Suit la ligne survolée par la souris pour le surlignage.                                                     #
    #--------------------------------------------------------------------------------------------------------------#
    def mouseMoveEvent(self, event):
        idx = self.indexAt(event.pos())
        row = idx.row() if idx.isValid() else -1
        if row != self._hover_row:
            self._hover_row = row
            self._delegate.set_hovered_row(row)
            self.viewport().update()
        super().mouseMoveEvent(event)

    #--------------------------------------------------------------------------------------------------------------#
    # Efface le surlignage quand la souris quitte la liste.                                                        #
    #--------------------------------------------------------------------------------------------------------------#
    def leaveEvent(self, event):
        if self._hover_row != -1:
            self._hover_row = -1
            self._delegate.set_hovered_row(-1)
            self.viewport().update()
        super().leaveEvent(event)


#--------------------------------------------------------------------------------------------------------------#
# Délégué de rendu d'une ligne : temps en colonne fixe et pilote aligné à droite (avec ellipsis).              #
#--------------------------------------------------------------------------------------------------------------#
class _SessionTimesDelegate(QStyledItemDelegate):

    #--------------------------------------------------------------------------------------------------------------#
    # Initialise les largeurs de colonnes, les couleurs et la ligne survolée.                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def __init__(self, lap_width: int, time_width: int, spacing: int = 12, parent=None):
        super().__init__(parent)
        self._lap_width = int(lap_width or 0)
        self._time_width = int(time_width or 0)
        self._spacing = int(spacing or 0)
        self._text_color = QColor("#000000")
        self._hover_bg = QColor(0, 0, 0, 0)
        self._hover_row = -1

    #--------------------------------------------------------------------------------------------------------------#
    # Définit la largeur de la colonne « n° de tour ».                                                             #
    #--------------------------------------------------------------------------------------------------------------#
    def set_lap_width(self, width: int):
        self._lap_width = int(width or 0)

    #--------------------------------------------------------------------------------------------------------------#
    # Définit la largeur de la colonne « temps ».                                                                  #
    #--------------------------------------------------------------------------------------------------------------#
    def set_time_width(self, width: int):
        self._time_width = int(width or 0)

    #--------------------------------------------------------------------------------------------------------------#
    # Définit la couleur du texte (repli sur noir si invalide).                                                    #
    #--------------------------------------------------------------------------------------------------------------#
    def set_text_color(self, color: str):
        if color:
            col = QColor(color)
            if col.isValid():
                self._text_color = col
                return
        self._text_color = QColor("#000000")

    #--------------------------------------------------------------------------------------------------------------#
    # Définit la couleur de survol (transparente si invalide).                                                     #
    #--------------------------------------------------------------------------------------------------------------#
    def set_hover_color(self, color):
        if color:
            col = QColor(color)
            if col.isValid():
                self._hover_bg = col
                return
        self._hover_bg = QColor(0, 0, 0, 0)

    #--------------------------------------------------------------------------------------------------------------#
    # Mémorise l'index de la ligne survolée.                                                                       #
    #--------------------------------------------------------------------------------------------------------------#
    def set_hovered_row(self, row: int):
        self._hover_row = int(row)

    #--------------------------------------------------------------------------------------------------------------#
    # Dessine une ligne : n° de tour, temps et pilote (avec surlignage et ellipsis).                               #
    #--------------------------------------------------------------------------------------------------------------#
    def paint(self, painter, option, index):
        data = index.data(Qt.UserRole)
        if not data or not isinstance(data, (tuple, list)) or len(data) < 2:
            super().paint(painter, option, index)
            return

        if len(data) >= 3:
            lap, time_str, player = data
        else:
            lap = ""
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

        # Colonne n° de tour
        lap_rect = QRect(rect)
        lap_rect.setWidth(max(0, self._lap_width))

        # Colonne temps
        time_rect = QRect(rect)
        time_rect.setLeft(lap_rect.right() + self._spacing)
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

        # Texte du n° de tour
        lap_text = fm.elidedText(str(lap), Qt.ElideRight, lap_rect.width())
        painter.drawText(lap_rect, Qt.AlignLeft | Qt.AlignVCenter, lap_text)

        painter.restore()

    #--------------------------------------------------------------------------------------------------------------#
    # Calcule la taille d'une ligne (hauteur de police + largeurs de colonnes).                                    #
    #--------------------------------------------------------------------------------------------------------------#
    def sizeHint(self, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        data = index.data(Qt.UserRole)
        player = ""
        if data and isinstance(data, (tuple, list)):
            if len(data) >= 3:
                player = str(data[2])
            elif len(data) >= 2:
                player = str(data[1])
        fm = opt.fontMetrics
        height = fm.height() + 4
        width = self._lap_width + self._spacing + self._time_width + self._spacing + fm.horizontalAdvance(player)
        return QSize(width, height)


# Alias de compatibilité
LastLapsList = SessionTimesList
