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
from spotify_auth import SpotifyAuth

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
SPOTIFY_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spotify_config.json")
snooze_alarms = []
spotify_auth = SpotifyAuth(SPOTIFY_CONFIG_PATH)

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
                
                # Try Spotify API first, fall back to browser
                track_uri = extract_track_uri(alarm.url)
                if track_uri and spotify_auth.is_authenticated():
                    try:
                        if spotify_auth.play_track(track_uri):
                            update_status(f"Alarm triggered (Spotify API): {alarm.label or alarm.time_str}")
                        else:
                            webbrowser.open(alarm.url)
                            update_status(f"Alarm triggered (Browser): {alarm.label or alarm.time_str}")
                    except Exception as e:
                        webbrowser.open(alarm.url)
                        update_status(f"Alarm triggered (Browser): {alarm.label or alarm.time_str}")
                else:
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

# Add Spotify connection status
spotify_status_frame = ttk.Frame(app)
spotify_status_frame.pack(pady=2)

def update_spotify_status_display():
    for widget in spotify_status_frame.winfo_children():
        widget.destroy()
    
    if spotify_auth.is_authenticated():
        ttk.Label(spotify_status_frame, text="🎵 Spotify Connected", 
                  foreground="green").pack(side="left", padx=5)
    else:
        ttk.Label(spotify_status_frame, text="⚠️ Spotify Not Connected (using browser)", 
                  foreground="orange").pack(side="left", padx=5)
    
    ttk.Button(spotify_status_frame, text="Spotify Settings", 
               command=open_spotify_settings, width=15).pack(side="left", padx=5)

update_spotify_status_display()

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

def extract_track_uri(url):
    """Extract Spotify URI from URL"""
    try:
        if 'track/' in url:
            track_id = url.split('track/')[1].split('?')[0]
            return f"spotify:track:{track_id}"
        elif 'album/' in url:
            album_id = url.split('album/')[1].split('?')[0]
            return f"spotify:album:{album_id}"
        elif 'playlist/' in url:
            playlist_id = url.split('playlist/')[1].split('?')[0]
            return f"spotify:playlist:{playlist_id}"
    except:
        pass
    return None

def open_spotify_settings():
    """Open Spotify connection settings dialog"""
    settings_window = tk.Toplevel(app)
    settings_window.title("Spotify Connection Settings")
    settings_window.geometry("500x400")
    settings_window.configure(bg="#2b2b2b")
    
    ttk.Label(settings_window, text="Connect BeatWake to Spotify", 
              font=("Segoe UI", 14, "bold")).pack(pady=10)
    
    # Status
    status_label = ttk.Label(settings_window, text="")
    status_label.pack(pady=5)
    
    def update_connection_status():
        if spotify_auth.is_authenticated():
            status_label.config(text="✅ Connected to Spotify", foreground="green")
        else:
            status_label.config(text="❌ Not Connected", foreground="red")
    
    update_connection_status()
    
    # Instructions
    info_frame = ttk.Frame(settings_window)
    info_frame.pack(pady=10, padx=20, fill="both", expand=True)
    
    instructions = """
To connect BeatWake to Spotify:

1. Create a Spotify App at:
   https://developer.spotify.com/dashboard

2. Click "Create App" and fill in:
   - App Name: BeatWake
   - Redirect URI: http://localhost:8888/callback

3. Copy your Client ID and Client Secret below

4. Click "Connect to Spotify" and authorize the app
    """
    
    ttk.Label(info_frame, text=instructions, justify="left", 
              wraplength=450).pack(pady=5)
    
    # Credentials input
    cred_frame = ttk.Frame(settings_window)
    cred_frame.pack(pady=10, padx=20, fill="x")
    
    ttk.Label(cred_frame, text="Client ID:").grid(row=0, column=0, sticky="w", pady=5)
    client_id_entry = ttk.Entry(cred_frame, width=50)
    client_id_entry.grid(row=0, column=1, pady=5, padx=5)
    if spotify_auth.client_id:
        client_id_entry.insert(0, spotify_auth.client_id)
    
    ttk.Label(cred_frame, text="Client Secret:").grid(row=1, column=0, sticky="w", pady=5)
    client_secret_entry = ttk.Entry(cred_frame, width=50, show="*")
    client_secret_entry.grid(row=1, column=1, pady=5, padx=5)
    if spotify_auth.client_secret:
        client_secret_entry.insert(0, spotify_auth.client_secret)
    
    # Buttons
    btn_frame = ttk.Frame(settings_window)
    btn_frame.pack(pady=10)
    
    def save_and_connect():
        client_id = client_id_entry.get().strip()
        client_secret = client_secret_entry.get().strip()
        
        if not client_id or not client_secret:
            messagebox.showerror("Error", "Please enter both Client ID and Client Secret")
            return
        
        spotify_auth.set_credentials(client_id, client_secret)
        
        def auth_callback(success):
            if success:
                settings_window.after(0, lambda: messagebox.showinfo(
                    "Success", "Successfully connected to Spotify!"))
                settings_window.after(0, update_connection_status)
            else:
                settings_window.after(0, lambda: messagebox.showerror(
                    "Error", "Failed to connect to Spotify. Please try again."))
        
        if spotify_auth.start_auth_flow(auth_callback):
            messagebox.showinfo("Authorization", 
                "Your browser will open. Please authorize BeatWake to access Spotify.")
        else:
            messagebox.showerror("Error", "Failed to start authorization flow")
    
    def open_dashboard():
        webbrowser.open("https://developer.spotify.com/dashboard")
    
    ttk.Button(btn_frame, text="Open Spotify Dashboard", 
               command=open_dashboard).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Connect to Spotify", 
               command=save_and_connect).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Close", 
               command=settings_window.destroy).pack(side="left", padx=5)

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

# Refresh Spotify status every 30 seconds
def refresh_spotify_status():
    update_spotify_status_display()
    app.after(30000, refresh_spotify_status)

refresh_spotify_status()

app.mainloop()
