# ODC Local Demo

This project is a local Docker Compose demo for indexing Sentinel-2-derived
Taiwan land-use/land-cover GeoTIFF files into Open Data Cube (ODC), then viewing
the indexed data through a small FastAPI + Leaflet web map.

The demo is intended for local development and teaching. It runs three services:

- `postgres`: local PostgreSQL database for ODC metadata
- `odc`: Open Data Cube command-line and Jupyter runtime
- `frontend`: FastAPI service that renders map overlays from ODC

## Prerequisites

- Docker Desktop installed and running
- Docker Desktop using Linux containers
- A terminal in this repository, preferably PowerShell on Windows
- One or more GeoTIFF files in `ODC/odc_local_demo/data/`

The expected raster filename pattern is:

```text
<label>_YYYYMMDD-YYYYMMDD.tif
```

Examples:

```text
51R_20170101-20180101.tif
51R_20180101-20190101.tif
```

The setup script reads `data/*.tif`, creates ODC dataset YAML files in
`datasets/`, adds the `s2_landcover_taiwan` product, and indexes the generated
datasets.

## Project Layout

```text
project_root/
|-- ODC/
|   |-- odc_local_demo/
|   |   |-- docker-compose.yml
|   |   |-- Dockerfile
|   |   |-- Dockerfile.postgres
|   |   |-- requirements.txt
|   |   |-- README.md
|   |   |-- data/
|   |   |-- datasets/
|   |   |-- frontend/
|   |   |-- products/
|   |   |   `-- s2_landcover_taiwan.yaml
|   |   `-- scripts/
|   |       |-- setup_odc_demo.sh
|   |       |-- reset_odc_demo.sh
|   |       |-- local_postgres_entrypoint.sh
|   |       |-- write_dataset_yaml.py
|   |       `-- check_odc_demo.py
|   `-- notebooks/
|       `-- 01_odc_load_demo.ipynb
```

## Docker Files

Both Dockerfiles are required.

```text
Dockerfile           ODC, Python, Jupyter, FastAPI, GDAL, and raster tools
Dockerfile.postgres  Local PostgreSQL image used by the postgres service
```

`Dockerfile.postgres` exists to avoid pulling the official `postgres:15` image.
Some networks can fail while downloading Docker Hub layers through CloudFront
with an `EOF` error. This demo instead builds PostgreSQL locally from the same
`python:3.11-slim` base image used by the ODC service.

## Quick Start

From the repository root:

```bash
cd ODC/odc_local_demo
docker compose up -d --build
docker compose exec odc bash /workspace/scripts/setup_odc_demo.sh
docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

Expected final output:

```text
ODC demo check passed.
```

If you are using Git Bash on Windows, disable MSYS path conversion for commands
that pass Linux container paths:

```bash
MSYS_NO_PATHCONV=1 docker compose exec odc bash /workspace/scripts/setup_odc_demo.sh
MSYS_NO_PATHCONV=1 docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

## Verify Services

Check that all services are running:

```bash
docker compose ps
```

Expected services:

```text
postgres   healthy
odc        running
frontend   running
```

Check the frontend API:

```bash
curl http://localhost:8000/api/config
```

On PowerShell:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/config
```

## Open Web Map Demo

Open:

```text
http://localhost:8000
```

The web map includes:

- Leaflet map with OpenStreetMap basemap
- Year selector based on files in `data/`
- Land-cover class filters
- PNG overlay rendered from ODC data
- Area summary endpoint
- Fixed Greater Taipei bounding box

## Open Jupyter

Start Jupyter Lab inside the `odc` container:

```bash
docker compose exec odc jupyter lab --ip=0.0.0.0 --port=8888 --allow-root --no-browser
```

Then open the URL printed by Jupyter. The container exposes port `8888`.

The external `../notebooks` directory is mounted at:

```text
/workspace/notebooks
```

## Data Assumptions

- Product name: `s2_landcover_taiwan`
- Measurement name: `classification`
- Measurement aliases: `land_cover`, `lulc`
- Data type: `uint8`
- NoData: `0`
- Units: `1`
- CRS is read from each GeoTIFF
- Current Taiwan sample data is expected around `EPSG:32651`
- Dataset time range is parsed from the filename
- Region code is parsed from the filename label, for example `51R`
- Pixel values are categorical class codes
- Use nearest-neighbor resampling for these rasters

Common class codes in the current data:

```text
0  NoData
1  Water
2  Trees
4  Flooded Vegetation
5  Crops
7  Built Area
8  Bare Ground
9  Snow/Ice
10 Clouds
11 Rangeland
```

## Rebuild ODC Index

Use this when you changed files in `data/`, changed the product definition, or
changed `scripts/write_dataset_yaml.py`, but want to keep the existing Docker
containers and PostgreSQL volume.

```bash
docker compose exec odc bash /workspace/scripts/reset_odc_demo.sh
docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

From Git Bash on Windows:

```bash
MSYS_NO_PATHCONV=1 docker compose exec odc bash /workspace/scripts/reset_odc_demo.sh
MSYS_NO_PATHCONV=1 docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

## Full Reset

Use this when you want to remove the demo PostgreSQL volume and recreate the ODC
database from scratch.

This deletes the indexed ODC database only. It does not delete your GeoTIFF
files, product YAML, scripts, frontend, generated dataset YAML files, or
notebooks.

```bash
docker compose down -v
docker compose up -d --build
docker compose exec odc bash /workspace/scripts/setup_odc_demo.sh
docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

## Stop The Demo

Stop containers but keep the PostgreSQL volume:

```bash
docker compose down
```

Stop containers and delete the PostgreSQL volume:

```bash
docker compose down -v
```

## Troubleshooting

### Docker Hub CloudFront EOF

If Docker prints an error similar to this:

```text
failed to copy: httpReadSeeker: failed open: failed to do request ... CloudFront ... EOF
```

This is a network interruption while Docker is downloading an image layer. Retry:

```bash
docker compose up -d --build
```

This project avoids pulling the official `postgres` image, but Docker may still
need to pull `python:3.11-slim` the first time.

### Docker Desktop Is Not Running

If Docker prints an error about `docker_engine`, `dockerDesktopLinuxEngine`, or a
missing pipe, start Docker Desktop and wait until it reports that the engine is
running.

Then retry:

```bash
docker compose up -d --build
```

### PowerShell Profile Warning

If you see:

```text
profile.ps1 cannot be loaded because running scripts is disabled
```

That warning comes from the local PowerShell execution policy. It does not
prevent Docker containers from running. You can ignore it for this demo.

### No Datasets Indexed

Confirm that `data/` contains files matching:

```text
<label>_YYYYMMDD-YYYYMMDD.tif
```

Then rebuild the index:

```bash
docker compose exec odc bash /workspace/scripts/reset_odc_demo.sh
docker compose exec odc python /workspace/scripts/check_odc_demo.py
```
