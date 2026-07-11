# Rasdaman 資料立方環境部署 — 初步標準作業流程 (SOP)

以 **rootless Podman** 將 **rasdaman Community**（多維陣列資料庫 + Petascope OGC 服務）
部署為單一 all-in-one 容器，並以 Python notebook 透過 WCS/WCPS 互動。本文件為初步標準作業流程，
涵蓋環境需求、逐步建置、資料匯入、驗證、備份與疑難排解，供後續於不同環境重現與正式化參考。

> rasdaman 官方僅支援 Ubuntu 20.04 / 22.04 / 24.04；透過容器將其與主機作業系統脫鉤，
> 即容器內執行 24.04，主機作業系統版本不受限，此為採用容器化部署之主要理由。

---

## 0. 名詞與架構

- **rasdaman**：raster/array DBMS。查詢語言 `rasql`；對外用 **Petascope** 提供 OGC 標準服務
  （WCS / WCPS / WMS）。後端用 PostgreSQL 存 geo metadata、SQLite + 檔案存 array tiles。
- **本容器（all-in-one）**：一個容器內含 `rasdaman` + `Petascope` + `SECORE` + `PostgreSQL`。
  rasdaman 套件本來就設計成自帶 postgres 相依、預期 localhost，所以 all-in-one 最貼合它。

```
容器 rasdaman
 ├─ PostgreSQL (petascope metadata)
 ├─ rasmgr / rasserver         ← array DBMS 核心 (rasql)
 └─ Petascope + SECORE (:8080) ← OGC WCS/WCPS/WMS
對外只發布 127.0.0.1:8080
```

---

## 1. 可調參數（機器專屬，集中在這）

本流程所有「環境專屬」的值都收斂成下面幾個變數，**以下為範例值，請依實際環境調整**；
換機器／換人時只需修改此處。

```bash
# 儲存空間：放 .deb 快取與 image 備份（請改為你有寫入權之路徑，例如個人空間或掛載儲存）
export STORAGE_ROOT="/path/to/your/storage/rasdaman"

# rasdaman 版本與 .deb 來源（見 §2 取得 .deb）
export RAS_DEB="$STORAGE_ROOT/cache/rasdaman_10.6.3noble-1_amd64.deb"

# 容器/帳密
export POD_IMAGE="localhost/rasdaman:latest"
export RAS_USER="rasadmin"      # Petascope/rasdaman 預設管理者（預設值，正式化前務必更換，見下方 ⚠️）
export RAS_PASS="rasadmin"
export PETASCOPE_PORT=8080      # 只綁 127.0.0.1
```

> ⚠️ **正式化前務必更換預設帳密**：`rasadmin:rasadmin` 為 rasdaman 之公開預設值，僅供研發/示範。
> 於正式或對外環境部署前，應更換 Petascope 管理者密碼並檢視存取控制設定。

> **image store 必須放本機，不能放 NAS（重要）。** rootless podman 解壓 image 層時要
> `lchown` 檔案到 user-namespace 的 subuid，而 **NFS（`sec=sys`）不允許這種 chown**
> → 在 NAS 上 build/load 會直接失敗（`lchown ... operation not permitted`）。
> 所以 image 一律用 **podman 預設 store（`~/.local/share/containers`，即本機 `/home`）**，
> 那是你的**個人家目錄**、overlay、快、可靠（postgres 也跑在本機檔案系統上）。
> image 約 2GB，本機家目錄放得下。
> NAS 個人區只拿來放 **`.deb` 快取**（§2）與 **image 備份**（§9）。
> （若本機 `/home` 真的不足，唯一選項是換**另一個本機**路徑當 store，不能是 NFS；見 §3。）

---

## 2. 取得 rasdaman 的 .deb（一次性）

容器從**本地 `.deb`** 安裝 rasdaman，不在每次 build 時連官方套件庫——因為官方源
（`download.rasdaman.org`，在德國）對台灣很慢（實測 ~0.1 MB/s，192MB 要數小時）。
先把 `.deb` 抓一次存起來，之後一勞永逸、也可重現。

