// Scripts extraits de index.html
function showNotif(msg, color) {
    const notif = document.getElementById('notif');
    notif.textContent = msg;
    notif.style.background = color || '#323232';
    notif.style.display = 'block';
    setTimeout(() => { notif.style.display = 'none'; }, 2500);
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
    const dataToSave = { file: file, exp: [eluant.textContent, colorant.textContent], echantillon: echantillon };
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
    if (img && coordsResult) {
        img.addEventListener('click', function(e) {
            // Récupère la position du clic relative à l'image
            const rect = img.getBoundingClientRect();
            const x = Math.round(e.clientX - rect.left);
            const y = Math.round(e.clientY - rect.top);

            // Affiche les coordonnées sous l'image
            coordsResult.textContent = `Coordonnées : x=${x}, y=${y}`;

            // Envoie les coordonnées au serveur Flask
            fetch('/get-coords', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ x: x, y: y })
            })
            .then(r => r.json())
            .then(data => {
                if (data.ok) {
                    coordsResult.textContent += " (envoyé au serveur)";
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
