#!/usr/bin/env python
# coding: utf-8

# In[10]:


import streamlit as st
import pandas as pd
import requests
from tqdm import tqdm
from streamlit_jupyter import StreamlitPatcher
from io import BytesIO
from dotenv import load_dotenv
import os

# Cargar las variables de entorno
load_dotenv()


# Patching Streamlit to work in Jupyter
StreamlitPatcher().jupyter()

# Credenciales desde variables de entorno
username = os.getenv('USERNAME')
grant_type = os.getenv('GRANT_TYPE')
password = os.getenv('PASSWORD')


# Función para obtener el token
def obtener_token():
    token_url = 'https://ruesapi.rues.org.co/Token'
    data = {
    'username': username,
    'password': password,
    'grant_type': grant_type
    }
    response = requests.get(token_url, data=data)
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info.get('access_token')
        return token_info.get('access_token')
    else:
        print('No se pudo obtener el token.')
        return None

# Función para realizar la consulta por NIT
def consultar_nits(file_path, access_token):
    NITS = pd.read_excel(file_path)
    resultados_temporales = []

    for index, row in tqdm(NITS.iterrows(), total=NITS.shape[0]):
        try:
            nit_a_consultar = int(row['NIT sin digito'])
            usuario2 = 'pruebas'
            consulta_url = f'https://ruesapi.rues.org.co/api/consultasRUES/ConsultaNIT?usuario={usuario2}&nit={nit_a_consultar}&dv'
            
            consulta_data = {'nit': nit_a_consultar, 'usuario': usuario2}
            headers = {'Authorization': f'Bearer {access_token}'}
            consulta_response = requests.post(consulta_url, headers=headers, data=consulta_data)

            if consulta_response.status_code == 200:
                json_data = consulta_response.json()
                nit = json_data['nit']
                registros = json_data['registros']
                df = pd.json_normalize(registros)
                df.insert(0, 'nit', nit)
                vinculos_df = pd.json_normalize(df['vinculos'].explode('vinculos'))
                vinculos_df.rename(columns={'numero_identificacion': 'Id_Representante'}, inplace=True)
                Infofinanciera_df = pd.json_normalize(df['informacionFinanciera'].explode('informacionFinanciera'))
                df.drop(['informacionFinanciera', 'vinculos'], axis=1, inplace=True)
                df = pd.concat([df, Infofinanciera_df, vinculos_df], axis=1)
                df['fecha_respuesta'] = json_data['fecha_respuesta']
                df['hora_respuesta'] = json_data['hora_respuesta']

                column_select = ['nit',
                             'codigo_camara',
                             'camara',
                             'matricula',
                             'inscripcion_proponente',
                             'razon_social',
                             'tipo_identificacion',
                             'numero_identificacion',
                             'digito_verificacion',
                             'codigo_estado_matricula',
                             'estado_matricula',
                             'codigo_tipo_sociedad',
                             'tipo_sociedad',
                             'codigo_organizacion_juridica',
                             'organizacion_juridica',
                             'codigo_categoria_matricula',
                             'categoria_matricula',
                             'ultimo_ano_renovado',
                             'fecha_renovacion',
                             'fecha_matricula',
                             'fecha_cancelacion',
                             'genero',
                             'cantidad_mujeres_empleadas',
                             'cantidad_mujeres_cargos_directivos',
                             'codigo_tamano_empresa',
                             'autorizacion_envio_correo_electronico',
                             'direccion_comercial',
                             'codigo_municipio_comercial', 
                             'municipio_comercial',
                             'cod_ciiu_act_econ_pri',
                             'desc_ciiu_act_econ_pri',
                            ]
                columnas_presentes = [col for col in column_select if col in df.columns]
                df_final = df[columnas_presentes]
                resultados_temporales.append(df_final)

            else:
                print('No se pudo realizar la consulta por NIT.')

        except Exception as e:
            print(f'Error con el NIT {nit_a_consultar}: {e}')
            continue

    resultados_df = pd.concat(resultados_temporales, axis=0, ignore_index=True)
    df_depurado = resultados_df.dropna(how='all').drop_duplicates()
    return df_depurado


st.title("Consulta de NITs desde Excel")

# Cargar archivo Excel
uploaded_file = st.file_uploader("Cargar archivo Excel con Nits a Consultar", type=["xlsx"])
if uploaded_file is not None:
    access_token = obtener_token() 
    df = consultar_nits(uploaded_file,access_token)
    st.write(df)
    
    # Crear un objeto BytesIO para exportar a Excel
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    
    # Reiniciar el puntero a la posición inicial
    output.seek(0)
    # Botón para descargar el archivo procesado como Excel
    st.download_button(
        label="Descargar archivo procesado",
        data=output,
        file_name='archivo_procesado.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )

from streamlit_jupyter import StreamlitPatcher

StreamlitPatcher().jupyter()



# In[ ]:




