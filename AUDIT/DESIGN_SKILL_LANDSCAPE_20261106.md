# Design skill landscape vs TAKY design gate — 2026-11-06

Status: RESEARCH RECORD (Claude independent review). Not authority. Feeds `MASTER/UI_REFERENCE_PROTOCOL.md` §20 and the design-gate harness.
Method: GitHub search via `gh`, shallow clones read (not executed), and web search. Star counts are from GitHub search on 2026-11-06.

## 1. Candidates

| Repo | ★ | License | Last push | What it is | Closest TAKY gate |
|---|---|---|---|---|---|
| nextlevelbuilder/ui-ux-pro-max-skill | 145,925 | MIT | 2026-11-05 | Searchable design database (styles, palettes, fonts) | DG-01 reference |
| Leonxlnx/taste-skill | 110,973 | MIT | 2026-11-05 | Anti-AI-look art direction, dials, reference images + browser loop | DG-05, DG-08 visual |
| alchaincyf/huashu-design | 28,854 | MIT (since 2026-05-14) | 2026-11-04 | Six thumbnails → three directions, 84+ style specimens, editable PPTX, facts-only check (type size, overflow, overlap), "look ledger" | DGC-05, DG-08 |
| pbakaus/impeccable | (not in search top) | Apache-2.0 | 2026-11-05 | `critique`/`audit` (P0–P3), **62 deterministic slop rules, no LLM**, `npx impeccable detect <url>` | GENERIC_TELLS, A11Y |
| emilkowalski/skills | (repo found by clone) | MIT | 2026-11-04 | `emil-design-eng`, `apple-design` (290 lines: response, direct manipulation, interruptibility, springs, materials), animation skills | DGC-10 Apple target |
| Jakeschincariol/replica-skill | 7,825 | MIT | 2026-10-03 | 11-skill app-clone pipeline; `replica-diff/imgdiff.py` stdlib layout diff (edge-map grid, colour-blind), `parity.py` | DG-08 visual compare (C-12) |
| JimLiu/baoyu-design | 6,151 | other | 2026-11-05 | Claude Design as a local skill | — |
| OpenCoworkAI/open-codesign | 8,166 | MIT | 2026-11-04 | Open Claude Design alternative app | — |
| mapbox/pixelmatch | 7,012 | ISC | 2026-10-06 | Pixel diff library | DG-08 regression |
| garris/BackstopJS | 7,198 | MIT | 2026-10-10 | Visual regression runner | DG-08 regression |

Directory listings quote replica-skill at 6.1k–7.5k stars, which is older data; the GitHub figure above is current. The third-party "security scores" are automated scans, not audits. One flags runtime package install in `replica-test`.

## 2. Findings

1. **The harness gap is visual compare against an approved reference (prior C-12).** `replica-diff/imgdiff.py` closes it with the right semantics: layout mode compares structure and ignores colour, `--mode pixel` is for self-regression, and height differences are reported. It is pure stdlib with no install. pixelmatch and BackstopJS are heavier alternatives.
2. **GENERIC_TELLS can get a real backend.** Impeccable's 62 deterministic rules run on a rendered URL. It stays advisory (DGC-12), and the license is Apache-2.0 (NOTICE file must be kept).
3. **The Notion item "애플 디자인 스킬" (RVR-28, SOURCE_NOT_RECOVERED) has a public source.** `emilkowalski/skills/skills/apple-design` (MIT). Use it as an Apple-target motion/interaction reference (§5 platform guidance), not as project authority.
4. **External practice matches DGC-05.** Huashu's "six thumbnails → three directions" and taste-skill's reference-image approach support the candidate-minimum rule.
5. **replica-skill as a whole conflicts with §7** ("do not copy a third-party product's branded composition wholesale"): its purpose is cloning a named app. Only the diff tooling is relevant.
6. **Installing any of these still needs USER approval.** Notion RVR-121 disposition is "hold third-party skill install".

## 3. Recommended adoption (pending USER approval)

| Step | Action | Risk |
|---|---|---|
| A | Vendor `imgdiff.py` (MIT, with attribution) and add a `VISUAL_COMPARE` sub-receipt fed by `--approved-ref` | Low: stdlib, read and reviewed before vendoring |
| B | Optional `impeccable detect` backend for GENERIC_TELLS, behind a flag, advisory only | Medium: npm dependency at runtime; pin a version |
| C | Register `emilkowalski/skills/apple-design` in UI_REFERENCE_REGISTRY as REFERENCE for Apple-target work | Low |
| D | Do not install replica-skill, taste-skill, huashu or ui-ux-pro-max wholesale | — |

## 4. Not verified

- None of the external code was executed (the session's policy blocks running external code). Behaviour claims come from README and source reading.
- Impeccable's star count was not captured.
- The quality claims in the READMEs (for example "looks like a real design team made it") are the authors' own.
