from __future__ import annotations

import sys

from datacube import Datacube


PRODUCT = "s2_landcover_taiwan"
MEASUREMENT = "classification"
OUTPUT_CRS = "EPSG:32651"
RESOLUTION = (-10, 10)
SAMPLE_SIZE = 1000


def sample_queries_from_dataset(dataset) -> list[dict]:
    """Build small load queries across the indexed dataset extent."""
    coords = dataset.extent.exterior.coords
    xs = [point.x if hasattr(point, "x") else point[0] for point in coords]
    ys = [point.y if hasattr(point, "y") else point[1] for point in coords]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    half = SAMPLE_SIZE / 2

    queries = []
    for x_frac in (0.2, 0.35, 0.5, 0.65, 0.8):
        for y_frac in (0.2, 0.35, 0.5, 0.65, 0.8):
            center_x = min_x + (max_x - min_x) * x_frac
            center_y = min_y + (max_y - min_y) * y_frac
            queries.append(
                {
                    "x": (center_x - half, center_x + half),
                    "y": (center_y - half, center_y + half),
                }
            )
    return queries


def main() -> int:
    dc = Datacube(app="check_odc_demo")

    products = dc.list_products()
    if PRODUCT not in products.index:
        print(f"ERROR: product '{PRODUCT}' is not indexed.")
        return 1

    datasets = list(dc.index.datasets.search(product=PRODUCT))
    print(f"Product: {PRODUCT}")
    print(f"Indexed datasets: {len(datasets)}")

    if not datasets:
        print(f"ERROR: no {PRODUCT} datasets are indexed.")
        return 1

    data = None
    for query in sample_queries_from_dataset(datasets[0]):
        print(f"Trying sample x: {query['x']}")
        print(f"Trying sample y: {query['y']}")
        sample = dc.load(
            product=PRODUCT,
            measurements=[MEASUREMENT],
            x=query["x"],
            y=query["y"],
            crs=OUTPUT_CRS,
            output_crs=OUTPUT_CRS,
            resolution=RESOLUTION,
        )
        if MEASUREMENT in sample and bool(sample[MEASUREMENT].notnull().any()):
            data = sample
            break

    if data is None:
        print("ERROR: loaded samples contain only NoData.")
        return 1

    print(data)

    if MEASUREMENT not in data:
        print(f"ERROR: {MEASUREMENT} measurement was not loaded.")
        return 1

    print("ODC demo check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
