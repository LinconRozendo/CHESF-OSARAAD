# =========================== Bibilotecas ===============================

import click
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import folium as fl
import json
from shapely import wkt
import shapely.geometry as geom
from shapely.geometry.multipolygon import MultiPolygon
from utils import read_geo_generico
import warnings
warnings.filterwarnings('ignore')


# =================================================================================
# =========================== Gera Camada Ambiental ===============================
# =================================================================================
# =================================================================================
# == Esta classe tem a finalidade de verificar se os pontos pertencentes ao grid ==
# == enviado como parâmetro se encontram em alguma área de proteção ambiental, ====
# == seja tal área de Proteção Integral ou Uso Sustentável. =======================
# =================================================================================


# ==============================================================================
# =========================== Parâmetros default ===============================
# ==============================================================================
filename_input_dft = './dados/municipiosPB.json'
filename_output_dft = './dados/output_pb_cmd_amb.csv'
#dict_camadas_improprias_dft = './dados/dict_camadas.json'
dict_camadas_improprias_dft = ''
#filename_camadas_improprias_dft = './camadas/ucsfus_uso_sustentavel.geojson'
filename_camadas_improprias_dft  = ''
filename_output_map_final_dft = './dados/mapa_camadas.html'
incluir_camadas_originais_no_mapa_dft = 'False'
# ==============================================================================

def criar_map_final(
    df,
    filename,
    columns,
    paleta_de_cores,
    camada_original = "False",
):
    paleta_de_cores_dft = ['red', 'orange', 'lime', 'DarkGreen', 'maroon', 'indigo', 'pink', 'purple', 'green', 'yellow']

    ## Variável que indica quantas colunas existem sem ser de camada ambiental
    fix_column = len(df.columns) - len(columns)

    ## Verificando se a lista de cores possui paleta de cores ou é 'default'
    if paleta_de_cores == "default":
        paleta_de_cores = paleta_de_cores_dft

    mapa = fl.Map(location=[-7.129694, -35.867750], zoom_start=5, tiles='OpenStreetMap')

    ## Transformando 'str' para objeto 'shapely'
    df['envelope'] = df['envelope'].apply(wkt.loads)

    feature_group = fl.FeatureGroup(name='Pontos Centrais', show=True)
    for _, row in df.iterrows():
        ponto = row['center_point']
        obj = fl.CircleMarker(
            location=[ponto.y, ponto.x],
            radius=5,
            fill_color='red',
            popup='Ponto',
            name='Ponto',
            tooltip=f'<strong>Latitude:</strong> {ponto.y} <br><strong>Longitude:</strong> {ponto.x}',
        )
        feature_group.add_child(obj)
    feature_group.add_to(mapa)

    feature_group = fl.FeatureGroup(name='Envelope', show=True)
    for _, row in df.iterrows():
        poligono = row['envelope']
        obj = fl.GeoJson(
            data=poligono,
            style_function=lambda x: {
                'fillColor': 'blue',
                'color': 'gray',
            },
        )
        feature_group.add_child(obj)
    feature_group.add_to(mapa)

    index_columns_original = 0

    ## Rotina para adicionar N camadas ao mapa final 
    for i in range(0, len(columns)):
        if columns[i] in df.columns:
            feature_group = fl.FeatureGroup(name='Pontos Impróprios - ' + str(columns[i]), show=True)

            # Verificando se a camada é do tipo original
            if 'original' in columns[i].lower(): 
                for _, row in df.iterrows():

                    if row[i + fix_column] is not None:
                        if row[i + fix_column].geom_type == 'Polygon':
                            poligono = MultiPolygon([row[i + fix_column]])
                        else:
                            poligono = row[i + fix_column]

                        
                        obj = fl.GeoJson(
                            data=poligono,
                            style_function=lambda x: {
                                'fillColor': 'green',
                                'color': paleta_de_cores_dft[i]
                            },
                        )
                        
                        #fl.Popup(columns[i]).add_to(obj)
                        feature_group.add_child(obj)                            
                feature_group.add_to(mapa)

                index_columns_original += 1
            # Caso para camada não original
            else:
                for _, row in df.iterrows():
                    if row[columns[i]] == 1:
                        ponto = row['center_point']
                        obj = fl.CircleMarker(
                            location=[ponto.y, ponto.x],
                            radius=5,
                            color=paleta_de_cores[i - index_columns_original],
                            popup='Ponto Impróprio',
                            name='Ponto',
                            tooltip=f'<strong>Latitude:</strong> {ponto.y} <br><strong>Longitude:</strong> {ponto.x}',
                        )
                        feature_group.add_child(obj)
                feature_group.add_to(mapa)  

    ## Adiciona a caixinha de opções de camadas "layers"
    fl.LayerControl().add_to(mapa)

    mapa.save(filename)

