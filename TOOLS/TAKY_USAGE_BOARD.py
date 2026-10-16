# TAKY usage board: read-only mobile/PC projection of existing local CLI telemetry.
# TAKY read-only monitor: explicitly connected credentials, no inference/billing mutations, no deployments.
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import secrets
import tempfile
import time
import sys
if sys.stdout is None: sys.stdout=open(os.devnull,"w")
if sys.stderr is None: sys.stderr=open(os.devnull,"w")
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

SOURCE = Path(tempfile.gettempdir()) / "TAKY_STATUSLINE_LAST.json"
HOME = Path.home() / ".codex"
KST = dt.timezone(dt.timedelta(hours=9))

def pct(v):
    try:
        n=float(v)
        return round(n,1) if 0 <= n <= 100 else None
    except (TypeError,ValueError,OverflowError):
        return None

def iso(v):
    try:
        ts = event_epoch(v)
        return dt.datetime.fromtimestamp(ts, KST).isoformat(timespec="minutes") if ts else None
    except (ValueError, TypeError, OverflowError, OSError):
        return None

def meter(value=None,reset=None):
    return {"usedPercent":pct(value),"resetAt":iso(reset)}

def entry(name,note=""):
    return {"name":name,"fiveHour":meter(),"week":meter(),"month":meter(),"context":meter(),
            "observedAt":None,"fresh":False,"note":note}

def event_epoch(value):
    if isinstance(value, (float, int)) and value > 0:
        return value / 1000 if value > 1e12 else float(value)
    if isinstance(value, str) and value:
        try:
            return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    return None


def limit_meter(value, reset, now):
    r = meter(value, reset)
    reset_epoch = event_epoch(reset)
    if reset_epoch is not None and reset_epoch <= now:
        r["usedPercent"] = None  # Expired limit evidence is not a new zero or live quota.
        r["expired"] = True
    return r


def quota_field_reason(row, usage_key, now):
    """Classify missing per-window evidence without estimating utilization."""
    if not isinstance(row, dict) or not row:
        return "WINDOW_NOT_REPORTED"
    if pct(row.get(usage_key)) is None:
        return "USAGE_VALUE_MISSING_OR_INVALID"
    reset = event_epoch(row.get("resets_at"))
    if reset is not None and reset <= now:
        return "RESET_TIME_ALREADY_PASSED"
    return "OBSERVED_VALID"


CLAUDE_POLL_MIN_SECONDS = 1800   # At most 1 provider GET per 30 minutes.
CLAUDE_429_BACKOFF = 7200      # 429: stop for at least two hours.


def claude_usage_paths():
    root = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()))/"TAKY"/"USAGE_BOARD"
    return root/"claude_oauth_usage.json", root/"claude_oauth_poll_state.json"


def save_small_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    os.replace(temp_path, path)


def refresh_claude_usage(now=None, credential_path=None, snapshot_path=None, state_path=None, fetcher=None):
    """Read-only authenticated account quota GET, zero LLM prompts.

    This OAuth endpoint is not a publicly guaranteed usage API. Respect
    429 responses with a persisted cooldown and never reuse or export the token.
    Returns a status word, not credentials or raw remote response.
    """
    import urllib.request
    import urllib.error
    now = time.time() if now is None else now
    default_snap, default_state = claude_usage_paths()
    snapshot_path = snapshot_path or default_snap
    state_path = state_path or default_state
    credential_path = credential_path or (Path.home()/".claude"/".credentials.json")
    prior = {}
    try:
        prior = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except (OSError, TypeError, ValueError, UnicodeError):
        pass
    if now < float(prior.get("nextAttempt", 0) or 0):
        return "COOLDOWN"
    try:
        blob = json.loads(credential_path.read_text(encoding="utf-8-sig"))
        oauth = blob.get("claudeAiOauth") or {}
        key = oauth.get("accessToken")
        expires = event_epoch(oauth.get("expiresAt"))
        if not isinstance(key, str) or len(key) < 20 or (expires and expires <= now + 60):
            save_small_json(state_path, {"nextAttempt":now+1800,"lastStatus":"AUTH_UNAVAILABLE"})
            return "AUTH_UNAVAILABLE"
    except (OSError, ValueError, TypeError, UnicodeError):
        save_small_json(state_path, {"nextAttempt":now+1800,"lastStatus":"AUTH_UNAVAILABLE"})
        return "AUTH_UNAVAILABLE"

    # No redirects: the OAuth bearer token must never be forwarded to another host.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    request = urllib.request.Request(
        "https://api.anthropic.com/api/oauth/usage",
        headers={"Authorization":"Bearer "+key,"anthropic-beta":"oauth-2025-04-20",
                 "Accept":"application/json","User-Agent":"TAKY-Usage-ReadOnly/1.0"},
        method="GET")
    try:
        reader = fetcher or urllib.request.build_opener(NoRedirect()).open
        with reader(request,timeout=8) as response:
            raw = response.read(150_000)
        remote = json.loads(raw)
        clean = {}
        for source in ("five_hour","seven_day"):
            field = remote.get(source) or {}
            if isinstance(field,dict):
                value = pct(field.get("utilization"))
                reset = field.get("resets_at")
                if value is not None:
                    clean[source] = {"utilization":value,"resets_at":reset if event_epoch(reset) else None}
        if not clean:
            save_small_json(state_path, {"nextAttempt":now+CLAUDE_POLL_MIN_SECONDS,
                                         "lastStatus":"NO_USAGE_FIELDS"})
            return "NO_USAGE_FIELDS"
        fresh = {"source":"claude_authenticated_usage","capturedAt":iso(now),**clean}
        save_small_json(snapshot_path,fresh)
        save_small_json(state_path, {"nextAttempt":now+CLAUDE_POLL_MIN_SECONDS,
                                     "lastStatus":"OK","lastSuccessAt":iso(now)})
        return "OK"
    except urllib.error.HTTPError as ex:
        status = int(ex.code)
        backoff = (CLAUDE_429_BACKOFF if status == 429 else
                   10800 if status in (401,403) else 3600)
        old_status = prior.get("lastStatus")
        if status == 429 and old_status == "HTTP_429":
            backoff = min(21600,CLAUDE_429_BACKOFF*2)
        save_small_json(state_path, {"nextAttempt":now+backoff,"lastStatus":"HTTP_"+str(status)})
        return "HTTP_"+str(status)
    except (urllib.error.URLError,TimeoutError,ValueError,TypeError,OSError,UnicodeError):
        save_small_json(state_path, {"nextAttempt":now+1800,"lastStatus":"NETWORK_UNAVAILABLE"})
        return "NETWORK_UNAVAILABLE"


def claude_auto_worker(server):
    """One lightweight background thread; no Claude CLI subprocess."""
    while not server.shutdown_event.is_set():
        outcome = refresh_claude_usage()
        if outcome == "OK":
            server.last = 0
        server.shutdown_event.wait(60)


