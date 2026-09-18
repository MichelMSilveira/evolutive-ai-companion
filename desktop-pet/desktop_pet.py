import json
import random
import math
import tkinter as tk
from tkinter import messagebox
import time
import keyboard
import mss
import mss.tools
import tempfile
from pathlib import Path

try:
    import win32api
    import win32con
    import win32gui
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

ROOT = Path(__file__).resolve().parent
IMAGE = ROOT.parent / "mascot-runtime" / "public" / "nova-placeholder.png"
STATE = ROOT / "nova-state.json"
YARD_CONFIG = ROOT / "yard-config.json"
CONVERSATION = ROOT.parent / "voice-engine" / "conversation.json"
CAPTION_LIVE = ROOT / "caption-live.json"
VISION_RESPONSE = ROOT / "vision-response.json"
VISION_REQUEST = ROOT / "vision-request.json"
STOP_REQUEST = ROOT / "nova-stop.json"
CONSOLE_LOG = ROOT / "nova-console.log"
CAPTION_POSITION = "below"
VOICE_KEY = "add"
VISION_KEY = "-"
YARD_KEY = "ctrl+shift+y"
STATUS_KEY = "ctrl+shift+s"
TEXT_KEY = "ctrl+shift+t"
WANDER_KEY = "ctrl+shift+w"
RESET_KEY = "ctrl+shift+r"
SESSION_STARTED_AT = time.time()
caption_mode = {"value": "auto"}

default_state = {"name": "Nova", "level": 1, "xp": 0, "mood": "happy"}
default_yard = {
    "name": "Quintal da Nova",
    "width": 8.0,
    "depth": 6.0,
    "height": 3.0,
    "theme": "natural",
    "privacy": "local",
    "objects": [],
}
try:
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else default_state
except (OSError, json.JSONDecodeError):
    state = default_state
try:
    yard_config = {**default_yard, **json.loads(YARD_CONFIG.read_text(encoding="utf-8"))} if YARD_CONFIG.exists() else default_yard.copy()
except (OSError, json.JSONDecodeError):
    yard_config = default_yard.copy()

window = tk.Tk()
window.title("Nova")
window.overrideredirect(True)
window.attributes("-topmost", True)
window.configure(bg="#07111f")
window.wm_attributes("-transparentcolor", "#07111f")

