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

        # Leer el archivo como CSV
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))

        # 1. Limpiar espacios en los nombres de las columnas detectadas por Pandas
        df.columns = df.columns.str.strip()
        
        # 2. Mapeo de las 8 columnas finales que confirmaste
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
        
        # 3. Eliminar filas sin categoría
        df.dropna(subset=['CATEGORIA'], inplace=True)
        
        # 4. Seleccionar y renombrar las columnas existentes
        #    Usamos una lista estricta para asegurar que solo se muestren las 8 columnas importantes.
        expected_cols_list = list(column_mapping.keys())
        
        # Verificar si faltan columnas cruciales
        missing_cols = [col for col in expected_cols_list if col not in df.columns]
        if missing_cols:
             st.warning(f"Advertencia: Faltan las siguientes columnas en tu archivo: {', '.join(missing_cols)}")
             # Usar solo las columnas que sí se encontraron
             existing_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
        else:
             existing_cols = column_mapping

        df = df[[k for k in existing_cols.keys()]].rename(columns=existing_cols)
        
        # 5. Convertir columnas numéricas, limpiando $ y comas
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
