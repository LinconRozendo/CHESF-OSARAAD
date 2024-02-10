
# os.environ['USE_PYGEOS'] = '0'

import click
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from shapely import wkt
from shapely.ops import unary_union

import folium as fl

from utils import read_geo_generico, gera_quadrados_simples_from_df

# ==============================================================================
# =========================== Parâmetros default ===============================
# ==============================================================================
filename_input_dft = './dados/municipiosPB.json'
filename_output_dft = './dados/output_pb.csv'
lat_min_dft = -999.0
lon_min_dft = -999.0
lat_max_dft = -999.0
lon_max_dft = -999.0
resolution_dft = 0.5
border_dft = 0.5
verbose_dft = 'False'
filename_output_fig_base_dft = ''
filename_output_fig_intermediario_dft = ''
filename_output_fig_final_dft = ''
filename_output_map_final_dft = ''
# ==============================================================================



def salvar_fig_base(df, filename):
    '''
    Gera e salva a figura base.
    '''

    fig, ax = plt.subplots(1, 1, figsize=(20, 20))
    gpd.GeoSeries(df['geometry']).plot(ax=ax, color='red', alpha=0.15)
    gpd.GeoSeries(df['geometry']).boundary.plot(ax=ax, color='black', label='Bordas', alpha=0.60)
    gpd.GeoSeries(df['geometry']).centroid.plot(ax=ax, color='black', label='Centróide', alpha=0.60, markersize=15)

    ax.legend()
    plt.savefig(filename, dpi='figure')

def salvar_fig_intermediario(df, df_grid, filename):
    '''
    Gera e salva a figura intermediária: base + grid inicial.
    '''

    fig, ax = plt.subplots(1, 1, figsize=(20, 20))
    gpd.GeoSeries(df['geometry']).plot(ax=ax, color='red', alpha=0.15)
    gpd.GeoSeries(df['geometry']).boundary.plot(ax=ax, color='black', label='Bordas', alpha=0.60)
    gpd.GeoSeries(df['geometry']).centroid.plot(ax=ax, color='black', label='Centróide', alpha=0.60, markersize=15)
    
    gpd.GeoSeries(df_grid['center_point']).plot(ax=ax, color='#0000CD', markersize=15, label='Pontos Centrais')
    gpd.GeoSeries(df_grid['envelope']).plot(ax=ax, color='gray', label='Envelope Área', alpha=0.25)
    gpd.GeoSeries(df_grid['envelope']).boundary.plot(ax=ax, color='blue', label='Envelope Borda', alpha=0.75)

    ax.legend()
    plt.savefig(filename, dpi='figure')

def salvar_fig_final(df, dff_grid, filename):
    '''
    Gera e salva a figura final: base + grid filtrado.
    '''

    fig, ax = plt.subplots(1, 1, figsize=(20, 20))
    gpd.GeoSeries(df['geometry']).plot(ax=ax, color='red', alpha=0.15)
    gpd.GeoSeries(df['geometry']).boundary.plot(ax=ax, color='black', label='Bordas', alpha=0.60)
    gpd.GeoSeries(df['geometry']).centroid.plot(ax=ax, color='black', label='Centróide', alpha=0.60, markersize=15)

    gpd.GeoSeries(dff_grid['center_point']).plot(ax=ax, color='#0000CD', markersize=15, label='Pontos Centrais')
    gpd.GeoSeries(dff_grid['envelope']).plot(ax=ax, color='gray', label='Envelope Área', alpha=0.25)
    gpd.GeoSeries(dff_grid['envelope']).boundary.plot(ax=ax, color='blue', label='Envelope Borda', alpha=0.75)

    ax.legend()
    plt.savefig(filename, dpi='figure')

