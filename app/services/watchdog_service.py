from watchdog.events import FileSystemEventHandler, EVENT_TYPE_CREATED, EVENT_TYPE_MODIFIED
from watchdog.observers.polling import PollingObserver  # <— important
import threading
import time
import os
import shutil

# Liste partagée des images détectées (noms de fichiers)
images_detected = []

class MonHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            print(f"Fichier créé : {event.src_path}")
            # Copie l'image dans static/images
            dest_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'images')
            dest_dir = os.path.abspath(dest_dir)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, os.path.basename(event.src_path))
            # Retry copy if file is locked
            for i in range(10):
                try:
                    shutil.copy2(event.src_path, dest_path)
                    images_detected.append(os.path.basename(event.src_path))
                    break
                except PermissionError:
                    time.sleep(0.5)
            else:
                print(f"Impossible de copier {event.src_path} après plusieurs tentatives.")

    def on_deleted(self, event):
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            if filename in images_detected:
                print(f"Fichier supprimé : {event.src_path}")
                images_detected.remove(filename)
                # Supprime aussi du dossier static/images
                dest_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'images')
                dest_dir = os.path.abspath(dest_dir)
                dest_path = os.path.join(dest_dir, filename)
                if os.path.exists(dest_path):
                    os.remove(dest_path)

def start_watchdog(path):
    observer = PollingObserver(timeout=5)          
    observer.schedule(MonHandler(), path=path, recursive=False)
    observer.start()
    def run():
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return observer
