#!/usr/bin/env python3
"""Evidence-only ChatGPT transcript/export -> TAKY topic projection.

Existing original files remain untouched. Only supported USER/ASSISTANT messages
are indexed. Text is used transiently to route topics; no message text is saved.
Classification is conservative and requires named context; unknown stays UNKNOWN.
No model calls, browser scraping, account tokens or authority promotion.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from TAKY_CONVERSATION_TOPIC_PROJECTION import build_projection

SHARE_HEADER = re.compile(r"^## \[(\d+)\] (USER|ASSISTANT) — (.+)$", re.M)
TOPIC_RULES = [
    ("TAKY-MOBILE", "webapp-management", "웹앱·계정·배포 관리",
     (r"관리자 인증", r"관리자 로그인", r"웹앱 설치", r"앱 배포", r"앱 바로가기", r"에셋.*뱃지", r"탐험대원.*관리")),
    ("TAKY-MOBILE", "drive-server-management", "Drive·서버 관제",
     (r"구글.?드라이브.*용량", r"서버.?관리", r"데이터 서버", r"운영 서버", r"drive.*storage", r"서버.?용량")),
    ("TAKY-MOBILE", "chat-orchestration", "대화·오케스트레이션 관제",
     (r"워크벤치", r"오케스트라", r"대화창.*파편", r"ai.?작업공간", r"중복.*충돌", r"상호.?결과물")),
    ("TAKY-MOBILE", "chat-topic-routing", "대화 주제 분류",
     (r"대화창.*주제", r"주제.*아이디", r"주제.*분류", r"topic.?id", r"주제.*바뀌", r"주제.*전환")),
    ("PLAY-CAMP", "learning-experience", "Play Camp 학습 경험",
     (r"플레이.?캠프", r"play.?camp", r"수련 캠프", r"한글.?플립북")),
    ("HIDE-SEEK", "learning-experience", "Hide & Seek 학습 경험",
     (r"하이드.?앤.?씩", r"하이드.?앤.?시크", r"hide.?&.?seek", r"hide.?seek")),
    ("READY-SET", "learning-experience", "Ready & Set 학습 경험",
     (r"레디.?앤.?셋", r"ready.?&.?set")),
    ("SNAP-POP", "learning-experience", "Snap & Pop 학습 경험",
     (r"스냅.?앤.?팝", r"snap.?&.?pop")),
    ("SAVEY", "finance-app", "SAVEY 가계부",
     (r"세이비", r"savey")),
    ("TAKY_ARCHI-GROW", "architecture", "Archi Grow 건축 실무",
     (r"아키.?그로우", r"archi.?grow", r"통합.?심의", r"소방.?성능위주")),
]
CONTINUATION = re.compile(r"^(ㄱ|r|계속|진행|이어서|ㅇㅋ|오케이|다음|재개|확인|좋아|네|응|ㅇㅇ|그래)\s*[.!?~]*$", re.I)
WORK_ID = re.compile(r"\bTAKY-CHAT-[0-9a-f]{32}\b", re.I)
META_KEYS = ["SHARE_CONVERSATION_ID", "BACKING_CONVERSATION_ID", "SOURCE_FILE"]

def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def class_topics(text: str) -> list[dict]:
    results = []
    for project, key, label, patterns in TOPIC_RULES:
        if any(re.search(p, text, re.I) for p in patterns):
            results.append({"project": project, "topic_key": key, "label": label})
    return results

def _as_time(value) -> str:
    try:
        if value is None: return ""
        return datetime.fromtimestamp(float(value), timezone.utc).isoformat()
    except (ValueError, TypeError, OverflowError, OSError):
        return ""

def _message_event(chat_ref, message_id, seq, role, body, when, source_ref, inherited):
    topics = class_topics(body) if role == "USER" else []
    reason = "MATCHED_LOCAL_RULE" if topics else "UNCLASSIFIED"
    if not topics and inherited and (role == "ASSISTANT" or CONTINUATION.fullmatch(body.strip())):
        topics = [inherited]
        reason = "CONTEXT_CONTINUATION_NOT_NEW_DECISION"
    primary = topics[0]["topic_key"] if len(topics) == 1 else None
    # Do not claim a primary for a multi-topic turn even if the previous turn was known.
    event_id = "CHATMSG-" + sha(chat_ref + "\x00" + message_id)[:24]
    return {
        "event_id": event_id, "conversation_id": chat_ref,
        "message_index": seq, "captured_at": when,
        "actor": role, "source_ref": source_ref,
        "source_text_sha256": sha(body),
        "topic_refs": topics, "primary_topic_key": primary,
        "classification_basis": reason,
        "work_ids": sorted({"TAKY-CHAT-" + x[10:].lower() for x in WORK_ID.findall(body)}),
        "authority": "SOURCE_LINK_NOT_DECISION_OR_COMPLETION",
        "source_coverage": "SUPPLIED_CONVERSATION_ONLY",
    }

def _messages_to_events(chat_ref, messages, source_path, source_kind):
    rows, inherited = [], None
    for i, msg in enumerate(messages, 1):
        role = str(msg["role"]).upper()
        if role not in ("USER", "ASSISTANT"): continue
        message_id = str(msg.get("message_id") or "")
        if not message_id or message_id == "UNKNOWN_MESSAGE_ID":
            raise ValueError("SOURCE_MESSAGE_ID_UNAVAILABLE")
        body = str(msg.get("text") or "")
        row = _message_event(chat_ref, message_id, i, role, body,
                             str(msg.get("timestamp") or ""),
                             str(source_path) + "#node=" + message_id, inherited)
        row["source_kind"] = source_kind
        if row["primary_topic_key"]:
            inherited = row["topic_refs"][0]
        elif role == "USER":
            # Ambiguous/new unknown user intent cannot silently preserve an old topic.
            inherited = None
        rows.append(row)
    return rows

def from_sanitized_share(path: Path):
    raw = path.read_text(encoding="utf-8-sig")
    required = ["STATUS: TRANSCRIPT_ONLY / NOTEBOOKLM_INPUT_CANDIDATE",
                "SCOPE: SAVED PAGE linear_conversation; USER↔ASSISTANT only"]
    if any(x not in raw for x in required):
        raise ValueError("UNTRUSTED_UNSANITIZED_SHARE")
    meta = {}
    for name in META_KEYS:
        m = re.search(r"^" + re.escape(name) + r": (.+)$", raw, re.M)
        if m: meta[name] = m.group(1).strip()
    backing = meta.get("BACKING_CONVERSATION_ID", "")
    shared = meta.get("SHARE_CONVERSATION_ID", "")
    origin = ("chatgpt:backing:" + backing
              if backing and not backing.startswith("UNKNOWN")
              else "chatgpt:share:" + shared
              if shared and not shared.startswith("UNKNOWN") else None)
    if not origin:
        raise ValueError("NATIVE_OR_SHARE_CONVERSATION_ID_REQUIRED")
    parts = list(SHARE_HEADER.finditer(raw))
    if not parts:
        raise ValueError("SANITIZED_SHARE_WITHOUT_MESSAGES")
    messages = []
    for i, match in enumerate(parts):
        chunk = raw[match.end():parts[i + 1].start() if i + 1 < len(parts) else len(raw)]
        node = re.search(r"^SOURCE_NODE_ID: (.+)$", chunk, re.M)
        if not node:
            raise ValueError("SOURCE_NODE_ID_MISSING")
        body = re.sub(r"(?ms)\n---\s*\Z", "", chunk)
        body = re.sub(r"(?s)^\s*SOURCE_NODE_ID: [^\n]+\nCONTENT_TYPE: [^\n]+\n\s*", "", body)
        messages.append({"role": match.group(2), "message_id": node.group(1).strip(),
                         "timestamp": match.group(3).strip(), "text": body.strip()})
    return _messages_to_events(origin, messages, path, "SANITIZED_SHARE")

def _selected_chain(convo):
    mapping = convo.get("mapping")
    if not isinstance(mapping, dict): raise ValueError("EXPORT_MAPPING_MISSING")
    current = convo.get("current_node")
    if not isinstance(current,str) or current not in mapping:
        # The export may omit current_node; ambiguity is surfaced, not guessed.
        raise ValueError("EXPORT_SELECTED_BRANCH_MISSING")
    chain, seen = [], set()
    while current:
        if current in seen: raise ValueError("EXPORT_CYCLE")
        seen.add(current)
        node = mapping.get(current)
        if not isinstance(node,dict): raise ValueError("EXPORT_BROKEN_PARENT")
        chain.append((current,node))
        current = node.get("parent")
    chain.reverse()
    return chain

def from_export(path: Path, max_bytes=200_000_000):
    if path.stat().st_size > max_bytes: raise ValueError("EXPORT_TOO_LARGE")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list): raise ValueError("CONVERSATIONS_EXPORT_ARRAY_REQUIRED")
    events = []
    for convo in payload:
        if not isinstance(convo, dict): raise ValueError("INVALID_EXPORTED_CONVERSATION")
        native = str(convo.get("id") or "").strip()
        if not native: raise ValueError("EXPORT_NATIVE_CHAT_ID_MISSING")
        messages = []
        for node_id, node in _selected_chain(convo):
            m = node.get("message")
            if not isinstance(m,dict): continue
            role = str((m.get("author") or {}).get("role") or "").upper()
            if role not in ("USER","ASSISTANT"): continue
            content = m.get("content") or {}
            parts = content.get("parts")
            if not isinstance(parts,list): parts = []
            bodies = []
            for part in parts:
                if isinstance(part,str): bodies.append(part)
                elif isinstance(part,dict) and isinstance(part.get("text"),str):
                    bodies.append(part["text"])
                else: bodies.append("[NON_TEXT_PART_SOURCE_REQUIRES_REVIEW]")
            messages.append({"role": role, "message_id": str(node_id),
                             "timestamp": _as_time(m.get("create_time")),
                             "text": "\n".join(bodies)})
        events.extend(_messages_to_events("chatgpt:backing:" + native, messages, path, "ACCOUNT_EXPORT_SELECTED_BRANCH"))
    return events

def merge_events(existing: list[dict], incoming: list[dict]):
    """Reconcile repeated observations of one real message without losing provenance."""
    merged = {}
    for row in existing + incoming:
        key = str(row.get("event_id") or "")
        if not key:
            raise ValueError("EVENT_ID_MISSING")
        if key not in merged:
            merged[key] = dict(row)
            continue
        prev = merged[key]
        # Native source equality is necessary, but different messages must NEVER be collapsed.
        essential = ("conversation_id", "actor", "source_text_sha256", "topic_refs",
                     "primary_topic_key", "work_ids")
        if any(prev.get(k) != row.get(k) for k in essential):
            raise ValueError("SOURCE_MESSAGE_CONFLICT:" + key)
        # Legacy event replay (no source-text SHA) still requires exact equality.
        if not prev.get("source_text_sha256"):
            if prev != row:
                raise ValueError("EVENT_ID_REPLAY_CONFLICT:" + key)
            continue
        all_refs = list(prev.get("source_observation_refs") or [prev.get("source_ref")])
        for ref in row.get("source_observation_refs") or [row.get("source_ref")]:
            if ref not in all_refs:
                all_refs.append(ref)
        prev["source_observation_refs"] = sorted(str(x) for x in all_refs if x)
        all_indices = set(prev.get("sequence_observations") or [prev.get("message_index")])
        all_indices.add(row.get("message_index"))
        prev["sequence_observations"] = sorted(i for i in all_indices if isinstance(i, int))
        all_times = set(prev.get("timestamp_observations") or [prev.get("captured_at")])
        all_times.add(row.get("captured_at"))
        prev["timestamp_observations"] = sorted(str(t) for t in all_times if t)
        # Explicit disagreement is visible; neither source is silently declared authoritative.
        if len(prev["sequence_observations"]) > 1 or len(prev["timestamp_observations"]) > 1:
            prev["multi_source_order_review"] = True
    return build_projection(list(merged.values()))

def attach_ai_assignments(view: dict, data: dict) -> dict:
    """Join work only by an explicit WORK_ID; never infer by project name alone."""
    rows = data.get("tasks")
    if not isinstance(rows, list):
        raise ValueError("WORK_ASSIGNMENTS_TASKS_MISSING")
    registry = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("work_id"), str):
            raise ValueError("WORK_ASSIGNMENT_INVALID")
        work_id = row["work_id"]
        if work_id in registry:
            raise ValueError("DUPLICATE_WORK_ID:" + work_id)
        registry[work_id] = row
    topic_counts = {}
    for t in view["topics"]:
        matches = []
        for work_id in t.get("work_ids", []):
            row = registry.get(work_id)
            if row is None:
                matches.append({"work_id": work_id, "binding": "WORK_ID_NOT_REGISTERED"})
                continue
            topic_counts[work_id] = topic_counts.get(work_id, 0) + 1
            matches.append({
                "work_id": work_id, "binding": "EXPLICIT_ID_MATCH",
                "executor": row.get("executor"), "reviewer": row.get("reviewer"),
                "registry_status": row.get("status"), "source_repo": row.get("project"),
                "evidence_refs": row.get("evidence_refs", []),
                "output_refs": row.get("output_refs", []),
                "reported_verified": row.get("execution_verified") is True,
                "verification": "REGISTRY_CLAIM_NOT_RUNTIME_ATTESTATION",
            })
        t["ai_work_links"] = matches
    unlinked = []
    for work_id, row in registry.items():
        if work_id not in topic_counts:
            unlinked.append({
                "work_id": work_id, "executor": row.get("executor"),
                "registry_status": row.get("status"), "reviewer": row.get("reviewer"),
                "output_count": len(row.get("output_refs") or []),
                "evidence_count": len(row.get("evidence_refs") or []),
                "reason": "NO_EXPLICIT_CONVERSATION_TOPIC_BINDING",
            })
    view["ai_workbench"] = {
        "authority": "ASSIGNMENT_REGISTRY_SNAPSHOT_NOT_LIVE_EXECUTION",
        "total_registered": len(registry), "topic_linked": len(topic_counts),
        "unlinked": unlinked, "cross_topic_work_ids":
            sorted(k for k, n in topic_counts.items() if n > 1),
        "unverified_or_missing":
            sorted(k for k, r in registry.items() if r.get("execution_verified") is not True),
        "no_completion_inferred_from_registration": True,
    }
    return view

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sanitized-share", type=Path, action="append", default=[])
    parser.add_argument("--conversations-export", type=Path, action="append", default=[])
    parser.add_argument("--event-journal", type=Path, action="append", default=[])
    parser.add_argument("--assignments", type=Path, help="Existing workbench AI_WORK_ASSIGNMENTS.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not any((args.sanitized_share, args.conversations_export, args.event_journal)):
        parser.error("AT_LEAST_ONE_SOURCE_REQUIRED")
    import TAKY_CONVERSATION_TOPIC_PROJECTION as proj
    evidence = []
    for p in args.event_journal: evidence.extend(proj.load_events([p]))
    for p in args.sanitized_share: evidence.extend(from_sanitized_share(p))
    for p in args.conversations_export: evidence.extend(from_export(p))
    view = merge_events([], evidence)
    if args.assignments:
        view = attach_ai_assignments(view, json.loads(args.assignments.read_text(encoding="utf-8-sig")))
    source_fps = []
    for p in args.sanitized_share + args.conversations_export + args.event_journal:
        if not p.is_file(): raise ValueError("SOURCE_MISSING")
        source_fps.append({"source_ref": str(p), "file_sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    if args.assignments:
        source_fps.append({"source_ref": str(args.assignments),
                           "file_sha256": hashlib.sha256(args.assignments.read_bytes()).hexdigest(),
                           "role": "AI_ASSIGNMENT_SNAPSHOT"})
    view["source_manifest"] = source_fps
    view["auto_classification"] = "CONSERVATIVE_RULE_BASED_NO_MODEL; UNKNOWN_NOT_PROMOTED"
    view["source_count"] = len(source_fps)
    if args.output:
        if not args.output.parent.is_dir(): raise ValueError("OUTPUT_PARENT_MISSING")
        data = json.dumps(view, ensure_ascii=False, indent=2) + "\n"
        tmp = args.output.with_name(args.output.name + ".bridge-tmp")
        try:
            tmp.write_text(data, encoding="utf-8")
            tmp.replace(args.output)
        finally: tmp.unlink(missing_ok=True)
    print(json.dumps({"schema": view["schema"],"sources":len(source_fps),
                      "counts":view["counts"], "status":"INDEX_ONLY_NO_CANONICAL_WRITE",
                      "output":str(args.output) if args.output else None}, ensure_ascii=False))

if __name__ == "__main__": run()
