# ODC 本機示範環境

這個專案是一個使用 Docker Compose 建立的 Open Data Cube (ODC) 本機示範環境。它會把 Sentinel-2 衍生的台灣土地利用/土地覆蓋 GeoTIFF 檔案索引到 ODC，並提供一個簡單的 FastAPI + Leaflet 網頁地圖來瀏覽資料。

這個 demo 適合本機開發、教學與流程測試。它包含三個服務：

- `postgres`：儲存 ODC metadata 的本機 PostgreSQL 資料庫
- `odc`：執行 ODC 指令、Python 腳本與 Jupyter 的環境
- `frontend`：提供 Leaflet 網頁地圖與 API 的 FastAPI 服務

## 前置需求

- 已安裝並啟動 Docker Desktop
- Docker Desktop 使用 Linux containers
- 在此 repository 內開啟終端機，Windows 建議使用 PowerShell
- `ODC/odc_local_demo/data/` 內至少有一個 GeoTIFF 檔案

GeoTIFF 檔名必須符合以下格式：

```text
<label>_YYYYMMDD-YYYYMMDD.tif
```

範例：

```text
51R_20170101-20180101.tif
51R_20180101-20190101.tif
```

初始化腳本會讀取 `data/*.tif`，在 `datasets/` 產生 ODC dataset YAML，加入 `s2_landcover_taiwan` product，並把資料索引進 ODC。

## 專案結構

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

## Dockerfile 說明

這個 demo 需要兩個 Dockerfile，請不要刪除其中任何一個。

```text
Dockerfile           ODC、Python、Jupyter、FastAPI、GDAL 與 raster 工具
Dockerfile.postgres  postgres service 使用的本機 PostgreSQL image
```


## 開始啟用

請從 repository root 執行：

```bash
cd ODC/odc_local_demo
docker compose up -d --build
docker compose exec odc bash /workspace/scripts/setup_odc_demo.sh
docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

最後如果看到以下訊息，代表 ODC product、dataset indexing 與資料讀取測試成功：

```text
ODC demo check passed.
```

在 Windows 使用 Git Bash 時，傳入 Linux container 路徑需要關閉 MSYS path conversion：

```bash
MSYS_NO_PATHCONV=1 docker compose exec odc bash /workspace/scripts/setup_odc_demo.sh
MSYS_NO_PATHCONV=1 docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

## 確認服務狀態

檢查三個服務是否都正常執行：

```bash
docker compose ps
```

預期會看到：

```text
postgres   healthy
odc        running
frontend   running
```

檢查 frontend API：

```bash
curl http://localhost:8000/api/config
```

PowerShell 可以使用：

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/config
```

## 開啟網頁地圖

在瀏覽器開啟：

```text
http://localhost:8000
```

網頁地圖包含：

- Leaflet 地圖與 OpenStreetMap 底圖
- 根據 `data/` 內檔案產生的年份選單
- 土地覆蓋類別篩選
- 由 ODC 資料產生的 PNG overlay
- 面積統計 API
- 固定的大台北範圍 bounding box

### 操作說明（一般使用者）

此介面無須撰寫任何程式，操作方式如下：

- **Year**：下拉選單切換年度，地圖圖層與統計即時更新；
- **Classes**：勾選／取消各土地覆蓋類別（水體、樹林、農作、建成區等），控制地圖顯示內容；
- **Area Summary**：顯示目前年度、目前勾選類別的面積統計；
- **地圖**：可縮放、平移；圖層由後端自 ODC 索引即時渲染。

此介面與 notebook 教學使用同一個 ODC 索引：notebook 供資料科學家／學研團隊
以 Python API 進行客製分析；網頁介面則供一般使用者直接查閱成果。

## 開啟 Jupyter

在 `odc` container 內啟動 Jupyter Lab：

```bash
docker compose exec odc jupyter lab --ip=0.0.0.0 --port=8888 --allow-root --no-browser
```

接著打開 Jupyter 印出的網址。container 對外使用 port `8888`。

外部的 `../notebooks` 目錄會掛載到 container 內：

```text
/workspace/notebooks
```

## 資料假設

- Product name：`s2_landcover_taiwan`
- Measurement name：`classification`
- Measurement aliases：`land_cover`, `lulc`
- Data type：`uint8`
- NoData：`0`
- Units：`1`
- CRS 會從各 GeoTIFF 讀取
- 目前台灣 sample data 預期約為 `EPSG:32651`
- Dataset time range 由檔名解析
- Region code 由檔名前段 label 解析，例如 `51R`
- Pixel value 是分類代碼，不是連續光譜值
- 這類分類 raster 重新投影或對齊時應使用 nearest-neighbor resampling

目前資料常見分類代碼：

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

## 重新建立 ODC 索引

如果更換了 `data/` 內的 GeoTIFF、修改 product definition，或修改 `scripts/write_dataset_yaml.py`，但欲保留現有 container 與 PostgreSQL volume，可以執行：

```bash
docker compose exec odc bash /workspace/scripts/reset_odc_demo.sh
docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

