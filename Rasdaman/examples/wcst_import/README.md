# wcst_import 範例（資料匯入）

`wcst_import.sh` 是 rasdaman 透過 WCS-T 把 raster 檔（GeoTIFF/NetCDF/GRIB…）
匯入成 coverage 的工具，吃一份 **ingredients JSON** 描述「資料在哪、用什麼 recipe、CRS、波段」。

## 在容器內執行（petascope 有存取控制，需帳密）

```bash
# 1) 把 ingredients 複製進容器
podman cp examples/wcst_import/<your>.json rasdaman:/tmp/ing.json
#    （管理本容器前先：export CONTAINERS_STORAGE_CONF=/var/tmp/rasdaman-measure/storage.conf）

# 2) 在容器內建立 identity file（username:password）並執行
podman exec rasdaman bash -lc '
  printf "rasadmin:rasadmin" > /tmp/rasid && chmod 600 /tmp/rasid
  wcst_import.sh -i /tmp/rasid /tmp/ing.json
'
```

匯入後可在 notebook（或 GetCapabilities）看到新 coverage。

## 本目錄檔案

- **`mean_summer_airtemp.template.json`** — 官方內建、與 10.6.3 一起測過的**可動範本**
  （`map_mosaic` recipe + 地理參考 GeoTIFF）。其中 `PETASCOPE_URL` / `SECORE_URL` /
  `DATA_FOLDER_PATH` 是佔位字串，實際要替換成：
  - `service_url`: `http://localhost:8080/rasdaman/ows`
  - `crs_resolver`: `http://localhost:8080/rasdaman/def`
  - `default_crs`: `http://localhost:8080/rasdaman/def/crs/EPSG/0/4326`
- **`mr_demo.json`** — 手寫的 `general_coverage` 範例（示範結構）。在 10.6.3 上，資料寫入步驟
  會踩到一個 petascope NPE（coverage 定義會建立、但 tile 資料插入失敗）；保留作為結構參考。

## 實測學到的重點

1. **CRS 路徑要含 `/crs/`**：`…/rasdaman/def/crs/EPSG/0/4326`（少了 `/crs/` 會解析失敗）。
2. **`map_mosaic` 需要「有地理參考」的影像**。對沒有地理參考的純影像（如 `mr_1.tif`），
   會在 Index2D 上產生反向 j 軸而失敗；先用 `gdal_translate -a_srs EPSG:4326 -a_ullr …`
   加上地理參考即可。
3. **所有 OGC/WCS-T 請求都要帶 `rasadmin:rasadmin`**（petascope 預設啟用存取控制）。

## 你的真實資料

NAS 上的 `imerg_tw`、`Himawari_JP`、`datacube` 等多為有地理參考的 GeoTIFF/NetCDF，
之後唯讀掛進容器、依上面方式寫 ingredients（時間序列可用 `time_series_regular` /
`general_coverage` recipe）即可匯入。官方範本見容器內
`/opt/rasdaman/share/rasdaman/wcst_import/ingredients/`。

---

## 真實資料範例（Taiwan，已驗證可跑通）

| Ingredient | 資料源 | Coverage | 時間軸來源 | 備註 |
|---|---|---|---|---|
| `qpesums_maxdbz.json` | QPESUMS 雷達（MAXDBZ 反射率） | `qpesums_maxdbz_demo` | 檔名 regex | 用原始 2D nc（`data/*.nc`），非加了 time 維度的 `_with_time` 版 |
| `era5_tp.json` | ERA5 再分析（總降雨 tp） | `era5_tp_tw_demo` | netcdf 內建 `valid_time` | 先用 `subset_era5.py` 從 NAS 切台灣小範圍 |

輔助腳本：`subset_era5.py`（ERA5 台灣範圍 subset）、`qpesums_process_netcdf.py`（QPESUMS 加 time 維度，本範例未使用）。

### QPESUMS 匯入
```bash
podman exec rasdaman mkdir -p /tmp/qpesums_orig
podman cp examples/wcst_import/data/MREF3D21L.20120102.1730.nc rasdaman:/tmp/qpesums_orig/
podman cp examples/wcst_import/data/MREF3D21L.20120102.1740.nc rasdaman:/tmp/qpesums_orig/
podman cp examples/wcst_import/qpesums_maxdbz.json rasdaman:/tmp/ing.json
podman exec rasdaman bash -lc 'printf "rasadmin:rasadmin" >/tmp/rasid; /opt/rasdaman/bin/wcst_import.sh -i /tmp/rasid /tmp/ing.json'
```

### ERA5 匯入（資料在 NAS `/path/to/ERA5_nc_hourly`，先 subset 再匯）
```bash
podman exec rasdaman mkdir -p /tmp/era5
podman cp /path/to/ERA5_nc_hourly/tp/2019/tp_201909.nc rasdaman:/tmp/era5/tp_201909.nc
podman cp examples/wcst_import/subset_era5.py rasdaman:/tmp/subset_era5.py
podman exec rasdaman python3 /tmp/subset_era5.py            # 產生 /tmp/era5/tp_tw_small.nc（台灣, 24h）
podman cp examples/wcst_import/era5_tp.json rasdaman:/tmp/ing.json
podman exec rasdaman bash -lc '/opt/rasdaman/bin/wcst_import.sh -i /tmp/rasid /tmp/ing.json'
```

### 三個踩雷重點（真實資料常見）
1. **band 名要對上 nc 實際變數**（QPESUMS: `dataset1`=MAXDBZ、`dataset9`=降雨率 mm/hr）。
2. **3D coverage 必填 `tiling`**（錯誤訊息會給建議值）。
3. **時間軸來源二選一**：來自檔名 → 該軸設 `dataBound:false`（如 QPESUMS）；來自 netcdf 內建 time 變數 → 直接讀（如 ERA5）。

> `data/*.nc` 為樣本資料，已 gitignore（不進版控）。
