"""
Utilitaires pour la gestion des chemins utilisateur.
Permet de factoriser la gestion des chemins OneDrive pour différents comptes utilisateur.
"""
import os


def get_current_username():
    """Récupère le nom d'utilisateur Windows actuel."""
    return os.getenv('USERNAME', 'utilisateur')


def get_onedrive_base_path():
    """Retourne le chemin de base OneDrive pour l'utilisateur actuel."""
    username = get_current_username()
    return rf"C:/Users/{username}/OneDrive/Analyses"


def get_tlc_data_path():
    """Retourne le chemin vers les données TLC dans OneDrive pour l'utilisateur actuel."""
    username = get_current_username()
    return rf"C:/Users/{username}/OneDrive/Analyses/Apps/TLC/TLC/app/data"


def get_onedrive_search_paths():
    """Retourne la liste des chemins de base pour la recherche d'images OneDrive."""
    base_path = get_onedrive_base_path()
    return [
        base_path,
        os.path.join(base_path, '2025'),
        os.path.join(base_path, '2024'),
    ]
