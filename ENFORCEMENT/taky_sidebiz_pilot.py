#!/usr/bin/env python3
"""TAKY-004 small offline CPA/micro-app economics checker.

This is a pure calculator, NOT a payout verifier, ad poster or new scheduler.
No external calls, secrets, shared user data, or canonical state updates.
"""
from __future__ import annotations
import argparse
import json
import hashlib
import re
from pathlib import Path
from bs4 import BeautifulSoup

SCHEMA = "TAKY_SIDE_INCOME_PILOT_V1"
LIMIT = 1_000_000_000

DEMO = {
    "schema": SCHEMA, "work_id": "TAKY-004", "pilot_id": "DEMO-CPA-001",
    "mode": "DEMO", "lane": "CPA",
    "views": 1000, "clicks": 50, "applications": 3, "approved": 1,
    "reward_per_approval_krw": 20000, "cash_received_krw": None,
    "ad_spend_krw": 0, "other_cost_krw": 0, "refunds_krw": 0,
    "owner_minutes": 90
}


def _number(data: dict, key: str, nullable: bool = False) -> int | None:
    value = data.get(key)
    if nullable and value is None:
        return None
    if type(value) is not int or not 0 <= value <= LIMIT:
        raise ValueError("INVALID_NONNEGATIVE_INTEGER:" + key)
    return value


def evaluate(data: dict) -> dict:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("INVALID_SCHEMA")
    if data.get("work_id") != "TAKY-004":
        raise ValueError("WORK_ID_MISMATCH")
    if data.get("mode") not in ("DEMO", "MANUAL"):
        raise ValueError("MODE_INVALID")
    if data.get("lane") not in ("CPA", "MICRO_APP"):
        raise ValueError("LANE_INVALID")
    pilot_id = data.get("pilot_id")
    if not isinstance(pilot_id, str) or not pilot_id or len(pilot_id) > 80:
        raise ValueError("PILOT_ID_INVALID")
    values = {k: _number(data, k) for k in (
        "views", "clicks", "applications", "approved",
        "reward_per_approval_krw", "ad_spend_krw",
        "other_cost_krw", "refunds_krw", "owner_minutes")}
    cash = _number(data, "cash_received_krw", nullable=True)
    if not (values["approved"] <= values["applications"] <=
            values["clicks"] <= values["views"]):
        raise ValueError("FUNNEL_COUNT_INCONSISTENT")
    anticipated = values["approved"] * values["reward_per_approval_krw"]
    if cash is not None and cash > anticipated:
        raise ValueError("CASH_EXCEEDS_THIS_PILOT_APPROVED_VALUE")
    cost = (values["ad_spend_krw"] + values["other_cost_krw"]
            + values["refunds_krw"])
    net_cash = cash - cost if cash is not None else None
    minutes = values["owner_minutes"]
    return {
        "schema": "TAKY_SIDE_INCOME_PILOT_RESULT_V1",
        "work_id": "TAKY-004", "pilot_id": pilot_id,
        "mode": data["mode"], "lane": data["lane"],
        "estimated_approved_value_krw": anticipated,
        "reported_cash_received_krw": cash,
        "known_total_cost_krw": cost,
        "net_cash_krw": net_cash,
        "hourly_cash_net_krw": (round(net_cash * 60 / minutes, 2)
                               if net_cash is not None and minutes else None),
        "click_through_rate_pct": (round(values["clicks"] * 100 / values["views"], 2)
                                   if values["views"] else None),
        "approval_per_application_pct": (
            round(values["approved"] * 100 / values["applications"], 2)
            if values["applications"] else None),
        "status": ("DEMO_ONLY" if data["mode"] == "DEMO" else
                   "CASH_NOT_REPORTED" if cash is None else
                   "CASH_REPORTED_NOT_INDEPENDENTLY_VERIFIED"),
        "verified_real_income": False,
        "notes": "Manual numbers are not bank-verified. Approval != cash settlement.",
    }


