@echo off
setlocal
if "%~1"=="" (
  echo Usage: materialize_v26_neural_local.cmd ^<V26_JSON_PATH^> [OUTPUT_DIR]
  exit /b 2
)
set "PAYLOAD=%~1"
if "%~2"=="" (set "OUT=%~dp1SEARCH_PROJECTION\V26_NEURAL") else (set "OUT=%~2")
python -m pip install -r "%~dp0requirements-embedding-local.txt" || exit /b 1
python "%~dp0materialize_v26_neural_local_v2.py" --payload "%PAYLOAD%" --output-dir "%OUT%" || exit /b 1\npython "%~dp0v26_neural_retrieval_regression.py" --payload "%PAYLOAD%" --vector-index "%OUT%\\v26-neural-index.json" --output-dir "%OUT%" || exit /b 1
echo PASS: %OUT%
