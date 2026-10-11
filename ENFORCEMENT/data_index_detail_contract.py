#!/usr/bin/env python3
"""Validate staged PDF/image/video DETAIL coordinates; no original content stored."""
from __future__ import annotations
import math
from typing import Any
from urllib.parse import urlsplit

SCHEMA = "TAKY_INDEX_DETAIL_COORDINATE_CANDIDATE_V1"
METHODS = {"PDF": "RENDERED_PAGE_VISUAL", "IMAGE": "ORIGINAL_IMAGE_VISUAL", "VIDEO": "DECODED_FRAME_VISUAL"}

def positive(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(label + "_INVALID")
    return value

def required(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + "_REQUIRED")
    return value.strip()

def validate_detail_candidate(c: dict) -> dict:
    if not isinstance(c, dict) or c.get("schema") != SCHEMA:
        raise ValueError("SCHEMA_INVALID")
    source_id = required(c.get("source_id"), "SOURCE_ID")
    locator = required(c.get("original_locator"), "LOCATOR")
    uri = urlsplit(locator)
    if uri.scheme != "https" or not uri.netloc:
        raise ValueError("LOCATOR_INVALID")
    modality = c.get("modality")
    if modality not in METHODS:
        raise ValueError("MODALITY_INVALID")
    if c.get("coverage") != "PARTIAL_REVIEWED_UNIT":
        raise ValueError("COVERAGE_OVERCLAIM")
    methods = c.get("inspection_methods")
    if not isinstance(methods, list) or METHODS[modality] not in methods:
        raise ValueError("VISUAL_METHOD_REQUIRED")
    required(c.get("observed_at"), "OBSERVED_AT")
    required(c.get("extract_recipe"), "RECIPE")
    required(c.get("evidence_note"), "EVIDENCE_NOTE")
    pos = c.get("coordinate")
    if not isinstance(pos, dict):
        raise ValueError("COORDINATE_INVALID")
    if modality == "PDF":
        p = positive(pos.get("physical_page_1based"), "PHYSICAL_PAGE")
        n = positive(pos.get("document_page_count"), "PAGE_COUNT")
        ix = pos.get("pdf_index_0based")
        if isinstance(ix, bool) or not isinstance(ix, int) or ix != p-1 or p > n:
            raise ValueError("PDF_PAGE_INDEX_MISMATCH")
        required(pos.get("section_heading"), "SECTION_HEADING")
        lab = pos.get("printed_page_label")
        if lab is not None:
            required(lab, "PRINTED_PAGE_LABEL")
    elif modality == "IMAGE":
        w = positive(pos.get("width_px"), "IMAGE_WIDTH")
        h = positive(pos.get("height_px"), "IMAGE_HEIGHT")
        box = pos.get("pixel_region")
        if not isinstance(box, list) or len(box) != 4 or any(isinstance(v,bool) or not isinstance(v,int) for v in box):
            raise ValueError("PIXEL_REGION_INVALID")
        x,y,bw,bh = box
        if x < 0 or y < 0 or bw < 1 or bh < 1 or x+bw > w or y+bh > h:
            raise ValueError("PIXEL_REGION_OUTSIDE")
        if pos.get("carousel_slide") is not None:
            positive(pos["carousel_slide"], "SLIDE_NUMBER")
        if pos.get("carousel_total") is not None:
            positive(pos["carousel_total"], "CAROUSEL_TOTAL")
            if pos.get("carousel_slide") is not None and pos["carousel_slide"] > pos["carousel_total"]:
                raise ValueError("SLIDE_OUTSIDE")
    else:
        duration,t = pos.get("duration_seconds"),pos.get("timestamp_seconds")
        if any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) for v in (duration,t)):
            raise ValueError("VIDEO_TIME_INVALID")
        if duration <= 0 or not 0 <= t < duration:
            raise ValueError("VIDEO_TIME_OUTSIDE")
        positive(pos.get("frame_width_px"), "FRAME_WIDTH")
        positive(pos.get("frame_height_px"), "FRAME_HEIGHT")
    return {
        "schema": SCHEMA, "source_id":source_id, "original_locator":locator,
        "modality":modality, "coordinate":pos, "inspection_methods":methods,
        "evidence_note":c["evidence_note"], "observed_at":c["observed_at"],
        "extract_recipe":c["extract_recipe"], "coverage":"PARTIAL_REVIEWED_UNIT",
        "state":"DETAIL_CANDIDATE_REVIEWED_NOT_CURRENT",
        "complete_source_review":False, "current_promoted":False,
    }
