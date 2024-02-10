
# os.environ['USE_PYGEOS'] = '0'

import click
import os
import math
import pandas as pd
import openturns as ot
import matplotlib.pyplot as plt

import geopandas as gpd
from shapely import wkt
from shapely.geometry import MultiPoint
from shapely.ops import nearest_points

from utils import read_geo_generico
from backend import dict_fcns

# ==============================================================================
# =========================== Parâmetros default ===============================
# ==============================================================================
filename_input_grid_interpolado_dft = './dados/input_gera_bd_interpolado_pb_sem_borda.csv'
filename_input_grid_dados_dft = './dados/input_gera_bd_interpolado_pb_nasa.csv'
filename_output_grid_interpolado_dft = './dados/output_gera_bd_interpolado_pb.csv'
algorithm_dft = 'IDW'
date_initial_dft = 20230530
date_final_dft = 20230531
neighbors_dft = 3
idw_p_dft = 1
foldername_output_figures_dft = ''
date_output_figures_dft = -1
turnon_grid_interpolado_in_figures_dft = 'True'
verbose_dft = 'False'
# ==============================================================================



def interpolate_idw(pt, df_vizinhos, cols, p):

    ret = {}
    for col in cols:

        numerador = 0
        denominador = 0

        for _, row in df_vizinhos.iterrows():

            ponto_vizinho = row['center_point']
            dx = ((pt.x - ponto_vizinho.x) * math.pi) / 180 # long em rad
            dy = ((pt.y - ponto_vizinho.y) * math.pi) / 180 # lat em rad

            a = math.sin(dy/2) * math.sin(dy/2) + math.cos((pt.y)/2) * math.cos((ponto_vizinho.y)/2) * pow(math.sin(dx/2),2)
            distance = 6378.1 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

            valor = float(row[col])
            numerador += (valor/distance**p)
            denominador += (1/distance**p)

        ret[col] = numerador/denominador

    return ret

def interpolate_kriging(point, df_vizinhos, cols):
    # https://openturns.github.io/openturns/1.17/auto_meta_modeling/kriging_metamodel/plot_kriging_beam_trend.html?highlight=krigingalgorithm
    # https://stackoverflow.com/questions/45175201/how-can-i-interpolate-station-data-with-kriging-in-python

    ret = {}
    for col in cols:

        xy_train = [[pt.x, pt.y] for pt in df_vizinhos['center_point']]
        value_train = [[float(valor)] for valor in df_vizinhos[col]]

        # for _, row in df_vizinhos.iterrows():

        #     ponto_vizinho = row['center_point']
        #     xy_train.append([ponto_vizinho.x,ponto_vizinho.y])
        #     value_train.append([float(row[col])])

        # Fit
        inputDimension = 2
        basis = ot.ConstantBasisFactory(inputDimension).build()

        # Modelo de covariância exponencial, uma vez que a precipitação deve ser 
        # regular em relação a localidade do ponto.
        covarianceModel = ot.SquaredExponential([1.] * inputDimension, [1.0])

        algo = ot.KrigingAlgorithm(xy_train, value_train, covarianceModel, basis)
        algo.run()
        result = algo.getResult()
        krigingMetamodel = result.getMetaModel()

        ret[col] = krigingMetamodel([point.x,point.y])[0]

    return ret

def get_nearest_points(center_point, df_dados, neighbors):

    base_de_pontos = list(df_dados['center_point'].copy())

    ret = [False] * len(df_dados.index)
    for i in range(neighbors):
        aux = nearest_points(center_point, MultiPoint(base_de_pontos))
        ponto_mais_proximo = aux[1]
        if ponto_mais_proximo not in ret:
            flag = [(ponto_mais_proximo == pt) for pt in df_dados['center_point']]
            if sum(flag) != 1:
                print('Erro em get_nearest_points: ocorrências diferente de 1.')
            else:
                ret = [a or b for a, b in zip(ret, flag)]
                base_de_pontos.remove(ponto_mais_proximo)

    return df_dados.loc[ret]

