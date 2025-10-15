import os

# --------------------------------------------------------------------
# Paramètres visuels et ressources (depuis ton ui.py)
# --------------------------------------------------------------------
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))
ICON_PATH = os.path.join(ASSETS_DIR, "icon.png")
WINDOWS_ICON_PATH = os.path.join(ASSETS_DIR, "icon.ico")

WINDOW_TITLE = "iRacing Tracker"
WINDOW_GEOMETRY = (1600, 1000)
MIN_WIDTH = 1200
MIN_HEIGHT = 800

# Chrome / bordure
WINDOW_BORDER_WIDTH   = 1
WINDOW_BORDER_RADIUS  = 12

# Redimensionnement
RESIZE_BORDER_THICKNESS = 8

# Thème clair
LIGHT_WINDOW_BORDER_COLOR = "#646464"
LIGHT_BG_MAIN         = "#f0f0f0"
LIGHT_TEXT            = "#000000"
LIGHT_BG_SECONDARY    = "#e5e5e5"
LIGHT_BANNER_BG       = "#f0f0f0"
LIGHT_BANNER_TEXT     = "#0d47a1"
LIGHT_DEBUG_BG        = "#f0f0f0"
LIGHT_LOG_BG          = "#f0f0f0"
LIGHT_SEPARATOR       = "#cccccc"
LIGHT_CONTROL_FG      = "#000000"
LIGHT_TIRE_BG         = "#eaeaea"
LIGHT_TIRE_BORDER     = "#bdbdbd"
LIGHT_TIRE_TEXT       = "#000000"
LIGHT_TITLE_BG                = "#e7e7e7"
LIGHT_TITLE_FG                = "#111111"
LIGHT_TITLE_BTN_HOVER         = "#d9d9d9"
LIGHT_TITLE_BTN_PRESSED       = "#c4c4c4"
LIGHT_TITLE_BTN_CLOSE_HOVER   = "#e81123"
LIGHT_TITLE_BTN_CLOSE_PRESSED = "#b50d1c"

# Thème sombre
DARK_WINDOW_BORDER_COLOR  = "#383838"
DARK_BG_MAIN          = "#1f1f1f"
DARK_TEXT             = "#b9b9b9"
DARK_BG_SECONDARY     = "#2a2a2a"
DARK_BANNER_BG        = "#1f1f1f"
DARK_BANNER_TEXT      = "#e6e6e6"
DARK_DEBUG_BG         = "#262626"
DARK_LOG_BG           = "#262626"
DARK_SEPARATOR        = "#3a3a3a"
DARK_CONTROL_FG       = "#e6e6e6"
DARK_TIRE_BG          = "#2b2b2b"
DARK_TIRE_BORDER      = "#4b4b4b"
DARK_TIRE_TEXT        = "#e6e6e6"
DARK_TITLE_BG                 = "#2a2a2a"
DARK_TITLE_FG                 = "#f1f1f1"
DARK_TITLE_BTN_HOVER          = "#3a3a3a"
DARK_TITLE_BTN_PRESSED        = "#4b4b4b"
DARK_TITLE_BTN_CLOSE_HOVER    = "#c42b1c"
DARK_TITLE_BTN_CLOSE_PRESSED  = "#9a1d13"

# Polices / tailles
FONT_FAMILY = "Arial"
FONT_SIZE_LABELS = 12
FONT_SIZE_SECTION_TITLE = 12
FONT_SIZE_BANNER = 22
FONT_SIZE_PLAYER = 20
FONT_SIZE_LAPTIME = 24
FONT_SIZE_LAST_LAPTIMES = 12
FONT_SIZE_DEBUG = 12
FONT_SIZE_LOG = 12
FONT_SIZE_BUTTON = 9

# "Carrés" pneus
TIRE_SQUARE_WIDTH = 48
TIRE_SQUARE_HEIGHT = 72
TIRE_SQUARE_RADIUS = 8
TIRE_SQUARE_FONT_PT = 12
TIRE_TEMP_PLACEHOLDER = "--°"
TIRE_WEAR_PLACEHOLDER = "--%"

# Layout
SECTION_MARGIN = 15
SECTION_TITLE_GAP = 10
SECTION_SEPARATOR_SPACING = 15
SEPARATOR_THICKNESS = 1

# Divers
DEBUG_INITIAL_VISIBLE = True
LOG_TEXT_HEIGHT_ROWS = 8
TIME_COL_PX = 120
