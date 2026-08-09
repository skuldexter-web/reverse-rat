```python
import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from protocols import recv_msg, send_msg


def test_roundtrip():
    a, b = socket.socketpair()
    send_msg(a, {"hello": "world"})
    assert recv_msg(b) == {"hello": "world"}
    a.close()
    b.close()


if __name__ == "__main__":
    test_roundtrip()
    print("OK")
```
