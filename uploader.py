import gspread

from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Autenticación con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("inventario-proy-18e59509428f.json", scope)
gc = gspread.authorize(credentials)

# Listar todos los documentos disponibles
from gspread.exceptions import APIError

try:
    spreadsheets = gc.list_spreadsheet_files()
    for sheet in spreadsheets:
        print(sheet["name"], sheet["id"])
except APIError as e:
    print("Error de API:", e)
