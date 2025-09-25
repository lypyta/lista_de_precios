import streamlit as st
import pandas as pd
import io
import requests

# --- Configuración de la URL de Google Drive (¡CORREGIDA!) ---
# Usa el ID de tu archivo y el GID de la hoja específica
GOOGLE_SHEETS_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ7X3A59hRnDO-A67ylZrigrrbAMN2Gd2Zf_3q80DyPKz2bbTJvGe836B-woafWKg/pub?output=xlsx&gid=1344588226'

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

        # 1. Limpiar espacios en los nombres de las columnas detectadas por Pandas
        df.columns = df.columns.str.strip()
        
        # 2. Mapeo de columnas basado en los títulos EXACTOS de tu Excel
        #    Pandas a veces renombra columnas repetidas agregando .1, .2, etc.
        #    Usamos 'Precio por: Mayor' y 'DESDE' como nombres de columna sin caracteres especiales.
        column_mapping = {
            'CATEGORIA': 'Categoría',
            'DESCRIPCION': 'Descripción',
            'UNIDAD': 'Unidad',
            'PRECIO DETALLE': 'Precio Detalle',
            'PRECIO POR: MAYOR': 'Precio por Mayor',
            'DESDE': 'Cantidad Mínima Mayor',
            'PRECIO DISTRIBUIDOR': 'Precio Distribuidor',
            'DESDE.1': 'Cantidad Mínima Distribuidor' # Asumiendo que esta es la segunda columna DESDE
        }
        
        # 3. Eliminar filas sin categoría
        df.dropna(subset=['CATEGORIA'], inplace=True)
        
        # 4. Seleccionar y renombrar las columnas existentes
        existing_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df[list(existing_cols.keys())].rename(columns=existing_cols)
        
        # 5. Convertir columnas numéricas, limpiando $ y comas
        price_and_qty_cols = ['Precio Detalle', 'Precio por Mayor', 'Cantidad Mínima Mayor', 'Precio Distribuidor', 'Cantidad Mínima Distribuidor']
        for col in price_and_qty_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        st.success('✅ ¡Datos de precios cargados y procesados con éxito!')
        return df

    except requests.exceptions.RequestException as req_err:
        st.error(f"❌ Error de conexión al cargar el archivo. Verifica el enlace y permisos de Drive (debe ser 'Cualquiera con el enlace' como lector).")
        st.error(f"Detalles: {req_err}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error inesperado al leer o procesar el archivo. ¿Tu Excel tiene 8 columnas con esos nombres?")
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
