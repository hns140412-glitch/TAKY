# Mining recovery incident — exact assessment attachments (2026-09-29)

Status: SOURCE_ACQUISITION_VERIFIED_4_OF_4 / INDEX_DEDUP_AND_USER_OUTCOME_OPEN (historical failed attempts preserved below)
Kind: REAL SOURCE ACQUISITION INVESTIGATION, NOT TEST PASS OR USER OUTCOME
Owner: MINING for acquisition; INDEX for persistent identity/duplication review after a successful fetch.
Canonical/source authority: official publisher's post, not this working draft.

## 2026-09-29 actual recovery — newest observation overrides older 0/4 attempt statuses below

**Actual original bytes were recovered 4/4**, not merely listed or mocked. On the isolated Draft branch, a single bounded [publisher HTML probe run](https://github.com/hns140412-glitch/TAKY/actions/runs/36556460535) fetched the official post (HTTP 200, HTML, 179,121 bytes). The failed earlier discovery technique had searched normal anchor hrefs/search snippets; the publisher instead exposes the four exact paths, original filenames, published sizes and per-file IDs in `DEXT5UPLOAD.AddUploadedFile('3383177', ...)` inline initializers. No page JavaScript was executed.

A separate [single original-acquisition run](https://github.com/hns140412-glitch/TAKY/actions/runs/36556615467) reread the publisher page, extracted exact same-post records, fetched only four publisher-path HTTPS originals with redirect/size bounds, checked actual reported vs received bytes, HWPX zip structure and PDF signatures, then computed original SHA-256. Logs report `ORIGINAL_CAPTURE_RESULT acquired_count:4 expected_count:4 errors:[]`. Temporary GitHub Actions artifact `incheon-official-originals-one-day` ID `11027589036` is **not a GitHub repository commit**, expires 2026-09-30T10:41:15Z.

The artifact ZIP was then downloaded into the active conversation working container and independently rechecked from the bytes. The user-facing original-name archive is `TAKY_Incheon_Official_Assessment_Originals_2026-09-29.zip` (130,422,195 bytes; SHA-256 `636a224875b40420c559246df9bc89441654d2c950c982f2c6e7cde23dfddf34`). Its `SOURCE_MANIFEST.json` contains exact publisher paths, file IDs, byte sizes, source hashes and no-promotion guards.

| Exact official asset | Source URL (publisher inline record) | Bytes | SHA-256 | Independent format checks |
| --- | --- | ---: | --- | --- |
| [부록] 초등 수학과 서논술형 평가 문항.hwpx | https://www.ice.go.kr/upload/ice/na/bbs_1630/2026/09/fc7f54814aad43d790d39eb799aba533.hwpx | 25,170,695 | `cce5604188b82eded4d12cf3d14f9ed22555f0159101bcc14d468baeac7e79de` | HWPX ZIP CRC and 66 members |
| [부록] 초등 과학과 서논술형 평가 문항.hwpx | https://www.ice.go.kr/upload/ice/na/bbs_1630/2026/09/322d8a263b0b4fe5860bf4b68bc66720.hwpx | 82,304,095 | `407e9cb48b383ff2e803e84b91ddadf0adf9e9e8192bfb950da603e4cb9d38f5` | HWPX ZIP CRC and 72 members |
| 초등 수학과 서논술형 평가 도움자료.pdf | https://www.ice.go.kr/upload/ice/na/bbs_1630/2026/09/611131ca7e3b4a759d63b64bdc81e2e3.pdf | 10,813,448 | `d14a34c1e9ab005727ab84bf563be3c3b2906578956890994ce9945bd981261e` | PDF opened successfully, 192 pages |
| 초등 과학과 서논술형 평가 도움자료.pdf | https://www.ice.go.kr/upload/ice/na/bbs_1630/2026/09/cea30c60a7d443a8aee27f481d76e073.pdf | 12,129,043 | `de694da0ab8ce9fa185d8402fd5610f2c5fb01eeaa0d0cbee514d3c2f93d6680` | PDF opened successfully, 160 pages |

Reusable fault correction: `ENFORCEMENT/mining_inline_attachment_discovery.py` conservatively extracts exact source candidates from inline DEXT5 upload initializer text with same-origin/path/name/post/size bounds; never executes JavaScript, treats candidates as **not acquired**, and requires independent binary fetch. Its fixture regression uses the four real metadata entries, plus near-name, wrong post, traversal, duplicate and oversized-path counterexamples. This is new *operational failure evidence*, not a reason to reopen all previously CLOSED V2 work.

**Completion boundary:** original acquisition and physical format/hash validation 4/4 VERIFIED. Original RAW is carried in the generated conversation archive, not in the GitHub source repository. User's Drive DATA/INDEX exact duplicate and revision review has **not** run; canonical source registration and domain application remain OPEN. This incident does not by itself meet the campaign's separately required validated user outcome, so the official ledger remains 0/12. Do not rewrite historical failed attempts as successes or invent persistence in the user's Drive.

---

## Original requirement restored from Operations Handoff
Recover the actual 2026-09-01 Incheon Office of Education elementary grades 3–6 mathematics and science written/essay assessment package; verify direct official attachment routes, binaries, integrity and exact duplicates against DATA. Avoid pretending that a post with a download list is a recovered file.

Official source post (verified via public search result, nttSn 3383177):
https://www.ice.go.kr/ice/na/ntt/selectNttInfo.do?mi=11633&nttSn=3383177
Publisher's page lists four attachments, published 2026-09-01:
1. [부록] 초등 수학과 서논술형 평가 문항.hwpx
2. [부록] 초등 과학과 서논술형 평가 문항.hwpx
3. 초등 수학과 서논술형 평가 도움자료.pdf
4. 초등 과학과 서논술형 평가 도움자료.pdf

## Attempt evidence and observed results
- Public web search: official post and four *file labels* verified. Post HTML access to extract actual attachment hrefs failed with a cache miss; these hrefs and file bytes were NOT observed.
- Separate direct HTTP request in the active container: www.ice.go.kr DNS name resolution failed before any response. This is TRANSPORT_BLOCKED, not a 404 and not proof the attachments do not exist.
- Official alternate listing/host search: same publisher's post and secondary institution education-support search were located; no independently verified byte-preserving direct mirror for these four exact files surfaced. Do not treat nearby 2026 Korean/social assessment PDF as a substitute.
- Exact-target Drive search against both connected accounts, separately for all four names: none of the exact named files was returned. Search miss is NOT verified file absence.
- A fuzzy Drive search for the math PDF returned `source.html` (2.45 MB) as an apparent match. Reading its original HTML title proved it is an unrelated teacher office-tool web page; the four named target strings and official nttSn were absent. Reject this hit as `SOURCE_IDENTITY_MISMATCH` rather than INDEX verified/ACQUIRED.
- Do not infer source capture, binary integrity, SHA-256 or exact duplication without bytes. No unauthorized download/control bypass.

## Per asset status (real, not projected)
| Target | Official listed | Exact Drive file confirmed | Direct attachment URL verified | Bytes/format/hash verified | Current state |
| --- | --- | --- | --- | --- | --- |
| Math appendix HWPX | YES | NO | NO | NO | SOURCE_POST_FOUND / BINARY_OPEN |
| Science appendix HWPX | YES | NO | NO | NO | SOURCE_POST_FOUND / BINARY_OPEN |
| Math assessment PDF | YES | NO; fuzzy `source.html` rejected | NO | NO | SOURCE_POST_FOUND / FALSE_POSITIVE_REJECTED / BINARY_OPEN |
| Science assessment PDF | YES | NO | NO | NO | SOURCE_POST_FOUND / BINARY_OPEN |

Measurable result: one actual authoritative source post recovered, 4 attached names identified, 1 fuzzy false positive inspected and rejected, 0/4 required binaries recovered, 0/4 hashes checked, 0/4 exact duplicate decisions. This is not a 1/12 real user-outcome completion.

## Root cause and applied change
Baseline Index retrieval ranks lexical/semantic relevance, which is appropriate for *topic discovery* but not exact filename acquisition. Using a fuzzy hit to satisfy an explicit file target masks missing deliverables. The scoped Draft PR #176 implementation introduces `exact_source_targets` -> per-frontier `expected_source_filename`: Index-first searches exact canonical title or locator basename before accepting a candidate. A near-only hit is tagged `SOURCE_IDENTITY_MISMATCH` and triggers actionable exact-file external acquisition, not HOLD for source review and not a recovered-source claim. A correct exact Index title remains only a candidate pending original binary/provenance validation. The four target names survive bounded depth overflows. Five dedicated deterministic regressions replay this failure pattern. This **prevents false acquisition claims in the TAKY adapter**; it does not repair the external Drive search engine or acquire the missing bytes by itself.

## Concrete continuation and exit
1. On an authorized HTTP/browser-capable route, fetch the official post and recover the four *actual* attachment hrefs; record HTTP status and content type per file, rather than replaying the same cache-miss/DNS route.
2. Fetch original bytes via the official publisher. For PDF verify signature/page parse, for HWPX verify ZIP structure/manifest; record byte count, SHA-256, official origin and retrieval timestamp. Keep original RAW immutable.
3. Compare exact content hash/size + identity against Drive DATA/Index; retain `VERSION_OF` distinct from `EXACT_DUPLICATE_OF`. Do not auto-upload/promote.
4. Accept per file only after readable original bytes, source link, hash and dedup review. If authorized alternative transport is still unavailable, retain `TRANSPORT_BLOCKED` with the attempted route and distinct next route; do not ask the user to debug by default.
5. Count a real operations outcome only when a usable user task outcome is separately observed and logged. Do not use this incident's static CI fixture as one of 12.

No main/CURRENT/Netlify mutation; feature PR remains Draft/HOLD.
