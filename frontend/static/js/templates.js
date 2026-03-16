/**
 * Page Templates — gestion complète des templates Heat.
 * CU1.1 : Créer template simple
 * CU1.2/1.3 : Composants réutilisables
 * CU1.4 : Validation template
 * CU1.5 : Bibliothèque organisée
 */

let modeCreation = 'editeur';
let composantsDisponibles = [];

document.addEventListener('DOMContentLoaded', () => {
    chargerTemplates();
    chargerComposants();
});

// =====================================================================
// CHARGEMENT TEMPLATES
// =====================================================================

async function chargerTemplates() {
    const c = document.getElementById('liste-templates');
    c.innerHTML = '<div class="loading">Chargement...</div>';
    try {
        const data = await api.get('/api/templates');
        const templates = data.templates || [];
        if (!templates.length) {
            c.innerHTML = '<div class="empty-state">Aucun template. Créez votre premier template.</div>';
            return;
        }
        // Séparer builtin et user
        const builtin = templates.filter(t => t.category === 'builtin');
        const user    = templates.filter(t => t.category !== 'builtin');

        let html = '';
        if (builtin.length) {
            html += `<h4 style="margin:0 0 0.75rem;color:#64748b;font-size:0.85rem;text-transform:uppercase;letter-spacing:0.05em;">
                Intégrés (${builtin.length})</h4>`;
            html += '<div class="table-container"><table><thead><tr><th>Nom</th><th>Description</th><th>Catégorie</th><th>Actions</th></tr></thead><tbody>';
            html += builtin.map(t => ligneTemplate(t)).join('');
            html += '</tbody></table></div>';
        }
        if (user.length) {
            html += `<h4 style="margin:1.5rem 0 0.75rem;color:#64748b;font-size:0.85rem;text-transform:uppercase;letter-spacing:0.05em;">
                Mes templates (${user.length})</h4>`;
            html += '<div class="table-container"><table><thead><tr><th>Nom</th><th>Description</th><th>Catégorie</th><th>Actions</th></tr></thead><tbody>';
            html += user.map(t => ligneTemplate(t)).join('');
            html += '</tbody></table></div>';
        }
        c.innerHTML = html;
    } catch (e) {
        c.innerHTML = `<div class="alert alert-danger">Erreur : ${e.message}</div>`;
    }
}

function ligneTemplate(t) {
    const isUser = t.category !== 'builtin';
    return `<tr>
        <td><strong>${t.name}</strong></td>
        <td style="font-size:0.85rem;color:#64748b;">${t.description || '--'}</td>
        <td><span class="badge ${t.category === 'builtin' ? 'badge-secondary' : 'badge-info'}">${t.category}</span></td>
        <td>
            <div class="actions-cell">
                <button class="btn btn-sm btn-outline" onclick="voirTemplate(${t.id})">Voir</button>
                <button class="btn btn-sm btn-outline" onclick="validerTemplate(${t.id})">✅ Valider</button>
                ${isUser ? `<button class="btn btn-sm btn-danger" onclick="supprimerTemplate(${t.id}, '${t.name}')">Supprimer</button>` : ''}
            </div>
        </td>
    </tr>`;
}

// =====================================================================
// COMPOSANTS RÉUTILISABLES (CU1.2 / CU1.3)
// =====================================================================

