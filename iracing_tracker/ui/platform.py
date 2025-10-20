# ui/platform.py — Windows only
import ctypes
from ctypes import wintypes

IS_WINDOWS = True  # indicateur conservé au cas où

# Hit-test codes
HTCLIENT = 1
HTCAPTION = 2
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17

# Windows messages & divers
WM_NCHITTEST = 0x0084
WM_GETMINMAXINFO = 0x0024
WM_NCLBUTTONDOWN  = 0x00A1
WM_NCLBUTTONDBLCLK = 0x00A3
WM_MOUSEMOVE       = 0x0200
WM_LBUTTONUP       = 0x0202
WM_LBUTTONDOWN     = 0x0201
WM_NCMOUSEMOVE     = 0x00A0
WM_SYSCOMMAND      = 0x0112
WM_SETCURSOR       = 0x0020
SC_SIZE            = 0xF000

# Directions de redimensionnement (WMSZ_*)
WMSZ_LEFT        = 1
WMSZ_RIGHT       = 2
WMSZ_TOP         = 3
WMSZ_TOPLEFT     = 4
WMSZ_TOPRIGHT    = 5
WMSZ_BOTTOM      = 6
WMSZ_BOTTOMLEFT  = 7
WMSZ_BOTTOMRIGHT = 8

# System metrics / monitor
SM_CXDRAG = 68
SM_CYDRAG = 69
MONITOR_DEFAULTTONEAREST = 0x00000002

# Cursors
IDC_ARROW    = 32512
IDC_SIZENWSE = 32642
IDC_SIZENESW = 32643
IDC_SIZEWE   = 32644
IDC_SIZENS   = 32645

# Structures Win32 utilisées par window.py
class MINMAXINFO(ctypes.Structure):
    _fields_ = [
        ("ptReserved", wintypes.POINT),
        ("ptMaxSize", wintypes.POINT),
        ("ptMaxPosition", wintypes.POINT),
        ("ptMinTrackSize", wintypes.POINT),
        ("ptMaxTrackSize", wintypes.POINT),
    ]

class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]
