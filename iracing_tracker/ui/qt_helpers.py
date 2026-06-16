################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui/qt_helpers.py                                                                   #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Fonctions utilitaires PySide partagées (alignement, rendu SVG, CSS scrollbar, poids police).   #
################################################################################################################

import os

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QFont, QIcon, QColor, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


#--------------------------------------------------------------------------------------------------------------#
# Aligne un widget en haut de son layout, sans planter si l'un des deux est absent.                            #
#--------------------------------------------------------------------------------------------------------------#
def align_top(layout, widget):
    if layout is None or widget is None:
        return
    try:
        layout.setAlignment(widget, Qt.AlignTop)
    except Exception:
        pass


#--------------------------------------------------------------------------------------------------------------#
# Charge un SVG en QIcon, recoloré uniformément (teinte unique via SourceIn).                                  #
#--------------------------------------------------------------------------------------------------------------#
def load_svg_icon(path: str, color: str, size: int) -> QIcon:
    if not path or not os.path.isfile(path):
        return QIcon()
    try:
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


#--------------------------------------------------------------------------------------------------------------#
# Charge un SVG en QPixmap en respectant le ratio d'origine (viewBox) et en centrant le rendu.                 #
#--------------------------------------------------------------------------------------------------------------#
def load_svg_pixmap(path: str, size: int) -> QPixmap:
    if not path or not os.path.isfile(path):
        return QPixmap()
    try:
        renderer = QSvgRenderer(path)
        if not renderer.isValid():
            return QPixmap()
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        view_box = renderer.viewBoxF()
        if not view_box.isValid() or view_box.isEmpty():
            view_box = QRectF(0, 0, size, size)
        max_dim = max(view_box.width(), view_box.height(), 1.0)
        scale = size / max_dim
        target_w = view_box.width() * scale
        target_h = view_box.height() * scale
        target_x = (size - target_w) / 2.0
        target_y = (size - target_h) / 2.0
        target_rect = QRectF(target_x, target_y, target_w, target_h)
        renderer.render(painter, target_rect)
        painter.end()
        return pixmap
    except Exception:
        return QPixmap()


#--------------------------------------------------------------------------------------------------------------#
# Convertit un poids de police (nom ou entier) en QFont.Weight, avec repli sur Normal.                         #
#--------------------------------------------------------------------------------------------------------------#
def resolve_font_weight(weight) -> QFont.Weight:
    mapping = {
        "thin": QFont.Weight.Thin,
        "extralight": QFont.Weight.ExtraLight,
        "ultralight": QFont.Weight.ExtraLight,
        "light": QFont.Weight.Light,
        "normal": QFont.Weight.Normal,
        "regular": QFont.Weight.Normal,
        "medium": QFont.Weight.Medium,
        "semibold": QFont.Weight.DemiBold,
        "demibold": QFont.Weight.DemiBold,
        "bold": QFont.Weight.Bold,
        "extrabold": QFont.Weight.ExtraBold,
        "black": QFont.Weight.Black,
    }
    if isinstance(weight, str):
        key = weight.strip().lower()
        if key in mapping:
            return mapping[key]
    try:
        value = int(weight)
        candidates = [
            QFont.Weight.Thin,
            QFont.Weight.ExtraLight,
            QFont.Weight.Light,
            QFont.Weight.Normal,
            QFont.Weight.Medium,
            QFont.Weight.DemiBold,
            QFont.Weight.Bold,
            QFont.Weight.ExtraBold,
            QFont.Weight.Black,
        ]
        return min(candidates, key=lambda enum: abs(enum.value - value))
    except Exception:
        return QFont.Weight.Normal


#--------------------------------------------------------------------------------------------------------------#
# Construit la feuille de style d'une scrollbar verticale custom pour un sélecteur Qt donné.                   #
#--------------------------------------------------------------------------------------------------------------#
def scrollbar_css(selector: str, track: str, border: str, handle_start: str, handle_end: str,
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
