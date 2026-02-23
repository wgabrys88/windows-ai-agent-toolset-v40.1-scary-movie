"""Franz region selector — transparent overlay for visual crop selection.
Outputs normalized CAPTURE_CROP coordinates for config.py.
Win32 GDI only, no dependencies."""

import ctypes
import ctypes.wintypes as W
import sys

u32 = ctypes.WinDLL("user32", use_last_error=True)
g32 = ctypes.WinDLL("gdi32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)

try:
    ctypes.WinDLL("shcore", use_last_error=True).SetProcessDpiAwareness(2)
except Exception:
    pass

WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
LWA_ALPHA = 0x00000002
LWA_COLORKEY = 0x00000001
GWL_EXSTYLE = -20
WM_PAINT = 0x000F
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_MOUSEMOVE = 0x0200
WM_KEYDOWN = 0x0100
WM_DESTROY = 0x0002
WM_ERASEBKGND = 0x0014
VK_ESCAPE = 0x1B
CS_HREDRAW = 2
CS_VREDRAW = 1
IDC_CROSS = 32515
COLOR_WINDOW = 5
SM_CXSCREEN = 0
SM_CYSCREEN = 1
DIB_RGB_COLORS = 0
BI_RGB = 0
SRCCOPY = 0x00CC0020
PS_SOLID = 0
PS_DASH = 1
TRANSPARENT = 1
OPAQUE = 2

WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, W.HWND, W.UINT, W.WPARAM, W.LPARAM)

u32.GetSystemMetrics.argtypes = [ctypes.c_int]
u32.GetSystemMetrics.restype = ctypes.c_int
u32.SetLayeredWindowAttributes.argtypes = [W.HWND, W.DWORD, W.BYTE, W.DWORD]
u32.SetLayeredWindowAttributes.restype = W.BOOL
u32.CreateWindowExW.argtypes = [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, W.HWND, W.HMENU, W.HINSTANCE, W.LPVOID]
u32.CreateWindowExW.restype = W.HWND
u32.DefWindowProcW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
u32.DefWindowProcW.restype = ctypes.c_long
u32.RegisterClassExW.restype = W.ATOM
u32.ShowWindow.argtypes = [W.HWND, ctypes.c_int]
u32.ShowWindow.restype = W.BOOL
u32.UpdateWindow.argtypes = [W.HWND]
u32.UpdateWindow.restype = W.BOOL
u32.GetMessageW.argtypes = [ctypes.POINTER(W.MSG), W.HWND, W.UINT, W.UINT]
u32.GetMessageW.restype = W.BOOL
u32.TranslateMessage.argtypes = [ctypes.POINTER(W.MSG)]
u32.TranslateMessage.restype = W.BOOL
u32.DispatchMessageW.argtypes = [ctypes.POINTER(W.MSG)]
u32.DispatchMessageW.restype = ctypes.c_long
u32.PostQuitMessage.argtypes = [ctypes.c_int]
u32.PostQuitMessage.restype = None
u32.InvalidateRect.argtypes = [W.HWND, ctypes.c_void_p, W.BOOL]
u32.InvalidateRect.restype = W.BOOL
u32.BeginPaint.argtypes = [W.HWND, ctypes.c_void_p]
u32.BeginPaint.restype = W.HDC
u32.EndPaint.argtypes = [W.HWND, ctypes.c_void_p]
u32.EndPaint.restype = W.BOOL
u32.GetDC.argtypes = [W.HWND]
u32.GetDC.restype = W.HDC
u32.ReleaseDC.argtypes = [W.HWND, W.HDC]
u32.ReleaseDC.restype = ctypes.c_int
u32.FillRect.argtypes = [W.HDC, ctypes.c_void_p, W.HBRUSH]
u32.FillRect.restype = ctypes.c_int
u32.LoadCursorW.argtypes = [W.HINSTANCE, W.LPCWSTR]
u32.LoadCursorW.restype = W.HCURSOR
u32.SetCursor.argtypes = [W.HCURSOR]
u32.SetCursor.restype = W.HCURSOR
u32.DestroyWindow.argtypes = [W.HWND]
u32.DestroyWindow.restype = W.BOOL
g32.CreateSolidBrush.argtypes = [W.DWORD]
g32.CreateSolidBrush.restype = W.HBRUSH
g32.CreatePen.argtypes = [ctypes.c_int, ctypes.c_int, W.DWORD]
g32.CreatePen.restype = W.HGDIOBJ
g32.SelectObject.argtypes = [W.HDC, W.HGDIOBJ]
g32.SelectObject.restype = W.HGDIOBJ
g32.DeleteObject.argtypes = [W.HGDIOBJ]
g32.DeleteObject.restype = W.BOOL
g32.Rectangle.argtypes = [W.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
g32.Rectangle.restype = W.BOOL
g32.SetBkMode.argtypes = [W.HDC, ctypes.c_int]
g32.SetBkMode.restype = ctypes.c_int
g32.GetStockObject.argtypes = [ctypes.c_int]
g32.GetStockObject.restype = W.HGDIOBJ
g32.SetROP2.argtypes = [W.HDC, ctypes.c_int]
g32.SetROP2.restype = ctypes.c_int


class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc", W.HDC), ("fErase", W.BOOL), ("rcPaint", W.RECT),
        ("fRestore", W.BOOL), ("fIncUpdate", W.BOOL), ("rgbReserved", W.BYTE * 32),
    ]


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", W.UINT), ("style", W.UINT), ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
        ("hInstance", W.HINSTANCE), ("hIcon", W.HICON), ("hCursor", W.HCURSOR),
        ("hbrBackground", W.HBRUSH), ("lpszMenuName", W.LPCWSTR),
        ("lpszClassName", W.LPCWSTR), ("hIconSm", W.HICON),
    ]


