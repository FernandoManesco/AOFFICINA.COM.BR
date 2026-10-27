#!/bin/bash
# Backup diário do banco da instância (mysqldump + gzip), mantém 30 dias.
# Lê DB_* do api/.env. Agendar no cron do usuário deploy:
#   15 3 * * * /home/deploy/aofficina/scripts/backup_mysql.sh >> /home/deploy/aofficina/logs/backup.log 2>&1
set -euo pipefail
BASE=/home/deploy/aofficina
DEST=$BASE/backups
mkdir -p "$DEST" "$BASE/logs"
set -a; source "$BASE/api/.env"; set +a
ARQ="$DEST/${DB_NAME}_$(date +%Y%m%d_%H%M).sql.gz"
MYSQL_PWD="$DB_PASSWORD" mysqldump -h "$DB_HOST" -P "${DB_PORT:-3306}" -u "$DB_USER" \
  --single-transaction --routines --triggers "$DB_NAME" | gzip -9 > "$ARQ"
find "$DEST" -name "${DB_NAME}_*.sql.gz" -mtime +30 -delete
echo "$(date '+%F %T') backup ok: $ARQ ($(du -h "$ARQ" | cut -f1))"