def salvar_map_final(df, dff_grid, filename):
    '''
    Gera e salva o mapa final: base + grid filtrado.
    '''

    mapa = fl.Map(location=[-7.129694, -35.867750], zoom_start=5, tiles='OpenStreetMap')

    feature_group = fl.FeatureGroup(name='Base', show=True)
    for _, row in df.iterrows():
        poligono = row['geometry']
        obj = fl.GeoJson(
            data=poligono,
            style_function=lambda x: {
                'fillColor': 'red',
                'color': 'red',
            },
        )
        feature_group.add_child(obj)
    feature_group.add_to(mapa)

    feature_group = fl.FeatureGroup(name='Pontos Centrais', show=True)
    for _, row in dff_grid.iterrows():
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
    for _, row in dff_grid.iterrows():
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

    # Adiciona a caixinha de opções de camadas "layers"
    lc = fl.LayerControl()
    lc.add_to(mapa)

    mapa.save(filename)



def execute_gera_grid(
        filename_input, 
        lat_min, 
        lon_min, 
        lat_max, 
        lon_max,
        resolution, 
        border, 
        verbose, 
        filename_output_fig_base, 
        filename_output_fig_intermediario, 
        filename_output_fig_final,
        filename_output_map_final,
):
    # Trata verbose...
    def depuracao(texto):
        if verbose.upper() == 'TRUE':
            print(texto)
    
    # Observe que fornecer os limites tem prioridade sobre o arquivo input.
    if (lat_min == lat_min_dft and \
        lon_min == lon_min_dft and \
        lat_max == lat_max_dft and \
        lon_max == lon_max_dft):
        
        depuracao('(execute_gera_grid)\n Ler dados de entrada...')
        try:
            df = read_geo_generico(filename_input, index_col=False, verbose=verbose)
        except Exception as e:
            return print(f'Não foi possível ler o arquivo de entrada.\n{str(e)}')

        depuracao('(execute_gera_grid)\n Simplificar dados para ficar apenas com limites geográficos...')
        df = gpd.GeoDataFrame(geometry=gpd.GeoSeries(unary_union(df['geometry'].buffer(0))))

    else:
        
        df = pd.DataFrame()
        df['geometry'] = [f'POLYGON (({lon_min} {lat_min}, {lon_max} {lat_min}, {lon_max} {lat_max}, {lon_min} {lat_max}, {lon_min} {lat_min}))']
        print(f'POLYGON (({lon_min} {lat_min}, {lon_max} {lat_min}, {lon_max} {lat_max}, {lon_min} {lat_max}, {lon_min} {lat_min}))')
        df = gpd.GeoDataFrame(df, geometry=df['geometry'].apply(wkt.loads))


    # Se foi solicitado: Criar a figura do grid base.
    if len(filename_output_fig_base) > 0:
        salvar_fig_base(df, filename_output_fig_base)

    depuracao('(execute_gera_grid)\n Criar o grid intermediário...')
    df_grid = gera_quadrados_simples_from_df(resolution, df, verbose=verbose)

    # Se foi solicitado: Criar a figura do grid intermediário.
    if len(filename_output_fig_intermediario) > 0:
        salvar_fig_intermediario(df, df_grid, filename_output_fig_intermediario)

    if border >= 0:
        depuracao('(execute_gera_grid)\n Criar o grid final considerando borda...')

        # Retira qualquer "quadrado" cuja distância para o mapa base é maior que "border".
        flag = [(df.distance(row['center_point'])[0] < border) for _, row in df_grid.iterrows()]
        dff_grid = df_grid.loc[flag].copy()
    else:
        depuracao('(execute_gera_grid)\n Criar o grid final limitando a área ao arquivo de entrada...')

        # Retira qualquer "quadrado" sem qualquer intersecção com o mapa base.
        flag = [any(df.intersects(row['envelope'])) for _, row in df_grid.iterrows()]
        df_grid = df_grid.loc[flag].copy()

        # Se o "quadrado" extrapola o mapa base:
        # Aplica recorte para respeitar os limites e atualiza o centróide.
        df_grid['geometry'] = df_grid['envelope']

        dff_grid = gpd.GeoDataFrame(gpd.overlay(df, df_grid, how='intersection'))
        dff_grid['envelope'] = dff_grid['geometry']
        dff_grid['center_point'] = dff_grid['geometry'].centroid
        dff_grid = dff_grid.drop(columns=['geometry'])

    # Se foi solicitado: Criar a figura do grid final.
    if len(filename_output_fig_final) > 0:
        salvar_fig_final(df, dff_grid, filename_output_fig_final)

    # Se foi solicitado: Criar o mapa folium do grid final.
    if len(filename_output_map_final) > 0:
        salvar_map_final(df, dff_grid, filename_output_map_final)

    depuracao('(execute_gera_grid)\n Salvar o grid final!\n')
    return dff_grid



