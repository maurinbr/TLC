// Variables globales pour les bornes
let bornesDefinies = false;
let depot = null;
let front = null;

// Scripts extraits de index.html
function showNotif(msg, color) {
    // Création d'un conteneur de notifications s'il n'existe pas déjà
    if (!document.getElementById('notif-container')) {
        const container = document.createElement('div');
        container.id = 'notif-container';
        container.style.position = 'fixed';
        container.style.zIndex = '9999';
        container.style.width = '100%';
        container.style.pointerEvents = 'none';
        document.body.appendChild(container);
    }
    
    // Création d'une nouvelle notification
    const notif = document.createElement('div');
    notif.className = 'notif';
    notif.textContent = msg;
    notif.style.background = color || '#323232';
    notif.style.color = '#fff';
    notif.style.padding = '10px 20px';
    notif.style.margin = '10px';
    notif.style.borderRadius = '5px';
    notif.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
    notif.style.display = 'block';
    notif.style.position = 'relative';
    notif.style.transition = 'opacity 0.5s';
    
    // Les notifications vertes (#4caf50) apparaissent en haut, les autres en bas
    const container = document.getElementById('notif-container');
    if (color === '#4caf50') {
        if (!container.querySelector('.top-notifs')) {
            const topDiv = document.createElement('div');
            topDiv.className = 'top-notifs';
            topDiv.style.position = 'fixed';
            topDiv.style.top = '20px';
            topDiv.style.left = '50%';
            topDiv.style.transform = 'translateX(-50%)';
            topDiv.style.display = 'flex';
            topDiv.style.flexDirection = 'column';
            topDiv.style.alignItems = 'center';
            container.appendChild(topDiv);
        }
        container.querySelector('.top-notifs').appendChild(notif);
    } else {
        if (!container.querySelector('.bottom-notifs')) {
            const bottomDiv = document.createElement('div');
            bottomDiv.className = 'bottom-notifs';
            bottomDiv.style.position = 'fixed';
            bottomDiv.style.bottom = '20px';
            bottomDiv.style.left = '50%';
            bottomDiv.style.transform = 'translateX(-50%)';
            bottomDiv.style.display = 'flex';
            bottomDiv.style.flexDirection = 'column';
            bottomDiv.style.alignItems = 'center';
            container.appendChild(bottomDiv);
        }
        container.querySelector('.bottom-notifs').appendChild(notif);
    }
    
    // Faire disparaître après un délai
    setTimeout(() => {
        notif.style.opacity = '0';
        setTimeout(() => {
            notif.parentNode.removeChild(notif);
        }, 3000);
    }, 5000);
}
function selectBtn(btn, rowId) {
    const row = document.getElementById(rowId);
    Array.from(row.getElementsByClassName('btn-tlc')).forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    // Sauvegarde le choix dans le localStorage
    localStorage.setItem('activeBtn_' + rowId, Array.from(row.children).indexOf(btn));
}
function restoreActiveBtns() {
    ['éluant', 'révélateur'].forEach(function(rowId) {
        const idx = localStorage.getItem('activeBtn_' + rowId);
        if (idx !== null) {
            const row = document.getElementById(rowId);
            if (row && row.children[idx]) {
                row.children[idx].classList.add('active');
            }
        }
    });
}
setTimeout(restoreActiveBtns, 100);
function saveData() {
    const eluant = document.querySelector('#éluant .btn-tlc.active');
    const colorant = document.querySelector('#révélateur .btn-tlc.active');
    const file = window.last_img;
    const echInput = document.getElementById('echantillons');
    // Récupère tous les spots dynamiques
    const resultInputs = document.querySelectorAll('.resultats-input');
    let echantillonsTags = [];
    if (echInput && echInput.value.trim()) {
        try {
            echantillonsTags = JSON.parse(echInput.value);
        } catch {
            echantillonsTags = echInput.value.split(',').map(s => ({ value: s.trim() })).filter(e => e.value);
        }
    }
    let echantillon = [];
    console.log('tous les échantillons:', echantillonsTags);
    console.log('tous les resultats:', resultInputs);
    for (let i = 1; i < (echantillonsTags.length*2); i=i+2) {
        let resultats = [];
        console.log(i + ' ieme résultat ' + resultInputs[i].value)
        if (resultInputs[i] && typeof resultInputs[i].value === 'string') {
            const val = resultInputs[i].value;
            console.log('Valeur brute du resultats-input', i, ':', val);
            if (val.trim()) {
                try {
                    const parsed = JSON.parse(val);
                    console.log('Parsed Tagify du resultats-input', i, ':', parsed);
                    if (Array.isArray(parsed)) {
                        resultats = parsed.map(tag => tag.value);
                    } else if (typeof parsed === 'string') {
                        resultats = [parsed];
                    }
                } catch {
                    resultats = val.split(',').map(s => s.trim()).filter(Boolean);
                    console.log('Résultats split du resultats-input', i, ':', resultats);
                }
            }
        }
        let echVal = echantillonsTags[(i-1)/2] ? echantillonsTags[(i-1)/2].value : '';
        console.log('Échantillon', i, ':', echVal, 'Résultats:', resultats);
        echantillon.push({
            echantillon: echVal,
            resultats: resultats
        });
    }
    console.log('Structure finale échantillon:', echantillon);
    if (!file || !eluant || !colorant) {
        showNotif('Référence absente (image, éluant, révélateur).', '#e53935');
        return;
    }
    // Vérifier si les bornes sont définies
    if (!bornesDefinies) {
        showNotif('Les bornes (dépôt et front) doivent être définies avant de sauvegarder !', '#e53935');
        return;
    }

    const dataToSave = { 
        file: file, 
        exp: [eluant.textContent, colorant.textContent], 
        echantillon: echantillon,
        bornes: {
            depot: depot,
            front: front
        }
    };
    showNotif('Données à sauvegarder : ' + JSON.stringify(dataToSave), '#1976d2');
    fetch('/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dataToSave)
    })
    .then(r => r.ok ? showNotif('Sauvegardé !', '#4caf50') : showNotif('Erreur sauvegarde', '#e53935'));

    // Génération du second JSON pour le journal
    const today = new Date();
    const dateStr = today.toISOString().slice(0, 10); // format YYYY-MM-DD
    // file: tableau (même si une seule image)
    const fileList = file ? [file] : [];
    // liste des échantillons
    const echantillonsList = echantillon.map(e => e.echantillon);
    // liste des résultats (tous les résultats à plat)
    const resultatsList = echantillon.flatMap(e => e.resultats);
    const journalJson = {
        date: dateStr,
        file: fileList,
        echantillon: echantillonsList,
        resultat: resultatsList
    };
    // Envoi du journal à une route dédiée
    fetch('/save-journal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(journalJson)
    });
}
// Tagify autocompletion for all pages with #echantillons
function initTagifyEchantillons() {
    const input = document.getElementById('echantillons');
    if (!input || typeof Tagify === 'undefined') return;
    // Tagify sur tous les inputs .resultats-input avec produits.json uniquement
    Promise.all([
        fetch('/static/echantillons.json').then(r => r.json()),
        fetch('/static/produits.json').then(r => r.json())
    ]).then(([echantillons, produits]) => {
        // Fusionne et dédoublonne
        const tags = Array.from(new Set([...echantillons, ...produits]));
        new Tagify(input, {
            whitelist: tags,
            dropdown: {
                enabled: 1,
                maxItems: 20,
                classname: 'tags-look',
                fuzzySearch: true,
                highlightFirst: true
            }
        });
    });
            document.querySelectorAll('.resultats-input').forEach(input => {
                // Détruit l'instance Tagify existante si présente
                if (input.tagify) input.tagify.destroy();
                new Tagify(input, {
                    whitelist: produits,
                    dropdown: {
                        enabled: 1,
                        maxItems: 20,
                        classname: 'tags-look',
                        fuzzySearch: true,
                        highlightFirst: true
                    }
                });
            });
        };
