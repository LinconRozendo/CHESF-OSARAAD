
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
filename_input_dft = './dados/dados_interpolados_pb.csv'
column_input_dft = 'WS50M'
filename_output_dft = './dados/dados_interpolados_pb_com_potencia_vento.csv'
column_output_dft = 'pot_vento'
densidade_do_ar_dft = 1.225
area_varredura_dft = 1521
coeficiente_aerodinamico_dft = 0.45
eficiencia_dft = 0.93
verbose_dft = 'False'
# ==============================================================================



def execute_gera_bd_potencia_vento(
        filename_input, 
        column_input,
        column_output,
        densidade_do_ar,
        area_varredura,
        coeficiente_aerodinamico,
        eficiencia,
        verbose, 
):
    # Trata verbose...
    def depuracao(texto):
        if verbose.upper() == 'TRUE':
            print(texto)

    depuracao('(execute_gera_bd_potencia_vento)\n Ler dados de entrada...')

    df = pd.read_csv(filename_input, sep=';', index_col=0)
    if column_input not in df.columns:
        return print(f'"{column_input}" não pertence ao arquivo de entrada.')

    depuracao('(execute_gera_bd_potencia_vento)\n Adiciona coluna...')

    cte = 0.5 * densidade_do_ar * area_varredura * coeficiente_aerodinamico * eficiencia
    df[column_output] = cte * df[column_input]**3

    depuracao('(execute_gera_bd_potencia_vento)\n Concluído!')

    return df



@click.command()
@click.option(
    '--filename_input', 
    default=filename_input_dft,
    help='''
        Nome do arquivo de entrada em que consta a coluna de velocidade de vento.

        Exemplo: "C:/Projeto/Resultados/dados_pb.csv"
    ''',
)
@click.option(
    '--column_input', 
    default=column_input_dft,
    help='''
        Nome da coluna em que estão os dados de velocidade de vento no arquivo 
        de entrada lido.
    ''',
)
@click.option(
    '--filename_output', 
    default=filename_output_dft, 
    help='''
        Nome do arquivo de saída com todas as informações do arquivo de entrada,
        mais a coluna da potência de vento.

        Exemplo: "C:/Projeto/Resultados/dados_pb_com_pot_vento.csv"
    ''',
)
@click.option(
    '--column_output', 
    default=column_output_dft,
    help='''
        Nome da coluna em que devem ser salvos os dados de potência de vento.
    ''',
)
@click.option(
    '--densidade_do_ar', 
    default=densidade_do_ar_dft, 
    help='''
        Densidade do ar, em kg/m³.

        Exemplo: 1.225 (temperatura de 15°C ao nível do mar).
    ''',
)
@click.option(
    '--area_varredura', 
    default=area_varredura_dft, 
    help='''
        Área de varredura da turbina eólica, em m².

        Exemplo: 1521 (turbina Enercon E-44).
    ''',
)
@click.option(
    '--coeficiente_aerodinamico', 
    default=coeficiente_aerodinamico_dft, 
    help='''
        Coeficiente Aerodinâmico, sem dimensão.

        Exemplo: 0.45 (típico).
    ''',
)
@click.option(
    '--eficiencia', 
    default=eficiencia_dft, 
    help='''
        Eficiência (varia entre 0.93 e 0.98).

        Exemplo: 0.93 (valor conservativo).
    ''',
)
@click.option(
    '--verbose', 
    default=verbose_dft, 
    help='Flag que habilita impressão de detalhes da execução.',
)
def cli_execute_gera_bd_potencia_vento(
        filename_input, 
        column_input,
        filename_output,
        column_output,
        densidade_do_ar,
        area_varredura,
        coeficiente_aerodinamico,
        eficiencia,
        verbose, 
):
    # Trata verbose...
    def depuracao(texto):
        if verbose.upper() == 'TRUE':
            print(texto)

    depuracao(f'')
    depuracao(f'Resumo dos parâmetros recebidos:\n')
    depuracao(f'{filename_input = }')
    depuracao(f'{column_input = }')
    depuracao(f'{filename_output = }')
    depuracao(f'{column_output = }')
    depuracao(f'{densidade_do_ar = }')
    depuracao(f'{area_varredura = }')
    depuracao(f'{coeficiente_aerodinamico = }')
    depuracao(f'{eficiencia = }')
    depuracao(f'{verbose = }')
    depuracao(f'-----\n')

    df = execute_gera_bd_potencia_vento(
        filename_input, 
        column_input,
        column_output, 
        densidade_do_ar, 
        area_varredura, 
        coeficiente_aerodinamico,
        eficiencia,
        verbose,
    )

    depuracao('(cli_execute_gera_bd_potencia_vento)\n Amostra do arquivo gerado:')
    depuracao(df.head())

    df.to_csv(filename_output, sep=';')

    depuracao('Concluído!')



if __name__ == '__main__':
    cli_execute_gera_bd_potencia_vento()


# Teste com "Parâmetros Default": 
# (ambiente_virtual) caminho>
# python cli_Gera_BD_Potencia_Vento.py

# ==============================================================================

# Teste para "Depuração 01": 
# - Liga verbose.
# (ambiente_virtual) caminho>
# python cli_Gera_BD_Potencia_Vento.py --verbose True

# ==============================================================================
