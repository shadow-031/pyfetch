#!/usr/bin/env python3
"""
pyfetch — a tiny, cross‑platform Neofetch‑style system info tool in pure Python.
- Tries to use only stdlib; enhances output if optional tools are available.
- Degrades gracefully when something isn't present.
Tested on Linux, macOS, and Windows (PowerShell/WSL).
"""

from __future__ import annotations
import os
import sys
import platform
import subprocess
import shutil
import time
import socket
from datetime import datetime
from typing import Optional, Tuple

# Optional extras (graceful fallback if missing)
try:
    import psutil  # type: ignore
except Exception:
    psutil = None  # fallback to stdlib

def run(cmd: list[str] | str, timeout: float = 1.5) -> str:
    """
    Run a shell command safely, return stdout (stripped). Empty string if fails.
    """
    try:
        if isinstance(cmd, str):
            shell = True
        else:
            shell = False
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, shell=shell, timeout=timeout)
        return out.decode(errors="ignore").strip()
    except Exception:
        return ""

def which(name: str) -> Optional[str]:
    return shutil.which(name)

def human_bytes(n: float) -> str:
    for unit in ["B","KB","MB","GB","TB","PB"]:
        if n < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} EB"

def parse_uptime(seconds: float) -> str:
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes or not parts: parts.append(f"{minutes}m")
    return " ".join(parts)

def get_os() -> Tuple[str, str]:
    system = platform.system()
    if system == "Linux":
        # best effort: /etc/os-release
        pretty = ""
        try:
            with open("/etc/os-release") as f:
                data = {}
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        data[k] = v.strip('"')
                pretty = data.get("PRETTY_NAME") or data.get("NAME", "")
        except Exception:
            pass
        return pretty or "Linux", platform.release()
    elif system == "Darwin":
        ver = run(["sw_vers", "-productVersion"]) or platform.mac_ver()[0]
        return "macOS", ver
    elif system == "Windows":
        ver = platform.version()
        rel = platform.release()
        return f"Windows {rel}", ver
    else:
        return system or "Unknown", platform.release()

def get_kernel() -> str:
    return platform.release()

def get_host() -> str:
    user = os.environ.get("USER") or os.environ.get("USERNAME") or "user"
    host = socket.gethostname()
    return f"{user}@{host}"

def get_shell() -> str:
    if os.name == "nt":
        return os.environ.get("COMSPEC","cmd.exe")
    return os.environ.get("SHELL", run(["getent","passwd",os.environ.get("USER","")]).split(":")[-1] if which("getent") else "sh")

def get_res() -> Optional[str]:
    # Try tkinter for primary display size, then xrandr (Linux), then fallback.
    try:
        import tkinter as tk  # type: ignore
        root = tk.Tk()
        root.withdraw()
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        root.destroy()
        return f"{w}x{h}"
    except Exception:
        pass
    if which("xrandr"):
        # parse connected monitors
        out = run("xrandr | grep -w connected | awk '{print $3}' | sed 's/+.*//g' | sed 's/primary //g'")
        if out:
            # Could be multiple lines; join with ", "
            vals = [v for v in out.splitlines() if "x" in v]
            if vals:
                return ", ".join(vals)
    return None

def get_de_wm() -> Optional[str]:
    # Very best effort; mostly Linux desktops
    for key in ("XDG_CURRENT_DESKTOP","DESKTOP_SESSION","GDMSESSION"):
        val = os.environ.get(key)
        if val:
            return val
    # macOS & Windows
    if platform.system() == "Darwin":
        return "Aqua"
    if platform.system() == "Windows":
        return "Explorer"
    return None

