# Rasdaman 資料立方環境部署 — 初步標準作業流程 (SOP)

以 **rootless Podman** 將 **rasdaman Community**（多維陣列資料庫與 Petascope OGC 服務）部署為單一 all-in-one 容器，並以 Python notebook 透過 WCS/WCPS 互動。本文件為初步標準作業流程，涵蓋環境需求、逐步建置、資料匯入、驗證、備份與疑難排解，供後續於不同環境重現與正式化之參考。

> rasdaman 官方僅支援 Ubuntu 20.04 / 22.04 / 24.04；透過容器將其與主機作業系統脫鉤，即容器內執行 24.04，主機作業系統版本不受限，此為採用容器化部署之主要理由。

---

## 0. 名詞與架構

- **rasdaman**：raster/array DBMS，查詢語言為 `rasql`；對外由 **Petascope** 提供 OGC 標準服務（WCS / WCPS / WMS）。後端以 PostgreSQL 儲存 geo metadata，並以 SQLite 與檔案儲存 array tiles。
- **all-in-one 容器**：單一容器內含 `rasdaman`、`Petascope`、`SECORE` 與 `PostgreSQL`。rasdaman 套件設計上自帶 PostgreSQL 相依並預期於 localhost 運行，故 all-in-one 之單容器架構最為貼合。

```
容器 rasdaman
 ├─ PostgreSQL (petascope metadata)
 ├─ rasmgr / rasserver         ← array DBMS 核心 (rasql)
 └─ Petascope + SECORE (:8080) ← OGC WCS/WCPS/WMS
對外只發布 127.0.0.1:8080
```

---

## 1. 環境參數設定

本流程之環境相關參數集中定義於下列變數，以下為範例值，實際部署時應依環境調整；變更部署主機時僅需修改此處。

```bash
# 儲存空間：存放 .deb 快取與 image 備份，應設定為具寫入權限之路徑（個人空間或掛載儲存）
export STORAGE_ROOT="/path/to/your/storage/rasdaman"

# rasdaman 版本與 .deb 來源（見 §2）
export RAS_DEB="$STORAGE_ROOT/cache/rasdaman_10.6.3noble-1_amd64.deb"

# 容器與帳號密碼
export POD_IMAGE="localhost/rasdaman:latest"
export RAS_USER="rasadmin"      # Petascope/rasdaman 預設管理者，正式化前務必更換，見下方 ⚠️
export RAS_PASS="rasadmin"
export PETASCOPE_PORT=8080      # 僅綁定 127.0.0.1
```

> ⚠️ **正式化前務必更換預設帳號密碼**：`rasadmin:rasadmin` 為 rasdaman 之公開預設值，僅供研發與示範。於正式或對外環境部署前，應更換 Petascope 管理者密碼並檢視存取控制設定。

> **image store 須置於本機檔案系統，不可置於 NAS。** rootless podman 於解壓 image 層時，需將檔案 `lchown` 至 user namespace 之 subuid，而 NFS（`sec=sys`）不允許此類 chown 操作，於 NAS 上建置或載入 image 將失敗（`lchown ... operation not permitted`）。故 image 一律使用 podman 預設 store（`~/.local/share/containers`，位於本機家目錄），採 overlay 驅動，效能與穩定性均佳；image 約 2 GB。NAS 僅用於存放 .deb 快取（§2）與 image 備份（§9）。若本機空間不足，替代方案為改用另一本機（非 NFS）路徑作為 store，詳見 §3。

---

## 2. 取得 rasdaman 安裝套件（.deb）

為確保建置之重現性並支援離線安裝，容器由本地 .deb 套件安裝 rasdaman，而非於每次建置時連線官方套件庫。安裝套件僅需事先下載一次。

下載指令如下（支援斷線續傳）：
```bash
wget -c --tries=0 --timeout=60 --waitretry=15 \
  "https://download.rasdaman.org/packages/deb/pool/stable/r/rasdaman/rasdaman_10.6.3noble-1_amd64.deb"
```
下載完成後，將檔案置於 `$STORAGE_ROOT/cache/`（檔案大小應為 `192439972` bytes）：
```bash
mkdir -p "$STORAGE_ROOT/cache"
mv rasdaman_10.6.3noble-1_amd64.deb "$STORAGE_ROOT/cache/"
```

