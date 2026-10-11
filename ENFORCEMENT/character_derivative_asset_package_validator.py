#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECTION = ROOT / 'CURRENT' / 'DATA' / 'CHARACTER_ASSET_REFERENCE_PROJECTION_CURRENT.json'
SHA256_RE = re.compile(r'^[0-9a-fA-F]{64}$')
REQUIRED_ROLES = ('TURNAROUND','FACE_SHEET','ACTION_SHEET')
REQUIRED_TURNAROUND = {'FRONT','THREE_QUARTER','SIDE','BACK'}

def _clean(value: object) -> str:
    return str(value or '').strip()

def _norm_view(value: object) -> str:
    x=_clean(value).upper().replace('-', '_').replace(' ', '_')
    return {'3/4':'THREE_QUARTER','3_4':'THREE_QUARTER','3/4_VIEW':'THREE_QUARTER','THREE_QUARTER_VIEW':'THREE_QUARTER'}.get(x,x)

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_projection(path: Path=PROJECTION) -> dict[str, Any]:
    if not path.exists():
        return {'state':'UNAVAILABLE','source_refs':[],'patterns':[],'consumer_contract':{}}
    return json.loads(path.read_text(encoding='utf-8-sig'))

def validate_projection_boundary(projection: dict[str, Any]) -> list[str]:
    errors=[]
    if projection.get('state')!='PASS':
        errors.append('REFERENCE_PROJECTION_NOT_PASS')
    if projection.get('authority')!='SUPPLEMENTAL_REFERENCE_PATTERN_ONLY':
        errors.append('REFERENCE_AUTHORITY_ESCALATION')
    if projection.get('canonical_visual_authority')!='EXISTING_APPROVED_SOURCE_AND_VISUAL_ID_ONLY':
        errors.append('CANONICAL_VISUAL_AUTHORITY_DRIFT')
    contract=projection.get('consumer_contract') or {}
    if contract.get('may_replace_visual_id') is not False:
        errors.append('REFERENCE_MAY_REPLACE_VISUAL_ID')
    if contract.get('may_generate_registration_sheet') is not False:
        errors.append('REFERENCE_MAY_GENERATE_REGISTRATION_SHEET')
    if contract.get('actual_image_review_required') is not True:
        errors.append('REFERENCE_ACTUAL_IMAGE_REVIEW_GUARD_MISSING')
    return errors

