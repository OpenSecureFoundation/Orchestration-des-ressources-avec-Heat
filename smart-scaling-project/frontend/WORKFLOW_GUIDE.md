# Guide Complet du Workflow - Smart Scaling Orchestrator

## Navigation et Exécution Complète

### Phase A: Déploiement & Découverte

**Étape 1: Ouvrir l'application**
- La page charge automatiquement
- Appel API: `GET /api/stacks`
- **Résultat attendu**: Liste des Stacks dans le panneau gauche

**Étape 2: Sélectionner un Stack**
- Cliquez sur un Stack dans le panneau gauche (ex: "mon_test")
- Le chevron tourne vers le bas
- Appel API: `GET /api/stacks/<stack_id>/resources`
- **Résultat attendu**: Le Stack se déploie et affiche:
  - **Réseaux** avec icône réseau (gris)
  - **VMs** avec icône serveur (VIOLET avec étiquette "VM")

### Phase B: Configuration & Monitoring

**Étape 3: Sélectionner une VM**
- Dans la liste déroulée des ressources, cliquez sur une **VM** (avec le libellé "VM" en violet)
- La VM se surbrille en bleu avec une bordure gauche violette
- **Important**: Ne sélectionnez PAS les réseaux (gris), seulement les VMs
- **Résultat attendu**: Le panneau droit s'affiche avec:
  - Nom, ID, Type, Statut
  - **BOUTON BLEU**: "Activer Auto-Scaling"

**Étape 4: Activer Auto-Scaling**
- Cliquez sur le bouton bleu "Activer Auto-Scaling"
- Appel API: `POST /api/scaler/start { instance_id }`
- Le bouton devient gris et affiche "Surveillance active"
- **Résultat attendu**: Le polling commence

### Phase C: Scaling & Audit

**Étape 5: Surveiller le graphique**
- Après activation, un **graphique CPU** apparaît
- **Polling automatique**: `GET /api/metrics/<instance_id>` toutes les 5 secondes
- Vous verrez:
  - Valeur CPU actuelle (grande, en violet)
  - Courbe temps réel
  - **Indicateurs de seuil**: 
    - Vert (< 20%) = Normal
    - Jaune (20-80%) = Attention
    - Rouge (> 80%) = Scale-up

**Étape 6: Observer le scaling**
- Si CPU dépasse 80%, le backend redimensionne la VM
- Le statut passe: ACTIVE → RESIZE → VERIFY_RESIZE → ACTIVE
- L'indicateur de statut change de couleur
- **Polling automatique**: `GET /api/scaler/audit` toutes les 10 secondes

**Étape 7: Consulter l'audit trail**
- Une section "Historique de Scaling" apparaît
- Affiche tous les événements pour cette VM:
  - `SCALE_UP: m1.tiny → m1.small`
  - Timestamp exact
  - Filtré uniquement pour la VM sélectionnée

---

## Éléments Interactifs et Leur Rôle

### Panneau Gauche (Stack Explorer)

| Élément | Type | Action | Résultat |
|---------|------|--------|----------|
| **Stack (avec chevron)** | Bouton + Chevron | Clic | Déploie/replie les ressources |
| **Réseau (icône réseau)** | Non-VM | Clic | Affiche info réseau (pas de bouton scaling) |
| **VM (icône serveur + "VM")** | VM | Clic | Affiche le panneau monitoring avec bouton bleu |

### Panneau Droit (Monitoring Panel)

| Élément | Apparition | Action | Résultat |
|---------|-----------|--------|----------|
| **Infos ressource** | Toujours | - | Affiche nom, ID, type, statut |
| **Message non-VM** | Si ressource non-VM | - | Explique qu'il faut sélectionner une VM |
| **Bouton bleu** | Si VM sélectionnée | Clic | Démarre le polling et graphique |
| **Graphique CPU** | Après activation | - | Affiche courbe temps réel |
| **Audit Trail** | Après activation + événements | - | Affiche historique de scaling |

### Sidebar Gauche (Workflow Info)

| Section | Rôle |
|---------|------|
| **Phase A, B, C** | **Informatif uniquement** (non cliquable) |
| **API ENDPOINTS** | Reference des 5 endpoints utilisés |

---

## Troubleshooting: Pourquoi le bouton n'apparaît pas?

1. **Vous avez sélectionné un réseau** (icône réseau gris)
   - Solution: Cliquez sur une **VM** (icône serveur + "VM" en violet)

2. **Vous avez sélectionné une autre ressource** (type non-VM)
   - Solution: Un message s'affiche expliquant cela. Cherchez une VM.

3. **Le graphique n'apparaît pas après clic**
   - Solution: Attendez 5 secondes (premier polling). Vérifiez les logs du navigateur.

4. **Aucun Stack n'apparaît**
   - Solution: Vérifiez que `NEXT_PUBLIC_API_URL` est correct dans `.env.local`
   - Testez: `curl http://localhost:8765/api/stacks`

---

## Format des Données Attendues

### Phase A: Stacks et Resources

```bash
# GET /api/stacks
[
  {"id": "stack-1", "name": "mon_test", "status": "CREATE_COMPLETE"}
]

# GET /api/stacks/stack-1/resources
[
  {"name": "Net_Front", "type": "OS::Neutron::Net", "physical_id": "net-1", "status": "ACTIVE"},
  {"name": "VM_Web", "type": "OS::Nova::Server", "physical_id": "vm-1", "status": "ACTIVE", "flavor": "m1.tiny"}
]
```

### Phase B: Monitoring

```bash
# POST /api/scaler/start
Body: {"instance_id": "vm-1"}
Response: {"status": "monitoring_started"}

# GET /api/metrics/vm-1
{
  "current_load": 75.5,
  "history": [
    {"time": "14:00:00", "val": 42},
    {"time": "14:00:05", "val": 65},
    {"time": "14:00:10", "val": 75.5}
  ]
}
```

### Phase C: Audit

```bash
# GET /api/scaler/audit
[
  {
    "timestamp": "2025-10-27 14:05:30",
    "vm": "VM_Web",
    "action": "SCALE_UP",
    "from": "m1.tiny",
    "to": "m1.small"
  }
]
```

---

## Checklist Complète du Workflow

- [ ] Phase A: Stack visible dans la liste
- [ ] Phase A: Chevron se tourne en cliquant
- [ ] Phase A: Ressources s'affichent (réseaux + VMs)
- [ ] Phase A: VMs marquées avec icône violet + "VM"
- [ ] Phase B: Sélection VM affiche le panneau droit
- [ ] Phase B: Bouton bleu "Activer Auto-Scaling" visible
- [ ] Phase B: Bouton cliquable et passe au gris
- [ ] Phase C: Graphique CPU apparaît
- [ ] Phase C: Courbe se met à jour (5s)
- [ ] Phase C: Audit trail affiche événements
- [ ] Phase C: Changement de statut visible (RESIZE)

**Tout le workflow est 100% wired et exécutable.**