@click.command()
@click.option(
    '--filename_input', 
    default=filename_input_dft,
    help='''
        Nome do arquivo gegdaláfico de entrada para criação do grid. 
        Arquivo gegdaláfico aqui significa que possui a coluna "geometry". 
        Não importam as divisões internas desse arquivo, pois será usado o 
        contorno externo. Extensões permitidas: csv, xls, xslx, shp, json, kml.

        Exemplo: "C:/Projeto/Resultados/grid_pb.csv"

        ou

        Link para o arquivo gegdaláfico de entrada para criação do grid.
        Exemplo: "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json"

        Atenção: fornecer limites de lat e lon tem precedência sobre esse arquivo!
    ''',
)
@click.option(
    '--filename_output', 
    default=filename_output_dft, 
    help='''
        Nome do arquivo gegdaláfico de saída com o grid que compreende duas 
        colunas: 
        
        "center_point" com as coordenada dos pontos;
        
        e 
        
        "envelope" com os polígonos quadrados que definem a área de validade 
        de cada ponto.

        O separador do csv é ";".

        Exemplo: "C:/Projeto/Resultados/output_grid_nordeste.csv"
    ''',
)
@click.option(
    '--lat_min', 
    default=lat_min_dft, 
    help='''
        Latitude (y) mínima, em graus.

        Integra a opção de entrar diretamente com as coordenadas externas de 
        interesse, em vez de um arquivo gegdaláfico base. 
    ''',
)
@click.option(
    '--lon_min', 
    default=lon_min_dft, 
    help='''
        Longitude (x) mínima, em graus.

        Integra a opção de entrar diretamente com as coordenadas externas de 
        interesse, em vez de um arquivo gegdaláfico base. 
    ''',
)
@click.option(
    '--lat_max', 
    default=lat_max_dft, 
    help='''
        Latitude (y) máxima, em graus.

        Integra a opção de entrar diretamente com as coordenadas externas de 
        interesse, em vez de um arquivo gegdaláfico base. 
    ''',
)
@click.option(
    '--lon_max', 
    default=lon_max_dft, 
    help='''
        Longitude (x) máxima, em graus.

        Integra a opção de entrar diretamente com as coordenadas externas de 
        interesse, em vez de um arquivo gegdaláfico base. 
    ''',
)
@click.option(
    '--resolution', 
    default=resolution_dft, 
    help='Resolução do grid de saída, em graus.',
)
@click.option(
    '--border', 
    default=border_dft, 
    help='''
        Tamanho da borda do grid de saída, em graus.

        Se a borda for definida negativa:

        O grid passa a ser gerado visando preencher o mapa base, deixando de 
        ser formado apenas por "quadrados" e de ter qualquer borda externa 
        além da delimitação do desenho base.
    ''',
)
@click.option(
    '--verbose', 
    default=verbose_dft, 
    help='Flag que habilita impressão de detalhes da execução.',
)
@click.option(
    '--filename_output_fig_base', 
    default=filename_output_fig_base_dft, 
    help='Se for fornecido: Nome do arquivo de saída com o mapa base - png.',
)
@click.option(
    '--filename_output_fig_intermediario', 
    default=filename_output_fig_intermediario_dft, 
    help='Se for fornecido: Nome do arquivo de saída com o mapa intermediário - png.',
)
@click.option(
    '--filename_output_fig_final', 
    default=filename_output_fig_final_dft, 
    help='Se for fornecido: Nome do arquivo de saída com o mapa final - png.',
)
@click.option(
    '--filename_output_map_final', 
    default=filename_output_map_final_dft, 
    help='Se for fornecido: Nome do arquivo de saída com o mapa final - html.',
)
def cli_execute_gera_grid(
        filename_input, 
        filename_output,
        lat_min, 
        lon_min, 
        lat_max, 
        lon_max,
        resolution, 
        border, 
        verbose, 
        filename_output_fig_base, 
        filename_output_fig_intermediario, 
        filename_output_fig_final,
        filename_output_map_final,
):
    # Trata verbose...
    def depuracao(texto):
        if verbose.upper() == 'TRUE':
            print(texto)

    depuracao(f'')
    depuracao(f'Resumo dos parâmetros recebidos:\n')
    depuracao(f'{filename_input = }')
    depuracao(f'{filename_output = }')
    depuracao(f'{lat_min = }')
    depuracao(f'{lon_min = }')
    depuracao(f'{lat_max = }')
    depuracao(f'{lon_max = }')
    depuracao(f'{resolution = }')
    depuracao(f'{border = }')
    depuracao(f'{verbose = }')
    depuracao(f'{filename_output_fig_base = }')
    depuracao(f'{filename_output_fig_intermediario = }')
    depuracao(f'{filename_output_fig_final = }')
    depuracao(f'{filename_output_map_final = }')
    depuracao(f'-----\n')

    dff_grid = execute_gera_grid(
        filename_input, 
        lat_min, 
        lon_min, 
        lat_max, 
        lon_max,
        resolution, 
        border, 
        verbose, 
        filename_output_fig_base, 
        filename_output_fig_intermediario, 
        filename_output_fig_final, 
        filename_output_map_final,
    )

    depuracao('(cli_execute_gera_grid)\n Amostra do arquivo gerado:')
    depuracao(dff_grid.head())

    dff_grid.to_csv(filename_output, index=False, sep=';')

    depuracao('Concluído!')



