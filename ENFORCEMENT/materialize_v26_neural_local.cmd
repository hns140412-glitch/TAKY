@echo off
setlocal
if "%~1"=="" (
  echo Usage: materialize_v26_neural_local.cmd ^<V26_JSON_PATH^> [OUTPUT_DIR]
  exit /b 2
)
set "PAYLOAD=%~1"
if "%~2"=="" (set "OUT=%~dp1SEARCH_PROJECTION\V26_NEURAL") else (set "OUT=%~2")
if not exist "%OUT%" mkdir "%OUT%"
set "LOG=%OUT%\one-shot.log"
set "FAIL=%OUT%\failure-receipt.txt"
if exist "%FAIL%" del "%FAIL%"

echo [TAKY] Installing/checking local embedding runtime... > "%LOG%"
python -m pip install -r "%~dp0requirements-embedding-local.txt" >> "%LOG%" 2>&1
if errorlevel 1 goto :DEPENDENCY_FAIL

echo [TAKY] Materializing 679-source neural index... >> "%LOG%"
python "%~dp0materialize_v26_neural_local_v2.py" --payload "%PAYLOAD%" --output-dir "%OUT%" >> "%LOG%" 2>&1
if errorlevel 1 goto :MATERIALIZATION_FAIL

echo [TAKY] Running evidence-backed retrieval regression... >> "%LOG%"
python "%~dp0v26_neural_retrieval_regression.py" --payload "%PAYLOAD%" --vector-index "%OUT%\v26-neural-index.json" --output-dir "%OUT%" >> "%LOG%" 2>&1
if errorlevel 1 goto :REGRESSION_FAIL

echo PASS: %OUT%
exit /b 0

:DEPENDENCY_FAIL
echo STAGE=DEPENDENCY_INSTALL_FAILED> "%FAIL%"
echo LOG=%LOG%>> "%FAIL%"
echo FAILED: dependency install. Receipt: %FAIL%
exit /b 11

:MATERIALIZATION_FAIL
echo STAGE=MATERIALIZATION_FAILED> "%FAIL%"
echo LOG=%LOG%>> "%FAIL%"
echo FAILED: materialization. Receipt: %FAIL%
exit /b 12

:REGRESSION_FAIL
echo STAGE=RETRIEVAL_REGRESSION_FAILED> "%FAIL%"
echo LOG=%LOG%>> "%FAIL%"
echo FAILED: retrieval regression. Receipt: %FAIL%
exit /b 13
