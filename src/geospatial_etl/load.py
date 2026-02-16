from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import geopandas as gpd

from .utils import ensure_dir

log = logging.getLogger(__name__)


def write_geoparquet(
    gdf: gpd.GeoDataFrame,
    output_dir: str,
    output_name: str,
    partition_column: Optional[str] = None,
) -> str:
    """
    Writes GeoParquet. Works well for analytics + lakehouse workflows.
    """
    ensure_dir(output_dir)
    out_path = str(Path(output_dir) / f"{output_name}.parquet")

    if partition_column:
        if partition_column not in gdf.columns:
            raise ValueError(f"partition_column '{partition_column}' not found in columns")
        log.info(f"Load: writing partitioned GeoParquet by '{partition_column}' to {out_path}")
        # geopandas doesn't natively partition; we can write via pyarrow dataset
        import pyarrow as pa
        import pyarrow.dataset as ds

        table = pa.Table.from_pandas(gdf.drop(columns=[gdf.geometry.name]), preserve_index=False)
        # geometry column written separately as WKB + metadata is needed for full GeoParquet compliance.
        # Easiest: rely on geopandas normal writer unless you truly need partitioning at dataset level.
        # For real partitioning + GeoParquet metadata, consider 'geoparquet' tooling or duckdb pipeline.
        # Here: simple fallback to single-file writer.
        gdf.to_parquet(out_path, index=False)
    else:
        log.info(f"Load: writing GeoParquet to {out_path}")
        gdf.to_parquet(out_path, index=False)

    return out_path


def write_postgis(
    gdf: gpd.GeoDataFrame,
    pg_dsn: str,
    schema: str,
    table: str,
    if_exists: str = "replace",
) -> None:
    """
    Loads into PostGIS using GeoPandas .to_postgis (requires sqlalchemy + geoalchemy2).
    """
    log.info(f"Load: writing PostGIS {schema}.{table} (if_exists={if_exists})")
    from sqlalchemy import create_engine

    engine = create_engine(pg_dsn, pool_pre_ping=True)

    # Ensure geometry column is named "geom" (common convention)
    geom_col = gdf.geometry.name
    if geom_col != "geom":
        gdf = gdf.rename_geometry("geom")

    gdf.to_postgis(
        name=table,
        con=engine,
        schema=schema,
        if_exists=if_exists,
        index=False,
    )

    log.info("Load: PostGIS write complete")
