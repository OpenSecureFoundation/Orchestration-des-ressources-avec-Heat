/*
Gestion des stacks Heat
*/

let allStacks = [];
let allTemplates = [];
let currentStackId = null;

document.addEventListener('DOMContentLoaded', function () {
  initStacksPage();
});

async function initStacksPage() {
  // Charger les stacks et templates
  await Promise.all([
    loadStacks(),
    loadTemplatesForSelect()
  ]);

  // Charger les statistiques
  await loadStatistics();

  // Setup formulaires
  setupCreateStackForm();

  // Verifier si un template est preselectionne (depuis la page templates)
  const urlParams = new URLSearchParams(window.location.search);
  const templateId = urlParams.get('template');
  if (templateId) {
    showCreateStackModal();
    document.getElementById('stack-template').value = templateId;
    await loadTemplateParameters();
  }
}

async function loadStacks() {
  const response = await api.get('/api/stacks');

  if (!response.success) {
    showNotification('Erreur lors du chargement des stacks', 'error');
    return;
  }

  allStacks = response.data.data;
  renderStacks(allStacks);
}

async function loadStatistics() {
  const response = await api.get('/api/stacks/statistics');

  if (!response.success) return;

  const stats = response.data.data;

  document.getElementById('stat-total').textContent = stats.total || 0;
  document.getElementById('stat-complete').textContent = stats.completed || 0;
  document.getElementById('stat-progress').textContent = stats.in_progress || 0;
  document.getElementById('stat-failed').textContent = stats.failed || 0;
}

async function loadTemplatesForSelect() {
  const response = await api.get('/api/templates');

  if (!response.success) return;

  allTemplates = response.data.data;

  const select = document.getElementById('stack-template');
  if (!select) return;

  select.innerHTML = '<option value="">Choisir un template...</option>';

  allTemplates.forEach(template => {
    const option = document.createElement('option');
    option.value = template.id;
    option.textContent = `${template.name} (${template.type})`;
    select.appendChild(option);
  });
}

function renderStacks(stacks) {
  const tbody = document.getElementById('stacks-tbody');
  if (!tbody) return;

  if (stacks.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">Aucune stack</td></tr>';
    return;
  }

  tbody.innerHTML = '';

  stacks.forEach(stack => {
    const tr = document.createElement('tr');

    let statusClass = 'badge-secondary';
    if (stack.status && stack.status.includes('COMPLETE')) {
      statusClass = 'badge-success';
    } else if (stack.status && stack.status.includes('FAILED')) {
      statusClass = 'badge-danger';
    } else if (stack.status && stack.status.includes('PROGRESS')) {
      statusClass = 'badge-warning';
    }

    tr.innerHTML = `
            <td>${stack.name}</td>
            <td><span class="badge ${statusClass}">${stack.status || 'UNKNOWN'}</span></td>
            <td>${stack.template_name || '-'}</td>
            <td>${stack.created_by_username || '-'}</td>
            <td>${formatDate(stack.created_at)}</td>
            <td>
                <button class="btn btn-sm btn-secondary action-btn" onclick="viewStackDetails('${stack.stack_id}')">Details</button>
                <button class="btn btn-sm btn-danger action-btn" onclick="deleteStack('${stack.stack_id}', '${stack.name}')">Supprimer</button>
            </td>
        `;
    tbody.appendChild(tr);
  });
}

function filterStacks() {
  const searchTerm = document.getElementById('search-stacks').value.toLowerCase();

  const filtered = allStacks.filter(stack => {
    return stack.name.toLowerCase().includes(searchTerm) ||
      (stack.template_name && stack.template_name.toLowerCase().includes(searchTerm));
  });

  renderStacks(filtered);
}

function showCreateStackModal() {
  openModal('create-stack-modal');
}

function closeCreateStackModal() {
  closeModal('create-stack-modal');
  document.getElementById('create-stack-form').reset();
  document.getElementById('parameters-section').style.display = 'none';
}

function setupCreateStackForm() {
  const form = document.getElementById('create-stack-form');
  if (!form) return;

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const name = document.getElementById('stack-name').value;
    const templateId = parseInt(document.getElementById('stack-template').value);

    // Collecter les parametres
    const parameters = {};
    const paramInputs = document.querySelectorAll('.parameter-input input, .parameter-input select');
    paramInputs.forEach(input => {
      parameters[input.name] = input.value;
    });

    const response = await api.post('/api/stacks', {
      name,
      template_id: templateId,
      parameters
    });

    if (response.success) {
      showNotification('Stack en cours de creation', 'success');
      closeCreateStackModal();
      await loadStacks();
      await loadStatistics();
    } else {
      showNotification(response.data.error || 'Erreur lors de la creation', 'error');
    }
  });
}