Windows Git Bash：

```bash
MSYS_NO_PATHCONV=1 docker compose exec odc bash /workspace/scripts/reset_odc_demo.sh
MSYS_NO_PATHCONV=1 docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

## 完全重設

如果要刪除 demo 的 PostgreSQL volume，並從零重建 ODC database：

```bash
docker compose down -v
docker compose up -d --build
docker compose exec odc bash /workspace/scripts/setup_odc_demo.sh
docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

這只會刪除已索引的 ODC database volume，不會刪除 GeoTIFF、product YAML、scripts、frontend、產生出的 dataset YAML 或 notebooks。

## 結束 demo

停止 containers，但保留 PostgreSQL volume：

```bash
docker compose down
```

停止 containers，並刪除 PostgreSQL volume：

```bash
docker compose down -v
```

一般只是暫時不用時，使用 `docker compose down` 即可。
下次再用 `docker compose up -d` 啟動。

## 常見問題

### Docker Hub CloudFront EOF

如果 Docker 出現類似錯誤：

```text
failed to copy: httpReadSeeker: failed open: failed to do request ... CloudFront ... EOF
```

這通常是 Docker 下載 image layer 時網路中斷。可以重試：

```bash
docker compose up -d --build
```
。

### Docker Desktop 尚未啟動

如果 Docker 出現 `docker_engine`、`dockerDesktopLinuxEngine` 或找不到 pipe 的錯誤，請先啟動 Docker Desktop，等待 engine 完成啟動後再執行：

```bash
docker compose up -d --build
```

### PowerShell Profile Warning

如果看到：

```text
profile.ps1 cannot be loaded because running scripts is disabled
```

這是本機 PowerShell execution policy 的警告，不會阻止 Docker container 執行。此 demo 可以忽略這個警告。

### 沒有 dataset 被索引

請確認 `data/` 內有符合以下格式的檔案：

```text
<label>_YYYYMMDD-YYYYMMDD.tif
```

然後重新建立索引：

```bash
docker compose exec odc bash /workspace/scripts/reset_odc_demo.sh
docker compose exec odc python /workspace/scripts/check_odc_demo.py
```

## Web Map Interface (一般使用者操作說明)

部署完成後，以瀏覽器開啟：

```text
http://localhost:8000
```

網頁地圖介面無須撰寫任何程式，操作方式如下：

- **Year**：下拉選單切換年度，地圖圖層與統計即時更新；
- **Classes**：勾選／取消各土地覆蓋類別（水體、樹林、農作、建成區等），
  控制地圖上顯示之圖層內容；
- **Area Summary**：顯示目前年度、目前勾選類別之面積統計；
- **地圖**：可縮放、平移；土地覆蓋圖層由後端自 ODC 索引即時渲染。

此介面與 notebook 教學使用同一個 ODC 索引：notebook 供資料科學家／學研團隊
以 Python API 進行客製分析；網頁介面則供一般使用者直接查閱成果。
