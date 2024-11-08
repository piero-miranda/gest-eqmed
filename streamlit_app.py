import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import threading

# Crear el objeto Lock para manejar concurrencia
lock = threading.Lock()

# Autenticación con Google Sheets usando google-auth
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_file("credentials.json", scopes=scope)
gc = gspread.authorize(credentials)

# Función para reintentar lectura con espera
def retry_read_sheet(retries=3, wait_time=5):
    for attempt in range(retries):
        try:
            spreadsheet = gc.open_by_key("1D3OHaLj2oARW3IJHEN7SV_uZSiZEOmFa8iRAsDGmyWY")
            hoja_usuarios = spreadsheet.worksheet("USUARIOS")
            hoja_accesorios = spreadsheet.worksheet("STOCK")
            hoja_in = spreadsheet.worksheet("IN")
            hoja_out = spreadsheet.worksheet("OUT")
            return hoja_usuarios, hoja_accesorios, hoja_in, hoja_out
        except Exception as e:
            st.warning(f"Error al leer la hoja de cálculo: {e}. Reintentando en {wait_time} segundos...")
            time.sleep(wait_time)
    st.error("No se pudo leer la hoja de cálculo después de varios intentos.")
    return None, None, None, None

# Cargar datos con caché
@st.cache_data(ttl=60)
def cargar_datos():
    hoja_usuarios, hoja_accesorios, hoja_in, hoja_out = retry_read_sheet()
    if hoja_usuarios and hoja_accesorios:
        usuarios_data = hoja_usuarios.get_all_records()
        accesorios_data = hoja_accesorios.get_all_records()
        usuarios_df = pd.DataFrame(usuarios_data)
        accesorios_df = pd.DataFrame(accesorios_data)
        return usuarios_df, accesorios_df, hoja_in, hoja_out
    else:
        st.error("No se pudieron cargar los datos.")
        return None, None, None, None

# Cargar datos
usuarios_df, df, hoja_in, hoja_out = cargar_datos()
if usuarios_df is None or df is None:
    st.stop()

# Inicializar el estado de la sesión
if "usuario" not in st.session_state:
    st.session_state["usuario"] = None

# Función de autenticación
def autenticar(usuario, contraseña):
    user = usuarios_df[(usuarios_df["Usuario"] == usuario) & (usuarios_df["Contraseña"] == contraseña)]
    if not user.empty:
        return user.iloc[0]["Nombre"]
    return None

# Pantalla de inicio de sesión
def login_page():
    st.title("🔐 Inicio de Sesión")
    usuario = st.text_input("Usuario", placeholder="Ingresa tu usuario")
    contraseña = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")

    if st.button("Iniciar sesión"):
        nombre_responsable = autenticar(usuario, contraseña)
        if nombre_responsable:
            st.session_state["usuario"] = nombre_responsable
            st.session_state["page"] = "home"
        else:
            st.error("Usuario o contraseña incorrectos.")

# Página principal de navegación
def home_page():
    st.title(f"👋 Hola, {st.session_state['usuario']}")
    st.write("Selecciona una opción en la barra lateral para comenzar.")

# Página de registro de ingresos y salidas
def registro_ingresos_salidas():
    st.title("📦 Registro de Ingresos y Salidas de Accesorios")
    codigo = st.selectbox("Código del accesorio", df["CÓDIGO"].unique())

    if codigo:
        accesorio = df[df["CÓDIGO"] == codigo].iloc[0]
        st.markdown(f"**Nombre:** {accesorio['NOMBRE']}")
        st.markdown(f"**Marca:** {accesorio['MARCA']}")
        st.markdown(f"**Modelo:** {accesorio['MODELO']}")
        st.markdown(f"**Ubicación:** {accesorio['UBICACIÓN']}")
        st.markdown(f"**Stock Disponible:** {accesorio['STOCK']}")

    tipo = st.selectbox("Tipo de transacción", ["Ingreso", "Salida"])
    cantidad = st.number_input("Cantidad", min_value=1)
    area_destino = st.text_input("Área de destino")
    fecha = st.date_input("Fecha de ingreso/salida", datetime.now())
    observaciones = st.text_area("Observaciones")

    if st.button("Registrar"):
        nombre_responsable = st.session_state["usuario"]
        nueva_fila = [
            codigo, accesorio['NOMBRE'], accesorio['MARCA'], accesorio['MODELO'],
            area_destino, fecha.strftime("%d/%m/%Y"), cantidad, observaciones, nombre_responsable
        ]
        with lock:
            try:
                if tipo == "Ingreso":
                    hoja_in.append_row(nueva_fila)
                    nuevo_stock = int(accesorio['STOCK']) + cantidad
                    hoja_accesorios.update_cell(df[df["CÓDIGO"] == codigo].index[0] + 2, 9, nuevo_stock)
                    st.success("Registro de ingreso agregado exitosamente.")
                elif tipo == "Salida":
                    hoja_out.append_row(nueva_fila)
                    nuevo_stock = int(accesorio['STOCK']) - cantidad
                    hoja_accesorios.update_cell(df[df["CÓDIGO"] == codigo].index[0] + 2, 9, nuevo_stock)
                    st.success("Registro de salida agregado exitosamente.")
            except Exception as e:
                st.error(f"Error al actualizar los datos: {e}")

# Página de mantenimiento correctivo
def mantenimiento_correctivo():
    st.title("🔧 Registro de Mantenimiento Correctivo")
    st.markdown("Funcionalidad en construcción. Próximamente podrás registrar mantenimientos correctivos realizados.")

# Página de mantenimiento preventivo
def mantenimiento_preventivo():
    st.title("🛠️ Registro de Mantenimiento Preventivo")
    st.markdown("Funcionalidad en construcción. Próximamente podrás registrar mantenimientos preventivos realizados.")

# Página para solicitar compra de accesorio
def solicitar_compra():
    st.title("🛒 Solicitar Compra de Accesorio")
    st.markdown("Funcionalidad en construcción. Próximamente podrás solicitar la compra de accesorios.")

# Navegación usando Sidebar
if "page" not in st.session_state:
    st.session_state["page"] = "login"

if st.session_state["page"] == "login":
    login_page()
else:
    st.sidebar.title("Navegación")
    st.sidebar.write(f"👤 Usuario: {st.session_state['usuario']}")
    st.sidebar.button("Página Principal", on_click=lambda: st.session_state.update({"page": "home"}))
    st.sidebar.button("Registrar Ingresos/Salidas", on_click=lambda: st.session_state.update({"page": "registro_ingresos_salidas"}))
    st.sidebar.button("Registrar Mantenimiento Correctivo", on_click=lambda: st.session_state.update({"page": "mantenimiento_correctivo"}))
    st.sidebar.button("Registrar Mantenimiento Preventivo", on_click=lambda: st.session_state.update({"page": "mantenimiento_preventivo"}))
    st.sidebar.button("Solicitar Compra de Accesorio", on_click=lambda: st.session_state.update({"page": "solicitar_compra"}))
    st.sidebar.button("Cerrar sesión", on_click=lambda: st.session_state.update({"page": "login"}))

    if st.session_state["page"] == "home":
        home_page()
    elif st.session_state["page"] == "registro_ingresos_salidas":
        registro_ingresos_salidas()
    elif st.session_state["page"] == "mantenimiento_correctivo":
        mantenimiento_correctivo()
    elif st.session_state["page"] == "mantenimiento_preventivo":
        mantenimiento_preventivo()
    elif st.session_state["page"] == "solicitar_compra":
        solicitar_compra()
