import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# Autenticación con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(credentials)

# Abrir el documento de Google Sheets
spreadsheet = gc.open_by_key("1D3OHaLj2oARW3IJHEN7SV_uZSiZEOmFa8iRAsDGmyWY")
hoja_usuarios = spreadsheet.worksheet("USUARIOS")
hoja_accesorios = spreadsheet.worksheet("STOCK")
hoja_in = spreadsheet.worksheet("IN")
hoja_out = spreadsheet.worksheet("OUT")

# Cargar datos de usuarios y accesorios
usuarios_data = hoja_usuarios.get_all_records()
usuarios_df = pd.DataFrame(usuarios_data)
data = hoja_accesorios.get_all_records()
df = pd.DataFrame(data)

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
    st.title("Inicio de Sesión")
    usuario = st.text_input("Usuario")
    contraseña = st.text_input("Contraseña", type="password")

    if st.button("Iniciar sesión"):
        nombre_responsable = autenticar(usuario, contraseña)
        if nombre_responsable:
            st.session_state["usuario"] = nombre_responsable
            st.sidebar.success(f"Bienvenido, {nombre_responsable}")
            st.sidebar.button("Ir a la página principal", on_click=lambda: st.session_state.update({"page": "main"}))
        else:
            st.error("Usuario o contraseña incorrectos.")

# Página principal
def main_page():
    st.title("Gestión de Inventario de Accesorios Médicos")
    st.write(f"Usuario logueado: {st.session_state['usuario']}")

    # Selección del código del accesorio
    codigo = st.selectbox("Código del accesorio", df["CÓDIGO"].unique())

    if codigo:
        accesorio = df[df["CÓDIGO"] == codigo].iloc[0]
        st.write(f"**Nombre:** {accesorio['NOMBRE']}")
        st.write(f"**Marca:** {accesorio['MARCA']}")
        st.write(f"**Modelo:** {accesorio['MODELO']}")
        st.write(f"**Ubicación:** {accesorio['UBICACIÓN']}")
        st.write(f"**Stock Disponible:** {accesorio['STOCK']}")

    # Campos adicionales
    tipo = st.selectbox("Tipo de transacción", ["Ingreso", "Salida"])
    cantidad = st.number_input("Cantidad", min_value=1)
    area_destino = st.text_input("Área de destino")
    fecha = st.date_input("Fecha de ingreso/salida", datetime.now())
    observaciones = st.text_area("Observaciones")

    # Validación y registro
    if st.button("Registrar"):
        nombre_responsable = st.session_state["usuario"]
        nueva_fila = [
            codigo,
            accesorio['NOMBRE'],
            accesorio['MARCA'],
            accesorio['MODELO'],
            area_destino,
            fecha.strftime("%d/%m/%Y"),
            cantidad,
            observaciones,
            nombre_responsable
        ]

        if tipo == "Ingreso":
            hoja_in.append_row(nueva_fila)
            nuevo_stock = accesorio['STOCK'] + cantidad
            hoja_accesorios.update_cell(df[df["CÓDIGO"] == codigo].index[0] + 2, 9, nuevo_stock)
            st.success("Registro de ingreso agregado exitosamente.")
        elif tipo == "Salida":
            hoja_out.append_row(nueva_fila)
            nuevo_stock = accesorio['STOCK'] - cantidad
            hoja_accesorios.update_cell(df[df["CÓDIGO"] == codigo].index[0] + 2, 9, nuevo_stock)
            st.success("Registro de salida agregado exitosamente.")

    # Botón para cerrar sesión
    if st.button("Cerrar sesión"):
        del st.session_state["usuario"]
        st.session_state["page"] = "login"
        st.sidebar.button("Ir a la página de inicio de sesión", on_click=lambda: st.session_state.update({"page": "login"}))

# Navegación entre páginas usando sidebar
if "page" not in st.session_state:
    st.session_state["page"] = "login"

st.sidebar.title("Navegación")
if st.session_state["page"] == "login":
    st.sidebar.button("Inicio de Sesión", on_click=lambda: st.session_state.update({"page": "login"}))
    login_page()
elif st.session_state["page"] == "main":
    st.sidebar.button("Página Principal", on_click=lambda: st.session_state.update({"page": "main"}))
    main_page()
