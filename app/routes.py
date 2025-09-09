import cv2
import numpy as np
from flask import send_file
from flask import render_template, request, jsonify
from app import app
from app.services.watchdog_service import start_watchdog, images_detected
from app.utils.paths import get_onedrive_base_path
import os
import json
import glob
import csv
import pandas as pd
import uuid
from werkzeug.utils import secure_filename 
from datetime import datetime 

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
# Le chemin s'adapte automatiquement à l'utilisateur courant
WATCH_PATH = get_onedrive_base_path()
start_watchdog(WATCH_PATH)

# Page de travail
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

# Route pour l'upload d'images
@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    if file:
        # Sécuriser le nom de fichier
        filename = secure_filename(file.filename)
        
        # Sauvegarder dans le dossier static/images
        STATIC_IMG_DIR = os.path.join(os.path.dirname(__file__), 'static', 'images')
        os.makedirs(STATIC_IMG_DIR, exist_ok=True)
        file_path = os.path.join(STATIC_IMG_DIR, filename)
        file.save(file_path)
        
        # Ajouter à la liste des images détectées
        images_detected.append(filename)
        
        return jsonify({
            'success': True, 
            'filename': filename,
            'message': f'Image {filename} uploadée avec succès'
        })
    
    return jsonify({'error': 'Erreur lors de l\'upload'}), 500

# Fichier de config pour le chemin surveillé
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'data', 'config.json')

def get_watch_path():
    # Priorité cookie, sinon fichier config, sinon défaut
    import flask
    cookie_path = flask.request.cookies.get('watch_path')
    if cookie_path:
        return cookie_path
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                conf = json.load(f)
            return conf.get('watch_path', WATCH_PATH)
        except Exception:
            pass
    return WATCH_PATH

# Route pour modifier le WATCH_PATH
@app.route('/set-watch-path', methods=['POST'])
def set_watch_path():
    data = request.get_json()
    new_path = data.get('watch_path')
    if new_path:
        # Sauvegarde dans le fichier config
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump({'watch_path': new_path}, f, ensure_ascii=False, indent=2)
        return jsonify({'ok': True, 'watch_path': new_path})
    return jsonify({'ok': False}), 400

# Route pour recevoir les coordonnées du clic
@app.route('/get-coords', methods=['POST'])
def get_coords():
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')
    displayX = data.get('displayX', x)  # Utilise x si displayX n'est pas fourni
    displayY = data.get('displayY', y)  # Utilise y si displayY n'est pas fourni
    print(f"Coordonnées image originale: x={x}, y={y}")
    print(f"Coordonnées affichées: x={displayX}, y={displayY}")
    # Acquisition RGB
    last_img = images_detected[-1] if images_detected else None
    rgb = None
    if last_img:
        img_path = os.path.join(os.path.dirname(__file__), 'static', 'images', last_img)
        if os.path.exists(img_path):
            img = cv2.imread(img_path)
            if img is not None:
                # OpenCV lit en BGR, donc on convertit
                if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
                    b, g, r = img[y, x]
                    rgb = [int(r), int(g), int(b)]
                    # Conversion en HSV
                    pixel_bgr = np.uint8([[[ b, g, r ]]])
                    pixel_hsv = cv2.cvtColor(pixel_bgr, cv2.COLOR_BGR2HSV)
                    h, s, v = pixel_hsv[0][0]
                    # Normalisation des valeurs HSV
                    h = float(h * 2)  # OpenCV utilise H sur [0,180], on convertit en [0,360]
                    s = float(s / 255.0)  # Conversion en [0,1]
                    v = float(v / 255.0)  # Conversion en [0,1]
                    hsv = [h, s, v]
    return jsonify({
        'ok': True, 
        'x': x, 
        'y': y, 
        'displayX': displayX,
        'displayY': displayY,
        'rgb': rgb, 
        'hsv': hsv
    })

# Route pour sauvegarder le journal des enregistrerments
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

