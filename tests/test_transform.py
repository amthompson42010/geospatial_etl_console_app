import geopandas as gpd
from shapely.geometry import Polygon
from geospatial_etl.transform import TransformSpec, apply_transformations

def test_transform_reproject_and_valid():
    poly = Polygon([(0,0),(1,0),(1,1),(0,1),(0,0)])
    gdf = gpd.GeoDataFrame({"name":["a"]}, geometry=[poly], crs="EPSG:4326")

    out = apply_transformations(gdf, TransformSpec(target_epsg=3857, require_valid_geom=True))
    assert out.crs.to_epsg() == 3857
    assert len(out) == 1
