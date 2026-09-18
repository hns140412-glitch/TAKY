#!/usr/bin/env python3
"""Extract a NotebookLM-safe USER↔ASSISTANT transcript from saved ChatGPT share HTML.

The saved page may contain authentication/session/bootstrap/application data in addition
to the shared conversation. This tool never copies the page wholesale. It decodes the
React Router flattened loader payload, selects the declared linear conversation, emits
only USER/ASSISTANT message content, and runs a post-output secret/session safety scan.

Claim boundary:
- output reflects the saved page's linear_conversation only;
- non-text parts are represented by explicit markers, not silently dropped;
- successful extraction does not prove account-history completeness.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENQUEUE_MARKER = 'window.__reactRouterContext.streamController.enqueue("'
ROLE_ALLOW = {"user", "assistant"}
SECRET_PATTERNS = {
    "access_token": re.compile(r"accessToken", re.I),
    "authorization_header": re.compile(r"Authorization\s*[:=]", re.I),
    "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9._~+/-]{12,}", re.I),
    "client_bootstrap": re.compile(r"client-bootstrap", re.I),
    "session_user_blob": re.compile(r'"session"\s*:\s*\{\s*"user"', re.I),
    "auth_status": re.compile(r'"authStatus"\s*:', re.I),
}


class ExtractionError(RuntimeError):
    pass


def _extract_js_string(src: str, marker_pos: int) -> str:
    start = marker_pos + len(ENQUEUE_MARKER)
    escaped = False
    i = start
    while i < len(src):
        ch = src[i]
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == '"' and src.startswith('");', i):
            return src[start:i]
        i += 1
    raise ExtractionError("unterminated React Router enqueue string")


def _decode_enqueue_payload(raw: str) -> Any:
    # The enqueue argument is a JavaScript/JSON string literal containing JSON text.
    decoded_text = json.loads('"' + raw + '"')
    return json.loads(decoded_text)


def _revive_flat(values: list[Any]) -> Any:
    """Revive React Router's flattened indexed representation.

    Object keys of the form "_123" refer to values[123] for the actual key string.
    Object values and array entries are integer references into the same values array.
    Negative integers are transport sentinels; they are retained as explicit markers.
    """
    memo: dict[int, Any] = {}
    special = {
        -1: "$UNDEFINED",
        -2: "$HOLE",
        -3: "$NAN",
        -4: "$POSITIVE_INFINITY",
        -5: "$NEGATIVE_INFINITY",
        -6: "$NEGATIVE_ZERO",
    }

    def decode_key(key: str) -> str:
        m = re.fullmatch(r"_(\d+)", key)
        if not m:
            return key
        idx = int(m.group(1))
        if 0 <= idx < len(values) and isinstance(values[idx], str):
            return values[idx]
        return key

    def decode_ref(ref: Any) -> Any:
        if isinstance(ref, bool):
            return ref
        if isinstance(ref, int):
            if ref < 0:
                return special.get(ref, f"$SPECIAL_{ref}")
            return decode_index(ref)
        return ref

    def decode_index(idx: int) -> Any:
        if idx in memo:
            return memo[idx]
        if not (0 <= idx < len(values)):
            return f"$BAD_REF_{idx}"
        value = values[idx]
        if isinstance(value, list):
            out: list[Any] = []
            memo[idx] = out
            out.extend(decode_ref(x) for x in value)
            return out
        if isinstance(value, dict):
            out: dict[str, Any] = {}
            memo[idx] = out
            for key, ref in value.items():
                out[decode_key(key)] = decode_ref(ref)
            return out
        return value

    return decode_index(0)


def _find_share_data(root: Any) -> dict[str, Any]:
    # Fast canonical path.
    if isinstance(root, dict):
        loader = root.get("loaderData")
        if isinstance(loader, dict):
            for item in loader.values():
                if not isinstance(item, dict):
                    continue
                server = item.get("serverResponse")
                if isinstance(server, dict):
                    data = server.get("data")
                    if isinstance(data, dict) and isinstance(data.get("linear_conversation"), list):
                        return data

    # Defensive recursive fallback.
    seen: set[int] = set()

    def walk(obj: Any) -> dict[str, Any] | None:
        if isinstance(obj, (dict, list)):
            oid = id(obj)
            if oid in seen:
                return None
            seen.add(oid)
        if isinstance(obj, dict):
            if isinstance(obj.get("linear_conversation"), list) and "mapping" in obj:
                return obj
            for v in obj.values():
                got = walk(v)
                if got:
                    return got
        elif isinstance(obj, list):
            for v in obj:
                got = walk(v)
                if got:
                    return got
        return None

    found = walk(root)
    if not found:
        raise ExtractionError("share conversation payload not found")
    return found


def _load_share_data(page: str) -> dict[str, Any]:
    positions = [m.start() for m in re.finditer(re.escape(ENQUEUE_MARKER), page)]
    if not positions:
        raise ExtractionError("React Router enqueue payload not found")

    errors: list[str] = []
    for pos in positions:
        try:
            raw = _extract_js_string(page, pos)
            if "linear_conversation" not in raw:
                continue
            flat = _decode_enqueue_payload(raw)
            if not isinstance(flat, list):
                continue
            return _find_share_data(_revive_flat(flat))
        except Exception as exc:  # keep trying other stream chunks
            errors.append(f"{type(exc).__name__}: {exc}")

    suffix = f"; errors={errors[:3]}" if errors else ""
    raise ExtractionError("no usable shared-conversation payload found" + suffix)


def _iso_time(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "UNKNOWN_TIME"
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    except Exception:
        return "UNKNOWN_TIME"


def _part_to_text(part: Any, message_id: str, counters: dict[str, int]) -> str:
    if isinstance(part, str):
        return part
    counters["non_text_parts"] += 1
    part_type = "unknown"
    if isinstance(part, dict):
        part_type = str(part.get("content_type") or part.get("type") or "object")
        # Some multimodal text pieces still carry a plain text field.
        for key in ("text", "content"):
            value = part.get(key)
            if isinstance(value, str) and value:
                return value
    return f"[NON_TEXT_PART type={part_type}; source_message_id={message_id}; inspect original source if material]"


def extract_messages(data: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    linear = data.get("linear_conversation")
    if not isinstance(linear, list):
        raise ExtractionError("linear_conversation missing")

    counters = {
        "linear_nodes": len(linear),
        "messages_emitted": 0,
        "excluded_non_user_assistant": 0,
        "nodes_without_message": 0,
        "non_text_parts": 0,
    }
    messages: list[dict[str, Any]] = []

    for node in linear:
        if not isinstance(node, dict):
            counters["nodes_without_message"] += 1
            continue
        msg = node.get("message")
        if not isinstance(msg, dict):
            counters["nodes_without_message"] += 1
            continue

        author = msg.get("author")
        role = author.get("role") if isinstance(author, dict) else None
        if role not in ROLE_ALLOW:
            counters["excluded_non_user_assistant"] += 1
            continue

        content = msg.get("content")
        parts: list[Any] = []
        content_type = None
        if isinstance(content, dict):
            content_type = content.get("content_type")
            p = content.get("parts")
            if isinstance(p, list):
                parts = p
            elif isinstance(p, str):
                parts = [p]

        message_id = str(node.get("id") or msg.get("id") or "UNKNOWN_MESSAGE_ID")
        body_parts = [_part_to_text(p, message_id, counters) for p in parts]
        body = "\n".join(x for x in body_parts if x is not None).strip()

        # Preserve empty USER/ASSISTANT nodes explicitly rather than fabricating text.
        if not body:
            body = "[EMPTY_MESSAGE_CONTENT]"

        messages.append(
            {
                "sequence": len(messages) + 1,
                "source_node_id": message_id,
                "role": role.upper(),
                "create_time_utc": _iso_time(msg.get("create_time")),
                "content_type": content_type or "unknown",
                "text": body,
            }
        )
        counters["messages_emitted"] += 1

    return messages, counters


def render_markdown(data: dict[str, Any], messages: list[dict[str, Any]], counters: dict[str, int], source_name: str) -> str:
    title = str(data.get("title") or "Untitled shared conversation")
    share_id = str(data.get("conversation_id") or "UNKNOWN_SHARE_ID")
    backing = str(data.get("backing_conversation_id") or "UNKNOWN_BACKING_ID")
    lines = [
        f"# SANITIZED CHATGPT TRANSCRIPT — {title}",
        "",
        "STATUS: TRANSCRIPT_ONLY / NOTEBOOKLM_INPUT_CANDIDATE",
        "AUTHORITY: DERIVED_FROM_SAVED_SHARE_PAGE / ORIGINAL HTML RETAINED SEPARATELY",
        f"SOURCE_FILE: {source_name}",
        f"SHARE_CONVERSATION_ID: {share_id}",
        f"BACKING_CONVERSATION_ID: {backing}",
        "SCOPE: SAVED PAGE linear_conversation; USER↔ASSISTANT only",
        "EXCLUDED: SYSTEM / DEVELOPER / TOOL / bootstrap / session / authentication / application state",
        "CLAIM_BOUNDARY: This transcript does not prove complete account-history coverage.",
        f"LINEAR_NODES: {counters['linear_nodes']}",
        f"USER_ASSISTANT_MESSAGES: {counters['messages_emitted']}",
        f"EXCLUDED_NON_USER_ASSISTANT_MESSAGES: {counters['excluded_non_user_assistant']}",
        f"NODES_WITHOUT_MESSAGE: {counters['nodes_without_message']}",
        f"NON_TEXT_PART_MARKERS: {counters['non_text_parts']}",
        "",
        "---",
        "",
    ]
    for m in messages:
        lines.extend(
            [
                f"## [{m['sequence']:04d}] {m['role']} — {m['create_time_utc']}",
                f"SOURCE_NODE_ID: {m['source_node_id']}",
                f"CONTENT_TYPE: {m['content_type']}",
                "",
                m["text"],
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def safety_scan(output: str) -> list[str]:
    return [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(output)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html_file", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()

    page = args.html_file.read_text(encoding="utf-8", errors="replace")
    data = _load_share_data(page)
    messages, counters = extract_messages(data)
    if not messages:
        raise ExtractionError("no USER/ASSISTANT messages emitted")

    out = render_markdown(data, messages, counters, args.html_file.name)
    findings = safety_scan(out)
    if findings:
        raise ExtractionError("sanitized output failed security scan: " + ", ".join(findings))

    if args.output:
        args.output.write_text(out, encoding="utf-8")
        print(f"PASS: {args.output} messages={len(messages)} non_text_parts={counters['non_text_parts']}")
    else:
        print(out, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