def execute_gera_camada_ambiental(
    filename_input,
    filename_output,
    dict_camadas_improprias,
    filename_camadas_improprias,
    filename_output_map_final,
    incluir_camadas_originais_no_mapa,
):
    ## Verificando o parâmetro filename_input
    try:
        df_inicial = pd.read_csv(filename_input, sep=';')
    except Exception as e:
            return print(f'Não foi possível ler o arquivo de entrada.\n{str(e)}')
    
    #####################################################################################################
    ## Verificando se tem dicionário com camada(s)
    try:
        with open(dict_camadas_improprias, 'r') as f:
            data_dict = json.load(f)
            lista_de_cores = []
            lista_de_colunas = []

            print('(execute_gera_camada_ambiental)\nVerificando se os pontos pertencem a alguma camada.\n')


            # Transformando a coluna 'center_point' (str) em 'center_point' (shapely.geometry.point.Point)
            df_inicial['center_point'] = df_inicial['center_point'].apply(wkt.loads)
            
            # Verificando se o dicionário possui 'filepath' e 'cor' para cada chave (camada)
            for key in data_dict:
                
                if 'filepath' in data_dict[key] and 'cor' in data_dict[key]:
                    df_camada = read_geo_generico(data_dict[key]['filepath'], index_col=False)
                   
                    lista_de_cores.append(data_dict[key]['cor'])
                    lista_de_colunas.append(key)

                    if 'geometry' in df_camada.columns:
                        df_camada = df_camada['geometry']
                        df_inicial[key] = 0

                        quant = 0
                        tam_grid_base = len(df_inicial)

                        # Realizando a comparação entre cada ponto do grid de entrada com todos os polígonos do arquivo de camada
                        for i in range(0, tam_grid_base):              
                            for j in df_camada.contains(df_inicial['center_point'].iloc[i]):
                                if j == True:
                                    df_inicial[key].iloc[i] = 1
                                    quant += 1
                            
                            for j in df_camada.intersects(df_inicial['center_point'].iloc[i]):
                                if j == True and df_inicial[key].iloc[i] != 1:
                                    df_inicial[key].iloc[i] = 1
                                    quant += 1
                        
                        print("\nInformações da camada {}.".format(key))
                        print("Quantidade de pontos impróprios encontrados: {}.\n".format(quant))

                        
                  
                    # Adicionando a camada original no grid de entrada    
                    if incluir_camadas_originais_no_mapa == "True":
                        df_inicial[key + ' Original'] = df_camada
                        lista_de_colunas.append(key + ' Original')

                            
                df_final = df_inicial
                

    except TypeError:
        pass
    except Exception as e:
            print(f'Não foi possível ler o arquivo de dicionário.\n{str(e)}')

    ######################################################################################################
    ## Verificando se tem filename com camada
    try:
        if len(dict_camadas_improprias) == 0:
            df_camada = read_geo_generico(filename_camadas_improprias, index_col=False) 

            print('(execute_gera_camada_ambiental)\nVerificando se os pontos pertencem a alguma camada.\n')

            # Verificando se possui a coluna 'geometry' e criando uma coluna para camada no grid de entrada
            if 'geometry' in df_camada.columns:
                
                df_camada = df_camada['geometry']
                #tipo_camada = 'filename'
                lista_de_cores = 'default'
                lista_de_colunas = []

                numero_camada = None
                for i in range(0, 10):
                    if ('camada' + str(i)) not in df_inicial.columns:
                        df_inicial['camada' + str(i)] = 0
                        numero_camada = i

                        lista_de_colunas.append('camada' + str(i))
                        
                        # Adicionando a camada original no grid de entrada
                        if incluir_camadas_originais_no_mapa == "True":
                            df_inicial['camada_original_' + str(i)] = df_camada
                            lista_de_colunas.append('camada_original_' + str(i))

                        break
                
                
                quant = 0
                tam_grid_base = len(df_inicial)
                
                # Transformando a coluna 'center_point' (str) em 'center_point' (shapely.geometry.point.Point)
                df_inicial['center_point'] = df_inicial['center_point'].apply(wkt.loads)

                # Realizando a comparação entre cada ponto do grid de entrada com todos os polígonos do arquivo de camada
                for i in range(0, tam_grid_base):
                    for j in df_camada.contains(df_inicial['center_point'].iloc[i]):
                        if j == True:
                            df_inicial[key].iloc[i] = 1
                            quant += 1
                    
                    for j in df_camada.intersects(df_inicial['center_point'].iloc[i]):
                        if j == True and df_inicial[key].iloc[i] != 1:
                            df_inicial[key].iloc[i] = 1
                            quant += 1
                
                print("\nInformações da camada.")
                print("Quantidade de pontos impróprios encontrados: {}.\n".format(quant))
                    
                df_final = df_inicial
                
                
                
            else:  
                return print(f'O arquivo enviado para verificação da camada não possue a coluna "geometry".')             

    except Exception as e:
        return print(f'Não foi possível ler o arquivo de camada ambiental.\n{str(e)}')

    ## Se foi solicitado: Criar o mapa folium do grid final.
    if len(filename_output_map_final) > 0:
        print('(execute_gera_camada_ambiental)\nCriando mapa .html!.\n')
        criar_map_final(df_final, filename_output_map_final, lista_de_colunas, lista_de_cores, incluir_camadas_originais_no_mapa)

        

    return df_inicial
    



