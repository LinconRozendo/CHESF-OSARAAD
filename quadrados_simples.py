import os
os.environ['USE_PYGEOS'] = '0'
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from shapely.ops import cascaded_union
from shapely import wkt
import json


def gera_quadrados_simples(resolucao, shapefile_path) -> pd.DataFrame:
    
    
    if shapefile_path.endswith('.csv'):
        df = pd.read_csv(shapefile_path)
        sf = gpd.GeoDataFrame(df, geometry=df['geometry'].map(wkt.loads))
    else:
        sf = gpd.read_file(shapefile_path)
    
    lat_min = sf.bounds['miny'].min()
    long_min = sf.bounds['minx'].min()

    lat_max = sf.bounds['maxy'].max()
    long_max = sf.bounds['maxx'].max()

    list_longitude = [
        x for x in np.arange(long_min - 0.2*resolucao, long_max + 1.2*resolucao, resolucao)
    ]
    list_latitude = [
        x for x in np.arange(lat_min - 0.2*resolucao, lat_max + 1.2*resolucao, resolucao)
    ]

    list_coordenadas = []
    for x in list_longitude:
        for y in list_latitude:
            list_coordenadas.append(tuple([x, y]))

    list_Points = [Point(x) for x in list_coordenadas]
    gdf = gpd.GeoDataFrame(list_Points, columns=['center_point'])

    raio = resolucao/2
    gdf['envelope'] = [x.buffer(raio).envelope for x in gdf['center_point']]

    return gdf, sf


if __name__ == '__main__':
    quadrados = gera_quadrados(resolucao = resolucao)