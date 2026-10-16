#!/usr/bin/env python3
"""Read-only Antigravity model-pool quota sampler for TAKY.

Uses the installed agy CLI's Windows credential, only requests model availability
metadata from Google's Code Assist backend. Never generates content, copies a
bearer token to disk, or writes to credential manager. Pool fraction != weekly
request quota. All persisted fields are sanitized aggregates.
"""
import ctypes
from ctypes import wintypes
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT=Path(os.environ.get("LOCALAPPDATA",tempfile.gettempdir()))/"TAKY"/"USAGE_BOARD"
SNAPSHOT=ROOT/"antigravity_model_pools.json"
STATE=ROOT/"antigravity_poll_state.json"
INTERVAL_SECONDS=1800
AGY_CLI=Path(os.environ.get("LOCALAPPDATA",""))/"agy"/"bin"/"agy.exe"
URL="https://cloudcode-pa.googleapis.com/v1internal:fetchAvailableModels"

class FileTime(ctypes.Structure):
    _fields_=[("dwLowDateTime",wintypes.DWORD),("dwHighDateTime",wintypes.DWORD)]

class Credential(ctypes.Structure):
    _fields_=[
        ("Flags",wintypes.DWORD),("Type",wintypes.DWORD),
        ("TargetName",ctypes.c_wchar_p),("Comment",ctypes.c_wchar_p),
        ("LastWritten",FileTime),("CredentialBlobSize",wintypes.DWORD),
        ("CredentialBlob",ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist",wintypes.DWORD),("AttributeCount",wintypes.DWORD),
        ("Attributes",ctypes.c_void_p),("TargetAlias",ctypes.c_wchar_p),
        ("UserName",ctypes.c_wchar_p),
    ]

def bearer_from_windows_keyring():
    if os.name!="nt":
        raise OSError("Windows keyring only")
    dll=ctypes.WinDLL("advapi32.dll",use_last_error=True)
    dll.CredReadW.argtypes=[ctypes.c_wchar_p,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(ctypes.POINTER(Credential))]
    dll.CredReadW.restype=wintypes.BOOL
    dll.CredFree.argtypes=[ctypes.c_void_p]
    ptr=ctypes.POINTER(Credential)()
    if not dll.CredReadW("gemini:antigravity",1,0,ctypes.byref(ptr)):
        raise OSError("Antigravity login unavailable")
    try:
        c=ptr.contents
        if c.CredentialBlobSize>100_000:
            raise ValueError("unexpected credential size")
        raw=ctypes.string_at(c.CredentialBlob,c.CredentialBlobSize)
    finally:
        dll.CredFree(ptr)
    blob=json.loads(raw.decode("utf-8"))
    token=(blob.get("token") or blob) if isinstance(blob,dict) else {}
    access=token.get("access_token")
    if not isinstance(access,str) or len(access)<30:
        raise ValueError("Antigravity access token unavailable")
    return access

def model_pools(models):
    if not isinstance(models,dict):
        raise ValueError("invalid available model response")
    groups={"gemini":[],"thirdParty":[]}
    for identifier,info in models.items():
        if not isinstance(info,dict) or info.get("isInternal"):
            continue
        name=str(identifier).lower()
        group="gemini" if name.startswith("gemini") else (
            "thirdParty" if name.startswith(("claude","gpt")) else None)
        if not group:
            continue
        quota=info.get("quotaInfo") or {}
        fraction=quota.get("remainingFraction")
        try:
            n=float(fraction)
        except (TypeError,ValueError):
            continue
        if not 0<=n<=1:
            continue
        reset=quota.get("resetTime")
        reset_value=reset if isinstance(reset,str) and len(reset)<70 else None
        groups[group].append({"remaining":n,"resetAt":reset_value})
    out={}
    for group,rows in groups.items():
        if not rows:
            out[group]=None
            continue
        lowest=min(rows,key=lambda x:x["remaining"])
        out[group]={"remainingPercent":round(lowest["remaining"]*100,1),
                    "resetAt":lowest["resetAt"],"modelCount":len(rows),
                    "unit":"shared_model_pool"}
    return out

def read_account_pools():
    access=bearer_from_windows_keyring()
    request=urllib.request.Request(
        URL,method="POST",data=b"{}",
        headers={"Authorization":"Bearer "+access,
                 "Content-Type":"application/json",
                 "Accept":"application/json",
                 "Client-Metadata":'{"ideType":"ANTIGRAVITY","platform":"WINDOWS","pluginType":"GEMINI"}',
                 "X-Goog-Api-Client":"google-cloud-sdk vscode_cloudshelleditor/0.1",
                 "User-Agent":"Antigravity/1.0.0"})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args):
            return None
    with urllib.request.build_opener(NoRedirect()).open(request,timeout=9) as response:
        document=json.load(response)
    return model_pools(document.get("models"))

def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(".tmp")
    temp.write_text(json.dumps(obj,ensure_ascii=False),encoding="utf-8")
    os.replace(temp,path)

