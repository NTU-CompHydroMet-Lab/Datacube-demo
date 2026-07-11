# rasdaman 互動 Notebook

透過 Python 環境，以 OGC Web 服務（WCS / WCPS）與 rasdaman 的 Petascope 互動。

## 前置：rasdaman 服務要在跑

Notebook 預設連 `http://127.0.0.1:8080/rasdaman`（Petascope 綁本機 8080）。
請先把 rasdaman 容器跑起來、並確認 `GetCapabilities` 有回應。

**注意**：rasdaman 10.6 的 Petascope **預設啟用存取控制**，所有 OGC 請求都要帶帳密
（HTTP Basic）。Notebook 預設用 `rasadmin / rasadmin`。若服務位址/帳密不同，設定環境變數：

```bash
export RASDAMAN_BASE=http://127.0.0.1:8080/rasdaman
export RASDAMAN_USER=rasadmin
export RASDAMAN_PASS=rasadmin
```

## 建立 Python 環境並啟動（uv）

本專案用 [uv](https://docs.astral.sh/uv/) 管理環境（已建好 `.venv`，Python 3.12，
並註冊了名為 **`Python (rasdaman)`** 的 Jupyter kernel）。

若要從頭重建：
```bash
cd notebooks
uv venv --python 3.12 .venv
VIRTUAL_ENV="$PWD/.venv" uv pip install -r requirements.txt ipykernel
.venv/bin/python -m ipykernel install --user --name rasdaman --display-name "Python (rasdaman)"
```

啟動 JupyterLab：
```bash
cd notebooks
.venv/bin/jupyter lab        # 或：source .venv/bin/activate && jupyter lab
```

開啟 `rasdaman_intro.ipynb`，**右上角 kernel 選 `Python (rasdaman)`**，由上而下執行即可。
（如連線位址/帳密不同，先 `export RASDAMAN_BASE=...` / `RASDAMAN_USER` / `RASDAMAN_PASS`。）

## Notebook 內容

1. 連線設定與健康檢查
2. WCS `GetCapabilities` — 列出已註冊的 coverage
3. WCS `DescribeCoverage` — 看某個 coverage 的維度與範圍
4. WCPS 查詢範例 — 在 server 端做陣列運算並取回結果
5. 後續：如何匯入自己的 raster（GeoTIFF/NetCDF）

> 註：`.venv/` 已在專案 `.gitignore` 忽略，不會進版控。
