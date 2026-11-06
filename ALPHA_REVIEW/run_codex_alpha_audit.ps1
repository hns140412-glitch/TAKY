$ErrorActionPreference='Continue'
$root='D:\Git PWA\TAKY_ALPHA_20261003'
Set-Location -LiteralPath $root
$out=Join-Path $root 'ALPHA_REVIEW\CODEX_ALPHA_V01_AUDIT.txt'
$log=Join-Path $root 'ALPHA_REVIEW\CODEX_ALPHA_V01_AUDIT_RESUME.log'
$exit=Join-Path $root 'ALPHA_REVIEW\CODEX_ALPHA_V01_AUDIT.exit'
$prompt='Continue the independent read-only audit. Complete repository inspection as needed, then return final BLOCKER/P1/P2/PASS findings with exact paths and minimal remediation. Do not inspect Claude output. Do not edit files, use network, push, merge or deploy.'
codex exec resume 01a1021b-ec8a-74a0-b18b-0fb9b5fc6879 -o $out $prompt *> $log
$c=$LASTEXITCODE
Set-Content -LiteralPath $exit -Value $c
