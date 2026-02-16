from __future__ import annotations

import logging
from typing import Optional

import geopandas as gpd

log = logging.getLogger(__name__)


def read_geodata(input_path: str, layer: Optional[str] = None, force_epsg: Optional[int] = None,
                 max_rows: Optional[int] = None) -> gpd.GeoDataFrame:
    """
    Uses pyogrio via geopandas when available for speed.
    """
    log.info(f"Extract: reading {input_path}" + (f" (layer={layer})" if layer else ""))

    gdf = gpd.read_file(input_path, layer=layer)

    if force_epsg is not None:
        if gdf.crs is None:
            log.warning(f"Input has no CRS; forcing EPSG:{force_epsg}")
            gdf = gdf.set_crs(epsg=force_epsg)
        else:
            log.info(f"Input CRS present ({gdf.crs}); ignoring force_epsg")

    if max_rows is not None:
        gdf = gdf.head(max_rows)

    log.info(f"Extract: rows={len(gdf):,}, cols={len(gdf.columns)}")
    return gdf
