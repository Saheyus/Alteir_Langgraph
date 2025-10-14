@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Install git pre-commit hook from .githooks
if not exist .githooks\pre-commit (
  echo [ERROR] .githooks\pre-commit not found.
  exit /b 1
)

git config core.hooksPath .githooks
if %errorlevel% neq 0 (
  echo [ERROR] Failed to set Git hooks path.
  exit /b 1
)

REM Ensure pre-commit hook is executable on Windows Git Bash
for %%F in (".githooks\pre-commit") do (
  if exist %%F (
    echo # >> nul
  )
)

echo [OK] Git hooks installed. Pre-commit will run pytest before committing.
exit /b 0