def scan_adpot_notices(raw: bytes, term: str = "") -> dict:
    """Review a saved PUBLIC Adpot notice-list HTML snapshot; never claim ad permission."""
    if not isinstance(raw, bytes) or not raw or len(raw) > 600000:
        raise ValueError("NOTICE_SOURCE_INVALID_OR_TOO_LARGE")
    if not isinstance(term, str) or len(term) > 80:
        raise ValueError("NOTICE_TERM_INVALID")
    html = raw.decode("utf-8-sig")
    soup = BeautifulSoup(html, "html.parser")
    notices = []
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) != 3:
            continue
        number = cells[0].get_text(" ", strip=True)
        date = cells[2].get_text(" ", strip=True)
        link = cells[1].find("a", href=True)
        if not number.isdigit() or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", date) or link is None:
            continue
        href = link.get("href", "")
        match = re.search(r"notice_view\.html\?code=(\d+)", href)
        if match is None:
            continue
        title = link.get_text(" ", strip=True)
        if not title or (term and term.casefold() not in title.casefold()):
            continue
        if "캠페인종료" in title or "캠페인 종료" in title:
            risk = "STOP_NOTICE"
        elif any(word in title for word in ("일시중지", "캠페인 중단", "미운영", "일시 중단")):
            risk = "PAUSE_NOTICE"
        elif any(word in title for word in ("변경", "단가 상향", "운영일정", "미운영", "타겟", "불가매체", "금지", "주의")):
            risk = "TERMS_CHANGED_RECHECK"
        elif any(word in title for word in ("재개", "재등록", "공개 전환")):
            risk = "REOPEN_UNVERIFIED"
        elif "신규등록" in title:
            risk = "NEW_OFFER_UNVERIFIED"
        else:
            risk = "NOTICE_REVIEW"
        notices.append({
            "notice_id": int(number),
            "date": date,
            "title": title,
            "public_url": "https://adpot.kr/pc/center/notice_view.html?code=" + match.group(1),
            "risk": risk,
        })
    if not notices:
        raise ValueError("NO_MATCHING_PUBLIC_NOTICES")
    notices.sort(key=lambda item: item["notice_id"], reverse=True)
    return {
        "schema": "TAKY004_PUBLIC_NOTICE_SCAN_V1",
        "work_id": "TAKY-004",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "term": term,
        "notice_count": len(notices),
        "notices": notices,
        "member_campaign_status": "UNKNOWN_NEEDS_CURRENT_CAMPAIGN_TERMS",
        "paid_ads_allowed": False,
        "next_step": "HUMAN_REVIEW_CURRENT_CAMPAIGN_TERMS_BEFORE_SPEND",
        "source_type": "PUBLIC_NOTICE_ONLY_NO_LOGIN_OR_NETWORK",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="TAKY-004 offline income pilot")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--demo", action="store_true")
    group.add_argument("--input", type=Path)
    group.add_argument("--notice-html", type=Path, help="Saved official public notice list; no network")
    parser.add_argument("--term", default="", help="Optional case-insensitive campaign keyword")
    args = parser.parse_args()
    try:
        if args.notice_html is not None:
            file = args.notice_html.resolve(strict=True)
            if not file.is_file() or file.stat().st_size > 600000:
                raise ValueError("NOTICE_SOURCE_INVALID_OR_TOO_LARGE")
            result = scan_adpot_notices(file.read_bytes(), term=args.term)
        else:
            if args.term:
                raise ValueError("NOTICE_TERM_REQUIRES_NOTICE_HTML")
            if args.demo:
                data = DEMO
            else:
                file = args.input.resolve(strict=True)
                if not file.is_file() or file.stat().st_size > 32768:
                    raise ValueError("INPUT_FILE_SIZE_OR_TYPE_INVALID")
                data = json.loads(file.read_text(encoding="utf-8-sig"))
            result = evaluate(data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
