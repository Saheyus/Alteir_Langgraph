@echo off
setlocal

REM Quick test runner (no slow tests)
set PYTHON_BIN=python

REM Ensure deterministic pytest environment (no external plugins)
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
set PYTEST_ADDOPTS=-p pytest_timeout -p no:agbenchmark

REM Change directory to the script location to ensure pytest.ini is found
cd /d "%~dp0"

echo Running quick test suite...
%PYTHON_BIN% -m pytest -q -m "not slow" -c pytest.ini
set EXITCODE=%errorlevel%

if %EXITCODE% neq 0 (
  echo.
  echo ❌ Quick tests failed with exit code %EXITCODE%.
  exit /b %EXITCODE%
)

echo.
echo ✅ Quick tests passed.
exit /b 0


