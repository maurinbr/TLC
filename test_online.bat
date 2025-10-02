@echo off
echo ====================================
echo    TLC - Test en ligne avec ngrok
echo ====================================
echo.

echo Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

echo.
echo Verification des packages installes...
python -c "import flask, pyngrok; print('✅ Flask et pyngrok installes')"

if errorlevel 1 (
    echo ❌ Erreur: Dependencies manquantes
    echo Installation automatique...
    pip install flask pyngrok
)

echo.
echo 🚀 Demarrage du serveur avec tunnel ngrok...
echo.
echo INSTRUCTIONS:
echo 1. Si c'est votre premiere utilisation de ngrok:
echo    - Creez un compte sur https://ngrok.com
echo    - Recuperez votre token d'authentification
echo    - Executez: ngrok authtoken VOTRE_TOKEN
echo.
echo 2. Le serveur demarrera automatiquement
echo 3. Une URL publique sera generee pour les tests
echo 4. Appuyez sur Ctrl+C pour arreter
echo.

python run_with_ngrok.py

pause
