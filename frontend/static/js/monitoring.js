/**
 * Page Monitoring - graphiques temps reel via WebSocket.
 */

const socket = io();
let vmSelectionnee = null;
let graphiques = {};
const MAX_POINTS = 30;

// Historique local pour les graphiques
const historiques = {
    cpu: [], ram: [], disk: [], net_sent: [], net_recv: [], labels: []
};

document.addEventListener('DOMContentLoaded', () => {
    chargerListeVMs();

    // Lecture du parametre URL ?vm=<id>
    const params = new URLSearchParams(window.location.search);
    const vmParam = params.get('vm');
    if (vmParam) {
        setTimeout(() => selectionnerVM(vmParam), 500);
    }

    // Reception des metriques en temps reel
    socket.on('metrics_update', (data) => {
        if (data.server_id === vmSelectionnee) {
            mettreAJourGraphiques(data);
        }
    });
});

async function chargerListeVMs() {
    try {
        const data = await api.get('/api/vms');
        const select = document.getElementById('vm-select');
        const vms = data.vms || [];
        select.innerHTML = '<option value="">-- Choisir une VM --</option>' +
            vms.map(v => `<option value="${v.id}">${v.name} (${v.status})</option>`).join('');
    } catch (e) {
        console.error('Erreur chargement VMs :', e);
    }
}

async function selectionnerVM(vmId) {
    if (!vmId) return;

    // Desabonnement de l'ancienne VM
    if (vmSelectionnee) {
        socket.emit('unsubscribe', { server_id: vmSelectionnee });
    }

    vmSelectionnee = vmId;

    // Mise a jour du select si appele depuis URL
    const select = document.getElementById('vm-select');
    if (select.value !== vmId) select.value = vmId;

    // Affichage de la zone graphiques
    document.getElementById('monitoring-placeholder').style.display = 'none';
    document.getElementById('monitoring-charts').style.display = 'block';
    document.getElementById('card-scaling').style.display = 'block';

    // Initialisation des graphiques
    reinitialiserHistoriques();
    creerGraphiques();

    // Abonnement WebSocket
    socket.emit('subscribe', { server_id: vmId });

    // Chargement de l'historique
    await chargerHistorique(vmId);

    // Chargement de la politique de scaling existante
    await chargerPolitiqueExistante(vmId);

    // Info VM
    try {
        const data = await api.get(`/api/vms/${vmId}`);
        const vm = data.vm;
        const ips = (vm.ip_addresses || []).map(a => a.ip).join(', ');
        document.getElementById('vm-info-bar').innerHTML =
            `VM : <strong>${vm.name}</strong> | ` +
            `Statut : <strong>${vm.status}</strong> | ` +
            `IP : <strong>${ips || '--'}</strong> | ` +
            `ID : <code style="font-size:0.8rem;">${vm.id.substring(0,12)}...</code>`;
    } catch (e) {
        console.error('Erreur infos VM :', e);
    }
}

function reinitialiserHistoriques() {
    historiques.cpu = [];
    historiques.ram = [];
    historiques.disk = [];
    historiques.net_sent = [];
    historiques.net_recv = [];
    historiques.labels = [];
}

function creerGraphiques() {
    // Destruction des graphiques existants
    Object.values(graphiques).forEach(g => g.destroy());
    graphiques = {};

    const optionsCommunes = {
        responsive: true,
        maintainAspectRatio: true,
        animation: { duration: 200 },
        scales: {
            y: { min: 0, max: 100, grid: { color: '#e2e8f0' } },
            x: { grid: { display: false }, ticks: { maxTicksLimit: 6 } },
        },
        plugins: { legend: { display: false } },
    };

    graphiques.cpu = new Chart(document.getElementById('chart-cpu').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{ data: [], borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,0.1)', fill: true, tension: 0.4, pointRadius: 2 }]
        },
        options: { ...optionsCommunes },
    });

    graphiques.ram = new Chart(document.getElementById('chart-ram').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{ data: [], borderColor: '#16a34a', backgroundColor: 'rgba(22,163,74,0.1)', fill: true, tension: 0.4, pointRadius: 2 }]
        },
        options: { ...optionsCommunes },
    });

    graphiques.disk = new Chart(document.getElementById('chart-disk').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{ data: [], borderColor: '#d97706', backgroundColor: 'rgba(217,119,6,0.1)', fill: true, tension: 0.4, pointRadius: 2 }]
        },
        options: { ...optionsCommunes },
    });

    graphiques.network = new Chart(document.getElementById('chart-network').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Envoye', data: [], borderColor: '#7c3aed', backgroundColor: 'transparent', tension: 0.4, pointRadius: 2 },
                { label: 'Recu', data: [], borderColor: '#db2777', backgroundColor: 'transparent', tension: 0.4, pointRadius: 2 },
            ]
        },
        options: {
            ...optionsCommunes,
            scales: { ...optionsCommunes.scales, y: { min: 0, grid: { color: '#e2e8f0' } } },
            plugins: { legend: { display: true } },
        },
    });
}

