import json
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGE = ROOT / "assistant-mascot.png"
STATE = ROOT / "nova-state.json"

default_state = {"name": "Nova", "level": 1, "xp": 0, "mood": "happy"}
try:
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else default_state
except (OSError, json.JSONDecodeError):
    state = default_state

window = tk.Tk()
window.title("Nova")
window.overrideredirect(True)
window.attributes("-topmost", True)
window.configure(bg="#07111f")
window.wm_attributes("-transparentcolor", "#07111f")

canvas = tk.Canvas(window, width=240, height=280, bg="#07111f", highlightthickness=0)
canvas.pack()
image = tk.PhotoImage(file=str(IMAGE))
image = image.subsample(max(1, image.width() // 190))
sprite = canvas.create_image(120, 112, image=image)
label = canvas.create_text(120, 245, text="Nova · pronta para conversar", fill="#b7ffd0", font=("Segoe UI", 10, "bold"))

drag = {"x": 0, "y": 0}

def begin(event):
    drag["x"], drag["y"] = event.x_root, event.y_root

def move(event):
    window.geometry(f"+{window.winfo_x() + event.x_root - drag['x']}+{window.winfo_y() + event.y_root - drag['y']}")
    drag["x"], drag["y"] = event.x_root, event.y_root

def interact(_event=None):
    state["xp"] = state.get("xp", 0) + 1
    state["level"] = 1 + state["xp"] // 10
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    canvas.itemconfigure(label, text=f"Nova · nível {state['level']} · {state['xp']} XP")

def close(_event=None):
    window.destroy()

def refresh_state():
    global state
    if STATE.exists():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
            canvas.itemconfigure(label, text=f"Nova · nível {state.get('level', 1)} · {state.get('xp', 0)} XP · {state.get('mood', 'happy')}")
        except (OSError, json.JSONDecodeError):
            pass
    window.after(1000, refresh_state)

canvas.bind("<ButtonPress-1>", begin)
canvas.bind("<B1-Motion>", move)
for item in (sprite, label):
    canvas.tag_bind(item, "<ButtonPress-1>", begin)
    canvas.tag_bind(item, "<B1-Motion>", move)
    canvas.tag_bind(item, "<Double-Button-1>", interact)
canvas.bind("<Escape>", close)
window.bind("<Escape>", close)
window.geometry("240x280+1100+500")
refresh_state()
window.mainloop()
