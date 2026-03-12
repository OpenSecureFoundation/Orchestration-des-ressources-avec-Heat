/**
 * Page Stacks - gestion des stacks Heat.
 */

let stackEnCours = null;

document.addEventListener('DOMContentLoaded', () => {
    chargerStacks();
    chargerTemplates();
});

async function chargerStacks() {
    const conteneur = document.getElementById('tableau-stacks');
    conteneur.innerHTML = '<div class="loading">Chargement des stacks...</div>';
    try {
        const data = await api.get('/api/stacks');
        const stacks = data.stacks || [];

        if (!stacks.length) {
            conteneur.innerHTML = '<div class="empty-state">Aucune stack deployee. Creez votre premiere stack.</div>';
            return;
        }

        conteneur.innerHTML = `
            <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Nom</th>
                        <th>Statut</th>
                        <th>Heat ID</th>
                        <th>Cree le</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${stacks.map(s => `
                        <tr>
                            <td><strong>${s.name}</strong></td>
                            <td>${badgeStatut(s.status)}</td>
                            <td style="font-family:monospace; font-size:0.8rem; color:#64748b;">
                                ${s.heat_id ? s.heat_id.substring(0, 12) + '...' : '--'}
                            </td>
                            <td>${formaterDate(s.created_at)}</td>
                            <td>
                                <div class="actions-cell">
                                    <button class="btn btn-sm btn-outline"
                                        onclick="voirDetails(${s.id}, '${s.heat_id}', '${s.name}')">
                                        Details
                                    </button>
                                    <button class="btn btn-sm btn-danger"
                                        onclick="demanderSuppression(${s.id}, '${s.name}')">
                                        Supprimer
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            </div>
        `;
    } catch (e) {
        conteneur.innerHTML = `<div class="alert alert-danger">Erreur : ${e.message}</div>`;
    }
}

async function chargerTemplates() {
    try {
        const data = await api.get('/api/templates');
        const select = document.getElementById('stack-template');
        const templates = data.templates || [];
        select.innerHTML = templates.map(t =>
            `<option value="${t.id}">${t.name} (${t.category})</option>`
        ).join('') || '<option value="">Aucun template disponible</option>';
    } catch (e) {
        console.error('Erreur chargement templates :', e);
    }
}

function ouvrirModalCreation() {
    chargerTemplates();
    ouvrirModal('modal-creation');
}

async function creerStack() {
    const name = document.getElementById('stack-name').value.trim();
    const templateId = document.getElementById('stack-template').value;

    if (!name) {
        afficherToast('Le nom de la stack est obligatoire', 'error');
        return;
    }
    if (!templateId) {
        afficherToast('Selectionnez un template', 'error');
        return;
    }

    const parametres = {
        key_name: document.getElementById('param-key-name').value,
        image_name: document.getElementById('param-image').value,
        flavor_name: document.getElementById('param-flavor').value,
    };

    const btnCreer = document.querySelector('#modal-creation .btn-primary');
    btnCreer.disabled = true;
    btnCreer.textContent = 'Creation en cours...';

    try {
        afficherToast('Creation de la stack en cours...', 'info', 6000);
        await api.post('/api/stacks', {
            name,
            template_id: parseInt(templateId),
            parameters: parametres,
        });
        fermerModal('modal-creation');
        afficherToast(`Stack '${name}' creee avec succes`, 'success');
        chargerStacks();
    } catch (e) {
        afficherToast(`Erreur : ${e.message}`, 'error', 8000);
    } finally {
        btnCreer.disabled = false;
        btnCreer.textContent = 'Creer la stack';
    }
}

// ---- Suppression avec confirmation ----

let stackASupprimer = null;

function demanderSuppression(stackId, nom) {
    stackASupprimer = { id: stackId, nom: nom };
    document.getElementById('confirm-stack-nom').textContent = nom;
    ouvrirModal('modal-confirm-suppr');
}

async function confirmerSuppression() {
    if (!stackASupprimer) return;

    const btnConfirm = document.querySelector('#modal-confirm-suppr .btn-danger');
    btnConfirm.disabled = true;
    btnConfirm.textContent = 'Suppression...';

    try {
        await api.delete(`/api/stacks/${stackASupprimer.id}`);
        fermerModal('modal-confirm-suppr');
        fermerModal('modal-details');
        afficherToast(`Stack '${stackASupprimer.nom}' supprimee`, 'success');
        stackASupprimer = null;
        chargerStacks();
    } catch (e) {
        afficherToast(`Erreur suppression : ${e.message}`, 'error', 8000);
    } finally {
        btnConfirm.disabled = false;
        btnConfirm.textContent = 'Supprimer definitivement';
    }
}

function supprimerStackEnCours() {
    if (!stackEnCours) return;
    fermerModal('modal-details');
    demanderSuppression(stackEnCours.id, stackEnCours.nom);
}

// ---- Details ----

async function voirDetails(stackId, heatId, nom) {
    document.getElementById('details-titre').textContent = `Stack : ${nom}`;
    stackEnCours = { id: stackId, heat_id: heatId, nom: nom };
    ouvrirModal('modal-details');
    await chargerRessources(stackId);
}

async function chargerRessources(stackId) {
    const conteneur = document.getElementById('liste-ressources');
    conteneur.innerHTML = '<div class="loading">Chargement...</div>';
    try {
        const data = await api.get(`/api/stacks/${stackId}/resources`);
        const ressources = data.resources || [];
        if (!ressources.length) {
            conteneur.innerHTML = '<div class="empty-state">Aucune ressource</div>';
            return;
        }
        conteneur.innerHTML = `
            <table>
                <thead><tr><th>Nom</th><th>Type</th><th>Statut</th><th>ID Physique</th></tr></thead>
                <tbody>
                ${ressources.map(r => `
                    <tr>
                        <td>${r.name}</td>
                        <td style="font-size:0.8rem;">${r.type}</td>
                        <td>${badgeStatut(r.status)}</td>
                        <td style="font-family:monospace; font-size:0.75rem;">${r.physical_id || '--'}</td>
                    </tr>
                `).join('')}
                </tbody>
            </table>
        `;
    } catch (e) {
        conteneur.innerHTML = `<div class="alert alert-danger">Erreur : ${e.message}</div>`;
    }
}

async function afficherOnglet(onglet) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
    document.getElementById(`onglet-${onglet}`).classList.remove('hidden');

    if (!stackEnCours) return;

    if (onglet === 'outputs') {
        const conteneur = document.getElementById('liste-outputs');
        conteneur.innerHTML = '<div class="loading">Chargement...</div>';
        try {
            const data = await api.get(`/api/stacks/${stackEnCours.id}/outputs`);
            const outputs = data.outputs || {};
            const entrees = Object.entries(outputs);
            if (!entrees.length) {
                conteneur.innerHTML = '<div class="empty-state">Aucun output</div>';
                return;
            }
            conteneur.innerHTML = entrees.map(([k, v]) => `
                <div style="padding:0.5rem 0; border-bottom:1px solid #e2e8f0;">
                    <strong>${k}</strong>
                    <div style="font-family:monospace; font-size:0.85rem; color:#1d4ed8; margin-top:0.25rem;">
                        ${v || '--'}
                    </div>
                </div>
            `).join('');
        } catch (e) {
            conteneur.innerHTML = `<div class="alert alert-danger">Erreur : ${e.message}</div>`;
        }
    }

    if (onglet === 'evenements') {
        const conteneur = document.getElementById('liste-evenements');
        conteneur.innerHTML = '<div class="loading">Chargement...</div>';
        try {
            const data = await api.get(`/api/stacks/${stackEnCours.id}/events`);
            const events = data.events || [];
            if (!events.length) {
                conteneur.innerHTML = '<div class="empty-state">Aucun evenement</div>';
                return;
            }
            conteneur.innerHTML = `
                <table>
                    <thead><tr><th>Ressource</th><th>Statut</th><th>Raison</th><th>Heure</th></tr></thead>
                    <tbody>
                    ${events.slice(-20).reverse().map(e => `
                        <tr>
                            <td>${e.resource_name}</td>
                            <td>${badgeStatut(e.resource_status)}</td>
                            <td style="font-size:0.8rem;">${e.resource_status_reason || '--'}</td>
                            <td style="font-size:0.8rem;">${e.event_time || '--'}</td>
                        </tr>
                    `).join('')}
                    </tbody>
                </table>
            `;
        } catch (e) {
            conteneur.innerHTML = `<div class="alert alert-danger">Erreur : ${e.message}</div>`;
        }
    }
}