canvas = tk.Canvas(window, width=240, height=370, bg="#07111f", highlightthickness=0)
canvas.pack()
frame_paths = [IMAGE]
images = [tk.PhotoImage(file=str(path)).subsample(3) for path in frame_paths if path.exists()]
behavior_paths = [ROOT / f"behavior-polished-{i}.png" for i in range(4)]
behavior_images = [tk.PhotoImage(file=str(path)).subsample(3) for path in behavior_paths if path.exists()]
walk_paths = [ROOT / f"walk-fixed-{i}.png" for i in range(8)]
walk_images = [tk.PhotoImage(file=str(path)).subsample(3) for path in walk_paths if path.exists()]
if not images:
    images = [tk.PhotoImage(file=str(IMAGE)).subsample(max(1, tk.PhotoImage(file=str(IMAGE)).width() // 190))]
# Os frames antigos de caminhada tinham poses assimétricas e ocultavam uma pata
# em algumas fases. Enquanto os frames articulados não forem refeitos a partir
# do mesmo sprite-base, usamos o personagem íntegro e deixamos o deslocamento
# da janela + o balanço vertical comunicarem a caminhada sem deformações.
# O ciclo completo usa os oito frames refeitos: 0–3 para a direita e 4–7
# para a esquerda. Todos foram derivados do mesmo sprite-base, com escala,
# linha dos pés e anatomia padronizadas.
if len(walk_images) < 8:
    walk_images = [images[0]] * 8
def restore_borderless(_event=None):
    if window.state() == "normal":
        window.overrideredirect(True)
        window.attributes("-topmost", True)
sprite = canvas.create_image(120, 200, image=images[0])
label = canvas.create_text(120, 258, text="", fill="#b7ffd0", font=("Segoe UI", 10, "bold"))
bubble = canvas.create_text(120, 35, text="", fill="#ffffff", font=("Segoe UI", 11, "bold"), state="hidden")
caption_window = tk.Toplevel(window)
caption_window.overrideredirect(True)
caption_window.attributes("-topmost", True)
caption_window.attributes("-alpha", 0.94)
caption_window.configure(bg="#101a2d")
caption_header = tk.Frame(caption_window, bg="#0d2639", height=30, cursor="fleur")
caption_header.pack(fill="x")
caption_header.pack_propagate(False)
caption_title = tk.Label(caption_header, text="NOVA  •  TEXTO E TRADUÇÕES", bg="#0d2639", fg="#73f5a5", anchor="w", padx=14, font=("Segoe UI", 10, "bold"))
caption_title.pack(side="left", fill="y")
caption_controls = tk.Frame(caption_header, bg="#0d2639")
caption_controls.pack(side="right", fill="y")

def request_nova_stop():
    """Send a lightweight stop signal to the independent voice process."""
    STOP_REQUEST.write_text(json.dumps({"requested_at": time.time(), "source": "desktop-button"}, ensure_ascii=False), encoding="utf-8")
    stop_voice_capture()
    canvas.itemconfigure(bubble, text="Parei.", state="normal")
    window.after(1600, lambda: canvas.itemconfigure(bubble, state="hidden"))

stop_button = tk.Button(caption_controls, text="PARAR NOVA", command=request_nova_stop, bg="#7d3544", fg="#ffffff", activebackground="#a8495b", activeforeground="#ffffff", relief="flat", bd=0, padx=8, font=("Segoe UI", 8, "bold"))
stop_button.pack(side="left", padx=(0, 4), pady=4)
caption_mode_button = tk.Button(caption_controls, text="AUTO", command=lambda: cycle_caption_mode(), bg="#173a50", fg="#9fe8ff", activebackground="#245875", activeforeground="#ffffff", relief="flat", bd=0, padx=8, font=("Segoe UI", 8, "bold"))
caption_mode_button.pack(side="left", padx=(0, 4), pady=4)
caption_hide_button = tk.Button(caption_controls, text="−", command=lambda: caption_window.withdraw(), bg="#173a50", fg="#d7e8ff", activebackground="#245875", activeforeground="#ffffff", relief="flat", bd=0, width=2, font=("Segoe UI", 10, "bold"))
caption_hide_button.pack(side="left", padx=2, pady=4)
caption_close_button = tk.Button(caption_controls, text="×", command=lambda: caption_window.withdraw(), bg="#173a50", fg="#ff9da9", activebackground="#7d3544", activeforeground="#ffffff", relief="flat", bd=0, width=2, font=("Segoe UI", 10, "bold"))
caption_close_button.pack(side="left", padx=(2, 8), pady=4)
caption_legend = tk.Label(caption_window, text="Você  •  Nova  •  inglês  •  português  •  visão  •  sistema", bg="#101a2d", fg="#7f97b5", anchor="w", padx=14, pady=4, font=("Segoe UI", 8))
caption_legend.pack(fill="x")
caption_label = tk.Text(caption_window, bg="#101a2d", fg="#a8bad2", width=112, height=8, wrap="word", padx=16, pady=10, font=("Segoe UI", 10), relief="flat", bd=0)
caption_label.tag_configure("past", foreground="#ffffff")
caption_label.tag_configure("active", foreground="#55f28b", underline=True)
caption_label.tag_configure("future", foreground="#777777")
caption_label.tag_configure("console_user", foreground="#8bd4ff")
caption_label.tag_configure("console_nova", foreground="#73f5a5")
caption_label.tag_configure("console_english", foreground="#ffd166")
caption_label.tag_configure("console_portuguese", foreground="#c5a3ff")
caption_label.tag_configure("console_vision", foreground="#65e5ff")
caption_label.tag_configure("console_system", foreground="#a8bad2")
caption_label.tag_configure("console_error", foreground="#ff7b8a")
caption_label.insert("1.0", "Aguardando conversa...", "future")
caption_label.configure(state="disabled")
caption_label.pack(fill="both", expand=True)
caption_resize_grip = tk.Label(caption_window, text="◢", bg="#101a2d", fg="#4e7897", cursor="size_nw_se", font=("Segoe UI", 11))
caption_resize_grip.place(relx=1.0, rely=1.0, anchor="se", width=18, height=18)

caption_drag = {"x": 0, "y": 0}
caption_resize = {"x": 0, "y": 0, "width": 0, "height": 0}

def start_caption_drag(event):
    caption_drag["x"] = event.x_root - caption_window.winfo_x()
    caption_drag["y"] = event.y_root - caption_window.winfo_y()

def move_caption_drag(event):
    caption_window.geometry(f"+{event.x_root - caption_drag['x']}+{event.y_root - caption_drag['y']}")

def start_caption_resize(event):
    caption_resize.update({"x": event.x_root, "y": event.y_root, "width": caption_window.winfo_width(), "height": caption_window.winfo_height()})

def move_caption_resize(event):
    width = max(520, caption_resize["width"] + event.x_root - caption_resize["x"])
    height = max(110, caption_resize["height"] + event.y_root - caption_resize["y"])
    caption_window.geometry(f"{width}x{height}+{caption_window.winfo_x()}+{caption_window.winfo_y()}")

for drag_target in (caption_header, caption_title):
    drag_target.bind("<ButtonPress-1>", start_caption_drag)
    drag_target.bind("<B1-Motion>", move_caption_drag)
caption_resize_grip.bind("<ButtonPress-1>", start_caption_resize)
caption_resize_grip.bind("<B1-Motion>", move_caption_resize)
caption_window.update_idletasks()
screen_width = caption_window.winfo_screenwidth()
screen_height = caption_window.winfo_screenheight()
caption_window.geometry(f"1000x180+{max(0, (screen_width - 1000) // 2)}+{max(0, screen_height - 245)}")
caption_window.protocol("WM_DELETE_WINDOW", lambda: caption_window.withdraw())

status_window = tk.Toplevel(window)
status_window.overrideredirect(True)
status_window.attributes("-topmost", True)
status_window.attributes("-alpha", 0.96)
status_window.configure(bg="#0a1728")
status_canvas = tk.Canvas(status_window, width=150, height=315, bg="#0a1728", highlightthickness=0)
status_canvas.pack()
status_canvas.create_rectangle(3, 3, 147, 312, fill="#10233d", outline="#35d07f", width=1)
status_canvas.create_text(75, 25, text="NOVA STATUS", fill="#73f5a5", font=("Segoe UI", 10, "bold"))
status_minimize = tk.Label(status_window, text="−", bg="#173a50", fg="#d7e8ff", cursor="hand2", font=("Segoe UI", 11, "bold"), width=2)
status_minimize.place(relx=1.0, x=-8, y=7, anchor="ne")
status_minimize.bind("<Button-1>", lambda _event: toggle_status_panel())

status_controls = tk.Frame(status_window, bg="#10233d")
status_controls.pack(fill="x", padx=4, pady=(0, 5))

def show_caption_window():
    caption_window.deiconify()
    caption_window.lift()

def reset_nova_position():
    """Stop wandering and return Nova to a predictable desktop corner."""
    movement["pinned"] = True
    movement["walking"] = False
    movement["mode"] = "cuddling"
    movement["walk_token"] += 1
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    window.geometry(f"+{max(0, screen_w - 430)}+{max(20, screen_h - 535)}")
    position_status_window()
    canvas.itemconfigure(bubble, text="Voltei para o meu cantinho.", state="normal")
    window.after(1800, lambda: canvas.itemconfigure(bubble, state="hidden"))

tk.Button(
    status_controls,
    text="REPOSICIONAR NOVA",
    command=reset_nova_position,
    bg="#245875",
    fg="#ffffff",
    activebackground="#2e7093",
    activeforeground="#ffffff",
    relief="flat",
    bd=0,
    padx=4,
    pady=3,
    font=("Segoe UI", 7, "bold"),
).pack(fill="x", pady=(0, 3))
tk.Button(
    status_controls,
    text="ABRIR LEGENDA",
    command=show_caption_window,
    bg="#173a50",
    fg="#9fe8ff",
    activebackground="#245875",
    activeforeground="#ffffff",
    relief="flat",
    bd=0,
    padx=4,
    pady=3,
    font=("Segoe UI", 7, "bold"),
).pack(fill="x")
needs_label = status_canvas.create_text(75, 105, text="energia 80\nfome 80\ndescanso 80\natenção 80", fill="#d7e8ff", font=("Segoe UI", 9), justify="left")
panel_details = status_canvas.create_text(75, 193, text="nível 1 · 0 XP\nhumor: happy", fill="#ffffff", font=("Segoe UI", 9), justify="center")
yard_label = status_canvas.create_text(75, 260, text="", fill="#73f5a5", font=("Segoe UI", 8, "bold"), justify="center")

drag = {"x": 0, "y": 0}
activity = {"last": time.time(), "keys": 0, "last_reward": 0.0}
movement = {"walking": False, "phase": 0, "direction": 1, "mode": "exploring", "pace": 1.0, "pinned": False, "walk_token": 0}
manual_drag = {"active": False}
voice_capture = {"active": False}
screen_pointing = {"active": False}
screen_selection = {"overlay": None, "canvas": None, "start": None, "rect": None}
yard_editor = {"window": None}
yard_tray = {"icon": None}
status_compact = {"value": False}

def begin(event):
    manual_drag["active"] = True
    movement["pinned"] = True
    movement["walking"] = False
    movement["walk_token"] += 1
    drag["x"], drag["y"] = event.x_root, event.y_root

def end_drag(_event=None):
    if manual_drag["active"]:
        manual_drag["active"] = False
        movement["mode"] = "cuddling"
        canvas.itemconfigure(bubble, text="Fiquei aqui.", state="normal")
        window.after(1800, lambda: canvas.itemconfigure(bubble, state="hidden"))

def toggle_wander():
    movement["pinned"] = not movement["pinned"]
    movement["walk_token"] += 1
    if movement["pinned"]:
        movement["walking"] = False
        canvas.itemconfigure(bubble, text="Vou ficar neste cantinho.", state="normal")
        window.after(1800, lambda: canvas.itemconfigure(bubble, state="hidden"))
    else:
        canvas.itemconfigure(bubble, text="Vou dar uma voltinha.", state="normal")
        window.after(1200, lambda: canvas.itemconfigure(bubble, state="hidden"))
        wander()

def start_voice_capture():
    """Hold the plus key long enough for the voice engine to enter recording mode."""
    if voice_capture["active"]:
        return
    voice_capture["active"] = True
    keyboard.press(VOICE_KEY)
    window.after(7000, stop_voice_capture)

def stop_voice_capture():
    if voice_capture["active"]:
        keyboard.release(VOICE_KEY)
        voice_capture["active"] = False

def trigger_voice_key():
    window.after(0, start_voice_capture)
    window.after(0, lambda: canvas.itemconfigure(bubble, text="Estou ouvindo...", state="normal"))
    window.after(2600, lambda: canvas.itemconfigure(bubble, state="hidden"))

def trigger_vision_key():
    window.after(0, start_screen_selection)

def trigger_yard_key():
    window.after(0, open_yard_config)

def position_status_window():
    if status_window.state() != "withdrawn":
        status_window.update_idletasks()
        height = max(315, status_window.winfo_reqheight())
        status_window.geometry(f"150x{height}+{window.winfo_x() + 245}+{window.winfo_y() + 18}")

def toggle_status_panel():
    if status_window.state() == "withdrawn":
        status_window.deiconify()
        position_status_window()
        status_window.lift()
    else:
        status_window.withdraw()

def toggle_caption_window():
    if caption_window.state() == "withdrawn":
        show_caption_window()
    else:
        caption_window.withdraw()

def cycle_caption_mode():
    modes = (("auto", "AUTO"), ("history", "HISTÓRICO"), ("caption", "LEGENDA"))
    current = caption_mode["value"]
    next_mode, label = modes[(next(index for index, item in enumerate(modes) if item[0] == current) + 1) % len(modes)]
    caption_mode["value"] = next_mode
    caption_mode_button.configure(text=label)
    refresh_state()

class WindowsTrayIcon:
    """Small native Windows tray icon used while the setup window is minimized."""

    WM_TRAY = win32con.WM_USER + 20 if TRAY_AVAILABLE else 0
    CMD_OPEN = 1001
    CMD_CLOSE = 1002

    def __init__(self, on_open, on_close):
        self.on_open = on_open
        self.on_close = on_close
        self.hwnd = None
        self.notify_id = None
        self.thread = None

    def start(self):
        if not TRAY_AVAILABLE or self.thread is not None:
            return
        import threading
        self.thread = threading.Thread(target=self._run, name="nova-yard-tray", daemon=True)
        self.thread.start()

    def _run(self):
        class_name = f"NovaYardTray_{id(self)}"
        window_class = win32gui.WNDCLASS()
        window_class.hInstance = win32api.GetModuleHandle(None)
        window_class.lpszClassName = class_name
        window_class.lpfnWndProc = self._window_proc
        atom = win32gui.RegisterClass(window_class)
        self.hwnd = win32gui.CreateWindow(atom, class_name, 0, 0, 0, 0, 0, 0, 0, window_class.hInstance, None)
        self.notify_id = (self.hwnd, 0, win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP, self.WM_TRAY, win32gui.LoadIcon(0, win32con.IDI_APPLICATION), "Nova — setup do quintal")
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, self.notify_id)
        win32gui.PumpMessages()

    def _window_proc(self, hwnd, message, wparam, lparam):
        if message == self.WM_TRAY:
            if lparam in (win32con.WM_LBUTTONUP, win32con.WM_LBUTTONDBLCLK):
                self.on_open()
            elif lparam == win32con.WM_RBUTTONUP:
                self._show_menu(hwnd)
            return 0
        if message == win32con.WM_COMMAND:
            command = wparam & 0xFFFF
            if command == self.CMD_OPEN:
                self.on_open()
            elif command == self.CMD_CLOSE:
                self.on_close()
            return 0
        if message == win32con.WM_CLOSE:
            if self.notify_id:
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, self.notify_id)
                self.notify_id = None
            win32gui.DestroyWindow(hwnd)
            return 0
        if message == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, message, wparam, lparam)

    def _show_menu(self, hwnd):
        menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(menu, win32con.MF_STRING, self.CMD_OPEN, "Abrir configuração")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        win32gui.AppendMenu(menu, win32con.MF_STRING, self.CMD_CLOSE, "Fechar setup")
        position = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(hwnd)
        win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, position[0], position[1], 0, hwnd, None)
        win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)
        win32gui.DestroyMenu(menu)

