/*
Dashboard de monitoring temps reel
*/

let selectedServer = null;
let availableMetrics = {};
let enabledMetrics = ['cpu', 'ram', 'disk'];

document.addEventListener('DOMContentLoaded', function () {
  initDashboard();
});

async function initDashboard() {
  // Charger les metriques disponibles
  await loadAvailableMetrics();

  // Charger la liste des serveurs
  await loadServers();

  // Initialiser WebSocket
  initWebSocket();

  // Ecouter les mises a jour
  onMetricsUpdate(handleMetricsUpdate);
  onScalingEvent(handleScalingEvent);

  // Setup des sliders de politique
  setupPolicySliders();
}

async function loadAvailableMetrics() {
  const response = await api.get('/api/metrics/available');

  if (response.success) {
    availableMetrics = response.data.data;
    renderMetricsCheckboxes();
  }
}

function renderMetricsCheckboxes() {
  const container = document.getElementById('metrics-checkboxes');
  if (!container) return;

  container.innerHTML = '';

  Object.keys(availableMetrics).forEach(metricType => {
    const metric = availableMetrics[metricType];

    const div = document.createElement('div');
    div.className = 'metric-checkbox';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `metric-${metricType}`;
    checkbox.checked = metric.default_enabled;
    checkbox.addEventListener('change', () => toggleMetric(metricType, checkbox.checked));

    const label = document.createElement('label');
    label.htmlFor = `metric-${metricType}`;
    label.textContent = `${metric.name} (${metric.unit})`;

    div.appendChild(checkbox);
    div.appendChild(label);
    container.appendChild(div);

    if (metric.default_enabled) {
      enabledMetrics.push(metricType);
    }
  });
}

function toggleMetric(metricType, enabled) {
  if (enabled) {
    if (!enabledMetrics.includes(metricType)) {
      enabledMetrics.push(metricType);
    }
  } else {
    enabledMetrics = enabledMetrics.filter(m => m !== metricType);
  }

  renderMetricsGrid();
}

function renderMetricsGrid() {
  const grid = document.getElementById('metrics-grid');
  if (!grid) return;

  grid.innerHTML = '';

  enabledMetrics.forEach(metricType => {
    const metric = availableMetrics[metricType];
    if (!metric) return;

    const card = document.createElement('div');
    card.className = 'metric-card';
    card.id = `metric-card-${metricType}`;

    card.innerHTML = `
            <h4>
                ${metric.name}
                <span id="value-${metricType}" class="metric-value">-</span>
            </h4>
            <canvas id="chart-${metricType}" class="metric-chart"></canvas>
        `;

    grid.appendChild(card);

    // Creer le graphique
    setTimeout(() => {
      createMetricChart(
        `chart-${metricType}`,
        metric.name,
        metric.unit,
        getMetricColor(metricType)
      );
    }, 100);
  });
}

async function loadServers() {
  const response = await api.get('/api/vms');

  if (!response.success) {
    showNotification('Erreur lors du chargement des serveurs', 'error');
    return;
  }

  const servers = response.data.data;
  const selector = document.getElementById('server-selector');

  if (!selector) return;

  selector.innerHTML = '<option value="">Selectionner un serveur...</option>';

  servers.forEach(server => {
    const option = document.createElement('option');
    option.value = server.id;
    option.textContent = `${server.name} (${server.status})`;
    selector.appendChild(option);
  });

  selector.addEventListener('change', function () {
    selectServer(this.value);
  });
}

async function selectServer(serverId) {
  if (!serverId) {
    hideServerInfo();
    return;
  }

  // Desabonner de l'ancien serveur
  if (selectedServer) {
    unsubscribeFromServer(selectedServer);
  }

  selectedServer = serverId;

  // Charger les infos du serveur
  const response = await api.get(`/api/vms/${serverId}`);

  if (!response.success) {
    showNotification('Erreur lors du chargement du serveur', 'error');
    return;
  }

  const server = response.data.data;
  displayServerInfo(server);

  // Charger la politique de scaling
  await loadScalingPolicy(serverId);

  // Charger l'historique des evenements
  await loadScalingEvents(serverId);

  // S'abonner aux mises a jour
  subscribeToServer(serverId);

  // Afficher les cartes
  document.getElementById('server-info').style.display = 'block';
  document.getElementById('metrics-config').style.display = 'block';
  document.getElementById('metrics-grid').style.display = 'grid';
  document.getElementById('policy-card').style.display = 'block';
  document.getElementById('events-card').style.display = 'block';

  // Détruire les anciens graphiques
  destroyAllCharts();

  renderMetricsGrid();

  // IMPORTANT : Attendre que les canvas soient créés
  setTimeout(() => {
    // S'abonner aux mises à jour WebSocket
    subscribeToServer(serverId);
  }, 500);
}

function displayServerInfo(server) {
  document.getElementById('server-name').textContent = server.name;
  document.getElementById('server-status').textContent = server.status;
  document.getElementById('server-flavor').textContent = server.flavor.name;
  document.getElementById('server-vcpus').textContent = server.flavor.vcpus;
  document.getElementById('server-ram').textContent = `${server.flavor.ram} MB`;
}

