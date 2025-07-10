from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import threading
import time

class MonHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"Fichier créé : {event.src_path}")

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"Fichier supprimé : {event.src_path}")

def start_watchdog(path):
    observer = Observer()
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
