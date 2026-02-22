# Smart Scaling Orchestrator - Frontend

Frontend React pour orchestration intelligent du scaling vertical des instances OpenStack. Interface minimaliste respectant un contrat API strict de 5 endpoints uniquement.

## Architecture: 3 Phases de Workflow

### Phase A: Déploiement et Découverte (Multi-VM/Réseau)
Lister les infrastructures (Stacks Heat) et afficher la hiérarchie: **Stack > Réseaux > Instances**

### Phase B: Configuration et Monitoring (Intelligence)
Sélectionner une VM et activer Auto-Scaling avec polling de métriques (5 secondes)

### Phase C: Scaling et Audit (Traçabilité SSI)
Détecter les changements d'état (RESIZE → VERIFY_RESIZE → ACTIVE) et consulter l'audit

## Les 5 Endpoints (Contrat Strict)

| # | Endpoint | Méthode | Usage | Phase |
|----|----------|---------|-------|-------|
| 1 | `/api/stacks` | GET | Lister l'infrastructure (Stacks Heat) | A |
| 2 | `/api/stacks/<stack_id>/resources` | GET | Détails Multi-VM et Réseaux | A |
| 3 | `/api/scaler/start` | POST | Activer Scaling Intelligent | B |
| 4 | `/api/metrics/<instance_id>` | GET | Flux de Métriques (polling 5s) | B/C |
| 5 | `/api/scaler/audit` | GET | Historique d'Audit SSI | C |

## Comportement Attendu

1. **Sélection Stack** → Charge ressources via `GET /api/stacks/<id>/resources`
2. **Sélection VM** → Affiche ses détails et statut
3. **Clic "Activer Auto-Scaling"** → `POST /api/scaler/start` avec `{"instance_id": "UUID"}`
4. **Polling actif** → `GET /api/metrics/<id>` toutes les 5 secondes
5. **Graphique CPU** → Affiche seuils (20%, 80%) et historique temps réel
6. **Audit Trail** → `GET /api/scaler/audit`, filtre par VM
7. **Changement d'état** → RESIZE → VERIFY_RESIZE → ACTIVE (spinner visuel)

## Installation & Démarrage

### Prérequis
- Node.js 20+ (ou 18+)
- pnpm (ou npm)

### Setup

```bash
# Installer les dépendances
pnpm install

# Configurer l'API
echo "NEXT_PUBLIC_API_URL=http://localhost:8765/api" > .env.local

# Démarrer le serveur dev
pnpm dev
```

Accès: http://localhost:3000

## Structure du Projet

```
app/
└── page.tsx                    # Page unique avec workflow complet

components/
├── stack-explorer.tsx          # Hiérarchie Stack > Réseaux > VMs
├── monitoring-panel.tsx        # Monitoring + Graphiques + Audit
├── header.tsx                  # En-tête
├── sidebar.tsx                 # Navigation
└── ui/                         # shadcn/ui components

lib/
├── types.ts                    # Types OpenStack Stack, StackResource, etc.
└── api.ts                      # Client API (5 endpoints uniquement)
```

## Configuration

### Variables d'Environnement

Créer `.env.local`:

```env
# URL du backend
NEXT_PUBLIC_API_URL=http://localhost:8765/api
```

## Design

- **Thème**: Sombre professionnel (fond #1a1a1a)
- **Couleur primaire**: Violet `oklch(0.52 0.15 260)`
- **Font**: Geist sans-serif (1 famille max)
- **Icons**: Lucide React
- **Graphiques**: Recharts

## Tech Stack

- React 19 (latest stable)
- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS 4
- shadcn/ui
- Recharts

## Build Production

```bash
pnpm build
pnpm start
```

## Support

Documentation détaillée: voir `ARCHITECTURE.md` et `QUICKSTART.md`

**Smart Scaling Orchestrator - Master 2 SSI**