# Route pour afficher le journal
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
    return render_template('parametres.html', active_page='parametres', WATCH_PATH=get_watch_path())

# Route pour obtenir le contenu de database.json
@app.route('/get-database')
def get_database():
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'database.json')
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify([])  # Retourne une liste vide si le fichier n'existe pas

# Route pour servir les images depuis le dossier surveillé
@app.route('/watch-images/<path:filename>')
def watch_images(filename):
    return send_file(os.path.join(WATCH_PATH, filename))


# Routes pour la chimithèque
@app.route('/chimotheque')
def chimotheque():
    return render_template('chimotheque.html', active_page='chimotheque')

@app.route('/get-chimotheque')
def get_chimotheque():
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'chimotheque.csv')
    if os.path.exists(csv_path):
        try:
            data = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify([])

@app.route('/save-chimotheque', methods=['POST'])
def save_chimotheque():
    try:
        data = request.get_json()
        csv_path = os.path.join(os.path.dirname(__file__), 'data', 'chimotheque.csv')
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            if data:
                fieldnames = ['boiteID', 'nom', 'loc', 'echantillon', 'contenu', 'notes']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for item in data:
                    # S'assurer que tous les champs existent
                    row = {
                        'boiteID': item.get('boiteID', ''),
                        'nom': item.get('nom', ''),
                        'loc': item.get('loc', ''),
                        'echantillon': item.get('echantillon', ''),
                        'contenu': item.get('contenu', ''),
                        'notes': item.get('notes', '')
                    }
                    writer.writerow(row)
        
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export-chimotheque')
def export_chimotheque():
    """Exporter les données de la chimithèque au format CSV"""
    try:
        # Chemin vers le fichier chimotheque.csv
        csv_path = os.path.join(os.path.dirname(__file__), 'data', 'chimotheque.csv')
        
        # Vérifier que le fichier existe
        if not os.path.exists(csv_path):
            return jsonify({'error': 'Fichier chimotheque.csv non trouvé'}), 404
        
        # Générer un nom de fichier avec la date
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f'chimotheque_{today}.csv'
        
        # Envoyer le fichier
        return send_file(
            csv_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        print(f"Erreur lors de l'export: {e}")
        return jsonify({'error': 'Erreur lors de l\'export'}), 500

# Route pour servir une image depuis OneDrive
@app.route('/onedrive-image')
def onedrive_image():
    import os
    from flask import send_file, request, abort
    from app.utils.paths import get_onedrive_search_paths
    
    rel_path = request.args.get('path')
    if not rel_path:
        abort(400, 'Paramètre path manquant')
    
    base_dirs = get_onedrive_search_paths()
    
    # TODO à sécuriser
    found_path = None
    for base in base_dirs:
        candidate = os.path.join(base, rel_path)
        if os.path.isfile(candidate):
            found_path = candidate
            break
    if not found_path:
        abort(404, 'Image non trouvée')
    return send_file(found_path)

# Routes pour PubMed Feed
@app.route('/pubmed-feed')
def pubmed_feed():
    return render_template('pubmed_feed.html', active_page='pubmed-feed')

@app.route('/get-pubmed-sets')
def get_pubmed_sets():
    """Récupérer tous les sets PubMed et leurs articles"""
    try:
        sets_path = os.path.join(os.path.dirname(__file__), 'data', 'pubmed_sets.json')
        
        if not os.path.exists(sets_path):
            # Créer le fichier avec le set par défaut
            default_sets = [{
                'id': str(uuid.uuid4()),
                'name': 'New Psychoactive Substances',
                'description': 'Substances psychoactives nouvelles - recherche exemple',
                'filename': 'csv-newpsychoa-set.csv',
                'created_date': datetime.now().isoformat()
            }]
            
            with open(sets_path, 'w', encoding='utf-8') as f:
                json.dump(default_sets, f, ensure_ascii=False, indent=2)
        
        # Charger les sets
        with open(sets_path, 'r', encoding='utf-8') as f:
            sets = json.load(f)
        
        # Charger les articles pour chaque set
        all_articles = []
        for set_data in sets:
            csv_path = os.path.join(os.path.dirname(__file__), 'data', set_data['filename'])
            articles = []
            
            if os.path.exists(csv_path):
                try:
                    # Essayer d'importer pandas localement
                    try:
                        import pandas as pd
                        df = pd.read_csv(csv_path)
                        
                        # Ajouter la colonne 'Read' si elle n'existe pas
                        if 'Read' not in df.columns:
                            df['Read'] = 'false'
                            # Sauvegarder le CSV modifié
                            df.to_csv(csv_path, index=False)
                        
                        # Ajouter la colonne 'Rating' si elle n'existe pas
                        if 'Rating' not in df.columns:
                            df['Rating'] = 0.0
                            # Sauvegarder le CSV modifié
                            df.to_csv(csv_path, index=False)
                        
                        # Convertir en liste de dictionnaires
                        articles = df.to_dict('records')
                        
                        # Remplacer les valeurs NaN par None (sera converti en null en JSON)
                        import math
                        for article in articles:
                            for key, value in article.items():
                                if isinstance(value, float) and math.isnan(value):
                                    article[key] = None
                                # Normaliser les valeurs Read en string minuscules
                                elif key == 'Read':
                                    article[key] = str(value).lower()
                        
                    except ImportError:
                        print(f"Pandas non disponible, utilisation de csv standard pour {set_data['filename']}")
                        # Fallback vers la méthode CSV classique
                        with open(csv_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            articles = []
                            for row in reader:
                                # Ajouter la colonne Read si elle n'existe pas
                                if 'Read' not in row:
                                    row['Read'] = 'false'
                                articles.append(row)
                    
                except Exception as e:
                    print(f"Erreur lecture CSV {set_data['filename']}: {e}")
                    articles = []
            set_data['articles'] = articles
            all_articles.extend(articles)
        
        return jsonify({
            'sets': sets,
            'articles': all_articles
        })
        
    except Exception as e:
        print(f"Erreur get_pubmed_sets: {e}")
        return jsonify({'sets': [], 'articles': []}), 500

@app.route('/add-pubmed-set', methods=['POST'])
def add_pubmed_set():
    """Ajouter un nouveau set PubMed"""
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        csv_file = request.files.get('csvFile')
        
        if not name or not csv_file:
            return jsonify({'success': False, 'error': 'Nom et fichier CSV requis'}), 400
        
        # Générer un nom de fichier sécurisé
        filename = secure_filename(csv_file.filename)
        if not filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Le fichier doit être un CSV'}), 400
        
        # Ajouter un UUID au nom pour éviter les conflits
        base_name = filename.rsplit('.', 1)[0]
        unique_filename = f"{base_name}_{str(uuid.uuid4())[:8]}.csv"
        
        # Sauvegarder le fichier CSV
        csv_path = os.path.join(os.path.dirname(__file__), 'data', unique_filename)
        csv_file.save(csv_path)
        
        # Valider et traiter le CSV (vérifier qu'il a les colonnes requises)
        try:
            # Essayer d'utiliser pandas d'abord
            try:
                import pandas as pd
                df = pd.read_csv(csv_path)
                
                # Vérifier les colonnes requises
                required_headers = ['PMID', 'Title', 'Authors']
                missing_headers = [h for h in required_headers if h not in df.columns]
                
                if missing_headers:
                    os.remove(csv_path)  # Supprimer le fichier invalide
                    return jsonify({
                        'success': False, 
                        'error': f'Colonnes manquantes dans le CSV: {", ".join(missing_headers)}'
                    }), 400
                
                # Ajouter la colonne 'Read' si elle n'existe pas
                if 'Read' not in df.columns:
                    df['Read'] = 'false'
                    # Sauvegarder le CSV modifié
                    df.to_csv(csv_path, index=False)
                    
            except ImportError:
                # Fallback sans pandas
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    required_headers = ['PMID', 'Title', 'Authors']
                    
                    missing_headers = [h for h in required_headers if h not in headers]
                    if missing_headers:
                        os.remove(csv_path)  # Supprimer le fichier invalide
                        return jsonify({
                            'success': False, 
                            'error': f'Colonnes manquantes dans le CSV: {", ".join(missing_headers)}'
                        }), 400
                
                # Ajouter la colonne Read si nécessaire avec CSV standard
                if 'Read' not in headers:
                    # Lire tout le CSV
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                    
                    # Ajouter la colonne Read
                    fieldnames = list(headers) + ['Read']
                    
                    # Réécrire le CSV
                    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for row in rows:
                            row['Read'] = 'false'
                            writer.writerow(row)
                
        except Exception as e:
            os.remove(csv_path)  # Supprimer le fichier en cas d'erreur
            return jsonify({'success': False, 'error': f'Erreur de lecture du CSV: {str(e)}'}), 400
        
        # Charger les sets existants
        sets_path = os.path.join(os.path.dirname(__file__), 'data', 'pubmed_sets.json')
        sets = []
        
        if os.path.exists(sets_path):
            with open(sets_path, 'r', encoding='utf-8') as f:
                sets = json.load(f)
        
        # Ajouter le nouveau set
        new_set = {
            'id': str(uuid.uuid4()),
            'name': name,
            'description': description,
            'filename': unique_filename,
            'created_date': datetime.now().isoformat()
        }
        
        sets.append(new_set)
        
        # Sauvegarder les sets
        with open(sets_path, 'w', encoding='utf-8') as f:
            json.dump(sets, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'set': new_set})
        
    except Exception as e:
        print(f"Erreur add_pubmed_set: {e}")
        return jsonify({'success': False, 'error': 'Erreur serveur'}), 500

@app.route('/toggle-article-read', methods=['POST'])
def toggle_article_read():
    """Marquer/démarquer un article comme lu dans TOUS les CSV (y compris les doublons)"""
    try:
        data = request.get_json()
        set_id = data.get('set_id')
        pmid = data.get('pmid')
        
        if not set_id or not pmid:
            return jsonify({'success': False, 'error': 'set_id et pmid requis'}), 400
        
        # Convertir pmid en entier pour la comparaison
        try:
            pmid_int = int(pmid)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'PMID invalide'}), 400
        
        # Charger les sets
        sets_path = os.path.join(os.path.dirname(__file__), 'data', 'pubmed_sets.json')
        with open(sets_path, 'r', encoding='utf-8') as f:
            sets = json.load(f)
        
        # Trouver l'article de référence pour obtenir son DOI
        target_set = next((s for s in sets if s['id'] == set_id), None)
        if not target_set:
            return jsonify({'success': False, 'error': 'Set non trouvé'}), 404
        
        # Charger le CSV du set de référence pour trouver le DOI
        csv_path = os.path.join(os.path.dirname(__file__), 'data', target_set['filename'])
        if not os.path.exists(csv_path):
            return jsonify({'success': False, 'error': 'Fichier CSV non trouvé'}), 404
        
        target_doi = None
        new_status = None
        
        # Essayer d'utiliser pandas en priorité
        try:
            import pandas as pd
            import math
            
            # Lire le CSV de référence avec pandas
            df = pd.read_csv(csv_path)
            
            # Ajouter la colonne 'Read' si elle n'existe pas
            if 'Read' not in df.columns:
                df['Read'] = 'false'
            
            # Trouver l'article par PMID pour obtenir son DOI et déterminer le nouveau statut
            mask = df['PMID'] == pmid_int
            if mask.any():
                target_doi = df.loc[mask, 'DOI'].iloc[0]
                current_status = str(df.loc[mask, 'Read'].iloc[0]).lower()
                new_status = 'false' if current_status == 'true' else 'true'
                print(f"Article PMID {pmid_int}, DOI: {target_doi}, nouveau statut: {new_status}")
            else:
                return jsonify({'success': False, 'error': 'Article non trouvé'}), 404
            
            # Maintenant, mettre à jour TOUS les CSV qui contiennent des articles avec ce DOI
            updated_count = 0
            
            for current_set in sets:
                current_csv_path = os.path.join(os.path.dirname(__file__), 'data', current_set['filename'])
                
                if not os.path.exists(current_csv_path):
                    continue
                
                try:
                    # Lire le CSV actuel
                    current_df = pd.read_csv(current_csv_path)
                    
                    # Ajouter la colonne 'Read' si elle n'existe pas
                    if 'Read' not in current_df.columns:
                        current_df['Read'] = 'false'
                    
                    # Trouver tous les articles avec le même DOI
                    doi_mask = current_df['DOI'] == target_doi
                    if doi_mask.any():
                        # Mettre à jour tous les articles avec ce DOI
                        current_df.loc[doi_mask, 'Read'] = new_status
                        
                        # Sauvegarder le CSV
                        current_df.to_csv(current_csv_path, index=False)
                        
                        articles_updated_in_set = doi_mask.sum()
                        updated_count += articles_updated_in_set
                        print(f"Mis à jour {articles_updated_in_set} articles dans {current_set['name']}")
                
                except Exception as e:
                    print(f"Erreur lors de la mise à jour du set {current_set['name']}: {e}")
                    continue
            
            print(f"Total: {updated_count} articles mis à jour avec le DOI {target_doi}")
            
            return jsonify({
                'success': True, 
                'read': new_status == 'true',
                'pmid': pmid,
                'updated_count': updated_count,
                'doi': target_doi
            })
                
        except ImportError:
            print("Pandas non disponible - fonctionnalité doublons non supportée avec csv standard")
            return jsonify({'success': False, 'error': 'Pandas requis pour traiter les doublons'}), 500
        
    except Exception as e:
        print(f"Erreur toggle_article_read: {e}")
        return jsonify({'success': False, 'error': 'Erreur serveur'}), 500

