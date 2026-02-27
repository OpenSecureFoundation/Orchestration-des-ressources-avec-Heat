# Spécification Finale du Frontend - Smart Scaling Orchestrator

## Vision

Frontend minimaliste et précis qui respecte **strictement** le cahier des charges:
- **5 endpoints uniquement** (pas un de plus, pas un de moins)
- **3 phases de workflow** (Découverte → Monitoring → Audit)
- **Aucune ambiguïté** dans la cinématique utilisateur
- **Backend décide, Frontend affiche**

---

## Les 5 Endpoints (Contrat Immuable)

### Phase A: Déploiement et Découverte

#### [1] `GET /api/stacks`
Lister l'infrastructure globale (Stacks Heat)

**Request:**
```
GET /api/stacks HTTP/1.1
Host: localhost:8765
```

**Response:**
```json
[
  {
    "id": "stack-uuid-1",
    "name": "Infra-SSI",
    "status": "CREATE_COMPLETE"
  },
  {
    "id": "stack-uuid-2",
    "name": "App-E-Commerce",
    "status": "CREATE_COMPLETE"
  }
]
```

#### [2] `GET /api/stacks/<stack_id>/resources`
Détails Multi-VM d'une infrastructure

**Request:**
```
GET /api/stacks/stack-uuid-1/resources HTTP/1.1
Host: localhost:8765
```

**Response:**
```json
[
  {
    "name": "VM_WEB",
    "type": "OS::Nova::Server",
    "physical_id": "instance-uuid-1",
    "status": "ACTIVE",
    "flavor": "m1.tiny"
  },
  {
    "name": "VM_DB",
    "type": "OS::Nova::Server",
    "physical_id": "instance-uuid-2",
    "status": "ACTIVE",
    "flavor": "m1.small"
  },
  {
    "name": "Net_Front",
    "type": "OS::Neutron::Net",
    "physical_id": "net-uuid-1",
    "status": "ACTIVE"
  },
  {
    "name": "Net_Back",
    "type": "OS::Neutron::Net",
    "physical_id": "net-uuid-2",
    "status": "ACTIVE"
  }
]
```

### Phase B: Configuration et Monitoring

#### [3] `POST /api/scaler/start`
Activer le Scaling Intelligent

**Request:**
```
POST /api/scaler/start HTTP/1.1
Host: localhost:8765
Content-Type: application/json

{
  "instance_id": "instance-uuid-1"
}
```

**Response:**
```json
{
  "status": "monitoring_started"
}
```

#### [4] `GET /api/metrics/<instance_id>`
Flux de Métriques (Graphiques) - **Polling 5 secondes**

**Request:**
```
GET /api/metrics/instance-uuid-1 HTTP/1.1
Host: localhost:8765
```

**Response:**
```json
{
  "current_load": 65.5,
  "history": [
    {
      "time": "14:05:00",
      "val": 42.0
    },
    {
      "time": "14:05:05",
      "val": 48.5
    },
    {
      "time": "14:05:10",
      "val": 52.3
    },
    {
      "time": "14:05:15",
      "val": 65.5
    }
  ]
}
```

**Seuils visuels sur le graphique:**
- `current_load < 20%` → Zone verte (Normal)
- `20% ≤ current_load < 80%` → Zone jaune (Attention)
- `current_load ≥ 80%` → Zone rouge (Scale-up déclenché)

### Phase C: Scaling et Audit

#### [5] `GET /api/scaler/audit`
Historique d'Audit (SSI) - **Polling 10 secondes**

**Request:**
```
GET /api/scaler/audit HTTP/1.1
Host: localhost:8765
```

**Response:**
```json
[
  {
    "timestamp": "2025-10-27 14:05:30",
    "vm": "VM_WEB",
    "action": "SCALE_UP",
    "from": "m1.tiny",
    "to": "m1.small"
  },
  {
    "timestamp": "2025-10-27 14:10:45",
    "vm": "VM_WEB",
    "action": "SCALE_UP",
    "from": "m1.small",
    "to": "m1.medium"
  }
]
```

---

## Workflow Utilisateur (Cinématique)

### Étape 1: Chargement initial
```
Frontend charge
  ↓
GET /api/stacks
  ↓
Affiche liste Stacks dans StackExplorer
  ↓
Utilisateur voit: "Infra-SSI", "App-E-Commerce"
```

### Étape 2: Sélection d'un Stack
```
Utilisateur clique sur "Infra-SSI"
  ↓
Frontend appelle GET /api/stacks/stack-uuid-1/resources
  ↓
Affiche hiérarchie dans StackExplorer:
  Stack: Infra-SSI
  ├── VM_WEB (OS::Nova::Server, ACTIVE, m1.tiny)
  ├── VM_DB (OS::Nova::Server, ACTIVE, m1.small)
  ├── Net_Front (OS::Neutron::Net, ACTIVE)
  └── Net_Back (OS::Neutron::Net, ACTIVE)
```

### Étape 3: Sélection d'une VM
```
Utilisateur clique sur "VM_WEB"
  ↓
MonitoringPanel affiche:
  - Nom: VM_WEB
  - ID: instance-uuid-1
  - Type: OS::Nova::Server
  - Statut: ACTIVE
  - Flavor: m1.tiny
  - Bouton: "Activer Auto-Scaling"
```

