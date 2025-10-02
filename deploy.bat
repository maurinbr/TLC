@echo off
echo ================================
echo    TLC - Deployment Script
echo ================================
echo.

echo Choix du mode de déploiement:
echo 1. Développement local (127.0.0.1:5000)
echo 2. Réseau local (0.0.0.0:5000) 
echo 3. Production en ligne (0.0.0.0:5000, sécurisé)
echo 4. Avec tunnel ngrok (accès internet temporaire)
echo.

set /p choice="Entrez votre choix (1-4): "

if "%choice%"=="1" (
    echo Démarrage en mode développement local...
    python run.py
) else if "%choice%"=="2" (
    echo Démarrage sur le réseau local...
    echo Votre serveur sera accessible sur:
    echo - http://localhost:5000
    echo - http://[votre-ip-locale]:5000
    python run.py
) else if "%choice%"=="3" (
    echo Démarrage en mode production...
    set FLASK_ENV=production
    python run.py --production
) else if "%choice%"=="4" (
    echo Installation et démarrage avec ngrok...
    echo.
    echo 1. Installer ngrok depuis https://ngrok.com si pas déjà fait
    echo 2. Créer un compte gratuit sur ngrok.com
    echo 3. Configurer le token d'auth: ngrok authtoken YOUR_TOKEN
    echo.
    echo Démarrage du serveur Flask...
    start "Flask Server" python run.py
    timeout /t 3 /nobreak > nul
    echo Démarrage du tunnel ngrok...
    ngrok http 5000
) else (
    echo Choix invalide. Redémarrage...
    goto start
)

pause
