import glob
import json
import pandas as pd
import matplotlib.pyplot as plt
import folium
import plotly.express as px
import numpy as np
from collections import Counter
import csv 
import os
import plotly.graph_objects as go
import warnings
import seaborn as sns
warnings.filterwarnings("ignore")

#Crear df con los json
def crear_data_frame():
    ruta = "C:/Users/andre/Desktop/Chill_Havana_Project/Jsons"
    data = []
    for archivo in glob.glob(ruta + "/*.json"):
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = json.load(f)
            data.append(contenido)
            
    df = pd.DataFrame(data)
    return df

#Retorna si un lugar tiene Instagram y Facebook
def social_networks(contact):
    return bool(contact.get('instagram')) and bool(contact.get('facebook'))

#Ver si un lugar tiene tipos únicos de comida
def tiene_tipo_unico(cuisine_list): 
    if isinstance(cuisine_list, list): 
        return any(tipo in tipos_unicos.values for tipo in cuisine_list) # True si hay algun tipo de cocina unico
    return False 

#Se obtiene el tipo de comida que hay en la lista "cuisine" si este es unico
def obtener_tipo_unico(cuisine_list): 
    for tipo in cuisine_list:
        if tipo in tipos_unicos.values:
            return tipo
    return None

#Evidentemente cuenta los establecimientos que tienen pizza
def contar_establecimientos_con_pizza():
    count = 0
    for index, row in df.iterrows(): 
        if isinstance(row['menu'], dict) and 'main_courses' in row['menu']:
            main_courses = row['menu']['main_courses']
            if isinstance(main_courses, dict) and 'items' in main_courses:
                if len(main_courses['items']) > 0:
                    if any('pizza' in item['name'].lower() for item in main_courses['items']):
                        count += 1
    return count

#Ver si un lugar tiene desayuno en su menu
def tiene_desayuno(menu):
    if isinstance(menu, dict): #Ver si 'breakfasts' es un dict y contiene una lista no vacía
        if isinstance(menu.get('breakfasts'), dict) and 'items' in menu['breakfasts']:
            return len(menu['breakfasts']['items']) > 0
    return False

#Ver si un lugar tiene ofertas especiales en su menu
def tiene_ofertas_especiales(menu):
    if isinstance(menu, dict): 
        if isinstance(menu.get('special_offers'), list) and menu['special_offers']:#Ver si special offers es una list y no está vacía
            return True
    return False

#Ver si un lugar tiene bebidas alcoholicas en menu/drinks
def tiene_alcohol(menu):
    if isinstance(menu.get('drinks'), dict): 
        alcoholic = menu['drinks'].get('alcoholic') 
        if isinstance(alcoholic, list):
            return len(alcoholic) > 0  #True si hay elementos en la lista
        elif isinstance(alcoholic, bool): 
            return alcoholic #si es un bool, entonces es False, por lo q retorna eso mismo
    return False

#Ver si un lugar tiene postres en su menu
def offers_desserts(menu):
    if isinstance(menu, dict) and 'desserts' in menu:
        desserts = menu['desserts']
        if isinstance(desserts, dict) and 'items' in desserts and isinstance(desserts['items'], list):
            return len(desserts['items']) > 0
    return False

#Funcion para sacar el plato principal mas costoso
def platillo_mas_costoso(row):
    if 'main_courses' in row['menu'] and isinstance(row['menu']['main_courses'], dict):
        items = row['menu']['main_courses'].get('items', [])
        if items:
            max_precio = -1
            platillo_costoso = None
            for item in items:
                precio_actual = item.get('price')
                if precio_actual is not None and isinstance(precio_actual, (int, float)):
                    precio_actual = float(precio_actual)  # Convertir a float
                    if (item['price'], (int, float)):
                        precio_actual = float(item['price'])
                        if precio_actual > max_precio:
                            max_precio = precio_actual
                            platillo_costoso = item['name']
            return platillo_costoso, max_precio
    return None, 0

#Funcion para aplicar la funcion platillo_mas_costoso al df
def aplicar_funcion(df_copia):
    platillos = []
    precios = []
    for index, row in df_copia.iterrows():
        platillo, precio = platillo_mas_costoso(row)
        platillos.append(platillo)
        precios.append(precio)   
    df_copia['platillo_mas_costoso'] = platillos
    df_copia['precio'] = precios    
    return df_copia
        
#Funcion para sacar el plato principal menos costoso
def platillo_menos_costoso(row):
    if 'main_courses' in row['menu'] and isinstance(row['menu']['main_courses'], dict):
        items = row['menu']['main_courses'].get('items', [])
        if items:
            min_precio = float('inf')
            platillo_barato = None
            for item in items:
                precio_actual = item.get('price')
                if precio_actual is not None and isinstance(precio_actual, (int, float)):
                    precio_actual = float(precio_actual)  # Convertir a float
                    if (item['price'], (int, float)):
                        precio_actual = float(item['price'])
                        if precio_actual <min_precio:
                            min_precio = precio_actual
                            platillo_barato = item['name']
                return platillo_barato, min_precio
    return None, 1000000000

#Funcion para aplicar la funcion platillo_menos_costoso al df
def aplicar_funcion_(df_copia):
    platillos = []
    precios = []
    for index, row in df_copia.iterrows():
        platillo, precio = platillo_menos_costoso(row)
        platillos.append(platillo)
        precios.append(precio)
    df_copia['platillo_menos_costoso'] = platillos
    df_copia['precio'] = precios
    return df_copia

