import pandas as pd
import streamlit as st
import plotly.express as px

# === Subida del archivo ===
st.title("Panel de Coordinación de Personas")
st.markdown("Subí el archivo CSV con los formularios de inscripción para comenzar a analizar.")

uploaded_file = st.file_uploader("Subí el archivo CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # === Normalizar nombres de columnas y datos ===
    df.columns = df.columns.str.strip().str.lower()
    df['departamento'] = df['departamento'].str.title().str.strip()
    df['ciudad'] = df['ciudad'].str.title().str.strip()

    # === Sidebar: filtros ===
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

    # === Aplicar filtros ===
    filtered_df = df[(df['departamento'].isin(departamentos)) &
                     (df['interes_sumarse_como'].isin(interes))]

    # === Gráfico: cantidad por departamento ===
    st.subheader("Cantidad de personas por departamento")
    departamento_counts = filtered_df['departamento'].value_counts().reset_index()
    departamento_counts.columns = ['Departamento', 'Cantidad']
    fig = px.bar(departamento_counts, x='Departamento', y='Cantidad', color='Departamento', text='Cantidad')
    st.plotly_chart(fig)

    # === Tabla de resultados ===
    st.subheader("Detalle de personas filtradas")
    st.dataframe(filtered_df[['nombre_completo', 'departamento', 'ciudad', 'interes_sumarse_como',
                             'área_colaboración', 'disponibilidad_horaria', 'modalidad_participación',
                             'comentarios']])

    # === Exportar CSV ===
    st.download_button(
        label="Descargar resultados filtrados como CSV",
        data=filtered_df.to_csv(index=False).encode('utf-8'),
        file_name='personas_filtradas.csv',
        mime='text/csv'
    )

    # === Footer ===
    st.markdown("---")
    st.markdown("Desarrollado por Pablo Andrés Silva Catepón - Coordinación de la plataforma")

else:
    st.warning("Por favor, subí un archivo CSV para continuar.")