param(
  [Parameter(Mandatory=$true)][string]$Source,
  [ValidateSet('CURRENT','HANDOFF','HISTORY')][string]$Role='HANDOFF',
  [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$')][string]$Project='TAKY'
)
$ErrorActionPreference='Stop'
$base='F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON'
$roleFolder=@{CURRENT='02_CURRENT';HANDOFF='03_HANDOFF';HISTORY='04_HISTORY'}
$from=(Resolve-Path -LiteralPath $Source -ErrorAction Stop).ProviderPath
if(!(Test-Path -LiteralPath $from -PathType Leaf)){throw 'SOURCE_IS_NOT_FILE'}
$destinationDir=Join-Path $base $roleFolder[$Role]
$historyDir=Join-Path $base '04_HISTORY'
foreach($p in @($destinationDir,$historyDir)){
  if(!(Test-Path -LiteralPath $p -PathType Container)){throw "SYNCED_ROLE_FOLDER_MISSING: $p"}
}
# Write new artifacts into existing role folders. Never overwrite a different file.
$now=[DateTime]::UtcNow
$tag=$now.ToString('yyyyMMddTHHmmssfffZ')+'_'+([guid]::NewGuid().ToString('N').Substring(0,8))
$stem=[IO.Path]::GetFileNameWithoutExtension($from)
$extension=[IO.Path]::GetExtension($from)
if($stem.Length -gt 70){$stem=$stem.Substring(0,70)}
$leaf="${Project}_${tag}_${stem}${extension}"
$to=Join-Path $destinationDir $leaf
if(Test-Path -LiteralPath $to){throw 'DEST_ALREADY_EXISTS'}
Copy-Item -LiteralPath $from -Destination $to -ErrorAction Stop
$srcHash=(Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash.ToLowerInvariant()
$dstHash=(Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash.ToLowerInvariant()
if($srcHash -ne $dstHash){throw 'HASH_MISMATCH_AFTER_COPY'}
$repo='D:\Git PWA\'+$Project
$head=$null
if(Test-Path -LiteralPath (Join-Path $repo '.git')){
 $h=(git -C $repo rev-parse HEAD 2>$null)
 if($LASTEXITCODE -eq 0){$head=[string]$h}
}
$receipt=[ordered]@{
 schema='TAKY_SYNCED_LOCAL_WORK_RESULT_V1'
 project=$Project;role=$Role
 created_utc=$now.ToString('o')
 original_local_path=$from
 synced_output_path=$to
 sha256=$dstHash
 bytes=(Get-Item -LiteralPath $to).Length
 source_hash_verified=$true
 repo_head=$head
 git_remote_updated=$false
 cloud_sync_readback='NOT_VERIFIED'
 verdict='LOCAL_COPY_HASH_VERIFIED_CLOUD_READBACK_OPEN'
}
$receiptFile=Join-Path $historyDir ("${Project}_${tag}_publish_receipt.json")
[IO.File]::WriteAllText($receiptFile,($receipt|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$receipt.receipt_path=$receiptFile
$receipt|ConvertTo-Json -Depth 6