async function loadTemplateParameters() {
  const templateId = document.getElementById('stack-template').value;

  if (!templateId) {
    document.getElementById('parameters-section').style.display = 'none';
    return;
  }

  const response = await api.get(`/api/templates/${templateId}/parameters`);

  if (!response.success) {
    showNotification('Erreur lors du chargement des parametres', 'error');
    return;
  }

  const parameters = response.data.data;
  const section = document.getElementById('parameters-section');
  const inputs = document.getElementById('parameters-inputs');

  if (!parameters || Object.keys(parameters).length === 0) {
    section.style.display = 'none';
    return;
  }

  section.style.display = 'block';
  inputs.innerHTML = '';

  Object.keys(parameters).forEach(paramName => {
    const param = parameters[paramName];

    const div = document.createElement('div');
    div.className = 'parameter-input';

    const label = document.createElement('label');
    label.textContent = paramName;
    div.appendChild(label);

    let input;
    if (param.type === 'number') {
      input = document.createElement('input');
      input.type = 'number';
    } else if (param.type === 'boolean') {
      input = document.createElement('select');
      input.innerHTML = '<option value="true">True</option><option value="false">False</option>';
    } else {
      input = document.createElement('input');
      input.type = 'text';
    }

    input.name = paramName;
    input.className = 'form-input';
    input.value = param.default || '';

    div.appendChild(input);

    if (param.description) {
      const small = document.createElement('small');
      small.textContent = param.description;
      div.appendChild(small);
    }

    inputs.appendChild(div);
  });
}

async function viewStackDetails(stackId) {
  const response = await api.get(`/api/stacks/${stackId}/status`);

  if (!response.success) {
    showNotification('Erreur lors du chargement des details', 'error');
    return;
  }

  const data = response.data.data;

  // Trouver la stack dans la liste
  const stack = allStacks.find(s => s.stack_id === stackId);

  document.getElementById('stack-details-title').textContent = `Details: ${stack ? stack.name : stackId}`;
  document.getElementById('detail-name').textContent = stack ? stack.name : '-';
  document.getElementById('detail-status').textContent = data.status || '-';
  document.getElementById('detail-template').textContent = stack ? stack.template_name : '-';
  document.getElementById('detail-created').textContent = stack ? formatDate(stack.created_at) : '-';

  // Charger les ressources
  await loadStackResources(stackId);

  // Afficher les outputs
  const outputsSection = document.getElementById('outputs-section');
  if (data.outputs && Object.keys(data.outputs).length > 0) {
    outputsSection.innerHTML = '';

    Object.keys(data.outputs).forEach(key => {
      const div = document.createElement('div');
      div.className = 'output-item';
      div.innerHTML = `
                <div class="output-key">${key}</div>
                <div class="output-value">${data.outputs[key]}</div>
            `;
      outputsSection.appendChild(div);
    });
  } else {
    outputsSection.innerHTML = '<p class="text-muted">Aucun output</p>';
  }

  openModal('stack-details-modal');
}

async function loadStackResources(stackId) {
  const response = await api.get(`/api/stacks/${stackId}/resources`);

  const tbody = document.getElementById('resources-tbody');

  if (!response.success || !response.data.data || response.data.data.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center">Aucune ressource</td></tr>';
    return;
  }

  const resources = response.data.data;
  tbody.innerHTML = '';

  resources.forEach(resource => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
            <td>${resource.name}</td>
            <td>${resource.type}</td>
            <td><span class="badge badge-${resource.status.includes('COMPLETE') ? 'success' : 'secondary'}">${resource.status}</span></td>
            <td><small>${resource.id}</small></td>
        `;
    tbody.appendChild(tr);
  });
}

function closeStackDetailsModal() {
  closeModal('stack-details-modal');
}

async function deleteStack(stackId, stackName) {
  if (!confirmAction(`Voulez-vous vraiment supprimer la stack "${stackName}" ?`)) {
    return;
  }

  const response = await api.delete(`/api/stacks/${stackId}`);

  if (response.success) {
    showNotification('Stack en cours de suppression', 'success');
    await loadStacks();
    await loadStatistics();
  } else {
    showNotification(response.data.error || 'Erreur lors de la suppression', 'error');
  }
}

async function refreshStacks() {
  await Promise.all([
    loadStacks(),
    loadStatistics()
  ]);
  showNotification('Liste actualisee', 'success');
}
