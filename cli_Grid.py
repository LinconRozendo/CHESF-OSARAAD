import click
import time
import datetime
import os

os.environ['USE_PYGEOS'] = '0'
import pandas as pd
from typing import Union
import geopandas as gpd
from shapely import wkt

from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import pandas as pd
import numpy as np
import glob
import json
from shapely.geometry import Point
from shapely.ops import cascaded_union, unary_union
import folium as fl
from shapely import wkt
import matplotlib.pyplot as plt

from quadrados_simples import gera_quadrados_simples
from quadrados_NE import gera_quadrados

GeoGenericoTypes = Union[gpd.GeoDataFrame, pd.DataFrame, str]




def __validate_geometry_label(df, geometry_label):

    if geometry_label not in df.columns:
        print('(format_converters.py: __validate_geometry_label) Aviso:')
        print('df supostamente geográfico sem coluna geometry_label.')
    else:
        try:
            df[geometry_label] = df[geometry_label].apply(wkt.loads)
            df = gpd.GeoDataFrame(df, geometry=geometry_label)
            if(df.crs is None):
                df.crs = {'init': 'epsg:4618', 'no_defs': True}
        except:
            print('(format_converters.py:__validate_geometry_label) Aviso:')
            print('Não foi possível criar a coluna geometry de df.')

    return df


def filter_and_sort_df(
        df,
        filter_df=[],
        sort_values=[],
        ascending=[]):
    """
    Filtra e/ou ordena um dataframe pandas a partir de um uma ou mais colunas 
    enviadas pelo usuário.

    Args:

    * df (DataFrame)

        DataFrame com os dados.

    * filter_df (list, optional, default([]))

        Lista de query's para filtrar o DataFrame.

    * sort_values (list, optional, default([]))

        Ordena a tabela lida de acordo com a hierarquia de colunas enviadas.

    * ascending (list, optional, default([]))

        Trabalha em conjunto com `sort_values`. 

        Deve ter uma lista de bool do mesmo tamanho que estabelece a ordem que
        deve ser usada para ordenar cada coluna hierarquicamente.

    Retorna:

    * O Dataframe após as operações solicitadas.
    """

    if type(sort_values) != list:
        sort_values = [sort_values]

    if type(ascending) != list:
        ascending = [ascending]

    if (sort_values != []):
        df = df.sort_values(by=sort_values, ascending=ascending)

    if type(filter_df) != list:
        filter_df = [filter_df]

    if(filter_df != []):
        # vai me ajudar na hr que eu quiser pegar as x primeiras ou ultimas
        # linhas do df organizado
        if 'number_of_rows' not in df.columns:
            df['number_of_rows'] = [x for x in range(1, len(df)+1)]

        if len(filter_df) > 1:
            for query in filter_df:
                df = df.query(query)
                # cria uma nova listagem para referência
                df['number_of_rows'] = [x for x in range(1, len(df)+1)]

        elif filter_df != ['']:
            df = df.query(filter_df[0])

    return df


