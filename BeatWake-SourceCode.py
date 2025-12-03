import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import time
import threading
import webbrowser
from ttkthemes import ThemedTk
import json
import os
import subprocess

# === Alarm Class ===
class Alarm:
    def __init__(self, time_str, url, repeat_days, enabled=True, label=""):
        self.time_str = time_str
        self.url = url
        self.repeat_days = repeat_days
        self.enabled = enabled
        self.label = label  # optional alarm name
        self._last_fired_key = None

    def should_trigger(self):
        if not self.enabled:
            return False
        now = datetime.now()
        now_str_hm = now.strftime("%H:%M")
        weekday = now.strftime("%A")
        # must match hour:minute
        if now_str_hm != self.time_str:
            return False
        # day must match or Once
        return "Once" in self.repeat_days or weekday in self.repeat_days

    def fire_key_for_now(self):
        # unique key per minute to avoid duplicate triggers in the same minute
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    def get_next_trigger(self):
        """Calculate next trigger time for display"""
        if not self.enabled:
            return "Disabled"
        
        now = datetime.now()
        alarm_hour, alarm_minute = map(int, self.time_str.split(':'))
        
        if "Once" in self.repeat_days:
            next_trigger = now.replace(hour=alarm_hour, minute=alarm_minute, second=0, microsecond=0)
            if next_trigger <= now:
                next_trigger += timedelta(days=1)
            return next_trigger.strftime("%Y-%m-%d %H:%M")
        
        # Find next matching weekday
        days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, 
                    "Friday": 4, "Saturday": 5, "Sunday": 6}
        today = now.weekday()
        alarm_time_today = now.replace(hour=alarm_hour, minute=alarm_minute, second=0, microsecond=0)
        
        for offset in range(8):  # check next 7 days
            check_day = (today + offset) % 7
            day_name = [k for k, v in days_map.items() if v == check_day][0]
            if day_name in self.repeat_days:
                if offset == 0 and alarm_time_today > now:
                    return alarm_time_today.strftime("%a %H:%M")
                elif offset > 0:
                    next_date = now + timedelta(days=offset)
                    return next_date.replace(hour=alarm_hour, minute=alarm_minute).strftime("%a %H:%M")
        return "Never"

    def to_dict(self):
        return {
            "time_str": self.time_str,
            "url": self.url,
            "repeat_days": self.repeat_days,
            "enabled": self.enabled,
            "label": self.label,
        }

    @staticmethod
    def from_dict(data):
        return Alarm(
            data["time_str"], 
            data["url"], 
            data["repeat_days"],
            data.get("enabled", True),
            data.get("label", "")
        )

alarms = []
PERSIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alarms.json")
snooze_alarms = []  # Track snoozed alarms

def load_alarms():
    global alarms
    try:
        if os.path.exists(PERSIST_PATH):
            with open(PERSIST_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            alarms = [Alarm.from_dict(a) for a in raw]
            update_alarm_listbox()
    except Exception as e:
        messagebox.showwarning("Load Failed", f"Could not load alarms: {e}")

def save_alarms():
    try:
        with open(PERSIST_PATH, "w", encoding="utf-8") as f:
            json.dump([a.to_dict() for a in alarms], f, indent=2)
    except Exception as e:
        messagebox.showwarning("Save Failed", f"Could not save alarms: {e}")

def play_system_beep():
    """Play system beep as backup notification"""
    try:
        subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"], 
                      stderr=subprocess.DEVNULL, timeout=1)
    except:
        print('\a')  # Terminal beep as last resort

def snooze_alarm(alarm, minutes=5):
    """Snooze alarm for specified minutes"""
    snooze_time = datetime.now() + timedelta(minutes=minutes)
    snooze_alarms.append((snooze_time, alarm))
    update_status(f"Alarm snoozed for {minutes} minutes")

def alarm_checker():
    while True:
        # Check regular alarms
        for alarm in list(alarms):
            if alarm.should_trigger():
                key = alarm.fire_key_for_now()
                if alarm._last_fired_key == key:
                    continue
                
                play_system_beep()
                try:
                    webbrowser.open(alarm.url)
                    update_status(f"Alarm triggered: {alarm.label or alarm.time_str}")
                except Exception as e:
                    update_status(f"Error opening browser: {e}")
                
                alarm._last_fired_key = key
                if "Once" in alarm.repeat_days:
                    alarms.remove(alarm)
                    update_alarm_listbox()
                    save_alarms()
        
        # Check snoozed alarms
        now = datetime.now()
        for snooze_time, alarm in list(snooze_alarms):
            if now >= snooze_time:
                play_system_beep()
                try:
                    webbrowser.open(alarm.url)
                    update_status(f"Snoozed alarm triggered: {alarm.label or alarm.time_str}")
                except Exception as e:
                    update_status(f"Error opening browser: {e}")
                snooze_alarms.remove((snooze_time, alarm))
        
        time.sleep(1)

# === THEMED GUI ===
app = ThemedTk(theme="equilux")
app.title("BeatWake - Spotify Alarm Clock")
app.geometry("600x500")
app.configure(bg="#2b2b2b")

# === Styles ===
style = ttk.Style(app)
style.configure("TLabel", background="#2b2b2b", foreground="white", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10))
style.configure("TCheckbutton", background="#2b2b2b", foreground="white")
style.configure("TEntry", font=("Segoe UI", 10))
style.configure("TSpinbox", font=("Segoe UI", 10))

# === Alarm Label ===
ttk.Label(app, text="Alarm Label (optional)").pack(pady=5)
label_entry = ttk.Entry(app, width=60)
label_entry.pack()

