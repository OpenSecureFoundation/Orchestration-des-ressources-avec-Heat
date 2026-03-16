/**
 * Page VMs — gestion complète des machines virtuelles.
 */

let vmSelectionnee = null;  // VM dont le panneau est ouvert
let vmEnCours     = null;   // VM pour le resize
let vmASupprimer  = null;   // VM pour la suppression

document.addEventListener('DOMContentLoaded', () => {
    chargerVMs();
    setInterval(chargerVMs, 30000);
});

// =====================================================================
// TABLEAU PRINCIPAL
// =====================================================================

async function chargerVMs() {
    const conteneur = document.getElementById('tableau-vms');
    try {
        const data = await api.get('/api/vms');
        const vms = data.vms || [];

        if (!vms.length) {
            conteneur.innerHTML = '<div class="empty-state">Aucune VM trouvée dans ce projet OpenStack.</div>';
            return;
        }

        conteneur.innerHTML = `
        <div class="table-container">
        <table>
            <thead><tr>
                <th>Nom / ID</th>
                <th>Statut</th>
                <th>IP</th>
                <th>Flavor</th>
                <th>CPU / RAM</th>
                <th>Créée le</th>
                <th>Actions</th>
            </tr></thead>
            <tbody>
            ${vms.map(v => {
                const isActive  = v.status === 'ACTIVE';
                const isShutoff = v.status === 'SHUTOFF';
                const ips = (v.ip_addresses || []).join(', ') || v.ip || '--';
                return `
                <tr id="row-${v.id}">
                    <td>
                        <a href="#" class="vm-nom-link" onclick="ouvrirPanneau('${v.id}','${v.name}'); return false;">
                            <strong>${v.name}</strong>
                        </a>
                        <div style="font-family:monospace;font-size:0.72rem;color:#94a3b8;margin-top:2px;">
                            ${v.id.substring(0,12)}...
                        </div>
                    </td>
                    <td>${badgeStatut(v.status)}</td>
                    <td style="font-size:0.85rem;">${ips}</td>
                    <td>
                        <span class="flavor-badge">${v.flavor || '--'}</span>
                    </td>
                    <td id="metrics-${v.id}" style="font-size:0.82rem;color:#64748b;">--</td>
                    <td style="font-size:0.82rem;">${formaterDate(v.created)}</td>
                    <td>
                        <div class="actions-cell">
                            ${isShutoff ? `
                            <button class="btn btn-sm btn-success" onclick="demarrerVM('${v.id}','${v.name}')">
                                ▶ Démarrer
                            </button>` : ''}
                            ${isActive ? `
                            <button class="btn btn-sm btn-warning" onclick="arreterVM('${v.id}','${v.name}')">
                                ⏸ Éteindre
                            </button>` : ''}
                            <button class="btn btn-sm btn-outline" onclick="ouvrirModalResize('${v.id}','${v.name}','${v.flavor||''}')">
                                Resize
                            </button>
                            <button class="btn btn-sm btn-outline" onclick="ouvrirPanneau('${v.id}','${v.name}')">
                                Détails
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="demanderSuppressionVM('${v.id}','${v.name}')">
                                Supprimer
                            </button>
                        </div>
                    </td>
                </tr>`;
            }).join('')}
            </tbody>
        </table>
        </div>`;

        // Charger les métriques pour chaque VM ACTIVE
        vms.filter(v => v.status === 'ACTIVE').forEach(v => chargerMetriqueRapide(v.id));

    } catch (e) {
        conteneur.innerHTML = `<div class="alert alert-danger">Erreur chargement VMs : ${e.message}</div>`;
    }
}

