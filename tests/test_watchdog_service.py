import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import pytest
from app.services import watchdog_service

def test_image_detection():
    # Purge la liste partagée
    watchdog_service.images_detected.clear()
    # Dossier Analyses réel
    analyses_dir = os.path.expanduser(r'C:/Users/bruno/OneDrive/Analyses')
    # Crée une image factice
    img_path = os.path.join(analyses_dir, 'test_image_watchdog.jpg')
    try:
        with open(img_path, 'wb') as f:
            f.write(b'\xff\xd8\xff')  # header JPEG minimal
        # Attend que le watchdog détecte l'image
        for _ in range(20):
            if 'test_image_watchdog.jpg' in watchdog_service.images_detected:
                break
            time.sleep(1)
        assert 'test_image_watchdog.jpg' in watchdog_service.images_detected
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)