def claude(path=None, now=None, usage_cache=None, oauth_snapshot=None):
    """Combine last native /usage cache and TAKY authenticated read-only observations.

    The background collector reads existing Claude Code OAuth login credentials;
    this renderer reads only sanitized numeric snapshots and timestamps.
    """
    r = entry("Claude Code", "Claude의 사용량을 관측하지 못했습니다")
    now = time.time() if now is None else now
    account = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "TAKY" / "USAGE_BOARD" / "claude_auth_status.json"
    try:
        identity = json.loads(account.read_text(encoding="utf-8-sig"))
        age = now - (event_epoch(identity.get("capturedAt")) or 0)
        if (identity.get("source") == "claude_cli_auth_status"
                and identity.get("authMethod") == "claude.ai"
                and identity.get("loggedIn") is True and 0 <= age < 86400):
            r["authConnected"] = True
            r["plan"] = str(identity.get("subscriptionType", "")).capitalize()[:30]
    except (OSError, ValueError, TypeError, UnicodeError):
        pass

    sources = [path] if path else [Path.home() / ".claude" / "statusline-last.json", SOURCE]
    observations = []
    try:
        found = [p for p in sources if p and p.is_file() and p.stat().st_size < 2_000_000]
        if found:
            selected = max(found, key=lambda p: p.stat().st_mtime)
            data = json.loads(selected.read_text(encoding="utf-8-sig"))
            if isinstance(data, dict):
                observed = selected.stat().st_mtime
                model = data.get("model") or {}
                r["model"] = str(model.get("display_name", ""))[:60] if isinstance(model, dict) else ""
                ctx = data.get("context_window") or {}
                if isinstance(ctx, dict):
                    r["context"] = meter(ctx.get("used_percentage"))
                    if r["context"]["usedPercent"] is None and isinstance(ctx.get("current_usage"), dict):
                        counts = ctx["current_usage"]
                        try:
                            tokens = sum(int(counts.get(k, 0) or 0) for k in (
                                "input_tokens", "output_tokens", "cache_creation_input_tokens",
                                "cache_read_input_tokens"))
                            max_tokens = float(ctx.get("context_window_size") or 0)
                            if tokens > 0 and max_tokens > 0:
                                r["context"] = meter(tokens * 100 / max_tokens)
                                r["context"]["estimated"] = True
                        except (ValueError, TypeError, OverflowError):
                            pass
                rates = data.get("rate_limits") or {}
                if isinstance(rates, dict):
                    windows = {}
                    reasons = {}
                    for source_key, target in (("five_hour", "fiveHour"), ("seven_day", "week")):
                        row = rates.get(source_key) or {}
                        reasons[target] = quota_field_reason(row, "used_percentage", now)
                        if isinstance(row, dict):
                            m = limit_meter(row.get("used_percentage"), row.get("resets_at"), now)
                            if m["usedPercent"] is not None:
                                windows[target] = m
                    if windows:
                        observations.append((observed, "claude_statusline", windows, reasons))
                r["observedAt"] = iso(observed)
                r["fresh"] = 0 <= now - observed <= 600
    except (OSError, UnicodeError, ValueError, AttributeError, TypeError):
        pass

    # Claude Code's own last /usage snapshot. Read only the needed fields:
    # never surface accountUuid or the rest of ~/.claude.json (may include secrets).
    cache_file = usage_cache if usage_cache is not None else Path.home() / ".claude.json"
    try:
        if cache_file.is_file() and cache_file.stat().st_size < 4_000_000:
            cache_root = json.loads(cache_file.read_text(encoding="utf-8-sig"))
            cached = cache_root.get("cachedUsageUtilization") or {}
            fetched = event_epoch(cached.get("fetchedAtMs"))
            util = cached.get("utilization") or {}
            if fetched and isinstance(util, dict) and 0 <= now - fetched < 14 * 86400:
                windows = {}
                reasons = {}
                for source_key, target in (("five_hour", "fiveHour"), ("seven_day", "week")):
                    row = util.get(source_key) or {}
                    reasons[target] = quota_field_reason(row, "utilization", now)
                    if isinstance(row, dict):
                        m = limit_meter(row.get("utilization"), row.get("resets_at"), now)
                        if m["usedPercent"] is not None:
                            windows[target] = m
                if windows:
                    observations.append((fetched, "claude_usage_cache", windows, reasons))
    except (OSError, UnicodeError, ValueError, AttributeError, TypeError):
        pass

    # If explicit test paths are provided, do not consult actual user account files.
    if oauth_snapshot is not None:
        auto_file = oauth_snapshot
    elif path is None and usage_cache is None:
        auto_file = claude_usage_paths()[0]
    else:
        auto_file = None
    try:
        if auto_file is not None and auto_file.is_file() and auto_file.stat().st_size < 10_000:
            auto = json.loads(auto_file.read_text(encoding="utf-8-sig"))
            observed = event_epoch(auto.get("capturedAt"))
            if auto.get("source") == "claude_authenticated_usage" and observed and 0 <= now - observed < 14*86400:
                windows = {}
                reasons = {}
                for source_key, target in (("five_hour","fiveHour"),("seven_day","week")):
                    item = auto.get(source_key) or {}
                    reasons[target] = quota_field_reason(item, "utilization", now)
                    if isinstance(item,dict):
                        m = limit_meter(item.get("utilization"), item.get("resets_at"), now)
                        if m["usedPercent"] is not None:
                            windows[target] = m
                if windows:
                    observations.append((observed, "claude_authenticated_usage", windows, reasons))
    except (OSError, TypeError, ValueError, AttributeError, UnicodeError):
        pass

    if observations:
        # Prefer the newest observation. Do not blend percentages from
        # different collection times, and do not use file mtime as cache time.
        observed, source, windows, reasons = max(observations, key=lambda item: item[0])
        r["quotaWindowStatus"] = dict(reasons)
        for key, m in windows.items():
            r[key] = m
            r[key]["source"] = source
            r[key]["observedAt"] = iso(observed)
        r["rateSource"] = source
        r["observedAt"] = iso(observed)
        r["fresh"] = 0 <= now - observed <= (CLAUDE_POLL_MIN_SECONDS + 120 if source == "claude_authenticated_usage" else 600)
        elapsed = max(0, round((now - observed) / 60))
        r["note"] = ("Claude Pro 인증됨 · " if r.get("authConnected") else "") + (
            "자동 계정 사용량 조회 · " if source == "claude_authenticated_usage" else
            "마지막 /usage 로컬 기록 · " if source == "claude_usage_cache" else "Claude 상태줄 기록 · "
        ) + ("최근 조회" if r["fresh"] else f"{elapsed}분 전 관측 · 실시간 아님")
    else:
        r["quotaWindowStatus"] = {"fiveHour": "NO_USABLE_OBSERVATION",
                                  "week": "NO_USABLE_OBSERVATION"}
        r["note"] = ("Claude Pro 인증됨 · " if r.get("authConnected") else "") + (
            "5시간·주간 한도 로컬 기록 없음"
        )
    if observations and not r["fresh"]:
        for period in ("fiveHour", "week"):
            if r["quotaWindowStatus"].get(period) == "OBSERVED_VALID":
                r["quotaWindowStatus"][period] = "OBSERVATION_STALE"
    return r


CODEX_POLL_MIN_SECONDS = 1800


def codex_usage_paths():
    root = Path(os.environ.get("LOCALAPPDATA",tempfile.gettempdir()))/"TAKY"/"USAGE_BOARD"
    return root/"codex_account_usage.json",root/"codex_account_poll_state.json"


def codex_app_server_read(timeout=14):
    """One-off official Codex app-server RPC. No auth file or model invocation."""
    import subprocess
    import queue
    import shutil
    import threading
    import time as clock
    command=shutil.which("codex")
    if not command:
        raise OSError("Codex CLI missing")
    env=os.environ.copy()
    env["TAKY_USER_EXPLICIT_AUTHORIZATION"]="1"
    env["TAKY_USER_INTENT"]="TAKY read-only Codex quota monitoring: no inference or mutations"
    options=dict(stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                 text=True,bufsize=1,env=env)
    if os.name=="nt":
        # A rare account-rate query must run below the user's IDE/browser priority.
        # Only this spawned process group is eligible for cleanup.
        options["creationflags"]=(subprocess.CREATE_NO_WINDOW |
                                   subprocess.BELOW_NORMAL_PRIORITY_CLASS |
                                   subprocess.CREATE_NEW_PROCESS_GROUP)
    process=subprocess.Popen([command,"app-server"],**options)
    messages=queue.Queue()
    def read_lines():
        for line in process.stdout:
            messages.put(line)
    reader=threading.Thread(target=read_lines,daemon=True)
    reader.start()
    def transmit(obj):
        process.stdin.write(json.dumps(obj,separators=(",",":"))+"\n")
        process.stdin.flush()
    deadline=clock.monotonic()+timeout
    def receive(ident):
        while clock.monotonic()<deadline:
            try:
                line=messages.get(timeout=max(0.05,min(.5,deadline-clock.monotonic())))
            except queue.Empty:
                continue
            try:response=json.loads(line)
            except ValueError:continue
            if response.get("id")==ident:
                return response
        raise TimeoutError("Codex app-server rate limit request timed out")
    try:
        transmit({"id":1,"method":"initialize",
                  "params":{"clientInfo":{"name":"TAKY-Usage","version":"1.0"},
                            "capabilities":{}}})
        init=receive(1)
        if "result" not in init:
            raise ValueError("Codex app-server initialization unavailable")
        transmit({"method":"initialized","params":{}})
        transmit({"id":2,"method":"account/rateLimits/read"})
        reply=receive(2)
        if "result" not in reply:
            raise ValueError("Codex account rate limits unavailable")
        result=reply["result"]
        if not isinstance(result,dict):
            raise ValueError("Codex response invalid")
        return result
    finally:
        try:process.stdin.close()
        except (OSError,ValueError):pass
        if os.name=="nt" and process.poll() is None:
            # The CLI may spawn a child for app-server; terminate only the
            # tree rooted at OUR subprocess PID to avoid orphaned monitors.
            try:
                subprocess.run(["taskkill","/T","/F","/PID",str(process.pid)],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, check=False, timeout=4)
            except (OSError,subprocess.TimeoutExpired):
                pass
        if process.poll() is None:
            process.terminate()
        try:process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        reader.join(timeout=0.4)


def refresh_codex_account(now=None,snapshot_path=None,state_path=None,fetcher=None):
    """Rate-gated, sanitized Codex app-server data; no credentials stored."""
    now=time.time() if now is None else now
    default_snap,default_state=codex_usage_paths()
    snapshot_path=snapshot_path or default_snap
    state_path=state_path or default_state
    try:prior=json.loads(state_path.read_text(encoding="utf-8-sig"))
    except (OSError,TypeError,ValueError,UnicodeError):prior={}
    if now < float(prior.get("nextAttempt",0) or 0):
        return "COOLDOWN"
    try:
        data=(fetcher or codex_app_server_read)()
        limits=data.get("rateLimitsByLimitId") or {}
        target=limits.get("codex") if isinstance(limits,dict) else None
        rate=target or data.get("rateLimits") or {}
        if not isinstance(rate,dict):
            raise ValueError("Codex rate limits schema invalid")
        windows={}
        for key in ("primary","secondary"):
            w=rate.get(key) or {}
            if not isinstance(w,dict):
                continue
            try:mins=int(w.get("windowDurationMins"))
            except (ValueError,TypeError):continue
            label="fiveHour" if 0 < mins <= 1440 else "week" if mins >= 2880 else None
            n=pct(w.get("usedPercent"))
            if label and n is not None:
                reset=w.get("resetsAt")
                windows[label]={"used_percent":n,
                                "resets_at":reset if event_epoch(reset) else None}
        if not windows:
            save_small_json(state_path,{"nextAttempt":now+CODEX_POLL_MIN_SECONDS,
                                        "lastStatus":"NO_RATE_LIMIT_WINDOWS"})
            return "NO_RATE_LIMIT_WINDOWS"
        clean={"source":"codex_appserver_rate_limits",
               "capturedAt":iso(now),"windows":windows,
               "planType":str(rate.get("planType",""))[:24]}
        save_small_json(snapshot_path,clean)
        save_small_json(state_path,{"nextAttempt":now+CODEX_POLL_MIN_SECONDS,
                                    "lastStatus":"OK","lastSuccessAt":iso(now)})
        return "OK"
    except (OSError,ValueError,TypeError,TimeoutError):
        save_small_json(state_path,{"nextAttempt":now+3600,
                                    "lastStatus":"RPC_UNAVAILABLE"})
        return "RPC_UNAVAILABLE"