// Appelle automatiquement sur chaque page
window.addEventListener('DOMContentLoaded', initTagifyEchantillons);

// Gestion du bouton pour afficher le négatif de l'image
document.addEventListener('DOMContentLoaded', function() {
    const negBtn = document.getElementById('negatif-btn');
    const img = document.getElementById('main-image');
    if (negBtn && img) {
        let isNegatif = false;
        negBtn.addEventListener('click', function() {
            if (!isNegatif) {
                img.src = '/image-process?' + Date.now();
                negBtn.textContent = 'Afficher l\'original';
            } else {
                img.src = img.getAttribute('data-original-src');
                negBtn.textContent = 'Afficher le négatif';
            }
            isNegatif = !isNegatif;
        });
        // Sauvegarde la src originale
        img.setAttribute('data-original-src', img.src);
    }
});

// Affichage des coordonnées du clic sur l'image
document.addEventListener('DOMContentLoaded', function() {
    const img = document.getElementById('main-image');
    const coordsResult = document.getElementById('coords-result');
    // Ajout du bouton "Définir les bornes"
    let bornesBtn = document.getElementById('bornes-btn');
    if (!bornesBtn && coordsResult) {
        bornesBtn = document.createElement('button');
        bornesBtn.id = 'bornes-btn';
        bornesBtn.textContent = 'Définir les bornes';
        bornesBtn.style.margin = '10px 0';
        coordsResult.parentNode.insertBefore(bornesBtn, coordsResult);
    }

    let modeBornes = false;
    let bornesY = [];

    if (bornesBtn) {
        bornesBtn.addEventListener('click', function() {
            modeBornes = true;
            bornesY = [];
            coordsResult.textContent = 'Cliquez sur le dépôt puis sur le front.';
            bornesBtn.disabled = true;
        });
    }

    if (img && coordsResult) {
        img.addEventListener('click', function(e) {
            const rect = img.getBoundingClientRect();
            const x = Math.round(e.clientX - rect.left);
            const y = Math.round(e.clientY - rect.top);

            if (modeBornes) {
                bornesY.push(y);
                if (bornesY.length === 2) {
                    depot = Math.min(...bornesY);
                    front = Math.max(...bornesY);
                    coordsResult.textContent = `Bornes définies : dépôt = y=${depot}, front = y=${front}`;
                    modeBornes = false;
                    bornesBtn.disabled = false;
                    bornesDefinies = true;
                } else {
                    coordsResult.textContent = 'Cliquez maintenant sur le front.';
                }
                return;
            }

            // Ne pas activer la fonction de récupération des coordonnées/RGB tant que les bornes ne sont pas définies
            if (!bornesDefinies) {
                coordsResult.textContent = 'Définissez d\'abord les bornes (dépôt et front) !';
                return;
            }

            // Envoie les coordonnées au serveur Flask
            fetch('/get-coords', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ x: x, y: y })
            })
            .then(r => r.json())
            .then(data => {
                if (data.ok) {
                    // Affiche les coordonnées et la valeur RGB sous l'image
                    coordsResult.textContent = `Coordonnées : x=${x}, y=${y} (envoyé au serveur)`;
                    if (data.rgb) {
                        coordsResult.textContent += ` | RGB : (${data.rgb.join(', ')})`;
                    }
                }
            });
        });
    }
});

// Pour compatibilité Flask/Jinja2, expose last_img côté JS si besoin
window.last_img = typeof last_img !== 'undefined' ? last_img : null;

let refreshInterval = null;
function startRefresh() {
    if (!refreshInterval) {
        refreshInterval = setInterval(() => {
            location.reload();
        }, 5000); // 5s
    }
}
function stopRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}
