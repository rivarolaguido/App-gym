import streamlit as st
import pandas as pd
import gspread
import json
from datetime import date
import time # Usado para la simulación de ID

# --- CONFIGURACIÓN DE LA BASE DE DATOS (GOOGLE SHEETS) ---

# Función para cargar las credenciales de la cuenta de servicio
def get_service_account():
    # En entorno local, usa el archivo JSON descargado.
    # En Streamlit Cloud, usa los secretos (st.secrets).
    if st.secrets:
        return st.secrets["gcp_service_account"]
    else:
        # Reemplaza 'path/a/tu-clave.json' con la ruta real en local si lo ejecutas sin la nube
        # Este es un paso opcional, en la nube es más seguro usar st.secrets
        # Para simplificar, asumimos que se va a desplegar en la nube directamente
        st.error("Error: Las credenciales de Google Sheets no están configuradas.")
        st.stop()


# Función para conectar al Google Sheet
def connect_gsheet():
    # Si ya tenemos la conexión en caché, la usamos
    if 'gc' not in st.session_state:
        try:
            # Autenticación con las credenciales de servicio
            creds = get_service_account()
            gc = gspread.service_account_from_dict(creds)
            st.session_state['gc'] = gc
        except Exception as e:
            st.error(f"Error de conexión a Google Sheets: {e}")
            return None

    gc = st.session_state['gc']
    try:
        # Abre el Spreadsheet por URL o título (usa el título de tu Hoja)
        # REEMPLAZA 'GymTracker DB' con el nombre exacto de tu Hoja de Google
        sh = gc.open_by_title("GymTracker DB")
        return sh
    except Exception as e:
        st.error(f"Error al abrir la hoja de cálculo 'GymTracker DB': {e}")
        st.stop()

