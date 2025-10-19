import os

# --------------------------------------------------------------------
# Paramètres visuels et ressources (depuis ton ui.py)
# --------------------------------------------------------------------
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))
ICON_PATH = os.path.join(ASSETS_DIR, "icon.png")
WINDOWS_ICON_PATH = os.path.join(ASSETS_DIR, "icon.ico")
EDIT_ICON_PATH = os.path.join(ASSETS_DIR, "edit.svg")
HIDE_ICON_PATH = os.path.join(ASSETS_DIR, "hide.svg")
LIST_ICON_PATH = os.path.join(ASSETS_DIR, "list.svg")
MEDAL_GOLD_ICON_PATH = os.path.join(ASSETS_DIR, "medal_gold.svg")
MEDAL_SILVER_ICON_PATH = os.path.join(ASSETS_DIR, "medal_silver.svg")
MEDAL_BRONZE_ICON_PATH = os.path.join(ASSETS_DIR, "medal_bronze.svg")
TIRE_ICON_PATH = os.path.join(ASSETS_DIR, "tire.svg")

WINDOW_TITLE = "iRacing Tracker"
WINDOW_GEOMETRY = (1600, 1300)
MIN_WIDTH = 1200
MIN_HEIGHT = 800

# Chrome / bordure
WINDOW_BORDER_WIDTH   = 1
WINDOW_BORDER_RADIUS  = 12

# Redimensionnement
RESIZE_BORDER_THICKNESS = 8

# Styles communs
BUTTON_BORDER_WIDTH = 1
BUTTON_BORDER_RADIUS = 6
BUTTON_PADDING = "6px 12px"
ICON_BUTTON_PADDING = "0px"

# Thème clair
LIGHT_WINDOW_BORDER_COLOR =     "#646464"
LIGHT_BG_MAIN         = "#f0f0f0"
LIGHT_TEXT            = "#000000"
LIGHT_BG_SECONDARY    = "#e5e5e5"
LIGHT_MENU_ITEM_BG    = "#f0f0f0"
LIGHT_BUTTON_BG            = "#e5e5e5"
LIGHT_BUTTON_BORDER_COLOR  = "#d0d0d0"
LIGHT_SCROLLBAR_TRACK      = "#f5f5f5"
LIGHT_SCROLLBAR_BORDER     = "#c8c8c8"
LIGHT_SCROLLBAR_HANDLE_START = "#cfcfcf"
LIGHT_SCROLLBAR_HANDLE_END   = "#8f8f8f"
LIGHT_SCROLLBAR_HANDLE_HOVER_START = "#a1a1a1"
LIGHT_SCROLLBAR_HANDLE_HOVER_END   = "#6f6f6f"
LIGHT_INTERACTIVE_HOVER_BG = "#dcdcdc"
LIGHT_LAST_LAPS_HOVER_BG = "#d8d8d8"
LIGHT_BANNER_BG       = "#f0f0f0"
LIGHT_BANNER_TEXT     = "#0d47a1"
LIGHT_DEBUG_BG        = "#f0f0f0"
LIGHT_LOG_BG          = "#f0f0f0"
LIGHT_SEPARATOR       = "#cccccc"
LIGHT_CONTROL_FG      = "#000000"
LIGHT_TIRE_BG         = "#eaeaea"
LIGHT_TIRE_BORDER     = "#bdbdbd"
LIGHT_TIRE_TEXT       = "#000000"
LIGHT_ACTION_ICON_COLOR = "#111111"

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
DARK_MENU_ITEM_BG     = "#1f1f1f"
DARK_BUTTON_BG             = "#2a2a2a"
DARK_BUTTON_BORDER_COLOR   = "#3a3a3a"
DARK_SCROLLBAR_TRACK      = "#1f1f1f"
DARK_SCROLLBAR_BORDER     = "#3a3a3a"
DARK_SCROLLBAR_HANDLE_START = "#4d4d4d"
DARK_SCROLLBAR_HANDLE_END   = "#888888"
DARK_SCROLLBAR_HANDLE_HOVER_START = "#6a6a6a"
DARK_SCROLLBAR_HANDLE_HOVER_END   = "#b0b0b0"
DARK_INTERACTIVE_HOVER_BG = "#353535"
DARK_LAST_LAPS_HOVER_BG = "#2f2f2f"
DARK_BANNER_BG        = "#1f1f1f"
DARK_BANNER_TEXT      = "#e6e6e6"
DARK_DEBUG_BG         = "#262626"
DARK_LOG_BG           = "#262626"
DARK_SEPARATOR        = "#3a3a3a"
DARK_CONTROL_FG       = "#e6e6e6"
DARK_TIRE_BG          = "#2b2b2b"
DARK_TIRE_BORDER      = "#4b4b4b"
DARK_TIRE_TEXT        = "#e6e6e6"
DARK_ACTION_ICON_COLOR = "#e6e6e6"

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
FONT_SIZE_RANKING_PLAYER = 20
FONT_WEIGHT_RANKING_PLAYER = "Light"

# "Carrés" pneus
TIRE_SQUARE_WIDTH = 48
TIRE_SQUARE_HEIGHT = 72
TIRE_SQUARE_RADIUS = 8
TIRE_SQUARE_FONT_PT = 12
TIRE_TEMP_PLACEHOLDER = "--°"
TIRE_WEAR_PLACEHOLDER = "--%"
TIRE_ICON_BASE_PX = 54
TIRE_ICON_MAX_SCALE = 1.5

# Layout
BANNER_HEIGHT = 150  # None pour hauteur automatique, sinon fixer en pixels
SECTION_MARGIN = 15
SECTION_TITLE_GAP = 10
SECTION_SEPARATOR_SPACING = 15
SEPARATOR_THICKNESS = 1

# Divers
DEBUG_INITIAL_VISIBLE = True
TIME_COL_PX = 120
MEDAL_ICON_SIZE = 48
