from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import geopandas as gpd
import pandas as pd
from shapely.geometry import box
from shapely.validation import make_valid

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class TransformSpec:
    target_epsg: int = 4326
    clip_bbox: Optional[str] = None  # "minx,miny,maxx,maxy" in target CRS
    require_valid_geom: bool = True
    simplify_tolerance: Optional[float] = None


def _parse_bbox(bbox_str: str) -> tuple[float, float, float, float]:
    parts = [p.strip() for p in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError('clip_bbox must be "minx,miny,maxx,maxy"')
    return tuple(float(x) for x in parts)  # type: ignore


def normalize_columns(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    # Lowercase, snake-ish
    cols = []
    for c in gdf.columns:
        if c == gdf.geometry.name:
            cols.append(c)
        else:
            cols.append(
                c.strip()
                 .lower()
                 .replace(" ", "_")
                 .replace("-", "_")
            )
    gdf.columns = cols
    return gdf


def add_derived_fields(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    # Example: area/length in meters by projecting to EPSG:3857 temporarily
    try:
        gdf_m = gdf.to_crs(epsg=3857)
        gdf["area_m2"] = gdf_m.geometry.area
        gdf["length_m"] = gdf_m.geometry.length
    except Exception:
        # some geometry types may not support in a meaningful way
        pass
    return gdf


def validate_and_fix_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    # Drop empty geometry rows
    before = len(gdf)
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()
    dropped = before - len(gdf)
    if dropped:
        log.warning(f"Transform: dropped {dropped:,} empty/null geometries")

    # Fix invalid geometries
    invalid_mask = ~gdf.geometry.is_valid
    invalid_count = int(invalid_mask.sum())
    if invalid_count:
        log.warning(f"Transform: fixing {invalid_count:,} invalid geometries with make_valid()")
        gdf.loc[invalid_mask, gdf.geometry.name] = gdf.loc[invalid_mask, gdf.geometry.name].apply(make_valid)

    # Re-check
    still_invalid = int((~gdf.geometry.is_valid).sum())
    if still_invalid:
        log.warning(f"Transform: {still_invalid:,} geometries still invalid after fix")
    return gdf


def apply_transformations(gdf: gpd.GeoDataFrame, spec: TransformSpec) -> gpd.GeoDataFrame:
    log.info("Transform: start")

    # Ensure CRS
    if gdf.crs is None:
        raise ValueError("Input CRS is missing. Provide input_crs in config/env or fix the source dataset.")

    # Normalize schema
    gdf = normalize_columns(gdf)

    # Reproject
    if int(gdf.crs.to_epsg() or -1) != spec.target_epsg:
        log.info(f"Transform: reproject {gdf.crs} -> EPSG:{spec.target_epsg}")
        gdf = gdf.to_crs(epsg=spec.target_epsg)

    # Validate/repair
    if spec.require_valid_geom:
        gdf = validate_and_fix_geometries(gdf)

    # Clip
    if spec.clip_bbox:
        minx, miny, maxx, maxy = _parse_bbox(spec.clip_bbox)
        clip_poly = box(minx, miny, maxx, maxy)
        before = len(gdf)
        gdf = gdf[gdf.geometry.intersects(clip_poly)].copy()
        log.info(f"Transform: clip kept {len(gdf):,}/{before:,} rows")

    # Simplify
    if spec.simplify_tolerance is not None:
        log.info(f"Transform: simplify tol={spec.simplify_tolerance}")
        gdf[gdf.geometry.name] = gdf.geometry.simplify(spec.simplify_tolerance, preserve_topology=True)

    # Derived fields
    gdf = add_derived_fields(gdf)

    # Basic dedupe example (optional): if you have an id field
    # if "id" in gdf.columns: gdf = gdf.drop_duplicates(subset=["id"])

    # Ensure plain pandas dtypes where possible (avoid weird objects)
    for c in gdf.columns:
        if c != gdf.geometry.name and gdf[c].dtype == "object":
            # try best-effort to keep as is; you can enforce schema here
            pass

    log.info(f"Transform: done rows={len(gdf):,}")
    return gdf
