#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/"OS"/"MOBILE_APP_DEVELOPMENT_REGISTRY.json"
data=json.loads(REG.read_text(encoding="utf-8"))

token=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if not token:
    print("FAIL: GitHub token required for live mobile registry refresh check")
    raise SystemExit(2)

apps=data.get("apps") or {}
drift=[]
checked=[]

def get_json(url):
    req=urllib.request.Request(
        url,
        headers={
            "Accept":"application/vnd.github+json",
            "Authorization":"Bearer "+token,
            "X-GitHub-Api-Version":"2022-11-28",
            "User-Agent":"TAKY-mobile-registry-live-refresh"
        }
    )
    try:
        with urllib.request.urlopen(req,timeout=20) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        body=e.read().decode("utf-8","replace")
        print(f"FAIL: GitHub API {e.code} for {url}: {body}")
        raise SystemExit(3)

for key,app in apps.items():
    gh=app.get("github") or {}
    repo=gh.get("repo")
    branch=gh.get("default_branch") or "main"
    stored=gh.get("main_head")
    if not repo or not stored:
        continue
    live=get_json(f"https://api.github.com/repos/{repo}/commits/{branch}")
    live_sha=live.get("sha")
    checked.append({"app":key,"repo":repo,"branch":branch,"stored":stored,"live":live_sha})
    if live_sha!=stored:
        drift.append({"app":key,"repo":repo,"branch":branch,"stored":stored,"live":live_sha})

print(json.dumps({"checked":checked,"drift":drift},ensure_ascii=False,indent=2))
if drift:
    print("FAIL: MOBILE_APP_REGISTRY_SOURCE_HEAD_DRIFT")
    raise SystemExit(1)
print("PASS: mobile app registry GitHub source heads match live default-branch heads")
