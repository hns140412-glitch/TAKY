from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

from voice_asset_reuse_router import VoiceAssetRequest, route_voice_asset, semantic_asset_key

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "CURRENT" / "VOICE_ASSET_REGISTRY_CURRENT.json"
OUTPUT = ROOT / "CURRENT" / "VOICE_EXPLORER_CREW_PRODUCTION_PREFLIGHT_CURRENT.json"

EXPECTED_LOCK = "EXPLORER_CREW_V2_SOURCE_LOCK_20261009_SCRIPT_LOCK_R10"
EXPECTED_MAIN = "SCRIPT_LOCKED_MAIN_CREW_E5_6_2026-10-09"
EXPECTED_PLAY = "SCRIPT_LOCKED_PLAY_CAMP_CORE6_2026-10-09"
CORE6 = ["dubi", "lori", "ink", "nova", "take", "zero"]
ALL24 = CORE6 + [f"guide-{i:02d}" for i in range(7, 25)]
INTENTS = ["ASK", "HINT", "ACKNOWLEDGE"]
FAMILY = {
    "dubi":"VF01_ADVENTURE","guide-08":"VF01_ADVENTURE","guide-14":"VF01_ADVENTURE","guide-21":"VF01_ADVENTURE",
    "lori":"VF02_CARE","guide-12":"VF02_CARE","guide-18":"VF02_CARE","guide-22":"VF02_CARE",
    "ink":"VF03_OBSERVE","guide-09":"VF03_OBSERVE","guide-17":"VF03_OBSERVE","guide-20":"VF03_OBSERVE",
    "take":"VF04_LEADER","guide-11":"VF04_LEADER","guide-19":"VF04_LEADER","guide-23":"VF04_LEADER",
    "nova":"VF05_CONNECT","guide-10":"VF05_CONNECT","guide-16":"VF05_CONNECT","guide-24":"VF05_CONNECT",
    "zero":"VF06_CALM_DISCOVERY","guide-07":"VF06_CALM_DISCOVERY","guide-13":"VF06_CALM_DISCOVERY","guide-15":"VF06_CALM_DISCOVERY",
}
FAMILY_ANCHOR = {
    "VF01_ADVENTURE":"dubi","VF02_CARE":"lori","VF03_OBSERVE":"ink",
    "VF04_LEADER":"take","VF05_CONNECT":"nova","VF06_CALM_DISCOVERY":"zero",
}


def _node_snapshot(repo: Path) -> dict:
    code = r"""
const A=require('./vendor/taky/explorer-crew/dialogue-script-authority-v1.js');
const R=require('./vendor/taky/explorer-crew/personality-registry-v2.js');
const ids=['dubi','lori','ink','nova','take','zero',...Array.from({length:18},(_,i)=>'guide-'+String(i+7).padStart(2,'0'))];
const intents=['ASK','HINT','ACKNOWLEDGE'];
const main=[],play=[],signatures={};
for(const id of ids){
  const p=R.get(id); signatures[id]=p?.signature||'';
  for(const intent of intents){
    (A.LINES?.[id]?.E5_6?.[intent]||[]).forEach((text,variant)=>main.push({id,intent,variant,text}));
  }
}
for(const id of ids.slice(0,6)){
  for(const intent of intents){
    (A.PLAY_CAMP_LINES?.[id]?.[intent]||[]).forEach((text,variant)=>play.push({id,intent,variant,text}));
  }
}
console.log(JSON.stringify({status:A.STATUS,play_status:A.PLAY_CAMP_CANDIDATE_STATUS,play_scope:A.PLAY_CAMP_CANDIDATE_SCOPE,locked:A.LOCKED_PRODUCTION_GROUPS,main,play,signatures}));
"""
    p = subprocess.run(["node", "-e", code], cwd=repo, capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(p.stdout)


def _normalized_sha(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _verify_source_lock(repo: Path) -> dict:
    lock_path = repo / "vendor" / "taky" / "explorer-crew" / "source-lock-v2.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8-sig"))
    bad = []
    for name, expected in lock["files"].items():
        p = lock_path.parent / name
        if not p.exists():
            bad.append({"file": name, "reason": "MISSING"})
            continue
        got = _normalized_sha(p)
        if got != expected:
            bad.append({"file": name, "reason": "SHA_MISMATCH", "expected": expected, "actual": got})
    return {"version": lock["version"], "count": len(lock["files"]), "bad": bad}


def _chars(text: str) -> int:
    return len(text)


def _cap(chars: int) -> int:
    return math.ceil(chars * 1.10)