def read_geo_generico(
        file_path,
        output_format,
        encoding='utf-8',
        index_col=0,
        usecols=None,
        filter_df=[],
        sort_values=[],
        ascending=[],
        geometry_label='geometry') -> GeoGenericoTypes:
    """
    Lê um dataframe pandas a partir de um arquivo csv, excel, shp e json sendo 
    possível aplicar o filtro solicitado e ordenar.

    Args:

    * filename (str)

        Caminho do arquivo com os dados.

    * output_format (str)

        Formato desejado para exportação dos dados do arquivo enviado.

    * encoding (str, optional, default('utf-8'))

        Codificação de caracteres utilizada no arquivo enviado. 

    * index_col (int, optional, default(0))

        Seta a coluna representada pelo valor enviado como índice. 

    * usecols ([type], optional, default(None))

        DataFrame com apenas as colunas enviadas. 

    * filter_df (list, optional, default([]))

        Uma lista de querys para filtrar o DataFrame.

    * sort_values (list, optional, default([]))

        Organiza os valores de acordo com a hierarquia de colunas enviadas.

    * ascending (list, optional, default([]))

        Trabalha em conjunto com `sort_values`. 

        Deve ter uma lista de bool do mesmo tamanho que estabelece a ordem que
        deve ser usada para ordenar cada coluna hierarquicamente.

    * geometry_label (str, optional, default('geometry'))

        Nome da coluna do dataframe que contem os polígonos. 

    Raises:

    * Exception: Extensão inesperada

        Permitidos: csv, xls, xlsx, shp, json, kml.

    * Exception: output_format

        Permitidos: pandas, geopandas ou geojson.

    Retorna:

    * Um DataFrame ou uma string JSON conforme "output_format" e após as 
      operações solicitadas.

    """

    # obtém geo-dataframe df
    if(file_path.endswith('.csv')):
        df = pd.read_csv(
            file_path,
            encoding=encoding,
            index_col=index_col,
            usecols=usecols
        )
        df = __validate_geometry_label(df, geometry_label)

    elif(file_path.endswith('.xls') or file_path.endswith('.xlsx')):
        df = pd.read_excel(
            open(file_path, 'rb'),
            # encoding=encoding, # a função read_excel n recebe esse parametro
            index_col=index_col,
            usecols=usecols
        )
        df = __validate_geometry_label(df, geometry_label)

    elif(file_path.endswith('.shp') or file_path.endswith('.json')):
        df = gpd.read_file(file_path)

    elif(file_path.endswith('.kml')):
        gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
        # the KML driver has to be activated
        df = gpd.read_file(filename=file_path, driver='KML')

    else:
        raise Exception("Extensão inesperada: csv, xls, xlsx, shp, json, kml.")

    df = filter_and_sort_df(
        df,
        filter_df=filter_df,
        sort_values=sort_values,
        ascending=ascending
    )

    # converte geo-dataframe para o formato desejado
    if(output_format.lower() == 'csv'):
        out = pd.DataFrame(df, copy=True)
    elif(output_format.lower() == 'geopandas'):
        out = df.copy()
    elif(output_format.lower() == 'geojson'):
        out = df.to_json()
    else:
        raise Exception("output_format: csv, geopandas ou geojson.")

    return out



###  
#   Construção do mecanismo que recebe os parâmetros do usuário via linha de comando e os utiliza
#   posteriormente para a construção do grid.
###
@click.command()
@click.option(
    '--locality', 
    default=None, 
    help='Local que o usuário deseja gerar seu grid.')

@click.option(
    '--file', 
    default=None, 
    help='Endereço do seu diretório ou link onde se encontra o arquivo contendo as informações do local para gerar o grid.')

@click.option(
    '--resolution', 
    default=0.5, 
    help='Resolução dos grid.')

@click.option(
    '--border', 
    default=0.5, 
    help='Tamanho da borda do grid.')

@click.option(
    '--filename', 
    default="User_Grid", 
    help='Nome do arquivo de saída com o grid.')

@click.option(
    '--verbose', 
    default=True, 
    help='Flag que habilita impressão de detalhes da execução.')

@click.option(
    '--filename_base', 
    default=None, 
    help='Nome do arquivo de saída com o mapa base.')

@click.option(
    '--filename_int', 
    default=None, 
    help='Nome do arquivo de saída com o mapa intermediário.')

@click.option(
    '--filename_grid', 
    default=None, 
    help='Nome do arquivo de saída com o mapa final.')