def collect(now=None,fetcher=None,snapshot=None,state=None,repair=None):
    now=time.time() if now is None else now
    snapshot=snapshot or SNAPSHOT
    state=state or STATE
    try:
        prior=json.loads(state.read_text(encoding="utf-8-sig"))
    except (OSError,ValueError,UnicodeError):
        prior={}
    if now<float(prior.get("nextAttempt") or 0):
        return "COOLDOWN"
    try:
        fetcher=fetcher or read_account_pools
        pools=fetcher()
        if not pools or not any(pools.values()):
            raise ValueError("no accessible model quota data")
        result={"source":"antigravity_model_pools",
                "capturedAt":dt.datetime.fromtimestamp(now,dt.timezone.utc).isoformat(),
                "gemini":pools.get("gemini"),"thirdParty":pools.get("thirdParty")}
        write_json(snapshot,result)
        write_json(state,{"lastStatus":"OK","nextAttempt":now+INTERVAL_SECONDS})
        return "OK"
    except urllib.error.HTTPError as e:
        if e.code in (401,403) and repair is not None:
            # Optional official CLI login refresh: no model or prompt invocation.
            try:
                if repair():
                    return collect(now,fetcher,snapshot,state,repair=None)
            except (OSError,subprocess.SubprocessError):
                pass
        delay=7200 if e.code==429 else 10800 if e.code in (401,403) else 3600
        write_json(state,{"lastStatus":"HTTP_"+str(e.code),"nextAttempt":now+delay})
        return "HTTP_"+str(e.code)
    except (OSError,ValueError,TypeError,TimeoutError,urllib.error.URLError):
        write_json(state,{"lastStatus":"UNAVAILABLE","nextAttempt":now+3600})
        return "UNAVAILABLE"

def refresh_login_via_official_cli():
    """Optional read-only model listing to refresh expired official CLI login."""
    if not AGY_CLI.is_file():
        return False
    options={"stdout":subprocess.DEVNULL,"stderr":subprocess.DEVNULL,"timeout":16}
    if os.name=="nt":
        options["creationflags"]=subprocess.CREATE_NO_WINDOW
    result=subprocess.run([str(AGY_CLI),"models"],**options)
    return result.returncode==0

def display(path=None,now=None):
    now=time.time() if now is None else now
    path=path or SNAPSHOT
    result={"name":"Antigravity","observedAt":None,"fresh":False,
            "source":"antigravity_model_pools",
            "geminiPool":None,"thirdPartyPool":None,
            "note":"Antigravity 모델 풀 잔여율 미확보 · CLI 계정 확인 필요"}
    try:
        data=json.loads(path.read_text(encoding="utf-8-sig"))
        obs=dt.datetime.fromisoformat(data["capturedAt"].replace("Z","+00:00")).timestamp()
        if (data.get("source")!="antigravity_model_pools" or
            not -60<=now-obs<=14*86400):
            return result
        result["observedAt"]=dt.datetime.fromtimestamp(obs,dt.timezone(dt.timedelta(hours=9))).isoformat(timespec="minutes")
        result["fresh"]=0<=now-obs<=INTERVAL_SECONDS+120
        for name,key in (("gemini","geminiPool"),("thirdParty","thirdPartyPool")):
            row=data.get(name)
            if not isinstance(row,dict):
                continue
            percent=row.get("remainingPercent")
            if not isinstance(percent,(int,float)) or not 0<=percent<=100:
                continue
            result[key]={"remainingPercent":percent,
                         "resetAt":row.get("resetAt"),
                         "unit":"shared_model_pool",
                         "modelCount":row.get("modelCount",0)}
        if result["geminiPool"] or result["thirdPartyPool"]:
            result["note"]="모델 풀 잔여율 · Gemini 요청 수/주간 한도와 구분" + (
                " · 과거 기록" if not result["fresh"] else "")
    except (OSError,ValueError,TypeError,KeyError,UnicodeError):
        pass
    return result

def selftest():
    import unittest
    from unittest.mock import Mock
    class Test(unittest.TestCase):
        def test_two_shared_pools(self):
            m={"gemini-a":{"quotaInfo":{"remainingFraction":.966,"resetTime":"2026-10-19T00:00:00Z"}},
               "gemini-b":{"quotaInfo":{"remainingFraction":.999}},
               "claude-x":{"quotaInfo":{"remainingFraction":1}},
               "gpt-oss":{"quotaInfo":{"remainingFraction":1}},
               "tab-internal":{"quotaInfo":{"remainingFraction":0}},
               "claude-hidden":{"isInternal":True,"quotaInfo":{"remainingFraction":0}}}
            p=model_pools(m)
            self.assertEqual(p["gemini"]["remainingPercent"],96.6)
            self.assertEqual(p["thirdParty"]["remainingPercent"],100)
            self.assertEqual(p["thirdParty"]["modelCount"],2)
        def test_missing_never_zero(self):
            self.assertIsNone(model_pools({})["gemini"])
            self.assertIsNone(model_pools({"claude-x":{}})["thirdParty"])
        def test_collect_gate_and_display(self):
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)
                snap=path/"a.json"
                state=path/"s.json"
                read=Mock(return_value={"gemini":{"remainingPercent":96.6,"resetAt":None,"modelCount":3},
                        "thirdParty":{"remainingPercent":100,"resetAt":None,"modelCount":3}})
                when=1_790_000_000
                self.assertEqual(collect(when,fetcher=read,snapshot=snap,state=state),"OK")
                self.assertEqual(collect(when+20,fetcher=read,snapshot=snap,state=state),"COOLDOWN")
                read.assert_called_once()
                self.assertTrue(display(snap,when+30)["fresh"])
                self.assertFalse(display(snap,when+3700)["fresh"])
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Test))
    return result.wasSuccessful()

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="--test":
        raise SystemExit(0 if selftest() else 1)
    print(collect(repair=refresh_login_via_official_cli))
    print(json.dumps(display(),ensure_ascii=False))
