from time import sleep
from typing import Dict, List, Text, Tuple, Union

import pandas as pd
from numpy.random import randn
from requests import Response, get
from requests.exceptions import Timeout


def _get(link: str, params: Union[Dict, None] = None) -> Response:
    while True:
        try:
            response = get(link, params, timeout=30)
        except Timeout:
            continue
        code = response.status_code

        if code == 200:
            return response
        elif code == 504:
            t = abs(10+randn())
        else:
            t = abs(60*(5 + randn()))
        print(f'Status code: {code}')
        print(f'Tentando novamente em {t:.0f} segundos')
        sleep(t)


def get_nasa_point(lat_lon: Tuple,
                   params: Union[List, Text],
                   start_date: int,
                   end_date: int,
                   temp_average: Text,
                   outputList: Union[List, Text] = 'CSV') -> Dict:

    lat, lon = lat_lon
    if isinstance(params, List):
        params = ','.join(params)

    if isinstance(outputList, List):
        outputList = ','.join(outputList)

    payload = {
        'start': start_date,
        'end': end_date,
        'request': 'execute',
        'identifier': 'SinglePoint',
        'latitude': lat,
        'longitude': lon,
        'community': 'SB',
        'parameters': params,
        'tempAverage': temp_average,
        'outputList': outputList,
        'user': 'UFPB'
    }
    base = 'https://power.larc.nasa.gov/api/temporal/daily/point'

    response = _get(base, payload)

    return response.json()
