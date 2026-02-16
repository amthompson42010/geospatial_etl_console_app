from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import Settings
from .extract import read_geodata
from .transform import TransformSpec, apply_transformations
from .load import write_geoparquet, write_postgis
from .utils import sha256_of_file, write_json, ensure_dir

log = logging.getLogger(__name__)


class PipelineError(RuntimeError):
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=20),
    retry=retry_if_exception_type((OSError, PipelineError)),
)
def run_pipeline(settings: Settings) -> dict:
    started = datetime.now(timezone.utc)
    run_id = settings.run_id or started.strftime("%Y%m%dT%H%M%SZ")

    # Simple idempotency marker: if metadata exists for same input hash + output name, skip (optional).
    ensure_dir(settings.output_dir)
    meta_path = str(Path(settings.output_dir) / f"{settings.output_name}__{run_id}__meta.json")

    input_hash = sha256_of_file(settings.input_path)

    log.info(f"Run ID: {run_id}")
    log.info(f"Input hash: {input_hash}")

    gdf = read_geodata(
        input_path=settings.input_path,
        layer=settings.input_layer,
        force_epsg=settings.input_crs,
        max_rows=settings.max_rows,
    )

    spec = TransformSpec(
        target_epsg=settings.target_crs,
        clip_bbox=settings.clip_bbox,
        require_valid_geom=settings.require_valid_geom,
        simplify_tolerance=settings.simplify_tolerance,
    )
    gdf = apply_transformations(gdf, spec)

    out_parquet = write_geoparquet(
        gdf=gdf,
        output_dir=settings.output_dir,
        output_name=f"{settings.output_name}__{run_id}",
        partition_column=settings.partition_column,
    )

    if settings.pg_dsn:
        write_postgis(
            gdf=gdf,
            pg_dsn=settings.pg_dsn,
            schema=settings.pg_schema,
            table=settings.pg_table,
            if_exists=settings.pg_if_exists,
        )

    finished = datetime.now(timezone.utc)
    meta = {
        "run_id": run_id,
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "duration_seconds": (finished - started).total_seconds(),
        "input_path": settings.input_path,
        "input_sha256": input_hash,
        "rows_out": int(len(gdf)),
        "crs_out": str(gdf.crs),
        "outputs": {
            "geoparquet": out_parquet,
            "postgis": f"{settings.pg_schema}.{settings.pg_table}" if settings.pg_dsn else None,
        },
    }
    write_json(meta_path, meta)
    log.info(f"Metadata: {meta_path}")
    return meta