sw = u32.GetSystemMetrics(SM_CXSCREEN)
sh = u32.GetSystemMetrics(SM_CYSCREEN)
if sw <= 0 or sh <= 0:
    sw, sh = 1920, 1080

dragging = False
sx, sy, ex, ey = 0, 0, 0, 0
done = False
result_rect = None
hwnd_global = None

NULL_BRUSH = g32.GetStockObject(5)


def wndproc(hwnd, msg, wp, lp):
    global dragging, sx, sy, ex, ey, done, result_rect, hwnd_global
    if msg == WM_ERASEBKGND:
        return 1
    if msg == WM_PAINT:
        ps = PAINTSTRUCT()
        hdc = u32.BeginPaint(hwnd, ctypes.byref(ps))
        rc = W.RECT(0, 0, sw, sh)
        brush = g32.CreateSolidBrush(0x00000001)
        u32.FillRect(hdc, ctypes.byref(rc), brush)
        g32.DeleteObject(brush)
        if dragging or (ex != sx or ey != sy):
            x1, y1 = min(sx, ex), min(sy, ey)
            x2, y2 = max(sx, ex), max(sy, ey)
            pen_white = g32.CreatePen(PS_SOLID, 2, 0x00FFFFFF)
            pen_dash = g32.CreatePen(PS_DASH, 1, 0x0000FF00)
            old_pen = g32.SelectObject(hdc, pen_white)
            old_brush = g32.SelectObject(hdc, NULL_BRUSH)
            g32.SetBkMode(hdc, TRANSPARENT)
            g32.Rectangle(hdc, x1, y1, x2, y2)
            g32.SelectObject(hdc, pen_dash)
            g32.Rectangle(hdc, x1 - 1, y1 - 1, x2 + 1, y2 + 1)
            g32.SelectObject(hdc, old_pen)
            g32.SelectObject(hdc, old_brush)
            g32.DeleteObject(pen_white)
            g32.DeleteObject(pen_dash)
            cross_pen = g32.CreatePen(PS_DASH, 1, 0x00808080)
            old_p = g32.SelectObject(hdc, cross_pen)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            from ctypes import windll
            windll.gdi32.MoveToEx(hdc, x1, cy, None)
            windll.gdi32.LineTo(hdc, x2, cy)
            windll.gdi32.MoveToEx(hdc, cx, y1, None)
            windll.gdi32.LineTo(hdc, cx, y2)
            g32.SelectObject(hdc, old_p)
            g32.DeleteObject(cross_pen)
        u32.EndPaint(hwnd, ctypes.byref(ps))
        return 0
    if msg == WM_LBUTTONDOWN:
        sx = lp & 0xFFFF
        sy = (lp >> 16) & 0xFFFF
        if sx > 32767:
            sx -= 65536
        if sy > 32767:
            sy -= 65536
        ex, ey = sx, sy
        dragging = True
        u32.InvalidateRect(hwnd, None, True)
        return 0
    if msg == WM_MOUSEMOVE:
        if dragging:
            ex = lp & 0xFFFF
            ey = (lp >> 16) & 0xFFFF
            if ex > 32767:
                ex -= 65536
            if ey > 32767:
                ey -= 65536
            u32.InvalidateRect(hwnd, None, True)
        return 0
    if msg == WM_LBUTTONUP:
        if dragging:
            ex = lp & 0xFFFF
            ey = (lp >> 16) & 0xFFFF
            if ex > 32767:
                ex -= 65536
            if ey > 32767:
                ey -= 65536
            dragging = False
            x1, y1 = min(sx, ex), min(sy, ey)
            x2, y2 = max(sx, ex), max(sy, ey)
            if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
                result_rect = (x1, y1, x2, y2)
                done = True
                u32.DestroyWindow(hwnd)
            else:
                u32.InvalidateRect(hwnd, None, True)
        return 0
    if msg == WM_KEYDOWN:
        if wp == VK_ESCAPE:
            done = True
            u32.DestroyWindow(hwnd)
            return 0
    if msg == WM_DESTROY:
        u32.PostQuitMessage(0)
        return 0
    return u32.DefWindowProcW(hwnd, msg, wp, lp)