async function chargerMetriqueRapide(vmId) {
    try {
        const data = await api.get(`/api/vms/${vmId}/metrics`);
        const m = data.metrics || {};
        const cell = document.getElementById(`metrics-${vmId}`);
        if (!cell) return;
        if (m.cpu_percent !== undefined) {
            const cpu = m.cpu_percent ?? '--';
            const ram = m.ram_percent ?? '--';
            const couleurCPU = cpu > 80 ? '#dc2626' : cpu > 50 ? '#d97706' : '#16a34a';
            cell.innerHTML = `
                <span style="color:${couleurCPU};font-weight:600;">CPU ${cpu}%</span>
                <span style="color:#64748b;margin-left:0.5rem;">RAM ${ram}%</span>`;
        } else {
            cell.textContent = 'Pas de données';
        }
    } catch (e) { /* silencieux */ }
}

// =====================================================================
// ACTIONS VM
// =====================================================================

async function demarrerVM(vmId, vmNom) {
    try {
        await api.post(`/api/vms/${vmId}/start`, {});
        afficherToast(`VM '${vmNom}' en cours de démarrage...`, 'info');
        setTimeout(chargerVMs, 3000);
    } catch (e) {
        afficherToast(`Erreur démarrage : ${e.message}`, 'error');
    }
}

async function arreterVM(vmId, vmNom) {
    if (!confirm(`Éteindre la VM '${vmNom}' ?`)) return;
    try {
        await api.post(`/api/vms/${vmId}/stop`, {});
        afficherToast(`VM '${vmNom}' en cours d'arrêt...`, 'info');
        setTimeout(chargerVMs, 3000);
    } catch (e) {
        afficherToast(`Erreur arrêt : ${e.message}`, 'error');
    }
}

// =====================================================================
// PANNEAU DETAILS
// =====================================================================

async function ouvrirPanneau(vmId, vmNom) {
    vmSelectionnee = { id: vmId, name: vmNom };
    document.getElementById('details-vm-titre').textContent = vmNom;
    document.getElementById('panneau-details').classList.remove('hidden');
    document.getElementById('panneau-overlay').classList.remove('hidden');

    // Réinitialiser onglets
    afficherOngletVMDirect('info');
    document.querySelectorAll('.side-panel .tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-btn-info').classList.add('active');

    await chargerDetailsVM(vmId);
}

function fermerPanneau() {
    document.getElementById('panneau-details').classList.add('hidden');
    document.getElementById('panneau-overlay').classList.add('hidden');
    vmSelectionnee = null;
}