function hideServerInfo() {
  document.getElementById('server-info').style.display = 'none';
  document.getElementById('metrics-config').style.display = 'none';
  document.getElementById('metrics-grid').style.display = 'none';
  document.getElementById('policy-card').style.display = 'none';
  document.getElementById('events-card').style.display = 'none';

  destroyAllCharts();
}

async function loadScalingPolicy(serverId) {
  const response = await api.get(`/api/metrics/policies/${serverId}`);

  if (response.success) {
    const policy = response.data.data;

    document.getElementById('policy-metric').value = policy.metric_type;
    document.getElementById('threshold-up').value = policy.scale_up_threshold;
    document.getElementById('threshold-down').value = policy.scale_down_threshold;
    document.getElementById('policy-enabled').checked = policy.enabled;

    document.getElementById('threshold-up-value').textContent = policy.scale_up_threshold;
    document.getElementById('threshold-down-value').textContent = policy.scale_down_threshold;
  } else {
    // Creer une politique par defaut
    document.getElementById('policy-metric').value = 'cpu';
    document.getElementById('threshold-up').value = 80;
    document.getElementById('threshold-down').value = 20;
    document.getElementById('policy-enabled').checked = true;
  }

  // Remplir le select des metriques
  const metricSelect = document.getElementById('policy-metric');
  metricSelect.innerHTML = '';

  Object.keys(availableMetrics).forEach(metricType => {
    const metric = availableMetrics[metricType];
    const option = document.createElement('option');
    option.value = metricType;
    option.textContent = `${metric.name} (${metric.unit})`;
    metricSelect.appendChild(option);
  });
}

async function loadScalingEvents(serverId) {
  const response = await api.get(`/api/metrics/scaling-events/${serverId}?limit=20`);

  if (!response.success) return;

  const events = response.data.data;
  const list = document.getElementById('events-list');

  if (events.length === 0) {
    list.innerHTML = '<p class="text-muted">Aucun evenement</p>';
    return;
  }

  list.innerHTML = '';

  events.forEach(event => {
    const item = document.createElement('div');
    item.className = `event-item ${event.event_type}`;

    item.innerHTML = `
            <div class="event-header">
                <span>${event.event_type.toUpperCase()}</span>
                <span class="event-time">${formatTimestamp(new Date(event.timestamp).getTime() / 1000)}</span>
            </div>
            <div class="event-message">${event.message}</div>
        `;

    list.appendChild(item);
  });
}

function handleMetricsUpdate(data) {
  if (data.server_id !== selectedServer) return;

  // Mettre a jour les valeurs affichees
  Object.keys(data.metrics).forEach(metricType => {
    const metric = data.metrics[metricType];
    const valueEl = document.getElementById(`value-${metricType}`);

    if (valueEl) {
      valueEl.textContent = `${metric.value.toFixed(1)} ${metric.unit}`;
    }

    // Mettre a jour le graphique
    updateMetricChart(`chart-${metricType}`, metric.value, data.timestamp);
  });

  // Mettre a jour le flavor si change
  if (data.flavor) {
    document.getElementById('server-flavor').textContent = data.flavor.name;
    document.getElementById('server-vcpus').textContent = data.flavor.vcpus;
    document.getElementById('server-ram').textContent = `${data.flavor.ram} MB`;
  }
}

function handleScalingEvent(data) {
  showNotification(`Scaling: ${data.event_type}`, 'info');

  // Recharger les evenements
  if (selectedServer) {
    loadScalingEvents(selectedServer);
  }
}

function setupPolicySliders() {
  const upSlider = document.getElementById('threshold-up');
  const downSlider = document.getElementById('threshold-down');
  const upValue = document.getElementById('threshold-up-value');
  const downValue = document.getElementById('threshold-down-value');

  if (upSlider) {
    upSlider.addEventListener('input', function () {
      upValue.textContent = this.value;
    });
  }

  if (downSlider) {
    downSlider.addEventListener('input', function () {
      downValue.textContent = this.value;
    });
  }
}

async function savePolicyConfig() {
  if (!selectedServer) return;

  const metricType = document.getElementById('policy-metric').value;
  const scaleUp = parseInt(document.getElementById('threshold-up').value);
  const scaleDown = parseInt(document.getElementById('threshold-down').value);
  const enabled = document.getElementById('policy-enabled').checked;

  if (scaleUp <= scaleDown) {
    showNotification('Le seuil scale up doit etre superieur a scale down', 'error');
    return;
  }

  const response = await api.put(`/api/metrics/policies/${selectedServer}`, {
    metric_type: metricType,
    scale_up_threshold: scaleUp,
    scale_down_threshold: scaleDown,
    enabled: enabled
  });

  if (response.success) {
    showNotification('Politique sauvegardee', 'success');
  } else {
    showNotification(response.data.error || 'Erreur lors de la sauvegarde', 'error');
  }
}

function refreshServers() {
  loadServers();
}