在**網路較快的機器**上抓（斷線會續傳）：
```bash
wget -c --tries=0 --timeout=60 --waitretry=15 \
  "https://download.rasdaman.org/packages/deb/pool/stable/r/rasdaman/rasdaman_10.6.3noble-1_amd64.deb"
```
抓到後放到 `$STORAGE_ROOT/cache/`（大小應為 `192439972` bytes）：
```bash
mkdir -p "$STORAGE_ROOT/cache"
mv rasdaman_10.6.3noble-1_amd64.deb "$STORAGE_ROOT/cache/"
```

> 想換版本：到 `https://download.rasdaman.org/packages/deb/pool/stable/r/rasdaman/`
> 找對應 `*noble*` 的檔，並同步改 `$RAS_DEB`。

---

## 3.（選用）本機 `/home` 不足時，把 image store 換到另一個本機路徑

**多數情況跳過這節**——直接用 podman 預設 store（家目錄）即可。

只有當你的本機 `/home` 真的塞不下時，才把 store 換到**另一個本機（非 NFS）**、且你有寫入權的
路徑（例如另一顆本機資料碟）。**不能用 NAS/NFS**（見 §1 的 lchown 限制）。
用**專案專屬**設定，不動全域：

```bash
LOCAL_STORE="/path/on/a/local/disk/rasdaman-store"   # 必須是本機檔案系統
mkdir -p "$LOCAL_STORE"
cat > storage.conf <<EOF
[storage]
driver = "overlay"
graphroot = "$LOCAL_STORE/containers"
runroot = "$LOCAL_STORE/run"
EOF
export CONTAINERS_STORAGE_CONF="$PWD/storage.conf"   # 之後每個 podman 指令都需這個 env
podman info --format '{{.Store.GraphRoot}} {{.Store.GraphDriverName}}'
```

> ⚠️ 絕不要執行 `podman system reset`（會清掉你帳號下所有容器/image）。

---

## 4. 建構 image

專案提供三個與機器無關的檔：`Dockerfile`、`scripts/build-install.sh`、`scripts/entrypoint.sh`。
build 時把 `.deb` 所在目錄用 `--volume` 唯讀掛進去（`.deb` 不進 image 層）：

```bash
podman build --volume "$(dirname "$RAS_DEB")":/debs:ro -t "$POD_IMAGE" .
```

build 做了什麼（重點）：
- base 用 `ubuntu:24.04`，裝 `postgresql`、`wget`（安裝器健康檢查必需）等。
- `build-install.sh`：**先啟動 postgres、建 petascopedb，再從 `/debs` 的 `.deb` 裝 rasdaman**。
  rasdaman 的安裝器需要 postgres 在跑才能完成（這也是為何不能在「無 postgres」的環境裝）。
- 成品約 **2.1 GB**。

---

## 5. 啟動容器

```bash
podman rm -f rasdaman 2>/dev/null
podman run -d --name rasdaman \
  --memory=8g --cpus=4 \
  -p 127.0.0.1:${PETASCOPE_PORT}:8080 \
  "$POD_IMAGE"
```

entrypoint 會：起 postgres → `start_rasdaman.sh`（rasmgr + rasserver + Petascope）。
Petascope 約需 **30–60 秒**完成部署。

---

## 6. 驗證

> **重要**：rasdaman 10.6 的 Petascope **預設啟用存取控制**，所有 OGC 請求都要帶帳密。

```bash
# 等 Petascope 就緒並取得能力文件（200 才算好）
curl -s -u "$RAS_USER:$RAS_PASS" \
  "http://127.0.0.1:${PETASCOPE_PORT}/rasdaman/ows?service=WCS&version=2.1.0&request=GetCapabilities" \
  | head -c 200

# rasql 核心測試（在容器內）
podman exec rasdaman bash -lc \
  "rasql -q 'select c from RAS_COLLECTIONNAMES as c' --out string --user $RAS_USER --passwd $RAS_PASS"
```

---

## 7. 匯入示範資料（wcst_import）

`wcst_import.sh` 吃一份 **ingredients JSON**，把 raster 匯成 coverage。先用官方內建 demo
（與此版本一起測過、保證可動）：

```bash
podman exec rasdaman bash -lc 'petascope_insertdemo.sh'
```