def interpolar_point(date, center_point, envelope, df_dados, algorithm, idw_p, neighbors):

    df_vizinhos = get_nearest_points(center_point, df_dados, neighbors)
    if algorithm.upper() == 'IDW':
        aux = interpolate_idw(center_point, df_vizinhos, list(dict_fcns.keys()), idw_p)
    elif algorithm.upper() == 'KRIGING':
        aux = interpolate_kriging(center_point, df_vizinhos, list(dict_fcns.keys()))

    ret = {'date': date, 'center_point': center_point, 'envelope': envelope}
    return {**ret, **aux}

def salvar_figures_date(date, df_dados, df_interpolado, cols, foldername_output, flag, verbose):
    '''
    Presume que foldername_output foi testado e não é vazio.
    '''

    # Trata verbose...
    def depuracao(texto):
        if verbose.upper() == 'TRUE':
            print(texto)

    depuracao('(salvar_figures_date)\n Testa se foldername_output existe e, se necessário, cria pasta.')
    if not os.path.isdir(foldername_output):
        os.makedirs(foldername_output)

    depuracao('(salvar_figures_date)\n Filtrar dfs para a data desejada.')
    dff_dados = df_dados.loc[(df_dados.index == date)]
    dff_interpolado = df_interpolado.loc[(df_interpolado['date'] == date)]

    depuracao('(salvar_figures_date)\n Criar dfs do geopandas com "center_point" e "envelope".')
    gdf_dados_pt = gpd.GeoDataFrame(dff_dados, geometry=dff_dados['center_point'], crs={'init': 'epsg:4618'})
    gdf_dados_env = gpd.GeoDataFrame(dff_dados, geometry=dff_dados['envelope'].apply(wkt.loads), crs={'init': 'epsg:4618'})
    gdf_interpolado_pt = gpd.GeoDataFrame(dff_interpolado, geometry=dff_interpolado['center_point'], crs={'init': 'epsg:4618'})
    gdf_interpolado_env = gpd.GeoDataFrame(dff_interpolado, geometry=dff_interpolado['envelope'].apply(wkt.loads), crs={'init': 'epsg:4618'})

    depuracao('(salvar_figures_date)\n Calcular limites por variável em "cols".')
    dict_limites = {}
    for col in cols:
        minimo1 = dff_dados[col].min()
        minimo2 = dff_interpolado[col].min()
        minimo = minimo1 if minimo1 < minimo2 else minimo2

        maximo1 = dff_dados[col].max()
        maximo2 = dff_interpolado[col].max()
        maximo = maximo1 if maximo1 > maximo2 else maximo2

        delta = maximo - minimo

        dict_limites[col] = {'min': minimo - 0.1*delta, 'max': maximo + 0.1*delta}

    depuracao('(salvar_figures_date)\n Figura 1: "dados base com center_point".')
    for col in cols:
        fig, ax = plt.subplots()
        gdf_dados_pt.plot(ax=ax, column=col, cmap="OrRd", legend=True, 
                          vmin=dict_limites[col]['min'], 
                          vmax=dict_limites[col]['max']) # Outro esquema de cor: Set1
        if flag.upper() == 'TRUE':
            gdf_interpolado_env.plot(ax=ax, color='none', edgecolor='lightgray')

        plt.xlabel("Longitude (°)")
        plt.ylabel("Latitude (°)")
        plt.title(f'Variável {col}: Pontos - Base')

        date_str = date.strftime('%Y%m%d')
        filename = f'{foldername_output}/dados_base_point_{col}_{date_str}.png'
        plt.savefig(filename, dpi=1200)
        plt.close(fig)

    depuracao('(salvar_figures_date)\n Figura 2: "dados base com envelope".')
    for col in cols:
        fig, ax = plt.subplots()
        gdf_dados_env.plot(ax=ax, column=col, cmap="OrRd", legend=True, 
                           vmin=dict_limites[col]['min'], 
                           vmax=dict_limites[col]['max']) # Outro esquema de cor: Set1

        if flag.upper() == 'TRUE':
            gdf_interpolado_env.plot(ax=ax, color='none', edgecolor='lightgray')

        plt.xlabel("Longitude (°)")
        plt.ylabel("Latitude (°)")
        plt.title(f'Variável {col}: Envelopes - Base')

        date_str = date.strftime('%Y%m%d')
        filename = f'{foldername_output}/dados_base_envelope_{col}_{date_str}.png'
        plt.savefig(filename, dpi=1200)
        plt.close(fig)

    depuracao('(salvar_figures_date)\n Figura 3: "dados interpolados com center_point".')
    for col in cols:
        fig, ax = plt.subplots()
        gdf_interpolado_pt.plot(ax=ax, column=col, cmap="OrRd", legend=True, 
                                vmin=dict_limites[col]['min'], 
                                vmax=dict_limites[col]['max']) # Outro esquema de cor: Set1
        
        if flag.upper() == 'TRUE':
            gdf_interpolado_env.plot(ax=ax, color='none', edgecolor='lightgray')

        plt.xlabel("Longitude (°)")
        plt.ylabel("Latitude (°)")
        plt.title(f'Variável {col}: Pontos - Interpolado')

        date_str = date.strftime('%Y%m%d')
        filename = f'{foldername_output}/dados_interpolados_point_{col}_{date_str}.png'
        plt.savefig(filename, dpi=1200)
        plt.close(fig)

    depuracao('(salvar_figures_date)\n Figura 4: "dados interpolados com envelope".')
    for col in cols:
        fig, ax = plt.subplots()
        gdf_interpolado_env.plot(ax=ax, column=col, cmap="OrRd", legend=True, 
                                 vmin=dict_limites[col]['min'], 
                                 vmax=dict_limites[col]['max']) # Outro esquema de cor: Set1
        
        if flag.upper() == 'TRUE':
            gdf_interpolado_env.plot(ax=ax, color='none', edgecolor='lightgray')

        plt.xlabel("Longitude (°)")
        plt.ylabel("Latitude (°)")
        plt.title(f'Variável {col}: Envelopes - Interpolado')

        date_str = date.strftime('%Y%m%d')
        filename = f'{foldername_output}/dados_interpolados_envelope_{col}_{date_str}.png'
        plt.savefig(filename, dpi=1200)
        plt.close(fig)