def stop_yard_tray():
    tray = yard_tray.get("icon")
    yard_tray["icon"] = None
    if tray is not None and tray.hwnd:
        win32api.PostMessage(tray.hwnd, win32con.WM_CLOSE, 0, 0)

def restore_yard_editor():
    editor = yard_editor.get("window")
    if editor is not None and editor.winfo_exists():
        editor.deiconify()
        editor.state("normal")
        editor.lift()
        editor.focus_force()

def close_yard_editor():
    editor = yard_editor.get("window")
    if editor is not None and editor.winfo_exists():
        stop_yard_tray()
        yard_editor["window"] = None
        editor.destroy()

def ensure_yard_tray():
    if not TRAY_AVAILABLE or yard_tray.get("icon") is not None:
        return
    tray = WindowsTrayIcon(
        on_open=lambda: window.after(0, restore_yard_editor),
        on_close=lambda: window.after(0, close_yard_editor),
    )
    yard_tray["icon"] = tray
    tray.start()

def minimize_yard_editor():
    editor = yard_editor.get("window")
    if editor is not None and editor.winfo_exists() and editor.state() == "iconic":
        editor.withdraw()
        ensure_yard_tray()

def format_dimension(value):
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError):
        return "-"

def update_yard_panel():
    status_canvas.itemconfigure(
        yard_label,
        text=(
            f"{yard_config.get('name', 'Quintal')}\n"
            f"{format_dimension(yard_config.get('width'))} × "
            f"{format_dimension(yard_config.get('depth'))} × "
            f"{format_dimension(yard_config.get('height'))} m"
        ),
    )

