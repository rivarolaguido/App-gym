import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import io 

# --- Mapeo Día de la Semana (Número a Nombre y viceversa) ---
# 1 = Lunes, 7 = Domingo
DIA_MAP = {
    1: "Lunes",
    2: "Martes",
    3: "Miércoles",
    4: "Jueves",
    5: "Viernes",
    6: "Sábado",
    7: "Domingo"
}
# Diccionario invertido para el selectbox
INVERSE_DIA_MAP = {v: k for k, v in DIA_MAP.items()}


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
    # NOTA: El campo 'dia' guarda números enteros (1-7)
    c.execute('''CREATE TABLE IF NOT EXISTS planes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  alumno_id INTEGER, 
                  ejercicio TEXT, 
                  series INTEGER, 
                  repeticiones TEXT, 
                  dia INTEGER,
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

# --- INICIALIZAR APP Y ESTADO DE SESIÓN ---
st.set_page_config(page_title="Gestión Gym", page_icon="💪")
init_db()

# Inicializar el estado de la sesión para la navegación y la selección del alumno
if 'menu' not in st.session_state:
    st.session_state['menu'] = "Registrar Alumno"
if 'selected_alumno_id' not in st.session_state:
    st.session_state['selected_alumno_id'] = None

# --- BARRA LATERAL (MENÚ) ---
menu_options = ["Registrar Alumno", "Ver Alumnos", "Crear Plan", "Ver Plan de Alumno", "Importar desde CSV"]

# El menú se enlaza al estado de la sesión para permitir la navegación programática
try:
    current_index = menu_options.index(st.session_state['menu'])
except ValueError:
    current_index = 0 # Valor por defecto si el estado es inválido

st.session_state['menu'] = st.sidebar.selectbox(
    "Menú Principal", 
    menu_options,
    index=current_index # Establece el índice actual basado en el estado
)
menu = st.session_state['menu']

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

# --- SECCIÓN 2: VER ALUMNOS (Lista Interactiva) ---
elif menu == "Ver Alumnos":
    st.header("👥 Base de Datos de Alumnos")
    data = run_query("SELECT * FROM alumnos", fetch=True)
    
    if data:
        df = pd.DataFrame(data, columns=['ID', 'Nombre', 'Edad', 'Peso', 'Objetivo', 'Ingreso'])
        
        st.subheader("Listado de Alumnos")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("Ver Plan de Entrenamiento")
        
        # Crea botones interactivos para cada alumno
        for index, row in df.iterrows():
            col1, col2 = st.columns([1, 4])
            
            # Función callback para cambiar el menú y el ID seleccionado
            def set_student_and_navigate(alumno_id):
                st.session_state['selected_alumno_id'] = alumno_id
                st.session_state['menu'] = "Ver Plan de Alumno"
            
            # Botón para la navegación directa
            if col1.button("Ver Plan", key=f"btn_plan_{row['ID']}", 
                           on_click=set_student_and_navigate, args=(row['ID'],)):
                pass # La función on_click ya maneja la lógica

            col2.write(f"**ID {row['ID']}**: {row['Nombre']} (Objetivo: {row['Objetivo']})")
            st.markdown("---") 
            
    else:
        st.info("Aún no hay alumnos registrados.")

# --- SECCIÓN 3: CREAR PLAN (Días con número) ---
elif menu == "Crear Plan":
    st.header("🏋️‍♂️ Crear Rutina")
    
    alumnos = run_query("SELECT id, nombre FROM alumnos", fetch=True)
    
    if alumnos:
        opciones_alumnos = {nombre: id_al for id_al, nombre in alumnos}
        seleccion = st.selectbox("Seleccionar Alumno", list(opciones_alumnos.keys()))
        alumno_id = opciones_alumnos[seleccion]

        st.subheader(f"Agregar ejercicio para {seleccion}")
        
        c1, c2, c3, c4 = st.columns(4)
        
        # Muestra el nombre del día, pero guarda el número
        dia_nombre = c1.selectbox("Día", list(INVERSE_DIA_MAP.keys()))
        dia_numero = INVERSE_DIA_MAP[dia_nombre] # Convertir el nombre a número (1-7)
        
        ejercicio = c2.text_input("Ejercicio (ej. Press Banca)")
        series = c3.number_input("Series", min_value=1, value=3)
        reps = c4.text_input("Repeticiones (ej. 10-12)")

        if st.button("Agregar al Plan"):
            if ejercicio:
                # El valor de 'dia' es un número entero (1-7)
                run_query("INSERT INTO planes (alumno_id, ejercicio, series, repeticiones, dia) VALUES (?, ?, ?, ?, ?)",
                          (alumno_id, ejercicio, series, reps, dia_numero))
                st.success("Ejercicio agregado.")
            else:
                st.warning("Escribe el nombre del ejercicio.")
    else:
        st.warning("Primero debes registrar alumnos.")

# --- SECCIÓN 4: VER PLAN (Día excluido de la visualización) ---
elif menu == "Ver Plan de Alumno":
    st.header("📅 Seguimiento de Rutinas")
    alumnos = run_query("SELECT id, nombre FROM alumnos", fetch=True)
    
    if alumnos:
        # Crea el mapeo de Nombre: ID
        nombre_a_id = {nombre: id_al for id_al, nombre in alumnos}
        
        # Crea el mapeo de ID: Nombre
        id_a_nombre = {id_al: nombre for id_al, nombre in alumnos}
        
        # Determina la selección inicial del selectbox (usa el ID del estado de sesión si existe)
        initial_nombre = ""
        initial_index = 0
        if st.session_state['selected_alumno_id'] in id_a_nombre:
            initial_nombre = id_a_nombre[st.session_state['selected_alumno_id']]
            initial_index = list(nombre_a_id.keys()).index(initial_nombre)
        elif alumnos:
            initial_nombre = alumnos[0][1]
            initial_index = 0

        # Selectbox
        seleccion = st.selectbox("Ver rutina de:", list(nombre_a_id.keys()), index=initial_index)
        alumno_id = nombre_a_id[seleccion]
        
        # Al seleccionar, actualiza el estado de sesión para mantener la consistencia
        st.session_state['selected_alumno_id'] = alumno_id
        
        # Consulta SQL: Se sigue consultando el 'dia' para poder ordenar
        plan_data = run_query("SELECT dia, ejercicio, series, repeticiones FROM planes WHERE alumno_id = ? ORDER BY dia ASC", (alumno_id,), fetch=True)
        
        if plan_data:
            df_plan = pd.DataFrame(plan_data, columns=['Día (Nro)', 'Ejercicio', 'Series', 'Repeticiones'])
            
            # **CAMBIO AQUÍ:** No mapeamos ni mostramos la columna 'Día'
            
            # Seleccionar solo las columnas de Ejercicio, Series y Repeticiones
            df_plan = df_plan[['Ejercicio', 'Series', 'Repeticiones']]
            
            st.table(df_plan)
            st.caption("Nota: Los ejercicios están ordenados por día de la semana (Lunes a Domingo), aunque la columna del día no se muestre.")
        else:
            st.info(f"{seleccion} no tiene ejercicios asignados todavía.")
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
            df_alumnos = pd.read_csv(uploaded_alumnos)
            expected_cols = ['nombre', 'edad', 'peso', 'objetivo', 'fecha_ingreso']
            
            if not all(col in df_alumnos.columns for col in expected_cols):
                st.error(f"Error: El CSV de alumnos debe contener las columnas: {', '.join(expected_cols)}")
            else:
                count = 0
                for index, row in df_alumnos.iterrows():
                    run_query("INSERT INTO alumnos (nombre, edad, peso, objetivo, fecha_ingreso) VALUES (?, ?, ?, ?, ?)", 
                              (row['nombre'], row['edad'], row['peso'], row['objetivo'], row['fecha_ingreso']))
                    count += 1
                st.success(f"✅ {count} alumnos importados con éxito.")
                st.dataframe(df_alumnos.head(5))

        except Exception as e:
            st.error(f"Ocurrió un error al procesar el CSV de alumnos: {e}")


    # --- Importar Planes ---
    st.subheader("2. Importar Planes de Entrenamiento")
    st.info("El campo 'dia' en este CSV debe ser un número entero del 1 al 7 (1=Lunes, 7=Domingo).")
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
                    run_query("INSERT INTO planes (alumno_id, ejercicio, series, repeticiones, dia) VALUES (?, ?, ?, ?, ?)",
                              (row['alumno_id'], row['ejercicio'], row['series'], row['repeticiones'], int(row['dia'])))
                    count += 1
                st.success(f"✅ {count} planes importados con éxito.")
                st.dataframe(df_planes.head(5))

        except Exception as e:
            st.error(f"Ocurrió un error al procesar el CSV de planes: {e}")