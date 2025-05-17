!pip install streamlit plotly

!pip install streamlit-aggrid

import pandas as pd
import streamlit as st
import plotly.express as px
import json
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, JsCode

st.set_page_config(layout="wide")
st.title("🧭 Panel de Coordinación de Personas")
st.markdown("Subí el archivo CSV con los formularios de inscripción para comenzar a analizar.")

uploaded_file = st.file_uploader("Subí el archivo CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.lower()
    df['departamento'] = df['departamento'].str.title().str.strip()
    df['ciudad'] = df['ciudad'].str.title().str.strip()

    if 'asignaciones' not in st.session_state:
        st.session_state['asignaciones'] = {}
    if 'ultima_comunicacion' not in st.session_state:
        st.session_state['ultima_comunicacion'] = {}

    sugerencias_sector = {
        'Organización': 'A',
        'Comunicación': 'B',
        'Legal': 'C',
        'Tecnología': 'D',
        'Territorio': 'E',
        'Educación': 'F'
    }

    nombres_sector = {
        'A': '🛠️ Organización',
        'B': '📣 Comunicación',
        'C': '⚖️ Legal',
        'D': '💻 Tecnología',
        'E': '🌍 Territorio',
        'F': '📚 Educación'
    }

    todos_los_sectores = list(nombres_sector.keys())

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Clasificación inicial", 
        "📦 Asignación a sectores",
        "📊 Métricas por sector",
        "🗓️ Comunicación personalizada",
        "📀 Guardar / Cargar progreso"
    ])

    # === TAB 1 ===
    with tab1:
        st.sidebar.title("Filtros")
        departamentos = st.sidebar.multiselect("Seleccionar departamento(s):",
            options=sorted(df['departamento'].unique()),
            default=sorted(df['departamento'].unique()))

        interes = st.sidebar.multiselect("Interés en participar como:",
            options=sorted(df['interes_sumarse_como'].dropna().unique()),
            default=sorted(df['interes_sumarse_como'].dropna().unique()))

        filtered_df = df[(df['departamento'].isin(departamentos)) &
                         (df['interes_sumarse_como'].isin(interes))].copy()

        filtered_df['sector'] = filtered_df.apply(
            lambda row: st.session_state['asignaciones'].get(row['nombre_completo'], 
                     sugerencias_sector.get(row['área_colaboración'], "")), axis=1)

        filtered_df['ultima_comunicacion'] = filtered_df['nombre_completo'].map(
            st.session_state['ultima_comunicacion'])

        filtered_df['sector_descriptivo'] = filtered_df['sector'].map(nombres_sector).fillna("🔘 No asignado")

        columnas_a_mostrar = ['nombre_completo', 'departamento', 'ciudad', 'interes_sumarse_como',
                              'área_colaboración', 'disponibilidad_horaria', 'modalidad_participación',
                              'comentarios', 'sector', 'sector_descriptivo', 'ultima_comunicacion']
        filtered_df = filtered_df[columnas_a_mostrar]

        st.subheader("📝 Editar y asignar sectores (tabla interactiva)")
        gb = GridOptionsBuilder.from_dataframe(filtered_df)
        gb.configure_column("sector", editable=True, cellEditor="agSelectCellEditor", 
                            cellEditorParams={'values': todos_los_sectores})
        gb.configure_column("ultima_comunicacion", editable=True)
        gb.configure_column("sector_descriptivo", editable=False)

        cellstyle_jscode = JsCode("""
        function(params) {
            let colorMap = {
                'A': '#f4cccc', 'B': '#d9ead3', 'C': '#cfe2f3',
                'D': '#fff2cc', 'E': '#ead1dc', 'F': '#d0e0e3'
            };
            if (params.value && colorMap[params.value]) {
                return { 'backgroundColor': colorMap[params.value] };
            }
        }
        """)
        gb.configure_column("sector", cellStyle=cellstyle_jscode)
        grid_options = gb.build()

        grid_response = AgGrid(filtered_df, gridOptions=grid_options,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            fit_columns_on_grid_load=True)

        updated_df = pd.DataFrame(grid_response['data'])
        for _, row in updated_df.iterrows():
            nombre = row['nombre_completo']
            st.session_state['asignaciones'][nombre] = row.get('sector', '')
            st.session_state['ultima_comunicacion'][nombre] = row.get('ultima_comunicacion', '')

        st.download_button("📥 Descargar resultados filtrados como CSV",
            data=filtered_df.to_csv(index=False).encode('utf-8'),
            file_name='personas_filtradas.csv', mime='text/csv')

    # === TAB 2 ===
    with tab2:
        st.subheader("📦 Personas asignadas por sector")
        asignaciones_df = pd.DataFrame([
            {'nombre_completo': n, 'sector': s}
            for n, s in st.session_state['asignaciones'].items()
        ])

        for sector in todos_los_sectores:
            nombre = nombres_sector.get(sector, f"Sector {sector}")
            st.markdown(f"### {nombre}")
            sector_df = asignaciones_df[asignaciones_df['sector'] == sector]
            if sector_df.empty:
                st.info(f"No hay personas asignadas a {nombre}.")
            else:
                st.table(sector_df[['nombre_completo']])

        if not asignaciones_df.empty:
            st.download_button("📥 Descargar asignaciones como CSV",
                data=asignaciones_df.to_csv(index=False).encode('utf-8'),
                file_name='asignaciones_por_sector.csv', mime='text/csv')

    # === TAB 3 ===
    with tab3:
        st.subheader("📊 Métricas generales por sector")

        full_df = df.copy()
        full_df['sector'] = full_df['nombre_completo'].map(st.session_state['asignaciones'])
        full_df['ultima_comunicacion'] = full_df['nombre_completo'].map(st.session_state['ultima_comunicacion'])

        sector_counts = full_df['sector'].value_counts().reindex(todos_los_sectores, fill_value=0).reset_index()
        sector_counts.columns = ['Sector', 'Cantidad']
        fig_sectores = px.bar(sector_counts, x='Sector', y='Cantidad', color='Sector', text='Cantidad')
        st.plotly_chart(fig_sectores)

        area_sector = full_df.groupby(['sector', 'área_colaboración']).size().reset_index(name='Cantidad')
        if not area_sector.empty:
            st.markdown("#### Distribución por área dentro de cada sector")
            fig_area = px.sunburst(area_sector, path=['sector', 'área_colaboración'], values='Cantidad')
            st.plotly_chart(fig_area)

        disponibilidad = full_df.groupby(['sector', 'disponibilidad_horaria']).size().reset_index(name='Cantidad')
        if not disponibilidad.empty:
            st.markdown("#### Disponibilidad horaria por sector")
            fig_disp = px.bar(disponibilidad, x='sector', y='Cantidad', color='disponibilidad_horaria',
                              barmode='stack', text='Cantidad')
            st.plotly_chart(fig_disp)

        st.markdown("### ⚠️ Alertas de comunicación")
        hoy = pd.Timestamp.now().date()
        umbral_dias = 14
        sin_fecha, vencidos = [], []

        for nombre, sector in st.session_state['asignaciones'].items():
            fecha_str = st.session_state['ultima_comunicacion'].get(nombre, '')
            if not fecha_str:
                sin_fecha.append((nombre, sector))
            else:
                try:
                    fecha = pd.to_datetime(fecha_str).date()
                    dias = (hoy - fecha).days
                    if dias > umbral_dias:
                        vencidos.append((nombre, sector, dias))
                except:
                    sin_fecha.append((nombre, sector))

        if sin_fecha:
            st.warning(f"📌 {len(sin_fecha)} persona(s) sin fecha de comunicación registrada:")
            for n, s in sin_fecha:
                st.markdown(f"- {n} (Sector {s})")

        if vencidos:
            st.error(f"⏰ {len(vencidos)} persona(s) con más de {umbral_dias} días sin contacto:")
            for n, s, d in vencidos:
                st.markdown(f"- {n} (Sector {s}) – Último contacto hace {d} días")
        elif not sin_fecha:
            st.success("✅ Todos los registros están actualizados dentro del rango de comunicación.")

        if sin_fecha or vencidos:
            st.markdown("#### 📥 Exportar alertas como CSV")
            data_alertas = []
            for n, s in sin_fecha:
                data_alertas.append({"nombre_completo": n, "sector": s, "tipo_alerta": "Sin fecha", "dias": ""})
            for n, s, d in vencidos:
                data_alertas.append({"nombre_completo": n, "sector": s, "tipo_alerta": f"{d} días sin contacto", "dias": d})
            alertas_df = pd.DataFrame(data_alertas)
            st.download_button("⬇️ Descargar alertas como CSV",
                data=alertas_df.to_csv(index=False).encode("utf-8"),
                file_name="alertas_comunicacion.csv", mime="text/csv")

    # === TAB 4 ===
    with tab4:
        st.subheader("🗓️ Registrar fecha de última comunicación")
        nombres_asignados = sorted(st.session_state['asignaciones'].keys())
        if not nombres_asignados:
            st.info("Todavía no hay personas asignadas.")
        else:
            persona = st.selectbox("Seleccionar persona:", options=nombres_asignados)
            fecha_actual = st.session_state['ultima_comunicacion'].get(persona, '')
            try:
                fecha_obj = pd.to_datetime(fecha_actual).date() if fecha_actual else None
            except:
                fecha_obj = None
            nueva_fecha = st.date_input("Fecha de última comunicación:", value=fecha_obj)
            if st.button("Guardar fecha"):
                st.session_state['ultima_comunicacion'][persona] = str(nueva_fecha)
                st.success(f"Fecha guardada para {persona}: {nueva_fecha}")

    # === TAB 5 ===
    with tab5:
        st.subheader("📀 Guardar o cargar estado del panel")
        if st.button("⬇️ Guardar progreso actual"):
            estado = {
                "asignaciones": st.session_state.get("asignaciones", {}),
                "ultima_comunicacion": st.session_state.get("ultima_comunicacion", {})
            }
            json_data = json.dumps(estado, indent=2)
            st.download_button("📥 Descargar archivo .json", data=json_data,
                file_name="progreso_panel.json", mime="application/json")

        st.markdown("### 📤 Cargar un archivo .json previamente guardado")
        uploaded_json = st.file_uploader("Seleccioná un archivo .json", type=["json"])
        if uploaded_json is not None:
            try:
                contenido = json.load(uploaded_json)
                st.session_state['asignaciones'] = contenido.get("asignaciones", {})
                st.session_state['ultima_comunicacion'] = contenido.get("ultima_comunicacion", {})
                st.success("✅ Progreso restaurado exitosamente.")
            except Exception as e:
                st.error(f"❌ Error al cargar el archivo: {e}")

else:
    st.warning("Por favor, subí un archivo CSV para continuar.")
