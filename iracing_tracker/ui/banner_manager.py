################################################################################################################
# Projet : iRacing Tracker                                                                                     #
# Fichier : iracing_tracker/ui/banner_manager.py                                                               #
# Date de modification : 20.10.2025                                                                            #
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
# Types de messages de bannière (avec priorité implicite par ordre décroissant).                               #
#--------------------------------------------------------------------------------------------------------------#
class BannerMessageType(Enum):
    """Types de messages affichables dans la bannière."""
    NONE = 0
    WAITING_SESSION = 1
    PERSONAL_RECORD = 2
    ABSOLUTE_RECORD = 3


#--------------------------------------------------------------------------------------------------------------#
# Gère l'affichage et les animations de la bannière d'information.                                             #
#--------------------------------------------------------------------------------------------------------------#
class BannerManager:
    """
    Responsabilités :
    - Afficher des messages dans la bannière
    - Animer le fond (clignotements) et le texte (fade)
    - Gérer la priorité des messages (record absolu > personnel > attente)
    """
    
    def __init__(self, banner_widget, banner_label, theme_colors: dict):
        self.banner = banner_widget
        self.label = banner_label
        self.colors = theme_colors
        
        # État actuel
        self.current_message = BannerMessageType.NONE
        self._is_animating = False
        
        # Animation fade pour texte (utilisée pour "attente session")
        self.text_opacity_effect = QGraphicsOpacityEffect(self.label)
        self.label.setGraphicsEffect(self.text_opacity_effect)
        
        from PySide6.QtCore import QSequentialAnimationGroup
        
        # Animation aller (fade in)
        self.text_fade_in = QPropertyAnimation(self.text_opacity_effect, b"opacity")
        self.text_fade_in.setDuration(BANNER_FADE_DURATION_MS)
        self.text_fade_in.setStartValue(0.1)
        self.text_fade_in.setEndValue(1.0)
        self.text_fade_in.setEasingCurve(QEasingCurve.InOutSine)
        
        # Animation retour (fade out)
        self.text_fade_out = QPropertyAnimation(self.text_opacity_effect, b"opacity")
        self.text_fade_out.setDuration(BANNER_FADE_DURATION_MS)
        self.text_fade_out.setStartValue(1.0)
        self.text_fade_out.setEndValue(0.1)
        self.text_fade_out.setEasingCurve(QEasingCurve.InOutSine)
        
        # Groupe séquentiel pour enchaîner aller-retour
        self.text_fade_animation = QSequentialAnimationGroup()
        self.text_fade_animation.addAnimation(self.text_fade_in)
        self.text_fade_animation.addAnimation(self.text_fade_out)
        self.text_fade_animation.setLoopCount(-1)  # Infini
        
        # Timer pour clignotements
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._on_blink_tick)
        self._blink_state = False
        self._blink_count_current = 0
        self._blink_count_target = 0
        self._blink_color = ""
    
    #--------------------------------------------------------------------------------------------------------------#
    # Met à jour les couleurs du thème.                                                                            #
    #--------------------------------------------------------------------------------------------------------------#
    def update_theme(self, colors: dict):
        """Applique les nouvelles couleurs du thème."""
        self.colors = colors
        # Réappliquer le message actuel avec les nouvelles couleurs
        if self.current_message != BannerMessageType.NONE:
            self._apply_message(self.current_message)
    
    #--------------------------------------------------------------------------------------------------------------#
    # Affiche un message dans la bannière avec animation appropriée.                                               #
    #--------------------------------------------------------------------------------------------------------------#
    def show_message(self, message_type: BannerMessageType):
        """Affiche un message dans la bannière (avec priorité)."""
        if message_type == self.current_message:
            return  # Déjà affiché
        
        # Arrêter toute animation en cours
        self._stop_all_animations()
        
        # Appliquer le nouveau message
        self.current_message = message_type
        self._apply_message(message_type)
    
    #--------------------------------------------------------------------------------------------------------------#
    # Vide la bannière (plus de message affiché).                                                                  #
    #--------------------------------------------------------------------------------------------------------------#
    def clear(self):
        """Vide la bannière."""
        self._stop_all_animations()
        self.current_message = BannerMessageType.NONE
        self.label.setText("")
        self._set_banner_background(self.colors.get("banner_bg", "#f0f0f0"))
    
    #--------------------------------------------------------------------------------------------------------------#
    # Applique le style et démarre l'animation pour un type de message donné.                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def _apply_message(self, message_type: BannerMessageType):
        """Configure et anime la bannière selon le type de message."""
        if message_type == BannerMessageType.NONE:
            self.clear()
            return
        
        if message_type == BannerMessageType.WAITING_SESSION:
            self.label.setText(BANNER_WAITING_TEXT)
            base_bg = self.colors.get("banner_bg", "#f0f0f0")
            self._set_banner_background(base_bg)
            # Animation fade du texte
            self.text_fade_animation.start()
        
        elif message_type == BannerMessageType.PERSONAL_RECORD:
            self.label.setText(BANNER_PERSONAL_RECORD_TEXT)
            self._start_blink_animation(BANNER_PERSONAL_RECORD_COLOR)
        
        elif message_type == BannerMessageType.ABSOLUTE_RECORD:
            self.label.setText(BANNER_ABSOLUTE_RECORD_TEXT)
            self._start_blink_animation(BANNER_ABSOLUTE_RECORD_COLOR)
    
    #--------------------------------------------------------------------------------------------------------------#
    # Démarre une animation de clignotement du fond.                                                               #
    #--------------------------------------------------------------------------------------------------------------#
    def _start_blink_animation(self, color: str):
        """Démarre l'animation de clignotement avec la couleur donnée."""
        self._is_animating = True
        self._blink_color = color
        self._blink_state = False
        self._blink_count_current = 0
        self._blink_count_target = BANNER_BLINK_COUNT * 2  # *2 car on alterne base->couleur->base
        
        # Définir opacité texte à 100%
        self.text_opacity_effect.setOpacity(1.0)
        
        # Démarrer avec la couleur de base
        base_bg = self.colors.get("banner_bg", "#f0f0f0")
        self._set_banner_background(base_bg)
        
        # Lancer le timer
        self.blink_timer.start(BANNER_BLINK_DURATION_MS)
    
    #--------------------------------------------------------------------------------------------------------------#
    # Callback appelé à chaque tick du timer de clignotement.                                                      #
    #--------------------------------------------------------------------------------------------------------------#
    def _on_blink_tick(self):
        """Gère chaque tick du clignotement."""
        if self._blink_count_current >= self._blink_count_target:
            # Fin de l'animation
            self.blink_timer.stop()
            self._is_animating = False
            # Revenir à la couleur de base
            base_bg = self.colors.get("banner_bg", "#f0f0f0")
            self._set_banner_background(base_bg)
            # Vider après un délai
            QTimer.singleShot(1000, self.clear)
            return
        
        # Alterner entre couleur de base et couleur cible
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
        """Change la couleur de fond de la bannière."""
        self.banner.setStyleSheet(f"QWidget{{background:{color};}}")
    
    #--------------------------------------------------------------------------------------------------------------#
    # Arrête toutes les animations en cours.                                                                       #
    #--------------------------------------------------------------------------------------------------------------#
    def _stop_all_animations(self):
        """Arrête toutes les animations en cours."""
        self.text_fade_animation.stop()
        self.blink_timer.stop()
        self.text_opacity_effect.setOpacity(1.0)
        self._is_animating = False
