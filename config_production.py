# Configuration pour la production
import os

class ProductionConfig:
    """Configuration pour le déploiement en production"""
    
    # Sécurité
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-very-secret-key-change-this-in-production'
    
    # Base de données (si nécessaire plus tard)
    # DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Serveur
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = False
    
    # CORS - Autoriser les domaines spécifiques en production
    ALLOWED_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:5000',
        # Ajoutez ici vos domaines autorisés
        # 'https://votre-domaine.com'
    ]
    
    # Limitation du taux de requêtes (protection contre les abus)
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Logs
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'app.log'

class DevelopmentConfig:
    """Configuration pour le développement local"""
    
    SECRET_KEY = 'dev-secret-key'
    HOST = '127.0.0.1'
    PORT = 5000
    DEBUG = True
    ALLOWED_ORIGINS = ['*']
    RATELIMIT_ENABLED = False
    LOG_LEVEL = 'DEBUG'

def get_config():
    """Retourne la configuration appropriée selon l'environnement"""
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig()
    else:
        return DevelopmentConfig()
