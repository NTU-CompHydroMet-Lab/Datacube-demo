# ODC Local Demo

This is a small Open Data Cube demo container for testing local Sentinel-2-derived
Taiwan land-use/land-cover GeoTIFF indexing.

Expected raster filename pattern:

```text
<label>_YYYYMMDD-YYYYMMDD.tif
```

Example:

```text
51R_20170101-20180101.tif
51R_20180101-20190101.tif
```

The setup script scans `data/*.tif`, generates ODC dataset YAML files in `datasets/`,
adds the `s2_landcover_taiwan` product, and indexes the generated datasets.

The rasters are treated as categorical land-cover data, not continuous spectral
imagery. The product reads band 1 as a `uint8` `classification` measurement with
NoData value `0`.

## Layout

```text
project_root/
├── odc_local_demo/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── README.md
│   ├── data/
│   ├── products/
│   │   └── s2_landcover_taiwan.yaml
│   ├── datasets/
│   └── scripts/
│       ├── setup_odc_demo.sh
│       ├── reset_odc_demo.sh
│       ├── write_dataset_yaml.py
│       └── check_odc_demo.py
└── notebooks/
    └── 01_odc_load_demo.ipynb
```

## Run

Put one or more GeoTIFF files in `odc_local_demo/data/`.

On Windows, PowerShell is the simplest shell for these commands. The container
commands still use `bash`, but that `bash` runs inside the Linux container.

```bash
cd odc_local_demo
docker compose up -d --build
docker compose exec odc bash /workspace/scripts/setup_odc_demo.sh
docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

If you run these commands from Git Bash on Windows, disable MSYS path conversion
for container paths:

```bash
MSYS_NO_PATHCONV=1 docker compose exec odc bash /workspace/scripts/setup_odc_demo.sh
MSYS_NO_PATHCONV=1 docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

## Open Jupyter

```bash
docker compose exec odc jupyter lab --ip=0.0.0.0 --port=8888 --allow-root --no-browser
```

From Git Bash on Windows:

```bash
MSYS_NO_PATHCONV=1 docker compose exec odc jupyter lab --ip=0.0.0.0 --port=8888 --allow-root --no-browser
```

The external `../notebooks` directory is mounted at `/workspace/notebooks`.

## Reset

### Rebuild ODC Index Only

Use this when you changed files in `data/`, changed the product definition, or
changed `scripts/write_dataset_yaml.py`, and want to rebuild the ODC database
index while keeping the Docker containers and volume.

```bash
docker compose exec odc bash /workspace/scripts/reset_odc_demo.sh
```

From Git Bash on Windows:

```bash
MSYS_NO_PATHCONV=1 docker compose exec odc bash /workspace/scripts/reset_odc_demo.sh
```

Then verify:

```bash
docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

From Git Bash on Windows:

```bash
MSYS_NO_PATHCONV=1 docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

### Stop After Demo

Use this when the demo is done and you want to stop containers but keep the ODC
database volume for next time:

```bash
docker compose down
```

### Full Reset From Scratch

Use this when you want to remove the demo PostgreSQL volume and recreate the
entire ODC database from scratch. This deletes the indexed ODC database only; it
does not delete your GeoTIFF files, scripts, product YAML, generated dataset YAML
files, or notebooks.

```bash
docker compose down -v
docker compose up -d --build
docker compose exec odc bash /workspace/scripts/setup_odc_demo.sh
docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

From Git Bash on Windows:

```bash
docker compose down -v
docker compose up -d --build
MSYS_NO_PATHCONV=1 docker compose exec odc bash /workspace/scripts/setup_odc_demo.sh
MSYS_NO_PATHCONV=1 docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

## Assumptions

- Product name: `s2_landcover_taiwan`
- Measurement name: `classification`
- Measurement aliases: `land_cover`, `lulc`
- Data type: `uint8`
- NoData: `0`
- Units: `1`
- CRS is read from each GeoTIFF, expected around EPSG:32651 for the current Taiwan data.
- Dataset time range comes from the filename.
- Region code comes from the filename label, for example `51R`.
- Pixel values are categorical class codes. Use nearest-neighbor resampling when reprojecting or aligning these rasters.

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
