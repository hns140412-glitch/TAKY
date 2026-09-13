#!/usr/bin/env python3
from preflight_gate import gate

cases = [
  ({'task_id':'r1','scope':'ReadySet','applicable_rules_loaded':True,'known_context_checked':True,'role':'ORCHESTRATOR','route':'CODEX','execution_owner':'CODEX','action_class':'IMPLEMENTATION_WRITE','validation_owner':'CI','user_role':'PRODUCT_OWNER_FINAL_APPROVER','historical_failure_classes_checked':True}, 'BLOCK', 'ROLE_OWNER_VIOLATION'),
  ({'task_id':'r2','scope':'ReadySet','applicable_rules_loaded':True,'known_context_checked':False,'role':'ORCHESTRATOR','route':'CODEX','execution_owner':'CODEX','action_class':'SPECIFY_ACCEPTANCE','validation_owner':'TAKY','user_role':'PRODUCT_OWNER_FINAL_APPROVER','historical_failure_classes_checked':True}, 'BLOCK', 'KNOWN_CONTEXT_OMISSION_RISK'),
  ({'task_id':'r3','scope':'ReadySet','applicable_rules_loaded':True,'known_context_checked':True,'role':'ORCHESTRATOR','route':'CI','execution_owner':'CI','action_class':'VALIDATION_ONLY','validation_owner':'CI','user_role':'PRODUCT_OWNER_FINAL_APPROVER','historical_failure_classes_checked':True}, 'PASS', None),
  ({'task_id':'r4','scope':'ReadySet','applicable_rules_loaded':True,'known_context_checked':True,'role':'ORCHESTRATOR','route':'CODEX','execution_owner':'CODEX','action_class':'SPECIFY_ACCEPTANCE','validation_owner':'TAKY','user_role':'PRODUCT_OWNER_FINAL_APPROVER','historical_failure_classes_checked':True}, 'PASS', None)
]
for i,(record,decision,failure) in enumerate(cases,1):
    result=gate(record)
    assert result['decision']==decision, (i,result)
    if failure: assert result.get('failure_class')==failure, (i,result)
    if record['action_class']=='VALIDATION_ONLY': assert result['product_progress_advance'] is False, result
print('PASS R-2026-09-14-READYSET-ORCHESTRATOR-DRIFT')