### Étape 4: Activation Auto-Scaling
```
Utilisateur clique "Activer Auto-Scaling"
  ↓
Frontend envoie POST /api/scaler/start
  {instance_id: "instance-uuid-1"}
  ↓
Backend répond: {status: "monitoring_started"}
  ↓
Frontend:
  ├── setIsMonitoring(true)
  ├── Démarre polling GET /api/metrics/instance-uuid-1 (5s)
  ├── Démarre polling GET /api/scaler/audit (10s)
  └── Affiche graphique Recharts + audit trail
```

### Étape 5: Monitoring actif
```
Toutes les 5 secondes:
  GET /api/metrics/instance-uuid-1
    ↓
  current_load = 65.5
    ↓
  Graphique se met à jour
  Zone jaune visible (20-80%)

Toutes les 10 secondes:
  GET /api/scaler/audit
    ↓
  Audit trail se met à jour
    ↓
  Utilisateur voit l'historique
```

### Étape 6: Scaling automatique
```
CPU dépasse 80%
  ↓ (décidé par le backend)
Backend redimensionne: m1.tiny → m1.small
  ↓
Statut change: ACTIVE → RESIZE → VERIFY_RESIZE → ACTIVE
  ↓
Frontend détecte via polling (5s):
  ├── Statut change dans ressource
  ├── Flavor change: m1.tiny → m1.small
  └── MonitoringPanel se met à jour
  ↓
Utilisateur voit:
  ├── Spinner animation pendant RESIZE
  ├── Flavor changé
  ├── Audit trail: SCALE_UP (m1.tiny → m1.small)
```

---

## Composants Frontend

### `app/page.tsx` (Orchestration)
**Responsabilités:**
- Gérer tous les états (stacks, selectedStackId, resources, metrics, auditEvents, isMonitoring)
- Orchestrer les appels API aux 5 endpoints
- Gérer les polling (5s pour métriques, 10s pour audit)
- Passer les données et callbacks aux composants enfants

**État:**
```typescript
const [stacks, setStacks] = useState<Stack[]>([]);
const [selectedStackId, setSelectedStackId] = useState<string | null>(null);
const [resources, setResources] = useState<StackResource[]>([]);
const [selectedResourceId, setSelectedResourceId] = useState<string | null>(null);
const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
const [isMonitoring, setIsMonitoring] = useState(false);
```

**useEffect:**
```typescript
useEffect(() => fetchStacks()) // Au chargement
useEffect(() => fetchResources()) // Si selectedStackId change
useEffect(() => pollingMetrics()) // Si isMonitoring ou selectedResourceId change
useEffect(() => pollingAudit()) // Si isMonitoring change
```

### `components/stack-explorer.tsx` (Hiérarchie)
**Responsabilités:**
- Afficher l'arborescence: Stack > Ressources
- Distinguer VMs (Server icon) et Réseaux (Network icon)
- Afficher indicateurs visuels de statut (vert/jaune/rouge/pulsing)
- Gérer l'expansion/collapse des Stacks
- Appeler callbacks onSelectStack et onSelectResource

### `components/monitoring-panel.tsx` (Monitoring)
**Responsabilités:**
- Afficher détails de la ressource sélectionnée
- Afficher bouton "Activer Auto-Scaling"
- Afficher graphique Recharts avec seuils (20%, 80%)
- Afficher historique audit filtré par VM
- Appeler callback onStartMonitoring

### `components/header.tsx`
Affiche logo et titre

### `components/sidebar.tsx`
Affiche:
- Branding (logo, nom)
- Workflow (Phase A, B, C)
- Les 5 endpoints
- Crédits

---

## Types TypeScript (lib/types.ts)

```typescript
interface Stack {
  id: string
  name: string
  status: 'CREATE_COMPLETE' | 'CREATE_IN_PROGRESS' | 'DELETE_COMPLETE' | 'ERROR'
}

interface StackResource {
  name: string
  type: 'OS::Nova::Server' | 'OS::Neutron::Net' | string
  physical_id: string
  status: 'ACTIVE' | 'RESIZE' | 'VERIFY_RESIZE' | 'ERROR' | string
  flavor?: string  // Flavor uniquement pour les VMs
}

interface MetricsResponse {
  current_load: number
  history: MetricPoint[]
}

interface MetricPoint {
  time: string
  val: number
}

interface AuditEvent {
  timestamp: string
  vm: string
  action: 'SCALE_UP' | 'SCALE_DOWN' | string
  from: string
  to: string
}
```

---

## Règles Strictes

1. **Backend décide, Frontend affiche**: Aucune logique de scaling côté frontend
2. **5 endpoints UNIQUEMENT**: Pas d'autres appels API autorisés
3. **Hiérarchie explicite**: Stack → Ressources (pas de requête unique "tout")
4. **Polling strict**: 5s pour métriques, 10s pour audit
5. **État transparent**: RESIZE visible immédiatement grâce aux métriques
6. **Nettoyage**: clearInterval à chaque unmount
7. **Pas de cache serveur**: Les données viennent toujours du backend

---

## Validation Backend

Pour que le frontend fonctionne, le backend DOIT:

1. Implémenter exactement ces 5 endpoints
2. Respecter les formats de réponse
3. Implémenter le polling côté backend (metrics, audit)
4. Gérer les changements d'état (RESIZE → VERIFY_RESIZE → ACTIVE)
5. Enregistrer les événements dans l'audit trail

**Aucun compromis sur ce contrat.**

---

## Déploiement

```bash
pnpm install
pnpm build
pnpm start
```

---

**Version 1.0.0 | Master 2 SSI | Février 2026**
