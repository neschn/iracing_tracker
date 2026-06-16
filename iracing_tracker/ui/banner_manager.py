################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui/banner_manager.py                                                               #
# Date de modification : 16.06.2026                                                                            #
# Auteur : Nicolas Schneeberger                                                                                #
# Description : Gère les animations et messages de la bannière d'information.                                  #
################################################################################################################

from enum import Enum
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QGraphicsOpacityEffect

from .constants import (
    BANNER_WAITING_TEXT,
    BANNER_PERSONAL_RECORD_TEXT,
    BANNER_ABSOLUTE_RECORD_TEXT,
    BANNER_PERSONAL_RECORD_COLOR,
    BANNER_ABSOLUTE_RECORD_COLOR,
    BANNER_BLINK_COUNT,
    BANNER_BLINK_DURATION_MS,
    BANNER_FADE_DURATION_MS,
)


#--------------------------------------------------------------------------------------------------------------#
# Types de messages affichables dans la bannière (priorité croissante : attente < perso < absolu).             #
#--------------------------------------------------------------------------------------------------------------#
class BannerMessageType(Enum):
    NONE = 0
    WAITING_SESSION = 1
    PERSONAL_RECORD = 2
    ABSOLUTE_RECORD = 3


#--------------------------------------------------------------------------------------------------------------#
# Gère l'affichage et les animations de la bannière (fade du texte « attente », clignotement des records).     #
#--------------------------------------------------------------------------------------------------------------#
class BannerManager:

    #--------------------------------------------------------------------------------------------------------------#
    # Construit les animations (fade du texte, timer de clignotement) et l'état initial.                           #
    #--------------------------------------------------------------------------------------------------------------#
    def __init__(self, banner_widget, banner_label, theme_colors: dict):
        self.banner = banner_widget
        self.label = banner_label
        self.colors = theme_colors

        self.current_message = BannerMessageType.NONE
        self._is_animating = False

        # Effet d'opacité du texte (fade pour « attente session »)
        self.text_opacity_effect = QGraphicsOpacityEffect(self.label)
        self.label.setGraphicsEffect(self.text_opacity_effect)

        from PySide6.QtCore import QSequentialAnimationGroup

        # Fade in
        self.text_fade_in = QPropertyAnimation(self.text_opacity_effect, b"opacity")
        self.text_fade_in.setDuration(BANNER_FADE_DURATION_MS)
        self.text_fade_in.setStartValue(0.1)
        self.text_fade_in.setEndValue(1.0)
        self.text_fade_in.setEasingCurve(QEasingCurve.InOutSine)

        # Fade out
        self.text_fade_out = QPropertyAnimation(self.text_opacity_effect, b"opacity")
        self.text_fade_out.setDuration(BANNER_FADE_DURATION_MS)
        self.text_fade_out.setStartValue(1.0)
        self.text_fade_out.setEndValue(0.1)
        self.text_fade_out.setEasingCurve(QEasingCurve.InOutSine)

        # Enchaînement aller-retour en boucle
        self.text_fade_animation = QSequentialAnimationGroup()
        self.text_fade_animation.addAnimation(self.text_fade_in)
        self.text_fade_animation.addAnimation(self.text_fade_out)
        self.text_fade_animation.setLoopCount(-1)  # Infini

        # Timer de clignotement du fond
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._on_blink_tick)
        self._blink_state = False
        self._blink_count_current = 0
        self._blink_count_target = 0
        self._blink_color = ""

    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour les couleurs du thème et réapplique le message courant.                                           #
    #--------------------------------------------------------------------------------------------------------------#
    def update_theme(self, colors: dict):
        self.colors = colors
        if self.current_message != BannerMessageType.NONE:
            self._apply_message(self.current_message)

    #--------------------------------------------------------------------------------------------------------------#
    # Affiche un message dans la bannière (ignore si déjà affiché).                                                #
    #--------------------------------------------------------------------------------------------------------------#
    def show_message(self, message_type: BannerMessageType):
        if message_type == self.current_message:
            return

        self._stop_all_animations()
        self.current_message = message_type
        self._apply_message(message_type)

    #--------------------------------------------------------------------------------------------------------------#
    # Vide la bannière (plus aucun message affiché).                                                               #
    #--------------------------------------------------------------------------------------------------------------#
    def clear(self):
        self._stop_all_animations()
        self.current_message = BannerMessageType.NONE
        self.label.setText("")
        self._set_banner_background(self.colors.get("banner_bg", "#f0f0f0"))

    #--------------------------------------------------------------------------------------------------------------#
    # Applique le texte, le style et l'animation correspondant au type de message.                                 #
    #--------------------------------------------------------------------------------------------------------------#
    def _apply_message(self, message_type: BannerMessageType):
        if message_type == BannerMessageType.NONE:
            self.clear()
            return

        if message_type == BannerMessageType.WAITING_SESSION:
            self.label.setText(BANNER_WAITING_TEXT)
            base_bg = self.colors.get("banner_bg", "#f0f0f0")
            self._set_banner_background(base_bg)
            self.text_fade_animation.start()

        elif message_type == BannerMessageType.PERSONAL_RECORD:
            self.label.setText(BANNER_PERSONAL_RECORD_TEXT)
            self._start_blink_animation(BANNER_PERSONAL_RECORD_COLOR)

        elif message_type == BannerMessageType.ABSOLUTE_RECORD:
            self.label.setText(BANNER_ABSOLUTE_RECORD_TEXT)
            self._start_blink_animation(BANNER_ABSOLUTE_RECORD_COLOR)

    #--------------------------------------------------------------------------------------------------------------#
    # Démarre le clignotement du fond avec la couleur donnée.                                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def _start_blink_animation(self, color: str):
        self._is_animating = True
        self._blink_color = color
        self._blink_state = False
        self._blink_count_current = 0
        self._blink_count_target = BANNER_BLINK_COUNT * 2  # *2 : on alterne base -> couleur -> base

        self.text_opacity_effect.setOpacity(1.0)

        base_bg = self.colors.get("banner_bg", "#f0f0f0")
        self._set_banner_background(base_bg)

        self.blink_timer.start(BANNER_BLINK_DURATION_MS)

    #--------------------------------------------------------------------------------------------------------------#
    # Gère chaque tick du clignotement (alterne les couleurs, vide la bannière à la fin).                          #
    #--------------------------------------------------------------------------------------------------------------#
    def _on_blink_tick(self):
        if self._blink_count_current >= self._blink_count_target:
            # Fin de l'animation : revenir au fond de base puis vider après un délai
            self.blink_timer.stop()
            self._is_animating = False
            base_bg = self.colors.get("banner_bg", "#f0f0f0")
            self._set_banner_background(base_bg)
            QTimer.singleShot(1000, self.clear)
            return

        # Alterner entre fond de base et couleur cible
        self._blink_state = not self._blink_state
        if self._blink_state:
            self._set_banner_background(self._blink_color)
        else:
            base_bg = self.colors.get("banner_bg", "#f0f0f0")
            self._set_banner_background(base_bg)

        self._blink_count_current += 1

    #--------------------------------------------------------------------------------------------------------------#
    # Applique une couleur de fond à la bannière.                                                                  #
    #--------------------------------------------------------------------------------------------------------------#
    def _set_banner_background(self, color: str):
        self.banner.setStyleSheet(f"QWidget{{background:{color};}}")

    #--------------------------------------------------------------------------------------------------------------#
    # Arrête toutes les animations en cours et remet le texte à pleine opacité.                                    #
    #--------------------------------------------------------------------------------------------------------------#
    def _stop_all_animations(self):
        self.text_fade_animation.stop()
        self.blink_timer.stop()
        self.text_opacity_effect.setOpacity(1.0)
        self._is_animating = False
