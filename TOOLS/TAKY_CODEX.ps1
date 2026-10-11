param(
  [Parameter(Mandatory=$true)][string]$PlanJson,
  [Parameter(Mandatory=$true)][string]$InvocationJson,
  [string]$ExecutorId = 'TAKY_CODEX_RECEIPT_EXECUTOR'
)
$ErrorActionPreference='Stop'
$runner='D:\Git PWA\TAKY\TOOLS\TAKY_RECEIPT_EXEC.py'
& python -X utf8 $runner --plan-json $PlanJson --invocation-json $InvocationJson --executor-id $ExecutorId
exit $LASTEXITCODE
