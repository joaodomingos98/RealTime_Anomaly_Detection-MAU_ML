# ------------------------------- Imports -------------------------------
import os
import sys
import platform
import subprocess
import threading
from datetime import datetime
from pathlib import Path

# OpenCV is required for the live preview (cv2).
# If it's missing in your venv, install it with:
#   pip install opencv-python
try:
    import cv2  # used for video/image processing and showing frames
except ModuleNotFoundError:
    cv2 = None

import tkinter as tk  # used for ToolTip Toplevel + a few Tk constants
import customtkinter as ctk
from PIL import Image, ImageTk

import serial
import serial.tools.list_ports

import pmain3


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "symbols"

# ------------------------------- Tooltip -------------------------------
class ToolTip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.delay = 500  # ms
        self.after_id = None

        widget.bind("<Enter>", self.schedule_tip)
        widget.bind("<Leave>", self.hide_tip)

    def schedule_tip(self, event=None):
        self.after_id = self.widget.after(self.delay, self.show_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            bg="#111827",
            fg="white",
            relief="solid",
            borderwidth=1,
            font=("Futura", 10),
            wraplength=280,
        )
        label.pack(ipadx=8, ipady=4)

    def hide_tip(self, event=None):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


# ------------------------------- Basic structure -------------------------------
BG_MAIN = "#E5E7EB"  # background
BG_PANEL = "#D4D8DE"  # panels and frames
BG_HEADER = "#5B677A"  # headers and top bar
BG_SOFT = "#F1F5F9"  # secondary surfaces
BG_DARK = "#0F172A"  # video / textbox

TEXT_PRIMARY = "#0F172A"
TEXT_SECONDARY = "#475569"
TEXT_INVERTED = "#FFFFFF"

STATUS_OK = "#22C55E"
STATUS_WARN = "#F59E0B"
STATUS_ERROR = "#EF4444"

FRAME_RADIUS = 18  # radius for frames/buttons
BTN_RADIUS = 18
LABEL_X = 18
VALUE_X = 135
BTN_X = VALUE_X + 90
WIN_W, WIN_H = 1200, 850

# ------------------------------- CTk app setup -------------------------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

window = ctk.CTk()
window.title("Occupancy Grid Review Frame")
window.configure(fg_color=BG_MAIN)

window.geometry(f"{WIN_W}x{WIN_H}")
window.minsize(1000, 720)
window.resizable(True, True)

content_frame = window


# ------------------------------- GUI helper methods -------------------------------
def createFrame(parentFrame, _bg, _highlightbackground, _x, _y, _width, _height, radius=FRAME_RADIUS):
    """Create and place a rounded CTkFrame. IMPORTANT: width/height must be in constructor for CTk."""
    frame = ctk.CTkFrame(
        parentFrame,
        fg_color=_bg,
        corner_radius=radius,
        border_width=1,
        border_color=_highlightbackground,
        width=_width,
        height=_height,
    )
    frame.place(x=_x, y=_y)
    return frame


def create_Label_Using_Config(parentFrame, packingSide, _padx, lblText, defaultText, _bg, fontSize, color):
    label = ctk.CTkLabel(
        parentFrame,
        text=(lblText or defaultText),
        text_color=color,
        fg_color=_bg,
        font=ctk.CTkFont(family="Futura", size=fontSize),
    )
    label.pack(side=packingSide, padx=_padx)
    return label


def create_Label_Using_Place(parentframe, _bg, _x, _y, _text, textSize, _wraplength, color):
    label = ctk.CTkLabel(
        parentframe,
        text=_text,
        text_color=color,
        fg_color=_bg,
        font=ctk.CTkFont(family="Futura", size=textSize),
        wraplength=_wraplength,
        justify="left",
    )
    label.place(x=_x, y=_y)
    return label


def create_TextBox(x_, y_, width_chars, height_lines, parentFrame):
    """Compact rounded value box"""
    px_w = int(width_chars * 10)     
    px_h = int(height_lines * 10) 

    textbox = ctk.CTkTextbox(
        parentFrame,
        width=px_w,
        height=px_h,
        fg_color=BG_DARK,
        text_color="white",

        corner_radius=12,          

        font=ctk.CTkFont(family="Futura", size=11),

        border_spacing=4
    )

    textbox.insert("1.0", "")
    textbox.configure(state="disabled")
    textbox.place(x=x_, y=y_)
    return textbox


