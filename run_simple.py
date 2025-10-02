import os
import shutil
import threading
import time
import subprocess
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


def start_flask_server():
    """Démarre le serveur Flask"""
    print("Démarrage du serveur Flask...")
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


def start_ngrok_tunnel():
    """Démarre le tunnel ngrok via ligne de commande"""
    try:
        print("🌐 Création du tunnel ngrok...")
        # Utiliser ngrok en ligne de commande (plus stable)
        result = subprocess.run(
            ["ngrok", "http", "5000", "--log=stdout"],
            capture_output=False,
            text=True
        )
        return result
    except Exception as e:
        print(f"Erreur lors du démarrage de ngrok : {e}")
        return None


def main():
    print("🚀 TLC - Démarrage avec tunnel ngrok (méthode CLI)")
    print("=" * 55)
    
    # Synchronisation des fichiers
    print("\n📁 Synchronisation des fichiers de configuration...")
    sync_config_files()
    
    print("\n🔧 Instructions pour le tunnel ngrok :")
    print("1. Dans ce terminal, Flask va démarrer sur le port 5000")
    print("2. Ouvrez un NOUVEAU terminal PowerShell")
    print("3. Exécutez : ngrok http 5000")
    print("4. Copiez l'URL publique générée")
    print("\n" + "="*55)
    
    # Démarrer Flask
    print("\n🚀 Démarrage du serveur Flask...")
    print("Votre serveur sera accessible sur : http://localhost:5000")
    print("\n⚠️  Pour arrêter le serveur, appuyez sur Ctrl+C")
    print("="*55 + "\n")
    
    try:
        # Démarrer Flask directement (plus simple)
        app.run(host='127.0.0.1', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du serveur Flask...")
        print("✅ Serveur arrêté")


if __name__ == '__main__':
    main()