def codex_auto_worker(server):
    while not server.shutdown_event.is_set():
        if refresh_codex_account()=="OK":
            server.last=0
        server.shutdown_event.wait(60)


def codex_cli(root=HOME, now=None):
    r = entry("Codex CLI", "최근 Codex CLI 사용한도 데이터 없음")
    now = time.time() if now is None else now
    today = dt.datetime.now().date()
    paths = []
    for days in range(3):
        day = today - dt.timedelta(days=days)
        folder = root/"sessions"/day.strftime("%Y")/day.strftime("%m")/day.strftime("%d")
        try:
            paths.extend(p for p in folder.iterdir() if p.suffix == ".jsonl")
        except OSError:
            pass
    try:
        paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        pass
    candidates = []
    for path in paths[:10]:
        try:
            modified = path.stat().st_mtime
            with path.open("rb") as f:
                f.seek(0, os.SEEK_END)
                f.seek(max(0, f.tell() - 500_000))
                lines = f.read().decode("utf-8", errors="replace").splitlines()
            for line in reversed(lines):
                try:
                    data = json.loads(line)
                except ValueError:
                    continue
                payload = data.get("payload") or {}
                if not isinstance(payload, dict):
                    continue
                rates = payload.get("rate_limits") or {}
                if not isinstance(rates, dict):
                    continue
                windows = {}
                for key in ("primary", "secondary"):
                    w = rates.get(key) or {}
                    if not isinstance(w, dict):
                        continue
                    try:
                        mins = int(w.get("window_minutes"))
                    except (ValueError, TypeError):
                        continue
                    if mins in (300, 10080):
                        windows["fiveHour" if mins == 300 else "week"] = w
                if not any(pct(w.get("used_percent")) is not None for w in windows.values()):
                    continue
                event_at = event_epoch(data.get("timestamp")) or modified
                if event_at > now + 120:  # An invalid future event must not win.
                    continue
                candidates.append((event_at, windows, payload))
                break
        except OSError:
            continue
    if not candidates:
        return r
    observed, windows, payload = max(candidates, key=lambda x: x[0])
    for key, w in windows.items():
        r[key] = limit_meter(w.get("used_percent"), w.get("resets_at"), now)
    info = payload.get("info") or {}
    if isinstance(info, dict):
        last = info.get("last_token_usage") or {}
        window = info.get("model_context_window")
        if isinstance(last, dict):
            try:
                tokens = float(last.get("total_tokens"))
                maximum = float(window)
                if 0 <= tokens <= maximum and maximum > 0:
                    r["context"] = meter(tokens * 100 / maximum)
                    r["context"]["estimated"] = True
            except (ValueError, TypeError, OverflowError, ZeroDivisionError):
                pass
    r["observedAt"] = iso(observed)
    r["fresh"] = 0 <= now - observed <= 600
    expired = all(w.get("expired", False) or w.get("usedPercent") is None
                  for w in (r["fiveHour"], r["week"]))
    if expired:
        r["note"] = "마지막 제한 기간 만료 · 최신 한도 재관측 필요"
    else:
        r["note"] = ("" if r["fresh"] else "마지막 CLI 기록 · 현재 값 아님")
    if r["context"]["usedPercent"] is not None:
        r["note"] = (r["note"] + " · " if r["note"] else "") + "컨텍스트는 마지막 턴 토큰 기반 추정"
    return r

def codex(root=HOME, now=None, usage_snapshot=None):
    """Prefer recent Codex app-server rate limits; retain CLI context evidence."""
    now=time.time() if now is None else now
    result=codex_cli(root=root,now=now)
    if usage_snapshot is None:
        # Unit tests with temporary CLI roots must not read the live user account.
        if Path(root)!=HOME:
            return result
        usage_snapshot=codex_usage_paths()[0]
    try:
        if usage_snapshot.stat().st_size > 10000:
            return result
        data=json.loads(usage_snapshot.read_text(encoding="utf-8-sig"))
        if data.get("source")!="codex_appserver_rate_limits":
            return result
        observed=event_epoch(data.get("capturedAt"))
        if not observed or not 0 <= now-observed <= 14*86400:
            return result
        prior=event_epoch(result.get("observedAt"))
        if prior and prior>observed:
            return result
        windows=data.get("windows") or {}
        # Never merge unknown new windows with obsolete session quota values.
        result["fiveHour"]=meter()
        result["week"]=meter()
        for period in ("fiveHour","week"):
            w=windows.get(period) or {}
            if isinstance(w,dict):
                result[period]=limit_meter(w.get("used_percent"),w.get("resets_at"),now)
                result[period]["source"]="codex_appserver_rate_limits"
        result["rateSource"]="codex_appserver_rate_limits"
        result["observedAt"]=iso(observed)
        result["fresh"]=now-observed <= CODEX_POLL_MIN_SECONDS+120
        result["plan"]=str(data.get("planType","")).capitalize()[:24]
        elapsed=round((now-observed)/60)
        result["note"]=("Codex 공식 앱 서버 자동 조회 · "
                        + ("최근 조회" if result["fresh"] else str(elapsed)+"분 전 기록"))
        if result["context"]["usedPercent"] is not None:
            result["note"]+=" · 컨텍스트는 CLI 마지막 턴 추정"
    except (OSError,ValueError,TypeError,AttributeError,UnicodeError):
        pass
    return result


def desktop_commander():
    r=entry("Desktop Commander","도구 호출 횟수이며 구독 한도 사용률이 아님")
    path=Path(os.environ.get("LOCALAPPDATA",tempfile.gettempdir()))/"TAKY"/"USAGE_BOARD"/"desktop_commander.json"
    try:
        data=json.loads(path.read_text(encoding="utf-8-sig"))
        count=int(data.get("totalCalls",0))
        captured=dt.datetime.fromisoformat(data["capturedAt"])
        if count < 0 or captured.tzinfo is None: return r
        r["activityCount"]=count
        r["observedAt"]=captured.isoformat(timespec="minutes")
        r["fresh"]=False
        r["note"]="MCP 호출 누적 기록 · 구독 사용률 미제공 · 실시간 아님"
    except (OSError,ValueError,TypeError,KeyError):
        pass
    return r

def netlify():
    r = entry("Netlify", "월간 크레딧 사용률은 계정 커넥터에서 제공되지 않음")
    path = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()))/"TAKY"/"USAGE_BOARD"/"netlify_account.json"
    try:
        info = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(info, dict) or info.get("source") != "authenticated_netlify_connector":
            return r
        teams = []
        for item in (info.get("teams") or [])[:6]:
            if not isinstance(item, dict):
                continue
            url = str(item.get("dashboardUrl", ""))
            if (not url.startswith("https://app.netlify.com/teams/")
                    or "?" in url or "#" in url):
                continue
            slug=url.rstrip("/").split("/")[-1]
            if slug not in NETLIFY_ALLOWED_TEAMS:continue
            detail={"name":str(item.get("name",""))[:60],
                    "slug":slug,"plan":str(item.get("plan",""))[:25],
                    "dashboardUrl":url[:200],
                    "apiConnected":netlify_connected(slug),
                    "monthlyIncluded":None,"monthlyUsed":None,
                    "monthlyIncludedRemaining":None,
                    "creditBalanceAvailable":None,
                    "balanceSource":"NOT_PROVIDED","creditObservedAt":None}
            try:
                record=json.loads(netlify_snapshot_path(slug).read_text(encoding="utf-8-sig"))
                if (record.get("source")=="netlify_official_accounts_api"
                        and record.get("slug")==slug):
                    for key in ("monthlyIncluded","monthlyUsed","monthlyIncludedRemaining",
                                "creditBalanceAvailable","balanceSource"):
                        detail[key]=record.get(key)
                    detail["creditObservedAt"]=record.get("observedAt")
            except (OSError,ValueError,TypeError,UnicodeError):
                pass
            teams.append(detail)
        r["teams"] = teams
        r["plan"] = " · ".join(sorted(set(x["plan"] for x in teams))) if teams else str(info.get("primaryPlan", ""))[:40]
        r["teamCount"] = len(teams) if teams else int(info.get("teamCount", 0))
        r["observedAt"] = str(info.get("verifiedAt", ""))[:35] or None
        r["note"] = ("팀별 API 월간 기본 제공량 확인 가능 · 실제 크레딧 잔액은 별도"
                     if any(v["balanceSource"]=="MONTHLY_CAPABILITY_ONLY" for v in teams)
                     else "팀별 계정 확인됨 · 실제 Credit balance 미확보 · 두 팀은 별도 잔액")
        r["teamCreditSource"]="monthly_capability_not_full_credit_ledger"
    except (OSError, ValueError, TypeError, UnicodeError):
        pass
    return r


NETLIFY_ALLOWED_TEAMS=("hns140412","siezeall-w0pgkzo")


def netlify_auth_path(slug):
    if slug not in NETLIFY_ALLOWED_TEAMS:
        raise ValueError("unknown Netlify team")
    return credential_file().parent / ("netlify_" + slug + ".credential.dpapi")


def netlify_snapshot_path(slug):
    return credential_file().parent / ("netlify_" + slug + "_credits.json")


def netlify_poll_path(slug):
    return credential_file().parent / ("netlify_" + slug + "_poll.json")


def netlify_connected(slug):
    try:
        return bool(dpapi_transform(netlify_auth_path(slug).read_bytes(),False))
    except (ValueError,OSError,UnicodeError):
        return False


def netlify_load_key(slug):
    try:
        return dpapi_transform(netlify_auth_path(slug).read_bytes(),False).decode("ascii")
    except (ValueError,OSError,UnicodeError):
        return None


