# Heat Orchestration Platform

Plateforme web de gestion et d'orchestration de ressources OpenStack via Heat, avec monitoring temps reel et scaling automatique.

## Fonctionnalites

- Deploiement de stacks Heat via une interface web
- Templates modulaires imbriques (reseau + VM + security group)
- Agent de metriques auto-installe dans les VMs (CPU, RAM, Disque, Reseau)
- Monitoring temps reel avec graphiques Chart.js et WebSocket
- Scaling automatique par resize de VM selon les seuils configures
- Resize manuel des VMs
- Detection automatique de l'environnement OpenStack

## Prerequis

- OpenStack avec Keystone, Nova, Neutron, Heat, Glance
- Python 3.8+
- pip3
- Credentials admin OpenStack (`~/admin-openrc`)

## Installation rapide

```bash
git clone <repo>
cd Orchestration-des-ressources-avec-Heat
chmod +x deploy.sh
./deploy.sh
```

Le script `deploy.sh` :
1. Cree l'environnement virtuel Python
2. Installe les dependances
3. Detecte automatiquement l'environnement OpenStack
4. Genere le fichier `.env`
5. Verifie la connexion OpenStack

## Demarrage

```bash
source venv/bin/activate
python3 run.py
```

L'interface est disponible sur `http://<IP-controller>:8080`

## Configuration manuelle (.env)

Si la detection automatique echoue, editez le fichier `.env` :

```ini
OS_AUTH_URL=http://controller:5000/v3
OS_USERNAME=admin
OS_PASSWORD=admin123
OS_PROJECT_NAME=admin
PUBLIC_NETWORK_NAME=public-network
DASHBOARD_IP=192.168.44.134
DASHBOARD_PORT=8080
```

## Structure des fichiers

```
Orchestration-des-ressources-avec-Heat/
├── backend/              # Serveur Flask
│   ├── config.py         # Configuration dynamique
│   ├── models/           # Modeles SQLite
│   ├── services/         # Logique metier OpenStack
│   └── routes/           # Routes API REST
├── frontend/             # Interface web
│   ├── templates/        # Pages HTML
│   └── static/           # CSS + JS
├── templates_storage/
│   └── builtin/          # Templates Heat fournis
├── scripts/              # Scripts utilitaires
├── deploy.sh             # Installation automatique
├── run.py                # Point d'entree
└── .env                  # Configuration (a creer)
```

## Utilisation

### 1. Creer une stack

1. Ouvrir l'onglet **Templates** et verifier que les templates builtin sont charges
2. Aller dans **Stacks** > **Nouvelle Stack**
3. Choisir le template "Stack Complete"
4. Renseigner les parametres (cle SSH, image, flavor)
5. Cliquer sur **Creer la stack**

La stack deploiera automatiquement :
- Un reseau prive avec subnet (10.10.10.0/24)
- Un routeur connecte au reseau public
- Un security group (SSH, HTTP, ICMP)
- Une VM Ubuntu 22.04 avec IP flottante
- L'agent de metriques installe automatiquement

### 2. Configurer le scaling

1. Aller dans **Monitoring**
2. Selectionner une VM
3. Configurer les seuils (ex: CPU > 80% = scale up)
4. Cliquer sur **Activer**

Le scaling execute un resize de flavor :
- Scale Up : m1.small -> m1.medium -> m1.large
- Scale Down : m1.large -> m1.medium -> m1.small

### 3. Prérequis cle SSH

Avant de creer une stack, creez une paire de cles SSH :

```bash
openstack keypair create heat-keypair > heat-keypair.pem
chmod 600 heat-keypair.pem
```

## Depannage

**Erreur "controller" non resolvable**

Ajoutez l'entree dans `/etc/hosts` :
```
192.168.44.134  controller
```

**Les metriques ne remontent pas**

Verifiez que le port 8080 est accessible depuis les VMs :
```bash
openstack security group rule list
```

Verifiez les logs de l'agent dans la VM :
```bash
ssh ubuntu@<ip-flottante> -i heat-keypair.pem
journalctl -u metrics-agent -f
```

**Erreur de connexion OpenStack**

Testez manuellement :
```bash
source venv/bin/activate
python3 scripts/test_openstack.py
```

## Logs

Les logs de l'application sont dans `logs/orchestration.log`.

Pour suivre en temps reel :
```bash
tail -f logs/orchestration.log
```
