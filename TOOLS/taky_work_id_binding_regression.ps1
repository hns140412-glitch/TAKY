param()
$ErrorActionPreference='Stop'
$root='D:\Git PWA\TAKY'
$prep=Join-Path $root 'TOOLS\taky_chat_task_prepare.ps1'
$dispatch=Join-Path $root 'TOOLS\taky_chat_codex_dispatch.ps1'
$cases=0
function Reject([scriptblock]$action,[string]$expected,[string]$name){
 try {
  & $action | Out-Null
  throw ('UNEXPECTED_PASS: '+$name)
 } catch {
  if($_.Exception.Message -notmatch [regex]::Escape($expected)){ throw }
  $script:cases++
  Write-Output ('PASS '+$name)
 }
}
Reject { & $prep -Task 'Review TOOLS/taky_chat_task_prepare.ps1' -Executor Codex -TaskKind review -TaskSize small -PlannedCalls 1 -Repo $root -PortfolioTaskId 'SAVEY-001' -DryRun } 'PORTFOLIO_WORK_ID_REPO_SCOPE_MISMATCH' 'REJECT_REPO_BORROW'
Reject { & $prep -Task 'Review TOOLS/TAKY_USAGE_BOARD.py' -Executor Codex -TaskKind review -TaskSize small -PlannedCalls 1 -Repo $root -PortfolioTaskId 'INT-001' -DryRun } 'PORTFOLIO_TASK_SOURCE_NOT_OWNED' 'REJECT_UNREGISTERED_SOURCE'
$valid=(& $prep -Task 'Review TOOLS/taky_chat_task_prepare.ps1 and TOOLS/taky_chat_codex_dispatch.ps1' -Executor Codex -TaskKind review -TaskSize small -PlannedCalls 1 -Repo $root -PortfolioTaskId 'INT-001' -DryRun|Out-String|ConvertFrom-Json)
if($valid.status -ne 'READY_FOR_SEPARATE_AUTHORIZATION' -or $valid.noModelCalled -ne $true){throw 'LEGITIMATE_PREPARATION_NOT_AVAILABLE'}
$cases++
Write-Output 'PASS ALLOW_MATCHED_SOURCE_WORK_ID_DRYRUN'
$parallel=(& $prep -Task 'Review TOOLS/taky_context_record.ps1' -Executor Codex -TaskKind review -TaskSize small -PlannedCalls 1 -Repo $root -PortfolioTaskId 'GATE-001' -DryRun|Out-String|ConvertFrom-Json)
if($parallel.status -ne 'READY_FOR_SEPARATE_AUTHORIZATION' -or $parallel.noModelCalled -ne $true){throw 'PARALLEL_SOURCE_OWNER_NOT_RECOGNIZED'}
$cases++;Write-Output 'PASS PARALLEL_REGISTERED_WORK_SOURCE'
Reject { & $prep -Task 'Review TOOLS/TAKY_USAGE_BOARD.py' -Executor Codex -TaskKind review -TaskSize small -PlannedCalls 1 -Repo $root -PortfolioTaskId 'GATE-001' -DryRun } 'PORTFOLIO_TASK_SOURCE_NOT_OWNED' 'REJECT_PARALLEL_UNOWNED_SOURCE'
$edit=(& $prep -Task 'Propose bounded change in the registered review source' -Executor Codex -TaskKind implementation -TaskSize small -PlannedCalls 1 -Repo $root -PortfolioTaskId 'INT-001' -AllowedFiles @('TOOLS/taky_chat_task_prepare.ps1') -AcceptanceCriteria 'No actual edits in dry run' -DryRun|Out-String|ConvertFrom-Json)
if($edit.status -ne 'READY_FOR_SEPARATE_AUTHORIZATION' -or $edit.noModelCalled -ne $true){throw 'REGISTERED_IMPLEMENTATION_NOT_READY'}
$cases++;Write-Output 'PASS REGISTERED_IMPLEMENTATION_DRYRUN'
Reject { & $prep -Task 'Propose a bounded edit to an unrelated file' -Executor Codex -TaskKind implementation -TaskSize small -PlannedCalls 1 -Repo $root -PortfolioTaskId 'INT-001' -AllowedFiles @('TOOLS/TAKY_USAGE_BOARD.py') -AcceptanceCriteria 'No actual edits in dry run' -DryRun } 'PORTFOLIO_EDIT_SOURCE_NOT_OWNED' 'REJECT_UNOWNED_EDIT_FILE'
$temporary=Join-Path ([IO.Path]::GetTempPath()) ('TAKY_BINDING_TEST_'+[guid]::NewGuid().ToString('N')+'.json')
try {
 $head=(git -C $root rev-parse HEAD).Trim()
 $fixture=[ordered]@{schema='TAKY_EXECUTION_REQUEST_V1';id='temporary_test_no_model';state='PREPARED_NOT_EXECUTED';executor='Codex';portfolio_task_id='SAVEY-001';repo=$root;head=$head;task='Review TOOLS/taky_chat_task_prepare.ps1';task_kind='review';task_size='small';planned_calls=1}
 [IO.File]::WriteAllText($temporary,($fixture|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
 Reject { & $dispatch -TaskFile $temporary } 'PORTFOLIO_WORK_ID_REPO_SCOPE_MISMATCH' 'REJECT_DISPATCH_BORROW'
 $fixture.portfolio_task_id='INT-001'
 $fixture.task='Review TOOLS/TAKY_USAGE_BOARD.py'
 [IO.File]::WriteAllText($temporary,($fixture|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
 Reject { & $dispatch -TaskFile $temporary } 'PORTFOLIO_TASK_SOURCE_NOT_OWNED' 'REJECT_DISPATCH_SOURCE'
 $fixture.task='Review TOOLS/taky_chat_task_prepare.ps1'
 [IO.File]::WriteAllText($temporary,($fixture|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
 $preview=(& $dispatch -TaskFile $temporary |Out-String|ConvertFrom-Json)
 if($preview.status -ne 'READY_NO_MODEL_CALL' -or $preview.modelCalled -ne $false){throw 'LEGITIMATE_DISPATCH_PREVIEW_NOT_READY'}
 $cases++
 Write-Output 'PASS ALLOW_MATCHED_DISPATCH_PREVIEW_NO_MODEL'
} finally { if(Test-Path -LiteralPath $temporary){Remove-Item -LiteralPath $temporary -Force} }
if($cases -ne 10){throw 'INCOMPLETE_TEST_CASES'}
Write-Output 'RESULT: TEN_REAL_SCOPE_CHECKS_PASS_ZERO_MODEL'