def open_yard_config():
    existing = yard_editor.get("window")
    if existing is not None and existing.winfo_exists():
        existing.deiconify()
        existing.state("normal")
        existing.lift()
        existing.focus_force()
        stop_yard_tray()
        return

    editor = tk.Toplevel(window)
    yard_editor["window"] = editor
    editor.title("Configurar quintal da Nova")
    editor.geometry("430x600")
    editor.resizable(False, False)
    editor.attributes("-topmost", True)
    editor.configure(bg="#101a2d")

    tk.Label(editor, text="QUINTAL DA NOVA", bg="#101a2d", fg="#73f5a5", font=("Segoe UI", 15, "bold")).pack(pady=(18, 2))
    tk.Label(editor, text="Defina o espaço e os status iniciais do personagem.", bg="#101a2d", fg="#a8bad2", font=("Segoe UI", 9)).pack(pady=(0, 14))

    form = tk.Frame(editor, bg="#101a2d")
    form.pack(fill="x", padx=28)
    fields = {}

    def add_entry(row, label_text, key, value):
        tk.Label(form, text=label_text, bg="#101a2d", fg="#d7e8ff", font=("Segoe UI", 10), anchor="w").grid(row=row, column=0, sticky="w", pady=5)
        variable = tk.StringVar(value=str(value))
        fields[key] = variable
        tk.Entry(form, textvariable=variable, bg="#172943", fg="#ffffff", insertbackground="#ffffff", relief="flat", width=24).grid(row=row, column=1, sticky="ew", padx=(16, 0), pady=5, ipady=4)

    form.columnconfigure(1, weight=1)
    add_entry(0, "Nome do quintal", "name", yard_config.get("name", "Quintal da Nova"))
    add_entry(1, "Largura (m)", "width", yard_config.get("width", 8.0))
    add_entry(2, "Profundidade (m)", "depth", yard_config.get("depth", 6.0))
    add_entry(3, "Altura (m)", "height", yard_config.get("height", 3.0))

    tk.Label(form, text="Tema visual", bg="#101a2d", fg="#d7e8ff", font=("Segoe UI", 10), anchor="w").grid(row=4, column=0, sticky="w", pady=5)
    theme = tk.StringVar(value=yard_config.get("theme", "natural"))
    tk.OptionMenu(form, theme, "natural", "praia", "floresta", "cidade", "espacial").grid(row=4, column=1, sticky="ew", padx=(16, 0), pady=5)

    tk.Frame(editor, bg="#29415f", height=1).pack(fill="x", padx=28, pady=15)
    tk.Label(editor, text="STATUS DO PERSONAGEM", bg="#101a2d", fg="#73f5a5", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=28)

    status_form = tk.Frame(editor, bg="#101a2d")
    status_form.pack(fill="x", padx=28, pady=(5, 0))
    status_fields = {}

    def add_status(row, label_text, key, value):
        tk.Label(status_form, text=label_text, bg="#101a2d", fg="#d7e8ff", font=("Segoe UI", 10), anchor="w").grid(row=row, column=0, sticky="w", pady=4)
        variable = tk.StringVar(value=str(value))
        status_fields[key] = variable
        tk.Entry(status_form, textvariable=variable, bg="#172943", fg="#ffffff", insertbackground="#ffffff", relief="flat", width=24).grid(row=row, column=1, sticky="ew", padx=(16, 0), pady=4, ipady=3)

    status_form.columnconfigure(1, weight=1)
    needs = state.setdefault("needs", {})
    add_status(0, "Energia", "energy", needs.get("energy", 80))
    add_status(1, "Fome", "hunger", needs.get("hunger", 80))
    add_status(2, "Descanso", "rest", needs.get("rest", 80))
    add_status(3, "Atenção", "attention", needs.get("attention", 80))
    add_status(4, "Nível", "level", state.get("level", 1))
    add_status(5, "XP", "xp", state.get("xp", 0))

    tk.Label(status_form, text="Humor", bg="#101a2d", fg="#d7e8ff", font=("Segoe UI", 10), anchor="w").grid(row=6, column=0, sticky="w", pady=4)
    mood = tk.StringVar(value=state.get("mood", "happy"))
    tk.OptionMenu(status_form, mood, "happy", "focused", "energetic", "resting", "playful", "content").grid(row=6, column=1, sticky="ew", padx=(16, 0), pady=4)

    feedback = tk.Label(editor, text="Tudo será salvo somente neste computador.", bg="#101a2d", fg="#7f97b5", font=("Segoe UI", 9))
    feedback.pack(pady=(18, 8))
    buttons = tk.Frame(editor, bg="#101a2d")
    buttons.pack(pady=(0, 18))

    def close_editor():
        close_yard_editor()

    def save_config():
        try:
            dimensions = {key: float(fields[key].get().replace(",", ".")) for key in ("width", "depth", "height")}
            if any(value <= 0 or value > 1000 for value in dimensions.values()):
                raise ValueError("As dimensões devem estar entre 0 e 1000 metros.")
            status_values = {key: int(status_fields[key].get()) for key in ("energy", "hunger", "rest", "attention", "level", "xp")}
            if any(status_values[key] < 0 for key in status_values):
                raise ValueError("Os status não podem ser negativos.")
        except ValueError as exc:
            messagebox.showerror("Valor inválido", str(exc), parent=editor)
            return

        yard_config.update({"name": fields["name"].get().strip() or "Quintal da Nova", **dimensions, "theme": theme.get()})
        state["level"] = status_values["level"]
        state["xp"] = status_values["xp"]
        state["mood"] = mood.get()
        state.setdefault("needs", {}).update({key: status_values[key] for key in ("energy", "hunger", "rest", "attention")})
        YARD_CONFIG.write_text(json.dumps(yard_config, ensure_ascii=False, indent=2), encoding="utf-8")
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        update_yard_panel()
        feedback.configure(text="Configuração salva.", fg="#73f5a5")
        editor.after(800, close_editor)

    tk.Button(buttons, text="Salvar", command=save_config, bg="#35d07f", fg="#07111f", activebackground="#73f5a5", relief="flat", padx=18, pady=7, font=("Segoe UI", 10, "bold")).pack(side="left", padx=5)
    tk.Button(buttons, text="Cancelar", command=close_editor, bg="#243852", fg="#d7e8ff", activebackground="#365477", relief="flat", padx=18, pady=7, font=("Segoe UI", 10)).pack(side="left", padx=5)
    editor.protocol("WM_DELETE_WINDOW", close_editor)
    editor.bind("<Unmap>", lambda _event: editor.after_idle(minimize_yard_editor))
    editor.bind("<Configure>", lambda _event: editor.after_idle(minimize_yard_editor))
    editor.bind("<Escape>", lambda _event: close_editor())
    editor.focus_force()