def execute_gera_bd_interpolado(
        filename_input_grid_interpolado, 
        filename_input_grid_dados, 
        algorithm,
        date_initial,
        date_final,
        neighbors,
        idw_p,
        foldername_output_figures,
        date_output_figures,
        turnon_grid_interpolado_in_figures,
        verbose, 
):
    # Trata verbose...
    def depuracao(texto):
        if verbose.upper() == 'TRUE':
            print(texto)

    depuracao('(execute_gera_bd_interpolado)\n Ler pontos de entrada para serem interpolados...')
    try:
        df_grid_interpolado = read_geo_generico(
            filename_input_grid_interpolado, 
            index_col=False, 
            geometry_label='center_point', 
            sep=';', 
            verbose=verbose
        )
    except Exception as e:
        return print(f'Não foi possível ler o arquivo de entrada com os pontos para serem interpolados.\n{str(e)}')

    depuracao('(execute_gera_bd_interpolado)\n Ler pontos de entrada com os dados de referência...')
    try:
        df_grid_dados = read_geo_generico(
            filename_input_grid_dados, 
            geometry_label='center_point', 
            sep=';', 
            verbose=verbose
        )

        # Atenção
        # =======
        # Aqui estou forçando o formato da data que serve como index do grid de dados a ter esse formato.
        df_grid_dados.index = pd.to_datetime(df_grid_dados.index, format='%Y%m%d')

    except Exception as e:
        return print(f'Não foi possível ler o arquivo de entrada com os pontos em que se tem dados.\n{str(e)}')

    depuracao('(execute_gera_bd_interpolado)\n Executa interpolação...')

    date = pd.to_datetime(date_initial, format='%Y%m%d')
    date_fim = pd.to_datetime(date_final, format='%Y%m%d')

    list_interpolados = []
    while date < date_fim:
        flag = (df_grid_dados.index == date)

        if sum(flag) > 0:
            dff_grid_dados = df_grid_dados.loc[flag]
            for idx, row in df_grid_interpolado.iterrows():
                aux = interpolar_point(
                    date, 
                    row['center_point'], 
                    row['envelope'],
                    dff_grid_dados, 
                    algorithm, 
                    idw_p, 
                    neighbors,
                )
                list_interpolados.append(aux)
        date = date + pd.DateOffset(1)

    df = pd.DataFrame(list_interpolados)

    if len(foldername_output_figures) > 0:
        depuracao('(execute_gera_bd_interpolado)\n Gerar gráficos...')
        date = pd.to_datetime(date_output_figures, format='%Y%m%d')
        salvar_figures_date(
            date, 
            df_grid_dados, 
            df, 
            list(dict_fcns.keys()), 
            foldername_output_figures, 
            turnon_grid_interpolado_in_figures,
            verbose,
        )

    return df


