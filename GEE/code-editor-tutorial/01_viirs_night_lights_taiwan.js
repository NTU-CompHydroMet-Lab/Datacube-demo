// Google Earth Engine Code Editor tutorial
// Example: 2023 VIIRS night lights over Taiwan
//
// Dataset:
// NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG
//
// Paste this script into https://code.earthengine.google.com/ and click Run.

// 1. Define the region of interest.
// This bounding box covers Taiwan and nearby islands.
var roi = ee.Geometry.Rectangle([119.3, 21.8, 122.1, 25.4]);

// 2. Set the analysis period.
// In Earth Engine, filterDate uses a start date and an exclusive end date.
var startDate = '2023-01-01';
var endDate = '2024-01-01';

// 3. Load the VIIRS monthly night lights collection.
var viirsCollection = ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG');

// 4. Filter, select the radiance band, compute annual mean, and clip to Taiwan.
var annualMean = viirsCollection
  .filterBounds(roi)
  .filterDate(startDate, endDate)
  .select('avg_rad')
  .mean()
  .clip(roi);

// 5. Mask very low radiance values.
// Increase this threshold to keep only brighter nighttime-light pixels.
var lightMask = annualMean.gt(0.1);
var nightLights = annualMean.updateMask(lightMask);

// 6. Set visualization style.
var nightLightsVis = {
  min: 1,
  max: 60,
  palette: ['050505', '4d2600', 'b35900', 'ff9900', 'ffdb4d', 'ffffff']
};

// 7. Display layers in the Code Editor map.
Map.setCenter(120.9, 23.6, 7);
Map.setOptions('HYBRID');
Map.addLayer(roi, {color: '00ffff'}, 'Taiwan ROI', false);
Map.addLayer(nightLights, nightLightsVis, 'VIIRS 2023 Night Lights');

// 8. Print useful information to the Console.
print('VIIRS collection after filtering:', viirsCollection
  .filterBounds(roi)
  .filterDate(startDate, endDate));
print('Annual mean night lights image:', annualMean);

// 9. Optional export to Google Drive.
// To export, uncomment this block, run the script, then start the task
// from the Tasks tab in the Code Editor.
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

