# GEE Code Editor Tutorial: VIIRS Night Lights over Taiwan

This tutorial shows how to reproduce the GEE notebook example in the official
Google Earth Engine Code Editor using JavaScript.

本教學說明如何於 Google Earth Engine 官方 Code Editor（網頁介面）中，
以 JavaScript 重現 GEE notebook（[`GEE/GEE.ipynb`](../GEE.ipynb)）之夜間燈光範例。
Code Editor 為 GEE 之原生開發介面，無須安裝任何環境，適合快速試驗與參數調整；
Python notebook 版本則適合與其他資料處理流程整合。兩者呼叫相同之後端運算。

Code file:

```text
01_viirs_night_lights_taiwan.js
```

## 1. Open GEE Code Editor

Go to:

```text
https://code.earthengine.google.com/
```

Sign in with an account that has Earth Engine access.

以具備 Earth Engine 存取權限之 Google 帳號登入
（申請方式參見 [`GEE/GEE.ipynb`](../GEE.ipynb) 之認證章節）。

## 2. Create a New Script

In the left panel, create a new script and give it a name such as:

```text
viirs_night_lights_taiwan
```

於左側面板建立新腳本並命名。腳本儲存於 GEE 雲端之個人 repository，可隨時回存與分享。

## 3. Copy the JavaScript Code

Open `01_viirs_night_lights_taiwan.js`, copy all code, and paste it into the
GEE Code Editor script panel.

開啟 `01_viirs_night_lights_taiwan.js`，複製全部程式碼並貼入 Code Editor 之腳本面板。

## 4. Run the Script

Click `Run`.

The map should center on Taiwan and show the 2023 annual mean VIIRS night lights.
Brighter areas correspond to higher nighttime radiance.

點擊 `Run` 後，地圖將置中於台灣並顯示 2023 年 VIIRS 夜間燈光之年平均影像；
亮度愈高代表夜間輻射值愈大。所有運算均於 Google 伺服器端執行，
本地瀏覽器僅接收渲染後之圖磚。

## 5. Main Steps in the Code

The script follows the same workflow as the notebook:

1. Define a Taiwan region of interest.
2. Load the VIIRS monthly night lights ImageCollection.
3. Filter the collection by region and date.
4. Select the `avg_rad` band.
5. Compute the 2023 annual mean image.
6. Mask pixels with very low radiance.
7. Add the result to the map.
8. Optionally export the raster to Google Drive.

腳本流程與 notebook 版本一致：定義台灣範圍框（ROI）→ 載入 VIIRS 月合成
夜間燈光影像集合 → 依空間與時間篩選 → 選取 `avg_rad`（平均輻射亮度）波段
→ 計算 2023 年平均影像（降低單月雲層與雜訊之影響）→ 遮罩低輻射值區域
→ 疊加至地圖，並可選擇性匯出至 Google Drive。

## 6. Change the Parameters

To analyze another year, update:

```js
var startDate = '2023-01-01';
var endDate = '2024-01-01';
```

To change the visible brightness range, update:

```js
min: 1,
max: 60
```

To make the mask stricter or looser, update:

```js
var lightMask = annualMean.gt(0.1);
```

參數調整說明：`startDate`／`endDate` 控制分析年度（`filterDate` 之結束日期為
排除式）；`min`／`max` 控制視覺化之亮度範圍；`gt(0.1)` 之門檻值控制遮罩之
嚴格程度——調高門檻僅保留較亮之區域。

## 7. Export Result

The export block is included but commented out. To export the image, remove the
comment markers around `Export.image.toDrive(...)`, run the script, then start
the task from the `Tasks` tab.

匯出區塊預設為註解狀態。如需匯出影像，取消 `Export.image.toDrive(...)` 周圍之
註解後重新執行，並於右側 `Tasks` 分頁啟動匯出工作；完成後檔案將出現於
Google Drive。
