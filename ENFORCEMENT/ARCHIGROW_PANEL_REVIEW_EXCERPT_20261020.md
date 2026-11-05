# Verbatim narrow code-review excerpt. Not canonical source; independent review only.
## TOOLS/ARCHIGROW_PANEL_WORKFLOW.py SHA256 e8fdf945b7983f4a1a853800b321af6dae03fcf455343a89203d4af5cdcb1ace
### Lines 596-701
0596:         "segmentation": {"method": "RULE_BASED_FROM_BUILD_MANIFEST",
0597:                          "note": "Blocks follow the builder's grid slots; rects are CSS-grid estimates, not measured. Not vision-based."},
0598:         "ai_disclosure": AI_DISCLOSURE,
0599:         "source_gaps": [b["block_id"] for b in blocks if b["binding_status"] != "BOUND"],
0600:         "blocks": blocks,
0601:     }
0602:     return doc
0603: 
0604: # ---------------------------------------------------------------- facts (anti-hallucination)
0605: 
0606: 
0607: NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
0608: TEXT_SOURCE_SUFFIX = {".txt", ".md", ".csv", ".tsv", ".json"}
0609: QUANTITY_KINDS = [("AREA", r"㎡|m²|m2|평"), ("RATIO", r"%|퍼센트|배"), ("COUNT", r"대|세대|호|층|개|명|실"),
0610:                   ("LENGTH", r"mm|cm|km|m(?![a-z²2])")]
0611: FACT_ROLES = {"PROJECT_FACT", "DERIVED", "BOARD_STATED", "INTERPRETATION", "EDITORIAL", "UNKNOWN"}
0612: BOARD_STATED_TAG = " (보드 기재·미검증)"
0613: MUST_OWNERS = {"BRIEF", "OFFICIAL_RULE", "USER"}
0614: 
0615: 
0616: def classify_numeric(text):
0617:     """Numeric claim classification: which numbers a statement carries and what kind of quantity they look like."""
0618:     text = str(text or "")
0619:     numbers = [n.replace(",", "") for n in NUMBER_RE.findall(text)]
0620:     kinds = [k for k, pattern in QUANTITY_KINDS if re.search(pattern, text)]
0621:     return {"is_numeric": bool(numbers), "numbers": numbers, "quantity_kinds": kinds}
0622: 
0623: 
0624: def verify_source_proof(entry, base_dir=None):
0625:     """A source_ref label proves nothing. Proof = an existing file whose sha256 equals the declared revision hash."""
0626:     ref = entry.get("source_file")
0627:     if not ref:
0628:         return {"status": "NO_SOURCE_FILE"}
0629:     path = Path(str(ref))
0630:     if not path.is_absolute() and base_dir:
0631:         path = Path(base_dir) / path
0632:     if not path.is_file():
0633:         return {"status": "SOURCE_FILE_MISSING", "path": str(path)}
0634:     actual = sha256_file(path)
0635:     declared = str(entry.get("source_sha256") or "").strip().lower()
0636:     if not re.fullmatch(r"[0-9a-f]{64}", declared):
0637:         return {"status": "NO_REVISION_HASH", "path": str(path), "actual_sha256": actual}
0638:     if declared != actual:
0639:         return {"status": "SOURCE_HASH_MISMATCH", "path": str(path), "declared_sha256": declared, "actual_sha256": actual}
0640:     return {"status": "HASH_VERIFIED", "path": str(path), "sha256": actual}
0641: 
0642: 
0643: def _cross_check_numbers(proof, numbers):
0644:     """Text-like sources must literally contain every number the claim states. Binary sources are not checked."""
0645:     path = Path(proof["path"])
0646:     if path.suffix.lower() not in TEXT_SOURCE_SUFFIX:
0647:         return "NOT_CHECKED_BINARY_SOURCE", []
0648:     source_text = path.read_text(encoding="utf-8", errors="replace")
0649:     present = {n.replace(",", "") for n in NUMBER_RE.findall(source_text)}
0650:     missing = [n for n in numbers if n not in present]
0651:     return ("NUMBERS_FOUND_IN_TEXT_SOURCE" if not missing else "NUMBER_NOT_IN_SOURCE"), missing
0652: 
0653: 
0654: def _fact_entry(f):
0655:     entry = dict(f)
0656:     if isinstance(f.get("source_ref"), dict):
0657:         entry.update(f["source_ref"])
0658:     label = entry.get("label") or (f.get("source_ref") if isinstance(f.get("source_ref"), str) else None) or entry.get("source_file")
0659:     return entry, (str(label) if label else "")
0660: 
0661: 
0662: def load_facts(path, valid_block_ids):
0663:     """Fact authority is proven, never assumed.
0664: 
0665:     VERIFIED   = existing source file + declared sha256 equal to the real file hash (+ numbers found when the source is text).
0666:     BOARD_STATED (UNVERIFIED) = labelled or explicitly board-stated claim without proof; numeric ones are accepted only when
0667:                  the author declares claim_role BOARD_STATED, and they are always rendered with a visible tag.
0668:     Everything else is HOLD with an explicit reason. A non-blank source_ref string alone NEVER grants VERIFIED.
0669:     """
0670:     accepted, held = [], []
0671:     if not path:
0672:         return accepted, held
0673:     data = read_json(path)
0674:     items = data.get("facts", []) if isinstance(data, dict) else data
0675:     valid = set(valid_block_ids)
0676:     base_dir = Path(path).parent
0677:     for f in items:
0678:         fid, text = f.get("id"), f.get("text")
0679:         ids = [b for b in (f.get("block_ids") or []) if b in valid]
0680:         entry, label = _fact_entry(f)
0681:         if not (fid and text):
0682:             held.append({"id": fid, "text": text, "reason": "INCOMPLETE"})
0683:             continue
0684:         if not ids:
0685:             held.append({"id": fid, "text": text, "reason": "NO_KNOWN_BLOCK"})
0686:             continue
0687:         numeric = classify_numeric(text)
0688:         proof = verify_source_proof(entry, base_dir)
0689:         role_in = str(f.get("claim_role") or "").upper()
0690:         record = {"id": str(fid), "text": str(text), "source_ref": label, "block_ids": ids, "numeric": numeric,
0691:                   "source_proof": {k: v for k, v in proof.items() if k != "path"}}
0692:         if proof["status"] == "HASH_VERIFIED":
0693:             cross, missing = _cross_check_numbers(proof, numeric["numbers"]) if numeric["is_numeric"] else ("NO_NUMBERS", [])
0694:             if missing:
0695:                 held.append({"id": fid, "text": text, "reason": "NUMBER_NOT_IN_SOURCE:" + ",".join(missing)})
0696:                 continue
0697:             record.update({"claim_role": role_in if role_in in FACT_ROLES - {"BOARD_STATED"} else "PROJECT_FACT",
0698:                            "authority": "VERIFIED", "cross_check": cross})
0699:             accepted.append(record)
0700:             continue
0701:         if proof["status"] == "SOURCE_HASH_MISMATCH":
### Lines 739-832
0739:             binding = "USER_REQUEST"
0740:         items.append({"id": str(mid), "label": str(m.get("label") or m.get("block_id") or m.get("mode")), "owner": owner,
0741:                       "binding": binding, "block_id": m.get("block_id"), "mode": m.get("mode"),
0742:                       "evidence_status": proof["status"], "version": m.get("version")})
0743:     return items, rejected
0744: 
0745: 
0746: BINDING_RANK = {"VERIFIED_MANDATORY": 0, "CLAIMED_MANDATORY_UNVERIFIED": 1, "USER_REQUEST": 2}
0747: BINDING_LABEL_KO = {"VERIFIED_MANDATORY": "공식·검증 필수", "CLAIMED_MANDATORY_UNVERIFIED": "필수 주장(증빙 미검증)",
0748:                     "USER_REQUEST": "사용자 요청(법적 구속 아님)"}
0749: HARD_FLOOR_SEC = 15
0750: 
0751: 
0752: def plan_must_show(blocks, bound, must_show, content_budget_sec):
0753:     """Decide which MUST_SHOW units get a slide. Nothing is silently dropped.
0754: 
0755:     A unit is a bound block (items sharing a block merge) or a PLACEHOLDER (no bound source block: shown, no numbers).
0756:     Capacity is the hard per-slide floor, not the density target; units beyond it are INFEASIBLE_AT_DURATION.
0757:     """
0758:     items = [dict(m) for m in (must_show or [])]
0759:     known = {m["id"] for m in items}
0760:     for b in blocks:  # an arbitrary per-block boolean is a user request, never binding law
0761:         if b.get("must_show") is True and ("BLOCKFLAG:" + b["block_id"]) not in known:
0762:             items.append({"id": "BLOCKFLAG:" + b["block_id"], "label": b.get("title_ko") or b["block_id"], "owner": "USER",
0763:                           "binding": "USER_REQUEST", "block_id": b["block_id"], "mode": None, "evidence_status": "NO_SOURCE_FILE",
0764:                           "version": None})
0765:     items.sort(key=lambda m: BINDING_RANK.get(m.get("binding"), 2))
0766:     units, by_block = [], {}
0767:     for it in items:
0768:         cand = None
0769:         if it.get("block_id"):
0770:             cand = next((b for b in bound if b["block_id"] == it["block_id"]), None)
0771:         elif it.get("mode"):
0772:             cand = next((b for b in bound if b.get("mode") == it["mode"]), None)
0773:         if cand is not None:
0774:             if cand["block_id"] in by_block:
0775:                 by_block[cand["block_id"]]["items"].append(it)
0776:             else:
0777:                 unit = {"kind": "BLOCK", "block": cand, "items": [it]}
0778:                 by_block[cand["block_id"]] = unit
0779:                 units.append(unit)
0780:         else:
0781:             units.append({"kind": "PLACEHOLDER", "block": None, "items": [it]})
0782:     capacity = max(0, int(content_budget_sec // HARD_FLOOR_SEC))
0783:     kept, dropped = units[:capacity], units[capacity:]
0784:     report = []
0785:     for unit, status in [(u, None) for u in kept] + [(u, "INFEASIBLE_AT_DURATION") for u in dropped]:
0786:         for it in unit["items"]:
0787:             report.append({"id": it["id"], "label": it["label"], "owner": it["owner"], "binding": it["binding"],
0788:                            "binding_label_ko": BINDING_LABEL_KO.get(it["binding"], ""), "block_id": unit["block"]["block_id"] if unit["block"] else None,
0789:                            "status": status or ("PLACED" if unit["kind"] == "BLOCK" else "PLACEHOLDER_SOURCE_UNVERIFIED")})
0790:     return {
0791:         "input_ids": [it["id"] for it in items],
0792:         "forced_blocks": [u["block"] for u in kept if u["kind"] == "BLOCK"],
0793:         "tags": {u["block"]["block_id"]: [it["id"] for it in u["items"]] for u in kept if u["kind"] == "BLOCK"},
0794:         "placeholders": [u["items"] for u in kept if u["kind"] == "PLACEHOLDER"],
0795:         "report": report,
0796:         "omitted_ids": [it["id"] for u in dropped for it in u["items"]],
0797:         "unit_count": len(units),
0798:     }
0799: 
0800: # ---------------------------------------------------------------- deck planning
0801: 
0802: 
0803: def find_slide_image(block, raster_dir=None):
0804:     """PPTX can embed PNG/JPEG only. Returns (path, sha256, hold_reason)."""
0805:     crop = block.get("crop_path")  # region crop written by ARCHIGROW_PANEL_SOURCE_EXTRACT.py
0806:     if crop and Path(crop).exists():
0807:         return str(crop), sha256_file(crop), None
0808:     src = block.get("source_path")
0809:     if src and Path(src).suffix.lower() in {".png", ".jpg", ".jpeg"} and Path(src).exists():
0810:         return str(src), sha256_file(src), None
0811:     if src and raster_dir:
0812:         stem = Path(src).stem
0813:         for ext in (".png", ".jpg", ".jpeg"):
0814:             cand = Path(raster_dir) / (stem + ext)
0815:             if cand.exists():
0816:                 return str(cand), sha256_file(cand), None
0817:     return None, None, "NO_PNG_JPEG_DERIVATIVE_FOR_PPTX"
0818: 
0819: 
0820: def _time_split(total, weights, floor=15):
0821:     """Integer seconds in steps of 5 that sum exactly to total."""
0822:     if not weights:
0823:         return []
0824:     raw = [max(floor, int(round(total * w / sum(weights) / 5.0)) * 5) for w in weights]
0825:     diff = total - sum(raw)
0826:     order = sorted(range(len(raw)), key=lambda i: -weights[i])
0827:     i = 0
0828:     while diff != 0 and i < 1000:
0829:         k = order[i % len(order)]
0830:         step = 5 if diff > 0 else -5
0831:         if raw[k] + step >= floor:
0832:             raw[k] += step
## TOOLS/ARCHIGROW_PANEL_SOURCE_EXTRACT.py SHA256 9bcf9b1d10cd8251975c0cbb9862fdae419c23836cf27e59e21b2a63ef21c5d5
### Lines 185-225
0185:     doc = fitz.open(str(path))
0186:     pages = []
0187:     try:
0188:         for index in range(doc.page_count):
0189:             page = doc[index]
0190:             page_no = index + 1
0191:             rect = page.rect  # visual frame: rotation + cropbox applied, origin top-left, PDF points
0192:             width, height = float(rect.width), float(rect.height)
0193:             derot = page.derotation_matrix
0194:             rot = page.rotation_matrix
0195:             sink = RegionSink(page_no, width, height, "pt", source_sha)
0196: 
0197:             def visual_bbox(b):
0198:                 # PyMuPDF returns PDF object rectangles in unrotated coordinates;
0199:                 # only Page.rect uses the displayed (rotated) page frame.
0200:                 q = fitz.Rect(*b) * rot
0201:                 return (q.x0, q.y0, q.x1, q.y1)
0202: 
0203:             def unrotated(b):
0204:                 return {"bbox_unrotated_pdf_pt": native_bbox(*b)}
0205: 
0206:             # text layer
0207:             for bi, block in enumerate(page.get_text("dict").get("blocks", [])):
0208:                 if block.get("type") != 0:
0209:                     continue
0210:                 text = "\n".join("".join(span.get("text", "") for span in line.get("spans", []))
0211:                                  for line in block.get("lines", [])).strip()
0212:                 if not text:
0213:                     continue
0214:                 bb = block["bbox"]
0215:                 sink.add("TEXT", visual_bbox(bb), f"P{page_no}-TXT-{block.get('number', bi)}", method_text, 0.95, text=text,
0216:                          native_ref={"text_block": block.get("number", bi)}, bbox_native_extra=unrotated(bb))
0217:             # embedded images
0218:             for ii, info in enumerate(page.get_image_info(xrefs=True)):
0219:                 bb = info["bbox"]
0220:                 sink.add("IMAGE", visual_bbox(bb), f"P{page_no}-IMG-{info.get('xref') or ii}-{ii}", method_img, 0.95,
0221:                          native_ref={"xref": info.get("xref"), "pixel_width": info.get("width"), "pixel_height": info.get("height")},
0222:                          bbox_native_extra=unrotated(bb))
0223:             # vector drawings -> clusters (extent measured, meaning unknown)
0224:             drawings = page.get_drawings()
0225:             truncated = len(drawings) > MAX_DRAWINGS
