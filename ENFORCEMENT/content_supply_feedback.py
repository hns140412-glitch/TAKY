"""Route content supply failures to the smallest recoverable pipeline stage."""
ROUTE = {
    ('INTENT', 'CONTRACT_INCOMPLETE'): 'INTENT',
    ('INTENT', None): 'INTENT',
    ('DISCOVERY', None): 'DISCOVERY',
    ('COVERAGE_DIAGNOSIS', None): 'COVERAGE_DIAGNOSIS',
    ('MINING', None): 'MINING',
    ('VALIDATION', None): 'VALIDATION',
    ('INDEXING', None): 'INDEXING',
    ('GATHERING', None): 'GATHERING',
    ('FORMING', None): 'FORMING',
    ('PRODUCTION', None): 'PRODUCTION',
    ('INTEGRATION', None): 'INTEGRATION',
}
def feedback(outcome, *, demand_id):
    if not isinstance(outcome,dict) or not isinstance(demand_id,str) or not demand_id.strip():
        return {'status':'INVALID_FEEDBACK','next_stage':None}
    if outcome.get('status') == 'LOCAL_E2E_PASS':
        return {'status':'LOCAL_VERIFIED','next_stage':'APPLICATION_INTEGRATION',
                'demand_id':demand_id,'release_approved':False,'needs_real_consumer':True}
    stage = outcome.get('stage')
    reason = outcome.get('reason')
    if not isinstance(stage,str) or (reason is not None and not isinstance(reason,str)):
        return {'status':'INVALID_FEEDBACK','next_stage':None}
    nxt = ROUTE.get((stage, reason), ROUTE.get((stage,None),'COVERAGE_DIAGNOSIS'))
    inventory=(outcome.get('detail') or {}).get('inventory',[]) if isinstance(outcome.get('detail'),dict) else []
    gap_ids=[x['id'] for x in inventory if isinstance(x,dict) and x.get('state')=='COVERAGE_RECHECK'
             and isinstance(x.get('id'),str)] if isinstance(inventory,list) else []
    return {'status':'REPLENISH_REQUIRED','next_stage':nxt,'demand_id':demand_id,
            'reason':outcome.get('reason') or 'MISSING_EVIDENCE','release_approved':False,
            'retry_scope':'AFFECTED_STAGE_ONLY','targeted_gap_ids':gap_ids,
            'automatic_mining_authorized':False}
