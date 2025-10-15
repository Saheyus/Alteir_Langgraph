@echo off
echo ========================================
echo   GDD Alteir - Systeme Multi-Agents
echo ========================================
echo.
echo Lancement de l'application Streamlit...
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

REM Vérifier que le fichier app_streamlit.py existe
if not exist "app_streamlit.py" (
    echo [ERREUR] Fichier app_streamlit.py non trouvé
    echo Assurez-vous d'être dans le bon répertoire
    pause
    exit /b 1
)

REM Vérifier que streamlit est installé
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Module streamlit non installé
    echo.
    echo Pour installer les dépendances, exécutez :
    echo   installer_dependances.cmd
    echo.
    echo Ou manuellement :
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Lancer l'application Streamlit (le port est choisi par Streamlit)
echo Lancement de l'application (le port exact sera affiché par Streamlit)
echo.
echo Pour arrêter l'application, appuyez sur Ctrl+C dans cette fenêtre
echo.
python -m streamlit run "app_streamlit.py"

REM Si on arrive ici, l'application s'est fermée
echo.
echo Application fermée.
pause
