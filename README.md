# Orchestration des ressources avec Heat
Projet d'orchestration des ressources avec OpenStack Heat

# Objectifs:

• Concevoir des templates Heat complexes pour déployer des architectures multi-VM et multi-réseaux en une seule commande

• Ajouter des modules personnalisés pour gérer le scaling automatique basé sur la charge



## Description
Ce projet améliore l'orchestration des ressources cloud en utilisant
le service Heat d'OpenStack. Il propose :
- Des **templates HOT modulaires** pour déployer des topologies
  multi-VM et multi-réseaux
- Un **scaling vertical automatique** : augmentation/diminution des
  ressources (CPU, RAM) d'une VM via le changement de flavor
- Un **adaptateur de métriques** Python pour déclencher le scaling
- Un **dashboard web** pour monitorer en temps réel et configurer
  les politiques de scaling

##  Équipe
- Ngouo Franck Leonel
- MOUDIO ABEGA Laurent Stéphane

Supervisé par : M. NGUIMBUS Emmanuel

## Architecture du projet
```
Orchestration-des-ressources-avec-Heat/
├── templates/                   # Templates HOT (YAML)
│   ├── main_stack.yaml          # Template racine
│   ├── network_template.yaml    # Réseau, subnet, routeur
│   ├── vm_template.yaml         # VMs + agent métriques
│   └── autoscaling_template.yaml# Politiques scaling vertical
│
├── metrics_adapter/             # Adaptateur de métriques (Python)
│   ├── adapter.py               # Middleware principal + API REST
│   ├── validator.py             # Validation et sécurité
│   └── heat_client.py           # Communication avec Heat/Nova
│
├── api/                         # Couche API REST
│   ├── routes.py                # Endpoints pour le frontend
│   ├── auth.py                  # Authentification utilisateur
│   └── websocket.py             # Métriques temps réel
│
├── frontend/                    # Interface web
│   ├── index.html               # Page de connexion
│   ├── dashboard.html           # Tableau de bord principal
│   └── static/
│       ├── css/style.css        # Design de l'interface
│       └── js/
│           ├── dashboard.js     # Graphiques temps réel
│           ├── policies.js      # Gestion politiques scaling
│           └── templates.js     # Sélection/déploiement templates
│
├── scripts/
│   └── deploy.py                # Script de déploiement CLI
├── tests/
│   ├── test_adapter.py          # Tests adaptateur
│   └── test_api.py              # Tests API REST
├── requirements.txt
└── README.md
```

## Prérequis
- Python 3.8+
- OpenStack / DevStack installé et configuré
- Git
- Navigateur web moderne (Chrome, Firefox)

## Installation

### 1. Cloner le projet
```bash
git clone https://github.com/OpenSecureFoundation/Orchestration-des-ressources-avec-Heat.git
cd Orchestration-des-ressources-avec-Heat
```

### 2. Installer les dépendances Python
```bash
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement
Crée un fichier `.env` à la racine :
```
OS_AUTH_URL=http://votre-openstack:5000/v3
OS_USERNAME=admin
OS_PASSWORD=votre_mot_de_passe
OS_PROJECT_NAME=admin
SECRET_TOKEN=heat-secret-token
DASHBOARD_USER=admin
DASHBOARD_PASSWORD=admin123
```

## Utilisation

### Étape 1 — Déployer l'infrastructure
```bash
python scripts/deploy.py create
```

### Étape 2 — Lancer l'application complète
```bash
python metrics_adapter/adapter.py
```

### Étape 3 — Ouvrir le dashboard
Ouvre ton navigateur sur : **http://localhost:5000**

Connecte-toi avec les identifiants du fichier `.env`

##  Fonctionnalités du Dashboard
- Métriques CPU et RAM en temps réel (WebSocket)
-  Visualisation du flavor actuel et historique des resizes
-  Modification des seuils de scaling (Scale Up / Scale Down)
- Sélection et déploiement des templates Heat
- Journal des actions et événements

## Flux de scaling vertical
```
VM génère métriques (CPU > seuil)
        ↓
adapter.py reçoit l'alerte
        ↓
validator.py valide la source
        ↓
heat_client.py resize la VM
(m1.small → m1.medium → m1.large)
        ↓
OpenStack Nova applique le nouveau flavor
        ↓
Dashboard mis à jour en temps réel
```

## Tests
```bash
pytest tests/ -v
```

## Sécurité
- Authentification requise pour accéder au dashboard
- Token secret pour valider les alertes des VMs
- Communication HTTPS recommandée en production
- RBAC via OpenStack Keystone

##  Licence
Projet académique — GROUPE 1