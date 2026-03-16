#!/bin/bash
# ============================================================
# Script d'installation automatique
# Heat Orchestration Platform
# ============================================================

set -e

COULEUR_VERT='\033[0;32m'
COULEUR_ROUGE='\033[0;31m'
COULEUR_JAUNE='\033[1;33m'
COULEUR_RESET='\033[0m'

ok()   { echo -e "${COULEUR_VERT}[OK]${COULEUR_RESET} $1"; }
err()  { echo -e "${COULEUR_ROUGE}[ERREUR]${COULEUR_RESET} $1"; exit 1; }
info() { echo -e "${COULEUR_JAUNE}[INFO]${COULEUR_RESET} $1"; }

echo "============================================================"
echo "  Heat Orchestration Platform - Installation"
echo "============================================================"

# ---- Verification des prerequis ----
info "Verification des prerequis..."

python3 --version >/dev/null 2>&1 || err "Python 3 requis. Installez-le avec : sudo apt install python3"
pip3 --version >/dev/null 2>&1 || err "pip3 requis. Installez-le avec : sudo apt install python3-pip"
ok "Python 3 et pip3 disponibles"

# ---- Repertoire du projet ----
PROJET_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJET_DIR"
info "Repertoire du projet : $PROJET_DIR"

# ---- Environnement virtuel ----
info "Creation de l'environnement virtuel Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    ok "Environnement virtuel cree"
else
    ok "Environnement virtuel existant detecte"
fi

source venv/bin/activate

# ---- Installation des dependances ----
info "Installation des dependances Python..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
ok "Dependances installees"

# ---- Creation des repertoires ----
info "Creation des repertoires..."
mkdir -p database logs templates_storage/user
ok "Repertoires crees"

# ---- Generation du fichier .env ----
if [ ! -f ".env" ]; then
    info "Generation du fichier .env (detection automatique)..."
    python3 scripts/detect_environment.py
    ok "Fichier .env genere"
else
    ok "Fichier .env existant detecte (non ecrase)"
fi

# ---- Test de connexion OpenStack ----
info "Test de connexion OpenStack..."
if python3 scripts/test_openstack.py; then
    ok "Connexion OpenStack validee"
else
    echo ""
    echo -e "${COULEUR_JAUNE}Connexion OpenStack echouee.${COULEUR_RESET}"
    echo "Verifiez votre fichier .env et relancez : source venv/bin/activate && python3 run.py"
fi

echo ""
echo "============================================================"
echo -e "${COULEUR_VERT}  Installation terminee !${COULEUR_RESET}"
echo "============================================================"
echo ""
echo "  Pour demarrer l'application :"
echo "    source venv/bin/activate"
echo "    python3 run.py"
echo ""
echo "  L'interface sera disponible sur :"
IP=$(python3 -c "
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    print(s.getsockname()[0])
    s.close()
except:
    print('localhost')
" 2>/dev/null)
echo "    http://$IP:8080"
echo "============================================================"
