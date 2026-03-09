#!/bin/bash

echo "======================================"
echo "TEST COMPLET DU SYSTÈME DE SCALING"
echo "======================================"

# Récupérer les infos du serveur
echo -e "\n1. RÉCUPÉRATION DES INFOS SERVEUR:"
SERVER_ID=$(openstack server show heat-vm-01 -f value -c id 2>/dev/null)

if [ -z "$SERVER_ID" ]; then
    echo "ERREUR: Serveur heat-vm-01 non trouvé"
    echo "Liste des serveurs disponibles:"
    openstack server list
    exit 1
fi

echo "✓ Serveur trouvé: $SERVER_ID"

# Vérifier les flavors
echo -e "\n2. FLAVORS DISPONIBLES:"
openstack flavor list

# Créer la politique via API
echo -e "\n3. CRÉATION DE LA POLITIQUE DE SCALING:"
curl -s -X PUT http://localhost:8080/api/metrics/policies/$SERVER_ID \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: $(cat .session_token 2>/dev/null || echo '')" \
  -d '{
    "metric_type": "cpu",
    "scale_up_threshold": 70,
    "scale_down_threshold": 20,
    "cooldown_seconds": 60,
    "enabled": true
  }' | python3 -m json.tool

# Test 1: Alerte normale
echo -e "\n4. TEST 1 - ALERTE NORMALE (CPU 50%):"
curl -s -X POST http://localhost:8080/api/metrics/alert \
  -H "Content-Type: application/json" \
  -d "{
    \"source\": \"$SERVER_ID\",
    \"token\": \"heat-secret-token\",
    \"cpu\": 50.0,
    \"ram\": 60.0,
    \"disk\": 45.0,
    \"network_in\": 10.0,
    \"network_out\": 5.0,
    \"network_latency\": 20.0,
    \"timestamp\": $(date +%s)
  }" | python3 -m json.tool

sleep 2

# Test 2: Alerte SCALE UP
echo -e "\n5. TEST 2 - ALERTE SCALE UP (CPU 85%):"
curl -s -X POST http://localhost:8080/api/metrics/alert \
  -H "Content-Type: application/json" \
  -d "{
    \"source\": \"$SERVER_ID\",
    \"token\": \"heat-secret-token\",
    \"cpu\": 85.0,
    \"ram\": 60.0,
    \"disk\": 45.0,
    \"network_in\": 10.0,
    \"network_out\": 5.0,
    \"network_latency\": 20.0,
    \"timestamp\": $(date +%s)
  }" | python3 -m json.tool

echo -e "\n6. ATTENTE DU RESIZE (30 secondes)..."
for i in {1..6}; do
    echo -n "."
    sleep 5
done
echo ""

# Vérifier le statut
echo -e "\n7. VÉRIFICATION DU STATUT:"
openstack server show heat-vm-01 -c status -c flavor

echo -e "\n======================================"
echo "TEST TERMINÉ"
echo "======================================"
echo -e "\nConsultez le dashboard pour voir les graphiques en temps réel"
