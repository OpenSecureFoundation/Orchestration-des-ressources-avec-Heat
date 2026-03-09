<<<<<<< HEAD
# Orchestration des ressources avec Heat
Projet d'orchestration des ressources avec OpenStack Heat

# Objectifs:

• Concevoir des templates Heat complexes pour déployer des architectures multi-VM et multi-réseaux en une seule commande

• Ajouter des modules personnalisés pour gérer le scaling automatique basé sur la charge
=======
# Orchestration des Ressources avec OpenStack Heat

Projet d'orchestration avancée avec OpenStack Heat - Scaling vertical automatique basé sur les métriques

## 📋 Table des matières

- [Description](#description)
- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Structure du projet](#structure-du-projet)
- [Technologies utilisées](#technologies-utilisées)
- [Documentation](#documentation)
- [Auteurs](#auteurs)
- [Superviseur](#superviseur)

---

## 📖 Description

Ce projet implémente une solution complète d'orchestration cloud avec OpenStack Heat, permettant le déploiement automatique d'infrastructures complexes et le scaling vertical automatique des ressources basé sur des métriques en temps réel.

### Objectifs du projet

- Déployer des architectures multi-VM et multi-réseaux via des templates Heat modulaires
- Implémenter un système de scaling vertical automatique basé sur les métriques réelles (CPU, RAM, Disque, Réseau)
- Fournir un dashboard web pour le monitoring temps réel et la gestion des ressources
- Garantir la sécurité via l'authentification des sources de métriques

### Cas d'utilisation

**CU1 - Déployer et Mettre à Jour une Architecture Modulaire**
- Import de templates depuis Git
- Upload de fichiers YAML locaux
- Création de templates via éditeur intégré
- Déploiement de stacks complètes

**CU2 - Configurer une Politique de Scaling**
- Choix de la métrique à surveiller (CPU, RAM, Disque, etc.)
- Configuration des seuils de déclenchement
- Périodes de cooldown personnalisables

**CU3 - Intégrer un Système de Métriques Externe**
- Agent Python déployé automatiquement dans les VMs
- Collecte de métriques toutes les 30 secondes
- Envoi sécurisé via token d'authentification

**CU4 - Exécution du Scaling Automatique**
- Analyse des métriques en temps réel
- Décision automatique de scaling (up/down)
- Resize vertical via Nova API
- Historique des événements

---

## ✨ Fonctionnalités

### Gestion des Templates

- **Import depuis Git** : Cloner des dépôts Git et importer tous les templates YAML
- **Upload de fichiers** : Drag & drop de fichiers locaux
- **Éditeur intégré** : Créer et modifier des templates avec coloration syntaxique YAML
- **Validation** : Vérification automatique de la syntaxe et de la structure Heat
- **Templates builtin** : 4 templates pré-configurés (main_stack, network, vm, autoscaling)

### Déploiement de Stacks

- **Création de stacks** : Déployer des infrastructures complètes en un clic
- **Paramètres dynamiques** : Interface pour remplir les paramètres du template
- **Suivi en temps réel** : Monitoring du statut de déploiement
- **Visualisation des ressources** : Liste détaillée des ressources créées
- **Outputs** : Affichage des outputs de la stack (IPs, URLs, etc.)
- **Mise à jour** : Modifier une stack existante
- **Suppression** : Supprimer proprement les ressources

### Gestion des VMs

- **Liste dynamique** : Toutes les VMs avec statut, flavor, IPs
- **Actions rapides** : Start, Stop, Reboot (soft/hard)
- **Resize manuel** : Changer de flavor manuellement
- **Détails complets** : Informations réseau, métadonnées, etc.
- **Filtres** : Rechercher par nom, filtrer par statut

### Monitoring Temps Réel

- **Métriques multiples** :
  - CPU (utilisation processeur en %)
  - RAM (utilisation mémoire en %)
  - Disque (utilisation espace en %)
  - Réseau entrant (Mbps)
  - Réseau sortant (Mbps)
  - Latence réseau (ms)

- **Sélection dynamique** : Choisir les métriques à afficher
- **Graphiques interactifs** : Chart.js avec historique de 40 points
- **WebSocket** : Mise à jour toutes les 5 secondes sans recharger
- **Multi-serveurs** : Surveillance simultanée de plusieurs VMs

### Scaling Automatique

- **Choix de la métrique** : CPU, RAM, Disque, Réseau, Latence
- **Seuils personnalisables** : Scale up (50-100%), Scale down (0-50%)
- **Cooldown** : Période d'attente entre deux scaling (60-600s)
- **Flavors supportés** : m1.small → m1.medium → m1.large
- **Historique** : Journal de tous les événements de scaling
- **Sécurité** : Validation des alertes par token + anti-replay

### Sécurité

- **Authentification** : Login/password avec sessions
- **Anti-brute force** : Max 5 tentatives, verrouillage 5 minutes
- **Validation des alertes** : Token secret + timestamp < 60s
- **HTTPS ready** : Configuration pour production
- **Rôles utilisateurs** : Admin vs User

---

## 🏗️ Architecture

### Architecture Globale
```
┌─────────────────────────────────────────────────────────┐
│                    UTILISATEUR                          │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │   NAVIGATEUR WEB      │
         │   (Dashboard)         │
         └───────────┬───────────┘
                     │ HTTP/WebSocket
         ┌───────────▼───────────┐
         │   BACKEND FLASK       │
         │   - API REST          │
         │   - WebSocket         │
         │   - Base SQLite       │
         └───────────┬───────────┘
                     │ API Calls
         ┌───────────▼───────────┐
         │   OPENSTACK           │
         │   - Heat Engine       │
         │   - Nova (VMs)        │
         │   - Neutron (Réseau)  │
         │   - Keystone (Auth)   │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │   VMs DÉPLOYÉES       │
         │   - Agent Métriques   │
         │   - Application       │
         └───────────────────────┘
```

### Flux de Scaling Automatique
```
1. VM (Agent Python)
   │
   ├─ Collecte métriques (psutil)
   │  - CPU, RAM, Disque, Réseau, Latence
   │
   └─ Envoie POST /api/metrics/alert
      │
      ▼
2. Backend (Validator)
   │
   ├─ Vérifie token secret
   ├─ Vérifie timestamp < 60s
   ├─ Vérifie plages (0-100%)
   │
   └─ Si valide → continue
      │
      ▼
3. Backend (Metrics Service)
   │
   ├─ Sauvegarde métriques en base
   ├─ Compare avec seuils politique
   ├─ Vérifie cooldown
   │
   └─ Décision : scale_up / scale_down / none
      │
      ▼
4. Backend (Heat Client)
   │
   ├─ Appelle Nova API resize
   ├─ m1.small → m1.medium (scale up)
   │  OU m1.medium → m1.small (scale down)
   │
   └─ Log événement en base
      │
      ▼
5. WebSocket
   │
   └─ Émet mise à jour vers dashboard
      │
      ▼
6. Dashboard
   │
   └─ Affiche nouveau flavor + graphiques
```

### Templates Heat Imbriqués
```
main_stack.yaml (Template racine)
├── network_template.yaml
│   ├── Réseau privé
│   ├── Subnet + DHCP
│   ├── Routeur
│   └── Security Groups
│
├── vm_template.yaml
│   ├── Port réseau
│   ├── Instance Nova
│   ├── IP flottante
│   └── User data (agent métriques)
│
└── autoscaling_template.yaml
    └── Configuration scaling
```

---

## 🔧 Prérequis

### Système d'exploitation

- **Ubuntu 22.04** ou supérieur
- **4 GB RAM** minimum (8 GB recommandé)
- **20 GB** espace disque

### OpenStack

L'application nécessite une installation OpenStack fonctionnelle avec :

- **Keystone** (authentification)
- **Heat** (orchestration)
- **Nova** (compute)
  - Nova API
  - Nova Scheduler
  - Nova Conductor
  - **Nova Compute** (OBLIGATOIRE - hypervisor)
- **Neutron** (réseau)
  - DHCP Agent
  - L3 Agent
  - Metadata Agent
- **Glance** (images)

### Ressources OpenStack

Avant de lancer l'application, créer :

- **3 Flavors** :
  - m1.small (1 vCPU, 2 GB RAM)
  - m1.medium (2 vCPU, 4 GB RAM)
  - m1.large (4 vCPU, 8 GB RAM)

- **1 Image** :
  - Ubuntu 22.04 ou CirrOS

- **1 Keypair SSH** :
  - Nom : `heat-keypair`

- **1 Réseau externe** :
  - Nom : `public`
  - Pool d'IPs flottantes configuré

### Python

- **Python 3.10** ou supérieur
- **pip** et **venv**

### Vérification de l'installation OpenStack
```bash
# Charger les credentials
source ~/admin-openrc

# Vérifier les services
openstack service list
# Heat, Nova, Neutron, Keystone, Glance doivent être "enabled"

# Vérifier les hypervisors (CRITIQUE)
openstack hypervisor list
# Doit afficher au moins 1 hypervisor

# Vérifier les flavors
openstack flavor list

# Vérifier les images
openstack image list

# Vérifier les réseaux
openstack network list
```

---

## 📦 Installation

### 1. Cloner le projet
```bash
cd ~/Downloads
git clone https://github.com/OpenSecureFoundation/Orchestration-des-ressources-avec-Heat.git
cd Orchestration-des-ressources-avec-Heat
```

### 2. Créer l'environnement virtuel Python
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

Cela installe :
- Flask + Flask-SocketIO
- OpenStack clients (heat, nova, neutron, keystone)
- GitPython (pour import templates depuis Git)
- PyYAML (validation templates)
- Et toutes les dépendances

---

## ⚙️ Configuration

### 1. Créer le fichier .env

**Option A : Script interactif (recommandé)**
```bash
python3 scripts/create_env.py
```

Répondre aux questions (appuyer sur Entrée pour garder les valeurs par défaut).

**Option B : Manuellement**
```bash
cp .env.example .env
nano .env
```

Modifier au minimum :
```env
OS_PASSWORD=votre_mot_de_passe_openstack
FLASK_SECRET_KEY=votre-cle-secrete-aleatoire
SECRET_TOKEN=votre-token-pour-agents-vm
```

### 2. Initialiser la base de données
```bash
python3 scripts/setup_database.py
```

Cela crée :
- La base SQLite dans `database/orchestration.db`
- Toutes les tables nécessaires
- Charge les 4 templates builtin

### 3. Créer l'utilisateur administrateur
```bash
python3 scripts/create_admin.py
```

Créer un compte :
- Username : `admin`
- Password : `admin123` (ou autre)

---

## 🚀 Utilisation

### Démarrer l'application
```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer le serveur
python3 run.py
```

L'application démarre sur **http://localhost:8080**

### Accéder au dashboard

Ouvrir un navigateur :
```
http://localhost:8080
```

ou
```
http://VOTRE_IP:8080
```

**Connexion :**
- Username : `admin`
- Password : `admin123`

### Workflow typique

#### 1. Déployer une infrastructure

1. Aller dans **Stacks** → **Nouvelle Stack**
2. Nom : `ma-stack`
3. Template : `main_stack`
4. Paramètres :
   - Key : `heat-keypair`
   - Image : `cirros` (ou votre image)
   - Flavor : `m1.small`
   - Network externe : `public`
5. Cliquer **Créer**
6. Attendre 3-5 minutes (statut → CREATE_COMPLETE)

#### 2. Surveiller les métriques

1. Aller dans **Monitoring**
2. Sélectionner le serveur : `heat-vm-01`
3. Cocher les métriques à surveiller
4. Les graphiques s'affichent en temps réel

#### 3. Configurer le scaling automatique

1. Dans la page Monitoring (serveur sélectionné)
2. Section "Politique de Scaling"
3. Métrique : `cpu`
4. Seuil Scale Up : `80%`
5. Seuil Scale Down : `20%`
6. Activer : ✓
7. Cliquer **Sauvegarder**

#### 4. Tester le scaling

**Simuler une charge CPU élevée :**
```bash
# Depuis une autre machine (ou terminal)
curl -X POST http://VOTRE_IP:8080/api/metrics/alert \
  -H "Content-Type: application/json" \
  -d '{
    "source": "heat-vm-01",
    "token": "heat-secret-token",
    "cpu": 85.0,
    "ram": 60.0,
    "disk": 45.0,
    "timestamp": '$(date +%s)'
  }'
```

Observer dans le dashboard :
- L'alerte est traitée
- Action : scale_up
- Flavor passe de m1.small → m1.medium
- Événement visible dans l'historique

### Arrêter l'application

Dans le terminal :
```bash
Ctrl+C
deactivate
```

---

## 📁 Structure du projet
```
Orchestration-des-ressources-avec-Heat/
│
├── backend/                        # Backend Flask
│   ├── app.py                     # Application principale
│   ├── config.py                  # Configuration
│   ├── models/                    # Modèles de données
│   │   ├── database.py           # Connexion SQLite
│   │   ├── user.py               # Utilisateurs
│   │   ├── template.py           # Templates
│   │   ├── stack.py              # Stacks
│   │   └── metrics.py            # Métriques
│   ├── services/                  # Logique métier
│   │   ├── auth_service.py       # Authentification
│   │   ├── openstack_service.py  # API OpenStack
│   │   ├── template_service.py   # Gestion templates
│   │   ├── stack_service.py      # Gestion stacks
│   │   ├── vm_service.py         # Gestion VMs
│   │   ├── metrics_service.py    # Métriques & scaling
│   │   └── git_service.py        # Import Git
│   ├── routes/                    # Routes API
│   │   ├── auth_routes.py
│   │   ├── template_routes.py
│   │   ├── stack_routes.py
│   │   ├── vm_routes.py
│   │   ├── metrics_routes.py
│   │   └── dashboard_routes.py
│   ├── websocket/                 # WebSocket temps réel
│   │   └── handlers.py
│   └── utils/                     # Utilitaires
│       ├── decorators.py
│       ├── validators.py
│       └── helpers.py
│
├── frontend/                       # Frontend HTML/CSS/JS
│   ├── templates/                 # Templates Jinja2
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── templates_manager.html
│   │   ├── stacks_manager.html
│   │   └── vms_manager.html
│   └── static/                    # Ressources statiques
│       ├── css/
│       │   ├── main.css
│       │   ├── dashboard.css
│       │   ├── templates.css
│       │   └── components.css
│       └── js/
│           ├── utils.js
│           ├── auth.js
│           ├── dashboard.js
│           ├── templates.js
│           ├── stacks.js
│           ├── vms.js
│           ├── metrics.js
│           └── websocket.js
│
├── templates_storage/              # Stockage templates Heat
│   ├── builtin/                   # Templates intégrés
│   │   ├── main_stack.yaml
│   │   ├── network_template.yaml
│   │   ├── vm_template.yaml
│   │   └── autoscaling_template.yaml
│   └── user/                      # Templates utilisateur
│
├── database/                       # Base de données
│   ├── schema.sql                 # Schéma SQL
│   └── orchestration.db           # BDD (généré)
│
├── scripts/                        # Scripts utilitaires
│   ├── setup_database.py          # Initialiser BDD
│   ├── create_admin.py            # Créer admin
│   ├── create_env.py              # Créer .env
│   └── seed_data.py               # Données de test
│
├── logs/                           # Logs application
│   └── app.log
│
├── tests/                          # Tests (optionnel)
│   ├── test_services.py
│   └── test_routes.py
│
├── .env                            # Configuration (NE PAS COMMIT)
├── .env.example                    # Exemple configuration
├── .gitignore                      # Fichiers à ignorer
├── requirements.txt                # Dépendances Python
├── README.md                       # Ce fichier
└── run.py                          # Point d'entrée
```

---

## 🛠️ Technologies utilisées

### Backend

- **Flask 3.0** - Framework web Python
- **Flask-SocketIO 5.3** - WebSocket temps réel
- **SQLite** - Base de données
- **python-openstackclient** - API OpenStack
- **python-heatclient** - API Heat
- **python-novaclient** - API Nova
- **GitPython** - Clone dépôts Git
- **PyYAML** - Validation YAML

### Frontend

- **HTML5 / CSS3** - Interface web
- **JavaScript ES6** - Logique client
- **Chart.js 4.4** - Graphiques métriques
- **Socket.IO 4.5** - WebSocket client
- **CodeMirror 5.65** - Éditeur YAML

### OpenStack

- **Heat** - Orchestration
- **Nova** - Compute
- **Neutron** - Réseau
- **Keystone** - Authentification
- **Glance** - Images

---

## 📚 Documentation

### Cahiers du projet

- **Cahier de Charge** : `Cahier_De_Charge_GROUPE_1_Heat_orchestration.pdf`
- **Cahier d'Analyse** : `Cahier_D_Analyse_GROUPE_1_Heat_orchestration.pdf`
- **Cahier de Conception** : `Cahier_Conception_GROUPE_1_Heat_orchestration.pdf`

### API Endpoints

#### Authentification
- `POST /api/auth/login` - Connexion
- `POST /api/auth/logout` - Déconnexion
- `GET /api/auth/me` - Utilisateur actuel

#### Templates
- `GET /api/templates` - Lister templates
- `POST /api/templates` - Créer template
- `PUT /api/templates/:id` - Modifier template
- `DELETE /api/templates/:id` - Supprimer template
- `POST /api/templates/import-git` - Import depuis Git
- `POST /api/templates/upload` - Upload fichier

#### Stacks
- `GET /api/stacks` - Lister stacks
- `POST /api/stacks` - Créer stack
- `GET /api/stacks/:id/status` - Statut stack
- `GET /api/stacks/:id/resources` - Ressources stack
- `DELETE /api/stacks/:id` - Supprimer stack

#### VMs
- `GET /api/vms` - Lister VMs
- `GET /api/vms/:id` - Détails VM
- `POST /api/vms/:id/start` - Démarrer VM
- `POST /api/vms/:id/stop` - Arrêter VM
- `POST /api/vms/:id/resize` - Resize VM

#### Métriques
- `POST /api/metrics/alert` - Recevoir alerte
- `GET /api/metrics/available` - Métriques disponibles
- `GET /api/metrics/history/:server_id` - Historique
- `PUT /api/metrics/policies/:server_id` - Config scaling

---

## 👥 Auteurs

**GROUPE 1**

- **Ngouo Franck Leonel**
- **MOUDIO ABEGA Laurent Stéphane**

Étudiants en Génie Logiciel
Année académique 2025-2026

---

## 👨‍🏫 Superviseur

**M. NGUIMBUS Emmanuel**

Enseignant-Chercheur

---

## 📝 Licence

Projet académique - Tous droits réservés

---

## 🐛 Problèmes connus et solutions

### "No valid host was found"

**Cause :** Nova Compute n'est pas démarré

**Solution :**
```bash
sudo systemctl status nova-compute
sudo systemctl start nova-compute
```

### Port 8080 déjà utilisé

**Solution :**
```bash
sudo lsof -ti:8080 | xargs kill -9
```

### Métriques ne s'affichent pas

**Vérifier :**
1. L'agent tourne dans la VM : `systemctl status metrics-agent`
2. Le SECRET_TOKEN est correct dans .env
3. Le dashboard est accessible depuis la VM

---

## 📞 Support

Pour toute question ou problème :

1. Vérifier les logs : `tail -f logs/app.log`
2. Consulter la documentation OpenStack
3. Contacter les auteurs

---

## 🎓 Contexte académique

Ce projet a été réalisé dans le cadre du cours d'Orchestration Cloud avec OpenStack. Il démontre la maîtrise de :

- Architecture modulaire avec templates imbriqués
- Scaling automatique basé sur métriques réelles
- Développement full-stack (Python/Flask + HTML/CSS/JS)
- Intégration avec APIs OpenStack
- Sécurité (authentification, validation)
- WebSocket pour temps réel
- Déploiement et monitoring d'infrastructures cloud

---

**Version :** 1.0.0
**Date :** Mars 2026
**Statut :** Production Ready
>>>>>>> feature/complete-rewrite
