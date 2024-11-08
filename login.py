import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Autenticación con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(credentials)

# Cargar hoja de usuarios
spreadsheet = gc.open_by_key("1D3OHaLj2oARW3IJHEN7SV_uZSiZEOmFa8iRAsDGmyWY")
hoja_usuarios = spreadsheet.worksheet("USUARIOS")
usuarios_data = hoja_usuarios.get_all_records()
usuarios_df = pd.DataFrame(usuarios_data)

# Inicializar página
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# Función de autenticación
def autenticar(usuario, contraseña):
    user = usuarios_df[(usuarios_df["Usuario"] == usuario) & (usuarios_df["Contraseña"] == contraseña)]
    if not user.empty:
        return user.iloc[0]["Nombre"]
    return None

# Interfaz de inicio de sesión
st.title("Inicio de Sesión")
usuario = st.text_input("Usuario")
contraseña = st.text_input("Contraseña", type="password")

if st.button("Iniciar sesión"):
    nombre_responsable = autenticar(usuario, contraseña)
    if nombre_responsable:
        st.session_state["usuario"] = nombre_responsable
        st.session_state["page"] = "main"
        st.update_query_params(page="main")
        st.success(f"Bienvenido, {nombre_responsable}")
    else:
        st.error("Usuario o contraseña incorrectos.")
