#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=[
    'MASTER/MASTER_LOGIC.md',
    'MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md',
    'MASTER/RULE_REGISTRY.json',
    'CURRENT/DESIGN_UI_ASSET_SOURCE_DEFAULT_2026-09-29.json',
    'CURRENT/CLOUD_ID_DRIVE_ASSET_DELTA_CURRENT_2026-10-07.json',
    'CURRENT/DRIVE_ROOT_LAYOUT_LOCK_CURRENT_2026-10-07.json',
    'OS/DRIVE_STORAGE_MAP.json',
    'OS/MOBILE_APP_DEVELOPMENT_REGISTRY.json',
    'OS/LOCAL_DRIVE_WORKSPACE.md',
    'OS/LEARNING_ENGINE_DRIVE_HYBRID_STORAGE_REVIEW_2026-09-26.md',
    'HANDOFF/TAKY_DESIGN_UI_ASSET_NEW_CHAT_START_2026-09-29_LATEST.md',
]
FORBIDDEN_PATHS=[
    'TAKY/01_LEARNING',
    'TAKY/02_ARCHIGROW',
    'TAKY/03_COMMON',
    'TAKY/90_TEMP',
    'TAKY/99_DELETE_PENDING',
    'TAKY/01_LEARNING_SHARE',
    'TAKY/02_ARCHIGROW_SHARE',
    'TAKY/03_UPDATES',
    'TAKY/04_USER_DATA',
    'TAKY/10_PROJECTS',
]
FORBIDDEN_AUTHORITY_PHRASES=[
    '`TAKY-ASSETS` is the canonical binary source repository',
    'go to GitHub `TAKY-ASSETS` first',
    '원본 및 분리 에셋은 GitHub TAKY-ASSETS에 저장',
]
errors=[]
for rel in FILES:
    p=ROOT/rel
    if not p.exists():
        errors.append(f'MISSING_GOVERNED_FILE:{rel}')
        continue
    txt=p.read_text(encoding='utf-8-sig')
    for s in FORBIDDEN_PATHS:
        if s in txt:
            errors.append(f'STALE_FLAT_PATH:{rel}:{s}')
    for s in FORBIDDEN_AUTHORITY_PHRASES:
        if s in txt:
            errors.append(f'STALE_ASSET_AUTHORITY:{rel}:{s}')
if errors:
    print('FAIL: drive path reference guard')
    for e in errors: print(e)
    raise SystemExit(1)
print('DRIVE_PATH_REFERENCE_GUARD: PASS')
