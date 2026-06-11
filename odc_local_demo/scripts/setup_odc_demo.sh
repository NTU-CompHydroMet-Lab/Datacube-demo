#!/usr/bin/env bash
set -euo pipefail

cat > "${DATACUBE_CONFIG_PATH:-/root/.datacube.conf}" <<EOF
[datacube]
db_hostname: ${DB_HOSTNAME:-postgres}
db_database: ${DB_DATABASE:-datacube}
db_username: ${DB_USERNAME:-datacube}
db_password: ${DB_PASSWORD:-datacube}
EOF

echo "Initializing ODC database schema..."
datacube -v system init

echo "Adding product..."
datacube product add /workspace/products/s2_landcover_taiwan.yaml || true

echo "Generating dataset YAML files from /workspace/data/*.tif..."
python /workspace/scripts/write_dataset_yaml.py \
  --data-dir /workspace/data \
  --dataset-dir /workspace/datasets \
  --product s2_landcover_taiwan \
  --measurement classification

echo "Indexing datasets..."
if compgen -G "/workspace/datasets/*.yaml" > /dev/null; then
  datacube dataset add /workspace/datasets/*.yaml
else
  echo "No dataset YAML files found. Put files like 51R_20170101-20180101.tif in /workspace/data."
fi

echo "ODC Sentinel-2 land-cover demo setup complete."