@app.route('/rate-article', methods=['POST'])
def rate_article():
    """Attribuer une note à un article et à tous ses doublons"""
    try:
        data = request.get_json()
        set_id = data.get('set_id')
        pmid = data.get('pmid')
        rating = data.get('rating')
        
        if not set_id or not pmid or rating is None:
            return jsonify({'success': False, 'error': 'set_id, pmid et rating requis'}), 400
        
        # Valider la note (doit être entre 0 et 1)
        try:
            rating_float = float(rating)
            if rating_float < 0 or rating_float > 1:
                return jsonify({'success': False, 'error': 'Rating doit être entre 0 et 1'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Rating invalide'}), 400
        
        # Convertir pmid en entier pour la comparaison
        try:
            pmid_int = int(pmid)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'PMID invalide'}), 400
        
        # Charger les sets
        sets_path = os.path.join(os.path.dirname(__file__), 'data', 'pubmed_sets.json')
        with open(sets_path, 'r', encoding='utf-8') as f:
            sets = json.load(f)
        
        # Trouver l'article de référence pour obtenir son DOI
        target_set = next((s for s in sets if s['id'] == set_id), None)
        if not target_set:
            return jsonify({'success': False, 'error': 'Set non trouvé'}), 404
        
        # Charger le CSV du set de référence pour trouver le DOI
        csv_path = os.path.join(os.path.dirname(__file__), 'data', target_set['filename'])
        if not os.path.exists(csv_path):
            return jsonify({'success': False, 'error': 'Fichier CSV non trouvé'}), 404
        
        target_doi = None
        
        # Essayer d'utiliser pandas en priorité
        try:
            import pandas as pd
            import math
            
            # Lire le CSV de référence avec pandas
            df = pd.read_csv(csv_path)
            
            # Ajouter les colonnes manquantes si nécessaire
            if 'Read' not in df.columns:
                df['Read'] = 'false'
            if 'Rating' not in df.columns:
                df['Rating'] = 0.0
            
            # Trouver l'article par PMID pour obtenir son DOI
            mask = df['PMID'] == pmid_int
            if mask.any():
                target_doi = df.loc[mask, 'DOI'].iloc[0]
                print(f"Article PMID {pmid_int}, DOI: {target_doi}, nouvelle note: {rating_float}")
            else:
                return jsonify({'success': False, 'error': 'Article non trouvé'}), 404
            
            # Maintenant, mettre à jour TOUS les CSV qui contiennent des articles avec ce DOI
            updated_count = 0
            
            for current_set in sets:
                current_csv_path = os.path.join(os.path.dirname(__file__), 'data', current_set['filename'])
                
                if not os.path.exists(current_csv_path):
                    continue
                
                try:
                    # Lire le CSV actuel
                    current_df = pd.read_csv(current_csv_path)
                    
                    # Ajouter les colonnes manquantes si nécessaire
                    if 'Read' not in current_df.columns:
                        current_df['Read'] = 'false'
                    if 'Rating' not in current_df.columns:
                        current_df['Rating'] = 0.0
                    
                    # Trouver tous les articles avec le même DOI
                    doi_mask = current_df['DOI'] == target_doi
                    if doi_mask.any():
                        # Mettre à jour la note de tous les articles avec ce DOI
                        current_df.loc[doi_mask, 'Rating'] = rating_float
                        
                        # Sauvegarder le CSV
                        current_df.to_csv(current_csv_path, index=False)
                        
                        articles_updated_in_set = doi_mask.sum()
                        updated_count += articles_updated_in_set
                        print(f"Note mise à jour pour {articles_updated_in_set} articles dans {current_set['name']}")
                
                except Exception as e:
                    print(f"Erreur lors de la mise à jour de la note du set {current_set['name']}: {e}")
                    continue
            
            print(f"Total: {updated_count} articles notés avec le DOI {target_doi}")
            
            return jsonify({
                'success': True, 
                'rating': rating_float,
                'pmid': pmid,
                'updated_count': updated_count,
                'doi': target_doi
            })
                
        except ImportError:
            print("Pandas non disponible - fonctionnalité rating non supportée avec csv standard")
            return jsonify({'success': False, 'error': 'Pandas requis pour traiter les notes'}), 500
        
    except Exception as e:
        print(f"Erreur rate_article: {e}")
        return jsonify({'success': False, 'error': 'Erreur serveur'}), 500