@click.command()
@click.option(
    '--filename_input_grid_interpolado', 
    default=filename_input_grid_interpolado_dft,
    help='''
        Nome do arquivo gegdaláfico de entrada com os pontos que devem ser 
        interpolados.

        Se o arquivo é csv, a separação deve ser com ";".

        Os pontos de interesse devem estar em uma coluna nomeada de "center_point".

        Exemplo: "C:/Projeto/Resultados/input_grid_interpolação.csv"
    ''',
)
@click.option(
    '--filename_input_grid_dados', 
    default=filename_input_grid_dados_dft, 
    help='''
        Nome do arquivo gegdaláfico de entrada com os pontos para os quais se tem
        dados e que, consequentemente, permitem interpolação.

        Se o arquivo é csv, a separação deve ser com ";".

        A primeira coluna deve ter datas no formato aaaammdd.

        Exemplo: "C:/Projeto/Resultados/input_grid_dados.csv"
    ''',
)
@click.option(
    '--filename_output_grid_interpolado', 
    default=filename_output_grid_interpolado_dft, 
    help='''
        Nome do arquivo gegdaláfico de saída com os pontos interpolados.

        Separador: ";".

        Exemplo: "C:/Projeto/Resultados/output_grid_interpolação.csv"
    ''',
)
@click.option(
    '--algorithm', 
    default=algorithm_dft, 
    help='''
        Algoritmo de interpolação: 'KRIGING' ou 'IDW'
        Exemplo: IDW
    ''',
)
@click.option(
    '--date_initial', 
    default=date_initial_dft, 
    help='''
        Data inicial para interpolação: aaaammdd.
        Exemplo: 20230101
    ''',
)
@click.option(
    '--date_final', 
    default=date_final_dft, 
    help='''
        Data final para interpolação: aaaammdd.
        Exemplo: 20230102
    ''',
)
@click.option(
    '--neighbors', 
    default=neighbors_dft, 
    help='Número de vizinhos usados na interpolação. Exemplo: 3.',
)
@click.option(
    '--idw_p', 
    default=idw_p_dft, 
    help='Parâmetro p específico do método IDW. Exemplo: 1.',
)
@click.option(
    '--foldername_output_figures', 
    default=foldername_output_figures_dft, 
    help='''
        Pasta em que deve gerar figuras com dados base e interpolados. 
        Exemplo: './dados/BD_Interpolado_Figures'.'
    ''',
)
@click.option(
    '--date_output_figures', 
    default=date_output_figures_dft, 
    help='Escolha de uma data para geração das figuras. Exemplo: 20230530.',
)
@click.option(
    '--turnon_grid_interpolado_in_figures', 
    default=turnon_grid_interpolado_in_figures_dft, 
    help='Flag para ligar/desligar a adição do grid a ser interpolado nas figuras.',
)
@click.option(
    '--verbose', 
    default=verbose_dft, 
    help='Flag que habilita impressão de detalhes da execução.',
)
def cli_execute_gera_bd_interpolado(
        filename_input_grid_interpolado, 
        filename_input_grid_dados,
        filename_output_grid_interpolado,
        algorithm,
        date_initial,
        date_final,
        neighbors,
        idw_p,
        foldername_output_figures,
        date_output_figures,
        turnon_grid_interpolado_in_figures,
        verbose, 
):
    # Trata verbose...
    def depuracao(texto):
        if verbose.upper() == 'TRUE':
            print(texto)

    depuracao(f'')
    depuracao(f'Resumo dos parâmetros recebidos:\n')
    depuracao(f'{filename_input_grid_interpolado = }')
    depuracao(f'{filename_input_grid_dados = }')
    depuracao(f'{filename_output_grid_interpolado = }')
    depuracao(f'{algorithm = }')
    depuracao(f'{date_initial = }')
    depuracao(f'{date_final = }')
    depuracao(f'{neighbors = }')
    depuracao(f'{idw_p = }')
    depuracao(f'{foldername_output_figures = }')
    depuracao(f'{date_output_figures = }')
    depuracao(f'{turnon_grid_interpolado_in_figures = }')
    depuracao(f'{verbose = }')
    depuracao(f'-----\n')

    df_interpolado = execute_gera_bd_interpolado(
        filename_input_grid_interpolado, 
        filename_input_grid_dados, 
        algorithm,
        date_initial,
        date_final,
        neighbors,
        idw_p,
        foldername_output_figures,
        date_output_figures,
        turnon_grid_interpolado_in_figures,
        verbose, 
    )

    depuracao('(cli_execute_gera_bd_interpolado)\n Amostra do arquivo interpolado gerado:')
    depuracao(df_interpolado.head())

    df_interpolado.to_csv(
        filename_output_grid_interpolado, 
        sep=';', 
        date_format='%Y%m%d',
    )

    depuracao('Concluído!')