def show(frame):
    frame.tkraise()

def set_active_tab(active_btn, inactive_btn):
    active_btn.configure(
        fg_color=BG_HEADER,
        text_color=TEXT_PRIMARY,
        border_width=1,
        border_color=BG_DARK
    )
    inactive_btn.configure(
        fg_color=BG_PANEL,
        text_color=TEXT_INVERTED,
        border_width=1
    )



def create_btn(Btnx, Btny, Btnwidth, Btnheight, btnText, parentFrame, isSubFrame, subFrame, methodCall):
    if isSubFrame:
        cmd = lambda: show(subFrame)
    else:
        cmd = methodCall if callable(methodCall) else (lambda: None)

    btn = ctk.CTkButton(
        parentFrame,
        text=btnText,
        command=cmd,
        width=Btnwidth,
        height=Btnheight,
        corner_radius=BTN_RADIUS,
        fg_color=BG_HEADER,
        hover_color="#4B5563",
        text_color=TEXT_INVERTED,
        font=ctk.CTkFont(family="Futura", size=12, weight="bold"),
    )
    btn.place(x=Btnx, y=Btny)
    return btn


def create_btn_with_image(picURL, imgW, imgH, parentFrame, methodCall, _x, _y):
    img = Image.open(ASSETS_DIR / "change.png").resize((36, 36), Image.LANCZOS) 
    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(imgW, imgH))

    btn = ctk.CTkButton(
        parentFrame,
        text="",
        image=ctk_img,
        command=methodCall if callable(methodCall) else (lambda: None),
        width=imgW,
        height=imgH,
        corner_radius=imgH // 2,
        fg_color=parentFrame.cget("fg_color"),
        hover_color=parentFrame.cget("fg_color"),
    )
    btn.place(x=_x, y=_y)
    return btn


# ------------------------------- App functions (kept mostly intact) -------------------------------
def createFolder():
    os.makedirs("results_Occupancy", exist_ok=True)


