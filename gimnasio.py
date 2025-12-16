import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import io # Necesario para manejar la carga de archivos

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('gimnasio.db')
    c = conn.cursor()
    # Tabla de Alumnos
    c.execute('''CREATE TABLE IF NOT EXISTS alumnos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nombre TEXT, 
                  edad INTEGER, 
                  peso REAL, 
                  objetivo TEXT, 
                  fecha_ingreso TEXT)''')
    # Tabla de Planes
    c.execute('''CREATE TABLE IF NOT EXISTS planes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  alumno_id INTEGER, 
                  ejercicio TEXT, 
                  series INTEGER, 
                  repeticiones TEXT, 
                  dia TEXT,
                  FOREIGN KEY(alumno_id) REFERENCES alumnos(id))''')
    conn.commit()
    conn.close()

def run_query(query, params=(), fetch=False):
    conn = sqlite3.connect('gimnasio.db')
    c = conn.cursor()
    c.execute(query, params)
    if fetch:
        data = c.fetchall()
        conn.close()
        return data
    conn.commit()
    conn.close()

# --- INICIALIZAR APP ---
st.set_page_config(page_title="Gestión Gym", page_icon="💪")
init_db()

# --- BARRA LATERAL (MENÚ) ---
menu = st.sidebar.selectbox("Menú Principal", ["Registrar Alumno", "Ver Alumnos", "Crear Plan", "Ver Plan de Alumno", "Importar desde CSV"])

# --- SECCIÓN 1: REGISTRAR ALUMNO (Sin cambios) ---
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
            run_query("INSERT INTO alumnos (nombre, edad, peso, objetivo, fecha_ingreso) VALUES (?, ?, ?, ?, ?)", 
                      (nombre, edad, peso, objetivo, date.today()))
            st.success(f"Alumno {nombre} registrado con éxito.")
        else:
            st.error("Por favor ingresa un nombre.")

# --- SECCIÓN 2: VER ALUMNOS (Sin cambios) ---
elif menu == "Ver Alumnos":
    st.header("👥 Base de Datos de Alumnos")
    data = run_query("SELECT * FROM alumnos", fetch=True)
    if data:
        df = pd.DataFrame(data, columns=['ID', 'Nombre', 'Edad', 'Peso', 'Objetivo', 'Ingreso'])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aún no hay alumnos registrados.")

