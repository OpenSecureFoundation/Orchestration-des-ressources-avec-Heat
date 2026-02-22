# Quick Start - Smart Scaling Orchestrator Frontend

## Installation (5 minutes)

### 1. Prérequis
- Node.js 20+ (ou 18+)
- pnpm (inclus si vous avez npm)

### 2. Installer les dépendances
```bash
cd frontend
pnpm install
```

### 3. Configurer l'API
```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8765/api" > .env.local
```

### 4. Démarrer le serveur
```bash
pnpm dev
```

### 5. Accéder au frontend
Ouvrir: http://localhost:3000

---

## Workflow d'Utilisation

### Étape 1: Lister les Stacks
Dès le chargement, le frontend appelle **`GET /api/stacks`** et affiche la liste des infrastructures.

### Étape 2: Sélectionner une Infrastructure
Cliquer sur un Stack → Le frontend appelle **`GET /api/stacks/<id>/resources`** et affiche:
- Réseaux (OS::Neutron::Net)
- Instances/VMs (OS::Nova::Server)

### Étape 3: Sélectionner une VM
Cliquer sur une VM → Affiche ses détails (nom, ID, statut, flavor).

### Étape 4: Activer Auto-Scaling
Cliquer sur **"Activer Auto-Scaling"**:
- Appel **`POST /api/scaler/start`** avec `{instance_id: "UUID"}`
- Frontend commence le polling:
  - **`GET /api/metrics/<id>`** toutes les 5 secondes
  - **`GET /api/scaler/audit`** toutes les 10 secondes
- Graphique CPU apparaît avec historique temps réel

### Étape 5: Voir le Scaling en Action
Si CPU dépasse 80%:
- Backend redimensionne la VM (m1.tiny → m1.small)
- Statut change: ACTIVE → RESIZE → VERIFY_RESIZE → ACTIVE
- Nouveau flavor visible dans l'interface
- Événement enregistré dans l'Audit Trail

---

## API Endpoints Utilisés (5 Uniquement)

### [1] GET /api/stacks
Récupère la liste des infrastructures Heat

```bash
curl http://localhost:8765/api/stacks
```

Réponse attendue:
```json
[
  {"id": "stack-1", "name": "Infra-SSI", "status": "CREATE_COMPLETE"},
  {"id": "stack-2", "name": "App-E-Commerce", "status": "CREATE_COMPLETE"}
]
```

### [2] GET /api/stacks/<stack_id>/resources
Récupère les ressources (VMs + Réseaux) d'un Stack

```bash
curl http://localhost:8765/api/stacks/stack-1/resources
```

Réponse attendue:
```json
[
  {
    "name": "VM_WEB",
    "type": "OS::Nova::Server",
    "physical_id": "uuid-vm-1",
    "status": "ACTIVE",
    "flavor": "m1.tiny"
  },
  {
    "name": "Net_Front",
    "type": "OS::Neutron::Net",
    "physical_id": "uuid-net-1",
    "status": "ACTIVE"
  }
]
```

### [3] POST /api/scaler/start
Activé le monitoring/scaling d'une instance

```bash
curl -X POST http://localhost:8765/api/scaler/start \
  -H "Content-Type: application/json" \
  -d '{"instance_id": "uuid-vm-1"}'
```

Réponse attendue:
```json
{"status": "monitoring_started"}
```

### [4] GET /api/metrics/<instance_id>
Récupère les métriques CPU (polling 5s)

```bash
curl http://localhost:8765/api/metrics/uuid-vm-1
```

Réponse attendue:
```json
{
  "current_load": 65.5,
  "history": [
    {"time": "10:00:00", "val": 42},
    {"time": "10:00:05", "val": 48},
    {"time": "10:00:10", "val": 65.5}
  ]
}
```

### [5] GET /api/scaler/audit
Récupère l'historique de scaling (polling 10s)

```bash
curl http://localhost:8765/api/scaler/audit
```

Réponse attendue:
```json
[
  {
    "timestamp": "2025-10-27 14:05:30",
    "vm": "VM_WEB",
    "action": "SCALE_UP",
    "from": "m1.tiny",
    "to": "m1.small"
  }
]
```

---

## Structure Simplifiée

```
app/
└── page.tsx                    # UNE SEULE PAGE avec workflow complet

components/
├── stack-explorer.tsx          # Hiérarchie Stack > Réseaux > VMs
├── monitoring-panel.tsx        # Graphique CPU + Audit Trail
├── header.tsx
└── sidebar.tsx

lib/
├── types.ts                    # Types OpenStack Stack, StackResource, etc.
└── api.ts                      # Client des 5 endpoints
```

---

## Troubleshooting

### Erreur: "Failed to fetch stacks"
1. Vérifier `NEXT_PUBLIC_API_URL` dans `.env.local`
2. Vérifier que le backend Flask tourne sur port 8765
3. Tester: `curl http://localhost:8765/api/stacks`

### Erreur: "Cannot find module 'next'"
1. Relancer `pnpm install`
2. Supprimer `node_modules` et `.next`
3. `pnpm install` à nouveau

### Les métriques ne se mettent pas à jour
1. Vérifier que `isMonitoring === true` (bouton actif)
2. Ouvrir la console du navigateur (F12)
3. Vérifier les appels réseau (onglet Network)
4. Vérifier que le backend retourne du JSON valide

---

## Variables d'Environnement

Fichier `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8765/api
```

---

## Build Production

```bash
pnpm build
pnpm start
```

Accès: http://localhost:3000

---

## Support

- Voir `ARCHITECTURE.md` pour la documentation technique complète
- Voir `README.md` pour une vue d'ensemble
- Vérifier les logs du navigateur (F12 → Console)
- Vérifier les logs du backend Flask

---

**Smart Scaling Orchestrator - Master 2 SSI**
