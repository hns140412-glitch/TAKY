$ErrorActionPreference='Stop'
$sourceRoot='D:\Git PWA\TAKY'
$destRoot='F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\WORK_OS\SOURCE_ARCHIVE\TAKY_CHAT_ORCHESTRATION'
$files=@('TOOLS\taky_chat_orchestrator.ps1','TOOLS\taky_bridge_worker.ps1','TOOLS\taky_headless_mailbox.ps1','TOOLS\taky_chat_mirror_checkpoint.ps1')
[IO.Directory]::CreateDirectory($destRoot)|Out-Null
$entries=@()
foreach($f in $files){
 $src=Join-Path $sourceRoot $f
 if(!(Test-Path -LiteralPath $src)){throw "Missing $f"}
 $dst=Join-Path $destRoot (Split-Path $f -Leaf)
 Copy-Item -LiteralPath $src -Destination $dst -Force
 $sha=(Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
 $shaMirror=(Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash
 if($sha -ne $shaMirror){throw "HASH_MISMATCH $f"}
 $entries+=@{repo_path=$f;mirror_path=$dst;sha256=$sha;verified=$true}
}
$manifest=[ordered]@{schema='TAKY_LOCAL_SOURCE_MIRROR_V1';timestamp_utc=[DateTime]::UtcNow.ToString('o');repo=$sourceRoot;head=(git -C $sourceRoot rev-parse HEAD);branch=(git -C $sourceRoot branch --show-current);git_push_performed=$false;mirror_kind='working-files-snapshot-not-github-remote';entries=$entries}
$target=Join-Path $destRoot 'MIRROR_MANIFEST.json'
[IO.File]::WriteAllText($target,($manifest|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
"FILES_VERIFIED=$($entries.Count)";"MANIFEST=$target";"HEAD=$($manifest.head)"