# --- SECCIÓN 3: CREAR PLAN (Sin cambios) ---
elif menu == "Crear Plan":
    st.header("🏋️‍♂️ Crear Rutina")
    
    # Obtener lista de alumnos para el dropdown
    alumnos = run_query("SELECT id, nombre FROM alumnos", fetch=True)
    
    if alumnos:
        opciones_alumnos = {nombre: id_al for id_al, nombre in alumnos}
        seleccion = st.selectbox("Seleccionar Alumno", list(opciones_alumnos.keys()))
        alumno_id = opciones_alumnos[seleccion]

        st.subheader(f"Agregar ejercicio para {seleccion}")
        
        c1, c2, c3, c4 = st.columns(4)
        dia = c1.selectbox("Día", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
        ejercicio = c2.text_input("Ejercicio (ej. Press Banca)")
        series = c3.number_input("Series", min_value=1, value=3)
        reps = c4.text_input("Repeticiones (ej. 10-12)")

        if st.button("Agregar al Plan"):
            if ejercicio:
                run_query("INSERT INTO planes (alumno_id, ejercicio, series, repeticiones, dia) VALUES (?, ?, ?, ?, ?)",
                          (alumno_id, ejercicio, series, reps, dia))
                st.success("Ejercicio agregado.")
            else:
                st.warning("Escribe el nombre del ejercicio.")
    else:
        st.warning("Primero debes registrar alumnos.")

# --- SECCIÓN 4: VER PLAN (Sin cambios) ---
elif menu == "Ver Plan de Alumno":
    st.header("📅 Seguimiento de Rutinas")
    alumnos = run_query("SELECT id, nombre FROM alumnos", fetch=True)
    
    if alumnos:
        opciones_alumnos = {nombre: id_al for id_al, nombre in alumnos}
        seleccion = st.selectbox("Ver rutina de:", list(opciones_alumnos.keys()))
        alumno_id = opciones_alumnos[seleccion]
        
        # Obtener plan del alumno
        plan_data = run_query("SELECT dia, ejercicio, series, repeticiones FROM planes WHERE alumno_id = ? ORDER BY dia", (alumno_id,), fetch=True)
        
        if plan_data:
            df_plan = pd.DataFrame(plan_data, columns=['Día', 'Ejercicio', 'Series', 'Repeticiones'])
            st.table(df_plan)
        else:
            st.info(f"{seleccion} no tiene ejercicios asignados todavía.")
    else:
        st.warning("No hay alumnos en la base de datos.")

# --- SECCIÓN 5: IMPORTAR CSV (NUEVA FUNCIONALIDAD) ---
elif menu == "Importar desde CSV":
    st.header("📥 Importación Masiva (CSV)")

    # --- Importar Alumnos ---
    st.subheader("1. Importar Base de Alumnos")
    uploaded_alumnos = st.file_uploader("Sube el archivo CSV de alumnos (nombre,edad,peso,objetivo,fecha_ingreso)", type="csv", key="alumnos")
    
    if uploaded_alumnos is not None:
        try:
            df_alumnos = pd.read_csv(uploaded_alumnos)
            expected_cols = ['nombre', 'edad', 'peso', 'objetivo', 'fecha_ingreso']
            
            if not all(col in df_alumnos.columns for col in expected_cols):
                st.error(f"Error: El CSV de alumnos debe contener las columnas: {', '.join(expected_cols)}")
            else:
                count = 0
                for index, row in df_alumnos.iterrows():
                    # Intenta insertar cada fila
                    run_query("INSERT INTO alumnos (nombre, edad, peso, objetivo, fecha_ingreso) VALUES (?, ?, ?, ?, ?)", 
                              (row['nombre'], row['edad'], row['peso'], row['objetivo'], row['fecha_ingreso']))
                    count += 1
                st.success(f"✅ {count} alumnos importados con éxito.")
                st.dataframe(df_alumnos.head(5)) # Mostrar las primeras 5 filas para verificación
                st.info("Revisa la sección 'Ver Alumnos' para ver la base de datos completa.")

        except Exception as e:
            st.error(f"Ocurrió un error al procesar el CSV de alumnos: {e}")


    # --- Importar Planes ---
    st.subheader("2. Importar Planes de Entrenamiento")
    uploaded_planes = st.file_uploader("Sube el archivo CSV de planes (alumno_id,ejercicio,series,repeticiones,dia)", type="csv", key="planes")

    if uploaded_planes is not None:
        st.warning("Asegúrate de que los 'alumno_id' en este CSV ya existan en la base de datos de Alumnos.")
        try:
            df_planes = pd.read_csv(uploaded_planes)
            expected_cols_plan = ['alumno_id', 'ejercicio', 'series', 'repeticiones', 'dia']
            
            if not all(col in df_planes.columns for col in expected_cols_plan):
                st.error(f"Error: El CSV de planes debe contener las columnas: {', '.join(expected_cols_plan)}")
            else:
                count = 0
                for index, row in df_planes.iterrows():
                    # Intenta insertar cada fila
                    run_query("INSERT INTO planes (alumno_id, ejercicio, series, repeticiones, dia) VALUES (?, ?, ?, ?, ?)",
                              (row['alumno_id'], row['ejercicio'], row['series'], row['repeticiones'], row['dia']))
                    count += 1
                st.success(f"✅ {count} planes importados con éxito.")
                st.dataframe(df_planes.head(5)) # Mostrar las primeras 5 filas para verificación
                st.info("Revisa la sección 'Ver Plan de Alumno' para verificar la importación.")

        except Exception as e:
            st.error(f"Ocurrió un error al procesar el CSV de planes: {e}")