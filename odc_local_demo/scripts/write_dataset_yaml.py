from __future__ import annotations

import argparse
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import rasterio
import yaml


FILENAME_RE = re.compile(r"^(?P<label>[^_]+)_(?P<start>\d{8})-(?P<end>\d{8})\.tif$", re.IGNORECASE)


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y%m%d").replace(tzinfo=timezone.utc)


def geometry_from_dataset(src: rasterio.io.DatasetReader) -> dict:
    bounds = src.bounds
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [bounds.left, bounds.bottom],
                [bounds.left, bounds.top],
                [bounds.right, bounds.top],
                [bounds.right, bounds.bottom],
                [bounds.left, bounds.bottom],
            ]
        ],
    }


def dataset_doc(path: Path, product: str, measurement: str) -> dict:
    match = FILENAME_RE.match(path.name)
    if not match:
        raise ValueError(
            f"{path.name} does not match expected pattern '<label>_YYYYMMDD-YYYYMMDD.tif'"
        )

    start = parse_date(match.group("start"))
    end = parse_date(match.group("end"))
    label = match.group("label")

    with rasterio.open(path) as src:
        crs = src.crs.to_string() if src.crs else None
        geometry = geometry_from_dataset(src)
        grids = {
            "default": {
                "shape": [src.height, src.width],
                "transform": list(src.transform),
            }
        }

    return {
        "$schema": "https://schemas.opendatacube.org/dataset",
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{product}:{path.name}")),
        "product": {"name": product},
        "crs": crs,
        "geometry": geometry,
        "grids": grids,
        "properties": {
            "odc:processing_datetime": datetime.now(timezone.utc).isoformat(),
            "odc:file_format": "GeoTIFF",
            "odc:product": product,
            "datetime": start.isoformat(),
            "dtr:start_datetime": start.isoformat(),
            "dtr:end_datetime": end.isoformat(),
            "region_code": label,
        },
        "measurements": {
            measurement: {
                "path": str(path),
                "band": 1,
            }
        },
        "lineage": {},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--product", required=True)
    parser.add_argument("--measurement", required=True)
    args = parser.parse_args()

    args.dataset_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for tif_path in sorted(args.data_dir.glob("*.tif")):
        doc = dataset_doc(tif_path, args.product, args.measurement)
        yaml_path = args.dataset_dir / f"{tif_path.stem}.yaml"
        with yaml_path.open("w", encoding="utf-8") as stream:
            yaml.safe_dump(doc, stream, sort_keys=False)
        print(f"Wrote {yaml_path}")
        count += 1

    if count == 0:
        print(f"No .tif files found in {args.data_dir}")


if __name__ == "__main__":
    main()
