# Offline synthetic WAV mock for EXACT approved source text; never creates provider/approved clips.
param([int]$Limit=0)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Speech
$base='D:\Git PWA\TAKY\staging\crew_voice_20261012'
$registry=Get-Content (Join-Path $base 'EXPLORER_CREW_PRERECORDING_ROUTING_264.json') -Raw | ConvertFrom-Json
if($registry.rows.Count -ne 264 -or $registry.voice_groups -ne 9){throw 'CANONICAL_264_SCOPE_MISMATCH'}
$dest=Join-Path $base 'mock_tts'
New-Item -ItemType Directory -Path $dest -Force | Out-Null
$manifestPath=Join-Path $dest 'EXPLORER_CREW_TTS_MOCK_MANIFEST_264.json'
$profiles=@{
 VF01=@{rate='+13%';pitch='+13%'}
 VF02=@{rate='-6%';pitch='+4%'}
 VF03=@{rate='-8%';pitch='-6%'}
 VF04=@{rate='-9%';pitch='-14%'}
 VF05=@{rate='+10%';pitch='+10%'}
 VF06=@{rate='-11%';pitch='-3%'}
 SP01=@{rate='-6%';pitch='-13%'}
 SP02=@{rate='-5%';pitch='-2%'}
 SP03=@{rate='+11%';pitch='+8%'}
}
$old=@{}
if(Test-Path $manifestPath){
 $m=Get-Content $manifestPath -Raw | ConvertFrom-Json
 foreach($entry in $m.clips){$old[$entry.key]=$entry}
}
$voice='Microsoft Heami Desktop'
$s=New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice($voice)
$entries=New-Object System.Collections.Generic.List[object]
$errors=New-Object System.Collections.Generic.List[string]
$made=0
$reused=0
$counter=0
try{
 foreach($row in $registry.rows){
  if($Limit -gt 0 -and $counter -ge $Limit){break}
  $counter++
  $profile=$profiles[[string]$row.voice_family]
  if($null -eq $profile){throw ('UNKNOWN_VOICE_GROUP '+$row.key)}
  $rel=([string]$row.scope)+'/'+([string]$row.visual_id)+'/'+([string]$row.file_stem)+'.wav'
  $full=Join-Path (Join-Path $dest 'audio\explorer-crew\mock') ($rel.Replace('/','\'))
  $styleHashRaw=('{0}|{1}|{2}|{3}|{4}|TTS_HEAMI_MOCK_V1' -f $row.text_sha256,$row.voice_family,$profile.rate,$profile.pitch,$voice)
  $styleHash=[Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData([System.Text.Encoding]::UTF8.GetBytes($styleHashRaw))).ToLowerInvariant()
  $prior=$old[[string]$row.key]
  $reusable=$false
  if($null -ne $prior -and (Test-Path -LiteralPath $full) -and $prior.style_sha256 -eq $styleHash){
    $f=Get-Item -LiteralPath $full
    if($f.Length -gt 1000){
      $sha=(Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
      if($sha -eq $prior.wav_sha256){$reusable=$true;$reused++}
    }
  }
  if(-not $reusable){
    New-Item -ItemType Directory -Path (Split-Path $full) -Force | Out-Null
    $tmp=$full+'.tmp.wav'
    if(Test-Path $tmp){Remove-Item $tmp -Force}
    $s.SetOutputToWaveFile($tmp)
    try{
      $escaped=[System.Security.SecurityElement]::Escape([string]$row.exact_text)
      $ssml="<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='ko-KR'><prosody rate='$($profile.rate)' pitch='$($profile.pitch)'>$escaped</prosody></speak>"
      $s.SpeakSsml($ssml)
    }finally{$s.SetOutputToNull()}
    $bytes=[System.IO.File]::ReadAllBytes($tmp)
    if($bytes.Length -lt 1000 -or [System.Text.Encoding]::ASCII.GetString($bytes,0,4) -ne 'RIFF' -or [System.Text.Encoding]::ASCII.GetString($bytes,8,4) -ne 'WAVE'){
      throw ('BAD_LOCAL_TTS_WAV '+$row.key)
    }
    Move-Item -LiteralPath $tmp -Destination $full -Force
    $sha=(Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
    $made++
  }
  $entries.Add([pscustomobject]@{
    key=$row.key;character_id=$row.character_id;scope=$row.scope;visual_id=$row.visual_id
    kind=$row.kind;voice_family=$row.voice_family;target_elevenlabs_voice_id=$row.voice_id
    exact_text=$row.exact_text;text_sha256=$row.text_sha256
    style_sha256=$styleHash;wav_sha256=$sha
    profile=@{rate=$profile.rate;pitch=$profile.pitch}
    provider='WINDOWS_SAPI_OFFLINE';source_voice=$voice
    mode='TTS_MOCK';approved_recording=$false
    relative_path=('audio/explorer-crew/mock/'+$rel)
    url=('./audio/explorer-crew/mock/'+$rel+'?v='+$sha.Substring(0,12))
  })
  if(($counter % 24) -eq 0){
    $doc=[ordered]@{schema_version='TAKY_EXPLORER_CREW_TTS_MOCK_264_V1';status='GENERATING';engine='Windows SAPI - Microsoft Heami Desktop';voice_groups=9;expected=264;clip_count=$entries.Count;clips=$entries.ToArray()}
    $doc | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8
    Write-Output "GENERATED_OR_REUSED $counter/264 created=$made reused=$reused"
  }
 }
}finally{$s.Dispose()}
$final=[ordered]@{
 schema_version='TAKY_EXPLORER_CREW_TTS_MOCK_264_V1'
 status=$(if($entries.Count -eq 264){'COMPLETE_MOCK_SOURCE'}else{'PARTIAL_MOCK_SOURCE'})
 engine='Windows SAPI - Microsoft Heami Desktop'
 voice_groups=9;expected=264;clip_count=$entries.Count
 caveat='9 expression profiles on ONE installed Korean SAPI voice; not 9 provider timbres.'
 clips=$entries.ToArray()
}
$final | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Output "RESULT total=$($entries.Count) newly_generated=$made reused=$reused status=$($final.status)"
if($entries.Count -ne 264 -and $Limit -eq 0){exit 2}