#Encuentra los diferentes precios de un plato
def check_price_range(aux, plato): 
    precios = []
    for i in aux:
        if i != "drinks" and i != "special_offers":
            if aux[i]:
                for j in aux[i]["items"]:
                    if (
                        j["name"].lower().strip().find(plato.lower().strip()) != -1
                    ):
                        precios.append(j["price"])
    return precios

#Halla el precio maximo y minimo de ese plato en cada municipio donde se oferta
def filter_price_range(_df, plato):
    municipios = _df['district'].unique()  #Obtiene todos los municipios
    resultados = []

    for municipio in municipios:
        aux = _df[_df['district'] == municipio]  #Filtra por municipio
        if len(aux) == 0:
            continue
        
        precios = [] 
        for index, row in aux.iterrows():
            precios += check_price_range(row['menu'], plato)
            
        if precios: 
            min_price = min(precios)
            max_price = max(precios)
            resultados.append({
                'municipio': municipio,
                'plato': plato,
                'precio_minimo': min_price,
                'precio_maximo': max_price
            })
    return pd.DataFrame(resultados) if resultados else "No hay resultados"

#Hallar precio promedio de un plato en cada municipio donde se oferta
def filter_average_price(_df, plato):
    municipios = _df['district'].unique()  
    resultados = []
    for municipio in municipios:
        aux = _df[_df['district'] == municipio]  
        if len(aux) == 0:
            continue
        precios = [] 
        for index, row in aux.iterrows():
            precios += check_price_range(row['menu'], plato)   
        if precios: 
            average_price = round(sum(precios) / len(precios))  # Calcular y redondear precio promedio
            resultados.append({
                'municipio': municipio,
                'plato': plato,
                'precio_promedio': average_price
            })
    return pd.DataFrame(resultados) if resultados else "No hay resultados"

#Ver si un lugar tiene el plato solicitado a un precio <= que el establecido
def check_name_price(aux, plato, price): 
    for i in aux:
        if i != "drinks" and i != "special_offers":
            if aux[i]:
                for j in aux[i]["items"]:
                    if (
                        j["name"].lower().strip().find(plato.lower().strip()) != -1
                        and j["price"] <= price
                    ):
                        return True
        elif i == "special_offers":
            if aux[i]:
                for j in aux[i]:
                    if (
                        j["name"].lower().strip().find(plato.lower().strip()) != -1
                        and j["price"] <= price
                    ):
                        return True
        else:
            if aux[i]:
                for j in aux[i]:
                    if aux[i][j]:
                        for k in aux[i][j]:
                            if (
                                k["name"].lower().strip().find(plato.lower().strip()) != -1
                            and k["price"] <= price
                            ):
                                return True
    return False

#chequea si el restaurante tiene el servicio pedido
def check_service(aux, servicio): 
    return aux[servicio]

#revisa si el lugar que tiene el plato y el servicio solicitado y cumple con el presupuesto es del muncipio pedido
def filter(_df, plato, price, servicios, municipio):
    aux = _df[_df['district'] == municipio]
    if len(aux) == 0:
        return "No hay resultado"
    aux["cumple_name_price"] = aux["menu"].apply(
        check_name_price, plato = plato, price = price # verifica algun restaurante del "menu" cumple con  nombre y precio, si cumple se guarda en 'cumple_name_price'.
    ) 
    aux["cumple_service"] = aux['services'].apply(check_service, servicio = servicios) #hace lo mismo con "services"
    result = aux[(aux["cumple_name_price"] ==  True) & (aux["cumple_service"] == True)] #se quedan solo los que cumplen ambas condiciones
    if len(result) != 0:
        r = result.sort_values(by = "rating") #los resultados se ordenan por rating
        return r.iloc[0] #se queda el de mejor rating
    return "No hay resultado"

#recomienda las rutas de guagua segun destino y origen solicitado
def ruta_ideal(origen, destino, df):
    x = df[(df['Origin'] == origen) & (df['Destination'] == destino)]
    if len(x) != 0:
        print(f"La/s ruta/s desde {origen} a {destino} es/son:")
        print(f"{x['Bus name']}")
    else:
        print(f"No hay rutas directas de {origen} a {destino}, pero aquí se ofrecen otras rutas que llegan al destino")
        y = df[df['Destination'] == destino]
        if len(y) != 0:
            print(f"La/s ruta/s a {destino} es/son:")
            print(f"{y[['Bus name', 'Origin']]}")
        else:
            print(f"No hay rutas a {destino}")
            
#cargar un archivo txt externo
def load_dict(ruta_dict):
    with open(ruta_dict, 'r', encoding='utf-8') as f:
        return set(word.strip().lower() for word in f.readlines())

#ver si un nombre de un restaurante esta en ingles
def es_nombre_en_ingles(nombre):
    if isinstance(nombre, str):
        palabras = nombre.lower().split()
        resultados = [palabra for palabra in palabras if palabra not in diccionario_ingles]
        return len(resultados) == 0  #True si todas estan en el dict
    return False 

#ver si un lugar tiene disable_support
def tiene_soporte(services):
    return services['disable_support']

#crear df con los lugares que ofrecen servicio 'disable_support' y sus respectivos municipios
def establecimientos_con_soporte(municipio):
    resultados = df[(df['district'].str.lower() == municipio.lower()) & (df['services'].apply(tiene_soporte))]
    if len(resultados) != 0:
        return resultados[['name', 'type_of_establishment']]
    else:
        print(f"No se encontraron lugares con soporte para discapacitados en {municipio}")