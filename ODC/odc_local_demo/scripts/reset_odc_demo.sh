#!/usr/bin/env bash
set -euo pipefail

cat > "${DATACUBE_CONFIG_PATH:-/root/.datacube.conf}" <<EOF
[datacube]
db_hostname: ${DB_HOSTNAME:-postgres}
db_database: ${DB_DATABASE:-datacube}
db_username: ${DB_USERNAME:-datacube}
db_password: ${DB_PASSWORD:-datacube}
EOF

echo "Dropping and recreating ODC schema..."
psql "host=${DB_HOSTNAME:-postgres} dbname=${DB_DATABASE:-datacube} user=${DB_USERNAME:-datacube} password=${DB_PASSWORD:-datacube}" \
  -c "DROP SCHEMA IF EXISTS agdc CASCADE;"

datacube -v system init
datacube product add /workspace/products/s2_landcover_taiwan.yaml

echo "Regenerating and indexing datasets..."
python /workspace/scripts/write_dataset_yaml.py \
  --data-dir /workspace/data \
  --dataset-dir /workspace/datasets \
  --product s2_landcover_taiwan \
  --measurement classification

if compgen -G "/workspace/datasets/*.yaml" > /dev/null; then
  datacube dataset add /workspace/datasets/*.yaml
fi

echo "ODC Sentinel-2 land-cover demo reset complete."
