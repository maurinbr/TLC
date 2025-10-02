# Guide de déploiement TLC en ligne

## Méthodes pour rendre le serveur accessible en ligne

### 1. 🏠 Réseau local (LAN)
Le serveur est déjà configuré pour être accessible sur votre réseau local.

**Démarrage :**
```bash
python run.py
```

**Accès :**
- Depuis votre machine : `http://localhost:5000`
- Depuis autres machines du réseau : `http://[VOTRE_IP]:5000`

**Trouver votre IP :**
```cmd
ipconfig
```
Cherchez l'adresse IPv4 de votre carte réseau.

---

### 2. 🌐 Tunnel ngrok (gratuit, temporaire)
Ngrok crée un tunnel sécurisé vers votre serveur local.

**Installation :**
1. Téléchargez ngrok : https://ngrok.com/download
2. Créez un compte gratuit
3. Configurez le token : `ngrok authtoken YOUR_TOKEN`

**Utilisation :**
```bash
# Terminal 1 : Démarrer le serveur
python run.py

# Terminal 2 : Créer le tunnel
ngrok http 5000
```

**Résultat :** Une URL publique comme `https://abc123.ngrok.io`

---

### 3. ☁️ VPS/Cloud (recommandé pour production)

#### A. DigitalOcean/Linode/AWS
1. Créer un VPS/instance
2. Installer Python et dépendances
3. Transférer les fichiers
4. Configurer le firewall (port 5000)
5. Démarrer avec : `python run.py --production`

#### B. Heroku (Platform as a Service)
1. Créer un `Procfile` :
   ```
   web: python run.py --production
   ```
2. Créer un `requirements.txt`
3. Déployer via Git

---

### 4. 🏡 Accès depuis Internet (routeur domestique)

**Configuration routeur :**
1. Ouvrir le port 5000 en TCP
2. Rediriger vers votre IP locale
3. Utiliser votre IP publique : `http://[IP_PUBLIQUE]:5000`

**Trouver votre IP publique :**
- https://whatismyipaddress.com
- `curl ifconfig.me`

**⚠️ Sécurité :** Changez le port par défaut, utilisez un VPN, ou limitez les IPs autorisées.

---

### 5. 🐳 Docker (optionnel)

**Dockerfile :**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "run.py", "--production"]
```

**Commandes :**
```bash
docker build -t tlc-app .
docker run -p 5000:5000 tlc-app
```

---

## Sécurité en production

### Configuration recommandée :
- ✅ `debug=False`
- ✅ Certificat SSL/HTTPS
- ✅ Firewall configuré
- ✅ Mots de passe forts
- ✅ Mise à jour régulière
- ✅ Sauvegarde des données

### Variables d'environnement :
```bash
export FLASK_ENV=production
export SECRET_KEY=your-very-secret-key
export PORT=5000
```

---

## Test de connectivité

**Depuis votre machine :**
```bash
curl http://localhost:5000
```

**Depuis une autre machine :**
```bash
curl http://[VOTRE_IP]:5000
```

**Depuis internet (avec tunnel/VPS) :**
```bash
curl http://[URL_PUBLIQUE]
```

---

## Dépannage

### Port déjà utilisé :
```bash
netstat -an | findstr :5000
```

### Firewall Windows :
```cmd
netsh advfirewall firewall add rule name="Flask TLC" dir=in action=allow protocol=TCP localport=5000
```

### Accès refusé :
- Vérifiez l'IP dans `run.py` (doit être `0.0.0.0`)
- Vérifiez le firewall
- Vérifiez les règles du routeur
