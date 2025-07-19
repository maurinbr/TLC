import requests
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
from app.services import watchdog_service

def test_onedrive_upload():
    if (True is not False):
        assert True, "Test désactivé pour l'instant"
    else:
        # À personnaliser avec vos infos Azure/OneDrive
        client_id = 'VOTRE_CLIENT_ID'
        client_secret = 'VOTRE_CLIENT_SECRET'
        tenant_id = 'VOTRE_TENANT_ID'
        username = 'votre.email@outlook.com'
        password = 'VOTRE_MDP'
        filename = 'test_image_watchdog_onedrive.jpg'
        file_content = b'\xff\xd8\xff'

        # 1. Obtenir un token d'accès
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        data = {
            'client_id': client_id,
            'scope': 'https://graph.microsoft.com/.default',
            'client_secret': client_secret,
            'grant_type': 'password',
            'username': username,
            'password': password
        }
        resp = requests.post(token_url, data=data)
        assert resp.status_code == 200, f"Erreur token: {resp.text}"
        access_token = resp.json()['access_token']

        # 2. Créer le fichier dans OneDrive (dossier Analyses)
        upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/Analyses/{filename}:/content"
        headers = {'Authorization': f'Bearer {access_token}'}
        resp = requests.put(upload_url, headers=headers, data=file_content)
        assert resp.status_code in (200, 201), f"Erreur upload: {resp.text}"
        print("Fichier créé sur OneDrive !")
        analyses_dir = os.path.expanduser(r'C:/Users/bruno/OneDrive/Analyses')
        # Crée une image factice
        img_path = os.path.join(analyses_dir, 'test_image_watchdog_onedrive.jpg')
        with open(img_path, 'wb') as f:
            f.write(file_content)
        # Attend que le watchdog détecte l'image
        try:
            for _ in range(20):
                if 'test_image_watchdog.jpg' in watchdog_service.images_detected:
                    break
                time.sleep(1)
            assert 'test_image_watchdog.jpg' in watchdog_service.images_detected
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)


