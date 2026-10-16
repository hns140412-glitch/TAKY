@echo off
setlocal
set "APP=D:\Git PWA\TAKY\TOOLS\TAKY_WRITING_FLOW.py"
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8767/health',timeout=1)" >nul 2>&1
if errorlevel 1 (
  start "TAKY Writing Desk" /min cmd /c python "%APP%" --serve --port 8767
  timeout /t 2 /nobreak >nul
)
start "" "http://127.0.0.1:8767/"
endlocal