def validate_package(data: dict[str, Any], root: Path, projection: dict[str, Any] | None=None) -> dict[str, Any]:
    root=Path(root).resolve()
    errors=[]
    if data.get('schema')!='TAKY_CHARACTER_DERIVATIVE_PACKAGE_V1':
        errors.append('INVALID_SCHEMA')
    visual_id=_clean(data.get('visual_id'))
    revision=_clean(data.get('visual_id_revision'))
    fingerprint=_clean(data.get('identity_fingerprint'))
    source_sha=_clean(data.get('approved_source_sha256')).lower()
    if not visual_id: errors.append('VISUAL_ID_REQUIRED')
    if not revision: errors.append('VISUAL_ID_REVISION_REQUIRED')
    if not fingerprint: errors.append('IDENTITY_FINGERPRINT_REQUIRED')
    if not SHA256_RE.fullmatch(source_sha): errors.append('APPROVED_SOURCE_SHA256_INVALID')
    if data.get('registration_generated_reference_sheet_used') is not False:
        errors.append('GENERATED_REFERENCE_SHEET_CANNOT_BE_REGISTRATION_AUTHORITY')
    if data.get('external_reference_as_visual_authority') is not False:
        errors.append('EXTERNAL_REFERENCE_VISUAL_AUTHORITY_FORBIDDEN')

    qa=data.get('qa') or {}
    for key,code in [
        ('actual_image_comparison_complete','ACTUAL_IMAGE_COMPARISON_REQUIRED'),
        ('cross_sheet_identity_match_pass','CROSS_SHEET_IDENTITY_MATCH_REQUIRED'),
        ('color_material_lock_pass','COLOR_MATERIAL_LOCK_REQUIRED'),
        ('costume_equipment_lock_pass','COSTUME_EQUIPMENT_LOCK_REQUIRED'),
    ]:
        if qa.get(key) is not True: errors.append(code)

    assets=data.get('assets') or {}
    paths=[]
    hashes=[]
    checked=[]
    for role in REQUIRED_ROLES:
        asset=assets.get(role)
        if not isinstance(asset,dict):
            errors.append(f'{role}_REQUIRED')
            continue
        rel=_clean(asset.get('path'))
        declared=_clean(asset.get('sha256')).lower()
        if not rel:
            errors.append(f'{role}_PATH_REQUIRED')
            continue
        target=(root/rel).resolve()
        try: target.relative_to(root)
        except ValueError:
            errors.append(f'{role}_PATH_ESCAPES_ROOT')
            continue
        paths.append(target.as_posix())
        if not target.is_file():
            errors.append(f'{role}_FILE_MISSING')
        if not SHA256_RE.fullmatch(declared):
            errors.append(f'{role}_SHA256_INVALID')
        elif target.is_file():
            actual=_sha256(target)
            hashes.append(actual)
            if actual!=declared: errors.append(f'{role}_SHA256_MISMATCH')
        if _clean(asset.get('visual_id'))!=visual_id:
            errors.append(f'{role}_VISUAL_ID_MISMATCH')
        if _clean(asset.get('identity_fingerprint'))!=fingerprint:
            errors.append(f'{role}_FINGERPRINT_MISMATCH')
        if asset.get('actual_image_review_pass') is not True:
            errors.append(f'{role}_ACTUAL_IMAGE_REVIEW_REQUIRED')
        if asset.get('production_gate_pass') is not True:
            errors.append(f'{role}_PRODUCTION_GATE_REQUIRED')
        checked.append(role)

    if len(paths)!=len(set(paths)): errors.append('DERIVATIVE_ASSET_PATHS_MUST_BE_DISTINCT')
    if len(hashes)==3 and len(set(hashes))<3: errors.append('DERIVATIVE_ASSET_BYTES_MUST_BE_DISTINCT')

    turnaround=assets.get('TURNAROUND') or {}
    views={_norm_view(x) for x in turnaround.get('views',[]) if _clean(x)}
    missing=sorted(REQUIRED_TURNAROUND-views)
    if missing: errors.append('TURNAROUND_REQUIRED_VIEWS_MISSING:'+','.join(missing))

    face=assets.get('FACE_SHEET') or {}
    if face.get('head_face_lock_verified') is not True:
        errors.append('FACE_SHEET_HEAD_FACE_LOCK_REQUIRED')
    anchors=[_clean(x) for x in face.get('identity_anchors',[]) if _clean(x)]
    if len(set(anchors))<3: errors.append('FACE_SHEET_IDENTITY_ANCHORS_MIN_3')

    action=assets.get('ACTION_SHEET') or {}
    if action.get('body_identity_lock_verified') is not True:
        errors.append('ACTION_SHEET_BODY_IDENTITY_LOCK_REQUIRED')
    actions=[_clean(x) for x in action.get('actions',[]) if _clean(x)]
    if not actions: errors.append('ACTION_SHEET_ACTIONS_REQUIRED')
    if action.get('may_redefine_body_identity') is not False:
        errors.append('ACTION_SHEET_MAY_NOT_REDEFINE_BODY_IDENTITY')

    projection=projection if projection is not None else load_projection()
    projection_errors=validate_projection_boundary(projection)
    errors.extend(projection_errors)
    patterns=[_clean(x.get('id')) for x in projection.get('patterns',[]) if isinstance(x,dict) and _clean(x.get('id'))]

    return {
        'pass':not errors,
        'errors':errors,
        'visual_id':visual_id or None,
        'visual_id_revision':revision or None,
        'checked_roles':checked,
        'supplemental_reference_sources':projection.get('source_refs') or [],
        'supplemental_pattern_ids':patterns,
        'authority':'APPROVED_SOURCE_AND_VISUAL_ID_ONLY',
        'canonical_promotion':False,
    }

def main() -> int:
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('manifest')
    parser.add_argument('--root',default=None)
    parser.add_argument('--projection',default=str(PROJECTION))
    args=parser.parse_args()
    manifest=Path(args.manifest).resolve()
    root=Path(args.root).resolve() if args.root else manifest.parent
    data=json.loads(manifest.read_text(encoding='utf-8-sig'))
    projection=load_projection(Path(args.projection))
    result=validate_package(data,root,projection)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['pass'] else 1

if __name__=='__main__':
    raise SystemExit(main())
