import click
import time
import datetime
import os

@click.command()
@click.option('--nro', default=3, help='Número que devemos calcular o fatorial.')
@click.option('--verbose', default=True, help='Flag que habilita impressão de detalhes da execução.')
def executa(nro: int, verbose: bool):

    if verbose.upper() == 'TRUE':
        print('Rotina executa de cli_Fatorial em execução...')

    aux = 1
    for i in range(nro,1,-1):
        aux = aux * i

    if verbose.upper() == 'TRUE':
        print('Terminou!')

    print(f'O valor calculado foi {aux}')

if __name__ == '__main__':
    executa()
