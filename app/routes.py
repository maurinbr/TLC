from flask import render_template
from app import app
from app.services.watchdog_service import start_watchdog, images_detected
import os

# Démarre le watchdog au lancement de l'app Flask
WATCH_PATH = os.path.expanduser(r'C:/Users/bruno/OneDrive/Analyses')
start_watchdog(WATCH_PATH)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', images=images_detected)