def start_screen_selection():
    if screen_selection["overlay"] is not None:
        return
    screen_pointing["active"] = True
    overlay = tk.Toplevel(window)
    screen_selection["overlay"] = overlay
    overlay.overrideredirect(True)
    overlay.attributes("-topmost", True)
    overlay.attributes("-alpha", 0.28)
    width, height = overlay.winfo_screenwidth(), overlay.winfo_screenheight()
    overlay.geometry(f"{width}x{height}+0+0")
    overlay.configure(bg="#07111f")
    select_canvas = tk.Canvas(overlay, bg="#07111f", highlightthickness=0, cursor="crosshair")
    select_canvas.pack(fill="both", expand=True)
    screen_selection["canvas"] = select_canvas
    select_canvas.create_text(width // 2, 32, text="Arraste para selecionar o que a Nova deve analisar · Esc cancela", fill="#ffffff", font=("Segoe UI", 14, "bold"))

    def press(event):
        screen_selection["start"] = (event.x, event.y)
        screen_selection["rect"] = select_canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="#55f28b", width=3)

    def drag_select(event):
        if screen_selection["rect"] is not None:
            x0, y0 = screen_selection["start"]
            select_canvas.coords(screen_selection["rect"], x0, y0, event.x, event.y)

    def release(event):
        x0, y0 = screen_selection["start"]
        x1, y1 = event.x, event.y
        left, top = min(x0, x1), min(y0, y1)
        right, bottom = max(x0, x1), max(y0, y1)
        if right - left >= 12 and bottom - top >= 12:
            # A camada de seleção não pode aparecer na imagem enviada à IA.
            close_overlay()
            # A própria Nova e a legenda também não devem virar "evidência".
            window_visible = window.winfo_viewable()
            status_visible = status_window.winfo_viewable()
            caption_visible = caption_window.winfo_viewable()
            if window_visible:
                window.withdraw()
            if status_visible:
                status_window.withdraw()
            if caption_visible:
                caption_window.withdraw()
            try:
                with mss.mss() as capture:
                    shot = capture.grab({"left": left, "top": top, "width": right - left, "height": bottom - top})
                    output = Path(tempfile.gettempdir()) / "nova-screen-selection.png"
                    mss.tools.to_png(shot.rgb, shot.size, output=str(output))
            finally:
                if window_visible:
                    window.deiconify()
                if status_visible:
                    status_window.deiconify()
                if caption_visible:
                    caption_window.deiconify()
            (ROOT / "vision-request.json").write_text(json.dumps({"image": str(output), "rect": [left, top, right, bottom], "created_at": time.time()}, ensure_ascii=False, indent=2), encoding="utf-8")
            canvas.itemconfigure(bubble, text="Área capturada. Vou analisar.", state="normal")
            window.after(3000, lambda: canvas.itemconfigure(bubble, state="hidden"))
        else:
            close_overlay()

    def cancel(_event=None):
        close_overlay()

    def close_overlay():
        screen_pointing["active"] = False
        screen_selection["overlay"] = None
        screen_selection["canvas"] = None
        overlay.destroy()

    select_canvas.bind("<ButtonPress-1>", press)
    select_canvas.bind("<B1-Motion>", drag_select)
    select_canvas.bind("<ButtonRelease-1>", release)
    overlay.bind("<Escape>", cancel)
    overlay.focus_force()

