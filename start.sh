#!/bin/bash
# Démarrage propre de Heat Orchestration Platform

cd "$(dirname "$0")"

echo "=== Heat Orchestration Platform ==="

# Charger les credentials OpenStack
source ~/admin-openrc 2>/dev/null && echo "✓ OpenStack credentials chargés" || echo "⚠ admin-openrc non trouvé"

# Activer le venv
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Environnement virtuel activé"
else
    echo "⚠ venv non trouvé, utilisez: python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

# Vérifier la BDD
if [ ! -f "database/orchestration.db" ]; then
    echo "ℹ Base de données inexistante, sera créée au démarrage"
fi

# Tuer les anciennes instances
pkill -f "python3 run.py" 2>/dev/null && echo "✓ Ancienne instance arrêtée" || true
sleep 1

# Démarrer
echo ""
echo "Démarrage sur http://192.168.44.134:8080"
echo "Ctrl+C pour arrêter"
echo ""
python3 run.py
