import requests
import json
import pandas as pd

####
#   Este arquivo tem como intuito receber um GeoJSON com dados para todas as regiões do Brasil e filtrar apenas para o NORDESTE brasileiro
####

# Recebendo o link e transformando-o em JSON
response = requests.get('https://raw.githubusercontent.com/fititnt/gis-dataset-brasil/master/municipio/geojson/municipio.json')
all_json = response.json()

# Inicializando as variáveis responsáveis por controlar o while
notNe = True
cont = 0

###
#   O while vai funcionar enquanto existir dados para outras regiões além do nordeste brasileiro, quando todos os dados
#   presentes no GeoJSON forem apenas do nordeste, o while será desligado
# 
#   Funcionamento: será verificando em cada registro a sua região, caso não for igual a "Nordeste" esse registro será apagado.
#   A variável cont será a responsável por percorrer todos os registros.   
###
while notNe:
    try:

        if all_json['features'][cont]['properties']['REGIAO'] != "Nordeste":
            all_json['features'].pop(cont)
            cont = 0
        else:
            cont = cont + 1

    except IndexError:
        notNe = False

##
## Trecho de códgio que cria um arquivo GeoJSON com dados apenas do nordeste
##
#with open('municipiosNordeste.json', 'w', encoding='utf8') as f:
    #json.dump(all_json, f, ensure_ascii=False)

##
## Verificar se o arquivo com os dados filtrados do GeoJSON está funcionando.
##
with open('municipiosNordeste.json') as j:
    municipiosNordeste = json.load(j)

print(type(municipiosNordeste))

