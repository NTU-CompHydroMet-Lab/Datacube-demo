from __future__ import annotations

import io
import os
import re
from pathlib import Path

import numpy as np
from datacube import Datacube
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from PIL import Image
from rasterio.warp import transform_bounds


PRODUCT = "s2_landcover_taiwan"
MEASUREMENT = "classification"
OUTPUT_CRS = "EPSG:32651"
RESOLUTION = (-10, 10)
TAIPEI_BBOX_LONLAT = (121.40, 24.95, 121.70, 25.20)
DATA_DIR = Path("/workspace/data")

CLASS_NAMES = {
    1: "Water",
    2: "Trees",
    4: "Flooded Vegetation",
    5: "Crops",
    7: "Built Area",
    8: "Bare Ground",
    9: "Snow/Ice",
    10: "Clouds",
    11: "Rangeland",
}

CLASS_COLORS = {
    1: (65, 155, 223, 205),
    2: (57, 125, 73, 205),
    4: (122, 135, 198, 205),
    5: (228, 150, 53, 205),
    7: (196, 40, 27, 215),
    8: (165, 155, 143, 205),
    9: (179, 159, 225, 205),
    10: (255, 255, 255, 190),
    11: (227, 226, 195, 205),
}

FILENAME_RE = re.compile(r"^[^_]+_(?P<start>\d{4})\d{4}-(?P<end>\d{4})\d{4}\.tif$", re.I)

app = FastAPI(title="ODC Land-Cover Demo")


def write_datacube_config() -> None:
    config_path = Path(os.environ.get("DATACUBE_CONFIG_PATH", "/root/.datacube.conf"))
    config_path.write_text(
        "\n".join(
            [
                "[datacube]",
                f"db_hostname: {os.environ.get('DB_HOSTNAME', 'postgres')}",
                f"db_database: {os.environ.get('DB_DATABASE', 'datacube')}",
                f"db_username: {os.environ.get('DB_USERNAME', 'datacube')}",
                f"db_password: {os.environ.get('DB_PASSWORD', 'datacube')}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def datacube() -> Datacube:
    write_datacube_config()
    return Datacube(app="odc_frontend_demo")


def available_years() -> list[int]:
    years = []
    for path in DATA_DIR.glob("*.tif"):
        match = FILENAME_RE.match(path.name)
        if match:
            years.append(int(match.group("start")))
    return sorted(set(years))


def taipei_query() -> dict[str, tuple[float, float]]:
    min_x, min_y, max_x, max_y = transform_bounds(
        "EPSG:4326",
        OUTPUT_CRS,
        *TAIPEI_BBOX_LONLAT,
        densify_pts=21,
    )
    return {"x": (min_x, max_x), "y": (min_y, max_y)}


def parse_classes(value: str | None) -> set[int]:
    if not value:
        return set(CLASS_NAMES)

    selected = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            code = int(item)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid class code: {item}") from exc
        if code not in CLASS_NAMES:
            raise HTTPException(status_code=400, detail=f"Unsupported class code: {code}")
        selected.add(code)
    return selected or set(CLASS_NAMES)


def load_classification(year: int):
    query = taipei_query()
    data = datacube().load(
        product=PRODUCT,
        measurements=[MEASUREMENT],
        time=(f"{year}-01-01", f"{year}-12-31"),
        x=query["x"],
        y=query["y"],
        crs=OUTPUT_CRS,
        output_crs=OUTPUT_CRS,
        resolution=RESOLUTION,
    )
    if MEASUREMENT not in data or data[MEASUREMENT].sizes.get("time", 0) == 0:
        raise HTTPException(status_code=404, detail=f"No indexed land-cover data for {year}")
    return data[MEASUREMENT].isel(time=0)


def rgba_image(classification, selected_classes: set[int], max_size: int = 1200) -> Image.Image:
    arr = classification.values
    if classification.y.values[0] < classification.y.values[-1]:
        arr = np.flipud(arr)

    rgba = np.zeros((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
    for code, color in CLASS_COLORS.items():
        if code in selected_classes:
            rgba[arr == code] = color

    image = Image.fromarray(rgba, mode="RGBA")
    image.thumbnail((max_size, max_size), Image.Resampling.NEAREST)
    return image


@app.get("/api/config")
def config():
    return {
        "bbox": {
            "west": TAIPEI_BBOX_LONLAT[0],
            "south": TAIPEI_BBOX_LONLAT[1],
            "east": TAIPEI_BBOX_LONLAT[2],
            "north": TAIPEI_BBOX_LONLAT[3],
        },
        "years": available_years(),
        "classes": [
            {
                "code": code,
                "name": CLASS_NAMES[code],
                "color": f"#{CLASS_COLORS[code][0]:02x}{CLASS_COLORS[code][1]:02x}{CLASS_COLORS[code][2]:02x}",
            }
            for code in CLASS_NAMES
        ],
    }


@app.get("/api/overlay.png")
def overlay(
    year: int = Query(..., description="Dataset start year, for example 2019"),
    classes: str | None = Query(None, description="Comma-separated class codes"),
):
    classification = load_classification(year)
    image = rgba_image(classification, parse_classes(classes))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return Response(buffer.getvalue(), media_type="image/png")


@app.get("/api/stats")
def stats(year: int = Query(...), classes: str | None = Query(None)):
    classification = load_classification(year)
    arr = classification.values
    selected = parse_classes(classes)
    pixel_area_m2 = 100
    rows = []
    for code in CLASS_NAMES:
        if code not in selected:
            continue
        pixel_count = int(np.count_nonzero(arr == code))
        rows.append(
            {
                "code": code,
                "name": CLASS_NAMES[code],
                "pixel_count": pixel_count,
                "area_km2": pixel_count * pixel_area_m2 / 1_000_000,
            }
        )
    return {"year": year, "stats": rows}


app.mount("/", StaticFiles(directory="/workspace/frontend/static", html=True), name="static")