def run():
    global hwnd_global
    hinst = k32.GetModuleHandleW(None)
    cls_name = "FranzSelector"
    wc = WNDCLASSEXW()
    wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
    wc.style = CS_HREDRAW | CS_VREDRAW
    wc.lpfnWndProc = WNDPROC(wndproc)
    wc.hInstance = hinst
    wc.hCursor = u32.LoadCursorW(None, ctypes.cast(IDC_CROSS, W.LPCWSTR))
    wc.hbrBackground = 0
    wc.lpszClassName = cls_name
    atom = u32.RegisterClassExW(ctypes.byref(wc))
    if not atom:
        print("ERR: RegisterClassExW failed", file=sys.stderr)
        return
    ex_style = WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW
    hwnd = u32.CreateWindowExW(
        ex_style, cls_name, "Franz Region Select",
        WS_POPUP | WS_VISIBLE,
        0, 0, sw, sh,
        None, None, hinst, None,
    )
    if not hwnd:
        print("ERR: CreateWindowExW failed", file=sys.stderr)
        return
    hwnd_global = hwnd
    u32.SetLayeredWindowAttributes(hwnd, 0x00000001, 0, LWA_COLORKEY)
    u32.ShowWindow(hwnd, 5)
    u32.UpdateWindow(hwnd)
    msg = W.MSG()
    while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        u32.TranslateMessage(ctypes.byref(msg))
        u32.DispatchMessageW(ctypes.byref(msg))
    if result_rect:
        px1, py1, px2, py2 = result_rect
        nx1 = round(px1 * 1000 / sw)
        ny1 = round(py1 * 1000 / sh)
        nx2 = round(px2 * 1000 / sw)
        ny2 = round(py2 * 1000 / sh)
        nx1 = max(0, min(1000, nx1))
        ny1 = max(0, min(1000, ny1))
        nx2 = max(0, min(1000, nx2))
        ny2 = max(0, min(1000, ny2))
        pw, ph = px2 - px1, py2 - py1
        print()
        print("=" * 72)
        print("FRANZ REGION SELECTOR RESULT")
        print("=" * 72)
        print(f"Screen:     {sw} x {sh}")
        print(f"Selected:   ({px1}, {py1}) -> ({px2}, {py2})  [{pw} x {ph} px]")
        print(f"Normalized: ({nx1}, {ny1}) -> ({nx2}, {ny2})")
        print()
        print("Copy this to config.py:")
        print()
        print(f'CAPTURE_CROP = {{"x1": {nx1}, "y1": {ny1}, "x2": {nx2}, "y2": {ny2}}}')
        print()
        print("Resize note: CAPTURE_CROP defines the region. CAPTURE_WIDTH/HEIGHT")
        print("resize AFTER cropping. Coordinate mapping is independent of resize.")
        print(f"Set CAPTURE_WIDTH=0, CAPTURE_HEIGHT=0 to keep native {pw}x{ph}.")
        print(f"Set CAPTURE_WIDTH={pw}, CAPTURE_HEIGHT={ph} for explicit same-size.")
        print("Set any other values to scale for the VLM (e.g. 512x288).")
        print("Normalized coords (0-1000) always map to the CROP region regardless.")
        print("=" * 72)
    else:
        print("Selection cancelled.")


if __name__ == "__main__":
    run()
