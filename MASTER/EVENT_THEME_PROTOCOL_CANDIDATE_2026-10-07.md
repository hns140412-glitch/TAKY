# TAKY EVENT THEME PROTOCOL — CANDIDATE 2026-10-07

Status: CANDIDATE / NOT PROMOTED / NO RUNTIME BINDING
Rule ID: TKY-EVENT-THEME-001
Scope: TAKY-governed mobile learning UI and PWA visual experience.
Parent authority: MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md + MASTER/UI_REFERENCE_PROTOCOL.md + project Golden/Visual IDs.

## 0. Core invariant — HARD CANDIDATE
EVENT MAY DECORATE THE EXPERIENCE, BUT MUST NOT REWRITE THE EXPERIENCE.

An event theme MAY change atmosphere, accent tokens, approved decorative props, ambient motion, short copy, sound cues and optional character accessories.
It MUST NOT change project Golden layout, navigation model, learning logic, touch targets, primary action hierarchy, character identity, Visual ID, planner/timer semantics or data authority.

## 1. Layer order
L0 Approved World / Golden background
L1 Event environment overlay
L2 Approved Character
L3 Event-safe character accessory
L4 Activity
L5 Live UI / Feedback
L6 Event copy / micro-celebration overlay

Event artwork never bakes live text, user data, progress, score or controls into the image.

## 2. Tone classes
- CELEBRATION: birthday, Children's Day, Christmas; warm and active.
- SEASONAL: Halloween and seasonal atmosphere; playful but subordinate.
- TRADITIONAL: Seollal, Chuseok; cultural material, seasonal light and respectful motifs.
- NATIONAL_COMMEMORATION: Samiljeol, Constitution Day, Liberation Day, Gaecheonjeol, Hangeul Day; restrained symbolism and short context.
- MEMORIAL: Memorial Day; calm, respectful, no celebratory effects.

## 3. Intensity
SUBTLE: accent + 1–2 props + minimal ambient motion.
STANDARD: SUBTLE + limited accessory + sound/copy.
SPECIAL: STANDARD + one short entry moment or reward skin. SPECIAL is prohibited for MEMORIAL.

Default is SUBTLE for national/memorial events and STANDARD for personal/seasonal/traditional celebrations.

## 4. Compositor rules
- At most one global event theme + one personal overlay.
- Memorial tone suppresses confetti, fireworks, fanfare, reward multipliers and high-energy motion.
- National commemoration does not become a quiz gate or forced lesson.
- Birthday may coexist as a private personal overlay; it cannot override a memorial/global restraint.
- Reduced Motion disables non-essential ambient animation without removing meaning.
- Event sound always has a silent equivalent and must respect sound/voice settings.

## 5. Cultural integrity
Use symbols as context, not decoration spam.
For Samiljeol/Liberation Day: restrained Taegeukgi/Mugunghwa/light/wind/paper texture is allowed; flag distortion, costume parody and reward farming are prohibited.
For Seollal/Chuseok: traditional palette/material/objects are allowed without stereotyping or forced costume replacement.
For Hangeul Day: optional Hangul discovery content may be surfaced, but core Learning Engine decisions remain authoritative.
For Memorial Day: use calm tone, remembrance copy and minimal motion.

## 6. Trigger model
- FIXED_DATE: Gregorian recurring date.
- LUNAR_RESOLVER: date supplied by authoritative calendar resolver; never hardcode a Gregorian date across years.
- USER_DATE: private per-user event such as birthday.
- MANUAL_OVERRIDE: preview/testing only, visibly non-production unless activated by runtime policy.

Date resolution is separate from theme rendering.

## 7. Asset and code boundary
Theme assets follow TKY-ASSET-001: approved reusable originals/layers -> HNS approved master -> manifest/hash gate -> SIEZEALL distribution -> verified device cache.
Git stores protocol/schema/registry/tokens/slot contracts, not a second binary authority.
App repositories pin an approved event-theme version and asset IDs.

## 8. Design Gate
Before promotion:
1. Base Golden screenshot/reference loaded.
2. Event candidate rendered as a separate overlay.
3. Compare base vs event.
4. Assert layout/navigation/touch/learning invariants unchanged.
5. Verify tone-class prohibitions.
6. Verify accessibility/reduced motion/sound-off.
7. Mark PRESERVED / IMPROVED / CHANGED / REGRESSED / UNKNOWN.
8. REGRESSED or material UNKNOWN blocks promotion.

## 9. Claude Design usage
Claude Design is an executor/reviewer, not authority.
Input = current Design Authority + Golden + event registry entry + exact DELTA.
Output must preserve immutable fields and return used tokens/assets plus self-review.
Do not regenerate the whole app for a theme.

## 10. Current event set
Personal: Birthday.
Traditional: Seollal, Chuseok.
National: Samiljeol, Constitution Day, Liberation Day, Gaecheonjeol, Hangeul Day.
Memorial: Memorial Day.
Celebration/seasonal: Children's Day, Halloween, Christmas.
Additional family/cultural dates may be added by registry revision without changing base app design.

## 11. Promotion boundary
This candidate does not alter any existing Golden, Visual ID, app MASTER or CURRENT owner.
Promotion requires impact review and explicit authority update.