if __name__ == '__main__':
    cli_execute_gera_grid()



# Teste com "Parâmetros Default": 
# - Usa municipiosPB.json como entrada.
# (ambiente_virtual) caminho>
# python cli_Gera_Grid.py

# ==============================================================================

# Teste com verbose ligado: 
# - Usa municipiosPB.json como entrada.
# (ambiente_virtual) caminho>
# python cli_Gera_Grid.py --verbose True

# ==============================================================================

# Teste com exportação de figuras e mapa: 
# - Usa municipiosPB.json como entrada.
# (ambiente_virtual) caminho>
# python cli_Gera_Grid.py --filename_output_fig_base "./dados/figure_base_depuração.png" --filename_output_fig_intermediario "./dados/figure_intermediario_depuração.png" --filename_output_fig_final "./dados/figure_final_depuração.png" --filename_output_map_final "./dados/map_final_depuração.html"

# ==============================================================================

# Template fornecendo filename_input e "Todos os Parâmetros": PB
# municipiosPB.json
# (ambiente_virtual) caminho>
# python cli_Gera_Grid.py --filename_input "./dados/municipiosPB.json" --filename_output "./dados/output_pb.csv" --resolution 0.5 --border 0.5 --verbose True --filename_output_fig_base "./dados/figure_base_depuração_pb.png" --filename_output_fig_intermediario "./dados/figure_intermediario_depuração_pb.png" --filename_output_fig_final "./dados/figure_final_depuração_pb.png" --filename_output_map_final "./dados/map_final_depuração_pb.html"

# Template fornecendo filename_input e "Todos os Parâmetros": NE
# municipiosNE.json
# (ambiente_virtual) caminho>
# python cli_Gera_Grid.py --filename_input "./dados/municipiosNE.json" --filename_output "./dados/output_ne.csv" --resolution 0.5 --border 0.5 --verbose True --filename_output_fig_base "./dados/figure_base_depuração_ne.png" --filename_output_fig_intermediario "./dados/figure_intermediario_depuração_ne.png" --filename_output_fig_final "./dados/figure_final_depuração_ne.png" --filename_output_map_final "./dados/map_final_depuração_ne.html"

