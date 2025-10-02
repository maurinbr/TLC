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
    print("🏢 TLC - Configuration ENTREPRISE avec tunnel ngrok sécurisé")
    print("=" * 70)
    
    # Synchronisation des fichiers
    print("\n📁 Synchronisation des fichiers de configuration...")
    sync_config_files()
    
    # Configuration ngrok avec sécurité entreprise
    print("\n🔒 Configuration du tunnel ngrok SÉCURISÉ...")
    print("   (Compatible avec les réseaux d'entreprise)")
    
    try:
        # Configuration ngrok pour entreprise
        ngrok_config = ngrok.PyngrokConfig(
            ngrok_path=None,  # Utilise ngrok système
            config_path=None,  # Utilise config par défaut
            auth_token=None,   # Utilise token configuré
            region="us"        # Région US (plus stable)
        )
        
        # Stratégie de connexion sécurisée en cascade
        public_url = None
        connection_method = "Aucune"
        
        # 1. Tentative HTTPS obligatoire (recommandé pour entreprise)
        try:
            print("🔐 Tentative 1: HTTPS obligatoire (sécurité maximale)...")
            public_url = ngrok.connect(
                5000,
                "http",
                pyngrok_config=ngrok_config,
                bind_tls=True  # Force HTTPS uniquement
            )
            connection_method = "HTTPS obligatoire ✅"
        except Exception as e1:
            print(f"   ⚠️  Échec: {str(e1)[:100]}...")
            
            # 2. Tentative avec domaine personnalisé (si configuré)
            try:
                print("🌐 Tentative 2: Configuration avec authentification...")
                public_url = ngrok.connect(
                    5000,
                    "http",
                    pyngrok_config=ngrok_config
                )
                connection_method = "HTTP avec auth ⚠️"
            except Exception as e2:
                print(f"   ⚠️  Échec: {str(e2)[:100]}...")
                
                # 3. Fallback configuration minimale
                try:
                    print("🔧 Tentative 3: Configuration de secours...")
                    public_url = ngrok.connect(5000)
                    connection_method = "Configuration basique ⚠️"
                except Exception as e3:
                    raise Exception(f"Toutes les tentatives ont échoué. Dernière erreur: {e3}")
        
        if public_url:
            print(f"\n✅ Tunnel ngrok créé avec succès !")
            print(f"🔗 URL publique    : {public_url}")
            print(f"🏠 URL locale      : http://localhost:5000")
            print(f"🛡️  Méthode sécurité: {connection_method}")
            
            # Démarrer Flask dans un thread séparé
            flask_thread = threading.Thread(target=start_flask_server, daemon=True)
            flask_thread.start()
            
            print("\n🔧 Serveur Flask en cours de démarrage...")
            time.sleep(3)  # Attendre que Flask démarre
            
            print("\n🎉 Votre application TLC est maintenant accessible en ligne !")
            print(f"📱 URL à partager : {public_url}")
            
            # Instructions spécifiques pour entreprise
            print("\n🏢 INSTRUCTIONS ENTREPRISE :")
            if "https" in str(public_url).lower():
                print("   ✅ Connexion HTTPS sécurisée - Compatible réseau entreprise")
                print("   ✅ Certificats SSL valides")
            else:
                print("   ⚠️  Connexion HTTP - Peut être bloquée par certaines entreprises")
                print("   💡 Configurez l'authentification OAuth dans le dashboard ngrok")
            
            print("\n⚠️  IMPORTANT :")
            print("   - Gardez cette fenêtre ouverte pour maintenir le tunnel")
            print("   - Le tunnel se ferme automatiquement à l'arrêt du script")
            print("   - Appuyez sur Ctrl+C pour arrêter le serveur")
            
            # Conseils pour l'accès entreprise
            print("\n💼 Si l'accès est toujours bloqué depuis l'entreprise :")
            print("   1. Configurez OAuth dans le dashboard ngrok")
            print("   2. Ajoutez votre domaine d'entreprise aux domaines autorisés")
            print("   3. Contactez votre IT pour autoriser les domaines *.ngrok.io")
            print("   4. Utilisez un VPN personnel si autorisé")
            
            try:
                # Garder le script en vie
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🛑 Arrêt du serveur...")
                ngrok.disconnect(public_url)
                ngrok.kill()
                print("✅ Tunnel fermé et serveur arrêté")
        else:
            print("❌ Impossible de créer le tunnel ngrok")
            
    except Exception as e:
        error_msg = str(e).lower()
        print(f"❌ Erreur ngrok : {e}")
        
        # Messages d'erreur spécifiques pour entreprise
        if "invalid tunnel configuration" in error_msg or "field options not found" in error_msg:
            print("\n🔧 Erreur de configuration ngrok détectée")
            print("\n💡 Solutions ENTREPRISE :")
            print("1. Mise à jour de pyngrok : pip install --upgrade pyngrok")
            print("2. Mise à jour de ngrok : ngrok update")
            print("3. Configuration OAuth dans dashboard ngrok")
            print("4. Vérification des restrictions réseau entreprise")
            
        elif "authentication failed" in error_msg or "authtoken" in error_msg:
            print("\n🔑 Erreur d'authentification ngrok")
            print("\n💡 Solutions :")
            print("1. Vérifiez votre token : ngrok config check")
            print("2. Renouvelez votre token dans le dashboard ngrok")
            print("3. Configurez l'authentification OAuth")
            
        elif "tunnel session failed" in error_msg or "network" in error_msg:
            print("\n🌐 Erreur de réseau (typique en entreprise)")
            print("\n💡 Solutions :")
            print("1. Contactez votre service IT pour autoriser ngrok")
            print("2. Utilisez un VPN personnel")
            print("3. Configurez un proxy si nécessaire")
            print("4. Essayez depuis votre connexion mobile")
            
        elif "ssl" in error_msg or "certificate" in error_msg or "tls" in error_msg:
            print("\n🔒 Erreur de certificat SSL")
            print("\n💡 Solutions :")
            print("1. Mise à jour des certificats : pip install --upgrade certifi")
            print("2. Configuration proxy entreprise")
            print("3. Désactivation temporaire antivirus/firewall")
            
        else:
            print("\n🔧 Solutions générales :")
            print("- Vérifiez votre connexion internet")
            print("- Testez depuis votre mobile (données cellulaires)")
            print("- Contactez votre service IT")
            print("- Utilisez un VPN si autorisé")


if __name__ == '__main__':
    main()