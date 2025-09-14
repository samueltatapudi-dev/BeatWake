import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import time
import threading
import webbrowser
from ttkthemes import ThemedTk

# === Alarm Class ===
class Alarm:
    def __init__(self, time_str, url, repeat_days):
        self.time_str = time_str
        self.url = url
        self.repeat_days = repeat_days

    def should_trigger(self):
        now = datetime.now()
        now_str = now.strftime("%H:%M")
        weekday = now.strftime("%A")
        if now_str != self.time_str:
            return False
        return "Once" in self.repeat_days or weekday in self.repeat_days

alarms = []

def alarm_checker():
    while True:
        for alarm in list(alarms):
            if alarm.should_trigger():
                webbrowser.open(alarm.url)
                if "Once" in alarm.repeat_days:
                    alarms.remove(alarm)
                    update_alarm_listbox()
        time.sleep(10)

# === THEMED GUI ===
app = ThemedTk(theme="equilux")  # Dark theme
app.title("Spotify Multi-Alarm Clock")
app.geometry("600x500")
app.configure(bg="#2b2b2b")

# === Styles ===
style = ttk.Style(app)
style.configure("TLabel", background="#2b2b2b", foreground="white", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10))
style.configure("TCheckbutton", background="#2b2b2b", foreground="white")
style.configure("TEntry", font=("Segoe UI", 10))
style.configure("TSpinbox", font=("Segoe UI", 10))

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
ttk.Label(app, text="Alarms List").pack(pady=5)
alarm_listbox = tk.Listbox(app, width=80, height=10, bg="#1e1e1e", fg="white", font=("Consolas", 9))
alarm_listbox.pack(pady=5)

# === Core Functions ===
def update_alarm_listbox():
    alarm_listbox.delete(0, tk.END)
    for alarm in alarms:
        label = f"{alarm.time_str} | {', '.join(alarm.repeat_days)} | {alarm.url}"
        alarm_listbox.insert(tk.END, label)

def add_alarm():
    alarm_time = f"{hour_var.get()}:{minute_var.get()}"
    url = url_entry.get().strip()
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

    new_alarm = Alarm(alarm_time, url, repeat_days)
    alarms.append(new_alarm)
    update_alarm_listbox()

def remove_selected():
    selected = alarm_listbox.curselection()
    if selected:
        index = selected[0]
        alarms.pop(index)
        update_alarm_listbox()

def test_alarm():
    url = url_entry.get().strip()
    if not url.startswith("https://open.spotify.com"):
        messagebox.showerror("Invalid URL", "Please enter a valid Spotify link.")
        return
    webbrowser.open(url)

# === Buttons ===
btn_frame = ttk.Frame(app)
btn_frame.pack(pady=10)
ttk.Button(btn_frame, text="Add Alarm", width=20, command=add_alarm).pack(side="left", padx=5)
ttk.Button(btn_frame, text="Remove Selected", width=20, command=remove_selected).pack(side="left", padx=5)
ttk.Button(btn_frame, text="Test Alarm", width=20, command=test_alarm).pack(side="left", padx=5)

# === Start Alarm Thread ===
threading.Thread(target=alarm_checker, daemon=True).start()

app.mainloop()