# === Time Inputs ===
ttk.Label(app, text="Set Time (HH:MM)").pack(pady=5)
time_frame = ttk.Frame(app)
time_frame.pack()
hour_var = tk.StringVar(value="07")
minute_var = tk.StringVar(value="00")
ttk.Spinbox(time_frame, from_=0, to=23, textvariable=hour_var, width=5, format="%02.0f").pack(side="left", padx=2)
ttk.Label(time_frame, text=":").pack(side="left")
ttk.Spinbox(time_frame, from_=0, to=59, textvariable=minute_var, width=5, format="%02.0f").pack(side="left", padx=2)

# === URL Input ===
ttk.Label(app, text="Spotify URL").pack(pady=5)
url_entry = ttk.Entry(app, width=60)
url_entry.insert(0, "https://open.spotify.com/track/6habFhsOp2NvshLv26DqMb")
url_entry.pack()

# === Repeat Options ===
ttk.Label(app, text="Repeat").pack(pady=5)
repeat_frame = ttk.Frame(app)
repeat_frame.pack()
repeat_vars = {day: tk.IntVar() for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
for day in repeat_vars:
    ttk.Checkbutton(repeat_frame, text=day, variable=repeat_vars[day]).pack(side="left")

once_var = tk.IntVar()
ttk.Checkbutton(app, text="Once", variable=once_var).pack(pady=3)

# === Alarm List Display ===
ttk.Label(app, text="Alarms List (Double-click to toggle enable/disable)").pack(pady=5)
alarm_listbox = tk.Listbox(app, width=80, height=10, bg="#1e1e1e", fg="white", font=("Consolas", 9))
alarm_listbox.pack(pady=5)

def toggle_alarm_enabled(event):
    """Toggle alarm enabled/disabled on double-click"""
    selected = alarm_listbox.curselection()
    if selected:
        index = selected[0]
        alarms[index].enabled = not alarms[index].enabled
        update_alarm_listbox()
        save_alarms()
        status = "enabled" if alarms[index].enabled else "disabled"
        update_status(f"Alarm {status}")

alarm_listbox.bind("<Double-Button-1>", toggle_alarm_enabled)

# === Core Functions ===
def update_alarm_listbox():
    alarm_listbox.delete(0, tk.END)
    # Sort alarms by time
    sorted_alarms = sorted(alarms, key=lambda a: a.time_str)
    for i, alarm in enumerate(sorted_alarms):
        status = "✓" if alarm.enabled else "✗"
        label = f"[{alarm.label}] " if alarm.label else ""
        next_trigger = alarm.get_next_trigger()
        display = f"{status} {alarm.time_str} | {label}{', '.join(alarm.repeat_days)} | Next: {next_trigger}"
        alarm_listbox.insert(tk.END, display)
        
        # Update global alarms list to match sorted order for selection
        alarms[i] = alarm

def add_alarm():
    alarm_time = f"{hour_var.get().zfill(2)}:{minute_var.get().zfill(2)}"
    url = url_entry.get().strip()
    label = label_entry.get().strip()
    
    if not url.startswith("https://open.spotify.com"):
        messagebox.showerror("Invalid URL", "Please enter a valid Spotify link.")
        return

    repeat_days = []
    if once_var.get():
        repeat_days = ["Once"]
    else:
        full_day_names = {
            "Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday",
            "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"
        }
        for short, full in full_day_names.items():
            if repeat_vars[short].get():
                repeat_days.append(full)

    if not repeat_days:
        messagebox.showwarning("No Repeat Selected", "Please choose at least one repeat option.")
        return

    new_alarm = Alarm(alarm_time, url, repeat_days, enabled=True, label=label)
    alarms.append(new_alarm)
    update_alarm_listbox()
    save_alarms()
    update_status(f"Alarm added: {label or alarm_time}")
    
    # Clear label entry after adding
    label_entry.delete(0, tk.END)

def remove_selected():
    selected = alarm_listbox.curselection()
    if selected:
        index = selected[0]
        alarms.pop(index)
        update_alarm_listbox()
        save_alarms()

def test_alarm():
    url = url_entry.get().strip()
    if not url.startswith("https://open.spotify.com"):
        messagebox.showerror("Invalid URL", "Please enter a valid Spotify link.")
        return
    webbrowser.open(url)

def snooze_selected(minutes=5):
    """Snooze selected alarm"""
    selected = alarm_listbox.curselection()
    if selected:
        index = selected[0]
        snooze_alarm(alarms[index], minutes)
    else:
        messagebox.showinfo("No Selection", "Please select an alarm to snooze.")

# === Status Bar ===
status_var = tk.StringVar(value="Ready")
status_bar = ttk.Label(app, textvariable=status_var, relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

def update_status(message):
    """Update status bar with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_var.set(f"[{timestamp}] {message}")

# === Buttons ===
btn_frame = ttk.Frame(app)
btn_frame.pack(pady=10)
ttk.Button(btn_frame, text="Add Alarm", width=15, command=add_alarm).pack(side="left", padx=5)
ttk.Button(btn_frame, text="Remove Selected", width=15, command=remove_selected).pack(side="left", padx=5)
ttk.Button(btn_frame, text="Test Alarm", width=15, command=test_alarm).pack(side="left", padx=5)
ttk.Button(btn_frame, text="Snooze 5min", width=15, command=lambda: snooze_selected(5)).pack(side="left", padx=5)

# === Start Alarm Thread ===
load_alarms()
threading.Thread(target=alarm_checker, daemon=True).start()
update_status("Application started")

app.mainloop()
