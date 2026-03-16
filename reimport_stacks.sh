#!/bin/bash
# Réimporte les stacks Heat existantes en base de données
# Utilisez ce script après un reset de la BDD pour retrouver vos stacks

DB_PATH="$(dirname "$0")/database/orchestration.db"

if [ ! -f "$DB_PATH" ]; then
    echo "Base de données non trouvée : $DB_PATH"
    echo "Démarrez d'abord l'application pour créer la BDD"
    exit 1
fi

echo "Réimportation des stacks dans : $DB_PATH"

sqlite3 "$DB_PATH" << 'SQL'
INSERT OR IGNORE INTO stacks (heat_id, name, status, template_id, parameters, created_at, updated_at) VALUES
  ('d8ef4eac-ccc0-4c87-96ad-ccfbba08e219', 'first_stack',    'CREATE_COMPLETE', 1, '{}', '2026-03-10 16:19:36', '2026-03-10 16:19:36'),
  ('648b3575-7927-4991-afe5-4a3a634fe543', 'heat-main-test', 'CREATE_FAILED',   1, '{}', '2026-03-10 08:36:28', '2026-03-10 08:36:28'),
  ('3243aaeb-5289-40a0-9ff8-ca372d8684b9', 'final-test',     'CREATE_COMPLETE', 1, '{}', '2026-03-10 06:12:14', '2026-03-10 06:12:14');
SQL

echo "Stacks réimportées. Vérification :"
sqlite3 "$DB_PATH" "SELECT id, name, status, heat_id FROM stacks;"