def netlify_store_key(slug,token):
    p=netlify_auth_path(slug)
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix(".tmp")
    temp.write_bytes(dpapi_transform(token.encode("ascii"),True))
    os.replace(temp,p)


def netlify_unlink(slug):
    for p in (netlify_auth_path(slug),netlify_snapshot_path(slug),netlify_poll_path(slug)):
        try:p.unlink(missing_ok=True)
        except OSError:pass


def netlify_read_team(slug,token,now=None):
    from TAKY_NETLIFY_USAGE import fetch
    from urllib.error import HTTPError, URLError
    now=time.time() if now is None else now
    try:
        record=fetch(slug,token)
        save_small_json(netlify_snapshot_path(slug),record)
        save_small_json(netlify_poll_path(slug),
                        {"nextAttempt":now+3600,"lastStatus":"OK"})
        return "OK"
    except HTTPError as e:
        seconds=7200 if e.code==429 else 10800 if e.code in (401,403) else 3600
        save_small_json(netlify_poll_path(slug),
                        {"nextAttempt":now+seconds,"lastStatus":"HTTP_"+str(e.code)})
        return "HTTP_"+str(e.code)
    except (OSError,ValueError,TypeError,URLError):
        save_small_json(netlify_poll_path(slug),
                        {"nextAttempt":now+3600,"lastStatus":"UNAVAILABLE"})
        return "UNAVAILABLE"


def netlify_auto_worker(server):
    while not server.shutdown_event.is_set():
        now=time.time()
        for slug in NETLIFY_ALLOWED_TEAMS:
            token=netlify_load_key(slug)
            if not token:continue
            try:
                st=json.loads(netlify_poll_path(slug).read_text(encoding="utf-8-sig"))
            except (OSError,ValueError,UnicodeError):st={}
            if now >= float(st.get("nextAttempt",0) or 0):
                if netlify_read_team(slug,token)=="OK":
                    server.last=0
        server.shutdown_event.wait(60)


def elevenlabs(path=None, now=None):
    r = entry("ElevenLabs", "공식 월간 구독 사용량 연동 대기 · 인증키 미연결")
    now = time.time() if now is None else now
    path = path or Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()))/"TAKY"/"USAGE_BOARD"/"elevenlabs_subscription.json"
    try:
        if path.stat().st_size > 10_000:
            return r
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if data.get("source") != "elevenlabs_subscription_endpoint":
            return r
        usage, maximum = int(data["character_count"]), int(data["character_limit"])
        if usage < 0 or maximum <= 0:
            return r
        observed = event_epoch(data.get("capturedAt"))
        if not observed or observed > now + 60:
            return r
        r["observedAt"] = iso(observed)
        r["fresh"] = 0 <= now - observed <= 3600
        r["plan"] = str(data.get("tier", ""))[:40]
        refresh = str(data.get("character_refresh_period") or data.get("billing_period") or "")
        reset = data.get("next_character_count_reset_unix")
        if refresh == "monthly_period":
            r["month"] = limit_meter(usage * 100 / maximum, reset, now)
            r["month"]["used"] = usage
            r["month"]["limit"] = maximum
            r["month"]["remaining"] = max(0, maximum - usage)
            r["month"]["unit"] = "subscription_characters"
        else:
            r["note"] = "월간 초기화 주기 미확인 · 공식 데이터 검토 필요"
            return r
        r["note"] = ("공식 구독 character_count 기준 · "
                     + str(usage) + "/" + str(maximum)
                     + (" · 과거 기록" if not r["fresh"] else ""))
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, OverflowError):
        pass
    return r



def credential_file():
    return Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()))/"TAKY"/"USAGE_BOARD"/"elevenlabs.credential.dpapi"


def dpapi_transform(raw, protect=True):
    """Windows user-bound DPAPI. Never use machine scope or persist plaintext keys."""
    import ctypes
    from ctypes import wintypes
    if os.name != "nt":
        raise OSError("Windows DPAPI required")
    class Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]
    source = ctypes.create_string_buffer(raw)
    src = Blob(len(raw), ctypes.cast(source, ctypes.POINTER(ctypes.c_char)))
    output = Blob()
    crypto = ctypes.windll.crypt32
    if protect:
        fn = crypto.CryptProtectData
        fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_wchar_p, ctypes.POINTER(Blob),
                       ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        args = [ctypes.byref(src), "TAKY ElevenLabs read-only", None, None, None, 1, ctypes.byref(output)]
    else:
        fn = crypto.CryptUnprotectData
        fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob),
                       ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        args = [ctypes.byref(src), None, None, None, None, 1, ctypes.byref(output)]
    fn.restype = wintypes.BOOL
    if not fn(*args):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output.pbData)


def save_elevenlabs_key(key):
    path = credential_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = dpapi_transform(key.encode("ascii"))
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(encoded)
    os.replace(tmp, path)


def load_elevenlabs_key():
    try:
        return dpapi_transform(credential_file().read_bytes(), protect=False).decode("ascii")
    except (OSError, ValueError, UnicodeError):
        return None


def elevenlabs_key_installed():
    return bool(load_elevenlabs_key())


def delete_elevenlabs_connection():
    root = credential_file().parent
    for path in (credential_file(), root/"elevenlabs_subscription.json"):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def refresh_elevenlabs_periodically(server):
    # Existing credential only. No API request at all before explicit local setup.
    while not server.shutdown_event.is_set():
        key = load_elevenlabs_key()
        if key:
            sync_elevenlabs(key=key)
            server.last = 0
        if server.shutdown_event.wait(1800):
            break


def sync_elevenlabs(key=None):
    """Official GET subscription only; never call TTS or reveal API keys."""
    from urllib.request import Request, urlopen
    key = (key or os.environ.get("ELEVENLABS_API_KEY", "")).strip()
    if not key:
        print("ELEVENLABS_NOT_CONNECTED: no key configured; no API request was sent.")
        return False
    request = Request("https://api.elevenlabs.io/v1/user/subscription",
                      headers={"xi-api-key": key, "Accept": "application/json"}, method="GET")
    try:
        with urlopen(request, timeout=8) as response:
            data = json.load(response)
        if not isinstance(data, dict):
            return False
        n, mx = int(data["character_count"]), int(data["character_limit"])
        if n < 0 or mx <= 0:
            return False
        clean = {"source": "elevenlabs_subscription_endpoint",
                 "capturedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
                 "character_count": n, "character_limit": mx,
                 "tier": str(data.get("tier", ""))[:40],
                 "billing_period": str(data.get("billing_period", ""))[:40],
                 "character_refresh_period": str(data.get("character_refresh_period", ""))[:40],
                 "next_character_count_reset_unix": data.get("next_character_count_reset_unix")}
        directory = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()))/"TAKY"/"USAGE_BOARD"
        directory.mkdir(parents=True, exist_ok=True)
        output = directory/"elevenlabs_subscription.json"
        output.write_text(json.dumps(clean, ensure_ascii=False), encoding="utf-8")
        try:
            os.chmod(output, 0o600)
        except OSError:
            pass
        print("ELEVENLABS_SUBSCRIPTION_SNAPSHOT_OK (read-only, no audio request)")
        return True
    except Exception as err:
        print("ELEVENLABS_SUBSCRIPTION_SNAPSHOT_UNAVAILABLE: "+type(err).__name__)
        return False


def antigravity(now=None):
    """Display sanitized Antigravity model-pool quota, independent of IDE."""
    try:
        from TAKY_ANTIGRAVITY_USAGE import display
        return display(now=now)
    except (ImportError,OSError,ValueError,TypeError):
        return entry("Antigravity","Antigravity 모델 풀 사용량 미확인")


def antigravity_auto_worker(server):
    """Low frequency quota metadata refresh; no inference and no account secrets on disk."""
    try:
        from TAKY_ANTIGRAVITY_USAGE import collect
    except ImportError:
        return
    while not server.shutdown_event.is_set():
        # Background monitoring must NEVER launch an IDE/CLI login-repair process.
        # Expired credentials are reported as unavailable until explicit user repair.
        if collect()=="OK":
            server.last=0
        server.shutdown_event.wait(60)


def snapshot(now=None):
    now=time.time() if now is None else now
    return {"schema":"TAKY_USAGE_READ_ONLY_V1","checkedAt":iso(now),
            "percentMeans":"consumed","providers":[
                claude(now=now),codex(now=now),
                entry("ChatGPT 웹/앱","구독 한도 및 대화 컨텍스트 공식 수치 미제공, Codex와 별개"),
                elevenlabs(now=now),
                netlify(),
                antigravity(now=now),
                desktop_commander()]}

