from logging import PlaceHolder
from operator import index
import requests
from bs4 import BeautifulSoup
import pandas as pd
import openpyxl
import streamlit as st
import lxml
import io
import random
import os
from io import BytesIO
import matplotlib.pyplot as plt



st.set_page_config(layout="wide")



user_agent_list = [ 
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36', 
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36', 
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15', 
]

for i in range(1,4): 
	user_agent = random.choice(user_agent_list)

headers = {'User-Agent' : user_agent}



@st.cache_data
def productos():

    mas_links = True
    pagina = 1
    productos = []
    while (mas_links):
        start_url = f"https://aricapetshop.cl/collections/todos?page={pagina}"
        request_session = requests.Session()
        web_page = request_session.get(start_url , headers=headers)
        soup_producto = BeautifulSoup(  web_page.content, 'lxml')

        nombres_producto = soup_producto.find_all('p', class_='grid-product__title')
        precios_producto = soup_producto.find_all('span', class_='price-regular')
        
        for nombre, precio in zip(nombres_producto,precios_producto):
            product_name = nombre.get_text(strip=True)

            if precio:
                product_price = precio.get_text(strip=True)
            else:
                product_price = "0"

            producto = {
                'Nombre': product_name,
                'Precio': product_price
            }

            productos.append(producto)
      

    
        siguiente_link = soup_producto.find(class_='text-center spacer-top-lg')
        
        if(siguiente_link):
            pagina += 1
        else:
            mas_links = False
    return productos


lista_de_productos = productos()
df = pd.DataFrame(data=lista_de_productos)
df['Prod']=df['Nombre'].str.split(' ').str[0]
df['Precio'] = df['Precio'].str.replace(r'[^\d.]', '', regex=True)
df['Precio'] = df['Precio'].str.replace('.', '')
df['Precio'] = df['Precio'].astype(int)





st.title('Analisis de Competencia 🐾')



st.sidebar.header('Filtro por Nombre')
filtro_nombre = st.sidebar.text_input("Ingrese el nombre a filtrar", key='filtro_nombre')

# Obtener el valor anterior del filtro desde la sesión
filtro_nombre_anterior = st.session_state.filtro_nombre if hasattr(st.session_state, 'filtro_nombre') else ""

# Obtener el valor anterior del filtro de nombre desde la sesión
filtro_nombre_anterior = st.session_state.filtro_nombre if hasattr(st.session_state, 'filtro_nombre') else ""


# Si el filtro de nombre ha cambiado, actualizar la sesión y filtrar el DataFrame
if filtro_nombre != filtro_nombre_anterior:
    st.session_state.filtro_nombre = filtro_nombre



# Filtrar el DataFrame por nombre y producto
df_filtrado = df[
    (df['Nombre'].str.contains( filtro_nombre , case=False)) 
]

suma_por_item = df_filtrado.groupby(['Prod'])['Nombre'].count().reset_index()
suma_por_item['Total_Precio'] = df_filtrado.groupby('Prod')['Precio'].sum().reset_index()['Precio']
suma_por_item.rename(columns={'Nombre': 'Cantidad'}, inplace=True)

top_10_productos = suma_por_item.sort_values(by='Total_Precio', ascending=False).head(10)

# Metricas

metrica1 = df_filtrado['Nombre'].value_counts().sum()
metrica2 = df_filtrado['Prod'].nunique()
metrica3 = df_filtrado['Precio'].sum()


# Mostrar los resultados
st.header('Arica Petshop')
if not df_filtrado.empty:
    


    col1,col2,col3=st.columns(3)
    col1.metric(label="Cant. de Productos",value=metrica1)
    col2.metric(label="Cant. de Marcas",value=metrica2)
    col3.metric(label="Monto Total",value=metrica3)

    plt.figure(figsize=(17, 6))
    
    plt.bar(top_10_productos['Prod'], top_10_productos['Total_Precio'])
    for i, monto in enumerate(top_10_productos['Total_Precio']):
        plt.text(i, monto, str(monto), ha='center', va='bottom')

    plt.xlabel('Producto')
    plt.ylabel('Precio')
    plt.xticks(rotation=90, ha='right')
    plt.title('Top 10 Marcas por Monto Total')
    
    st.pyplot(plt)

    st.header('Productos')

    rows = st.columns(2)
    rows[0].dataframe(df_filtrado)
    rows[1].dataframe(suma_por_item)


    
    
    

    # Crear un flujo de bytes para el archivo Excel
    output_excel = BytesIO()
    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
        df_filtrado.to_excel(writer, sheet_name='Productos', index=False)
    
    # Agregar botón de descarga
    st.download_button(
        label='Descargar Excel',
        data=output_excel.getvalue(),
        file_name='productos_filtrados.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
else:
    st.warning('No se encontraron productos con los filtros proporcionados.')