def get_wifi_name():
    os_name = platform.system()

    if os_name == "Windows":
        command = ["netsh", "wlan", "show", "interfaces"]
        result = subprocess.run(command, capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            if "SSID" in line and "BSSID" not in line:
                return line.split(":")[1].strip()

    elif os_name == "Darwin":
        command = [
            "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
            "-I",
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            if " SSID" in line:
                return line.split(":")[1].strip()

    elif os_name == "Linux":
        command = ["iwgetid", "-r"]
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout.strip()

    return None


def display_notes_text(text):
    notes_textbox.configure(state="normal")
    notes_textbox.insert(tk.END, text + "\n")
    notes_textbox.see(tk.END)
    notes_textbox.configure(state="disabled")


def display_status_text(text):
    status_textbox.configure(state="normal")
    status_textbox.insert(tk.END, text + "\n")
    status_textbox.see(tk.END)
    status_textbox.configure(state="disabled")


def clear_notes():
    notes_textbox.configure(state="normal")
    notes_textbox.delete("1.0", tk.END)
    notes_textbox.configure(state="disabled")


def find_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "USB" in port.description or "Arduino" in port.description or "CP210" in port.description:
            return port.device
    return None


# Live parameters
def update_live_parameter(tb, notesError, setter, notesVariable):
    try:
        value_str = tb.get("1.0", tk.END).strip()
        value = float(value_str)
    except ValueError:
        display_status_text(notesError)
        return

    setter(value)
    display_status_text(f"{notesVariable} changed to: {value}")


def set_value_TB(value, tb):
    tb.configure(state="normal")
    tb.delete("1.0", tk.END)
    tb.insert("1.0", str(value))
    tb.configure(state="normal")


def create_live_parameter_control(
    tb_x,
    tb_y,
    tb_w,
    tb_h,
    tb_parentFrame,
    lbl_x,
    lbl_y,
    lblText,
    btn_x,
    btn_y,
    notesError,
    variableChange,
    notesVariable,
):
    tb = create_TextBox(tb_x, tb_y, tb_w, tb_h, tb_parentFrame)
    lbl = create_Label_Using_Place(tb_parentFrame, BG_PANEL, lbl_x, lbl_y, lblText, 12, 200, TEXT_PRIMARY)
    create_btn_with_image(
        "symbols/change.png",
        23,
        23,
        tb_parentFrame,
        lambda: update_live_parameter(tb, notesError, variableChange, notesVariable),
        btn_x,
        btn_y,
    )
    return tb, lbl


# Preview update
fps_var = None 


def update_fps(fps):
    if fps_var is not None:
        fps_var.set(f"FPS: {fps:.1f}")


def update_preview(frame):
    if cv2 is None:
        return

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # resize to match preview window
    rgb = cv2.resize(rgb, (520, 290), interpolation=cv2.INTER_AREA)

    img = Image.fromarray(rgb)
    imgtk = ImageTk.PhotoImage(image=img)

    preview_label.imgtk = imgtk
    preview_label.configure(image=imgtk)



stop_event = threading.Event()


def start_recording():
    if cv2 is None:
        display_status_text("OpenCV (cv2) is missing. Install it: pip install opencv-python")
        return

    stop_event.clear()

    threading.Thread(
        target=pmain3.run,
        args=(update_preview, display_notes_text, stop_event, update_fps),
        daemon=True,
    ).start()

    display_status_text("Recording started")

def stop_recording():
    stop_event.set()
    preview_label.configure(image=None)
    clear_notes()
    display_status_text("Recording stopped")

def reset_values():
    pmain3.MIN_CONFIDENCE = 0.35
    pmain3.MIN_AREA = 100
    pmain3.MAX_AREA = float("inf")
    pmain3.ASPECT_RATIO_MIN = 0.25
    pmain3.ASPECT_RATIO_MAX = 4.0
    pmain3.VIDEO_FPS_VALUE = 5
    pmain3.DRAW_BOXES = True

    set_value_TB(pmain3.MIN_CONFIDENCE, confTB[0])
    set_value_TB(pmain3.MIN_AREA, MIN_AREA_TB[0])
    set_value_TB(pmain3.MAX_AREA, MAX_AREA_TB[0])
    set_value_TB(pmain3.ASPECT_RATIO_MIN, ASPECT_RATIO_MIN_TB[0])
    set_value_TB(pmain3.ASPECT_RATIO_MAX, ASPECT_RATIO_MAX_TB[0])
    set_value_TB(pmain3.VIDEO_FPS_VALUE, VIDEO_FPS_TB[0])

    draw_boxes_var.set(True)
    display_status_text("Parameters reset to default")


def set_stable_values():
    pmain3.MIN_CONFIDENCE = 0.35
    pmain3.MIN_AREA = 100
    pmain3.MAX_AREA = float("inf")
    pmain3.ASPECT_RATIO_MIN = 0.25
    pmain3.ASPECT_RATIO_MAX = 4.0
    pmain3.VIDEO_FPS_VALUE = 5
    pmain3.DRAW_BOXES = True

    reset_values()
    display_status_text("Parameters set to stable")


def set_sensitive_values():
    pmain3.MIN_CONFIDENCE = 0.30
    pmain3.MIN_AREA = 80
    pmain3.MAX_AREA = float("inf")
    pmain3.ASPECT_RATIO_MIN = 0.20
    pmain3.ASPECT_RATIO_MAX = 4.5
    pmain3.VIDEO_FPS_VALUE = 8
    pmain3.DRAW_BOXES = True

    set_value_TB(pmain3.MIN_CONFIDENCE, confTB[0])
    set_value_TB(pmain3.MIN_AREA, MIN_AREA_TB[0])
    set_value_TB(pmain3.MAX_AREA, MAX_AREA_TB[0])
    set_value_TB(pmain3.ASPECT_RATIO_MIN, ASPECT_RATIO_MIN_TB[0])
    set_value_TB(pmain3.ASPECT_RATIO_MAX, ASPECT_RATIO_MAX_TB[0])
    set_value_TB(pmain3.VIDEO_FPS_VALUE, VIDEO_FPS_TB[0])

    draw_boxes_var.set(True)
    display_status_text("Parameters set to sensitive")


# ------------------------------- Settings window -------------------------------
def open_settings_window():
    popUpSettings = ctk.CTkToplevel(window)
    popUpSettings.title("Settings")
    popUpSettings.geometry("1000x650")
    popUpSettings.configure(fg_color=BG_MAIN)

    # main container
    settingsFrame = createFrame(popUpSettings, BG_PANEL, BG_DARK, 20, 20, 960, 600, radius=FRAME_RADIUS)

    # RIGHT: About us
    aboutUsFrame = createFrame(settingsFrame, BG_PANEL, BG_DARK, 680, 20, 260, 560, radius=FRAME_RADIUS)
    create_Label_Using_Place(aboutUsFrame, BG_PANEL, 20, 20, "About us", 32, 220, TEXT_PRIMARY)

    about_text = (
        "We are a team of 8 students who developed this product as our thesis project. "
        "The system collects indoor radar data and uses machine learning to estimate occupancy. "
        "A camera running YOLOv13 provides ground-truth data synchronized with the radar for training. "
        "Once trained, the radar alone can estimate the number of people in real time, "
        "with the camera used only for optional validation."
    )
    create_Label_Using_Place(aboutUsFrame, BG_PANEL, 20, 110, about_text, 16, 220, TEXT_PRIMARY)

    # LEFT TOP: Recommended specifications
    specsFrameOut = createFrame(settingsFrame, BG_PANEL, BG_DARK, 20, 20, 640, 340, radius=FRAME_RADIUS)
    create_Label_Using_Place(specsFrameOut, BG_PANEL, 40, 20, "Recommended specifications", 32, 600, TEXT_PRIMARY)

    # Tabs row
    tab_y = 105
    create_btn(40, tab_y, 130, 40, "Radar", specsFrameOut, False, None, None)
    create_btn(200, tab_y, 130, 40, "Hardware", specsFrameOut, False, None, None)
    create_btn(360, tab_y, 130, 40, "Camera", specsFrameOut, False, None, None)

    # Inner content area
    tab_container = createFrame(specsFrameOut, BG_PANEL, BG_DARK, 40, 160, 560, 160, radius=FRAME_RADIUS)

    radarFrame = ctk.CTkFrame(tab_container, fg_color=BG_PANEL, corner_radius=FRAME_RADIUS, width=560, height=160)
    hardwareFrame = ctk.CTkFrame(tab_container, fg_color=BG_PANEL, corner_radius=FRAME_RADIUS, width=560, height=160)
    cameraFrame = ctk.CTkFrame(tab_container, fg_color=BG_PANEL, corner_radius=FRAME_RADIUS, width=560, height=160)

    for f in (radarFrame, hardwareFrame, cameraFrame):
        f.place(x=0, y=0)

    # tab switching (keep simple)
    def _show_tab(f):
        f.tkraise()

    # re-bind the buttons to switch
    create_btn(40, tab_y, 130, 40, "Radar", specsFrameOut, False, None, lambda: _show_tab(radarFrame))
    create_btn(200, tab_y, 130, 40, "Hardware", specsFrameOut, False, None, lambda: _show_tab(hardwareFrame))
    create_btn(360, tab_y, 130, 40, "Camera", specsFrameOut, False, None, lambda: _show_tab(cameraFrame))

    # Radar tab content
    create_Label_Using_Place(radarFrame, BG_PANEL, 240, 15, "Radar", 28, 500, TEXT_PRIMARY)
    radar_txt = (
        "Radar name: HMMD mmWave\n"
        "Radar chip: S3KM1110\n"
        "Communication method: UART\n"
        "Radar baud rate: 115200"
    )
    create_Label_Using_Place(radarFrame, BG_PANEL, 40, 70, radar_txt, 18, 520, TEXT_PRIMARY)

    # Hardware tab content
    create_Label_Using_Place(hardwareFrame, BG_PANEL, 220, 15, "Hardware", 28, 500, TEXT_PRIMARY)
    hw_txt = (
        "Hardware name: Jetson Nano\n"
        "UART-pins: 40-pin header\n"
        "Baud rate: 115200"
    )
    create_Label_Using_Place(hardwareFrame, BG_PANEL, 40, 70, hw_txt, 18, 520, TEXT_PRIMARY)

    # Camera tab content
    create_Label_Using_Place(cameraFrame, BG_PANEL, 235, 15, "Camera", 28, 500, TEXT_PRIMARY)
    cam_txt = (
        "Processor: Dual-core Tensilica LX6, 240 MHz\n"
        "Memory: 4 MB PSRAM, 32 Mbit flash\n"
        "Wireless: Wi-Fi 802.11 b/g/n, Bluetooth 4.2\n"
        "Camera: OV2640, 2 MP, JPEG\n"
        "GPIO: UART, SPI, I²C, PWM"
    )
    create_Label_Using_Place(cameraFrame, BG_PANEL, 40, 60, cam_txt, 16, 520, TEXT_PRIMARY)

    _show_tab(radarFrame)

    # LEFT BOTTOM: Other
    otherFrame = createFrame(settingsFrame, BG_PANEL, BG_DARK, 20, 380, 640, 200, radius=FRAME_RADIUS)
    create_Label_Using_Place(otherFrame, BG_PANEL, 280, 20, "Other", 36, 500, TEXT_PRIMARY)

    create_btn(
        int((640 - 200) / 2),
        110,
        200,
        45,
        "Create folder",
        otherFrame,
        False,
        None,
        createFolder
    )



# ------------------------------- Build GUI -------------------------------
# Hero bar
heroFrame = createFrame(content_frame, BG_HEADER, BG_HEADER, 0, 0, WIN_W, 60, radius=0)

# Date label
date_label = ctk.CTkLabel(
    heroFrame,
    text="",
    text_color=TEXT_INVERTED,
    fg_color=BG_HEADER,
    font=ctk.CTkFont(family="Futura", size=16, weight="bold"),
)
date_label.place(x=540, y=18)


def update_date():
    current_date = datetime.now().strftime("%Y-%m-%d")
    date_label.configure(text=current_date)


update_date()

# Settings button (image)
settings_img = Image.open(ASSETS_DIR / "settings.png").resize((36, 36), Image.LANCZOS) 
settings_ctk_img = ctk.CTkImage(light_image=settings_img, dark_image=settings_img, size=(36, 36))
settingsBtn = ctk.CTkButton(
    heroFrame,
    text="",
    image=settings_ctk_img,
    command=open_settings_window,
    width=40,
    height=40,
    corner_radius=20,
    fg_color=BG_HEADER,
    hover_color=BG_HEADER,
)
settingsBtn.place(x=10, y=10)

# WiFi frame + icon + label
wifi_frame = createFrame(content_frame, BG_HEADER, BG_HEADER, 1064, 8, 210, 45, radius=0)

wifi_inner = ctk.CTkFrame(
    wifi_frame,
    fg_color="transparent",
    width=210 - 24,
    height=45 - 12
)
wifi_inner.place(x=12, y=6)

wifi_img = Image.open(ASSETS_DIR / "wifi.webp").resize((36, 36), Image.LANCZOS) 
wifi_ctk_img = ctk.CTkImage(light_image=wifi_img, dark_image=wifi_img, size=(28, 28))

wifi_icon = ctk.CTkLabel(wifi_inner, text="", image=wifi_ctk_img, fg_color="transparent")
wifi_icon.pack(side="right", padx=(0, 6))

wifi_name = get_wifi_name() or "No Wifi"
wifi_lbl = ctk.CTkLabel(
    wifi_inner,
    text=wifi_name,
    text_color=TEXT_INVERTED,
    fg_color="transparent", 
    font=ctk.CTkFont(family="Futura", size=12, weight="bold"),
)
wifi_lbl.pack(side="left")

CONTAINER_X, CONTAINER_Y = 48, 110
CONTAINER_W, CONTAINER_H = 1040, 460
container = createFrame(content_frame, BG_PANEL, BG_DARK, CONTAINER_X, CONTAINER_Y, CONTAINER_W, CONTAINER_H, radius=FRAME_RADIUS)
INNER_PAD = 10

YoloCameraFrame = ctk.CTkFrame(
    container,
    fg_color=BG_PANEL,
    corner_radius=FRAME_RADIUS,
    width=CONTAINER_W - INNER_PAD * 2,
    height=CONTAINER_H - INNER_PAD * 2,
)
reviewFrame = ctk.CTkFrame(
    container,
    fg_color=BG_PANEL,
    corner_radius=FRAME_RADIUS,
    width=CONTAINER_W - INNER_PAD * 2,
    height=CONTAINER_H - INNER_PAD * 2,
)

for frame in (reviewFrame, YoloCameraFrame):
    frame.place(x=INNER_PAD, y=INNER_PAD)

# Top navigation buttons
data_btn = create_btn(
    48, 65, 170, 30,
    "Data collection",
    content_frame,
    False,
    None,
    None
)

eval_btn = create_btn(
    258, 65, 170, 30,
    "Evaluation",
    content_frame,
    False,
    None,
    None
)

def show_data_collection():
    show(YoloCameraFrame)
    set_active_tab(data_btn, eval_btn)

def show_evaluation():
    show(reviewFrame)
    set_active_tab(eval_btn, data_btn)

data_btn.configure(command=show_data_collection)
eval_btn.configure(command=show_evaluation)

show_data_collection()


show(YoloCameraFrame)

GAP_Y = 10      
NOTES_H = 150
GAP_X = 20         

NOTES_Y = 590

TOTAL_WIDTH = 1036
FRAME_W = (TOTAL_WIDTH - GAP_X) // 2

LEFT_X  = 50 
RIGHT_X = LEFT_X + FRAME_W + GAP_X


# -------------------- Notes --------------------
notesFrame = createFrame(
    content_frame,
    BG_PANEL,
    BG_DARK,
    LEFT_X,
    NOTES_Y,
    FRAME_W,
    NOTES_H,
    radius=FRAME_RADIUS
)

create_Label_Using_Place(
    notesFrame,
    BG_PANEL,
    14, 8,
    "Notes",
    22, 400,
    TEXT_PRIMARY
)

notes_textbox = ctk.CTkTextbox(
    notesFrame,
    width=FRAME_W - 32,
    height=NOTES_H - 60,
    fg_color=BG_DARK,
    text_color="white",
    corner_radius=FRAME_RADIUS,
    font=ctk.CTkFont(family="Futura", size=12),
)
notes_textbox.place(x=16, y=48)
notes_textbox.configure(state="disabled")


# -------------------- Status --------------------
statusFrame = createFrame(
    content_frame,
    BG_PANEL,
    BG_DARK,
    RIGHT_X,
    NOTES_Y,
    FRAME_W,
    NOTES_H,
    radius=FRAME_RADIUS
)

create_Label_Using_Place(
    statusFrame,
    BG_PANEL,
    14, 8,
    "Status",
    22, 400,
    TEXT_PRIMARY
)

status_textbox = ctk.CTkTextbox(
    statusFrame,
    width=FRAME_W - 32,
    height=NOTES_H - 60,
    fg_color=BG_DARK,
    text_color="white",
    corner_radius=FRAME_RADIUS,
    font=ctk.CTkFont(family="Futura", size=12),
)
status_textbox.place(x=16, y=48)
status_textbox.configure(state="disabled")




# ------------------------------- REVIEW FRAME -------------------------------
modelReviewFrame = createFrame(reviewFrame, BG_PANEL, BG_DARK, 14, 14, 1060, 160, radius=18)

create_Label_Using_Place(
    modelReviewFrame, BG_PANEL, 14, 14,
    "Model Review: Compare Radar",
    24, 900, TEXT_PRIMARY
)

# Run Review button (left)
create_btn(20, 92, 180, 40, "Run Review", modelReviewFrame, False, None, None)

# Helper: small value box (dark)
def _metric_box(parent, x, y):
    entry = ctk.CTkEntry(
        parent,
        width=70,
        height=28,
        corner_radius=4,
        fg_color=BG_DARK,
        text_color="white",
        border_width=1,
        border_color="#111827",
        font=ctk.CTkFont(family="Futura", size=12, weight="bold"),
    )
    entry.place(x=x, y=y)
    entry.configure(state="disabled")
    return entry

# MAE
create_Label_Using_Place(modelReviewFrame, BG_PANEL, 250, 98, "MAE:", 14, 100, TEXT_PRIMARY)
mae_box = _metric_box(modelReviewFrame, 305, 94)

# RMSE
create_Label_Using_Place(modelReviewFrame, BG_PANEL, 410, 98, "RMSE:", 14, 100, TEXT_PRIMARY)
rmse_box = _metric_box(modelReviewFrame, 475, 94)

# Corr
create_Label_Using_Place(modelReviewFrame, BG_PANEL, 585, 98, "Corr:", 14, 100, TEXT_PRIMARY)
corr_box = _metric_box(modelReviewFrame, 640, 94)

def set_metric(entry, value):
    entry.configure(state="normal")
    entry.delete(0, "end")
    entry.insert(0, f"{value:.2f}")
    entry.configure(state="disabled")

# example:
# set_metric(mae_box, 1.23)
# set_metric(rmse_box, 2.34)
# set_metric(corr_box, 0.91)

# ------------------------------- YOLO FRAME -------------------------------
fps_var = tk.StringVar(master=window, value="FPS: -")

title_lbl = ctk.CTkLabel(
    YoloCameraFrame,
    text="IP adress for camera stream",
    text_color=TEXT_PRIMARY,
    fg_color=BG_PANEL,
    font=ctk.CTkFont(family="Futura", size=14, weight="bold"),
)
title_lbl.place(x=18, y=18)

ip_entry = ctk.CTkEntry(
    YoloCameraFrame,
    width=240,
    height=30,
    corner_radius=15,
    fg_color=BG_DARK,
    text_color="white",
    border_color="#111827",
    border_width=1,
    font=ctk.CTkFont(family="Futura", size=12, weight="bold"),
)
ip_entry.place(x=330, y=16)
ip_entry.insert(0, "169.254.41.207")
ip_entry.configure(state="disabled")

# Rounded preview box + label
preview_box = ctk.CTkFrame(
    YoloCameraFrame,
    fg_color=BG_DARK,
    corner_radius=FRAME_RADIUS,
    width=520,
    height=290,
    border_width=1,
    border_color="#111827",
)
preview_box.place(x=390, y=100)

preview_label = tk.Label(preview_box, bg="black")
preview_label.place(x=0, y=0, width=520, height=290)

# FPS label
fps_label = ctk.CTkLabel(
    YoloCameraFrame,
    textvariable=fps_var,
    fg_color=BG_PANEL,
    text_color=TEXT_PRIMARY,
    font=ctk.CTkFont(family="Futura", size=14, weight="bold"),
)
fps_label.place(x=950, y=115)

# Parameter controls (aligned column)
confTB = create_live_parameter_control(
    VALUE_X,
    110,
    6,
    1.2,
    YoloCameraFrame,
    LABEL_X,
    110,
    "Confidence",
    BTN_X,
    110,
    "Invalid confidence value",
    lambda v: setattr(pmain3, "MIN_CONFIDENCE", v),
    "Confidence",
)
set_value_TB(pmain3.MIN_CONFIDENCE, confTB[0])
ToolTip(
    confTB[1],
    "Minimum confidence score required for a detection to be counted as a person.\nHigher reduces false positives.\nLower increases sensitivity.",
)

MIN_AREA_TB = create_live_parameter_control(
    VALUE_X,
    160,
    6,
    1.2,
    YoloCameraFrame,
    LABEL_X,
    160,
    "Minimum area",
    BTN_X,
    160,
    "Invalid minimum area value",
    lambda v: setattr(pmain3, "MIN_AREA", v),
    "Minimum area",
)
set_value_TB(pmain3.MIN_AREA, MIN_AREA_TB[0])
ToolTip(MIN_AREA_TB[1], "Minimum bounding box area in pixels.\nFilters small/partial detections.")

MAX_AREA_TB = create_live_parameter_control(
    VALUE_X,
    210,
    6,
    1.2,
    YoloCameraFrame,
    LABEL_X,
    210,
    "Maximum area",
    BTN_X,
    210,
    "Invalid maximum area value",
    lambda v: setattr(pmain3, "MAX_AREA", v),
    "Maximum area",
)
set_value_TB(pmain3.MAX_AREA, MAX_AREA_TB[0])
ToolTip(MAX_AREA_TB[1], "Maximum allowed bounding box area in pixels.\nHelps prevent huge false positives.")

ASPECT_RATIO_MIN_TB = create_live_parameter_control(
    VALUE_X,
    260,
    5,
    1.2,
    YoloCameraFrame,
    LABEL_X,
    260,
    "Aspect Ratio Min",
    BTN_X,
    260,
    "Invalid Aspect Ratio Min value",
    lambda v: setattr(pmain3, "ASPECT_RATIO_MIN", v),
    "Aspect Ratio Min",
)
set_value_TB(pmain3.ASPECT_RATIO_MIN, ASPECT_RATIO_MIN_TB[0])
ToolTip(ASPECT_RATIO_MIN_TB[1], "Minimum height/width ratio.\nFilters shapes that don't look like a person.")

ASPECT_RATIO_MAX_TB = create_live_parameter_control(
    VALUE_X,
    310,
    5,
    1.2,
    YoloCameraFrame,
    LABEL_X,
    310,
    "Aspect Ratio Max",
    BTN_X,
    310,
    "Invalid Aspect Ratio Max value",
    lambda v: setattr(pmain3, "ASPECT_RATIO_MAX", v),
    "Aspect Ratio Max",
)
set_value_TB(pmain3.ASPECT_RATIO_MAX, ASPECT_RATIO_MAX_TB[0])
ToolTip(ASPECT_RATIO_MAX_TB[1], "Maximum height/width ratio.\nPrevents extremely tall/narrow false detections.")

VIDEO_FPS_TB = create_live_parameter_control(
    VALUE_X,
    360,
    3,
    1.2,
    YoloCameraFrame,
    LABEL_X,
    360,
    "Frames per second",
    BTN_X,
    360,
    "Invalid FPS value",
    lambda v: setattr(pmain3, "VIDEO_FPS_VALUE", v),
    "FPS",
)
set_value_TB(pmain3.VIDEO_FPS_VALUE, VIDEO_FPS_TB[0])
ToolTip(VIDEO_FPS_TB[1], "Target processing frame rate.\nLower = less CPU load. Higher = smoother.")

# Draw boxes checkbox
draw_boxes_var = tk.BooleanVar(master=window, value=getattr(pmain3, "DRAW_BOXES", True))


def toggle_draw_boxes():
    pmain3.DRAW_BOXES = draw_boxes_var.get()
    display_status_text(f"Draw boxes set to: {pmain3.DRAW_BOXES}")


draw_boxes_cb = ctk.CTkCheckBox(
    YoloCameraFrame,
    text="Show bounding boxes",
    variable=draw_boxes_var,
    command=toggle_draw_boxes,
    fg_color=BG_HEADER,
    text_color=TEXT_PRIMARY,
    font=ctk.CTkFont(family="Futura", size=12, weight="bold"),
)
draw_boxes_cb.place(x=LABEL_X, y=410)

create_btn(LABEL_X, 450, 90, 32, "Stable", YoloCameraFrame, False, None, set_stable_values)
create_btn(LABEL_X + 110, 450, 110, 32, "Sensitive", YoloCameraFrame, False, None, set_sensitive_values)

BTN_WIDTH  = 150
BTN_HEIGHT = 32
BTN_GAP    = 40

BTN_Y = 400

SHIFT_RIGHT = 112

TOTAL = BTN_WIDTH * 3 + BTN_GAP * 2
START_X = int((1100 - INNER_PAD * 2 - TOTAL) / 2) + SHIFT_RIGHT


create_btn(
    START_X,
    BTN_Y,
    BTN_WIDTH,
    BTN_HEIGHT,
    "Stop recording",
    YoloCameraFrame,
    False,
    None,
    stop_recording,
)

create_btn(
    START_X + BTN_WIDTH + BTN_GAP,
    BTN_Y,
    BTN_WIDTH,
    BTN_HEIGHT,
    "Start recording",
    YoloCameraFrame,
    False,
    None,
    start_recording,
)

create_btn(
    START_X + 2 * (BTN_WIDTH + BTN_GAP),
    BTN_Y,
    BTN_WIDTH,
    BTN_HEIGHT,
    "Reset values",
    YoloCameraFrame,
    False,
    None,
    reset_values,
)

# Initial message if cv2 missing
if cv2 is None:
    display_status_text("OpenCV (cv2) is missing. Install it inside your venv:\n  pip install opencv-python")

window.mainloop()