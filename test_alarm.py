from datetime import datetime, timedelta

# Calculate time 1 minute from now
test_time = datetime.now() + timedelta(minutes=1)
print(f"Set alarm to: {test_time.strftime('%H:%M')}")
print(f"Current day: {test_time.strftime('%A')}")
print("\nSteps:")
print("1. Run BeatWake-SourceCode.py")
print(f"2. Set time to {test_time.strftime('%H:%M')}")
print(f"3. Check '{test_time.strftime('%A')[:3]}' or 'Once'")
print("4. Click 'Add Alarm'")
print("5. Wait ~1 minute for alarm to trigger")
