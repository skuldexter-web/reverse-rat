```python
import json


def recv_exact(conn, n):
    data = b""
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            raise ConnectionError("connection closed")
        data += chunk
    return data


def send_msg(conn, obj):
    data = json.dumps(obj).encode("utf-8")
    conn.sendall(len(data).to_bytes(4, "big"))
    conn.sendall(data)


def recv_msg(conn):
    try:
        header = recv_exact(conn, 4)
        length = int.from_bytes(header, "big")
        payload = recv_exact(conn, length)
        return json.loads(payload.decode("utf-8"))
    except Exception:
        return None
```
