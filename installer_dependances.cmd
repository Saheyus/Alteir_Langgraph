@echo off
echo ========================================
echo   GDD Alteir - Installation Dependances
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

echo Vérification de Python...
python --version
echo.

REM Vérifier que pip est disponible
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] pip n'est pas disponible
    echo Veuillez installer pip
    pause
    exit /b 1
)

echo Vérification de pip...
pip --version
echo.

REM Vérifier que le fichier requirements.txt existe
if not exist "requirements.txt" (
    echo [ERREUR] Fichier requirements.txt non trouvé
    echo Assurez-vous d'être dans le bon répertoire
    pause
    exit /b 1
)

echo Installation des dépendances depuis requirements.txt...
echo.
echo Cela peut prendre quelques minutes...
echo.

REM Installer les dépendances
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERREUR] Échec de l'installation des dépendances
    echo Vérifiez votre connexion internet et réessayez
    pause
    exit /b 1
)

echo.
echo [SUCCES] Toutes les dépendances ont été installées !
echo.
echo Vous pouvez maintenant lancer l'application avec :
echo   - GDD_Alteir.cmd (menu principal)
echo   - lancer_app.cmd (application directe)
echo.
pause

