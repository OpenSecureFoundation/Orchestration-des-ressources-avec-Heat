/*
Gestion des templates Heat
*/

let allTemplates = [];
let currentTemplateId = null;
let codeEditor = null;

document.addEventListener('DOMContentLoaded', function () {
  initTemplatesPage();
});

async function initTemplatesPage() {
  // Charger les templates
  await loadTemplates();

  // Setup formulaires
  setupGitImportForm();
  setupUploadForm();
  setupTemplateForm();

  // Setup drag & drop
  setupDragAndDrop();
}

async function loadTemplates() {
  const response = await api.get('/api/templates');

  if (!response.success) {
    showNotification('Erreur lors du chargement des templates', 'error');
    return;
  }

  allTemplates = response.data.data;
  renderTemplates(allTemplates);
}

function renderTemplates(templates) {
  const tbody = document.getElementById('templates-tbody');
  if (!tbody) return;

  if (templates.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">Aucun template</td></tr>';
    return;
  }

  tbody.innerHTML = '';

  templates.forEach(template => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
            <td>${template.name}</td>
            <td><span class="badge badge-secondary">${template.type}</span></td>
            <td>${template.description || '-'}</td>
            <td>${template.created_by_username || 'Systeme'}</td>
            <td>${formatDate(template.created_at)}</td>
            <td>
                <button class="btn btn-sm btn-secondary action-btn" onclick="viewTemplate(${template.id})">Voir</button>
                ${template.type !== 'builtin' ? `
                    <button class="btn btn-sm btn-primary action-btn" onclick="editTemplate(${template.id})">Modifier</button>
                    <button class="btn btn-sm btn-danger action-btn" onclick="deleteTemplate(${template.id})">Supprimer</button>
                ` : ''}
                <button class="btn btn-sm btn-success action-btn" onclick="deployTemplate(${template.id})">Deployer</button>
            </td>
        `;
    tbody.appendChild(tr);
  });
}

function filterTemplates() {
  const searchTerm = document.getElementById('search-templates').value.toLowerCase();
  const typeFilter = document.getElementById('filter-type').value;

  const filtered = allTemplates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm) ||
      (template.description && template.description.toLowerCase().includes(searchTerm));

    const matchesType = !typeFilter || template.type === typeFilter;

    return matchesSearch && matchesType;
  });

  renderTemplates(filtered);
}

async function viewTemplate(templateId) {
  const response = await api.get(`/api/templates/${templateId}`);

  if (!response.success) {
    showNotification('Erreur lors du chargement du template', 'error');
    return;
  }

  const template = response.data.data;

  document.getElementById('modal-title').textContent = template.name;
  document.getElementById('template-name').value = template.name;
  document.getElementById('template-name').disabled = true;
  document.getElementById('template-description').value = template.description || '';
  document.getElementById('template-description').disabled = true;
  document.getElementById('template-content').value = template.content;
  document.getElementById('template-public').checked = template.is_public;
  document.getElementById('template-public').disabled = true;

  // Initialiser l'editeur si CodeMirror est disponible
  if (typeof CodeMirror !== 'undefined') {
    if (codeEditor) {
      codeEditor.toTextArea();
    }

    const textarea = document.getElementById('template-content');
    codeEditor = CodeMirror.fromTextArea(textarea, {
      mode: 'yaml',
      theme: 'monokai',
      lineNumbers: true,
      readOnly: true
    });
  }

  // Cacher le bouton submit
  document.querySelector('#template-form button[type="submit"]').style.display = 'none';

  openModal('template-modal');
}

async function editTemplate(templateId) {
  const response = await api.get(`/api/templates/${templateId}`);

  if (!response.success) {
    showNotification('Erreur lors du chargement du template', 'error');
    return;
  }

  const template = response.data.data;
  currentTemplateId = templateId;

  document.getElementById('modal-title').textContent = 'Modifier: ' + template.name;
  document.getElementById('template-name').value = template.name;
  document.getElementById('template-name').disabled = true;
  document.getElementById('template-description').value = template.description || '';
  document.getElementById('template-description').disabled = false;
  document.getElementById('template-content').value = template.content;
  document.getElementById('template-public').checked = template.is_public;
  document.getElementById('template-public').disabled = false;

  // Initialiser l'editeur
  if (typeof CodeMirror !== 'undefined') {
    if (codeEditor) {
      codeEditor.toTextArea();
    }

    const textarea = document.getElementById('template-content');
    codeEditor = CodeMirror.fromTextArea(textarea, {
      mode: 'yaml',
      theme: 'monokai',
      lineNumbers: true,
      readOnly: false
    });
  }

  document.querySelector('#template-form button[type="submit"]').style.display = 'block';

  openModal('template-modal');
}

async function deleteTemplate(templateId) {
  if (!confirmAction('Voulez-vous vraiment supprimer ce template ?')) {
    return;
  }

  const response = await api.delete(`/api/templates/${templateId}`);

  if (response.success) {
    showNotification('Template supprime', 'success');
    await loadTemplates();
  } else {
    showNotification(response.data.error || 'Erreur lors de la suppression', 'error');
  }
}

function showCreateModal() {
  currentTemplateId = null;

  document.getElementById('modal-title').textContent = 'Nouveau Template';
  document.getElementById('template-name').value = '';
  document.getElementById('template-name').disabled = false;
  document.getElementById('template-description').value = '';
  document.getElementById('template-description').disabled = false;
  document.getElementById('template-content').value = `heat_template_version: 2021-04-16

description: Mon template

resources:
  # Definir vos ressources ici
`;
  document.getElementById('template-public').checked = false;
  document.getElementById('template-public').disabled = false;

  // Initialiser l'editeur
  if (typeof CodeMirror !== 'undefined') {
    if (codeEditor) {
      codeEditor.toTextArea();
    }

    const textarea = document.getElementById('template-content');
    codeEditor = CodeMirror.fromTextArea(textarea, {
      mode: 'yaml',
      theme: 'monokai',
      lineNumbers: true,
      readOnly: false
    });
  }

  document.querySelector('#template-form button[type="submit"]').style.display = 'block';

  openModal('template-modal');
}

function closeTemplateModal() {
  if (codeEditor) {
    codeEditor.toTextArea();
    codeEditor = null;
  }

  closeModal('template-modal');
}

function setupTemplateForm() {
  const form = document.getElementById('template-form');
  if (!form) return;

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const name = document.getElementById('template-name').value;
    const description = document.getElementById('template-description').value;
    const isPublic = document.getElementById('template-public').checked;

    let content;
    if (codeEditor) {
      content = codeEditor.getValue();
    } else {
      content = document.getElementById('template-content').value;
    }

    if (currentTemplateId) {
      // Modification
      const response = await api.put(`/api/templates/${currentTemplateId}`, {
        content,
        description,
        is_public: isPublic
      });

      if (response.success) {
        showNotification('Template modifie', 'success');
        closeTemplateModal();
        await loadTemplates();
      } else {
        showNotification(response.data.error || 'Erreur lors de la modification', 'error');
      }
    } else {
      // Creation
      const response = await api.post('/api/templates', {
        name,
        content,
        description,
        is_public: isPublic
      });

      if (response.success) {
        showNotification('Template cree', 'success');
        closeTemplateModal();
        await loadTemplates();
      } else {
        showNotification(response.data.error || 'Erreur lors de la creation', 'error');
      }
    }
  });
}

function setupGitImportForm() {
  const form = document.getElementById('git-import-form');
  if (!form) return;

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const url = document.getElementById('git-url').value;
    const branch = document.getElementById('git-branch').value;

    showNotification('Import en cours...', 'info');

    const response = await api.post('/api/templates/import-git', {
      repo_url: url,
      branch: branch
    });

    if (response.success) {
      const data = response.data.data;

      // Afficher les resultats
      const resultsDiv = document.getElementById('import-results');
      const successList = document.getElementById('import-success-list');
      const errorList = document.getElementById('import-error-list');

      resultsDiv.style.display = 'block';

      if (data.imported.length > 0) {
        successList.innerHTML = '<h5>Templates importes:</h5>';
        data.imported.forEach(t => {
          const div = document.createElement('div');
          div.className = 'import-success-item';
          div.textContent = `${t.name} (${t.file})`;
          successList.appendChild(div);
        });
      } else {
        successList.innerHTML = '';
      }

      if (data.errors.length > 0) {
        errorList.innerHTML = '<h5>Erreurs:</h5>';
        data.errors.forEach(err => {
          const div = document.createElement('div');
          div.className = 'import-error-item';
          div.textContent = err;
          errorList.appendChild(div);
        });
      } else {
        errorList.innerHTML = '';
      }

      showNotification(`${data.imported.length} templates importes`, 'success');
      await loadTemplates();
    } else {
      showNotification(response.data.error || 'Erreur lors de l\'import', 'error');
    }
  });
}

function setupUploadForm() {
  const form = document.getElementById('upload-form');
  const fileInput = document.getElementById('file-input');
  const fileInfo = document.getElementById('file-info');
  const fileName = document.getElementById('file-name');

  if (!form || !fileInput) return;

  fileInput.addEventListener('change', function () {
    if (this.files.length > 0) {
      const file = this.files[0];
      fileName.textContent = file.name;
      fileInfo.style.display = 'block';
    }
  });

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    if (fileInput.files.length === 0) {
      showNotification('Veuillez selectionner un fichier', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
      const response = await fetch('/api/templates/upload', {
        method: 'POST',
        headers: {
          'X-Session-Token': getSessionToken()
        },
        body: formData
      });

      const data = await response.json();

      if (data.success) {
        showNotification('Template uploade', 'success');
        fileInput.value = '';
        fileInfo.style.display = 'none';
        await loadTemplates();
      } else {
        showNotification(data.error || 'Erreur lors de l\'upload', 'error');
      }
    } catch (error) {
      showNotification('Erreur lors de l\'upload', 'error');
    }
  });
}

function setupDragAndDrop() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');

  if (!dropZone || !fileInput) return;

  dropZone.addEventListener('click', function () {
    fileInput.click();
  });

  dropZone.addEventListener('dragover', function (e) {
    e.preventDefault();
    this.classList.add('dragover');
  });

  dropZone.addEventListener('dragleave', function () {
    this.classList.remove('dragover');
  });

  dropZone.addEventListener('drop', function (e) {
    e.preventDefault();
    this.classList.remove('dragover');

    if (e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      fileInput.dispatchEvent(new Event('change'));
    }
  });
}

function deployTemplate(templateId) {
  // Rediriger vers la page stacks avec le template preselectionne
  window.location.href = `/stacks?template=${templateId}`;
}
