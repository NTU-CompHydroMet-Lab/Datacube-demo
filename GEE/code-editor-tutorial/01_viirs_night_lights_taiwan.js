// Google Earth Engine Code Editor 教學
// 範例：2023 年台灣 VIIRS 夜間燈光
//
// 使用資料集：
// NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG
//
// 最快方式：開啟 https://code.earthengine.google.com/b7e3a1999822da32ab31169fb049dc20
// 進入範例 script 後，按下 Run 即可執行。

// 1. 定義研究範圍。
// 這個 bounding box 涵蓋台灣本島與周邊島嶼。
var roi = ee.Geometry.Rectangle([119.3, 21.8, 122.1, 25.4]);

// 2. 設定分析時間。
// 在 Earth Engine 中，filterDate 會包含起始日期，但不包含結束日期。
var startDate = '2023-01-01';
var endDate = '2024-01-01';

// 3. 載入 VIIRS monthly night lights 影像集合。
var viirsCollection = ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG');

// 4. 篩選資料、選擇亮度波段、計算年度平均，並裁切到台灣範圍。
var annualMean = viirsCollection
  .filterBounds(roi)
  .filterDate(startDate, endDate)
  .select('avg_rad')
  .mean()
  .clip(roi);

// 5. 遮罩低亮度像素。
// 如果只想保留更亮的夜間燈光區域，可以把門檻值調高。
var lightMask = annualMean.gt(0.1);
var nightLights = annualMean.updateMask(lightMask);

// 6. 設定地圖顯示樣式。
var nightLightsVis = {
  min: 1,
  max: 60,
  palette: ['050505', '4d2600', 'b35900', 'ff9900', 'ffdb4d', 'ffffff']
};

// 7. 將圖層加入 Code Editor 的地圖。
Map.setCenter(120.9, 23.6, 7);
Map.setOptions('HYBRID');
Map.addLayer(roi, {color: '00ffff'}, 'Taiwan ROI', false);
Map.addLayer(nightLights, nightLightsVis, 'VIIRS 2023 Night Lights');

// 8. 在 Console 印出資料資訊，方便確認影像集合與輸出影像是否正確。
print('VIIRS collection after filtering:', viirsCollection
  .filterBounds(roi)
  .filterDate(startDate, endDate));
print('Annual mean night lights image:', annualMean);

// 9. 選擇性：匯出結果到 Google Drive。
// 若要匯出，請移除下方區塊的註解，重新執行程式，
// 再到 Code Editor 右側的 Tasks 分頁啟動匯出任務。
/*
Export.image.toDrive({
  image: nightLights,
  description: 'viirs_2023_night_lights_taiwan',
  folder: 'GEE_exports',
  fileNamePrefix: 'viirs_2023_night_lights_taiwan',
  region: roi,
  scale: 500,
  maxPixels: 1e13
});
*/