def build(repo: Path, voice_config: Path | None) -> dict:
    snap = _node_snapshot(repo)
    lock = _verify_source_lock(repo)
    if lock["version"] != EXPECTED_LOCK or lock["bad"]:
        raise RuntimeError("Explorer Crew R10 source lock verification failed")
    if snap["status"] != EXPECTED_MAIN or snap["play_status"] != EXPECTED_PLAY:
        raise RuntimeError("Explorer Crew script lock status mismatch")
    if snap["locked"] != ["PLAY_CAMP", "MAIN_CREW"]:
        raise RuntimeError("Explorer Crew production-group lock mismatch")
    if snap["play_scope"] != "COMMON_NEUTRAL_BANK__SCRIPT_LOCKED__RUNTIME_ENABLED":
        raise RuntimeError("Play Camp runtime scope mismatch")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assets = registry.get("assets", [])
    lines = []
    exact_texts = set()
    duplicate_texts = []
    for group, rows in (("PLAY_CAMP", snap["play"]), ("MAIN_CREW", snap["main"])):
        for row in rows:
            text = row["text"]
            if text in exact_texts:
                duplicate_texts.append(text)
            exact_texts.add(text)
            cid = row["id"]
            key = semantic_asset_key(
                role="EXPLORER_CREW",
                locale="ko-KR",
                voice_family=FAMILY[cid],
                character_id=cid,
                intent=row["intent"],
                meaning=text,
            )
            decision = route_voice_asset(
                VoiceAssetRequest(
                    semantic_asset_key=key, role="EXPLORER_CREW", locale="ko-KR",
                    text=text, voice_family=FAMILY[cid], character_id=cid, intent=row["intent"],
                ),
                assets,
            )
            lines.append({
                "production_group": group, "character_id": cid, "voice_family": FAMILY[cid],
                "intent": row["intent"], "variant": row["variant"], "chars": _chars(text),
                "script_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "semantic_asset_key": key, "route": decision.route, "reuse_asset_id": decision.asset_id,
            })

    core = set(CORE6)
    play_lines = [x for x in lines if x["production_group"] == "PLAY_CAMP"]
    main_core = [x for x in lines if x["production_group"] == "MAIN_CREW" and x["character_id"] in core]
    main_later = [x for x in lines if x["production_group"] == "MAIN_CREW" and x["character_id"] not in core]

    casting = []
    for family, cid in FAMILY_ANCHOR.items():
        text = snap["signatures"][cid]
        casting.append({
            "voice_family": family, "anchor_character_id": cid,
            "signature_chars": _chars(text),
            "signature_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "candidate_count": 3,
        })
    casting_chars = sum(x["signature_chars"] * x["candidate_count"] for x in casting)

    stages = [
        {"id":"P2_VOICE_FAMILY_CASTING","calls":18,"chars":casting_chars,"planning_cap_10pct":_cap(casting_chars)},
        {"id":"P3_PLAY_CAMP_CORE6","calls":len(play_lines),"chars":sum(x["chars"] for x in play_lines),"planning_cap_10pct":_cap(sum(x["chars"] for x in play_lines))},
        {"id":"P4_MAIN_CORE6","calls":len(main_core),"chars":sum(x["chars"] for x in main_core),"planning_cap_10pct":_cap(sum(x["chars"] for x in main_core))},
        {"id":"P5_MAIN_LATER18","calls":len(main_later),"chars":sum(x["chars"] for x in main_later),"planning_cap_10pct":_cap(sum(x["chars"] for x in main_later))},
    ]

    cfg = {}
    if voice_config and voice_config.exists():
        cfg = json.loads(voice_config.read_text(encoding="utf-8"))
    families = cfg.get("families", {})
    config_ready = all(
        families.get(f, {}).get("voice_id")
        and families.get(f, {}).get("model_id")
        and families.get(f, {}).get("output_format")
        for f in FAMILY_ANCHOR
    )

    routes = {}
    for x in lines:
        routes[x["route"]] = routes.get(x["route"], 0) + 1

    result = {
        "schema": "TAKY_EXPLORER_CREW_VOICE_PRODUCTION_PREFLIGHT_V1",
        "source_lock": lock,
        "script_lock": {
            "main": snap["status"], "play_camp": snap["play_status"],
            "play_camp_scope": snap["play_scope"], "locked_production_groups": snap["locked"],
        },
        "route_policy": "ROUTE_BEFORE_CREATE",
        "registry_asset_count": len(assets),
        "route_summary": routes,
        "exact_text_duplicate_count": len(duplicate_texts),
        "production_lines": {
            "total_clips": len(lines),
            "total_chars": sum(x["chars"] for x in lines),
            "play_camp_core6": {"clips": len(play_lines), "chars": sum(x["chars"] for x in play_lines)},
            "main_core6": {"clips": len(main_core), "chars": sum(x["chars"] for x in main_core)},
            "main_later18": {"clips": len(main_later), "chars": sum(x["chars"] for x in main_later)},
        },
        "casting": {"families": casting, "calls": 18, "chars": casting_chars, "selected_signature_assets_reusable": 6},
        "stages": stages,
        "planning_assumption": "Approx. 1 credit/input character based on prior observed technical probes; provider/account billing not yet re-verified.",
        "planning_total": {
            "calls": sum(x["calls"] for x in stages),
            "chars": sum(x["chars"] for x in stages),
            "sum_stage_caps_10pct": sum(x["planning_cap_10pct"] for x in stages),
        },
        "voice_configuration_ready": config_ready,
        "generation_authorized": False,
        "blocking_reasons": ([] if config_ready else ["VOICE_IDS_MODEL_OUTPUT_FORMAT_NOT_LOCKED"]) + ["EXPLICIT_USER_PAID_GENERATION_APPROVAL_REQUIRED"],
        "status": "READY_FOR_USER_APPROVAL" if config_ready else "HOLD_PREPRODUCTION_CONFIGURATION",
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--crew-repo", required=True)
    ap.add_argument("--voice-config")
    args = ap.parse_args()
    result = build(Path(args.crew_repo), Path(args.voice_config) if args.voice_config else None)
    print(json.dumps({
        "status": result["status"],
        "source_lock_bad": len(result["source_lock"]["bad"]),
        "route_summary": result["route_summary"],
        "production_lines": result["production_lines"],
        "casting": {"calls":result["casting"]["calls"],"chars":result["casting"]["chars"]},
        "planning_total": result["planning_total"],
        "blocking_reasons": result["blocking_reasons"],
        "output": str(OUTPUT),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
