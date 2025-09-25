import streamlit as st
import pandas as pd
import io
import requests
import os

# --- Configuración de la URL de Google Drive (Funcional) ---
# Usando la sintaxis de exportación CSV con tu ID de documento y GID
GOOGLE_SHEETS_URL = 'https://docs.google.com/spreadsheets/d/1ZvUejwjZXwtXhJgdP-hS6u5DH7tXUwbu/export?format=csv&gid=1344588226'

# --- Nombre del Archivo del Logo ---
LOGO_FILE_NAME = 'LOGO SIN FONDO.png' 

# --- Configuración inicial de la página de Streamlit ---
st.set_page_config(layout="wide")

# --- Sección de Cabecera (Logo y Título) ---
# 1. Intentamos mostrar el logo
if os.path.exists(LOGO_FILE_NAME):
    st.image(LOGO_FILE_NAME, width=150) 
else:
    # Este mensaje solo se verá si la imagen no se carga (útil para ti, no para el cliente)
    # st.warning(f"⚠️ Archivo de logo '{LOGO_FILE_NAME}' no encontrado.")
    pass

st.title('📋 Lista de Precios')
st.markdown("---")

# --- Función para Cargar Datos (Caché para eficiencia) ---
@st.cache_data
def load_and_process_prices_data(url):
    try:
        st.info('Cargando y procesando datos de la lista de precios...')
        response = requests.get(url)
        response.raise_for_status() 

        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))

        # Limpiar espacios en los nombres de las columnas
        df.columns = df.columns.str.strip()
        
        # Mapeo de las 8 columnas finales
        column_mapping = {
            'CATEGORIA': 'Categoría',
            'DESCRIPCION': 'Descripción',
            'UNIDAD': 'Unidad',
            'PRECIO DETALLE': 'Precio Detalle',
            'PRECIO POR MAYOR': 'Precio por Mayor',
            'MAYOR DESDE': 'Cant. Mín. Mayor',       
            'PRECIO DISTRIBUIDOR': 'Precio Distribuidor',
            'DISTRIBUIDOR DESDE': 'Cant. Mín. Distribuidor' 
        }
        
        # Eliminar filas sin categoría
        df.dropna(subset=['CATEGORIA'], inplace=True)
        
        # Seleccionar y renombrar las columnas
        existing_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
        
        # Advertencia si faltan columnas esenciales
        if len(existing_cols) < 8:
             # Este mensaje se verá en la app, es para tu información
             # st.warning(f"Advertencia: Solo se encontraron {len(existing_cols)} de las 8 columnas esperadas. Revisa los títulos de tu Excel.")
             pass

        df = df[[k for k in existing_cols.keys()]].rename(columns=existing_cols)
        
        # Convertir columnas numéricas, limpiando $ y comas
        price_and_qty_cols = [col for col in df.columns if 'Precio' in col or 'Cant. Mín.' in col]

        for col in price_and_qty_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        st.success('✅ ¡Datos de precios cargados y procesados con éxito!')
        return df

    except Exception as e:
        st.error(f"❌ Error al procesar o mapear columnas. Revisa tu Excel.")
        # st.error(f"Detalles: {e}") # Descomenta para ver el error completo
        st.stop()

# --- Cargar los datos ---
df_precios = load_and_process_prices_data(GOOGLE_SHEETS_URL)

# --- Componentes Interactivos (Filtros) ---
st.subheader('Filtros de Búsqueda')

# Si el DataFrame está vacío, mostramos una advertencia
if df_precios.empty:
    st.warning("El DataFrame de precios está vacío. Revisa tu Google Sheet.")
    st.stop() 


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
    
    # CAMBIO CLAVE para adaptabilidad: Usar st.table()
    # Muestra la tabla filtrada de forma compacta y adaptable al móvil.
    st.table(df_filtrado_precios) 

st.markdown("---")
st.success("¡Dashboard de Lista de Precios listo!")
