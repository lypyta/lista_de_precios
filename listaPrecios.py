import streamlit as st
import pandas as pd
import io
import requests

# --- Configuración de la URL de Google Drive (¡CORREGIDA con tu ID de documento!) ---
# Usamos la sintaxis de exportación CSV con la ID de documento 1ZvUejwjZXwtXhJgdP-hS6u5DH7tXUwbu y GID 1344588226
GOOGLE_SHEETS_URL = 'https://docs.google.com/spreadsheets/d/1ZvUejwjZXwtXhJgdP-hS6u5DH7tXUwbu/export?format=csv&gid=1344588226'

# --- Configuración inicial de la página de Streamlit ---
st.set_page_config(layout="wide")
st.title('📋 Lista de Precios')
st.markdown("---")

# --- Función para Cargar Datos (Caché para eficiencia) ---
@st.cache_data
def load_and_process_prices_data(url):
    try:
        st.info('Cargando y procesando datos de la lista de precios (usando CSV) desde Google Drive...')
        response = requests.get(url)
        response.raise_for_status() 

        # Leer el archivo como CSV (más robusto que XLSX)
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))

        # 1. Limpiar espacios en los nombres de las columnas detectadas por Pandas
        df.columns = df.columns.str.strip()
        
        # 2. Mapeo de columnas basado en los títulos de tu Excel (8 columnas)
        column_mapping = {
            'CATEGORIA': 'Categoría',
            'DESCRIPCION': 'Descripción',
            'UNIDAD': 'Unidad',
            'PRECIO DETALLE': 'Precio Detalle',
            'PRECIO POR: MAYOR': 'Precio por Mayor',
            'DESDE': 'Cant. Mín. Mayor',
            'PRECIO DISTRIBUIDOR': 'Precio Distribuidor',
            'DESDE.1': 'Cant. Mín. Distribuidor' 
        }
        
        # 3. Eliminar filas sin categoría
        df.dropna(subset=['CATEGORIA'], inplace=True)
        
        # 4. Seleccionar y renombrar las columnas existentes
        existing_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df[list(existing_cols.keys())].rename(columns=existing_cols)
        
        # 5. Convertir columnas numéricas, limpiando $ y comas
        price_and_qty_cols = ['Precio Detalle', 'Precio por Mayor', 'Cant. Mín. Mayor', 'Precio Distribuidor', 'Cant. Mín. Distribuidor']
        for col in price_and_qty_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        st.success('✅ ¡Datos de precios cargados y procesados con éxito!')
        return df

    except requests.exceptions.RequestException as req_err:
        st.error(f"❌ Error de conexión al cargar el archivo. Verifica la configuración de **Compartir** en Google Sheets y asegúrate de que dice **'Cualquier persona con el enlace'**.")
        st.error(f"Detalles: {req_err}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error inesperado al leer o procesar el archivo. Asegúrate de que el encabezado de tu Excel esté en la primera fila y las columnas sean correctas.")
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
st.success("¡Dashboard de Lista de Precios listo!")
