/**
 * Page Dashboard - vue d'ensemble de l'infrastructure.
 */

document.addEventListener('DOMContentLoaded', () => {
    chargerDashboard();
    // Actualisation toutes les 30 secondes
    setInterval(chargerDashboard, 30000);
});

async function chargerDashboard() {
    await Promise.all([
        chargerCompteurs(),
        chargerStacksRecentes(),
        chargerMetriquesGlobales(),
    ]);
}

async function chargerCompteurs() {
    try {
        const [stacks, vms, metriques, politiques] = await Promise.all([
            api.get('/api/stacks'),
            api.get('/api/vms'),
            api.get('/api/metrics/all/latest'),
            api.get('/api/metrics/scaling'),
        ]);

        document.getElementById('nb-stacks').textContent =
            stacks.stacks ? stacks.stacks.filter(s =>
                s.status && s.status.includes('COMPLETE')
            ).length : '--';

        document.getElementById('nb-vms').textContent =
            vms.vms ? vms.vms.filter(v => v.status === 'ACTIVE').length : '--';

        document.getElementById('nb-metriques').textContent =
            metriques.metrics ? metriques.metrics.length : '--';

        document.getElementById('nb-politiques').textContent =
            politiques.policies ? politiques.policies.length : '--';

    } catch (e) {
        console.error('Erreur chargement compteurs :', e);
    }
}

async function chargerStacksRecentes() {
    const conteneur = document.getElementById('liste-stacks-recentes');
    try {
        const data = await api.get('/api/stacks');
        const stacks = data.stacks || [];

        if (!stacks.length) {
            conteneur.innerHTML = '<div class="empty-state">Aucune stack deployee</div>';
            return;
        }

        const lignes = stacks.slice(0, 5).map(s => `
            <div style="display:flex; justify-content:space-between; align-items:center; padding:0.6rem 0; border-bottom:1px solid #e2e8f0;">
                <div>
                    <strong>${s.name}</strong>
                    <div style="font-size:0.8rem; color:#64748b;">${formaterDate(s.created_at)}</div>
                </div>
                ${badgeStatut(s.status)}
            </div>
        `).join('');

        conteneur.innerHTML = lignes;

    } catch (e) {
        conteneur.innerHTML = `<div class="alert alert-danger">Erreur : ${e.message}</div>`;
    }
}

async function chargerMetriquesGlobales() {
    const conteneur = document.getElementById('metriques-globales');
    try {
        const data = await api.get('/api/metrics/all/latest');
        const metriques = data.metrics || [];

        if (!metriques.length) {
            conteneur.innerHTML = '<div class="empty-state">Aucune VM ne transmet de metriques</div>';
            return;
        }

        const lignes = metriques.map(m => `
            <div style="display:flex; justify-content:space-between; align-items:center; padding:0.6rem 0; border-bottom:1px solid #e2e8f0;">
                <div>
                    <strong>${m.server_name || m.server_id}</strong>
                    <div style="font-size:0.8rem; color:#64748b;">${formaterDate(m.timestamp)}</div>
                </div>
                <div style="display:flex; gap:0.75rem; font-size:0.875rem;">
                    <span title="CPU">CPU: <strong>${m.cpu ? m.cpu.toFixed(1) : '--'}%</strong></span>
                    <span title="RAM">RAM: <strong>${m.ram ? m.ram.toFixed(1) : '--'}%</strong></span>
                </div>
            </div>
        `).join('');

        conteneur.innerHTML = lignes;

    } catch (e) {
        conteneur.innerHTML = `<div class="alert alert-danger">Erreur : ${e.message}</div>`;
    }
}