def get_cpu() -> Optional[str]:
    system = platform.system()
    if system == "Windows":
        name = os.environ.get("PROCESSOR_IDENTIFIER")
        if not name:
            name = run('wmic cpu get Name /value').split("=",1)[-1].strip()
        return name or platform.processor() or None
    elif system == "Darwin":
        name = run(["sysctl","-n","machdep.cpu.brand_string"])
        return name or platform.processor() or None
    else:
        # Linux
        try:
            with open("/proc/cpuinfo","r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":",1)[1].strip()
        except Exception:
            pass
        return platform.processor() or None

def get_gpu() -> Optional[str]:
    system = platform.system()
    if system == "Windows":
        val = run('wmic path win32_VideoController get name').splitlines()
        names = [v.strip() for v in val if v.strip() and "Name" not in v]
        return ", ".join(names) if names else None
    elif system == "Darwin":
        out = run(["system_profiler","SPDisplaysDataType"])
        lines = [l.strip() for l in out.splitlines() if "Chipset Model" in l or "Vendor" in l]
        return "; ".join(lines) if lines else None
    else:
        if which("lspci"):
            out = run("lspci | grep -i -E 'vga|3d|display'")
            return out if out else None
    return None

def get_memory() -> Optional[str]:
    if psutil:
        vm = psutil.virtual_memory()
        return f"{human_bytes(vm.used)} / {human_bytes(vm.total)}"
    else:
        if platform.system() == "Linux":
            try:
                meminfo = {}
                with open("/proc/meminfo") as f:
                    for line in f:
                        k, v = line.split(":",1)
                        meminfo[k] = v.strip()
                total_kb = float(meminfo["MemTotal"].split()[0])
                avail_kb = float(meminfo.get("MemAvailable", "0 kB").split()[0])
                used = (total_kb - avail_kb) * 1024
                total = total_kb * 1024
                return f"{human_bytes(used)} / {human_bytes(total)}"
            except Exception:
                return None
    return None

def get_disk() -> Optional[str]:
    try:
        st = shutil.disk_usage("/")
        used = st.total - st.free
        return f"{human_bytes(used)} / {human_bytes(st.total)} ({int(used*100/st.total)}%)"
    except Exception:
        return None

def get_uptime() -> Optional[str]:
    if psutil and hasattr(psutil, "boot_time"):
        return parse_uptime(time.time() - psutil.boot_time())
    # Fallbacks
    if platform.system() == "Linux":
        try:
            with open("/proc/uptime") as f:
                up = float(f.read().split()[0])
                return parse_uptime(up)
        except Exception:
            return None
    if platform.system() == "Darwin":
        out = run(["sysctl","-n","kern.boottime"])
        # { sec = 1700000000, usec = ... } ...
        try:
            sec = int(out.split("sec =")[1].split(",")[0].strip())
            return parse_uptime(time.time() - sec)
        except Exception:
            pass
    if platform.system() == "Windows":
        out = run("net stats srv")
        for line in out.splitlines():
            if "Statistics since" in line:
                try:
                    boot = datetime.strptime(line.split("since",1)[1].strip(), "%m/%d/%Y %I:%M:%S %p")
                except Exception:
                    # Locale differences; give up
                    return None
                return parse_uptime((datetime.now() - boot).total_seconds())
    return None

def get_packages() -> Optional[str]:
    # Count packages from common managers (best-effort, Linux/macOS). This can be slow—keep it snappy.
    candidates = []
    if which("dpkg-query"):
        out = run(["bash","-lc","dpkg-query -f '${binary:Package}\n' -W | wc -l"])
        if out.isdigit():
            candidates.append(("apt (dpkg)", out))
    if which("pacman"):
        out = run(["bash","-lc","pacman -Qq | wc -l"])
        if out.isdigit():
            candidates.append(("pacman", out))
    if which("rpm"):
        out = run(["bash","-lc","rpm -qa | wc -l"])
        if out.isdigit():
            candidates.append(("rpm", out))
    if which("apk"):
        out = run(["bash","-lc","apk info | wc -l"])
        if out.isdigit():
            candidates.append(("apk", out))
    if which("brew"):
        out = run(["bash","-lc","brew list --formula | wc -l"])
        if out.isdigit():
            candidates.append(("brew", out))
    # Python packages (user env)
    try:
        import pkgutil
        pycount = sum(1 for _ in pkgutil.iter_modules())
        candidates.append(("python", str(pycount)))
    except Exception:
        pass
    if not candidates:
        return None
    return ", ".join(f"{mgr}: {count}" for mgr, count in candidates)

def get_battery() -> Optional[str]:
    if psutil and hasattr(psutil, "sensors_battery"):
        b = psutil.sensors_battery()
        if b is None: return None
        pct = int(b.percent)
        plugged = " (AC)" if b.power_plugged else ""
        return f"{pct}%{plugged}"
    # macOS fallback
    if platform.system() == "Darwin":
        out = run(["pmset","-g","batt"])
        if out:
            line = out.splitlines()[1] if len(out.splitlines()) > 1 else out
            return line.strip()
    return None

def get_ip() -> Optional[str]:
    # best-effort local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

# --- ASCII logos -------------------------------------------------------------

LOGOS = {
"Linux": [
"        .--.      ",
"       |o_o |     ",
"       |:_/ |     ",
"      //   \\ \\   ",
"     (|     | )   ",
"    /'\\_   _/`\\  ",
"    \\___)=(___/  ",
],
"Ubuntu": [
"         _        ",
"     ---(_)       ",
" _/  ---  \\_     ",
"(_) |     | (_)   ",
"   _\\___/_        ",
"  /  ___  \\       ",
"  \\_/   \\_/       ",
],
"Arch": [
"       /\\         ",
"      /  \\        ",
"     /\\   \\       ",
"    /      \\      ",
"   /   ,,   \\     ",
"  /   |  |  -\\    ",
" /_-''    ''-_\\   ",
],
"Debian":[
"   ____           ",
"  / __ \\___  ___  ",
" / / / / _ \\/ _ \\ ",
"/ /_/ /  __/  __/ ",
"\\____/\\___/\\___/  ",
],
"macOS":[
"       .:         ",
"     .::::.       ",
"   .::::::::.     ",
"  ::::::::::::    ",
"  ':::::::::'     ",
"    ':::::'       ",
],
"Windows":[
"⠀⠀⠀⣤⣴⣾⣿⣿⣿⣿⣿⣶⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠ ",
"⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⢰⣦⣄⣀⣀⣠⣴⣾⣿ ",
"⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⡏⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿ ",⠀
"⠀⠀⣼⣿⡿⠿⠛⠻⠿⣿⣿⡇⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⡿ ",⠀
"⠀⠀⠉⠀⠀⠀⢀⠀⠀⠀⠈⠁⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⠇ ",⠀
"⠀⠀⣠⣴⣶⣿⣿⣿⣷⣶⣤⠀⠀⠀⠈⠉⠛⠛⠛⠉⠉⠀⠀ ",⠀
"⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⣶⣦⣄⣀⣀⣀⣤⣤⣶⠀⠀",
"⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀",
" ⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀",
"⢠⣿⡿⠿⠛⠉⠉⠉⠛⠿⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀",
"⠘⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⢿⣿⣿⣿⣿⣿⠿⠛⠀⠀⠀",
],
}

def pick_logo(pretty_os: str) -> list[str]:
    for key in ("Ubuntu","Arch","Debian","Windows","macOS"):
        if key.lower() in pretty_os.lower():
            return LOGOS[key]
    if "linux" in pretty_os.lower():
        return LOGOS["Linux"]
    return LOGOS["Linux"]

# --- colors & printing -------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
DIM  = "\033[2m"
C1 = "\033[38;5;81m"   # cyan-ish
C2 = "\033[38;5;39m"   # blue-ish
C3 = "\033[38;5;213m"  # magenta-ish
C4 = "\033[38;5;190m"  # yellow-ish
C5 = "\033[38;5;118m"  # green-ish

def colorize(label: str, val: Optional[str], color=C2) -> str:
    if val is None or val == "":
        val = "—"
    return f"{BOLD}{color}{label:<10}{RESET}{val}"

def main() -> int:
    os_name, os_ver = get_os()
    host = get_host()
    kernel = get_kernel()
    shell = get_shell()
    res = get_res()
    de = get_de_wm()
    cpu = get_cpu()
    gpu = get_gpu()
    mem = get_memory()
    disk = get_disk()
    up = get_uptime()
    pkgs = get_packages()
    batt = get_battery()
    ip = get_ip()

    logo = pick_logo(os_name)

    left_width = max(len(line) for line in logo)
    rows = [
        ("OS",        f"{os_name} {os_ver}".strip()),
        ("Host",      host),
        ("Kernel",    kernel),
        ("Uptime",    up),
        ("Shell",     shell),
        ("Resolution",res),
        ("DE/WM",     de),
        ("CPU",       cpu),
        ("GPU",       gpu),
        ("Memory",    mem),
        ("Disk",      disk),
        ("Packages",  pkgs),
        ("Battery",   batt),
        ("IP",        ip),
    ]

    # Build right-hand info lines
    info_lines = [colorize(f"{k}:", v, color=[C2,C3,C4,C5,C1][i % 5]) for i,(k,v) in enumerate(rows)]

    # Interleave logo and info
    total_lines = max(len(logo), len(info_lines))
    logo += [" " * left_width] * (total_lines - len(logo))
    info_lines += [""] * (total_lines - len(info_lines))

    # Title
    title = f"{BOLD}{C1}{host}{RESET}"
    underline = f"{C1}{'─'*len(host)}{RESET}"
    print(title)
    print(underline)

    for l, info in zip(logo, info_lines):
        print(f"{C5}{l}{RESET}  {info}")

    # Palette
    palette = " ".join(f"\033[48;5;{c}m  \033[0m" for c in (196,202,226,82,45,27,93,99))
    print(f"\n{palette}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