@click.command()
@click.option(
    '--filename_input', 
    default=filename_input_dft,
    help='''
        Nome do arquivo geográfico de entrada para verificação dos pontos presentes na coluna "center_point". 
        Arquivo geográfico aqui significa que possui, no mínimo, a coluna "center_point". 
        A verificação será dada pela consulta dos pontos ("center_point") em áreas de preservação. Caso os
        pontos estejam localizados em áreas protegidas, será sinalizado no grid de sáida.

        Exemplo: "C:/Projeto/Resultados/grid_pb.csv"

        ou

        Link para o arquivo geográfico de entrada para verificação do grid.
        Exemplo: "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json"

    ''',
)
@click.option(
    '--filename_output', 
    default=filename_output_dft, 
    help='''
        Nome do arquivo geográfico de saída com o grid que compreende obrigatoriamente duas 
        colunas extras: 
        
        "Uso Sustentavel" representando se o ponto está localizado em área de Uso Sustentável.
            Seguindo a lógica Python,        
                1 = True.
                0 = False.;
        
        e 
        
        "Proteção Integral" representando se o ponto está localizado em área de Proteção Integral.
            Seguindo a lógica Python,        
                1 = True.
                0 = False.;

        O termo Uso Sustentável se refere a área de preservação ambiental que são abertas parcialmente
        para exploração sustentável.

        O termo Proteção Integral se refere a área de preservação ambiental que não possuem nenhuma
        possibilidade de exploração, permitindo apenas a realização de atividades relacionadas a
        pesquisa cientifíca, educacionais e/ou turismo.


        Exemplo: "C:/Projeto/Resultados/output_grid_nordeste_ambiental.csv"
    ''',
)
@click.option(
    '--dict_camadas_improprias',
    default=dict_camadas_improprias_dft, 
    help='''
        Dicionário contendo n camadas a serem avaliadas, alem da sua personalização no arquivo de grid final e
        mapa final.
        Este parâmetro possibilita maior personalização dos resultados da comparação entre pontos do grid e áreas de preservação.
        É possível passar n camadas como parâmetros, indicar seus nomes e cores que serão exibidas no mapa final.

        Para ser aceito, o dicionário deverá ter a seguinte estrutura:

        Exemplo: {
                    'Uso sustentável': {
                        'filename': 'C:/Projeto/Resultados/Dados/ucs.shp',
                        'cor': 'blue',
                    },
                    'Proteção Integral': {
                        'filename': 'C:/Projeto/Resultados/Dados/uci.shp',
                        'cor': 'red',
                    },
                }
        
        O dicionário acima fornece duas camadas de preservação e duas cores que serão expostas no mapa final.
    ''',

)
@click.option(
    '--filename_camadas_improprias',
    default=filename_camadas_improprias_dft,
    help='''
        Nome do arquivo shapefile ou geojson contendo a camada que será analisada em conjunto com os pontos
        do grid de entrada. 
        É necessário a coluna "geometry" contendo os polígonos representando áreas impróprias.

        A análise ocorrerá pela verificação se um ponto do grid de entrada pertence a algum dos polígonos 
        presente no arquivo enviado que representa áreas impróprias;

        Seguindo a lógica Python,        
                1 = True.
                0 = False.

        Exemplo: "C:/Projeto/Resultados/Dados/ucs.shp"

        O parâmetro '--dict_camadas_improprias' possui maior prioridade em relação a este parâmetro.
    ''',
)
@click.option(
    '--filename_output_map_final', 
    default=filename_output_map_final_dft, 
    help='''
        Se for fornecido: Nome do arquivo de saída com o mapa final - html.'

        Exemplo: "C:/Projeto/Resultados/Dados/map_final.html"
    ''',
)
@click.option(
    '--incluir_camadas_originais_no_mapa',
    default=incluir_camadas_originais_no_mapa_dft,
    help='''
        Parâmetro boolean para adicionar todos os pontos lidos no arquivo de camada no mapa final.
        Em caso de False, o arquivo do mapa final não conterá todos os polígonos do arquivo de camada.
        
    ''',
)
def cli_execute_gera_camada_ambiental(
    filename_input,
    filename_output,
    dict_camadas_improprias,
    filename_camadas_improprias,
    filename_output_map_final,
    incluir_camadas_originais_no_mapa,
):
    print(f'')
    print(f'Resumo dos parâmetros recebidos:\n')
    print(f'{filename_input = }')
    print(f'{filename_output = }')
    print(f'{dict_camadas_improprias = }')
    print(f'{filename_camadas_improprias = }')
    print(f'{filename_output_map_final = }')
    print(f'{incluir_camadas_originais_no_mapa = }')
    print(f'-----\n')

    df_grid = execute_gera_camada_ambiental(
        filename_input,
        filename_output,
        dict_camadas_improprias,
        filename_camadas_improprias,
        filename_output_map_final,
        incluir_camadas_originais_no_mapa
    )

    try:
        print('\n\n(cli_execute_gera_camada_ambiental)\n Amostra do arquivo gerado:\n')
        print(df_grid.head())
        df_grid.to_csv(filename_output, index=False, sep=';')
        print('\nConcluído!')
    except Exception as e:
        return print(f'Erro nos parâmetros fornecidos.\nOperação finalizada.\n')

    

    

if __name__ == '__main__':
    cli_execute_gera_camada_ambiental()