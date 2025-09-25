import streamlit as st
import pandas as pd
import io
import requests
import os

# --- Configuración de la URL de Google Drive ---
GOOGLE_SHEETS_URL = 'https://docs.google.com/spreadsheets/d/1ZvUejwjZXwtXhJgdP-hS6u5DH7tXUwbu/export?format=csv&gid=1344588226'

# --- Nombre del Archivo del Logo ---
# ATENCIÓN: Corregí el nombre del logo a minúsculas por seguridad, ya que los sistemas Linux/Git son sensibles a mayúsculas/minúsculas.
LOGO_FILE_NAME = 'logo sin fondo.png' 

# --- Configuración inicial de la página de Streamlit ---
st.set_page_config(layout="wide")

# --- Sección de Cabecera (Logo y Título) ---
if os.path.exists(LOGO_FILE_NAME):
    st.image(LOGO_FILE_NAME, width=150) 
else:
    pass

st.title('📋 Lista de Precios')
st.markdown("---")

# --- Función para Cargar y Procesar Datos (Caché para eficiencia) ---
@st.cache_data
def load_and_process_prices_data(url):
    try:
        with st.spinner('Cargando y procesando datos de la lista de precios...'):
            response = requests.get(url)
            response.raise_for_status() 

            df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))

            df.columns = df.columns.str.strip()
            
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
            
            df.dropna(subset=['CATEGORIA'], inplace=True)
            
            existing_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
            
            df = df[[k for k in existing_cols.keys()]].rename(columns=existing_cols)
            
            price_and_qty_cols = [col for col in df.columns if 'Precio' in col or 'Cant. Mín.' in col]

            for col in price_and_qty_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            return df

    except requests.exceptions.RequestException:
        st.error("❌ Error de conexión. El enlace de la hoja de precios no es accesible.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error al procesar datos. Revisa la estructura de tu Excel.")
        st.stop()

# --- Cargar los datos ---
df_precios = load_and_process_prices_data(GOOGLE_SHEETS_URL)

# --- Componentes Interactivos (Filtros) ---
st.subheader('Filtros de Búsqueda')

if df_precios.empty:
    st.warning("El archivo de precios está vacío o no contiene categorías válidas.")
    st.stop() 

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
    st.warning(f"No hay productos para la categoría '{categoria_seleccionada}'.")
else:
    st.subheader(f'Lista de Precios - {categoria_seleccionada}')
    
    # Usamos st.table() para mejor adaptabilidad móvil
    st.table(df_filtrado_precios) 
    
    # -----------------------------------------------------
    # --- BOTÓN DE DESCARGA A CSV ---
    # Convertir el DataFrame filtrado a CSV para la descarga
    csv_export = df_filtrado_precios.to_csv(index=False).encode('utf-8')
    
    # Crear un nombre de archivo dinámico
    file_name = f"Lista_Precios_{categoria_seleccionada.replace(' ', '_')}.csv"
    
    st.download_button(
        label="⬇️ Descargar como CSV (Para convertir a PDF)",
        data=csv_export,
        file_name=file_name,
        mime='text/csv',
    )
    # -----------------------------------------------------

st.markdown("---")
st.success("¡Lista de Precios lista para compartir!")
