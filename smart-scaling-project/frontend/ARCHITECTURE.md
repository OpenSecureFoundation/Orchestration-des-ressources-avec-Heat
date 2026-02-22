# Architecture - Smart Scaling Orchestrator Frontend

## Contrat API Strict (5 Endpoints Uniquement)

```
Phase A: Découverte
├── [1] GET /api/stacks
│   └── Récupère: [{id, name, status}]
└── [2] GET /api/stacks/<stack_id>/resources
    └── Récupère: [{name, type, physical_id, status, flavor?}]

Phase B: Monitoring
├── [3] POST /api/scaler/start
│   └── Body: {instance_id: string}
│   └── Réponse: {status: "monitoring_started"}
└── [4] GET /api/metrics/<instance_id>
    └── Polling 5 secondes
    └── Récupère: {current_load: number, history: [{time, val}]}

Phase C: Audit
└── [5] GET /api/scaler/audit
    └── Polling 10 secondes
    └── Récupère: [{timestamp, vm, action, from, to}]
```

## Workflow Utilisateur (Cinématique)

```
1. Page chargée
   └── GET /api/stacks
       └── Affiche liste Stacks dans StackExplorer

2. Utilisateur clique sur Stack
   └── GET /api/stacks/<id>/resources
       └── Affiche hiérarchie Stack > Réseaux > Instances

3. Utilisateur clique sur VM
   └── Affiche détails + bouton "Activer Auto-Scaling"

4. Utilisateur clique "Activer Auto-Scaling"
   └── POST /api/scaler/start {instance_id}
       └── setIsMonitoring(true)
           ├── Polling GET /api/metrics/<id> (5s)
           ├── Polling GET /api/scaler/audit (10s)
           └── Affiche graphique + audit trail
```

## Composants (3 Principaux)

```
app/page.tsx (Orchestration)
├── États: stacks, selectedStackId, resources, selectedResourceId, metrics, auditEvents, isMonitoring
├── useEffect[1]: Fetch stacks → GET /api/stacks
├── useEffect[2]: Fetch resources → GET /api/stacks/<id>/resources (si selectedStackId)
├── useEffect[3]: Polling metrics → GET /api/metrics/<id> (si isMonitoring, 5s)
├── useEffect[4]: Polling audit → GET /api/scaler/audit (si isMonitoring, 10s)
├── handleStartMonitoring(): POST /api/scaler/start
└── Render:
    ├── StackExplorer (gauche)
    └── MonitoringPanel (droite)

StackExplorer (Hiérarchie)
├── Props: stacks, resources, selectedStackId, selectedResourceId
├── Arborescence complète Stack > Ressources
├── Indicateurs statut (ACTIVE=vert, RESIZE=jaune, ERROR=rouge)
└── Callbacks: onSelectStack, onSelectResource

MonitoringPanel (Monitoring)
├── Props: resource, metrics, auditEvents, isMonitoring
├── Affiche détails ressource
├── Bouton "Activer Auto-Scaling"
├── Graphique CPU (Recharts) avec seuils 20% et 80%
├── Historique audit filtré par VM
└── Callback: onStartMonitoring
```

## Types TypeScript

```typescript
Stack {
  id: string
  name: string
  status: 'CREATE_COMPLETE' | 'CREATE_IN_PROGRESS' | 'DELETE_COMPLETE' | 'ERROR'
}

StackResource {
  name: string
  type: 'OS::Nova::Server' | 'OS::Neutron::Net' | string
  physical_id: string
  status: 'ACTIVE' | 'RESIZE' | 'VERIFY_RESIZE' | 'ERROR' | string
  flavor?: string  // Flavor m1.tiny, m1.small, etc.
}

MetricsResponse {
  current_load: number
  history: MetricPoint[]
}

MetricPoint {
  time: string
  val: number
}

AuditEvent {
  timestamp: string
  vm: string
  action: 'SCALE_UP' | 'SCALE_DOWN' | string
  from: string  // Ancienne flavor
  to: string    // Nouvelle flavor
}
```

