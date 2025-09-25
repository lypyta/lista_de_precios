import streamlit as st
import pandas as pd
import io
import requests

# --- Configuración de la URL de Google Drive (Funcional) ---
# Usando la sintaxis de exportación CSV con tu ID de documento y GID
GOOGLE_SHEETS_URL = 'https://docs.google.com/spreadsheets/d/1ZvUejwjZXwtXhJgdP-hS6u5DH7tXUwbu/export?format=csv&gid=1344588226'

# --- Configuración inicial de la página de Streamlit ---
st.set_page_config(layout="wide")
st.title('📋 Lista de Precios')
st.markdown("---")

# --- Función para Cargar Datos (Caché para eficiencia) ---
@st.cache_data
def load_and_process_prices_data(url):
    try:
        st.info('Cargando y procesando datos de la lista de precios...')
        response = requests.get(url)
        response.raise_for_status() 

        # Leer el archivo como CSV (más robusto)
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))

        # 1. Limpiar espacios en los nombres de las columnas detectadas por Pandas
        df.columns = df.columns.str.strip()
        
        # DEBUG: Mostrar las columnas detectadas para que puedas verificar
        st.write("Columnas detectadas por Pandas (revisa que coincidan con tu Excel):", df.columns.tolist())
        
        # 2. Mapeo de columnas basado en los 8 nombres que confirmaste (usando nombres limpios para el mapeo)
        #    Si tu Excel tiene nombres con espacios o caracteres especiales, Pandas los simplifica en el CSV.
        column_mapping = {
            'CATEGORIA': 'Categoría',
            'DESCRIPCION': 'Descripción',
            'UNIDAD': 'Unidad',
            'PRECIO DETALLE': 'Precio Detalle',
            'PRECIO POR MAYOR': 'Precio por Mayor',
            'MAYOR DESDE': 'Cant. Mín. Mayor',       # Asumiendo que esta es la columna 'DESDE' del precio por mayor
            'PRECIO DISTRIBUIDOR': 'Precio Distribuidor',
            'DISTRIBUIDOR DESDE': 'Cant. Mín. Distribuidor' # Asumiendo que esta es la segunda columna 'DESDE'
        }
        
        # Intenta mapear con los nombres exactos que nos diste, además de las posibles variaciones:
        backup_mapping = {
            'PRECIO POR: MAYOR': 'Precio por Mayor', # Nombre de imagen anterior
            'DESDE': 'Cant. Mín. Mayor',             # Nombre de imagen anterior
            'DESDE.1': 'Cant. Mín. Distribuidor'     # Nombre de imagen anterior
        }

        # Combinar los mapeos. Los nombres exactos que diste tienen prioridad
        final_mapping = {**backup_mapping, **column_mapping}
        
        # 3. Eliminar filas sin categoría
        df.dropna(subset=['CATEGORIA'], inplace=True)
        
        # 4. Seleccionar y renombrar las columnas existentes
        existing_cols = {k: v for k, v in final_mapping.items() if k in df.columns}
        df = df[list(existing_cols.keys())].rename(columns=existing_cols)
        
        # 5. Convertir columnas numéricas, limpiando $ y comas
        #    Solo incluimos las columnas cuyo nombre final incluye 'Precio' o 'Cant. Mín.'
        price_and_qty_cols = [col for col in df.columns if 'Precio' in col or 'Cant. Mín.' in col]

        for col in price_and_qty_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        st.success('✅ ¡Datos de precios cargados y procesados con éxito!')
        return df

    except Exception as e:
        st.error(f"❌ Error al procesar o mapear columnas. Detalles: {e}")
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