function afficherOngletVM(nom, btn) {
    afficherOngletVMDirect(nom);
    document.querySelectorAll('.side-panel .tab-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    if (nom === 'scaling' && vmSelectionnee) chargerHistoriqueScaling(vmSelectionnee.id);
    if (nom === 'console' && vmSelectionnee) rechargerConsole();
}

function afficherOngletVMDirect(nom) {
    ['info','scaling','console'].forEach(n => {
        const el = document.getElementById(`vm-tab-${n}`);
        if (el) el.classList.toggle('hidden', n !== nom);
    });
}

async function chargerDetailsVM(vmId) {
    const cont = document.getElementById('details-vm-contenu');
    cont.innerHTML = '<div class="loading">Chargement...</div>';
    try {
        const [dataVM, dataMetrics] = await Promise.all([
            api.get(`/api/vms/${vmId}`),
            api.get(`/api/vms/${vmId}/metrics`).catch(() => ({ metrics: {} }))
        ]);
        const v = dataVM.vm;
        const m = dataMetrics.metrics || {};
        const fi = v.flavor || {};
        const flavorNom = fi.original_name || fi.id || '--';
        const vcpus = fi.vcpus || '--';
        const ram   = fi.ram   ? `${fi.ram} Mo` : '--';
        const disk  = fi.disk  ? `${fi.disk} Go` : '--';

        const ips = (v.ip_addresses || []).map(a =>
            `<div><span class="badge ${a.type==='floating'?'badge-info':'badge-secondary'}" style="font-size:0.75rem;">${a.type||'fixed'}</span> ${a.ip}</div>`
        ).join('') || '--';

        const sgs = (v.security_groups || []).join(', ') || '--';

        cont.innerHTML = `
        <div class="details-section">
            <h4 class="details-section-titre">Identité</h4>
            <div class="detail-row"><span class="detail-label">Nom</span><strong>${v.name}</strong></div>
            <div class="detail-row"><span class="detail-label">UUID</span><code style="font-size:0.8rem;">${v.id}</code></div>
            <div class="detail-row"><span class="detail-label">Statut</span>${badgeStatut(v.status)}</div>
            <div class="detail-row"><span class="detail-label">Créée le</span>${formaterDate(v.created)}</div>
            <div class="detail-row"><span class="detail-label">Clé SSH</span>${v.key_name || '--'}</div>
            <div class="detail-row"><span class="detail-label">Security groups</span>${sgs}</div>
        </div>

        <div class="details-section">
            <h4 class="details-section-titre">&#9881; Flavor actuelle : <span style="color:#2563eb;">${flavorNom}</span></h4>
            <div class="flavor-grid">
                <div class="flavor-card"><div class="flavor-val">${vcpus}</div><div class="flavor-key">vCPUs</div></div>
                <div class="flavor-card"><div class="flavor-val">${ram}</div><div class="flavor-key">RAM</div></div>
                <div class="flavor-card"><div class="flavor-val">${disk}</div><div class="flavor-key">Disque</div></div>
            </div>
        </div>

        <div class="details-section">
            <h4 class="details-section-titre">Réseau</h4>
            ${ips}
        </div>

        ${m.cpu_percent !== undefined ? `
        <div class="details-section">
            <h4 class="details-section-titre">Métriques (dernière valeur)</h4>
            <div class="metrics-mini-grid">
                ${metriqueBar('CPU', m.cpu_percent)}
                ${metriqueBar('RAM', m.ram_percent)}
                ${metriqueBar('Disque', m.disk_percent)}
            </div>
            <div style="font-size:0.75rem;color:#94a3b8;margin-top:0.5rem;">
                Relevé le ${formaterDate(m.timestamp)}
            </div>
        </div>` : ''}

        <div style="margin-top:1rem;display:flex;gap:0.5rem;flex-wrap:wrap;">
            <button class="btn btn-sm btn-outline"
                onclick="ouvrirModalResize('${v.id}','${v.name}','${flavorNom}')">
                Resize flavor
            </button>
            <a href="/monitoring?vm=${v.id}" class="btn btn-sm btn-outline">
                Voir métriques temps réel
            </a>
        </div>`;
    } catch (e) {
        cont.innerHTML = `<div class="alert alert-danger">Erreur : ${e.message}</div>`;
    }
}

function metriqueBar(label, val) {
    if (val === undefined || val === null) return '';
    const pct = Math.round(val);
    const couleur = pct > 80 ? '#dc2626' : pct > 50 ? '#d97706' : '#16a34a';
    return `
    <div style="margin-bottom:0.6rem;">
        <div style="display:flex;justify-content:space-between;font-size:0.82rem;margin-bottom:3px;">
            <span>${label}</span><strong style="color:${couleur};">${pct}%</strong>
        </div>
        <div style="background:#e2e8f0;border-radius:4px;height:6px;">
            <div style="width:${pct}%;background:${couleur};height:100%;border-radius:4px;transition:width 0.3s;"></div>
        </div>
    </div>`;
}

async function chargerHistoriqueScaling(vmId) {
    const cont = document.getElementById('details-scaling-contenu');
    cont.innerHTML = '<div class="loading">Chargement...</div>';
    try {
        const data = await api.get(`/api/vms/${vmId}/scaling-history`);
        const hist = data.history || [];
        if (!hist.length) {
            cont.innerHTML = '<div class="empty-state">Aucun scaling effectué sur cette VM.</div>';
            return;
        }
        cont.innerHTML = `
        <table style="font-size:0.82rem;width:100%;">
            <thead><tr>
                <th>Date</th><th>Type</th><th>Flavors</th><th>Métrique</th><th>Statut</th>
            </tr></thead>
            <tbody>
            ${hist.map(h => {
                const dirBadge = h.direction === 'scale_up'
                    ? '<span class="badge badge-danger">▲ Scale UP</span>'
                    : '<span class="badge badge-info">▼ Scale DOWN</span>';
                const statutBadge = h.statut === 'succes'
                    ? '<span class="badge badge-success">✓ Succès</span>'
                    : '<span class="badge badge-danger">✗ Échec</span>';
                const metriqueInfo = h.metrique && h.valeur_metrique !== null
                    ? `${h.metrique.toUpperCase()} ${h.valeur_metrique}%`
                    : '--';
                return `<tr>
                    <td>${formaterDate(h.timestamp)}</td>
                    <td>${dirBadge}</td>
                    <td style="font-family:monospace;">${h.flavor_avant} → ${h.flavor_apres}</td>
                    <td>${metriqueInfo}</td>
                    <td>${statutBadge}${h.message ? `<div style="color:#dc2626;font-size:0.75rem;">${h.message}</div>` : ''}</td>
                </tr>`;
            }).join('')}
            </tbody>
        </table>`;
    } catch (e) {
        cont.innerHTML = `<div class="alert alert-danger">Erreur : ${e.message}</div>`;
    }
}

async function rechargerConsole() {
    if (!vmSelectionnee) return;
    document.getElementById('console-output').textContent = 'Chargement...';
    try {
        const data = await api.get(`/api/vms/${vmSelectionnee.id}/console`);
        document.getElementById('console-output').textContent = data.log || 'Aucun log disponible';
    } catch (e) {
        document.getElementById('console-output').textContent = `Erreur : ${e.message}`;
    }
}

// =====================================================================
// RESIZE
// =====================================================================

function ouvrirModalResize(vmId, vmNom, flavorActuel) {
    vmEnCours = { id: vmId, name: vmNom };
    document.getElementById('resize-vm-name').textContent = vmNom;
    document.getElementById('resize-flavor-actuel').textContent = flavorActuel || 'inconnu';
    const sel = document.getElementById('resize-nouveau-flavor');
    Array.from(sel.options).forEach(o => { o.selected = o.value === flavorActuel; });
    ouvrirModal('modal-resize');
}

async function confirmerResize() {
    if (!vmEnCours) return;
    const nouveauFlavor = document.getElementById('resize-nouveau-flavor').value;
    const btn = document.querySelector('#modal-resize .btn-primary');
    btn.disabled = true; btn.textContent = 'Lancement...';
    try {
        await api.post(`/api/vms/${vmEnCours.id}/resize`, { flavor: nouveauFlavor });
        fermerModal('modal-resize');
        afficherToast(`Resize lancé vers ${nouveauFlavor}. Confirmation automatique en arrière-plan.`, 'success', 7000);
        setTimeout(chargerVMs, 5000);
    } catch (e) {
        afficherToast(`Erreur resize : ${e.message}`, 'error', 8000);
    } finally {
        btn.disabled = false; btn.textContent = 'Confirmer le resize';
    }
}

// =====================================================================
// SUPPRESSION
// =====================================================================

function demanderSuppressionVM(vmId, vmNom) {
    vmASupprimer = { id: vmId, nom: vmNom };
    document.getElementById('confirm-vm-nom').textContent = vmNom;
    ouvrirModal('modal-confirm-suppr-vm');
}

async function confirmerSuppressionVM() {
    if (!vmASupprimer) return;
    const btn = document.querySelector('#modal-confirm-suppr-vm .btn-danger');
    btn.disabled = true; btn.textContent = 'Suppression...';
    try {
        await api.delete(`/api/vms/${vmASupprimer.id}`);
        fermerModal('modal-confirm-suppr-vm');
        fermerPanneau();
        afficherToast(`VM '${vmASupprimer.nom}' supprimée`, 'success');
        vmASupprimer = null;
        chargerVMs();
    } catch (e) {
        afficherToast(`Erreur suppression : ${e.message}`, 'error', 8000);
    } finally {
        btn.disabled = false; btn.textContent = 'Supprimer définitivement';
    }
}