function mettreAJourGraphiques(data) {
    const heure = new Date(data.timestamp || Date.now()).toLocaleTimeString('fr-FR');

    // Ajout dans les historiques (limite a MAX_POINTS)
    const ajouter = (liste, valeur) => {
        liste.push(valeur || 0);
        if (liste.length > MAX_POINTS) liste.shift();
    };

    ajouter(historiques.labels, heure);
    ajouter(historiques.cpu, data.cpu);
    ajouter(historiques.ram, data.ram);
    ajouter(historiques.disk, data.disk);

    const net = data.network || {};
    ajouter(historiques.net_sent, Math.round((net.bytes_sent || 0) / 1024));
    ajouter(historiques.net_recv, Math.round((net.bytes_recv || 0) / 1024));

    // Mise a jour des graphiques Chart.js
    const mettrAJourChart = (chart, donnees, labels) => {
        chart.data.labels = labels;
        chart.data.datasets[0].data = donnees;
        chart.update('none');
    };

    mettrAJourChart(graphiques.cpu, historiques.cpu, historiques.labels);
    mettrAJourChart(graphiques.ram, historiques.ram, historiques.labels);
    mettrAJourChart(graphiques.disk, historiques.disk, historiques.labels);

    graphiques.network.data.labels = historiques.labels;
    graphiques.network.data.datasets[0].data = historiques.net_sent;
    graphiques.network.data.datasets[1].data = historiques.net_recv;
    graphiques.network.update('none');

    // Valeurs courantes
    document.getElementById('cpu-value').textContent = data.cpu ? `${data.cpu.toFixed(1)}%` : '--';
    document.getElementById('ram-value').textContent = data.ram ? `${data.ram.toFixed(1)}%` : '--';
    document.getElementById('disk-value').textContent = data.disk ? `${data.disk.toFixed(1)}%` : '--';
}

async function chargerHistorique(vmId) {
    try {
        const data = await api.get(`/api/metrics/${vmId}/history?hours=1`);
        const historique = data.history || [];
        historique.forEach(m => mettreAJourGraphiques(m));
    } catch (e) {
        console.error('Erreur chargement historique :', e);
    }
}

async function chargerPolitiqueExistante(vmId) {
    try {
        const data = await api.get(`/api/metrics/scaling/${vmId}`);
        const p = data.policy;
        if (p && p.metric) {
            document.getElementById('scaling-metric').value = p.metric;
            document.getElementById('scaling-threshold-up').value = p.threshold_up;
            document.getElementById('scaling-threshold-down').value = p.threshold_down;
            document.getElementById('scaling-cooldown').value = p.cooldown;
            document.getElementById('politique-status').innerHTML =
                '<div class="alert alert-success">Politique de scaling active</div>';
        } else {
            document.getElementById('politique-status').innerHTML = '';
        }
    } catch (e) {
        console.error('Erreur chargement politique :', e);
    }
}

async function sauvegarderPolitique() {
    if (!vmSelectionnee) return;
    try {
        await api.post(`/api/metrics/scaling/${vmSelectionnee}`, {
            server_name: document.getElementById('vm-select').options[document.getElementById('vm-select').selectedIndex].text.split(' ')[0],
            metric: document.getElementById('scaling-metric').value,
            threshold_up: parseFloat(document.getElementById('scaling-threshold-up').value),
            threshold_down: parseFloat(document.getElementById('scaling-threshold-down').value),
            cooldown: parseInt(document.getElementById('scaling-cooldown').value),
        });
        document.getElementById('politique-status').innerHTML =
            '<div class="alert alert-success">Politique sauvegardee et active</div>';
        afficherToast('Politique de scaling activee', 'success');
    } catch (e) {
        afficherToast(`Erreur : ${e.message}`, 'error');
    }
}

async function supprimerPolitique() {
    if (!vmSelectionnee) return;
    try {
        await api.delete(`/api/metrics/scaling/${vmSelectionnee}`);
        document.getElementById('politique-status').innerHTML = '';
        afficherToast('Politique de scaling desactivee', 'success');
    } catch (e) {
        afficherToast(`Erreur : ${e.message}`, 'error');
    }
}
