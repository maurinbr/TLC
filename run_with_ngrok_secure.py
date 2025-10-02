import os
import shutil
import threading
import time
import ssl
import urllib3
from pyngrok import ngrok
from app import app
from app.utils.paths import get_tlc_data_path

# Désactiver les avertissements SSL pour ngrok
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration SSL plus permissive pour les tests
ssl._create_default_https_context = ssl._create_unverified_context


def sync_config_files():
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
                print(f" Fichier {filename} synchronisé avec succès")
            except Exception as e:
                print(f" Erreur lors de la copie de {filename}: {e}")
        else:
            print(f" Fichier {filename} introuvable dans {source_dir}")


def start_flask_server():
    """Démarre le serveur Flask"""
    print("Démarrage du serveur Flask...")
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


def main():
    print(" TLC - Démarrage avec tunnel ngrok (mode SSL permissif)")
    print("=" * 60)
    
    # Synchronisation des fichiers
    print("\n Synchronisation des fichiers de configuration...")
    sync_config_files()
    
    # Configuration ngrok avec gestion d'erreurs SSL
    print("\n Configuration du tunnel ngrok...")
    
    try:
        # Configuration ngrok avec gestion d'erreurs SSL
        ngrok_config = ngrok.PyngrokConfig(
            ngrok_path=None,  # Utilise ngrok système
            config_path=None,  # Utilise config par défaut
            auth_token=None,   # Utilise token configuré
            region="us"        # Région US (plus stable)
        )
        
        # Créer le tunnel avec gestion de compatibilité
        try:
            # Méthode moderne (ngrok v3+) - essayer sans bind_tls d'abord
            public_url = ngrok.connect(5000, pyngrok_config=ngrok_config)
        except Exception as e1:
            try:
                # Fallback: spécifier explicitement le protocole
                public_url = ngrok.connect(5000, "http", pyngrok_config=ngrok_config)
            except Exception as e2:
                # Fallback: configuration minimale
                print(f"  Tentative avec configuration minimale...")
                public_url = ngrok.connect(5000)
        
        print(f" Tunnel ngrok créé avec succès !")
        print(f" URL publique : {public_url}")
        print(f" URL locale   : http://localhost:5000")
        
        # Démarrer Flask dans un thread séparé
        flask_thread = threading.Thread(target=start_flask_server, daemon=True)
        flask_thread.start()
        
        print("\n Serveur Flask en cours de démarrage...")
        time.sleep(3)  # Attendre que Flask démarre
        
        print("\n Votre application TLC est maintenant accessible en ligne !")
        print(f" Partagez cette URL : {public_url}")
        print("\n  IMPORTANT :")
        print("   - Gardez cette fenêtre ouverte pour maintenir le tunnel")
        print("   - Le tunnel se ferme automatiquement à l'arrêt du script")
        print("   - Appuyez sur Ctrl+C pour arrêter le serveur")
        
        try:
            # Garder le script en vie
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n Arrêt du serveur...")
            ngrok.disconnect(public_url)
            ngrok.kill()
            print(" Tunnel fermé et serveur arrêté")
            
    except Exception as e:
        error_msg = str(e).lower()
        print(f" Erreur ngrok : {e}")
        
        if "invalid tunnel configuration" in error_msg or "field options not found" in error_msg:
            print("\n Erreur de configuration ngrok détectée")
            print("\n Solutions :")
            print("1. Mise à jour de pyngrok : pip install --upgrade pyngrok")
            print("2. Mise à jour de ngrok : ngrok update")
            print("3. Vérification de la version : ngrok version")
            print("4. Reset de la configuration : ngrok config reset")
            
        elif "ssl" in error_msg or "certificate" in error_msg or "tls" in error_msg:
            print("\n Erreur de certificat SSL détectée")
            print("\n Solutions :")
            print("1. Mise à jour des certificats : pip install --upgrade certifi requests urllib3")
            print("2. Vérification du firewall/antivirus")
            print("3. Utilisation d'un VPN si vous êtes sur un réseau d'entreprise")
            print("4. Test avec : ngrok http 5000 (en ligne de commande)")
            
        elif "authtoken" in error_msg or "authenticate" in error_msg:
            print("\n Erreur d'authentification ngrok")
            print("Vérifiez votre token avec : ngrok config check")
            
        else:
            print("\n Solutions possibles :")
            print("- Vérifiez votre connexion internet")
            print("- Vérifiez que le port 5000 n'est pas déjà utilisé")
            print("- Essayez de redémarrer ngrok : ngrok kill puis relancer")


if __name__ == '__main__':
    main()
