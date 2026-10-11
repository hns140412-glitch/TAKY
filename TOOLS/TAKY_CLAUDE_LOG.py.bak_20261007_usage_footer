import json, time
from pathlib import Path
from datetime import datetime

ROOT = Path.home()/".claude"/"projects"/"D--Git-PWA-TAKY"

def latest():
    files=list(ROOT.glob("*.jsonl"))
    return max(files,key=lambda p:p.stat().st_mtime) if files else None

def short(s,n=110):
    s=" ".join(str(s).split())
    return s if len(s)<=n else s[:n-1]+"…"

def emit(obj):
    typ=obj.get("type","")
    msg=obj.get("message") or {}
    ts=datetime.now().strftime("%H:%M:%S")
    if typ=="assistant":
        for c in msg.get("content") or []:
            if isinstance(c,dict) and c.get("type")=="tool_use":
                print(f"[{ts}] [TOOL] {c.get('name','tool')}",flush=True)
            elif isinstance(c,dict) and c.get("type")=="text" and c.get("text"):
                print(f"[{ts}] [CLAUDE] {short(c['text'])}",flush=True)
        u=msg.get("usage") or {}
        if u:
            i=u.get("input_tokens",0); o=u.get("output_tokens",0)
            cr=u.get("cache_read_input_tokens",0)
            print(f"[{ts}] [TOKENS] in {i} | out {o} | cache {cr}",flush=True)
    elif typ=="user":
        for c in msg.get("content") or []:
            if isinstance(c,dict) and c.get("type")=="tool_result":
                print(f"[{ts}] [RESULT] tool complete",flush=True)
    elif typ in ("system","progress"):
        txt=obj.get("content") or obj.get("status") or ""
        if txt: print(f"[{ts}] [{typ.upper()}] {short(txt)}",flush=True)

print('[REMOTE] Desktop Commander connected')
print('[LOG] Waiting for Claude activity...')
current=None
pos=0
while True:
    f=latest()
    if f and f!=current:
        current=f
        print(f'[SESSION] {f.stem}',flush=True)
        try:
            lines=current.read_text(encoding='utf-8',errors='ignore').splitlines()[-12:]
            for line in lines:
                try: emit(json.loads(line))
                except Exception: pass
        except Exception: pass
        pos=f.stat().st_size
    if current and current.exists():
        with current.open('r',encoding='utf-8',errors='ignore') as h:
            h.seek(pos)
            while True:
                line=h.readline()
                if not line: break
                pos=h.tell()
                try: emit(json.loads(line))
                except Exception: pass
    time.sleep(0.5)