> 如需使用其他版本，請至 `https://download.rasdaman.org/packages/deb/pool/stable/r/rasdaman/` 取得對應之 `*noble*` 套件，並同步更新 `$RAS_DEB`。

---

## 3.（選用）變更 image store 至其他本機路徑

多數情況可略過本節，直接使用 podman 預設 store（家目錄）。

僅當本機 `/home` 空間不足時，方需將 store 變更至另一具寫入權限之本機（非 NFS）路徑，例如另一本機資料碟；不可使用 NAS/NFS（參見 §1 之 lchown 限制）。以下採專案層級設定，不影響全域組態：

```bash
LOCAL_STORE="/path/on/a/local/disk/rasdaman-store"   # 必須為本機檔案系統
mkdir -p "$LOCAL_STORE"
cat > storage.conf <<EOF
[storage]
driver = "overlay"
graphroot = "$LOCAL_STORE/containers"
runroot = "$LOCAL_STORE/run"
EOF
export CONTAINERS_STORAGE_CONF="$PWD/storage.conf"   # 後續每個 podman 指令均需此環境變數
podman info --format '{{.Store.GraphRoot}} {{.Store.GraphDriverName}}'
```

> ⚠️ 請勿執行 `podman system reset`，該指令將清除當前帳號下所有容器與 image。

---

## 4. 建構 image

本專案提供三個與環境無關之檔案：`Dockerfile`、`scripts/build-install.sh`、`scripts/entrypoint.sh`。建置時將 `.deb` 所在目錄以 `--volume` 唯讀掛載，使 `.deb` 不納入 image 層：

```bash
podman build --volume "$(dirname "$RAS_DEB")":/debs:ro -t "$POD_IMAGE" .
```

建置流程重點：
- 以 `ubuntu:24.04` 為基底，安裝 `postgresql`、`wget`（安裝器健康檢查所需）等套件。
- `build-install.sh`：先啟動 postgres 並建立 petascopedb，再由 `/debs` 之 `.deb` 安裝 rasdaman。rasdaman 安裝器須於 postgres 運行中方能完成，故無法於未具 postgres 之環境安裝。
- 產出 image 約 **2.1 GB**。

---

## 5. 啟動容器

```bash
podman rm -f rasdaman 2>/dev/null
podman run -d --name rasdaman \
  --memory=8g --cpus=4 \
  -p 127.0.0.1:${PETASCOPE_PORT}:8080 \
  "$POD_IMAGE"
```

entrypoint 依序啟動 postgres 與 `start_rasdaman.sh`（rasmgr、rasserver、Petascope）。Petascope 約需 **30–60 秒**完成部署。

---

## 6. 驗證

> **重要**：rasdaman 10.6 之 Petascope 預設啟用存取控制，所有 OGC 請求均須帶帳號密碼。

```bash
# 等待 Petascope 就緒並取得能力文件（回應 200 為正常）
curl -s -u "$RAS_USER:$RAS_PASS" \
  "http://127.0.0.1:${PETASCOPE_PORT}/rasdaman/ows?service=WCS&version=2.1.0&request=GetCapabilities" \
  | head -c 200

# rasql 核心測試（於容器內執行）
podman exec rasdaman bash -lc \
  "rasql -q 'select c from RAS_COLLECTIONNAMES as c' --out string --user $RAS_USER --passwd $RAS_PASS"
```

---

## 7. 匯入示範資料（wcst_import）

`wcst_import.sh` 讀取一份 **ingredients JSON**，將 raster 匯入為 coverage。可先執行官方內建示範資料：

```bash
podman exec rasdaman bash -lc 'petascope_insertdemo.sh'
```

執行後將新增三個 coverage：`AverageChlorophyll`、`AverageTemperature`、`mean_summer_airtemp`。

