@echo off
echo ====================================
echo    Configuration complete ngrok
echo ====================================
echo.

echo 1. Verification de l'installation ngrok...
where ngrok >nul 2>&1
if errorlevel 1 (
    echo ❌ ngrok non trouve dans le PATH
    echo.
    echo 🔧 Solutions:
    echo 1. Redemarrez VS Code completement
    echo 2. Ou ajoutez manuellement ngrok au PATH
    echo 3. Ou utilisez le chemin complet: C:\Users\%USERNAME%\AppData\Local\Microsoft\WinGet\Links\ngrok.exe
    echo.
    pause
    exit /b 1
) else (
    echo ✅ ngrok trouve!
    ngrok version
)

echo.
echo 2. Configuration du token d'authentification...
set /p TOKEN="Entrez votre token ngrok (ou appuyez sur Entree si deja configure): "

if not "%TOKEN%"=="" (
    echo Configuration du token...
    ngrok authtoken %TOKEN%
    echo ✅ Token configure!
) else (
    echo ⚠️  Verification du token existant...
    ngrok config check
)

echo.
echo 3. Test de connexion ngrok...
echo Demarrage d'un tunnel de test sur le port 5000...
echo.
echo 🚀 IMPORTANT: Votre serveur Flask doit etre lance sur le port 5000
echo    Si ce n'est pas le cas, lancez d'abord: python run_simple.py
echo.
echo ⚠️  Appuyez sur Ctrl+C pour arreter le tunnel
echo.

ngrok http 5000

pause
