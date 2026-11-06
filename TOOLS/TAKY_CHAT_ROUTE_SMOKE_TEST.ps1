param()
$ErrorActionPreference='Stop'
$orchestrator='D:\Git PWA\TAKY\TOOLS\taky_chat_orchestrator.ps1'
$direct='D:\Git PWA\TAKY\TOOLS\taky_chat_codex_dispatch.ps1'
$repo='D:\Git PWA\TAKY'
$tag=[guid]::NewGuid().ToString('N')
$intent='TAKY_NO_MODEL_SMOKE_'+$tag+' read-only review contract; do not execute.'
$files=@()
$results=@()
$first=$null
try {
  # Real deterministic TAKY work: two production source files get syntax
  # validation and SHA-256 evidence without any provider call or task queue.
  $local=(& $orchestrator -Action Dispatch -Repo $repo -TaskKind validation -Task 'Local-only source syntax proof' -AllowedFiles @('TOOLS/TAKY_USAGE_EFFICIENCY_AUDIT.py','ENFORCEMENT/ui_playwright_capture.mjs') -AcceptanceCriteria 'SYNTAX_ONLY' | Out-String | ConvertFrom-Json)
  $results+= $local
  if($local.status -ne 'LOCAL_VALIDATION_PASS' -or $local.model_called -ne $false -or
     $local.files_checked -ne 2 -or @($local.verified_files|Where-Object {-not $_.passed}).Count -ne 0){
    throw ('LOCAL_WORK_DID_NOT_EXECUTE: '+$local.status+' '+$local.output)
  }
  foreach($item in $local.verified_files){
    $p=Join-Path $repo ($item.path -replace '/','\')
    if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -cne $item.sha256){throw 'LOCAL_SOURCE_HASH_MISMATCH'}
  }
  Write-Output 'PASS_LOCAL_REAL_PYTHON_AND_JS_SYNTAX_ZERO_MODEL=true'
  # Application logic E2E through TAKY's real validation route, with 0 LLM.
  $play=(& $orchestrator -Action Dispatch -Repo 'D:\Git PWA\Play Camp' -TaskKind validation -Task 'Verify real Play Camp Hangul and paper-fold mathematics locally' -AllowedFiles @('tests/hangul.test.ts','tests/paperFoldGeometry.test.ts') -AcceptanceCriteria 'UNIT_TESTS' | Out-String | ConvertFrom-Json)
  $results+= $play
  if($play.status -ne 'LOCAL_VALIDATION_PASS' -or $play.model_called -ne $false -or
     $play.tests_executed -lt 8 -or $play.tests_passed -ne $play.tests_executed -or
     $play.tests_failed -ne 0 -or $play.test_exit_code -ne 0){
    throw ('PLAY_CAMP_LOCAL_FUNCTION_QA_NOT_EXECUTED: '+$play.status)
  }
  foreach($item in $play.verified_files){
    $p=Join-Path 'D:\Git PWA\Play Camp' ($item.path -replace '/','\')
    if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -cne $item.sha256){throw 'PLAY_CAMP_TEST_HASH_NOT_BOUND'}
  }
  Write-Output 'PASS_PLAY_CAMP_AT_LEAST_EIGHT_UNIT_TESTS_ZERO_MODEL=true'
  $match=(& $orchestrator -Action Dispatch -Repo 'D:\Git PWA\Play Camp' -TaskKind validation -Task 'Verify matchstick missions and shortest move solver without model' -AllowedFiles @('tests/matchstick.test.ts','tests/matchstickSolver.test.ts') -AcceptanceCriteria 'UNIT_TESTS' | Out-String | ConvertFrom-Json)
  $results+= $match
  if($match.status -ne 'LOCAL_VALIDATION_PASS' -or $match.tests_passed -lt 8 -or $match.tests_failed -ne 0 -or $match.model_called -ne $false){throw 'MATCHSTICK_QA_DID_NOT_PASS'}
  $cube=(& $orchestrator -Action Dispatch -Repo 'D:\Git PWA\Play Camp' -TaskKind validation -Task 'Verify all cube-net fold geometries without model' -AllowedFiles @('tests/cubeNetGeometry.test.ts') -AcceptanceCriteria 'UNIT_TESTS' | Out-String | ConvertFrom-Json)
  $results+= $cube
  if($cube.status -ne 'LOCAL_VALIDATION_PASS' -or $cube.tests_passed -lt 8 -or $cube.tests_failed -ne 0 -or $cube.model_called -ne $false){throw 'CUBE_GEOMETRY_QA_DID_NOT_PASS'}
  Write-Output 'PASS_PLAY_CAMP_AT_LEAST_TWENTY_FOUR_DOMAIN_UNIT_TESTS_ZERO_MODEL=true'
  $forbidden=(& $orchestrator -Action Dispatch -Repo 'D:\Git PWA\Play Camp' -TaskKind validation -Task 'Reject arbitrary test' -AllowedFiles @('tests/fake.test.ts') -AcceptanceCriteria 'UNIT_TESTS' | Out-String | ConvertFrom-Json)
  $results+= $forbidden
  if($forbidden.status -ne 'HOLD' -or $forbidden.model_called -ne $false){throw 'UNAPPROVED_FUNCTION_TEST_NOT_HELD'}
  Write-Output 'PASS_UNAPPROVED_FUNCTION_TEST_FAIL_CLOSED=true'
  $missing=(& $orchestrator -Action Dispatch -Repo $repo -TaskKind validation -Task 'Missing file must HOLD' -AllowedFiles @('TOOLS/TAKY_FILE_NOT_EXISTING_QA.py') -AcceptanceCriteria 'SYNTAX_ONLY' | Out-String | ConvertFrom-Json)
  $results+= $missing
  if($missing.status -ne 'HOLD' -or $missing.model_called -ne $false){throw 'MISSING_LOCAL_SOURCE_WAS_NOT_HELD'}
  Write-Output 'PASS_LOCAL_MISSING_SOURCE_FAIL_CLOSED=true'
  $first=(& $orchestrator -Action Dispatch -Repo $repo -Executor Auto -TaskKind review -TaskSize small -Task $intent | Out-String | ConvertFrom-Json)
  $results+= $first
  if($first.status -eq 'HOLD' -and $first.output -match 'PORTFOLIO_WORK_ID_REQUIRED_FOR_MODEL_TASK'){
    Write-Output 'PASS_UNBOUND_FUTURE_MODEL_TASK_HELD_NO_MODEL=true'
    return
  }
  if($first.status -eq 'HOLD' -and $first.output -match 'TAKY_GOVERNANCE_ROUTE_HOLD'){
    throw 'MISSING_PORTFOLIO_ID_WAS_NOT_CHECKED_BEFORE_ROUTE'
  }
  if($first.status -ne 'PREPARED_NOT_EXECUTED' -or $first.preparation_reused -ne $false -or !$first.task_file){throw ('FIRST_DISPATCH_FAILED: '+$first.status+' '+$first.output)}
  $taskFile=[string]$first.task_file
  $files+= $taskFile
  $second=(& $orchestrator -Action Dispatch -Repo $repo -Executor Auto -TaskKind review -TaskSize small -Task $intent | Out-String | ConvertFrom-Json)
  $results+= $second
  if($second.status -ne 'PREPARED_NOT_EXECUTED' -or $second.preparation_reused -ne $true -or $second.task_id -ne $first.task_id){throw ('SECOND_DISPATCH_NOT_REUSED: '+$second.status+' '+$second.output)}
  if($first.executor -eq 'Codex'){
    $directPreview=(& $direct -TaskFile $taskFile | Out-String | ConvertFrom-Json)
    if($directPreview.status -ne 'READY_NO_MODEL_CALL' -or $directPreview.modelCalled -ne $false){throw 'DIRECT_CODEX_PREVIEW_FAILED'}
    Write-Output 'PASS_DIRECT_CODEX_PREVIEW_NO_MODEL=true'
  }else{
    Write-Output 'PASS_SAFE_FALLBACK_CLAUDE_WHEN_CODEX_STALE=true'
  }
  $preparedPreview=(& $orchestrator -Action RunPrepared -Repo $repo -TaskFile $taskFile | Out-String | ConvertFrom-Json)
  $results+= $preparedPreview
  if($preparedPreview.status -ne 'PREVIEW_ONLY_NOT_EXECUTED' -or $preparedPreview.model_called -ne $false){throw ('RUN_PREVIEW_FAILED: '+$preparedPreview.status+' '+$preparedPreview.output)}
  $claudePreview=(& $orchestrator -Action RouteDryRun -Repo $repo -Executor Claude -TaskKind code -TaskSize small -Task $intent | Out-String | ConvertFrom-Json)
  if($claudePreview.status -ne 'DRYRUN_READY' -or $claudePreview.model_called -ne $false){throw ('CLAUDE_ROUTE_FAILED: '+$claudePreview.status+' '+$claudePreview.output)}
  $item=Get-Content -LiteralPath $taskFile -Raw -Encoding UTF8 | ConvertFrom-Json
  if($item.state -ne 'PREPARED_NOT_EXECUTED' -or $item.task -ne $intent){throw 'PREPARED_RECEIPT_CHANGED'}
  Write-Output ('PASS_FIRST_PREP_ID='+$first.task_id)
  Write-Output 'PASS_IDENTICAL_SECOND_DISPATCH_REUSED=true'
  Write-Output 'PASS_ORCHESTRATOR_RUNPREPARED_PREVIEW_NO_MODEL=true'
  Write-Output 'PASS_CLAUDE_ROUTE_PREVIEW_NO_MODEL=true'
  Write-Output 'PASS_NO_INFERENCE_CALLS_OR_PAID_API=true'
} finally {
  $history='F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY'
  foreach($r in $results){
    if($r -and $r.id -match '^[0-9a-f]{32}$'){
      $path=Join-Path $history ('TAKY_CHAT_ORCH_'+$r.id+'.json')
      if(Test-Path -LiteralPath $path){Remove-Item -LiteralPath $path -Force}
    }
  }
  if($first -and $first.task_file){
    if(Test-Path -LiteralPath ([string]$first.task_file)){
      $existing=Get-Content -LiteralPath ([string]$first.task_file) -Raw -Encoding UTF8 | ConvertFrom-Json
      if($existing.task -eq $intent -and $existing.id -eq $first.task_id){
        if($first.work_id -eq ('TAKY-CHAT-'+[string]$first.task_id)){
          $reg='D:\Git PWA\TAKY_AI_WORKBENCH\00_CONTROL\AI_WORK_ASSIGNMENTS.json'
          $gate=[Threading.Mutex]::new($false,'Local\TAKY_WORK_ASSIGNMENT_MUTEX')
          $locked=$false
          try {
            $locked=$gate.WaitOne(5000)
            if(!$locked){throw 'TEST_REGISTRY_LOCK_BUSY'}
            $doc=Get-Content -LiteralPath $reg -Raw -Encoding UTF8|ConvertFrom-Json
            $owned=@($doc.tasks|Where-Object {$_.work_id -eq $first.work_id})
            if($owned.Count -ne 1 -or @($owned[0].input_refs) -notcontains [string]$first.task_file -or
               $owned[0].status -ne 'OPEN' -or @($owned[0].output_refs).Count -gt 0){throw 'TEST_ASSIGNMENT_NOT_OWNED'}
            $doc.tasks=@($doc.tasks|Where-Object {$_.work_id -ne $first.work_id})
            $tmp=$reg+'.smoke.'+[guid]::NewGuid().ToString('N')
            try {
              [IO.File]::WriteAllText($tmp,($doc|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
              Move-Item -LiteralPath $tmp -Destination $reg -Force -ErrorAction Stop
            }finally{if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Force}}
          }finally{if($locked){$gate.ReleaseMutex()|Out-Null};$gate.Dispose()}
        }
        Remove-Item -LiteralPath ([string]$first.task_file) -Force
      }
    }
  }
  Write-Output 'SMOKE_GENERATED_RECEIPTS_CLEANED'
}