###
#   Função executada automaticamente com a finalidade de criar o(s) grid(s) que o usuário deseja.
###
def execute(locality, file, resolution, border, filename, verbose, filename_base, filename_int, filename_grid):

    ## Verifica se o usuário enviou um arquivo e locais para criar o grid
    ## O programa só será executado caso receba apenas um dos dois (arquivo ou locais de interesse)
    if file is not None and locality is None:
        
        try:
            dados = read_geo_generico(file, output_format="csv")
        except: 
            return print("Não foi possível gerar o grid. O formato do arquivo não é aceitável.")

    else:
        return print("Erro ao executar. Envie apenas a localidade ou arquivo, os dois ao mesmo tempo não serão aceitos.")
    

    dados = dados.reset_index(inplace=False)

    ## Criando o grid base e grid intermediário
    dados_grid, sf = gera_quadrados_simples(resolution, file)


    ## Adicionando os limites entre o grid base e intermediário

    try:
        limites = gpd.GeoDataFrame(geometry=gpd.GeoSeries(cascaded_union(sf['geometry'].buffer(0))))
    except:
        limites = gpd.GeoDataFrame(geometry=gpd.GeoSeries(unary_union(sf['geometry'].buffer(0))))
    
    # verificando os pontos que estão no grid + borda
    flag = [
        limites.distance(row['center_point'])[0] < 2 * border
        for idx, row in dados_grid.iterrows()
    ]

    ## Criando o grid final constituído do grid ajustado + borda
    grid_filtrado = dados_grid.loc[flag].copy()
    grid_filtrado.shape

    ## Criando a figura (opcional) do grid base e salvando.
    if filename_base is not None:
        fig, ax = plt.subplots(1, 1, figsize=(20, 20))
        gpd.GeoSeries(dados['geometry']).plot(ax=ax, color='red', alpha=0.15)
        gpd.GeoSeries(dados['geometry']).boundary.plot(ax=ax, color='#00CED1', label='Municípios', alpha=0.30)
        gpd.GeoSeries(dados['geometry']).centroid.plot(ax=ax, color='#0000CD', label='Centroid', alpha=1.00, markersize=5)
        ax.legend()
        plt.savefig(filename_base + '.png', dpi='figure')
    
    ## Criando a figura (opcional) do grid intermediário e salvando.
    if filename_int is not None:

        fig, ax = plt.subplots(1, 1, figsize=(20, 20))
        gpd.GeoSeries(sf['geometry']).plot(ax=ax, color='red', alpha=0.15)
        gpd.GeoSeries(sf['geometry']).boundary.plot(ax=ax, color='black', label='Municípios', alpha=0.30)
        gpd.GeoSeries(sf['geometry']).centroid.plot(ax=ax, color='blue', label='Centroid', alpha=0.30, markersize=15)

        gpd.GeoSeries(dados_grid['center_point']).plot(ax=ax, color='#0000CD', markersize=15, label='Center_Point')
        gpd.GeoSeries(dados_grid['envelope']).plot(ax=ax, color='white', label='Envelope', alpha=0.25)
        gpd.GeoSeries(dados_grid['envelope']).boundary.plot(ax=ax, color='gray', label='Envelope-Boundary', alpha=0.15)
        ax.legend()
        plt.savefig(filename_int + '.png', dpi='figure')
    
    ## Criando a figura (opcional) do grid intermediário e salvando.
    if filename_grid is not None:

        fig, ax = plt.subplots(1, 1, figsize=(20, 20))
        gpd.GeoSeries(sf['geometry']).plot(ax=ax, color='red', alpha=0.10)
        gpd.GeoSeries(sf['geometry']).boundary.plot(ax=ax, color='black', label='Municípios', alpha=0.40)
        gpd.GeoSeries(sf['geometry']).centroid.plot(ax=ax, color='blue', label='Centroid', alpha=0.10, markersize=15)

        gpd.GeoSeries(grid_filtrado['center_point']).plot(ax=ax, color='#0000CD', markersize=15, label='Center_Point')
        gpd.GeoSeries(grid_filtrado['envelope']).plot(ax=ax, color='white', label='Envelope', alpha=0.25)
        gpd.GeoSeries(grid_filtrado['envelope']).boundary.plot(ax=ax, color='gray', label='Envelope-Boundary', alpha=0.15)
        ax.legend()
        plt.savefig(filename_grid + '.png', dpi='figure')
        plt.show()

    ##  Retornando o grid final (grid ajustado + borda)    

    print(grid_filtrado)
    return grid_filtrado.to_csv(filename + ".csv", index=False)


if __name__ == '__main__':
    execute()


# Exemplo de caminho no diretório
#"C:/Users/Lincon/Desktop/Fede/Pesquisa/Projeto CHESF OSARAAD/Modulos/Pre Resultado (Modulo Pre 0)/grid_nordeste.csv"
###
#   Exemplo de comandos para gerar os grids. 👇👇👇
###
"""
python cli_grid.py 
--file "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json" 
--filename_base figura1 
--filename_int figura2 
--filename_grid figura3 
--resolution 0.5 
--border 0.5
"""
