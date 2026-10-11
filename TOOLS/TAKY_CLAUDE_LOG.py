import json, os, shutil, time
from pathlib import Path
from datetime import datetime
from collections import deque

CLAUDE_ROOT = Path.home()/".claude"/"projects"/"D--Git-PWA-TAKY"
CODEX_ROOT = Path.home()/".codex"
STATUS_FILE = Path(os.environ.get("TEMP","."))/"TAKY_STATUSLINE_LAST.json"
events = deque(maxlen=80)

def short(s,n=110):
    s=" ".join(str(s).split())
    return s if len(s)<=n else s[:n-1]+"…"

def latest_claude():
    files=list(CLAUDE_ROOT.glob("*.jsonl"))
    return max(files,key=lambda p:p.stat().st_mtime) if files else None

def add_event(obj):
    typ=obj.get("type","")
    msg=obj.get("message") or {}
    ts=datetime.now().strftime("%H:%M:%S")
    if typ=="assistant":
        for c in msg.get("content") or []:
            if isinstance(c,dict) and c.get("type")=="tool_use":
                events.append(f"[{ts}] [TOOL] {c.get('name','tool')}")
            elif isinstance(c,dict) and c.get("type")=="text" and c.get("text"):
                events.append(f"[{ts}] [CLAUDE] {short(c['text'])}")
        u=msg.get("usage") or {}
        if u:
            events.append(f"[{ts}] [TOKENS] in {u.get('input_tokens',0)} | out {u.get('output_tokens',0)} | cache {u.get('cache_read_input_tokens',0)}")
    elif typ=="user":
        for c in msg.get("content") or []:
            if isinstance(c,dict) and c.get("type")=="tool_result":
                events.append(f"[{ts}] [RESULT] tool complete")
    elif typ in ("system","progress"):
        txt=obj.get("content") or obj.get("status") or ""
        if txt:
            events.append(f"[{ts}] [{typ.upper()}] {short(txt)}")

def pct_left(used):
    try:
        return f"{max(0, round(100-float(used)))}%"
    except Exception:
        return "N/A"

def claude_usage():
    try:
        d=json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        rl=d.get("rate_limits") or {}
        five=((rl.get("five_hour") or {}).get("used_percentage"))
        week=((rl.get("seven_day") or {}).get("used_percentage"))
        ctx=((d.get("context_window") or {}).get("used_percentage"))
        return pct_left(five), pct_left(week), ("N/A" if ctx is None else f"{round(float(ctx))}%")
    except Exception:
        return "N/A","N/A","N/A"

_codex_cache=(0,None)
def codex_usage():
    global _codex_cache
    now=time.time()
    if now-_codex_cache[0] < 5 and _codex_cache[1] is not None:
        return _codex_cache[1]
    candidates=[]
    for sub in ("sessions","archived_sessions"):
        root=CODEX_ROOT/sub
        if root.exists():
            try:
                candidates.extend(root.rglob("*.jsonl"))
            except Exception:
                pass
    candidates=sorted(candidates,key=lambda p:p.stat().st_mtime,reverse=True)[:30]
    best=None
    for p in candidates:
        try:
            lines=p.read_text(encoding="utf-8",errors="ignore").splitlines()
        except Exception:
            continue
        for line in reversed(lines[-400:]):
            try:
                o=json.loads(line)
                payload=o.get("payload") or {}
                rl=payload.get("rate_limits")
                if not rl:
                    continue
                pri=rl.get("primary") or {}
                sec=rl.get("secondary") or {}
                if pri.get("window_minutes")==300 and sec.get("window_minutes")==10080:
                    best=(pct_left(pri.get("used_percent")),pct_left(sec.get("used_percent")))
                    break
            except Exception:
                pass
        if best:
            break
    if best is None:
        best=("N/A","N/A")
    _codex_cache=(now,best)
    return best

def render(session_name="waiting"):
    cols,rows=shutil.get_terminal_size((120,30))
    body_rows=max(6,rows-8)
    visible=list(events)[-body_rows:]
    claude5,claude7,ctx=claude_usage()
    chat5,chat7=codex_usage()
    out=[]
    out.append("TAKY | REMOTE + CLAUDE LIVE")
    out.append(f"[REMOTE] Desktop Commander connected  |  [SESSION] {session_name}")
    out.append("-"*min(cols,110))
    out.extend(visible)
    while len(out)<rows-4:
        out.append("")
    out.append("-"*min(cols,110))
    out.append(f"[CLAUDE REMOTE] context {ctx} | 5h left {claude5} | week left {claude7}")
    out.append(f"[CHATGPT/CODEX] 5h left {chat5} | week left {chat7}")
    out.append("usage refresh: 5 sec | values are remaining % | Ctrl+C: stop")
    print("\x1b[2J\x1b[H"+"\n".join(out),end="",flush=True)

current=None
pos=0
last_render=0
session_name="waiting"
events.append("[LOG] Waiting for Claude activity...")

while True:
    f=latest_claude()
    if f and f!=current:
        current=f
        session_name=f.stem
        events.append(f"[SESSION] {session_name}")
        try:
            lines=current.read_text(encoding="utf-8",errors="ignore").splitlines()[-12:]
            for line in lines:
                try: add_event(json.loads(line))
                except Exception: pass
            pos=f.stat().st_size
        except Exception:
            pass
    if current and current.exists():
        try:
            with current.open("r",encoding="utf-8",errors="ignore") as h:
                h.seek(pos)
                while True:
                    line=h.readline()
                    if not line: break
                    pos=h.tell()
                    try: add_event(json.loads(line))
                    except Exception: pass
        except Exception:
            pass
    now=time.time()
    if now-last_render>=1:
        render(session_name)
        last_render=now
    time.sleep(0.5)