匯入自訂資料時，ingredients 範例參見 `examples/wcst_import/`（含官方範本與說明）。因 Petascope 啟用存取控制，執行時需提供 identity file：
```bash
podman cp examples/wcst_import/your.json rasdaman:/tmp/ing.json
podman exec rasdaman bash -lc '
  printf "rasadmin:rasadmin" > /tmp/rasid && chmod 600 /tmp/rasid
  wcst_import.sh -i /tmp/rasid /tmp/ing.json'
```

---

## 8. 以 Notebook 互動（WCS / WCPS）

```bash
cd notebooks
uv venv --python 3.12 .venv
VIRTUAL_ENV="$PWD/.venv" uv pip install -r requirements.txt ipykernel
.venv/bin/python -m ipykernel install --user --name rasdaman --display-name "Python (rasdaman)"
.venv/bin/jupyter lab        # 開啟 rasdaman_intro.ipynb，kernel 選擇「Python (rasdaman)」
```

notebook 預設連線 `http://127.0.0.1:8080/rasdaman`，帳號密碼為 `rasadmin:rasadmin`，可透過 `RASDAMAN_BASE` / `RASDAMAN_USER` / `RASDAMAN_PASS` 覆寫。內容涵蓋：列出 coverage、DescribeCoverage、WCPS 聚合、2D 影像化，以及 **3D 時間序列切片**。

---

## 9. 持久化與備份

- 容器於 `podman stop` / `start` 之間資料保留，未執行 `podman rm` 前資料持續存在。
- **可攜備份**：將 image 儲存為 tarball 置於 NAS，變更部署主機時可直接 `podman load`，無須重新建置：
  ```bash
  podman save "$POD_IMAGE" | gzip > "$STORAGE_ROOT/rasdaman-image.tar.gz"
  # 還原： gunzip -c "$STORAGE_ROOT/rasdaman-image.tar.gz" | podman load
  ```
- （進階）將 `pgdata` 與 array tiles 掛載為 volume 並置於 NAS，可於 `podman rm` 後仍保留資料。

---

## 10. 疑難排解（常見問題）

| 症狀 | 原因與處理 |
|---|---|
| `apt install rasdaman` 耗時過長 | 改由本地 `.deb` 安裝（§2） |
| 建置時安裝器停滯於 "Starting rasdaman..." | 建置環境未運行 postgres → 使用 `build-install.sh`（先啟動 postgres） |
| 安裝器回報 `No such file: 'wget'` | 安裝器健康檢查需 `wget`，image 已內含 |
| OGC 請求回 **403 InvalidCredentials** | Petascope 存取控制，所有請求須帶 `-u rasadmin:rasadmin` |
| wcst_import 回報 `Failed parsing the crs ... Index2D` | CRS 路徑須包含 `/crs/`，例如 `…/def/crs/EPSG/0/4326` |
| wcst_import 軸方向錯誤或 NPE | `map_mosaic` 需具地理參考之影像；無地理參考者須先以 `gdal_translate -a_srs … -a_ullr …` 處理 |
| encode PNG 回 **400 "only supports 2D"** | 該 coverage 為 3D 時間序列，須先於時間軸切取一格降為 2D（notebook 第 6 節有範例） |
| 於 NAS 建置或載入 image 失敗（`lchown ... operation not permitted`） | rootless 與 NFS 之限制，image store 僅能置於本機（§1），NAS 僅存放 `.deb` 與備份 |
| podman image 佔滿 `/home` | 改用另一本機碟作為 store（§3）；NAS 不可用（lchown 限制） |

---

## 專案結構

```
Rasdaman/
├── README.md                     # 本標準作業流程 (SOP)
├── Dockerfile                    # all-in-one image（與環境無關）
├── scripts/
│   ├── build-install.sh          # 建置時：啟動 postgres → 由本地 .deb 安裝 rasdaman
│   └── entrypoint.sh             # 啟動時：啟動 postgres → 啟動 rasdaman 與 Petascope
├── examples/wcst_import/         # 資料匯入 ingredients 範例與說明
└── notebooks/                    # Python notebook（WCS/WCPS 互動）與環境說明
```
