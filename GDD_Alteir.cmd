@echo off
title GDD Alteir - Systeme Multi-Agents
color 0A

:menu
cls
echo.
echo  ========================================
echo    GDD Alteir - Systeme Multi-Agents
echo  ========================================
echo.
echo  Que voulez-vous faire ?
echo.
echo  1. Lancer l'application Streamlit
echo  2. Lancer les tests
echo  3. Lancer une démo
echo  4. Installer les dépendances
echo  5. Voir l'aide
echo  6. Quitter
echo.
set /p choice="Votre choix (1-6) : "

if "%choice%"=="1" (
    call lancer_app.cmd
    goto menu
) else if "%choice%"=="2" (
    call lancer_tests.cmd
    goto menu
) else if "%choice%"=="3" (
    call lancer_demo.cmd
    goto menu
) else if "%choice%"=="4" (
    call installer_dependances.cmd
    goto menu
) else if "%choice%"=="5" (
    cls
    echo.
    echo  ========================================
    echo    AIDE - GDD Alteir
    echo  ========================================
    echo.
    echo  Ce système multi-agents permet de :
    echo.
    echo  • Générer des personnages pour le GDD Alteir
    echo  • Utiliser des templates Notion complets
    echo  • Tester la cohérence narrative
    echo  • Corriger et valider le contenu
    echo.
    echo  Installation :
    echo  • installer_dependances.cmd - Installe toutes les dépendances
    echo  • requirements.txt          - Liste des dépendances Python
    echo.
    echo  Fichiers importants :
    echo  • app_streamlit.py     - Interface web principale
    echo  • agents_demo.py       - Démo des agents
    echo  • demo_workflow.py     - Démo du workflow complet
    echo  • tests/               - Tests automatisés
    echo.
    echo  Documentation :
    echo  • .cursor/rules/       - Règles de développement
    echo  • docs/                - Documentation technique
    echo.
    echo  Pour plus d'informations, consultez le README.md
    echo.
    pause
    goto menu
) else if "%choice%"=="6" (
    echo.
    echo Au revoir !
    exit /b 0
) else (
    echo Choix invalide. Veuillez choisir 1, 2, 3, 4, 5 ou 6.
    timeout /t 2 >nul
    goto menu
)
