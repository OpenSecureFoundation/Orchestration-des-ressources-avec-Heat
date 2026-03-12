/**
 * Page Templates — gestion des templates Heat.
 */

let templateASupprimer = null;
let modeCreation = 'editeur';

document.addEventListener('DOMContentLoaded', chargerTemplates);

async function chargerTemplates() {
    const cont = document.getElementById('liste-templates');
    cont.innerHTML = '<div class="loading">Chargement...</div>';
    try {
        const data = await api.get('/api/templates');
        const templates = data.templates || [];

        if (!templates.length) {
            cont.innerHTML = '<div class="empty-state">Aucun template disponible.</div>';
            return;
        }

        const builtin = templates.filter(t => t.category === 'builtin');
        const user    = templates.filter(t => t.category === 'user');

        cont.innerHTML = `
        ${builtin.length ? `
        <h3 style="margin-bottom:0.75rem;color:#475569;font-size:0.9rem;text-transform:uppercase;letter-spacing:0.05em;">
            Templates intégrés
        </h3>
        <div class="templates-grid">${builtin.map(templateCard).join('')}</div>` : ''}

        ${user.length ? `
        <h3 style="margin:1.5rem 0 0.75rem;color:#475569;font-size:0.9rem;text-transform:uppercase;letter-spacing:0.05em;">
            Mes templates
        </h3>
        <div class="templates-grid">${user.map(templateCard).join('')}</div>` : ''}

        ${!user.length ? `
        <div style="margin-top:1.5rem;padding:1rem;background:#f8fafc;border:1px dashed #e2e8f0;border-radius:8px;text-align:center;color:#94a3b8;">
            Aucun template personnalisé — cliquez sur <strong>+ Nouveau Template</strong> pour créer le vôtre.
        </div>` : ''}`;

    } catch (e) {
        cont.innerHTML = `<div class="alert alert-danger">Erreur : ${e.message}</div>`;
    }
}

function templateCard(t) {
    const estUser = t.category === 'user';
    return `
    <div class="template-card">
        <div class="template-card-header">
            <span class="badge ${estUser ? 'badge-info' : 'badge-secondary'}" style="font-size:0.72rem;">
                ${estUser ? 'Mon template' : 'Builtin'}
            </span>
            <h4 class="template-card-titre">${t.name}</h4>
            <p class="template-card-desc">${t.description || 'Aucune description'}</p>
        </div>
        <div class="template-card-footer">
            <button class="btn btn-sm btn-outline" onclick="voirTemplate(${t.id},'${t.name}')">
                Voir le YAML
            </button>
            ${estUser ? `
            <button class="btn btn-sm btn-danger" onclick="demanderSuppressionTemplate(${t.id},'${t.name}')">
                Supprimer
            </button>` : ''}
        </div>
    </div>`;
}

// =====================================================================
// CREATION TEMPLATE
// =====================================================================