def route_dry_run(usage, kind="code", size="medium", planned_calls=1):
    """Zero-inference planning from observed quota. Ranges are scenario budgets, NOT measured forecasts."""
    if kind not in ("code", "implementation", "review", "validation") or size not in ("small", "medium", "large"):
        raise ValueError("unsupported task class")
    if not isinstance(planned_calls, int) or not 1 <= planned_calls <= 4:
        raise ValueError("planned_calls must be 1..4")
    # Assumed upper/lower percentage-point costs per bounded invocation.
    # These are conservative WHAT-IF envelopes until task receipts provide calibration.
    envelopes = {"small": ((1, 4), (0.5, 2)),
                 "medium": ((3, 10), (1, 5)),
                 "large": ((8, 25), (3, 12))}
    (five_min, five_max), (week_min, week_max) = envelopes[size]
    estimated = {"fiveHour": [five_min * planned_calls, five_max * planned_calls],
                 "week": [week_min * planned_calls, week_max * planned_calls]}
    result = {"schema": "TAKY_USAGE_ROUTING_DRYRUN_V1", "dryRun": True, "inferenceCalls": 0,
              "paidApiCalls": 0, "checkedAt": usage.get("checkedAt"),
              "kind": kind, "size": size, "plannedCalls": planned_calls,
              "forecastType": "UNVALIDATED_SCENARIO_ENVELOPE_NOT_EMPIRICAL_PREDICTION",
              "assumedAdditionalPercentagePoints": estimated, "reservePercentagePoints": 15,
              "candidates": [], "recommended": None, "status": "HOLD"}
    if kind == "validation":
        result.update(recommended="LOCAL_DETERMINISTIC", status="READY_LOCAL_ONLY")
        return result
    providers = {p.get("name"): p for p in usage.get("providers", [])}
    # TAKY: Claude executes code by default; Codex is independent verifier/fallback.
    # An unsafe/stale/exhausted primary is never forced through the quota gate.
    order = ("Claude Code", "Codex CLI") if kind in ("code", "implementation") else ("Codex CLI", "Claude Code")
    for provider_name in order:
        provider = providers.get(provider_name) or {}
        before = {}
        after = {}
        fresh = provider.get("fresh") is True
        for period in ("fiveHour", "week"):
            meter_row = provider.get(period) or {}
            value = pct(meter_row.get("usedPercent"))
            before[period] = value
            after[period] = ([round(value + estimated[period][0], 1),
                              round(value + estimated[period][1], 1)]
                             if value is not None else None)
        known = all(before[p] is not None for p in ("fiveHour", "week"))
        within = known and all(after[p][1] + 15 <= 100 for p in ("fiveHour", "week"))
        risk = "STALE" if not fresh else "UNKNOWN" if not known else "SAFE" if within else "BUDGET_RISK"
        missing_windows = [period for period in ("fiveHour", "week") if before[period] is None]
        gate_reason = ("QUOTA_OBSERVATION_STALE" if not fresh else
                       "QUOTA_WINDOW_UNOBSERVED" if missing_windows else
                       "QUOTA_WITHIN_FORECAST_AND_RESERVE" if within else
                       "QUOTA_FORECAST_EXCEEDS_RESERVE")
        result["candidates"].append({"provider": provider_name, "fresh": fresh,
                                     "observedAt": provider.get("observedAt"),
                                     "beforeUsedPercent": before,
                                     "afterUsedPercentRange": after,
                                     "missingQuotaWindows": missing_windows,
                                     "missingQuotaReasons": {
                                         period: (provider.get("quotaWindowStatus") or {}).get(
                                             period, "NO_VALID_OBSERVATION")
                                         for period in missing_windows},
                                     "quotaGateReason": gate_reason,
                                     "risk": risk})
    good = [p for p in result["candidates"] if p["risk"] == "SAFE"]
    if good:
        result["recommended"] = good[0]["provider"]
        result["status"] = "READY_FOR_SEPARATE_AUTHORIZATION"
    else:
        result["status"] = "HOLD_REFRESH_OR_REDUCE_SCOPE"
    return result


def governed_route_dry_run(usage, kind="code", size="medium", planned_calls=1,
                           repo=r"D:\Git PWA\TAKY", health_reader=None):
    """Read-only combined quota+signed-governance gate. No preflight or model."""
    route = route_dry_run(usage, kind, size, planned_calls)
    route["schema"] = "TAKY_GOVERNED_USAGE_ROUTING_DRYRUN_V1"
    if kind == "validation":
        return route
    if health_reader is None:
        from TAKY_GOVERNED_ROUTE_HEALTH import signed_health as health_reader
    eligible = []
    for candidate in route["candidates"]:
        provider = "Codex" if candidate["provider"] == "Codex CLI" else "Claude"
        check = health_reader(provider, repo)
        candidate["governance"] = {
            "status": check.get("status", "HOLD"),
            "reason": check.get("reason"),
            "signedStateIntegrity": check.get("signedStateIntegrity"),
        }
        if (candidate["risk"] == "SAFE" and
            check.get("status") == "READY_FOR_EXISTING_COST_AND_APPROVAL_GATES"):
            eligible.append(candidate)
    route["recommended"] = eligible[0]["provider"] if eligible else None
    route["status"] = ("READY_FOR_SEPARATE_AUTHORIZATION" if eligible
                       else "HOLD_NO_QUOTA_AND_GOVERNANCE_SAFE_ROUTE")
    return route


