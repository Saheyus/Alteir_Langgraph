@echo off
echo ========================================
echo   GDD Alteir - Demo
echo ========================================
echo.

REM Changer vers le répertoire du script
cd /d "%~dp0"

REM Vérifier que Python est disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou pas dans le PATH
    echo Veuillez installer Python ou ajouter Python au PATH
    pause
    exit /b 1
)

echo Démo disponible :
echo.
echo 1. Demo des agents
echo 2. Demo du workflow complet
echo.

set /p choice="Choisissez une démo (1-2) : "

if "%choice%"=="1" (
    echo.
    echo Lancement de la démo des agents...
    python agents_demo.py
) else if "%choice%"=="2" (
    echo.
    echo Lancement de la démo du workflow complet...
    python demo_workflow.py
) else (
    echo Choix invalide. Veuillez choisir 1 ou 2.
)

echo.
echo Démo terminée.
pause

