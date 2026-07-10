# GEE Code Editor Tutorial: VIIRS Night Lights over Taiwan

This tutorial shows how to reproduce the GEE notebook example in the official
Google Earth Engine Code Editor using JavaScript.

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

## 2. Create a New Script

In the left panel, create a new script and give it a name such as:

```text
viirs_night_lights_taiwan
```

## 3. Copy the JavaScript Code

Open `01_viirs_night_lights_taiwan.js`, copy all code, and paste it into the
GEE Code Editor script panel.

## 4. Run the Script

Click `Run`.

The map should center on Taiwan and show the 2023 annual mean VIIRS night lights.
Brighter areas correspond to higher nighttime radiance.

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

## 7. Export Result

The export block is included but commented out. To export the image, remove the
comment markers around `Export.image.toDrive(...)`, run the script, then start
the task from the `Tasks` tab.


