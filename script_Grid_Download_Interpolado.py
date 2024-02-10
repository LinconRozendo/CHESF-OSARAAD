import cli_Gera_Grid
import cli_Gera_BD_Download
import cli_Gera_BD_Interpolado
import cli_Gera_BD_Potencia_Vento


def execute():

    verbose = 'True'

    print('Início...\n')

    filename_gera_grid_base = './dados/municipiosPB.json'

    filename_gera_grid_download = './dados/pontos_para_download_pb.csv'
    filename_gera_grid_interpolado = './dados/pontos_para_interpolacao_pb.csv'

    filename_dados_apos_download = './dados/dados_apos_download_pb.csv'
    filename_dados_interpolados = './dados/dados_interpolados_pb.csv'
    filename_dados_com_pot_vento = './dados/dados_interpolados_pb_com_pot_vento.csv'

    print('Etapa 1: Gera_Grid Base.\n')

    gdf_base = cli_Gera_Grid.execute_gera_grid(
        filename_input = filename_gera_grid_base, 
        lat_min = -999.0,
        lon_min = -999.0,
        lat_max = -999.0,
        lon_max = -999.0,
        resolution = 0.50, 
        border = 0.50, 
        verbose = verbose, 
        filename_output_fig_base = '', 
        filename_output_fig_intermediario = '', 
        filename_output_fig_final = '',
        filename_output_map_final = '',
    )
    gdf_base.to_csv(filename_gera_grid_download, index=False, sep=';')

    print('Etapa 2: Gera_Grid Interpolação.\n')

    gdf_interpolado = cli_Gera_Grid.execute_gera_grid(
        filename_input = filename_gera_grid_base, 
        lat_min = -999.0,
        lon_min = -999.0,
        lat_max = -999.0,
        lon_max = -999.0,
        resolution = 0.20, 
        border = -1, 
        verbose = verbose, 
        filename_output_fig_base = '', 
        filename_output_fig_intermediario = '', 
        filename_output_fig_final = '',
        filename_output_map_final = '',
    )
    gdf_interpolado.to_csv(filename_gera_grid_interpolado, index=False, sep=';')

    print('Etapa 3: Gera_BD_Download.\n')

    df_mes, df_bim, df_tri, df_sem, df_ano, df_his = \
        cli_Gera_BD_Download.execute_gera_bd_download(
            filename_input = filename_gera_grid_download, 
            foldername_output = './dados/BD_PB',
            date_initial = 20000101,
            date_final = 20230530,
            verbose = verbose, 
    )
    df_his.to_csv(filename_dados_apos_download, sep=';', date_format='%Y%m%d')

    print('Etapa 4: Gera_BD_Interpolado.\n')

    df_interpolado = cli_Gera_BD_Interpolado.execute_gera_bd_interpolado(
        filename_input_grid_interpolado = filename_gera_grid_interpolado, 
        filename_input_grid_dados = filename_dados_apos_download, 
        algorithm = 'idw',
        date_initial = 20230530,
        date_final = 20230531,
        neighbors = 3,
        idw_p = 1,
        foldername_output_figures = '',
        date_output_figures = -1,
        turnon_grid_interpolado_in_figures = 'False',
        verbose = verbose, 
    )
    df_interpolado.to_csv(filename_dados_interpolados, sep=';', date_format='%Y%m%d')

    print('Etapa 5: Gera_BD_Potencia_Vento.\n')

    df_com_pot_vento = cli_Gera_BD_Potencia_Vento.execute_gera_bd_potencia_vento(
        filename_input = filename_dados_interpolados, 
        column_input = 'WS50M',
        column_output = 'pot_vento', 
        densidade_do_ar = 1.225, 
        area_varredura = 1521, 
        coeficiente_aerodinamico = 0.45,
        eficiencia = 0.93,
        verbose = verbose,
    )
    df_com_pot_vento.to_csv(filename_dados_com_pot_vento, sep=';')

    print('Concluído!\n')



if __name__ == '__main__':
    execute()
