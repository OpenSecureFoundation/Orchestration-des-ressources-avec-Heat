/**
 * Client API centralisé + utilitaires partagés entre toutes les pages.
 */

const api = {
    /**
     * Requete GET vers l'API backend.
     * @param {string} url
     * @returns {Promise<object>}
     */
    async get(url) {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    },

    /**
     * Requete POST avec corps JSON.
     * @param {string} url
     * @param {object} data
     * @returns {Promise<object>}
     */
    async post(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const erreur = await response.json().catch(() => ({ error: 'Erreur inconnue' }));
            throw new Error(erreur.error || `HTTP ${response.status}`);
        }
        return response.json();
    },

    /**
     * Requete DELETE.
     * @param {string} url
     * @returns {Promise<object>}
     */
    async delete(url) {
        const response = await fetch(url, { method: 'DELETE' });
        if (!response.ok) {
            const erreur = await response.json().catch(() => ({ error: 'Erreur inconnue' }));
            throw new Error(erreur.error || `HTTP ${response.status}`);
        }
        return response.json();
    },

    /**
     * Upload d'un fichier via FormData.
     * @param {string} url
     * @param {FormData} formData
     * @returns {Promise<object>}
     */
    async upload(url, formData) {
        const response = await fetch(url, { method: 'POST', body: formData });
        if (!response.ok) {
            const erreur = await response.json().catch(() => ({ error: 'Erreur inconnue' }));
            throw new Error(erreur.error || `HTTP ${response.status}`);
        }
        return response.json();
    },
};

/* ---- Notifications toast ---- */

/**
 * Affiche une notification toast temporaire.
 * @param {string} message
 * @param {'success'|'error'|'info'} type
 * @param {number} duree - duree d'affichage en ms
 */
function afficherToast(message, type = 'info', duree = 4000) {
    let conteneur = document.getElementById('toast-container');
    if (!conteneur) {
        conteneur = document.createElement('div');
        conteneur.id = 'toast-container';
        document.body.appendChild(conteneur);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    conteneur.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, duree);
}

/* ---- Gestion des modales ---- */

function fermerModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('hidden');
}

function ouvrirModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('hidden');
}

/* ---- Formatage des statuts ---- */

/**
 * Retourne le HTML d'un badge selon le statut d'une stack ou VM.
 * @param {string} statut
 * @returns {string}
 */
function badgeStatut(statut) {
    const classes = {
        'CREATE_COMPLETE': 'badge-success',
        'UPDATE_COMPLETE': 'badge-success',
        'ACTIVE': 'badge-success',
        'CREATE_IN_PROGRESS': 'badge-warning',
        'UPDATE_IN_PROGRESS': 'badge-warning',
        'BUILD': 'badge-warning',
        'CREATE_FAILED': 'badge-danger',
        'UPDATE_FAILED': 'badge-danger',
        'DELETE_IN_PROGRESS': 'badge-warning',
        'ERROR': 'badge-danger',
        'SHUTOFF': 'badge-secondary',
        'SUSPENDED': 'badge-secondary',
    };
    const classe = classes[statut] || 'badge-secondary';
    return `<span class="badge ${classe}">${statut || 'INCONNU'}</span>`;
}

/**
 * Formate une date ISO en heure locale lisible.
 * @param {string} isoString
 * @returns {string}
 */
function formaterDate(isoString) {
    if (!isoString) return '--';
    try {
        return new Date(isoString).toLocaleString('fr-FR');
    } catch {
        return isoString;
    }
}