# Template fornecendo filename_input e "Todos os Parâmetros": BR
# arquivo da internet com o Brasil.
# (ambiente_virtual) caminho>
# python cli_Gera_Grid.py --filename_input "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json" --filename_output "./dados/output_br.csv" --resolution 0.5 --border 0.5 --verbose True --filename_output_fig_base "./dados/figure_base_depuração_br.png" --filename_output_fig_intermediario "./dados/figure_intermediario_depuração_br.png" --filename_output_fig_final "./dados/figure_final_depuração_br.png" --filename_output_map_final "./dados/map_final_depuração_br.html"

# ==============================================================================

# Template fornecendo limites de lat e lon e "Todos os Parâmetros": Linha sobre PB
# (ambiente_virtual) caminho>
# python cli_Gera_Grid.py --lat_min -7.0 --lon_min -39.0 --lat_max -7.0 --lon_max -34.5 --filename_output "./dados/output_pb.csv" --resolution 0.25 --border 0.25 --verbose True --filename_output_fig_base "./dados/figure_base_depuração_pb.png" --filename_output_fig_intermediario "./dados/figure_intermediario_depuração_pb.png" --filename_output_fig_final "./dados/figure_final_depuração_pb.png" --filename_output_map_final "./dados/map_final_depuração_pb.html"

# ==============================================================================

# Template fornecendo filename_input, "Todos os Parâmetros" e borda NEGATIVA: PB
# municipiosPB.json
# (ambiente_virtual) caminho>
# python cli_Gera_Grid.py --filename_input "./dados/municipiosPB.json" --filename_output "./dados/output_pb_sem_borda.csv" --resolution 0.05 --border -1 --verbose True --filename_output_fig_base "./dados/figure_base_depuração_pb_sem_borda.png" --filename_output_fig_intermediario "./dados/figure_intermediario_depuração_pb_sem_borda.png" --filename_output_fig_final "./dados/figure_final_depuração_pb_sem_borda.png" --filename_output_map_final "./dados/map_final_depuração_pb.html"

# Template fornecendo filename_input, "Todos os Parâmetros" e borda NEGATIVA: NE
# municipiosNE.json
# (ambiente_virtual) caminho>
# python cli_Gera_Grid.py --filename_input "./dados/municipiosNE.json" --filename_output "./dados/output_ne_sem_borda.csv" --resolution 0.05 --border -1 --verbose True --filename_output_fig_base "./dados/figure_base_depuração_ne_sem_borda.png" --filename_output_fig_intermediario "./dados/figure_intermediario_depuração_ne_sem_borda.png" --filename_output_fig_final "./dados/figure_final_depuração_ne_sem_borda.png" --filename_output_map_final "./dados/map_final_depuração_ne_sem_borda.html"

# Template fornecendo filename_input, "Todos os Parâmetros" e borda NEGATIVA: BR
# municipiosBR.json
# (ambiente_virtual) caminho>
# python cli_Gera_Grid.py --filename_input "./dados/municipiosBR.json" --filename_output "./dados/output_br_sem_borda.csv" --resolution 0.05 --border -1 --verbose True --filename_output_fig_base "./dados/figure_base_depuração_br_sem_borda.png" --filename_output_fig_intermediario "./dados/figure_intermediario_depuração_br_sem_borda.png" --filename_output_fig_final "./dados/figure_final_depuração_br_sem_borda.png" --filename_output_map_final "./dados/map_final_depuração_br_sem_borda.html"

# ==============================================================================

# Apresentação de slides:
# python cli_Gera_Grid.py --lat_min -5.0 --lon_min -35.0 --lat_max -6.0 --lon_max -37.0 --filename_output "./dados/output_rn.csv" --resolution 0.25 --border 0.25 --verbose True --filename_output_fig_base "./dados/figure_base_rn.png" --filename_output_fig_intermediario "./dados/figure_intermediario_rn.png" --filename_output_fig_final "./dados/figure_final_rn.png" --filename_output_map_final "./dados/map_final_rn.html"
# python cli_Gera_Grid.py --lat_min -5.2 --lon_min -35.5 --lat_max -5.8 --lon_max -36.5 --filename_output "./dados/output_rn_menor.csv" --resolution 0.15 --border -1 --verbose True --filename_output_map_final "./dados/map_final_rn_menor.html"