## Flux de Données

### 1. Chargement initial
```
useEffect ([] dépendances)
  → fetch /api/stacks
  → setStacks([...])
  → StackExplorer rendu avec liste Stacks
```

### 2. Sélection Stack
```
StackExplorer
  → onClick(stack)
    → onSelectStack(stackId)
      → setSelectedStackId(stackId)
        → useEffect ([selectedStackId])
          → fetch /api/stacks/{id}/resources
          → setResources([...])
          → StackExplorer réaffiche avec ressources
```

### 3. Sélection Ressource
```
StackExplorer
  → onClick(resource)
    → onSelectResource(physicalId)
      → setSelectedResourceId(physicalId)
        → MonitoringPanel rendu
```

### 4. Activation Monitoring
```
MonitoringPanel
  → onClick("Activer Auto-Scaling")
    → handleStartMonitoring()
      → POST /api/scaler/start {instance_id}
      → setIsMonitoring(true)
        → useEffect ([isMonitoring, selectedResourceId])
          → interval = setInterval(() => {
              fetch /api/metrics/<id>
              setMetrics(...)
            }, 5000)
        → useEffect ([isMonitoring, selectedResourceId])
          → interval = setInterval(() => {
              fetch /api/scaler/audit
              setAuditEvents(...)
            }, 10000)
```

## Gestion des États

### Indicateurs Visuels

| Statut | Couleur | Interactivité |
|--------|---------|---------------|
| ACTIVE | Vert | Sélectionnable |
| RESIZE | Jaune | Spinner animation |
| VERIFY_RESIZE | Jaune (pulsing) | Spinner animation |
| ERROR | Rouge | Sélectionnable |

### Changement d'État OpenStack

```
VM en m1.tiny avec CPU > 80%
  ↓
Backend redimensionne → m1.small
  ↓
Statut: ACTIVE → RESIZE → VERIFY_RESIZE → ACTIVE
  ↓
Frontend détecte via polling des métriques
  ↓
Flavor changé de m1.tiny à m1.small
  ↓
Audit enregistré: SCALE_UP (m1.tiny → m1.small)
```

## Client API (lib/api.ts)

Centralise les 5 endpoints:

```typescript
api.fetchStacks()
  → GET /api/stacks
  → retourne Stack[]

api.fetchStackResources(stackId)
  → GET /api/stacks/{stackId}/resources
  → retourne StackResource[]

api.startScaling(instanceId)
  → POST /api/scaler/start
  → body: {instance_id: instanceId}
  → retourne {status: "monitoring_started"}

api.fetchMetrics(instanceId)
  → GET /api/metrics/{instanceId}
  → retourne MetricsResponse

api.fetchAuditTrail()
  → GET /api/scaler/audit
  → retourne AuditEvent[]
```

## Responsabilités Strictes

| Composant | Responsabilité | Endpoints |
|-----------|-----------------|-----------|
| `page.tsx` | Orchestration des états, appels API, polling | Tous |
| `StackExplorer` | Affichage hiérarchie, sélection ressource | Aucun |
| `MonitoringPanel` | Affichage métriques, graphique, audit, contrôle | Aucun (callback via page) |
| `Header` | Branding, titre | Aucun |
| `Sidebar` | Infos workflow, documentation | Aucun |

## Points Clés de la Spec

1. **Backend décide, Frontend affiche**: Aucune logique de scaling côté frontend
2. **5 endpoints UNIQUEMENT**: Pas d'autres appels API autorisés
3. **Hiérarchie explicite**: Stack → Ressources (pas de requête unique "tout")
4. **Polling strict**: 5s pour métriques, 10s pour audit
5. **État transparent**: RESIZE visible immédiatement grâce aux métriques
6. **Nettoyage**: clearInterval à chaque unmount

## Performance

- Polling stoppé si `isMonitoring === false`
- Nettoyage des intervalles à chaque unmount
- Pas de requêtes simultanées en doublon
- Cache implicite via les états React

---

**Contrat API = Contrat Frontend. Rien de plus, rien de moins.**
