#!/usr/bin/env python3
"""Phase 24-C commit+push via GitHub Git Data API (full pack fetch is
sandbox-blocked; same path as Phase 21.11/22.16). Tokens from /tmp/.ems_tokens
(never printed). Commits tracked files under the repo dir, then badge audit."""
import os, json, base64, urllib.request

REPO = "Dani-Devlop/edit-master-skill"
REPO_DIR = "/home/z/my-project/download/edit-master-skill"
TOK = [l.split("=", 1)[1].strip() for l in open("/tmp/.ems_tokens") if l.startswith("GH_TOKEN=")][0]
API = f"https://api.github.com/repos/{REPO}"

def req(method, path, payload=None, m="GET"):
    url = path if path.startswith("http") else f"{API}/{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(url, data=data, method=m, headers={
        "Authorization": f"token {TOK}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read())

# 1) files to commit (git status; local snapshot repo root = /home/z/my-project,
# so paths carry the download/edit-master-skill/ prefix — strip it)
import subprocess
PREFIX = "download/edit-master-skill/"
st = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_DIR, capture_output=True, text=True).stdout
paths = set()
for line in st.splitlines():
    code, p = line[:2], line[3:].strip()
    if not p.startswith(PREFIX):
        continue
    p = p[len(PREFIX):]
    if code in ("M ", " M", "AM", "MM", "A "):
        paths.add(p)
    elif code == "??":
        if os.path.isfile(os.path.join(REPO_DIR, p)):
            paths.add(p)
        else:
            for root, _, files in os.walk(os.path.join(REPO_DIR, p)):
                for f in files:
                    rel = os.path.relpath(os.path.join(root, f), REPO_DIR)
                    if os.path.getsize(os.path.join(REPO_DIR, rel)) < 8 * 1000 * 1000:
                        paths.add(rel)
paths = sorted(p for p in paths if not p.startswith("test-results/videos/")
               and not p.endswith(".mp4") and not p.endswith(".wav"))
print("files:", len(paths))

head = req("", "git/ref/heads/main")["object"]["sha"]
head_commit = req("", f"git/commits/{head}")
base_tree = head_commit["tree"]["sha"]
print("remote HEAD:", head[:12])

# 2) blobs
tree = []
for p in paths:
    fp = os.path.join(REPO_DIR, p)
    data = open(fp, "rb").read()
    b = req("", "git/blobs", {"content": base64.b64encode(data).decode(), "encoding": "base64"}, m="POST")
    tree.append({"path": p, "mode": "100644", "type": "blob", "sha": b["sha"]})
    print("blob ok:", p, flush=True)

# 3) tree
tr = req("", "git/trees", {"base_tree": base_tree, "tree": tree}, m="POST")
print("tree:", tr["sha"][:12], len(tr["tree"]), "entries")

# 4) commit
msg = ("Phase 24 IG-native feel: beat-lock + pseudo-UI + seamless loop + kinetic slams\n\n"
       "- IG1-IG10 implemented on ONE render path (render_t1_v24 + ig24kit)\n"
       "- CRITICAL FIX: find_coeffs homography direction (M1/M2/M5 quad_warp were empty)\n"
       "- selective_color luma *255 fix (isolation beat was black)\n"
       "- camera guarantee: monotone push-in + velocity-positive pans (G3/IG12)\n"
       "- gates 17/17 PASS on delivered file; loudness I -14.1 TP -2.5\n"
       "- replica(live) critic 8.5/10 PASS round 1\n"
       "- master blind critic honest NO-PASS 6.9-7.6 (bar 8.5); blockers + r25 plan logged\n"
       "- task.md Phase 24-C run log included")
c = req("", "git/commits", {"message": msg, "tree": tr["sha"], "parents": [head]}, m="POST")
print("commit:", c["sha"])

# 5) push (fast-forward)
ref = req("", "git/refs/heads/main", {"sha": c["sha"], "force": False}, m="PATCH")
print("pushed:", ref["object"]["sha"][:12])

# 6) badge audit
commits = req("", "commits?per_page=10&sha=main")
unv = 0
for c2 in commits:
    v = c2["commit"]["verification"]
    tag = "verified" if v["verified"] else ("unverified" if v.get("reason") not in ("unsigned",) else "unsigned")
    if tag == "unverified":
        unv += 1
    print(f'  {c2["sha"][:9]} {tag}')
print(f"BADGE AUDIT: {unv} unverified (policy: verified or unsigned-no-badge)")
