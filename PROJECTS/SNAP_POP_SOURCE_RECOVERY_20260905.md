# SNAP & POP — TAKY SOURCE RECOVERY / GOLDEN REFERENCE FREEZE
Date: 2026-09-05
State: VALIDATED RECOVERY CANDIDATE
Release: NOT RELEASED

## 1. Recovered Golden Reference

GR_ID: `SNAP_POP_GOLDEN_REFERENCE_01`

Canonical visual baseline recovered:
- File: `아이디어 탐험대 판타지 RPG UI 모음.png`
- Library file id: `file_00000000ab2c8206b0dc6620f939ff10`
- SHA-256: `ca6a597539ec40f3a81ee527e95fda4e83191ca70cc31fd47265d892cfd63b79`

Recovery evidence:
1. `Snap_Pop_V12_복구_비교표_및_명세.md` explicitly identifies `idea_expedition_v12_1_REFINED.zip` as execution baseline and `아이디어 탐험대 판타지 RPG UI 모음.png` as final UI/function baseline.
2. Multiple handoff documents record that the user selected / strongly preferred the V12 second UI concept.
3. The recovered PNG is the exact named final UI/function board described by the V12 recovery specification.

Decision:
- `PS-01 GOLDEN_REFERENCE = VERIFIED_BY_CANONICAL_RECOVERY`
- direct raw chat approval line is not currently recovered; approval provenance is preserved by independent project recovery documents.
- later failed generated boards do not supersede this baseline.

## 2. Protected State Manifest — Recovered Status

| ID | Protected State | Recovery result | Current status |
|---|---|---|---|
| PS-01 | GOLDEN_REFERENCE | exact final board + canonical docs | VERIFIED_BY_CANONICAL_RECOVERY |
| PS-02 | WORLD_MAP_GEOGRAPHY | composition visible in Golden Reference | VERIFIED_APPEARANCE / SOURCE_ASSET_MISSING |
| PS-03 | CHARACTER_MASTER | historical appearance visible; current original isolated source missing | HOLD |
| PS-04 | GUIDE_MASTER | current MASTER defines Maltipoo lineage; isolated approved source missing | HOLD |
| PS-05 | GEM_MASTER_APPROVED | five approved region gem appearances visible; isolated source missing | VERIFIED_APPEARANCE / SOURCE_ASSET_MISSING |
| PS-06 | GROWTH_TREE_MASTER | one persistent tree is locked by current MASTER; isolated source missing | HOLD |
| PS-07 | TYPOGRAPHY_DNA | hierarchy recoverable; exact production font source unresolved | PARTIAL |
| PS-08 | MATERIAL_DNA | parchment / emerald / natural material language visible | VERIFIED |
| PS-09 | NAVIGATION_DNA | 5-tab nav confirmed by MASTER and board | VERIFIED |
| PS-10 | COLOR_LIGHTING_DNA | bright sky/natural green/parchment/deep-teal confirmed | VERIFIED |
| PS-11 | LANDMARK_STATE_RULES | current MASTER overrides old default density: HOME default TITLE ONLY | VERIFIED |
| PS-12 | WALKIE_TALKIE_POSITION | right-side HARD LOCK | VERIFIED |

## 3. Golden Reference Protection

PRESERVE:
- bright daytime fantasy exploration world
- natural sky / forest / water / mountain spatial depth
- parchment + deep emerald/teal + restrained brass/gold material language
- five-landmark map relationship
- explorer-forward composition
- five region-linked gem identities
- six-shard completion logic
- bottom navigation: 지도 · 기록 · 탐험 · 보석함 · 성장
- writing-first product hierarchy

ADJUST BY CURRENT MASTER:
- HOME default landmark state = TITLE ONLY
- all five tools freely usable; no map/level unlock
- live DOM text instead of baked UI text
- no fake status bar/notch
- Character Master must be original/stable
- Guide follows current companion lineage
- Growth main screen = one current tree
- exact labels: 탐험가의 소원 상점 / 소원 사용하기 / 축복 사용하기
- ORIGINAL first; FAMILY hidden by default

REJECT:
- copying historical third-party-like character likeness
- using presentation-board crops as production runtime UI
- new shiny gem redesign
- generic SVG map replacement
- generated PASS labels as evidence

## 4. Evidence Ledger

- `E-GR-01`: exact final V12 UI/function baseline filename and role — HIGH confidence — PASS.
- `E-GR-02`: user selected second V12 UI concept — HIGH confidence / MEDIUM completeness because raw approval turn is not recovered — PASS_WITH_PROVENANCE_NOTE.
- `E-MAP-01`: map geography/material direction protected by Golden Reference + REV_10 — PASS.
- `E-GEM-01`: approved gem appearance protected; isolated source asset unresolved — HOLD_FOR_ISOLATED_SOURCE.
- `E-CHAR-01`: stable reusable Character Master required; isolated approved source unresolved — HOLD.
- `E-GUIDE-01`: current Guide lineage required; isolated approved source unresolved — HOLD.
- `E-TREE-01`: one persistent Growth Tree required; isolated approved source unresolved — HOLD.

## 5. HOME_MAP_DEFAULT Visual Delta Baseline

Protected:
- macro map geography
- bright daytime natural-light direction
- green/blue landscape balance
- parchment + deep-teal material family
- map-dominant composition
- five landmark spatial relationship
- bottom-nav DNA
- explorer-world narrative density

Required corrections:
- remove fake status/device chrome
- remove always-visible descriptions/progress/gem counts
- HOME landmark default = TITLE ONLY
- no persistent generic `탐험 시작` CTA
- do not invent Character/Guide source
- reserve right walkie-talkie position
- live DOM Korean text
- full-bleed portrait + Safe Area

Allowed refinement:
- higher environmental resolution
- natural-light refinement
- atmospheric depth
- spacing/alignment
- typography clarity
- responsive 390×844 / 393×852 / 430×932
- accessibility/touch-target correction

## 6. Gate Result

- GATE 0 MASTER + TAKY LOAD: PASS
- GATE 1 GOLDEN REFERENCE RECOVERY: PASS_WITH_PROVENANCE_NOTE
- GATE 2 VISUAL DELTA BASELINE: PASS
- PS-03 CHARACTER SOURCE: HOLD
- PS-04 GUIDE SOURCE: HOLD
- PS-05 ISOLATED GEM SOURCE: HOLD
- PS-06 GROWTH TREE SOURCE: HOLD

Therefore:
- production PWA generation remains blocked;
- Deployment UI is NOT APPROVED;
- a structural prototype may exist only with explicit placeholders and cannot become production lineage.

## 7. Next Gate

1. recover `idea_expedition_v12_1_REFINED.zip` or equivalent actual V12 asset package;
2. inspect its `assets/` tree;
3. identify map/gem/character/tree source files and checksums;
4. update PS-02~PS-06;
5. create exactly one `HOME_MAP_DEFAULT_REFINED` candidate;
6. compare it against `SNAP_POP_GOLDEN_REFERENCE_01` before advancing.