def move(event):
    window.geometry(f"+{window.winfo_x() + event.x_root - drag['x']}+{window.winfo_y() + event.y_root - drag['y']}")
    position_status_window()
    drag["x"], drag["y"] = event.x_root, event.y_root

def close(_event=None):
    caption_window.destroy()
    window.destroy()

def record_activity(_event=None):
    now = time.time()
    activity["last"] = now
    activity["keys"] += 1
    if activity["keys"] >= 20 and now - activity["last_reward"] > 30:
        activity["keys"] = 0
        activity["last_reward"] = now
        state["xp"] = state.get("xp", 0) + 2
        state["level"] = 1 + state["xp"] // 10
        state["mood"] = "focused"
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def update_mood():
    if time.time() - activity["last"] > 60:
        state["mood"] = "resting"
    window.after(5000, update_mood)

def console_line_tag(line):
    normalized = line.strip().lower()
    if normalized.startswith(("you:", "você:", "user:")):
        return "console_user"
    if normalized.startswith(("you-en:", "en:")):
        return "console_english"
    if normalized.startswith(("you-pt:", "pt:")):
        return "console_portuguese"
    if "vision" in normalized or "visão" in normalized:
        return "console_vision"
    if "error" in normalized or "erro" in normalized or "exception" in normalized:
        return "console_error"
    if normalized.startswith(("nova ", "nova:", "nova registered")):
        return "console_nova"
    if normalized.startswith(("listening", "audio:", "system:", "loading")):
        return "console_system"
    return "console_system"

