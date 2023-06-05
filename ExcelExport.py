import pygsheets
import streamlit as st
import json
from google.oauth2 import service_account


class ExcelExport:
    '''
        Класс для экспорта данных в google sheets

        Параметры:
            df : датафрейм для экспорта в google sheets 
    '''

    def __init__(self, df):
        self.__df = df
        SCOPES = ('https://www.googleapis.com/auth/spreadsheets',
                  'https://www.googleapis.com/auth/drive')
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES)
        gc = pygsheets.authorize(custom_credentials=credentials)
        sheet = gc.open('my sheet')
        self.workspace = sheet.sheet1

    def export_to_google_sheet(self):
        counts = int(self.workspace[1][1]) + 3
        self.workspace.set_dataframe(self.__df, (counts, 1), copy_head=False)
