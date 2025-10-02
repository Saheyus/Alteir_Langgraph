@echo off
echo ========================================
echo   GDD Alteir - Tests
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

echo Tests disponibles :
echo.
echo 1. Tests du template narratif
echo 2. Tests d'intégration Notion
echo 3. Tests avec vraies données
echo 4. Tous les tests
echo.

set /p choice="Choisissez un test (1-4) : "

if "%choice%"=="1" (
    echo.
    echo Lancement des tests du template narratif...
    python tests/test_narrative_template.py
) else if "%choice%"=="2" (
    echo.
    echo Lancement des tests d'intégration Notion...
    python tests/test_notion_integration.py
) else if "%choice%"=="3" (
    echo.
    echo Lancement des tests avec vraies données...
    python tests/test_real_data.py
) else if "%choice%"=="4" (
    echo.
    echo Lancement de tous les tests...
    echo.
    echo === Tests Template Narratif ===
    python tests/test_narrative_template.py
    echo.
    echo === Tests Intégration Notion ===
    python tests/test_notion_integration.py
    echo.
    echo === Tests Vraies Données ===
    python tests/test_real_data.py
) else (
    echo Choix invalide. Veuillez choisir 1, 2, 3 ou 4.
)

echo.
echo Tests terminés.
pause

