# Archived former atomic relocation script. Current TAKY authority keeps
# the immutable RAW collector in D:\Git PWA\TAKY-SOURCE-VAULT, separate
# from D:\Git PWA\TAKY and from AI_WORKBENCH.
# The old script moved this root under TAKY\.local: DISALLOWED.
# This compatibility entrypoint is intentionally read-only and non-destructive.
[CmdletBinding()]
param([switch]$Audit)
$ErrorActionPreference='Stop'
$src='D:\Git PWA\TAKY-SOURCE-VAULT'
$authority='D:\Git PWA\TAKY\CURRENT\TAKY_PATH_AUTHORITY.md'
Write-Output 'TAKY_SOURCE_VAULT_REHOME=DISABLED_BY_CURRENT_AUTHORITY'
Write-Output ('SOURCE_EXISTS='+(Test-Path -LiteralPath $src))
Write-Output ('AUTHORITY='+$authority)
Write-Output 'REASON=RAW_MUST_REMAIN_SEPARATE_AND_SCHEDULED_COLLECTOR_ENTRYPOINTS_USE_ORIGINAL_ROOT'
Write-Output 'AUDIT_COMMAND=python "D:\Git PWA\TAKY\TOOLS\TAKY_WORKSPACE_CLEANUP.py" --audit'
if($Audit){& python 'D:\Git PWA\TAKY\TOOLS\TAKY_WORKSPACE_CLEANUP.py' --audit; exit $LASTEXITCODE}
exit 0
