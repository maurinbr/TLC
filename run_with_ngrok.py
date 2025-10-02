import os
import shutil
import threading
import time
from pyngrok import ngrok
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


def main():
    print("🚀 TLC - Démarrage avec tunnel ngrok")
    print("=" * 50)
    
    # Synchronisation des fichiers
    print("\n📁 Synchronisation des fichiers de configuration...")
    sync_config_files()
    
    # Configuration ngrok
    print("\n🌐 Configuration du tunnel ngrok...")
    
    # Vérifier si un token d'authentification est configuré
    try:
        # Essayer de créer un tunnel pour voir si ngrok est configuré
        public_url = ngrok.connect(5000, "http")
        print(f"✅ Tunnel ngrok créé avec succès !")
        print(f"🔗 URL publique : {public_url}")
        print(f"🏠 URL locale   : http://localhost:5000")
        
        # Démarrer Flask dans un thread séparé
        flask_thread = threading.Thread(target=start_flask_server, daemon=True)
        flask_thread.start()
        
        print("\n🔧 Serveur Flask en cours de démarrage...")
        time.sleep(2)  # Attendre que Flask démarre
        
        print("\n🎉 Votre application TLC est maintenant accessible en ligne !")
        print(f"📱 Partagez cette URL : {public_url}")
        print("\n⚠️  IMPORTANT :")
        print("   - Gardez cette fenêtre ouverte pour maintenir le tunnel")
        print("   - Le tunnel se ferme automatiquement à l'arrêt du script")
        print("   - Appuyez sur Ctrl+C pour arrêter le serveur")
        
        try:
            # Garder le script en vie
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Arrêt du serveur...")
            ngrok.disconnect(public_url)
            ngrok.kill()
            print("✅ Tunnel fermé et serveur arrêté")
            
    except Exception as e:
        error_msg = str(e)
        if "authtoken" in error_msg.lower() or "authenticate" in error_msg.lower():
            print("❌ Erreur d'authentification ngrok")
            print("\n🔑 Configuration requise :")
            print("1. Créez un compte gratuit sur https://ngrok.com")
            print("2. Récupérez votre token d'authentification")
            print("3. Configurez-le avec : ngrok authtoken VOTRE_TOKEN")
            print("4. Ou via Python : ngrok.set_auth_token('VOTRE_TOKEN')")
        else:
            print(f"❌ Erreur ngrok : {e}")
            print("\n🔧 Solutions possibles :")
            print("- Vérifiez votre connexion internet")
            print("- Vérifiez que le port 5000 n'est pas déjà utilisé")
            print("- Redémarrez le script")


if __name__ == '__main__':
    main()
