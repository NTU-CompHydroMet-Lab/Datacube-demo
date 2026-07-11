# Datacube-demo

Tutorials for cross-datacube analysis: Google Earth Engine (GEE) and Open Data Cube (ODC).

跨數據立方分析教學：涵蓋 Google Earth Engine（Google 代管之雲端資料立方）與
Open Data Cube（自建之開源資料立方），以相同案例呈現兩種代表性架構之使用方式。

## Tutorials

| Tutorial | Interface | Open | Notes |
| --- | --- | --- | --- |
| GEE: VIIRS Night Lights (Python) | Colab notebook | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NTU-CompHydroMet-Lab/Datacube-demo/blob/main/GEE/GEE.ipynb) | 需具備已啟用 Earth Engine API 之 Google Cloud 專案。 |
| GEE: VIIRS Night Lights (JavaScript) | [GEE Code Editor](https://code.earthengine.google.com/) | [`GEE/code-editor-tutorial/`](GEE/code-editor-tutorial/) | 同一範例之 Code Editor 版本，操作步驟見資料夾內 README。 |
| ODC: Sentinel-2 Land-Cover Load Demo | Colab notebook | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NTU-CompHydroMet-Lab/Datacube-demo/blob/main/ODC/notebooks/01_odc_load_demo.ipynb) | Colab 上自足執行：Setup 區段自動建置 PostgreSQL 與 ODC 並匯入示範資料（約 3–5 分鐘）。 |

## Local (Docker) deployment for the ODC demo

[`ODC/odc_local_demo/`](ODC/odc_local_demo/) 提供同一示範之本地 Docker Compose 部署：
常駐 PostgreSQL 索引、Jupyter 分析環境，以及 FastAPI + Leaflet 之互動網頁地圖
（自 ODC 索引即時渲染土地覆蓋圖層）。適用於正式環境之建置參考，
操作說明見 [`ODC/odc_local_demo/README.md`](ODC/odc_local_demo/README.md)。
