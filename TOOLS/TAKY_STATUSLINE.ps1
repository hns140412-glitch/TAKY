[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$raw = [Console]::In.ReadToEnd()
try { [IO.File]::WriteAllText((Join-Path $env:TEMP 'TAKY_STATUSLINE_LAST.json'), $raw, [Text.UTF8Encoding]::new($false)) } catch {}
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
try { $d = $raw | ConvertFrom-Json } catch { exit 0 }

$model = if ($d.model.display_name) { $d.model.display_name } else { 'Claude' }
$ctx = if ($null -ne $d.context_window.used_percentage) { [math]::Round([double]$d.context_window.used_percentage) } else { 0 }

function Remaining($node) {
  if ($null -eq $node -or $null -eq $node.used_percentage) { return '확인불가' }
  $left = [math]::Max(0, 100 - [double]$node.used_percentage)
  return ([math]::Round($left)).ToString() + '% 남음'
}

$five = Remaining $d.rate_limits.five_hour
$seven = Remaining $d.rate_limits.seven_day

$cache = ''
if ($null -ne $d.prompt_cache.hit_ratio) {
  $hit = [math]::Round(([double]$d.prompt_cache.hit_ratio) * 100)
  $cache = " | 캐시 $hit%"
}

Write-Output "[SAVEY] $model | 컨텍스트 $ctx% | 5시간 $five | 주간 $seven$cache"

