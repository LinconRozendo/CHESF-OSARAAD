import json
import numpy as np
import pandas as pd
from distutils.dir_util import mkpath


from api_nasa import get_nasa_point


params = ['QV2M',
          'RH2M',
          'PS',
          'T2M',
          'T2M_MIN',
          'T2M_MAX',
          'WS10M',
          'WS50M',
          'WS10M_MAX',
          'WS50M_MAX',
          'WS10M_MIN',
          'WS50M_MIN']


dict_fcns = {
    'QV2M': np.mean,
    'RH2M': np.mean,
    'PS': np.mean,
    'T2M': np.mean,
    'T2M_MIN': np.mean,
    'T2M_MAX': np.mean,
    'WS10M': np.mean,
    'WS50M': np.mean,
    'WS10M_MAX': np.mean,
    'WS50M_MAX': np.mean,
    'WS10M_MIN': np.mean,
    'WS50M_MIN': np.mean,
    'T2M_MIN_MINIMO': np.min,
    'T2M_MAX_MAXIMO': np.max,
    'WS10M_MAX_MAXIMO': np.max,
    'WS50M_MAX_MAXIMO': np.max,
    'WS10M_MIN_MINIMO': np.min,
    'WS50M_MIN_MINIMO': np.min,
}


def to_dataFrame(data):
    df = pd.DataFrame.from_dict(data['properties']['parameter'])
    point = data['geometry']['coordinates']
    return point, df


def remove_outliers(df):
    df = df.replace(-999, np.nan)
    return df.interpolate()


def resample_MBTSAH(df):
    df.index = pd.to_datetime(df.index)

    df['T2M_MIN_MINIMO'] = df['T2M_MIN']
    df['T2M_MAX_MAXIMO'] = df['T2M_MAX']
    df['WS10M_MAX_MAXIMO'] = df['WS10M_MAX']
    df['WS50M_MAX_MAXIMO'] = df['WS50M_MAX']
    df['WS10M_MIN_MINIMO'] = df['WS10M_MIN']
    df['WS50M_MIN_MINIMO'] = df['WS50M_MIN']

    df_mes = df.resample('M').agg(dict_fcns)
    df_bim = df.resample('2M').agg(dict_fcns)
    df_tri = df.resample('3M').agg(dict_fcns)
    df_sem = df.resample('6M').agg(dict_fcns)
    df_ano = df.resample('12M').agg(dict_fcns)

    aux = pd.DataFrame(df.agg(dict_fcns), columns=[df.index[-1]])
    df_his = aux.transpose()

    return df_mes, df_bim, df_tri, df_sem, df_ano, df_his


def save(point, df_mes, df_bim, df_tri, df_sem, df_ano, df_his, foldername):
    name_file = f"{point[0]}_{point[1]}"
    df_mes.to_csv(f'{foldername}/mensal/{name_file}.csv', date_format='%Y%m%d')
    df_bim.to_csv(f'{foldername}/bimestral/{name_file}.csv', date_format='%Y%m%d')
    df_tri.to_csv(f'{foldername}/trimestral/{name_file}.csv', date_format='%Y%m%d')
    df_sem.to_csv(f'{foldername}/semestral/{name_file}.csv', date_format='%Y%m%d')
    df_ano.to_csv(f'{foldername}/anual/{name_file}.csv', date_format='%Y%m%d')
    df_his.to_csv(f'{foldername}/histórico/{name_file}.csv', date_format='%Y%m%d')
    # with open(f'{foldername}/histórico/{name_file}.json', mode='w') as f:
    #     json.dump(df_his.to_dict(), f)


def pipeline(lat_lon, start_date, end_date, foldername):
    mkpath(foldername + '/mensal')
    mkpath(foldername + '/bimestral')
    mkpath(foldername + '/trimestral')
    mkpath(foldername + '/semestral')
    mkpath(foldername + '/anual')
    mkpath(foldername + '/histórico')
    data = get_nasa_point(lat_lon, params, start_date, end_date, 'DAILY')
    point, df = to_dataFrame(data)
    df = remove_outliers(df)
    df_mes, df_bim, df_tri, df_sem, df_ano, df_his = resample_MBTSAH(df)
    save(point, df_mes, df_bim, df_tri, df_sem, df_ano, df_his, foldername)
