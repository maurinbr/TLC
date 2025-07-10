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
    const resInput = document.getElementById('resultats');
    let echantillons = [];
    let resultats = [];
    if (resInput && resInput.value.trim()) {
        // Découpe chaque ligne, puis chaque ligne par les virgules
        resultats = resInput.value.split(/\r?\n/).map(ligne =>
            ligne.split(',').map(r => r.trim()).filter(Boolean)
        );
    }
    if (echInput && echInput.value.trim()) {
        const echList = echInput.value.split(',').map(s => s.trim()).filter(Boolean);
        echantillons = echList.map((val, i) => {
            console.log([i+1], val, resultats[i])
            return {
                [i+1]: val,
                resultats: resultats[i] || []
            };
        });
    }
    console.log(file, eluant, colorant, echantillons);
    if (!file || !eluant || !colorant) {
        showNotif('Référence absente (image, éluant, révélateur).', '#e53935');
        return;
    }
    const dataToSave = { file: file, exp: [eluant.textContent, colorant.textContent], échantillon: echantillons };
    showNotif('Données à sauvegarder : ' + JSON.stringify(dataToSave), '#1976d2');
    fetch('/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dataToSave)
    })
    .then(r => r.ok ? showNotif('Sauvegardé !', '#4caf50') : showNotif('Erreur sauvegarde', '#e53935'));
}
// Pour compatibilité Flask/Jinja2, expose last_img côté JS si besoin
window.last_img = typeof last_img !== 'undefined' ? last_img : null;
