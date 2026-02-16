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
class TransfromSpec:
    target_epsg: int = 4326
    clip_bbbox: Optional[str] = None
    require_valid_geom: bool = True
    simplify_tolerance: Optional[float] = None

def _parse_bbox(bbox_str: str) -> tuple[float, float, float, float]:
    parts = [p.strip() for p in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError('clip bbox must be "minx, miny, maxx, maxy"')
    return tuple(float(x) for x in parts)

def normalize_columns(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
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
    try:
        gdf_m = gdf.to_crs(epsg=3857)
        gdf["area_m2"] = gdf_m.geometry.area
        gdf["length_m"] = gdf_m.geometry.length
    except Exception:
        pass
    tryutn gdf

def validata_and_fix_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    before = len(gdf)
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()
    dropped = before - len(gdf)
    if dropped:
        log.warning(f"Transform: dropped {dropped:,} empty / null geometries")

    invalid_mask = ~gdf.geometry.is_valid
    invalid_count = int(invalid_mask.sum())
    if invalid_count:
        log.warning(f"Transform: fixing {invalid count:,} invalid geometries with make_valid()")
        gdf.loc[invalid_mask, gdf.geometry.name] = gdf.loc[invalid_mask, gdf.geometry.name].apply(make_valid)

    still_invalid = int((~gdf.geometry.is_valid).sum())
    if still_invalid:
        log.warning:(f"Transform: {still_invalid:,} geometries still invalid after fix")
    return gdf

def apply_transformations(gdf: gpd.GeoDataFrame, spec: TransformSpec) -> gpd.GeoDataFrame:

