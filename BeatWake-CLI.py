#!/usr/bin/env python3
"""BeatWake CLI - Headless alarm manager"""

import json
import os
import sys
import time
import webbrowser
import subprocess
from datetime import datetime, timedelta

PERSIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alarms.json")

def load_alarms():
    if os.path.exists(PERSIST_PATH):
        with open(PERSIST_PATH, "r") as f:
            return json.load(f)
    return []

def save_alarms(alarms):
    with open(PERSIST_PATH, "w") as f:
        json.dump(alarms, f, indent=2)

def list_alarms():
    alarms = load_alarms()
    if not alarms:
        print("No alarms set.")
        return
    
    print("\n📋 Current Alarms:")
    print("-" * 80)
    for i, alarm in enumerate(alarms, 1):
        status = "✓" if alarm.get("enabled", True) else "✗"
        label = f"[{alarm.get('label', '')}] " if alarm.get('label') else ""
        print(f"{i}. {status} {alarm['time_str']} | {label}{', '.join(alarm['repeat_days'])}")
        print(f"   URL: {alarm['url']}")
    print("-" * 80)

def add_alarm_interactive():
    print("\n➕ Add New Alarm")
    time_str = input("Time (HH:MM): ").strip()
    label = input("Label (optional): ").strip()
    url = input("Spotify URL: ").strip()
    
    print("\nRepeat days (comma-separated): Mon,Tue,Wed,Thu,Fri,Sat,Sun")
    days_input = input("Or type 'Once': ").strip()
    
    if days_input.lower() == "once":
        repeat_days = ["Once"]
    else:
        day_map = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday",
                   "thu": "Thursday", "fri": "Friday", "sat": "Saturday", "sun": "Sunday"}
        repeat_days = [day_map[d.lower()] for d in days_input.split(",") if d.lower() in day_map]
    
    alarm = {
        "time_str": time_str,
        "url": url,
        "repeat_days": repeat_days,
        "enabled": True,
        "label": label
    }
    
    alarms = load_alarms()
    alarms.append(alarm)
    save_alarms(alarms)
    print(f"✅ Alarm added: {label or time_str}")

def delete_alarm():
    alarms = load_alarms()
    if not alarms:
        print("No alarms to delete.")
        return
    
    list_alarms()
    try:
        idx = int(input("\nEnter alarm number to delete: ")) - 1
        if 0 <= idx < len(alarms):
            deleted = alarms.pop(idx)
            save_alarms(alarms)
            print(f"✅ Deleted alarm: {deleted.get('label', deleted['time_str'])}")
        else:
            print("❌ Invalid alarm number")
    except ValueError:
        print("❌ Invalid input")

def run_daemon():
    print("🚀 BeatWake daemon started. Press Ctrl+C to stop.")
    print("Monitoring alarms...")
    
    alarms = load_alarms()
    last_check = {}
    
    try:
        while True:
            now = datetime.now()
            now_str = now.strftime("%H:%M")
            weekday = now.strftime("%A")
            
            for i, alarm in enumerate(alarms):
                if not alarm.get("enabled", True):
                    continue
                
                if alarm["time_str"] == now_str:
                    check_key = f"{i}_{now.strftime('%Y-%m-%d %H:%M')}"
                    if check_key in last_check:
                        continue
                    
                    if "Once" in alarm["repeat_days"] or weekday in alarm["repeat_days"]:
                        print(f"\n🔔 ALARM: {alarm.get('label', alarm['time_str'])}")
                        try:
                            # Try to open in browser using $BROWSER
                            subprocess.run([os.environ.get("BROWSER", "xdg-open"), alarm["url"]])
                        except:
                            print(f"   URL: {alarm['url']}")
                        
                        last_check[check_key] = True
                        
                        # Remove "Once" alarms
                        if "Once" in alarm["repeat_days"]:
                            alarms.pop(i)
                            save_alarms(alarms)
                            print("   (One-time alarm removed)")
            
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        print("\n\n👋 BeatWake daemon stopped.")

def main():
    if len(sys.argv) < 2:
        print("BeatWake CLI - Headless Alarm Manager")
        print("\nUsage:")
        print("  python BeatWake-CLI.py list          - List all alarms")
        print("  python BeatWake-CLI.py add           - Add new alarm (interactive)")
        print("  python BeatWake-CLI.py delete        - Delete an alarm")
        print("  python BeatWake-CLI.py daemon        - Run alarm daemon")
        print("\nFor GUI version, use: xvfb-run python BeatWake-SourceCode.py")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_alarms()
    elif command == "add":
        add_alarm_interactive()
    elif command == "delete":
        delete_alarm()
    elif command == "daemon":
        run_daemon()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