# Funciones de Lectura y Escritura
def read_sheet(sheet_name):
    sh = connect_gsheet()
    if sh:
        try:
            ws = sh.worksheet(sheet_name)
            data = ws.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error al leer la hoja '{sheet_name}': {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def append_row(sheet_name, row_data):
    sh = connect_gsheet()
    if sh:
        try:
            ws = sh.worksheet(sheet_name)
            ws.append_row(row_data)
            return True
        except Exception as e:
            st.error(f"Error al escribir en la hoja '{sheet_name}': {e}")
            return False
    return False


# --- INICIALIZAR APP ---
st.set_page_config(page_title="Gestión Gym", page_icon="💪")
# No necesitamos init_db() ya que la base de datos es la Hoja de Google

# --- BARRA LATERAL (MENÚ) ---
menu = st.sidebar.selectbox("Menú Principal", ["Registrar Alumno", "Ver Alumnos", "Crear Plan", "Ver Plan de Alumno", "Importar desde CSV"])


# --- SECCIÓN 1: REGISTRAR ALUMNO ---
if menu == "Registrar Alumno":
    st.header("📝 Nuevo Alumno")
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre Completo")
        edad = st.number_input("Edad", min_value=10, max_value=100)
    with col2:
        peso = st.number_input("Peso (kg)", min_value=30.0)
        objetivo = st.selectbox("Objetivo", ["Hipertrofia", "Pérdida de Peso", "Fuerza", "Resistencia"])
    
    if st.button("Guardar Alumno"):
        if nombre:
            # Leer el dataframe actual para calcular el nuevo ID
            df_alumnos = read_sheet('alumnos')
            # El ID debe ser el máximo ID actual + 1. Si está vacía, ID = 1.
            new_id = df_alumnos['id'].max() + 1 if not df_alumnos.empty else 1
            
            row_data = [new_id, nombre, edad, peso, objetivo, date.today().strftime("%Y-%m-%d")]
            
            if append_row('alumnos', row_data):
                st.success(f"Alumno {nombre} registrado con éxito. ID asignado: {new_id}")
            else:
                st.error("Error al guardar en Google Sheets.")
        else:
            st.error("Por favor ingresa un nombre.")

# --- SECCIÓN 2: VER ALUMNOS ---
elif menu == "Ver Alumnos":
    st.header("👥 Base de Datos de Alumnos")
    # Cargar datos desde Google Sheets
    df = read_sheet('alumnos')
    
    if not df.empty:
        # Reordenar y mostrar el DataFrame
        df.columns = ['ID', 'Nombre', 'Edad', 'Peso', 'Objetivo', 'Ingreso']
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aún no hay alumnos registrados o la conexión falló.")

# --- SECCIÓN 3: CREAR PLAN ---
elif menu == "Crear Plan":
    st.header("🏋️‍♂️ Crear Rutina")
    
    df_alumnos = read_sheet('alumnos')
    
    if not df_alumnos.empty:
        # Crear un diccionario para mapear Nombre a ID
        opciones_alumnos = pd.Series(df_alumnos.nombre.values, index=df_alumnos.id).to_dict()
        
        # Invertir para el selectbox
        nombre_a_id = {v: k for k, v in opciones_alumnos.items()}
        
        seleccion_nombre = st.selectbox("Seleccionar Alumno", list(nombre_a_id.keys()))
        alumno_id = nombre_a_id[seleccion_nombre]

        st.subheader(f"Agregar ejercicio para {seleccion_nombre} (ID: {alumno_id})")
        
        c1, c2, c3, c4 = st.columns(4)
        dia = c1.selectbox("Día", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
        ejercicio = c2.text_input("Ejercicio (ej. Press Banca)")
        series = c3.number_input("Series", min_value=1, value=3)
        reps = c4.text_input("Repeticiones (ej. 10-12)")

        if st.button("Agregar al Plan"):
            if ejercicio:
                df_planes = read_sheet('planes')
                new_id = df_planes['id'].max() + 1 if not df_planes.empty else 1
                
                row_data = [new_id, alumno_id, ejercicio, series, reps, dia]
                
                if append_row('planes', row_data):
                    st.success("Ejercicio agregado al plan.")
                else:
                    st.error("Error al guardar el plan en Google Sheets.")
            else:
                st.warning("Escribe el nombre del ejercicio.")
    else:
        st.warning("Primero debes registrar alumnos.")

# --- SECCIÓN 4: VER PLAN ---
elif menu == "Ver Plan de Alumno":
    st.header("📅 Seguimiento de Rutinas")
    
    df_alumnos = read_sheet('alumnos')
    
    if not df_alumnos.empty:
        nombre_a_id = pd.Series(df_alumnos.id.values, index=df_alumnos.nombre).to_dict()
        seleccion_nombre = st.selectbox("Ver rutina de:", list(nombre_a_id.keys()))
        alumno_id = nombre_a_id[seleccion_nombre]
        
        df_planes = read_sheet('planes')
        
        if not df_planes.empty:
            # Filtrar por el ID del alumno
            df_plan = df_planes[df_planes['alumno_id'] == alumno_id]
            
            if not df_plan.empty:
                df_plan = df_plan[['dia', 'ejercicio', 'series', 'repeticiones']]
                df_plan.columns = ['Día', 'Ejercicio', 'Series', 'Repeticiones']
                st.table(df_plan)
            else:
                st.info(f"{seleccion_nombre} no tiene ejercicios asignados todavía.")
        else:
            st.warning("Aún no hay planes de entrenamiento registrados.")
    else:
        st.warning("No hay alumnos en la base de datos.")

# --- SECCIÓN 5: IMPORTAR CSV ---
elif menu == "Importar desde CSV":
    st.header("📥 Importación Masiva (CSV)")

    # --- Importar Alumnos ---
    st.subheader("1. Importar Base de Alumnos")
    uploaded_alumnos = st.file_uploader("Sube el archivo CSV de alumnos (nombre,edad,peso,objetivo,fecha_ingreso)", type="csv", key="alumnos")
    
    if uploaded_alumnos is not None:
        try:
            df_alumnos_new = pd.read_csv(uploaded_alumnos)
            expected_cols = ['nombre', 'edad', 'peso', 'objetivo', 'fecha_ingreso']
            
            if not all(col in df_alumnos_new.columns for col in expected_cols):
                st.error(f"Error: El CSV de alumnos debe contener las columnas: {', '.join(expected_cols)}")
            else:
                # Cargar el DF existente para generar IDs
                df_alumnos_existente = read_sheet('alumnos')
                next_id = df_alumnos_existente['id'].max() + 1 if not df_alumnos_existente.empty else 1
                
                count = 0
                
                # Obtener la hoja de trabajo una sola vez para eficiencia
                sh = connect_gsheet()
                ws_alumnos = sh.worksheet('alumnos')
                
                rows_to_append = []
                for index, row in df_alumnos_new.iterrows():
                    new_id = next_id + index
                    rows_to_append.append([new_id, row['nombre'], row['edad'], row['peso'], row['objetivo'], row['fecha_ingreso']])
                    count += 1
                
                # Añadir todas las filas de golpe
                ws_alumnos.append_rows(rows_to_append)
                
                st.success(f"✅ {count} alumnos importados con éxito. Los IDs nuevos comienzan en {next_id}.")
                st.dataframe(df_alumnos_new.head(5))

        except Exception as e:
            st.error(f"Ocurrió un error al procesar el CSV de alumnos: {e}")


    # --- Importar Planes ---
    st.subheader("2. Importar Planes de Entrenamiento")
    uploaded_planes = st.file_uploader("Sube el archivo CSV de planes (alumno_id,ejercicio,series,repeticiones,dia)", type="csv", key="planes")

    if uploaded_planes is not None:
        st.warning("Asegúrate de que los 'alumno_id' en este CSV ya existan en la base de datos de Alumnos.")
        try:
            df_planes_new = pd.read_csv(uploaded_planes)
            expected_cols_plan = ['alumno_id', 'ejercicio', 'series', 'repeticiones', 'dia']
            
            if not all(col in df_planes_new.columns for col in expected_cols_plan):
                st.error(f"Error: El CSV de planes debe contener las columnas: {', '.join(expected_cols_plan)}")
            else:
                df_planes_existente = read_sheet('planes')
                next_id = df_planes_existente['id'].max() + 1 if not df_planes_existente.empty else 1

                sh = connect_gsheet()
                ws_planes = sh.worksheet('planes')
                
                count = 0
                rows_to_append = []
                for index, row in df_planes_new.iterrows():
                    new_id = next_id + index
                    rows_to_append.append([new_id, row['alumno_id'], row['ejercicio'], row['series'], row['repeticiones'], row['dia']])
                    count += 1
                
                # Añadir todas las filas de golpe
                ws_planes.append_rows(rows_to_append)
                
                st.success(f"✅ {count} planes importados con éxito. Los IDs nuevos comienzan en {next_id}.")
                st.dataframe(df_planes_new.head(5))

        except Exception as e:
            st.error(f"Ocurrió un error al procesar el CSV de planes: {e}")