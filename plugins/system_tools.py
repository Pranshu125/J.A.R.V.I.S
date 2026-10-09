from core.plugin_manager import registry
import os
import psutil
import time

@registry.register(
    name="system_report",
    description="Generates a diagnostic string of the current CPU, RAM, and time."
)
def system_report(args):
    sys_time = time.strftime('%I:%M %p')
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    return f"Time: {sys_time}, CPU: {cpu}%, Memory: {ram}%"

@registry.register(
    name="lock_workstation",
    description="Locks the user's Windows computer."
)
def lock_workstation(args):
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return "Workstation locked successfully."
