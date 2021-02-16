# Our convertion from millimeters to inches
MM_TO_IN = 0.0393700787

# Import the libraries
import ctypes
import math
import tkinter

# Set process DPI awareness
ctypes.windll.shcore.SetProcessDpiAwareness(1)
# Create a tkinter window
root = tkinter.Tk()
# Get a DC from the window's HWND
dc = ctypes.windll.user32.GetDC(root.winfo_id())
# The the monitor phyical width
# (returned in millimeters then converted to inches)
mw = ctypes.windll.gdi32.GetDeviceCaps(dc, 4) * MM_TO_IN
# The the monitor phyical height
mh = ctypes.windll.gdi32.GetDeviceCaps(dc, 6) * MM_TO_IN
# Get the monitor horizontal resolution
dw = ctypes.windll.gdi32.GetDeviceCaps(dc, 8)
print(dw)
dw = root.winfo_screenwidth()
print(dw)

# Get the monitor vertical resolution
dh = ctypes.windll.gdi32.GetDeviceCaps(dc, 10)
print(dh)
dh = root.winfo_screenheight()
print(dh)
# Destroy the window
root.destroy()

# Horizontal and vertical DPIs calculated
hdpi, vdpi = dw / mw, dh / mh
# Diagonal DPI calculated using Pythagoras
ddpi = math.hypot(dw, dh) / math.hypot(mw, mh)
# Print the DPIs
print(round(hdpi, 1), round(vdpi, 1), round(ddpi, 1))
