
# os.environ['USE_PYGEOS'] = '0'

import numpy as np
import pandas as pd
import geopandas as gpd

from shapely import wkt
from shapely.geometry import Point

def validate_geometry_label(df, geometry_label, verbose='False'):

    # Trata verbose...
    def depuracao(texto):
        if verbose.upper() == 'TRUE':
            print(texto)

    if geometry_label not in df.columns:
        depuracao('(validate_geometry_label)\n df supostamente gegdaláfico sem coluna geometry_label.')
    else:
        try:
            df[geometry_label] = df[geometry_label].apply(wkt.loads)
            df = gpd.GeoDataFrame(df, geometry=geometry_label)
            if(df.crs is None):
                df.crs = {'init': 'epsg:4618', 'no_defs': True}
        except:
            depuracao('(validate_geometry_label)\n Não foi possível criar a coluna geometry de df.')

    return df

def read_geo_generico(
        file_path,
        encoding='utf-8',
        index_col=0,
        usecols=None,
        geometry_label='geometry',
        sep=',',
        verbose='False',
):
    # Trata verbose...
    def depuracao(texto):
        if verbose.upper() == 'TRUE':
            print(texto)

    if(file_path.endswith('.csv')):
        depuracao('(read_geo_generico)\n Leitura de arquivo csv.')
        df = pd.read_csv(file_path, encoding=encoding, index_col=index_col, usecols=usecols, sep=sep)
        df = validate_geometry_label(df, geometry_label, verbose)

    elif(file_path.endswith('.xls') or file_path.endswith('.xlsx')):
        depuracao('(read_geo_generico)\n Leitura de arquivo xls ou xlsx.')
        df = pd.read_excel(open(file_path, 'rb'), index_col=index_col, usecols=usecols)
        df = validate_geometry_label(df, geometry_label, verbose)

    elif(file_path.endswith('.shp') or file_path.endswith('.json') or file_path.endswith('.geojson')):
        depuracao('(read_geo_generico)\n Leitura de arquivo shp ou json.')
        df = gpd.read_file(file_path)

    elif(file_path.endswith('.kml')):
        depuracao('(read_geo_generico)\n Leitura de arquivo kml.')
        gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
        df = gpd.read_file(filename=file_path, driver='KML')

    else:
        depuracao('(read_geo_generico)\n Exception "input_format".')
        raise Exception("input_format: extensão inesperada. Esperado: csv, xls, xlsx, shp, json, kml.")

    return df

def gera_quadrados_simples(resolucao, lat_min, long_min, lat_max, long_max, verbose) -> pd.DataFrame:

    # Trata verbose...
    def depuracao(texto):
        if verbose.upper() == 'TRUE':
            print(texto)

    depuracao('(gera_quadrados_simples)\n Gerar o grid "sem qualquer otimização"...')
    list_longitude = [
        x for x in np.arange(long_min - resolucao, long_max + 1.2*resolucao, resolucao)
    ]
    list_latitude = [
        x for x in np.arange(lat_min - resolucao, lat_max + 1.2*resolucao, resolucao)
    ]

    list_points = []
    for x in list_longitude:
        for y in list_latitude:
            list_points.append(Point([x, y]))

    depuracao('(gera_quadrados_simples)\n Criar novo df com os pontos do grid "sem qualquer otimização"...')
    gdf = gpd.GeoDataFrame(list_points, columns=['center_point'])

    depuracao('(gera_quadrados_simples)\n Adicionar coluna "envelope"...')
    gdf['envelope'] = [x.buffer(resolucao/2).envelope for x in gdf['center_point']]

    return gdf

def gera_quadrados_simples_from_df(resolucao, df, verbose) -> pd.DataFrame:

    # Trata verbose...
    def depuracao(texto):
        if verbose.upper() == 'TRUE':
            print(texto)

    depuracao('(gera_quadrados_simples_from_df)\n Obter extremos de interesse...')
    lat_min = df.bounds['miny'].min()
    long_min = df.bounds['minx'].min()
    lat_max = df.bounds['maxy'].max()
    long_max = df.bounds['maxx'].max()

    return gera_quadrados_simples(resolucao, lat_min, long_min, lat_max, long_max, verbose)