@app.route('/delete-pubmed-set/<set_id>', methods=['DELETE'])
def delete_pubmed_set(set_id):
    """Supprimer un set PubMed"""
    try:
        sets_path = os.path.join(os.path.dirname(__file__), 'data', 'pubmed_sets.json')
        
        if not os.path.exists(sets_path):
            return jsonify({'success': False, 'error': 'Aucun set trouvé'}), 404
        
        # Charger les sets
        with open(sets_path, 'r', encoding='utf-8') as f:
            sets = json.load(f)
        
        # Trouver le set à supprimer
        set_to_delete = next((s for s in sets if s['id'] == set_id), None)
        
        if not set_to_delete:
            return jsonify({'success': False, 'error': 'Set non trouvé'}), 404
        
        # Supprimer le fichier CSV (sauf s'il s'agit du fichier exemple)
        if set_to_delete['filename'] != 'csv-newpsychoa-set.csv':
            csv_path = os.path.join(os.path.dirname(__file__), 'data', set_to_delete['filename'])
            if os.path.exists(csv_path):
                os.remove(csv_path)
        
        # Supprimer le set de la liste
        sets = [s for s in sets if s['id'] != set_id]
        
        # Sauvegarder les sets mis à jour
        with open(sets_path, 'w', encoding='utf-8') as f:
            json.dump(sets, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Erreur delete_pubmed_set: {e}")
        return jsonify({'success': False, 'error': 'Erreur serveur'}), 500