def render_console_history():
    if not CONSOLE_LOG.exists():
        return
    try:
        lines = CONSOLE_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
        # A janela maior mostra mais histórico; a largura maior permite mais texto por linha.
        visible_lines = max(6, min(180, caption_label.winfo_height() // 19))
        selected = lines[-visible_lines:]
        caption_label.configure(state="normal")
        caption_label.delete("1.0", "end")
        for line in selected:
            caption_label.insert("end", line + "\n", console_line_tag(line))
        caption_label.configure(state="disabled")
    except OSError:
        pass

def refresh_state():
    global state
    if STATE.exists():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
            mood = state.get("mood", "happy")
            phrases = {"focused": "Estou aprendendo!", "energetic": "Vamos nos mexer!", "resting": "Vou descansar...", "playful": "Oba, vamos brincar!", "content": "Estou bem cuidada!", "happy": "Oi, Michel!"}
            status_canvas.itemconfigure(panel_details, text=f"nível {state.get('level', 1)} · {state.get('xp', 0)} XP\nhumor: {mood}")
            update_yard_panel()
            canvas.itemconfigure(bubble, text=phrases.get(mood, "Estou com você!"))
            needs = state.get("needs", {})
            now = time.time()
            last_tick = state.get("last_tick", now)
            if now - last_tick >= 60:
                minutes = int((now - last_tick) // 60)
                needs["hunger"] = max(0, needs.get("hunger", 80) - minutes)
                needs["rest"] = max(0, needs.get("rest", 80) - minutes // 2)
                needs["attention"] = max(0, needs.get("attention", 80) - minutes // 3)
                state["last_tick"] = now
                STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            status_canvas.itemconfigure(needs_label, text=f"energia  {needs.get('energy', 80)}\nfome      {needs.get('hunger', 80)}\ndescanso  {needs.get('rest', 80)}\natenção   {needs.get('attention', 80)}")
            if VISION_RESPONSE.exists():
                try:
                    request = json.loads(VISION_REQUEST.read_text(encoding="utf-8")) if VISION_REQUEST.exists() else {}
                    vision = json.loads(VISION_RESPONSE.read_text(encoding="utf-8"))
                    answer = vision.get("answer")
                    created_at = vision.get("created_at")
                    if answer and created_at == request.get("created_at"):
                        # Respostas visuais nunca aparecem no balão acima do personagem.
                        canvas.itemconfigure(bubble, state="hidden")
                        if isinstance(created_at, (int, float)) and created_at >= SESSION_STARTED_AT and caption_window.winfo_height() < 150:
                            caption_label.configure(state="normal")
                            caption_label.delete("1.0", "end")
                            caption_label.insert("end", answer, "past")
                            caption_label.configure(state="disabled")
                except (OSError, json.JSONDecodeError):
                    pass
            technical_mode = caption_mode["value"] == "history" or (caption_mode["value"] == "auto" and caption_window.winfo_height() >= 150)
            if technical_mode and CONSOLE_LOG.exists():
                render_console_history()
            elif CAPTION_POSITION == "below" and CAPTION_LIVE.exists():
                try:
                    live = json.loads(CAPTION_LIVE.read_text(encoding="utf-8"))
                    words = live.get("text", "").split()
                    index = live.get("index", -1)
                    boundaries = live.get("boundaries", [])
                    started_at = live.get("started_at")
                    if live.get("active") and boundaries and started_at:
                        elapsed_ms = (time.time() - started_at) * 1000
                        index = max((i for i, item in enumerate(boundaries) if item.get("offset_ms", 0) <= elapsed_ms), default=0)
                    if live.get("active") and 0 <= index < len(words):
                        caption_label.configure(state="normal")
                        caption_label.delete("1.0", "end")
                        caption_label.insert("end", " ".join(words[:index]) + " ", "past")
                        caption_label.insert("end", words[index], "active")
                        caption_label.insert("end", " " + " ".join(words[index + 1:]), "future")
                        caption_label.configure(state="disabled")
                    else:
                        caption_label.configure(state="normal")
                        caption_label.delete("1.0", "end")
                        caption_label.insert("end", live.get("text", ""), "past")
                        caption_label.configure(state="disabled")
                except (OSError, json.JSONDecodeError, IndexError):
                    pass
        except (OSError, json.JSONDecodeError):
            pass
    # Caption needs a fast refresh for karaoke; state files remain lightweight.
    window.after(80, refresh_state)

def wander():
    if movement["pinned"]:
        return
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    # Reserve space for the separate NOVA STATUS window beside the mascot.
    target_x = random.randint(40, max(40, screen_w - 430))
    target_y = random.randint(60, max(60, screen_h - 340))
    start_x, start_y = window.winfo_x(), window.winfo_y()
    movement["direction"] = 1 if target_x >= start_x else -1
    movement["mode"] = "walking"
    steps = random.choice((220, 250, 280))
    movement["pace"] = random.choice((0.82, 1.0, 1.12))
    movement["walking"] = True
    movement["walk_token"] += 1
    walk_token = movement["walk_token"]
    def glide(step=0):
        if walk_token != movement["walk_token"] or manual_drag["active"] or movement["pinned"]:
            return
        if step > steps:
            movement["walking"] = False
            movement["mode"] = "sniffing"
            canvas.itemconfigure(bubble, text=random.choice(("Deixa eu investigar...", "Hmm, este lugar parece bom.", "Vou conferir este cantinho.")))
            window.after(random.randint(1200, 2600), settle)
            return
        progress = step / steps
        eased = progress * progress * (3 - 2 * progress)
        x = round(start_x + (target_x - start_x) * eased)
        y = round(start_y + (target_y - start_y) * eased)
        window.geometry(f"+{x}+{y}")
        position_status_window()
        # A slower cadence and eased timing make the gait less mechanical.
        delay = int(28 / movement["pace"])
        window.after(delay, lambda: glide(step + 1))
    glide()

def settle():
    movement["mode"] = random.choice(("cuddling", "stretching", "sniffing"))
    canvas.itemconfigure(bubble, text=random.choice(("Vou ficar aqui um pouquinho.", "Que cantinho gostoso!", "Hora de aconchegar.")))
    window.after(random.randint(5000, 11000), wander)

def idle_bob(step=0):
    mood = state.get("mood", "happy")
    rate = 0.72 if mood == "energetic" else 0.48 if movement["walking"] else 0.16
    amplitude = 4.5 if mood == "energetic" else 2.5 if movement["walking"] else 1.5
    bob = math.sin(step * rate) * amplitude
    canvas.coords(sprite, 120, 200 + bob)
    if movement["walking"] and len(walk_images) >= 8:
        # Cada direção percorre as quatro fases do passo em sequência.
        gait_frame = (movement["phase"] // 2) % 4
        frame_index = gait_frame if movement["direction"] >= 0 else 4 + gait_frame
        canvas.itemconfigure(sprite, image=walk_images[frame_index])
    elif movement["mode"] == "sniffing" and len(behavior_images) >= 3:
        canvas.itemconfigure(sprite, image=behavior_images[2])
    elif movement["mode"] == "cuddling" and len(behavior_images) >= 1:
        canvas.itemconfigure(sprite, image=behavior_images[0])
    elif movement["mode"] == "stretching" and len(behavior_images) >= 2:
        canvas.itemconfigure(sprite, image=behavior_images[1])
    elif mood == "playful" and len(behavior_images) >= 4:
        canvas.itemconfigure(sprite, image=behavior_images[3])
    elif mood == "resting" and len(behavior_images) >= 1:
        canvas.itemconfigure(sprite, image=behavior_images[0])
    elif mood == "playful" and len(images) >= 3:
        canvas.itemconfigure(sprite, image=images[1 + ((movement["phase"] // 2) % 2)])
    elif len(images):
        canvas.itemconfigure(sprite, image=images[0])
    if movement["walking"]:
        movement["phase"] += 1
        offset = 3 if (movement["phase"] // 3) % 2 == 0 else -1
    else:
        offset = 1 if step % 2 == 0 else -1
    window.after(70 if movement["walking"] else 120, lambda: idle_bob(step + 1))

canvas.bind("<ButtonPress-1>", begin)
canvas.bind("<ButtonRelease-1>", end_drag)
canvas.bind("<B1-Motion>", move)
window.bind("<ButtonPress-1>", begin)
window.bind("<ButtonRelease-1>", end_drag)
window.focus_force()
for item in (sprite, label):
    canvas.tag_bind(item, "<ButtonPress-1>", begin)
    canvas.tag_bind(item, "<B1-Motion>", move)
canvas.bind("<Escape>", close)
window.bind("<Escape>", close)
keyboard.on_press(record_activity)
keyboard.add_hotkey("shift+=", trigger_voice_key)
keyboard.add_hotkey("add", trigger_voice_key)
keyboard.add_hotkey(VISION_KEY, trigger_vision_key)
keyboard.add_hotkey(YARD_KEY, trigger_yard_key)
keyboard.add_hotkey(STATUS_KEY, lambda: window.after(0, toggle_status_panel))
keyboard.add_hotkey(TEXT_KEY, lambda: window.after(0, toggle_caption_window))
keyboard.add_hotkey(WANDER_KEY, lambda: window.after(0, toggle_wander))
keyboard.add_hotkey(RESET_KEY, lambda: window.after(0, reset_nova_position))
window.update_idletasks()
window.update_idletasks()
screen_w = window.winfo_screenwidth()
screen_h = window.winfo_screenheight()
# Keep Nova in the largest unobstructed desktop corner, above the caption bar/taskbar.
pet_x = max(0, screen_w - 430)
pet_y = max(20, screen_h - 535)
window.geometry(f"240x370+{pet_x}+{pet_y}")
position_status_window()
refresh_state()
wander()
idle_bob()
update_mood()
window.mainloop()
