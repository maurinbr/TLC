import cv2
import numpy as np
from flask import send_file
from flask import render_template, request, jsonify
from app import app
from app.services.watchdog_service import start_watchdog, images_detected
import os
import json
import glob

# Purge le dossier static/images au démarrage
print("Purge du dossier static/images...")
STATIC_IMG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'images'))
if os.path.exists(STATIC_IMG_DIR):
    for f in glob.glob(os.path.join(STATIC_IMG_DIR, '*')):
        try:
            os.remove(f)
        except Exception:
            pass

# Démarre le watchdog au lancement de l'app Flask
WATCH_PATH = os.path.expanduser(r'C:/Users/bruno/OneDrive/Analyses')
start_watchdog(WATCH_PATH)

@app.route('/')
@app.route('/index')
def index():
    last_img = images_detected[-1] if images_detected else None
    return render_template('index.html', images=images_detected, last_img=last_img)

# Route pour obtenir le négatif de l'image
@app.route('/image-process')
def image_process():
    last_img = images_detected[-1] if images_detected else None
    if not last_img:
        return "Aucune image", 404
    img_path = os.path.join(os.path.dirname(__file__), 'static', 'images', last_img)
    if not os.path.exists(img_path):
        return "Image introuvable", 404
    img = cv2.imread(img_path)
    if img is None:
        return "Erreur lecture image", 500
    neg = cv2.bitwise_not(img)
    out_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'negatif_' + last_img)
    cv2.imwrite(out_path, neg)
    return send_file(out_path, mimetype='image/jpeg')

# Route pour recevoir les coordonnées du clic
@app.route('/get-coords', methods=['POST'])
def get_coords():
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')
    print(f"Coordonnées cliquées: x={x}, y={y}")
    return jsonify({'ok': True, 'x': x, 'y': y})

@app.route('/save-journal', methods=['POST'])
def save_journal():
    data = request.get_json()
    journal_path = os.path.join(os.path.dirname(__file__), 'data', 'journal.json')
    os.makedirs(os.path.dirname(journal_path), exist_ok=True)
    # Charge l'existant
    if os.path.exists(journal_path):
        with open(journal_path, 'r', encoding='utf-8') as f:
            try:
                journal = json.load(f)
                if isinstance(journal, dict):
                    journal = [journal]
            except Exception:
                journal = []
    else:
        journal = []
    journal.append(data)
    with open(journal_path, 'w', encoding='utf-8') as f:
        json.dump(journal, f, ensure_ascii=False, indent=2)
    return jsonify({'ok': True})

@app.route('/journal')
def journal():
    import os, json
    journal_path = os.path.join(os.path.dirname(__file__), 'data', 'journal.json')
    if os.path.exists(journal_path):
        with open(journal_path, 'r', encoding='utf-8') as f:
            try:
                journal = json.load(f)
            except Exception:
                journal = []
    else:
        journal = []
    return render_template('journal.html', active_page='journal', journal=journal)

# Route pour sauvegarder les attribus d'un échantillon
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

@app.route('/explorateur')
def explorateur():
    return render_template('explorateur.html', active_page='explorateur')

@app.route('/database')
def database():
    return render_template('database.html', active_page='database')

@app.route('/parametres')
def parametre():
    return render_template('parametres.html', active_page='parametres', WATCH_PATH=WATCH_PATH)