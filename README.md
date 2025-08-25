pyfetch:-
A tiny, cross-platform Neofetch-style system information tool written in pure Python.
It displays your system details alongside a simple ASCII logo of your OS.

Features:-
1. Works on Linux, macOS, and Windows (including WSL/PowerShell).
2. Pure Python – only uses the standard library (with graceful enhancements if psutil is available).

Gathers system info:
1. OS, kernel, uptime
2. Host, shell, DE/WM
3. CPU, GPU, memory, disk usage
4. Battery status, IP address
5. Installed package counts (APT, pacman, RPM, apk, Homebrew, Python)
5. ASCII logos for Linux, Ubuntu, Arch, Debian, macOS, and Windows.
6. Colorful output similar to Neofetch.

Installation:-<br>
Clone the repo and run directly.<br>
Usage:<br>
python3 pyfetch.py<br>

Output example (Linux):
username@hostname
───────────────
        .--.         OS: Ubuntu 22.04
       |o_o |        Host: user@machine
       |:_/ |        Kernel: 6.8.0-35-generic
      //   \\        Uptime: 2h 15m
     (|     | )      Shell: /bin/bash
    /'\_   _/`\      Resolution: 1920x1080
    \___)=(___/      DE/WM: GNOME
                     CPU: Intel i5-1135G7
                     GPU: Intel Iris Xe
                     Memory: 3.1 GB / 7.7 GB
                     Disk: 52 GB / 120 GB (43%)
                     Packages: apt: 1823, python: 88
                     Battery: 97% (AC)
                     IP: 192.0.x.x

-> Runs fine without extra dependencies.<br>
-> If psutil is installed, memory, battery, and uptime detection improve.<br>
-> Package detection works best on Linux/macOS with common package managers available.<br>

Contributing:-
Pull requests and improvements are welcome!
If you want to add more ASCII logos or extend detection, feel free to open an issue or PR.
