import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from shapely.ops import cascaded_union

PB_shapfile = 'https://raw.githubusercontent.com/CEARDados/mmp/master/Dados/PB_munic%C3%ADpios.json'


def gera_quadrados(resolucao, shapfile_path=PB_shapfile, init_lat_lon=None) -> pd.DataFrame:

    casas_decimais = len(str(float(resolucao)).split('.')[1]) + 1

    sf = gpd.read_file(shapfile_path)

    if init_lat_lon:
        lat_min = np.float64(init_lat_lon[0])
        long_min = np.float64(init_lat_lon[1])
    else:
        lat_min = sf.bounds['miny'].min()
        long_min = sf.bounds['minx'].min()

    long_max = sf.bounds['maxx'].max()
    lat_max = sf.bounds['maxy'].max()

    list_longitude = [round(x, casas_decimais)
                      for x in np.arange(long_min, long_max + resolucao, resolucao)]
    list_latitude = [round(x, casas_decimais)
                     for x in np.arange(lat_min, lat_max + resolucao, resolucao)]

    list_coordenadas = []
    for x in list_longitude:
        for y in list_latitude:
            list_coordenadas.append(tuple([x, y]))

    list_Points = [Point(x) for x in list_coordenadas]
    df_geometria = gpd.GeoDataFrame(list_Points, columns=['center_point'])

    raio = resolucao/2
    df_geometria['envelope'] = [x.buffer(raio).envelope
                                for x in df_geometria['center_point']]

    def is_envelope_ok(polygon):
        for nome_municipio, polygon_municipio in zip(sf['Nome_Munic'],
                                                     sf['geometry']):
            if(polygon.intersects(polygon_municipio)):
                return (True, nome_municipio)
        return (False, '')

    list_envelope_ok_municipio = [is_envelope_ok(x)
                                  for x in df_geometria['envelope']]
    list_ok = [x[0] for x in list_envelope_ok_municipio]
    list_municipio = [x[1] for x in list_envelope_ok_municipio]

    df_geometria['Nome_Munic'] = list_municipio

    df_geometria_ok = df_geometria[list_ok].copy()
    df_geometria_ok['geometry'] = df_geometria_ok['envelope']
    quadrados = gpd.GeoDataFrame(df_geometria_ok)

    limites = gpd.GeoDataFrame(
        geometry=gpd.GeoSeries(cascaded_union(sf['geometry']))
    )

    quadrado_recortado = gpd.GeoDataFrame(
        gpd.overlay(limites, quadrados, how='intersection')
    )

    quadrado_recortado['centroid'] = quadrado_recortado['geometry'].centroid

    return pd.DataFrame(quadrado_recortado)


if __name__ == '__main__':
    quadrados = gera_quadrados(0.05, './paraiba/Municipios.shp')
    quadrados.to_pickle('./QuadradoRecortado.pkl')
