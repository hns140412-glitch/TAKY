#!/usr/bin/env python3
import argparse, hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
parser = argparse.ArgumentParser()
parser.add_argument('--manifest', default=os.path.join(ROOT, 'TAKY_BADGE_ART_BINDING_MANIFEST_V1.json'))
parser.add_argument('--assets-root', default=None, help='Directory containing BDG-DRAFT-NNN.png. If omitted, validates metadata only.')
args = parser.parse_args()

obj = json.load(open(args.manifest, encoding='utf-8'))
items = obj.get('items', [])
errs = []
if len(items) != 60:
    errs.append(f'count={len(items)} expected=60')
for key in ('badge_id', 'visual_id', 'asset_slot_id', 'asset_revision_id'):
    vals = [x.get(key) for x in items]
    if len(vals) != len(set(vals)):
        errs.append(f'duplicate {key}')
shas = [x.get('current_art', {}).get('sha256') for x in items]
if len(shas) != len(set(shas)):
    errs.append('duplicate sha256')
for i, x in enumerate(items, 1):
    exp = f'{i:03d}'
    if x.get('badge_id') != f'BDG-DRAFT-{exp}': errs.append(f'{i}: badge_id')
    if x.get('visual_id') != f'BADGE_VISUAL_DRAFT_{exp}': errs.append(f'{i}: visual_id')
    if x.get('asset_slot_id') != f'TAKY_BADGE_ART_{exp}': errs.append(f'{i}: asset_slot_id')
    art = x.get('current_art', {})
    sha = art.get('sha256', '')
    if not re.fullmatch(r'[0-9a-f]{64}', sha): errs.append(f'{i}: invalid sha256')
    if art.get('content_address') != f'sha256:{sha}': errs.append(f'{i}: content_address')
    for k in ('display_title', 'core_detail', 'story_authority', 'rank_tone_wit', 'primary_anchor'):
        if not x.get(k): errs.append(f'{i}: missing {k}')
    if args.assets_root:
        p = os.path.join(args.assets_root, art.get('file_name', ''))
        if not os.path.exists(p):
            errs.append(f'{i}: missing file')
        else:
            actual = hashlib.sha256(open(p, 'rb').read()).hexdigest()
            if actual != sha: errs.append(f'{i}: sha mismatch')
g = obj.get('groups', {})
allg = sum((g.get(k, []) for k in ('current_approved', 'current_candidate', 'current_future_update')), [])
if len(allg) != 60 or len(set(allg)) != 60:
    errs.append('group partition invalid')
if errs:
    print('FAIL')
    for e in errs: print('-', e)
    sys.exit(1)
mode = 'byte+metadata' if args.assets_root else 'metadata'
print(f'PASS ({mode}): 60 stable badge art slots, IDs, semantic bindings, and SHA-256 verified')