import os
import shutil
from app import app
from app.utils.paths import get_tlc_data_path


def sync_config_files():
    """
    Synchronise les fichiers de configuration depuis le dossier local
    vers l'application actuelle au démarrage.
    """
    # Dossier source (local) - utilise la fonction factorisée
    source_dir = get_tlc_data_path()
    
    # Dossier destination (application actuelle)
    dest_dir = os.path.join(os.path.dirname(__file__), "app", "data")
    
    # Liste des fichiers à synchroniser
    files_to_sync = [
        "config.json",
        "database.json", 
        "echantillons.json",
        "chimotheque.csv"
    ]
    
    # Vérifier que le dossier source existe
    if not os.path.exists(source_dir):
        print(f"Attention: Le dossier source {source_dir} n'existe pas.")
        return
    
    # Créer le dossier destination s'il n'existe pas
    os.makedirs(dest_dir, exist_ok=True)
    
    # Copier chaque fichier
    for filename in files_to_sync:
        source_file = os.path.join(source_dir, filename)
        dest_file = os.path.join(dest_dir, filename)
        
        if os.path.exists(source_file):
            try:
                shutil.copy2(source_file, dest_file)
                print(f"✓ Fichier {filename} synchronisé avec succès")
            except Exception as e:
                print(f"✗ Erreur lors de la copie de {filename}: {e}")
        else:
            print(f"⚠ Fichier {filename} introuvable dans {source_dir}")


if __name__ == '__main__':
    print("Synchronisation des fichiers de configuration...")
    sync_config_files()
    print("Démarrage de l'application Flask...")
    # host='0.0.0.0' permet l'accès depuis d'autres machines du réseau
    app.run(debug=True, host='0.0.0.0', port=5000)
