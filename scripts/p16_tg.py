#!/usr/bin/env python3
"""Telegram LIVE-ONLY sender for Phase 16. Tokens read from /tmp/.ems_tokens, never printed."""
import os, sys, json, time, urllib.request, urllib.parse

def load_tokens(path="/tmp/.ems_tokens"):
    d = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                d[k] = v
    return d

T = load_tokens()
API = f"https://api.telegram.org/bot{T['TG_TOKEN']}"
CHAT = T["OWNER_CHAT_ID"]

def _post(method, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{API}/{method}", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send(text, silent=False):
    # chunk to 4000 chars
    for i in range(0, max(len(text), 1), 4000):
        r = _post("sendMessage", {"chat_id": CHAT, "text": text[i:i+4000],
                                  "disable_notification": silent,
                                  "parse_mode": "HTML"})
        if not r.get("ok"):
            print("TG-ERR", r.get("error", r.get("description")), file=sys.stderr)
            return False
        time.sleep(0.4)
    return True

def send_photo(path, caption=""):
    with open(path, "rb") as f:
        boundary = "----ems16boundary"
        parts = []
        parts.append(("--{0}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{1}\r\n".format(boundary, CHAT)).encode())
        if caption:
            parts.append(("--{0}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{1}\r\n".format(boundary, caption[:1000])).encode())
        parts.append(("--{0}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{1}\"\r\n\r\n".format(boundary, os.path.basename(path))).encode())
        body = b"".join(parts) + f.read() + ("\r\n--{0}--\r\n".format(boundary)).encode()
        req = urllib.request.Request(f"{API}/sendPhoto", data=body,
                                     headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read()).get("ok", False)
        except Exception as e:
            print("TG-ERR", e, file=sys.stderr)
            return False

def send_video(path, caption=""):
    size = os.path.getsize(path)
    if size > 49 * 1000 * 1000:
        return False
    with open(path, "rb") as f:
        boundary = "----ems16boundary"
        parts = []
        parts.append(("--{0}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{1}\r\n".format(boundary, CHAT)).encode())
        parts.append(("--{0}\r\nContent-Disposition: form-data; name=\"supports_streaming\"\r\n\r\ntrue\r\n".format(boundary)).encode())
        if caption:
            parts.append(("--{0}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{1}\r\n".format(boundary, caption[:1000])).encode())
        parts.append(("--{0}\r\nContent-Disposition: form-data; name=\"video\"; filename=\"{1}\"\r\n\r\n".format(boundary, os.path.basename(path))).encode())
        body = b"".join(parts) + f.read() + ("\r\n--{0}--\r\n".format(boundary)).encode()
        req = urllib.request.Request(f"{API}/sendVideo", data=body,
                                     headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read()).get("ok", False)
        except Exception as e:
            print("TG-ERR", e, file=sys.stderr)
            return False

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "msg":
        sys.exit(0 if send(sys.argv[2], silent=(len(sys.argv) > 3 and sys.argv[3] == "silent")) else 1)
    elif cmd == "photo":
        sys.exit(0 if send_photo(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "") else 1)
    elif cmd == "video":
        sys.exit(0 if send_video(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "") else 1)
