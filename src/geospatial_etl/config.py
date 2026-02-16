from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    input_path: str = Field(..., description="Path to input dataset (GeoJSON/SHP/GPKG/etc.)")
    input_layer: str | None = Field(default=None, description="Layer name for GPKG; optional")
    input_crs: int | None = Field(default=None, description="Force CRS EPSG if source lacks CRS")

    target_crs: int = Field(default=4326)
    clip_bbox: str | None = Field(default=None, description='Optional bbox "minx, miny, maxx, maxy" in target CRS')
    require_valid_geom: bool = Field(default=True)
    simplify_tolerance: float | None = Field(default=None, description="Optional simplify tolerance in target CRS units")

    output_dir: str = Field(default="data/out")
    output_name: str = Field(default="dataset")
    partition_column: str | None = Field(default=None, description="Optional partition column for parquet")

    pg_dsn: str | None = Field(default=None, description="SQLAlchemy DSN e.g. postgresql+psycopg2://...")
    pg_schema: str = Field(default="public")
    pg_table: str = Field(default="geodata")
    pg_if_exists: str = Field(default="replace", description="replace|append|fail")

    run_id: str | None = Field(default=None, description="Optional explicit run id")
    max_rows: int | None = Field(default=None, description="Optional limit rows for test runs")