function ouvrirModalCreation() {
    // Réinitialiser
    ['tmpl-nom','tmpl-desc','tmpl-contenu','tmpl-upload-nom','tmpl-upload-desc'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    document.getElementById('upload-label').textContent = 'Cliquez ou glissez un fichier .yaml / .yml';
    switchCreationMode('editeur', document.getElementById('tab-btn-editeur'));
    ouvrirModal('modal-creation-template');
}

function switchCreationMode(mode, btn) {
    modeCreation = mode;
    document.getElementById('mode-editeur').classList.toggle('hidden', mode !== 'editeur');
    document.getElementById('mode-upload').classList.toggle('hidden', mode !== 'upload');
    document.querySelectorAll('#modal-creation-template .tab-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
}

function insererSquelette(type) {
    const editor = document.getElementById('tmpl-contenu');
    if (type === 'minimal') {
        editor.value = `heat_template_version: 2018-08-31

description: Mon template personnalisé

parameters:
  key_name:
    type: string
    description: Nom de la paire de clés SSH
  image_name:
    type: string
    default: ubuntu-22.04
  flavor_name:
    type: string
    default: m1.small
  private_network:
    type: string
    default: private-network

resources:
  ma_vm:
    type: OS::Nova::Server
    properties:
      name: ma-vm
      key_name: { get_param: key_name }
      image: { get_param: image_name }
      flavor: { get_param: flavor_name }
      networks:
        - network: { get_param: private_network }

outputs:
  vm_id:
    description: ID de la VM créée
    value: { get_resource: ma_vm }
`;
    } else {
        editor.value = `heat_template_version: 2018-08-31

description: Template avec agent de métriques intégré

parameters:
  key_name:
    type: string
  image_name:
    type: string
    default: ubuntu-22.04
  flavor_name:
    type: string
    default: m1.small
  private_network:
    type: string
    default: private-network
  dashboard_ip:
    type: string
    description: IP du dashboard Heat Orchestration (pour les métriques)

resources:
  ma_vm:
    type: OS::Nova::Server
    properties:
      name: ma-vm
      key_name: { get_param: key_name }
      image: { get_param: image_name }
      flavor: { get_param: flavor_name }
      networks:
        - network: { get_param: private_network }
      user_data_format: RAW
      user_data:
        str_replace:
          template: |
            #!/bin/bash
            apt-get update -qq
            apt-get install -y python3-pip -qq
            pip3 install psutil requests -q
            cat > /usr/local/bin/metrics-agent.py << 'AGENT'
            import psutil, requests, time, socket
            SERVER_ID = socket.gethostname()
            DASHBOARD_URL = "http://DASHBOARD_IP:8080"
            while True:
                try:
                    net = psutil.net_io_counters()
                    requests.post(f"{DASHBOARD_URL}/api/metrics/alert", json={
                        "server_id": SERVER_ID,
                        "server_name": SERVER_ID,
                        "cpu": psutil.cpu_percent(interval=1),
                        "ram": psutil.virtual_memory().percent,
                        "disk": psutil.disk_usage('/').percent,
                        "network": {
                            "bytes_sent": net.bytes_sent,
                            "bytes_recv": net.bytes_recv
                        }
                    }, timeout=5)
                except Exception as e:
                    pass
                time.sleep(30)
            AGENT
            chmod +x /usr/local/bin/metrics-agent.py
            nohup python3 /usr/local/bin/metrics-agent.py > /var/log/metrics-agent.log 2>&1 &
          params:
            DASHBOARD_IP: { get_param: dashboard_ip }

outputs:
  vm_id:
    value: { get_resource: ma_vm }
`;
    }
}

function previewFichier(input) {
    const fichier = input.files[0];
    if (fichier) {
        document.getElementById('upload-label').textContent = `✓ ${fichier.name} (${Math.round(fichier.size/1024)} Ko)`;
    }
}

async function sauvegarderTemplate() {
    const btn = document.querySelector('#modal-creation-template .btn-primary');
    btn.disabled = true; btn.textContent = 'Création...';
    try {
        if (modeCreation === 'editeur') {
            const nom     = document.getElementById('tmpl-nom').value.trim();
            const desc    = document.getElementById('tmpl-desc').value.trim();
            const contenu = document.getElementById('tmpl-contenu').value.trim();
            if (!nom)     { afficherToast('Le nom est obligatoire', 'error'); return; }
            if (!contenu) { afficherToast('Le contenu YAML est obligatoire', 'error'); return; }

            await api.post('/api/templates', { name: nom, description: desc, content: contenu });

        } else {
            const fichier = document.getElementById('tmpl-fichier').files[0];
            if (!fichier) { afficherToast('Sélectionnez un fichier YAML', 'error'); return; }
            const nom  = document.getElementById('tmpl-upload-nom').value.trim() || fichier.name;
            const desc = document.getElementById('tmpl-upload-desc').value.trim();
            const fd   = new FormData();
            fd.append('file', fichier);
            fd.append('name', nom);
            fd.append('description', desc);
            await api.upload('/api/templates', fd);
        }

        fermerModal('modal-creation-template');
        afficherToast('Template créé avec succès', 'success');
        chargerTemplates();
    } catch (e) {
        afficherToast(`Erreur : ${e.message}`, 'error', 8000);
    } finally {
        btn.disabled = false; btn.textContent = 'Créer le template';
    }
}

// =====================================================================
// VISUALISATION
// =====================================================================

async function voirTemplate(id, nom) {
    document.getElementById('visu-titre').textContent = nom;
    document.getElementById('visu-contenu').textContent = 'Chargement...';
    ouvrirModal('modal-visualisation');
    try {
        const data = await api.get(`/api/templates/${id}`);
        document.getElementById('visu-contenu').textContent = data.template.content || 'Contenu vide';
    } catch (e) {
        document.getElementById('visu-contenu').textContent = `Erreur : ${e.message}`;
    }
}

// =====================================================================
// SUPPRESSION
// =====================================================================

function demanderSuppressionTemplate(id, nom) {
    templateASupprimer = { id, nom };
    document.getElementById('confirm-tmpl-nom').textContent = nom;
    ouvrirModal('modal-confirm-suppr-tmpl');
}

async function confirmerSuppressionTemplate() {
    if (!templateASupprimer) return;
    const btn = document.querySelector('#modal-confirm-suppr-tmpl .btn-danger');
    btn.disabled = true; btn.textContent = 'Suppression...';
    try {
        await api.delete(`/api/templates/${templateASupprimer.id}`);
        fermerModal('modal-confirm-suppr-tmpl');
        afficherToast(`Template '${templateASupprimer.nom}' supprimé`, 'success');
        templateASupprimer = null;
        chargerTemplates();
    } catch (e) {
        afficherToast(`Erreur : ${e.message}`, 'error');
    } finally {
        btn.disabled = false; btn.textContent = 'Supprimer';
    }
}