完成後會多出 3 個 coverage：`AverageChlorophyll`、`AverageTemperature`、`mean_summer_airtemp`。

匯入你自己的資料時，ingredients 範例見 `examples/wcst_import/`（含官方可動範本與說明）。
執行方式（petascope 有存取控制，需 identity file）：
```bash
podman cp examples/wcst_import/your.json rasdaman:/tmp/ing.json
podman exec rasdaman bash -lc '
  printf "rasadmin:rasadmin" > /tmp/rasid && chmod 600 /tmp/rasid
  wcst_import.sh -i /tmp/rasid /tmp/ing.json'
```

---

## 8. 用 Notebook 互動（WCS / WCPS）

```bash
cd notebooks
uv venv --python 3.12 .venv
VIRTUAL_ENV="$PWD/.venv" uv pip install -r requirements.txt ipykernel
.venv/bin/python -m ipykernel install --user --name rasdaman --display-name "Python (rasdaman)"
.venv/bin/jupyter lab        # 開 rasdaman_intro.ipynb，kernel 選「Python (rasdaman)」
```

notebook 預設連 `http://127.0.0.1:8080/rasdaman`、帳密 `rasadmin:rasadmin`（可用
`RASDAMAN_BASE` / `RASDAMAN_USER` / `RASDAMAN_PASS` 覆寫）。內容涵蓋：列 coverage、
DescribeCoverage、WCPS 聚合、2D 影像化、**3D 時間序列切片**。

---

## 9. 持久化與備份

- 容器 `podman stop` / `start` 之間資料保留；只要不 `podman rm` 就在。
- **可攜備份**：把 image 存成 tarball 到 NAS，換機器直接 `podman load`，免重 build：
  ```bash
  podman save "$POD_IMAGE" | gzip > "$STORAGE_ROOT/rasdaman-image.tar.gz"
  # 還原： gunzip -c "$STORAGE_ROOT/rasdaman-image.tar.gz" | podman load
  ```
- （進階）把 `pgdata` / array tiles 拉成 volume 放 NAS，可在 `podman rm` 後仍保留資料。

---

## 10. 疑難排解（實測踩過的雷）

| 症狀 | 原因 / 解法 |
|---|---|
| `apt install rasdaman` 卡很久 | 官方源在德國很慢 → 用本地 `.deb`（§2） |
| build 時安裝器卡在 "Starting rasdaman..." | 沒有 postgres / 在 build 沙箱啟動服務 → 用 `build-install.sh`（先起 postgres） |
| 安裝器 `No such file: 'wget'` | 安裝器健康檢查需要 `wget` → image 已裝 |
| OGC 請求回 **403 InvalidCredentials** | Petascope 存取控制 → 所有請求帶 `-u rasadmin:rasadmin` |
| wcst_import `Failed parsing the crs ... Index2D` | CRS 路徑要含 `/crs/`：`…/def/crs/EPSG/0/4326` |
| wcst_import 軸方向錯 / NPE | `map_mosaic` 需「有地理參考」的影像；純影像先 `gdal_translate -a_srs … -a_ullr …` |
| encode PNG 回 **400 "only supports 2D"** | 該 coverage 是 3D 時間序列 → 先在時間軸切一格降成 2D（notebook 第 6 節有自動範例） |
| NAS 上 build/load image 失敗 `lchown ... operation not permitted` | rootless+NFS 的硬限制 → image store **只能放本機**（§1）；NAS 僅放 `.deb` 與備份 |
| podman image 把 `/home` 塞滿 | 換到**另一個本機**碟當 store（§3）；NAS 不行（lchown） |

---

## 專案結構

```
Rasdaman/
├── README.md                     # 本標準作業流程 (SOP)
├── Dockerfile                    # all-in-one image（與機器無關）
├── scripts/
│   ├── build-install.sh          # build 時：起 postgres → 從本地 .deb 裝 rasdaman
│   └── entrypoint.sh             # 啟動時：起 postgres → 起 rasdaman + Petascope
├── examples/wcst_import/         # 資料匯入 ingredients 範例 + 說明
└── notebooks/                    # Python notebook（WCS/WCPS 互動）+ 環境說明
```