if __name__ == '__main__':
    cli_execute_gera_bd_interpolado()


# Teste com "Parâmetros Default": 
# - Usa Paraíba como entrada.
# (ambiente_virtual) caminho>
# python cli_Gera_BD_Interpolado.py

# Teste para "Depuração 01": 
# - Usa Paraíba como entrada.
# - Liga verbose.
# (ambiente_virtual) caminho>
# python cli_Gera_BD_Interpolado.py --verbose True

# Template com "Todos os Parâmetros": IDW com p=1
# input_gera_bd_pb.csv
# (ambiente_virtual) caminho>
# python cli_Gera_BD_Interpolado.py --filename_input_grid_interpolado "./dados/input_gera_bd_interpolado_pb_sem_borda.csv" --filename_input_grid_dados "./dados/input_gera_bd_interpolado_pb_nasa.csv" --filename_output_grid_interpolado "./dados/output_gera_bd_interpolado_pb.csv" --algorithm "IDW" --date_initial 20230530 --date_final 20230531 --neighbors 3 --idw_p 1 --foldername_output_figures "./dados/BD_Interpolado_Figures" --date_output_figures 20230530 --turnon_grid_interpolado_in_figures True --verbose True

# Template com "Todos os Parâmetros": Kriging
# input_gera_bd_pb.csv
# (ambiente_virtual) caminho>
# python cli_Gera_BD_Interpolado.py --filename_input_grid_interpolado "./dados/input_gera_bd_interpolado_pb_sem_borda.csv" --filename_input_grid_dados "./dados/input_gera_bd_interpolado_pb_nasa.csv" --filename_output_grid_interpolado "./dados/output_gera_bd_interpolado_pb.csv" --algorithm "Kriging" --date_initial 20230530 --date_final 20230531 --neighbors 3 --idw_p 1 --foldername_output_figures "./dados/BD_Interpolado_Figures" --date_output_figures 20230530 --turnon_grid_interpolado_in_figures False --verbose False

# Apresentação de slides:
# python cli_Gera_BD_Interpolado.py --filename_input_grid_interpolado "./dados/output_rn_menor.csv" --filename_input_grid_dados "./dados/bd_rn_historico_compactado.csv" --filename_output_grid_interpolado "./dados/output_rn_menor_interpolado.csv" --algorithm "idw" --date_initial 20230530 --date_final 20230531 --neighbors 3 --idw_p 1 --foldername_output_figures "./dados/BD_RN_Interpolado_Figures" --date_output_figures 20230530 --turnon_grid_interpolado_in_figures True --verbose True