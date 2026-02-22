# Test Manual des 5 Endpoints

Utilisez ces commandes curl pour tester chaque endpoint du backend.

## Prérequis

- Backend Flask tournant sur `http://localhost:8765`
- curl installé

## Endpoint 1: GET /api/stacks

```bash
curl -X GET http://localhost:8765/api/stacks \
  -H "Content-Type: application/json"
```

**Réponse attendue:**
```json
[
  {
    "id": "stack-1",
    "name": "Infra-SSI",
    "status": "CREATE_COMPLETE"
  }
]
```

**Validation:**
- Status HTTP: 200
- Type: Array
- Chaque Stack a: id, name, status

---

## Endpoint 2: GET /api/stacks/<stack_id>/resources

Remplacer `<stack_id>` par un ID de la réponse de l'endpoint 1.

```bash
curl -X GET http://localhost:8765/api/stacks/stack-1/resources \
  -H "Content-Type: application/json"
```

**Réponse attendue:**
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

**Validation:**
- Status HTTP: 200
- Type: Array
- Chaque Resource a: name, type, physical_id, status
- VMs (OS::Nova::Server) doivent avoir: flavor

---

## Endpoint 3: POST /api/scaler/start

Remplacer `<instance_id>` par un physical_id d'une VM (type OS::Nova::Server) de l'endpoint 2.

```bash
curl -X POST http://localhost:8765/api/scaler/start \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "uuid-vm-1"
  }'
```

**Réponse attendue:**
```json
{
  "status": "monitoring_started"
}
```

**Validation:**
- Status HTTP: 200 ou 201
- Type: Object
- Contient: status
- La valeur: "monitoring_started"

---

## Endpoint 4: GET /api/metrics/<instance_id>

Remplacer `<instance_id>` par le même que l'endpoint 3.
Appeler cet endpoint **toutes les 5 secondes** après avoir appelé l'endpoint 3.

```bash
curl -X GET http://localhost:8765/api/metrics/uuid-vm-1 \
  -H "Content-Type: application/json"
```

**Réponse attendue:**
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

**Validation:**
- Status HTTP: 200
- Type: Object
- Contient: current_load (number), history (array)
- Chaque élément de history a: time (string), val (number)
- current_load doit être entre 0 et 100
- history doit être en ordre chronologique

**Test du Seuil:**
- Attendre que current_load dépasse 80%
- Vérifier que le backend déclenche le scaling
- Statut de la VM doit passer de ACTIVE → RESIZE → VERIFY_RESIZE → ACTIVE
- Flavor doit changer (ex: m1.tiny → m1.small)
- Un événement doit apparaître dans l'endpoint 5

---

## Endpoint 5: GET /api/scaler/audit

Appeler cet endpoint **toutes les 10 secondes** après avoir appelé l'endpoint 3.

```bash
curl -X GET http://localhost:8765/api/scaler/audit \
  -H "Content-Type: application/json"
```

**Réponse attendue:**
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

**Validation:**
- Status HTTP: 200
- Type: Array
- Chaque AuditEvent a: timestamp, vm, action, from, to
- Tous les événements doivent être listés (pas de limite)
- Ordre chronologique (du plus ancien au plus récent)

**Test du Contenu:**
- Vérifier que les événements correspondent aux changements détectés
- Flavor "from" et "to" doivent correspondre aux changements réels
- Les timestamps doivent être croissants

---

## Test Complet (Scénario)

### 1. Récupérer les Stacks
```bash
curl -X GET http://localhost:8765/api/stacks
# Copier un stack_id
```

### 2. Récupérer les Ressources du Stack
```bash
curl -X GET http://localhost:8765/api/stacks/STACK_ID/resources
# Copier un instance_id (VM avec type OS::Nova::Server)
```

### 3. Démarrer le Monitoring
```bash
curl -X POST http://localhost:8765/api/scaler/start \
  -H "Content-Type: application/json" \
  -d '{"instance_id": "INSTANCE_ID"}'
```

### 4. Polling Métriques (5 appels, espacés de 5 secondes)
```bash
for i in {1..5}; do
  echo "=== Appel $i ==="
  curl -X GET http://localhost:8765/api/metrics/INSTANCE_ID
  sleep 5
done
```

### 5. Polling Audit (3 appels, espacés de 10 secondes)
```bash
for i in {1..3}; do
  echo "=== Appel $i ==="
  curl -X GET http://localhost:8765/api/scaler/audit
  sleep 10
done
```

---

## Checklist de Validation Backend

- [ ] Endpoint 1 retourne une liste de Stacks
- [ ] Endpoint 2 retourne les ressources (VMs + Réseaux)
- [ ] Endpoint 3 accepte instance_id et démarre le monitoring
- [ ] Endpoint 4 retourne current_load et history
- [ ] Endpoint 5 retourne un array d'AuditEvent
- [ ] Seuil 80% déclenche le scaling
- [ ] Flavor change après scaling (m1.tiny → m1.small, etc.)
- [ ] AuditEvent enregistre le changement
- [ ] Statut passe par RESIZE et VERIFY_RESIZE
- [ ] history contient des données en temps réel
- [ ] Polling retourne toujours les données actuelles

---

## Debugging

### Réponse 404
```
Le endpoint n'existe pas ou le format est incorrect.
Vérifier l'URL exacte et les paramètres.
```

### Réponse 500
```
Erreur serveur. Vérifier les logs du backend Flask.
Vérifier que OpenStack est accessible.
```

### JSON invalide
```
Vérifier que la réponse est du JSON valide.
Utiliser: curl ... | python -m json.tool
```

### Données manquantes
```
Vérifier que OpenStack a au moins:
- 1 Stack Heat
- 1+ Instances dans le Stack
- Métriques disponibles pour les instances
```

---

## Script Test Complet

```bash
#!/bin/bash

API_URL="http://localhost:8765/api"

echo "1. GET /api/stacks"
STACKS=$(curl -s $API_URL/stacks)
echo $STACKS | python -m json.tool
STACK_ID=$(echo $STACKS | python -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")

echo -e "\n2. GET /api/stacks/<id>/resources"
RESOURCES=$(curl -s $API_URL/stacks/$STACK_ID/resources)
echo $RESOURCES | python -m json.tool
INSTANCE_ID=$(echo $RESOURCES | python -c "import sys, json; data=json.load(sys.stdin); vm=[x for x in data if x['type']=='OS::Nova::Server'][0]; print(vm['physical_id'])")

echo -e "\n3. POST /api/scaler/start"
curl -s -X POST $API_URL/scaler/start \
  -H "Content-Type: application/json" \
  -d "{\"instance_id\": \"$INSTANCE_ID\"}" | python -m json.tool

echo -e "\n4. GET /api/metrics/<id>"
curl -s $API_URL/metrics/$INSTANCE_ID | python -m json.tool

echo -e "\n5. GET /api/scaler/audit"
curl -s $API_URL/scaler/audit | python -m json.tool

echo -e "\n✅ Test complet"
```

Sauvegarder comme `test.sh` et exécuter:
```bash
chmod +x test.sh
./test.sh
```

---

**Smart Scaling Orchestrator - Test Manual**
