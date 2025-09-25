import streamlit as st
import pandas as pd
import plotly.express as px
import io
import requests

# --- Configuración de la URL de Google Drive ---
# ASEGÚRATE DE CAMBIAR ESTA URL POR LA DE TU HOJA DE PRECIOS
GOOGLE_SHEETS_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSNRv2kzy2qIDvRbljlj5nHEqbzSYhcZF9oqklzmmt_1-hQfO8Mjf4ZdvmwSdXt9A/pub?output=xlsx'

# --- Configuración inicial de la página de Streamlit ---
st.set_page_config(layout="wide")
st.title('📋 Lista de Precios')
st.markdown("---")

# --- Función para Cargar Datos (Caché para eficiencia) ---
@st.cache_data
def load_and_process_prices_data(url):
    try:
        st.info('Cargando y procesando datos de la lista de precios desde Google Drive...')
        response = requests.get(url)
        response.raise_for_status()

        # Leer el archivo Excel, asumiendo que el encabezado está en la primera fila (header=0)
        df = pd.read_excel(io.BytesIO(response.content), header=0, engine='openpyxl')

        # Opcional: Limpiar espacios en los nombres de las columnas para evitar errores
        df.columns = df.columns.str.strip()

        # Muestra al usuario los nombres de las columnas que el script detectó en su archivo
        st.info(f"Columnas detectadas en tu archivo: {df.columns.tolist()}")

        # Seleccionar y renombrar las columnas clave que vas a mostrar
        column_mapping = {
            'CATEGORIA': 'Categoría',
            'DESCRIPCION': 'Descripción',
            'UNIDAD': 'Unidad',
            'PRECIO POR DETALLE': 'Precio por Detalle',
            'PRECIO POR: MAYOR': 'Precio por Mayor',
            'DESDE?': 'Cantidad Mínima', # Asumiendo que esta es la cantidad para el precio por mayor
            'PRECIO DISTRIBUIDOR': 'Precio Distribuidor',
            # Si hay otra columna "DESDE?", asegúrate de que el nombre sea único en el mapeo
            'DESDE?.1': 'Cantidad Mínima Distribuidor' # Por si hay otra columna igual
        }
        
        # Eliminar las filas que no tienen una CATEGORIA, ya que no son productos válidos
        df.dropna(subset=['CATEGORIA'], inplace=True)
        
        # Asegurarse de que las columnas mapeadas existan en el DataFrame antes de seleccionarlas
        existing_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df[list(existing_cols.keys())].rename(columns=existing_cols)

        # Convertir las columnas de precios y cantidades a numérico, eliminando símbolos y comas
        price_and_qty_cols = ['Precio por Detalle', 'Precio por Mayor', 'Cantidad Mínima', 'Precio Distribuidor', 'Cantidad Mínima Distribuidor']
        for col in price_and_qty_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('$', '').str.replace(',', '').str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        st.success('✅ ¡Datos de precios cargados y procesados con éxito!')
        return df

    except requests.exceptions.RequestException as req_err:
        st.error(f"❌ Error de conexión al cargar el archivo. Verifica el enlace y permisos de Drive.")
        st.error(f"Detalles: {req_err}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error inesperado al leer o procesar el archivo. Asegúrate que sea un Excel válido y la estructura de columnas sea la esperada.")
        st.error(f"Detalles: {e}")
        st.stop()

# --- Cargar los datos ---
df_precios = load_and_process_prices_data(GOOGLE_SHEETS_URL)

# --- Componentes Interactivos (Filtros) ---
st.subheader('Filtros de Búsqueda')

# Crea un selectbox para filtrar por categoría
categorias_disponibles = ['Todas'] + sorted(df_precios['Categoría'].unique().tolist())
categoria_seleccionada = st.selectbox('Filtrar por Categoría', categorias_disponibles)

st.markdown("---")

# --- Filtrar y Mostrar la Lista de Precios ---
if categoria_seleccionada == 'Todas':
    df_filtrado_precios = df_precios.copy()
else:
    df_filtrado_precios = df_precios[df_precios['Categoría'] == categoria_seleccionada].copy()

# Mensaje si no hay datos después de filtrar
if df_filtrado_precios.empty:
    st.warning("No hay productos para la categoría seleccionada.")
else:
    st.subheader(f'Lista de Precios - {categoria_seleccionada}')
    
    # Muestra la tabla filtrada con todas las columnas
    st.dataframe(df_filtrado_precios, use_container_width=True, hide_index=True)

st.markdown("---")
st.success("¡Dashboard de Lista de Precios actualizado!")
