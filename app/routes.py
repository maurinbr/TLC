from flask import render_template, request, jsonify
from app import app
from app.services.watchdog_service import start_watchdog, images_detected
import os
import json

# Démarre le watchdog au lancement de l'app Flask
WATCH_PATH = os.path.expanduser(r'C:/Users/bruno/OneDrive/Analyses')
start_watchdog(WATCH_PATH)

@app.route('/')
@app.route('/index')
def index():
    last_img = images_detected[-1] if images_detected else None
    return render_template('index.html', images=images_detected, last_img=last_img)

@app.route('/save', methods=['POST'])
def save():
    data = request.get_json()
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'database.json')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    # Charge l'existant
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            try:
                db = json.load(f)
                if isinstance(db, dict):
                    db = [db]
            except Exception:
                db = []
    else:
        db = []
    db.append(data)
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    return jsonify({'ok': True})
