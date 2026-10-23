param(
 [Parameter(ParameterSetName='EventFile',Mandatory=$true)][string]$EventJsonPath,
 [Parameter(ParameterSetName='UserCorrection',Mandatory=$true)][string]$CorrectionText,
 [Parameter(ParameterSetName='UserCorrection',Mandatory=$true)][string]$SourceRef,
 [Parameter(ParameterSetName='UserCorrection',Mandatory=$true)]
 [ValidatePattern('^[A-Za-z0-9_.-]{1,64}$')][string]$ProjectNamespace,
 [Parameter(ParameterSetName='UserCorrection',Mandatory=$true)][switch]$AttestDirectUserTurn,
 [string]$DriveRoot = 'F:\내 드라이브\TAKY'
)
$ErrorActionPreference='Stop'
if($PSCmdlet.ParameterSetName -eq 'UserCorrection'){
 if(-not $AttestDirectUserTurn){throw 'DIRECT_USER_SOURCE_ATTESTATION_REQUIRED'}
 if([string]::IsNullOrWhiteSpace($CorrectionText) -or $CorrectionText.Length -gt 300 -or
    $CorrectionText -match '[\x00-\x1f\x7f]' -or $CorrectionText -match '(?i)-----BEGIN|sk-[A-Za-z0-9]{8,}|gh[pousr]_[A-Za-z0-9]{8,}'){
   throw 'USER_CORRECTION_TEXT_REJECTED'
 }
 if($SourceRef -notmatch '^[A-Za-z0-9_.:/#-]{6,200}$'){throw 'USER_SOURCE_REF_INVALID'}
 $stable=$ProjectNamespace+[char]0+$SourceRef+[char]0+$CorrectionText
 $digest=([Security.Cryptography.SHA256]::Create()).ComputeHash([Text.Encoding]::UTF8.GetBytes($stable))
 $eventId='UC-'+([BitConverter]::ToString($digest).Replace("-","").ToLowerInvariant().Substring(0,24))
 $event=[pscustomobject][ordered]@{
  event_id=$eventId
  session_id='taky-correction-'+[DateTime]::UtcNow.ToString('yyyyMMdd')
  captured_at=[DateTime]::UtcNow.ToString('o')
  actor='USER'
  project_namespace=$ProjectNamespace
  event_type='USER_CORRECTION'
  intent='Preserve sourced user correction for future task-context review'
  action='RECORD_CORRECTION_CANDIDATE'
  outcome='CAPTURED_NOT_APPLIED'
  provenance='Direct-user-turn attestation by caller. Native chat transcript not independently authenticated'
  source_ref=$SourceRef
  source_coverage='CALLER_ATTESTED_DIRECT_USER_TURN'
  exact_user_words=$CorrectionText
  status='IN_PROGRESS'
  canonical_promotion=$false
  implementation_verified=$false
 }
}else{
 $event = Get-Content -LiteralPath $EventJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
}
$required=@('event_id','session_id','captured_at','actor','project_namespace','intent','action','outcome','provenance')
foreach($key in $required) { if(-not $event.PSObject.Properties[$key] -or [string]::IsNullOrWhiteSpace([string]$event.$key)) { throw "Missing required field: $key" } }
$valid=@('PLANNED','IN_PROGRESS','VERIFIED','BLOCKED','UNKNOWN','SUPERSEDED')
if($event.PSObject.Properties['status'] -and $event.status -notin $valid) { throw "Invalid status: $($event.status)" }
if([string]$event.session_id -notmatch '^[A-Za-z0-9_-]{1,128}$' -or
   [string]$event.event_id -notmatch '^[A-Za-z0-9_.:-]{1,128}$'){throw 'EVENT_ID_OR_SESSION_INVALID'}
$history=Join-Path $DriveRoot '20_PLATFORM\03_COMMON\04_HISTORY'
if(-not (Test-Path -LiteralPath $history -PathType Container)){throw "Existing Drive history folder not found: $history"}
$target=Join-Path $history ('TAKY_CONVERSATION_EVENTS_'+$event.session_id+'.jsonl')
if((Test-Path -LiteralPath $target) -and (Get-Item -LiteralPath $target).Length -gt 2097152){throw 'EVENT_JOURNAL_SIZE_LIMIT'}
$line=$event | ConvertTo-Json -Depth 20 -Compress
$bytes=[System.Text.UTF8Encoding]::new($false).GetBytes($line+[Environment]::NewLine)
$stream=[System.IO.FileStream]::new($target,[System.IO.FileMode]::OpenOrCreate,[System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::None)
try {
 if($stream.Length -gt 2097152){throw 'EVENT_JOURNAL_SIZE_LIMIT'}
 $existingBytes=New-Object byte[] ([int]$stream.Length)
 if($existingBytes.Length){[void]$stream.Read($existingBytes,0,$existingBytes.Length)}
 $duplicate=$false
 foreach($row in ([Text.Encoding]::UTF8.GetString($existingBytes) -split '\r?\n')){
  if(-not $row.Trim()){continue}
  try{$prior=$row|ConvertFrom-Json -ErrorAction Stop}catch{throw 'EVENT_JOURNAL_EXISTING_ROW_INVALID'}
  if([string]$prior.event_id -ceq [string]$event.event_id){
   if($PSCmdlet.ParameterSetName -eq 'UserCorrection'){
    if([string]$prior.exact_user_words -cne [string]$event.exact_user_words -or
       [string]$prior.source_ref -cne [string]$event.source_ref -or
       [string]$prior.project_namespace -cne [string]$event.project_namespace){throw 'EVENT_REPLAY_CONFLICT'}
   }elseif(($prior|ConvertTo-Json -Depth 20 -Compress) -cne ($event|ConvertTo-Json -Depth 20 -Compress)){
    throw 'EVENT_REPLAY_CONFLICT'
   }
   $duplicate=$true
   break
  }
 }
 if(-not $duplicate){
  $stream.Seek(0,[IO.SeekOrigin]::End)|Out-Null
  $stream.Write($bytes,0,$bytes.Length)
  $stream.Flush($true)
 }
}finally{$stream.Dispose()}
Write-Output ('EVENT_'+$(if($duplicate){'REUSED'}else{'APPENDED'})+'='+$target)
Write-Output "EVENT_ID=$($event.event_id)"
Write-Output 'CANONICAL_PROMOTION=false'
