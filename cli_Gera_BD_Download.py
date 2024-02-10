
# os.environ['USE_PYGEOS'] = '0'

import click
import pandas as pd

from time import sleep
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

from utils import read_geo_generico
from backend import pipeline

# ==============================================================================
# =========================== Parâmetros default ===============================
# ==============================================================================
filename_input_dft = './dados/input_gera_bd_download_com_6_pontos.csv'
foldername_output_dft = './dados/BD_6_pontos'
date_initial_dft = 20120101
date_final_dft = 20221230
verbose_dft = 'False'
# ==============================================================================

def compacta_bd(df, foldername):
    df_compacto = None
    for _, row in df.iterrows():

        name_file = f"{row['center_point'].x}_{row['center_point'].y}.csv"
        df = pd.read_csv(f'{foldername}/{name_file}', index_col=0)

        df['center_point'] = row['center_point']
        df['envelope'] = row['envelope']

        if df_compacto is None:
            df_compacto = df.copy()
        else:
            df_compacto = pd.concat([df_compacto, df])

    return df_compacto



def execute_gera_bd_download(
        filename_input, 
        foldername_output,
        date_initial,
        date_final,
        verbose, 
):
    # Trata verbose...
    def depuracao(texto):
        if verbose.upper() == 'TRUE':
            print(texto)

    depuracao('(execute_gera_bd_download)\n Ler pontos de entrada...')
    try:
        df = read_geo_generico(
            filename_input, 
            index_col=False, 
            geometry_label='center_point', 
            sep=';', 
            verbose=verbose
        )
    except Exception as e:
        return print(f'Não foi possível ler o arquivo de entrada.\n{str(e)}')

    depuracao('(execute_gera_bd_download)\n Executa download...')
    points_lat_lon = [(ponto.y, ponto.x) for ponto in df['center_point']]
    with ThreadPoolExecutor(5) as pool:

        futures = [
            (
                point, 
                pool.submit(
                    pipeline, 
                    lat_lon=point, 
                    start_date=date_initial, 
                    end_date=date_final,
                    foldername=foldername_output,
                )
            )
            for point in points_lat_lon
        ]

        if verbose.upper() == 'TRUE':
            pbar = tqdm(total=len(points_lat_lon))

        for point, future in futures:
            while not future.done:
                sleep(0.5)

            e = future.exception()
            if e:
                if verbose.upper() == 'TRUE':
                    pbar.write(str(e))
                f = pool.submit(
                    pipeline, 
                    lat_lon=point, 
                    start_date=date_initial, 
                    end_date=date_final,
                    foldername=foldername_output,
                )
                futures.append((point, f))
            else:
                if verbose.upper() == 'TRUE':
                    pbar.update()

        if verbose.upper() == 'TRUE':
            pbar.close()

    depuracao('(execute_gera_bd_download)\n Compactação de arquivos em arquivo único...')
    df_mes = compacta_bd(df, f'{foldername_output}/mensal')
    df_bim = compacta_bd(df, f'{foldername_output}/bimestral')
    df_tri = compacta_bd(df, f'{foldername_output}/trimestral')
    df_sem = compacta_bd(df, f'{foldername_output}/semestral')
    df_ano = compacta_bd(df, f'{foldername_output}/anual')
    df_his = compacta_bd(df, f'{foldername_output}/histórico')

    depuracao('(execute_gera_bd_download)\n Concluído!')
    return df_mes, df_bim, df_tri, df_sem, df_ano, df_his



