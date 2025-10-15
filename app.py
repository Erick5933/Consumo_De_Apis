import streamlit as st
import requests
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Usuarios",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para diseño llamativo
st.markdown("""
<style>
    /* Estilo general */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Tarjetas de métricas */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
    }
    
    /* Título principal */
    .title-container {
        background: linear-gradient(90deg, #667eea, #764ba2);
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-title {
        color: white;
        font-size: 3em;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .subtitle {
        color: #f0f0f0;
        font-size: 1.2em;
        margin-top: 10px;
    }
    
    /* Botones */
    .stButton>button {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 10px 30px;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Tablas */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Variables globales
DB_NAME = 'usuarios_dashboard.db'
API_URL = 'https://jsonplaceholder.typicode.com/users'

# Función para crear la base de datos y obtener datos
@st.cache_data(ttl=3600)
def fetch_and_store_data():
    try:
        # Consumir API
        response = requests.get(API_URL, timeout=20)
        if response.status_code != 200:
            st.error(f'Error al consumir la API ({response.status_code})')
            return None
        
        users = response.json()
        
        # Guardar en SQLite
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        
        cur.execute('DROP TABLE IF EXISTS users;')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            username TEXT,
            email TEXT,
            phone TEXT,
            website TEXT
        )
        ''')
        
        for u in users:
            cur.execute('''
                INSERT OR REPLACE INTO users (id, name, username, email, phone, website)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                u.get('id'), u.get('name'), u.get('username'), 
                u.get('email'), u.get('phone'), u.get('website')
            ))
        
        conn.commit()
        conn.close()
        
        return len(users)
    except Exception as e:
        st.error(f'❌ Error: {str(e)}')
        return None

# Función para leer datos desde SQLite
@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query('SELECT * FROM users', conn)
    conn.close()
    
    # Feature engineering
    df['name_length'] = df['name'].astype(str).apply(len)
    df['email_domain'] = df['email'].astype(str).apply(
        lambda x: x.split('@')[-1].lower() if '@' in str(x) else None
    )
    
    return df

# Función para crear gráfica de histograma
def create_histogram(df):
    fig = px.histogram(
        df, 
        x='name_length', 
        nbins=10, 
        title='📊 Distribución de caracteres en los nombres',
        color_discrete_sequence=['#667eea']
    )
    fig.update_layout(
        xaxis_title='Cantidad de caracteres',
        yaxis_title='Frecuencia',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14),
        title_font_size=20,
        height=400
    )
    return fig

# Función para crear gráfica de barras
def create_bar_chart(df):
    dom_counts = df['email_domain'].value_counts().reset_index()
    dom_counts.columns = ['email_domain', 'count']
    
    fig = px.bar(
        dom_counts, 
        x='count', 
        y='email_domain', 
        orientation='h',
        title='Usuarios por dominio de correo electrónico',
        color='count',
        color_continuous_scale='Viridis'
    )
    fig.update_layout(
        xaxis_title='Cantidad de usuarios',
        yaxis_title='Dominio',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14),
        title_font_size=20,
        height=500,
        showlegend=False
    )
    return fig

# Función para crear gráfica de dona
def create_donut_chart(df):
    dom_counts = df['email_domain'].value_counts().reset_index()
    dom_counts.columns = ['email_domain', 'count']
    
    fig = px.pie(
        dom_counts, 
        names='email_domain', 
        values='count', 
        hole=0.4,
        title='Distribución de dominios de email (Donut)',
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14),
        title_font_size=20,
        height=500
    )
    return fig

# Función para crear tabla interactiva
def create_table(df):
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['<b>ID</b>', '<b>Nombre</b>', '<b>Usuario</b>', 
                    '<b>Email</b>', '<b>Teléfono</b>', '<b>Website</b>'],
            fill_color="#253993",
            align='left',
            font=dict(color='white', size=14)
        ),
        cells=dict(
            values=[df['id'], df['name'], df['username'], 
                    df['email'], df['phone'], df['website']],
            fill_color='lavender',
            align='left',
            font=dict(size=12)
        )
    )])
    fig.update_layout(
        title='📋 Tabla de Usuarios',
        title_font_size=20,
        height=600
    )
    return fig

# Función principal
def main():
    # Título principal con diseño llamativo
    st.markdown("""
    <div class="title-container">
        <h1 class="main-title">👥 Dashboard de Usuarios</h1>
        <p class="subtitle">API → SQLite → Pandas → Plotly</p>
        <p class="subtitle">by Erick Chacon</p>

    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
        st.markdown("### ⚙️ Panel de Control")
        
        if st.button("🔄 Actualizar Datos desde API", use_container_width=True):
            with st.spinner('Cargando datos...'):
                result = fetch_and_store_data()
                if result:
                    st.success(f'✅ {result} usuarios cargados correctamente!')
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Opciones de Visualización")
        show_histogram = st.checkbox("Histograma", value=True)
        show_bar = st.checkbox("Gráfica de Barras", value=True)
        show_donut = st.checkbox("Gráfica de Dona", value=True)
        show_table = st.checkbox("Tabla de Datos", value=True)
        
        st.markdown("---")
        st.markdown("### 📄 Información")
        st.info("**Fuente:** jsonplaceholder.typicode.com")
        st.markdown(f"**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Cargar datos
    try:
        df = load_data()
        
        # Métricas principales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3 style="color: #667eea; margin: 0;">Total Usuarios</h3>
                <h1 style="color: #333; margin: 10px 0;">{}</h1>
            </div>
            """.format(len(df)), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3 style="color: #667eea; margin: 0;">Dominios Únicos</h3>
                <h1 style="color: #333; margin: 10px 0;">{}</h1>
            </div>
            """.format(df['email_domain'].nunique()), unsafe_allow_html=True)
        

        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3 style="color: #667eea; margin: 0;">Nombre Más Largo</h3>
                <h1 style="color: #333; margin: 10px 0;">{}</h1>
            </div>
            """.format(df['name_length'].max()), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Visualizaciones
        if show_histogram:
            st.plotly_chart(create_histogram(df), use_container_width=True)
        
        if show_bar or show_donut:
            col1, col2 = st.columns(2)
            
            with col1:
                if show_bar:
                    st.plotly_chart(create_bar_chart(df), use_container_width=True)
            
            with col2:
                if show_donut:
                    st.plotly_chart(create_donut_chart(df), use_container_width=True)
        
        if show_table:
            st.plotly_chart(create_table(df), use_container_width=True)
        
        # Sección de exportación
        st.markdown("---")
        st.markdown("### Exportar Datos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name='usuarios_data.csv',
                mime='text/csv',
                use_container_width=True
            )
        
        with col2:
            # Guardar gráfica como HTML
            if st.button("Exportar Histograma HTML", use_container_width=True):
                fig = create_histogram(df)
                fig.write_html('hist_name_length.html', include_plotlyjs='cdn')
                st.success("✅ Archivo exportado: hist_name_length.html")
        
        with col3:
            st.markdown("""
            <a href="#" style="text-decoration: none;">
                <button style="width: 100%; padding: 10px; background: linear-gradient(90deg, #667eea, #764ba2); color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
                    📊 Ver Estadísticas
                </button>
            </a>
            """, unsafe_allow_html=True)
        
        # Estadísticas adicionales
        with st.expander("📈 Ver Estadísticas Detalladas"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Estadísticas de Longitud de Nombres")
                st.dataframe(df['name_length'].describe(), use_container_width=True)
            
            with col2:
                st.markdown("#### Top 5 Dominios")
                top_domains = df['email_domain'].value_counts().head(5).reset_index()
                top_domains.columns = ['Dominio', 'Cantidad']
                st.dataframe(top_domains, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"❌ Error al cargar los datos: {str(e)}")
        st.info("💡 Presiona el botón '🔄 Actualizar Datos desde API' en el panel lateral para cargar los datos.")

# Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: white; padding: 20px;">
        <p>Desarrollado con ❤️ usando Streamlit | Datos de JSONPlaceholder</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()