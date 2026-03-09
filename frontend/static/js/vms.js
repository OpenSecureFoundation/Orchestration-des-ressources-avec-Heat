/*
Gestion des VMs (serveurs Nova)
*/

let allVMs = [];
let currentVMId = null;

document.addEventListener('DOMContentLoaded', function () {
  initVMsPage();
});

async function initVMsPage() {
  await loadVMs();
  setupResizeForm();
}

async function loadVMs() {
  const response = await api.get('/api/vms');

  if (!response.success) {
    showNotification('Erreur lors du chargement des VMs', 'error');
    return;
  }

  allVMs = response.data.data;
  renderVMs(allVMs);
}

function renderVMs(vms) {
  const tbody = document.getElementById('vms-tbody');
  if (!tbody) return;

  if (vms.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center">Aucune VM</td></tr>';
    return;
  }

  tbody.innerHTML = '';

  vms.forEach(vm => {
    const tr = document.createElement('tr');

    // Determiner le statut CSS
    let statusClass = 'status-shutoff';
    if (vm.status === 'ACTIVE') statusClass = 'status-active';
    else if (vm.status === 'ERROR') statusClass = 'status-error';
    else if (vm.status.includes('RESIZE')) statusClass = 'status-resize';

    // Trouver les IPs
    let publicIP = '-';
    let privateIP = '-';

    vm.addresses.forEach(addr => {
      if (addr.type === 'floating') {
        publicIP = addr.address;
      } else if (addr.type === 'fixed') {
        privateIP = addr.address;
      }
    });

    tr.innerHTML = `
            <td>${vm.name}</td>
            <td><span class="${statusClass}">${vm.status}</span></td>
            <td>${vm.flavor.name}</td>
            <td>${vm.flavor.vcpus}</td>
            <td>${vm.flavor.ram} MB</td>
            <td>${publicIP}</td>
            <td>${privateIP}</td>
            <td>
                <button class="btn btn-sm btn-secondary action-btn" onclick="viewVMDetails('${vm.id}')">Details</button>
                ${vm.status === 'SHUTOFF' ?
        `<button class="btn btn-sm btn-success action-btn" onclick="startVM('${vm.id}')">Start</button>` :
        `<button class="btn btn-sm btn-warning action-btn" onclick="stopVM('${vm.id}')">Stop</button>`
      }
                <button class="btn btn-sm btn-primary action-btn" onclick="showResizeModal('${vm.id}', '${vm.name}', '${vm.flavor.name}')">Resize</button>
            </td>
        `;
    tbody.appendChild(tr);
  });
}

function filterVMs() {
  const searchTerm = document.getElementById('search-vms').value.toLowerCase();
  const statusFilter = document.getElementById('filter-status').value;

  const filtered = allVMs.filter(vm => {
    const matchesSearch = vm.name.toLowerCase().includes(searchTerm);
    const matchesStatus = !statusFilter || vm.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  renderVMs(filtered);
}

async function viewVMDetails(vmId) {
  const response = await api.get(`/api/vms/${vmId}`);

  if (!response.success) {
    showNotification('Erreur lors du chargement des details', 'error');
    return;
  }

  const vm = response.data.data;
  currentVMId = vmId;

  document.getElementById('vm-details-title').textContent = `VM: ${vm.name}`;
  document.getElementById('vm-detail-name').textContent = vm.name;
  document.getElementById('vm-detail-status').textContent = vm.status;
  document.getElementById('vm-detail-flavor').textContent = vm.flavor.name;
  document.getElementById('vm-detail-vcpus').textContent = vm.flavor.vcpus;
  document.getElementById('vm-detail-ram').textContent = `${vm.flavor.ram} MB`;
  document.getElementById('vm-detail-disk').textContent = `${vm.flavor.disk} GB`;
  document.getElementById('vm-detail-created').textContent = formatDate(vm.created);

  // Adresses reseau
  const addressesTbody = document.getElementById('vm-addresses-tbody');
  addressesTbody.innerHTML = '';

  vm.addresses.forEach(addr => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
            <td>${addr.network}</td>
            <td>${addr.type}</td>
            <td>${addr.address}</td>
        `;
    addressesTbody.appendChild(tr);
  });

  openModal('vm-details-modal');
}

function closeVMDetailsModal() {
  closeModal('vm-details-modal');
}

async function startVM(vmId) {
  const response = await api.post(`/api/vms/${vmId}/start`, {});

  if (response.success) {
    showNotification('VM en cours de demarrage', 'success');
    setTimeout(() => loadVMs(), 2000);
  } else {
    showNotification(response.data.error || 'Erreur lors du demarrage', 'error');
  }
}

async function stopVM(vmId) {
  if (!confirmAction('Voulez-vous vraiment arreter cette VM ?')) {
    return;
  }

  const response = await api.post(`/api/vms/${vmId}/stop`, {});

  if (response.success) {
    showNotification('VM en cours d\'arret', 'success');
    setTimeout(() => loadVMs(), 2000);
  } else {
    showNotification(response.data.error || 'Erreur lors de l\'arret', 'error');
  }
}

async function rebootVM(vmId, hard) {
  const type = hard ? 'hard' : 'soft';

  if (!confirmAction(`Voulez-vous vraiment redemarrer cette VM (${type}) ?`)) {
    return;
  }

  const response = await api.post(`/api/vms/${vmId}/reboot`, { hard });

  if (response.success) {
    showNotification('VM en cours de redemarrage', 'success');
    setTimeout(() => loadVMs(), 2000);
  } else {
    showNotification(response.data.error || 'Erreur lors du redemarrage', 'error');
  }
}

function showResizeModal(vmId, vmName, currentFlavor) {
  currentVMId = vmId;

  document.getElementById('resize-vm-name').textContent = vmName;
  document.getElementById('resize-current-flavor').textContent = currentFlavor;

  // Preselectionner le flavor actuel dans le select
  const select = document.getElementById('new-flavor');
  Array.from(select.options).forEach(option => {
    if (option.value === currentFlavor) {
      option.disabled = true;
      option.textContent += ' (actuel)';
    } else {
      option.disabled = false;
    }
  });

  openModal('resize-modal');
}

function closeResizeModal() {
  closeModal('resize-modal');
  document.getElementById('resize-form').reset();
}


function setupResizeForm() {
  const form = document.getElementById('resize-form');
  if (!form) return;

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const newFlavorSelect = document.getElementById('new-flavor');
    const newFlavor = newFlavorSelect.value;

    if (!newFlavor) {
      showNotification('Veuillez selectionner un flavor', 'error');
      return;
    }

    console.log('Resize vers:', newFlavor);

    const response = await api.post(`/api/vms/${currentVMId}/resize`, {
      flavor: newFlavor
    });

    console.log('Reponse resize:', response);

    if (response.success) {
      showNotification('Resize en cours (2-5 min)', 'success');
      closeResizeModal();

      setTimeout(() => loadVMs(), 10000);
    } else {
      showNotification(response.data.error || 'Erreur lors du resize', 'error');
    }
  });
}

async function refreshVMs() {
  await loadVMs();
  showNotification('Liste actualisee', 'success');
}
