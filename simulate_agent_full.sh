#!/bin/bash

echo "=== Simulation Agent Métriques (Scale UP et DOWN) ==="
SERVER_ID=$(openstack server show heat-vm-01 -f value -c id)
echo "Serveur: $SERVER_ID"
echo "Cycle: 3 alertes HIGH (scale up) puis 3 alertes LOW (scale down)"
echo ""

CYCLE=0
while true; do
    CYCLE=$((CYCLE + 1))
    
    # Alterner entre charge haute et basse
    if [ $((CYCLE % 6)) -lt 3 ]; then
        # Charge HAUTE (scale up)
        CPU=$((RANDOM % 30 + 70))  # 70-100%
        MODE="HIGH"
    else
        # Charge BASSE (scale down)
        CPU=$((RANDOM % 15 + 5))   # 5-20%
        MODE="LOW"
    fi
    
    RAM=$((RANDOM % 30 + 40))
    DISK=$((RANDOM % 20 + 30))
    TIMESTAMP=$(date +%s)
    
    echo -n "[$(date +'%H:%M:%S')] $MODE CPU=${CPU}% RAM=${RAM}% → "
    
    RESPONSE=$(curl -s -X POST http://localhost:8080/api/metrics/alert \
      -H "Content-Type: application/json" \
      -d "{
        \"source\": \"$SERVER_ID\",
        \"token\": \"heat-secret-token\",
        \"cpu\": ${CPU}.0,
        \"ram\": ${RAM}.0,
        \"disk\": ${DISK}.0,
        \"network_in\": 10.0,
        \"network_out\": 5.0,
        \"network_latency\": 20.0,
        \"timestamp\": $TIMESTAMP
      }")
    
    ACTION=$(echo "$RESPONSE" | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('data',{}).get('action','error'))" 2>/dev/null || echo "error")
    
    echo "$ACTION"
    
    sleep 30
done