HTML = Path(__file__).with_suffix(".html").read_text(encoding="utf-8")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Match the URL path only; UI links such as /?elevenlabs=1 are valid.
        route = self.path.partition("?")[0]
        if route not in ("/","/api/usage","/api/local-access","/api/elevenlabs/status","/api/netlify/status"):return self.send_error(404)
        # Only the workstation itself is trusted (including its own LAN address).
        is_local=self.client_address[0] in ("127.0.0.1","::1",self.server.local_ipv4)
        if route in ("/api/local-access","/api/elevenlabs/status","/api/netlify/status") and not is_local:return self.send_error(403)
        if route=="/api/usage" and self.server.token and not is_local:
            if not secrets.compare_digest(self.headers.get("X-TAKY-Token",""),self.server.token):
                return self.send_error(401)
        if route=="/api/local-access":
            output={"mobileUrl":self.server.mobile_url,"accessKey":self.server.token}
        elif route=="/api/elevenlabs/status":
            output={"connected":elevenlabs_key_installed(),"provider":"ElevenLabs"}
        elif route=="/api/netlify/status":
            output={"teams":[{"slug":slug,"connected":netlify_connected(slug)}
                    for slug in NETLIFY_ALLOWED_TEAMS]}
        else:
            output=self.server.cached()
        body=(HTML if route=="/" else json.dumps(output,ensure_ascii=False)).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8" if route=="/" else "application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Referrer-Policy","no-referrer")
        self.send_header("Content-Security-Policy","default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_POST(self):
        # Credential mutations are strictly loopback-only, not reachable from Wi-Fi clients.
        # Reject cross-site and non-JSON forms before parsing any submitted secret.
        if self.path not in ("/api/elevenlabs/connect", "/api/elevenlabs/disconnect",
                             "/api/netlify/connect", "/api/netlify/disconnect"):
            return self.send_error(404)
        if self.client_address[0] not in ("127.0.0.1", "::1"):
            return self.send_error(403)
        expected = "http://127.0.0.1:" + str(self.server.server_port)
        if self.headers.get("Origin") != expected:
            return self.send_error(403)
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            return self.send_error(415)
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.send_error(400)
        if size < 2 or size > 2048:
            return self.send_error(413)
        try:
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError("JSON object required")
        except (UnicodeError, ValueError):
            return self.send_error(400)
        if self.path.startswith("/api/netlify/"):
            slug=payload.get("slug")
            if slug not in NETLIFY_ALLOWED_TEAMS:
                return self.send_json_result(400,{"connected":False,"status":"UNKNOWN_TEAM"})
            if self.path.endswith("/disconnect"):
                netlify_unlink(slug)
                self.server.last=0
                return self.send_json_result(200,{"connected":False,"status":"DISCONNECTED"})
            token=payload.get("apiKey")
            if (not isinstance(token,str) or not 16<=len(token)<=512
                    or not token.isascii() or any(ch.isspace() for ch in token)):
                return self.send_json_result(400,{"connected":False,"status":"INVALID_TOKEN_FORMAT"})
            # Validate a single read-only authenticated account GET first.
            try:
                from TAKY_NETLIFY_USAGE import fetch
                observed=fetch(slug,token)
            except Exception as exc:
                from urllib.error import HTTPError
                code="NOT_AUTHORIZED" if isinstance(exc,HTTPError) and exc.code in (401,403) else "ACCOUNT_READ_FAILED"
                return self.send_json_result(422,{"connected":False,"status":code})
            try:
                netlify_store_key(slug,token)
                save_small_json(netlify_snapshot_path(slug),observed)
                save_small_json(netlify_poll_path(slug),
                    {"nextAttempt":time.time()+3600,"lastStatus":"OK"})
            except (OSError,ValueError):
                netlify_unlink(slug)
                return self.send_json_result(500,{"connected":False,"status":"CREDENTIAL_STORAGE_FAILED"})
            self.server.last=0
            return self.send_json_result(200,{"connected":True,"status":"CONNECTED",
                "balanceSource":observed.get("balanceSource","NOT_PROVIDED")})
        if self.path.endswith("/disconnect"):
            delete_elevenlabs_connection()
            self.server.last = 0
            return self.send_json_result(200, {"connected":False,"status":"DISCONNECTED"})
        key = payload.get("apiKey")
        if not isinstance(key,str) or not 16 <= len(key) <= 512:
            return self.send_json_result(400, {"connected":False,"status":"INVALID_KEY_FORMAT"})
        try:
            key.encode("ascii")
            if any(c.isspace() or ord(c) < 33 or ord(c) > 126 for c in key):
                raise ValueError("bad key characters")
        except (ValueError,UnicodeError):
            return self.send_json_result(400, {"connected":False,"status":"INVALID_KEY_FORMAT"})
        # Only a successful read-only subscription GET authorizes storing the credential.
        if not sync_elevenlabs(key=key):
            return self.send_json_result(422, {"connected":False,"status":"SUBSCRIPTION_READ_FAILED"})
        try:
            save_elevenlabs_key(key)
        except (OSError,ValueError):
            return self.send_json_result(500, {"connected":False,"status":"CREDENTIAL_STORAGE_FAILED"})
        self.server.last = 0
        self.server.elevenlabs_last_sync=time.time()
        return self.send_json_result(200, {"connected":True,"status":"CONNECTED"})

    def send_json_result(self, status, result):
        encoded = json.dumps(result,ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Referrer-Policy","no-referrer")
        self.send_header("Content-Length",str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self,*args):pass

class Server(ThreadingHTTPServer):
    def __init__(self,address,token):
        super().__init__(address,Handler)
        self.token=token
        self.mobile_url=""
        self.local_ipv4="127.0.0.1"
        import threading
        self.elevenlabs_refresh_lock=threading.Lock()
        self.cache_lock=threading.Lock()
        self.cache_seconds=120  # Provider quota snapshots update far less often.
        # Preserve the last successful collection time across monitor restarts.
        # A stale snapshot triggers a refresh even when nobody opens the UI.
        self.elevenlabs_last_sync=0
        try:
            root=credential_file().parent
            info=json.loads((root/"elevenlabs_subscription.json").read_text(encoding="utf-8-sig"))
            if info.get("source")=="elevenlabs_subscription_endpoint":
                self.elevenlabs_last_sync=event_epoch(info.get("capturedAt")) or 0
        except (OSError,ValueError,TypeError,AttributeError):
            pass
        self.shutdown_event=threading.Event()
        self.last=0
        self.state=None
    def _refresh_subscription(self):
        try:
            key=load_elevenlabs_key()
            if key:
                success=sync_elevenlabs(key=key)
                # Success: 30-minute cadence; errors: wait 2 hours before retry.
                self.elevenlabs_last_sync=time.time() if success else time.time()+5400
                if success:
                    self.last=0
        finally:
            self.elevenlabs_refresh_lock.release()
    def _maybe_refresh_subscription(self):
        # Never request usage without a credential previously approved via the UI.
        if time.time()-self.elevenlabs_last_sync >= 1800 and elevenlabs_key_installed():
            if self.elevenlabs_refresh_lock.acquire(blocking=False):
                self.elevenlabs_last_sync=time.time()
                import threading
                threading.Thread(target=self._refresh_subscription,daemon=True,
                                 name="taky-elevenlabs-refresh").start()
    def cached(self):
        self._maybe_refresh_subscription()
        # One snapshot across concurrent browser tabs/mobile clients. Avoid
        # duplicated disk scans and transient thread/CPU spikes.
        if self.state is not None and time.time()-self.last<self.cache_seconds:
            return self.state
        with self.cache_lock:
            if self.state is None or time.time()-self.last>=self.cache_seconds:
                self.state=snapshot()
                self.last=time.time()
            return self.state

def elevenlabs_auto_worker(server):
    """Scheduled read-only subscription refresh, independent of browser visits."""
    server._maybe_refresh_subscription()
    while not server.shutdown_event.wait(60):
        server._maybe_refresh_subscription()


def selftest():
    import unittest
    class Tests(unittest.TestCase):
        def test_dashboard_concurrent_requests_share_one_snapshot(self):
            from concurrent.futures import ThreadPoolExecutor
            from unittest.mock import patch
            server=Server(("127.0.0.1",0),token="")
            try:
                output={"providers":[]}
                with patch.object(server,"_maybe_refresh_subscription"), \
                     patch(__name__+".snapshot",return_value=output) as scan:
                    with ThreadPoolExecutor(max_workers=8) as workers:
                        observations=list(workers.map(lambda _: server.cached(), range(16)))
                    self.assertTrue(all(x is output for x in observations))
                    scan.assert_called_once()
            finally:
                server.server_close()
        def test_antigravity_background_never_runs_login_repair(self):
            import threading
            from unittest.mock import patch
            from types import SimpleNamespace
            event=threading.Event()
            state=SimpleNamespace(shutdown_event=event,last=0)
            def once(**kwargs):
                self.assertNotIn("repair",kwargs)
                event.set()
                return "OK"
            with patch("TAKY_ANTIGRAVITY_USAGE.collect",side_effect=once) as collect:
                antigravity_auto_worker(state)
            collect.assert_called_once()
        def test_route_dry_run_fallback_and_no_inference(self):
            def p(name, five, week, fresh=True):
                return {"name": name, "fresh": fresh, "observedAt": "fixture",
                        "fiveHour": {"usedPercent": five}, "week": {"usedPercent": week}}
            usage = {"checkedAt": "fixture", "providers": [
                p("Claude Code", 94, 97), p("Codex CLI", 12, 25)]}
            plan = route_dry_run(usage, "review", "medium")
            self.assertEqual(plan["recommended"], "Codex CLI")
            self.assertEqual(plan["inferenceCalls"], 0)
            self.assertEqual(plan["paidApiCalls"], 0)
            self.assertEqual(plan["forecastType"], "UNVALIDATED_SCENARIO_ENVELOPE_NOT_EMPIRICAL_PREDICTION")
        def test_route_dry_run_taky_role_preference_and_fallback(self):
            def p(name, five, week, fresh=True):
                return {"name": name, "fresh": fresh, "observedAt": "fixture",
                        "fiveHour": {"usedPercent": five}, "week": {"usedPercent": week}}
            observed = {"providers": [p("Claude Code", 6, 4), p("Codex CLI", 10, 25)]}
            self.assertEqual(route_dry_run(observed, "code")["recommended"], "Claude Code")
            self.assertEqual(route_dry_run(observed, "review")["recommended"], "Codex CLI")
            blocked = {"providers": [p("Claude Code", 96, 97), p("Codex CLI", 10, 25)]}
            decision = route_dry_run(blocked, "code")
            self.assertEqual(decision["recommended"], "Codex CLI")
            self.assertEqual(decision["paidApiCalls"], 0)
            self.assertEqual(decision["inferenceCalls"], 0)
        def test_route_dry_run_stale_or_missing_holds(self):
            usage = {"providers": [
                {"name": "Codex CLI", "fresh": False,
                 "fiveHour": {"usedPercent": 2}, "week": {"usedPercent": 5}},
                {"name": "Claude Code", "fresh": True,
                 "fiveHour": {"usedPercent": 3}, "week": {"usedPercent": None}}]}
            plan = route_dry_run(usage, "code", "medium")
            self.assertEqual(plan["status"], "HOLD_REFRESH_OR_REDUCE_SCOPE")
            self.assertIsNone(plan["recommended"])
        def test_route_dry_run_local_and_budget_reserve(self):
            usage = {"providers": [{"name": "Codex CLI", "fresh": True,
                "fiveHour": {"usedPercent": 65}, "week": {"usedPercent": 60}},
                {"name": "Claude Code", "fresh": True,
                "fiveHour": {"usedPercent": 10}, "week": {"usedPercent": 12}}]}
            self.assertEqual(route_dry_run(usage, "code", "large")["recommended"], "Claude Code")
            self.assertEqual(route_dry_run(usage, "validation")["recommended"], "LOCAL_DETERMINISTIC")
        def test_missing_not_zero(self):
            self.assertIsNone(pct(None))
            self.assertIsNone(pct(-1))
            self.assertEqual(pct(0),0)
        def test_known_claude(self):
            with tempfile.TemporaryDirectory() as tmp:
                file=Path(tmp)/"sample.json"
                file.write_text(json.dumps({"rate_limits":{"five_hour":{"used_percentage":22},"seven_day":{"used_percentage":73}},"context_window":{"used_percentage":49}}))
                r=claude(file)
                self.assertEqual(r["fiveHour"]["usedPercent"],22)
                self.assertEqual(r["week"]["usedPercent"],73)
                self.assertEqual(r["context"]["usedPercent"],49)
                self.assertIsNone(r["month"]["usedPercent"])
        def test_claude_native_usage_cache_stale(self):
            with tempfile.TemporaryDirectory() as tmp:
                now = time.time()
                src = Path(tmp) / "status.json"
                src.write_text(json.dumps({"context_window":{"used_percentage":12}}))
                cache = Path(tmp) / ".claude.json"
                fetched = now - 8*3600
                cache.write_text(json.dumps({"cachedUsageUtilization":{
                    "fetchedAtMs":int(fetched*1000),
                    "utilization":{
                        "five_hour":{"utilization":0,"resets_at":None},
                        "seven_day":{"utilization":0,"resets_at":dt.datetime.fromtimestamp(now+86400,dt.timezone.utc).isoformat()}
                    }
                }}))
                r=claude(path=src,now=now,usage_cache=cache)
                self.assertEqual(r["fiveHour"]["usedPercent"],0)
                self.assertEqual(r["week"]["usedPercent"],0)
                self.assertFalse(r["fresh"])
                self.assertEqual(r["rateSource"],"claude_usage_cache")
                self.assertIn("480분 전",r["note"])
        def test_claude_statusline_newer_than_usage_cache(self):
            with tempfile.TemporaryDirectory() as tmp:
                now=time.time()
                src=Path(tmp)/"live.json"
                src.write_text(json.dumps({"rate_limits":{
                    "five_hour":{"used_percentage":47},
                    "seven_day":{"used_percentage":66}}}))
                cache=Path(tmp)/".claude.json"
                cache.write_text(json.dumps({"cachedUsageUtilization":{
                    "fetchedAtMs":int((now-1800)*1000),
                    "utilization":{"five_hour":{"utilization":15},"seven_day":{"utilization":24}}
                }}))
                r=claude(path=src,now=now,usage_cache=cache)
                self.assertEqual(r["fiveHour"]["usedPercent"],47)
                self.assertEqual(r["week"]["usedPercent"],66)
                self.assertEqual(r["rateSource"],"claude_statusline")
        def test_claude_expired_usage_window(self):
            with tempfile.TemporaryDirectory() as tmp:
                now=time.time()
                src=Path(tmp)/"last.json"
                src.write_text("{}")
                cache=Path(tmp)/".claude.json"
                cache.write_text(json.dumps({"cachedUsageUtilization":{
                    "fetchedAtMs":int((now-600)*1000),
                    "utilization":{
                        "five_hour":{"utilization":99,"resets_at":dt.datetime.fromtimestamp(now-30,dt.timezone.utc).isoformat()},
                        "seven_day":{"utilization":25,"resets_at":dt.datetime.fromtimestamp(now+3600,dt.timezone.utc).isoformat()}
                    }
                }}))
                r=claude(path=src,now=now,usage_cache=cache)
                self.assertIsNone(r["fiveHour"]["usedPercent"])
                self.assertEqual(r["week"]["usedPercent"],25)
        def test_claude_partial_latest_snapshot_explains_hold(self):
            with tempfile.TemporaryDirectory() as tmp:
                now = time.time()
                src = Path(tmp)/"status.json"
                src.write_text("{}")
                cache = Path(tmp)/"cache.json"
                reset = dt.datetime.fromtimestamp(now+3600,dt.timezone.utc).isoformat()
                cache.write_text(json.dumps({"cachedUsageUtilization":{
                    "fetchedAtMs":int((now-90)*1000),
                    "utilization":{"five_hour":{"utilization":45,"resets_at":reset},
                                   "seven_day":{"utilization":8,"resets_at":reset}}}}))
                auto = Path(tmp)/"oauth.json"
                auto.write_text(json.dumps({"source":"claude_authenticated_usage",
                    "capturedAt":dt.datetime.fromtimestamp(now-10,dt.timezone.utc).isoformat(),
                    "seven_day":{"utilization":5,"resets_at":reset}}))
                provider = claude(path=src,now=now,usage_cache=cache,oauth_snapshot=auto)
                self.assertIsNone(provider["fiveHour"]["usedPercent"])
                self.assertEqual(provider["week"]["usedPercent"],5)
                self.assertTrue(provider["fresh"])
                self.assertEqual(provider["quotaWindowStatus"]["fiveHour"],
                                 "WINDOW_NOT_REPORTED")
                plan = route_dry_run({"providers":[provider]},"review","small")
                selected = next(x for x in plan["candidates"] if x["provider"]=="Claude Code")
                self.assertEqual(selected["risk"],"UNKNOWN")
                self.assertEqual(selected["missingQuotaReasons"]["fiveHour"],
                                 "WINDOW_NOT_REPORTED")
                self.assertIsNone(plan["recommended"])

        def test_claude_expired_reset_classified_not_zeroed(self):
            with tempfile.TemporaryDirectory() as tmp:
                now=time.time()
                reset_old=dt.datetime.fromtimestamp(now-30,dt.timezone.utc).isoformat()
                reset_future=dt.datetime.fromtimestamp(now+3600,dt.timezone.utc).isoformat()
                src=Path(tmp)/"status.json"
                src.write_text("{}")
                cache=Path(tmp)/"cache.json"
                cache.write_text("{}")
                auto=Path(tmp)/"oauth.json"
                auto.write_text(json.dumps({"source":"claude_authenticated_usage",
                    "capturedAt":dt.datetime.fromtimestamp(now-10,dt.timezone.utc).isoformat(),
                    "five_hour":{"utilization":74,"resets_at":reset_old},
                    "seven_day":{"utilization":3,"resets_at":reset_future}}))
                provider=claude(path=src,now=now,usage_cache=cache,oauth_snapshot=auto)
                self.assertIsNone(provider["fiveHour"]["usedPercent"])
                self.assertEqual(provider["quotaWindowStatus"]["fiveHour"],
                                 "RESET_TIME_ALREADY_PASSED")

        def test_claude_background_snapshot_wins(self):
            with tempfile.TemporaryDirectory() as tmp:
                now = time.time()
                status = Path(tmp)/"status.json"
                status.write_text(json.dumps({"context_window":{"used_percentage":18}}))
                cache = Path(tmp)/".claude.json"
                cache.write_text(json.dumps({"cachedUsageUtilization":{
                    "fetchedAtMs":int((now-6000)*1000),
                    "utilization":{"five_hour":{"utilization":0},"seven_day":{"utilization":0}}
                }}))
                auto = Path(tmp)/"snapshot.json"
                auto.write_text(json.dumps({"source":"claude_authenticated_usage",
                    "capturedAt":dt.datetime.fromtimestamp(now-40,dt.timezone.utc).isoformat(),
                    "five_hour":{"utilization":39,"resets_at":dt.datetime.fromtimestamp(now+3600,dt.timezone.utc).isoformat()},
                    "seven_day":{"utilization":3,"resets_at":dt.datetime.fromtimestamp(now+86400,dt.timezone.utc).isoformat()}}))
                r = claude(path=status,usage_cache=cache,oauth_snapshot=auto,now=now)
                self.assertEqual(r["fiveHour"]["usedPercent"],39)
                self.assertEqual(r["week"]["usedPercent"],3)
                self.assertEqual(r["rateSource"],"claude_authenticated_usage")
                self.assertTrue(r["fresh"])
                self.assertEqual(r["context"]["usedPercent"],18)
        def test_claude_background_refresh_and_rate_gate(self):
            import io
            with tempfile.TemporaryDirectory() as tmp:
                now=time.time()
                cred=Path(tmp)/"creds.json"
                token="fixture_only_fake_token_"+"z"*30
                cred.write_text(json.dumps({"claudeAiOauth":{
                    "accessToken":token,"expiresAt":int((now+3600)*1000)}}))
                snap=Path(tmp)/"snapshot.json"
                poll=Path(tmp)/"poll.json"
                calls=[]
                class Response:
                    def __enter__(self):return self
                    def __exit__(self,*args):return False
                    def read(self,max_bytes):return json.dumps({
                        "five_hour":{"utilization":39,"resets_at":None},
                        "seven_day":{"utilization":3,"resets_at":None}}).encode()
                def fetch(request,timeout):
                    self.assertTrue(request.full_url.startswith("https://api.anthropic.com/"))
                    calls.append(request)
                    return Response()
                result=refresh_claude_usage(now=now,credential_path=cred,snapshot_path=snap,
                        state_path=poll,fetcher=fetch)
                self.assertEqual(result,"OK")
                self.assertEqual(json.loads(snap.read_text())["five_hour"]["utilization"],39)
                self.assertNotIn(token,snap.read_text())
                self.assertNotIn(token,poll.read_text())
                self.assertEqual(refresh_claude_usage(now=now+60,credential_path=cred,
                    snapshot_path=snap,state_path=poll,fetcher=fetch),"COOLDOWN")
                self.assertEqual(len(calls),1)
        def test_claude_background_429_backoff(self):
            import urllib.error
            with tempfile.TemporaryDirectory() as tmp:
                now=time.time()
                cred=Path(tmp)/"creds.json"
                cred.write_text(json.dumps({"claudeAiOauth":{
                    "accessToken":"fixture_only_fake_token_"+"y"*30,
                    "expiresAt":int((now+3600)*1000)}}))
                state=Path(tmp)/"poll.json"
                def throttle(request,timeout):
                    raise urllib.error.HTTPError(request.full_url,429,"rate limited",{},None)
                result=refresh_claude_usage(now=now,credential_path=cred,
                        snapshot_path=Path(tmp)/"s.json",state_path=state,fetcher=throttle)
                self.assertEqual(result,"HTTP_429")
                self.assertGreaterEqual(json.loads(state.read_text())["nextAttempt"]-now,7200)
        def test_antigravity_snapshot_present_or_unknown(self):
            observed=antigravity(now=time.time())
            self.assertEqual(observed["name"],"Antigravity")
            self.assertIn("geminiPool",observed)
            self.assertIn("thirdPartyPool",observed)
            # Real values can be absent when agy is logged out.
            for key in ("geminiPool","thirdPartyPool"):
                if isinstance(observed[key],dict):
                    self.assertGreaterEqual(observed[key]["remainingPercent"],0)
                    self.assertLessEqual(observed[key]["remainingPercent"],100)
        def test_codex_official_appserver_quota_and_cooldown(self):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                now=time.time()
                snap=root/"codex_usage.json"
                state=root/"codex_poll.json"
                calls=[]
                def read():
                    calls.append(1)
                    return {"rateLimitsByLimitId":{"codex":{
                        "planType":"plus",
                        "primary":{"usedPercent":6,"windowDurationMins":300,"resetsAt":now+3600},
                        "secondary":{"usedPercent":24,"windowDurationMins":10080,"resetsAt":now+86400}
                    }}}
                result=refresh_codex_account(now=now,snapshot_path=snap,
                    state_path=state,fetcher=read)
                self.assertEqual(result,"OK")
                stored=json.loads(snap.read_text())
                self.assertEqual(stored["windows"]["fiveHour"]["used_percent"],6)
                self.assertEqual(stored["windows"]["week"]["used_percent"],24)
                self.assertEqual(refresh_codex_account(now=now+60,
                    snapshot_path=snap,state_path=state,fetcher=read),"COOLDOWN")
                self.assertEqual(len(calls),1)
                merged=codex(root=root,now=now+70,usage_snapshot=snap)
                self.assertEqual(merged["fiveHour"]["usedPercent"],6)
                self.assertEqual(merged["week"]["usedPercent"],24)
                self.assertTrue(merged["fresh"])
                self.assertEqual(merged["rateSource"],"codex_appserver_rate_limits")
        def test_codex_official_appserver_week_only(self):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                now=time.time()
                def read():
                    return {"rateLimits":{"planType":"plus",
                        "primary":{"usedPercent":9,"windowDurationMins":10080,"resetsAt":now+90000},
                        "secondary":None}}
                outcome=refresh_codex_account(now=now,snapshot_path=root/"usage.json",
                    state_path=root/"state.json",fetcher=read)
                self.assertEqual(outcome,"OK")
                actual=codex(root=root,now=now+10,usage_snapshot=root/"usage.json")
                self.assertIsNone(actual["fiveHour"]["usedPercent"])
                self.assertEqual(actual["week"]["usedPercent"],9)
        def test_codex(self):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                d=dt.datetime.now().date()
                folder=root/"sessions"/d.strftime("%Y")/d.strftime("%m")/d.strftime("%d")
                folder.mkdir(parents=True)
                (folder/"s.jsonl").write_text(json.dumps({"payload":{"rate_limits":{"primary":{"window_minutes":300,"used_percent":31},"secondary":{"window_minutes":10080,"used_percent":63}}}}))
                r=codex(root)
                self.assertEqual(r["fiveHour"]["usedPercent"],31)
                self.assertEqual(r["week"]["usedPercent"],63)
        def test_expired_is_not_fake_zero(self):
            now=time.time()
            a=limit_meter(89,now-20,now)
            b=limit_meter(45,now+1200,now)
            self.assertIsNone(a["usedPercent"])
            self.assertTrue(a["expired"])
            self.assertEqual(b["usedPercent"],45)
        def test_codex_event_time_and_context(self):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                d=dt.datetime.now().date()
                folder=root/"sessions"/d.strftime("%Y")/d.strftime("%m")/d.strftime("%d")
                folder.mkdir(parents=True)
                now=time.time()
                old={"timestamp":dt.datetime.fromtimestamp(now-7200,dt.timezone.utc).isoformat(),
                    "payload":{"rate_limits":{"primary":{"window_minutes":300,"used_percent":80}}}}
                new={"timestamp":dt.datetime.fromtimestamp(now-40,dt.timezone.utc).isoformat(),
                    "payload":{"rate_limits":{"primary":{"window_minutes":300,"used_percent":33,"resets_at":now+600},
                                               "secondary":{"window_minutes":10080,"used_percent":11}},
                               "info":{"last_token_usage":{"total_tokens":12000},"model_context_window":200000}}}
                (folder/"a.jsonl").write_text(json.dumps(old))
                (folder/"b.jsonl").write_text(json.dumps(new))
                r=codex(root,now)
                self.assertEqual(r["fiveHour"]["usedPercent"],33)
                self.assertEqual(r["week"]["usedPercent"],11)
                self.assertEqual(r["context"]["usedPercent"],6)
                self.assertTrue(r["context"]["estimated"])
        def test_elevenlabs_monthly_snapshot_and_expiry(self):
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/"elevenlabs_subscription.json"
                now=time.time()
                sample={"source":"elevenlabs_subscription_endpoint",
                        "capturedAt":dt.datetime.fromtimestamp(now-10,dt.timezone.utc).isoformat(),
                        "tier":"trial", "billing_period":"monthly_period",
                        "character_refresh_period":"monthly_period",
                        "character_count":2800, "character_limit":10000,
                        "next_character_count_reset_unix":now+86400}
                p.write_text(json.dumps(sample))
                r=elevenlabs(p,now)
                self.assertEqual(r["month"]["usedPercent"],28)
                self.assertEqual(r["month"]["used"],2800)
                self.assertEqual(r["month"]["remaining"],7200)
                self.assertEqual(r["month"]["limit"],10000)
                sample["next_character_count_reset_unix"]=now-100
                p.write_text(json.dumps(sample))
                expired=elevenlabs(p,now)
                self.assertIsNone(expired["month"]["usedPercent"])
        def test_subscription_refresh_without_browser_and_backoff(self):
            from unittest.mock import patch
            with tempfile.TemporaryDirectory() as tmp:
                fake_root=Path(tmp)
                with patch(__name__+".credential_file",return_value=fake_root/"key.dpapi"):
                    server=Server(("127.0.0.1",0),token="")
                try:
                    with patch(__name__+".elevenlabs_key_installed",return_value=True), \
                         patch(__name__+".load_elevenlabs_key",return_value="fake_local_fixture"), \
                         patch(__name__+".sync_elevenlabs",return_value=True) as read:
                        server.elevenlabs_last_sync=0
                        server._maybe_refresh_subscription()
                        for _ in range(100):
                            if not server.elevenlabs_refresh_lock.locked():break
                            time.sleep(0.01)
                        read.assert_called_once_with(key="fake_local_fixture")
                        server._maybe_refresh_subscription()
                        read.assert_called_once()
                    with patch(__name__+".elevenlabs_key_installed",return_value=True), \
                         patch(__name__+".load_elevenlabs_key",return_value="fake_local_fixture"), \
                         patch(__name__+".sync_elevenlabs",return_value=False) as failing:
                        server.elevenlabs_last_sync=0
                        server._maybe_refresh_subscription()
                        for _ in range(100):
                            if not server.elevenlabs_refresh_lock.locked():break
                            time.sleep(0.01)
                        failing.assert_called_once()
                        self.assertGreater(server.elevenlabs_last_sync-time.time(),5300)
                finally:
                    server.server_close()
        def test_non_monthly_elevenlabs_not_mislabelled(self):
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/"elevenlabs_subscription.json"
                now=time.time()
                p.write_text(json.dumps({"source":"elevenlabs_subscription_endpoint",
                     "capturedAt":dt.datetime.fromtimestamp(now-10,dt.timezone.utc).isoformat(),
                     "character_count":1, "character_limit":10,
                     "character_refresh_period":"annual_period"}))
                r=elevenlabs(p,now)
                self.assertIsNone(r["month"]["usedPercent"])
    return unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--test",action="store_true")
    parser.add_argument("--sync-elevenlabs", action="store_true", help="Explicit opt-in read-only subscription GET; never scheduled")
    parser.add_argument("--snapshot",action="store_true")
    parser.add_argument("--route-dry-run", action="store_true",
                        help="Plan executor and assumed usage envelope; never invoke a model")
    parser.add_argument("--governed-route-dry-run", action="store_true",
                        help="Combine quota and signed TAKY2 route health without an AI call")
    parser.add_argument("--repo", default=r"D:\Git PWA\TAKY")
    parser.add_argument("--audit-execution", action="store_true",
                        help="Audit existing execution receipts without generating model calls")
    parser.add_argument("--audit-efficiency", action="store_true",
                        help="Signed per-task token evidence, never infer savings or billing")
    parser.add_argument("--task-kind", choices=("code","implementation","review","validation"), default="code")
    parser.add_argument("--task-size", choices=("small","medium","large"), default="medium")
    parser.add_argument("--planned-calls", type=int, choices=range(1,5), default=1)
    parser.add_argument("--lan",action="store_true")
    parser.add_argument("--port",type=int,default=8765)
    a=parser.parse_args()
    if a.test:raise SystemExit(0 if selftest() else 1)
    if a.sync_elevenlabs:
        raise SystemExit(0 if sync_elevenlabs() else 2)
    if a.snapshot:
        print(json.dumps(snapshot(),ensure_ascii=False,indent=2))
        return
    if a.audit_execution:
        from TAKY_USAGE_RECEIPT_AUDIT import audit
        print(json.dumps(audit(),ensure_ascii=False,indent=2))
        return
    if a.audit_efficiency:
        from TAKY_USAGE_EFFICIENCY_AUDIT import audit_signed
        result=audit_signed()
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if result.get("runtimeIntegrity") != "PASS":
            raise SystemExit(2)
        return
    if a.governed_route_dry_run:
        print(json.dumps(governed_route_dry_run(snapshot(), a.task_kind, a.task_size,
                                               a.planned_calls, a.repo),ensure_ascii=False,indent=2))
        return
    if a.route_dry_run:
        print(json.dumps(route_dry_run(snapshot(), a.task_kind, a.task_size, a.planned_calls),
                         ensure_ascii=False, indent=2))
        return
    token=""
    if a.lan:
        local=Path(os.environ.get("LOCALAPPDATA",tempfile.gettempdir()))/"TAKY"/"USAGE_BOARD"
        local.mkdir(parents=True,exist_ok=True)
        keyfile=local/"access_key"
        if keyfile.exists():
            token=keyfile.read_text(encoding="ascii").strip()
        if len(token)<24:
            token=secrets.token_urlsafe(24)
            keyfile.write_text(token,encoding="ascii")
            try:os.chmod(keyfile,0o600)
            except OSError:pass
    bind="0.0.0.0" if a.lan else "127.0.0.1"
    s=Server((bind,a.port),token)
    if a.lan:
        import socket
        try:
            sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            sock.connect(("192.0.2.1",80))
            local_ip=sock.getsockname()[0]
            sock.close()
            s.local_ipv4=local_ip
            s.mobile_url="http://"+local_ip+":"+str(s.server_port)+"/"
        except OSError:
            pass
    print("TAKY usage board listening at http://127.0.0.1:"+str(s.server_port),flush=True)
    if s.mobile_url:print("Trusted Wi-Fi mobile URL: "+s.mobile_url,flush=True)
    if a.lan:
        print("LAN access enabled on trusted private Wi-Fi only (HTTP is not encrypted).",flush=True)
        print("Local one-time access key: "+token,flush=True)
    import threading
    auto = threading.Thread(target=claude_auto_worker,args=(s,),daemon=True,name="taky-claude-usage")
    auto.start()
    subscription = threading.Thread(target=elevenlabs_auto_worker,args=(s,),daemon=True,
                                    name="taky-elevenlabs-usage")
    subscription.start()
    codex_monitor=threading.Thread(target=codex_auto_worker,args=(s,),daemon=True,
                                    name="taky-codex-usage")
    codex_monitor.start()
    gravity_monitor=threading.Thread(target=antigravity_auto_worker,args=(s,),daemon=True,
                                      name="taky-antigravity-usage")
    gravity_monitor.start()
    netlify_monitor=threading.Thread(target=netlify_auto_worker,args=(s,),daemon=True,
                                    name="taky-netlify-account-usage")
    netlify_monitor.start()
    try:s.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        s.shutdown_event.set()
        s.server_close()

if __name__=="__main__":main()
