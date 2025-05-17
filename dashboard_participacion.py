import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")

# === Título y carga de archivo ===
st.title("🧭 Panel de Coordinación de Personas")
st.markdown("Subí el archivo CSV con los formularios de inscripción para comenzar a analizar.")

uploaded_file = st.file_uploader("Subí el archivo CSV", type=["csv"])

# === Estructura por pestañas ===
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # === Normalizar columnas y datos ===
    df.columns = df.columns.str.strip().str.lower()
    df['departamento'] = df['departamento'].str.title().str.strip()
    df['ciudad'] = df['ciudad'].str.title().str.strip()

    # === Inicializar asignaciones si no existen ===
    if 'asignaciones' not in st.session_state:
        st.session_state['asignaciones'] = {}

    # === Crear pestañas ===
    tab1, tab2 = st.tabs(["🔍 Clasificación inicial", "📦 Asignación a sectores"])

    # === TAB 1: Filtrado y asignación ===
    with tab1:
        st.sidebar.title("Filtros")

        departamentos = st.sidebar.multiselect(
            "Seleccionar departamento(s):",
            options=sorted(df['departamento'].unique()),
            default=sorted(df['departamento'].unique())
        )

        interes = st.sidebar.multiselect(
            "Interés en participar como:",
            options=sorted(df['interes_sumarse_como'].dropna().unique()),
            default=sorted(df['interes_sumarse_como'].dropna().unique())
        )

        # Aplicar filtros
        filtered_df = df[
            (df['departamento'].isin(departamentos)) &
            (df['interes_sumarse_como'].isin(interes))
        ]

        st.subheader("Cantidad de personas por departamento")
        departamento_counts = filtered_df['departamento'].value_counts().reset_index()
        departamento_counts.columns = ['Departamento', 'Cantidad']
        fig = px.bar(departamento_counts, x='Departamento', y='Cantidad', color='Departamento', text='Cantidad')
        st.plotly_chart(fig)

        st.subheader("Detalle de personas filtradas")
        st.dataframe(filtered_df[['nombre_completo', 'departamento', 'ciudad', 'interes_sumarse_como',
                                  'área_colaboración', 'disponibilidad_horaria', 'modalidad_participación',
                                  'comentarios']])

        # Exportar CSV
        st.download_button(
            label="📥 Descargar resultados filtrados como CSV",
            data=filtered_df.to_csv(index=False).encode('utf-8'),
            file_name='personas_filtradas.csv',
            mime='text/csv'
        )

        st.markdown("---")
        st.subheader("✏️ Asignar personas a sectores")

        # Selección de personas
        selected_names = st.multiselect(
            "Seleccionar personas para asignar:",
            options=filtered_df['nombre_completo'].tolist()
        )

        sector = st.selectbox("Asignar al sector:", options=["A", "B", "C", "D", "E"])

        if st.button("Asignar personas seleccionadas"):
            for name in selected_names:
                st.session_state['asignaciones'][name] = sector
            st.success(f"{len(selected_names)} persona(s) asignadas al sector {sector}")

    # === TAB 2: Visualizar sectores ===
    with tab2:
        st.subheader("Personas asignadas por sector")

        asignaciones = st.session_state.get('asignaciones', {})
        asignaciones_df = pd.DataFrame([
            {'nombre_completo': nombre, 'sector': sector}
            for nombre, sector in asignaciones.items()
        ])

        if asignaciones_df.empty:
            st.info("Todavía no se han asignado personas a sectores.")
        else:
            for sector in sorted(asignaciones_df['sector'].unique()):
                st.markdown(f"### Sector {sector}")
                sector_df = asignaciones_df[asignaciones_df['sector'] == sector]
                st.table(sector_df[['nombre_completo']])

    # === Footer ===
    st.markdown("---")
    st.markdown("Desarrollado por **Pablo Andrés Silva Catepón** - Coordinación de la plataforma")

else:
    st.warning("Por favor, subí un archivo CSV para continuar.")
