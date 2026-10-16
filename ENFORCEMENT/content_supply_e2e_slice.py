"""Evidence-based local content supply vertical slice; no runtime release or external calls."""
import hashlib
import json
from pathlib import Path
from content_supply_contract import audit
from content_supply_index_bridge import inspect
from content_supply_raw_bridge import verify_raw_candidates
from content_supply_atomic import publish_bytes

def digest(b): return hashlib.sha256(b).hexdigest()

def run_slice(contract, index_path, manifest, root, output_path, consumer, forming_evidence_path=None):
    """Produce a grounded JSON package only when every requirement has verified RAW bytes.

    Consumer callback must parse the exact package bytes and return a receipt with
    artifact_sha256 and requirement_ids. This proves local contract consumption only.
    """
    base = Path(root).resolve()
    initial = audit(contract)
    if initial.get('reason'):
        return {'status':'BLOCKED','stage':'INTENT','detail':initial}
    indexed = inspect(contract, index_path, forming_evidence_path)
    if indexed.get('index_error'):
        return {'status':'BLOCKED','stage':'INDEXING','reason':'INDEX_UNAVAILABLE','detail':indexed}
    findings = indexed.get('inventory', [])
    if any(x['state'] == 'QUERY_REQUIRED' for x in findings):
        return {'status':'BLOCKED','stage':'INTENT','reason':'QUERY_REQUIRED','detail':indexed}
    if any(x['state'] == 'SEARCH_FAILED' for x in findings):
        return {'status':'BLOCKED','stage':'INDEXING','reason':'SEARCH_FAILED','detail':indexed}
    if any(x['state'] == 'COVERAGE_RECHECK' for x in findings):
        return {'status':'BLOCKED','stage':'COVERAGE_DIAGNOSIS','reason':'INDEX_NO_MATCH_NOT_SOURCE_ABSENCE','detail':indexed}
    # A referenced RAW document is not a mined or formed consumer-ready source.
    # The INDEX bridge rechecks SHA at lookup, then routes the next *real* stage.
    if any(x['state'] == 'RAW_RECHECK_REQUIRED' for x in findings):
        return {'status':'BLOCKED','stage':'GATHERING','reason':'REVIEW_RAW_INTEGRITY_RECHECK_REQUIRED','detail':indexed}
    if any(x['state'] == 'FORMING_EVIDENCE_RECHECK_REQUIRED' for x in findings):
        return {'status':'BLOCKED','stage':'FORMING','reason':'REVIEW_FORMING_PROOF_INVALID','detail':indexed}
    if any(x['state'] == 'REVIEW_FORMING_RUNTIME_VERIFIED' for x in findings):
        if not findings or any(x['state'] != 'REVIEW_FORMING_RUNTIME_VERIFIED' for x in findings):
            return {'status':'BLOCKED','stage':'FORMING','reason':'MIXED_FORMING_STATES','detail':indexed}
        # A code-capability scenario is not a teaching-content candidate.
        # Do not publish a TAKY_SUPPLY_SLICE_V1 or invoke the app activity parser.
        return {'status':'HOLD','stage':'INTEGRATION',
                'reason':'CODE_CAPABILITY_SCENARIO_TESTED_APP_RELEASE_UNVERIFIED',
                'local_runtime_evidence_verified':True,
                'forming_receipts':[x['forming_receipt'] for x in findings],
                'content_artifact_created':False,'learning_consumed':False,
                'release_approved':False,'authority':'WORKBENCH_EVIDENCE_ONLY'}
    if any(x['state'] == 'RAW_READY_FOR_MINING' for x in findings):
        return {'status':'BLOCKED','stage':'MINING','reason':'REVIEW_RAW_BODY_MINING_REQUIRED','detail':indexed}
    if any(x['state'] != 'REUSE_CANDIDATES' for x in findings):
        return {'status':'BLOCKED','stage':'INDEXING','reason':'INDEX_STATE_UNKNOWN','detail':indexed}
    raw = verify_raw_candidates(indexed['inventory'], root=base, manifest=manifest, capture_bytes=True)
    selected = {}
    for row in raw['items']:
        valid = next((x for x in row['raw_candidates'] if x['state'] == 'RAW_HASH_MATCH_CANDIDATE'), None)
        if valid is None:
            return {'status':'BLOCKED','stage':'GATHERING',
                    'detail':{k:v for k,v in raw.items() if k!='verified_bytes'}}
        selected[row['requirement_id']] = valid['source_id']
    # FORMING: build extractive content from confirmed RAW, not generated claims.
    units = []
    for req in contract['requirements']:
        sid = selected[req['id']]
        meta = manifest[sid]
        # Reuse the bytes checked on the original file handle; never reopen RAW by path.
        data = raw['verified_bytes'].get(sid)
        if not isinstance(data, bytes) or not data or digest(data) != meta['sha256'].lower():
            return {'status':'BLOCKED','stage':'FORMING','reason':'RAW_CHANGED'}
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            return {'status':'BLOCKED','stage':'MINING','reason':'TEXT_EXTRACTION_REQUIRED'}
        units.append({'requirement_id': req['id'], 'source_id': sid,
                      'raw_sha256': digest(data), 'source_excerpt': text[:240]})
    trace = [{'requirement_id':u['requirement_id'], 'source_id':u['source_id'],
              'raw_sha256':u['raw_sha256']} for u in units]
    input_fingerprint = digest(json.dumps({'demand_id':contract['demand_id'],
        'consumer':contract['consumer'],'trace':trace},sort_keys=True,ensure_ascii=False).encode('utf-8'))
    output_fingerprint = digest(json.dumps(units,sort_keys=True,ensure_ascii=False).encode('utf-8'))
    payload = {'schema':'TAKY_SUPPLY_SLICE_V1','demand_id':contract['demand_id'],
               'consumer':contract['consumer'],'units':units,'generated_content':False,
               'forming': {'owner_namespace':contract['consumer'],
                           'forming_kind':'CONTENT_FORMING',
                           'artifact_revision':'sha256:'+output_fingerprint,
                           'source_refs':[u['source_id'] for u in units],
                           'index_refs':['INDEX_SEARCH_READBACK'],
                           'ruleset_revision':'TKY-FORMING-001:LOCAL_SLICE_V1',
                           'input_fingerprint':input_fingerprint,
                           'output_fingerprint':output_fingerprint,
                           'provenance_trace':trace,
                           'consumer_contract':'PLAY_CAMP_CANDIDATE_INSPECTION_ONLY',
                           'validation_status':'LOCAL_CONTRACT_CANDIDATE',
                           'approval_status':'NOT_APPROVED',
                           'known_gaps':['SOURCE_AUTHORITY_REVIEW','DOMAIN_SEMANTIC_REVIEW',
                                         'APP_RUNTIME_BINDING','LEARNING_ENGINE_REPLAY']}}
    artifact = json.dumps(payload,ensure_ascii=False,sort_keys=True).encode('utf-8')
    path = Path(output_path)
    try:
        publication = publish_bytes(path, artifact)
    except FileExistsError:
        return {'status':'BLOCKED','stage':'PRODUCTION','reason':'OUTPUT_CONFLICT'}
    except (OSError, TypeError):
        return {'status':'BLOCKED','stage':'PRODUCTION','reason':'OUTPUT_WRITE_FAILED'}
    reused = publication == 'REUSED'
    try:
        receipt = consumer(path)
    except (OSError, ValueError, TypeError, RuntimeError):
        receipt = None
    allowed = {'APP_CANDIDATE_PARSED':'PLAY_CAMP_TS_SUPPLY_CANDIDATE_V1',
               'LOCAL_FIXTURE_PARSED':'LOCAL_TEST_FIXTURE'}
    receipt_valid = (isinstance(receipt, dict)
        and receipt.get('status') in allowed
        and receipt.get('consumer_adapter') == allowed.get(receipt.get('status'))
        and receipt.get('artifact_sha256') == digest(artifact)
        and receipt.get('canRegisterActivity') is False
        and receipt.get('canEmitLearningEvidence') is False
        and isinstance(receipt.get('requirement_ids'), list)
        and receipt['requirement_ids'] == list(selected.keys())
        and isinstance(receipt.get('source_ids'), list)
        and receipt['source_ids'] == list(selected.values()))
    if not receipt_valid:
        return {'status':'BLOCKED','stage':'INTEGRATION','reason':'CONSUMER_RECEIPT_INVALID','artifact_sha256':digest(artifact)}
    return {'status':'LOCAL_E2E_PASS','stage':'VALIDATION','artifact_sha256':digest(artifact),
            'unit_count':len(units),'receipt':receipt,'reused_artifact':reused,'release_approved':False,
            'scope':'LOCAL_FIXTURE_ONLY_NOT_APPLICATION_RUNTIME'}

def local_consumer(path):
    data = Path(path).read_bytes()
    decoded = json.loads(data)
    if decoded.get('schema') != 'TAKY_SUPPLY_SLICE_V1':
        return {}
    return {'status':'LOCAL_FIXTURE_PARSED','consumer_adapter':'LOCAL_TEST_FIXTURE',
            'artifact_sha256':digest(data),
            'requirement_ids':[u['requirement_id'] for u in decoded['units']],
            'source_ids':[u['source_id'] for u in decoded['units']],
            'canRegisterActivity':False,'canEmitLearningEvidence':False}
