import json
import random
import tkinter as tk
import time
import keyboard
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
bubble = canvas.create_text(120, 25, text="Oi!", fill="#ffffff", font=("Segoe UI", 11, "bold"))
needs_label = canvas.create_text(120, 262, text="energia 80 · fome 80 · descanso 80", fill="#8da1ba", font=("Segoe UI", 8))

drag = {"x": 0, "y": 0}
activity = {"last": time.time(), "keys": 0, "last_reward": 0.0}

def begin(event):
    drag["x"], drag["y"] = event.x_root, event.y_root

def move(event):
    window.geometry(f"+{window.winfo_x() + event.x_root - drag['x']}+{window.winfo_y() + event.y_root - drag['y']}")
    drag["x"], drag["y"] = event.x_root, event.y_root

def interact(_event=None):
    state["xp"] = state.get("xp", 0) + 1
    state["level"] = 1 + state["xp"] // 10
    state["mood"] = "playful"
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    canvas.itemconfigure(label, text=f"Nova · nível {state['level']} · {state['xp']} XP")
    window.after(2500, lambda: canvas.itemconfigure(label, text=f"Nova · nível {state['level']} · {state.get('mood', 'happy')}"))

def close(_event=None):
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
        canvas.itemconfigure(label, text=f"Nova · nível {state.get('level', 1)} · descansando")
    window.after(5000, update_mood)

def refresh_state():
    global state
    if STATE.exists():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
            mood = state.get("mood", "happy")
            phrases = {"focused": "Estou aprendendo!", "energetic": "Vamos nos mexer!", "resting": "Vou descansar...", "playful": "Oba, vamos brincar!", "content": "Estou bem cuidada!", "happy": "Oi, Michel!"}
            canvas.itemconfigure(label, text=f"Nova · nível {state.get('level', 1)} · {state.get('xp', 0)} XP · {mood}")
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
            canvas.itemconfigure(needs_label, text=f"energia {needs.get('energy', 80)} · fome {needs.get('hunger', 80)} · descanso {needs.get('rest', 80)}")
        except (OSError, json.JSONDecodeError):
            pass
    window.after(1000, refresh_state)

def wander():
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    target_x = random.randint(40, max(40, screen_w - 280))
    target_y = random.randint(60, max(60, screen_h - 340))
    start_x, start_y = window.winfo_x(), window.winfo_y()
    steps = 45
    def glide(step=0):
        if step > steps:
            window.after(random.randint(1800, 4000), wander)
            return
        progress = step / steps
        eased = progress * progress * (3 - 2 * progress)
        x = round(start_x + (target_x - start_x) * eased)
        y = round(start_y + (target_y - start_y) * eased)
        window.geometry(f"+{x}+{y}")
        window.after(35, lambda: glide(step + 1))
    glide()

def idle_bob(step=0):
    offset = 2 if step % 2 == 0 else -2
    canvas.move(sprite, 0, offset)
    window.after(700, lambda: idle_bob(step + 1))

canvas.bind("<ButtonPress-1>", begin)
canvas.bind("<B1-Motion>", move)
for item in (sprite, label):
    canvas.tag_bind(item, "<ButtonPress-1>", begin)
    canvas.tag_bind(item, "<B1-Motion>", move)
    canvas.tag_bind(item, "<Double-Button-1>", interact)
canvas.bind("<Escape>", close)
window.bind("<Escape>", close)
keyboard.on_press(record_activity)
window.geometry("240x280+1100+500")
refresh_state()
wander()
idle_bob()
update_mood()
window.mainloop()
