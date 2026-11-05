#!/usr/bin/env python3
"""Rebuild a read-only CHAT / TOPIC / WORK projection from existing conversation evidence.

This is an INDEX, never a second conversation store or canonical authority.
Explicit topic links are projected. Untagged turns remain unclassified rather
than using unverified semantic guesses. Does not invoke any model or remote API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from collections import defaultdict

SCHEMA = "TAKY_CONVERSATION_TOPIC_PROJECTION_V1"


def digest(value: str, size: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:size]


def normalized(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def stable_topic_id(project: str, key: str) -> str:
    if not project.strip() or not key.strip():
        raise ValueError("TOPIC_PROJECT_AND_KEY_REQUIRED")
    return "TOPIC-" + digest(normalized(project) + "\x00" + normalized(key))


def stable_chat_id(native_id: str) -> str:
    if not native_id.strip():
        raise ValueError("NATIVE_CHAT_ID_REQUIRED")
    return "CHAT-" + digest(native_id.strip())


def _topic_refs(row: dict) -> list[dict]:
    refs = row.get("topic_refs")
    if refs is None and row.get("topic_key"):
        refs = [{"project": row.get("project_namespace") or row.get("project"),
                 "topic_key": row.get("topic_key"), "label": row.get("topic_label") or row.get("topic_key")}]
    if refs is None:
        return []
    if not isinstance(refs, list):
        raise ValueError("TOPIC_REFS_NOT_ARRAY")
    out = []
    for ref in refs:
        if not isinstance(ref, dict):
            raise ValueError("TOPIC_REF_NOT_OBJECT")
        project = str(ref.get("project") or row.get("project_namespace") or row.get("project") or "").strip()
        key = str(ref.get("topic_key") or "").strip()
        label = str(ref.get("label") or key).strip()
        if not project or not key or not label:
            raise ValueError("TOPIC_REF_MISSING_PROJECT_KEY_LABEL")
        out.append({"topic_id": stable_topic_id(project, key), "project": project,
                    "topic_key": normalized(key), "label": label})
    if len(set(t["topic_id"] for t in out)) != len(out):
        raise ValueError("DUPLICATE_TOPIC_REF_ON_EVENT")
    return out


def load_events(paths: list[Path]) -> list[dict]:
    events = []
    for path in paths:
        for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("EVENT_NOT_OBJECT")
            if not row.get("event_id"):
                raise ValueError(f"EVENT_ID_REQUIRED:{path.name}:{line_no}")
            events.append(row)
    return events


def build_projection(events: list[dict]) -> dict:
    unique = {}
    for row in events:
        event_id = str(row["event_id"])
        encoded = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if event_id in unique:
            prior = json.dumps(unique[event_id], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if encoded != prior:
                raise ValueError("EVENT_ID_REPLAY_CONFLICT:" + event_id)
            continue
        unique[event_id] = row

    by_chat = defaultdict(list)
    unbound = []
    for row in unique.values():
        native = str(row.get("conversation_id") or row.get("chat_id") or "").strip()
        if not native:
            unbound.append({"event_id": str(row["event_id"]),
                            "reason": "NATIVE_CHAT_ID_UNAVAILABLE",
                            "session_ref": str(row.get("session_id") or "")})
            continue
        by_chat[native].append(row)

    topics, chats, transitions, unresolved = {}, [], [], []
    for native in sorted(by_chat):
        rows = by_chat[native]
        rows.sort(key=lambda r: (str(r.get("captured_at") or ""),
                                 int(r["message_index"]) if str(r.get("message_index", "")).isdigit() else -1,
                                 str(r["event_id"])))
        chat_id = stable_chat_id(native)
        active = None
        visited = set()
        links = []
        for row in rows:
            event_id = str(row["event_id"])
            topic_refs = _topic_refs(row)
            ids = [t["topic_id"] for t in topic_refs]
            for t in topic_refs:
                prev = topics.get(t["topic_id"])
                if prev and (prev["project"] != t["project"] or prev["topic_key"] != t["topic_key"]):
                    raise ValueError("TOPIC_ID_COLLISION")
                if not prev:
                    topics[t["topic_id"]] = {**t, "chat_ids": [], "event_ids": [], "work_ids": [],
                                             "authority": "DERIVED_INDEX_NOT_CANONICAL"}
                    prev = topics[t["topic_id"]]
                if chat_id not in prev["chat_ids"]:
                    prev["chat_ids"].append(chat_id)
                prev["event_ids"].append(event_id)
                for w in row.get("work_ids", []):
                    if not isinstance(w, str):
                        raise ValueError("INVALID_WORK_ID")
                    if w not in prev["work_ids"]:
                        prev["work_ids"].append(w)

            main_key = row.get("primary_topic_key")
            primary = None
            if main_key:
                wanted = normalized(str(main_key))
                selected = [t for t in topic_refs if t["topic_key"] == wanted]
                if len(selected) != 1:
                    raise ValueError("PRIMARY_TOPIC_NOT_IN_REFERENCES:" + event_id)
                primary = selected[0]["topic_id"]
            elif len(ids) == 1:
                primary = ids[0]

            status = "LINKED" if ids else "REQUIRES_TOPIC_CLASSIFICATION"
            if len(ids) > 1 and primary is None:
                status = "MULTI_TOPIC_PRIMARY_UNRESOLVED"
            links.append({"event_id": event_id, "topic_ids": ids, "primary_topic_id": primary,
                          "source_ref": str(row.get("source_ref") or ""),
                          "source_observation_refs": row.get("source_observation_refs", []),
                          "source_order_review": row.get("multi_source_order_review", False),
                          "classification_source": row.get("classification_source","UNSPECIFIED"),
                          "review_required": row.get("review_required",False),
                          "work_ids": row.get("work_ids", []), "status": status})
            if status != "LINKED":
                unresolved.append({"chat_id": chat_id, "event_id": event_id, "reason": status})
            if primary and primary != active:
                kind = "TOPIC_STARTED" if active is None else "TOPIC_RETURNED" if primary in visited else "TOPIC_SWITCHED"
                transitions.append({"chat_id": chat_id, "event_id": event_id, "kind": kind,
                                    "from_topic_id": active, "to_topic_id": primary})
                active = primary
            visited.update(ids)
        chats.append({"chat_id": chat_id, "native_chat_ref": native, "event_count": len(rows),
                      "topic_ids": sorted(visited), "active_topic_id": active,
                      "links": links, "source_scope": "ONLY_SUPPLIED_EVENTS"})

    return {"schema": SCHEMA, "authority": "REBUILDABLE_VIEW_NOT_CANONICAL",
            "source_coverage": "ONLY_SUPPLIED_EVENTS_NOT_ALL_CHATGPT_HISTORY",
            "chats": chats, "topics": [topics[k] for k in sorted(topics)],
            "transitions": transitions, "unresolved_events": unresolved,
            "unbound_events": unbound,
            "counts": {"chat": len(chats), "topic": len(topics), "transitions": len(transitions),
                       "unresolved": len(unresolved), "without_native_chat_id": len(unbound)},
            "no_ai_or_remote_calls": True, "canonical_changed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, action="append", required=True, help="Existing JSONL conversation event journal(s)")
    parser.add_argument("--output", type=Path, help="Derived workbench view (optional)")
    args = parser.parse_args()
    view = build_projection(load_events(args.events))
    blob = json.dumps(view, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        if not args.output.parent.is_dir():
            parser.error("OUTPUT_PARENT_MISSING")
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != blob:
            tmp = args.output.with_name(args.output.name + ".topic-tmp")
            try:
                tmp.write_text(blob, encoding="utf-8")
                os.replace(tmp, args.output)
            finally:
                tmp.unlink(missing_ok=True)
    print(json.dumps({"schema": SCHEMA, "counts": view["counts"],
                      "output": str(args.output) if args.output else None,
                      "source_coverage": view["source_coverage"],
                      "no_ai_or_remote_calls": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