@click.command()
@click.option(
    '--filename_input', 
    default=filename_input_dft,
    help='''
        Nome do arquivo gegdaláfico de entrada para download dos dados da NASA.

        Se o arquivo é csv, a separação deve ser com ";".

        Os pontos de interesse devem estar em uma coluna nomeada de "center_point".

        Exemplo: "C:/Projeto/Resultados/input_grid_nasa.csv"
    ''',
)
@click.option(
    '--foldername_output', 
    default=foldername_output_dft, 
    help='''
        Nome da pasta de saída, em que devem ser salvos os dados organizados.
        São geradas as seguintes sub-pastas:

        "mensal", 
        "bimestral", 
        "trimestral", 
        "semestral",
        "anual" e 
        "histórico". 

        Em cada uma dessa sub-pastas e para cada ponto de interesse, há um 
        arquivo com dados daquele ponto gegdaláfico. 
        
        Em cada sub-pasta, há um arquivo extra nomeado de "compactado.csv",
        em que as colunas são as variáveis de interesse obtidas da NASA e as 
        linhas são os valores referentes a cada um dos pontos.

        Exemplo: "C:/Projeto/Resultados"
    ''',
)
@click.option(
    '--date_initial', 
    default=date_initial_dft, 
    help='''
        Data inicial para o download da Internet: aaaammdd.

        Exemplo: 20220101
    ''',
)
@click.option(
    '--date_final', 
    default=date_final_dft, 
    help='''
        Data final para o download da Internet (não incluída): aaaammdd.

        Exemplo: 20221230
    ''',
)
@click.option(
    '--verbose', 
    default=verbose_dft, 
    help='Flag que habilita impressão de detalhes da execução.',
)
def cli_execute_gera_bd_download(
        filename_input, 
        foldername_output,
        date_initial,
        date_final,
        verbose, 
):
    # Trata verbose...
    def depuracao(texto):
        if verbose.upper() == 'TRUE':
            print(texto)

    depuracao(f'')
    depuracao(f'Resumo dos parâmetros recebidos:\n')
    depuracao(f'{filename_input = }')
    depuracao(f'{foldername_output = }')
    depuracao(f'{date_initial = }')
    depuracao(f'{date_final = }')
    depuracao(f'{verbose = }')
    depuracao(f'-----\n')

    df_mes, df_bim, df_tri, df_sem, df_ano, df_his = execute_gera_bd_download(
        filename_input, foldername_output, date_initial, date_final, verbose
    )

    depuracao('(cli_execute_gera_bd_download)\n Amostra do arquivo histórico gerado:')
    depuracao(df_his.head())

    df_mes.to_csv(f'{foldername_output}/mensal/compactado.csv', sep=';', date_format='%Y%m%d')
    df_bim.to_csv(f'{foldername_output}/bimestral/compactado.csv', sep=';', date_format='%Y%m%d')
    df_tri.to_csv(f'{foldername_output}/trimestral/compactado.csv', sep=';', date_format='%Y%m%d')
    df_sem.to_csv(f'{foldername_output}/semestral/compactado.csv', sep=';', date_format='%Y%m%d')
    df_ano.to_csv(f'{foldername_output}/anual/compactado.csv', sep=';', date_format='%Y%m%d')
    df_his.to_csv(f'{foldername_output}/histórico/compactado.csv', sep=';', date_format='%Y%m%d')

    depuracao('Concluído!')



if __name__ == '__main__':
    cli_execute_gera_bd_download()


# Teste com "Parâmetros Default": 
# - Usa 6 pontos como entrada.
# (ambiente_virtual) caminho>
# python cli_Gera_BD_Download.py

# ==============================================================================

# Teste para "Depuração 01": 
# - Usa 6 pontos como entrada.
# - Liga verbose.
# (ambiente_virtual) caminho>
# python cli_Gera_BD_Download.py --verbose True

# ==============================================================================

# Template com "Todos os Parâmetros": 
# input_gera_bd_pb.csv
# (ambiente_virtual) caminho>
# python cli_Gera_BD_Download.py --filename_input "./dados/input_gera_bd_download_pb.csv" --foldername_output "./dados/BD_PB" --date_initial 19900101 --date_final 20230530 --verbose True

# Apresentação de slides:
# (venv) caminho> python cli_Gera_BD_Download.py --filename_input "./dados/output_rn.csv" --foldername_output "./dados/BD_RN" --date_initial 20000101 --date_final 20230530 --verbose True
