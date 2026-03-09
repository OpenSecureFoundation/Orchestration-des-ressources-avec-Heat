/*
Gestion des graphiques de metriques avec Chart.js
*/

// Stockage des instances de graphiques
const charts = {};

// Historique des metriques (cote client)
const metricsHistory = {};

// Creer un graphique pour une metrique
function createMetricChart(canvasId, metricName, unit, color) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) {
    console.error(`Canvas ${canvasId} non trouve`);
    return null;
  }

  // Détruire l'ancien graphique s'il existe
  if (charts[canvasId]) {
    charts[canvasId].destroy();
    delete charts[canvasId];
  }

  // Forcer les dimensions du canvas
  canvas.style.width = '100%';
  canvas.style.height = '200px';
  canvas.width = canvas.offsetWidth;
  canvas.height = 200;

  try {
    const chart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: metricName,
          data: [],
          borderColor: color,
          backgroundColor: color + '20',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 2,
          pointHoverRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            mode: 'index',
            intersect: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: unit === '%' ? 100 : undefined,
            ticks: {
              callback: function (value) {
                return value + unit;
              }
            }
          },
          x: {
            display: false
          }
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false
        }
      }
    });

    charts[canvasId] = chart;
    metricsHistory[canvasId] = [];

    console.log(`Graphique cree: ${canvasId}`);
    return chart;

  } catch (error) {
    console.error(`Erreur creation graphique ${canvasId}:`, error);
    return null;
  }
}

// Mettre a jour un graphique avec une nouvelle valeur
function updateMetricChart(canvasId, value, timestamp) {
  const chart = charts[canvasId];
  if (!chart) {
    console.warn(`Graphique ${canvasId} non trouve pour mise a jour`);
    return;
  }

  const history = metricsHistory[canvasId];

  // Ajouter la nouvelle valeur
  history.push({ value, timestamp });

  // Garder seulement les 40 derniers points
  if (history.length > 40) {
    history.shift();
  }

  try {
    // Mettre a jour le graphique
    chart.data.labels = history.map((_, i) => i);
    chart.data.datasets[0].data = history.map(h => h.value);
    chart.update('none'); // Animation desactivee pour fluidite

    console.log(`Graphique ${canvasId} mis a jour: ${value}`);
  } catch (error) {
    console.error(`Erreur mise a jour graphique ${canvasId}:`, error);
  }
}

// Couleurs par type de metrique
const metricColors = {
  'cpu': '#667eea',
  'ram': '#f59e0b',
  'disk': '#10b981',
  'network_in': '#3b82f6',
  'network_out': '#8b5cf6',
  'network_latency': '#ef4444'
};

// Obtenir la couleur pour une metrique
function getMetricColor(metricType) {
  return metricColors[metricType] || '#6c757d';
}

// Detruire tous les graphiques
function destroyAllCharts() {
  console.log('Destruction de tous les graphiques');

  Object.keys(charts).forEach(canvasId => {
    if (charts[canvasId]) {
      try {
        charts[canvasId].destroy();
      } catch (error) {
        console.error(`Erreur destruction ${canvasId}:`, error);
      }
      delete charts[canvasId];
    }
  });

  Object.keys(metricsHistory).forEach(key => {
    delete metricsHistory[key];
  });
}