async function chargerComposants() {
    const c = document.getElementById('liste-composants');
    const sel = document.getElementById('select-composant');
    try {
        const data = await api.get('/api/templates/components');
        composantsDisponibles = data.components || [];
        if (!composantsDisponibles.length) {
            c.innerHTML = '<div class="empty-state">Aucun composant disponible</div>';
            return;
        }
        c.innerHTML = `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem;">
            ${composantsDisponibles.map(comp => `
                <div class="card" style="margin:0;border:1px solid #e2e8f0;">
                    <div class="card-body" style="padding:1rem;">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.5rem;">
                            <strong style="font-size:0.95rem;">📄 ${comp.name}</strong>
                            <button class="btn btn-sm btn-outline" onclick="utiliserComposant('${comp.filename}')">
                                Utiliser ↗
                            </button>
                        </div>
                        <p style="font-size:0.82rem;color:#64748b;margin:0 0 0.5rem;">${comp.description}</p>
                        <div style="font-size:0.78rem;color:#94a3b8;">
                            Paramètres : ${comp.parameters.join(', ') || 'aucun'}
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>`;
        // Peupler le select dans l'éditeur
        if (sel) {
            sel.innerHTML = '<option value="">Choisir un composant...</option>' +
                composantsDisponibles.map(c => `<option value="${c.filename}">${c.name}</option>`).join('');
        }
    } catch (e) {
        c.innerHTML = `<div class="alert alert-danger">Erreur composants : ${e.message}</div>`;
    }
}

function utiliserComposant(filename) {
    ouvrirModalCreation();
    // Pré-sélectionner le composant dans le select
    const sel = document.getElementById('select-composant');
    if (sel) sel.value = filename;
    afficherToast(`Composant "${filename}" sélectionné — cliquez sur Insérer`, 'info', 4000);
}

function insererComposantDansEditeur() {
    const sel = document.getElementById('select-composant');
    if (!sel || !sel.value) { afficherToast('Sélectionnez un composant', 'error'); return; }
    const comp = composantsDisponibles.find(c => c.filename === sel.value);
    if (!comp) return;
    const textarea = document.getElementById('tmpl-contenu');
    const snippet = `\n  # --- Composant: ${comp.name} ---\n  ${comp.filename.replace('.yaml','')}:\n    type: ${comp.filename}\n    properties:\n      vm_name: ma-vm\n`;
    textarea.value += snippet;
    afficherToast(`Composant "${comp.name}" inséré dans l'éditeur`, 'success');
}

// =====================================================================
// CRÉATION / UPLOAD
// =====================================================================

function ouvrirModalCreation() {
    chargerComposants();
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
    const textarea = document.getElementById('tmpl-contenu');
    if (type === 'minimal') {
        textarea.value = `heat_template_version: 2018-08-31
description: "Mon template Heat"

parameters:
  image_name:
    type: string
    default: ubuntu-22.04
  flavor_name:
    type: string
    default: m1.small
  key_name:
    type: string
    default: heat-keypair
  network_name:
    type: string
    default: private-network

resources:
  ma_vm:
    type: OS::Nova::Server
    properties:
      name: ma-vm
      image: { get_param: image_name }
      flavor: { get_param: flavor_name }
      key_name: { get_param: key_name }
      networks:
        - network: { get_param: network_name }

outputs:
  vm_ip:
    description: IP de la VM
    value: { get_attr: [ma_vm, first_address] }
`;
    } else {
        textarea.value = `heat_template_version: 2018-08-31
description: "Template avec agent de monitoring"

parameters:
  image_name:
    type: string
    default: ubuntu-22.04
  flavor_name:
    type: string
    default: m1.small
  key_name:
    type: string
    default: heat-keypair
  network_name:
    type: string
    default: private-network
  public_network:
    type: string
    default: public-network
  dashboard_ip:
    type: string
    description: IP du dashboard Heat Orchestration

resources:
  security_group:
    type: OS::Neutron::SecurityGroup
    properties:
      name: heat-sg
      rules:
        - protocol: tcp
          port_range_min: 22
          port_range_max: 22
          remote_ip_prefix: 0.0.0.0/0
        - protocol: icmp
          remote_ip_prefix: 0.0.0.0/0

  server:
    type: OS::Nova::Server
    properties:
      name: heat-vm
      image: { get_param: image_name }
      flavor: { get_param: flavor_name }
      key_name: { get_param: key_name }
      networks:
        - network: { get_param: network_name }
      security_groups:
        - { get_resource: security_group }
      user_data_format: RAW
      user_data:
        str_replace:
          template: |
            #!/bin/bash
            apt-get update -qq
            apt-get install -y python3 python3-pip
            pip3 install psutil requests
            cat > /usr/local/bin/metrics-agent.py << 'AGENT'
            #!/usr/bin/env python3
            import psutil, requests, socket, time, logging
            logging.basicConfig(filename='/var/log/metrics-agent.log', level=logging.INFO,
                format='%(asctime)s [%(levelname)s] %(message)s')
            DASHBOARD_URL = "http://__DASHBOARD__:8080"
            HOSTNAME = socket.gethostname()
            while True:
                try:
                    data = {"server_id": HOSTNAME, "server_name": HOSTNAME,
                            "cpu": psutil.cpu_percent(interval=1),
                            "ram": psutil.virtual_memory().percent,
                            "disk": psutil.disk_usage('/').percent,
                            "network": {"bytes_sent": 0, "bytes_recv": 0}}
                    requests.post(f"{DASHBOARD_URL}/api/metrics/alert", json=data, timeout=10)
                    logging.info("Métriques envoyées")
                except Exception as e:
                    logging.error(f"Erreur: {e}")
                time.sleep(30)
            AGENT
            chmod +x /usr/local/bin/metrics-agent.py
            cat > /etc/systemd/system/metrics-agent.service << SVC
            [Unit]
            Description=Heat Metrics Agent
            After=network.target
            [Service]
            ExecStart=/usr/bin/python3 /usr/local/bin/metrics-agent.py
            Restart=always
            [Install]
            WantedBy=multi-user.target
            SVC
            systemctl enable metrics-agent && systemctl start metrics-agent
          params:
            __DASHBOARD__: { get_param: dashboard_ip }

  floating_ip:
    type: OS::Neutron::FloatingIP
    properties:
      floating_network: { get_param: public_network }

  association:
    type: OS::Neutron::FloatingIPAssociation
    properties:
      floatingip_id: { get_resource: floating_ip }
      port_id: { get_attr: [server, addresses, { get_param: network_name }, 0, port] }

outputs:
  server_ip_private:
    value: { get_attr: [server, first_address] }
  server_ip_public:
    value: { get_attr: [floating_ip, floating_ip_address] }
`;
    }
    afficherToast('Squelette inséré', 'success');
}

// =====================================================================
// VALIDATION (CU1.4)
// =====================================================================

async function validerYAML() {
    const contenu = document.getElementById('tmpl-contenu').value.trim();
    const resultDiv = document.getElementById('validation-result');
    if (!contenu) { afficherToast('Entrez du contenu YAML', 'error'); return; }
    resultDiv.innerHTML = '<div class="loading">Validation en cours...</div>';
    try {
        const data = await api.post('/api/stacks/validate', { content: contenu });
        afficherRapportValidation(data, resultDiv);
    } catch (e) {
        resultDiv.innerHTML = `<div class="alert alert-danger">Erreur : ${e.message}</div>`;
    }
}

async function validerTemplate(templateId) {
    const rapport = document.getElementById('rapport-validation') || document.createElement('div');
    rapport.innerHTML = '<div class="loading">Validation en cours...</div>';
    ouvrirModal('modal-validation');
    try {
        const data = await api.post('/api/stacks/validate', { template_id: templateId });
        afficherRapportValidation(data, document.getElementById('rapport-validation'));
    } catch (e) {
        document.getElementById('rapport-validation').innerHTML =
            `<div class="alert alert-danger">Erreur : ${e.message}</div>`;
    }
}

function afficherRapportValidation(data, container) {
    if (!data.success && data.error) {
        container.innerHTML = `<div class="alert alert-danger">Erreur serveur : ${data.error}</div>`;
        return;
    }
    const valid = data.valid;
    const errors = data.errors || [];
    const warnings = data.warnings || [];
    const params = data.parameters || {};
    const nbRes = data.resources_count || 0;

    let html = `<div class="alert ${valid ? 'alert-success' : 'alert-danger'}" style="margin-bottom:1rem;">
        ${valid ? '✅ Template valide' : '❌ Template invalide'}
        ${nbRes ? ` — ${nbRes} ressource(s) définie(s)` : ''}
    </div>`;

    if (errors.length) {
        html += `<div style="margin-bottom:1rem;">
            <strong style="color:#dc2626;">Erreurs (${errors.length})</strong>
            <ul style="margin-top:0.5rem;">${errors.map(e => `<li style="color:#dc2626;font-size:0.9rem;">${e}</li>`).join('')}</ul>
        </div>`;
    }
    if (warnings.length) {
        html += `<div style="margin-bottom:1rem;">
            <strong style="color:#d97706;">Avertissements (${warnings.length})</strong>
            <ul style="margin-top:0.5rem;">${warnings.map(w => `<li style="color:#d97706;font-size:0.9rem;">${w}</li>`).join('')}</ul>
        </div>`;
    }
    if (Object.keys(params).length) {
        html += `<div>
            <strong>Paramètres du template</strong>
            <table style="width:100%;margin-top:0.5rem;font-size:0.85rem;">
                <thead><tr><th>Nom</th><th>Type</th><th>Obligatoire</th><th>Défaut</th><th>Description</th></tr></thead>
                <tbody>${Object.entries(params).map(([k,v]) => `<tr>
                    <td><code>${k}</code></td>
                    <td>${v.type}</td>
                    <td>${v.required ? '<span style="color:#dc2626;">Oui</span>' : 'Non'}</td>
                    <td><code>${v.default !== null && v.default !== undefined ? v.default : '--'}</code></td>
                    <td style="color:#64748b;">${v.description || '--'}</td>
                </tr>`).join('')}</tbody>
            </table>
        </div>`;
    }
    container.innerHTML = html;
}

// =====================================================================
// SAUVEGARDE
// =====================================================================

async function sauvegarderTemplate() {
    const btn = document.getElementById('btn-sauvegarder');
    btn.disabled = true; btn.textContent = 'Sauvegarde...';
    try {
        if (modeCreation === 'editeur') {
            const nom = document.getElementById('tmpl-nom').value.trim();
            const desc = document.getElementById('tmpl-desc').value.trim();
            const contenu = document.getElementById('tmpl-contenu').value.trim();
            if (!nom) { afficherToast('Le nom est obligatoire', 'error'); return; }
            if (!contenu) { afficherToast('Le contenu YAML est obligatoire', 'error'); return; }
            await api.post('/api/templates', { name: nom, description: desc, content: contenu });
        } else {
            const fichier = document.getElementById('upload-fichier').files[0];
            if (!fichier) { afficherToast('Sélectionnez un fichier', 'error'); return; }
            const formData = new FormData();
            formData.append('file', fichier);
            const nom = document.getElementById('upload-nom').value.trim();
            if (nom) formData.append('name', nom);
            const resp = await fetch('/api/templates', { method: 'POST', body: formData });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error || 'Erreur upload');
        }
        fermerModal('modal-creation-template');
        afficherToast('Template sauvegardé avec succès', 'success');
        chargerTemplates();
    } catch (e) {
        afficherToast(`Erreur : ${e.message}`, 'error', 8000);
    } finally {
        btn.disabled = false; btn.textContent = 'Sauvegarder';
    }
}

// =====================================================================
// VOIR / SUPPRIMER
// =====================================================================

async function voirTemplate(templateId) {
    try {
        const data = await api.get(`/api/templates/${templateId}`);
        const t = data.template;
        const contenu = t.content || '(vide)';
        const win = window.open('', '_blank');
        win.document.write(`<pre style="font-family:monospace;padding:1rem;white-space:pre-wrap;">${contenu}</pre>`);
    } catch (e) {
        afficherToast(`Erreur : ${e.message}`, 'error');
    }
}

async function supprimerTemplate(templateId, nom) {
    if (!confirm(`Supprimer le template "${nom}" ?`)) return;
    try {
        await api.delete(`/api/templates/${templateId}`);
        afficherToast(`Template "${nom}" supprimé`, 'success');
        chargerTemplates();
    } catch (e) {
        afficherToast(`Erreur : ${e.message}`, 'error');
    }
}
