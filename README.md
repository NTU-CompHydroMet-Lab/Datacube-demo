# Datacube-demo

Tutorials for cross-datacube analysis: Google Earth Engine (GEE) and Open Data Cube (ODC).

跨數據立方分析教學：涵蓋 Google Earth Engine（Google 代管之雲端資料立方）與
Open Data Cube（自建之開源資料立方），以相同案例呈現兩種代表性架構之使用方式。

## GEE Tutorials

同一夜間燈光範例，提供兩種介面之教學：

| Tutorial | 介面 | 開啟 | 說明 |
| --- | --- | --- | --- |
| VIIRS Night Lights (Python) | Colab notebook | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NTU-CompHydroMet-Lab/Datacube-demo/blob/main/GEE/GEE.ipynb) | Python API，適合與資料處理流程整合。需具備已啟用 Earth Engine API 之 Google Cloud 專案。 |
| VIIRS Night Lights (JavaScript) | [GEE Code Editor](https://code.earthengine.google.com/) | [`GEE/code-editor-tutorial/`](GEE/code-editor-tutorial/) | GEE 原生網頁介面，無須安裝環境，適合快速試驗。 |

## ODC Tutorials

依使用者角色，提供兩種教學：

| Tutorial | 對象 | 開啟 | 說明 |
| --- | --- | --- | --- |
| Sentinel-2 Land-Cover Load Demo (notebook) | 資料科學家／學研團隊 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NTU-CompHydroMet-Lab/Datacube-demo/blob/main/ODC/notebooks/01_odc_load_demo.ipynb) | 以 Python API 完整操作資料立方：查詢產品、`dc.load()` 載入、跨年度統計與視覺化。兩種執行方式：**Colab**（零安裝，Setup 區段自動建置環境，約 3–5 分鐘）或**本地 Docker**（見下方部署）。 |
| Land-Cover Web Map (前端介面) | 一般使用者 | 部署後開啟 `http://localhost:8000` | 無須撰寫程式：於互動地圖切換年度、勾選地覆類別、檢視面積統計；圖層由 ODC 索引即時渲染。 |

## Deployment（容器化部署，兩種教學之共同基座）

[`ODC/odc_local_demo/`](ODC/odc_local_demo/) 以 Docker Compose 一鍵啟動三個服務：

- `postgres`：常駐之 ODC 索引資料庫；
- `odc`：資料匯入工具與 JupyterLab 分析環境（供學研團隊執行上述 notebook）；
- `frontend`：FastAPI + Leaflet 網頁地圖（供一般使用者操作）。

前端介面即建構於此部署之上；學研團隊亦可以同一套部署自建正式分析環境。
操作說明見 [`ODC/odc_local_demo/README.md`](ODC/odc_local_demo/README.md)。
