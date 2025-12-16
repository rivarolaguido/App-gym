import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

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
menu = st.sidebar.selectbox("Menú Principal", ["Registrar Alumno", "Ver Alumnos", "Crear Plan", "Ver Plan de Alumno"])

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
            run_query("INSERT INTO alumnos (nombre, edad, peso, objetivo, fecha_ingreso) VALUES (?, ?, ?, ?, ?)", 
                      (nombre, edad, peso, objetivo, date.today()))
            st.success(f"Alumno {nombre} registrado con éxito.")
        else:
            st.error("Por favor ingresa un nombre.")

# --- SECCIÓN 2: VER ALUMNOS ---
elif menu == "Ver Alumnos":
    st.header("👥 Base de Datos de Alumnos")
    data = run_query("SELECT * FROM alumnos", fetch=True)
    if data:
        df = pd.DataFrame(data, columns=['ID', 'Nombre', 'Edad', 'Peso', 'Objetivo', 'Ingreso'])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aún no hay alumnos registrados.")

# --- SECCIÓN 3: CREAR PLAN ---
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

# --- SECCIÓN 4: VER PLAN ---
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